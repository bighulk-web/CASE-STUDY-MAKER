"""Local BGE embeddings via sentence-transformers (optional heavy dependency)."""

from __future__ import annotations

from app.logging import get_logger

logger = get_logger(__name__)

_model_cache: dict[str, object] = {}


class BGELocalEmbedding:
    name = "bge_local"

    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5") -> None:
        self.model_name = model_name
        self.dim = 1024 if "large" in model_name else 768

    def _model(self):  # pragma: no cover - heavy/optional
        if self.model_name not in _model_cache:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model %s", self.model_name)
            _model_cache[self.model_name] = SentenceTransformer(self.model_name)
        return _model_cache[self.model_name]

    def embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover - optional
        model = self._model()
        vecs = model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vecs]
