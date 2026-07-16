"""LLM provider protocol and shared helpers."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    model: str

    def available(self) -> bool:
        """Whether this provider can actually be called (SDK + key present)."""
        ...

    def structured(
        self, system: str, user: str, schema: dict[str, Any], *, temperature: float = 0.0
    ) -> dict[str, Any]:
        """Return a JSON object matching ``schema``."""
        ...

    def complete(self, system: str, user: str, *, temperature: float = 0.3) -> str:
        """Return a free-text completion."""
        ...


def parse_json_object(text: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from a model response."""
    text = text.strip()
    # Strip markdown fences.
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("No JSON object found in model output")
