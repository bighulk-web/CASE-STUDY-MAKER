"""Run extraction for a stored document and persist results to the DB."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, Extraction, ExtractionAsset
from app.logging import get_logger
from app.services.ingestion.storage import save_asset

from .base import extract

logger = get_logger(__name__)


def run_extraction(session: Session, document: Document) -> Extraction:
    """Extract content from ``document`` and persist an Extraction (+ assets).

    Any previous extraction for the document is replaced so re-runs are idempotent.
    """
    document.status = "extracting"
    document.error_message = None
    session.flush()

    prev = session.scalars(
        select(Extraction).where(Extraction.document_id == document.id)
    ).first()
    if prev is not None:
        session.delete(prev)
        session.flush()

    result = extract(document.stored_path, document.doc_type)

    extraction = Extraction(
        document_id=document.id,
        raw_text=result.combined_text(),
        page_count=result.page_count,
        has_ocr=1 if result.has_ocr else 0,
    )
    session.add(extraction)
    session.flush()

    ordinal = 0
    for img in result.images:
        try:
            path = save_asset(img.data, img.ext, subdir=f"doc_{document.id}")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed saving image asset: %s", exc)
            continue
        session.add(
            ExtractionAsset(
                extraction_id=extraction.id,
                kind="image",
                ordinal=ordinal,
                stored_path=str(path),
                caption=img.caption,
            )
        )
        ordinal += 1

    for i, tbl in enumerate(result.tables):
        session.add(
            ExtractionAsset(
                extraction_id=extraction.id,
                kind="table",
                ordinal=i,
                payload={"rows": tbl.rows, "caption": tbl.caption},
            )
        )

    for i, chart in enumerate(result.charts):
        session.add(
            ExtractionAsset(
                extraction_id=extraction.id,
                kind="chart",
                ordinal=i,
                payload={
                    "title": chart.title,
                    "categories": chart.categories,
                    "series": chart.series,
                },
            )
        )

    session.flush()
    logger.info(
        "Extracted document %s: %d chars, %d images, %d tables, %d charts",
        document.id,
        len(result.text),
        len(result.images),
        len(result.tables),
        len(result.charts),
    )
    return extraction
