"""Ops wash field actions (OPS-WASH-01–05)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, NotFoundError
from app.models.ops_operator import OpsOperator
from app.models.society import Society
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.wash import Wash, WashStatus
from app.schemas.ops_wash import (
    OpsRosterItemOut,
    OpsRosterOut,
    OpsWashCompleteIn,
    OpsWashGenerateIn,
    OpsWashGenerateOut,
    OpsWashListOut,
    OpsWashMissIn,
    OpsWashOut,
)
from app.services.wash import WashService

INDIA_TZ = ZoneInfo("Asia/Kolkata")

_OPEN_SUB = {
    SubscriptionStatus.pending_payment,
    SubscriptionStatus.active,
    SubscriptionStatus.cancel_scheduled,
}


class OpsWashService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.washes = WashService(session)

    async def list_washes(
        self,
        *,
        society_id: UUID | None = None,
        service_date: date | None = None,
        status: WashStatus | None = None,
        user_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OpsWashListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        q = select(Wash).options(
            selectinload(Wash.user),
            selectinload(Wash.society),
        )
        count_q = select(func.count()).select_from(Wash)
        if society_id is not None:
            q = q.where(Wash.society_id == society_id)
            count_q = count_q.where(Wash.society_id == society_id)
        if service_date is not None:
            q = q.where(Wash.service_date == service_date)
            count_q = count_q.where(Wash.service_date == service_date)
        if status is not None:
            q = q.where(Wash.status == status)
            count_q = count_q.where(Wash.status == status)
        if user_id is not None:
            q = q.where(Wash.user_id == user_id)
            count_q = count_q.where(Wash.user_id == user_id)

        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (
            (
                await self.session.execute(
                    q.order_by(Wash.service_date.desc(), Wash.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return OpsWashListOut(
            items=[self._to_out(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def complete(
        self,
        wash_id: UUID,
        operator: OpsOperator,
        body: OpsWashCompleteIn | None = None,
    ) -> OpsWashOut:
        wash = await self._get(wash_id)
        if wash.status == WashStatus.completed:
            return await self._reload_out(wash.id)
        if wash.status not in {
            WashStatus.scheduled,
            WashStatus.retry_scheduled,
            WashStatus.missed,
        }:
            raise AppError(
                "Wash cannot be completed in its current status",
                code="wash_not_completable",
                status_code=409,
            )
        body = body or OpsWashCompleteIn()
        wash.status = WashStatus.completed
        wash.includes_exterior = True
        wash.includes_interior = body.includes_interior
        wash.completed_at = datetime.now(UTC)
        wash.completed_by_operator_id = operator.id
        wash.miss_reason = None
        if body.notes:
            wash.notes = body.notes
        await self.session.commit()
        return await self._reload_out(wash.id)

    async def miss(
        self,
        wash_id: UUID,
        operator: OpsOperator,
        body: OpsWashMissIn | None = None,
    ) -> OpsWashOut:
        wash = await self._get(wash_id)
        if wash.status == WashStatus.missed:
            return await self._reload_out(wash.id)
        if wash.status not in {WashStatus.scheduled, WashStatus.retry_scheduled}:
            raise AppError(
                "Wash cannot be marked missed in its current status",
                code="wash_not_missable",
                status_code=409,
            )
        body = body or OpsWashMissIn()
        wash.status = WashStatus.missed
        wash.miss_reason = body.reason
        wash.completed_by_operator_id = operator.id
        if body.notes:
            wash.notes = body.notes

        if body.schedule_retry:
            # Next calendar day, but never Sunday (not serviceable) — use Monday.
            retry_date = wash.service_date + timedelta(days=1)
            if retry_date.weekday() == 6:  # Sunday
                retry_date = retry_date + timedelta(days=1)
            existing = (
                await self.session.execute(
                    select(Wash).where(
                        Wash.user_id == wash.user_id,
                        Wash.service_date == retry_date,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self.session.add(
                    Wash(
                        user_id=wash.user_id,
                        subscription_id=wash.subscription_id,
                        society_id=wash.society_id,
                        vehicle_id=wash.vehicle_id,
                        service_date=retry_date,
                        status=WashStatus.retry_scheduled,
                        includes_exterior=True,
                        includes_interior=False,
                        retry_of_wash_id=wash.id,
                        notes="Next-day retry after miss",
                    )
                )
            elif existing.status in {WashStatus.scheduled, WashStatus.retry_scheduled}:
                existing.status = WashStatus.retry_scheduled
                existing.retry_of_wash_id = wash.id

        await self.session.commit()
        return await self._reload_out(wash.id)

    async def roster(self, society_id: UUID, service_date: date | None = None) -> OpsRosterOut:
        society = await self.session.get(Society, society_id)
        if society is None:
            raise NotFoundError("Society not found", code="society_not_found")
        day = service_date or datetime.now(INDIA_TZ).date()
        rows = (
            (
                await self.session.execute(
                    select(Wash)
                    .options(selectinload(Wash.user))
                    .where(
                        Wash.society_id == society_id,
                        Wash.service_date == day,
                        Wash.status.in_(
                            {
                                WashStatus.scheduled,
                                WashStatus.retry_scheduled,
                                WashStatus.completed,
                                WashStatus.missed,
                            }
                        ),
                    )
                    .order_by(Wash.status.asc())
                )
            )
            .scalars()
            .all()
        )
        items = [
            OpsRosterItemOut(
                wash_id=w.id,
                user_id=w.user_id,
                user_phone=w.user.phone if w.user else "",
                user_name=w.user.name if w.user else None,
                vehicle_id=w.vehicle_id,
                service_date=w.service_date,
                status=w.status,
                includes_exterior=w.includes_exterior,
                includes_interior=w.includes_interior,
                subscription_id=w.subscription_id,
            )
            for w in rows
        ]
        return OpsRosterOut(
            society_id=society.id,
            society_name=society.name,
            service_date=day,
            items=items,
            total=len(items),
        )

    async def generate(self, body: OpsWashGenerateIn) -> OpsWashGenerateOut:
        created = 0
        skipped = 0
        q = (
            select(Subscription)
            .options(selectinload(Subscription.society))
            .where(Subscription.status.in_(_OPEN_SUB))
        )
        if body.subscription_id is not None:
            q = q.where(Subscription.id == body.subscription_id)
        if body.society_id is not None:
            q = q.where(Subscription.society_id == body.society_id)
        subs = (await self.session.execute(q)).scalars().all()
        for sub in subs:
            n = await self.washes.ensure_generated(sub)
            created += n
            # approximate skipped not tracked precisely; remaining service days - created
        return OpsWashGenerateOut(
            created=created,
            skipped_existing=skipped,
            message=f"Generated {created} wash row(s) for {len(subs)} subscription(s).",
        )

    async def _get(self, wash_id: UUID) -> Wash:
        wash = await self.session.get(Wash, wash_id)
        if wash is None:
            raise NotFoundError("Wash not found", code="wash_not_found")
        return wash

    async def _reload_out(self, wash_id: UUID) -> OpsWashOut:
        wash = (
            await self.session.execute(
                select(Wash)
                .options(selectinload(Wash.user), selectinload(Wash.society))
                .where(Wash.id == wash_id)
            )
        ).scalar_one()
        return self._to_out(wash)

    @staticmethod
    def _to_out(wash: Wash) -> OpsWashOut:
        return OpsWashOut(
            id=wash.id,
            user_id=wash.user_id,
            subscription_id=wash.subscription_id,
            society_id=wash.society_id,
            vehicle_id=wash.vehicle_id,
            service_date=wash.service_date,
            status=wash.status,
            includes_exterior=wash.includes_exterior,
            includes_interior=wash.includes_interior,
            completed_at=wash.completed_at,
            completed_by_operator_id=wash.completed_by_operator_id,
            miss_reason=wash.miss_reason,
            retry_of_wash_id=wash.retry_of_wash_id,
            notes=wash.notes,
            user_phone=wash.user.phone if wash.user else None,
            user_name=wash.user.name if wash.user else None,
            society_name=wash.society.name if wash.society else None,
            created_at=wash.created_at,
            updated_at=wash.updated_at,
        )
