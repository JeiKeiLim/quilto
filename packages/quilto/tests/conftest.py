"""Pytest configuration for Quilto tests.

This module provides pytest hooks and fixtures for the Quilto test suite.
"""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options for pytest.

    Args:
        parser: The pytest argument parser.
    """
    parser.addoption(
        "--use-real-ollama",
        action="store_true",
        default=False,
        help="Run integration tests that require a running Ollama instance",
    )


@pytest.fixture
def use_real_ollama(request: pytest.FixtureRequest) -> bool:
    """Check if real Ollama tests should run.

    Args:
        request: The pytest fixture request.

    Returns:
        True if --use-real-ollama flag was passed.
    """
    return bool(request.config.getoption("--use-real-ollama"))
