"""Offline provider: reports itself unavailable so callers use heuristics.

This is the default, ensuring the whole application works with zero API keys.
"""

from __future__ import annotations

from typing import Any


class OfflineProvider:
    name = "offline"
    model = "heuristic"

    def available(self) -> bool:
        return False

    def structured(
        self, system: str, user: str, schema: dict[str, Any], *, temperature: float = 0.0
    ) -> dict[str, Any]:
        raise RuntimeError("offline provider cannot produce structured output")

    def complete(self, system: str, user: str, *, temperature: float = 0.3) -> str:
        raise RuntimeError("offline provider cannot complete")
