from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from dendridb import __version__
from dendridb.api.routes import episodes, health, memories, semantic_memory, working_memory
from dendridb.config import get_settings
from dendridb.core.database import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await get_engine().dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A brain-inspired memory database for AI systems.",
        lifespan=lifespan,
        debug=settings.debug,
    )
    application.include_router(health.router, tags=["health"])
    application.include_router(memories.router)
    application.include_router(working_memory.router)
    application.include_router(episodes.router)
    application.include_router(semantic_memory.router)
    return application


app = create_app()


def get_app_metadata() -> dict[str, Any]:
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
    }
