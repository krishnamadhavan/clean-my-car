"""Ops waitlist triage endpoints — Module 4 (Must + Should)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.models.waitlist import WaitlistStatus
from app.schemas.ops_waitlist import (
    OpsWaitlistEntryOut,
    OpsWaitlistListOut,
    OpsWaitlistPatch,
    OpsWaitlistSummaryOut,
)
from app.services.ops_waitlist import OpsWaitlistService

router = APIRouter(prefix="/waitlist", tags=["ops-waitlist"])


def get_ops_waitlist_service(db: DbSession) -> OpsWaitlistService:
    return OpsWaitlistService(session=db)


OpsWaitlistServiceDep = Annotated[OpsWaitlistService, Depends(get_ops_waitlist_service)]


@router.get(
    "",
    response_model=OpsWaitlistListOut,
    summary="List waitlist entries (OPS-WAIT-01)",
)
async def list_waitlist(
    _ops: CurrentOpsOperator,
    svc: OpsWaitlistServiceDep,
    city_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[WaitlistStatus | None, Query()] = None,
    phone: Annotated[str | None, Query()] = None,
    society_name: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> OpsWaitlistListOut:
    return await svc.list_entries(
        city_id=city_id,
        status=status,
        phone=phone,
        society_name=society_name,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/summary",
    response_model=OpsWaitlistSummaryOut,
    summary="Waitlist demand summary (OPS-WAIT-04)",
)
async def waitlist_summary(
    _ops: CurrentOpsOperator,
    svc: OpsWaitlistServiceDep,
) -> OpsWaitlistSummaryOut:
    return await svc.summary()


@router.get(
    "/{entry_id}",
    response_model=OpsWaitlistEntryOut,
    summary="Waitlist entry detail (OPS-WAIT-02)",
)
async def get_waitlist_entry(
    entry_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsWaitlistServiceDep,
) -> OpsWaitlistEntryOut:
    return await svc.get_entry(entry_id)


@router.patch(
    "/{entry_id}",
    response_model=OpsWaitlistEntryOut,
    summary="Update waitlist status/notes (OPS-WAIT-03)",
)
async def patch_waitlist_entry(
    entry_id: UUID,
    body: OpsWaitlistPatch,
    _ops: CurrentOpsOperator,
    svc: OpsWaitlistServiceDep,
) -> OpsWaitlistEntryOut:
    return await svc.patch_entry(entry_id, body)
