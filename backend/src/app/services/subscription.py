"""Consumer subscription lifecycle (Module 7)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, NotFoundError
from app.models.payment import Payment, PaymentKind, PaymentStatus
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.location import CityOut, SocietySummaryOut
from app.schemas.pricing import QuoteIn
from app.schemas.subscription import (
    SubscriptionOut,
    SubscriptionStartIn,
    SubscriptionStartOut,
)
from app.services.ops_subscription import month_end
from app.services.pricing import PricingService

INDIA_TZ = ZoneInfo("Asia/Kolkata")

_OPEN_STATUSES = {
    SubscriptionStatus.pending_payment,
    SubscriptionStatus.active,
    SubscriptionStatus.cancel_scheduled,
    SubscriptionStatus.paused,
}


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pricing = PricingService(session)

    async def get_current(self, user: User) -> SubscriptionOut:
        sub = await self._get_open(user.id)
        if sub is None:
            raise NotFoundError("No subscription", code="subscription_not_found")
        return self._to_out(sub)

    async def start(self, user: User, body: SubscriptionStartIn) -> SubscriptionStartOut:
        if await self._get_open(user.id) is not None:
            raise AppError(
                "You already have an open subscription",
                code="subscription_exists",
                status_code=409,
            )
        if user.city_id is None or user.society_id is None:
            raise AppError(
                "Set your city and society before subscribing",
                code="location_required",
                status_code=400,
            )

        vehicle = await self._require_vehicle(user)
        start = body.start_date or datetime.now(INDIA_TZ).date()
        quote = await self.pricing.quote(
            QuoteIn(
                city_id=user.city_id,
                size_tier=vehicle.size_tier,
                interior_frequency=body.interior_frequency,
                start_date=start,
                society_id=user.society_id,
            )
        )

        period_start = start
        period_end = month_end(start)
        sub = Subscription(
            user_id=user.id,
            city_id=user.city_id,
            society_id=user.society_id,
            vehicle_id=vehicle.id,
            size_tier=vehicle.size_tier,
            interior_frequency=body.interior_frequency,
            status=SubscriptionStatus.pending_payment,
            monthly_amount_paise=quote.full_monthly_total_paise,
            currency=quote.currency,
            period_start=period_start,
            period_end=period_end,
        )
        self.session.add(sub)
        await self.session.flush()

        payment = Payment(
            user_id=user.id,
            subscription_id=sub.id,
            amount_paise=quote.amount_due_now_paise,
            currency=quote.currency,
            status=PaymentStatus.pending,
            kind=PaymentKind.subscription_start,
            period_start=period_start,
            period_end=period_end,
            provider="manual",
        )
        self.session.add(payment)
        await self.session.commit()

        sub = await self._load(sub.id)
        assert sub is not None
        return SubscriptionStartOut(
            subscription=self._to_out(sub),
            payment_intent_id=payment.id,
            amount_due_now_paise=quote.amount_due_now_paise,
            currency=quote.currency,
            quote=quote,
        )

    async def cancel(self, user: User) -> SubscriptionOut:
        sub = await self._get_open(user.id)
        if sub is None:
            raise NotFoundError("No subscription", code="subscription_not_found")
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

        sub.status = SubscriptionStatus.cancel_scheduled
        sub.cancel_at = sub.period_end
        await self.session.commit()
        loaded = await self._load(sub.id)
        assert loaded is not None
        return self._to_out(loaded)

    async def undo_cancel(self, user: User) -> SubscriptionOut:
        sub = await self._get_open(user.id)
        if sub is None:
            raise NotFoundError("No subscription", code="subscription_not_found")
        if sub.status != SubscriptionStatus.cancel_scheduled:
            raise AppError(
                "No scheduled cancellation to undo",
                code="cancel_not_scheduled",
                status_code=409,
            )
        # Paid / active period still covers service
        sub.status = SubscriptionStatus.active
        sub.cancel_at = None
        await self.session.commit()
        loaded = await self._load(sub.id)
        assert loaded is not None
        return self._to_out(loaded)

    async def _get_open(self, user_id: UUID) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.city),
                selectinload(Subscription.society),
            )
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_(_OPEN_STATUSES),
            )
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _load(self, subscription_id: UUID) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.city),
                selectinload(Subscription.society),
            )
            .where(Subscription.id == subscription_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _require_vehicle(self, user: User) -> Vehicle:
        result = await self.session.execute(
            select(Vehicle).where(Vehicle.user_id == user.id).limit(1)
        )
        vehicle = result.scalar_one_or_none()
        if vehicle is None:
            raise AppError(
                "Add a vehicle before subscribing",
                code="vehicle_required",
                status_code=400,
            )
        return vehicle

    @staticmethod
    def _to_out(sub: Subscription) -> SubscriptionOut:
        city = CityOut.model_validate(sub.city) if sub.city is not None else None
        society = SocietySummaryOut.from_society(sub.society) if sub.society is not None else None
        return SubscriptionOut(
            id=sub.id,
            status=sub.status,
            city_id=sub.city_id,
            society_id=sub.society_id,
            vehicle_id=sub.vehicle_id,
            size_tier=sub.size_tier,
            interior_frequency=sub.interior_frequency,
            monthly_amount_paise=sub.monthly_amount_paise,
            currency=sub.currency,
            period_start=sub.period_start,
            period_end=sub.period_end,
            cancel_at=sub.cancel_at,
            paused_from=sub.paused_from,
            paused_until=sub.paused_until,
            city=city,
            society=society,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )
