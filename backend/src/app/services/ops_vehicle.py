"""Ops vehicle catalog service (Ops Module 5)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleMake, VehicleModel
from app.schemas.ops_vehicle import (
    OpsUserVehicleOut,
    OpsUserVehiclePatch,
    OpsVehicleMakeCreate,
    OpsVehicleMakeListOut,
    OpsVehicleMakeOut,
    OpsVehicleMakePatch,
    OpsVehicleModelCreate,
    OpsVehicleModelListOut,
    OpsVehicleModelOut,
    OpsVehicleModelPatch,
)


class OpsVehicleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_makes(
        self,
        *,
        include_inactive: bool = True,
        page: int = 1,
        page_size: int = 50,
    ) -> OpsVehicleMakeListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size
        filters = []
        if not include_inactive:
            filters.append(VehicleMake.is_active.is_(True))

        count_q = select(func.count()).select_from(VehicleMake)
        list_q = select(VehicleMake).order_by(
            VehicleMake.display_order.asc(),
            VehicleMake.name.asc(),
        )
        if filters:
            count_q = count_q.where(*filters)
            list_q = list_q.where(*filters)

        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (await self.session.execute(list_q.offset(offset).limit(page_size))).scalars().all()
        return OpsVehicleMakeListOut(
            items=[OpsVehicleMakeOut.model_validate(m) for m in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_make(self, data: OpsVehicleMakeCreate) -> OpsVehicleMakeOut:
        make = VehicleMake(
            name=data.name,
            is_active=data.is_active,
            display_order=data.display_order,
        )
        self.session.add(make)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "A vehicle make with this name already exists",
                code="vehicle_make_exists",
            ) from exc
        await self.session.refresh(make)
        return OpsVehicleMakeOut.model_validate(make)

    async def patch_make(self, make_id: UUID, data: OpsVehicleMakePatch) -> OpsVehicleMakeOut:
        make = await self._get_make(make_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(make, key, value)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "A vehicle make with this name already exists",
                code="vehicle_make_exists",
            ) from exc
        await self.session.refresh(make)
        return OpsVehicleMakeOut.model_validate(make)

    async def list_models(
        self,
        make_id: UUID,
        *,
        include_inactive: bool = True,
        page: int = 1,
        page_size: int = 50,
    ) -> OpsVehicleModelListOut:
        await self._get_make(make_id)
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size
        filters = [VehicleModel.make_id == make_id]
        if not include_inactive:
            filters.append(VehicleModel.is_active.is_(True))

        count_q = select(func.count()).select_from(VehicleModel).where(*filters)
        list_q = (
            select(VehicleModel)
            .where(*filters)
            .order_by(VehicleModel.display_order.asc(), VehicleModel.name.asc())
            .offset(offset)
            .limit(page_size)
        )
        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (await self.session.execute(list_q)).scalars().all()
        return OpsVehicleModelListOut(
            items=[OpsVehicleModelOut.model_validate(m) for m in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_model(self, make_id: UUID, data: OpsVehicleModelCreate) -> OpsVehicleModelOut:
        await self._get_make(make_id)
        model = VehicleModel(
            make_id=make_id,
            name=data.name,
            size_tier=data.size_tier,
            is_active=data.is_active,
            display_order=data.display_order,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return OpsVehicleModelOut.model_validate(model)

    async def patch_model(self, model_id: UUID, data: OpsVehicleModelPatch) -> OpsVehicleModelOut:
        model = await self._get_model(model_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(model, key, value)
        await self.session.commit()
        await self.session.refresh(model)
        return OpsVehicleModelOut.model_validate(model)

    async def get_user_vehicle(self, user_id: UUID) -> OpsUserVehicleOut:
        await self._require_user(user_id)
        vehicle = await self._get_user_vehicle_row(user_id)
        if vehicle is None:
            raise NotFoundError("User has no vehicle", code="vehicle_not_found")
        return self._user_vehicle_out(vehicle)

    async def patch_user_vehicle(
        self, user_id: UUID, data: OpsUserVehiclePatch
    ) -> OpsUserVehicleOut:
        await self._require_user(user_id)
        vehicle = await self._get_user_vehicle_row(user_id)
        if vehicle is None:
            raise NotFoundError("User has no vehicle", code="vehicle_not_found")

        payload = data.model_dump(exclude_unset=True)
        if "model_id" in payload:
            model_id = payload.pop("model_id")
            if model_id is None:
                raise AppError(
                    "model_id cannot be cleared",
                    code="model_required",
                    status_code=422,
                )
            catalog = await self._require_active_model(model_id)
            vehicle.model = catalog
            vehicle.size_tier = catalog.size_tier

        for key, value in payload.items():
            setattr(vehicle, key, value)

        await self.session.commit()
        vehicle = await self._get_user_vehicle_row(user_id)
        assert vehicle is not None
        return self._user_vehicle_out(vehicle)

    async def _get_make(self, make_id: UUID) -> VehicleMake:
        make = await self.session.get(VehicleMake, make_id)
        if make is None:
            raise NotFoundError("Vehicle make not found", code="vehicle_make_not_found")
        return make

    async def _get_model(self, model_id: UUID) -> VehicleModel:
        model = await self.session.get(VehicleModel, model_id)
        if model is None:
            raise NotFoundError("Vehicle model not found", code="vehicle_model_not_found")
        return model

    async def _require_user(self, user_id: UUID) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found", code="user_not_found")
        return user

    async def _require_active_model(self, model_id: UUID) -> VehicleModel:
        result = await self.session.execute(
            select(VehicleModel)
            .options(selectinload(VehicleModel.make))
            .where(VehicleModel.id == model_id)
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if model is None or not model.is_active or model.make is None or not model.make.is_active:
            raise AppError(
                "Vehicle model is not available",
                code="vehicle_model_not_available",
                status_code=400,
            )
        return model

    async def _get_user_vehicle_row(self, user_id: UUID) -> Vehicle | None:
        result = await self.session.execute(
            select(Vehicle)
            .options(selectinload(Vehicle.model).selectinload(VehicleModel.make))
            .where(Vehicle.user_id == user_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _user_vehicle_out(vehicle: Vehicle) -> OpsUserVehicleOut:
        make_out = None
        model_out = None
        if vehicle.model is not None:
            model_out = OpsVehicleModelOut.model_validate(vehicle.model)
            if vehicle.model.make is not None:
                make_out = OpsVehicleMakeOut.model_validate(vehicle.model.make)
        return OpsUserVehicleOut(
            id=vehicle.id,
            user_id=vehicle.user_id,
            model_id=vehicle.model_id,
            size_tier=vehicle.size_tier,
            nickname=vehicle.nickname,
            plate_number=vehicle.plate_number,
            colour=vehicle.colour,
            parking_slot=vehicle.parking_slot,
            parking_tower=vehicle.parking_tower,
            make=make_out,
            model=model_out,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
        )
