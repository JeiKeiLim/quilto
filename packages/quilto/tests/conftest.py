"""Shared pytest fixtures for Quilto tests.

This module provides common fixtures used across test modules,
including the mock_llm fixture for mocking LLM completions.
"""

from collections.abc import Callable, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_llm() -> Generator[Callable[[dict[str, str]], None]]:
    """Mock litellm.acompletion for testing without real LLM calls.

    This fixture patches litellm.acompletion and allows tests to
    configure canned responses based on model name patterns.

    Yields:
        A function to set canned responses. The function accepts a
        dict mapping patterns to response strings. Patterns are matched
        against the litellm model name (e.g., "ollama/qwen2.5:7b").

    Matching priority:
        1. Exact model name match (e.g., "claude-3-haiku-20240307")
        2. Substring match in model name (e.g., "claude" matches "claude-3-haiku")
        3. "_default" key as fallback

    Example:
        >>> def test_with_model_pattern(mock_llm):
        ...     mock_llm({
        ...         "claude": "Response from Claude",  # Matches any Claude model
        ...         "ollama/": "Response from Ollama",  # Matches Ollama models
        ...         "_default": "Fallback response",
        ...     })
        ...
        ...     client = LLMClient(config)
        ...     result = await client.complete("analyzer", messages)

    Advanced usage:
        >>> mock_llm._call_history  # List of all call kwargs
        >>> mock_llm._mock  # The underlying AsyncMock

    Note:
        Since litellm.acompletion only receives the resolved model name
        (not the agent name), matching is based on model name patterns.
        Use provider-specific model names for precise matching.
    """
    canned_responses: dict[str, str] = {}
    call_history: list[dict[str, Any]] = []
    mock_acompletion = AsyncMock()

    def set_responses(responses: dict[str, str]) -> None:
        """Set canned responses by model pattern.

        Args:
            responses: Dict mapping model patterns to response strings.
                Use "_default" for fallback response.
        """
        canned_responses.update(responses)

    def create_response(content: str) -> MagicMock:
        """Create a mock response object with the given content."""
        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content=content))]
        return response

    async def mock_completion(**kwargs: Any) -> MagicMock:
        """Mock implementation of litellm.acompletion."""
        call_history.append(kwargs)

        model = kwargs.get("model", "")

        # Priority 1: Exact match
        if model in canned_responses:
            return create_response(canned_responses[model])

        # Priority 2: Substring match (skip _default)
        for pattern, response_text in canned_responses.items():
            if pattern == "_default":
                continue
            if pattern.lower() in model.lower():
                return create_response(response_text)

        # Priority 3: Default fallback
        default_response = canned_responses.get("_default", "Mock response")
        return create_response(default_response)

    mock_acompletion.side_effect = mock_completion

    with patch("quilto.llm.client.litellm.acompletion", mock_acompletion):
        # Expose the mock for advanced usage
        set_responses._mock = mock_acompletion  # type: ignore[attr-defined]
        set_responses._call_history = call_history  # type: ignore[attr-defined]
        yield set_responses


@pytest.fixture
def mock_llm_json() -> Generator[Callable[[dict[str, dict[str, Any]]], None]]:
    """Mock litellm.acompletion for structured JSON responses.

    Similar to mock_llm but accepts dict responses that are
    serialized to JSON strings, useful for testing complete_structured.

    Yields:
        A function to set canned JSON responses.

    Example:
        >>> def test_structured_response(mock_llm_json):
        ...     mock_llm_json({
        ...         "_default": {"score": 95, "message": "Great!"},
        ...     })
        ...
        ...     client = LLMClient(config)
        ...     result = await client.complete_structured(
        ...         "evaluator", messages, response_model=EvalResult
        ...     )
        ...     assert result.score == 95
    """
    import json

    canned_responses: dict[str, dict[str, Any]] = {}
    mock_acompletion = AsyncMock()

    def set_responses(responses: dict[str, dict[str, Any]]) -> None:
        """Set canned JSON responses for agents."""
        canned_responses.update(responses)

    def create_response(content: str) -> MagicMock:
        """Create a mock response object with the given content."""
        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content=content))]
        return response

    async def mock_completion(**kwargs: Any) -> MagicMock:
        """Mock implementation of litellm.acompletion."""
        model = kwargs.get("model", "")

        for agent_name, response_dict in canned_responses.items():
            if agent_name == "_default":
                continue
            if agent_name.lower() in model.lower():
                return create_response(json.dumps(response_dict))

        # Default response
        default_dict: dict[str, Any] = canned_responses.get("_default", {"result": "ok"})
        return create_response(json.dumps(default_dict))

    mock_acompletion.side_effect = mock_completion

    with patch("quilto.llm.client.litellm.acompletion", mock_acompletion):
        yield set_responses


@pytest.fixture
def mock_llm_error() -> Generator[Callable[[str], None]]:
    """Mock litellm.acompletion to raise errors.

    Useful for testing error handling and fallback behavior.

    Yields:
        A function to set the error message.

    Example:
        >>> def test_fallback_on_error(mock_llm_error):
        ...     mock_llm_error("Connection timeout")
        ...
        ...     with pytest.raises(Exception, match="Connection timeout"):
        ...         await client.complete("agent", messages)
    """
    mock_acompletion = AsyncMock()

    def set_error(message: str) -> None:
        """Set the error to raise on completion calls."""
        mock_acompletion.side_effect = Exception(message)

    with patch("quilto.llm.client.litellm.acompletion", mock_acompletion):
        yield set_error
