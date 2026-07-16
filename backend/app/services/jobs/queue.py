"""Background job execution.

Jobs run on a bounded ThreadPoolExecutor so CPU/IO-bound work (extraction, embedding)
never blocks the event loop. Progress is written to the ``jobs`` table and broadcast
to WebSocket clients. In ``sync_jobs`` mode (tests) jobs run inline for determinism.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.config import get_settings
from app.db.base import session_scope
from app.db.models import Job
from app.logging import get_logger

from .broadcaster import broadcaster

logger = get_logger(__name__)

_executor: ThreadPoolExecutor | None = None


async def start_worker() -> None:
    global _executor
    loop = asyncio.get_running_loop()
    broadcaster.bind_loop(loop)
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=get_settings().job_concurrency, thread_name_prefix="csm-job"
        )


async def stop_worker() -> None:
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False)
        _executor = None


def _update_job(job_id: int, **fields: object) -> None:
    with session_scope() as session:
        job = session.get(Job, job_id)
        if job is None:
            return
        for k, v in fields.items():
            setattr(job, k, v)


def _make_progress(job_id: int, ref_id: int | None, job_type: str):
    def progress(pct: int, message: str) -> None:
        _update_job(job_id, status="running", progress=pct, message=message)
        broadcaster.publish(
            {
                "job_id": job_id,
                "type": job_type,
                "ref_id": ref_id,
                "status": "running",
                "progress": pct,
                "message": message,
            }
        )

    return progress


def _dispatch(job_type: str, ref_id: int | None, progress) -> None:
    if job_type in ("pipeline", "extract", "analyze"):
        from app.services.pipeline import process_document

        if ref_id is not None:
            process_document(ref_id, progress=progress)
    elif job_type == "build":
        from app.services.pptx.build import run_build_job

        if ref_id is not None:
            run_build_job(ref_id, progress=progress)
    elif job_type == "reindex":
        from app.services.search.reindex import reindex_all

        reindex_all(progress=progress)
    else:
        raise ValueError(f"Unknown job type: {job_type}")


def _run_job(job_id: int, job_type: str, ref_id: int | None) -> None:
    progress = _make_progress(job_id, ref_id, job_type)
    _update_job(job_id, status="running", progress=1, message="Started")
    try:
        _dispatch(job_type, ref_id, progress)
        _update_job(job_id, status="done", progress=100, message="Completed")
        broadcaster.publish(
            {"job_id": job_id, "type": job_type, "ref_id": ref_id, "status": "done", "progress": 100}
        )
    except Exception as exc:
        logger.exception("Job %s (%s) failed", job_id, job_type)
        _update_job(job_id, status="error", message=str(exc), error=str(exc))
        broadcaster.publish(
            {"job_id": job_id, "type": job_type, "ref_id": ref_id, "status": "error", "message": str(exc)}
        )


def enqueue(job_type: str, ref_id: int | None = None) -> int:
    """Create a Job and run it (inline in sync mode, else on the thread pool)."""
    with session_scope() as session:
        job = Job(type=job_type, ref_id=ref_id, status="pending", message="Queued")
        session.add(job)
        session.flush()
        job_id = job.id

    if get_settings().sync_jobs or _executor is None:
        _run_job(job_id, job_type, ref_id)
    else:
        _executor.submit(_run_job, job_id, job_type, ref_id)
    return job_id
