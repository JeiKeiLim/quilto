"""Tests for quilto.cli.output module."""

from io import StringIO

from quilto.cli import output
from rich.console import Console


def test_console_exists() -> None:
    """Test that console singleton is available."""
    assert output.console is not None
    assert isinstance(output.console, Console)


class TestOutputHelpers:
    """Test suite for output helper functions."""

    def test_print_success(self) -> None:
        """Test print_success outputs green checkmark."""
        captured = StringIO()
        test_console = Console(file=captured, force_terminal=True)

        # Temporarily replace console
        original_console = output.console
        output.console = test_console

        try:
            output.print_success("Test success")
            out = captured.getvalue()
            assert "✓" in out
            assert "Test success" in out
        finally:
            output.console = original_console

    def test_print_error(self) -> None:
        """Test print_error outputs red X."""
        captured = StringIO()
        test_console = Console(file=captured, force_terminal=True)

        original_console = output.console
        output.console = test_console

        try:
            output.print_error("Test error")
            out = captured.getvalue()
            assert "✗" in out
            assert "Test error" in out
        finally:
            output.console = original_console

    def test_print_warning(self) -> None:
        """Test print_warning outputs yellow exclamation."""
        captured = StringIO()
        test_console = Console(file=captured, force_terminal=True)

        original_console = output.console
        output.console = test_console

        try:
            output.print_warning("Test warning")
            out = captured.getvalue()
            assert "!" in out
            assert "Test warning" in out
        finally:
            output.console = original_console

    def test_print_info(self) -> None:
        """Test print_info outputs blue info symbol."""
        captured = StringIO()
        test_console = Console(file=captured, force_terminal=True)

        original_console = output.console
        output.console = test_console

        try:
            output.print_info("Test info")
            out = captured.getvalue()
            assert "ℹ" in out
            assert "Test info" in out
        finally:
            output.console = original_console

    def test_print_panel(self) -> None:
        """Test print_panel outputs panel content."""
        captured = StringIO()
        test_console = Console(file=captured, force_terminal=True)

        original_console = output.console
        output.console = test_console

        try:
            output.print_panel("Panel content", title="Test Title")
            out = captured.getvalue()
            assert "Panel content" in out
            assert "Test Title" in out
        finally:
            output.console = original_console

    def test_print_panel_no_title(self) -> None:
        """Test print_panel works without title."""
        captured = StringIO()
        test_console = Console(file=captured, force_terminal=True)

        original_console = output.console
        output.console = test_console

        try:
            output.print_panel("Just content")
            out = captured.getvalue()
            assert "Just content" in out
        finally:
            output.console = original_console

    def test_print_table(self) -> None:
        """Test print_table outputs table with headers and rows."""
        captured = StringIO()
        test_console = Console(file=captured, force_terminal=True)

        original_console = output.console
        output.console = test_console

        try:
            headers = ["Name", "Value"]
            rows = [["foo", "bar"], ["baz", "qux"]]
            output.print_table(headers, rows, title="Test Table")
            out = captured.getvalue()
            assert "Name" in out
            assert "Value" in out
            assert "foo" in out
            assert "bar" in out
            assert "Test Table" in out
        finally:
            output.console = original_console

    def test_print_table_no_title(self) -> None:
        """Test print_table works without title."""
        captured = StringIO()
        test_console = Console(file=captured, force_terminal=True)

        original_console = output.console
        output.console = test_console

        try:
            headers = ["Col1"]
            rows = [["val1"]]
            output.print_table(headers, rows)
            out = captured.getvalue()
            assert "Col1" in out
            assert "val1" in out
        finally:
            output.console = original_console

    def test_print_table_empty_rows(self) -> None:
        """Test print_table handles empty rows."""
        captured = StringIO()
        test_console = Console(file=captured, force_terminal=True)

        original_console = output.console
        output.console = test_console

        try:
            headers = ["Header1", "Header2"]
            rows: list[list[str]] = []
            output.print_table(headers, rows)
            out = captured.getvalue()
            assert "Header1" in out
            assert "Header2" in out
        finally:
            output.console = original_console
