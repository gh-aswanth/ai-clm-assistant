import logging
import os
from typing import Optional

from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from fastapi import WebSocket
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_review_agent():
    checkpoint = InMemorySaver()
    return create_agent(
        model=ChatOpenAI(model=os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4"), streaming=True),
        checkpointer=checkpoint,
        debug=False,
        system_prompt="""You are a helpful assistant. You are given a contract document (assembled from stored text chunks for the selected version) and you need to answer questions about it.""",
        middleware=[TodoListMiddleware()],
    )


class ReviewSystemError(RuntimeError):
    pass


def build_contract_text_for_review(
    db: Session,
    *,
    contract_id: Optional[int] = None,
    version_id: Optional[int] = None,
) -> str:
    """
    Full contract body for the review agent: ordered chunks for ``version_id``'s file,
    else legacy ``contracts.content`` when chunks are missing.
    """
    from app.models.models import Contract, DocumentVersion
    from app.services.document_chunker import get_chunks_for_version

    if version_id and db:
        version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
        if not version:
            logger.warning("Review: document version id=%s not found", version_id)
        elif contract_id is not None and version.contract_id != contract_id:
            logger.warning(
                "Review: version id=%s belongs to contract %s, not %s — skipping chunk context",
                version_id,
                version.contract_id,
                contract_id,
            )
        elif not version.file_id:
            logger.warning("Review: version id=%s has no file_id — no chunks", version_id)
        else:
            stored = get_chunks_for_version(db, version_id)
            parts = [c.content for c in stored]
            if parts:
                return "\n\n".join(parts)

    if contract_id and db:
        c = db.query(Contract).filter(Contract.id == contract_id).first()
        if c and c.content and str(c.content).strip():
            return str(c.content).strip()

    return ""


def _cap_review_contract_text(text: str, max_len: int = 800_000) -> str:
    t = str(text or "").strip()
    if len(t) <= max_len:
        return t
    return t[:max_len] + "\n\n[… truncated to context limit …]"


async def run_review(
    websocket: WebSocket,
    message: str,
    review_agent,
    *,
    version_id: Optional[int] = None,
    contract_id: Optional[int] = None,
    db: Optional[Session] = None,
    cpwd_augmentation: Optional[str] = None,
    comprehensive_contract_override: Optional[str] = None,
):
    """
    Stream agent events to the client.
    json_data matches the shape in notebook/events.json: { "name": "write_todos"|"model", "data": ... }

    Contract text is loaded from ``document_chunks`` via the selected ``DocumentVersion``'s ``file_id``,
    unless ``comprehensive_contract_override`` is set (e.g. preview highlight only).
    """
    comprehensive_contract = ""
    if comprehensive_contract_override is not None and str(comprehensive_contract_override).strip():
        comprehensive_contract = _cap_review_contract_text(comprehensive_contract_override)
    elif db:
        comprehensive_contract = build_contract_text_for_review(
            db, contract_id=contract_id, version_id=version_id
        )
    if not comprehensive_contract.strip():
        comprehensive_contract = (
            "(No contract text available for this version. "
            "Ensure a document is uploaded, linked to the version, and chunked.)"
        )

    logger.debug(
        "Review agent: contract_id=%s version_id=%s text_len=%s cpwd_copilot=%s",
        contract_id,
        version_id,
        len(comprehensive_contract),
        bool(cpwd_augmentation),
    )

    messages: list[dict] = [{"role": "user", "content": comprehensive_contract}]
    if cpwd_augmentation and str(cpwd_augmentation).strip():
        messages.append(
            {
                "role": "user",
                "content": (
                    "[PREMIUM CPWD COPILOT — CONTEXT PACK]\n"
                    "For this run, treat the sections below as your standing reference material alongside the contract text:\n"
                    "- Guideline snapshot — corporate / CPWD posture and mandatory themes to check against.\n"
                    "- Compliance rows — automated check outcomes; use them as pointers to clauses to validate.\n"
                    "- Scoring summary — multi-agent risk and quality signals; weigh them in your conclusions.\n"
                    "Ground every material point in the actual contract language; use the reference pack to flag misalignment, "
                    "gaps, and priority issues. Tie recommendations to specific clauses where possible.\n\n"
                    + str(cpwd_augmentation).strip()
                    + "\n[END CPWD COPILOT CONTEXT]"
                ),
            }
        )
    messages.append(
        {
            "role": "user",
            "content": f"""
                     UserQuery: {message}\n
                     ---------------------------------
                     ###workflow
                     1. use todo tool prepare a plan
                     2. update the todo list everytime a after plan is executed
                     """,
        }
    )

    async for event in review_agent.astream_events(
        {"messages": messages},
        config=RunnableConfig(configurable={"thread_id": 1}, recursion_limit=100),
        version="v2",
    ):
        if event.get("name") == "write_todos":
            todos = event.get("data", {}).get("input", {}).get("todos", [])
            await websocket.send_json(
                {"type": "stream", "json_data": {"name": "write_todos", "data": todos}}
            )
        if event["event"] == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            await websocket.send_json(
                {"type": "stream", "json_data": {"name": "model", "data": content}}
            )
        if event.get("event") == "on_chain_stream" and event.get("name") == "model":
            chunk = event.get("data", {}).get("chunk")
            if chunk is None:
                continue
            chunks = chunk if isinstance(chunk, (list, tuple)) else [chunk]
            for ev in chunks:
                try:
                    update = getattr(ev, "update", None) or (
                        ev.get("update") if isinstance(ev, dict) else None
                    )
                    if not update:
                        continue
                    messages = update.get("messages") if isinstance(update, dict) else None
                    if not messages:
                        continue
                    first = messages[0]
                    content = getattr(first, "content", None)
                    if content is None and isinstance(first, dict):
                        content = first.get("content")
                    if content:
                        await websocket.send_json(
                            {"type": "stream", "json_data": {"name": "model", "data": content}}
                        )
                except Exception:
                    continue

    await websocket.send_json({"type": "done"})
