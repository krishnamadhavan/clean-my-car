"""Ops Modules 7–8 — subscriptions & payments."""

from __future__ import annotations

from datetime import date

from httpx import AsyncClient

from app.core.passwords import hash_password
from app.db.session import AsyncSessionLocal
from app.models.city import City
from app.models.ops_operator import OPS_ROLE_SUPPORT, OpsOperator
from app.models.payment import Payment, PaymentKind, PaymentStatus
from app.models.society import Society
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.vehicle import VehicleSizeTier
from app.services.ops_subscription import month_end
from tests.helpers import unique_city_display_order, unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _ops_token(client: AsyncClient) -> tuple[str, object]:
    from uuid import UUID

    email = f"subpay-{unique_phone()}@ops.test"
    password = "password99"
    async with AsyncSessionLocal() as session:
        op = OpsOperator(
            email=email,
            password_hash=hash_password(password),
            name="Support",
            roles=[OPS_ROLE_SUPPORT],
        )
        session.add(op)
        await session.commit()
        await session.refresh(op)
        op_id: UUID = op.id
    login = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"], op_id


async def _seed_sub_and_payment() -> dict:
    phone = f"+91{unique_phone()}"
    today = date.today()
    async with AsyncSessionLocal() as session:
        user = User(phone=phone, name="Sub User", is_active=True)
        city = City(
            name="Pune",
            state="MH",
            is_active=True,
            display_order=unique_city_display_order(),
        )
        session.add_all([user, city])
        await session.flush()
        society = Society(
            city_id=city.id,
            name="Oak Residency",
            service_weekdays=[0, 2, 4],
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
            interior_frequency=2,
            status=SubscriptionStatus.active,
            monthly_amount_paise=149900,
            currency="INR",
            period_start=today.replace(day=1),
            period_end=month_end(today),
        )
        session.add(sub)
        await session.flush()
        pay = Payment(
            user_id=user.id,
            subscription_id=sub.id,
            amount_paise=149900,
            currency="INR",
            status=PaymentStatus.pending,
            kind=PaymentKind.subscription_start,
            period_start=sub.period_start,
            period_end=sub.period_end,
            provider="manual",
            provider_ref="MANUAL-001",
        )
        session.add(pay)
        await session.commit()
        return {
            "user_id": user.id,
            "phone": phone,
            "subscription_id": sub.id,
            "payment_id": pay.id,
            "society_id": society.id,
            "period_end": sub.period_end,
        }


async def test_ops_subscriptions_list_and_detail(client: AsyncClient) -> None:
    access, _op_id = await _ops_token(client)
    seeded = await _seed_sub_and_payment()

    listed = await client.get(
        "/api/v1/ops/subscriptions",
        headers=_auth(access),
        params={"q": seeded["phone"][-10:]},
    )
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total"] >= 1
    assert any(item["id"] == str(seeded["subscription_id"]) for item in body["items"])

    detail = await client.get(
        f"/api/v1/ops/subscriptions/{seeded['subscription_id']}",
        headers=_auth(access),
    )
    assert detail.status_code == 200, detail.text
    d = detail.json()
    assert d["status"] == "active"
    assert d["user"]["phone"] == seeded["phone"]
    assert d["society"]["name"] == "Oak Residency"
    assert d["monthly_amount_paise"] == 149900


async def test_ops_subscription_admin_cancel(client: AsyncClient) -> None:
    access, _op_id = await _ops_token(client)
    seeded = await _seed_sub_and_payment()

    cancelled = await client.post(
        f"/api/v1/ops/subscriptions/{seeded['subscription_id']}/cancel",
        headers=_auth(access),
        json={"notes": "user requested via support"},
    )
    assert cancelled.status_code == 200, cancelled.text
    body = cancelled.json()
    assert body["status"] == "cancel_scheduled"
    assert body["cancel_at"] == seeded["period_end"].isoformat()
    assert "ops cancel" in (body.get("notes") or "")

    # Idempotent
    again = await client.post(
        f"/api/v1/ops/subscriptions/{seeded['subscription_id']}/cancel",
        headers=_auth(access),
    )
    assert again.status_code == 200
    assert again.json()["status"] == "cancel_scheduled"


async def test_ops_payments_list_detail_reconcile(client: AsyncClient) -> None:
    access, op_id = await _ops_token(client)
    seeded = await _seed_sub_and_payment()

    listed = await client.get(
        "/api/v1/ops/payments",
        headers=_auth(access),
        params={"status": "pending"},
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] >= 1

    detail = await client.get(
        f"/api/v1/ops/payments/{seeded['payment_id']}",
        headers=_auth(access),
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["status"] == "pending"
    assert detail.json()["provider_ref"] == "MANUAL-001"

    reconciled = await client.post(
        f"/api/v1/ops/payments/{seeded['payment_id']}/reconcile",
        headers=_auth(access),
        json={"notes": "bank UTR matched", "provider_ref": "UTR-999"},
    )
    assert reconciled.status_code == 200, reconciled.text
    body = reconciled.json()
    assert body["status"] == "succeeded"
    assert body["provider_ref"] == "UTR-999"
    assert body["reconciled_by_operator_id"] == str(op_id)
    assert body["captured_at"] is not None
    assert body["reconciled_at"] is not None

    # Idempotent success
    again = await client.post(
        f"/api/v1/ops/payments/{seeded['payment_id']}/reconcile",
        headers=_auth(access),
    )
    assert again.status_code == 200
    assert again.json()["status"] == "succeeded"


async def test_ops_sub_pay_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/ops/subscriptions")).status_code == 401
    assert (await client.get("/api/v1/ops/payments")).status_code == 401
