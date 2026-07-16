"""Runtime settings resolved from the DB ``settings`` table, overlaying config defaults.

The env/config :class:`app.config.Settings` provides defaults; users can override
provider selection, models, API keys, and theme at runtime via the Settings page.
Values are persisted key/value in the ``settings`` table.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.config import get_settings
from app.db.base import session_scope

# Keys that are safe to expose to the frontend (never return raw API keys).
SECRET_KEYS = {"openai_api_key", "anthropic_api_key", "gemini_api_key"}

_DEFAULT_KEYS = (
    "llm_provider",
    "llm_model",
    "embedding_provider",
    "embedding_model",
    "vectorstore_provider",
    "openai_api_key",
    "anthropic_api_key",
    "gemini_api_key",
    "theme",
)


def _config_default(key: str) -> str:
    cfg = get_settings()
    mapping: dict[str, Any] = {
        "llm_provider": cfg.llm_provider,
        "llm_model": cfg.llm_model,
        "embedding_provider": cfg.embedding_provider,
        "embedding_model": cfg.embedding_model,
        "vectorstore_provider": cfg.vectorstore_provider,
        "openai_api_key": cfg.openai_api_key,
        "anthropic_api_key": cfg.anthropic_api_key,
        "gemini_api_key": cfg.gemini_api_key,
        "theme": "dark",
    }
    return str(mapping.get(key, ""))


def get_value(key: str) -> str:
    from app.db.models import Setting

    with session_scope() as session:
        row = session.scalars(select(Setting).where(Setting.key == key)).first()
        if row is not None and row.value != "":
            return row.value
    return _config_default(key)


def set_value(key: str, value: str) -> None:
    from app.db.models import Setting

    with session_scope() as session:
        row = session.scalars(select(Setting).where(Setting.key == key)).first()
        if row is None:
            session.add(Setting(key=key, value=value))
        else:
            row.value = value


def set_many(values: dict[str, str]) -> None:
    for k, v in values.items():
        set_value(k, v)


def public_settings() -> dict[str, Any]:
    """Return settings for the UI, with secrets masked to a boolean 'configured' flag."""
    out: dict[str, Any] = {}
    for key in _DEFAULT_KEYS:
        val = get_value(key)
        if key in SECRET_KEYS:
            out[key] = ""
            out[f"{key}_configured"] = bool(val)
        else:
            out[key] = val
    return out
