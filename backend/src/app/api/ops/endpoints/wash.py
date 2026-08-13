"""Ops wash endpoints — Module 10 field actions."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.models.wash import WashStatus
from app.schemas.ops_wash import (
    OpsRosterOut,
    OpsWashCompleteIn,
    OpsWashGenerateIn,
    OpsWashGenerateOut,
    OpsWashListOut,
    OpsWashMissIn,
    OpsWashOut,
)
from app.services.ops_wash import OpsWashService

router = APIRouter(tags=["ops-washes"])


def get_ops_wash_service(db: DbSession) -> OpsWashService:
    return OpsWashService(session=db)


OpsWashServiceDep = Annotated[OpsWashService, Depends(get_ops_wash_service)]


@router.get(
    "/washes",
    response_model=OpsWashListOut,
    summary="List washes (OPS-WASH-04)",
)
async def list_washes(
    _ops: CurrentOpsOperator,
    svc: OpsWashServiceDep,
    society_id: Annotated[UUID | None, Query()] = None,
    service_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    status: Annotated[WashStatus | None, Query()] = None,
    user_id: Annotated[UUID | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OpsWashListOut:
    from datetime import date

    day = date.fromisoformat(service_date) if service_date else None
    return await svc.list_washes(
        society_id=society_id,
        service_date=day,
        status=status,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/washes/{wash_id}/complete",
    response_model=OpsWashOut,
    summary="Mark wash complete (OPS-WASH-01)",
)
async def complete_wash(
    wash_id: UUID,
    ops: CurrentOpsOperator,
    svc: OpsWashServiceDep,
    body: OpsWashCompleteIn | None = None,
) -> OpsWashOut:
    return await svc.complete(wash_id, ops, body)


@router.post(
    "/washes/{wash_id}/miss",
    response_model=OpsWashOut,
    summary="Mark wash missed + optional retry (OPS-WASH-02)",
)
async def miss_wash(
    wash_id: UUID,
    ops: CurrentOpsOperator,
    svc: OpsWashServiceDep,
    body: OpsWashMissIn | None = None,
) -> OpsWashOut:
    return await svc.miss(wash_id, ops, body)


@router.get(
    "/societies/{society_id}/roster",
    response_model=OpsRosterOut,
    summary="Society roster for a date (OPS-WASH-03)",
)
async def society_roster(
    society_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsWashServiceDep,
    service_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
) -> OpsRosterOut:
    from datetime import date

    day = date.fromisoformat(service_date) if service_date else None
    return await svc.roster(society_id, day)


@router.post(
    "/washes/generate",
    response_model=OpsWashGenerateOut,
    summary="Materialise schedule rows (OPS-WASH-05)",
)
async def generate_washes(
    _ops: CurrentOpsOperator,
    svc: OpsWashServiceDep,
    body: OpsWashGenerateIn | None = None,
) -> OpsWashGenerateOut:
    return await svc.generate(body or OpsWashGenerateIn())
