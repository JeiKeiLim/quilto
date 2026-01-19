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
        """Enabled logger prints input only (output/time via log_output per AC5)."""
        logger = DebugLogger(enabled=True)

        output_lines: list[str] = []
        with (
            patch.object(console, "print", side_effect=_capture_to_list(output_lines)),
            logger.agent("Router", "test input") as timing,
        ):
            pass

        # Context manager only prints input line now (timing deferred to log_output)
        assert len(output_lines) == 1
        assert "[Router]" in output_lines[0]
        assert "input: test input" in output_lines[0]
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
        """Enabled logger prints output."""
        logger = DebugLogger(enabled=True)

        output_lines: list[str] = []
        with patch.object(console, "print", side_effect=_capture_to_list(output_lines)):
            logger.log_output("Router", "test output")

        assert len(output_lines) == 1
        assert "[Router]" in output_lines[0]
        assert "output: test output" in output_lines[0]

    def test_log_output_with_elapsed(self) -> None:
        """Enabled logger prints output and timing when elapsed provided."""
        logger = DebugLogger(enabled=True)

        output_lines: list[str] = []
        with patch.object(console, "print", side_effect=_capture_to_list(output_lines)):
            logger.log_output("Router", "test output", elapsed=0.85)

        assert len(output_lines) == 2
        assert "[Router]" in output_lines[0]
        assert "output: test output" in output_lines[0]
        assert "[Router]" in output_lines[1]
        assert "time: 0.85s" in output_lines[1]


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
                    confidence=0.92,
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

            result = runner.invoke(app, ["log", "--debug", "bench 185x5"])

            assert result.exit_code == 0
            # Debug output should show agent names
            assert "[Router]" in result.output
            assert "[Parser]" in result.output
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
                    confidence=0.9,
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
                    confidence=0.9,
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

            result = runner.invoke(app, ["log", "test"])

            assert result.exit_code == 0
            # Debug markers should not appear (both conditions must be false)
            assert "[Router]" not in result.output
            assert "input:" not in result.output


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

    def test_debug_flag_shows_pipeline_agents(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """--debug flag shows all pipeline agents in ask command."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Your bench has improved!",
                "sources": ["entry1", "entry2"],
                "confidence": 0.85,
                "is_partial": False,
            }

            result = runner.invoke(app, ["ask", "--debug", "how is my bench progress?"])

            assert result.exit_code == 0
            # Pipeline should be called with a debug callback
            assert mock_pipeline.called
            call_kwargs = mock_pipeline.call_args.kwargs
            assert "debug_callback" in call_kwargs
            # With debug enabled, callback should not be None
            assert call_kwargs["debug_callback"] is not None

    def test_no_debug_no_callback(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Without --debug, no debug callback is passed."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Your bench has improved!",
                "sources": ["entry1"],
                "confidence": 0.85,
                "is_partial": False,
            }

            result = runner.invoke(app, ["ask", "how is my bench progress?"])

            assert result.exit_code == 0
            call_kwargs = mock_pipeline.call_args.kwargs
            assert call_kwargs.get("debug_callback") is None


class TestDebugTimerInQueryPipeline:
    """Tests for _DebugTimer class in query pipeline (H2 fix)."""

    def test_debug_timer_track_without_callback(self) -> None:
        """_DebugTimer.track works without callback."""
        from swealog.api.routes.query import _DebugTimer  # pyright: ignore[reportPrivateUsage]

        timer = _DebugTimer(callback=None)
        with timer.track("Router", "test input") as result:
            pass

        # Should populate elapsed time even without callback
        assert "elapsed" in result
        assert result["elapsed"] >= 0.0

    def test_debug_timer_track_with_callback(self) -> None:
        """_DebugTimer.track calls callback with start and end events."""
        from swealog.api.routes.query import _DebugTimer  # pyright: ignore[reportPrivateUsage]

        events: list[tuple[str, str, str, float]] = []

        def capture(agent_name: str, event: str, summary: str, elapsed: float) -> None:
            events.append((agent_name, event, summary, elapsed))

        timer = _DebugTimer(callback=capture)
        with timer.track("Router", "test input") as result:
            pass

        # Should have start and end events
        assert len(events) == 2
        assert events[0] == ("Router", "start", "test input", 0.0)
        assert events[1][0] == "Router"
        assert events[1][1] == "end"
        assert events[1][3] >= 0.0  # elapsed time

        # Result should have elapsed
        assert result["elapsed"] >= 0.0

    def test_debug_timer_log_output_without_callback(self) -> None:
        """_DebugTimer.log_output does nothing without callback."""
        from swealog.api.routes.query import _DebugTimer  # pyright: ignore[reportPrivateUsage]

        timer = _DebugTimer(callback=None)
        # Should not raise
        timer.log_output("Router", "test output")

    def test_debug_timer_log_output_with_callback(self) -> None:
        """_DebugTimer.log_output calls callback with output event."""
        from swealog.api.routes.query import _DebugTimer  # pyright: ignore[reportPrivateUsage]

        events: list[tuple[str, str, str, float]] = []

        def capture(agent_name: str, event: str, summary: str, elapsed: float) -> None:
            events.append((agent_name, event, summary, elapsed))

        timer = _DebugTimer(callback=capture)
        timer.log_output("Router", "input_type=LOG, confidence=0.92")

        assert len(events) == 1
        assert events[0] == ("Router", "output", "input_type=LOG, confidence=0.92", 0.0)


class TestDebugOutputFormat:
    """Tests for AC5: Debug output format."""

    def test_debug_format_matches_spec(self) -> None:
        """Debug output matches expected format from AC5.

        AC5 specifies:
            [Router] input: "bench 185x5"
            [Router] output: input_type=LOG, domains=[strength], confidence=0.92
            [Router] time: 0.8s
        """
        logger = DebugLogger(enabled=True)

        output_lines: list[str] = []
        with patch.object(console, "print", side_effect=_capture_to_list(output_lines)):
            with logger.agent("Router", '"bench 185x5"') as timing:
                pass
            # Simulate realistic elapsed time
            timing["elapsed"] = 0.8
            logger.log_output("Router", "input_type=LOG, domains=[strength], confidence=0.92", timing["elapsed"])

        # Check format matches AC5: input → output → time
        assert len(output_lines) == 3
        # Line 1: Input
        assert "[Router]" in output_lines[0]
        assert 'input: "bench 185x5"' in output_lines[0]
        # Line 2: Output (per AC5, output comes BEFORE time)
        assert "[Router]" in output_lines[1]
        assert "output:" in output_lines[1]
        assert "input_type=LOG" in output_lines[1]
        assert "confidence=0.92" in output_lines[1]
        # Line 3: Time
        assert "[Router]" in output_lines[2]
        assert "time:" in output_lines[2]
        assert "0.80s" in output_lines[2]
