"""Debug logging utilities for CLI commands."""

import json
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.syntax import Syntax

console = Console()


def _format_output(data: Any) -> str:
    """Format output data as JSON string.

    Args:
        data: Data to format (dict, list, or primitive).

    Returns:
        JSON-formatted string.
    """
    if data is None:
        return ""
    if isinstance(data, dict | list):
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)
    return str(data)


def create_debug_callback(enabled: bool) -> Callable[[str, str, Any, float], None] | None:
    """Create a debug callback for query pipeline agents.

    Creates a callback function that prints full debug output for pipeline agents.
    Shows input summary, full JSON output, and timing.

    Args:
        enabled: Whether debug output is enabled.

    Returns:
        Callback function or None if disabled.
    """
    if not enabled:
        return None

    def callback(agent_name: str, event: str, data: Any, elapsed: float) -> None:
        if event == "start":
            console.print(f"\n[cyan]{'=' * 60}[/cyan]")
            console.print(f"[cyan][{agent_name}][/cyan] input: {data}")
        elif event == "output":
            console.print(f"[cyan][{agent_name}][/cyan] output:")
            if isinstance(data, dict | list):
                json_str = _format_output(data)
                syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
                console.print(syntax)
            else:
                console.print(f"  {data}")
        elif event == "end":
            console.print(f"[cyan][{agent_name}][/cyan] [dim]time: {elapsed:.2f}s[/dim]")

    return callback


class DebugLogger:
    """Logger for debug output in CLI commands.

    Provides full debug output showing agent execution with timing.
    Output is only displayed when enabled. Shows complete JSON output
    for agent responses.

    Attributes:
        enabled: Whether debug output is enabled.
    """

    def __init__(self, enabled: bool = False) -> None:
        """Initialize the debug logger.

        Args:
            enabled: Whether debug output should be displayed.
        """
        self.enabled = enabled

    @contextmanager
    def agent(self, name: str, input_summary: str) -> Generator[dict[str, float]]:
        """Context manager for logging agent execution.

        Logs the agent name and input at start. Yields a dict that will contain
        'elapsed' time after the context exits. Use with log_output() to print
        full output and timing.

        Args:
            name: Agent name (e.g., "Router", "Parser").
            input_summary: Brief description of input.

        Yields:
            Dict with 'elapsed' key (0.0 initially, populated after context exits).
        """
        result: dict[str, float] = {"elapsed": 0.0}
        if not self.enabled:
            yield result
            return

        console.print(f"\n[cyan]{'=' * 60}[/cyan]")
        console.print(f"[cyan][{name}][/cyan] input: {input_summary}")
        start = time.perf_counter()
        yield result
        result["elapsed"] = time.perf_counter() - start

    def log_output(self, name: str, output_data: Any, elapsed: float | None = None) -> None:
        """Log agent output and optionally timing.

        Call after context manager exits to print full output then timing.

        Args:
            name: Agent name.
            output_data: Full output data (dict from model_dump() or any serializable).
            elapsed: Optional elapsed time in seconds. If provided, prints timing line.
        """
        if self.enabled:
            console.print(f"[cyan][{name}][/cyan] output:")
            if isinstance(output_data, dict | list):
                json_str = _format_output(output_data)
                syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
                console.print(syntax)
            else:
                console.print(f"  {output_data}")
            if elapsed is not None:
                console.print(f"[cyan][{name}][/cyan] [dim]time: {elapsed:.2f}s[/dim]")
