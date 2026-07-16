from __future__ import annotations


def test_health_ok(client) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "offline"


def test_capabilities_shape(client) -> None:
    resp = client.get("/api/capabilities")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("chromadb", "sentence_transformers", "libreoffice", "tesseract"):
        assert key in body
        assert isinstance(body[key], bool)
