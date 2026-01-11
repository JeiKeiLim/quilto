"""Shared pytest fixtures for Swealog tests.

This module provides fixtures specific to Swealog application tests:
- mock_llm: Mocked LLM completions for unit tests
- storage_fixture: Isolated file storage per test
- domain_fixture: Test domain module instances

Note: use_real_ollama fixture is defined in the root conftest.py.
"""

from collections.abc import Callable, Generator
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from quilto import DomainModule
from swealog.domains.general_fitness import general_fitness


def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers.

    Args:
        config: pytest configuration object.
    """
    config.addinivalue_line(
        "markers",
        "accuracy: marks tests as accuracy tests (deselect with '-m \"not accuracy\"')",
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require real Ollama (run with --use-real-ollama)",
    )


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
        ...         "claude": "Response from Claude",
        ...         "ollama/": "Response from Ollama",
        ...         "_default": "Fallback response",
        ...     })
        ...
        ...     client = LLMClient(config)
        ...     result = await client.complete("analyzer", messages)

    Advanced usage:
        >>> mock_llm._call_history  # List of all call kwargs
        >>> mock_llm._mock  # The underlying AsyncMock
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
def storage_fixture(tmp_path: Path) -> Path:
    """Provide isolated storage directory with proper directory structure.

    Creates logs/(raw|parsed)/{YYYY}/{MM}/ structure per AR2 architecture decision.
    This is a stub implementation; real StorageRepository comes in Story 2.1.

    Args:
        tmp_path: pytest's built-in tmp_path fixture for isolation.

    Returns:
        Path to the isolated storage root directory.
    """
    now = datetime.now()
    year, month = now.strftime("%Y"), now.strftime("%m")

    for subdir in ["raw", "parsed"]:
        (tmp_path / "logs" / subdir / year / month).mkdir(parents=True)

    return tmp_path


@pytest.fixture
def domain_fixture() -> DomainModule:
    """Provide GeneralFitness domain module for tests.

    Returns the general_fitness singleton from swealog.domains.general_fitness.
    Supports parameterized domains for future subdomain testing via pytest.param.

    Returns:
        The general_fitness domain module instance.
    """
    return general_fitness


@pytest.fixture
def skip_without_real_ollama(use_real_ollama: bool) -> None:
    """Skip test if not running with real Ollama.

    Use with @pytest.mark.integration marker for real LLM tests.

    Args:
        use_real_ollama: Boolean indicating if real Ollama is enabled.

    Raises:
        pytest.skip: If real Ollama is not enabled.
    """
    if not use_real_ollama:
        pytest.skip("Requires --use-real-ollama flag")
