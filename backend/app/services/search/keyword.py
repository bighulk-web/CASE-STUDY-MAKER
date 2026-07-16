"""Keyword search over the FTS5 index."""

from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _fts_query(query: str) -> str:
    """Build a safe FTS5 MATCH expression: OR of prefix-matched tokens."""
    tokens = [t for t in _TOKEN_RE.findall(query.lower()) if len(t) >= 2]
    if not tokens:
        return ""
    # Prefix match each token; OR them so partial matches still rank.
    return " OR ".join(f"{t}*" for t in tokens)


def keyword_ranked_ids(session: Session, query: str, limit: int = 100) -> list[int]:
    """Return case_study_ids ordered by FTS relevance (best first)."""
    match = _fts_query(query)
    if not match:
        return []
    rows = session.execute(
        text(
            "SELECT case_study_id FROM case_studies_fts "
            "WHERE case_studies_fts MATCH :q ORDER BY rank LIMIT :lim"
        ),
        {"q": match, "lim": limit},
    ).fetchall()
    return [int(r[0]) for r in rows]
