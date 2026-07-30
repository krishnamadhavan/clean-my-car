"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Startup hooks (e.g. warm pools) go here.
    yield
    # Shutdown hooks go here.


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
        }

    return application


app = create_app()
