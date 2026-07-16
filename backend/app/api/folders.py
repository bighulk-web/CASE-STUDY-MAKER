"""Folder organization API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Document, Folder
from app.schemas.documents import FolderCreate, FolderOut

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("", response_model=list[FolderOut])
def list_folders(session: Session = Depends(get_db)) -> list[Folder]:
    return list(session.scalars(select(Folder).order_by(Folder.name)))


@router.post("", response_model=FolderOut)
def create_folder_ep(body: FolderCreate, session: Session = Depends(get_db)) -> Folder:
    folder = Folder(name=body.name, parent_id=body.parent_id)
    session.add(folder)
    session.commit()
    session.refresh(folder)
    return folder


@router.patch("/{folder_id}", response_model=FolderOut)
def rename_folder(folder_id: int, body: FolderCreate, session: Session = Depends(get_db)) -> Folder:
    folder = session.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    folder.name = body.name
    folder.parent_id = body.parent_id
    session.commit()
    session.refresh(folder)
    return folder


@router.delete("/{folder_id}")
def delete_folder(folder_id: int, session: Session = Depends(get_db)) -> dict[str, bool]:
    folder = session.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    # Detach documents (keep them, move to root).
    for doc in session.scalars(select(Document).where(Document.folder_id == folder_id)):
        doc.folder_id = None
    session.delete(folder)
    session.commit()
    return {"deleted": True}
