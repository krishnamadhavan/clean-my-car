"""Modules 9–11 — washes, dashboard, notifications (consumer)."""

from __future__ import annotations

import uuid
from datetime import date

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
            name=f"Wsh {suffix}",
            state="KA",
            is_active=True,
            display_order=unique_city_display_order(),
        )
        session.add(city)
        await session.flush()
        society = Society(
            city_id=city.id,
            name="Wash Society",
            service_weekdays=weekdays if weekdays is not None else [0, 1, 2, 3, 4, 5, 6],
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
            name="Swift",
            size_tier=VehicleSizeTier.small,
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
                CityInteriorPrice(
                    pricing_id=pricing.id, interior_frequency=0, monthly_amount_paise=0
                ),
                CityInteriorPrice(
                    pricing_id=pricing.id, interior_frequency=2, monthly_amount_paise=34900
                ),
            ]
        )
        await session.commit()
        return {
            "city_id": city.id,
            "society_id": society.id,
            "model_id": model.id,
        }


async def _subscribe(client: AsyncClient, world: dict, *, interior: int = 0) -> dict:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])
    assert (
        await client.put(
            "/api/v1/me/location",
            headers=headers,
            json={"city_id": str(world["city_id"]), "society_id": str(world["society_id"])},
        )
    ).status_code == 200
    assert (
        await client.put(
            "/api/v1/me/vehicle",
            headers=headers,
            json={"model_id": str(world["model_id"]), "nickname": "Daily"},
        )
    ).status_code == 200
    start = await client.post(
        "/api/v1/me/subscription",
        headers=headers,
        json={"interior_frequency": interior},
    )
    assert start.status_code == 201, start.text
    intent = start.json()["payment_intent_id"]
    assert (
        await client.post(
            f"/api/v1/me/payments/intents/{intent}/confirm",
            headers=headers,
            json={"provider_ref": "WASH-PAY"},
        )
    ).status_code == 200
    tokens["headers"] = headers
    tokens["subscription"] = start.json()["subscription"]
    return tokens


async def test_wash_summary_schedule_and_list(client: AsyncClient) -> None:
    world = await _seed_world(weekdays=[0, 2, 4])
    tokens = await _subscribe(client, world, interior=2)
    headers = tokens["headers"]

    summary = await client.get("/api/v1/me/washes/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["subscription_status"] == "active"
    assert body["exterior_entitled"] >= 1
    assert body["exterior_pending"] >= 1
    assert body["interior_included"] >= 0

    schedule = await client.get("/api/v1/me/schedule", headers=headers)
    assert schedule.status_code == 200, schedule.text
    items = schedule.json()["items"]
    assert items, "expected materialised wash days"
    assert all(i["kind"] in {"scheduled", "retry_scheduled"} for i in items)

    history = await client.get("/api/v1/me/washes", headers=headers)
    assert history.status_code == 200, history.text
    assert history.json()["total"] >= 1
    wash_id = history.json()["items"][0]["id"]

    detail = await client.get(f"/api/v1/me/washes/{wash_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == wash_id

    missing = await client.get(f"/api/v1/me/washes/{uuid.uuid4()}", headers=headers)
    assert missing.status_code == 404


async def test_dashboard_with_and_without_subscription(client: AsyncClient) -> None:
    world = await _seed_world()
    bare = await register_and_login(client)
    bare_headers = _auth(bare["access_token"])
    empty = await client.get("/api/v1/me/dashboard", headers=bare_headers)
    assert empty.status_code == 200, empty.text
    assert empty.json()["has_subscription"] is False
    assert empty.json()["message"]

    tokens = await _subscribe(client, world)
    dash = await client.get("/api/v1/me/dashboard", headers=tokens["headers"])
    assert dash.status_code == 200, dash.text
    body = dash.json()
    assert body["has_subscription"] is True
    assert body["subscription"]["status"] == "active"
    assert body["vehicle"] is not None
    assert body["wash_summary"] is not None
    assert body["wash_summary"]["exterior_entitled"] >= 0


async def test_wash_list_month_filter_and_empty_summary(client: AsyncClient) -> None:
    world = await _seed_world(weekdays=[0, 2, 4])
    tokens = await _subscribe(client, world)
    headers = tokens["headers"]

    month = date.today().strftime("%Y-%m")
    filtered = await client.get(
        "/api/v1/me/washes",
        headers=headers,
        params={"month": month, "status": "scheduled"},
    )
    assert filtered.status_code == 200, filtered.text
    assert filtered.json()["page"] == 1

    bad = await client.get(
        "/api/v1/me/washes",
        headers=headers,
        params={"month": "not-a-month"},
    )
    assert bad.status_code == 422

    bare = await register_and_login(client)
    empty = await client.get(
        "/api/v1/me/washes/summary",
        headers=_auth(bare["access_token"]),
    )
    assert empty.status_code == 200
    assert empty.json()["exterior_entitled"] == 0
    assert empty.json()["message"]

    # Dashboard with location but no subscription
    await client.put(
        "/api/v1/me/location",
        headers=_auth(bare["access_token"]),
        json={"city_id": str(world["city_id"]), "society_id": str(world["society_id"])},
    )
    dash = await client.get("/api/v1/me/dashboard", headers=_auth(bare["access_token"]))
    assert dash.status_code == 200
    assert dash.json()["has_subscription"] is False
    assert dash.json()["city"] is not None
    assert dash.json()["society"] is not None


async def test_notification_devices_and_preferences(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    prefs = await client.get("/api/v1/me/notification-preferences", headers=headers)
    assert prefs.status_code == 200, prefs.text
    assert prefs.json()["wash_completed"] is True
    assert prefs.json()["marketing"] is False

    updated = await client.put(
        "/api/v1/me/notification-preferences",
        headers=headers,
        json={"marketing": True, "service_reminders": False},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["marketing"] is True
    assert updated.json()["service_reminders"] is False

    device = await client.put(
        "/api/v1/me/devices",
        headers=headers,
        json={
            "token": f"apns-token-{uuid.uuid4().hex}",
            "platform": "ios",
            "app_version": "1.0.0",
            "device_name": "iPhone",
        },
    )
    assert device.status_code == 200, device.text
    device_id = device.json()["id"]
    assert device.json()["platform"] == "ios"

    # Upsert same token again
    again = await client.put(
        "/api/v1/me/devices",
        headers=headers,
        json={"token": device.json()["token"], "platform": "ios", "app_version": "1.0.1"},
    )
    assert again.status_code == 200
    assert again.json()["id"] == device_id
    assert again.json()["app_version"] == "1.0.1"

    deleted = await client.delete(f"/api/v1/me/devices/{device_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["message"]

    gone = await client.delete(f"/api/v1/me/devices/{device_id}", headers=headers)
    assert gone.status_code == 404
