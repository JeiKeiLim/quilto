"""Progress handler protocol for Quilto processing callbacks.

This module defines the ProgressHandler Protocol that applications can
implement to receive progress updates during Quilto processing.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProgressHandler(Protocol):
    """Protocol for progress callbacks during Quilto processing.

    Implement methods you care about. All methods are optional due to
    Protocol semantics - just implement what you need.

    Example:
        class MyUIHandler:
            async def on_agent_start(self, agent: str, input_summary: str) -> None:
                print(f"Starting {agent}...")

            async def on_agent_complete(self, agent: str, elapsed: float) -> None:
                print(f"{agent} done in {elapsed:.2f}s")
    """

    async def on_agent_start(self, agent: str, input_summary: str) -> None:
        """Called when an agent begins execution.

        Args:
            agent: Name of the agent starting (e.g., "router", "planner").
            input_summary: Brief summary of input being processed.
        """
        ...

    async def on_agent_complete(self, agent: str, elapsed: float) -> None:
        """Called when an agent completes execution.

        Args:
            agent: Name of the agent that completed.
            elapsed: Execution time in seconds.
        """
        ...

    async def on_retry(self, attempt: int, reason: str) -> None:
        """Called when a retry is attempted.

        Args:
            attempt: Current retry attempt number (1-based).
            reason: Why the retry is happening.
        """
        ...

    async def on_stage(self, stage: str) -> None:
        """Called when processing enters a new stage.

        Args:
            stage: Name of the stage (e.g., "routing", "planning", "retrieving").
        """
        ...
