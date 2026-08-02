"""Waitlist module tests (Module 4 — Should + Could)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.models.city import City
from tests.helpers import register_and_login, unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _seed_city() -> dict:
    city = City(name="Bengaluru", state="Karnataka", is_active=True, display_order=1)
    inactive = City(name="Hidden", state="XX", is_active=False, display_order=99)
    async with AsyncSessionLocal() as session:
        session.add_all([city, inactive])
        await session.commit()
        await session.refresh(city)
        await session.refresh(inactive)
        return {"city_id": city.id, "inactive_city_id": inactive.id}


@pytest.fixture
async def cities() -> dict:
    return await _seed_city()


async def test_join_waitlist_anonymous(client: AsyncClient, cities: dict) -> None:
    phone = unique_phone()
    response = await client.post(
        "/api/v1/waitlist",
        json={
            "city_id": str(cities["city_id"]),
            "society_name": "  Maple Heights  ",
            "phone": phone,
            "notes": "Tower B basement",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["society_name"] == "Maple Heights"
    assert body["phone"] == f"+91{phone}"
    assert body["status"] == "pending"
    assert body["notes"] == "Tower B basement"
    assert body["city"]["name"] == "Bengaluru"


async def test_join_waitlist_requires_phone_when_anonymous(
    client: AsyncClient, cities: dict
) -> None:
    response = await client.post(
        "/api/v1/waitlist",
        json={
            "city_id": str(cities["city_id"]),
            "society_name": "Some Society",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "phone_required"


async def test_join_waitlist_authenticated_defaults_phone(
    client: AsyncClient, cities: dict
) -> None:
    tokens = await register_and_login(client)
    response = await client.post(
        "/api/v1/waitlist",
        headers=_auth(tokens["access_token"]),
        json={
            "city_id": str(cities["city_id"]),
            "society_name": "Palm Grove",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["phone"] == tokens["user"]["phone"]
    assert body["status"] == "pending"

    listed = await client.get("/api/v1/me/waitlist", headers=_auth(tokens["access_token"]))
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) == 1
    assert items[0]["society_name"] == "Palm Grove"


async def test_join_waitlist_one_per_user_updates_in_place(
    client: AsyncClient, cities: dict
) -> None:
    """Authenticated users may only have one waitlist row; re-join updates it."""
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    first = await client.post(
        "/api/v1/waitlist",
        headers=headers,
        json={
            "city_id": str(cities["city_id"]),
            "society_name": "Same Society",
            "notes": "first",
        },
    )
    second = await client.post(
        "/api/v1/waitlist",
        headers=headers,
        json={
            "city_id": str(cities["city_id"]),
            "society_name": "Different Society",
            "notes": "updated later",
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["society_name"] == "Different Society"
    assert second.json()["notes"] == "updated later"

    listed = await client.get("/api/v1/me/waitlist", headers=headers)
    items = listed.json()["items"]
    assert len(items) == 1
    assert items[0]["society_name"] == "Different Society"


async def test_join_waitlist_anonymous_one_per_phone(client: AsyncClient, cities: dict) -> None:
    phone = unique_phone()
    first = await client.post(
        "/api/v1/waitlist",
        json={
            "city_id": str(cities["city_id"]),
            "society_name": "Alpha Towers",
            "phone": phone,
        },
    )
    second = await client.post(
        "/api/v1/waitlist",
        json={
            "city_id": str(cities["city_id"]),
            "society_name": "Beta Residency",
            "phone": phone,
            "notes": "moved interest",
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["society_name"] == "Beta Residency"


async def test_join_waitlist_rejects_inactive_city(client: AsyncClient, cities: dict) -> None:
    response = await client.post(
        "/api/v1/waitlist",
        json={
            "city_id": str(cities["inactive_city_id"]),
            "society_name": "Anywhere",
            "phone": unique_phone(),
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "city_not_available"


async def test_me_waitlist_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me/waitlist")
    assert response.status_code == 401


async def test_me_waitlist_empty(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    response = await client.get("/api/v1/me/waitlist", headers=_auth(tokens["access_token"]))
    assert response.status_code == 200
    assert response.json()["items"] == []
