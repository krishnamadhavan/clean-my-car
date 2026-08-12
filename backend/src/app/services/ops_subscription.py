"""Ops subscription support service (Module 7)."""

from __future__ import annotations

import calendar
from datetime import date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, NotFoundError
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.location import CityOut, SocietySummaryOut
from app.schemas.ops_subscription import (
    OpsSubscriptionCancelIn,
    OpsSubscriptionListOut,
    OpsSubscriptionOut,
    OpsSubscriptionUserOut,
)


class OpsSubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_subscriptions(
        self,
        *,
        q: str | None = None,
        status: SubscriptionStatus | None = None,
        society_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OpsSubscriptionListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        filters: list = []
        if status is not None:
            filters.append(Subscription.status == status)
        if society_id is not None:
            filters.append(Subscription.society_id == society_id)
        if q and q.strip():
            term = q.strip()
            user_match = or_(
                User.phone.ilike(f"%{term}%"),
                User.name.ilike(f"%{term}%"),
                User.email.ilike(f"%{term}%"),
            )
            id_filters: list = [
                Subscription.user_id.in_(select(User.id).where(user_match)),
            ]
            try:
                as_uuid = UUID(term)
                id_filters.extend(
                    [
                        Subscription.id == as_uuid,
                        Subscription.user_id == as_uuid,
                    ]
                )
            except ValueError:
                pass
            filters.append(or_(*id_filters))

        count_q = select(func.count()).select_from(Subscription)
        list_q = (
            select(Subscription)
            .options(
                selectinload(Subscription.user),
                selectinload(Subscription.city),
                selectinload(Subscription.society),
            )
            .order_by(Subscription.created_at.desc())
        )
        if filters:
            count_q = count_q.where(*filters)
            list_q = list_q.where(*filters)

        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (await self.session.execute(list_q.offset(offset).limit(page_size))).scalars().all()
        return OpsSubscriptionListOut(
            items=[self._to_out(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_subscription(self, subscription_id: UUID) -> OpsSubscriptionOut:
        sub = await self._get(subscription_id)
        return self._to_out(sub)

    async def admin_cancel(
        self,
        subscription_id: UUID,
        body: OpsSubscriptionCancelIn | None = None,
    ) -> OpsSubscriptionOut:
        """Schedule cancel at end of current calendar period (OPS-SUB-03)."""
        sub = await self._get(subscription_id)
        if sub.status in {
            SubscriptionStatus.expired,
            SubscriptionStatus.inactive,
        }:
            raise AppError(
                "Subscription is already ended",
                code="subscription_already_ended",
                status_code=409,
            )
        if sub.status == SubscriptionStatus.cancel_scheduled:
            return self._to_out(sub)

        # Service continues through period_end (calendar month end policy)
        sub.status = SubscriptionStatus.cancel_scheduled
        sub.cancel_at = sub.period_end
        if body and body.notes:
            note = body.notes.strip()
            if note:
                existing = (sub.notes or "").strip()
                sub.notes = (
                    f"{existing}\n[ops cancel] {note}".strip()
                    if existing
                    else f"[ops cancel] {note}"
                )

        await self.session.commit()
        return await self.get_subscription(subscription_id)

    async def _get(self, subscription_id: UUID) -> Subscription:
        result = await self.session.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.user),
                selectinload(Subscription.city),
                selectinload(Subscription.society),
            )
            .where(Subscription.id == subscription_id)
            .limit(1)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            raise NotFoundError("Subscription not found", code="subscription_not_found")
        return sub

    @staticmethod
    def _to_out(sub: Subscription) -> OpsSubscriptionOut:
        user_out = None
        if sub.user is not None:
            user_out = OpsSubscriptionUserOut.model_validate(sub.user)
        city_out = CityOut.model_validate(sub.city) if sub.city is not None else None
        society_out = (
            SocietySummaryOut.from_society(sub.society) if sub.society is not None else None
        )
        return OpsSubscriptionOut(
            id=sub.id,
            user_id=sub.user_id,
            user=user_out,
            city_id=sub.city_id,
            city=city_out,
            society_id=sub.society_id,
            society=society_out,
            vehicle_id=sub.vehicle_id,
            size_tier=sub.size_tier,
            interior_frequency=sub.interior_frequency,
            status=sub.status,
            monthly_amount_paise=sub.monthly_amount_paise,
            currency=sub.currency,
            period_start=sub.period_start,
            period_end=sub.period_end,
            cancel_at=sub.cancel_at,
            paused_from=sub.paused_from,
            paused_until=sub.paused_until,
            notes=sub.notes,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )


def month_end(d: date) -> date:
    last = calendar.monthrange(d.year, d.month)[1]
    return date(d.year, d.month, last)
