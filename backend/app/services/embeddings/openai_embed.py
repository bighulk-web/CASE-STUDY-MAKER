"""OpenAI embeddings (optional)."""

from __future__ import annotations

_DIMS = {
    "text-embedding-3-large": 3072,
    "text-embedding-3-small": 1536,
}


class OpenAIEmbedding:
    name = "openai"

    def __init__(self, api_key: str, model: str = "text-embedding-3-large") -> None:
        self._api_key = api_key
        self.model = model
        self.dim = _DIMS.get(model, 3072)

    def available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import openai  # noqa: F401
        except Exception:
            return False
        return True

    def embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover - network
        import openai

        client = openai.OpenAI(api_key=self._api_key)
        resp = client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]
