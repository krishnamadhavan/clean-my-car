"""Profile / account lifecycle service (Module 2)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ForbiddenError
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import MeOut, MeUpdate


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def build_me(self, user: User) -> MeOut:
        """Assemble /me payload. Vehicle/subscription flags until those modules land."""
        return MeOut(
            id=user.id,
            phone=user.phone,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            deleted_at=user.deleted_at,
            has_vehicle=False,
            has_subscription=False,
        )

    async def update_profile(self, user: User, data: MeUpdate) -> User:
        self._ensure_mutable(user)
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return user

        if "name" in payload:
            user.name = payload["name"]
        if "email" in payload:
            user.email = payload["email"]

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def deactivate(self, user: User) -> User:
        """Soft-deactivate (PROF-03). User cannot authenticate until reactivated by support."""
        self._ensure_mutable(user)
        user.is_active = False
        await self._revoke_all_refresh_tokens(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def request_deletion(self, user: User) -> User:
        """Account deletion request (PROF-04): soft-delete + clear profile PII + revoke sessions.

        Phone is retained so ops can honour retention / support trails. Re-login is blocked.
        Full purge can be a later offline job.
        """
        if user.deleted_at is not None:
            raise AppError(
                "Account already scheduled for deletion",
                code="already_deleted",
                status_code=409,
            )

        user.is_active = False
        user.deleted_at = datetime.now(UTC)
        user.name = None
        user.email = None
        await self._revoke_all_refresh_tokens(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def _revoke_all_refresh_tokens(self, user: User) -> None:
        now = datetime.now(UTC)
        await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

    @staticmethod
    def _ensure_mutable(user: User) -> None:
        if user.deleted_at is not None:
            raise ForbiddenError("Account has been deleted", code="account_deleted")
        if not user.is_active:
            raise ForbiddenError("Account is deactivated", code="account_inactive")
