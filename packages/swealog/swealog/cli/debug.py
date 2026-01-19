"""Debug logging utilities for CLI commands."""

import time
from collections.abc import Generator
from contextlib import contextmanager

from rich.console import Console

console = Console()


class DebugLogger:
    """Logger for debug output in CLI commands.

    Provides formatted debug output showing agent execution with timing.
    Output is only displayed when enabled.

    Format per AC5:
        [AgentName] input: <summary>
        [AgentName] output: <summary>
        [AgentName] time: <elapsed>s

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
        output and timing in correct order (input → output → time per AC5).

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

        console.print(f"[cyan][{name}][/cyan] input: {input_summary}")
        start = time.perf_counter()
        yield result
        result["elapsed"] = time.perf_counter() - start

    def log_output(self, name: str, output_summary: str, elapsed: float | None = None) -> None:
        """Log agent output and optionally timing.

        Call after context manager exits to print output then timing (per AC5 format).

        Args:
            name: Agent name.
            output_summary: Brief description of output.
            elapsed: Optional elapsed time in seconds. If provided, prints timing line.
        """
        if self.enabled:
            console.print(f"[cyan][{name}][/cyan] output: {output_summary}")
            if elapsed is not None:
                console.print(f"[cyan][{name}][/cyan] [dim]time: {elapsed:.2f}s[/dim]")
