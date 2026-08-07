"""Ops location catalog service — cities & societies (Ops Module 3)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.city import City
from app.models.society import Society
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


class OpsLocationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_cities(
        self,
        *,
        include_inactive: bool = True,
        page: int = 1,
        page_size: int = 50,
    ) -> OpsCityListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        filters = []
        if not include_inactive:
            filters.append(City.is_active.is_(True))

        count_q = select(func.count()).select_from(City)
        list_q = select(City).order_by(City.display_order.asc(), City.name.asc())
        if filters:
            count_q = count_q.where(*filters)
            list_q = list_q.where(*filters)

        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (await self.session.execute(list_q.offset(offset).limit(page_size))).scalars().all()
        return OpsCityListOut(
            items=[OpsCityOut.model_validate(c) for c in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_city(self, data: OpsCityCreate) -> OpsCityOut:
        order = data.display_order
        if order is None:
            order = await self._next_city_display_order()
        else:
            await self._ensure_city_display_order_available(order)
        city = City(
            name=data.name,
            state=data.state,
            is_active=data.is_active,
            display_order=order,
        )
        self.session.add(city)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                f"display_order {order} is already used by another city",
                code="city_display_order_exists",
            ) from exc
        await self.session.refresh(city)
        return OpsCityOut.model_validate(city)

    async def patch_city(self, city_id: UUID, data: OpsCityPatch) -> OpsCityOut:
        city = await self._get_city(city_id)
        payload = data.model_dump(exclude_unset=True)
        if "display_order" in payload and payload["display_order"] is not None:
            await self._ensure_city_display_order_available(
                int(payload["display_order"]),
                exclude_city_id=city_id,
            )
        for key, value in payload.items():
            setattr(city, key, value)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            order = payload.get("display_order", city.display_order)
            raise ConflictError(
                f"display_order {order} is already used by another city",
                code="city_display_order_exists",
            ) from exc
        await self.session.refresh(city)
        return OpsCityOut.model_validate(city)

    async def _next_city_display_order(self) -> int:
        result = await self.session.execute(select(func.coalesce(func.max(City.display_order), -1)))
        return int(result.scalar_one()) + 1

    async def _ensure_city_display_order_available(
        self,
        order: int,
        *,
        exclude_city_id: UUID | None = None,
    ) -> None:
        q = select(City.id).where(City.display_order == order)
        if exclude_city_id is not None:
            q = q.where(City.id != exclude_city_id)
        taken = (await self.session.execute(q.limit(1))).scalar_one_or_none()
        if taken is not None:
            raise ConflictError(
                f"display_order {order} is already used by another city",
                code="city_display_order_exists",
            )

    async def list_societies(
        self,
        city_id: UUID,
        *,
        include_non_serviceable: bool = True,
        q: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> OpsSocietyListOut:
        await self._get_city(city_id)
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        filters = [Society.city_id == city_id]
        if not include_non_serviceable:
            filters.append(Society.is_serviceable.is_(True))
        if q and q.strip():
            term = f"%{q.strip()}%"
            filters.append(Society.name.ilike(term))

        count_q = select(func.count()).select_from(Society).where(*filters)
        list_q = (
            select(Society)
            .where(*filters)
            .order_by(Society.display_order.asc(), Society.name.asc())
            .offset(offset)
            .limit(page_size)
        )
        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (await self.session.execute(list_q)).scalars().all()
        return OpsSocietyListOut(
            items=[OpsSocietyOut.model_validate(s) for s in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_society(self, city_id: UUID, data: OpsSocietyCreate) -> OpsSocietyOut:
        await self._get_city(city_id)
        society = Society(
            city_id=city_id,
            name=data.name,
            address_line=data.address_line,
            service_weekdays=list(data.service_weekdays),
            is_serviceable=data.is_serviceable,
            display_order=data.display_order,
        )
        self.session.add(society)
        await self.session.commit()
        await self.session.refresh(society)
        return OpsSocietyOut.model_validate(society)

    async def get_society(self, society_id: UUID) -> OpsSocietyOut:
        society = await self._get_society(society_id)
        return OpsSocietyOut.model_validate(society)

    async def patch_society(self, society_id: UUID, data: OpsSocietyPatch) -> OpsSocietyOut:
        society = await self._get_society(society_id)
        payload = data.model_dump(exclude_unset=True)
        # Explicit null for address_line clears it
        for key, value in payload.items():
            setattr(society, key, value)
        await self.session.commit()
        await self.session.refresh(society)
        return OpsSocietyOut.model_validate(society)

    async def _get_city(self, city_id: UUID) -> City:
        city = await self.session.get(City, city_id)
        if city is None:
            raise NotFoundError("City not found", code="city_not_found")
        return city

    async def _get_society(self, society_id: UUID) -> Society:
        society = await self.session.get(Society, society_id)
        if society is None:
            raise NotFoundError("Society not found", code="society_not_found")
        return society
