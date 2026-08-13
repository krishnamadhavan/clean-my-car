"""Upcoming wash schedule for the consumer (WASH-04).

Until wash rows / ops complete-miss land, the schedule is projected from the
user's open subscription + society service weekdays (0=Mon … 6=Sun).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import SubscriptionStatus
from app.models.user import User
from app.schemas.location import WEEKDAY_LABELS
from app.schemas.schedule import (
    ScheduleOccurrenceKind,
    ScheduleOccurrenceOut,
    ScheduleOut,
)
from app.services.subscription import SubscriptionService

INDIA_TZ = ZoneInfo("Asia/Kolkata")

# Service is considered scheduled once the plan exists (including pending pay).
_SCHEDULE_STATUSES = {
    SubscriptionStatus.pending_payment,
    SubscriptionStatus.active,
    SubscriptionStatus.cancel_scheduled,
}


class ScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subscriptions = SubscriptionService(session)

    async def upcoming(
        self,
        user: User,
        *,
        days: int | None = None,
    ) -> ScheduleOut:
        """List only days that have a planned exterior wash.

        ``days`` caps the window from today (1–62). Default: through the
        current subscription period end, or 31 days when unsubscribed.
        """
        today = datetime.now(INDIA_TZ).date()
        sub = await self.subscriptions._get_open(user.id)

        if sub is None or sub.status not in _SCHEDULE_STATUSES:
            until = today + timedelta(days=30)
            return ScheduleOut(
                items=[],
                from_date=today,
                until_date=until,
                message="Subscribe to see your upcoming wash schedule.",
            )

        # Ensure society is loaded for weekdays + name
        if sub.society is None:
            loaded = await self.subscriptions._load(sub.id)
            sub = loaded or sub

        society = sub.society
        weekdays = list(society.service_weekdays or []) if society is not None else []
        labels = [WEEKDAY_LABELS[d] for d in weekdays if 0 <= d <= 6]

        period_end = sub.period_end
        if sub.status == SubscriptionStatus.cancel_scheduled and sub.cancel_at is not None:
            period_end = min(period_end, sub.cancel_at)

        if days is not None:
            window_end = today + timedelta(days=max(1, min(days, 62)) - 1)
            until = min(period_end, window_end)
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

        items: list[ScheduleOccurrenceOut] = []
        if weekdays:
            society_id = society.id if society is not None else None
            society_name = society.name if society is not None else None
            cursor = today
            while cursor <= until:
                # Python: Monday=0 … Sunday=6 — matches product convention
                wd = cursor.weekday()
                if wd in weekdays:
                    items.append(
                        ScheduleOccurrenceOut(
                            date=cursor,
                            weekday=wd,
                            weekday_label=WEEKDAY_LABELS[wd],
                            kind=ScheduleOccurrenceKind.scheduled,
                            title="Exterior wash",
                            note=None,
                            society_id=society_id,
                            society_name=society_name,
                        )
                    )
                cursor += timedelta(days=1)

        message = None
        if not weekdays:
            message = "Your society has no service days configured."
        elif not items:
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
