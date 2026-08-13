"""Support tickets (Module 12)."""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class SupportTicketStatus(StrEnum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class SupportTicketCategory(StrEnum):
    billing = "billing"
    service = "service"
    account = "account"
    other = "other"


_ticket_status_enum = Enum(
    SupportTicketStatus,
    name="support_ticket_status",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

_ticket_category_enum = Enum(
    SupportTicketCategory,
    name="support_ticket_category",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class SupportTicket(Base, TimestampMixin):
    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[SupportTicketCategory] = mapped_column(
        _ticket_category_enum,
        nullable=False,
        default=SupportTicketCategory.other,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SupportTicketStatus] = mapped_column(
        _ticket_status_enum,
        nullable=False,
        default=SupportTicketStatus.open,
        index=True,
    )
    wash_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("washes.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    ops_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ops_reply: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
