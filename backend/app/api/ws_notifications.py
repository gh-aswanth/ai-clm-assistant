"""WebSocket endpoint: real-time background-task notifications."""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.notifier import notifier

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/notifications")
async def notifications_websocket(websocket: WebSocket) -> None:
    """Clients connect here to receive push notifications for background tasks.

    Message schema (JSON):
        {
            "type":        "chunking_started" | "chunking_done" | "chunking_failed"
                         | "compliance_started" | "compliance_done" | "compliance_failed",
            "file_id":     int,
            "contract_id": int | null,   // null for drive-only files
            "folder_id":   int | null,   // null for contract uploads
            "filename":    str,
            "message":     str
        }
    """
    await notifier.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        notifier.disconnect(websocket)
