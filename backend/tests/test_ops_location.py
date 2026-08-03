"""Ops Module 3 — cities and societies catalog APIs."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.passwords import hash_password
from app.db.session import AsyncSessionLocal
from app.models.ops_operator import OPS_ROLE_CATALOG_ADMIN, OpsOperator
from app.schemas.ops_location import OpsCityCreate, OpsCityPatch, OpsSocietyCreate, OpsSocietyPatch
from tests.helpers import unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _ops_token(client: AsyncClient) -> str:
    email = f"catalog-{unique_phone()}@ops.test"
    password = "password99"
    async with AsyncSessionLocal() as session:
        session.add(
            OpsOperator(
                email=email,
                password_hash=hash_password(password),
                name="Catalog Admin",
                roles=[OPS_ROLE_CATALOG_ADMIN],
            )
        )
        await session.commit()
    login = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def test_ops_location_schema_validators() -> None:
    with pytest.raises(ValidationError):
        OpsCityCreate(name="  ", state="KA")
    with pytest.raises(ValidationError):
        OpsCityPatch(name="  ")
    with pytest.raises(ValidationError):
        OpsSocietyCreate(name="X", service_weekdays=[0, 1, 7])
    with pytest.raises(ValidationError):
        OpsSocietyCreate(name="  ", service_weekdays=[0, 1, 2])
    with pytest.raises(ValidationError):
        OpsSocietyPatch(service_weekdays=[0, 1])
    with pytest.raises(ValidationError):
        OpsSocietyPatch(name="  ")
    assert OpsSocietyCreate(
        name="Ok",
        address_line="  ",
        service_weekdays=[4, 0, 2],
    ).service_weekdays == [0, 2, 4]
    assert OpsSocietyPatch(address_line="  ").address_line is None


async def test_ops_location_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/ops/cities")).status_code == 401


async def test_create_list_patch_city(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))

    created = await client.post(
        "/api/v1/ops/cities",
        headers=headers,
        json={
            "name": "  Pune  ",
            "state": "Maharashtra",
            "is_active": False,
            "display_order": 5,
        },
    )
    assert created.status_code == 201, created.text
    city = created.json()
    assert city["name"] == "Pune"
    assert city["is_active"] is False
    city_id = city["id"]

    listed = await client.get(
        "/api/v1/ops/cities",
        headers=headers,
        params={"include_inactive": True},
    )
    assert listed.status_code == 200
    assert any(c["id"] == city_id for c in listed.json()["items"])

    # Inactive hidden when include_inactive=false
    active_only = await client.get(
        "/api/v1/ops/cities",
        headers=headers,
        params={"include_inactive": False},
    )
    assert all(c["id"] != city_id for c in active_only.json()["items"])

    patched = await client.patch(
        f"/api/v1/ops/cities/{city_id}",
        headers=headers,
        json={"is_active": True, "display_order": 1},
    )
    assert patched.status_code == 200
    assert patched.json()["is_active"] is True
    assert patched.json()["display_order"] == 1

    # Consumer can see it once active
    consumer = await client.get("/api/v1/cities")
    assert consumer.status_code == 200
    assert any(c["id"] == city_id for c in consumer.json())


async def test_society_crud_and_consumer_live_filter(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))

    city_res = await client.post(
        "/api/v1/ops/cities",
        headers=headers,
        json={"name": "Hyderabad", "state": "Telangana", "is_active": True},
    )
    city_id = city_res.json()["id"]

    live = await client.post(
        f"/api/v1/ops/cities/{city_id}/societies",
        headers=headers,
        json={
            "name": "  Live Towers  ",
            "address_line": "Gachibowli",
            "service_weekdays": [0, 2, 4],
            "is_serviceable": True,
        },
    )
    assert live.status_code == 201, live.text
    assert live.json()["name"] == "Live Towers"
    assert live.json()["service_weekdays"] == [0, 2, 4]
    live_id = live.json()["id"]

    not_live = await client.post(
        f"/api/v1/ops/cities/{city_id}/societies",
        headers=headers,
        json={
            "name": "Future Park",
            "service_weekdays": [1, 3, 5],
            "is_serviceable": False,
        },
    )
    assert not_live.status_code == 201
    not_live_id = not_live.json()["id"]

    ops_list = await client.get(
        f"/api/v1/ops/cities/{city_id}/societies",
        headers=headers,
    )
    assert ops_list.status_code == 200
    ops_ids = {s["id"] for s in ops_list.json()["items"]}
    assert live_id in ops_ids and not_live_id in ops_ids

    consumer_list = await client.get(f"/api/v1/cities/{city_id}/societies")
    assert consumer_list.status_code == 200
    consumer_ids = {s["id"] for s in consumer_list.json()["items"]}
    assert live_id in consumer_ids
    assert not_live_id not in consumer_ids

    # Go live via patch
    patched = await client.patch(
        f"/api/v1/ops/societies/{not_live_id}",
        headers=headers,
        json={"is_serviceable": True, "service_weekdays": [0, 1, 2]},
    )
    assert patched.status_code == 200
    assert patched.json()["is_serviceable"] is True
    assert patched.json()["service_weekdays"] == [0, 1, 2]

    detail = await client.get(
        f"/api/v1/ops/societies/{not_live_id}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["name"] == "Future Park"

    consumer_list2 = await client.get(f"/api/v1/cities/{city_id}/societies")
    assert not_live_id in {s["id"] for s in consumer_list2.json()["items"]}


async def test_society_rejects_bad_weekdays(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    city = await client.post(
        "/api/v1/ops/cities",
        headers=headers,
        json={"name": "Kochi", "state": "Kerala"},
    )
    city_id = city.json()["id"]

    bad = await client.post(
        f"/api/v1/ops/cities/{city_id}/societies",
        headers=headers,
        json={"name": "Bad", "service_weekdays": [0, 0, 1]},
    )
    assert bad.status_code == 422

    bad2 = await client.post(
        f"/api/v1/ops/cities/{city_id}/societies",
        headers=headers,
        json={"name": "Bad2", "service_weekdays": [0, 1]},
    )
    assert bad2.status_code == 422


async def test_city_not_found(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    response = await client.patch(
        "/api/v1/ops/cities/00000000-0000-0000-0000-000000000099",
        headers=headers,
        json={"name": "Nope"},
    )
    assert response.status_code == 404


async def test_society_not_found_and_search(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    city = await client.post(
        "/api/v1/ops/cities",
        headers=headers,
        json={"name": "Jaipur", "state": "Rajasthan", "is_active": True},
    )
    city_id = city.json()["id"]
    await client.post(
        f"/api/v1/ops/cities/{city_id}/societies",
        headers=headers,
        json={
            "name": "Pink City Residency",
            "service_weekdays": [0, 2, 4],
            "is_serviceable": True,
        },
    )
    await client.post(
        f"/api/v1/ops/cities/{city_id}/societies",
        headers=headers,
        json={
            "name": "Other Place",
            "service_weekdays": [1, 3, 5],
            "is_serviceable": False,
        },
    )

    search = await client.get(
        f"/api/v1/ops/cities/{city_id}/societies",
        headers=headers,
        params={"q": "Pink"},
    )
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["name"] == "Pink City Residency"

    live_only = await client.get(
        f"/api/v1/ops/cities/{city_id}/societies",
        headers=headers,
        params={"include_non_serviceable": False},
    )
    assert live_only.status_code == 200
    assert all(s["is_serviceable"] for s in live_only.json()["items"])

    missing = await client.get(
        "/api/v1/ops/societies/00000000-0000-0000-0000-000000000099",
        headers=headers,
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "society_not_found"
