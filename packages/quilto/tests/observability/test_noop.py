"""Tests for NoOpProvider implementation.

Tests verify that NoOpProvider:
1. Satisfies the ObservabilityProvider protocol
2. All methods work as safe no-ops without raising exceptions
3. Returns correct values (False for is_enabled, None for callback, etc.)
"""

from quilto.observability import NoOpProvider, ObservabilityProvider, SpanContext


class TestNoOpProviderProtocol:
    """Tests that NoOpProvider satisfies the ObservabilityProvider protocol."""

    def test_noop_provider_satisfies_protocol(self) -> None:
        """Verify isinstance(NoOpProvider(), ObservabilityProvider) is True."""
        provider = NoOpProvider()
        assert isinstance(provider, ObservabilityProvider)


class TestNoOpProviderIsEnabled:
    """Tests for is_enabled() method."""

    def test_noop_provider_is_enabled_returns_false(self) -> None:
        """Verify is_enabled() returns False."""
        provider = NoOpProvider()
        assert provider.is_enabled() is False


class TestNoOpProviderCallback:
    """Tests for get_langgraph_callback() method."""

    def test_noop_provider_get_langgraph_callback_returns_none(self) -> None:
        """Verify get_langgraph_callback() returns None."""
        provider = NoOpProvider()
        assert provider.get_langgraph_callback() is None


class TestNoOpProviderSpan:
    """Tests for span() context manager."""

    def test_noop_provider_span_context_manager(self) -> None:
        """Verify span() works as context manager without raising."""
        provider = NoOpProvider()

        # Should not raise any exception
        with provider.span("test_operation") as ctx:
            assert isinstance(ctx, SpanContext)
            assert ctx.span_id == ""
            assert ctx.trace_id == ""

    def test_noop_provider_span_with_metadata(self) -> None:
        """Verify span() accepts metadata without raising."""
        provider = NoOpProvider()

        with provider.span("test_op", metadata={"key": "value"}) as ctx:
            assert isinstance(ctx, SpanContext)

    def test_noop_provider_span_with_input(self) -> None:
        """Verify span() accepts input without raising."""
        provider = NoOpProvider()

        with provider.span("test_op", input={"data": [1, 2, 3]}) as ctx:
            assert isinstance(ctx, SpanContext)

    def test_noop_provider_span_with_all_params(self) -> None:
        """Verify span() accepts all parameters without raising."""
        provider = NoOpProvider()

        with provider.span(
            "test_op",
            metadata={"operation": "test"},
            input={"query": "test query"},
        ) as ctx:
            assert isinstance(ctx, SpanContext)
            assert ctx.span_id == ""
            assert ctx.trace_id == ""


class TestNoOpProviderLogEvent:
    """Tests for log_event() method."""

    def test_noop_provider_log_event_no_exception(self) -> None:
        """Verify log_event() doesn't raise."""
        provider = NoOpProvider()

        # Should not raise any exception
        provider.log_event("test_event")

    def test_noop_provider_log_event_with_metadata(self) -> None:
        """Verify log_event() accepts metadata without raising."""
        provider = NoOpProvider()

        provider.log_event("test_event", metadata={"key": "value"})


class TestNoOpProviderLogError:
    """Tests for log_error() method."""

    def test_noop_provider_log_error_no_exception(self) -> None:
        """Verify log_error() doesn't raise."""
        provider = NoOpProvider()

        # Should not raise any exception
        provider.log_error(ValueError("test error"))

    def test_noop_provider_log_error_with_metadata(self) -> None:
        """Verify log_error() accepts metadata without raising."""
        provider = NoOpProvider()

        provider.log_error(RuntimeError("test"), metadata={"context": "test"})


class TestNoOpProviderFlush:
    """Tests for flush() method."""

    def test_noop_provider_flush_no_exception(self) -> None:
        """Verify flush() doesn't raise."""
        provider = NoOpProvider()

        # Should not raise any exception
        provider.flush()


class TestSpanContext:
    """Tests for SpanContext dataclass."""

    def test_span_context_creation(self) -> None:
        """Verify SpanContext can be created with required fields."""
        ctx = SpanContext(span_id="span-123", trace_id="trace-456")
        assert ctx.span_id == "span-123"
        assert ctx.trace_id == "trace-456"

    def test_span_context_empty_values(self) -> None:
        """Verify SpanContext accepts empty string values."""
        ctx = SpanContext(span_id="", trace_id="")
        assert ctx.span_id == ""
        assert ctx.trace_id == ""
