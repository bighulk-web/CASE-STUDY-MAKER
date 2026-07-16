"""Placeholder replacement that preserves template formatting.

Design notes
------------
PowerPoint splits a logical string into multiple *runs*, each with its own character
formatting, and it does so unpredictably. A token like ``{{Title}}`` may therefore be
spread across several runs. Naively rewriting ``shape.text`` collapses all runs and
destroys formatting.

The text algorithm here works at the *paragraph* level:
  1. Concatenate run texts and record each run's character span.
  2. Locate ``{{token}}`` matches in the concatenated text.
  3. For each match, blank the token's characters in every run they touch and write
     the replacement into the run where the token *starts* — inheriting that run's
     font (name, size, bold/italic, color). All other characters keep their original
     run (and thus their formatting) untouched.

Image/logo/table placeholders are whole-shape tokens: the placeholder shape's geometry
is captured, the shape is removed, and the replacement (picture or table) is inserted
into the identical bounding box, so positions never move.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

TOKEN_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
# Special whole-shape tokens: kind + optional argument, e.g. {{Image}}, {{Table:Benefits}}
SPECIAL_KINDS = {"image", "logo", "icon", "table", "chart"}
# Optional slot prefix for multi-case-study-per-slide layouts, e.g. {{2.Title}}.
_SLOT_RE = re.compile(r"^(\d+)\.(.*)$")


def split_slot(token: str) -> tuple[int, str]:
    """Split an optional ``N.`` slot prefix. Returns (slot, rest); default slot=1."""
    m = _SLOT_RE.match(token.strip())
    if m:
        return int(m.group(1)), m.group(2).strip()
    return 1, token.strip()


def token_kind(token: str) -> str:
    """Classify a token as a special kind (image/logo/…) or 'text'."""
    _, rest = split_slot(token)
    base = rest.split(":", 1)[0].strip().lower()
    return base if base in SPECIAL_KINDS else "text"


def _iter_text_frames(shapes):
    """Yield every text frame in a shape tree (recursing into groups)."""
    for shape in shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _iter_text_frames(shape.shapes)
            continue
        if shape.has_text_frame:
            yield shape.text_frame
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    yield cell.text_frame


def replace_text_in_paragraph(paragraph, resolve) -> None:
    """Replace ``{{tokens}}`` in one paragraph, preserving run formatting.

    ``resolve(key) -> str | None``. Returning ``None`` leaves the token untouched
    (useful for special/whole-shape tokens handled elsewhere).
    """
    runs = paragraph.runs
    if not runs:
        return
    texts = [r.text for r in runs]
    full = "".join(texts)
    if "{{" not in full:
        return

    bounds: list[tuple[int, int]] = []
    pos = 0
    for t in texts:
        bounds.append((pos, pos + len(t)))
        pos += len(t)

    matches = list(TOKEN_RE.finditer(full))
    if not matches:
        return

    run_chars: list[list[str]] = [list(t) for t in texts]

    for m in matches:
        key = m.group(1).strip()
        replacement = resolve(key)
        if replacement is None:
            continue
        s, e = m.start(), m.end()
        anchor: int | None = None
        anchor_offset = 0
        for i, (bs, be) in enumerate(bounds):
            lo, hi = max(s, bs), min(e, be)
            for c in range(lo, hi):
                run_chars[i][c - bs] = ""
            if bs <= s < be:
                anchor = i
                anchor_offset = s - bs
        if anchor is not None:
            run_chars[anchor][anchor_offset] = replacement

    for i, r in enumerate(runs):
        new_text = "".join(run_chars[i])
        if new_text != r.text:
            r.text = new_text


def replace_text_placeholders(shapes, mapping: dict[str, str]) -> None:
    """Replace textual placeholders across all text frames in ``shapes``.

    Keys are matched case-insensitively. Special whole-shape tokens (Image/Table/…)
    are intentionally left for :func:`find_special_placeholders`.
    """
    lower_map = {k.lower(): v for k, v in mapping.items()}

    def resolve(key: str) -> str | None:
        if token_kind(key) != "text":
            return None  # whole-shape special tokens are handled elsewhere
        if key.lower() in lower_map:
            return lower_map[key.lower()]
        base = key.split(":", 1)[0].strip().lower()
        if base in lower_map:
            return lower_map[base]
        # Unknown text token -> blank it so no raw {{X}} ships in the output.
        return ""

    for tf in _iter_text_frames(shapes):
        for paragraph in tf.paragraphs:
            replace_text_in_paragraph(paragraph, resolve)


@dataclass
class SpecialPlaceholder:
    shape: object
    kind: str  # image | logo | icon | table | chart
    arg: str
    slot: int
    left: int
    top: int
    width: int
    height: int


def find_special_placeholders(slide) -> list[SpecialPlaceholder]:
    """Find whole-shape tokens like ``{{Image}}`` / ``{{2.Table:Benefits}}``."""
    found: list[SpecialPlaceholder] = []
    for shape in list(slide.shapes):
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text.strip()
        m = TOKEN_RE.fullmatch(text)
        if not m:
            continue
        slot, rest = split_slot(m.group(1).strip())
        kind = rest.split(":", 1)[0].strip().lower()
        arg = rest.split(":", 1)[1].strip() if ":" in rest else ""
        if kind in SPECIAL_KINDS:
            found.append(
                SpecialPlaceholder(
                    shape=shape,
                    kind=kind,
                    arg=arg,
                    slot=slot,
                    left=shape.left or 0,
                    top=shape.top or 0,
                    width=shape.width or Emu(0),
                    height=shape.height or Emu(0),
                )
            )
    return found


def insert_picture(slide, ph: SpecialPlaceholder, image_path: str) -> None:
    """Replace a special placeholder with a picture fit into its box."""
    from PIL import Image

    left, top, box_w, box_h = ph.left, ph.top, ph.width, ph.height
    try:
        with Image.open(image_path) as im:
            iw, ih = im.size
    except Exception:
        iw, ih = 4, 3

    # Fit (contain) the image within the placeholder box, preserving aspect ratio.
    if box_w and box_h and iw and ih:
        scale = min(box_w / iw, box_h / ih)
        w = int(iw * scale)
        h = int(ih * scale)
        left = ph.left + (box_w - w) // 2
        top = ph.top + (box_h - h) // 2
        slide.shapes.add_picture(image_path, left, top, width=w, height=h)
    else:
        slide.shapes.add_picture(image_path, left, top)

    _remove_shape(ph.shape)


def insert_table(slide, ph: SpecialPlaceholder, rows: list[list[str]]) -> None:
    if not rows:
        _remove_shape(ph.shape)
        return
    n_rows = len(rows)
    n_cols = max(len(r) for r in rows)
    graphic = slide.shapes.add_table(
        n_rows, n_cols, ph.left, ph.top, ph.width or Emu(3000000), ph.height or Emu(1500000)
    )
    table = graphic.table
    for i, row in enumerate(rows):
        for j in range(n_cols):
            table.cell(i, j).text = row[j] if j < len(row) else ""
    _remove_shape(ph.shape)


def _remove_shape(shape) -> None:
    el = shape._element
    el.getparent().remove(el)
