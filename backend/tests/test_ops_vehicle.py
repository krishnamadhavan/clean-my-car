"""Ops Module 5 — vehicle make/model catalog APIs."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.passwords import hash_password
from app.db.session import AsyncSessionLocal
from app.models.ops_operator import OPS_ROLE_CATALOG_ADMIN, OpsOperator
from app.schemas.ops_vehicle import (
    OpsUserVehiclePatch,
    OpsVehicleMakeCreate,
    OpsVehicleMakePatch,
    OpsVehicleModelCreate,
    OpsVehicleModelPatch,
)
from tests.helpers import register_and_login, unique_display_order, unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _ops_token(client: AsyncClient) -> str:
    email = f"veh-{unique_phone()}@ops.test"
    password = "password99"
    async with AsyncSessionLocal() as session:
        session.add(
            OpsOperator(
                email=email,
                password_hash=hash_password(password),
                name="Catalog",
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


def test_ops_vehicle_schema_validators() -> None:
    with pytest.raises(ValidationError):
        OpsVehicleMakeCreate(name="   ")
    with pytest.raises(ValidationError):
        OpsVehicleMakePatch(name="  ")
    with pytest.raises(ValidationError):
        OpsVehicleModelCreate(name=" ", size_tier="small")
    with pytest.raises(ValidationError):
        OpsVehicleModelPatch(name="")
    with pytest.raises(ValidationError):
        OpsUserVehiclePatch(plate_number="NOT-A-PLATE")
    # Optional blanks become None
    patch = OpsUserVehiclePatch(nickname="  ", colour=" red ", parking_slot=" ")
    assert patch.nickname is None
    assert patch.colour == "red"
    assert patch.parking_slot is None
    assert OpsUserVehiclePatch(plate_number=None).plate_number is None
    assert OpsUserVehiclePatch(plate_number="  ").plate_number is None
    assert OpsVehicleMakePatch(name=None).name is None
    assert OpsVehicleModelPatch(name=None).name is None


async def test_ops_vehicle_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/ops/vehicle-makes")).status_code == 401


async def test_make_and_model_catalog(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    suffix = unique_phone()[:6]

    order_a = unique_display_order()
    order_b = unique_display_order()
    created = await client.post(
        "/api/v1/ops/vehicle-makes",
        headers=headers,
        json={"name": f"  Tata {suffix}  ", "is_active": True, "display_order": order_a},
    )
    assert created.status_code == 201, created.text
    make = created.json()
    assert make["name"] == f"Tata {suffix}"
    make_id = make["id"]

    # Duplicate name
    dup = await client.post(
        "/api/v1/ops/vehicle-makes",
        headers=headers,
        json={"name": f"Tata {suffix}"},
    )
    assert dup.status_code == 409
    assert dup.json()["code"] == "vehicle_make_exists"

    # Duplicate display_order
    order_dup = await client.post(
        "/api/v1/ops/vehicle-makes",
        headers=headers,
        json={"name": f"OrderClash {suffix}", "display_order": order_a},
    )
    assert order_dup.status_code == 409
    assert order_dup.json()["code"] == "vehicle_make_display_order_exists"

    # Empty name rejected
    empty = await client.post(
        "/api/v1/ops/vehicle-makes",
        headers=headers,
        json={"name": "   "},
    )
    assert empty.status_code == 422

    inactive_make = await client.post(
        "/api/v1/ops/vehicle-makes",
        headers=headers,
        json={"name": f"DeadBrand {suffix}", "is_active": False, "display_order": order_b},
    )
    assert inactive_make.status_code == 201
    inactive_make_id = inactive_make.json()["id"]

    makes_all = await client.get(
        "/api/v1/ops/vehicle-makes",
        headers=headers,
        params={"include_inactive": True},
    )
    assert makes_all.status_code == 200
    assert makes_all.json()["total"] >= 2
    make_ids = {m["id"] for m in makes_all.json()["items"]}
    assert make_id in make_ids and inactive_make_id in make_ids

    makes_active = await client.get(
        "/api/v1/ops/vehicle-makes",
        headers=headers,
        params={"include_inactive": False, "page": 1, "page_size": 50},
    )
    assert makes_active.status_code == 200
    assert all(m["is_active"] for m in makes_active.json()["items"])
    assert inactive_make_id not in {m["id"] for m in makes_active.json()["items"]}

    model = await client.post(
        f"/api/v1/ops/vehicle-makes/{make_id}/models",
        headers=headers,
        json={"name": "  Nexon  ", "size_tier": "medium", "is_active": True},
    )
    assert model.status_code == 201, model.text
    assert model.json()["name"] == "Nexon"
    assert model.json()["size_tier"] == "medium"
    model_id = model.json()["id"]

    inactive_model = await client.post(
        f"/api/v1/ops/vehicle-makes/{make_id}/models",
        headers=headers,
        json={"name": "Old", "size_tier": "small", "is_active": False},
    )
    assert inactive_model.status_code == 201

    models = await client.get(
        f"/api/v1/ops/vehicle-makes/{make_id}/models",
        headers=headers,
        params={"include_inactive": True},
    )
    assert models.status_code == 200
    assert models.json()["total"] >= 2

    active_only = await client.get(
        f"/api/v1/ops/vehicle-makes/{make_id}/models",
        headers=headers,
        params={"include_inactive": False},
    )
    assert all(m["is_active"] for m in active_only.json()["items"])

    # Consumer list only active makes/models
    consumer_makes = await client.get("/api/v1/vehicle-makes")
    assert consumer_makes.status_code == 200
    assert any(m["id"] == make_id for m in consumer_makes.json())

    consumer_models = await client.get(f"/api/v1/vehicle-makes/{make_id}/models")
    assert consumer_models.status_code == 200
    cids = {m["id"] for m in consumer_models.json()["items"]}
    assert model_id in cids
    assert inactive_model.json()["id"] not in cids

    other = await client.post(
        "/api/v1/ops/vehicle-makes",
        headers=headers,
        json={"name": f"Other {suffix}", "is_active": True},
    )
    other_id = other.json()["id"]

    # Rename conflict on patch
    conflict = await client.patch(
        f"/api/v1/ops/vehicle-makes/{other_id}",
        headers=headers,
        json={"name": f"Tata {suffix}"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "vehicle_make_exists"

    new_order = unique_display_order()
    patched_make = await client.patch(
        f"/api/v1/ops/vehicle-makes/{make_id}",
        headers=headers,
        json={"display_order": new_order, "name": f"  Tata Motors {suffix}  "},
    )
    assert patched_make.status_code == 200
    assert patched_make.json()["display_order"] == new_order
    assert patched_make.json()["name"] == f"Tata Motors {suffix}"

    patch_order_dup = await client.patch(
        f"/api/v1/ops/vehicle-makes/{make_id}",
        headers=headers,
        json={"display_order": order_b},
    )
    assert patch_order_dup.status_code == 409
    assert patch_order_dup.json()["code"] == "vehicle_make_display_order_exists"

    patched_model = await client.patch(
        f"/api/v1/ops/vehicle-models/{model_id}",
        headers=headers,
        json={"size_tier": "large", "name": "Nexon EV", "is_active": True},
    )
    assert patched_model.status_code == 200
    assert patched_model.json()["size_tier"] == "large"
    assert patched_model.json()["name"] == "Nexon EV"


async def test_user_vehicle_inspect_and_correct(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    suffix = unique_phone()[:6]

    make = await client.post(
        "/api/v1/ops/vehicle-makes",
        headers=headers,
        json={"name": f"Hyundai {suffix}", "is_active": True},
    )
    make_id = make.json()["id"]
    small = await client.post(
        f"/api/v1/ops/vehicle-makes/{make_id}/models",
        headers=headers,
        json={"name": "i20", "size_tier": "small", "is_active": True},
    )
    large = await client.post(
        f"/api/v1/ops/vehicle-makes/{make_id}/models",
        headers=headers,
        json={"name": "Creta", "size_tier": "large", "is_active": True},
    )
    inactive = await client.post(
        f"/api/v1/ops/vehicle-makes/{make_id}/models",
        headers=headers,
        json={"name": "Legacy", "size_tier": "medium", "is_active": False},
    )
    small_id = small.json()["id"]
    large_id = large.json()["id"]
    inactive_id = inactive.json()["id"]

    tokens = await register_and_login(client)
    user_id = tokens["user"]["id"]
    put = await client.put(
        "/api/v1/me/vehicle",
        headers=_auth(tokens["access_token"]),
        json={
            "model_id": small_id,
            "plate_number": "KA01AB1234",
            "nickname": "City car",
        },
    )
    assert put.status_code == 200, put.text
    assert put.json()["size_tier"] == "small"

    ops_view = await client.get(
        f"/api/v1/ops/users/{user_id}/vehicle",
        headers=headers,
    )
    assert ops_view.status_code == 200, ops_view.text
    assert ops_view.json()["model"]["name"] == "i20"
    assert ops_view.json()["make"]["name"] == f"Hyundai {suffix}"

    # Patch fields without changing model
    fields_only = await client.patch(
        f"/api/v1/ops/users/{user_id}/vehicle",
        headers=headers,
        json={
            "colour": "  white  ",
            "parking_slot": "B-12",
            "parking_tower": "Tower A",
        },
    )
    assert fields_only.status_code == 200, fields_only.text
    assert fields_only.json()["colour"] == "white"
    assert fields_only.json()["parking_slot"] == "B-12"
    assert fields_only.json()["size_tier"] == "small"

    # Cannot assign inactive catalog model
    bad_model = await client.patch(
        f"/api/v1/ops/users/{user_id}/vehicle",
        headers=headers,
        json={"model_id": inactive_id},
    )
    assert bad_model.status_code == 400
    assert bad_model.json()["code"] == "vehicle_model_not_available"

    # Cannot clear model_id
    clear_model = await client.patch(
        f"/api/v1/ops/users/{user_id}/vehicle",
        headers=headers,
        json={"model_id": None},
    )
    assert clear_model.status_code == 422

    corrected = await client.patch(
        f"/api/v1/ops/users/{user_id}/vehicle",
        headers=headers,
        json={
            "model_id": large_id,
            "plate_number": "26BH1234AB",
            "nickname": "Corrected SUV",
        },
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["size_tier"] == "large"
    assert corrected.json()["model"]["name"] == "Creta"
    assert corrected.json()["plate_number"] == "26BH1234AB"
    assert corrected.json()["nickname"] == "Corrected SUV"

    # Consumer sees corrected vehicle
    consumer = await client.get(
        "/api/v1/me/vehicle",
        headers=_auth(tokens["access_token"]),
    )
    assert consumer.status_code == 200
    assert consumer.json()["size_tier"] == "large"


async def test_user_vehicle_not_found(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    tokens = await register_and_login(client)
    user_id = tokens["user"]["id"]

    response = await client.get(
        f"/api/v1/ops/users/{user_id}/vehicle",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"

    patch = await client.patch(
        f"/api/v1/ops/users/{user_id}/vehicle",
        headers=headers,
        json={"nickname": "ghost"},
    )
    assert patch.status_code == 404
    assert patch.json()["code"] == "vehicle_not_found"


async def test_make_model_user_not_found(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    missing = "00000000-0000-0000-0000-000000000099"

    response = await client.get(
        f"/api/v1/ops/vehicle-makes/{missing}/models",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_make_not_found"

    create_on_missing = await client.post(
        f"/api/v1/ops/vehicle-makes/{missing}/models",
        headers=headers,
        json={"name": "X", "size_tier": "small"},
    )
    assert create_on_missing.status_code == 404

    model_missing = await client.patch(
        f"/api/v1/ops/vehicle-models/{missing}",
        headers=headers,
        json={"name": "Nope"},
    )
    assert model_missing.status_code == 404
    assert model_missing.json()["code"] == "vehicle_model_not_found"

    make_missing = await client.patch(
        f"/api/v1/ops/vehicle-makes/{missing}",
        headers=headers,
        json={"name": "Nope"},
    )
    assert make_missing.status_code == 404

    user_missing = await client.get(
        f"/api/v1/ops/users/{missing}/vehicle",
        headers=headers,
    )
    assert user_missing.status_code == 404
    assert user_missing.json()["code"] == "user_not_found"

    user_patch = await client.patch(
        f"/api/v1/ops/users/{missing}/vehicle",
        headers=headers,
        json={"nickname": "x"},
    )
    assert user_patch.status_code == 404
    assert user_patch.json()["code"] == "user_not_found"
