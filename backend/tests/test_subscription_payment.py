"""Consumer Modules 7–8 — subscription start, pay, cancel, billing."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.models.city import City
from app.models.pricing import CityInteriorPrice, CityPricing, CitySizePrice
from app.models.society import Society
from app.models.vehicle import VehicleMake, VehicleModel, VehicleSizeTier
from tests.helpers import register_and_login, unique_city_display_order, unique_display_order


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _seed_world() -> dict:
    suffix = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as session:
        city = City(
            name=f"Hyd {suffix}",
            state="TS",
            is_active=True,
            display_order=unique_city_display_order(),
        )
        session.add(city)
        await session.flush()
        society = Society(
            city_id=city.id,
            name="Lake View",
            service_weekdays=[0, 2, 4],
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
                    size_tier=VehicleSizeTier.small,
                    monthly_amount_paise=99900,
                ),
                CitySizePrice(
                    pricing_id=pricing.id,
                    size_tier=VehicleSizeTier.medium,
                    monthly_amount_paise=129900,
                ),
                CitySizePrice(
                    pricing_id=pricing.id,
                    size_tier=VehicleSizeTier.large,
                    monthly_amount_paise=159900,
                ),
                CityInteriorPrice(
                    pricing_id=pricing.id, interior_frequency=0, monthly_amount_paise=0
                ),
                CityInteriorPrice(
                    pricing_id=pricing.id, interior_frequency=1, monthly_amount_paise=19900
                ),
                CityInteriorPrice(
                    pricing_id=pricing.id, interior_frequency=2, monthly_amount_paise=34900
                ),
                CityInteriorPrice(
                    pricing_id=pricing.id, interior_frequency=4, monthly_amount_paise=59900
                ),
            ]
        )
        await session.commit()
        return {
            "city_id": city.id,
            "society_id": society.id,
            "model_id": model.id,
        }


async def _ready_user(client: AsyncClient, world: dict) -> dict:
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
    tokens["headers"] = headers
    return tokens


async def test_subscription_start_pay_cancel_flow(client: AsyncClient) -> None:
    world = await _seed_world()
    tokens = await _ready_user(client, world)
    headers = tokens["headers"]

    missing = await client.get("/api/v1/me/subscription", headers=headers)
    assert missing.status_code == 404

    start = await client.post(
        "/api/v1/me/subscription",
        headers=headers,
        json={"interior_frequency": 2},
    )
    assert start.status_code == 201, start.text
    body = start.json()
    assert body["subscription"]["status"] == "pending_payment"
    assert body["subscription"]["interior_frequency"] == 2
    assert body["subscription"]["size_tier"] == "medium"
    assert body["payment_intent_id"]
    assert body["amount_due_now_paise"] > 0
    assert body["quote"]["full_monthly_total_paise"] == 129900 + 34900
    intent_id = body["payment_intent_id"]

    # Duplicate start rejected
    again = await client.post(
        "/api/v1/me/subscription",
        headers=headers,
        json={"interior_frequency": 0},
    )
    assert again.status_code == 409

    intent = await client.get(
        f"/api/v1/me/payments/intents/{intent_id}",
        headers=headers,
    )
    assert intent.status_code == 200
    assert intent.json()["status"] == "pending"

    confirm = await client.post(
        f"/api/v1/me/payments/intents/{intent_id}/confirm",
        headers=headers,
        json={"provider_ref": "DEV-PAY-1"},
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["status"] == "succeeded"
    assert confirm.json()["provider_ref"] == "DEV-PAY-1"

    current = await client.get("/api/v1/me/subscription", headers=headers)
    assert current.status_code == 200
    assert current.json()["status"] == "active"

    billing = await client.get("/api/v1/me/billing/summary", headers=headers)
    assert billing.status_code == 200
    assert billing.json()["has_subscription"] is True
    assert billing.json()["subscription_status"] == "active"
    assert billing.json()["amount_due_paise"] == 0

    cancelled = await client.post("/api/v1/me/subscription/cancel", headers=headers)
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancel_scheduled"
    assert cancelled.json()["cancel_at"] == cancelled.json()["period_end"]

    undone = await client.post("/api/v1/me/subscription/cancel/undo", headers=headers)
    assert undone.status_code == 200
    assert undone.json()["status"] == "active"
    assert undone.json()["cancel_at"] is None

    history = await client.get("/api/v1/me/payments", headers=headers)
    assert history.status_code == 200
    assert history.json()["total"] >= 1

    me = await client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["has_subscription"] is True


async def test_start_requires_location_and_vehicle(client: AsyncClient) -> None:
    world = await _seed_world()
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    no_loc = await client.post(
        "/api/v1/me/subscription",
        headers=headers,
        json={"interior_frequency": 0},
    )
    assert no_loc.status_code == 400
    assert no_loc.json()["code"] == "location_required"

    await client.put(
        "/api/v1/me/location",
        headers=headers,
        json={"city_id": str(world["city_id"]), "society_id": str(world["society_id"])},
    )
    no_veh = await client.post(
        "/api/v1/me/subscription",
        headers=headers,
        json={"interior_frequency": 0},
    )
    assert no_veh.status_code == 400
    assert no_veh.json()["code"] == "vehicle_required"
