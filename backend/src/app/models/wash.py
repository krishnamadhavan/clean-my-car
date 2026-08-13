"""Wash / visit domain (Module 10) — scheduled, completed, missed, retry."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.ops_operator import OpsOperator
    from app.models.society import Society
    from app.models.subscription import Subscription
    from app.models.user import User
    from app.models.vehicle import Vehicle


class WashStatus(StrEnum):
    scheduled = "scheduled"
    completed = "completed"
    missed = "missed"
    retry_scheduled = "retry_scheduled"
    skipped = "skipped"


_wash_status_enum = Enum(
    WashStatus,
    name="wash_status",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class Wash(Base, TimestampMixin):
    """One service visit occurrence for a subscriber."""

    __tablename__ = "washes"
    __table_args__ = (
        UniqueConstraint("user_id", "service_date", name="uq_washes_user_service_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    society_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("societies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    service_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[WashStatus] = mapped_column(
        _wash_status_enum,
        nullable=False,
        default=WashStatus.scheduled,
        index=True,
    )
    includes_exterior: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    includes_interior: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by_operator_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ops_operators.id", ondelete="SET NULL"),
        nullable=True,
    )
    miss_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retry_of_wash_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("washes.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    subscription: Mapped[Subscription] = relationship(
        "Subscription", foreign_keys=[subscription_id]
    )
    society: Mapped[Society] = relationship("Society", foreign_keys=[society_id])
    vehicle: Mapped[Vehicle | None] = relationship("Vehicle", foreign_keys=[vehicle_id])
    completed_by: Mapped[OpsOperator | None] = relationship(
        "OpsOperator", foreign_keys=[completed_by_operator_id]
    )
