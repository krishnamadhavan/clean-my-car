"""Payment gateway webhooks (Module 14)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.payment import Payment, PaymentStatus
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.webhook import PaymentWebhookIn, PaymentWebhookOut


class WebhookService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def handle_payment_event(
        self, provider: str, body: PaymentWebhookIn
    ) -> PaymentWebhookOut:
        provider = (provider or "manual").strip().lower()
        payment = await self._resolve_payment(body)
        event = body.event.strip().lower()
        now = datetime.now(UTC)

        if event in {"captured", "succeeded", "paid"}:
            if payment.status != PaymentStatus.succeeded:
                payment.status = PaymentStatus.succeeded
                payment.captured_at = now
                payment.failure_reason = None
                if body.provider_ref:
                    payment.provider_ref = body.provider_ref
                payment.provider = provider
                if payment.subscription_id is not None:
                    sub = await self.session.get(Subscription, payment.subscription_id)
                    if sub is not None and sub.status == SubscriptionStatus.pending_payment:
                        sub.status = SubscriptionStatus.active
                await self.session.commit()
                await self.session.refresh(payment)
            return PaymentWebhookOut(
                accepted=True,
                payment_id=payment.id,
                status=payment.status.value,
                message="Payment marked succeeded.",
                processed_at=now,
            )

        if event in {"failed", "failure"}:
            if payment.status not in {PaymentStatus.succeeded, PaymentStatus.cancelled}:
                payment.status = PaymentStatus.failed
                payment.failure_reason = body.failure_reason or "gateway_failed"
                if body.provider_ref:
                    payment.provider_ref = body.provider_ref
                payment.provider = provider
                await self.session.commit()
                await self.session.refresh(payment)
            return PaymentWebhookOut(
                accepted=True,
                payment_id=payment.id,
                status=payment.status.value,
                message="Payment marked failed.",
                processed_at=now,
            )

        if event in {"refunded", "refund"}:
            # Soft-mark: store note; full refund ledger later
            note = f"refund webhook at {now.isoformat()}"
            payment.notes = f"{payment.notes}\n{note}".strip() if payment.notes else note
            if body.provider_ref:
                payment.provider_ref = body.provider_ref
            await self.session.commit()
            await self.session.refresh(payment)
            return PaymentWebhookOut(
                accepted=True,
                payment_id=payment.id,
                status=payment.status.value,
                message="Refund event recorded.",
                processed_at=now,
            )

        raise AppError(
            f"Unsupported webhook event: {body.event}",
            code="unsupported_webhook_event",
            status_code=400,
        )

    async def _resolve_payment(self, body: PaymentWebhookIn) -> Payment:
        if body.payment_id is not None:
            payment = await self.session.get(Payment, body.payment_id)
            if payment is None:
                raise NotFoundError("Payment not found", code="payment_not_found")
            return payment
        if body.provider_ref:
            payment = (
                await self.session.execute(
                    select(Payment)
                    .where(Payment.provider_ref == body.provider_ref)
                    .order_by(Payment.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if payment is None:
                raise NotFoundError("Payment not found", code="payment_not_found")
            return payment
        raise AppError(
            "payment_id or provider_ref is required",
            code="invalid_webhook",
            status_code=400,
        )
