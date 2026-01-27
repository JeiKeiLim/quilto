"""Tests for swealog unified CLI command.

Tests the `swealog run` command that routes all input through Quilto.
"""

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


def _create_mock_process_result(
    response: str = "Test response",
    sources: list[str] | None = None,
    confidence: float = 0.85,
    debug_retry_count: int = 0,
    clarification_questions: list[str] | None = None,
    with_debug: bool = False,
    input_type: str = "query",
    parsed_data: dict[str, Any] | None = None,
) -> MagicMock:
    """Create a mock ProcessResult for testing."""
    mock_result = MagicMock()
    mock_result.response = response
    mock_result.source_entry_ids = sources or []
    mock_result.confidence = confidence
    mock_result.input_type = input_type
    mock_result.parsed_data = parsed_data

    # Set up clarification questions
    if clarification_questions:
        mock_questions = []
        for q in clarification_questions:
            mock_q = MagicMock()
            mock_q.question = q
            mock_q.options = None
            mock_questions.append(mock_q)
        mock_result.clarification_questions = mock_questions
    else:
        mock_result.clarification_questions = None

    # Set up debug info
    if debug_retry_count >= 2 or with_debug:
        mock_debug = MagicMock()
        mock_debug.retry_count = debug_retry_count
        mock_debug.traces = []
        mock_result.debug = mock_debug
    else:
        mock_result.debug = None

    return mock_result


class TestUnifiedCommandRoutesLog:
    """AC1: Unified command routes LOG correctly via Quilto."""

    def test_command_routes_log(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Command routes LOG input through Quilto and shows success message."""
        mock_result = _create_mock_process_result(
            input_type="log",
            parsed_data={"entry_id": "2026-01-19_12-00-00"},
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "bench 185x5"])

            assert result.exit_code == 0
            assert "Logged entry:" in result.output
            mock_session.process.assert_called_once_with("bench 185x5", mode="auto")


class TestUnifiedCommandRoutesQuery:
    """AC2: Unified command routes QUERY correctly via Quilto."""

    def test_command_routes_query(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Command routes QUERY input through Quilto and shows response panel."""
        mock_result = _create_mock_process_result(
            response="Your bench improved by 10 lbs.",
            sources=["2026-01-15"],
            confidence=0.85,
            input_type="query",
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "how's my bench progress?"])

            assert result.exit_code == 0
            assert "bench improved" in result.output
            mock_session.process.assert_called_once_with("how's my bench progress?", mode="auto")


class TestUnifiedCommandHandlesBoth:
    """AC3: Unified command handles BOTH input type."""

    def test_command_handles_both(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Command handles BOTH input_type showing log success and response."""
        mock_result = _create_mock_process_result(
            response="Compared to last week, you lifted 5 more lbs.",
            sources=["2026-01-12", "2026-01-19"],
            confidence=0.8,
            input_type="both",
            parsed_data={"entry_id": "2026-01-19_12-00-00"},
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "bench 185x5, how does this compare to last week?"])

            assert result.exit_code == 0
            # Both results shown
            assert "Logged entry:" in result.output
            assert "Compared to last week" in result.output


class TestUnifiedCommandHandlesCorrection:
    """AC4: Unified command handles CORRECTION input type."""

    def test_command_handles_correction(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Command handles CORRECTION input_type showing corrected message."""
        mock_result = _create_mock_process_result(
            input_type="correction",
            parsed_data={"entry_id": "2026-01-19_12-00-00"},
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "actually yesterday was 195x5 not 185x5"])

            assert result.exit_code == 0
            assert "Corrected entry:" in result.output


class TestUnifiedCommandDebugFlag:
    """AC5: Debug flag support."""

    def test_debug_shows_traces(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """--debug shows agent traces."""
        mock_trace = MagicMock()
        mock_trace.agent_name = "router"
        mock_trace.elapsed_ms = 150.5
        mock_trace.output_summary = "input_type=log"

        mock_result = _create_mock_process_result(
            input_type="log",
            parsed_data={"entry_id": "2026-01-19_12-00-00"},
            with_debug=True,
        )
        mock_result.debug.traces = [mock_trace]

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
            patch("swealog.cli.app.typer.prompt", return_value=""),  # Skip feedback prompt
            patch("swealog.cli.app.FeedbackRecorder"),  # Prevent writing to real directory
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "--debug", "bench 185x5"])

            assert result.exit_code == 0
            # Debug output shows agent traces - format is "[agent] Xms - summary"
            # Rich output strips some formatting, so just check for timing
            assert "150ms" in result.output or "151ms" in result.output
            assert "input_type=log" in result.output


class TestUnifiedCommandOptions:
    """Test unified command options work correctly."""

    def test_with_config_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Command respects --config option."""
        mock_result = _create_mock_process_result(
            input_type="log",
            parsed_data={"entry_id": "2026-01-19_12-00-00"},
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "--config", "/custom/config.yaml", "bench 185x5"])

            assert result.exit_code == 0
            call_args = mock_get_deps.call_args
            assert call_args is not None
            assert str(call_args[0][0]) == "/custom/config.yaml"

    def test_with_storage_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Command respects --storage option."""
        mock_result = _create_mock_process_result(
            input_type="log",
            parsed_data={"entry_id": "2026-01-19_12-00-00"},
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "--storage", "/custom/storage", "bench 185x5"])

            assert result.exit_code == 0
            call_args = mock_get_deps.call_args
            assert call_args is not None
            assert str(call_args[0][1]) == "/custom/storage"


class TestUnifiedCommandErrors:
    """Test error handling in unified command."""

    def test_error_shows_message(self, runner: CliRunner) -> None:
        """Error shows user-friendly message and exits with error code."""
        with patch("swealog.cli.app.get_dependencies", side_effect=Exception("Config error")):
            result = runner.invoke(app, ["run", "test"])

            assert result.exit_code == 1
            assert "Failed to process input" in result.output

    def test_empty_text_shows_error(self, runner: CliRunner) -> None:
        """Empty text input shows error message."""
        result = runner.invoke(app, ["run", "   "])  # Whitespace-only

        assert result.exit_code == 1
        assert "Input text cannot be empty" in result.output


class TestUnifiedCommandClarification:
    """Test clarification question handling."""

    def test_clarification_questions_displayed(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Clarification questions are displayed properly."""
        mock_result = _create_mock_process_result(
            clarification_questions=["What exercise did you do?", "What weight?"],
            input_type="query",
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "something ambiguous"])

            assert result.exit_code == 0
            assert "Clarification needed" in result.output
            assert "What exercise did you do?" in result.output
            assert "What weight?" in result.output


class TestUnifiedCommandSession:
    """Test session support for multi-turn conversations."""

    def test_session_id_creates_persistent_session(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """--session option uses persistent session database."""
        mock_result = _create_mock_process_result(
            input_type="log",
            parsed_data={"entry_id": "2026-01-19_12-00-00"},
        )

        mock_session = MagicMock()
        mock_session.session_id = "test-session-123"
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.get_session.return_value = None  # New session
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "--session", "my-session", "bench 185x5"])

            assert result.exit_code == 0
            # Verify persistent db path was used
            call_kwargs = mock_quilto_cls.call_args.kwargs
            assert call_kwargs["session_db_path"] == "quilto_sessions.db"


class TestPromptForFeedback:
    """Tests for _prompt_for_feedback() helper function."""

    def test_returns_none_when_debug_disabled(self) -> None:
        """_prompt_for_feedback returns None when debug=False."""
        from swealog.cli.app import _prompt_for_feedback  # pyright: ignore[reportPrivateUsage]

        result = _prompt_for_feedback(debug=False, non_interactive=False)
        assert result is None

    def test_returns_user_input_when_debug_enabled(self) -> None:
        """_prompt_for_feedback returns user input when debug=True."""
        from swealog.cli.app import _prompt_for_feedback  # pyright: ignore[reportPrivateUsage]

        with patch("swealog.cli.app.typer.prompt", return_value="Great response!"):
            result = _prompt_for_feedback(debug=True, non_interactive=False)
            assert result == "Great response!"

    def test_returns_empty_string_when_user_skips(self) -> None:
        """_prompt_for_feedback returns empty string when user presses Enter."""
        from swealog.cli.app import _prompt_for_feedback  # pyright: ignore[reportPrivateUsage]

        with patch("swealog.cli.app.typer.prompt", return_value=""):
            result = _prompt_for_feedback(debug=True, non_interactive=False)
            assert result == ""

    def test_prompt_message_is_correct(self) -> None:
        """_prompt_for_feedback uses correct prompt message."""
        from swealog.cli.app import _prompt_for_feedback  # pyright: ignore[reportPrivateUsage]

        with patch("swealog.cli.app.typer.prompt", return_value="feedback") as mock_prompt:
            _prompt_for_feedback(debug=True, non_interactive=False)
            mock_prompt.assert_called_once_with(
                "How was this response? (press Enter to skip)",
                default="",
                show_default=False,
            )


class TestUnifiedCommandFeedbackIntegration:
    """Integration tests for feedback recording in unified command."""

    def test_query_flow_prompts_feedback_when_debug(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """QUERY flow with --debug prompts for feedback and records it."""
        mock_result = _create_mock_process_result(
            response="Your progress is good.",
            sources=["2026-01-15"],
            confidence=0.85,
            with_debug=True,
            input_type="query",
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
            patch("swealog.cli.app.typer.prompt", return_value="Good answer!"),
            patch("swealog.cli.app.FeedbackRecorder") as mock_recorder_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto
            mock_recorder = MagicMock()
            mock_recorder_cls.return_value = mock_recorder

            result = runner.invoke(app, ["run", "--debug", "how's my progress?"])

            assert result.exit_code == 0
            # Verify feedback was recorded (uses record() with handler)
            mock_recorder.record.assert_called_once()

    def test_query_flow_no_feedback_prompt_without_debug(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """QUERY flow without --debug does not prompt for feedback."""
        mock_result = _create_mock_process_result(
            response="Your progress is good.",
            sources=["2026-01-15"],
            confidence=0.85,
            input_type="query",
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
            patch("swealog.cli.app.typer.prompt") as mock_prompt,
            patch("swealog.cli.app.FeedbackRecorder") as mock_recorder_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["run", "how's my progress?"])

            assert result.exit_code == 0
            # No prompt, no recording
            mock_prompt.assert_not_called()
            mock_recorder_cls.return_value.record.assert_not_called()

    def test_log_flow_prompts_feedback_when_debug(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """LOG flow with --debug still prompts for feedback."""
        mock_result = _create_mock_process_result(
            input_type="log",
            parsed_data={"entry_id": "2026-01-20_12-00-00"},
            with_debug=True,
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
            patch("swealog.cli.app.typer.prompt", return_value="Works well"),
            patch("swealog.cli.app.FeedbackRecorder") as mock_recorder_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto
            mock_recorder = MagicMock()
            mock_recorder_cls.return_value = mock_recorder

            result = runner.invoke(app, ["run", "--debug", "bench 200x5"])

            assert result.exit_code == 0
            # Uses record() with handler (not record_simplified)
            mock_recorder.record.assert_called_once()


class TestUnifiedCommandNonInteractive:
    """Test --non-interactive option."""

    def test_non_interactive_skips_prompt(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """--non-interactive skips feedback prompt even with --debug."""
        mock_result = _create_mock_process_result(
            response="Your progress is good.",
            input_type="query",
            with_debug=True,
        )

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.app.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.app.Quilto") as mock_quilto_cls,
            patch("swealog.cli.app.typer.prompt") as mock_prompt,
            patch("swealog.cli.app.FeedbackRecorder") as mock_recorder_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto
            mock_recorder = MagicMock()
            mock_recorder_cls.return_value = mock_recorder

            result = runner.invoke(app, ["run", "--debug", "--non-interactive", "how's my progress?"])

            assert result.exit_code == 0
            # No interactive prompt
            mock_prompt.assert_not_called()
            # But feedback still recorded with handler (uses record())
            mock_recorder.record.assert_called_once()


class TestUnifiedCommandVersion:
    """Test --version option."""

    def test_version_shows_version(self, runner: CliRunner) -> None:
        """--version shows version and exits."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "swealog version" in result.output


class TestUnifiedCommandHelp:
    """Test help display."""

    def test_help_flag_shows_help(self, runner: CliRunner) -> None:
        """--help flag shows help text."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "swealog" in result.output.lower()


class TestRunCommandHelp:
    """Test run command help."""

    def test_run_help_shows_usage(self, runner: CliRunner) -> None:
        """Run --help shows command usage."""
        result = runner.invoke(app, ["run", "--help"])

        assert result.exit_code == 0
        assert "Process any input through Quilto" in result.output
