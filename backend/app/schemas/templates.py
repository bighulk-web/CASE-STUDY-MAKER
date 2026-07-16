from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category: str
    placeholders: list[dict[str, Any]]
    slide_count: int
    thumbnail_path: str | None
    created_at: dt.datetime


class TemplateUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
