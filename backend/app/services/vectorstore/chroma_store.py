"""ChromaDB-backed vector store (optional)."""

from __future__ import annotations

from typing import Any

from app.config import get_settings

from .base import QueryHit


class ChromaVectorStore:  # pragma: no cover - optional dependency
    name = "chroma"

    def __init__(self, collection_name: str = "case_studies") -> None:
        import chromadb

        settings = get_settings()
        self._client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self._collection = self._client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        documents: list[str],
    ) -> None:
        self._collection.upsert(
            ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents
        )

    def query(self, embedding: list[float], n: int = 10) -> list[QueryHit]:
        res = self._collection.query(query_embeddings=[embedding], n_results=n)
        hits: list[QueryHit] = []
        ids = res.get("ids", [[]])[0]
        distances = res.get("distances", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        for i, _id in enumerate(ids):
            # Chroma cosine distance -> similarity.
            dist = distances[i] if i < len(distances) else 0.0
            hits.append(
                QueryHit(id=_id, score=1.0 - float(dist), metadata=metadatas[i] if metadatas else {})
            )
        return hits

    def delete(self, ids: list[str]) -> None:
        self._collection.delete(ids=ids)

    def count(self) -> int:
        return self._collection.count()
