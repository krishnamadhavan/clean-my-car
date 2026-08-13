"""Consumer + ops support tickets (Module 12)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.support import SupportTicket, SupportTicketStatus
from app.models.user import User
from app.schemas.support import (
    OpsSupportTicketListOut,
    OpsSupportTicketOut,
    OpsSupportTicketPatchIn,
    SupportTicketCreateIn,
    SupportTicketListOut,
    SupportTicketOut,
)


class SupportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_ticket(self, user: User, body: SupportTicketCreateIn) -> SupportTicketOut:
        ticket = SupportTicket(
            user_id=user.id,
            category=body.category,
            message=body.message.strip(),
            wash_id=body.wash_id,
            payment_id=body.payment_id,
            status=SupportTicketStatus.open,
        )
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return SupportTicketOut.model_validate(ticket)

    async def list_mine(
        self, user: User, *, page: int = 1, page_size: int = 20
    ) -> SupportTicketListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        total = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(SupportTicket)
                    .where(SupportTicket.user_id == user.id)
                )
            ).scalar_one()
        )
        rows = (
            (
                await self.session.execute(
                    select(SupportTicket)
                    .where(SupportTicket.user_id == user.id)
                    .order_by(SupportTicket.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return SupportTicketListOut(
            items=[SupportTicketOut.model_validate(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_mine(self, user: User, ticket_id: UUID) -> SupportTicketOut:
        ticket = await self.session.get(SupportTicket, ticket_id)
        if ticket is None or ticket.user_id != user.id:
            raise NotFoundError("Ticket not found", code="ticket_not_found")
        return SupportTicketOut.model_validate(ticket)

    async def ops_list(
        self,
        *,
        status: SupportTicketStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OpsSupportTicketListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        q = select(SupportTicket).options(selectinload(SupportTicket.user))
        count_q = select(func.count()).select_from(SupportTicket)
        if status is not None:
            q = q.where(SupportTicket.status == status)
            count_q = count_q.where(SupportTicket.status == status)
        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (
            (
                await self.session.execute(
                    q.order_by(SupportTicket.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return OpsSupportTicketListOut(
            items=[self._ops_out(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def ops_patch(
        self, ticket_id: UUID, body: OpsSupportTicketPatchIn
    ) -> OpsSupportTicketOut:
        ticket = (
            await self.session.execute(
                select(SupportTicket)
                .options(selectinload(SupportTicket.user))
                .where(SupportTicket.id == ticket_id)
            )
        ).scalar_one_or_none()
        if ticket is None:
            raise NotFoundError("Ticket not found", code="ticket_not_found")
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(ticket, key, value)
        await self.session.commit()
        await self.session.refresh(ticket)
        if ticket.user is None:
            ticket = (
                await self.session.execute(
                    select(SupportTicket)
                    .options(selectinload(SupportTicket.user))
                    .where(SupportTicket.id == ticket_id)
                )
            ).scalar_one()
        return self._ops_out(ticket)

    @staticmethod
    def _ops_out(ticket: SupportTicket) -> OpsSupportTicketOut:
        return OpsSupportTicketOut(
            id=ticket.id,
            user_id=ticket.user_id,
            category=ticket.category,
            message=ticket.message,
            status=ticket.status,
            wash_id=ticket.wash_id,
            payment_id=ticket.payment_id,
            ops_reply=ticket.ops_reply,
            ops_notes=ticket.ops_notes,
            user_phone=ticket.user.phone if ticket.user else None,
            user_name=ticket.user.name if ticket.user else None,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )
