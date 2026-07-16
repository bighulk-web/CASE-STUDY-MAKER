"""Anthropic (Claude) provider."""

from __future__ import annotations

import json
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from .base import parse_json_object

DEFAULT_MODEL = "claude-3-5-sonnet-latest"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "") -> None:
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL

    def available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import anthropic  # noqa: F401
        except Exception:
            return False
        return True

    def _client(self):  # pragma: no cover
        import anthropic

        return anthropic.Anthropic(api_key=self._api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def structured(  # pragma: no cover
        self, system: str, user: str, schema: dict[str, Any], *, temperature: float = 0.0
    ) -> dict[str, Any]:
        client = self._client()
        msg = client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=temperature,
            system=system + "\nReturn ONLY a valid JSON object.",
            messages=[
                {"role": "user", "content": user + "\n\nJSON schema:\n" + json.dumps(schema)}
            ],
        )
        return parse_json_object(msg.content[0].text)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def complete(  # pragma: no cover
        self, system: str, user: str, *, temperature: float = 0.3
    ) -> str:
        client = self._client()
        msg = client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
