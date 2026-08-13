"""Ops payment support service (Module 8)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, NotFoundError
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.ops_payment import OpsPaymentListOut, OpsPaymentOut, OpsPaymentReconcileIn
from app.schemas.ops_subscription import OpsSubscriptionUserOut


class OpsPaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_payments(
        self,
        *,
        q: str | None = None,
        status: PaymentStatus | None = None,
        subscription_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OpsPaymentListOut:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        filters: list = []
        if status is not None:
            filters.append(Payment.status == status)
        if subscription_id is not None:
            filters.append(Payment.subscription_id == subscription_id)
        if q and q.strip():
            term = q.strip()
            user_filters = [User.phone.ilike(f"%{term}%")]
            try:
                uid = UUID(term)
                filters.append(
                    or_(
                        Payment.id == uid,
                        Payment.user_id == uid,
                        Payment.provider_ref.ilike(f"%{term}%"),
                        Payment.user_id.in_(select(User.id).where(or_(*user_filters))),
                    )
                )
            except ValueError:
                filters.append(
                    or_(
                        Payment.provider_ref.ilike(f"%{term}%"),
                        Payment.user_id.in_(
                            select(User.id).where(
                                or_(
                                    User.phone.ilike(f"%{term}%"),
                                    User.name.ilike(f"%{term}%"),
                                    User.email.ilike(f"%{term}%"),
                                )
                            )
                        ),
                    )
                )

        count_q = select(func.count()).select_from(Payment)
        list_q = (
            select(Payment).options(selectinload(Payment.user)).order_by(Payment.created_at.desc())
        )
        if filters:
            count_q = count_q.where(*filters)
            list_q = list_q.where(*filters)

        total = int((await self.session.execute(count_q)).scalar_one())
        rows = (await self.session.execute(list_q.offset(offset).limit(page_size))).scalars().all()
        return OpsPaymentListOut(
            items=[self._to_out(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_payment(self, payment_id: UUID) -> OpsPaymentOut:
        payment = await self._get(payment_id)
        return self._to_out(payment)

    async def reconcile(
        self,
        payment_id: UUID,
        operator_id: UUID,
        body: OpsPaymentReconcileIn | None = None,
    ) -> OpsPaymentOut:
        """Mark a payment as captured (OPS-PAY-03) for exceptions / manual settle."""
        payment = await self._get(payment_id)
        if payment.status == PaymentStatus.succeeded:
            return self._to_out(payment)
        if payment.status == PaymentStatus.cancelled:
            raise AppError(
                "Cancelled payments cannot be reconciled",
                code="payment_cancelled",
                status_code=409,
            )

        now = datetime.now(UTC)
        payment.status = PaymentStatus.succeeded
        payment.captured_at = payment.captured_at or now
        payment.reconciled_at = now
        payment.reconciled_by_operator_id = operator_id
        payment.failure_reason = None
        if body:
            if body.provider_ref:
                payment.provider_ref = body.provider_ref.strip() or payment.provider_ref
            if body.notes:
                note = body.notes.strip()
                if note:
                    existing = (payment.notes or "").strip()
                    payment.notes = (
                        f"{existing}\n[ops reconcile] {note}".strip()
                        if existing
                        else f"[ops reconcile] {note}"
                    )

        await self.session.commit()
        return await self.get_payment(payment_id)

    async def _get(self, payment_id: UUID) -> Payment:
        result = await self.session.execute(
            select(Payment)
            .options(selectinload(Payment.user))
            .where(Payment.id == payment_id)
            .limit(1)
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            raise NotFoundError("Payment not found", code="payment_not_found")
        return payment

    @staticmethod
    def _to_out(payment: Payment) -> OpsPaymentOut:
        user_out = None
        if payment.user is not None:
            user_out = OpsSubscriptionUserOut.model_validate(payment.user)
        return OpsPaymentOut(
            id=payment.id,
            user_id=payment.user_id,
            user=user_out,
            subscription_id=payment.subscription_id,
            amount_paise=payment.amount_paise,
            currency=payment.currency,
            status=payment.status,
            kind=payment.kind,
            period_start=payment.period_start,
            period_end=payment.period_end,
            provider=payment.provider,
            provider_ref=payment.provider_ref,
            failure_reason=payment.failure_reason,
            captured_at=payment.captured_at,
            reconciled_at=payment.reconciled_at,
            reconciled_by_operator_id=payment.reconciled_by_operator_id,
            notes=payment.notes,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
