"""Waitlist service (Module 4).

Product rule: at most one waitlist entry per authenticated user (and per
phone for anonymous joins). Re-joining updates the existing row.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.core.phone import normalize_indian_phone
from app.models.city import City
from app.models.user import User
from app.models.waitlist import WaitlistEntry, WaitlistStatus
from app.schemas.location import CityOut
from app.schemas.waitlist import WaitlistCreate, WaitlistEntryOut, WaitlistListOut


class WaitlistService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def join(
        self,
        data: WaitlistCreate,
        *,
        user: User | None = None,
    ) -> WaitlistEntryOut:
        city = await self.session.get(City, data.city_id)
        if city is None or not city.is_active:
            raise AppError("City is not available", code="city_not_available", status_code=400)

        raw_phone = data.phone
        if raw_phone is None or not str(raw_phone).strip():
            if user is None:
                raise AppError(
                    "Phone number is required when not authenticated",
                    code="phone_required",
                    status_code=422,
                )
            phone = user.phone
        else:
            phone = normalize_indian_phone(raw_phone)

        existing = await self._find_existing(user=user, phone=phone)
        if existing is not None:
            existing.city_id = city.id
            existing.society_name = data.society_name
            existing.phone = phone
            existing.notes = data.notes
            existing.status = WaitlistStatus.pending
            if user is not None:
                existing.user_id = user.id
            await self.session.commit()
            await self.session.refresh(existing)
            return self._to_out(existing, city)

        entry = WaitlistEntry(
            user_id=user.id if user else None,
            city_id=city.id,
            society_name=data.society_name,
            phone=phone,
            notes=data.notes,
            status=WaitlistStatus.pending,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return self._to_out(entry, city)

    async def list_for_user(self, user: User) -> WaitlistListOut:
        result = await self.session.execute(
            select(WaitlistEntry)
            .options(selectinload(WaitlistEntry.city))
            .where(WaitlistEntry.user_id == user.id)
            .order_by(WaitlistEntry.created_at.desc())
            .limit(1)
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            return WaitlistListOut(items=[])
        return WaitlistListOut(items=[self._to_out(entry, entry.city if entry.city else None)])

    async def _find_existing(
        self,
        *,
        user: User | None,
        phone: str,
    ) -> WaitlistEntry | None:
        """One entry per user (auth) or per phone (anonymous)."""
        if user is not None:
            result = await self.session.execute(
                select(WaitlistEntry)
                .where(WaitlistEntry.user_id == user.id)
                .order_by(WaitlistEntry.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

        result = await self.session.execute(
            select(WaitlistEntry)
            .where(
                WaitlistEntry.phone == phone,
                WaitlistEntry.user_id.is_(None),
            )
            .order_by(WaitlistEntry.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_out(entry: WaitlistEntry, city: City | None) -> WaitlistEntryOut:
        return WaitlistEntryOut(
            id=entry.id,
            city_id=entry.city_id,
            city=CityOut.model_validate(city) if city is not None else None,
            society_name=entry.society_name,
            phone=entry.phone,
            notes=entry.notes,
            status=entry.status,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
