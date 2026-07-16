"""Google Gemini provider."""

from __future__ import annotations

import json
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from .base import parse_json_object

DEFAULT_MODEL = "gemini-1.5-pro"


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str = "") -> None:
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL

    def available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import google.generativeai  # noqa: F401
        except Exception:
            return False
        return True

    def _model(self):  # pragma: no cover
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        return genai.GenerativeModel(self.model)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def structured(  # pragma: no cover
        self, system: str, user: str, schema: dict[str, Any], *, temperature: float = 0.0
    ) -> dict[str, Any]:
        model = self._model()
        prompt = (
            system
            + "\nReturn ONLY valid JSON.\n"
            + user
            + "\n\nJSON schema:\n"
            + json.dumps(schema)
        )
        resp = model.generate_content(
            prompt, generation_config={"response_mime_type": "application/json"}
        )
        return parse_json_object(resp.text)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def complete(  # pragma: no cover
        self, system: str, user: str, *, temperature: float = 0.3
    ) -> str:
        model = self._model()
        resp = model.generate_content(system + "\n\n" + user)
        return resp.text
