"""API DTOs for documents and folders."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class FolderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    parent_id: int | None = None


class FolderCreate(BaseModel):
    name: str
    parent_id: int | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_filename: str
    doc_type: str
    sha256: str
    size_bytes: int
    title: str
    folder_id: int | None
    status: str
    error_message: str | None
    is_duplicate_of: int | None
    uploaded_at: dt.datetime
    updated_at: dt.datetime


class DocumentUpdate(BaseModel):
    title: str | None = None
    folder_id: int | None = None


class DocumentVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version_no: int
    sha256: str
    note: str
    created_at: dt.datetime


class DocumentListOut(BaseModel):
    items: list[DocumentOut]
    total: int
