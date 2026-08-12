"""Consumer subscription endpoints — Module 7 (Must)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.subscription import (
    SubscriptionOut,
    SubscriptionStartIn,
    SubscriptionStartOut,
)
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/me/subscription", tags=["subscription"])


def get_subscription_service(db: DbSession) -> SubscriptionService:
    return SubscriptionService(session=db)


SubscriptionServiceDep = Annotated[SubscriptionService, Depends(get_subscription_service)]


@router.get(
    "",
    response_model=SubscriptionOut,
    summary="Current subscription (SUB-01)",
)
async def get_subscription(
    user: CurrentUser,
    svc: SubscriptionServiceDep,
) -> SubscriptionOut:
    return await svc.get_current(user)


@router.post(
    "",
    response_model=SubscriptionStartOut,
    status_code=status.HTTP_201_CREATED,
    summary="Start subscription (SUB-02)",
)
async def start_subscription(
    body: SubscriptionStartIn,
    user: CurrentUser,
    svc: SubscriptionServiceDep,
) -> SubscriptionStartOut:
    return await svc.start(user, body)


@router.post(
    "/cancel",
    response_model=SubscriptionOut,
    summary="Cancel at end of current calendar month (SUB-03)",
)
async def cancel_subscription(
    user: CurrentUser,
    svc: SubscriptionServiceDep,
) -> SubscriptionOut:
    return await svc.cancel(user)


@router.post(
    "/cancel/undo",
    response_model=SubscriptionOut,
    summary="Undo scheduled cancel (SUB-04)",
)
async def undo_cancel_subscription(
    user: CurrentUser,
    svc: SubscriptionServiceDep,
) -> SubscriptionOut:
    return await svc.undo_cancel(user)
