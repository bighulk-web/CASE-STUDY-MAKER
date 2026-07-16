"""Construct the configured LLM provider (falling back to offline)."""

from __future__ import annotations

from app.logging import get_logger

from .base import LLMProvider
from .offline import OfflineProvider

logger = get_logger(__name__)


def get_llm_provider() -> LLMProvider:
    from app.services.settings_service import get_value

    provider = (get_value("llm_provider") or "offline").lower()
    model = get_value("llm_model")

    p: LLMProvider
    if provider == "openai":
        from .openai_provider import OpenAIProvider

        p = OpenAIProvider(api_key=get_value("openai_api_key"), model=model)
    elif provider == "anthropic":
        from .anthropic_provider import AnthropicProvider

        p = AnthropicProvider(api_key=get_value("anthropic_api_key"), model=model)
    elif provider == "gemini":
        from .gemini_provider import GeminiProvider

        p = GeminiProvider(api_key=get_value("gemini_api_key"), model=model)
    else:
        return OfflineProvider()

    if not p.available():
        logger.info("LLM provider %s not available; using offline heuristics", provider)
        return OfflineProvider()
    return p
