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
from swealog.api.routes.query import get_quilto_dependency


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


def _create_mock_quilto_override(
    response: str = "Your bench press has improved.",
    sources: list[str] | None = None,
    confidence: float = 0.85,
    clarification_questions: list[MagicMock] | None = None,
    debug: MagicMock | None = None,
    raise_error: Exception | None = None,
) -> MagicMock:
    """Create a mock Quilto instance with configured session.process() behavior."""
    mock_process_result = MagicMock()
    mock_process_result.response = response
    mock_process_result.source_entry_ids = sources or []
    mock_process_result.confidence = confidence
    mock_process_result.clarification_questions = clarification_questions
    mock_process_result.debug = debug

    mock_session = MagicMock()
    if raise_error:
        mock_session.process = AsyncMock(side_effect=raise_error)
    else:
        mock_session.process = AsyncMock(return_value=mock_process_result)

    mock_quilto = MagicMock()
    mock_quilto.create_session.return_value = mock_session

    return mock_quilto


class TestQueryEndpoint:
    """Tests for POST /query endpoint."""

    @pytest.mark.asyncio
    async def test_query_returns_response(self, override_dependencies: None) -> None:
        """Test /query returns a response with all required fields."""
        mock_quilto = _create_mock_quilto_override(
            response="Your bench press has improved.",
            sources=["2026-01-10_09-00-00"],
            confidence=0.85,
        )

        app.dependency_overrides[get_quilto_dependency] = lambda: mock_quilto
        try:
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
            assert data["response"] == "Your bench press has improved."
        finally:
            app.dependency_overrides.pop(get_quilto_dependency, None)

    @pytest.mark.asyncio
    async def test_query_handles_clarification(self, override_dependencies: None) -> None:
        """Test /query handles clarification questions from Quilto."""
        mock_question = MagicMock()
        mock_question.question = "What time period are you interested in?"

        mock_quilto = _create_mock_quilto_override(
            response=None,  # type: ignore[arg-type]
            sources=[],
            confidence=None,  # type: ignore[arg-type]
            clarification_questions=[mock_question],
        )

        app.dependency_overrides[get_quilto_dependency] = lambda: mock_quilto
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/query",
                    json={"text": "How did I do?"},
                )

            assert response.status_code == 200
            data = response.json()
            assert "Clarification needed" in data["response"]
            assert data["confidence"] == 0.0
        finally:
            app.dependency_overrides.pop(get_quilto_dependency, None)

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

    @pytest.mark.asyncio
    async def test_query_session_error_returns_500(self, override_dependencies: None) -> None:
        """Test that RuntimeError from Quilto session returns 500."""
        mock_quilto = _create_mock_quilto_override(raise_error=RuntimeError("Session not connected"))

        app.dependency_overrides[get_quilto_dependency] = lambda: mock_quilto
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/query",
                    json={"text": "test query"},
                )

            assert response.status_code == 500
            data = response.json()
            assert "Session error" in data.get("detail", "")
        finally:
            app.dependency_overrides.pop(get_quilto_dependency, None)


class TestQueryPartialResponse:
    """Tests for partial response handling via Quilto."""

    @pytest.mark.asyncio
    async def test_partial_when_retry_count_exceeds_threshold(self, override_dependencies: None) -> None:
        """Test partial=True when debug.retry_count >= 2."""
        mock_debug = MagicMock()
        mock_debug.retry_count = 2

        mock_quilto = _create_mock_quilto_override(
            response="Partial response.",
            sources=[],
            confidence=0.4,
            debug=mock_debug,
        )

        app.dependency_overrides[get_quilto_dependency] = lambda: mock_quilto
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/query",
                    json={"text": "test query"},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["partial"] is True
        finally:
            app.dependency_overrides.pop(get_quilto_dependency, None)

    @pytest.mark.asyncio
    async def test_not_partial_when_debug_none(self, override_dependencies: None) -> None:
        """Test partial=False when debug is None."""
        mock_quilto = _create_mock_quilto_override(
            response="Full response.",
            sources=["entry1"],
            confidence=0.9,
            debug=None,
        )

        app.dependency_overrides[get_quilto_dependency] = lambda: mock_quilto
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/query",
                    json={"text": "test query"},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["partial"] is False
        finally:
            app.dependency_overrides.pop(get_quilto_dependency, None)
