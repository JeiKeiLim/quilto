"""Tests for swealog.api.routes - input and query endpoints.

Tests use mocked dependencies to avoid actual LLM calls.
"""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from swealog.api import app
from swealog.api.dependencies import (
    ConfigNotFoundError,
    get_llm_client,
    get_storage,
)


def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    return MagicMock()


def mock_storage() -> MagicMock:
    """Create a mock storage repository."""
    return MagicMock()


@pytest.fixture
def override_dependencies() -> Generator[None]:
    """Override app dependencies with mocks."""
    app.dependency_overrides[get_llm_client] = mock_llm_client
    app.dependency_overrides[get_storage] = mock_storage
    yield
    app.dependency_overrides.clear()


class TestInputEndpoint:
    """Tests for POST /input endpoint."""

    @pytest.mark.asyncio
    async def test_input_accepts_valid_log(self, override_dependencies: None) -> None:
        """Test /input accepts valid log input."""
        # Mock the RouterAgent
        mock_router_output = MagicMock()
        mock_router_output.input_type.value = "LOG"
        mock_router_output.selected_domains = ["GeneralFitness"]
        mock_router_output.correction_target = None

        with patch("swealog.api.routes.input.RouterAgent") as mock_router_cls:
            mock_router = AsyncMock()
            mock_router.classify.return_value = mock_router_output
            mock_router_cls.return_value = mock_router

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/input",
                    json={"text": "Did bench press 5x5 at 185 lbs"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["input_type"] == "LOG"
        assert data["entry_id"] is not None

    @pytest.mark.asyncio
    async def test_input_accepts_query(self, override_dependencies: None) -> None:
        """Test /input accepts query input."""
        mock_router_output = MagicMock()
        mock_router_output.input_type.value = "QUERY"
        mock_router_output.selected_domains = ["GeneralFitness"]
        mock_router_output.correction_target = None

        with patch("swealog.api.routes.input.RouterAgent") as mock_router_cls:
            mock_router = AsyncMock()
            mock_router.classify.return_value = mock_router_output
            mock_router_cls.return_value = mock_router

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/input",
                    json={"text": "How has my bench press progressed?"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["input_type"] == "QUERY"
        assert data["entry_id"] is None  # No entry_id for pure query

    @pytest.mark.asyncio
    async def test_input_accepts_both(self, override_dependencies: None) -> None:
        """Test /input accepts BOTH input type."""
        mock_router_output = MagicMock()
        mock_router_output.input_type.value = "BOTH"
        mock_router_output.selected_domains = ["GeneralFitness"]
        mock_router_output.correction_target = None
        mock_router_output.query_portion = "How does this compare?"

        with patch("swealog.api.routes.input.RouterAgent") as mock_router_cls:
            mock_router = AsyncMock()
            mock_router.classify.return_value = mock_router_output
            mock_router_cls.return_value = mock_router

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/input",
                    json={"text": "Did bench 200 lbs. How does this compare?"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["input_type"] == "BOTH"
        assert data["entry_id"] is not None
        assert "How does this compare?" in data["message"]

    @pytest.mark.asyncio
    async def test_input_rejects_empty_text(self) -> None:
        """Test /input rejects empty text."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/input",
                json={"text": ""},
            )

        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_input_rejects_missing_text(self) -> None:
        """Test /input rejects missing text field."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/input",
                json={},
            )

        assert response.status_code == 422


class TestQueryEndpoint:
    """Tests for POST /query endpoint."""

    @pytest.mark.asyncio
    async def test_query_returns_response(self, override_dependencies: None) -> None:
        """Test /query returns a response with all required fields."""
        # This test mocks the entire pipeline
        mock_result = {
            "response": "Your bench press has improved.",
            "sources": ["2026-01-10_09-00-00"],
            "confidence": 0.85,
            "is_partial": False,
        }

        with patch(
            "swealog.api.routes.query.execute_query_pipeline",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/query",
                    json={"text": "How has my bench press progressed?"},
                )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert "confidence" in data
        assert "partial" in data

    @pytest.mark.asyncio
    async def test_query_rejects_empty_text(self) -> None:
        """Test /query rejects empty text."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/query",
                json={"text": ""},
            )

        assert response.status_code == 422


class TestErrorHandling:
    """Tests for error handling in API routes."""

    @pytest.mark.asyncio
    async def test_value_error_returns_400(self, override_dependencies: None) -> None:
        """Test that ValueError returns 400."""
        with patch("swealog.api.routes.input.RouterAgent") as mock_router_cls:
            mock_router = AsyncMock()
            mock_router.classify.side_effect = ValueError("Invalid input")
            mock_router_cls.return_value = mock_router

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/input",
                    json={"text": "test input"},
                )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_config_error_returns_500(self) -> None:
        """Test that ConfigNotFoundError returns 500."""

        def raise_config_error() -> None:
            raise ConfigNotFoundError("Config not found")

        app.dependency_overrides[get_llm_client] = raise_config_error
        app.dependency_overrides[get_storage] = mock_storage

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/input",
                    json={"text": "test input"},
                )

            assert response.status_code == 500
            data = response.json()
            assert data["error"] == "configuration_error"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_generic_error_returns_500(self, override_dependencies: None) -> None:
        """Test that generic exceptions return 500."""
        with patch("swealog.api.routes.input.RouterAgent") as mock_router_cls:
            mock_router = AsyncMock()
            mock_router.classify.side_effect = RuntimeError("Unexpected error")
            mock_router_cls.return_value = mock_router

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/input",
                    json={"text": "test input"},
                )

        assert response.status_code == 500
        data = response.json()
        # Generic exceptions are caught by the route handler and returned as HTTPException
        # The detail contains the error type name
        assert "RuntimeError" in data.get("detail", "")
