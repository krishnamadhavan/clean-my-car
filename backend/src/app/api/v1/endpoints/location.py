"""Location & eligibility endpoints — Module 3 (Must)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.location import (
    CityOut,
    SocietyDetailOut,
    SocietyListOut,
    UserLocationOut,
    UserLocationUpdate,
)
from app.services.location import LocationService

router = APIRouter(tags=["location"])


def get_location_service(db: DbSession) -> LocationService:
    return LocationService(session=db)


LocationServiceDep = Annotated[LocationService, Depends(get_location_service)]


@router.get(
    "/cities",
    response_model=list[CityOut],
    summary="List active cities (LOC-01)",
)
async def list_cities(svc: LocationServiceDep) -> list[CityOut]:
    return await svc.list_active_cities()


@router.get(
    "/cities/{city_id}/societies",
    response_model=SocietyListOut,
    summary="List live societies in a city (LOC-02)",
)
async def list_societies(
    city_id: UUID,
    svc: LocationServiceDep,
    q: Annotated[str | None, Query(description="Search by name or address")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SocietyListOut:
    return await svc.list_live_societies(city_id, q=q, page=page, page_size=page_size)


@router.get(
    "/societies/{society_id}",
    response_model=SocietyDetailOut,
    summary="Get live society detail (LOC-03)",
)
async def get_society(society_id: UUID, svc: LocationServiceDep) -> SocietyDetailOut:
    return await svc.get_live_society(society_id)


@router.get(
    "/me/location",
    response_model=UserLocationOut,
    summary="Get current user location (LOC-04)",
)
async def get_my_location(user: CurrentUser, svc: LocationServiceDep) -> UserLocationOut:
    return await svc.get_user_location(user)


@router.put(
    "/me/location",
    response_model=UserLocationOut,
    summary="Set user city and society (LOC-05)",
)
async def put_my_location(
    body: UserLocationUpdate,
    user: CurrentUser,
    svc: LocationServiceDep,
) -> UserLocationOut:
    return await svc.set_user_location(user, body)
