"""Root pytest configuration for the entire workspace.

Shared fixtures available to all test directories:
- tests/
- packages/quilto/tests/
- packages/swealog/tests/
"""

from pathlib import Path

import pytest

# Project root for config file discovery
PROJECT_ROOT = Path(__file__).parent


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


@pytest.fixture
def integration_llm_config_path() -> Path:
    """Return path to config.yaml for integration tests.

    This ensures all integration tests use the same config file,
    matching what users experience with the CLI.

    Returns:
        Path to config.yaml in project root.

    Raises:
        FileNotFoundError: If config.yaml doesn't exist.
    """
    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"config.yaml not found at {config_path}. Integration tests require this file to match production config."
        )
    return config_path
