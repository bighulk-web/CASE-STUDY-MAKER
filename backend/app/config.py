"""Application configuration and filesystem layout.

All runtime state (SQLite DB, uploaded documents, extracted assets, vector store,
generated presentations) lives under a single *data directory* so the app is fully
offline and portable. The location can be overridden with the ``CSM_DATA_DIR``
environment variable (used heavily in tests to get an isolated sandbox).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    env = os.environ.get("CSM_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".case-study-maker").resolve()


class Settings(BaseSettings):
    """Global settings, overridable via ``CSM_`` prefixed environment variables."""

    model_config = SettingsConfigDict(env_prefix="CSM_", extra="ignore")

    data_dir: Path = Field(default_factory=_default_data_dir)

    # Provider defaults are intentionally offline so the app works with no API keys.
    llm_provider: str = "offline"  # offline | openai | anthropic | gemini
    llm_model: str = ""
    embedding_provider: str = "auto"  # auto | bge_local | openai | hashing
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    vectorstore_provider: str = "auto"  # auto | chroma | numpy

    # API keys (empty => provider disabled, falls back to offline).
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    # Server
    host: str = "127.0.0.1"
    port: int = 8756

    # Jobs
    job_concurrency: int = 2

    # ---- Derived paths -------------------------------------------------
    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def storage_dir(self) -> Path:
        return self.data_dir / "storage"

    @property
    def assets_dir(self) -> Path:
        return self.data_dir / "assets"

    @property
    def templates_dir(self) -> Path:
        return self.data_dir / "templates"

    @property
    def presentations_dir(self) -> Path:
        return self.data_dir / "presentations"

    @property
    def previews_dir(self) -> Path:
        return self.data_dir / "previews"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    def ensure_dirs(self) -> None:
        for p in (
            self.data_dir,
            self.storage_dir,
            self.assets_dir,
            self.templates_dir,
            self.presentations_dir,
            self.previews_dir,
            self.chroma_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings


def reset_settings_cache() -> None:
    """Clear cached settings (used by tests that swap ``CSM_DATA_DIR``)."""
    get_settings.cache_clear()
