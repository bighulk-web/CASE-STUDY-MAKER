"""Document library API: upload, list, update, delete, versions, preview, download."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Document, DocumentVersion
from app.schemas.documents import (
    DocumentListOut,
    DocumentOut,
    DocumentUpdate,
    DocumentVersionOut,
)
from app.services.extraction.base import detect_doc_type
from app.services.ingestion.documents import (
    add_version,
    create_document,
    delete_document,
    move_document,
    rename_document,
)
from app.services.ingestion.preview import preview_image_path, preview_text

router = APIRouter(prefix="/documents", tags=["documents"])


def _enqueue_or_process(document_id: int) -> None:
    """Kick off processing via the job worker if available, else run inline."""
    try:
        from app.services.jobs.queue import enqueue

        enqueue("pipeline", document_id)
    except Exception:
        from app.services.pipeline import process_document

        process_document(document_id)


@router.post("", response_model=list[DocumentOut])
async def upload_documents(
    files: list[UploadFile] = File(...),
    folder_id: int | None = Form(default=None),
    session: Session = Depends(get_db),
) -> list[Document]:
    created: list[Document] = []
    for f in files:
        data = await f.read()
        try:
            detect_doc_type(f.filename or "")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        doc = create_document(
            session, filename=f.filename or "upload", data=data, folder_id=folder_id
        )
        created.append(doc)
    session.commit()
    for doc in created:
        _enqueue_or_process(doc.id)
    for doc in created:
        session.refresh(doc)
    return created


@router.get("", response_model=DocumentListOut)
def list_documents(
    folder_id: int | None = None,
    doc_type: str | None = None,
    status: str | None = None,
    q: str | None = None,
    include_duplicates: bool = True,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db),
) -> DocumentListOut:
    stmt = select(Document)
    count_stmt = select(func.count(Document.id))
    conditions = []
    if folder_id is not None:
        conditions.append(Document.folder_id == folder_id)
    if doc_type:
        conditions.append(Document.doc_type == doc_type)
    if status:
        conditions.append(Document.status == status)
    if q:
        conditions.append(Document.title.ilike(f"%{q}%"))
    if not include_duplicates:
        conditions.append(Document.is_duplicate_of.is_(None))
    for c in conditions:
        stmt = stmt.where(c)
        count_stmt = count_stmt.where(c)
    total = session.scalar(count_stmt) or 0
    items = list(
        session.scalars(stmt.order_by(Document.uploaded_at.desc()).limit(limit).offset(offset))
    )
    return DocumentListOut(items=[DocumentOut.model_validate(i) for i in items], total=total)


def _get_or_404(session: Session, document_id: int) -> Document:
    doc = session.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, session: Session = Depends(get_db)) -> Document:
    return _get_or_404(session, document_id)


@router.patch("/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: int, body: DocumentUpdate, session: Session = Depends(get_db)
) -> Document:
    doc = _get_or_404(session, document_id)
    if body.title is not None:
        rename_document(session, doc, body.title)
    if body.folder_id is not None or "folder_id" in body.model_fields_set:
        move_document(session, doc, body.folder_id)
    session.commit()
    session.refresh(doc)
    return doc


@router.delete("/{document_id}")
def remove_document(document_id: int, session: Session = Depends(get_db)) -> dict[str, bool]:
    doc = _get_or_404(session, document_id)
    delete_document(session, doc)
    session.commit()
    return {"deleted": True}


@router.get("/{document_id}/versions", response_model=list[DocumentVersionOut])
def list_versions(document_id: int, session: Session = Depends(get_db)) -> list[DocumentVersion]:
    _get_or_404(session, document_id)
    return list(
        session.scalars(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_no.desc())
        )
    )


@router.post("/{document_id}/versions", response_model=DocumentOut)
async def upload_version(
    document_id: int,
    file: UploadFile = File(...),
    note: str = Form(default=""),
    session: Session = Depends(get_db),
) -> Document:
    doc = _get_or_404(session, document_id)
    data = await file.read()
    add_version(session, doc, filename=file.filename or "upload", data=data, note=note)
    session.commit()
    _enqueue_or_process(doc.id)
    session.refresh(doc)
    return doc


@router.get("/{document_id}/preview")
def get_preview(document_id: int, session: Session = Depends(get_db)):
    doc = _get_or_404(session, document_id)
    img = preview_image_path(doc)
    if img is not None:
        return FileResponse(str(img))
    return PlainTextResponse(preview_text(doc) or "(no preview available)")


@router.get("/{document_id}/file")
def download_file(document_id: int, session: Session = Depends(get_db)) -> FileResponse:
    doc = _get_or_404(session, document_id)
    return FileResponse(doc.stored_path, filename=doc.original_filename)
