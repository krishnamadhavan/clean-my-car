"""Ops Module 2 — consumer user support APIs."""

from __future__ import annotations

from uuid import UUID

from httpx import AsyncClient

from app.core.passwords import hash_password
from app.db.session import AsyncSessionLocal
from app.models.city import City
from app.models.ops_operator import OPS_ROLE_SUPPORT, OpsOperator
from app.models.society import Society
from app.models.user import User
from tests.helpers import register_and_login, unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _ops_login(client: AsyncClient) -> str:
    email = f"support-{unique_phone()}@ops.test"
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


async def test_ops_users_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/ops/users")).status_code == 401


async def test_list_and_get_user(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    user_id = tokens["user"]["id"]
    phone = tokens["user"]["phone"]
    ops_token = await _ops_login(client)
    headers = _auth(ops_token)

    listed = await client.get(
        "/api/v1/ops/users",
        headers=headers,
        params={"q": phone},
    )
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total"] >= 1
    assert any(item["id"] == user_id for item in body["items"])

    by_id = await client.get(
        "/api/v1/ops/users",
        headers=headers,
        params={"q": user_id},
    )
    assert by_id.status_code == 200
    assert by_id.json()["total"] >= 1

    detail = await client.get(f"/api/v1/ops/users/{user_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    d = detail.json()
    assert d["id"] == user_id
    assert d["phone"] == phone
    assert d["has_vehicle"] is False
    assert d["has_subscription"] is False


async def test_get_user_404(client: AsyncClient) -> None:
    ops_token = await _ops_login(client)
    response = await client.get(
        "/api/v1/ops/users/00000000-0000-0000-0000-000000000001",
        headers=_auth(ops_token),
    )
    assert response.status_code == 404
    assert response.json()["code"] == "user_not_found"


async def test_deactivate_and_reactivate(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    user_id = tokens["user"]["id"]
    consumer_access = tokens["access_token"]
    ops_token = await _ops_login(client)
    headers = _auth(ops_token)

    # Consumer can access before deactivate
    me = await client.get("/api/v1/me", headers=_auth(consumer_access))
    assert me.status_code == 200

    deactivated = await client.post(
        f"/api/v1/ops/users/{user_id}/deactivate",
        headers=headers,
    )
    assert deactivated.status_code == 200, deactivated.text
    assert deactivated.json()["is_active"] is False

    # Consumer access blocked
    me2 = await client.get("/api/v1/me", headers=_auth(consumer_access))
    assert me2.status_code == 401

    reactivated = await client.post(
        f"/api/v1/ops/users/{user_id}/reactivate",
        headers=headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["is_active"] is True


async def test_deactivate_deleted_account_conflict(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    user_id = tokens["user"]["id"]
    # Soft-delete via consumer API
    deleted = await client.delete("/api/v1/me", headers=_auth(tokens["access_token"]))
    assert deleted.status_code == 200

    ops_token = await _ops_login(client)
    response = await client.post(
        f"/api/v1/ops/users/{user_id}/deactivate",
        headers=_auth(ops_token),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "account_deleted"

    react = await client.post(
        f"/api/v1/ops/users/{user_id}/reactivate",
        headers=_auth(ops_token),
    )
    assert react.status_code == 409


async def test_list_users_by_name_partial(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    await client.patch(
        "/api/v1/me",
        headers=_auth(tokens["access_token"]),
        json={"name": "ZedUniqueOpsUser"},
    )
    ops_token = await _ops_login(client)
    listed = await client.get(
        "/api/v1/ops/users",
        headers=_auth(ops_token),
        params={"q": "ZedUnique"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    assert any(i["name"] == "ZedUniqueOpsUser" for i in listed.json()["items"])


async def test_get_user_with_location(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    user_id = tokens["user"]["id"]
    async with AsyncSessionLocal() as session:
        city = City(name="Chennai", state="TN", is_active=True, display_order=1)
        session.add(city)
        await session.flush()
        society = Society(
            city_id=city.id,
            name="Sea View",
            service_weekdays=[0, 2, 4],
            is_serviceable=True,
        )
        session.add(society)
        await session.flush()
        user = await session.get(User, UUID(str(user_id)))
        assert user is not None
        user.city_id = city.id
        user.society_id = society.id
        await session.commit()

    ops_token = await _ops_login(client)
    detail = await client.get(
        f"/api/v1/ops/users/{user_id}",
        headers=_auth(ops_token),
    )
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["city"]["name"] == "Chennai"
    assert body["society"]["name"] == "Sea View"
