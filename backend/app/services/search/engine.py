"""Hybrid search engine.

Combines four signals and fuses them with Reciprocal Rank Fusion (RRF):
  1. Semantic similarity (vector store),
  2. Keyword relevance (FTS5),
  3. Metadata filters (hard filters that constrain the candidate set),
  4. Tag / keyword overlap (a boost).

RRF is robust to score-scale differences across rankers: an item at rank ``r`` in a
list contributes ``weight / (K + r)`` to its fused score.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.logging import get_logger
from app.schemas.search import SearchRequest, SearchResultItem
from app.services.embeddings.factory import get_embedding_provider
from app.services.vectorstore.factory import get_vector_store

from .keyword import keyword_ranked_ids
from .metadata_filter import filter_candidates

logger = get_logger(__name__)

RRF_K = 60
W_SEMANTIC = 1.0
W_KEYWORD = 0.8
W_TAG = 0.5


def _semantic_ranked_ids(query: str, limit: int = 100) -> list[int]:
    if not query.strip():
        return []
    provider = get_embedding_provider()
    store = get_vector_store()
    vec = provider.embed([query])[0]
    hits = store.query(vec, n=limit)
    ids: list[int] = []
    for h in hits:
        cid = h.metadata.get("case_study_id")
        ids.append(int(cid) if cid is not None else int(h.id))
    return ids


def _rrf(ids: list[int], weight: float, scores: dict[int, float]) -> None:
    for rank, cid in enumerate(ids):
        scores[cid] += weight / (RRF_K + rank + 1)


def _overlap_terms(req: SearchRequest) -> set[str]:
    terms = req.keywords + req.tags + req.technologies + req.products
    return {t.strip().lower() for t in terms if t.strip()}


def search(session: Session, req: SearchRequest) -> list[SearchResultItem]:
    candidates = filter_candidates(session, req)
    candidate_ids = {cs.id for cs in candidates}
    by_id = {cs.id: cs for cs in candidates}
    if not candidate_ids:
        return []

    semantic_ids = [i for i in _semantic_ranked_ids(req.query) if i in candidate_ids]
    keyword_ids = [i for i in keyword_ranked_ids(session, req.query) if i in candidate_ids]

    scores: dict[int, float] = defaultdict(float)
    _rrf(semantic_ids, W_SEMANTIC, scores)
    _rrf(keyword_ids, W_KEYWORD, scores)

    signals: dict[int, set[str]] = defaultdict(set)
    for cid in semantic_ids:
        signals[cid].add("semantic")
    for cid in keyword_ids:
        signals[cid].add("keyword")

    overlap = _overlap_terms(req)
    if overlap:
        for cs in candidates:
            cs_terms = {
                t.strip().lower()
                for t in (cs.technology or [])
                + (cs.products_used or [])
                + (cs.tags_json or [])
                + (cs.keywords or [])
            }
            n = len(overlap & cs_terms)
            if n:
                scores[cs.id] += W_TAG * n
                signals[cs.id].add("tag")

    # Items with no signal still rank (filter-only browse) via a small base score.
    for cs in candidates:
        scores.setdefault(cs.id, 0.0)

    def sort_key(cid: int) -> tuple[float, float, float]:
        cs = by_id[cid]
        created = cs.created_at.timestamp() if cs.created_at else 0.0
        if req.sort_order == "recent":
            return (created, scores[cid], cs.confidence_score)
        if req.sort_order == "confidence":
            return (cs.confidence_score, scores[cid], created)
        return (scores[cid], cs.confidence_score, created)

    ranked = sorted(candidate_ids, key=sort_key, reverse=True)[: req.max_results]

    results: list[SearchResultItem] = []
    # Normalize scores to 0..1 for display.
    max_score = max((scores[c] for c in ranked), default=0.0) or 1.0
    for cid in ranked:
        cs = by_id[cid]
        results.append(
            SearchResultItem(
                case_study_id=cs.id,
                document_id=cs.document_id,
                title=cs.title,
                customer=cs.customer,
                industry=cs.industry,
                region=cs.region,
                technology=cs.technology or [],
                one_line_summary=cs.one_line_summary,
                confidence_score=cs.confidence_score,
                score=round(scores[cid] / max_score, 4),
                signals=sorted(signals.get(cid, set())) or ["filter"],
            )
        )
    return results
