"""Ops pricing catalog endpoints — Module 6 (Must + Should)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.schemas.ops_pricing import (
    OpsCityPricingOut,
    OpsCityPricingPut,
    OpsInteriorPricesPut,
    OpsMissingPricingListOut,
    OpsSizePricesPut,
    QuoteIn,
    QuoteOut,
)
from app.services.ops_pricing import OpsPricingService

router = APIRouter(tags=["ops-pricing"])


def get_ops_pricing_service(db: DbSession) -> OpsPricingService:
    return OpsPricingService(session=db)


OpsPricingServiceDep = Annotated[OpsPricingService, Depends(get_ops_pricing_service)]


@router.get(
    "/cities/{city_id}/pricing",
    response_model=OpsCityPricingOut,
    summary="Get city pricing including inactive (OPS-PRICE-01)",
)
async def get_city_pricing(
    city_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsPricingServiceDep,
) -> OpsCityPricingOut:
    return await svc.get_city_pricing(city_id)


@router.put(
    "/cities/{city_id}/pricing",
    response_model=OpsCityPricingOut,
    summary="Upsert city pricing config (OPS-PRICE-02)",
)
async def put_city_pricing(
    city_id: UUID,
    body: OpsCityPricingPut,
    _ops: CurrentOpsOperator,
    svc: OpsPricingServiceDep,
) -> OpsCityPricingOut:
    return await svc.put_city_pricing(city_id, body)


@router.put(
    "/cities/{city_id}/pricing/size-prices",
    response_model=OpsCityPricingOut,
    summary="Replace size-tier base prices in paise (OPS-PRICE-03)",
)
async def put_size_prices(
    city_id: UUID,
    body: OpsSizePricesPut,
    _ops: CurrentOpsOperator,
    svc: OpsPricingServiceDep,
) -> OpsCityPricingOut:
    return await svc.put_size_prices(city_id, body)


@router.put(
    "/cities/{city_id}/pricing/interior-prices",
    response_model=OpsCityPricingOut,
    summary="Replace interior add-on prices in paise (OPS-PRICE-04)",
)
async def put_interior_prices(
    city_id: UUID,
    body: OpsInteriorPricesPut,
    _ops: CurrentOpsOperator,
    svc: OpsPricingServiceDep,
) -> OpsCityPricingOut:
    return await svc.put_interior_prices(city_id, body)


@router.post(
    "/pricing/quote",
    response_model=QuoteOut,
    summary="Ops preview quote using consumer engine (OPS-PRICE-05)",
)
async def create_ops_quote(
    body: QuoteIn,
    _ops: CurrentOpsOperator,
    svc: OpsPricingServiceDep,
) -> QuoteOut:
    return await svc.quote(body)


@router.get(
    "/pricing/missing",
    response_model=OpsMissingPricingListOut,
    summary="Active cities without active pricing (OPS-PRICE-06)",
)
async def list_missing_pricing(
    _ops: CurrentOpsOperator,
    svc: OpsPricingServiceDep,
) -> OpsMissingPricingListOut:
    return await svc.list_missing()
