"""Rich output helpers for CLI formatting."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()  # Singleton for all output


def print_success(message: str) -> None:
    """Print success message in green with checkmark prefix.

    Args:
        message: The message to display.
    """
    console.print(f"[green]\u2713 {message}[/green]")


def print_error(message: str) -> None:
    """Print error message in red with X prefix.

    Args:
        message: The error message to display.
    """
    console.print(f"[red]\u2717 {message}[/red]")


def print_warning(message: str) -> None:
    """Print warning message in yellow with exclamation prefix.

    Args:
        message: The warning message to display.
    """
    console.print(f"[yellow]! {message}[/yellow]")


def print_info(message: str) -> None:
    """Print info message in blue with info symbol prefix.

    Args:
        message: The info message to display.
    """
    console.print(f"[blue]\u2139[/blue] {message}")


def print_panel(content: str, title: str = "") -> None:
    """Print content in a rich panel.

    Args:
        content: The content to display inside the panel.
        title: Optional title for the panel.
    """
    console.print(Panel(content, title=title))


def print_table(headers: list[str], rows: list[list[str]], title: str = "") -> None:
    """Print data in a rich table.

    Args:
        headers: Column headers for the table.
        rows: List of rows, each row is a list of cell values.
        title: Optional title for the table.
    """
    table = Table(title=title)
    for header in headers:
        table.add_column(header)
    for row in rows:
        table.add_row(*row)
    console.print(table)
