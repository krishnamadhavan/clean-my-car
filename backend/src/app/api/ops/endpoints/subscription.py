"""Ops subscription endpoints — Module 7 (Should + Could)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.models.subscription import SubscriptionStatus
from app.schemas.ops_subscription import (
    OpsSubscriptionCancelIn,
    OpsSubscriptionListOut,
    OpsSubscriptionOut,
)
from app.services.ops_subscription import OpsSubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["ops-subscriptions"])


def get_ops_subscription_service(db: DbSession) -> OpsSubscriptionService:
    return OpsSubscriptionService(session=db)


OpsSubscriptionServiceDep = Annotated[OpsSubscriptionService, Depends(get_ops_subscription_service)]


@router.get(
    "",
    response_model=OpsSubscriptionListOut,
    summary="Search subscriptions (OPS-SUB-01)",
)
async def list_subscriptions(
    _ops: CurrentOpsOperator,
    svc: OpsSubscriptionServiceDep,
    q: Annotated[
        str | None,
        Query(description="Phone, name, email, user id, or subscription id"),
    ] = None,
    status: Annotated[SubscriptionStatus | None, Query()] = None,
    society_id: Annotated[UUID | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OpsSubscriptionListOut:
    return await svc.list_subscriptions(
        q=q,
        status=status,
        society_id=society_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{subscription_id}",
    response_model=OpsSubscriptionOut,
    summary="Subscription detail (OPS-SUB-02)",
)
async def get_subscription(
    subscription_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsSubscriptionServiceDep,
) -> OpsSubscriptionOut:
    return await svc.get_subscription(subscription_id)


@router.post(
    "/{subscription_id}/cancel",
    response_model=OpsSubscriptionOut,
    status_code=status.HTTP_200_OK,
    summary="Admin schedule cancel at period end (OPS-SUB-03)",
)
async def cancel_subscription(
    subscription_id: UUID,
    _ops: CurrentOpsOperator,
    svc: OpsSubscriptionServiceDep,
    body: OpsSubscriptionCancelIn | None = None,
) -> OpsSubscriptionOut:
    return await svc.admin_cancel(subscription_id, body)
