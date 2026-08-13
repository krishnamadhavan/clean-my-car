"""Ops overview aggregates (OPS-DASH-01)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.society import Society
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.waitlist import WaitlistEntry, WaitlistStatus
from app.models.wash import Wash, WashStatus
from app.schemas.ops_dashboard import OpsOverviewOut

INDIA_TZ = ZoneInfo("Asia/Kolkata")


class OpsDashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def overview(self) -> OpsOverviewOut:
        today = datetime.now(INDIA_TZ).date()
        cities_total = int(
            (await self.session.execute(select(func.count()).select_from(City))).scalar_one()
        )
        cities_active = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(City).where(City.is_active.is_(True))
                )
            ).scalar_one()
        )
        societies_live = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(Society)
                    .where(Society.is_serviceable.is_(True))
                )
            ).scalar_one()
        )
        waitlist_open = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(WaitlistEntry)
                    .where(
                        WaitlistEntry.status.in_([WaitlistStatus.pending, WaitlistStatus.contacted])
                    )
                )
            ).scalar_one()
        )
        subs_active = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(Subscription)
                    .where(
                        Subscription.status.in_(
                            [
                                SubscriptionStatus.active,
                                SubscriptionStatus.cancel_scheduled,
                            ]
                        )
                    )
                )
            ).scalar_one()
        )
        subs_pending = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(Subscription)
                    .where(Subscription.status == SubscriptionStatus.pending_payment)
                )
            ).scalar_one()
        )
        washes_scheduled = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(Wash)
                    .where(
                        Wash.service_date == today,
                        Wash.status.in_([WashStatus.scheduled, WashStatus.retry_scheduled]),
                    )
                )
            ).scalar_one()
        )
        washes_completed = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(Wash)
                    .where(
                        Wash.service_date == today,
                        Wash.status == WashStatus.completed,
                    )
                )
            ).scalar_one()
        )
        return OpsOverviewOut(
            cities_total=cities_total,
            cities_active=cities_active,
            societies_live=societies_live,
            waitlist_open=waitlist_open,
            subscriptions_active=subs_active,
            subscriptions_pending_payment=subs_pending,
            washes_scheduled_today=washes_scheduled,
            washes_completed_today=washes_completed,
        )
