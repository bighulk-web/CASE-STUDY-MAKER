"""Search API: structured search, natural-language intent search, and facets."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.search import (
    Facets,
    IntentRequest,
    SearchRequest,
    SearchResponse,
)
from app.services.prompt.intent import parse_intent
from app.services.search.engine import search as run_search
from app.services.search.metadata_filter import compute_facets
from app.services.search.reindex import convert_intent_to_request

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_endpoint(req: SearchRequest, session: Session = Depends(get_db)) -> SearchResponse:
    items = run_search(session, req)
    return SearchResponse(items=items, total=len(items))


@router.post("/intent", response_model=SearchResponse)
def intent_search(body: IntentRequest, session: Session = Depends(get_db)) -> SearchResponse:
    intent = parse_intent(body.prompt)
    req = convert_intent_to_request(intent)
    items = run_search(session, req)
    return SearchResponse(items=items, total=len(items), intent=intent)


@router.post("/parse", response_model=dict)
def parse_only(body: IntentRequest) -> dict:
    """Parse a prompt into a SearchIntent without running the search."""
    return {"intent": parse_intent(body.prompt).model_dump()}


@router.get("/facets", response_model=Facets)
def facets(session: Session = Depends(get_db)) -> Facets:
    return compute_facets(session)
