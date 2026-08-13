"""Consumer Modules 7–8 — subscription start, pay, cancel, billing."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.models.city import City
from app.models.payment import Payment, PaymentKind, PaymentStatus
from app.models.pricing import CityInteriorPrice, CityPricing, CitySizePrice
from app.models.society import Society
from app.models.subscription import Subscription, SubscriptionStatus
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


async def _start_subscription(client: AsyncClient, headers: dict, interior: int = 0) -> dict:
    start = await client.post(
        "/api/v1/me/subscription",
        headers=headers,
        json={"interior_frequency": interior},
    )
    assert start.status_code == 201, start.text
    return start.json()


async def test_billing_summary_without_subscription(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])
    billing = await client.get("/api/v1/me/billing/summary", headers=headers)
    assert billing.status_code == 200
    body = billing.json()
    assert body["has_subscription"] is False
    assert body["amount_due_paise"] == 0
    assert "No active" in body["message"]


async def test_create_intent_reuses_pending_and_creates_renewal(client: AsyncClient) -> None:
    world = await _seed_world()
    tokens = await _ready_user(client, world)
    headers = tokens["headers"]
    started = await _start_subscription(client, headers, interior=1)
    sub_id = started["subscription"]["id"]
    first_intent = started["payment_intent_id"]

    # Explicit create with subscription_id reuses open pending start intent
    reuse = await client.post(
        "/api/v1/me/payments/intents",
        headers=headers,
        json={"subscription_id": sub_id},
    )
    assert reuse.status_code == 201, reuse.text
    assert reuse.json()["id"] == first_intent
    assert reuse.json()["status"] == "pending"

    # Empty body also resolves open subscription and reuses
    reuse2 = await client.post("/api/v1/me/payments/intents", headers=headers)
    assert reuse2.status_code == 201
    assert reuse2.json()["id"] == first_intent

    # Confirm start payment
    confirm = await client.post(
        f"/api/v1/me/payments/intents/{first_intent}/confirm",
        headers=headers,
        json={},
    )
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "succeeded"

    # Idempotent re-confirm
    again = await client.post(
        f"/api/v1/me/payments/intents/{first_intent}/confirm",
        headers=headers,
    )
    assert again.status_code == 200
    assert again.json()["status"] == "succeeded"

    # New intent after prior succeeded → renewal kind
    renewal = await client.post(
        "/api/v1/me/payments/intents",
        headers=headers,
        json={"subscription_id": sub_id},
    )
    assert renewal.status_code == 201, renewal.text
    assert renewal.json()["id"] != first_intent
    assert renewal.json()["kind"] == "renewal"
    assert renewal.json()["status"] == "pending"
    assert renewal.json()["amount_paise"] == started["subscription"]["monthly_amount_paise"]

    billing = await client.get("/api/v1/me/billing/summary", headers=headers)
    assert billing.status_code == 200
    b = billing.json()
    assert b["amount_due_paise"] == renewal.json()["amount_paise"]
    assert b["open_payment_intent_id"] == renewal.json()["id"]
    assert "Payment due" in b["message"]


async def test_create_intent_errors(client: AsyncClient) -> None:
    world = await _seed_world()
    tokens = await _ready_user(client, world)
    headers = tokens["headers"]

    no_sub = await client.post("/api/v1/me/payments/intents", headers=headers)
    assert no_sub.status_code == 404
    assert no_sub.json()["code"] == "subscription_not_found"

    missing_id = await client.post(
        "/api/v1/me/payments/intents",
        headers=headers,
        json={"subscription_id": str(uuid.uuid4())},
    )
    assert missing_id.status_code == 404

    # Other user's subscription
    started = await _start_subscription(client, headers)
    other = await register_and_login(client)
    other_headers = _auth(other["access_token"])
    foreign = await client.post(
        "/api/v1/me/payments/intents",
        headers=other_headers,
        json={"subscription_id": started["subscription"]["id"]},
    )
    assert foreign.status_code == 404

    # Paused subscription is not billable
    async with AsyncSessionLocal() as session:
        sub = await session.get(Subscription, uuid.UUID(started["subscription"]["id"]))
        assert sub is not None
        sub.status = SubscriptionStatus.paused
        await session.commit()

    not_billable = await client.post(
        "/api/v1/me/payments/intents",
        headers=headers,
        json={"subscription_id": started["subscription"]["id"]},
    )
    assert not_billable.status_code == 409
    assert not_billable.json()["code"] == "subscription_not_billable"


async def test_confirm_payment_edge_cases(client: AsyncClient) -> None:
    world = await _seed_world()
    tokens = await _ready_user(client, world)
    headers = tokens["headers"]
    started = await _start_subscription(client, headers)
    intent_id = started["payment_intent_id"]
    sub_id = uuid.UUID(started["subscription"]["id"])

    me = await client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    user_id = uuid.UUID(me.json()["id"])

    # Confirm with whitespace-only provider_ref keeps prior ref null
    ok = await client.post(
        f"/api/v1/me/payments/intents/{intent_id}/confirm",
        headers=headers,
        json={"provider_ref": "   "},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "succeeded"

    # Payment not found / other user
    ghost = await client.get(
        f"/api/v1/me/payments/intents/{uuid.uuid4()}",
        headers=headers,
    )
    assert ghost.status_code == 404

    other = await register_and_login(client)
    foreign = await client.post(
        f"/api/v1/me/payments/intents/{intent_id}/confirm",
        headers=_auth(other["access_token"]),
    )
    assert foreign.status_code == 404

    # Cancelled payment cannot be confirmed; failed can (manual retry)
    async with AsyncSessionLocal() as session:
        cancelled_pay = Payment(
            user_id=user_id,
            subscription_id=sub_id,
            amount_paise=100,
            currency="INR",
            status=PaymentStatus.cancelled,
            kind=PaymentKind.renewal,
            provider="manual",
        )
        failed_pay = Payment(
            user_id=user_id,
            subscription_id=sub_id,
            amount_paise=200,
            currency="INR",
            status=PaymentStatus.failed,
            kind=PaymentKind.renewal,
            provider="manual",
            failure_reason="card_declined",
        )
        session.add_all([cancelled_pay, failed_pay])
        await session.commit()
        await session.refresh(cancelled_pay)
        await session.refresh(failed_pay)
        cancelled_id = cancelled_pay.id
        failed_id = failed_pay.id

    cancelled = await client.post(
        f"/api/v1/me/payments/intents/{cancelled_id}/confirm",
        headers=headers,
    )
    assert cancelled.status_code == 409
    assert cancelled.json()["code"] == "payment_cancelled"

    recovered = await client.post(
        f"/api/v1/me/payments/intents/{failed_id}/confirm",
        headers=headers,
        json={"provider_ref": "RETRY-1"},
    )
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()["status"] == "succeeded"
    assert recovered.json()["provider_ref"] == "RETRY-1"


async def test_cancel_idempotent_and_undo_errors(client: AsyncClient) -> None:
    world = await _seed_world()
    tokens = await _ready_user(client, world)
    headers = tokens["headers"]

    # cancel / undo with no subscription
    no_cancel = await client.post("/api/v1/me/subscription/cancel", headers=headers)
    assert no_cancel.status_code == 404
    no_undo = await client.post("/api/v1/me/subscription/cancel/undo", headers=headers)
    assert no_undo.status_code == 404

    started = await _start_subscription(client, headers)
    intent_id = started["payment_intent_id"]
    await client.post(
        f"/api/v1/me/payments/intents/{intent_id}/confirm",
        headers=headers,
        json={"provider_ref": "X"},
    )

    # undo when not scheduled
    not_sched = await client.post("/api/v1/me/subscription/cancel/undo", headers=headers)
    assert not_sched.status_code == 409
    assert not_sched.json()["code"] == "cancel_not_scheduled"

    c1 = await client.post("/api/v1/me/subscription/cancel", headers=headers)
    assert c1.status_code == 200
    assert c1.json()["status"] == "cancel_scheduled"

    # Idempotent second cancel
    c2 = await client.post("/api/v1/me/subscription/cancel", headers=headers)
    assert c2.status_code == 200
    assert c2.json()["status"] == "cancel_scheduled"
    assert c2.json()["cancel_at"] == c1.json()["cancel_at"]

    billing = await client.get("/api/v1/me/billing/summary", headers=headers)
    assert billing.status_code == 200
    assert "Service continues until" in billing.json()["message"]
    assert billing.json()["subscription_status"] == "cancel_scheduled"

    # pending_payment billing message before pay
    other_tokens = await _ready_user(client, world)
    other_headers = other_tokens["headers"]
    await _start_subscription(client, other_headers, interior=2)
    pending_billing = await client.get("/api/v1/me/billing/summary", headers=other_headers)
    assert pending_billing.status_code == 200
    pb = pending_billing.json()
    assert pb["subscription_status"] == "pending_payment"
    assert pb["is_overdue"] is True
    assert pb["amount_due_paise"] > 0
    assert "Pay to activate" in pb["message"]


async def test_start_with_explicit_start_date_and_invalid_frequency(
    client: AsyncClient,
) -> None:
    world = await _seed_world()
    tokens = await _ready_user(client, world)
    headers = tokens["headers"]

    bad = await client.post(
        "/api/v1/me/subscription",
        headers=headers,
        json={"interior_frequency": 3},
    )
    assert bad.status_code == 422

    start = await client.post(
        "/api/v1/me/subscription",
        headers=headers,
        json={"interior_frequency": 0, "start_date": "2026-08-15"},
    )
    assert start.status_code == 201, start.text
    assert start.json()["subscription"]["period_start"] == "2026-08-15"
    assert start.json()["subscription"]["period_end"] == "2026-08-31"


async def test_recreate_start_intent_after_failed_pending(client: AsyncClient) -> None:
    """When the start intent fails and is no longer pending, create a new start intent."""
    world = await _seed_world()
    tokens = await _ready_user(client, world)
    headers = tokens["headers"]
    started = await _start_subscription(client, headers)
    intent_id = uuid.UUID(started["payment_intent_id"])

    async with AsyncSessionLocal() as session:
        pay = await session.get(Payment, intent_id)
        assert pay is not None
        pay.status = PaymentStatus.failed
        pay.failure_reason = "network"
        await session.commit()

    recreate = await client.post("/api/v1/me/payments/intents", headers=headers)
    assert recreate.status_code == 201, recreate.text
    body = recreate.json()
    assert body["id"] != str(intent_id)
    assert body["kind"] == "subscription_start"
    assert body["status"] == "pending"
    assert body["amount_paise"] == started["subscription"]["monthly_amount_paise"]
