"""Content-addressed file storage helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.config import get_settings


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def store_bytes(data: bytes, ext: str) -> tuple[str, Path]:
    """Store bytes content-addressed under the storage dir.

    Returns ``(sha256, path)``. Identical content is stored once.
    """
    digest = sha256_bytes(data)
    settings = get_settings()
    subdir = settings.storage_dir / digest[:2]
    subdir.mkdir(parents=True, exist_ok=True)
    ext = ext.lstrip(".")
    path = subdir / f"{digest}.{ext}"
    if not path.exists():
        path.write_bytes(data)
    return digest, path


def save_asset(data: bytes, ext: str, subdir: str = "") -> Path:
    """Persist an extracted asset (image) and return its path."""
    settings = get_settings()
    digest = sha256_bytes(data)
    base = settings.assets_dir / subdir if subdir else settings.assets_dir
    base.mkdir(parents=True, exist_ok=True)
    ext = ext.lstrip(".") or "png"
    path = base / f"{digest}.{ext}"
    if not path.exists():
        path.write_bytes(data)
    return path
