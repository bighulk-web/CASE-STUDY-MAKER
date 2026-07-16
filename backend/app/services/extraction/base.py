"""Extraction data types and the format dispatcher."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedTable:
    """A table as a list of rows of cell strings."""

    rows: list[list[str]] = field(default_factory=list)
    caption: str = ""

    def to_text(self) -> str:
        return "\n".join(" | ".join(cell for cell in row) for row in self.rows)


@dataclass
class ExtractedImage:
    """An embedded image with raw bytes (persisted by the caller)."""

    data: bytes
    ext: str = "png"
    caption: str = ""


@dataclass
class ExtractedChart:
    """A chart reduced to a title + tabular data payload."""

    title: str = ""
    categories: list[str] = field(default_factory=list)
    series: dict[str, list[float]] = field(default_factory=dict)

    def to_text(self) -> str:
        parts = [f"Chart: {self.title}"] if self.title else ["Chart"]
        if self.categories:
            parts.append("Categories: " + ", ".join(self.categories))
        for name, values in self.series.items():
            parts.append(f"{name}: " + ", ".join(str(v) for v in values))
        return "\n".join(parts)


@dataclass
class ExtractionResult:
    text: str = ""
    tables: list[ExtractedTable] = field(default_factory=list)
    images: list[ExtractedImage] = field(default_factory=list)
    charts: list[ExtractedChart] = field(default_factory=list)
    page_count: int = 0
    has_ocr: bool = False

    def combined_text(self) -> str:
        """Text used for LLM analysis + embeddings: body + tables + charts."""
        parts = [self.text]
        for t in self.tables:
            parts.append(t.to_text())
        for c in self.charts:
            parts.append(c.to_text())
        return "\n\n".join(p for p in parts if p.strip())


def extract(path: str | Path, doc_type: str) -> ExtractionResult:
    """Dispatch to the appropriate format extractor.

    ``doc_type`` is one of ``pdf|docx|pptx|txt``.
    """
    p = Path(path)
    dt = doc_type.lower().lstrip(".")
    try:
        if dt == "pdf":
            from .pdf import extract_pdf

            return extract_pdf(p)
        if dt == "docx":
            from .docx import extract_docx

            return extract_docx(p)
        if dt == "pptx":
            from .pptx import extract_pptx

            return extract_pptx(p)
        if dt == "txt":
            from .txt import extract_txt

            return extract_txt(p)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Extraction failed for %s (%s): %s", p, dt, exc)
        raise
    raise ValueError(f"Unsupported document type: {doc_type}")


def detect_doc_type(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext in {"pptx", "docx", "pdf", "txt"}:
        return ext
    if ext in {"ppt"}:
        return "pptx"
    if ext in {"doc"}:
        return "docx"
    if ext in {"md", "text", "rtf"}:
        return "txt"
    raise ValueError(f"Unsupported file extension: .{ext}")
