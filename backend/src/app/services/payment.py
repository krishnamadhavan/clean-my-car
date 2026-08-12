"""Consumer payments and billing summary (Module 8)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.payment import Payment, PaymentKind, PaymentStatus
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.payment import (
    BillingSummaryOut,
    PaymentConfirmIn,
    PaymentIntentCreateIn,
    PaymentListOut,
    PaymentOut,
)
from app.services.subscription import SubscriptionService


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subscriptions = SubscriptionService(session)

    async def create_intent(
        self,
        user: User,
        body: PaymentIntentCreateIn | None = None,
    ) -> PaymentOut:
        sub = await self._resolve_subscription(user, body.subscription_id if body else None)
        if sub.status not in {
            SubscriptionStatus.pending_payment,
            SubscriptionStatus.active,
            SubscriptionStatus.cancel_scheduled,
        }:
            raise AppError(
                "Subscription is not billable in its current status",
                code="subscription_not_billable",
                status_code=409,
            )

        # Reuse open pending intent for same period if present
        existing = await self._open_intent(user.id, sub.id)
        if existing is not None:
            return PaymentOut.model_validate(existing)

        amount = sub.monthly_amount_paise
        kind = PaymentKind.renewal
        if sub.status == SubscriptionStatus.pending_payment:
            kind = PaymentKind.subscription_start
            # Prefer amount from any prior pending start intent path; full month if already set
            amount = sub.monthly_amount_paise

        # For first period still pending, keep amount from original start if we re-create
        # (start flow already created the intent with pro-rate amount)
        payment = Payment(
            user_id=user.id,
            subscription_id=sub.id,
            amount_paise=amount,
            currency=sub.currency,
            status=PaymentStatus.pending,
            kind=kind,
            period_start=sub.period_start,
            period_end=sub.period_end,
            provider="manual",
        )
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return PaymentOut.model_validate(payment)

    async def get_intent(self, user: User, intent_id: UUID) -> PaymentOut:
        payment = await self._get_user_payment(user.id, intent_id)
        return PaymentOut.model_validate(payment)

    async def confirm_intent(
        self,
        user: User,
        intent_id: UUID,
        body: PaymentConfirmIn | None = None,
    ) -> PaymentOut:
        """Mark intent paid (manual/dev provider; gateway webhooks later)."""
        payment = await self._get_user_payment(user.id, intent_id)
        if payment.status == PaymentStatus.succeeded:
            return PaymentOut.model_validate(payment)
        if payment.status in {PaymentStatus.cancelled, PaymentStatus.failed}:
            # Allow confirm from failed for manual retry path
            if payment.status == PaymentStatus.cancelled:
                raise AppError(
                    "Payment was cancelled",
                    code="payment_cancelled",
                    status_code=409,
                )

        now = datetime.now(UTC)
        payment.status = PaymentStatus.succeeded
        payment.captured_at = now
        payment.failure_reason = None
        if body and body.provider_ref:
            payment.provider_ref = body.provider_ref.strip() or payment.provider_ref

        if payment.subscription_id is not None:
            sub = await self.session.get(Subscription, payment.subscription_id)
            if sub is not None and sub.status == SubscriptionStatus.pending_payment:
                sub.status = SubscriptionStatus.active

        await self.session.commit()
        await self.session.refresh(payment)
        return PaymentOut.model_validate(payment)

    async def list_payments(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaymentListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(Payment).where(Payment.user_id == user.id)
                )
            ).scalar_one()
        )
        rows = (
            (
                await self.session.execute(
                    select(Payment)
                    .where(Payment.user_id == user.id)
                    .order_by(Payment.created_at.desc())
                    .offset(offset)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return PaymentListOut(
            items=[PaymentOut.model_validate(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def billing_summary(self, user: User) -> BillingSummaryOut:
        sub = await self.subscriptions._get_open(user.id)
        if sub is None:
            return BillingSummaryOut(
                has_subscription=False,
                message="No active subscription.",
            )

        open_intent = await self._open_intent(user.id, sub.id)
        amount_due = open_intent.amount_paise if open_intent else 0
        is_overdue = sub.status == SubscriptionStatus.pending_payment and open_intent is not None
        if sub.status == SubscriptionStatus.pending_payment:
            message = "Pay to activate service for this period."
        elif open_intent is not None:
            message = "Payment due for the current period."
        elif sub.status == SubscriptionStatus.cancel_scheduled:
            end = sub.cancel_at or sub.period_end
            message = f"Service continues until {end}. No further charge after that."
        else:
            message = "Nothing due right now."

        return BillingSummaryOut(
            has_subscription=True,
            subscription_id=sub.id,
            subscription_status=sub.status.value,
            amount_due_paise=amount_due,
            currency=sub.currency,
            period_start=sub.period_start,
            period_end=sub.period_end,
            is_overdue=is_overdue,
            open_payment_intent_id=open_intent.id if open_intent else None,
            message=message,
        )

    async def _resolve_subscription(self, user: User, subscription_id: UUID | None) -> Subscription:
        if subscription_id is not None:
            sub = await self.session.get(Subscription, subscription_id)
            if sub is None or sub.user_id != user.id:
                raise NotFoundError("Subscription not found", code="subscription_not_found")
            return sub
        sub = await self.subscriptions._get_open(user.id)
        if sub is None:
            raise NotFoundError("No subscription", code="subscription_not_found")
        return sub

    async def _open_intent(self, user_id: UUID, subscription_id: UUID) -> Payment | None:
        result = await self.session.execute(
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.subscription_id == subscription_id,
                Payment.status == PaymentStatus.pending,
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_user_payment(self, user_id: UUID, payment_id: UUID) -> Payment:
        payment = await self.session.get(Payment, payment_id)
        if payment is None or payment.user_id != user_id:
            raise NotFoundError("Payment not found", code="payment_not_found")
        return payment
