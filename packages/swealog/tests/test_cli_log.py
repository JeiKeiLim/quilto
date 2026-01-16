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
            patch("swealog.cli.log_cmd.ParserAgent") as mock_parser_cls,
            patch("swealog.cli.log_cmd.ParserInput"),
            patch("swealog.cli.log_cmd.Entry"),
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                )
            )
            mock_parser_cls.return_value.parse = AsyncMock(
                return_value=MagicMock(
                    date="2026-01-16",
                    timestamp="2026-01-16T12:00:00",
                    domain_data={},
                    is_correction=False,
                )
            )

            result = runner.invoke(app, ["log", "bench 185x5"])

            assert result.exit_code == 0
            assert "Logged entry:" in result.output

    def test_log_query_suggests_ask(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Log with QUERY input suggests using ask command."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.log_cmd.RouterInput"),
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="QUERY"),
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
            patch("swealog.cli.log_cmd.ParserAgent") as mock_parser_cls,
            patch("swealog.cli.log_cmd.ParserInput"),
            patch("swealog.cli.log_cmd.Entry"),
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="BOTH"),
                    selected_domains=["GeneralFitness"],
                    query_portion="how does this compare?",
                    correction_target=None,
                )
            )
            mock_parser_cls.return_value.parse = AsyncMock(
                return_value=MagicMock(
                    date="2026-01-16",
                    timestamp="2026-01-16T12:00:00",
                    domain_data={},
                    is_correction=False,
                )
            )

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
        _mock_client, mock_storage, _mock_domains = mock_dependencies
        mock_storage.get_entries_by_pattern.return_value = []

        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.log_cmd.ParserAgent") as mock_parser_cls,
            patch("swealog.cli.log_cmd.ParserInput"),
            patch("swealog.cli.log_cmd.Entry"),
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="CORRECTION"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target="yesterday",
                )
            )
            mock_parser_cls.return_value.parse = AsyncMock(
                return_value=MagicMock(
                    date="2026-01-15",
                    timestamp="2026-01-15T12:00:00",
                    domain_data={},
                    is_correction=True,
                )
            )

            result = runner.invoke(app, ["log", "actually it was 195x5 yesterday"])

            assert result.exit_code == 0
            assert "Logged entry:" in result.output

    def test_log_with_config_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Log command respects --config option."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.log_cmd.ParserAgent") as mock_parser_cls,
            patch("swealog.cli.log_cmd.ParserInput"),
            patch("swealog.cli.log_cmd.Entry"),
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                )
            )
            mock_parser_cls.return_value.parse = AsyncMock(
                return_value=MagicMock(
                    date="2026-01-16",
                    timestamp="2026-01-16T12:00:00",
                    domain_data={},
                    is_correction=False,
                )
            )

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
            patch("swealog.cli.log_cmd.ParserAgent") as mock_parser_cls,
            patch("swealog.cli.log_cmd.ParserInput"),
            patch("swealog.cli.log_cmd.Entry"),
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                )
            )
            mock_parser_cls.return_value.parse = AsyncMock(
                return_value=MagicMock(
                    date="2026-01-16",
                    timestamp="2026-01-16T12:00:00",
                    domain_data={},
                    is_correction=False,
                )
            )

            result = runner.invoke(app, ["log", "--storage", "/custom/storage", "test entry"])

            assert result.exit_code == 0
            # Verify get_dependencies was called with custom storage path
            call_args = mock_get_deps.call_args
            assert call_args is not None
            assert str(call_args[0][1]) == "/custom/storage"
