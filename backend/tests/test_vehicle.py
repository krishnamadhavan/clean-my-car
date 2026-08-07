"""Vehicle module tests (Module 5 — make/model catalog + one car per user)."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.models.vehicle import VehicleMake, VehicleModel, VehicleSizeTier
from tests.helpers import register_and_login, unique_display_order


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _seed_catalog() -> dict:
    # Unique names so parallel/sequential tests sharing one DB do not collide.
    suffix = uuid.uuid4().hex[:8]
    maruti = VehicleMake(
        name=f"Maruti Suzuki {suffix}",
        is_active=True,
        display_order=unique_display_order(),
    )
    hyundai = VehicleMake(
        name=f"Hyundai {suffix}",
        is_active=True,
        display_order=unique_display_order(),
    )
    hidden = VehicleMake(
        name=f"Hidden Brand {suffix}",
        is_active=False,
        display_order=unique_display_order(),
    )

    async with AsyncSessionLocal() as session:
        session.add_all([maruti, hyundai, hidden])
        await session.flush()

        swift = VehicleModel(
            make_id=maruti.id,
            name="Swift",
            size_tier=VehicleSizeTier.small,
            is_active=True,
            display_order=1,
        )
        baleno = VehicleModel(
            make_id=maruti.id,
            name="Baleno",
            size_tier=VehicleSizeTier.small,
            is_active=True,
            display_order=2,
        )
        creta = VehicleModel(
            make_id=hyundai.id,
            name="Creta",
            size_tier=VehicleSizeTier.large,
            is_active=True,
            display_order=1,
        )
        inactive_model = VehicleModel(
            make_id=maruti.id,
            name="Old Model",
            size_tier=VehicleSizeTier.medium,
            is_active=False,
            display_order=99,
        )
        session.add_all([swift, baleno, creta, inactive_model])
        await session.commit()
        for row in (maruti, hyundai, hidden, swift, baleno, creta, inactive_model):
            await session.refresh(row)
        return {
            "maruti_id": maruti.id,
            "maruti_name": maruti.name,
            "hyundai_id": hyundai.id,
            "hyundai_name": hyundai.name,
            "hidden_make_id": hidden.id,
            "hidden_name": hidden.name,
            "swift_id": swift.id,
            "baleno_id": baleno.id,
            "creta_id": creta.id,
            "inactive_model_id": inactive_model.id,
        }


@pytest.fixture
async def catalog() -> dict:
    return await _seed_catalog()


async def test_list_makes_only_active(client: AsyncClient, catalog: dict) -> None:
    response = await client.get("/api/v1/vehicle-makes")
    assert response.status_code == 200, response.text
    names = {row["name"] for row in response.json()}
    assert catalog["maruti_name"] in names
    assert catalog["hyundai_name"] in names
    assert catalog["hidden_name"] not in names


async def test_list_models_for_make(client: AsyncClient, catalog: dict) -> None:
    response = await client.get(f"/api/v1/vehicle-makes/{catalog['maruti_id']}/models")
    assert response.status_code == 200, response.text
    body = response.json()
    names = {item["name"] for item in body["items"]}
    assert "Swift" in names
    assert "Baleno" in names
    assert "Old Model" not in names
    swift = next(i for i in body["items"] if i["name"] == "Swift")
    assert swift["size_tier"] == "small"


async def test_list_models_inactive_make_404(client: AsyncClient, catalog: dict) -> None:
    response = await client.get(f"/api/v1/vehicle-makes/{catalog['hidden_make_id']}/models")
    assert response.status_code == 404


async def test_size_tiers_informational(client: AsyncClient) -> None:
    response = await client.get("/api/v1/vehicle-size-tiers")
    assert response.status_code == 200, response.text
    codes = [row["code"] for row in response.json()["items"]]
    assert codes == ["small", "medium", "large"]


async def test_get_vehicle_404_when_none(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    response = await client.get("/api/v1/me/vehicle", headers=_auth(tokens["access_token"]))
    assert response.status_code == 404
    assert response.json()["code"] == "vehicle_not_found"


async def test_put_derives_size_from_model(client: AsyncClient, catalog: dict) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    created = await client.put(
        "/api/v1/me/vehicle",
        headers=headers,
        json={
            "model_id": str(catalog["creta_id"]),
            "nickname": "  Family car  ",
            "plate_number": "ka 01 ab 1234",
            "colour": "white",
            "parking_slot": "B-12",
            "parking_tower": "Tower 2",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["size_tier"] == "large"  # from Creta catalog, not user input
    assert body["model_id"] == str(catalog["creta_id"])
    assert body["make"]["name"] == catalog["hyundai_name"]
    assert body["model"]["name"] == "Creta"
    assert body["nickname"] == "Family car"
    assert body["plate_number"] == "KA01AB1234"
    vehicle_id = body["id"]

    me = await client.get("/api/v1/me", headers=headers)
    assert me.json()["has_vehicle"] is True

    # Replace with a small hatch — size re-derived
    replaced = await client.put(
        "/api/v1/me/vehicle",
        headers=headers,
        json={
            "model_id": str(catalog["swift_id"]),
            "nickname": "City runabout",
        },
    )
    assert replaced.status_code == 200
    again = replaced.json()
    assert again["id"] == vehicle_id
    assert again["size_tier"] == "small"
    assert again["model"]["name"] == "Swift"
    assert again["plate_number"] is None


async def test_put_rejects_size_tier_field(client: AsyncClient, catalog: dict) -> None:
    """Clients must not set size_tier directly (extra=forbid)."""
    tokens = await register_and_login(client)
    response = await client.put(
        "/api/v1/me/vehicle",
        headers=_auth(tokens["access_token"]),
        json={
            "model_id": str(catalog["swift_id"]),
            "size_tier": "large",
        },
    )
    assert response.status_code == 422


async def test_put_rejects_inactive_model(client: AsyncClient, catalog: dict) -> None:
    tokens = await register_and_login(client)
    response = await client.put(
        "/api/v1/me/vehicle",
        headers=_auth(tokens["access_token"]),
        json={"model_id": str(catalog["inactive_model_id"])},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "vehicle_model_not_available"


async def test_patch_model_and_optional_fields(client: AsyncClient, catalog: dict) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    await client.put(
        "/api/v1/me/vehicle",
        headers=headers,
        json={
            "model_id": str(catalog["swift_id"]),
            "nickname": "Hatch",
            "colour": "red",
        },
    )

    patched = await client.patch(
        "/api/v1/me/vehicle",
        headers=headers,
        json={
            "model_id": str(catalog["creta_id"]),
            "colour": "blue",
            "parking_slot": "A-1",
        },
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert body["size_tier"] == "large"
    assert body["model"]["name"] == "Creta"
    assert body["nickname"] == "Hatch"
    assert body["colour"] == "blue"
    assert body["parking_slot"] == "A-1"


async def test_delete_vehicle(client: AsyncClient, catalog: dict) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    await client.put(
        "/api/v1/me/vehicle",
        headers=headers,
        json={"model_id": str(catalog["baleno_id"])},
    )
    deleted = await client.delete("/api/v1/me/vehicle", headers=headers)
    assert deleted.status_code == 200

    gone = await client.get("/api/v1/me/vehicle", headers=headers)
    assert gone.status_code == 404

    me = await client.get("/api/v1/me", headers=headers)
    assert me.json()["has_vehicle"] is False


async def test_vehicle_requires_auth(client: AsyncClient, catalog: dict) -> None:
    assert (await client.get("/api/v1/me/vehicle")).status_code == 401
    assert (
        await client.put(
            "/api/v1/me/vehicle",
            json={"model_id": str(catalog["swift_id"])},
        )
    ).status_code == 401


async def test_put_accepts_standard_and_bh_plate_formats(
    client: AsyncClient, catalog: dict
) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])

    standard = await client.put(
        "/api/v1/me/vehicle",
        headers=headers,
        json={
            "model_id": str(catalog["swift_id"]),
            "plate_number": "ka 01 ab 1234",
        },
    )
    assert standard.status_code == 200, standard.text
    assert standard.json()["plate_number"] == "KA01AB1234"

    bh = await client.put(
        "/api/v1/me/vehicle",
        headers=headers,
        json={
            "model_id": str(catalog["swift_id"]),
            "plate_number": "26 bh 1234 ab",
        },
    )
    assert bh.status_code == 200, bh.text
    assert bh.json()["plate_number"] == "26BH1234AB"


async def test_put_rejects_invalid_plate(client: AsyncClient, catalog: dict) -> None:
    tokens = await register_and_login(client)
    response = await client.put(
        "/api/v1/me/vehicle",
        headers=_auth(tokens["access_token"]),
        json={
            "model_id": str(catalog["swift_id"]),
            "plate_number": "NOT-A-PLATE",
        },
    )
    assert response.status_code == 422
