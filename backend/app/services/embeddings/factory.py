"""Construct the configured embedding provider with graceful fallback."""

from __future__ import annotations

import importlib.util

from app.logging import get_logger

from .base import EmbeddingProvider
from .hashing import HashingEmbedding

logger = get_logger(__name__)

_cache: dict[str, EmbeddingProvider] = {}


def _has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def get_embedding_provider() -> EmbeddingProvider:
    from app.services.settings_service import get_value

    provider = (get_value("embedding_provider") or "auto").lower()
    model = get_value("embedding_model")

    if provider in _cache:
        return _cache[provider]

    result: EmbeddingProvider
    if provider == "hashing":
        result = HashingEmbedding()
    elif provider == "openai":
        from .openai_embed import OpenAIEmbedding

        oa = OpenAIEmbedding(api_key=get_value("openai_api_key"), model=model or "text-embedding-3-large")
        result = oa if oa.available() else HashingEmbedding()
    elif provider == "bge_local" or (provider == "auto" and _has("sentence_transformers")):
        from .bge_local import BGELocalEmbedding

        result = BGELocalEmbedding(model or "BAAI/bge-large-en-v1.5")
    else:
        result = HashingEmbedding()

    _cache[provider] = result
    logger.info("Embedding provider: %s (dim=%s)", result.name, getattr(result, "dim", "?"))
    return result


def reset_cache() -> None:
    _cache.clear()
