"""Document content extraction subsystem.

Each format extractor turns a file into an :class:`ExtractionResult` containing the
concatenated text plus structured tables, images, and charts. Storage of assets to
disk is handled by callers (the ingestion/analysis layer), keeping extractors pure.
"""

from __future__ import annotations

from .base import (
    ExtractedChart,
    ExtractedImage,
    ExtractedTable,
    ExtractionResult,
    extract,
)

__all__ = [
    "ExtractedChart",
    "ExtractedImage",
    "ExtractedTable",
    "ExtractionResult",
    "extract",
]
