"""Consumer wash endpoints — Module 10 (WASH-01–03)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import CurrentUser, DbSession
from app.models.wash import WashStatus
from app.schemas.wash import WashListOut, WashOut, WashSummaryOut
from app.services.wash import WashService

router = APIRouter(tags=["washes"])


def get_wash_service(db: DbSession) -> WashService:
    return WashService(session=db)


WashServiceDep = Annotated[WashService, Depends(get_wash_service)]


@router.get(
    "/me/washes/summary",
    response_model=WashSummaryOut,
    summary="Wash progress this month (WASH-01)",
)
async def wash_summary(user: CurrentUser, svc: WashServiceDep) -> WashSummaryOut:
    return await svc.summary(user)


@router.get(
    "/me/washes",
    response_model=WashListOut,
    summary="Wash history (WASH-02)",
)
async def list_washes(
    user: CurrentUser,
    svc: WashServiceDep,
    month: Annotated[str | None, Query(description="YYYY-MM")] = None,
    status: Annotated[WashStatus | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> WashListOut:
    try:
        return await svc.list_washes(
            user, month=month, status=status, page=page, page_size=page_size
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/me/washes/{wash_id}",
    response_model=WashOut,
    summary="Wash detail (WASH-03)",
)
async def get_wash(wash_id: UUID, user: CurrentUser, svc: WashServiceDep) -> WashOut:
    return await svc.get_wash(user, wash_id)
