"""Template CRUD: store uploaded PPTX, discover placeholders, thumbnails."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Template
from app.logging import get_logger
from app.services.ingestion.storage import sha256_bytes

from .discovery import discover_placeholders

logger = get_logger(__name__)


def create_template(
    session: Session, *, name: str, data: bytes, category: str = "custom"
) -> Template:
    settings = get_settings()
    digest = sha256_bytes(data)
    path = settings.templates_dir / f"{digest}.pptx"
    if not path.exists():
        path.write_bytes(data)

    placeholders, slide_count = discover_placeholders(path)

    template = Template(
        name=name,
        category=category,
        stored_path=str(path),
        placeholders=placeholders,
        slide_count=slide_count,
    )
    session.add(template)
    session.flush()

    # Best-effort thumbnail (requires LibreOffice).
    try:
        from app.services.pptx.pdf_export import render_thumbnail

        thumb = settings.previews_dir / f"template_{template.id}.png"
        if render_thumbnail(path, thumb) is not None:
            template.thumbnail_path = str(thumb)
            session.flush()
    except Exception as exc:  # pragma: no cover
        logger.debug("template thumbnail failed: %s", exc)

    logger.info("Created template %s (%d placeholders)", template.id, len(placeholders))
    return template


def delete_template(session: Session, template: Template) -> None:
    stored = template.stored_path
    session.delete(template)
    session.flush()
    # Remove stored file if unreferenced.
    from sqlalchemy import select

    still = session.scalars(select(Template).where(Template.stored_path == stored)).first()
    if still is None:
        try:
            Path(stored).unlink(missing_ok=True)
        except OSError:
            pass
