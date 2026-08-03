"""FastAPI application entrypoint.

Two OpenAPI / Swagger surfaces:

- **Consumer:** ``/docs`` + ``/openapi.json`` — mobile / public product APIs under ``/api/v1``
  (excludes ``/api/v1/ops``).
- **Ops:** ``/ops/docs`` + ``/ops/openapi.json`` — internal catalog & field APIs under
  ``/api/v1/ops``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse

from app import __version__
from app.api.ops.router import ops_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError

OPS_PATH_PREFIX = "/api/v1/ops"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Optional ops bootstrap operator from env when that email is not present yet
    settings = get_settings()
    if settings.ops_bootstrap_email and settings.ops_bootstrap_password:
        from app.db.session import AsyncSessionLocal
        from app.services.ops_auth import OpsAuthService

        async with AsyncSessionLocal() as session:
            await OpsAuthService(session, settings).ensure_bootstrap_operator()

    yield
    from app.db.session import dispose_engine

    await dispose_engine()


def _build_openapi(
    application: FastAPI,
    *,
    title: str,
    description: str,
    include_ops_only: bool,
) -> dict[str, Any]:
    schema = get_openapi(
        title=title,
        version=__version__,
        description=description,
        routes=application.routes,
    )
    paths = schema.get("paths") or {}
    if include_ops_only:
        filtered = {path: item for path, item in paths.items() if path.startswith(OPS_PATH_PREFIX)}
    else:
        filtered = {
            path: item for path, item in paths.items() if not path.startswith(OPS_PATH_PREFIX)
        }
    schema["paths"] = filtered

    # Drop unused tag definitions so each UI stays focused
    used: set[str] = set()
    for path_item in filtered.values():
        for operation in path_item.values():
            if isinstance(operation, dict):
                for tag in operation.get("tags") or []:
                    used.add(tag)
    if "tags" in schema:
        schema["tags"] = [t for t in schema["tags"] if t.get("name") in used]

    return schema


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
        lifespan=lifespan,
        # Dual Swagger/OpenAPI registered explicitly below
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @application.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        body: dict = {"code": exc.code, "message": exc.message}
        if exc.details is not None:
            body["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=body)

    origins = settings.cors_origin_list
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Consumer product APIs
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    # Ops catalog / field APIs (same process; separate OpenAPI UI)
    application.include_router(ops_router, prefix=OPS_PATH_PREFIX)

    # ----- Consumer OpenAPI + Swagger -----
    @application.get("/openapi.json", include_in_schema=False)
    async def consumer_openapi() -> dict[str, Any]:
        return _build_openapi(
            application,
            title=f"{settings.app_name} (Consumer)",
            description=(
                "Mobile consumer APIs for Clean My Car. "
                "Ops/admin routes are documented separately at `/ops/docs`."
            ),
            include_ops_only=False,
        )

    @application.get("/docs", include_in_schema=False)
    async def consumer_swagger() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{settings.app_name} — Consumer API",
        )

    @application.get("/redoc", include_in_schema=False)
    async def consumer_redoc() -> HTMLResponse:
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{settings.app_name} — Consumer API",
        )

    # ----- Ops OpenAPI + Swagger -----
    @application.get("/ops/openapi.json", include_in_schema=False)
    async def ops_openapi() -> dict[str, Any]:
        return _build_openapi(
            application,
            title=f"{settings.app_name} (Ops)",
            description=(
                "Internal ops APIs for master data (cities, societies, vehicle catalog, "
                "pricing) and field actions. Inventory: docs/OPS_API_INVENTORY.md. "
                "Not for the consumer iOS app."
            ),
            include_ops_only=True,
        )

    @application.get("/ops/docs", include_in_schema=False)
    async def ops_swagger() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url="/ops/openapi.json",
            title=f"{settings.app_name} — Ops API",
        )

    @application.get("/ops/redoc", include_in_schema=False)
    async def ops_redoc() -> HTMLResponse:
        return get_redoc_html(
            openapi_url="/ops/openapi.json",
            title=f"{settings.app_name} — Ops API",
        )

    @application.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "docs_ops": "/ops/docs",
            "openapi": "/openapi.json",
            "openapi_ops": "/ops/openapi.json",
        }

    return application


app = create_app()
