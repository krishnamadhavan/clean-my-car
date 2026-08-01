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


async def get_current_user(
    db: DbSession,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing bearer token")

    try:
        payload = decode_access_token(credentials.credentials, settings=settings)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired access token", code="token_invalid") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid access token", code="token_invalid")

    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Invalid access token", code="token_invalid") from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive", code="user_inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
