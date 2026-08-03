"""Ops auth endpoints — Module 1 (Must + Should)."""

from fastapi import APIRouter, status

from app.api.deps import SettingsDep
from app.api.ops.deps import CurrentOpsOperator, OpsAuthServiceDep
from app.schemas.ops_auth import (
    OpsAccessTokenOut,
    OpsLoginIn,
    OpsLogoutIn,
    OpsMessageOut,
    OpsOperatorPublic,
    OpsRefreshIn,
    OpsTokenPairOut,
)

router = APIRouter(prefix="/auth", tags=["ops-auth"])


@router.post(
    "/login",
    response_model=OpsTokenPairOut,
    status_code=status.HTTP_200_OK,
    summary="Ops operator login (OPS-AUTH-01)",
)
async def ops_login(
    body: OpsLoginIn,
    auth: OpsAuthServiceDep,
    settings: SettingsDep,
) -> OpsTokenPairOut:
    operator, access, refresh = await auth.login(body.email, body.password)
    return OpsTokenPairOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
        operator=OpsOperatorPublic.model_validate(operator),
    )


@router.post(
    "/logout",
    response_model=OpsMessageOut,
    status_code=status.HTTP_200_OK,
    summary="Revoke ops refresh token (OPS-AUTH-02)",
)
async def ops_logout(body: OpsLogoutIn, auth: OpsAuthServiceDep) -> OpsMessageOut:
    await auth.logout(body.refresh_token)
    return OpsMessageOut(message="Logged out")


@router.post(
    "/token/refresh",
    response_model=OpsAccessTokenOut,
    status_code=status.HTTP_200_OK,
    summary="Refresh ops access token (OPS-AUTH-03)",
)
async def ops_refresh(
    body: OpsRefreshIn,
    auth: OpsAuthServiceDep,
    settings: SettingsDep,
) -> OpsAccessTokenOut:
    _operator, access, new_refresh = await auth.refresh_tokens(body.refresh_token)
    return OpsAccessTokenOut(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=OpsOperatorPublic,
    summary="Current ops operator (OPS-AUTH-04)",
)
async def ops_me(operator: CurrentOpsOperator) -> OpsOperatorPublic:
    return OpsOperatorPublic.model_validate(operator)
