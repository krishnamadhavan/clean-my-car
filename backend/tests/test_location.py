"""Location module tests (Module 3 — Must)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.models.city import City
from app.models.society import Society
from tests.helpers import register_and_login


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _seed_catalog() -> dict:
    """Insert active city + live/non-live societies; return ids."""
    city = City(name="Bengaluru", state="Karnataka", is_active=True, display_order=1)
    inactive_city = City(name="Hidden", state="XX", is_active=False, display_order=99)

    async with AsyncSessionLocal() as session:
        session.add_all([city, inactive_city])
        await session.flush()

        live = Society(
            city_id=city.id,
            name="Green Park Residency",
            address_line="Whitefield",
            service_weekdays=[0, 2, 4],  # Mon Wed Fri
            is_serviceable=True,
            display_order=1,
        )
        live2 = Society(
            city_id=city.id,
            name="Lake View Apartments",
            address_line="Koramangala",
            service_weekdays=[1, 3, 5],
            is_serviceable=True,
            display_order=2,
        )
        not_live = Society(
            city_id=city.id,
            name="Future Towers",
            address_line="Not live yet",
            service_weekdays=[0, 2, 4],
            is_serviceable=False,
            display_order=3,
        )
        session.add_all([live, live2, not_live])
        await session.commit()
        await session.refresh(city)
        await session.refresh(live)
        await session.refresh(live2)
        await session.refresh(not_live)
        await session.refresh(inactive_city)
        return {
            "city_id": city.id,
            "inactive_city_id": inactive_city.id,
            "live_id": live.id,
            "live2_id": live2.id,
            "not_live_id": not_live.id,
        }


@pytest.fixture
async def catalog() -> dict:
    return await _seed_catalog()


async def test_list_cities_only_active(client: AsyncClient, catalog: dict) -> None:
    response = await client.get("/api/v1/cities")
    assert response.status_code == 200, response.text
    body = response.json()
    ids = {row["id"] for row in body}
    assert str(catalog["city_id"]) in ids
    assert str(catalog["inactive_city_id"]) not in ids
    bengaluru = next(r for r in body if r["id"] == str(catalog["city_id"]))
    assert bengaluru["name"] == "Bengaluru"
    assert bengaluru["state"] == "Karnataka"


async def test_list_societies_only_live(client: AsyncClient, catalog: dict) -> None:
    city_id = catalog["city_id"]
    response = await client.get(f"/api/v1/cities/{city_id}/societies")
    assert response.status_code == 200, response.text
    body = response.json()
    names = {item["name"] for item in body["items"]}
    assert "Green Park Residency" in names
    assert "Lake View Apartments" in names
    assert "Future Towers" not in names
    assert body["total"] == 2


async def test_list_societies_search(client: AsyncClient, catalog: dict) -> None:
    city_id = catalog["city_id"]
    response = await client.get(
        f"/api/v1/cities/{city_id}/societies",
        params={"q": "Green"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Green Park Residency"


async def test_get_society_detail(client: AsyncClient, catalog: dict) -> None:
    response = await client.get(f"/api/v1/societies/{catalog['live_id']}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["service_weekdays"] == [0, 2, 4]
    assert body["service_weekday_labels"] == ["mon", "wed", "fri"]
    assert body["city"]["name"] == "Bengaluru"


async def test_get_non_live_society_404(client: AsyncClient, catalog: dict) -> None:
    response = await client.get(f"/api/v1/societies/{catalog['not_live_id']}")
    assert response.status_code == 404


async def test_me_location_set_and_get(client: AsyncClient, catalog: dict) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    empty = await client.get("/api/v1/me/location", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["city"] is None
    assert empty.json()["society"] is None

    put = await client.put(
        "/api/v1/me/location",
        headers=headers,
        json={
            "city_id": str(catalog["city_id"]),
            "society_id": str(catalog["live_id"]),
        },
    )
    assert put.status_code == 200, put.text
    body = put.json()
    assert body["city"]["id"] == str(catalog["city_id"])
    assert body["society"]["id"] == str(catalog["live_id"])
    assert body["society"]["service_weekday_labels"] == ["mon", "wed", "fri"]

    got = await client.get("/api/v1/me/location", headers=headers)
    assert got.status_code == 200
    assert got.json()["society"]["name"] == "Green Park Residency"


async def test_me_location_rejects_non_live_society(client: AsyncClient, catalog: dict) -> None:
    tokens = await register_and_login(client)
    response = await client.put(
        "/api/v1/me/location",
        headers=_auth(tokens["access_token"]),
        json={
            "city_id": str(catalog["city_id"]),
            "society_id": str(catalog["not_live_id"]),
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "society_not_serviceable"


async def test_me_location_requires_auth(client: AsyncClient, catalog: dict) -> None:
    response = await client.get("/api/v1/me/location")
    assert response.status_code == 401
