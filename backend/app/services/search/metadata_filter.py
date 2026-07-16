"""SQL + in-memory metadata filtering and facet computation."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CaseStudy
from app.schemas.search import Facets, SearchRequest


def _ci_in(value: str, options: list[str]) -> bool:
    v = value.strip().lower()
    return any(v == o.strip().lower() for o in options)


def _list_overlap(values: list[str], options: list[str]) -> bool:
    low = {v.strip().lower() for v in (values or [])}
    return any(o.strip().lower() in low for o in options)


def filter_candidates(session: Session, req: SearchRequest) -> list[CaseStudy]:
    """Return case studies passing all hard metadata filters.

    Scalar fields (industry, region, customer, year) are filtered in SQL; list-valued
    fields (technology, products, business functions, tags) are filtered in Python.
    """
    stmt = select(CaseStudy)
    if req.year is not None:
        stmt = stmt.where(CaseStudy.year == req.year)
    if req.customer:
        stmt = stmt.where(CaseStudy.customer.ilike(f"%{req.customer}%"))

    candidates = list(session.scalars(stmt))

    def keep(cs: CaseStudy) -> bool:
        if req.industries and not _ci_in(cs.industry, req.industries):
            return False
        if req.regions and not _ci_in(cs.region, req.regions):
            return False
        if req.technologies and not _list_overlap(cs.technology or [], req.technologies):
            return False
        if req.products and not _list_overlap(cs.products_used or [], req.products):
            return False
        if req.business_functions and not _list_overlap(
            cs.business_functions or [], req.business_functions
        ):
            return False
        if req.tags and not _list_overlap(
            (cs.tags_json or []) + (cs.keywords or []), req.tags
        ):
            return False
        return True

    return [cs for cs in candidates if keep(cs)]


def compute_facets(session: Session) -> Facets:
    industries: set[str] = set()
    regions: set[str] = set()
    customers: set[str] = set()
    technologies: set[str] = set()
    products: set[str] = set()
    functions: set[str] = set()
    tags: set[str] = set()
    years: set[int] = set()

    for cs in session.scalars(select(CaseStudy)):
        if cs.industry:
            industries.add(cs.industry)
        if cs.region:
            regions.add(cs.region)
        if cs.customer:
            customers.add(cs.customer)
        if cs.year:
            years.add(cs.year)
        technologies.update(cs.technology or [])
        products.update(cs.products_used or [])
        functions.update(cs.business_functions or [])
        tags.update(cs.tags_json or [])

    return Facets(
        industries=sorted(industries),
        technologies=sorted(technologies),
        regions=sorted(regions),
        customers=sorted(customers),
        products=sorted(products),
        business_functions=sorted(functions),
        years=sorted(years, reverse=True),
        tags=sorted(tags),
    )


def total_case_studies(session: Session) -> int:
    return session.scalar(select(func.count(CaseStudy.id))) or 0
