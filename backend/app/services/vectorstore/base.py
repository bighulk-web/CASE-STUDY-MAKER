"""Vector store protocol and result type."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class QueryHit:
    id: str
    score: float  # cosine similarity in [-1, 1] (higher is better)
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore(Protocol):
    name: str

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        documents: list[str],
    ) -> None: ...

    def query(self, embedding: list[float], n: int = 10) -> list[QueryHit]: ...

    def delete(self, ids: list[str]) -> None: ...

    def count(self) -> int: ...
