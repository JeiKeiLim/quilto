"""Tests for swealog.api.app module - app creation and health endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient
from swealog.api import app


@pytest.mark.asyncio
async def test_app_exists() -> None:
    """Test that the FastAPI app instance exists."""
    assert app is not None
    assert app.title == "Swealog API"


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """Test /health endpoint returns ok status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


@pytest.mark.asyncio
async def test_cors_headers() -> None:
    """Test CORS middleware is configured."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # OPTIONS request to check CORS preflight
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    # CORS should allow the origin (wildcard configured)
    assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
async def test_openapi_schema_available() -> None:
    """Test that OpenAPI schema is available."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Swealog API"
    assert data["info"]["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_docs_available() -> None:
    """Test that Swagger docs are available."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/docs")

    assert response.status_code == 200
