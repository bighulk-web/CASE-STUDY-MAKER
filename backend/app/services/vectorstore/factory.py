"""Construct the configured vector store (Chroma if available, else numpy)."""

from __future__ import annotations

import importlib.util

from app.logging import get_logger

from .base import VectorStore
from .numpy_store import NumpyVectorStore

logger = get_logger(__name__)

_instance: VectorStore | None = None
_instance_key: str | None = None


def _has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def get_vector_store() -> VectorStore:
    global _instance, _instance_key
    from app.config import get_settings
    from app.services.settings_service import get_value

    provider = (get_value("vectorstore_provider") or "auto").lower()
    key = f"{provider}:{get_settings().data_dir}"
    if _instance is not None and _instance_key == key:
        return _instance

    if provider == "numpy":
        store: VectorStore = NumpyVectorStore()
    elif provider == "chroma" or (provider == "auto" and _has("chromadb")):
        try:
            from .chroma_store import ChromaVectorStore

            store = ChromaVectorStore()
        except Exception as exc:  # pragma: no cover
            logger.warning("Chroma unavailable (%s); using numpy store", exc)
            store = NumpyVectorStore()
    else:
        store = NumpyVectorStore()

    _instance = store
    _instance_key = key
    logger.info("Vector store: %s", store.name)
    return store


def reset_instance() -> None:
    global _instance, _instance_key
    _instance = None
    _instance_key = None
