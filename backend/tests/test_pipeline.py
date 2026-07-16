from __future__ import annotations

from pathlib import Path

from tests import fixtures


def _upload(client, path: Path):
    with path.open("rb") as fh:
        return client.post("/api/documents", files=[("files", (path.name, fh.read()))])


def test_upload_produces_case_study_and_index(client, tmp_path: Path) -> None:
    p = fixtures.make_pptx(tmp_path / "acme.pptx")
    resp = _upload(client, p)
    assert resp.status_code == 200
    doc_id = resp.json()[0]["id"]

    # Document is ready and a case study was created + indexed.
    doc = client.get(f"/api/documents/{doc_id}").json()
    assert doc["status"] == "ready"

    # A job was recorded.
    jobs = client.get("/api/jobs").json()
    assert any(j["type"] == "pipeline" and j["status"] == "done" for j in jobs)


def test_pipeline_analysis_offline(client, tmp_path: Path) -> None:
    from app.db.base import session_scope
    from app.db.models import CaseStudy

    p = fixtures.make_txt(
        tmp_path / "c.txt",
        text="Globex Healthcare deployed an AI diagnostics platform in APAC, "
        "cutting patient wait times by 40% in 9 months.",
    )
    _upload(client, p)

    with session_scope() as s:
        cs = s.query(CaseStudy).first()
        assert cs is not None
        assert cs.industry == "Healthcare"
        assert "Artificial Intelligence" in (cs.technology or [])
        assert cs.region == "APAC"
        assert cs.indexed == 1
