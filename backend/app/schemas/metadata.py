"""Pydantic schema for the 23 structured case-study metadata fields.

Field descriptions double as the instruction set for LLM structured extraction:
:func:`CaseStudyMetadata.llm_json_schema` produces a JSON schema handed to the
provider so the model returns exactly these fields.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CaseStudyMetadata(BaseModel):
    title: str = Field("", description="Concise, descriptive title of the case study.")
    customer: str = Field("", description="Name of the client/customer organization.")
    industry: str = Field("", description="Primary industry, e.g. Manufacturing, Healthcare, BFSI.")
    sector: str = Field("", description="Broad sector within the industry.")
    sub_sector: str = Field("", description="More specific sub-sector.")
    technology: list[str] = Field(
        default_factory=list, description="Technologies/platforms used (e.g. SAP S/4HANA, Azure)."
    )
    products_used: list[str] = Field(
        default_factory=list, description="Specific products/tools deployed."
    )
    business_challenge: str = Field("", description="The core business problem addressed.")
    solution: str = Field("", description="How the challenge was solved.")
    key_features: list[str] = Field(default_factory=list, description="Notable solution features.")
    benefits: list[str] = Field(default_factory=list, description="Concrete benefits delivered.")
    business_outcome: str = Field("", description="Measurable business outcome / ROI.")
    implementation_duration: str = Field("", description="Duration, e.g. '6 months'.")
    region: str = Field("", description="Geographic region, e.g. EMEA, North America, APAC.")
    keywords: list[str] = Field(default_factory=list, description="Salient search keywords.")
    tags: list[str] = Field(default_factory=list, description="Short categorical tags.")
    confidence_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Extractor confidence in this metadata (0-1)."
    )
    one_line_summary: str = Field("", description="A single sentence summary.")
    executive_summary: str = Field("", description="A short executive summary paragraph.")
    suitable_for: list[str] = Field(
        default_factory=list, description="Audiences/contexts this case suits."
    )
    use_cases: list[str] = Field(default_factory=list, description="Applicable use cases.")
    business_functions: list[str] = Field(
        default_factory=list, description="Business functions involved (e.g. Finance, Supply Chain)."
    )

    @staticmethod
    def llm_json_schema() -> dict[str, Any]:
        """Return a provider-friendly JSON schema for structured extraction."""
        schema = CaseStudyMetadata.model_json_schema()
        schema["additionalProperties"] = False
        return schema
