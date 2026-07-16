"""FastAPI application factory.

Mounts all routers under ``/api`` and initializes the database on startup. Routers
that belong to later build phases are imported lazily and mounted only if present,
so the app boots cleanly at every stage of development.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from importlib import import_module

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.base import init_db
from app.logging import get_logger

logger = get_logger(__name__)

# (module path, router attribute) for optional routers mounted when available.
_OPTIONAL_ROUTERS = [
    "app.api.documents",
    "app.api.folders",
    "app.api.jobs",
    "app.api.templates",
    "app.api.search",
    "app.api.builder",
    "app.api.settings",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings().ensure_dirs()
    init_db()
    # Start background job worker if the module is available (Phase 2+).
    try:
        from app.services.jobs.queue import start_worker

        await start_worker()
        logger.info("Job worker started")
    except Exception as exc:  # pragma: no cover - optional at early phases
        logger.info("Job worker not started: %s", exc)
    yield
    try:
        from app.services.jobs.queue import stop_worker

        await stop_worker()
    except Exception:  # pragma: no cover
        pass


def create_app() -> FastAPI:
    app = FastAPI(title="Case Study Maker API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix="/api")

    from app.api.health import router as health_router

    api.include_router(health_router)

    for mod_path in _OPTIONAL_ROUTERS:
        try:
            module = import_module(mod_path)
            api.include_router(module.router)
            logger.info("Mounted router: %s", mod_path)
        except ModuleNotFoundError:
            logger.debug("Router not available yet: %s", mod_path)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to mount %s: %s", mod_path, exc)

    app.include_router(api)

    # WebSocket for job progress (mounted if available).
    try:
        from app.api.ws import register_ws

        register_ws(app)
    except Exception:  # pragma: no cover
        pass

    return app


app = create_app()
