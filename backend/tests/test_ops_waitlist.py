"""Ops Module 4 — waitlist triage APIs."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.passwords import hash_password
from app.db.session import AsyncSessionLocal
from app.models.city import City
from app.models.ops_operator import OPS_ROLE_SUPPORT, OpsOperator
from app.models.waitlist import WaitlistEntry, WaitlistStatus
from app.schemas.ops_waitlist import OpsWaitlistPatch
from tests.helpers import unique_city_display_order, unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _ops_token(client: AsyncClient) -> str:
    email = f"wait-{unique_phone()}@ops.test"
    password = "password99"
    async with AsyncSessionLocal() as session:
        session.add(
            OpsOperator(
                email=email,
                password_hash=hash_password(password),
                name="Support",
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


async def _seed_entries() -> dict:
    phone_a = f"+91{unique_phone()}"
    phone_b = f"+91{unique_phone()}"
    async with AsyncSessionLocal() as session:
        city1 = City(
            name="Mumbai",
            state="MH",
            is_active=True,
            display_order=unique_city_display_order(),
        )
        city2 = City(
            name="Delhi",
            state="DL",
            is_active=True,
            display_order=unique_city_display_order(),
        )
        session.add_all([city1, city2])
        await session.flush()
        e1 = WaitlistEntry(
            city_id=city1.id,
            society_name="Alpha Heights",
            phone=phone_a,
            notes="first",
            status=WaitlistStatus.pending,
        )
        e2 = WaitlistEntry(
            city_id=city1.id,
            society_name="Beta Towers",
            phone=phone_b,
            status=WaitlistStatus.contacted,
        )
        e3 = WaitlistEntry(
            city_id=city2.id,
            society_name="Gamma Residency",
            phone=phone_a,
            status=WaitlistStatus.pending,
        )
        session.add_all([e1, e2, e3])
        await session.commit()
        for e in (e1, e2, e3):
            await session.refresh(e)
        await session.refresh(city1)
        await session.refresh(city2)
        return {
            "city1_id": city1.id,
            "city2_id": city2.id,
            "e1_id": e1.id,
            "e2_id": e2.id,
            "e3_id": e3.id,
            "phone_a": phone_a,
            "phone_b": phone_b,
        }


def test_ops_waitlist_patch_validators() -> None:
    assert OpsWaitlistPatch(notes="  hi  ").notes == "hi"
    assert OpsWaitlistPatch(notes="   ").notes is None
    assert OpsWaitlistPatch(society_name="  X  ").society_name == "X"
    with pytest.raises(ValidationError):
        OpsWaitlistPatch(society_name="  ")


async def test_ops_waitlist_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/ops/waitlist")).status_code == 401


async def test_list_filter_get_patch_summary(client: AsyncClient) -> None:
    data = await _seed_entries()
    headers = _auth(await _ops_token(client))

    listed = await client.get("/api/v1/ops/waitlist", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] >= 3

    by_city = await client.get(
        "/api/v1/ops/waitlist",
        headers=headers,
        params={"city_id": str(data["city1_id"])},
    )
    assert by_city.status_code == 200
    assert by_city.json()["total"] >= 2
    assert all(i["city_id"] == str(data["city1_id"]) for i in by_city.json()["items"])

    by_status = await client.get(
        "/api/v1/ops/waitlist",
        headers=headers,
        params={"status": "contacted"},
    )
    assert by_status.status_code == 200
    assert all(i["status"] == "contacted" for i in by_status.json()["items"])

    by_phone = await client.get(
        "/api/v1/ops/waitlist",
        headers=headers,
        params={"phone": data["phone_a"]},
    )
    assert by_phone.status_code == 200
    assert by_phone.json()["total"] >= 2

    by_society = await client.get(
        "/api/v1/ops/waitlist",
        headers=headers,
        params={"society_name": "Alpha"},
    )
    assert by_society.status_code == 200
    assert by_society.json()["total"] >= 1
    assert "Alpha" in by_society.json()["items"][0]["society_name"]

    detail = await client.get(
        f"/api/v1/ops/waitlist/{data['e1_id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["society_name"] == "Alpha Heights"
    assert detail.json()["city"]["name"] == "Mumbai"

    patched = await client.patch(
        f"/api/v1/ops/waitlist/{data['e1_id']}",
        headers=headers,
        json={"status": "converted", "notes": "  Society onboarded  "},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["status"] == "converted"
    assert patched.json()["notes"] == "Society onboarded"

    summary = await client.get("/api/v1/ops/waitlist/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["total"] >= 3
    statuses = {row["status"]: row["count"] for row in body["by_status"]}
    assert "converted" in statuses or statuses.get("pending", 0) >= 0
    assert len(body["by_city"]) >= 1


async def test_waitlist_entry_not_found(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    response = await client.get(
        "/api/v1/ops/waitlist/00000000-0000-0000-0000-000000000099",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "waitlist_not_found"


async def test_waitlist_phone_partial_and_empty_patch(client: AsyncClient) -> None:
    data = await _seed_entries()
    headers = _auth(await _ops_token(client))
    suffix = data["phone_b"][-4:]
    listed = await client.get(
        "/api/v1/ops/waitlist",
        headers=headers,
        params={"phone": suffix},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    # Empty patch returns current row unchanged
    before = await client.get(
        f"/api/v1/ops/waitlist/{data['e2_id']}",
        headers=headers,
    )
    empty = await client.patch(
        f"/api/v1/ops/waitlist/{data['e2_id']}",
        headers=headers,
        json={},
    )
    assert empty.status_code == 200
    assert empty.json()["status"] == before.json()["status"]
