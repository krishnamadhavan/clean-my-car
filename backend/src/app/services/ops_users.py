"""Ops support tooling for consumer user accounts (Ops Module 2)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.core.phone import normalize_indian_phone
from app.models.city import City
from app.models.refresh_token import RefreshToken
from app.models.society import Society
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.location import CityOut, SocietySummaryOut
from app.schemas.ops_users import OpsUserDetail, OpsUserListOut, OpsUserSummary

_ACTIVE_SUB_STATUSES = (
    SubscriptionStatus.active,
    SubscriptionStatus.cancel_scheduled,
    SubscriptionStatus.paused,
    SubscriptionStatus.pending_payment,
)


class OpsUsersService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_users(
        self,
        *,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OpsUserListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        filters = []
        if q and q.strip():
            term = q.strip()
            # UUID exact match
            try:
                uid = UUID(term)
                filters.append(User.id == uid)
            except ValueError:
                # Phone search: try normalize, else ilike raw digits
                phone_term = term
                try:
                    phone_term = normalize_indian_phone(term)
                    filters.append(User.phone == phone_term)
                except HTTPException:
                    digits = "".join(c for c in term if c.isdigit())
                    if digits:
                        filters.append(User.phone.ilike(f"%{digits}%"))
                    else:
                        filters.append(
                            or_(
                                User.name.ilike(f"%{term}%"),
                                User.email.ilike(f"%{term}%"),
                            )
                        )

        count_q = select(func.count()).select_from(User)
        list_q = select(User).order_by(User.created_at.desc())
        if filters:
            count_q = count_q.where(*filters)
            list_q = list_q.where(*filters)

        total = int((await self.session.execute(count_q)).scalar_one())
        result = await self.session.execute(list_q.offset(offset).limit(page_size))
        users = result.scalars().all()
        items = [OpsUserSummary.model_validate(u) for u in users]
        return OpsUserListOut(items=items, total=total, page=page, page_size=page_size)

    async def get_user(self, user_id: UUID) -> OpsUserDetail:
        user = await self._get_user(user_id)
        return await self._to_detail(user)

    async def deactivate(self, user_id: UUID) -> OpsUserDetail:
        """Force-deactivate account and revoke sessions (OPS-PROF-03)."""
        user = await self._get_user(user_id)
        if user.deleted_at is not None:
            raise AppError(
                "Cannot deactivate a deleted account",
                code="account_deleted",
                status_code=409,
            )
        user.is_active = False
        await self._revoke_all_refresh_tokens(user)
        await self.session.commit()
        await self.session.refresh(user)
        return await self._to_detail(user)

    async def reactivate(self, user_id: UUID) -> OpsUserDetail:
        """Undo soft deactivate (OPS-PROF-04). Does not clear account deletion."""
        user = await self._get_user(user_id)
        if user.deleted_at is not None:
            raise AppError(
                "Cannot reactivate a deleted account; cool-off re-signup applies",
                code="account_deleted",
                status_code=409,
            )
        user.is_active = True
        await self.session.commit()
        await self.session.refresh(user)
        return await self._to_detail(user)

    async def _get_user(self, user_id: UUID) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found", code="user_not_found")
        return user

    async def _to_detail(self, user: User) -> OpsUserDetail:
        city_out: CityOut | None = None
        society_out: SocietySummaryOut | None = None
        if user.city_id:
            city = await self.session.get(City, user.city_id)
            if city is not None:
                city_out = CityOut.model_validate(city)
        if user.society_id:
            society = await self.session.get(Society, user.society_id)
            if society is not None:
                society_out = SocietySummaryOut.from_society(society)

        has_vehicle = (
            await self.session.execute(
                select(Vehicle.id).where(Vehicle.user_id == user.id).limit(1)
            )
        ).scalar_one_or_none() is not None

        has_subscription = (
            await self.session.execute(
                select(Subscription.id)
                .where(
                    Subscription.user_id == user.id,
                    Subscription.status.in_(_ACTIVE_SUB_STATUSES),
                )
                .limit(1)
            )
        ).scalar_one_or_none() is not None

        return OpsUserDetail(
            id=user.id,
            phone=user.phone,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            deleted_at=user.deleted_at,
            city_id=user.city_id,
            society_id=user.society_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
            city=city_out,
            society=society_out,
            has_vehicle=has_vehicle,
            has_subscription=has_subscription,
        )

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
