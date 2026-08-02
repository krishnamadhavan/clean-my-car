"""Waitlist endpoints — Module 4 (Should + Could)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession, OptionalCurrentUser
from app.schemas.waitlist import WaitlistCreate, WaitlistEntryOut, WaitlistListOut
from app.services.waitlist import WaitlistService

router = APIRouter(tags=["waitlist"])


def get_waitlist_service(db: DbSession) -> WaitlistService:
    return WaitlistService(session=db)


WaitlistServiceDep = Annotated[WaitlistService, Depends(get_waitlist_service)]


@router.post(
    "/waitlist",
    response_model=WaitlistEntryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Join waitlist (WAIT-01)",
)
async def join_waitlist(
    body: WaitlistCreate,
    svc: WaitlistServiceDep,
    user: OptionalCurrentUser,
) -> WaitlistEntryOut:
    return await svc.join(body, user=user)


@router.get(
    "/me/waitlist",
    response_model=WaitlistListOut,
    summary="List my waitlist entries (WAIT-02)",
)
async def list_my_waitlist(
    user: CurrentUser,
    svc: WaitlistServiceDep,
) -> WaitlistListOut:
    return await svc.list_for_user(user)
