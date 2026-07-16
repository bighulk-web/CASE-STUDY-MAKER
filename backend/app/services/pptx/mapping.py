"""Map a CaseStudy to template placeholder values (with common aliases)."""

from __future__ import annotations

from app.db.models import CaseStudy


def _join(items: list[str] | None, sep: str = ", ") -> str:
    return sep.join(i for i in (items or []) if i)


def _bullets(items: list[str] | None) -> str:
    return "\n".join(f"• {i}" for i in (items or []) if i)


def build_value_map(cs: CaseStudy) -> dict[str, str]:
    """Return a case-insensitive-friendly mapping of placeholder name -> value.

    Multiple aliases point at the same data so a variety of template conventions
    ({{Client}} vs {{Customer}}, {{Challenge}} vs {{BusinessChallenge}}) all work.
    """
    m: dict[str, str] = {
        "Title": cs.title,
        "Customer": cs.customer,
        "Client": cs.customer,
        "Company": cs.customer,
        "Industry": cs.industry,
        "Sector": cs.sector,
        "SubSector": cs.sub_sector,
        "Technology": _join(cs.technology),
        "Technologies": _join(cs.technology),
        "Products": _join(cs.products_used),
        "ProductsUsed": _join(cs.products_used),
        "Challenge": cs.business_challenge,
        "BusinessChallenge": cs.business_challenge,
        "Solution": cs.solution,
        "KeyFeatures": _bullets(cs.key_features),
        "Features": _bullets(cs.key_features),
        "Benefits": _bullets(cs.benefits),
        "Outcome": cs.business_outcome,
        "BusinessOutcome": cs.business_outcome,
        "Duration": cs.implementation_duration,
        "ImplementationDuration": cs.implementation_duration,
        "Region": cs.region,
        "Keywords": _join(cs.keywords),
        "Tags": _join(cs.tags_json),
        "Summary": cs.one_line_summary,
        "OneLineSummary": cs.one_line_summary,
        "ExecutiveSummary": cs.executive_summary,
        "UseCases": _bullets(cs.use_cases),
        "BusinessFunctions": _join(cs.business_functions),
        "SuitableFor": _join(cs.suitable_for),
        "Confidence": f"{cs.confidence_score:.0%}",
        "Year": str(cs.year or ""),
    }
    return m
