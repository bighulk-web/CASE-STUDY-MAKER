"""Analyze a document's extracted text into structured CaseStudy metadata."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CaseStudy, Document, Extraction, Tag
from app.logging import get_logger
from app.schemas.metadata import CaseStudyMetadata
from app.services.llm.factory import get_llm_provider

from .heuristic import heuristic_metadata, heuristic_year

logger = get_logger(__name__)

_SYSTEM = (
    "You are an expert consulting analyst. Extract structured metadata about a single "
    "customer case study from the provided document text. Be accurate and concise. "
    "If a field is unknown, use an empty string or empty list. Lists must be arrays of "
    "short strings."
)

# Cap the amount of text sent to the LLM to control cost/latency.
_MAX_CHARS = 12000


def extract_metadata(text: str) -> CaseStudyMetadata:
    """Return metadata using the configured LLM, falling back to heuristics."""
    provider = get_llm_provider()
    if provider.available():
        try:
            data = provider.structured(
                _SYSTEM,
                f"Document text:\n\n{text[:_MAX_CHARS]}",
                CaseStudyMetadata.llm_json_schema(),
            )
            meta = CaseStudyMetadata.model_validate(data)
            if not meta.confidence_score:
                meta.confidence_score = 0.9
            return meta
        except Exception as exc:
            logger.warning("LLM metadata extraction failed (%s); using heuristics", exc)
    return heuristic_metadata(text)


def _sync_tags(session: Session, case_study: CaseStudy, tag_names: list[str]) -> None:
    case_study.tags.clear()
    for name in {t.strip() for t in tag_names if t.strip()}:
        tag = session.scalars(select(Tag).where(Tag.name == name)).first()
        if tag is None:
            tag = Tag(name=name)
            session.add(tag)
            session.flush()
        case_study.tags.append(tag)


def _apply(meta: CaseStudyMetadata, cs: CaseStudy, model_used: str, text: str) -> None:
    cs.title = meta.title
    cs.customer = meta.customer
    cs.industry = meta.industry
    cs.sector = meta.sector
    cs.sub_sector = meta.sub_sector
    cs.technology = meta.technology
    cs.products_used = meta.products_used
    cs.business_challenge = meta.business_challenge
    cs.solution = meta.solution
    cs.key_features = meta.key_features
    cs.benefits = meta.benefits
    cs.business_outcome = meta.business_outcome
    cs.implementation_duration = meta.implementation_duration
    cs.region = meta.region
    cs.keywords = meta.keywords
    cs.tags_json = meta.tags
    cs.confidence_score = meta.confidence_score
    cs.one_line_summary = meta.one_line_summary
    cs.executive_summary = meta.executive_summary
    cs.suitable_for = meta.suitable_for
    cs.use_cases = meta.use_cases
    cs.business_functions = meta.business_functions
    cs.year = heuristic_year(text)
    cs.model_used = model_used
    cs.indexed = False


def analyze_document(session: Session, document: Document) -> CaseStudy:
    """Create/refresh the CaseStudy row for ``document`` and sync FTS."""
    extraction = session.scalars(
        select(Extraction).where(Extraction.document_id == document.id)
    ).first()
    text = extraction.raw_text if extraction else ""

    provider = get_llm_provider()
    meta = extract_metadata(text)
    model_used = provider.model if provider.available() else "heuristic"

    cs = session.scalars(
        select(CaseStudy).where(CaseStudy.document_id == document.id)
    ).first()
    if cs is None:
        cs = CaseStudy(document_id=document.id)
        session.add(cs)
        session.flush()

    _apply(meta, cs, model_used, text)
    _sync_tags(session, cs, meta.tags + meta.keywords)
    session.flush()

    sync_fts(session, cs)
    logger.info(
        "Analyzed document %s -> case study %s (%s, conf=%.2f)",
        document.id,
        cs.id,
        model_used,
        cs.confidence_score,
    )
    return cs


def sync_fts(session: Session, cs: CaseStudy) -> None:
    """Upsert the FTS row mirroring searchable fields."""
    from sqlalchemy import text as sql

    session.execute(
        sql("DELETE FROM case_studies_fts WHERE case_study_id = :id"), {"id": cs.id}
    )
    session.execute(
        sql(
            """INSERT INTO case_studies_fts
            (case_study_id, title, customer, one_line_summary, executive_summary,
             business_challenge, solution, benefits, keywords, tags, technology,
             products_used, industry)
            VALUES (:id, :title, :customer, :ols, :es, :bc, :sol, :ben, :kw, :tags,
                    :tech, :prod, :ind)"""
        ),
        {
            "id": cs.id,
            "title": cs.title,
            "customer": cs.customer,
            "ols": cs.one_line_summary,
            "es": cs.executive_summary,
            "bc": cs.business_challenge,
            "sol": cs.solution,
            "ben": " ".join(cs.benefits or []),
            "kw": " ".join(cs.keywords or []),
            "tags": " ".join(cs.tags_json or []),
            "tech": " ".join(cs.technology or []),
            "prod": " ".join(cs.products_used or []),
            "ind": cs.industry,
        },
    )
