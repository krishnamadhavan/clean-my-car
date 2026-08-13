"""Ops platform helpers — audit + seed preview (Module 15)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.city import City
from app.models.ops_operator import OpsOperator
from app.models.pricing import CityPricing
from app.models.society import Society
from app.models.vehicle import VehicleMake, VehicleModel
from app.schemas.ops_platform import (
    AuditEventListOut,
    AuditEventOut,
    SeedPreviewIn,
    SeedPreviewOut,
)


class OpsPlatformService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_audit(
        self,
        *,
        action: str | None = None,
        resource_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditEventListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        q = select(AuditEvent)
        count_q = select(func.count()).select_from(AuditEvent)
        if action:
            q = q.where(AuditEvent.action == action)
            count_q = count_q.where(AuditEvent.action == action)
        if resource_type:
            q = q.where(AuditEvent.resource_type == resource_type)
            count_q = count_q.where(AuditEvent.resource_type == resource_type)
        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (
            (
                await self.session.execute(
                    q.order_by(AuditEvent.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return AuditEventListOut(
            items=[AuditEventOut.model_validate(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def record(
        self,
        *,
        operator: OpsOperator | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        summary: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            operator_id=operator.id if operator else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            summary=summary,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def seed_preview(self, body: SeedPreviewIn) -> SeedPreviewOut:
        warnings: list[str] = []
        city_names = {r for r in (await self.session.execute(select(City.name))).scalars().all()}
        make_names = {
            r for r in (await self.session.execute(select(VehicleMake.name))).scalars().all()
        }

        would_cities = 0
        for item in body.cities:
            name = str(item.get("name") or "").strip()
            if not name:
                warnings.append("city missing name")
                continue
            if name in city_names:
                warnings.append(f"city already exists: {name}")
            else:
                would_cities += 1

        would_societies = 0
        for item in body.societies:
            if not item.get("name") or not item.get("city_name"):
                warnings.append("society requires name and city_name")
                continue
            would_societies += 1

        would_makes = 0
        for item in body.vehicle_makes:
            name = str(item.get("name") or "").strip()
            if not name:
                warnings.append("vehicle make missing name")
                continue
            if name in make_names:
                warnings.append(f"make already exists: {name}")
            else:
                would_makes += 1

        would_models = len([m for m in body.vehicle_models if m.get("name") and m.get("make_name")])
        would_pricing = len([p for p in body.pricing if p.get("city_name")])

        existing_cities = int(
            (await self.session.execute(select(func.count()).select_from(City))).scalar_one()
        )
        existing_societies = int(
            (await self.session.execute(select(func.count()).select_from(Society))).scalar_one()
        )
        existing_makes = int(
            (await self.session.execute(select(func.count()).select_from(VehicleMake))).scalar_one()
        )
        existing_models = int(
            (
                await self.session.execute(select(func.count()).select_from(VehicleModel))
            ).scalar_one()
        )
        existing_pricing = int(
            (await self.session.execute(select(func.count()).select_from(CityPricing))).scalar_one()
        )

        return SeedPreviewOut(
            dry_run=True,
            would_create_cities=would_cities,
            would_create_societies=would_societies,
            would_create_makes=would_makes,
            would_create_models=would_models,
            would_create_pricing=would_pricing,
            warnings=warnings,
            message=(
                f"Dry-run only. DB currently has {existing_cities} cities, "
                f"{existing_societies} societies, {existing_makes} makes, "
                f"{existing_models} models, {existing_pricing} pricing rows."
            ),
        )
