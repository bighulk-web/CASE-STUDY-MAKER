"""Helpers that programmatically generate small sample documents for tests.

Keeping fixtures generated (rather than committing binaries) keeps the repo small
and makes the expected content explicit.
"""

from __future__ import annotations

import io
from pathlib import Path

SAMPLE_TEXT = (
    "Acme Manufacturing modernized its ERP with SAP S/4HANA. "
    "The challenge was fragmented supply chain data across EMEA. "
    "The solution delivered a 30% reduction in inventory costs over 6 months."
)


def _png_bytes(color: tuple[int, int, int] = (200, 100, 50)) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (64, 48), color).save(buf, format="PNG")
    return buf.getvalue()


def make_txt(path: Path, text: str = SAMPLE_TEXT) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def make_docx(path: Path, text: str = SAMPLE_TEXT) -> Path:
    import docx

    doc = docx.Document()
    doc.add_heading("Acme Manufacturing Case Study", level=1)
    doc.add_paragraph(text)
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Metric"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Inventory reduction"
    table.cell(1, 1).text = "30%"
    doc.save(str(path))
    return path


def make_pptx(path: Path, text: str = SAMPLE_TEXT) -> Path:
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Acme Manufacturing Case Study"
    slide.placeholders[1].text = text

    # A slide with a table + image.
    slide2 = prs.slides.add_slide(prs.slide_layouts[5])
    rows, cols = 2, 2
    tbl = slide2.shapes.add_table(
        rows, cols, Inches(1), Inches(1), Inches(4), Inches(1.2)
    ).table
    tbl.cell(0, 0).text = "Benefit"
    tbl.cell(0, 1).text = "Impact"
    tbl.cell(1, 0).text = "Cost savings"
    tbl.cell(1, 1).text = "30%"

    img_path = path.parent / "_tmp_img.png"
    img_path.write_bytes(_png_bytes())
    slide2.shapes.add_picture(str(img_path), Inches(6), Inches(1), Inches(2), Inches(1.5))

    prs.save(str(path))
    img_path.unlink(missing_ok=True)
    return path


def make_pdf(path: Path, text: str = SAMPLE_TEXT) -> Path:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 720, "Acme Manufacturing Case Study")
    c.setFont("Helvetica", 11)
    y = 690
    for line in _wrap(text, 80):
        c.drawString(72, y, line)
        y -= 16
    c.showPage()
    c.save()
    return path


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines
