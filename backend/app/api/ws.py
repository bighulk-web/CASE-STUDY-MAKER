"""WebSocket endpoint streaming job progress events."""

from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.services.jobs.broadcaster import broadcaster


def register_ws(app: FastAPI) -> None:
    @app.websocket("/ws/jobs")
    async def jobs_ws(ws: WebSocket) -> None:
        await ws.accept()
        await broadcaster.connect(ws)
        try:
            while True:
                # We only push; keep the connection alive by awaiting client pings.
                await ws.receive_text()
        except WebSocketDisconnect:
            broadcaster.disconnect(ws)
        except Exception:
            broadcaster.disconnect(ws)
