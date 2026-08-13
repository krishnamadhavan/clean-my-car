"""Consumer support tickets — Module 12 (SUP-03–05)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.support import (
    SupportTicketCreateIn,
    SupportTicketListOut,
    SupportTicketOut,
)
from app.services.support import SupportService

router = APIRouter(prefix="/me/support/tickets", tags=["support"])


def get_support_service(db: DbSession) -> SupportService:
    return SupportService(session=db)


SupportServiceDep = Annotated[SupportService, Depends(get_support_service)]


@router.post(
    "",
    response_model=SupportTicketOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create support ticket (SUP-03)",
)
async def create_ticket(
    body: SupportTicketCreateIn,
    user: CurrentUser,
    svc: SupportServiceDep,
) -> SupportTicketOut:
    return await svc.create_ticket(user, body)


@router.get(
    "",
    response_model=SupportTicketListOut,
    summary="List my tickets (SUP-04)",
)
async def list_tickets(
    user: CurrentUser,
    svc: SupportServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SupportTicketListOut:
    return await svc.list_mine(user, page=page, page_size=page_size)


@router.get(
    "/{ticket_id}",
    response_model=SupportTicketOut,
    summary="Ticket detail (SUP-05)",
)
async def get_ticket(
    ticket_id: UUID,
    user: CurrentUser,
    svc: SupportServiceDep,
) -> SupportTicketOut:
    return await svc.get_mine(user, ticket_id)
