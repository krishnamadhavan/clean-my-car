"""Modules 12–15 — content, support, app config, webhooks, ops platform."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from app.core.passwords import hash_password
from app.db.session import AsyncSessionLocal
from app.models.ops_operator import OPS_ROLE_SUPPORT, OpsOperator
from app.models.payment import Payment, PaymentKind, PaymentStatus
from app.models.user import User
from tests.helpers import register_and_login, unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _ops_token(client: AsyncClient) -> str:
    email = f"m1215-{unique_phone()}@ops.test"
    password = "password99"
    async with AsyncSessionLocal() as session:
        session.add(
            OpsOperator(
                email=email,
                password_hash=hash_password(password),
                name="Platform Ops",
                roles=[OPS_ROLE_SUPPORT],
            )
        )
        await session.commit()
    login = await client.post(
        "/api/v1/ops/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


async def test_public_content_and_app_config(client: AsyncClient) -> None:
    faq = await client.get("/api/v1/content/faq")
    assert faq.status_code == 200
    assert faq.json()["items"]

    legal = await client.get("/api/v1/content/legal/terms")
    assert legal.status_code == 200
    assert legal.json()["doc_type"] == "terms"
    assert legal.json()["title"]

    contact = await client.get("/api/v1/support/contact")
    assert contact.status_code == 200

    cfg = await client.get("/api/v1/app/config")
    assert cfg.status_code == 200
    assert cfg.json()["min_ios_version"]

    boot = await client.get("/api/v1/app/bootstrap")
    assert boot.status_code == 200
    assert boot.json()["authenticated"] is False

    tokens = await register_and_login(client)
    boot_auth = await client.get(
        "/api/v1/app/bootstrap",
        headers=_auth(tokens["access_token"]),
    )
    assert boot_auth.status_code == 200
    assert boot_auth.json()["authenticated"] is True
    assert boot_auth.json()["user_id"]


async def test_support_tickets_consumer_and_ops(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    created = await client.post(
        "/api/v1/me/support/tickets",
        headers=headers,
        json={"category": "billing", "message": "Need help with payment"},
    )
    assert created.status_code == 201, created.text
    ticket_id = created.json()["id"]
    assert created.json()["status"] == "open"

    listed = await client.get("/api/v1/me/support/tickets", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    detail = await client.get(f"/api/v1/me/support/tickets/{ticket_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == ticket_id

    ops = _auth(await _ops_token(client))
    queue = await client.get("/api/v1/ops/support/tickets", headers=ops)
    assert queue.status_code == 200
    assert queue.json()["total"] >= 1

    patched = await client.patch(
        f"/api/v1/ops/support/tickets/{ticket_id}",
        headers=ops,
        json={"status": "in_progress", "ops_reply": "Looking into it"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["status"] == "in_progress"
    assert patched.json()["ops_reply"] == "Looking into it"


async def test_ops_content_app_config_audit_seed(client: AsyncClient) -> None:
    ops = _auth(await _ops_token(client))

    faq = await client.put(
        "/api/v1/ops/content/faq",
        headers=ops,
        json={
            "items": [
                {
                    "question": "How do I cancel?",
                    "answer": "Cancel from Plan; service continues until month end.",
                    "category": "billing",
                    "display_order": 0,
                }
            ]
        },
    )
    assert faq.status_code == 200, faq.text
    assert len(faq.json()["items"]) == 1

    public_faq = await client.get("/api/v1/content/faq")
    assert public_faq.json()["items"][0]["question"] == "How do I cancel?"

    legal = await client.put(
        "/api/v1/ops/content/legal/privacy",
        headers=ops,
        json={
            "version": "1.1",
            "title": "Privacy Policy",
            "body": "We respect your privacy.",
        },
    )
    assert legal.status_code == 200, legal.text
    assert legal.json()["version"] == "1.1"

    pub_legal = await client.get("/api/v1/content/legal/privacy")
    assert pub_legal.json()["body"] == "We respect your privacy."

    cfg = await client.put(
        "/api/v1/ops/app/config",
        headers=ops,
        json={
            "min_ios_version": "17.0",
            "force_update": False,
            "feature_flags": {"washes": True},
            "support_email": "help@cleanmycar.in",
        },
    )
    assert cfg.status_code == 200, cfg.text
    assert cfg.json()["feature_flags"]["washes"] is True
    assert cfg.json()["support_email"] == "help@cleanmycar.in"

    got = await client.get("/api/v1/ops/app/config", headers=ops)
    assert got.status_code == 200
    assert got.json()["support_email"] == "help@cleanmycar.in"

    audit = await client.get("/api/v1/ops/audit", headers=ops)
    assert audit.status_code == 200
    assert audit.json()["total"] >= 1

    preview = await client.post(
        "/api/v1/ops/seed/preview",
        headers=ops,
        json={
            "cities": [{"name": "UniqueCityXYZ", "state": "KA"}],
            "societies": [{"name": "Soc", "city_name": "UniqueCityXYZ"}],
            "vehicle_makes": [{"name": "UniqueMakeXYZ"}],
            "vehicle_models": [{"name": "Model", "make_name": "UniqueMakeXYZ"}],
            "pricing": [{"city_name": "UniqueCityXYZ"}],
        },
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["dry_run"] is True
    assert preview.json()["would_create_cities"] >= 1


async def test_payment_webhooks(client: AsyncClient) -> None:
    phone = f"+91{unique_phone()}"
    async with AsyncSessionLocal() as session:
        user = User(phone=phone, is_active=True)
        session.add(user)
        await session.flush()
        payment = Payment(
            user_id=user.id,
            amount_paise=10000,
            currency="INR",
            status=PaymentStatus.pending,
            kind=PaymentKind.subscription_start,
            provider="manual",
            provider_ref="WH-REF-1",
        )
        pay2 = Payment(
            user_id=user.id,
            amount_paise=5000,
            currency="INR",
            status=PaymentStatus.pending,
            kind=PaymentKind.renewal,
            provider="manual",
            provider_ref="WH-REF-2",
        )
        session.add_all([payment, pay2])
        await session.commit()
        await session.refresh(payment)
        await session.refresh(pay2)
        payment_id = payment.id
        pay2_id = pay2.id

    ok = await client.post(
        "/api/v1/webhooks/payments/manual",
        json={"event": "captured", "payment_id": str(payment_id)},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["accepted"] is True
    assert ok.json()["status"] == "succeeded"

    again = await client.post(
        "/api/v1/webhooks/payments/manual",
        json={"event": "captured", "provider_ref": "WH-REF-1"},
    )
    assert again.status_code == 200
    assert again.json()["status"] == "succeeded"

    failed = await client.post(
        "/api/v1/webhooks/payments/razorpay",
        json={
            "event": "failed",
            "payment_id": str(pay2_id),
            "failure_reason": "insufficient_funds",
        },
    )
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"

    refund = await client.post(
        "/api/v1/webhooks/payments/manual/refunds",
        json={"event": "refunded", "payment_id": str(payment_id)},
    )
    assert refund.status_code == 200
    assert "Refund" in refund.json()["message"]

    bad = await client.post(
        "/api/v1/webhooks/payments/manual",
        json={"event": "unknown", "payment_id": str(payment_id)},
    )
    assert bad.status_code == 400

    missing = await client.post(
        "/api/v1/webhooks/payments/manual",
        json={"event": "captured", "payment_id": str(uuid.uuid4())},
    )
    assert missing.status_code == 404

    no_ref = await client.post(
        "/api/v1/webhooks/payments/manual",
        json={"event": "captured"},
    )
    assert no_ref.status_code == 400


async def test_support_ticket_not_found_and_audit_filters(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])
    missing = await client.get(
        f"/api/v1/me/support/tickets/{uuid.uuid4()}",
        headers=headers,
    )
    assert missing.status_code == 404

    ops = _auth(await _ops_token(client))
    await client.put(
        "/api/v1/ops/content/faq",
        headers=ops,
        json={"items": [{"question": "Q", "answer": "A"}]},
    )
    filtered = await client.get(
        "/api/v1/ops/audit",
        headers=ops,
        params={"action": "faq.replace", "resource_type": "faq"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] >= 1

    seed_warn = await client.post(
        "/api/v1/ops/seed/preview",
        headers=ops,
        json={
            "cities": [{"name": ""}],
            "vehicle_makes": [{"name": ""}],
            "societies": [{"name": "Only"}],
        },
    )
    assert seed_warn.status_code == 200
    assert seed_warn.json()["warnings"]

    # Ops ticket not found
    ghost = await client.patch(
        f"/api/v1/ops/support/tickets/{uuid.uuid4()}",
        headers=ops,
        json={"status": "closed"},
    )
    assert ghost.status_code == 404
