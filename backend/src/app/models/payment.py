"""Payment / intent domain (Module 8) — manual monthly pay + ops reconcile."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.ops_operator import OpsOperator
    from app.models.subscription import Subscription
    from app.models.user import User


class PaymentStatus(StrEnum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class PaymentKind(StrEnum):
    subscription_start = "subscription_start"
    renewal = "renewal"
    adjustment = "adjustment"


_payment_status_enum = Enum(
    PaymentStatus,
    name="payment_status",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

_payment_kind_enum = Enum(
    PaymentKind,
    name="payment_kind",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class Payment(Base, TimestampMixin):
    """Payment intent / capture record (gateway-agnostic)."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[PaymentStatus] = mapped_column(
        _payment_status_enum,
        nullable=False,
        default=PaymentStatus.pending,
        index=True,
    )
    kind: Mapped[PaymentKind] = mapped_column(
        _payment_kind_enum,
        nullable=False,
        default=PaymentKind.subscription_start,
    )
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="manual")
    provider_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reconciled_by_operator_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ops_operators.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    subscription: Mapped[Subscription | None] = relationship(
        "Subscription",
        back_populates="payments",
        foreign_keys=[subscription_id],
    )
    reconciled_by: Mapped[OpsOperator | None] = relationship(
        "OpsOperator",
        foreign_keys=[reconciled_by_operator_id],
    )
