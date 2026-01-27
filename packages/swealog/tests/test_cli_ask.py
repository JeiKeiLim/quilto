"""Tests for swealog ask CLI command."""

from unittest.mock import AsyncMock, MagicMock, patch

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


def _create_mock_process_result(
    response: str = "Test response",
    sources: list[str] | None = None,
    confidence: float = 0.85,
    debug_retry_count: int = 0,
    clarification_questions: list[str] | None = None,
) -> MagicMock:
    """Create a mock ProcessResult for testing."""
    mock_result = MagicMock()
    mock_result.response = response
    mock_result.source_entry_ids = sources or []
    mock_result.confidence = confidence

    # Set up clarification questions
    if clarification_questions:
        mock_questions = []
        for q in clarification_questions:
            mock_q = MagicMock()
            mock_q.question = q
            mock_questions.append(mock_q)
        mock_result.clarification_questions = mock_questions
    else:
        mock_result.clarification_questions = None

    # Set up debug info
    if debug_retry_count >= 2:
        mock_debug = MagicMock()
        mock_debug.retry_count = debug_retry_count
        mock_debug.traces = []
        mock_result.debug = mock_debug
    else:
        mock_result.debug = None

    return mock_result


class TestAskCommand:
    """Tests for the ask CLI command."""

    def test_ask_success(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask displays response, sources, and confidence."""
        mock_result = _create_mock_process_result(
            response="Your bench improved from 175 to 185 lbs.",
            sources=["2026-01-10", "2026-01-15"],
            confidence=0.85,
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["ask", "how has my bench progressed?"])

        assert result.exit_code == 0
        assert "bench improved" in result.output
        assert "85%" in result.output

    def test_ask_partial_shows_warning(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Partial response shows warning message."""
        mock_result = _create_mock_process_result(
            response="Limited data available.",
            sources=[],
            confidence=0.4,
            debug_retry_count=2,  # Triggers partial
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

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
        mock_result = _create_mock_process_result(
            response="Analysis based on multiple entries.",
            sources=[
                "2026-01-01",
                "2026-01-02",
                "2026-01-03",
                "2026-01-04",
                "2026-01-05",
                "2026-01-06",
                "2026-01-07",
                "2026-01-08",
            ],
            confidence=0.9,
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["ask", "summarize my week"])

        assert result.exit_code == 0
        assert "(+3 more)" in result.output

    def test_ask_with_config_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask command respects --config option."""
        mock_result = _create_mock_process_result()

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

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
        mock_result = _create_mock_process_result()

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

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
        mock_result = _create_mock_process_result(
            response="No data found for your query.",
            sources=[],
            confidence=0.3,
            debug_retry_count=2,
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["ask", "what happened last year?"])

        assert result.exit_code == 0
        # Should not show "Sources:" line when empty
        assert "Sources:" not in result.output
        assert "30%" in result.output

    def test_ask_confidence_formatting(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask formats confidence as percentage."""
        mock_result = _create_mock_process_result(
            response="Test response",
            sources=["entry1"],
            confidence=0.72,
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["ask", "test"])

        assert result.exit_code == 0
        assert "72%" in result.output

    def test_ask_handles_clarification(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MagicMock]]
    ) -> None:
        """Ask handles clarification questions from Quilto."""
        mock_result = _create_mock_process_result(
            response="",
            clarification_questions=["What time period?", "What metric?"],
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["ask", "how did I do?"])

        assert result.exit_code == 0
        assert "Clarification needed" in result.output
        assert "What time period?" in result.output
