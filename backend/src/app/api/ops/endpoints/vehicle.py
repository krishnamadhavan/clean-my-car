"""Ops vehicle catalog endpoints — Module 5 (Must + Should + Could)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.schemas.ops_vehicle import (
    OpsUserVehicleOut,
    OpsUserVehiclePatch,
    OpsVehicleMakeCreate,
    OpsVehicleMakeListOut,
    OpsVehicleMakeOut,
    OpsVehicleMakePatch,
    OpsVehicleModelCreate,
    OpsVehicleModelListOut,
    OpsVehicleModelOut,
    OpsVehicleModelPatch,
)
from app.services.ops_vehicle import OpsVehicleService

router = APIRouter(tags=["ops-vehicle"])


def get_ops_vehicle_service(db: DbSession) -> OpsVehicleService:
    return OpsVehicleService(session=db)


OpsVehicleServiceDep = Annotated[OpsVehicleService, Depends(get_ops_vehicle_service)]


@router.get(
    "/vehicle-makes",
    response_model=OpsVehicleMakeListOut,
    summary="List vehicle makes including inactive (OPS-VEH-01)",
)
async def list_makes(
    _ops: CurrentOpsOperator,
    svc: OpsVehicleServiceDep,
    include_inactive: Annotated[bool, Query()] = True,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> OpsVehicleMakeListOut:
    return await svc.list_makes(
        include_inactive=include_inactive,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/vehicle-makes",
    response_model=OpsVehicleMakeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create vehicle make (OPS-VEH-02)",
)
async def create_make(
    body: OpsVehicleMakeCreate,
    _ops: CurrentOpsOperator,
    svc: OpsVehicleServiceDep,
) -> OpsVehicleMakeOut:
    return await svc.create_make(body)


@router.patch(
    "/vehicle-makes/{make_id}",
    response_model=OpsVehicleMakeOut,
    summary="Update vehicle make (OPS-VEH-03)",
)
async def patch_make(
    make_id: UUID,
    body: OpsVehicleMakePatch,
    _ops: CurrentOpsOperator,
    svc: OpsVehicleServiceDep,
) -> OpsVehicleMakeOut:
    return await svc.patch_make(make_id, body)


@router.get(
    "/vehicle-makes/{make_id}/models",
    response_model=OpsVehicleModelListOut,
    summary="List models for a make including inactive (OPS-VEH-04)",
)
async def list_models(
    make_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsVehicleServiceDep,
    include_inactive: Annotated[bool, Query()] = True,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> OpsVehicleModelListOut:
    return await svc.list_models(
        make_id,
        include_inactive=include_inactive,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/vehicle-makes/{make_id}/models",
    response_model=OpsVehicleModelOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create vehicle model with size_tier (OPS-VEH-05)",
)
async def create_model(
    make_id: UUID,
    body: OpsVehicleModelCreate,
    _ops: CurrentOpsOperator,
    svc: OpsVehicleServiceDep,
) -> OpsVehicleModelOut:
    return await svc.create_model(make_id, body)


@router.patch(
    "/vehicle-models/{model_id}",
    response_model=OpsVehicleModelOut,
    summary="Update vehicle model (OPS-VEH-06)",
)
async def patch_model(
    model_id: UUID,
    body: OpsVehicleModelPatch,
    _ops: CurrentOpsOperator,
    svc: OpsVehicleServiceDep,
) -> OpsVehicleModelOut:
    return await svc.patch_model(model_id, body)


@router.get(
    "/users/{user_id}/vehicle",
    response_model=OpsUserVehicleOut,
    summary="Inspect user's registered vehicle (OPS-VEH-07)",
)
async def get_user_vehicle(
    user_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsVehicleServiceDep,
) -> OpsUserVehicleOut:
    return await svc.get_user_vehicle(user_id)


@router.patch(
    "/users/{user_id}/vehicle",
    response_model=OpsUserVehicleOut,
    summary="Correct user's vehicle (OPS-VEH-08)",
)
async def patch_user_vehicle(
    user_id: UUID,
    body: OpsUserVehiclePatch,
    _ops: CurrentOpsOperator,
    svc: OpsVehicleServiceDep,
) -> OpsUserVehicleOut:
    return await svc.patch_user_vehicle(user_id, body)
