"""Unit tests for LangfuseProvider - missing credentials scenario.

Tests verify that LangfuseProvider:
1. Handles missing credentials gracefully
2. Returns correct disabled state values
3. All methods work as safe no-ops when disabled
"""

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
from quilto.observability import ObservabilityProvider, SpanContext
from quilto.observability.langfuse import LangfuseProvider


@pytest.fixture
def cleared_langfuse_env() -> Generator[None]:
    """Clear Langfuse environment variables."""
    with patch.dict(
        os.environ,
        {
            "LANGFUSE_PUBLIC_KEY": "",
            "LANGFUSE_SECRET_KEY": "",
            "LANGFUSE_BASE_URL": "",
        },
        clear=True,
    ):
        yield


class TestLangfuseProviderMissingCredentials:
    """Tests for LangfuseProvider with missing credentials."""

    def test_missing_credentials_is_enabled_returns_false(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify is_enabled() returns False when credentials are missing."""
        provider = LangfuseProvider()
        assert provider.is_enabled() is False

    def test_missing_public_key_is_enabled_returns_false(self) -> None:
        """Verify is_enabled() returns False when only secret_key is provided."""
        with patch.dict(
            os.environ,
            {
                "LANGFUSE_PUBLIC_KEY": "",
                "LANGFUSE_SECRET_KEY": "sk-lf-test",
                "LANGFUSE_BASE_URL": "",
            },
            clear=True,
        ):
            provider = LangfuseProvider()
            assert provider.is_enabled() is False

    def test_missing_secret_key_is_enabled_returns_false(self) -> None:
        """Verify is_enabled() returns False when only public_key is provided."""
        with patch.dict(
            os.environ,
            {
                "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
                "LANGFUSE_SECRET_KEY": "",
                "LANGFUSE_BASE_URL": "",
            },
            clear=True,
        ):
            provider = LangfuseProvider()
            assert provider.is_enabled() is False

    def test_missing_credentials_get_langgraph_callback_returns_none(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify get_langgraph_callback() returns None when disabled."""
        provider = LangfuseProvider()
        assert provider.get_langgraph_callback() is None

    def test_missing_credentials_span_works_without_exception(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify span() works without raising when credentials missing."""
        provider = LangfuseProvider()

        # Should not raise any exception
        with provider.span("test_operation") as ctx:
            assert isinstance(ctx, SpanContext)
            assert ctx.span_id == ""
            assert ctx.trace_id == ""

    def test_missing_credentials_span_with_metadata(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify span() accepts metadata without raising when disabled."""
        provider = LangfuseProvider()

        with provider.span("test_op", metadata={"key": "value"}) as ctx:
            assert isinstance(ctx, SpanContext)
            assert ctx.span_id == ""

    def test_missing_credentials_span_with_input(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify span() accepts input without raising when disabled."""
        provider = LangfuseProvider()

        with provider.span("test_op", input={"data": [1, 2, 3]}) as ctx:
            assert isinstance(ctx, SpanContext)

    def test_missing_credentials_log_event_no_exception(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify log_event() doesn't raise when disabled."""
        provider = LangfuseProvider()

        # Should not raise any exception
        provider.log_event("test_event")
        provider.log_event("test_event", metadata={"key": "value"})

    def test_missing_credentials_log_error_no_exception(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify log_error() doesn't raise when disabled."""
        provider = LangfuseProvider()

        # Should not raise any exception
        provider.log_error(ValueError("test error"))
        provider.log_error(RuntimeError("test"), metadata={"context": "test"})

    def test_missing_credentials_flush_no_exception(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify flush() doesn't raise when disabled."""
        provider = LangfuseProvider()

        # Should not raise any exception
        provider.flush()


class TestLangfuseProviderProtocol:
    """Tests that LangfuseProvider satisfies the ObservabilityProvider protocol."""

    def test_langfuse_provider_satisfies_protocol(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify isinstance(LangfuseProvider(), ObservabilityProvider) is True."""
        provider = LangfuseProvider()
        assert isinstance(provider, ObservabilityProvider)


class TestLangfuseProviderExplicitParams:
    """Tests for LangfuseProvider with explicit parameters."""

    def test_explicit_none_params_falls_back_to_env(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify explicit None params fall back to environment variables."""
        provider = LangfuseProvider(public_key=None, secret_key=None)
        assert provider.is_enabled() is False

    def test_empty_string_params_treated_as_missing(
        self, cleared_langfuse_env: None
    ) -> None:
        """Verify empty string params are treated as missing credentials."""
        provider = LangfuseProvider(public_key="", secret_key="")
        assert provider.is_enabled() is False
