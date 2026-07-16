from __future__ import annotations

from pathlib import Path

from app.services.embeddings.hashing import HashingEmbedding
from app.services.vectorstore.numpy_store import NumpyVectorStore


def test_hashing_embedding_is_deterministic_and_normalized() -> None:
    emb = HashingEmbedding(dim=256)
    a = emb.embed(["SAP S/4HANA manufacturing"])[0]
    b = emb.embed(["SAP S/4HANA manufacturing"])[0]
    assert a == b
    norm = sum(x * x for x in a) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_hashing_similarity_orders_related_text() -> None:
    emb = HashingEmbedding(dim=512)
    q = emb.embed(["manufacturing SAP ERP implementation"])[0]
    related = emb.embed(["SAP ERP manufacturing supply chain project"])[0]
    unrelated = emb.embed(["healthcare patient scheduling mobile app"])[0]

    def cos(x, y):
        return sum(a * b for a, b in zip(x, y, strict=False))

    assert cos(q, related) > cos(q, unrelated)


def test_numpy_store_roundtrip(tmp_path: Path) -> None:
    store = NumpyVectorStore(path=tmp_path / "vec.json")
    emb = HashingEmbedding(dim=128)
    ids = ["1", "2", "3"]
    docs = ["manufacturing SAP", "healthcare AI", "banking oracle"]
    vecs = emb.embed(docs)
    store.upsert(ids, vecs, [{"case_study_id": int(i)} for i in ids], docs)
    assert store.count() == 3

    q = emb.embed(["SAP manufacturing project"])[0]
    hits = store.query(q, n=2)
    assert hits[0].id == "1"

    # Persistence: a fresh store loads the same data.
    store2 = NumpyVectorStore(path=tmp_path / "vec.json")
    assert store2.count() == 3
    store2.delete(["1"])
    assert store2.count() == 2
