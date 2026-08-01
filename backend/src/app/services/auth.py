"""Auth domain service: OTP request/verify, tokens, logout."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AppError, RateLimitError, UnauthorizedError
from app.core.phone import normalize_indian_phone
from app.core.security import (
    create_access_token,
    generate_otp,
    generate_refresh_token,
    hash_otp,
    hash_token,
    verify_otp,
)
from app.models.otp_challenge import OtpChallenge
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.sms import SmsSender, get_sms_sender


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        sms: SmsSender | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.sms = sms or get_sms_sender()

    async def request_otp(self, raw_phone: str) -> tuple[OtpChallenge, str]:
        phone = normalize_indian_phone(raw_phone)
        now = datetime.now(UTC)

        await self._enforce_otp_rate_limits(phone, now)

        otp = generate_otp(self.settings.otp_length)
        challenge = OtpChallenge(
            phone=phone,
            code_hash=hash_otp(otp, secret=self.settings.jwt_secret_key),
            expires_at=now + timedelta(minutes=self.settings.otp_expire_minutes),
            attempt_count=0,
        )
        self.session.add(challenge)
        await self.session.commit()
        await self.session.refresh(challenge)

        await self.sms.send_otp(phone, otp)
        return challenge, otp

    async def verify_otp(self, raw_phone: str, otp: str) -> tuple[User, str, str]:
        phone = normalize_indian_phone(raw_phone)
        now = datetime.now(UTC)

        result = await self.session.execute(
            select(OtpChallenge)
            .where(
                OtpChallenge.phone == phone,
                OtpChallenge.consumed_at.is_(None),
                OtpChallenge.expires_at > now,
            )
            .order_by(OtpChallenge.created_at.desc())
            .limit(1)
        )
        challenge = result.scalar_one_or_none()
        if challenge is None:
            raise UnauthorizedError("Invalid or expired OTP", code="otp_invalid")

        if challenge.attempt_count >= self.settings.otp_max_attempts:
            raise RateLimitError("Too many invalid OTP attempts", code="otp_attempts_exceeded")

        if not verify_otp(otp, challenge.code_hash, secret=self.settings.jwt_secret_key):
            challenge.attempt_count += 1
            await self.session.commit()
            remaining = self.settings.otp_max_attempts - challenge.attempt_count
            raise UnauthorizedError(
                f"Invalid OTP ({max(remaining, 0)} attempts remaining)",
                code="otp_invalid",
            )

        challenge.consumed_at = now
        user = await self._get_or_create_user(phone)
        if not user.is_active:
            raise AppError("Account is deactivated", code="account_inactive", status_code=403)

        access, refresh = await self._issue_token_pair(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user, access, refresh

    async def refresh_tokens(self, raw_refresh: str) -> tuple[User, str, str]:
        now = datetime.now(UTC)
        token_hash = hash_token(raw_refresh)

        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash).limit(1)
        )
        stored = result.scalar_one_or_none()
        if stored is None or stored.revoked_at is not None or stored.expires_at <= now:
            raise UnauthorizedError("Invalid refresh token", code="refresh_invalid")

        user = await self.session.get(User, stored.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid refresh token", code="refresh_invalid")

        # Rotate refresh token
        stored.revoked_at = now
        access, refresh = await self._issue_token_pair(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user, access, refresh

    async def logout(self, raw_refresh: str) -> None:
        token_hash = hash_token(raw_refresh)
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash).limit(1)
        )
        stored = result.scalar_one_or_none()
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            await self.session.commit()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def _get_or_create_user(self, phone: str) -> User:
        result = await self.session.execute(select(User).where(User.phone == phone).limit(1))
        user = result.scalar_one_or_none()
        if user is not None:
            return user
        user = User(phone=phone)
        self.session.add(user)
        await self.session.flush()
        return user

    async def _issue_token_pair(self, user: User) -> tuple[str, str]:
        access = create_access_token(subject=user.id, settings=self.settings)
        raw_refresh = generate_refresh_token()
        refresh_row = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=datetime.now(UTC) + timedelta(days=self.settings.refresh_token_expire_days),
        )
        self.session.add(refresh_row)
        return access, raw_refresh

    async def _enforce_otp_rate_limits(self, phone: str, now: datetime) -> None:
        cooldown = now - timedelta(seconds=self.settings.otp_resend_cooldown_seconds)
        recent = await self.session.execute(
            select(OtpChallenge)
            .where(OtpChallenge.phone == phone, OtpChallenge.created_at >= cooldown)
            .order_by(OtpChallenge.created_at.desc())
            .limit(1)
        )
        if recent.scalar_one_or_none() is not None:
            wait = self.settings.otp_resend_cooldown_seconds
            raise RateLimitError(
                f"Please wait {wait}s before requesting another OTP",
                code="otp_cooldown",
            )

        hour_ago = now - timedelta(hours=1)
        count_result = await self.session.execute(
            select(func.count())
            .select_from(OtpChallenge)
            .where(OtpChallenge.phone == phone, OtpChallenge.created_at >= hour_ago)
        )
        count = int(count_result.scalar_one())
        if count >= self.settings.otp_max_requests_per_hour:
            raise RateLimitError(
                "OTP request limit reached. Try again later.",
                code="otp_rate_limited",
            )
