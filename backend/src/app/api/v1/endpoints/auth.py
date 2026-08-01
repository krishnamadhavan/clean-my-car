"""Auth endpoints — Module 1 (Must): OTP login, refresh, logout."""

from datetime import timedelta

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep, SettingsDep
from app.schemas.auth import (
    AccessTokenOut,
    LogoutIn,
    MessageOut,
    OtpRequestIn,
    OtpRequestOut,
    OtpVerifyIn,
    RefreshTokenIn,
    TokenPairOut,
)
from app.schemas.user import UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/otp/request",
    response_model=OtpRequestOut,
    status_code=status.HTTP_200_OK,
    summary="Request OTP (AUTH-01)",
)
async def request_otp(
    body: OtpRequestIn,
    auth: AuthServiceDep,
    settings: SettingsDep,
) -> OtpRequestOut:
    challenge, otp = await auth.request_otp(body.phone)

    env = settings.app_env.lower()
    if env in {"production", "prod"}:
        debug_otp = otp if settings.otp_return_in_response else None
    else:
        # development / test: return OTP so clients and automated tests can verify
        debug_otp = otp

    resend_at = challenge.created_at + timedelta(seconds=settings.otp_resend_cooldown_seconds)
    return OtpRequestOut(
        phone=challenge.phone,
        expires_at=challenge.expires_at,
        resend_available_at=resend_at,
        debug_otp=debug_otp,
    )


@router.post(
    "/otp/verify",
    response_model=TokenPairOut,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and issue tokens (AUTH-02)",
)
async def verify_otp(
    body: OtpVerifyIn,
    auth: AuthServiceDep,
    settings: SettingsDep,
) -> TokenPairOut:
    user, access, refresh = await auth.verify_otp(body.phone, body.otp)
    return TokenPairOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserPublic.model_validate(user),
    )


@router.post(
    "/token/refresh",
    response_model=AccessTokenOut,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token (AUTH-03)",
)
async def refresh_token(
    body: RefreshTokenIn,
    auth: AuthServiceDep,
    settings: SettingsDep,
) -> AccessTokenOut:
    _user, access, new_refresh = await auth.refresh_tokens(body.refresh_token)
    return AccessTokenOut(
        access_token=access,
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_token=new_refresh,
    )


@router.post(
    "/logout",
    response_model=MessageOut,
    status_code=status.HTTP_200_OK,
    summary="Revoke refresh token (AUTH-04)",
)
async def logout(body: LogoutIn, auth: AuthServiceDep) -> MessageOut:
    await auth.logout(body.refresh_token)
    return MessageOut(message="Logged out")
