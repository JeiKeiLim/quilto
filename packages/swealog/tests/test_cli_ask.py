"""Tests for swealog ask CLI command."""

from unittest.mock import MagicMock, patch

import pytest
from swealog.cli import app
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_dependencies() -> tuple[MagicMock, MagicMock, list[MagicMock]]:
    """Create mock dependencies tuple."""
    return (MagicMock(), MagicMock(), [])


class TestAskCommand:
    """Tests for the ask CLI command."""

    def test_ask_success(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask displays response, sources, and confidence."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Your bench improved from 175 to 185 lbs.",
                "sources": ["2026-01-10", "2026-01-15"],
                "confidence": 0.85,
                "is_partial": False,
            }

            result = runner.invoke(app, ["ask", "how has my bench progressed?"])

            assert result.exit_code == 0
            assert "bench improved" in result.output
            assert "85%" in result.output

    def test_ask_partial_shows_warning(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Partial response shows warning message."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Limited data available.",
                "sources": [],
                "confidence": 0.4,
                "is_partial": True,
            }

            result = runner.invoke(app, ["ask", "how fast?"])

            assert result.exit_code == 0
            assert "Partial response" in result.output

    def test_ask_error_shows_message(self, runner: CliRunner) -> None:
        """Ask error shows user-friendly message."""
        with patch("swealog.cli.ask_cmd.get_dependencies", side_effect=Exception("LLM error")):
            result = runner.invoke(app, ["ask", "test"])

            assert result.exit_code == 1
            assert "Query failed" in result.output

    def test_ask_sources_truncation(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask shows first 5 sources with count of remaining."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Analysis based on multiple entries.",
                "sources": [
                    "2026-01-01",
                    "2026-01-02",
                    "2026-01-03",
                    "2026-01-04",
                    "2026-01-05",
                    "2026-01-06",
                    "2026-01-07",
                    "2026-01-08",
                ],
                "confidence": 0.9,
                "is_partial": False,
            }

            result = runner.invoke(app, ["ask", "summarize my week"])

            assert result.exit_code == 0
            assert "(+3 more)" in result.output

    def test_ask_with_config_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask command respects --config option."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Test response",
                "sources": [],
                "confidence": 0.8,
                "is_partial": False,
            }

            result = runner.invoke(app, ["ask", "--config", "/custom/config.yaml", "test query"])

            assert result.exit_code == 0
            # Verify get_dependencies was called with custom config path
            call_args = mock_get_deps.call_args
            assert call_args is not None
            assert str(call_args[0][0]) == "/custom/config.yaml"

    def test_ask_with_storage_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask command respects --storage option."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Test response",
                "sources": [],
                "confidence": 0.8,
                "is_partial": False,
            }

            result = runner.invoke(app, ["ask", "--storage", "/custom/storage", "test query"])

            assert result.exit_code == 0
            # Verify get_dependencies was called with custom storage path
            call_args = mock_get_deps.call_args
            assert call_args is not None
            assert str(call_args[0][1]) == "/custom/storage"

    def test_ask_no_sources(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask with no sources does not show sources line."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "No data found for your query.",
                "sources": [],
                "confidence": 0.3,
                "is_partial": True,
            }

            result = runner.invoke(app, ["ask", "what happened last year?"])

            assert result.exit_code == 0
            # Should not show "Sources:" line when empty
            assert "Sources:" not in result.output
            assert "30%" in result.output

    def test_ask_confidence_formatting(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask formats confidence as percentage."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Test response",
                "sources": ["entry1"],
                "confidence": 0.72,
                "is_partial": False,
            }

            result = runner.invoke(app, ["ask", "test"])

            assert result.exit_code == 0
            assert "72%" in result.output
