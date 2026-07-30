"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — process is up."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Readiness probe — process can serve traffic (DB reachable)."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": "down", "detail": str(exc)},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "database": "up"},
    )
