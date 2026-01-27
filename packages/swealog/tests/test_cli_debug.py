"""Tests for swealog.cli.debug module and debug flag functionality."""

import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swealog.cli import DebugLogger, app
from swealog.cli.debug import console
from typer.testing import CliRunner


def _capture_to_list(output_list: list[str]) -> Callable[[Any], None]:
    """Create a capture function for mocking console.print.

    Args:
        output_list: List to append captured output to.

    Returns:
        Callable that captures output to the list.
    """

    def capture(x: Any) -> None:
        output_list.append(str(x))

    return capture


class TestDebugLogger:
    """Tests for the DebugLogger class."""

    def test_disabled_by_default(self) -> None:
        """DebugLogger is disabled by default."""
        logger = DebugLogger()
        assert not logger.enabled

    def test_enabled_when_specified(self) -> None:
        """DebugLogger can be enabled via constructor."""
        logger = DebugLogger(enabled=True)
        assert logger.enabled

    def test_agent_context_manager_disabled(self) -> None:
        """Disabled logger executes code without printing."""
        logger = DebugLogger(enabled=False)
        executed = False

        with logger.agent("Router", "test input") as timing:
            executed = True

        assert executed
        assert timing["elapsed"] == 0.0  # No timing when disabled

    def test_agent_context_manager_enabled(self) -> None:
        """Enabled logger prints separator and input (output/time via log_output)."""
        logger = DebugLogger(enabled=True)

        output_lines: list[str] = []
        with (
            patch.object(console, "print", side_effect=_capture_to_list(output_lines)),
            logger.agent("Router", "test input") as timing,
        ):
            pass

        # Context manager prints separator line then input line
        assert len(output_lines) == 2
        assert "====" in output_lines[0]  # Separator
        assert "[Router]" in output_lines[1]
        assert "input: test input" in output_lines[1]
        # Elapsed time should be populated
        assert timing["elapsed"] >= 0.0

    def test_log_output_disabled(self) -> None:
        """Disabled logger doesn't print output."""
        logger = DebugLogger(enabled=False)

        output_lines: list[str] = []
        with patch.object(console, "print", side_effect=_capture_to_list(output_lines)):
            logger.log_output("Router", "test output")

        assert len(output_lines) == 0

    def test_log_output_enabled(self) -> None:
        """Enabled logger prints output header and data."""
        logger = DebugLogger(enabled=True)

        output_lines: list[str] = []
        with patch.object(console, "print", side_effect=_capture_to_list(output_lines)):
            logger.log_output("Router", "test output")

        # Output is now: "[Router] output:" then "  test output" (for string data)
        assert len(output_lines) == 2
        assert "[Router]" in output_lines[0]
        assert "output:" in output_lines[0]
        assert "test output" in output_lines[1]

    def test_log_output_with_elapsed(self) -> None:
        """Enabled logger prints output header, data, and timing when elapsed provided."""
        logger = DebugLogger(enabled=True)

        output_lines: list[str] = []
        with patch.object(console, "print", side_effect=_capture_to_list(output_lines)):
            logger.log_output("Router", "test output", elapsed=0.85)

        # Output is now: "[Router] output:" then "  test output" then "[Router] time: ..."
        assert len(output_lines) == 3
        assert "[Router]" in output_lines[0]
        assert "output:" in output_lines[0]
        assert "test output" in output_lines[1]
        assert "[Router]" in output_lines[2]
        assert "time: 0.85s" in output_lines[2]


class TestDotEnvLoading:
    """Tests for .env file auto-loading."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner with environment isolation."""
        return CliRunner(env={"HOME": "/tmp"})

    def test_dotenv_loads_when_present(self, runner: CliRunner) -> None:
        """CLI loads .env file when present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, ".env")
            with open(env_file, "w") as f:
                f.write("TEST_VAR_FOR_SWEALOG=loaded_value\n")

            # Run CLI from the directory with .env
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["--version"])
                # Just verify CLI runs without error - env loading happens in callback
                assert result.exit_code == 0
            finally:
                os.chdir(original_cwd)

    def test_no_dotenv_no_error(self, runner: CliRunner) -> None:
        """CLI runs without error when no .env file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No .env file in this directory
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = runner.invoke(app, ["--version"])
                assert result.exit_code == 0
            finally:
                os.chdir(original_cwd)


@dataclass
class MockDomain:
    """Mock domain for testing."""

    name: str
    log_schema: dict[str, Any]
    vocabulary: dict[str, str]


class TestDebugFlagLog:
    """Tests for --debug flag on log command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_dependencies(self) -> tuple[MagicMock, MagicMock, list[MockDomain]]:
        """Create mock dependencies tuple."""
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_domains = [MockDomain(name="GeneralFitness", log_schema={}, vocabulary={})]
        return (mock_client, mock_storage, mock_domains)

    def test_debug_flag_shows_output(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """--debug flag shows agent debug output."""
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
                    confidence=0.92,
                )
            )
            mock_log_flow.return_value = "2026-01-16_12-00-00"

            result = runner.invoke(app, ["log", "--debug", "bench 185x5"])

            assert result.exit_code == 0
            # Debug output should show Router agent name
            assert "[Router]" in result.output
            # Should still show success message
            assert "Logged entry:" in result.output

    def test_short_debug_flag(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """-d flag works as short form of --debug."""
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

            result = runner.invoke(app, ["log", "-d", "test"])

            assert result.exit_code == 0
            assert "[Router]" in result.output

    def test_no_debug_flag_no_debug_output(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Without --debug flag, no debug output is shown."""
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

            result = runner.invoke(app, ["log", "test"])

            assert result.exit_code == 0
            # Debug markers should not appear (both conditions must be false)
            assert "[Router]" not in result.output
            assert "input:" not in result.output


def _create_mock_process_result(
    response: str = "Test response",
    sources: list[str] | None = None,
    confidence: float = 0.85,
    debug_retry_count: int = 0,
) -> MagicMock:
    """Create a mock ProcessResult for testing."""
    mock_result = MagicMock()
    mock_result.response = response
    mock_result.source_entry_ids = sources or []
    mock_result.confidence = confidence
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


class TestDebugFlagAsk:
    """Tests for --debug flag on ask command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_dependencies(self) -> tuple[MagicMock, MagicMock, list[MockDomain]]:
        """Create mock dependencies tuple."""
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_domains = [MockDomain(name="GeneralFitness", log_schema={}, vocabulary={})]
        return (mock_client, mock_storage, mock_domains)

    def test_debug_flag_calls_quilto_with_debug(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """--debug flag passes debug=True to Quilto."""
        mock_result = _create_mock_process_result()

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["ask", "--debug", "how is my bench progress?"])

            assert result.exit_code == 0
            # Quilto should be called with debug=True
            call_kwargs = mock_quilto_cls.call_args.kwargs
            assert call_kwargs.get("debug") is True

    def test_no_debug_no_debug_flag(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Without --debug, Quilto is called with debug=False."""
        mock_result = _create_mock_process_result()

        mock_session = MagicMock()
        mock_session.process = AsyncMock(return_value=mock_result)

        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.Quilto") as mock_quilto_cls,
        ):
            mock_quilto = MagicMock()
            mock_quilto.create_session.return_value = mock_session
            mock_quilto_cls.return_value = mock_quilto

            result = runner.invoke(app, ["ask", "how is my bench progress?"])

            assert result.exit_code == 0
            call_kwargs = mock_quilto_cls.call_args.kwargs
            assert call_kwargs.get("debug") is False


class TestDebugOutputFormat:
    """Tests for AC5: Debug output format."""

    def test_debug_format_matches_spec(self) -> None:
        """Debug output matches expected format showing full JSON.

        Format now shows:
            ============...
            [Router] input: "bench 185x5"
            [Router] output:
            <JSON data>
            [Router] time: 0.8s
        """
        logger = DebugLogger(enabled=True)

        output_lines: list[str] = []
        with patch.object(console, "print", side_effect=_capture_to_list(output_lines)):
            with logger.agent("Router", '"bench 185x5"') as timing:
                pass
            # Simulate realistic elapsed time
            timing["elapsed"] = 0.8
            # Pass dict data like real usage
            logger.log_output(
                "Router",
                {"input_type": "LOG", "domains": ["strength"], "confidence": 0.92},
                timing["elapsed"],
            )

        # Check format: separator → input → output header → JSON (Syntax object) → time
        assert len(output_lines) == 5
        # Line 1: Separator
        assert "====" in output_lines[0]
        # Line 2: Input
        assert "[Router]" in output_lines[1]
        assert 'input: "bench 185x5"' in output_lines[1]
        # Line 3: Output header
        assert "[Router]" in output_lines[2]
        assert "output:" in output_lines[2]
        # Line 4: JSON data (Rich Syntax object for syntax highlighting)
        assert "Syntax" in output_lines[3]  # Rich Syntax object
        # Line 5: Time
        assert "[Router]" in output_lines[4]
        assert "time:" in output_lines[4]
        assert "0.80s" in output_lines[4]
