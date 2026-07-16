"""Deterministic, dependency-free metadata extraction.

Used when no LLM provider is configured (the default offline path) and as a fallback
when a provider errors. It is intentionally conservative and assigns a low confidence
score so downstream ranking can prefer LLM-derived metadata when available.
"""

from __future__ import annotations

import re
from collections import Counter

from app.schemas.metadata import CaseStudyMetadata

from .dictionaries import (
    BUSINESS_FUNCTIONS,
    INDUSTRIES,
    REGIONS,
    STOPWORDS,
    TECHNOLOGIES,
)

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+/\-]{2,}")


def _match_dict(text_lower: str, mapping: dict[str, list[str]]) -> list[str]:
    found: list[str] = []
    for label, triggers in mapping.items():
        if any(trigger in text_lower for trigger in triggers):
            found.append(label)
    return found


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.split(text.strip()) if s.strip()]


def _title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:200]
    return "Untitled Case Study"


def _customer(text: str, title: str) -> str:
    # Company often appears as a capitalized phrase before an action verb.
    m = re.search(
        r"\b([A-Z][A-Za-z&.\- ]{2,40}?)\s+(?:modernized|deployed|implemented|adopted|"
        r"migrated|transformed|automated|selected|partnered|reduced|improved)\b",
        text,
    )
    if m:
        return m.group(1).strip()
    # Fallback: leading capitalized words of the title.
    words = title.replace("Case Study", "").strip().split()
    lead = []
    for w in words:
        if w[:1].isupper():
            lead.append(w)
        else:
            break
    return " ".join(lead[:4]).strip()


def _keywords(text: str, limit: int = 12) -> list[str]:
    counts: Counter[str] = Counter()
    for w in _WORD_RE.findall(text.lower()):
        if w in STOPWORDS or len(w) < 4:
            continue
        counts[w] += 1
    return [w for w, _ in counts.most_common(limit)]


def _benefits(sentences: list[str]) -> list[str]:
    out = []
    for s in sentences:
        if re.search(r"\d+\s?%|\breduc|\bincreas|\bsaving|\bfaster|\bimprov|\broi\b", s, re.I):
            out.append(s)
    return out[:6]


def _year(text: str) -> int | None:
    years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", text)]
    return max(years) if years else None


def _duration(text: str) -> str:
    m = re.search(r"\b(\d+)\s*(months?|weeks?|years?)\b", text, re.I)
    return f"{m.group(1)} {m.group(2)}" if m else ""


def heuristic_metadata(text: str) -> CaseStudyMetadata:
    text = text or ""
    low = f" {text.lower()} "
    sentences = _sentences(text)
    title = _title(text)

    industries = _match_dict(low, INDUSTRIES)
    technologies = _match_dict(low, TECHNOLOGIES)
    regions = _match_dict(low, REGIONS)
    functions = _match_dict(low, BUSINESS_FUNCTIONS)
    benefits = _benefits(sentences)
    keywords = _keywords(text)

    one_liner = sentences[0] if sentences else ""
    exec_summary = " ".join(sentences[:3])

    challenge = next(
        (s for s in sentences if re.search(r"challenge|problem|struggl|fragment|pain", s, re.I)),
        "",
    )
    solution = next(
        (s for s in sentences if re.search(r"solution|deployed|implemented|delivered|built", s, re.I)),
        "",
    )
    outcome = next(
        (s for s in sentences if re.search(r"outcome|result|achiev|roi|reduction|increase", s, re.I)),
        "",
    )

    tags = sorted(set(industries + technologies))[:10]

    return CaseStudyMetadata(
        title=title,
        customer=_customer(text, title),
        industry=industries[0] if industries else "",
        sector=industries[0] if industries else "",
        sub_sector="",
        technology=technologies,
        products_used=technologies,
        business_challenge=challenge,
        solution=solution,
        key_features=[],
        benefits=benefits,
        business_outcome=outcome,
        implementation_duration=_duration(text),
        region=regions[0] if regions else "",
        keywords=keywords,
        tags=tags,
        confidence_score=0.35 if text.strip() else 0.0,
        one_line_summary=one_liner,
        executive_summary=exec_summary,
        suitable_for=[],
        use_cases=[],
        business_functions=functions,
    )


def heuristic_year(text: str) -> int | None:
    return _year(text)
