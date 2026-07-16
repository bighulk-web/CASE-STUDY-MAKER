"""Structured search intent parsed from a natural-language prompt."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchIntent(BaseModel):
    query: str = Field("", description="Free-text semantic query distilled from the prompt.")
    industries: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    business_functions: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    year: int | None = None
    num_slides: int | None = None
    max_case_studies: int = 10
    sort_order: str = Field("relevance", description="relevance | recent | confidence")
    template_hint: str = Field("", description="Template category hinted by the prompt.")
    layout: str = Field("one_per_slide", description="one_per_slide | two_per_slide")
    include_executive_summary: bool = True
    include_contents: bool = True
    include_agenda: bool = True
    include_thank_you: bool = True
