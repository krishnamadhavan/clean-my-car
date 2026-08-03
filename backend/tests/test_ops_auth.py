"""Ops Module 1 — operator auth tests."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from httpx import AsyncClient

from app.core.config import get_settings
from app.core.passwords import hash_password, verify_password
from app.core.security import create_access_token
from app.db.session import AsyncSessionLocal
from app.models.ops_operator import OPS_ROLE_CATALOG_ADMIN, OpsOperator
from app.services.ops_auth import OpsAuthService


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


def _email(prefix: str = "ops") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@ops.test"


async def _create_operator(
    *,
    email: str | None = None,
    password: str = "password99",
    roles: list[str] | None = None,
    is_active: bool = True,
) -> tuple[OpsOperator, str, str]:
    """Returns (operator, email, password)."""
    email = email or _email()
    password = password
    async with AsyncSessionLocal() as session:
        op = OpsOperator(
            email=email.lower(),
            password_hash=hash_password(password),
            name="Ops Admin",
            is_active=is_active,
            roles=roles or [OPS_ROLE_CATALOG_ADMIN],
        )
        session.add(op)
        await session.commit()
        await session.refresh(op)
        return op, email, password


def test_password_hash_roundtrip() -> None:
    stored = hash_password("correct horse")
    assert verify_password("correct horse", stored)
    assert not verify_password("wrong", stored)
    assert not verify_password("x", "not-a-valid-hash")
    assert not verify_password("x", "scrypt$zz$nothex")


async def test_ops_login_success(client: AsyncClient) -> None:
    _op, email, password = await _create_operator()
    response = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email.upper(), "password": password},  # case-insensitive email
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["operator"]["email"] == email.lower()
    assert "catalog_admin" in body["operator"]["roles"]


async def test_ops_login_bad_password(client: AsyncClient) -> None:
    _op, email, _pw = await _create_operator()
    response = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": "wrongpass1"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "ops_login_failed"


async def test_ops_login_inactive(client: AsyncClient) -> None:
    _op, email, password = await _create_operator(is_active=False)
    response = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 401


async def test_ops_me_and_consumer_token_rejected(client: AsyncClient) -> None:
    _op, email, password = await _create_operator()
    login = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": password},
    )
    access = login.json()["access_token"]

    me = await client.get("/api/v1/ops/auth/me", headers=_auth(access))
    assert me.status_code == 200
    assert me.json()["email"] == email.lower()

    consumer = await client.get("/api/v1/me", headers=_auth(access))
    assert consumer.status_code == 401


async def test_ops_refresh_and_logout(client: AsyncClient) -> None:
    _op, email, password = await _create_operator()
    login = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": password},
    )
    refresh = login.json()["refresh_token"]

    refreshed = await client.post(
        "/api/v1/ops/auth/token/refresh",
        json={"refresh_token": refresh},
    )
    assert refreshed.status_code == 200, refreshed.text
    new_refresh = refreshed.json()["refresh_token"]
    assert new_refresh != refresh

    again = await client.post(
        "/api/v1/ops/auth/token/refresh",
        json={"refresh_token": refresh},
    )
    assert again.status_code == 401

    logout = await client.post(
        "/api/v1/ops/auth/logout",
        json={"refresh_token": new_refresh},
    )
    assert logout.status_code == 200

    logout2 = await client.post(
        "/api/v1/ops/auth/logout",
        json={"refresh_token": new_refresh},
    )
    assert logout2.status_code == 200

    dead = await client.post(
        "/api/v1/ops/auth/token/refresh",
        json={"refresh_token": new_refresh},
    )
    assert dead.status_code == 401


async def test_ops_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ops/auth/me")
    assert response.status_code == 401


async def test_bootstrap_operator_once() -> None:
    settings = get_settings()
    email = _email("boot")
    async with AsyncSessionLocal() as session:
        base = SimpleNamespace(
            ops_bootstrap_email=email,
            ops_bootstrap_password="bootstrap1",
            ops_bootstrap_name="Boot",
            access_token_expire_minutes=settings.access_token_expire_minutes,
            refresh_token_expire_days=settings.refresh_token_expire_days,
            jwt_secret_key=settings.jwt_secret_key,
            jwt_algorithm=settings.jwt_algorithm,
        )
        svc = OpsAuthService(session, base)  # type: ignore[arg-type]
        # Works even when other operators already exist
        first = await svc.ensure_bootstrap_operator()
        assert first is not None
        assert first.email == email
        second = await svc.ensure_bootstrap_operator()
        assert second is None  # same email already present

        weak = SimpleNamespace(**{**base.__dict__, "ops_bootstrap_password": "short"})
        assert await OpsAuthService(session, weak).ensure_bootstrap_operator() is None  # type: ignore[arg-type]

        empty_email = SimpleNamespace(**{**base.__dict__, "ops_bootstrap_email": ""})
        assert (
            await OpsAuthService(session, empty_email).ensure_bootstrap_operator()  # type: ignore[arg-type]
            is None
        )


async def test_consumer_access_token_rejected_on_ops_me(client: AsyncClient) -> None:
    settings = get_settings()
    op, _email, _pw = await _create_operator()
    fake = create_access_token(subject=op.id, settings=settings, token_type="access")
    response = await client.get("/api/v1/ops/auth/me", headers=_auth(fake))
    assert response.status_code == 401
    assert response.json()["code"] == "ops_token_invalid"


async def test_ops_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": _email("nobody"), "password": "password99"},
    )
    assert response.status_code == 401


async def test_ops_login_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": "a@b.co", "password": "short"},
    )
    assert response.status_code == 422


async def test_ops_login_rejects_bad_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": "not-an-email", "password": "password99"},
    )
    assert response.status_code == 422


async def test_ops_refresh_fails_if_operator_deactivated(client: AsyncClient) -> None:
    op, email, password = await _create_operator()
    login = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": password},
    )
    refresh = login.json()["refresh_token"]

    async with AsyncSessionLocal() as session:
        row = await session.get(OpsOperator, op.id)
        assert row is not None
        row.is_active = False
        await session.commit()

    response = await client.post(
        "/api/v1/ops/auth/token/refresh",
        json={"refresh_token": refresh},
    )
    assert response.status_code == 401


async def test_ops_me_fails_if_operator_deactivated(client: AsyncClient) -> None:
    op, email, password = await _create_operator()
    login = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": password},
    )
    access = login.json()["access_token"]

    async with AsyncSessionLocal() as session:
        row = await session.get(OpsOperator, op.id)
        assert row is not None
        row.is_active = False
        await session.commit()

    response = await client.get("/api/v1/ops/auth/me", headers=_auth(access))
    assert response.status_code == 401
    assert response.json()["code"] == "ops_operator_inactive"
