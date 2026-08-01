"""Profile module tests (Module 2 — Must + Should)."""

from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import register_and_login, unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def test_get_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")
    assert response.status_code == 401


async def test_get_me(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    response = await client.get("/api/v1/me", headers=_auth(tokens["access_token"]))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["phone"].startswith("+91")
    assert body["is_active"] is True
    assert body["has_vehicle"] is False
    assert body["has_subscription"] is False
    assert body["name"] is None
    assert body["deleted_at"] is None


async def test_patch_me(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    updated = await client.patch(
        "/api/v1/me",
        headers=headers,
        json={"name": "  Krishna  ", "email": "Krishna@Example.com"},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["name"] == "Krishna"
    assert body["email"] == "krishna@example.com"

    # Partial update — only name
    again = await client.patch("/api/v1/me", headers=headers, json={"name": "K"})
    assert again.status_code == 200
    assert again.json()["name"] == "K"
    assert again.json()["email"] == "krishna@example.com"

    # Clear email with null
    cleared = await client.patch("/api/v1/me", headers=headers, json={"email": None})
    assert cleared.status_code == 200
    assert cleared.json()["email"] is None


async def test_patch_me_rejects_bad_email(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    response = await client.patch(
        "/api/v1/me",
        headers=_auth(tokens["access_token"]),
        json={"email": "not-an-email"},
    )
    assert response.status_code == 422


async def test_deactivate_blocks_access(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    deactivated = await client.post("/api/v1/me/deactivate", headers=_auth(access))
    assert deactivated.status_code == 200, deactivated.text

    me = await client.get("/api/v1/me", headers=_auth(access))
    assert me.status_code == 401

    refreshed = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": refresh},
    )
    assert refreshed.status_code == 401


async def test_delete_account_blocks_login_during_cooloff(client: AsyncClient) -> None:
    phone = unique_phone()
    tokens = await register_and_login(client, phone=phone)
    access = tokens["access_token"]

    deleted = await client.delete("/api/v1/me", headers=_auth(access))
    assert deleted.status_code == 200, deleted.text

    me = await client.get("/api/v1/me", headers=_auth(access))
    assert me.status_code == 401

    # Same phone cannot complete OTP verify during cool-off (default 1 day)
    req = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert req.status_code == 200
    otp = req.json()["debug_otp"]
    verify = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": otp},
    )
    assert verify.status_code == 403
    body = verify.json()
    assert body["code"] == "account_deletion_cooling_off"
    assert "available_at" in body["details"]
    assert body["details"]["cooloff_days"] == 1.0


async def test_reregister_after_cooloff_elapsed(client: AsyncClient) -> None:
    """After cool-off, OTP verify reactivates the same phone account."""
    from datetime import UTC, datetime, timedelta

    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import update

    phone = unique_phone()
    tokens = await register_and_login(client, phone=phone)
    deleted = await client.delete("/api/v1/me", headers=_auth(tokens["access_token"]))
    assert deleted.status_code == 200

    # Simulate cool-off already finished (deleted 2 days ago; default cool-off = 1 day)
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.phone == f"+91{phone}")
            .values(deleted_at=datetime.now(UTC) - timedelta(days=2))
        )
        await session.commit()

    again = await register_and_login(client, phone=phone)
    assert again["access_token"]
    assert again["user"]["phone"] == f"+91{phone}"
    assert again["user"]["is_active"] is True

    me = await client.get("/api/v1/me", headers=_auth(again["access_token"]))
    assert me.status_code == 200
    assert me.json()["deleted_at"] is None
