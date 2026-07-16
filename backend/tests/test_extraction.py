from __future__ import annotations

from pathlib import Path

import pytest

from app.services.extraction import extract
from app.services.extraction.base import detect_doc_type
from tests import fixtures


def test_detect_doc_type() -> None:
    assert detect_doc_type("a.pptx") == "pptx"
    assert detect_doc_type("a.PDF") == "pdf"
    assert detect_doc_type("a.md") == "txt"
    with pytest.raises(ValueError):
        detect_doc_type("a.xyz")


def test_extract_txt(tmp_path: Path) -> None:
    p = fixtures.make_txt(tmp_path / "s.txt")
    res = extract(p, "txt")
    assert "SAP S/4HANA" in res.text
    assert res.page_count == 1


def test_extract_docx(tmp_path: Path) -> None:
    p = fixtures.make_docx(tmp_path / "s.docx")
    res = extract(p, "docx")
    assert "Acme Manufacturing" in res.text
    assert len(res.tables) == 1
    assert any("30%" in cell for row in res.tables[0].rows for cell in row)


def test_extract_pptx(tmp_path: Path) -> None:
    p = fixtures.make_pptx(tmp_path / "s.pptx")
    res = extract(p, "pptx")
    assert "Acme Manufacturing" in res.text
    assert len(res.tables) >= 1
    assert len(res.images) >= 1
    assert "Cost savings" in res.combined_text()


def test_extract_pdf(tmp_path: Path) -> None:
    p = fixtures.make_pdf(tmp_path / "s.pdf")
    res = extract(p, "pdf")
    assert "Acme Manufacturing" in res.text
    assert res.page_count == 1
