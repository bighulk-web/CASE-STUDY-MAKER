"""Rebuild the vector index and FTS for all case studies (incremental or full)."""

from __future__ import annotations

from sqlalchemy import select

from app.db.base import session_scope
from app.db.models import CaseStudy
from app.logging import get_logger

from .indexer import index_case_study

logger = get_logger(__name__)


def reindex_all(progress=None, *, only_missing: bool = False) -> int:
    """Re-embed and re-index case studies. Returns the number indexed."""
    with session_scope() as session:
        stmt = select(CaseStudy)
        if only_missing:
            stmt = stmt.where(CaseStudy.indexed == False)  # noqa: E712
        ids = [cs.id for cs in session.scalars(stmt)]

    total = len(ids)
    for i, cs_id in enumerate(ids):
        with session_scope() as session:
            cs = session.get(CaseStudy, cs_id)
            if cs is not None:
                index_case_study(session, cs)
                from app.services.metadata.analyze import sync_fts

                sync_fts(session, cs)
        if progress is not None and total:
            progress(int((i + 1) / total * 100), f"Indexed {i + 1}/{total}")
    logger.info("Reindexed %d case studies", total)
    return total


def convert_intent_to_request(intent, max_results: int | None = None):
    """Map a SearchIntent into a SearchRequest for the engine."""
    from app.schemas.search import SearchRequest

    return SearchRequest(
        query=intent.query,
        industries=intent.industries,
        technologies=intent.technologies,
        products=intent.products,
        business_functions=intent.business_functions,
        regions=intent.regions,
        keywords=intent.keywords,
        year=intent.year,
        sort_order=intent.sort_order,
        max_results=max_results or intent.max_case_studies or 20,
    )
