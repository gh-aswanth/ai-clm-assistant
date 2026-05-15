"""WebSocket endpoint: graph-backed chat using GraphCypherQAChain."""

from __future__ import annotations

import asyncio
import json
import logging
import os

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.db.database import SessionLocal
from app.api.auth import _get_current_user_from_token
from app.services.graph_cypher_chat import GraphChatConfigError, run_graph_chat_question
from app.services.review_system import run_review, ReviewSystemError, get_review_agent
from app.services.draft_system import run_draft, DraftSystemError, get_redline_agent
from app.services.comparison_chat import run_document_compare, ComparisonSystemError
from app.services.cpwd_copilot import build_cpwd_copilot_augmentation

logger = logging.getLogger(__name__)

router = APIRouter()


def _premium_cpwd_eligible(db, access_token: str | None) -> bool:
    """When CLM_ENFORCE_PREMIUM is set, require a valid JWT and User.premium_access."""
    enforce = os.getenv("CLM_ENFORCE_PREMIUM", "").lower() in ("1", "true", "yes")
    if not enforce:
        return True
    if not access_token or not str(access_token).strip():
        return False
    try:
        user = _get_current_user_from_token(str(access_token).strip(), db)
        return bool(getattr(user, "premium_access", False))
    except HTTPException:
        return False


@router.websocket("/review")
async def review_chat_websocket(websocket: WebSocket):
    await websocket.accept()
    agent = get_review_agent()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "detail": "Invalid JSON. Send {\"type\":\"chat\",\"message\":\"...\"}"}
                )
                continue

            if payload.get("type") != "chat":
                await websocket.send_json({"type": "error", "detail": "Unsupported message type"})
                continue

            message = payload.get("message") or payload.get("text") or ""
            if not isinstance(message, str):
                await websocket.send_json({"type": "error", "detail": "message must be a string"})
                continue

            def _opt_int(name: str) -> int | None:
                v = payload.get(name)
                if v is None or v == "":
                    return None
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return None

            version_id = _opt_int("version_id")
            contract_id = _opt_int("contract_id")
            want_copilot = bool(
                payload.get("cpwd_copilot") or payload.get("premium_cpwd_copilot")
            )
            access_token = payload.get("access_token")

            raw_override = payload.get("comprehensive_contract")
            comprehensive_contract_override = None
            if isinstance(raw_override, str) and raw_override.strip():
                comprehensive_contract_override = raw_override

            db = SessionLocal()
            try:
                cpwd_aug = None
                if want_copilot:
                    if not _premium_cpwd_eligible(db, access_token):
                        await websocket.send_json(
                            {
                                "type": "error",
                                "detail": (
                                    "CPWD Copilot is a premium capability. "
                                    "Use an account with premium access, or ask your admin to enable it."
                                ),
                            }
                        )
                        continue
                    if contract_id is not None:
                        cpwd_aug = build_cpwd_copilot_augmentation(
                            db,
                            contract_id=contract_id,
                            version_id=version_id,
                            include_saved_review_items=False,
                        )
                await run_review(
                    websocket,
                    message,
                    agent,
                    version_id=version_id,
                    contract_id=contract_id,
                    db=db,
                    cpwd_augmentation=cpwd_aug,
                    comprehensive_contract_override=comprehensive_contract_override,
                )
            except ReviewSystemError as e:
                logger.warning("Review agent misconfigured: %s", e)
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": str(e) + " — ensure OPENAI_API_KEY is set for the review agent.",
                    }
                )
            except Exception as e:
                logger.exception("Review chat failed")
                await websocket.send_json({"type": "error", "detail": str(e) or "Review chat failed"})
            finally:
                db.close()

    except WebSocketDisconnect:
        pass


@router.websocket("/draft")
async def draft_chat_websocket(websocket: WebSocket):
    await websocket.accept()
    agent = get_redline_agent()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "detail": "Invalid JSON. Send {\"type\":\"chat\",\"message\":\"...\"}"}
                )
                continue

            if payload.get("type") != "chat":
                await websocket.send_json({"type": "error", "detail": "Unsupported message type"})
                continue

            message = payload.get("message") or payload.get("text") or ""
            if not isinstance(message, str):
                await websocket.send_json({"type": "error", "detail": "message must be a string"})
                continue

            def _opt_int(name: str) -> int | None:
                v = payload.get(name)
                if v is None or v == "":
                    return None
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return None

            version_id = _opt_int("version_id")
            contract_id = _opt_int("contract_id")
            want_copilot = bool(
                payload.get("cpwd_copilot") or payload.get("premium_cpwd_copilot")
            )
            access_token = payload.get("access_token")

            db = SessionLocal()
            try:
                cpwd_aug = None
                if want_copilot:
                    if not _premium_cpwd_eligible(db, access_token):
                        await websocket.send_json(
                            {
                                "type": "error",
                                "detail": (
                                    "CPWD Copilot is a premium capability. "
                                    "Use an account with premium access, or ask your admin to enable it."
                                ),
                            }
                        )
                        continue
                    if contract_id is not None:
                        cpwd_aug = build_cpwd_copilot_augmentation(
                            db,
                            contract_id=contract_id,
                            version_id=version_id,
                        )
                        print(cpwd_aug)
                await run_draft(
                    websocket,
                    message,
                    agent,
                    version_id=version_id,
                    contract_id=contract_id,
                    db=db,
                    cpwd_augmentation=cpwd_aug,
                )
            except DraftSystemError as e:
                logger.warning("Draft agent misconfigured: %s", e)
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": str(e) + " — ensure OPENAI_API_KEY is set for the draft agent.",
                    }
                )
            except Exception as e:
                logger.exception("Draft chat failed")
                await websocket.send_json({"type": "error", "detail": str(e) or "Draft chat failed"})
            finally:
                db.close()

    except WebSocketDisconnect:
        pass


@router.websocket("/compare")
async def compare_chat_websocket(websocket: WebSocket):
    """Compare two contract document versions: extracts PDF/DOCX text, streams LLM table-style answer."""
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": "Invalid JSON. Send "
                        '{"type":"chat","contract_id":1,"version_a_id":2,"version_b_id":3,"message":"..."}',
                    }
                )
                continue

            if payload.get("type") != "chat":
                await websocket.send_json({"type": "error", "detail": "Unsupported message type"})
                continue

            message = payload.get("message") or payload.get("text") or ""
            if not isinstance(message, str):
                await websocket.send_json({"type": "error", "detail": "message must be a string"})
                continue

            def _req_int(name: str) -> int | None:
                v = payload.get(name)
                if v is None or v == "":
                    return None
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return None

            contract_id = _req_int("contract_id")
            version_a_id = _req_int("version_a_id")
            version_b_id = _req_int("version_b_id")
            if contract_id is None or version_a_id is None or version_b_id is None:
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": "contract_id, version_a_id, and version_b_id are required integers.",
                    }
                )
                continue

            db = SessionLocal()
            try:
                await run_document_compare(
                    websocket,
                    db=db,
                    contract_id=contract_id,
                    version_a_id=version_a_id,
                    version_b_id=version_b_id,
                    user_message=message,
                )
            except ComparisonSystemError as e:
                logger.warning("Document compare validation / IO: %s", e)
                await websocket.send_json({"type": "error", "detail": str(e)})
            except Exception as e:
                logger.exception("Document compare failed")
                await websocket.send_json({"type": "error", "detail": str(e) or "Compare chat failed"})
            finally:
                db.close()

    except WebSocketDisconnect:
        pass


@router.websocket("/graph-chat")
async def graph_chat_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "detail": "Invalid JSON. Send {\"type\":\"chat\",\"message\":\"...\"}"}
                )
                continue

            if payload.get("type") != "chat":
                await websocket.send_json({"type": "error", "detail": "Unsupported message type"})
                continue

            message = payload.get("message") or payload.get("text") or ""
            if not isinstance(message, str):
                await websocket.send_json({"type": "error", "detail": "message must be a string"})
                continue

            try:
                answer = await asyncio.to_thread(run_graph_chat_question, message)
                await websocket.send_json({"type": "final", "text": answer})
                await websocket.send_json({"type": "final", "json_data": answer})

            except GraphChatConfigError as e:
                logger.warning("Graph chat misconfigured: %s", e)
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": str(e)
                        + " — set OPENAI_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in the server environment.",
                    }
                )
            except Exception as e:
                logger.exception("Graph chat failed")
                await websocket.send_json({"type": "error", "detail": str(e) or "Graph chat failed"})

    except WebSocketDisconnect:
        pass
