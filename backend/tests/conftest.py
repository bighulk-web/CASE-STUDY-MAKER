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
    os.environ["CSM_DATA_DIR"] = str(tmp_path)

    from app.config import reset_settings_cache
    from app.db.base import init_db, reset_engine

    reset_settings_cache()
    reset_engine()
    init_db()

    yield tmp_path

    if prev is None:
        os.environ.pop("CSM_DATA_DIR", None)
    else:
        os.environ["CSM_DATA_DIR"] = prev
    reset_settings_cache()
    reset_engine()


@pytest.fixture()
def client(data_dir: Path) -> Iterator[object]:
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
