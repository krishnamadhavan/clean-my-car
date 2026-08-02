"""Vehicle service (Module 5 — make/model catalog; one car per account)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, NotFoundError
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleMake, VehicleModel, VehicleSizeTier
from app.schemas.vehicle import (
    VehicleMakeOut,
    VehicleModelListOut,
    VehicleModelOut,
    VehicleOut,
    VehiclePatch,
    VehiclePut,
    VehicleSizeTierListOut,
    VehicleSizeTierOut,
)

# Informational labels only — not user-selectable for pricing
SIZE_TIER_GUIDE: list[VehicleSizeTierOut] = [
    VehicleSizeTierOut(
        code=VehicleSizeTier.small,
        label="Small",
        description="Hatchbacks and compact city cars (derived from model catalog)",
    ),
    VehicleSizeTierOut(
        code=VehicleSizeTier.medium,
        label="Medium",
        description="Sedans and compact crossovers (derived from model catalog)",
    ),
    VehicleSizeTierOut(
        code=VehicleSizeTier.large,
        label="Large",
        description="SUVs / MUVs (derived from model catalog)",
    ),
]


class VehicleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_makes(self) -> list[VehicleMakeOut]:
        result = await self.session.execute(
            select(VehicleMake)
            .where(VehicleMake.is_active.is_(True))
            .order_by(VehicleMake.display_order.asc(), VehicleMake.name.asc())
        )
        return [VehicleMakeOut.model_validate(m) for m in result.scalars().all()]

    async def list_models_for_make(self, make_id: UUID) -> VehicleModelListOut:
        make = await self.session.get(VehicleMake, make_id)
        if make is None or not make.is_active:
            raise NotFoundError("Vehicle make not found", code="vehicle_make_not_found")

        result = await self.session.execute(
            select(VehicleModel)
            .where(
                VehicleModel.make_id == make_id,
                VehicleModel.is_active.is_(True),
            )
            .order_by(VehicleModel.display_order.asc(), VehicleModel.name.asc())
        )
        items = [VehicleModelOut.model_validate(m) for m in result.scalars().all()]
        return VehicleModelListOut(items=items)

    async def get_for_user(self, user: User) -> VehicleOut:
        vehicle = await self._get_row(user)
        if vehicle is None:
            raise NotFoundError("No vehicle registered", code="vehicle_not_found")
        return self._to_out(vehicle)

    async def put_for_user(self, user: User, data: VehiclePut) -> VehicleOut:
        """Create or fully replace the single vehicle (VEH-02)."""
        catalog_model = await self._require_active_model(data.model_id)
        optional = data.model_dump(exclude={"model_id"})

        vehicle = await self._get_row(user)
        if vehicle is None:
            vehicle = Vehicle(
                user_id=user.id,
                model=catalog_model,
                size_tier=catalog_model.size_tier,
                **optional,
            )
            self.session.add(vehicle)
        else:
            # Assign relationship (not only FK) so loaded make/model stay in sync.
            vehicle.model = catalog_model
            vehicle.size_tier = catalog_model.size_tier
            for key, value in optional.items():
                setattr(vehicle, key, value)

        await self.session.commit()
        return await self.get_for_user(user)

    async def patch_for_user(self, user: User, data: VehiclePatch) -> VehicleOut:
        vehicle = await self._get_row(user)
        if vehicle is None:
            raise NotFoundError("No vehicle registered", code="vehicle_not_found")

        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return self._to_out(vehicle)

        if "model_id" in payload:
            model_id = payload.pop("model_id")
            if model_id is None:
                raise AppError(
                    "model_id cannot be cleared",
                    code="model_required",
                    status_code=422,
                )
            catalog_model = await self._require_active_model(model_id)
            vehicle.model = catalog_model
            vehicle.size_tier = catalog_model.size_tier

        for key, value in payload.items():
            setattr(vehicle, key, value)

        await self.session.commit()
        return await self.get_for_user(user)

    async def delete_for_user(self, user: User) -> None:
        """Remove vehicle (VEH-04). Subscription block deferred to Module 7."""
        vehicle = await self._get_row(user)
        if vehicle is None:
            raise NotFoundError("No vehicle registered", code="vehicle_not_found")
        await self.session.delete(vehicle)
        await self.session.commit()

    @staticmethod
    def size_tiers() -> VehicleSizeTierListOut:
        return VehicleSizeTierListOut(items=list(SIZE_TIER_GUIDE))

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

    async def _get_row(self, user: User) -> Vehicle | None:
        result = await self.session.execute(
            select(Vehicle)
            .options(selectinload(Vehicle.model).selectinload(VehicleModel.make))
            .where(Vehicle.user_id == user.id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_out(vehicle: Vehicle) -> VehicleOut:
        make_out: VehicleMakeOut | None = None
        model_out: VehicleModelOut | None = None
        if vehicle.model is not None:
            model_out = VehicleModelOut.model_validate(vehicle.model)
            if vehicle.model.make is not None:
                make_out = VehicleMakeOut.model_validate(vehicle.model.make)
        return VehicleOut(
            id=vehicle.id,
            model_id=vehicle.model_id,
            make=make_out,
            model=model_out,
            size_tier=vehicle.size_tier,
            nickname=vehicle.nickname,
            plate_number=vehicle.plate_number,
            colour=vehicle.colour,
            parking_slot=vehicle.parking_slot,
            parking_tower=vehicle.parking_tower,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
        )
