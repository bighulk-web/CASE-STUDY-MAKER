"""Plain-text extractor."""

from __future__ import annotations

from pathlib import Path

from .base import ExtractionResult


def extract_txt(path: Path) -> ExtractionResult:
    text = path.read_text(encoding="utf-8", errors="replace")
    return ExtractionResult(text=text, page_count=1)
