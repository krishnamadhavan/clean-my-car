"""Payment webhooks — Module 14 (WH-01, WH-02)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.webhook import PaymentWebhookIn, PaymentWebhookOut
from app.services.webhook import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def get_webhook_service(db: DbSession) -> WebhookService:
    return WebhookService(session=db)


WebhookServiceDep = Annotated[WebhookService, Depends(get_webhook_service)]


@router.post(
    "/payments/{provider}",
    response_model=PaymentWebhookOut,
    summary="Payment gateway webhook (WH-01)",
)
async def payment_webhook(
    provider: str,
    body: PaymentWebhookIn,
    svc: WebhookServiceDep,
) -> PaymentWebhookOut:
    return await svc.handle_payment_event(provider, body)


@router.post(
    "/payments/{provider}/refunds",
    response_model=PaymentWebhookOut,
    summary="Refund gateway webhook (WH-02)",
)
async def payment_refund_webhook(
    provider: str,
    body: PaymentWebhookIn,
    svc: WebhookServiceDep,
) -> PaymentWebhookOut:
    # Force refund event path when provider hits refunds URL without event field
    if body.event not in {"refunded", "refund"}:
        body = PaymentWebhookIn(
            event="refunded",
            payment_id=body.payment_id,
            provider_ref=body.provider_ref,
            failure_reason=body.failure_reason,
            amount_paise=body.amount_paise,
        )
    return await svc.handle_payment_event(provider, body)
