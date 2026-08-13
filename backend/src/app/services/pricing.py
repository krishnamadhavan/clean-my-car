"""Pricing catalog and quote service (Module 6)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, NotFoundError
from app.core.pricing_math import (
    count_service_days,
    days_in_month,
    pro_rate_amount_paise,
    pro_rate_interior_entitlement,
    remaining_days_in_month,
    split_gst_paise,
)
from app.models.city import City
from app.models.pricing import CityPricing
from app.models.society import Society
from app.models.vehicle import VehicleSizeTier
from app.schemas.location import WEEKDAY_LABELS, CityOut, SocietySummaryOut
from app.schemas.pricing import (
    INTERIOR_FREQUENCIES,
    CityPricingOut,
    InteriorOptionOut,
    InteriorOptionsOut,
    InteriorPriceOut,
    MoneyBreakdownOut,
    PricingMatrixCellOut,
    QuoteIn,
    QuoteOut,
    SizePriceOut,
)

INDIA_TZ = ZoneInfo("Asia/Kolkata")

INTERIOR_OPTION_META: dict[int, tuple[str, str, str]] = {
    0: ("none", "None", "Exterior-only subscription"),
    1: ("once", "1× / month", "One interior clean per calendar month"),
    2: ("twice", "2× / month", "Two interior cleans per calendar month"),
    4: ("four", "4× / month", "Four interior cleans per calendar month"),
}


class PricingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def interior_options() -> InteriorOptionsOut:
        items = [
            InteriorOptionOut(
                frequency=freq,
                code=meta[0],
                label=meta[1],
                description=meta[2],
            )
            for freq, meta in INTERIOR_OPTION_META.items()
        ]
        return InteriorOptionsOut(items=items)

    async def get_city_pricing(self, city_id: UUID) -> CityPricingOut:
        city, pricing = await self._require_active_city_pricing(city_id)
        size_map = {row.size_tier: row.monthly_amount_paise for row in pricing.size_prices}
        interior_map = {
            row.interior_frequency: row.monthly_amount_paise for row in pricing.interior_prices
        }
        # Ensure frequency 0 is present as 0 if missing
        if 0 not in interior_map:
            interior_map[0] = 0

        size_prices = [
            SizePriceOut(size_tier=tier, monthly_amount_paise=size_map[tier])
            for tier in VehicleSizeTier
            if tier in size_map
        ]
        interior_prices = [
            InteriorPriceOut(interior_frequency=freq, monthly_amount_paise=interior_map[freq])
            for freq in INTERIOR_FREQUENCIES
            if freq in interior_map
        ]

        matrix: list[PricingMatrixCellOut] = []
        for tier in VehicleSizeTier:
            if tier not in size_map:
                continue
            base = size_map[tier]
            for freq in INTERIOR_FREQUENCIES:
                interior = interior_map.get(freq, 0 if freq == 0 else None)
                if interior is None:
                    continue
                matrix.append(
                    PricingMatrixCellOut(
                        size_tier=tier,
                        interior_frequency=freq,
                        base_amount_paise=base,
                        interior_amount_paise=interior,
                        monthly_total_paise=base + interior,
                    )
                )

        return CityPricingOut(
            city=CityOut.model_validate(city),
            currency=pricing.currency,
            amounts_include_gst=pricing.amounts_include_gst,
            gst_rate_bps=pricing.gst_rate_bps,
            size_prices=size_prices,
            interior_prices=interior_prices,
            matrix=matrix,
        )

    async def quote(self, data: QuoteIn) -> QuoteOut:
        city, pricing = await self._require_active_city_pricing(data.city_id)

        size_row = next(
            (r for r in pricing.size_prices if r.size_tier == data.size_tier),
            None,
        )
        if size_row is None:
            raise AppError(
                "No base price for this size in the city",
                code="size_price_missing",
                status_code=400,
            )

        if data.interior_frequency == 0:
            interior_amount = 0
        else:
            interior_row = next(
                (
                    r
                    for r in pricing.interior_prices
                    if r.interior_frequency == data.interior_frequency
                ),
                None,
            )
            if interior_row is None:
                raise AppError(
                    "No interior price for this frequency in the city",
                    code="interior_price_missing",
                    status_code=400,
                )
            interior_amount = interior_row.monthly_amount_paise

        base_amount = size_row.monthly_amount_paise
        full_monthly = base_amount + interior_amount

        start = data.start_date or datetime.now(INDIA_TZ).date()

        dim = days_in_month(start.year, start.month)
        remaining = remaining_days_in_month(start)
        due_now = pro_rate_amount_paise(full_monthly, start)
        is_prorated = remaining < dim

        full_breakdown = self._money(full_monthly, pricing)
        due_breakdown = self._money(due_now, pricing)

        # Next calendar month label
        if start.month == 12:
            next_month = date(start.year + 1, 1, 1)
        else:
            next_month = date(start.year, start.month + 1, 1)
        next_billing_month = f"{next_month.year:04d}-{next_month.month:02d}"
        billing_month = f"{start.year:04d}-{start.month:02d}"

        society_out: SocietySummaryOut | None = None
        weekdays: list[int] | None = None
        labels: list[str] | None = None
        exterior_period: int | None = None
        exterior_full: int | None = None

        if data.society_id is not None:
            society = await self._require_live_society(data.society_id, city_id=city.id)
            society_out = SocietySummaryOut.from_society(society)
            weekdays = [d for d in (society.service_weekdays or []) if 0 <= d <= 5]
            labels = [WEEKDAY_LABELS[d] for d in weekdays]
            month_start = date(start.year, start.month, 1)
            month_end = date(start.year, start.month, dim)
            exterior_full = count_service_days(
                month_start, service_weekdays=weekdays, end=month_end
            )
            exterior_period = count_service_days(start, service_weekdays=weekdays, end=month_end)

        interior_full = data.interior_frequency
        interior_period = pro_rate_interior_entitlement(data.interior_frequency, start)

        return QuoteOut(
            city=CityOut.model_validate(city),
            size_tier=data.size_tier,
            interior_frequency=data.interior_frequency,
            currency=pricing.currency,
            amounts_include_gst=pricing.amounts_include_gst,
            gst_rate_bps=pricing.gst_rate_bps,
            full_monthly_base_paise=base_amount,
            full_monthly_interior_paise=interior_amount,
            full_monthly_total_paise=full_monthly,
            full_monthly_breakdown=full_breakdown,
            start_date=start,
            billing_month=billing_month,
            days_in_month=dim,
            remaining_days=remaining,
            amount_due_now_paise=due_now,
            amount_due_now_breakdown=due_breakdown,
            is_prorated=is_prorated,
            next_billing_month=next_billing_month,
            next_full_month_amount_paise=full_monthly,
            exterior_entitled_this_period=exterior_period,
            exterior_entitled_full_month=exterior_full,
            interior_entitled_this_period=interior_period,
            interior_entitled_full_month=interior_full,
            society=society_out,
            service_weekdays=weekdays,
            service_weekday_labels=labels,
            pro_rate_method="calendar_days",
        )

    @staticmethod
    def _money(amount_paise: int, pricing: CityPricing) -> MoneyBreakdownOut:
        base, gst, total = split_gst_paise(
            amount_paise,
            include_gst=pricing.amounts_include_gst,
            gst_rate_bps=pricing.gst_rate_bps,
        )
        return MoneyBreakdownOut(base_amount_paise=base, gst_paise=gst, total_paise=total)

    async def _require_active_city_pricing(self, city_id: UUID) -> tuple[City, CityPricing]:
        city = await self.session.get(City, city_id)
        if city is None or not city.is_active:
            raise NotFoundError("City not found", code="city_not_found")

        result = await self.session.execute(
            select(CityPricing)
            .options(
                selectinload(CityPricing.size_prices),
                selectinload(CityPricing.interior_prices),
            )
            .where(
                CityPricing.city_id == city_id,
                CityPricing.is_active.is_(True),
            )
            .limit(1)
        )
        pricing = result.scalar_one_or_none()
        if pricing is None:
            raise NotFoundError(
                "Pricing not available for this city",
                code="pricing_not_found",
            )
        return city, pricing

    async def _require_live_society(self, society_id: UUID, *, city_id: UUID) -> Society:
        result = await self.session.execute(
            select(Society).where(Society.id == society_id).limit(1)
        )
        society = result.scalar_one_or_none()
        if society is None or not society.is_serviceable:
            raise AppError(
                "Society is not serviceable",
                code="society_not_serviceable",
                status_code=400,
            )
        if society.city_id != city_id:
            raise AppError(
                "Society does not belong to the selected city",
                code="society_city_mismatch",
                status_code=400,
            )
        return society
