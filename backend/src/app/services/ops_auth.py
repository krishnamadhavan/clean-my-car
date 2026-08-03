"""Ops operator authentication (email/password + rotating refresh tokens)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.core.passwords import hash_password, verify_password
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
)
from app.models.ops_operator import OPS_ROLE_CATALOG_ADMIN, OpsOperator
from app.models.ops_refresh_token import OpsRefreshToken


class OpsAuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def login(self, email: str, password: str) -> tuple[OpsOperator, str, str]:
        result = await self.session.execute(
            select(OpsOperator).where(OpsOperator.email == email.strip().lower()).limit(1)
        )
        operator = result.scalar_one_or_none()
        # Constant-ish failure path: still verify a dummy hash shape if missing
        if operator is None or not operator.is_active:
            raise UnauthorizedError("Invalid email or password", code="ops_login_failed")

        if not verify_password(password, operator.password_hash):
            raise UnauthorizedError("Invalid email or password", code="ops_login_failed")

        operator.last_login_at = datetime.now(UTC)
        access, refresh = await self._issue_token_pair(operator)
        await self.session.commit()
        await self.session.refresh(operator)
        return operator, access, refresh

    async def refresh_tokens(self, raw_refresh: str) -> tuple[OpsOperator, str, str]:
        now = datetime.now(UTC)
        token_hash = hash_token(raw_refresh)
        result = await self.session.execute(
            select(OpsRefreshToken).where(OpsRefreshToken.token_hash == token_hash).limit(1)
        )
        stored = result.scalar_one_or_none()
        if stored is None or stored.revoked_at is not None or stored.expires_at <= now:
            raise UnauthorizedError("Invalid refresh token", code="ops_refresh_invalid")

        operator = await self.session.get(OpsOperator, stored.operator_id)
        if operator is None or not operator.is_active:
            raise UnauthorizedError("Invalid refresh token", code="ops_refresh_invalid")

        stored.revoked_at = now
        access, refresh = await self._issue_token_pair(operator)
        await self.session.commit()
        await self.session.refresh(operator)
        return operator, access, refresh

    async def logout(self, raw_refresh: str) -> None:
        """Idempotent: unknown or already-revoked tokens still succeed."""
        token_hash = hash_token(raw_refresh)
        result = await self.session.execute(
            select(OpsRefreshToken).where(OpsRefreshToken.token_hash == token_hash).limit(1)
        )
        stored = result.scalar_one_or_none()
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            await self.session.commit()

    async def ensure_bootstrap_operator(self) -> OpsOperator | None:
        """Create the env-configured operator if that email is not present yet.

        Safe when other operators already exist (e.g. local test data): only inserts
        when ``OPS_BOOTSTRAP_EMAIL`` is missing from ``ops_operators``.
        Does not reset an existing operator's password.
        """
        email = (self.settings.ops_bootstrap_email or "").strip().lower()
        password = self.settings.ops_bootstrap_password or ""
        if not email or not password:
            return None

        if len(password) < 8:
            # Misconfiguration: refuse silent weak bootstrap
            return None

        existing = await self.session.execute(
            select(OpsOperator).where(OpsOperator.email == email).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            return None

        operator = OpsOperator(
            email=email,
            password_hash=hash_password(password),
            name=(self.settings.ops_bootstrap_name or "Bootstrap Admin").strip() or None,
            is_active=True,
            roles=[OPS_ROLE_CATALOG_ADMIN, "field_ops", "support"],
        )
        self.session.add(operator)
        await self.session.commit()
        await self.session.refresh(operator)
        return operator

    async def _issue_token_pair(self, operator: OpsOperator) -> tuple[str, str]:
        access = create_access_token(
            subject=operator.id,
            settings=self.settings,
            token_type="ops_access",
            extra_claims={"roles": list(operator.roles or [])},
        )
        raw_refresh = generate_refresh_token()
        self.session.add(
            OpsRefreshToken(
                operator_id=operator.id,
                token_hash=hash_token(raw_refresh),
                expires_at=datetime.now(UTC)
                + timedelta(days=self.settings.refresh_token_expire_days),
            )
        )
        return access, raw_refresh
