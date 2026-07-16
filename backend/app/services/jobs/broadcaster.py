"""Fan-out of job progress events to connected WebSocket clients."""

from __future__ import annotations

import asyncio
from typing import Any

from app.logging import get_logger

logger = get_logger(__name__)


class Broadcaster:
    def __init__(self) -> None:
        self._clients: set[Any] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, ws: Any) -> None:
        self._clients.add(ws)

    def disconnect(self, ws: Any) -> None:
        self._clients.discard(ws)

    async def _send_all(self, message: dict[str, Any]) -> None:
        dead = []
        for ws in list(self._clients):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._clients.discard(ws)

    def publish(self, message: dict[str, Any]) -> None:
        """Thread-safe publish; schedules the send on the bound event loop."""
        if self._loop is None or not self._clients:
            return
        try:
            asyncio.run_coroutine_threadsafe(self._send_all(message), self._loop)
        except Exception as exc:  # pragma: no cover
            logger.debug("broadcast failed: %s", exc)


broadcaster = Broadcaster()
