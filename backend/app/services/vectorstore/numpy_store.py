"""Dependency-free persistent vector store backed by a JSON file + numpy math.

Suitable for local libraries of up to tens of thousands of case studies. Vectors are
kept in memory and flushed to disk on every mutation (each write is synchronous).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import numpy as np

from app.config import get_settings

from .base import QueryHit


class NumpyVectorStore:
    name = "numpy"

    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self._path = path or (settings.data_dir / "vectors.json")
        self._lock = threading.RLock()
        self._ids: list[str] = []
        self._vectors: list[list[float]] = []
        self._metadata: dict[str, dict[str, Any]] = {}
        self._documents: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            data = json.loads(self._path.read_text())
            self._ids = data.get("ids", [])
            self._vectors = data.get("vectors", [])
            self._metadata = data.get("metadata", {})
            self._documents = data.get("documents", {})

    def _flush(self) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                {
                    "ids": self._ids,
                    "vectors": self._vectors,
                    "metadata": self._metadata,
                    "documents": self._documents,
                }
            )
        )
        tmp.replace(self._path)

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        documents: list[str],
    ) -> None:
        with self._lock:
            for i, _id in enumerate(ids):
                if _id in self._ids:
                    pos = self._ids.index(_id)
                    self._vectors[pos] = embeddings[i]
                else:
                    self._ids.append(_id)
                    self._vectors.append(embeddings[i])
                self._metadata[_id] = metadatas[i]
                self._documents[_id] = documents[i]
            self._flush()

    def query(self, embedding: list[float], n: int = 10) -> list[QueryHit]:
        with self._lock:
            if not self._ids:
                return []
            mat = np.asarray(self._vectors, dtype=np.float32)
            q = np.asarray(embedding, dtype=np.float32)
            # Vectors are stored normalized; normalize query defensively.
            qn = np.linalg.norm(q)
            if qn > 0:
                q = q / qn
            sims = mat @ q
            order = np.argsort(-sims)[:n]
            return [
                QueryHit(
                    id=self._ids[i],
                    score=float(sims[i]),
                    metadata=self._metadata.get(self._ids[i], {}),
                )
                for i in order
            ]

    def delete(self, ids: list[str]) -> None:
        with self._lock:
            for _id in ids:
                if _id in self._ids:
                    pos = self._ids.index(_id)
                    del self._ids[pos]
                    del self._vectors[pos]
                self._metadata.pop(_id, None)
                self._documents.pop(_id, None)
            self._flush()

    def count(self) -> int:
        return len(self._ids)
