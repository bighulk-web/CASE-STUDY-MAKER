"""Document lifecycle operations: create, list, rename, move, delete, versions."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentVersion, Folder
from app.logging import get_logger
from app.services.extraction.base import detect_doc_type

from .storage import store_bytes

logger = get_logger(__name__)


def create_document(
    session: Session,
    *,
    filename: str,
    data: bytes,
    folder_id: int | None = None,
    title: str | None = None,
) -> Document:
    """Store an uploaded file and create a Document (+ initial version).

    Duplicate detection: if an existing document has the same sha256, the new
    document is flagged via ``is_duplicate_of``.
    """
    doc_type = detect_doc_type(filename)
    digest, path = store_bytes(data, doc_type)

    existing = session.scalars(
        select(Document).where(Document.sha256 == digest).order_by(Document.id)
    ).first()

    doc = Document(
        original_filename=filename,
        stored_path=str(path),
        doc_type=doc_type,
        sha256=digest,
        size_bytes=len(data),
        title=title or Path(filename).stem,
        folder_id=folder_id,
        status="uploaded",
        is_duplicate_of=existing.id if existing else None,
    )
    session.add(doc)
    session.flush()

    version = DocumentVersion(
        document_id=doc.id,
        version_no=1,
        stored_path=str(path),
        sha256=digest,
        note="initial upload",
    )
    session.add(version)
    session.flush()
    logger.info("Created document %s (%s) dup=%s", doc.id, filename, doc.is_duplicate_of)
    return doc


def add_version(
    session: Session, document: Document, *, filename: str, data: bytes, note: str = ""
) -> DocumentVersion:
    """Attach a new version to an existing document and make it current."""
    doc_type = detect_doc_type(filename)
    digest, path = store_bytes(data, doc_type)

    last = session.scalars(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document.id)
        .order_by(DocumentVersion.version_no.desc())
    ).first()
    next_no = (last.version_no + 1) if last else 1

    version = DocumentVersion(
        document_id=document.id,
        version_no=next_no,
        stored_path=str(path),
        sha256=digest,
        note=note or f"version {next_no}",
    )
    session.add(version)

    document.stored_path = str(path)
    document.sha256 = digest
    document.size_bytes = len(data)
    document.doc_type = doc_type
    document.status = "uploaded"
    session.flush()
    return version


def rename_document(session: Session, document: Document, title: str) -> Document:
    document.title = title
    session.flush()
    return document


def move_document(session: Session, document: Document, folder_id: int | None) -> Document:
    document.folder_id = folder_id
    session.flush()
    return document


def delete_document(session: Session, document: Document) -> None:
    """Delete a document. Stored file is removed only if unreferenced."""
    sha = document.sha256
    stored = document.stored_path
    session.delete(document)
    session.flush()

    others = session.scalars(select(Document).where(Document.sha256 == sha)).first()
    if others is None:
        try:
            p = Path(stored)
            if p.exists():
                p.unlink()
        except OSError:
            logger.warning("Could not remove stored file %s", stored)


# ---- Folders -----------------------------------------------------------


def create_folder(session: Session, name: str, parent_id: int | None = None) -> Folder:
    folder = Folder(name=name, parent_id=parent_id)
    session.add(folder)
    session.flush()
    return folder
