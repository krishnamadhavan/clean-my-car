"""Ops Modules 9–11 — overview, washes field actions, notification templates."""

from __future__ import annotations

from datetime import date, timedelta

from httpx import AsyncClient

from app.core.passwords import hash_password
from app.db.session import AsyncSessionLocal
from app.models.city import City
from app.models.ops_operator import OPS_ROLE_SUPPORT, OpsOperator
from app.models.society import Society
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.vehicle import VehicleSizeTier
from app.models.wash import Wash, WashStatus
from app.services.ops_subscription import month_end
from tests.helpers import unique_city_display_order, unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _ops_token(client: AsyncClient) -> str:
    email = f"wash-{unique_phone()}@ops.test"
    password = "password99"
    async with AsyncSessionLocal() as session:
        op = OpsOperator(
            email=email,
            password_hash=hash_password(password),
            name="Wash Ops",
            roles=[OPS_ROLE_SUPPORT],
        )
        session.add(op)
        await session.commit()
    login = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


async def _seed_wash_world() -> dict:
    phone = f"+91{unique_phone()}"
    today = date.today()
    async with AsyncSessionLocal() as session:
        user = User(phone=phone, name="Wash User", is_active=True)
        city = City(
            name="Wash City",
            state="KA",
            is_active=True,
            display_order=unique_city_display_order(),
        )
        session.add_all([user, city])
        await session.flush()
        society = Society(
            city_id=city.id,
            name="Ops Society",
            service_weekdays=[0, 1, 2, 3, 4, 5, 6],
            is_serviceable=True,
            display_order=0,
        )
        session.add(society)
        await session.flush()
        sub = Subscription(
            user_id=user.id,
            city_id=city.id,
            society_id=society.id,
            size_tier=VehicleSizeTier.medium,
            interior_frequency=0,
            status=SubscriptionStatus.active,
            monthly_amount_paise=149900,
            currency="INR",
            period_start=today.replace(day=1),
            period_end=month_end(today),
        )
        session.add(sub)
        await session.flush()
        wash = Wash(
            user_id=user.id,
            subscription_id=sub.id,
            society_id=society.id,
            service_date=today,
            status=WashStatus.scheduled,
            includes_exterior=True,
        )
        session.add(wash)
        await session.commit()
        return {
            "user_id": user.id,
            "society_id": society.id,
            "subscription_id": sub.id,
            "wash_id": wash.id,
            "service_date": today.isoformat(),
        }


async def test_ops_overview_and_wash_lifecycle(client: AsyncClient) -> None:
    world = await _seed_wash_world()
    token = await _ops_token(client)
    headers = _auth(token)

    overview = await client.get("/api/v1/ops/overview", headers=headers)
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["cities_total"] >= 1
    assert body["societies_live"] >= 1
    assert body["subscriptions_active"] >= 1
    assert body["washes_scheduled_today"] >= 1

    washes = await client.get(
        "/api/v1/ops/washes",
        headers=headers,
        params={"society_id": str(world["society_id"])},
    )
    assert washes.status_code == 200, washes.text
    assert washes.json()["total"] >= 1

    roster = await client.get(
        f"/api/v1/ops/societies/{world['society_id']}/roster",
        headers=headers,
        params={"service_date": world["service_date"]},
    )
    assert roster.status_code == 200, roster.text
    assert roster.json()["total"] >= 1

    # Miss creates next-day retry
    miss = await client.post(
        f"/api/v1/ops/washes/{world['wash_id']}/miss",
        headers=headers,
        json={"reason": "gate locked", "schedule_retry": True},
    )
    assert miss.status_code == 200, miss.text
    assert miss.json()["status"] == "missed"
    assert miss.json()["miss_reason"] == "gate locked"

    retry_day = (date.fromisoformat(world["service_date"]) + timedelta(days=1)).isoformat()
    retries = await client.get(
        "/api/v1/ops/washes",
        headers=headers,
        params={"service_date": retry_day, "status": "retry_scheduled"},
    )
    assert retries.status_code == 200
    assert retries.json()["total"] >= 1
    retry_id = retries.json()["items"][0]["id"]

    complete = await client.post(
        f"/api/v1/ops/washes/{retry_id}/complete",
        headers=headers,
        json={"includes_interior": True, "notes": "done"},
    )
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "completed"
    assert complete.json()["includes_interior"] is True

    # Idempotent complete
    again = await client.post(
        f"/api/v1/ops/washes/{retry_id}/complete",
        headers=headers,
        json={},
    )
    assert again.status_code == 200
    assert again.json()["status"] == "completed"

    gen = await client.post(
        "/api/v1/ops/washes/generate",
        headers=headers,
        json={"subscription_id": str(world["subscription_id"])},
    )
    assert gen.status_code == 200, gen.text
    assert gen.json()["created"] >= 0


async def test_ops_notification_templates(client: AsyncClient) -> None:
    token = await _ops_token(client)
    headers = _auth(token)

    listed = await client.get("/api/v1/ops/notification-templates", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["items"]
    keys = {i["key"] for i in listed.json()["items"]}
    assert "wash_completed" in keys

    put = await client.put(
        "/api/v1/ops/notification-templates/wash_completed",
        headers=headers,
        json={"title": "Done", "body": "Your wash is complete.", "channel": "push"},
    )
    assert put.status_code == 200, put.text
    assert put.json()["title"] == "Done"

    # Create new template key
    created = await client.put(
        "/api/v1/ops/notification-templates/custom_alert",
        headers=headers,
        json={"title": "Alert", "body": "Hello", "channel": "push"},
    )
    assert created.status_code == 200
    assert created.json()["key"] == "custom_alert"

    send = await client.post(
        "/api/v1/ops/notifications/send",
        headers=headers,
        json={"template_key": "wash_completed"},
    )
    assert send.status_code == 200, send.text
    assert send.json()["accepted"] is True

    world = await _seed_wash_world()
    send_user = await client.post(
        "/api/v1/ops/notifications/send",
        headers=headers,
        json={
            "user_id": str(world["user_id"]),
            "title": "Hi",
            "body": "Manual",
        },
    )
    assert send_user.status_code == 200

    missing_tpl = await client.post(
        "/api/v1/ops/notifications/send",
        headers=headers,
        json={"template_key": "does_not_exist"},
    )
    assert missing_tpl.status_code == 404

    invalid = await client.post(
        "/api/v1/ops/notifications/send",
        headers=headers,
        json={},
    )
    assert invalid.status_code == 400

    bad_user = await client.post(
        "/api/v1/ops/notifications/send",
        headers=headers,
        json={
            "user_id": "00000000-0000-0000-0000-000000000099",
            "title": "x",
            "body": "y",
        },
    )
    assert bad_user.status_code == 404


async def test_ops_wash_edge_cases(client: AsyncClient) -> None:
    world = await _seed_wash_world()
    token = await _ops_token(client)
    headers = _auth(token)

    # Miss without retry
    miss = await client.post(
        f"/api/v1/ops/washes/{world['wash_id']}/miss",
        headers=headers,
        json={"schedule_retry": False, "reason": "rain"},
    )
    assert miss.status_code == 200
    assert miss.json()["status"] == "missed"

    # Already missed — idempotent
    miss2 = await client.post(
        f"/api/v1/ops/washes/{world['wash_id']}/miss",
        headers=headers,
        json={},
    )
    assert miss2.status_code == 200
    assert miss2.json()["status"] == "missed"

    # Extra rows outside the subscription period avoid unique collisions with generate()
    far = date.fromisoformat(world["service_date"]) + timedelta(days=60)
    async with AsyncSessionLocal() as session:
        wash = Wash(
            user_id=world["user_id"],
            subscription_id=world["subscription_id"],
            society_id=world["society_id"],
            service_date=far,
            status=WashStatus.scheduled,
            includes_exterior=True,
        )
        skipped = Wash(
            user_id=world["user_id"],
            subscription_id=world["subscription_id"],
            society_id=world["society_id"],
            service_date=far + timedelta(days=1),
            status=WashStatus.skipped,
            includes_exterior=True,
        )
        session.add_all([wash, skipped])
        await session.commit()
        await session.refresh(wash)
        await session.refresh(skipped)
        new_id = wash.id
        skipped_id = skipped.id

    done = await client.post(
        f"/api/v1/ops/washes/{new_id}/complete",
        headers=headers,
        json={"includes_interior": False},
    )
    assert done.status_code == 200
    assert done.json()["status"] == "completed"

    not_found = await client.post(
        "/api/v1/ops/washes/00000000-0000-0000-0000-000000000001/complete",
        headers=headers,
        json={},
    )
    assert not_found.status_code == 404

    roster_missing = await client.get(
        "/api/v1/ops/societies/00000000-0000-0000-0000-000000000001/roster",
        headers=headers,
    )
    assert roster_missing.status_code == 404

    gen = await client.post(
        "/api/v1/ops/washes/generate",
        headers=headers,
        json={"society_id": str(world["society_id"])},
    )
    assert gen.status_code == 200

    bad = await client.post(
        f"/api/v1/ops/washes/{skipped_id}/complete",
        headers=headers,
        json={},
    )
    assert bad.status_code == 409

    bad_miss = await client.post(
        f"/api/v1/ops/washes/{new_id}/miss",
        headers=headers,
        json={},
    )
    assert bad_miss.status_code == 409

    by_user = await client.get(
        "/api/v1/ops/washes",
        headers=headers,
        params={"user_id": str(world["user_id"]), "page": 1},
    )
    assert by_user.status_code == 200
    assert by_user.json()["total"] >= 1
