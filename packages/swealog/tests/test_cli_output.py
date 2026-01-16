"""Tests for swealog.cli.output module."""

from io import StringIO
from unittest.mock import patch

from rich.console import Console
from swealog.cli import console as cli_console
from swealog.cli.output import (
    print_error,
    print_info,
    print_panel,
    print_success,
    print_table,
    print_warning,
)


def test_console_exists() -> None:
    """Test that the console singleton is available."""
    assert cli_console is not None
    assert isinstance(cli_console, Console)


class TestOutputHelpers:
    """Tests for output helper functions."""

    def test_print_success(self) -> None:
        """Test print_success outputs green text with checkmark."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        with patch("swealog.cli.output.console", test_console):
            print_success("Operation completed")
        result = output.getvalue()
        assert "Operation completed" in result
        # Check for ANSI green color code or checkmark
        assert "\u2713" in result or "32m" in result  # Green ANSI or checkmark

    def test_print_error(self) -> None:
        """Test print_error outputs red text with X."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        with patch("swealog.cli.output.console", test_console):
            print_error("Something failed")
        result = output.getvalue()
        assert "Something failed" in result
        # Check for ANSI red color code or X mark
        assert "\u2717" in result or "31m" in result  # Red ANSI or X mark

    def test_print_warning(self) -> None:
        """Test print_warning outputs yellow text with exclamation."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        with patch("swealog.cli.output.console", test_console):
            print_warning("Be careful")
        result = output.getvalue()
        assert "Be careful" in result
        # Check for ANSI yellow color code or exclamation
        assert "!" in result or "33m" in result  # Yellow ANSI or !

    def test_print_info(self) -> None:
        """Test print_info outputs blue text with info symbol."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        with patch("swealog.cli.output.console", test_console):
            print_info("FYI")
        result = output.getvalue()
        assert "FYI" in result
        # Check for ANSI blue color code or info symbol
        assert "\u2139" in result or "34m" in result  # Blue ANSI or info symbol

    def test_print_panel(self) -> None:
        """Test print_panel outputs content in a panel with title."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        with patch("swealog.cli.output.console", test_console):
            print_panel("Panel content", title="My Panel")
        result = output.getvalue()
        assert "Panel content" in result
        assert "My Panel" in result

    def test_print_panel_no_title(self) -> None:
        """Test print_panel works without title."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        with patch("swealog.cli.output.console", test_console):
            print_panel("Just content")
        result = output.getvalue()
        assert "Just content" in result

    def test_print_table(self) -> None:
        """Test print_table outputs formatted table with headers and rows."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        with patch("swealog.cli.output.console", test_console):
            print_table(
                headers=["Name", "Value"],
                rows=[["foo", "1"], ["bar", "2"]],
                title="Test Table",
            )
        result = output.getvalue()
        assert "Name" in result
        assert "Value" in result
        assert "foo" in result
        assert "bar" in result
        assert "Test Table" in result

    def test_print_table_no_title(self) -> None:
        """Test print_table works without title."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        with patch("swealog.cli.output.console", test_console):
            print_table(
                headers=["Col1", "Col2"],
                rows=[["a", "b"]],
            )
        result = output.getvalue()
        assert "Col1" in result
        assert "a" in result

    def test_print_table_empty_rows(self) -> None:
        """Test print_table works with no rows."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)
        with patch("swealog.cli.output.console", test_console):
            print_table(
                headers=["Header1", "Header2"],
                rows=[],
            )
        result = output.getvalue()
        assert "Header1" in result
        assert "Header2" in result
