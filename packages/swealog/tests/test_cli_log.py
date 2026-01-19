"""Tests for swealog log CLI command."""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swealog.cli import app
from typer.testing import CliRunner


@dataclass
class MockDomain:
    """Mock domain for testing."""

    name: str
    log_schema: dict[str, Any]
    vocabulary: dict[str, str]


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_dependencies() -> tuple[MagicMock, MagicMock, list[MockDomain]]:
    """Create mock dependencies tuple."""
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_domains = [MockDomain(name="GeneralFitness", log_schema={}, vocabulary={})]
    return (mock_client, mock_storage, mock_domains)


class TestLogCommand:
    """Tests for the log CLI command."""

    def test_log_success(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Log with LOG input saves entry and shows success."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.log_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-16_12-00-00"

            result = runner.invoke(app, ["log", "bench 185x5"])

            assert result.exit_code == 0
            assert "Logged entry:" in result.output
            mock_log_flow.assert_called_once()

    def test_log_query_suggests_ask(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Log with QUERY input suggests using ask command."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="QUERY"),
                    confidence=0.9,
                )
            )

            result = runner.invoke(app, ["log", "how much did I bench?"])

            assert result.exit_code == 0
            assert "swealog ask" in result.output

    def test_log_both_shows_query_info(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Log with BOTH input saves entry and shows query portion info."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.log_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="BOTH"),
                    selected_domains=["GeneralFitness"],
                    query_portion="how does this compare?",
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-16_12-00-00"

            result = runner.invoke(app, ["log", "bench 185x5, how does this compare?"])

            assert result.exit_code == 0
            assert "Logged entry:" in result.output
            assert "Query detected" in result.output

    def test_log_error_shows_message(self, runner: CliRunner) -> None:
        """Log error shows user-friendly message and exits with error code."""
        with patch("swealog.cli.log_cmd.get_dependencies", side_effect=Exception("Config error")):
            result = runner.invoke(app, ["log", "test"])

            assert result.exit_code == 1
            assert "Failed to log entry" in result.output

    def test_log_correction_mode(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Log with CORRECTION input handles correction mode."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.log_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="CORRECTION"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target="yesterday",
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-16_12-00-00"

            result = runner.invoke(app, ["log", "actually it was 195x5 yesterday"])

            assert result.exit_code == 0
            assert "Logged entry:" in result.output
            # Verify correction mode was passed
            call_kwargs = mock_log_flow.call_args.kwargs
            assert call_kwargs.get("is_correction") is True
            assert call_kwargs.get("correction_target") == "yesterday"

    def test_log_with_config_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Log command respects --config option."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.log_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-16_12-00-00"

            result = runner.invoke(app, ["log", "--config", "/custom/config.yaml", "test entry"])

            assert result.exit_code == 0
            # Verify get_dependencies was called with custom config path
            call_args = mock_get_deps.call_args
            assert call_args is not None
            assert str(call_args[0][0]) == "/custom/config.yaml"

    def test_log_with_storage_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Log command respects --storage option."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.log_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-16_12-00-00"

            result = runner.invoke(app, ["log", "--storage", "/custom/storage", "test entry"])

            assert result.exit_code == 0
            # Verify get_dependencies was called with custom storage path
            call_args = mock_get_deps.call_args
            assert call_args is not None
            assert str(call_args[0][1]) == "/custom/storage"
