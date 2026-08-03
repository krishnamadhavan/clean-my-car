"""Ops location catalog endpoints — Module 3 (Must + Should)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.schemas.ops_location import (
    OpsCityCreate,
    OpsCityListOut,
    OpsCityOut,
    OpsCityPatch,
    OpsSocietyCreate,
    OpsSocietyListOut,
    OpsSocietyOut,
    OpsSocietyPatch,
)
from app.services.ops_location import OpsLocationService

router = APIRouter(tags=["ops-location"])


def get_ops_location_service(db: DbSession) -> OpsLocationService:
    return OpsLocationService(session=db)


OpsLocationServiceDep = Annotated[OpsLocationService, Depends(get_ops_location_service)]


@router.get(
    "/cities",
    response_model=OpsCityListOut,
    summary="List cities including inactive (OPS-LOC-01)",
)
async def list_cities(
    _ops: CurrentOpsOperator,
    svc: OpsLocationServiceDep,
    include_inactive: Annotated[bool, Query()] = True,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> OpsCityListOut:
    return await svc.list_cities(
        include_inactive=include_inactive,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/cities",
    response_model=OpsCityOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create city (OPS-LOC-02)",
)
async def create_city(
    body: OpsCityCreate,
    _ops: CurrentOpsOperator,
    svc: OpsLocationServiceDep,
) -> OpsCityOut:
    return await svc.create_city(body)


@router.patch(
    "/cities/{city_id}",
    response_model=OpsCityOut,
    summary="Update city (OPS-LOC-03)",
)
async def patch_city(
    city_id: UUID,
    body: OpsCityPatch,
    _ops: CurrentOpsOperator,
    svc: OpsLocationServiceDep,
) -> OpsCityOut:
    return await svc.patch_city(city_id, body)


@router.get(
    "/cities/{city_id}/societies",
    response_model=OpsSocietyListOut,
    summary="List societies including non-live (OPS-LOC-04)",
)
async def list_societies(
    city_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsLocationServiceDep,
    include_non_serviceable: Annotated[bool, Query()] = True,
    q: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> OpsSocietyListOut:
    return await svc.list_societies(
        city_id,
        include_non_serviceable=include_non_serviceable,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/cities/{city_id}/societies",
    response_model=OpsSocietyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create society (OPS-LOC-05)",
)
async def create_society(
    city_id: UUID,
    body: OpsSocietyCreate,
    _ops: CurrentOpsOperator,
    svc: OpsLocationServiceDep,
) -> OpsSocietyOut:
    return await svc.create_society(city_id, body)


@router.get(
    "/societies/{society_id}",
    response_model=OpsSocietyOut,
    summary="Society detail (OPS-LOC-07)",
)
async def get_society(
    society_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsLocationServiceDep,
) -> OpsSocietyOut:
    return await svc.get_society(society_id)


@router.patch(
    "/societies/{society_id}",
    response_model=OpsSocietyOut,
    summary="Update society (OPS-LOC-06)",
)
async def patch_society(
    society_id: UUID,
    body: OpsSocietyPatch,
    _ops: CurrentOpsOperator,
    svc: OpsLocationServiceDep,
) -> OpsSocietyOut:
    return await svc.patch_society(society_id, body)
