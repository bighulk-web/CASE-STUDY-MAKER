"""Vector store abstraction (Chroma when available, numpy JSON fallback otherwise)."""

from __future__ import annotations

from .base import QueryHit, VectorStore
from .factory import get_vector_store

__all__ = ["QueryHit", "VectorStore", "get_vector_store"]
