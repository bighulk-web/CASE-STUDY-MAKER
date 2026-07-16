"""Assemble a presentation by populating a template per selected case study.

The uploaded template is treated as a *single-case-study block* (one or more slides
containing ``{{tokens}}``). For each selected case study the block is duplicated and
its placeholders are filled. Formatting is preserved because we never rebuild slides —
we only rewrite run text and swap special (image/table) placeholder shapes in place.

Optional auto-generated slides (title, agenda, executive summary, thank-you) are added
using the template's own layouts so the theme/fonts stay consistent.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path

from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.presentation import Presentation as PresentationT
from pptx.util import Emu, Pt

from app.logging import get_logger

from .placeholder_engine import (
    find_special_placeholders,
    insert_picture,
    insert_table,
    replace_text_placeholders,
)

logger = get_logger(__name__)

_REL_ATTRS = (qn("r:embed"), qn("r:link"), qn("r:pict"), qn("r:id"))


@dataclass
class SlotData:
    """Data for one case study slot within a block."""

    value_map: dict[str, str]
    image_path: str | None = None
    tables: dict[str, list[list[str]]] = field(default_factory=dict)


@dataclass
class DeckOptions:
    layout: str = "one_per_slide"  # one_per_slide | two_per_slide
    include_title: bool = True
    include_agenda: bool = True
    include_executive_summary: bool = False
    include_thank_you: bool = True
    deck_title: str = "Case Study Deck"
    deck_subtitle: str = ""


# --------------------------------------------------------------------------
# Low-level slide manipulation
# --------------------------------------------------------------------------


def _clone_relationships(source_slide, new_slide, spTree) -> None:
    """Re-point relationship ids (images/links) on cloned shapes to copied parts."""
    for el in spTree.iter():
        for attr in _REL_ATTRS:
            rId = el.get(attr)
            if not rId:
                continue
            rels = source_slide.part.rels
            if rId not in rels:
                continue
            rel = rels[rId]
            if rel.is_external:
                new_rId = new_slide.part.relate_to(rel.target_ref, rel.reltype, is_external=True)
            else:
                new_rId = new_slide.part.relate_to(rel.target_part, rel.reltype)
            el.set(attr, new_rId)


def duplicate_slide(prs: PresentationT, index: int):
    """Deep-copy the slide at ``index`` (shapes + image relationships)."""
    source = prs.slides[index]
    new_slide = prs.slides.add_slide(source.slide_layout)

    # Remove placeholders the layout injected so we start from a clean tree.
    for shp in list(new_slide.shapes):
        shp._element.getparent().remove(shp._element)

    for shp in source.shapes:
        new_slide.shapes._spTree.append(copy.deepcopy(shp._element))

    _clone_relationships(source, new_slide, new_slide.shapes._spTree)
    return new_slide


def _move_slide(prs: PresentationT, old_index: int, new_index: int) -> None:
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    el = ids[old_index]
    sldIdLst.remove(el)
    sldIdLst.insert(new_index, el)


# --------------------------------------------------------------------------
# Filling
# --------------------------------------------------------------------------


def _fill_slide(slide, slots: list[SlotData]) -> None:
    # Special (image/table/chart) placeholders first: insert or remove the shape.
    for ph in find_special_placeholders(slide):
        sd = slots[ph.slot - 1] if 0 <= ph.slot - 1 < len(slots) else None
        if ph.kind in ("image", "logo", "icon"):
            if sd and sd.image_path and Path(sd.image_path).exists():
                insert_picture(slide, ph, sd.image_path)
            else:
                _remove(ph.shape)
        elif ph.kind == "table":
            rows = sd.tables.get(ph.arg or "Benefits") if sd else None
            if rows:
                insert_table(slide, ph, rows)
            else:
                _remove(ph.shape)
        else:  # chart (best-effort: drop placeholder for now)
            _remove(ph.shape)

    # Text placeholders (slot-prefixed + unprefixed for slot 1).
    mapping: dict[str, str] = {}
    for idx, sd in enumerate(slots, start=1):
        for k, v in sd.value_map.items():
            mapping[f"{idx}.{k}"] = v
            if idx == 1:
                mapping.setdefault(k, v)
    replace_text_placeholders(slide.shapes, mapping)


def _remove(shape) -> None:
    el = shape._element
    el.getparent().remove(el)


# --------------------------------------------------------------------------
# Generated meta slides
# --------------------------------------------------------------------------


def _blank_layout(prs: PresentationT):
    """Pick a simple layout (prefer Title Only / Blank) for generated slides."""
    layouts = prs.slide_layouts
    for i in (5, 6):
        if i < len(layouts):
            return layouts[i]
    return layouts[0]


def _add_text_slide(prs: PresentationT, title: str, body_lines: list[str]):
    slide = prs.slides.add_slide(_blank_layout(prs))
    width = prs.slide_width or Emu(9144000)
    # Title textbox.
    tb = slide.shapes.add_textbox(Emu(457200), Emu(457200), width - Emu(914400), Emu(1000000))
    p = tb.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = title
    run.font.size = Pt(32)
    run.font.bold = True
    if body_lines:
        body = slide.shapes.add_textbox(
            Emu(457200), Emu(1600000), width - Emu(914400), (prs.slide_height or Emu(6858000)) - Emu(2200000)
        )
        tf = body.text_frame
        tf.word_wrap = True
        for i, line in enumerate(body_lines):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            r = para.add_run()
            r.text = line
            r.font.size = Pt(18)
    return slide


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------


def assemble_deck(
    template_path: str | Path,
    out_path: str | Path,
    blocks: list[list[SlotData]],
    options: DeckOptions,
    *,
    case_titles: list[str] | None = None,
) -> Path:
    """Build the deck and save it to ``out_path``."""
    prs = Presentation(str(template_path))
    original_count = len(prs.slides._sldIdLst)
    if original_count == 0:
        raise ValueError("Template has no slides")

    original_indices = list(range(original_count))

    # 1) Duplicate the block once per extra case-study block (from pristine originals).
    block_slide_sets: list[list[int]] = [original_indices]
    for _ in range(1, len(blocks)):
        new_indices = []
        for i in original_indices:
            duplicate_slide(prs, i)
            new_indices.append(len(prs.slides._sldIdLst) - 1)
        block_slide_sets.append(new_indices)

    # 2) Fill each block's slides.
    for slide_indices, slots in zip(block_slide_sets, blocks, strict=False):
        for si in slide_indices:
            _fill_slide(prs.slides[si], slots)

    # 3) Generated meta slides.
    front = 0
    if options.include_title:
        _add_text_slide(prs, options.deck_title, [options.deck_subtitle] if options.deck_subtitle else [])
        _move_slide(prs, len(prs.slides._sldIdLst) - 1, front)
        front += 1
    if options.include_agenda:
        titles = case_titles or []
        _add_text_slide(prs, "Agenda", [f"{i + 1}. {t}" for i, t in enumerate(titles)])
        _move_slide(prs, len(prs.slides._sldIdLst) - 1, front)
        front += 1
    if options.include_executive_summary:
        summary_lines = []
        for block in blocks:
            for sd in block:
                s = sd.value_map.get("Summary") or sd.value_map.get("OneLineSummary")
                if s:
                    summary_lines.append(f"• {s}")
        _add_text_slide(prs, "Executive Summary", summary_lines)
        _move_slide(prs, len(prs.slides._sldIdLst) - 1, front)
        front += 1
    if options.include_thank_you:
        _add_text_slide(prs, "Thank You", [])

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    logger.info("Assembled deck with %d slides -> %s", len(prs.slides._sldIdLst), out_path)
    return out_path
