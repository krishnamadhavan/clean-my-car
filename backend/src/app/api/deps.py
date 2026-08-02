"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth import AuthService

DbSession = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

_bearer = HTTPBearer(auto_error=False)


def get_auth_service(db: DbSession, settings: SettingsDep) -> AuthService:
    return AuthService(session=db, settings=settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def _resolve_user_from_bearer(
    db: AsyncSession,
    settings: Settings,
    credentials: HTTPAuthorizationCredentials | None,
    *,
    required: bool,
) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        if required:
            raise UnauthorizedError("Missing bearer token")
        return None

    try:
        payload = decode_access_token(credentials.credentials, settings=settings)
    except jwt.PyJWTError as exc:
        if required:
            raise UnauthorizedError(
                "Invalid or expired access token", code="token_invalid"
            ) from exc
        return None

    if payload.get("type") != "access":
        if required:
            raise UnauthorizedError("Invalid access token", code="token_invalid")
        return None

    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        if required:
            raise UnauthorizedError("Invalid access token", code="token_invalid") from exc
        return None

    user = await db.get(User, user_id)
    if user is None or user.deleted_at is not None or not user.is_active:
        if required:
            if user is not None and user.deleted_at is not None:
                raise UnauthorizedError("Account has been deleted", code="account_deleted")
            raise UnauthorizedError("User not found or inactive", code="user_inactive")
        return None
    return user


async def get_current_user(
    db: DbSession,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    user = await _resolve_user_from_bearer(db, settings, credentials, required=True)
    assert user is not None
    return user


async def get_optional_current_user(
    db: DbSession,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User | None:
    """Return the authenticated user if a valid bearer token is present; else None."""
    return await _resolve_user_from_bearer(db, settings, credentials, required=False)


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]
