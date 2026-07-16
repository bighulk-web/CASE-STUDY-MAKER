"""Deterministic hashing embedding (no external dependencies).

Maps tokens into a fixed-dimensional vector via feature hashing with sub-linear term
weighting, then L2-normalizes. This yields cosine similarities that track lexical /
topical overlap well enough for offline semantic search and fully deterministic tests.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashingEmbedding:
    name = "hashing"

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = _TOKEN_RE.findall((text or "").lower())
        counts = Counter(tokens)
        for tok, cnt in counts.items():
            h = int.from_bytes(hashlib.md5(tok.encode()).digest()[:8], "little")
            idx = h % self.dim
            sign = 1.0 if (h >> 63) & 1 else -1.0
            vec[idx] += sign * (1.0 + math.log(cnt))
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]
