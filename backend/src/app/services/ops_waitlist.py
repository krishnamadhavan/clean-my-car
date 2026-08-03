"""Ops waitlist triage service (Ops Module 4)."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.phone import normalize_indian_phone
from app.models.city import City
from app.models.waitlist import WaitlistEntry, WaitlistStatus
from app.schemas.location import CityOut
from app.schemas.ops_waitlist import (
    OpsWaitlistCityCount,
    OpsWaitlistEntryOut,
    OpsWaitlistListOut,
    OpsWaitlistPatch,
    OpsWaitlistStatusCount,
    OpsWaitlistSummaryOut,
)


class OpsWaitlistService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_entries(
        self,
        *,
        city_id: UUID | None = None,
        status: WaitlistStatus | None = None,
        phone: str | None = None,
        society_name: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> OpsWaitlistListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        filters = []
        if city_id is not None:
            filters.append(WaitlistEntry.city_id == city_id)
        if status is not None:
            filters.append(WaitlistEntry.status == status)
        if phone and phone.strip():
            try:
                normalized = normalize_indian_phone(phone.strip())
                filters.append(WaitlistEntry.phone == normalized)
            except HTTPException:
                digits = "".join(c for c in phone if c.isdigit())
                if digits:
                    filters.append(WaitlistEntry.phone.ilike(f"%{digits}%"))
        if society_name and society_name.strip():
            filters.append(WaitlistEntry.society_name.ilike(f"%{society_name.strip()}%"))

        count_q = select(func.count()).select_from(WaitlistEntry)
        list_q = (
            select(WaitlistEntry)
            .options(selectinload(WaitlistEntry.city))
            .order_by(WaitlistEntry.created_at.desc())
        )
        if filters:
            count_q = count_q.where(*filters)
            list_q = list_q.where(*filters)

        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (await self.session.execute(list_q.offset(offset).limit(page_size))).scalars().all()
        return OpsWaitlistListOut(
            items=[self._to_out(e) for e in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_entry(self, entry_id: UUID) -> OpsWaitlistEntryOut:
        entry = await self._get_entry(entry_id)
        return self._to_out(entry)

    async def patch_entry(self, entry_id: UUID, data: OpsWaitlistPatch) -> OpsWaitlistEntryOut:
        entry = await self._get_entry(entry_id)
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return self._to_out(entry)
        for key, value in payload.items():
            setattr(entry, key, value)
        await self.session.commit()
        # Reload city relationship
        entry = await self._get_entry(entry_id)
        return self._to_out(entry)

    async def summary(self) -> OpsWaitlistSummaryOut:
        count_result = await self.session.execute(select(func.count()).select_from(WaitlistEntry))
        total = int(count_result.scalar_one())

        status_rows = (
            await self.session.execute(
                select(WaitlistEntry.status, func.count())
                .group_by(WaitlistEntry.status)
                .order_by(WaitlistEntry.status)
            )
        ).all()
        by_status = [
            OpsWaitlistStatusCount(status=row[0], count=int(row[1])) for row in status_rows
        ]

        city_rows = (
            await self.session.execute(
                select(WaitlistEntry.city_id, City.name, func.count())
                .join(City, City.id == WaitlistEntry.city_id)
                .group_by(WaitlistEntry.city_id, City.name)
                .order_by(func.count().desc())
            )
        ).all()
        by_city = [
            OpsWaitlistCityCount(
                city_id=row[0],
                city_name=row[1],
                count=int(row[2]),
            )
            for row in city_rows
        ]

        return OpsWaitlistSummaryOut(total=total, by_status=by_status, by_city=by_city)

    async def _get_entry(self, entry_id: UUID) -> WaitlistEntry:
        result = await self.session.execute(
            select(WaitlistEntry)
            .options(selectinload(WaitlistEntry.city))
            .where(WaitlistEntry.id == entry_id)
            .limit(1)
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            raise NotFoundError("Waitlist entry not found", code="waitlist_not_found")
        return entry

    @staticmethod
    def _to_out(entry: WaitlistEntry) -> OpsWaitlistEntryOut:
        city_out = CityOut.model_validate(entry.city) if entry.city is not None else None
        return OpsWaitlistEntryOut(
            id=entry.id,
            user_id=entry.user_id,
            city_id=entry.city_id,
            city=city_out,
            society_name=entry.society_name,
            phone=entry.phone,
            notes=entry.notes,
            status=entry.status,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
