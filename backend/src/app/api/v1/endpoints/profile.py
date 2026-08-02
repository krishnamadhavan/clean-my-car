"""Profile endpoints — Module 2 (Must + Should)."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.user import MeOut, MessageOut, MeUpdate
from app.services.profile import ProfileService

router = APIRouter(prefix="/me", tags=["profile"])


def _profile_service(db: DbSession) -> ProfileService:
    return ProfileService(session=db)


@router.get(
    "",
    response_model=MeOut,
    summary="Get current user profile (PROF-01)",
)
async def get_me(user: CurrentUser, db: DbSession) -> MeOut:
    return await _profile_service(db).build_me(user)


@router.patch(
    "",
    response_model=MeOut,
    summary="Update profile name/email (PROF-02)",
)
async def patch_me(body: MeUpdate, user: CurrentUser, db: DbSession) -> MeOut:
    service = _profile_service(db)
    updated = await service.update_profile(user, body)
    return await service.build_me(updated)


@router.post(
    "/deactivate",
    response_model=MessageOut,
    status_code=status.HTTP_200_OK,
    summary="Soft-deactivate account (PROF-03)",
)
async def deactivate_me(user: CurrentUser, db: DbSession) -> MessageOut:
    await _profile_service(db).deactivate(user)
    return MessageOut(message="Account deactivated")


@router.delete(
    "",
    response_model=MessageOut,
    status_code=status.HTTP_200_OK,
    summary="Request account deletion (PROF-04)",
)
async def delete_me(user: CurrentUser, db: DbSession) -> MessageOut:
    await _profile_service(db).request_deletion(user)
    return MessageOut(message="Account deletion requested")
