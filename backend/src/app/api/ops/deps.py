"""Ops-specific FastAPI dependencies (ops JWT ≠ consumer JWT)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import DbSession, SettingsDep
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.models.ops_operator import OpsOperator
from app.services.ops_auth import OpsAuthService

_bearer = HTTPBearer(auto_error=False)


def get_ops_auth_service(db: DbSession, settings: SettingsDep) -> OpsAuthService:
    return OpsAuthService(session=db, settings=settings)


OpsAuthServiceDep = Annotated[OpsAuthService, Depends(get_ops_auth_service)]


async def get_current_ops_operator(
    db: DbSession,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> OpsOperator:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing bearer token", code="ops_unauthorized")

    try:
        payload = decode_access_token(credentials.credentials, settings=settings)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError(
            "Invalid or expired access token", code="ops_token_invalid"
        ) from exc

    if payload.get("type") != "ops_access":
        raise UnauthorizedError("Invalid ops access token", code="ops_token_invalid")

    try:
        operator_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Invalid ops access token", code="ops_token_invalid") from exc

    operator = await db.get(OpsOperator, operator_id)
    if operator is None or not operator.is_active:
        raise UnauthorizedError("Operator not found or inactive", code="ops_operator_inactive")
    return operator


CurrentOpsOperator = Annotated[OpsOperator, Depends(get_current_ops_operator)]
