"""Subscription domain (Module 7) — calendar-month service plan."""

from __future__ import annotations

import uuid
from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.models.vehicle import VehicleSizeTier, _size_tier_enum

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.payment import Payment
    from app.models.society import Society
    from app.models.user import User
    from app.models.vehicle import Vehicle


class SubscriptionStatus(StrEnum):
    pending_payment = "pending_payment"
    active = "active"
    cancel_scheduled = "cancel_scheduled"
    paused = "paused"
    expired = "expired"
    inactive = "inactive"


_subscription_status_enum = Enum(
    SubscriptionStatus,
    name="subscription_status",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class Subscription(Base, TimestampMixin):
    """One subscription lifecycle row for a consumer account."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    city_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cities.id", ondelete="RESTRICT"),
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
        index=True,
    )
    size_tier: Mapped[VehicleSizeTier] = mapped_column(_size_tier_enum, nullable=False)
    interior_frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[SubscriptionStatus] = mapped_column(
        _subscription_status_enum,
        nullable=False,
        default=SubscriptionStatus.pending_payment,
        index=True,
    )
    monthly_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    cancel_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    paused_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    paused_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    city: Mapped[City] = relationship("City", foreign_keys=[city_id])
    society: Mapped[Society] = relationship("Society", foreign_keys=[society_id])
    vehicle: Mapped[Vehicle | None] = relationship("Vehicle", foreign_keys=[vehicle_id])
    payments: Mapped[list[Payment]] = relationship(
        "Payment",
        back_populates="subscription",
    )
