"""Orchestrate presentation building: select case studies, populate, export."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.base import session_scope
from app.db.models import CaseStudy, Extraction, ExtractionAsset, Presentation, Template
from app.logging import get_logger

from .deck_assembler import DeckOptions, SlotData, assemble_deck
from .mapping import build_value_map
from .pdf_export import convert_to_pdf

logger = get_logger(__name__)


def _first_image(session: Session, document_id: int) -> str | None:
    ext = session.scalars(
        select(Extraction).where(Extraction.document_id == document_id)
    ).first()
    if ext is None:
        return None
    asset = session.scalars(
        select(ExtractionAsset)
        .where(ExtractionAsset.extraction_id == ext.id, ExtractionAsset.kind == "image")
        .order_by(ExtractionAsset.ordinal)
    ).first()
    if asset and asset.stored_path and Path(asset.stored_path).exists():
        return asset.stored_path
    return None


def _slot_for(session: Session, cs: CaseStudy) -> SlotData:
    value_map = build_value_map(cs)
    tables = {}
    if cs.benefits:
        tables["Benefits"] = [["Benefit"]] + [[b] for b in cs.benefits]
    if cs.key_features:
        tables["Features"] = [["Key Feature"]] + [[f] for f in cs.key_features]
    return SlotData(
        value_map=value_map,
        image_path=_first_image(session, cs.document_id),
        tables=tables,
    )


def _chunk(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def run_build_job(presentation_id: int, progress=None) -> None:
    def _p(pct: int, msg: str) -> None:
        if progress is not None:
            progress(pct, msg)

    settings = get_settings()
    _p(5, "Loading presentation")

    with session_scope() as session:
        pres = session.get(Presentation, presentation_id)
        if pres is None:
            raise ValueError(f"Presentation {presentation_id} not found")
        template = session.get(Template, pres.template_id) if pres.template_id else None
        if template is None:
            raise ValueError("Presentation has no valid template")
        template_path = template.stored_path

        options_data = pres.options or {}
        layout = options_data.get("layout", "one_per_slide")
        cs_ids = pres.selected_case_study_ids or []

        loaded = [session.get(CaseStudy, cid) for cid in cs_ids]
        case_studies: list[CaseStudy] = [cs for cs in loaded if cs is not None]
        if not case_studies:
            raise ValueError("No case studies selected for this presentation")

        _p(30, "Preparing content")
        slots = [_slot_for(session, cs) for cs in case_studies]
        titles = [cs.title for cs in case_studies]

        slot_size = 2 if layout == "two_per_slide" else 1
        blocks = _chunk(slots, slot_size)

        options = DeckOptions(
            layout=layout,
            include_title=options_data.get("include_title", True),
            include_agenda=options_data.get("include_agenda", True),
            include_executive_summary=options_data.get("include_executive_summary", False),
            include_thank_you=options_data.get("include_thank_you", True),
            deck_title=pres.name or "Case Study Deck",
            deck_subtitle=options_data.get("deck_subtitle", ""),
        )
        pres_name = pres.name

    _p(55, "Assembling slides")
    out_pptx = settings.presentations_dir / f"presentation_{presentation_id}.pptx"
    assemble_deck(template_path, out_pptx, blocks, options, case_titles=titles)

    _p(80, "Exporting PDF")
    pdf = convert_to_pdf(out_pptx, settings.presentations_dir)

    with session_scope() as session:
        pres = session.get(Presentation, presentation_id)
        if pres is not None:
            pres.output_pptx_path = str(out_pptx)
            pres.output_pdf_path = str(pdf) if pdf else None
            pres.status = "ready"
    _p(100, f"Ready: {pres_name}")
