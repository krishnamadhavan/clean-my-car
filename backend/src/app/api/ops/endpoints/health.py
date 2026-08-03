"""Ops platform health — placeholder so the Ops OpenAPI surface is non-empty."""

from fastapi import APIRouter

router = APIRouter(tags=["ops-platform"])


@router.get(
    "/health",
    summary="Ops API health (OPS-PLAT-01)",
    response_model=dict[str, str],
)
async def ops_health() -> dict[str, str]:
    """Liveness for the ops surface. Catalog APIs will be added under this prefix."""
    return {"status": "ok", "surface": "ops"}
