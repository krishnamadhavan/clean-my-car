"""Pricing endpoints — Module 6 (Must + Should)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.pricing import CityPricingOut, InteriorOptionsOut, QuoteIn, QuoteOut
from app.services.pricing import PricingService

router = APIRouter(tags=["pricing"])


def get_pricing_service(db: DbSession) -> PricingService:
    return PricingService(session=db)


PricingServiceDep = Annotated[PricingService, Depends(get_pricing_service)]


@router.get(
    "/interior-options",
    response_model=InteriorOptionsOut,
    summary="Interior package options (PRICE-03)",
)
async def list_interior_options(svc: PricingServiceDep) -> InteriorOptionsOut:
    return svc.interior_options()


@router.get(
    "/cities/{city_id}/pricing",
    response_model=CityPricingOut,
    summary="City price matrix (PRICE-01)",
)
async def get_city_pricing(city_id: UUID, svc: PricingServiceDep) -> CityPricingOut:
    return await svc.get_city_pricing(city_id)


@router.post(
    "/pricing/quote",
    response_model=QuoteOut,
    summary="Compute subscription quote with pro-rate (PRICE-02)",
)
async def create_quote(body: QuoteIn, svc: PricingServiceDep) -> QuoteOut:
    return await svc.quote(body)
