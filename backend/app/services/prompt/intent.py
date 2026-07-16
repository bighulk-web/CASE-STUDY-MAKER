"""Parse a user's natural-language prompt into a structured SearchIntent.

Uses the configured LLM when available; otherwise a deterministic heuristic based on
the same keyword dictionaries used for metadata extraction, so it works offline.
"""

from __future__ import annotations

import re

from app.logging import get_logger
from app.schemas.intent import SearchIntent
from app.services.llm.factory import get_llm_provider
from app.services.metadata.dictionaries import (
    BUSINESS_FUNCTIONS,
    INDUSTRIES,
    REGIONS,
    STOPWORDS,
    TECHNOLOGIES,
)

logger = get_logger(__name__)

_SYSTEM = (
    "You convert a user's request for a sales/proposal presentation into a structured "
    "search intent. Extract industries, sectors, technologies, products, business "
    "functions, keywords, regions, target year, number of slides, maximum case studies, "
    "sort order (relevance|recent|confidence), a template hint, layout "
    "(one_per_slide|two_per_slide), and whether to include executive summary, contents, "
    "agenda, and thank-you slides. Use empty values when unknown."
)


def _match(prompt_low: str, mapping: dict[str, list[str]]) -> list[str]:
    return [
        label
        for label, triggers in mapping.items()
        if any(trig in prompt_low for trig in triggers)
    ]


def heuristic_intent(prompt: str) -> SearchIntent:
    low = f" {prompt.lower()} "

    industries = _match(low, INDUSTRIES)
    technologies = _match(low, TECHNOLOGIES)
    regions = _match(low, REGIONS)
    functions = _match(low, BUSINESS_FUNCTIONS)

    num_slides = None
    m = re.search(r"(\d+)\s*slides?", low)
    if m:
        num_slides = int(m.group(1))

    max_cases = 10
    m = re.search(r"top\s+(\d+)", low)
    if m:
        max_cases = int(m.group(1))
    else:
        m = re.search(r"(\d+)\s*(?:case studies|cases|projects|examples)", low)
        if m:
            max_cases = int(m.group(1))

    sort_order = "relevance"
    if re.search(r"recent|latest|newest", low):
        sort_order = "recent"

    layout = "two_per_slide" if re.search(r"two per slide|2 per slide", low) else "one_per_slide"

    year = None
    ym = re.search(r"\b(20\d{2})\b", low)
    if ym:
        year = int(ym.group(1))

    template_hint = industries[0] if industries else ""

    # Keywords: salient tokens not already captured and not stopwords.
    captured = " ".join(industries + technologies + regions + functions).lower()
    keywords = []
    for tok in re.findall(r"[a-z][a-z0-9+/\-]{2,}", low):
        if tok in STOPWORDS or tok in captured or tok in {"create", "presentation", "deck", "show", "showing", "make"}:
            continue
        if tok not in keywords:
            keywords.append(tok)

    return SearchIntent(
        query=prompt.strip(),
        industries=industries,
        technologies=technologies,
        products=technologies,
        business_functions=functions,
        keywords=keywords[:12],
        regions=regions,
        year=year,
        num_slides=num_slides,
        max_case_studies=max_cases,
        sort_order=sort_order,
        template_hint=template_hint,
        layout=layout,
    )


def parse_intent(prompt: str) -> SearchIntent:
    provider = get_llm_provider()
    if provider.available():
        try:
            data = provider.structured(_SYSTEM, f"Request: {prompt}", SearchIntent.model_json_schema())
            intent = SearchIntent.model_validate(data)
            if not intent.query:
                intent.query = prompt.strip()
            return intent
        except Exception as exc:
            logger.warning("LLM intent parse failed (%s); using heuristics", exc)
    return heuristic_intent(prompt)
