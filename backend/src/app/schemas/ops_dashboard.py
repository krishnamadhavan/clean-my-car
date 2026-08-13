"""Ops overview dashboard (OPS-DASH-01)."""

from __future__ import annotations

from pydantic import BaseModel


class OpsOverviewOut(BaseModel):
    cities_total: int
    cities_active: int
    societies_live: int
    waitlist_open: int
    subscriptions_active: int
    subscriptions_pending_payment: int
    washes_scheduled_today: int
    washes_completed_today: int
