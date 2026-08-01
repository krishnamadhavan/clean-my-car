"""Extra tests to keep application coverage ≥ 95%."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
)
from app.core.security import create_access_token, decode_access_token
from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.city import City
from app.models.society import Society
from app.models.user import User
from app.schemas.user import MeUpdate
from httpx import AsyncClient
from sqlalchemy import update

from tests.helpers import register_and_login, unique_phone


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


# ---------------------------------------------------------------------------
# Core / config / security / exceptions
# ---------------------------------------------------------------------------


def test_settings_database_url_normalization() -> None:
    get_settings.cache_clear()
    s = Settings(
        DATABASE_URL="postgres://u:p@localhost:5432/db",
        JWT_SECRET_KEY="x",
    )
    assert s.async_database_url.startswith("postgresql+asyncpg://")

    get_settings.cache_clear()
    s2 = Settings(
        DATABASE_URL="postgresql://u:p@localhost:5432/db",
        JWT_SECRET_KEY="x",
    )
    assert "+asyncpg" in s2.async_database_url

    get_settings.cache_clear()
    s3 = Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
        JWT_SECRET_KEY="x",
    )
    assert s3.async_database_url == "postgresql+asyncpg://u:p@localhost:5432/db"
    get_settings.cache_clear()


def test_settings_is_development() -> None:
    get_settings.cache_clear()
    assert Settings(APP_ENV="local", JWT_SECRET_KEY="x").is_development
    get_settings.cache_clear()
    assert not Settings(APP_ENV="production", JWT_SECRET_KEY="x").is_development
    get_settings.cache_clear()


def test_create_access_token_extra_claims() -> None:
    settings = get_settings()
    token = create_access_token(
        subject=uuid4(),
        settings=settings,
        extra_claims={"role": "user"},
    )
    payload = decode_access_token(token, settings=settings)
    assert payload["role"] == "user"
    assert payload["type"] == "access"


def test_exception_classes() -> None:
    assert ForbiddenError().status_code == 403
    assert NotFoundError().status_code == 404
    assert ConflictError().status_code == 409
    assert RateLimitError().status_code == 429


def test_me_update_validators() -> None:
    assert MeUpdate(name="  ").name is None
    assert MeUpdate(name="  A  ").name == "A"
    assert MeUpdate(email="").email is None
    with pytest.raises(ValueError):
        MeUpdate.model_validate({"email": "not-an-email"})


# ---------------------------------------------------------------------------
# Health ready + auth edge cases
# ---------------------------------------------------------------------------


async def test_ready_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "up"


async def test_invalid_bearer_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401


async def test_wrong_scheme(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/me",
        headers={"Authorization": "Basic abc"},
    )
    assert response.status_code == 401


async def test_refresh_token_as_access_rejected(client: AsyncClient) -> None:
    """Craft a JWT with type != access."""
    settings = get_settings()
    now = datetime.now(UTC)
    bad = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    response = await client.get("/api/v1/me", headers=_auth(bad))
    assert response.status_code == 401


async def test_access_token_bad_sub(client: AsyncClient) -> None:
    settings = get_settings()
    now = datetime.now(UTC)
    bad = jwt.encode(
        {
            "sub": "not-a-uuid",
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    response = await client.get("/api/v1/me", headers=_auth(bad))
    assert response.status_code == 401


async def test_access_token_unknown_user(client: AsyncClient) -> None:
    settings = get_settings()
    token = create_access_token(subject=uuid4(), settings=settings)
    response = await client.get("/api/v1/me", headers=_auth(token))
    assert response.status_code == 401


async def test_otp_verify_without_request(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": unique_phone(), "otp": "123456"},
    )
    assert response.status_code == 401


async def test_otp_cooldown(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "otp_resend_cooldown_seconds", 60)
    phone = unique_phone()
    first = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert first.status_code == 200
    second = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert second.status_code == 429
    assert second.json()["code"] == "otp_cooldown"
    monkeypatch.setattr(settings, "otp_resend_cooldown_seconds", 0)


async def test_otp_hourly_rate_limit(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "otp_resend_cooldown_seconds", 0)
    monkeypatch.setattr(settings, "otp_max_requests_per_hour", 2)
    phone = unique_phone()
    assert (await client.post("/api/v1/auth/otp/request", json={"phone": phone})).status_code == 200
    assert (await client.post("/api/v1/auth/otp/request", json={"phone": phone})).status_code == 200
    third = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert third.status_code == 429
    assert third.json()["code"] == "otp_rate_limited"
    monkeypatch.setattr(settings, "otp_max_requests_per_hour", 100)


async def test_otp_max_attempts(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "otp_max_attempts", 2)
    phone = unique_phone()
    req = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert req.status_code == 200
    for _ in range(2):
        bad = await client.post(
            "/api/v1/auth/otp/verify",
            json={"phone": phone, "otp": "000000"},
        )
        assert bad.status_code in (401, 429)
    # After max attempts the challenge is locked
    locked = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": req.json()["debug_otp"]},
    )
    assert locked.status_code == 429
    monkeypatch.setattr(settings, "otp_max_attempts", 5)


async def test_deactivate_then_otp_login_forbidden(client: AsyncClient) -> None:
    phone = unique_phone()
    tokens = await register_and_login(client, phone=phone)
    await client.post("/api/v1/me/deactivate", headers=_auth(tokens["access_token"]))
    req = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    otp = req.json()["debug_otp"]
    verify = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": otp},
    )
    assert verify.status_code == 403
    assert verify.json()["code"] == "account_inactive"


async def test_logout_unknown_token_ok(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "totally-unknown-token"},
    )
    assert response.status_code == 200


async def test_production_otp_hides_debug(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "otp_return_in_response", False)
    phone = unique_phone()
    response = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert response.status_code == 200
    assert response.json()["debug_otp"] is None
    monkeypatch.setattr(settings, "app_env", "test")


async def test_deleted_user_naive_datetime_cooloff(client: AsyncClient) -> None:
    """Cover deleted_at without tzinfo branch in cool-off policy."""
    phone = unique_phone()
    tokens = await register_and_login(client, phone=phone)
    await client.delete("/api/v1/me", headers=_auth(tokens["access_token"]))

    async with AsyncSessionLocal() as session:
        # strip tz for branch coverage
        await session.execute(
            update(User)
            .where(User.phone == f"+91{phone}")
            .values(deleted_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=3))
        )
        await session.commit()

    again = await register_and_login(client, phone=phone)
    assert again["access_token"]


# ---------------------------------------------------------------------------
# Location edge cases
# ---------------------------------------------------------------------------


async def _seed() -> dict:
    city = City(name=f"City-{uuid4().hex[:6]}", state="KA", is_active=True, display_order=1)
    other = City(name=f"Other-{uuid4().hex[:6]}", state="MH", is_active=True, display_order=2)
    async with AsyncSessionLocal() as session:
        session.add_all([city, other])
        await session.flush()
        live = Society(
            city_id=city.id,
            name="Live Soc",
            address_line="Addr",
            service_weekdays=[0, 2, 4],
            is_serviceable=True,
        )
        orphan_live = Society(
            city_id=other.id,
            name="Other Live",
            service_weekdays=[1, 3, 5],
            is_serviceable=True,
        )
        session.add_all([live, orphan_live])
        await session.commit()
        await session.refresh(city)
        await session.refresh(other)
        await session.refresh(live)
        await session.refresh(orphan_live)
        return {
            "city_id": city.id,
            "other_city_id": other.id,
            "live_id": live.id,
            "other_live_id": orphan_live.id,
        }


async def test_list_societies_city_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/cities/{uuid4()}/societies")
    assert response.status_code == 404


async def test_list_societies_pagination_bounds(client: AsyncClient) -> None:
    data = await _seed()
    response = await client.get(
        f"/api/v1/cities/{data['city_id']}/societies",
        params={"page": 1, "page_size": 500},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 100  # clamped in LocationService


async def test_set_location_city_unavailable(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    response = await client.put(
        "/api/v1/me/location",
        headers=_auth(tokens["access_token"]),
        json={"city_id": str(uuid4()), "society_id": str(uuid4())},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "city_not_available"


async def test_set_location_society_city_mismatch(client: AsyncClient) -> None:
    data = await _seed()
    tokens = await register_and_login(client)
    response = await client.put(
        "/api/v1/me/location",
        headers=_auth(tokens["access_token"]),
        json={
            "city_id": str(data["city_id"]),
            "society_id": str(data["other_live_id"]),
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "society_city_mismatch"


async def test_get_user_location_stale_inactive_city(client: AsyncClient) -> None:
    data = await _seed()
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])
    put = await client.put(
        "/api/v1/me/location",
        headers=headers,
        json={"city_id": str(data["city_id"]), "society_id": str(data["live_id"])},
    )
    assert put.status_code == 200

    async with AsyncSessionLocal() as session:
        await session.execute(
            update(City).where(City.id == data["city_id"]).values(is_active=False)
        )
        await session.commit()

    got = await client.get("/api/v1/me/location", headers=headers)
    assert got.status_code == 200
    assert got.json()["city"] is None
    assert got.json()["society"] is None


async def test_get_society_missing(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/societies/{uuid4()}")
    assert response.status_code == 404


async def test_patch_me_empty_body(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    response = await client.patch(
        "/api/v1/me",
        headers=_auth(tokens["access_token"]),
        json={},
    )
    assert response.status_code == 200


async def test_double_delete_blocked(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    headers = _auth(tokens["access_token"])
    assert (await client.delete("/api/v1/me", headers=headers)).status_code == 200
    # Second call: auth fails because deleted
    again = await client.delete("/api/v1/me", headers=headers)
    assert again.status_code == 401


async def test_app_error_details_in_response(client: AsyncClient) -> None:
    phone = unique_phone()
    tokens = await register_and_login(client, phone=phone)
    await client.delete("/api/v1/me", headers=_auth(tokens["access_token"]))
    req = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
    verify = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": req.json()["debug_otp"]},
    )
    assert verify.status_code == 403
    assert "details" in verify.json()


async def test_dispose_engine() -> None:
    await dispose_engine()
