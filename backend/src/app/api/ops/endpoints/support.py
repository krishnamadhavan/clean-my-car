"""Ops support ticket queue — Module 12 (OPS-SUP-03/04)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.models.support import SupportTicketStatus
from app.schemas.support import (
    OpsSupportTicketListOut,
    OpsSupportTicketOut,
    OpsSupportTicketPatchIn,
)
from app.services.ops_platform import OpsPlatformService
from app.services.support import SupportService

router = APIRouter(prefix="/support/tickets", tags=["ops-support"])


def get_support_service(db: DbSession) -> SupportService:
    return SupportService(session=db)


SupportServiceDep = Annotated[SupportService, Depends(get_support_service)]


@router.get(
    "",
    response_model=OpsSupportTicketListOut,
    summary="Ticket queue (OPS-SUP-03)",
)
async def list_tickets(
    _ops: CurrentOpsOperator,
    svc: SupportServiceDep,
    status: Annotated[SupportTicketStatus | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OpsSupportTicketListOut:
    return await svc.ops_list(status=status, page=page, page_size=page_size)


@router.patch(
    "/{ticket_id}",
    response_model=OpsSupportTicketOut,
    summary="Update ticket (OPS-SUP-04)",
)
async def patch_ticket(
    ticket_id: UUID,
    body: OpsSupportTicketPatchIn,
    ops: CurrentOpsOperator,
    svc: SupportServiceDep,
    db: DbSession,
) -> OpsSupportTicketOut:
    result = await svc.ops_patch(ticket_id, body)
    await OpsPlatformService(db).record(
        operator=ops,
        action="ticket.patch",
        resource_type="support_ticket",
        resource_id=str(ticket_id),
        summary=f"Updated ticket {ticket_id}",
    )
    return result
