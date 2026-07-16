"""Embedding provider abstraction.

Default is a dependency-free deterministic hashing embedding so semantic search
works fully offline. ``bge_local`` (sentence-transformers) and ``openai`` are opt-in.
"""

from __future__ import annotations

from .base import EmbeddingProvider
from .factory import get_embedding_provider

__all__ = ["EmbeddingProvider", "get_embedding_provider"]
