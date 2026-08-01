"""Shared test helpers."""

from __future__ import annotations

import uuid

from httpx import AsyncClient


def unique_phone() -> str:
    suffix = uuid.uuid4().int % 10_000_0000
    return f"9{suffix:09d}"[:10]


async def register_and_login(client: AsyncClient, phone: str | None = None) -> dict:
    """OTP request + verify; returns token pair JSON body."""
    phone = phone or unique_phone()
    req = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert req.status_code == 200, req.text
    otp = req.json()["debug_otp"]
    verify = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": otp},
    )
    assert verify.status_code == 200, verify.text
    body = verify.json()
    body["_phone"] = phone
    return body
