"""Singleton in-process notification broadcaster for background-task events.

Background threads call ``notifier.broadcast_from_thread(msg)``; the manager
schedules the coroutine on the main asyncio event loop so all connected
WebSocket clients receive the message without blocking or thread-safety issues.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class NotificationManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        logger.debug("Notification WS connected; total=%d", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        logger.debug("Notification WS disconnected; total=%d", len(self._connections))

    async def _broadcast(self, message: dict[str, Any]) -> None:
        dead: set[WebSocket] = set()
        for ws in list(self._connections):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections.discard(ws)

    def broadcast_from_thread(self, message: dict[str, Any]) -> None:
        """Safe to call from any background thread."""
        if self._loop is None or self._loop.is_closed():
            logger.debug("No event loop available for notification: %s", message)
            return
        try:
            asyncio.run_coroutine_threadsafe(self._broadcast(message), self._loop)
        except Exception as exc:
            logger.warning("Failed to schedule notification broadcast: %s", exc)


notifier = NotificationManager()
