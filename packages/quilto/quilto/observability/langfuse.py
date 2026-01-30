"""LangfuseProvider - Langfuse observability backend implementation.

This module provides Langfuse integration for tracing LLM calls,
agent execution, and tool operations.
"""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from quilto.observability.provider import SpanContext

logger = logging.getLogger(__name__)


class LangfuseProvider:
    """Langfuse observability provider.

    Integrates with Langfuse for tracing LLM calls and agent execution.
    Falls back gracefully when credentials are missing.

    This class satisfies the ObservabilityProvider protocol.

    Example:
        provider = LangfuseProvider()
        if provider.is_enabled():
            with provider.span("operation", metadata={"key": "value"}):
                # Traced operation
                pass
    """

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        host: str | None = None,
    ) -> None:
        """Initialize LangfuseProvider.

        Args:
            public_key: Langfuse public key. Falls back to LANGFUSE_PUBLIC_KEY env var.
            secret_key: Langfuse secret key. Falls back to LANGFUSE_SECRET_KEY env var.
            host: Langfuse host URL. Falls back to LANGFUSE_BASE_URL env var.
        """
        # Resolve credentials from params or environment
        self._public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self._secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self._host = host or os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

        # Initialize Langfuse client if credentials available
        self._enabled = False
        self._langfuse: Any = None
        self._last_callback: Any = None  # Store last callback handler for trace_id retrieval

        if self._public_key and self._secret_key:
            try:
                from langfuse import Langfuse

                self._langfuse = Langfuse(
                    public_key=self._public_key,
                    secret_key=self._secret_key,
                    host=self._host,
                )
                self._enabled = True
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse client: {e}")
        else:
            logger.warning(
                "Langfuse credentials not found. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables."
            )

    def is_enabled(self) -> bool:
        """Check if observability is active.

        Returns:
            True if Langfuse is enabled and traces will be recorded.
        """
        return self._enabled

    def get_langgraph_callback(self) -> Any | None:
        """Return callback handler for LangGraph execution.

        The CallbackHandler uses the Langfuse client credentials from
        environment variables or the global client configured by this provider.

        Returns:
            A LangchainCallbackHandler instance compatible with LangGraph,
            or None if observability is disabled.
        """
        if not self._enabled:
            return None

        try:
            from langfuse.langchain import CallbackHandler

            # Create and store callback handler for later trace_id retrieval
            self._last_callback = CallbackHandler(public_key=self._public_key)
            return self._last_callback
        except Exception as e:
            logger.warning(f"Failed to create LangGraph callback handler: {e}")
            return None

    @contextmanager
    def span(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        input: Any | None = None,
    ) -> Generator[SpanContext]:
        """Create a span for tracing an operation.

        Uses Langfuse's start_as_current_observation pattern to create
        nested spans in the trace.

        Args:
            name: Name of the operation being traced.
            metadata: Optional key-value pairs for additional context.
            input: Optional input data to record with the span.

        Yields:
            SpanContext with span_id and trace_id from the active observation.
        """
        if not self._enabled or self._langfuse is None:
            yield SpanContext(span_id="", trace_id="")
            return

        try:
            with self._langfuse.start_as_current_observation(
                as_type="span",
                name=name,
                metadata=metadata,
                input=input,
            ):
                span_id = self._langfuse.get_current_observation_id() or ""
                trace_id = self._langfuse.get_current_trace_id() or ""
                yield SpanContext(span_id=span_id, trace_id=trace_id)
        except Exception as e:
            logger.warning(f"Failed to create Langfuse span '{name}': {e}")
            yield SpanContext(span_id="", trace_id="")

    def log_event(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        """Log an event within the current trace context.

        Creates an event in the current Langfuse trace.

        Args:
            name: Name of the event.
            metadata: Optional key-value pairs for event details.
        """
        if not self._enabled or self._langfuse is None:
            return

        try:
            self._langfuse.create_event(
                name=name,
                metadata=metadata,
            )
        except Exception as e:
            logger.warning(f"Failed to log Langfuse event '{name}': {e}")

    def log_error(self, error: Exception, metadata: dict[str, Any] | None = None) -> None:
        """Log an error with correlation to current span.

        Creates an error event in Langfuse with the exception details.

        Args:
            error: The exception to log.
            metadata: Optional key-value pairs for additional context.
        """
        if not self._enabled or self._langfuse is None:
            return

        try:
            error_metadata = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                **(metadata or {}),
            }
            self._langfuse.create_event(
                name="error",
                metadata=error_metadata,
                level="ERROR",
            )
        except Exception as e:
            logger.warning(f"Failed to log Langfuse error: {e}")

    def flush(self) -> None:
        """Ensure all traces are sent.

        Call before application shutdown to ensure all pending traces
        are transmitted to Langfuse.
        """
        if not self._enabled or self._langfuse is None:
            return

        try:
            self._langfuse.flush()
        except Exception as e:
            logger.warning(f"Failed to flush Langfuse: {e}")

    def get_current_trace_id(self) -> str | None:
        """Return the current trace ID if in an active trace context.

        Returns:
            The trace ID string if in an active trace, None otherwise.
        """
        if not self._enabled or self._langfuse is None:
            return None

        try:
            return self._langfuse.get_current_trace_id()
        except Exception:
            return None

    def get_last_trace_id(self) -> str | None:
        """Return the trace ID from the last LangGraph callback execution.

        Use this after LangGraph processing to retrieve the trace ID
        for display or logging purposes.

        Returns:
            The trace ID from the last callback execution, or None if not available.
        """
        if not self._enabled or self._last_callback is None:
            return None

        try:
            # Access the last_trace_id property from the callback handler
            return getattr(self._last_callback, "last_trace_id", None)
        except Exception:
            return None
