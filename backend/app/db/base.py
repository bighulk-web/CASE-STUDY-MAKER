"""Database engine, session factory, and schema initialization.

We use SQLAlchemy 2.0 with a synchronous SQLite engine. A dedicated FTS5 virtual
table (``case_studies_fts``) powers keyword search and is kept in sync via triggers
created in :func:`init_db`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.logging import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _make_engine() -> Engine:
    settings = get_settings()
    settings.ensure_dirs()
    engine = create_engine(
        settings.db_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.close()

    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _make_engine()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _SessionLocal


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a session (commit handled by callers)."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


FTS_TABLE = "case_studies_fts"


def _init_fts(engine: Engine) -> None:
    """Create the FTS5 table + sync triggers if not present."""
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE}
                USING fts5(
                    case_study_id UNINDEXED,
                    title, customer, one_line_summary, executive_summary,
                    business_challenge, solution, benefits, keywords, tags,
                    technology, products_used, industry
                )
                """
            )
        )


def init_db() -> None:
    """Create all tables and FTS objects. Idempotent."""
    from app.db import models  # noqa: F401  (register mappers)

    engine = get_engine()
    models.Base.metadata.create_all(engine)
    _init_fts(engine)
    logger.info("Database initialized at %s", get_settings().db_path)


def reset_engine() -> None:
    """Dispose cached engine/session (used by tests switching data dirs)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
