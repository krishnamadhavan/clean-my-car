"""Consumer WASH-04 — upcoming schedule (service days only)."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.models.city import City
from app.models.pricing import CityInteriorPrice, CityPricing, CitySizePrice
from app.models.society import Society
from app.models.vehicle import VehicleMake, VehicleModel, VehicleSizeTier
from tests.helpers import register_and_login, unique_city_display_order, unique_display_order


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _seed_world(*, weekdays: list[int] | None = None) -> dict:
    suffix = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as session:
        city = City(
            name=f"Sch {suffix}",
            state="TS",
            is_active=True,
            display_order=unique_city_display_order(),
        )
        session.add(city)
        await session.flush()
        society = Society(
            city_id=city.id,
            name="Service Society",
            service_weekdays=weekdays if weekdays is not None else [0, 2, 4],
            is_serviceable=True,
            display_order=0,
        )
        pricing = CityPricing(
            city_id=city.id,
            currency="INR",
            amounts_include_gst=True,
            gst_rate_bps=1800,
            is_active=True,
        )
        make = VehicleMake(
            name=f"Make {suffix}",
            is_active=True,
            display_order=unique_display_order(),
        )
        session.add_all([society, pricing, make])
        await session.flush()
        model = VehicleModel(
            make_id=make.id,
            name="City",
            size_tier=VehicleSizeTier.medium,
            is_active=True,
            display_order=1,
        )
        session.add(model)
        session.add_all(
            [
                CitySizePrice(
                    pricing_id=pricing.id,
                    size_tier=VehicleSizeTier.medium,
                    monthly_amount_paise=129900,
                ),
                CityInteriorPrice(
                    pricing_id=pricing.id, interior_frequency=0, monthly_amount_paise=0
                ),
            ]
        )
        await session.commit()
        return {
            "city_id": city.id,
            "society_id": society.id,
            "model_id": model.id,
            "weekdays": list(society.service_weekdays),
        }


async def _ready_subscribed(client: AsyncClient, world: dict) -> dict:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])
    loc = await client.put(
        "/api/v1/me/location",
        headers=headers,
        json={"city_id": str(world["city_id"]), "society_id": str(world["society_id"])},
    )
    assert loc.status_code == 200, loc.text
    veh = await client.put(
        "/api/v1/me/vehicle",
        headers=headers,
        json={"model_id": str(world["model_id"]), "nickname": "Daily"},
    )
    assert veh.status_code == 200, veh.text
    start = await client.post(
        "/api/v1/me/subscription",
        headers=headers,
        json={"interior_frequency": 0},
    )
    assert start.status_code == 201, start.text
    intent_id = start.json()["payment_intent_id"]
    confirm = await client.post(
        f"/api/v1/me/payments/intents/{intent_id}/confirm",
        headers=headers,
        json={"provider_ref": "SCH-1"},
    )
    assert confirm.status_code == 200, confirm.text
    tokens["headers"] = headers
    tokens["subscription"] = start.json()["subscription"]
    return tokens


async def test_schedule_empty_without_subscription(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])
    res = await client.get("/api/v1/me/schedule", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["items"] == []
    assert body["message"]
    assert "Subscribe" in body["message"]


async def test_schedule_only_service_days(client: AsyncClient) -> None:
    world = await _seed_world(weekdays=[0, 2, 4])  # Mon / Wed / Fri
    tokens = await _ready_subscribed(client, world)
    headers = tokens["headers"]

    res = await client.get("/api/v1/me/schedule", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["subscription_status"] == "active"
    assert body["service_weekdays"] == [0, 2, 4]
    assert body["items"], "expected at least one upcoming service day"
    # Only wash days — never off-days
    for item in body["items"]:
        assert item["kind"] == "scheduled"
        assert item["title"] == "Exterior wash"
        assert item["weekday"] in {0, 2, 4}
        d = date.fromisoformat(item["date"])
        assert d.weekday() == item["weekday"]

    # Cap window
    capped = await client.get("/api/v1/me/schedule?days=7", headers=headers)
    assert capped.status_code == 200
    until = date.fromisoformat(capped.json()["until_date"])
    today = date.fromisoformat(capped.json()["from_date"])
    assert until <= today + timedelta(days=6)
    for item in capped.json()["items"]:
        assert date.fromisoformat(item["date"]) <= until


async def test_schedule_requires_auth(client: AsyncClient) -> None:
    res = await client.get("/api/v1/me/schedule")
    assert res.status_code == 401
