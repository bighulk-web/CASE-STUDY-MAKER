"""Settings API: read/update provider configuration and trigger reindex."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    llm_provider: str | None = None
    llm_model: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    vectorstore_provider: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    theme: str | None = None


@router.get("", response_model=dict)
def get_settings_ep() -> dict[str, Any]:
    return settings_service.public_settings()


@router.put("", response_model=dict)
def update_settings_ep(body: SettingsUpdate) -> dict[str, Any]:
    values = {k: v for k, v in body.model_dump().items() if v is not None}
    if values:
        settings_service.set_many(values)
    # Provider/embedding changes invalidate cached instances.
    from app.services.embeddings.factory import reset_cache
    from app.services.vectorstore.factory import reset_instance

    reset_cache()
    reset_instance()
    return settings_service.public_settings()


@router.post("/reindex", response_model=dict)
def reindex_ep() -> dict[str, int]:
    from app.services.jobs.queue import enqueue

    job_id = enqueue("reindex")
    return {"job_id": job_id}
