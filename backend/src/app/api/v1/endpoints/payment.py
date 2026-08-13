"""Consumer payment and billing endpoints — Module 8 (Must + Should)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.payment import (
    BillingSummaryOut,
    PaymentConfirmIn,
    PaymentIntentCreateIn,
    PaymentListOut,
    PaymentOut,
)
from app.services.payment import PaymentService

router = APIRouter(tags=["payments"])


def get_payment_service(db: DbSession) -> PaymentService:
    return PaymentService(session=db)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]


@router.post(
    "/me/payments/intents",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create payment intent (PAY-01)",
)
async def create_payment_intent(
    user: CurrentUser,
    svc: PaymentServiceDep,
    body: PaymentIntentCreateIn | None = None,
) -> PaymentOut:
    return await svc.create_intent(user, body)


@router.get(
    "/me/payments/intents/{intent_id}",
    response_model=PaymentOut,
    summary="Get payment intent status (PAY-02)",
)
async def get_payment_intent(
    intent_id: UUID,
    user: CurrentUser,
    svc: PaymentServiceDep,
) -> PaymentOut:
    return await svc.get_intent(user, intent_id)


@router.post(
    "/me/payments/intents/{intent_id}/confirm",
    response_model=PaymentOut,
    summary="Confirm payment intent (PAY-03)",
)
async def confirm_payment_intent(
    intent_id: UUID,
    user: CurrentUser,
    svc: PaymentServiceDep,
    body: PaymentConfirmIn | None = None,
) -> PaymentOut:
    return await svc.confirm_intent(user, intent_id, body)


@router.get(
    "/me/payments",
    response_model=PaymentListOut,
    summary="Payment history (PAY-04)",
)
async def list_payments(
    user: CurrentUser,
    svc: PaymentServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaymentListOut:
    return await svc.list_payments(user, page=page, page_size=page_size)


@router.get(
    "/me/billing/summary",
    response_model=BillingSummaryOut,
    summary="Billing summary (PAY-07)",
)
async def billing_summary(
    user: CurrentUser,
    svc: PaymentServiceDep,
) -> BillingSummaryOut:
    return await svc.billing_summary(user)
