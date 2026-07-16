"""Consistent error handling for the API.

All unhandled exceptions become a JSON body ``{"error": {"type", "message"}}`` so the
frontend can surface a useful message instead of an opaque 500. API keys and other
secrets are never echoed back.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging import get_logger

logger = get_logger(__name__)


def _payload(kind: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"type": kind, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exc(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_payload("http_error", str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def validation_exc(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content=_payload("validation_error", str(exc.errors())))

    @app.exception_handler(Exception)
    async def unhandled_exc(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_payload("internal_error", "An unexpected error occurred."),
        )
