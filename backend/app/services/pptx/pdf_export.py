"""Convert PPTX to PDF (and render thumbnails) using headless LibreOffice."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from app.logging import get_logger

logger = get_logger(__name__)


def _soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def libreoffice_available() -> bool:
    return _soffice() is not None


def convert_to_pdf(pptx_path: str | Path, out_dir: str | Path, timeout: int = 120) -> Path | None:
    """Convert a PPTX to PDF, returning the PDF path (or None if unavailable)."""
    soffice = _soffice()
    if soffice is None:
        logger.warning("LibreOffice not available; skipping PDF export")
        return None

    pptx_path = Path(pptx_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Use an isolated user profile to avoid clashes with concurrent conversions.
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            soffice,
            "--headless",
            "--norestore",
            f"-env:UserInstallation=file://{profile}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(pptx_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            logger.error("LibreOffice conversion failed: %s", exc)
            return None

    pdf = out_dir / (pptx_path.stem + ".pdf")
    return pdf if pdf.exists() else None


def render_thumbnail(pptx_path: str | Path, out_png: str | Path, dpi: int = 90) -> Path | None:
    """Render the first slide of a PPTX to a PNG thumbnail (via PDF)."""
    out_png = Path(out_png)
    with tempfile.TemporaryDirectory() as tmp:
        pdf = convert_to_pdf(pptx_path, tmp)
        if pdf is None:
            return None
        try:
            import fitz

            doc = fitz.open(str(pdf))
            if not doc.page_count:
                return None
            pix = doc[0].get_pixmap(dpi=dpi)
            out_png.parent.mkdir(parents=True, exist_ok=True)
            pix.save(str(out_png))
            doc.close()
            return out_png
        except Exception as exc:  # pragma: no cover
            logger.debug("thumbnail render failed: %s", exc)
            return None
