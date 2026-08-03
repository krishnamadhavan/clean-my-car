"""Ops pricing catalog service (Ops Module 6)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.city import City
from app.models.pricing import CityInteriorPrice, CityPricing, CitySizePrice
from app.models.vehicle import VehicleSizeTier
from app.schemas.ops_location import OpsCityOut
from app.schemas.ops_pricing import (
    OpsCityPricingOut,
    OpsCityPricingPut,
    OpsInteriorPriceOut,
    OpsInteriorPricesPut,
    OpsMissingPricingListOut,
    OpsMissingPricingOut,
    OpsSizePriceOut,
    OpsSizePricesPut,
)
from app.schemas.pricing import INTERIOR_FREQUENCIES, PricingMatrixCellOut, QuoteIn, QuoteOut
from app.services.pricing import PricingService


class OpsPricingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_city_pricing(self, city_id: UUID) -> OpsCityPricingOut:
        city = await self._require_city(city_id)
        pricing = await self._get_pricing_row(city_id)
        if pricing is None:
            raise NotFoundError(
                "Pricing not configured for this city",
                code="pricing_not_found",
            )
        return self._to_out(city, pricing)

    async def put_city_pricing(self, city_id: UUID, data: OpsCityPricingPut) -> OpsCityPricingOut:
        city = await self._require_city(city_id)
        pricing = await self._get_pricing_row(city_id)
        if pricing is None:
            pricing = CityPricing(city_id=city_id)
            self.session.add(pricing)

        pricing.currency = data.currency
        pricing.amounts_include_gst = data.amounts_include_gst
        pricing.gst_rate_bps = data.gst_rate_bps
        pricing.is_active = data.is_active

        await self.session.commit()
        pricing = await self._get_pricing_row(city_id)
        assert pricing is not None
        return self._to_out(city, pricing)

    async def put_size_prices(self, city_id: UUID, data: OpsSizePricesPut) -> OpsCityPricingOut:
        city = await self._require_city(city_id)
        pricing = await self._require_pricing(city_id)

        # Full replace
        pricing.size_prices.clear()
        await self.session.flush()
        for item in data.items:
            pricing.size_prices.append(
                CitySizePrice(
                    size_tier=item.size_tier,
                    monthly_amount_paise=item.monthly_amount_paise,
                )
            )
        await self.session.commit()
        pricing = await self._get_pricing_row(city_id)
        assert pricing is not None
        return self._to_out(city, pricing)

    async def put_interior_prices(
        self, city_id: UUID, data: OpsInteriorPricesPut
    ) -> OpsCityPricingOut:
        city = await self._require_city(city_id)
        pricing = await self._require_pricing(city_id)

        pricing.interior_prices.clear()
        await self.session.flush()
        for item in data.items:
            pricing.interior_prices.append(
                CityInteriorPrice(
                    interior_frequency=item.interior_frequency,
                    monthly_amount_paise=item.monthly_amount_paise,
                )
            )
        await self.session.commit()
        pricing = await self._get_pricing_row(city_id)
        assert pricing is not None
        return self._to_out(city, pricing)

    async def quote(self, data: QuoteIn) -> QuoteOut:
        """Delegate to consumer quote engine (OPS-PRICE-05)."""
        return await PricingService(session=self.session).quote(data)

    async def list_missing(self) -> OpsMissingPricingListOut:
        """Active cities without an active pricing row (OPS-PRICE-06)."""
        result = await self.session.execute(
            select(City).where(City.is_active.is_(True)).order_by(City.display_order, City.name)
        )
        cities = list(result.scalars().all())
        if not cities:
            return OpsMissingPricingListOut(items=[], total=0)

        pricing_result = await self.session.execute(
            select(CityPricing).where(CityPricing.city_id.in_([c.id for c in cities]))
        )
        by_city: dict[UUID, list[CityPricing]] = {}
        for row in pricing_result.scalars().all():
            by_city.setdefault(row.city_id, []).append(row)

        missing: list[OpsMissingPricingOut] = []
        for city in cities:
            rows = by_city.get(city.id, [])
            has_active = any(r.is_active for r in rows)
            if has_active:
                continue
            missing.append(
                OpsMissingPricingOut(
                    city=OpsCityOut.model_validate(city),
                    has_inactive_pricing=bool(rows),
                )
            )
        return OpsMissingPricingListOut(items=missing, total=len(missing))

    async def _require_city(self, city_id: UUID) -> City:
        city = await self.session.get(City, city_id)
        if city is None:
            raise NotFoundError("City not found", code="city_not_found")
        return city

    async def _require_pricing(self, city_id: UUID) -> CityPricing:
        pricing = await self._get_pricing_row(city_id)
        if pricing is None:
            raise NotFoundError(
                "Pricing not configured for this city; create it first via PUT .../pricing",
                code="pricing_not_found",
            )
        return pricing

    async def _get_pricing_row(self, city_id: UUID) -> CityPricing | None:
        result = await self.session.execute(
            select(CityPricing)
            .options(
                selectinload(CityPricing.size_prices),
                selectinload(CityPricing.interior_prices),
            )
            .where(CityPricing.city_id == city_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_out(city: City, pricing: CityPricing) -> OpsCityPricingOut:
        size_map = {row.size_tier: row.monthly_amount_paise for row in pricing.size_prices}
        interior_map = {
            row.interior_frequency: row.monthly_amount_paise for row in pricing.interior_prices
        }
        if 0 not in interior_map:
            interior_map[0] = 0

        size_prices = [
            OpsSizePriceOut(size_tier=tier, monthly_amount_paise=amount)
            for tier, amount in sorted(size_map.items(), key=lambda x: x[0].value)
        ]
        interior_prices = [
            OpsInteriorPriceOut(interior_frequency=freq, monthly_amount_paise=interior_map[freq])
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

        return OpsCityPricingOut(
            id=pricing.id,
            city_id=pricing.city_id,
            city=OpsCityOut.model_validate(city),
            currency=pricing.currency,
            amounts_include_gst=pricing.amounts_include_gst,
            gst_rate_bps=pricing.gst_rate_bps,
            is_active=pricing.is_active,
            size_prices=size_prices,
            interior_prices=interior_prices,
            matrix=matrix,
            created_at=pricing.created_at,
            updated_at=pricing.updated_at,
        )
