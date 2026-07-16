"""Search request/response DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.intent import SearchIntent


class SearchRequest(BaseModel):
    query: str = ""
    industries: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    business_functions: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    customer: str = ""
    year: int | None = None
    sort_order: str = "relevance"  # relevance | recent | confidence
    max_results: int = 20


class SearchResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    case_study_id: int
    document_id: int
    title: str
    customer: str
    industry: str
    region: str
    technology: list[str]
    one_line_summary: str
    confidence_score: float
    score: float
    signals: list[str]


class SearchResponse(BaseModel):
    items: list[SearchResultItem]
    total: int
    intent: SearchIntent | None = None


class IntentRequest(BaseModel):
    prompt: str


class Facets(BaseModel):
    industries: list[str]
    technologies: list[str]
    regions: list[str]
    customers: list[str]
    products: list[str]
    business_functions: list[str]
    years: list[int]
    tags: list[str]
