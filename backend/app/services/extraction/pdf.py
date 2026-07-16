"""PDF extractor using PyMuPDF (fitz), with optional OCR fallback."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from app.logging import get_logger

from .base import ExtractedImage, ExtractedTable, ExtractionResult

logger = get_logger(__name__)

# Pages with fewer than this many characters of text are considered image-only
# candidates for OCR.
_OCR_TEXT_THRESHOLD = 12


def extract_pdf(path: Path) -> ExtractionResult:
    result = ExtractionResult()
    doc = fitz.open(str(path))
    texts: list[str] = []
    result.page_count = doc.page_count

    for page in doc:
        page_text = page.get_text("text") or ""

        if len(page_text.strip()) < _OCR_TEXT_THRESHOLD:
            ocr_text = _try_ocr(page)
            if ocr_text:
                page_text = ocr_text
                result.has_ocr = True

        if page_text.strip():
            texts.append(page_text)

        # Tables (best-effort; available in modern PyMuPDF).
        try:
            tables = page.find_tables()
            for tbl in tables.tables:
                rows = [[(c or "") for c in row] for row in tbl.extract()]
                if rows:
                    result.tables.append(ExtractedTable(rows=rows))
        except Exception:
            pass

        # Embedded images.
        try:
            for img in page.get_images(full=True):
                xref = img[0]
                base = doc.extract_image(xref)
                result.images.append(
                    ExtractedImage(data=base["image"], ext=base.get("ext", "png"))
                )
        except Exception:
            pass

    result.text = "\n\n".join(texts)
    doc.close()
    return result


def _try_ocr(page) -> str:
    """OCR a page if pytesseract + the tesseract binary are available."""
    import shutil

    if shutil.which("tesseract") is None:
        return ""
    try:
        import io

        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=200)
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(image)
    except Exception as exc:  # pragma: no cover - optional path
        logger.debug("OCR failed: %s", exc)
        return ""
