"""Ops payment endpoints — Module 8 (Should + Could)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.models.payment import PaymentStatus
from app.schemas.ops_payment import OpsPaymentListOut, OpsPaymentOut, OpsPaymentReconcileIn
from app.services.ops_payment import OpsPaymentService

router = APIRouter(prefix="/payments", tags=["ops-payments"])


def get_ops_payment_service(db: DbSession) -> OpsPaymentService:
    return OpsPaymentService(session=db)


OpsPaymentServiceDep = Annotated[OpsPaymentService, Depends(get_ops_payment_service)]


@router.get(
    "",
    response_model=OpsPaymentListOut,
    summary="Search payments / intents (OPS-PAY-01)",
)
async def list_payments(
    _ops: CurrentOpsOperator,
    svc: OpsPaymentServiceDep,
    q: Annotated[
        str | None,
        Query(description="Phone, name, payment id, user id, or provider_ref"),
    ] = None,
    status: Annotated[PaymentStatus | None, Query()] = None,
    subscription_id: Annotated[UUID | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OpsPaymentListOut:
    return await svc.list_payments(
        q=q,
        status=status,
        subscription_id=subscription_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{payment_id}",
    response_model=OpsPaymentOut,
    summary="Payment detail (OPS-PAY-02)",
)
async def get_payment(
    payment_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsPaymentServiceDep,
) -> OpsPaymentOut:
    return await svc.get_payment(payment_id)


@router.post(
    "/{payment_id}/reconcile",
    response_model=OpsPaymentOut,
    status_code=status.HTTP_200_OK,
    summary="Manual mark payment captured (OPS-PAY-03)",
)
async def reconcile_payment(
    payment_id: UUID,
    ops: CurrentOpsOperator,
    svc: OpsPaymentServiceDep,
    body: OpsPaymentReconcileIn | None = None,
) -> OpsPaymentOut:
    return await svc.reconcile(payment_id, operator_id=ops.id, body=body)
