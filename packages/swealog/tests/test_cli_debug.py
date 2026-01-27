"""Tests for swealog.cli.debug module and debug flag functionality."""

import os
import tempfile
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

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
