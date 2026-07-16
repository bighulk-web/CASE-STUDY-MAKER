"""Template management API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Template
from app.schemas.templates import TemplateOut, TemplateUpdate
from app.services.template.manager import create_template, delete_template

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=TemplateOut)
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(default=""),
    category: str = Form(default="custom"),
    session: Session = Depends(get_db),
) -> Template:
    if not (file.filename or "").lower().endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Template must be a .pptx file")
    data = await file.read()
    template = create_template(
        session, name=name or (file.filename or "Template"), data=data, category=category
    )
    session.commit()
    session.refresh(template)
    return template


@router.get("", response_model=list[TemplateOut])
def list_templates(session: Session = Depends(get_db)) -> list[Template]:
    return list(session.scalars(select(Template).order_by(Template.created_at.desc())))


def _get_or_404(session: Session, template_id: int) -> Template:
    t = session.get(Template, template_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, session: Session = Depends(get_db)) -> Template:
    return _get_or_404(session, template_id)


@router.patch("/{template_id}", response_model=TemplateOut)
def update_template(
    template_id: int, body: TemplateUpdate, session: Session = Depends(get_db)
) -> Template:
    t = _get_or_404(session, template_id)
    if body.name is not None:
        t.name = body.name
    if body.category is not None:
        t.category = body.category
    session.commit()
    session.refresh(t)
    return t


@router.delete("/{template_id}")
def remove_template(template_id: int, session: Session = Depends(get_db)) -> dict[str, bool]:
    t = _get_or_404(session, template_id)
    delete_template(session, t)
    session.commit()
    return {"deleted": True}


@router.get("/{template_id}/thumbnail")
def template_thumbnail(template_id: int, session: Session = Depends(get_db)):
    t = _get_or_404(session, template_id)
    if t.thumbnail_path:
        return FileResponse(t.thumbnail_path)
    raise HTTPException(status_code=404, detail="No thumbnail available")
