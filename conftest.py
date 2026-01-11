"""Root pytest configuration for the entire workspace.

Shared fixtures available to all test directories:
- tests/
- packages/quilto/tests/
- packages/swealog/tests/
"""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add workspace-wide pytest CLI options."""
    parser.addoption(
        "--use-real-ollama",
        action="store_true",
        default=False,
        help="Run integration tests with real Ollama instead of mocks",
    )


@pytest.fixture
def use_real_ollama(request: pytest.FixtureRequest) -> bool:
    """Return True if --use-real-ollama flag was passed."""
    return bool(request.config.getoption("--use-real-ollama", default=False))
