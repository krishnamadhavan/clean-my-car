"""Consumer dashboard — Module 9 (DASH-01)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardOut
from app.services.dashboard import DashboardService

router = APIRouter(tags=["dashboard"])


def get_dashboard_service(db: DbSession) -> DashboardService:
    return DashboardService(session=db)


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


@router.get(
    "/me/dashboard",
    response_model=DashboardOut,
    summary="Home dashboard aggregate (DASH-01)",
)
async def get_dashboard(user: CurrentUser, svc: DashboardServiceDep) -> DashboardOut:
    return await svc.get_dashboard(user)
