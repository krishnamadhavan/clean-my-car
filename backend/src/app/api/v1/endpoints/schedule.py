"""Consumer schedule endpoints — Module 10 (WASH-04)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.schedule import ScheduleOut
from app.services.schedule import ScheduleService

router = APIRouter(tags=["schedule"])


def get_schedule_service(db: DbSession) -> ScheduleService:
    return ScheduleService(session=db)


ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]


@router.get(
    "/me/schedule",
    response_model=ScheduleOut,
    summary="Upcoming wash days (WASH-04)",
)
async def get_schedule(
    user: CurrentUser,
    svc: ScheduleServiceDep,
    days: Annotated[
        int | None,
        Query(
            ge=1,
            le=62,
            description="Optional cap from today (default: through current period end).",
        ),
    ] = None,
) -> ScheduleOut:
    return await svc.upcoming(user, days=days)
