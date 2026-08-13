"""Ops payment schemas (Ops Module 8)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentKind, PaymentStatus
from app.schemas.ops_subscription import OpsSubscriptionUserOut


class OpsPaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user: OpsSubscriptionUserOut | None = None
    subscription_id: UUID | None = None
    amount_paise: int
    currency: str
    status: PaymentStatus
    kind: PaymentKind
    period_start: date | None = None
    period_end: date | None = None
    provider: str
    provider_ref: str | None = None
    failure_reason: str | None = None
    captured_at: datetime | None = None
    reconciled_at: datetime | None = None
    reconciled_by_operator_id: UUID | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class OpsPaymentListOut(BaseModel):
    items: list[OpsPaymentOut]
    total: int
    page: int
    page_size: int


class OpsPaymentReconcileIn(BaseModel):
    """Manual capture / reconcile (OPS-PAY-03)."""

    model_config = ConfigDict(extra="forbid")

    notes: str | None = Field(default=None, max_length=2000)
    provider_ref: str | None = Field(default=None, max_length=120)
