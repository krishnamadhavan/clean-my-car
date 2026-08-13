"""Consumer wash summary/history + schedule materialisation (Module 10)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pricing_math import count_service_days, days_in_month, pro_rate_interior_entitlement
from app.models.society import Society
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.wash import Wash, WashStatus
from app.schemas.location import WEEKDAY_LABELS
from app.schemas.schedule import (
    ScheduleOccurrenceKind,
    ScheduleOccurrenceOut,
    ScheduleOut,
)
from app.schemas.wash import WashListOut, WashOut, WashSummaryOut
from app.services.subscription import SubscriptionService

INDIA_TZ = ZoneInfo("Asia/Kolkata")

_OPEN_SUB = {
    SubscriptionStatus.pending_payment,
    SubscriptionStatus.active,
    SubscriptionStatus.cancel_scheduled,
}

_OPEN_WASH = {WashStatus.scheduled, WashStatus.retry_scheduled}


class WashService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subscriptions = SubscriptionService(session)

    async def summary(self, user: User) -> WashSummaryOut:
        today = datetime.now(INDIA_TZ).date()
        year_month = f"{today.year:04d}-{today.month:02d}"
        sub = await self.subscriptions._get_open(user.id)
        if sub is None or sub.status not in _OPEN_SUB:
            return WashSummaryOut(
                year_month=year_month,
                exterior_entitled=0,
                exterior_completed=0,
                exterior_pending=0,
                exterior_missed=0,
                interior_included=0,
                interior_completed=0,
                message="No active subscription.",
            )

        await self.ensure_generated(sub)
        month_start = date(today.year, today.month, 1)
        month_end = date(today.year, today.month, days_in_month(today.year, today.month))
        period_start = max(sub.period_start, month_start)
        period_end = min(sub.period_end, month_end)
        if sub.cancel_at is not None:
            period_end = min(period_end, sub.cancel_at)

        society = sub.society
        weekdays = list(society.service_weekdays or []) if society else []
        exterior_entitled = count_service_days(
            period_start, service_weekdays=weekdays, end=period_end
        )
        interior_included = pro_rate_interior_entitlement(
            sub.interior_frequency, period_start if period_start.day > 1 else month_start
        )
        if period_start.day == 1 and period_end == month_end:
            interior_included = sub.interior_frequency

        rows = (
            (
                await self.session.execute(
                    select(Wash).where(
                        Wash.user_id == user.id,
                        Wash.service_date >= month_start,
                        Wash.service_date <= month_end,
                    )
                )
            )
            .scalars()
            .all()
        )

        exterior_completed = sum(
            1 for w in rows if w.status == WashStatus.completed and w.includes_exterior
        )
        exterior_missed = sum(1 for w in rows if w.status == WashStatus.missed)
        exterior_pending = sum(1 for w in rows if w.status in _OPEN_WASH and w.includes_exterior)
        interior_completed = sum(
            1 for w in rows if w.status == WashStatus.completed and w.includes_interior
        )

        return WashSummaryOut(
            year_month=year_month,
            exterior_entitled=exterior_entitled,
            exterior_completed=exterior_completed,
            exterior_pending=exterior_pending,
            exterior_missed=exterior_missed,
            interior_included=interior_included,
            interior_completed=interior_completed,
            subscription_id=sub.id,
            subscription_status=sub.status.value,
        )

    async def list_washes(
        self,
        user: User,
        *,
        month: str | None = None,
        status: WashStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> WashListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        q = select(Wash).where(Wash.user_id == user.id)
        count_q = select(func.count()).select_from(Wash).where(Wash.user_id == user.id)

        if month:
            year, mon = _parse_year_month(month)
            start = date(year, mon, 1)
            end = date(year, mon, days_in_month(year, mon))
            q = q.where(Wash.service_date >= start, Wash.service_date <= end)
            count_q = count_q.where(Wash.service_date >= start, Wash.service_date <= end)
        if status is not None:
            q = q.where(Wash.status == status)
            count_q = count_q.where(Wash.status == status)

        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (
            (
                await self.session.execute(
                    q.order_by(Wash.service_date.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return WashListOut(
            items=[WashOut.model_validate(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_wash(self, user: User, wash_id: UUID) -> WashOut:
        wash = await self.session.get(Wash, wash_id)
        if wash is None or wash.user_id != user.id:
            raise NotFoundError("Wash not found", code="wash_not_found")
        return WashOut.model_validate(wash)

    async def upcoming_schedule(self, user: User, *, days: int | None = None) -> ScheduleOut:
        """WASH-04 — prefer materialised washes; fall back to projection."""
        today = datetime.now(INDIA_TZ).date()
        sub = await self.subscriptions._get_open(user.id)
        if sub is None or sub.status not in _OPEN_SUB:
            until = today + timedelta(days=30)
            return ScheduleOut(
                items=[],
                from_date=today,
                until_date=until,
                message="Subscribe to see your upcoming wash schedule.",
            )

        await self.ensure_generated(sub)
        if sub.society is None:
            loaded = await self.subscriptions._load(sub.id)
            sub = loaded or sub
        society = sub.society
        weekdays = list(society.service_weekdays or []) if society else []
        labels = [WEEKDAY_LABELS[d] for d in weekdays if 0 <= d <= 6]

        period_end = sub.period_end
        if sub.cancel_at is not None:
            period_end = min(period_end, sub.cancel_at)
        if days is not None:
            until = min(period_end, today + timedelta(days=max(1, min(days, 62)) - 1))
        else:
            until = period_end

        if until < today:
            return ScheduleOut(
                items=[],
                service_weekdays=weekdays,
                service_weekday_labels=labels,
                subscription_id=sub.id,
                subscription_status=sub.status.value,
                from_date=today,
                until_date=until,
                message="No more service days in the current period.",
            )

        rows = (
            (
                await self.session.execute(
                    select(Wash)
                    .where(
                        Wash.user_id == user.id,
                        Wash.service_date >= today,
                        Wash.service_date <= until,
                        Wash.status.in_(_OPEN_WASH),
                    )
                    .order_by(Wash.service_date.asc())
                )
            )
            .scalars()
            .all()
        )

        items: list[ScheduleOccurrenceOut] = []
        for w in rows:
            kind = (
                ScheduleOccurrenceKind.retry_scheduled
                if w.status == WashStatus.retry_scheduled
                else ScheduleOccurrenceKind.scheduled
            )
            title = (
                "Retry wash" if kind == ScheduleOccurrenceKind.retry_scheduled else "Exterior wash"
            )
            if w.includes_interior:
                title = f"{title} + interior"
            items.append(
                ScheduleOccurrenceOut(
                    date=w.service_date,
                    weekday=w.service_date.weekday(),
                    weekday_label=WEEKDAY_LABELS[w.service_date.weekday()],
                    kind=kind,
                    title=title,
                    note=w.notes,
                    society_id=w.society_id,
                    society_name=society.name if society else None,
                )
            )

        message = None
        if not items:
            message = "No service days remaining in this period."

        return ScheduleOut(
            items=items,
            service_weekdays=weekdays,
            service_weekday_labels=labels,
            subscription_id=sub.id,
            subscription_status=sub.status.value,
            from_date=today,
            until_date=until,
            message=message,
        )

    async def ensure_generated(self, sub: Subscription) -> int:
        """Create scheduled wash rows for service days in the subscription period."""
        if sub.status not in _OPEN_SUB:
            return 0
        society = sub.society
        if society is None:
            society = await self.session.get(Society, sub.society_id)
        if society is None:
            return 0
        weekdays = list(society.service_weekdays or [])
        if not weekdays:
            return 0

        period_end = sub.period_end
        if sub.cancel_at is not None:
            period_end = min(period_end, sub.cancel_at)

        existing_dates = set(
            (
                await self.session.execute(
                    select(Wash.service_date).where(
                        Wash.user_id == sub.user_id,
                        Wash.service_date >= sub.period_start,
                        Wash.service_date <= period_end,
                    )
                )
            )
            .scalars()
            .all()
        )

        created = 0
        cursor = sub.period_start
        while cursor <= period_end:
            if cursor.weekday() in weekdays and cursor not in existing_dates:
                self.session.add(
                    Wash(
                        user_id=sub.user_id,
                        subscription_id=sub.id,
                        society_id=sub.society_id,
                        vehicle_id=sub.vehicle_id,
                        service_date=cursor,
                        status=WashStatus.scheduled,
                        includes_exterior=True,
                        includes_interior=False,
                    )
                )
                created += 1
            cursor += timedelta(days=1)

        if created:
            await self.session.commit()
        return created


def _parse_year_month(value: str) -> tuple[int, int]:
    parts = value.strip().split("-")
    if len(parts) != 2:
        raise ValueError("month must be YYYY-MM")
    year = int(parts[0])
    mon = int(parts[1])
    if mon < 1 or mon > 12:
        raise ValueError("month must be 1–12")
    return year, mon
