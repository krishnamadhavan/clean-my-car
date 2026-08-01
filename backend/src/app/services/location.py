"""Location catalog and user eligibility service (Module 3)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, NotFoundError
from app.models.city import City
from app.models.society import Society
from app.models.user import User
from app.schemas.location import (
    CityOut,
    SocietyDetailOut,
    SocietyListOut,
    SocietySummaryOut,
    UserLocationOut,
    UserLocationUpdate,
)


class LocationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active_cities(self) -> list[CityOut]:
        result = await self.session.execute(
            select(City)
            .where(City.is_active.is_(True))
            .order_by(City.display_order.asc(), City.name.asc())
        )
        cities = result.scalars().all()
        return [CityOut.model_validate(c) for c in cities]

    async def list_live_societies(
        self,
        city_id: UUID,
        *,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SocietyListOut:
        city = await self.session.get(City, city_id)
        if city is None or not city.is_active:
            raise NotFoundError("City not found", code="city_not_found")

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        filters = [
            Society.city_id == city_id,
            Society.is_serviceable.is_(True),
        ]
        if q and q.strip():
            term = f"%{q.strip()}%"
            filters.append(
                or_(
                    Society.name.ilike(term),
                    Society.address_line.ilike(term),
                )
            )

        count_result = await self.session.execute(
            select(func.count()).select_from(Society).where(*filters)
        )
        total = int(count_result.scalar_one())

        result = await self.session.execute(
            select(Society)
            .where(*filters)
            .order_by(Society.display_order.asc(), Society.name.asc())
            .offset(offset)
            .limit(page_size)
        )
        societies = result.scalars().all()
        items = [SocietySummaryOut.from_society(s) for s in societies]
        return SocietyListOut(items=items, total=total, page=page, page_size=page_size)

    async def get_live_society(self, society_id: UUID) -> SocietyDetailOut:
        result = await self.session.execute(
            select(Society)
            .options(selectinload(Society.city))
            .where(Society.id == society_id)
            .limit(1)
        )
        society = result.scalar_one_or_none()
        if (
            society is None
            or not society.is_serviceable
            or society.city is None
            or not society.city.is_active
        ):
            raise NotFoundError("Society not found", code="society_not_found")

        summary = SocietySummaryOut.from_society(society)
        return SocietyDetailOut(
            **summary.model_dump(),
            city=CityOut.model_validate(society.city),
            is_serviceable=True,
        )

    async def get_user_location(self, user: User) -> UserLocationOut:
        city_out: CityOut | None = None
        society_out: SocietySummaryOut | None = None

        if user.city_id:
            city = await self.session.get(City, user.city_id)
            if city is not None and city.is_active:
                city_out = CityOut.model_validate(city)

        if user.society_id and city_out is not None:
            society = await self.session.get(Society, user.society_id)
            if society is not None and society.is_serviceable and society.city_id == city_out.id:
                society_out = SocietySummaryOut.from_society(society)

        return UserLocationOut(
            city=city_out,
            society=society_out,
            updated_at=user.updated_at if (city_out or society_out or user.city_id) else None,
        )

    async def set_user_location(self, user: User, data: UserLocationUpdate) -> UserLocationOut:
        city = await self.session.get(City, data.city_id)
        if city is None or not city.is_active:
            raise AppError("City is not available", code="city_not_available", status_code=400)

        society = await self.session.get(Society, data.society_id)
        if society is None or not society.is_serviceable:
            raise AppError(
                "Society is not serviceable",
                code="society_not_serviceable",
                status_code=400,
            )
        if society.city_id != city.id:
            raise AppError(
                "Society does not belong to the selected city",
                code="society_city_mismatch",
                status_code=400,
            )

        user.city_id = city.id
        user.society_id = society.id
        await self.session.commit()
        await self.session.refresh(user)
        return await self.get_user_location(user)
