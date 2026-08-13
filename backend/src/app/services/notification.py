"""Consumer devices + notification preferences (Module 11)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.device import UserDevice
from app.models.notification import NotificationPreferences
from app.models.user import User
from app.schemas.notification import (
    DeviceOut,
    DeviceUpsertIn,
    NotificationPreferencesOut,
    NotificationPreferencesUpdate,
)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_device(self, user: User, body: DeviceUpsertIn) -> DeviceOut:
        token = body.token.strip()
        existing = (
            await self.session.execute(select(UserDevice).where(UserDevice.token == token))
        ).scalar_one_or_none()
        if existing is not None:
            existing.user_id = user.id
            existing.platform = (body.platform or "ios").strip().lower()[:20]
            existing.app_version = body.app_version
            existing.device_name = body.device_name
            await self.session.commit()
            await self.session.refresh(existing)
            return DeviceOut.model_validate(existing)

        device = UserDevice(
            user_id=user.id,
            token=token,
            platform=(body.platform or "ios").strip().lower()[:20],
            app_version=body.app_version,
            device_name=body.device_name,
        )
        self.session.add(device)
        await self.session.commit()
        await self.session.refresh(device)
        return DeviceOut.model_validate(device)

    async def delete_device(self, user: User, device_id: UUID) -> None:
        device = await self.session.get(UserDevice, device_id)
        if device is None or device.user_id != user.id:
            raise NotFoundError("Device not found", code="device_not_found")
        await self.session.delete(device)
        await self.session.commit()

    async def get_preferences(self, user: User) -> NotificationPreferencesOut:
        prefs = await self._get_or_create_prefs(user)
        return NotificationPreferencesOut.model_validate(prefs)

    async def update_preferences(
        self, user: User, body: NotificationPreferencesUpdate
    ) -> NotificationPreferencesOut:
        prefs = await self._get_or_create_prefs(user)
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(prefs, key, value)
        await self.session.commit()
        await self.session.refresh(prefs)
        return NotificationPreferencesOut.model_validate(prefs)

    async def _get_or_create_prefs(self, user: User) -> NotificationPreferences:
        prefs = (
            await self.session.execute(
                select(NotificationPreferences).where(NotificationPreferences.user_id == user.id)
            )
        ).scalar_one_or_none()
        if prefs is not None:
            return prefs
        prefs = NotificationPreferences(user_id=user.id)
        self.session.add(prefs)
        await self.session.commit()
        await self.session.refresh(prefs)
        return prefs
