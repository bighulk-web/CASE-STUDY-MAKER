from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BuildOptions(BaseModel):
    layout: str = "one_per_slide"  # one_per_slide | two_per_slide
    include_title: bool = True
    include_agenda: bool = True
    include_executive_summary: bool = False
    include_thank_you: bool = True
    deck_subtitle: str = ""
    max_case_studies: int = 10


class BuildRequest(BaseModel):
    name: str = "Untitled Deck"
    template_id: int
    prompt: str = ""
    case_study_ids: list[int] = Field(default_factory=list)
    options: BuildOptions = Field(default_factory=BuildOptions)


class PresentationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    prompt: str
    template_id: int | None
    intent: dict[str, Any] | None
    selected_case_study_ids: list[int]
    options: dict[str, Any] | None
    output_pptx_path: str | None
    output_pdf_path: str | None
    status: str
    created_at: dt.datetime
