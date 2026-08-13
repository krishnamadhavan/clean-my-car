"""Consumer home dashboard aggregate (DASH-01)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.city import City
from app.models.society import Society
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleModel
from app.models.wash import Wash, WashStatus
from app.schemas.dashboard import DashboardNextServiceOut, DashboardOut
from app.schemas.location import WEEKDAY_LABELS, CityOut, SocietySummaryOut
from app.schemas.vehicle import VehicleMakeOut, VehicleModelOut, VehicleOut
from app.services.payment import PaymentService
from app.services.subscription import SubscriptionService
from app.services.wash import WashService

INDIA_TZ = ZoneInfo("Asia/Kolkata")


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subscriptions = SubscriptionService(session)
        self.washes = WashService(session)
        self.payments = PaymentService(session)

    async def get_dashboard(self, user: User) -> DashboardOut:
        sub = await self.subscriptions._get_open(user.id)
        vehicle = await self._get_vehicle(user)
        billing = await self.payments.billing_summary(user)

        if sub is None:
            city_out = None
            society_out = None
            weekdays: list[int] = []
            if user.city_id:
                c = await self.session.get(City, user.city_id)
                if c is not None:
                    city_out = CityOut.model_validate(c)
                if user.society_id:
                    s = await self.session.get(Society, user.society_id)
                    if s is not None:
                        society_out = SocietySummaryOut.from_society(s)
                        weekdays = [d for d in (s.service_weekdays or []) if 0 <= d <= 5]
            return DashboardOut(
                has_subscription=False,
                vehicle=vehicle,
                city=city_out,
                society=society_out,
                service_weekdays=weekdays,
                service_weekday_labels=[WEEKDAY_LABELS[d] for d in weekdays],
                amount_due_paise=billing.amount_due_paise,
                currency=billing.currency,
                billing_message=billing.message,
                message="Subscribe to start service and see wash progress.",
            )

        await self.washes.ensure_generated(sub)
        if sub.society is None or sub.city is None:
            loaded = await self.subscriptions._load(sub.id)
            if loaded is not None:
                sub = loaded

        weekdays = (
            [d for d in (sub.society.service_weekdays or []) if 0 <= d <= 5] if sub.society else []
        )
        summary = await self.washes.summary(user)
        next_service = await self._next_service(user.id)
        sub_out = self.subscriptions._to_out(sub)

        return DashboardOut(
            has_subscription=True,
            subscription=sub_out,
            vehicle=vehicle,
            city=CityOut.model_validate(sub.city) if sub.city else None,
            society=SocietySummaryOut.from_society(sub.society) if sub.society else None,
            service_weekdays=weekdays,
            service_weekday_labels=[WEEKDAY_LABELS[d] for d in weekdays],
            wash_summary=summary,
            next_service=next_service,
            amount_due_paise=billing.amount_due_paise,
            currency=billing.currency,
            billing_message=billing.message,
        )

    async def _next_service(self, user_id) -> DashboardNextServiceOut | None:
        today = datetime.now(INDIA_TZ).date()
        wash = (
            await self.session.execute(
                select(Wash)
                .where(
                    Wash.user_id == user_id,
                    Wash.service_date >= today,
                    Wash.status.in_({WashStatus.scheduled, WashStatus.retry_scheduled}),
                )
                .order_by(Wash.service_date.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if wash is None:
            return None
        is_retry = wash.status == WashStatus.retry_scheduled
        return DashboardNextServiceOut(
            date=wash.service_date,
            kind=wash.status.value,
            title="Retry wash" if is_retry else "Exterior wash",
            is_retry=is_retry,
            wash_id=wash.id,
        )

    async def _get_vehicle(self, user: User) -> VehicleOut | None:
        result = await self.session.execute(
            select(Vehicle)
            .options(selectinload(Vehicle.model).selectinload(VehicleModel.make))
            .where(Vehicle.user_id == user.id)
            .limit(1)
        )
        vehicle = result.scalar_one_or_none()
        if vehicle is None:
            return None
        make = None
        model_out = None
        if vehicle.model is not None:
            model_out = VehicleModelOut.model_validate(vehicle.model)
            if vehicle.model.make is not None:
                make = VehicleMakeOut.model_validate(vehicle.model.make)
        return VehicleOut(
            id=vehicle.id,
            model_id=vehicle.model_id,
            make=make,
            model=model_out,
            size_tier=vehicle.size_tier,
            nickname=vehicle.nickname,
            plate_number=vehicle.plate_number,
            colour=vehicle.colour,
            parking_slot=vehicle.parking_slot,
            parking_tower=vehicle.parking_tower,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
        )
