"""Ops Module 6 — city pricing master-data APIs."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.passwords import hash_password
from app.db.session import AsyncSessionLocal
from app.models.ops_operator import OPS_ROLE_CATALOG_ADMIN, OpsOperator
from app.schemas.ops_pricing import (
    OpsCityPricingPut,
    OpsInteriorPricesPut,
    OpsSizePricesPut,
)
from tests.helpers import unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


async def _ops_token(client: AsyncClient) -> str:
    email = f"price-{unique_phone()}@ops.test"
    password = "password99"
    async with AsyncSessionLocal() as session:
        session.add(
            OpsOperator(
                email=email,
                password_hash=hash_password(password),
                name="Pricing Admin",
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


async def _create_city(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    res = await client.post(
        "/api/v1/ops/cities",
        headers=headers,
        json={"name": name, "state": "Karnataka", "is_active": True},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_ops_pricing_schema_validators() -> None:
    with pytest.raises(ValidationError):
        OpsCityPricingPut(currency="IN")
    with pytest.raises(ValidationError):
        OpsCityPricingPut(currency="12A")
    with pytest.raises(ValidationError):
        OpsCityPricingPut(gst_rate_bps=-1)
    with pytest.raises(ValidationError):
        OpsSizePricesPut(items=[])
    with pytest.raises(ValidationError):
        OpsSizePricesPut(
            items=[
                {"size_tier": "small", "monthly_amount_paise": 100},
                {"size_tier": "small", "monthly_amount_paise": 200},
            ]
        )
    with pytest.raises(ValidationError):
        OpsSizePricesPut(items=[{"size_tier": "small", "monthly_amount_paise": -1}])
    with pytest.raises(ValidationError):
        OpsInteriorPricesPut(items=[{"interior_frequency": 3, "monthly_amount_paise": 0}])
    with pytest.raises(ValidationError):
        OpsInteriorPricesPut(
            items=[
                {"interior_frequency": 1, "monthly_amount_paise": 100},
                {"interior_frequency": 1, "monthly_amount_paise": 200},
            ]
        )
    put = OpsCityPricingPut(currency=" inr ")
    assert put.currency == "INR"


async def test_ops_pricing_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/ops/pricing/missing")).status_code == 401


async def test_full_pricing_upsert_and_consumer_quote(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    suffix = unique_phone()[:6]
    city_id = await _create_city(client, headers, f"PriceCity {suffix}")

    # Missing before config
    missing = await client.get("/api/v1/ops/pricing/missing", headers=headers)
    assert missing.status_code == 200
    assert any(item["city"]["id"] == city_id for item in missing.json()["items"])

    get_empty = await client.get(f"/api/v1/ops/cities/{city_id}/pricing", headers=headers)
    assert get_empty.status_code == 404
    assert get_empty.json()["code"] == "pricing_not_found"

    # Size prices require pricing config first
    early_sizes = await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing/size-prices",
        headers=headers,
        json={"items": [{"size_tier": "small", "monthly_amount_paise": 99900}]},
    )
    assert early_sizes.status_code == 404

    # Create config
    config = await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing",
        headers=headers,
        json={
            "currency": "inr",
            "amounts_include_gst": True,
            "gst_rate_bps": 1800,
            "is_active": True,
        },
    )
    assert config.status_code == 200, config.text
    body = config.json()
    assert body["currency"] == "INR"
    assert body["city"]["id"] == city_id
    assert body["size_prices"] == []
    assert body["is_active"] is True

    sizes = await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing/size-prices",
        headers=headers,
        json={
            "items": [
                {"size_tier": "small", "monthly_amount_paise": 99900},
                {"size_tier": "medium", "monthly_amount_paise": 129900},
                {"size_tier": "large", "monthly_amount_paise": 159900},
            ]
        },
    )
    assert sizes.status_code == 200, sizes.text
    assert len(sizes.json()["size_prices"]) == 3

    interiors = await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing/interior-prices",
        headers=headers,
        json={
            "items": [
                {"interior_frequency": 0, "monthly_amount_paise": 0},
                {"interior_frequency": 1, "monthly_amount_paise": 19900},
                {"interior_frequency": 2, "monthly_amount_paise": 34900},
                {"interior_frequency": 4, "monthly_amount_paise": 59900},
            ]
        },
    )
    assert interiors.status_code == 200, interiors.text
    assert len(interiors.json()["interior_prices"]) == 4
    assert len(interiors.json()["matrix"]) == 12

    # Ops GET matches
    ops_get = await client.get(f"/api/v1/ops/cities/{city_id}/pricing", headers=headers)
    assert ops_get.status_code == 200
    assert ops_get.json()["gst_rate_bps"] == 1800

    # Consumer PRICE-01 works
    consumer = await client.get(f"/api/v1/cities/{city_id}/pricing")
    assert consumer.status_code == 200, consumer.text
    assert consumer.json()["size_prices"][0]["monthly_amount_paise"] == 99900

    # Consumer + ops quote
    quote_body = {
        "city_id": city_id,
        "size_tier": "medium",
        "interior_frequency": 2,
        "start_date": "2026-08-01",
    }
    consumer_quote = await client.post("/api/v1/pricing/quote", json=quote_body)
    assert consumer_quote.status_code == 200, consumer_quote.text
    assert consumer_quote.json()["full_monthly_total_paise"] == 129900 + 34900

    ops_quote = await client.post(
        "/api/v1/ops/pricing/quote",
        headers=headers,
        json=quote_body,
    )
    assert ops_quote.status_code == 200, ops_quote.text
    assert (
        ops_quote.json()["full_monthly_total_paise"]
        == consumer_quote.json()["full_monthly_total_paise"]
    )

    # No longer missing
    missing2 = await client.get("/api/v1/ops/pricing/missing", headers=headers)
    assert not any(item["city"]["id"] == city_id for item in missing2.json()["items"])

    # Replace size prices (full replace drops omitted tiers)
    replace = await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing/size-prices",
        headers=headers,
        json={"items": [{"size_tier": "small", "monthly_amount_paise": 88800}]},
    )
    assert replace.status_code == 200
    assert len(replace.json()["size_prices"]) == 1
    assert replace.json()["size_prices"][0]["monthly_amount_paise"] == 88800

    # Deactivate → consumer 404, missing list again
    deactivated = await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing",
        headers=headers,
        json={"is_active": False},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    consumer_off = await client.get(f"/api/v1/cities/{city_id}/pricing")
    assert consumer_off.status_code == 404
    assert consumer_off.json()["code"] == "pricing_not_found"

    # Ops still sees inactive pricing
    ops_inactive = await client.get(f"/api/v1/ops/cities/{city_id}/pricing", headers=headers)
    assert ops_inactive.status_code == 200
    assert ops_inactive.json()["is_active"] is False

    missing3 = await client.get("/api/v1/ops/pricing/missing", headers=headers)
    hit = next(item for item in missing3.json()["items"] if item["city"]["id"] == city_id)
    assert hit["has_inactive_pricing"] is True


async def test_pricing_city_not_found(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    missing = "00000000-0000-0000-0000-000000000099"
    response = await client.put(
        f"/api/v1/ops/cities/{missing}/pricing",
        headers=headers,
        json={"currency": "INR"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "city_not_found"


async def test_invalid_size_and_interior_payloads(client: AsyncClient) -> None:
    headers = _auth(await _ops_token(client))
    city_id = await _create_city(client, headers, f"BadPrice {unique_phone()[:6]}")
    await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing",
        headers=headers,
        json={},
    )

    bad_dup = await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing/size-prices",
        headers=headers,
        json={
            "items": [
                {"size_tier": "small", "monthly_amount_paise": 1},
                {"size_tier": "small", "monthly_amount_paise": 2},
            ]
        },
    )
    assert bad_dup.status_code == 422

    bad_freq = await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing/interior-prices",
        headers=headers,
        json={"items": [{"interior_frequency": 3, "monthly_amount_paise": 0}]},
    )
    assert bad_freq.status_code == 422

    bad_currency = await client.put(
        f"/api/v1/ops/cities/{city_id}/pricing",
        headers=headers,
        json={"currency": "RUPEE"},
    )
    assert bad_currency.status_code == 422
