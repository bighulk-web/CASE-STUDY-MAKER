"""End-to-end per-document processing pipeline.

Runs extraction, then (when available) LLM metadata analysis and vector indexing.

Each stage uses its own short-lived transaction and progress is reported *between*
stages. This avoids holding a long SQLite write transaction while progress updates
(which write to the ``jobs`` table on another connection) run, preventing lock
contention.
"""

from __future__ import annotations

from app.db.base import session_scope
from app.db.models import Document
from app.logging import get_logger
from app.services.extraction.persist import run_extraction

logger = get_logger(__name__)


def _set_status(document_id: int, status: str, error: str | None = None) -> None:
    with session_scope() as session:
        doc = session.get(Document, document_id)
        if doc is not None:
            doc.status = status
            doc.error_message = error


def process_document(document_id: int, progress=None) -> None:
    """Extract, analyze, and index a single document."""

    def _p(pct: int, msg: str) -> None:
        if progress is not None:
            progress(pct, msg)

    try:
        _p(10, "Extracting content")
        _set_status(document_id, "extracting")
        with session_scope() as session:
            document = session.get(Document, document_id)
            if document is None:
                logger.warning("process_document: document %s not found", document_id)
                return
            run_extraction(session, document)

        _maybe_analyze_and_index(document_id, _p)

        _set_status(document_id, "ready")
        _p(100, "Ready")
    except Exception as exc:
        logger.exception("Pipeline failed for document %s", document_id)
        _set_status(document_id, "error", str(exc))
        _p(100, f"Error: {exc}")
        raise


def _maybe_analyze_and_index(document_id: int, progress) -> bool:
    """Run metadata analysis + indexing if those subsystems import successfully."""
    try:
        from app.services.metadata.analyze import analyze_document
        from app.services.search.indexer import index_case_study
    except Exception:
        return False

    progress(50, "Analyzing with AI")
    _set_status(document_id, "analyzing")
    with session_scope() as session:
        document = session.get(Document, document_id)
        if document is None:
            return False
        case_study = analyze_document(session, document)
        case_study_id = case_study.id

    progress(80, "Indexing for search")
    _set_status(document_id, "indexing")
    with session_scope() as session:
        from app.db.models import CaseStudy

        cs = session.get(CaseStudy, case_study_id)
        if cs is not None:
            index_case_study(session, cs)
    return True
