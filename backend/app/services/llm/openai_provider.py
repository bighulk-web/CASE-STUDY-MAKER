"""OpenAI chat provider with JSON structured output."""

from __future__ import annotations

import json
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.logging import get_logger

from .base import parse_json_object

logger = get_logger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str = "") -> None:
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL

    def available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import openai  # noqa: F401
        except Exception:
            return False
        return True

    def _client(self):  # pragma: no cover - requires network/sdk
        import openai

        return openai.OpenAI(api_key=self._api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def structured(  # pragma: no cover - requires network
        self, system: str, user: str, schema: dict[str, Any], *, temperature: float = 0.0
    ) -> dict[str, Any]:
        client = self._client()
        resp = client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system + "\nReturn ONLY valid JSON."},
                {"role": "user", "content": user + "\n\nJSON schema:\n" + json.dumps(schema)},
            ],
        )
        return parse_json_object(resp.choices[0].message.content or "{}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def complete(  # pragma: no cover - requires network
        self, system: str, user: str, *, temperature: float = 0.3
    ) -> str:
        client = self._client()
        resp = client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""
