"""Separate consumer vs ops Swagger / OpenAPI surfaces."""

from __future__ import annotations

from httpx import AsyncClient


async def test_root_lists_both_docs(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["docs"] == "/docs"
    assert body["docs_ops"] == "/ops/docs"
    assert body["openapi"] == "/openapi.json"
    assert body["openapi_ops"] == "/ops/openapi.json"


async def test_consumer_openapi_excludes_ops_paths(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/ops/health" not in paths
    assert schema["info"]["title"].endswith("(Consumer)")


async def test_ops_openapi_only_ops_paths(client: AsyncClient) -> None:
    response = await client.get("/ops/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]
    assert paths, "ops OpenAPI should list at least one route"
    assert all(p.startswith("/api/v1/ops") for p in paths)
    assert "/api/v1/ops/health" in paths
    assert "/api/v1/health" not in paths
    assert schema["info"]["title"].endswith("(Ops)")


async def test_swagger_ui_pages(client: AsyncClient) -> None:
    consumer = await client.get("/docs")
    assert consumer.status_code == 200
    assert "swagger" in consumer.text.lower() or "Swagger" in consumer.text

    ops = await client.get("/ops/docs")
    assert ops.status_code == 200
    assert "swagger" in ops.text.lower() or "Swagger" in ops.text
    assert "/ops/openapi.json" in ops.text


async def test_ops_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ops/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "surface": "ops"}
