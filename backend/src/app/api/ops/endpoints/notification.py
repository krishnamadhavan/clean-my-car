"""Ops notification templates — Module 11 (Could)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.schemas.ops_notification import (
    OpsNotificationSendIn,
    OpsNotificationSendOut,
    OpsNotificationTemplateListOut,
    OpsNotificationTemplateOut,
    OpsNotificationTemplateUpsertIn,
)
from app.services.ops_notification import OpsNotificationService

router = APIRouter(tags=["ops-notifications"])


def get_ops_notification_service(db: DbSession) -> OpsNotificationService:
    return OpsNotificationService(session=db)


OpsNotificationServiceDep = Annotated[OpsNotificationService, Depends(get_ops_notification_service)]


@router.get(
    "/notification-templates",
    response_model=OpsNotificationTemplateListOut,
    summary="List notification templates (OPS-NOTIF-01)",
)
async def list_templates(
    _ops: CurrentOpsOperator,
    svc: OpsNotificationServiceDep,
) -> OpsNotificationTemplateListOut:
    return await svc.list_templates()


@router.put(
    "/notification-templates/{key}",
    response_model=OpsNotificationTemplateOut,
    summary="Create/update template (OPS-NOTIF-02)",
)
async def upsert_template(
    key: str,
    body: OpsNotificationTemplateUpsertIn,
    _ops: CurrentOpsOperator,
    svc: OpsNotificationServiceDep,
) -> OpsNotificationTemplateOut:
    return await svc.upsert_template(key, body)


@router.post(
    "/notifications/send",
    response_model=OpsNotificationSendOut,
    summary="Manual notification send (OPS-NOTIF-03)",
)
async def send_notification(
    body: OpsNotificationSendIn,
    _ops: CurrentOpsOperator,
    svc: OpsNotificationServiceDep,
) -> OpsNotificationSendOut:
    return await svc.send(body)
