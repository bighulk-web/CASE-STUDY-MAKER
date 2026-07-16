"""End-to-end per-document processing pipeline.

Phase 1 runs extraction only. Later phases extend this to also run LLM metadata
analysis and vector indexing. The function is written so it can be called either
synchronously (tests / simple flows) or from the background job worker.
"""

from __future__ import annotations

from app.db.base import session_scope
from app.db.models import Document
from app.logging import get_logger
from app.services.extraction.persist import run_extraction

logger = get_logger(__name__)

ProgressFn = "callable"


def process_document(document_id: int, progress=None) -> None:
    """Extract (and later analyze + index) a single document.

    ``progress`` is an optional callable ``(pct: int, message: str) -> None`` used
    by the job worker to stream updates.
    """

    def _p(pct: int, msg: str) -> None:
        if progress is not None:
            progress(pct, msg)

    with session_scope() as session:
        document = session.get(Document, document_id)
        if document is None:
            logger.warning("process_document: document %s not found", document_id)
            return
        try:
            _p(10, "Extracting content")
            run_extraction(session, document)

            # Phase 2 hook: metadata analysis + indexing.
            analyzed = _maybe_analyze_and_index(session, document, _p)

            document.status = "ready" if analyzed else "ready"
            _p(100, "Ready")
        except Exception as exc:
            logger.exception("Pipeline failed for document %s", document_id)
            document.status = "error"
            document.error_message = str(exc)
            _p(100, f"Error: {exc}")
            raise


def _maybe_analyze_and_index(session, document: Document, progress) -> bool:
    """Run metadata analysis + indexing if those subsystems are available.

    Returns True if analysis ran. Implemented in Phase 2; returns False here so the
    pipeline still completes with extraction only.
    """
    try:
        from app.services.metadata.analyze import analyze_document
        from app.services.search.indexer import index_case_study
    except Exception:
        return False

    progress(50, "Analyzing with AI")
    document.status = "analyzing"
    session.flush()
    case_study = analyze_document(session, document)

    progress(80, "Indexing for search")
    document.status = "indexing"
    session.flush()
    index_case_study(session, case_study)
    return True
