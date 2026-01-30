"""ObservabilityProvider protocol for pluggable observability backends.

This module defines the protocol that all observability providers must implement,
enabling swappable backends (Langfuse, OpenTelemetry, etc.) without changing
application code.
"""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass
class SpanContext:
    """Context for an active span.

    Attributes:
        span_id: Unique identifier for this span.
        trace_id: Identifier for the overall trace this span belongs to.
    """

    span_id: str
    trace_id: str


@runtime_checkable
class ObservabilityProvider(Protocol):
    """Protocol for observability backends.

    Implement this protocol to create custom observability providers
    (e.g., Langfuse, OpenTelemetry, DataDog).

    All methods should be safe to call even when observability is disabled.
    Use is_enabled() to check if observability is active before expensive operations.

    Example:
        class MyProvider:
            def get_langgraph_callback(self) -> Any | None:
                return MyLangGraphCallback()

            def span(self, name: str, ...) -> AbstractContextManager[SpanContext]:
                return my_span_context(name, ...)

            def is_enabled(self) -> bool:
                return True
    """

    def get_langgraph_callback(self) -> Any | None:
        """Return callback handler for LangGraph execution.

        Returns:
            A callback handler compatible with LangGraph's callback system,
            or None if observability is disabled.
        """
        ...

    def span(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        input: Any | None = None,
    ) -> AbstractContextManager[SpanContext]:
        """Create a span for tracing an operation.

        Usage:
            with provider.span("operation_name", metadata={"key": "value"}):
                # code to trace
                pass

        Args:
            name: Name of the operation being traced.
            metadata: Optional key-value pairs for additional context.
            input: Optional input data to record with the span.

        Returns:
            A context manager yielding SpanContext for the active span.
        """
        ...

    def log_event(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        """Log an event within the current trace context.

        Args:
            name: Name of the event.
            metadata: Optional key-value pairs for event details.
        """
        ...

    def log_error(self, error: Exception, metadata: dict[str, Any] | None = None) -> None:
        """Log an error with correlation to current span.

        Args:
            error: The exception to log.
            metadata: Optional key-value pairs for additional context.
        """
        ...

    def is_enabled(self) -> bool:
        """Check if observability is active.

        Returns:
            True if observability is enabled and traces will be recorded.
        """
        ...

    def flush(self) -> None:
        """Ensure all traces are sent.

        Call before application shutdown to ensure all pending traces
        are transmitted to the observability backend.
        """
        ...
