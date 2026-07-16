"""Job status API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Job
from app.schemas.jobs import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(
    status: str | None = None,
    limit: int = 50,
    session: Session = Depends(get_db),
) -> list[Job]:
    stmt = select(Job).order_by(Job.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Job.status == status)
    return list(session.scalars(stmt))


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, session: Session = Depends(get_db)) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
