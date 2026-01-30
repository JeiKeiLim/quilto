"""NoOpProvider - null implementation for disabled observability.

This module provides a no-op implementation of ObservabilityProvider
that safely does nothing. Use this when observability is disabled.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from quilto.observability.provider import SpanContext


class NoOpProvider:
    """No-operation observability provider.

    All methods are safe no-ops that do nothing. Use this provider
    when observability is disabled or not configured.

    This class satisfies the ObservabilityProvider protocol.

    Example:
        provider = NoOpProvider()
        with provider.span("operation"):
            # This works but traces nothing
            pass
    """

    def get_langgraph_callback(self) -> None:
        """Return None since observability is disabled.

        Returns:
            None - no callback handler when observability is off.
        """
        return None

    @contextmanager
    def span(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        input: Any | None = None,
    ) -> Generator[SpanContext]:
        """No-op span that yields a dummy SpanContext.

        The span context manager works correctly but records nothing.

        Args:
            name: Ignored - name of the operation.
            metadata: Ignored - optional metadata.
            input: Ignored - optional input data.

        Yields:
            SpanContext with empty span_id and trace_id.
        """
        yield SpanContext(span_id="", trace_id="")

    def log_event(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        """No-op event logging.

        Args:
            name: Ignored - name of the event.
            metadata: Ignored - optional metadata.
        """
        pass

    def log_error(self, error: Exception, metadata: dict[str, Any] | None = None) -> None:
        """No-op error logging.

        Args:
            error: Ignored - the exception.
            metadata: Ignored - optional metadata.
        """
        pass

    def is_enabled(self) -> bool:
        """Check if observability is active.

        Returns:
            False - observability is always disabled for NoOpProvider.
        """
        return False

    def flush(self) -> None:
        """No-op flush - nothing to send."""
        pass
