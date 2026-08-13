"""Consumer payment / billing schemas (Module 8)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentKind, PaymentStatus


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
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
    created_at: datetime
    updated_at: datetime


class PaymentIntentCreateIn(BaseModel):
    """POST /me/payments/intents — pay current period (first or renewal)."""

    model_config = ConfigDict(extra="forbid")

    subscription_id: UUID | None = Field(
        default=None,
        description="Defaults to the user's current open subscription.",
    )


class PaymentConfirmIn(BaseModel):
    """POST /me/payments/intents/{id}/confirm — client confirm (manual/dev gateway)."""

    model_config = ConfigDict(extra="forbid")

    provider_ref: str | None = Field(default=None, max_length=120)


class PaymentListOut(BaseModel):
    items: list[PaymentOut]
    total: int
    page: int
    page_size: int


class BillingSummaryOut(BaseModel):
    """GET /me/billing/summary — what is due now."""

    has_subscription: bool
    subscription_id: UUID | None = None
    subscription_status: str | None = None
    amount_due_paise: int = 0
    currency: str = "INR"
    period_start: date | None = None
    period_end: date | None = None
    is_overdue: bool = False
    open_payment_intent_id: UUID | None = None
    message: str
