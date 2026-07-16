"""Health and capability reporting endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "data_dir": str(settings.data_dir),
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
    }


@router.get("/capabilities")
def capabilities() -> dict[str, bool]:
    """Report which optional subsystems are available in this environment."""

    def _has(mod: str) -> bool:
        import importlib.util

        try:
            return importlib.util.find_spec(mod) is not None
        except (ModuleNotFoundError, ValueError):
            return False

    import shutil

    return {
        "chromadb": _has("chromadb"),
        "sentence_transformers": _has("sentence_transformers"),
        "openai": _has("openai"),
        "anthropic": _has("anthropic"),
        "gemini": _has("google.generativeai"),
        "tesseract": shutil.which("tesseract") is not None,
        "libreoffice": (shutil.which("soffice") or shutil.which("libreoffice")) is not None,
    }
