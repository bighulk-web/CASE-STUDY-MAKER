"""Index a CaseStudy into the vector store for semantic search."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import CaseStudy
from app.logging import get_logger
from app.services.embeddings.factory import get_embedding_provider
from app.services.vectorstore.factory import get_vector_store

logger = get_logger(__name__)


def embedding_text(cs: CaseStudy) -> str:
    """Build the text representation embedded for semantic search."""
    parts = [
        cs.title,
        cs.customer,
        cs.industry,
        cs.sector,
        " ".join(cs.technology or []),
        " ".join(cs.products_used or []),
        cs.one_line_summary,
        cs.executive_summary,
        cs.business_challenge,
        cs.solution,
        cs.business_outcome,
        " ".join(cs.benefits or []),
        " ".join(cs.keywords or []),
        " ".join(cs.business_functions or []),
        cs.region,
    ]
    return "\n".join(p for p in parts if p)


def _metadata(cs: CaseStudy) -> dict[str, object]:
    return {
        "case_study_id": cs.id,
        "document_id": cs.document_id,
        "industry": cs.industry,
        "region": cs.region,
        "customer": cs.customer,
        "year": cs.year or 0,
    }


def index_case_study(session: Session, cs: CaseStudy) -> None:
    provider = get_embedding_provider()
    store = get_vector_store()
    text = embedding_text(cs)
    vec = provider.embed([text])[0]
    store.upsert(
        ids=[str(cs.id)],
        embeddings=[vec],
        metadatas=[_metadata(cs)],
        documents=[text],
    )
    cs.embedding_id = str(cs.id)
    cs.indexed = True
    session.flush()
    logger.info("Indexed case study %s (embedding dim=%d)", cs.id, len(vec))


def remove_from_index(cs_id: int) -> None:
    store = get_vector_store()
    store.delete([str(cs_id)])
