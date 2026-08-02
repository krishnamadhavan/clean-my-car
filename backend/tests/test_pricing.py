"""Pricing module API tests (Module 6)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.models.city import City
from app.models.pricing import CityInteriorPrice, CityPricing, CitySizePrice
from app.models.society import Society
from app.models.vehicle import VehicleSizeTier


async def _seed_pricing() -> dict:
    city = City(name="Bengaluru", state="Karnataka", is_active=True, display_order=1)
    other = City(name="No Prices", state="XX", is_active=True, display_order=2)

    async with AsyncSessionLocal() as session:
        session.add_all([city, other])
        await session.flush()

        society = Society(
            city_id=city.id,
            name="Green Park",
            address_line="Whitefield",
            service_weekdays=[0, 2, 4],  # Mon Wed Fri
            is_serviceable=True,
            display_order=1,
        )
        pricing = CityPricing(
            city_id=city.id,
            currency="INR",
            amounts_include_gst=True,
            gst_rate_bps=1800,
            is_active=True,
        )
        session.add_all([society, pricing])
        await session.flush()

        session.add_all(
            [
                CitySizePrice(
                    pricing_id=pricing.id,
                    size_tier=VehicleSizeTier.small,
                    monthly_amount_paise=99900,  # ₹999
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
                    pricing_id=pricing.id,
                    interior_frequency=0,
                    monthly_amount_paise=0,
                ),
                CityInteriorPrice(
                    pricing_id=pricing.id,
                    interior_frequency=1,
                    monthly_amount_paise=19900,
                ),
                CityInteriorPrice(
                    pricing_id=pricing.id,
                    interior_frequency=2,
                    monthly_amount_paise=34900,
                ),
                CityInteriorPrice(
                    pricing_id=pricing.id,
                    interior_frequency=4,
                    monthly_amount_paise=59900,
                ),
            ]
        )
        await session.commit()
        await session.refresh(city)
        await session.refresh(other)
        await session.refresh(society)
        return {
            "city_id": city.id,
            "other_city_id": other.id,
            "society_id": society.id,
        }


@pytest.fixture
async def catalog() -> dict:
    return await _seed_pricing()


async def test_interior_options(client: AsyncClient) -> None:
    response = await client.get("/api/v1/interior-options")
    assert response.status_code == 200, response.text
    freqs = [row["frequency"] for row in response.json()["items"]]
    assert freqs == [0, 1, 2, 4]


async def test_city_pricing_matrix(client: AsyncClient, catalog: dict) -> None:
    response = await client.get(f"/api/v1/cities/{catalog['city_id']}/pricing")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["currency"] == "INR"
    assert body["amounts_include_gst"] is True
    assert body["gst_rate_bps"] == 1800
    assert len(body["size_prices"]) == 3
    assert {r["interior_frequency"] for r in body["interior_prices"]} == {0, 1, 2, 4}
    # 3 sizes × 4 frequencies
    assert len(body["matrix"]) == 12
    medium_2x = next(
        c for c in body["matrix"] if c["size_tier"] == "medium" and c["interior_frequency"] == 2
    )
    assert medium_2x["base_amount_paise"] == 129900
    assert medium_2x["interior_amount_paise"] == 34900
    assert medium_2x["monthly_total_paise"] == 129900 + 34900


async def test_city_pricing_missing(client: AsyncClient, catalog: dict) -> None:
    response = await client.get(f"/api/v1/cities/{catalog['other_city_id']}/pricing")
    assert response.status_code == 404
    assert response.json()["code"] == "pricing_not_found"


async def test_quote_full_month_start(client: AsyncClient, catalog: dict) -> None:
    response = await client.post(
        "/api/v1/pricing/quote",
        json={
            "city_id": str(catalog["city_id"]),
            "size_tier": "medium",
            "interior_frequency": 2,
            "start_date": "2026-08-01",
            "society_id": str(catalog["society_id"]),
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["full_monthly_total_paise"] == 129900 + 34900
    assert body["amount_due_now_paise"] == body["full_monthly_total_paise"]
    assert body["is_prorated"] is False
    assert body["billing_month"] == "2026-08"
    assert body["next_billing_month"] == "2026-09"
    assert body["interior_entitled_full_month"] == 2
    assert body["interior_entitled_this_period"] == 2
    assert body["exterior_entitled_full_month"] is not None
    assert body["exterior_entitled_this_period"] == body["exterior_entitled_full_month"]
    assert body["service_weekday_labels"] == ["mon", "wed", "fri"]
    assert body["full_monthly_breakdown"]["total_paise"] == body["full_monthly_total_paise"]


async def test_quote_prorated_mid_month(client: AsyncClient, catalog: dict) -> None:
    response = await client.post(
        "/api/v1/pricing/quote",
        json={
            "city_id": str(catalog["city_id"]),
            "size_tier": "small",
            "interior_frequency": 0,
            "start_date": "2026-08-16",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    full = 99900
    assert body["full_monthly_total_paise"] == full
    assert body["is_prorated"] is True
    assert body["remaining_days"] == 16
    assert body["days_in_month"] == 31
    assert body["amount_due_now_paise"] == int(round(full * 16 / 31))
    assert body["amount_due_now_paise"] < full
    assert body["next_full_month_amount_paise"] == full
    assert body["exterior_entitled_this_period"] is None  # no society


async def test_quote_rejects_bad_interior(client: AsyncClient, catalog: dict) -> None:
    response = await client.post(
        "/api/v1/pricing/quote",
        json={
            "city_id": str(catalog["city_id"]),
            "size_tier": "small",
            "interior_frequency": 3,
        },
    )
    assert response.status_code == 422


async def test_quote_rejects_society_city_mismatch(client: AsyncClient, catalog: dict) -> None:
    # Create a society in the other city
    async with AsyncSessionLocal() as session:
        soc = Society(
            city_id=catalog["other_city_id"],
            name="Wrong City Society",
            service_weekdays=[1, 3, 5],
            is_serviceable=True,
        )
        session.add(soc)
        await session.commit()
        await session.refresh(soc)
        bad_society_id = soc.id

    response = await client.post(
        "/api/v1/pricing/quote",
        json={
            "city_id": str(catalog["city_id"]),
            "size_tier": "small",
            "interior_frequency": 0,
            "start_date": "2026-08-01",
            "society_id": str(bad_society_id),
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "society_city_mismatch"
