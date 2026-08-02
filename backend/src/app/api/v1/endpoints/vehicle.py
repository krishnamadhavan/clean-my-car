"""Vehicle endpoints — Module 5 (Must + Should).

Users choose make + model; size_tier is derived from the catalog.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.user import MessageOut
from app.schemas.vehicle import (
    VehicleMakeOut,
    VehicleModelListOut,
    VehicleOut,
    VehiclePatch,
    VehiclePut,
    VehicleSizeTierListOut,
)
from app.services.vehicle import VehicleService

router = APIRouter(tags=["vehicle"])


def get_vehicle_service(db: DbSession) -> VehicleService:
    return VehicleService(session=db)


VehicleServiceDep = Annotated[VehicleService, Depends(get_vehicle_service)]


@router.get(
    "/vehicle-size-tiers",
    response_model=VehicleSizeTierListOut,
    summary="Size tier labels (informational; not user-selectable) (VEH-05)",
)
async def list_size_tiers(svc: VehicleServiceDep) -> VehicleSizeTierListOut:
    return svc.size_tiers()


@router.get(
    "/vehicle-makes",
    response_model=list[VehicleMakeOut],
    summary="List active vehicle makes / brands (VEH-06)",
)
async def list_makes(svc: VehicleServiceDep) -> list[VehicleMakeOut]:
    return await svc.list_makes()


@router.get(
    "/vehicle-makes/{make_id}/models",
    response_model=VehicleModelListOut,
    summary="List active models for a make (includes derived size_tier) (VEH-07)",
)
async def list_models_for_make(
    make_id: UUID,
    svc: VehicleServiceDep,
) -> VehicleModelListOut:
    return await svc.list_models_for_make(make_id)


@router.get(
    "/me/vehicle",
    response_model=VehicleOut,
    summary="Get current vehicle (VEH-01)",
)
async def get_my_vehicle(user: CurrentUser, svc: VehicleServiceDep) -> VehicleOut:
    return await svc.get_for_user(user)


@router.put(
    "/me/vehicle",
    response_model=VehicleOut,
    summary="Create or replace vehicle via model_id (VEH-02)",
)
async def put_my_vehicle(
    body: VehiclePut,
    user: CurrentUser,
    svc: VehicleServiceDep,
) -> VehicleOut:
    return await svc.put_for_user(user, body)


@router.patch(
    "/me/vehicle",
    response_model=VehicleOut,
    summary="Partial update vehicle (VEH-03)",
)
async def patch_my_vehicle(
    body: VehiclePatch,
    user: CurrentUser,
    svc: VehicleServiceDep,
) -> VehicleOut:
    return await svc.patch_for_user(user, body)


@router.delete(
    "/me/vehicle",
    response_model=MessageOut,
    status_code=status.HTTP_200_OK,
    summary="Remove vehicle (VEH-04)",
)
async def delete_my_vehicle(user: CurrentUser, svc: VehicleServiceDep) -> MessageOut:
    await svc.delete_for_user(user)
    return MessageOut(message="Vehicle removed")
