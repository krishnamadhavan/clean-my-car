"""Smoke tests for health endpoints (no DB required for /health)."""

from httpx import AsyncClient


async def test_root(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "service" in body
    assert body["docs"] == "/docs"


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
