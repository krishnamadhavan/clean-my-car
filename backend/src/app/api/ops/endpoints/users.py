"""Ops user support endpoints — Module 2 (Should + Could)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.schemas.ops_users import OpsUserDetail, OpsUserListOut
from app.services.ops_users import OpsUsersService

router = APIRouter(prefix="/users", tags=["ops-users"])


def get_ops_users_service(db: DbSession) -> OpsUsersService:
    return OpsUsersService(session=db)


OpsUsersServiceDep = Annotated[OpsUsersService, Depends(get_ops_users_service)]


@router.get(
    "",
    response_model=OpsUserListOut,
    summary="Search consumer users (OPS-PROF-01)",
)
async def list_users(
    _ops: CurrentOpsOperator,
    svc: OpsUsersServiceDep,
    q: Annotated[
        str | None,
        Query(description="Phone (E.164 or 10-digit), user UUID, name, or email"),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OpsUserListOut:
    return await svc.list_users(q=q, page=page, page_size=page_size)


@router.get(
    "/{user_id}",
    response_model=OpsUserDetail,
    summary="Consumer user detail (OPS-PROF-02)",
)
async def get_user(
    user_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsUsersServiceDep,
) -> OpsUserDetail:
    return await svc.get_user(user_id)


@router.post(
    "/{user_id}/deactivate",
    response_model=OpsUserDetail,
    status_code=status.HTTP_200_OK,
    summary="Force-deactivate consumer account (OPS-PROF-03)",
)
async def deactivate_user(
    user_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsUsersServiceDep,
) -> OpsUserDetail:
    return await svc.deactivate(user_id)


@router.post(
    "/{user_id}/reactivate",
    response_model=OpsUserDetail,
    status_code=status.HTTP_200_OK,
    summary="Reactivate consumer account (OPS-PROF-04)",
)
async def reactivate_user(
    user_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsUsersServiceDep,
) -> OpsUserDetail:
    return await svc.reactivate(user_id)
