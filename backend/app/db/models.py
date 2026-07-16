"""SQLAlchemy ORM models.

List-valued metadata fields (technology, products, keywords, etc.) are stored as
JSON text columns for simplicity; normalized tags live in ``tags`` /
``case_study_tags`` to support fast tag filtering and faceting.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("folders.id", ondelete="SET NULL"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    documents: Mapped[list[Document]] = relationship(back_populates="folder")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(512))
    stored_path: Mapped[str] = mapped_column(String(1024))
    doc_type: Mapped[str] = mapped_column(String(16))  # pptx|docx|pdf|txt
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(512), default="")
    folder_id: Mapped[int | None] = mapped_column(ForeignKey("folders.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(24), default="uploaded")
    # uploaded|extracting|analyzing|indexing|ready|error
    error_message: Mapped[str | None] = mapped_column(Text)
    is_duplicate_of: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL")
    )
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    folder: Mapped[Folder | None] = relationship(back_populates="documents")
    versions: Mapped[list[DocumentVersion]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    extraction: Mapped[Extraction | None] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )
    case_study: Mapped[CaseStudy | None] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    version_no: Mapped[int] = mapped_column(Integer)
    stored_path: Mapped[str] = mapped_column(String(1024))
    sha256: Mapped[str] = mapped_column(String(64))
    note: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    document: Mapped[Document] = relationship(back_populates="versions")


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    raw_text: Mapped[str] = mapped_column(Text, default="")
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    has_ocr: Mapped[bool] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    document: Mapped[Document] = relationship(back_populates="extraction")
    assets: Mapped[list[ExtractionAsset]] = relationship(
        back_populates="extraction", cascade="all, delete-orphan"
    )


class ExtractionAsset(Base):
    __tablename__ = "extraction_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    extraction_id: Mapped[int] = mapped_column(ForeignKey("extractions.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))  # image|table|chart
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    stored_path: Mapped[str | None] = mapped_column(String(1024))
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    caption: Mapped[str] = mapped_column(String(1024), default="")

    extraction: Mapped[Extraction] = relationship(back_populates="assets")


case_study_tags = Table(
    "case_study_tags",
    Base.metadata,
    Column("case_study_id", ForeignKey("case_studies.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    case_studies: Mapped[list[CaseStudy]] = relationship(
        secondary=case_study_tags, back_populates="tags"
    )


class CaseStudy(Base):
    __tablename__ = "case_studies"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))

    # --- The 23 structured metadata fields ---
    title: Mapped[str] = mapped_column(String(512), default="")
    customer: Mapped[str] = mapped_column(String(255), default="")
    industry: Mapped[str] = mapped_column(String(128), default="")
    sector: Mapped[str] = mapped_column(String(128), default="")
    sub_sector: Mapped[str] = mapped_column(String(128), default="")
    technology: Mapped[list[str]] = mapped_column(JSON, default=list)
    products_used: Mapped[list[str]] = mapped_column(JSON, default=list)
    business_challenge: Mapped[str] = mapped_column(Text, default="")
    solution: Mapped[str] = mapped_column(Text, default="")
    key_features: Mapped[list[str]] = mapped_column(JSON, default=list)
    benefits: Mapped[list[str]] = mapped_column(JSON, default=list)
    business_outcome: Mapped[str] = mapped_column(Text, default="")
    implementation_duration: Mapped[str] = mapped_column(String(128), default="")
    region: Mapped[str] = mapped_column(String(128), default="")
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    one_line_summary: Mapped[str] = mapped_column(Text, default="")
    executive_summary: Mapped[str] = mapped_column(Text, default="")
    suitable_for: Mapped[list[str]] = mapped_column(JSON, default=list)
    use_cases: Mapped[list[str]] = mapped_column(JSON, default=list)
    business_functions: Mapped[list[str]] = mapped_column(JSON, default=list)

    # bookkeeping
    year: Mapped[int | None] = mapped_column(Integer)
    model_used: Mapped[str] = mapped_column(String(64), default="")
    embedding_id: Mapped[str | None] = mapped_column(String(64))
    indexed: Mapped[bool] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    document: Mapped[Document] = relationship(back_populates="case_study")
    tags: Mapped[list[Tag]] = relationship(secondary=case_study_tags, back_populates="case_studies")


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(64), default="custom")
    stored_path: Mapped[str] = mapped_column(String(1024))
    placeholders: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    slide_count: Mapped[int] = mapped_column(Integer, default=0)
    thumbnail_path: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)


class Presentation(Base):
    __tablename__ = "presentations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    prompt: Mapped[str] = mapped_column(Text, default="")
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL")
    )
    intent: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    selected_case_study_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    options: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_pptx_path: Mapped[str | None] = mapped_column(String(1024))
    output_pdf_path: Mapped[str | None] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(24), default="draft")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(24))  # extract|analyze|index|build|pipeline
    ref_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    # pending|running|done|error
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(String(512), default="")
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class Setting(Base):
    __tablename__ = "settings"
    __table_args__ = (UniqueConstraint("key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(Text, default="")
