"""Presentation builder API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Presentation, Template
from app.schemas.builder import BuildRequest, PresentationOut
from app.services.prompt.intent import parse_intent
from app.services.search.engine import search as run_search
from app.services.search.reindex import convert_intent_to_request

router = APIRouter(prefix="/presentations", tags=["builder"])


@router.post("", response_model=PresentationOut)
def create_presentation(body: BuildRequest, session: Session = Depends(get_db)) -> Presentation:
    template = session.get(Template, body.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    intent_data = None
    case_study_ids = list(body.case_study_ids)

    # If no explicit selection, derive it from the prompt via intent + search.
    if not case_study_ids and body.prompt:
        intent = parse_intent(body.prompt)
        intent_data = intent.model_dump()
        req = convert_intent_to_request(intent, max_results=body.options.max_case_studies)
        results = run_search(session, req)
        case_study_ids = [r.case_study_id for r in results]

    if not case_study_ids:
        raise HTTPException(
            status_code=400,
            detail="No case studies selected or matched by the prompt.",
        )
    case_study_ids = case_study_ids[: body.options.max_case_studies]

    pres = Presentation(
        name=body.name,
        prompt=body.prompt,
        template_id=body.template_id,
        intent=intent_data,
        selected_case_study_ids=case_study_ids,
        options=body.options.model_dump(),
        status="building",
    )
    session.add(pres)
    session.commit()

    try:
        from app.services.jobs.queue import enqueue

        enqueue("build", pres.id)
    except Exception:
        from app.services.pptx.build import run_build_job

        run_build_job(pres.id)

    session.refresh(pres)
    return pres


@router.get("", response_model=list[PresentationOut])
def list_presentations(session: Session = Depends(get_db)) -> list[Presentation]:
    return list(session.scalars(select(Presentation).order_by(Presentation.created_at.desc())))


def _get_or_404(session: Session, pres_id: int) -> Presentation:
    p = session.get(Presentation, pres_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return p


@router.get("/{pres_id}", response_model=PresentationOut)
def get_presentation(pres_id: int, session: Session = Depends(get_db)) -> Presentation:
    return _get_or_404(session, pres_id)


@router.get("/{pres_id}/download")
def download_pptx(pres_id: int, session: Session = Depends(get_db)) -> FileResponse:
    p = _get_or_404(session, pres_id)
    if not p.output_pptx_path:
        raise HTTPException(status_code=404, detail="Presentation not built yet")
    return FileResponse(
        p.output_pptx_path,
        filename=f"{p.name}.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@router.get("/{pres_id}/download.pdf")
def download_pdf(pres_id: int, session: Session = Depends(get_db)) -> FileResponse:
    p = _get_or_404(session, pres_id)
    if not p.output_pdf_path:
        raise HTTPException(status_code=404, detail="PDF not available")
    return FileResponse(p.output_pdf_path, filename=f"{p.name}.pdf", media_type="application/pdf")
