"""Consumer notification endpoints — Module 11."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession
from app.schemas.notification import (
    DeviceOut,
    DeviceUpsertIn,
    NotificationPreferencesOut,
    NotificationPreferencesUpdate,
)
from app.services.notification import NotificationService

router = APIRouter(tags=["notifications"])


def get_notification_service(db: DbSession) -> NotificationService:
    return NotificationService(session=db)


NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]


@router.put(
    "/me/devices",
    response_model=DeviceOut,
    summary="Register or update device token (NOTIF-01)",
)
async def upsert_device(
    body: DeviceUpsertIn,
    user: CurrentUser,
    svc: NotificationServiceDep,
) -> DeviceOut:
    return await svc.upsert_device(user, body)


@router.delete(
    "/me/devices/{device_id}",
    summary="Unregister device (NOTIF-02)",
)
async def delete_device(
    device_id: UUID,
    user: CurrentUser,
    svc: NotificationServiceDep,
) -> dict[str, str]:
    await svc.delete_device(user, device_id)
    return {"message": "Device unregistered"}


@router.get(
    "/me/notification-preferences",
    response_model=NotificationPreferencesOut,
    summary="Read notification preferences (NOTIF-03)",
)
async def get_preferences(
    user: CurrentUser,
    svc: NotificationServiceDep,
) -> NotificationPreferencesOut:
    return await svc.get_preferences(user)


@router.put(
    "/me/notification-preferences",
    response_model=NotificationPreferencesOut,
    summary="Update notification preferences (NOTIF-04)",
)
async def update_preferences(
    body: NotificationPreferencesUpdate,
    user: CurrentUser,
    svc: NotificationServiceDep,
) -> NotificationPreferencesOut:
    return await svc.update_preferences(user, body)
