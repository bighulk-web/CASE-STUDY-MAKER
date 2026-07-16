from __future__ import annotations

from pathlib import Path

from tests import fixtures


def _upload(client, path: Path, folder_id: int | None = None):
    data = {"folder_id": str(folder_id)} if folder_id is not None else {}
    with path.open("rb") as fh:
        return client.post(
            "/api/documents",
            files=[("files", (path.name, fh.read()))],
            data=data,
        )


def test_upload_and_extract_all_formats(client, tmp_path: Path) -> None:
    makers = {
        "s.txt": fixtures.make_txt,
        "s.docx": fixtures.make_docx,
        "s.pptx": fixtures.make_pptx,
        "s.pdf": fixtures.make_pdf,
    }
    for name, maker in makers.items():
        p = maker(tmp_path / name)
        resp = _upload(client, p)
        assert resp.status_code == 200, resp.text
        doc = resp.json()[0]
        # Extraction runs synchronously (Phase 1) -> ready.
        got = client.get(f"/api/documents/{doc['id']}")
        assert got.json()["status"] == "ready"

    listing = client.get("/api/documents").json()
    assert listing["total"] == 4


def test_duplicate_detection(client, tmp_path: Path) -> None:
    p = fixtures.make_txt(tmp_path / "dup.txt")
    first = _upload(client, p).json()[0]
    second = _upload(client, p).json()[0]
    assert first["is_duplicate_of"] is None
    assert second["is_duplicate_of"] == first["id"]


def test_rename_and_delete(client, tmp_path: Path) -> None:
    p = fixtures.make_docx(tmp_path / "r.docx")
    doc = _upload(client, p).json()[0]
    patched = client.patch(f"/api/documents/{doc['id']}", json={"title": "Renamed"})
    assert patched.json()["title"] == "Renamed"
    deleted = client.delete(f"/api/documents/{doc['id']}")
    assert deleted.json()["deleted"] is True
    assert client.get(f"/api/documents/{doc['id']}").status_code == 404


def test_versions(client, tmp_path: Path) -> None:
    p = fixtures.make_txt(tmp_path / "v.txt", text="version one content")
    doc = _upload(client, p).json()[0]
    p2 = fixtures.make_txt(tmp_path / "v2.txt", text="version two different content")
    with p2.open("rb") as fh:
        resp = client.post(
            f"/api/documents/{doc['id']}/versions",
            files=[("file", ("v.txt", fh.read()))],
            data={"note": "second"},
        )
    assert resp.status_code == 200
    versions = client.get(f"/api/documents/{doc['id']}/versions").json()
    assert len(versions) == 2
    assert versions[0]["version_no"] == 2


def test_folders(client, tmp_path: Path) -> None:
    folder = client.post("/api/folders", json={"name": "Manufacturing"}).json()
    p = fixtures.make_txt(tmp_path / "f.txt")
    doc = _upload(client, p, folder_id=folder["id"]).json()[0]
    assert doc["folder_id"] == folder["id"]
    listing = client.get(f"/api/documents?folder_id={folder['id']}").json()
    assert listing["total"] == 1


def test_preview(client, tmp_path: Path) -> None:
    p = fixtures.make_pdf(tmp_path / "prev.pdf")
    doc = _upload(client, p).json()[0]
    resp = client.get(f"/api/documents/{doc['id']}/preview")
    assert resp.status_code == 200
