"""Generate a lightweight preview (thumbnail image or text) for a document."""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings
from app.db.models import Document
from app.logging import get_logger

logger = get_logger(__name__)


def preview_image_path(document: Document) -> Path | None:
    """Return a path to a preview PNG, generating it on demand.

    PDFs are rendered with PyMuPDF. Other formats fall back to the first extracted
    image asset if present; otherwise ``None`` (callers show a text preview).
    """
    settings = get_settings()
    out = settings.previews_dir / f"doc_{document.id}.png"
    if out.exists():
        return out

    if document.doc_type == "pdf":
        try:
            import fitz

            doc = fitz.open(document.stored_path)
            if doc.page_count:
                pix = doc[0].get_pixmap(dpi=110)
                pix.save(str(out))
                doc.close()
                return out
            doc.close()
        except Exception as exc:  # pragma: no cover
            logger.debug("PDF preview failed: %s", exc)

    # Fallback: first extracted image.
    if document.extraction is not None:
        for asset in document.extraction.assets:
            if asset.kind == "image" and asset.stored_path and Path(asset.stored_path).exists():
                return Path(asset.stored_path)
    return None


def preview_text(document: Document, limit: int = 1200) -> str:
    if document.extraction is not None and document.extraction.raw_text:
        return document.extraction.raw_text[:limit]
    return ""
