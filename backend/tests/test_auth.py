"""Auth module integration tests (requires Postgres)."""

from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import unique_phone as _unique_phone


async def test_otp_request_normalizes_phone(client: AsyncClient) -> None:
    phone = _unique_phone()
    response = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["phone"] == f"+91{phone}"
    assert body["debug_otp"] is not None
    assert len(body["debug_otp"]) == 6


async def test_otp_request_rejects_invalid_phone(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/otp/request", json={"phone": "12345"})
    assert response.status_code == 422


async def test_otp_verify_issues_tokens(client: AsyncClient) -> None:
    phone = _unique_phone()
    req = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert req.status_code == 200, req.text
    otp = req.json()["debug_otp"]

    verify = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": otp},
    )
    assert verify.status_code == 200, verify.text
    body = verify.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["phone"] == f"+91{phone}"
    assert body["expires_in"] > 0


async def test_refresh_and_logout(client: AsyncClient) -> None:
    phone = _unique_phone()
    req = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert req.status_code == 200, req.text
    otp = req.json()["debug_otp"]
    verify = await client.post("/api/v1/auth/otp/verify", json={"phone": phone, "otp": otp})
    assert verify.status_code == 200, verify.text
    refresh = verify.json()["refresh_token"]

    refreshed = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": refresh},
    )
    assert refreshed.status_code == 200, refreshed.text
    new_refresh = refreshed.json()["refresh_token"]
    assert new_refresh
    assert refreshed.json()["access_token"]

    # Old refresh should be invalid after rotation
    old_again = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": refresh},
    )
    assert old_again.status_code == 401

    logout = await client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh})
    assert logout.status_code == 200

    after_logout = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": new_refresh},
    )
    assert after_logout.status_code == 401


async def test_wrong_otp(client: AsyncClient) -> None:
    phone = _unique_phone()
    req = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert req.status_code == 200
    verify = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": "000000"},
    )
    assert verify.status_code == 401
