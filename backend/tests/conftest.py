"""Shared pytest fixtures.

Every test runs against an isolated temporary data directory so tests never touch
the developer's real ``~/.case-study-maker`` state and never collide with each other.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture()
def data_dir(tmp_path: Path) -> Iterator[Path]:
    """Point the app at an isolated data directory and reset cached singletons."""
    prev = os.environ.get("CSM_DATA_DIR")
    prev_sync = os.environ.get("CSM_SYNC_JOBS")
    os.environ["CSM_DATA_DIR"] = str(tmp_path)
    os.environ["CSM_SYNC_JOBS"] = "true"

    from app.config import reset_settings_cache
    from app.db.base import init_db, reset_engine
    from app.services.embeddings.factory import reset_cache as reset_embed_cache
    from app.services.vectorstore.factory import reset_instance as reset_vs

    reset_settings_cache()
    reset_engine()
    reset_embed_cache()
    reset_vs()
    init_db()

    yield tmp_path

    if prev is None:
        os.environ.pop("CSM_DATA_DIR", None)
    else:
        os.environ["CSM_DATA_DIR"] = prev
    if prev_sync is None:
        os.environ.pop("CSM_SYNC_JOBS", None)
    else:
        os.environ["CSM_SYNC_JOBS"] = prev_sync
    reset_settings_cache()
    reset_engine()
    reset_embed_cache()
    reset_vs()


@pytest.fixture()
def client(data_dir: Path) -> Iterator[object]:
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
