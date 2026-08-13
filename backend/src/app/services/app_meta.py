"""App config and bootstrap (Module 13)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_config import AppConfig
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.app_meta import AppBootstrapOut, AppConfigOut, OpsAppConfigUpdateIn

_OPEN_SUB = {
    SubscriptionStatus.pending_payment,
    SubscriptionStatus.active,
    SubscriptionStatus.cancel_scheduled,
}


class AppMetaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_config(self) -> AppConfigOut:
        cfg = await self.get_or_create_config()
        return self._to_out(cfg)

    async def bootstrap(self, user: User | None) -> AppBootstrapOut:
        config = await self.get_config()
        if user is None:
            return AppBootstrapOut(config=config, authenticated=False)
        has_vehicle = (
            await self.session.execute(
                select(Vehicle.id).where(Vehicle.user_id == user.id).limit(1)
            )
        ).scalar_one_or_none() is not None
        has_sub = (
            await self.session.execute(
                select(Subscription.id)
                .where(
                    Subscription.user_id == user.id,
                    Subscription.status.in_(_OPEN_SUB),
                )
                .limit(1)
            )
        ).scalar_one_or_none() is not None
        return AppBootstrapOut(
            config=config,
            authenticated=True,
            user_id=user.id,
            has_vehicle=has_vehicle,
            has_subscription=has_sub,
        )

    async def ops_update(self, body: OpsAppConfigUpdateIn) -> AppConfigOut:
        cfg = await self.get_or_create_config()
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(cfg, key, value)
        await self.session.commit()
        await self.session.refresh(cfg)
        return self._to_out(cfg)

    async def get_or_create_config(self) -> AppConfig:
        row = (
            await self.session.execute(
                select(AppConfig).order_by(AppConfig.created_at.asc()).limit(1)
            )
        ).scalar_one_or_none()
        if row is not None:
            return row
        row = AppConfig(
            min_ios_version="17.0",
            force_update=False,
            feature_flags={},
            support_email="support@cleanmycar.in",
            support_whatsapp="+919999999999",
            support_whatsapp_url="https://wa.me/919999999999",
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    @staticmethod
    def _to_out(cfg: AppConfig) -> AppConfigOut:
        return AppConfigOut(
            min_ios_version=cfg.min_ios_version,
            force_update=cfg.force_update,
            feature_flags=cfg.feature_flags or {},
            support_whatsapp=cfg.support_whatsapp,
            support_email=cfg.support_email,
            support_phone=cfg.support_phone,
            support_whatsapp_url=cfg.support_whatsapp_url,
        )
