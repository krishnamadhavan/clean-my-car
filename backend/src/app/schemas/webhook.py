"""Payment webhook schemas (Module 14)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentWebhookIn(BaseModel):
    """Generic gateway event payload (provider-specific mapping later)."""

    model_config = ConfigDict(extra="allow")

    event: str = Field(description="captured | failed | refunded")
    payment_id: UUID | None = None
    provider_ref: str | None = Field(default=None, max_length=120)
    failure_reason: str | None = Field(default=None, max_length=500)
    amount_paise: int | None = None


class PaymentWebhookOut(BaseModel):
    accepted: bool
    payment_id: UUID | None = None
    status: str | None = None
    message: str
    processed_at: datetime
