from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    ref_id: int | None
    status: str
    progress: int
    message: str
    error: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
