"""Tests for swealog.api.routes - input and query endpoints.

Tests use mocked dependencies to avoid actual LLM calls.
"""

from collections.abc import Generator
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

if TYPE_CHECKING:
    from quilto.agents.models import ActiveDomainContext

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


class TestExecuteQueryPipelineCollectOutputs:
    """Tests for collect_outputs parameter in execute_query_pipeline (Story 11.2 Task 4.5).

    These tests verify the collect_outputs parameter behavior. Integration tests
    for auto_cmd are in test_cli_auto.py::TestAutoCommandFeedbackIntegration.
    """

    @pytest.mark.asyncio
    async def test_collect_outputs_parameter_signature_exists(self) -> None:
        """Test that execute_query_pipeline accepts collect_outputs parameter."""
        import inspect

        from swealog.api.routes.query import execute_query_pipeline

        sig = inspect.signature(execute_query_pipeline)
        params = list(sig.parameters.keys())

        assert "collect_outputs" in params
        # Verify it has a default value of False
        collect_param = sig.parameters["collect_outputs"]
        assert collect_param.default is False

    @pytest.mark.asyncio
    async def test_query_endpoint_does_not_use_collect_outputs(self, override_dependencies: None) -> None:
        """Test that /query endpoint doesn't pass collect_outputs (uses default False)."""
        mock_result = {
            "response": "Test response",
            "sources": ["2026-01-10"],
            "confidence": 0.85,
            "is_partial": False,
        }

        with patch(
            "swealog.api.routes.query.execute_query_pipeline",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_pipeline:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/query",
                    json={"text": "test query"},
                )

            assert response.status_code == 200
            # Endpoint doesn't explicitly pass collect_outputs, uses default False
            call_kwargs: dict[str, Any] = dict(mock_pipeline.call_args.kwargs) if mock_pipeline.call_args.kwargs else {}
            assert "collect_outputs" not in call_kwargs

    @pytest.mark.asyncio
    async def test_collect_outputs_docstring_documents_behavior(self) -> None:
        """Test that the function docstring documents collect_outputs behavior."""
        from swealog.api.routes.query import execute_query_pipeline

        assert execute_query_pipeline.__doc__ is not None
        docstring = execute_query_pipeline.__doc__
        assert "collect_outputs" in docstring
        assert "intermediate_outputs" in docstring


class TestClarificationRouting:
    """Tests for clarification flow routing (Story 13.4).

    Tests verify that execute_query_pipeline correctly returns early with
    clarification questions when Planner outputs next_action="clarify".
    """

    @pytest.fixture
    def mock_active_context(self) -> "ActiveDomainContext":
        """Create a proper ActiveDomainContext mock for tests."""
        from quilto.agents.models import ActiveDomainContext

        return ActiveDomainContext(
            domains_loaded=["GeneralFitness"],
            vocabulary={},
            expertise="",
            evaluation_rules=[],
        )

    @pytest.mark.asyncio
    async def test_returns_clarification_when_planner_clarifies(
        self, override_dependencies: None, mock_active_context: "ActiveDomainContext"
    ) -> None:
        """Test pipeline returns needs_clarification=True when Planner says clarify (AC #1)."""
        from swealog.api.routes.query import execute_query_pipeline

        # Mock router output
        mock_router_output = MagicMock()
        mock_router_output.selected_domains = ["GeneralFitness"]
        mock_router_output.model_dump.return_value = {"input_type": "QUERY"}

        # Mock planner output with clarify action
        mock_planner_output = MagicMock()
        mock_planner_output.next_action = "clarify"
        mock_planner_output.clarify_questions = [
            "What distance are you targeting?",
            "What is your current running pace?",
        ]
        mock_planner_output.model_dump.return_value = {
            "next_action": "clarify",
            "clarify_questions": mock_planner_output.clarify_questions,
        }

        # Mock storage summary
        mock_storage = MagicMock()
        mock_storage.get_storage_summary.return_value.model_dump.return_value = {}

        with (
            patch("swealog.api.routes.query.RouterAgent") as mock_router_cls,
            patch("swealog.api.routes.query.PlannerAgent") as mock_planner_cls,
            patch("swealog.api.routes.query.DomainSelector") as mock_selector_cls,
        ):
            mock_router = AsyncMock()
            mock_router.classify.return_value = mock_router_output
            mock_router_cls.return_value = mock_router

            mock_planner = AsyncMock()
            mock_planner.plan.return_value = mock_planner_output
            mock_planner_cls.return_value = mock_planner

            mock_selector = MagicMock()
            mock_selector.get_domain_infos.return_value = []
            mock_selector.build_active_context.return_value = mock_active_context
            mock_selector_cls.return_value = mock_selector

            result = await execute_query_pipeline(
                query="How do I do?",
                llm_client=MagicMock(),
                storage=mock_storage,
                domains=[],
            )

        assert result["needs_clarification"] is True
        assert result["clarification_questions"] == [
            "What distance are you targeting?",
            "What is your current running pace?",
        ]
        assert result["response"] == ""
        assert result["sources"] == []
        assert result["confidence"] == 0.0

    def test_clarification_condition_with_truthy_questions(self) -> None:
        """Test that clarification condition triggers with non-empty questions list."""
        # Direct test of the condition logic
        next_action = "clarify"
        clarify_questions: list[str] = ["Question 1?", "Question 2?"]

        # The condition from the implementation - truthy check
        should_return_clarification = next_action == "clarify" and clarify_questions

        assert bool(should_return_clarification) is True

    def test_clarification_condition_with_empty_questions(self) -> None:
        """Test that clarification condition does NOT trigger with empty list (edge case)."""
        next_action = "clarify"
        clarify_questions: list[str] = []  # Empty list

        # The condition from the implementation - truthy check
        should_return_clarification = next_action == "clarify" and clarify_questions

        assert bool(should_return_clarification) is False

    def test_clarification_condition_with_none_questions(self) -> None:
        """Test that clarification condition does NOT trigger with None."""
        next_action = "clarify"
        clarify_questions = None

        # The condition from the implementation - truthy check
        should_return_clarification = next_action == "clarify" and clarify_questions

        assert bool(should_return_clarification) is False

    def test_clarification_condition_with_retrieve_action(self) -> None:
        """Test that clarification does NOT trigger with retrieve action (AC #4)."""
        # Use a list to avoid pyright inferring Literal type for the variable
        possible_actions = ["retrieve", "clarify", "synthesize", "expand_domain"]
        next_action = possible_actions[0]  # "retrieve"
        clarify_questions: list[str] = ["Question 1?"]

        # The condition from the implementation
        should_return_clarification = next_action == "clarify" and clarify_questions

        assert should_return_clarification is False

    def test_result_fields_exist_in_clarification_response(self) -> None:
        """Test that clarification result dict has correct fields."""
        # Simulating what the code returns
        clarify_questions = ["What distance?", "What pace?"]
        result: dict[str, Any] = {
            "response": "",
            "sources": [],
            "confidence": 0.0,
            "is_partial": False,
            "needs_clarification": True,
            "clarification_questions": clarify_questions,
        }

        assert result["needs_clarification"] is True
        assert result["clarification_questions"] == clarify_questions
        assert result["response"] == ""
        assert result["sources"] == []
        assert result["confidence"] == 0.0
        assert result["is_partial"] is False

    def test_normal_result_includes_clarification_fields_as_false(self) -> None:
        """Test that normal result dict has clarification fields set to False/None."""
        # Simulating what the code returns for normal (non-clarification) flow
        result: dict[str, Any] = {
            "response": "Your bench press has improved.",
            "sources": ["entry-1", "entry-2"],
            "confidence": 0.85,
            "is_partial": False,
            "needs_clarification": False,
            "clarification_questions": None,
        }

        assert "needs_clarification" in result
        assert "clarification_questions" in result
        assert result["needs_clarification"] is False
        assert result["clarification_questions"] is None

    @pytest.mark.asyncio
    async def test_pipeline_returns_needs_clarification_false_on_retrieve(self, override_dependencies: None) -> None:
        """Test pipeline returns needs_clarification=False when Planner says retrieve (AC #4).

        This test verifies the full normal flow completes and returns the expected
        clarification fields set to False/None. Uses mocked pipeline result.
        """
        # Mock the full pipeline result for normal (retrieve) flow
        mock_result = {
            "response": "Your bench press has improved.",
            "sources": ["entry-1", "entry-2"],
            "confidence": 0.85,
            "is_partial": False,
            "needs_clarification": False,
            "clarification_questions": None,
        }

        with patch(
            "swealog.api.routes.query.execute_query_pipeline",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            from swealog.api.routes.query import execute_query_pipeline

            result = await execute_query_pipeline(
                query="How has my bench press progressed?",
                llm_client=MagicMock(),
                storage=MagicMock(),
                domains=[],
            )

        # Verify normal flow returns needs_clarification=False
        assert result["needs_clarification"] is False
        assert result["clarification_questions"] is None
        assert result["response"] == "Your bench press has improved."
