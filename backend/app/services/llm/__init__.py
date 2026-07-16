"""LLM provider abstraction.

Providers implement structured (JSON) and free-text completion. The default is the
``offline`` provider, which reports itself unavailable so callers transparently fall
back to deterministic heuristics — the app works with no API keys. Real providers
(OpenAI / Anthropic / Gemini) activate when a key is configured in Settings.
"""

from __future__ import annotations

from .base import LLMProvider
from .factory import get_llm_provider

__all__ = ["LLMProvider", "get_llm_provider"]
