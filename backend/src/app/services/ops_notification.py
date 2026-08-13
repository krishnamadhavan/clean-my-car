"""Ops notification templates (OPS-NOTIF-01–03)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.notification import NotificationTemplate
from app.models.user import User
from app.schemas.ops_notification import (
    OpsNotificationSendIn,
    OpsNotificationSendOut,
    OpsNotificationTemplateListOut,
    OpsNotificationTemplateOut,
    OpsNotificationTemplateUpsertIn,
)

_DEFAULT_TEMPLATES = (
    ("wash_completed", "Wash completed", "Your car wash is done for today.", "push"),
    ("payment_due", "Payment due", "Please pay to keep your Clean My Car plan active.", "push"),
    (
        "service_reminder",
        "Service tomorrow",
        "We will visit your society tomorrow for a wash.",
        "push",
    ),
)


class OpsNotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_templates(self) -> OpsNotificationTemplateListOut:
        await self._ensure_defaults()
        rows = (
            (
                await self.session.execute(
                    select(NotificationTemplate).order_by(NotificationTemplate.key)
                )
            )
            .scalars()
            .all()
        )
        return OpsNotificationTemplateListOut(
            items=[OpsNotificationTemplateOut.model_validate(r) for r in rows]
        )

    async def upsert_template(
        self, key: str, body: OpsNotificationTemplateUpsertIn
    ) -> OpsNotificationTemplateOut:
        key = key.strip()
        if not key:
            raise AppError("Template key is required", code="invalid_key", status_code=400)
        row = (
            await self.session.execute(
                select(NotificationTemplate).where(NotificationTemplate.key == key)
            )
        ).scalar_one_or_none()
        if row is None:
            row = NotificationTemplate(
                key=key,
                title=body.title,
                body=body.body,
                channel=body.channel,
            )
            self.session.add(row)
        else:
            row.title = body.title
            row.body = body.body
            row.channel = body.channel
        await self.session.commit()
        await self.session.refresh(row)
        return OpsNotificationTemplateOut.model_validate(row)

    async def send(self, body: OpsNotificationSendIn) -> OpsNotificationSendOut:
        """Accept a send request (no real push provider in v1 — logs as accepted)."""
        title = body.title
        text = body.body
        if body.template_key:
            tpl = (
                await self.session.execute(
                    select(NotificationTemplate).where(
                        NotificationTemplate.key == body.template_key
                    )
                )
            ).scalar_one_or_none()
            if tpl is None:
                raise NotFoundError("Template not found", code="template_not_found")
            title = title or tpl.title
            text = text or tpl.body
        if not title or not text:
            raise AppError(
                "title and body (or template_key) are required",
                code="invalid_send",
                status_code=400,
            )
        if body.user_id is not None:
            user = await self.session.get(User, body.user_id)
            if user is None:
                raise NotFoundError("User not found", code="user_not_found")
        return OpsNotificationSendOut(
            accepted=True,
            message="Notification accepted (delivery provider not configured).",
        )

    async def _ensure_defaults(self) -> None:
        existing = {
            r
            for r in (await self.session.execute(select(NotificationTemplate.key))).scalars().all()
        }
        added = False
        for key, title, body, channel in _DEFAULT_TEMPLATES:
            if key not in existing:
                self.session.add(
                    NotificationTemplate(key=key, title=title, body=body, channel=channel)
                )
                added = True
        if added:
            await self.session.commit()
