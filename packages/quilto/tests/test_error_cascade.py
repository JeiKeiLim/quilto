"""Unit tests for LLM error cascade functionality."""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import litellm.exceptions
import pytest
from pydantic import BaseModel, ValidationError
from quilto.llm import LLMClient, PartialResult, load_llm_config_from_dict
from quilto.llm.config import LLMConfig, ProviderConfig
from quilto.llm.errors import ErrorType, classify_error


class TestErrorClassification:
    """Tests for error classification (AC4)."""

    def test_rate_limit_is_transient(self) -> None:
        """RateLimitError should be classified as transient."""
        error = litellm.exceptions.RateLimitError(
            message="rate limited",
            llm_provider="test",
            model="test-model",
            response=MagicMock(),
        )
        assert classify_error(error) == ErrorType.TRANSIENT

    def test_timeout_is_transient(self) -> None:
        """Timeout should be classified as transient."""
        error = litellm.exceptions.Timeout(
            message="timeout",
            model="test-model",
            llm_provider="test",
        )
        assert classify_error(error) == ErrorType.TRANSIENT

    def test_api_connection_error_is_transient(self) -> None:
        """APIConnectionError should be classified as transient."""
        error = litellm.exceptions.APIConnectionError(
            message="connection failed",
            llm_provider="test",
            model="test-model",
        )
        assert classify_error(error) == ErrorType.TRANSIENT

    def test_service_unavailable_is_transient(self) -> None:
        """ServiceUnavailableError should be classified as transient."""
        error = litellm.exceptions.ServiceUnavailableError(
            message="service unavailable",
            llm_provider="test",
            model="test-model",
            response=MagicMock(),
        )
        assert classify_error(error) == ErrorType.TRANSIENT

    def test_auth_error_is_permanent(self) -> None:
        """AuthenticationError should be classified as permanent."""
        error = litellm.exceptions.AuthenticationError(
            message="bad api key",
            llm_provider="test",
            model="test-model",
            response=MagicMock(),
        )
        assert classify_error(error) == ErrorType.PERMANENT

    def test_invalid_request_is_permanent(self) -> None:
        """InvalidRequestError should be classified as permanent."""
        error = litellm.exceptions.InvalidRequestError(
            message="invalid request",
            model="test-model",
            llm_provider="test",
        )
        assert classify_error(error) == ErrorType.PERMANENT

    def test_not_found_is_permanent(self) -> None:
        """NotFoundError should be classified as permanent."""
        error = litellm.exceptions.NotFoundError(
            message="model not found",
            model="test-model",
            llm_provider="test",
            response=MagicMock(),
        )
        assert classify_error(error) == ErrorType.PERMANENT

    def test_json_decode_error_is_permanent(self) -> None:
        """JSONDecodeError should be classified as permanent."""
        error = json.JSONDecodeError("Invalid JSON", "doc", 0)
        assert classify_error(error) == ErrorType.PERMANENT

    def test_validation_error_is_permanent(self) -> None:
        """Pydantic ValidationError should be classified as permanent."""

        class TestModel(BaseModel):
            required_field: str

        with pytest.raises(ValidationError) as exc_info:
            TestModel()  # type: ignore[call-arg]
        assert classify_error(exc_info.value) == ErrorType.PERMANENT

    def test_unknown_error_is_unknown(self) -> None:
        """Generic exceptions should be classified as unknown."""
        error = ValueError("something else")
        assert classify_error(error) == ErrorType.UNKNOWN

    def test_status_code_429_is_transient(self) -> None:
        """Exception with status_code 429 should be transient."""

        class CustomError(Exception):
            status_code = 429

        assert classify_error(CustomError()) == ErrorType.TRANSIENT

    def test_status_code_401_is_permanent(self) -> None:
        """Exception with status_code 401 should be permanent."""

        class CustomError(Exception):
            status_code = 401

        assert classify_error(CustomError()) == ErrorType.PERMANENT

    def test_status_code_5xx_is_transient(self) -> None:
        """Exception with 5xx status codes should be transient."""

        class CustomError(Exception):
            status_code = 503

        assert classify_error(CustomError()) == ErrorType.TRANSIENT

    def test_internal_server_error_is_transient(self) -> None:
        """InternalServerError should be classified as transient."""
        error = litellm.exceptions.InternalServerError(
            message="internal server error",
            llm_provider="test",
            model="test-model",
            response=MagicMock(),
        )
        assert classify_error(error) == ErrorType.TRANSIENT

    def test_bad_gateway_error_is_transient(self) -> None:
        """BadGatewayError should be classified as transient."""
        error = litellm.exceptions.BadGatewayError(
            message="bad gateway",
            llm_provider="test",
            model="test-model",
            response=MagicMock(),
        )
        assert classify_error(error) == ErrorType.TRANSIENT

    def test_bad_request_error_is_permanent(self) -> None:
        """BadRequestError should be classified as permanent."""
        error = litellm.exceptions.BadRequestError(
            message="bad request",
            model="test-model",
            llm_provider="test",
            response=MagicMock(),
        )
        assert classify_error(error) == ErrorType.PERMANENT

    def test_permission_denied_error_is_permanent(self) -> None:
        """PermissionDeniedError should be classified as permanent."""
        error = litellm.exceptions.PermissionDeniedError(
            message="permission denied",
            llm_provider="test",
            model="test-model",
            response=MagicMock(),
        )
        assert classify_error(error) == ErrorType.PERMANENT

    def test_content_policy_violation_is_permanent(self) -> None:
        """ContentPolicyViolationError should be classified as permanent."""
        error = litellm.exceptions.ContentPolicyViolationError(
            message="content policy violation",
            model="test-model",
            llm_provider="test",
            response=MagicMock(),
        )
        assert classify_error(error) == ErrorType.PERMANENT


class TestPartialResult:
    """Tests for PartialResult model (AC3, AC6)."""

    def test_is_partial_returns_true(self) -> None:
        """is_partial() should always return True."""
        result = PartialResult(
            error_message="test error",
            error_type="degraded",
        )
        assert result.is_partial() is True

    def test_success_defaults_to_false(self) -> None:
        """Success field should default to False."""
        result = PartialResult(
            error_message="test error",
            error_type="degraded",
        )
        assert result.success is False

    def test_stores_provider_info(self) -> None:
        """PartialResult stores provider and retry information."""
        result = PartialResult(
            error_message="test error",
            error_type="degraded",
            providers_attempted=["ollama", "anthropic"],
            retry_count=6,
        )
        assert result.providers_attempted == ["ollama", "anthropic"]
        assert result.retry_count == 6

    def test_frozen_model(self) -> None:
        """PartialResult should be immutable."""
        result = PartialResult(
            error_message="test error",
            error_type="degraded",
        )
        with pytest.raises(ValidationError):
            result.error_message = "new error"  # type: ignore[misc]


class TestLLMConfigRetrySettings:
    """Tests for LLMConfig retry settings (AC5)."""

    def test_default_max_retries(self) -> None:
        """Default max_retries should be 3."""
        config = load_llm_config_from_dict(
            {
                "default_provider": "ollama",
                "providers": {"ollama": {"api_base": "http://localhost:11434"}},
            }
        )
        assert config.max_retries == 3

    def test_default_base_retry_delay(self) -> None:
        """Default base_retry_delay should be 1.0."""
        config = load_llm_config_from_dict(
            {
                "default_provider": "ollama",
                "providers": {"ollama": {"api_base": "http://localhost:11434"}},
            }
        )
        assert config.base_retry_delay == 1.0

    def test_default_enable_graceful_degradation(self) -> None:
        """Default enable_graceful_degradation should be True."""
        config = load_llm_config_from_dict(
            {
                "default_provider": "ollama",
                "providers": {"ollama": {"api_base": "http://localhost:11434"}},
            }
        )
        assert config.enable_graceful_degradation is True

    def test_custom_max_retries(self) -> None:
        """Custom max_retries is respected."""
        config = load_llm_config_from_dict(
            {
                "default_provider": "ollama",
                "providers": {"ollama": {"api_base": "http://localhost:11434"}},
                "max_retries": 5,
            }
        )
        assert config.max_retries == 5

    def test_max_retries_validation_non_negative(self) -> None:
        """max_retries must be >= 0."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            load_llm_config_from_dict(
                {
                    "default_provider": "ollama",
                    "providers": {"ollama": {"api_base": "http://localhost:11434"}},
                    "max_retries": -1,
                }
            )

    def test_base_retry_delay_validation_positive(self) -> None:
        """base_retry_delay must be > 0."""
        with pytest.raises(ValueError, match="base_retry_delay must be > 0"):
            load_llm_config_from_dict(
                {
                    "default_provider": "ollama",
                    "providers": {"ollama": {"api_base": "http://localhost:11434"}},
                    "base_retry_delay": 0,
                }
            )


def create_test_config(
    max_retries: int = 3,
    base_retry_delay: float = 0.01,
    enable_graceful_degradation: bool = True,
    fallback_provider: str | None = None,
) -> LLMConfig:
    """Create a test LLMConfig.

    Args:
        max_retries: Max retry attempts per provider.
        base_retry_delay: Base delay for exponential backoff.
        enable_graceful_degradation: Whether to return PartialResult on failure.
        fallback_provider: Optional fallback provider name.

    Returns:
        Configured LLMConfig for testing.
    """
    return LLMConfig(
        default_provider="ollama",
        fallback_provider=fallback_provider,  # type: ignore[arg-type]
        providers={
            "ollama": ProviderConfig(api_base="http://localhost:11434"),
            "anthropic": ProviderConfig(api_key="test-key"),
        },
        max_retries=max_retries,
        base_retry_delay=base_retry_delay,
        enable_graceful_degradation=enable_graceful_degradation,
    )


class TestRetryWithBackoff:
    """Tests for retry mechanism (AC1)."""

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self) -> None:
        """Should retry max_retries times on transient errors."""
        config = create_test_config(max_retries=3)
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = litellm.exceptions.Timeout(
                message="timeout",
                model="test",
                llm_provider="ollama",
            )

            with patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock):
                result, exception, retries = await client._retry_with_backoff(  # pyright: ignore[reportPrivateUsage]
                    "router", [{"role": "user", "content": "test"}]
                )

        assert result is None
        assert exception is not None
        assert retries == 3
        assert mock_complete.call_count == 3

    @pytest.mark.asyncio
    async def test_stops_early_on_permanent_error(self) -> None:
        """Should NOT retry on permanent errors."""
        config = create_test_config(max_retries=3)
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = litellm.exceptions.AuthenticationError(
                message="bad key",
                response=MagicMock(),
                llm_provider="ollama",
                model="test",
            )

            result, _, retries = await client._retry_with_backoff(  # pyright: ignore[reportPrivateUsage]
                "router", [{"role": "user", "content": "test"}]
            )

        assert result is None
        assert retries == 1  # Only 1 attempt, no retries
        assert mock_complete.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_on_first_success(self) -> None:
        """Should return immediately on success."""
        config = create_test_config(max_retries=3)
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = "Success!"

            result, exception, retries = await client._retry_with_backoff(  # pyright: ignore[reportPrivateUsage]
                "router", [{"role": "user", "content": "test"}]
            )

        assert result == "Success!"
        assert exception is None
        assert retries == 1
        assert mock_complete.call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retry(self) -> None:
        """Should succeed after transient failure."""
        config = create_test_config(max_retries=3)
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = [
                litellm.exceptions.Timeout(message="timeout", model="test", llm_provider="ollama"),
                "Success!",
            ]

            with patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock):
                result, exception, retries = await client._retry_with_backoff(  # pyright: ignore[reportPrivateUsage]
                    "router", [{"role": "user", "content": "test"}]
                )

        assert result == "Success!"
        assert exception is None
        assert retries == 2

    @pytest.mark.asyncio
    async def test_max_retries_zero_makes_no_attempts(self) -> None:
        """max_retries=0 should make no attempts at all.

        This documents the current behavior: when max_retries=0, the retry loop
        executes 0 times, meaning no LLM calls are made. The method returns
        (None, None, 0) indicating no result, no error, and 0 attempts.
        """
        config = create_test_config(max_retries=0)
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = "Would succeed"

            result, exception, retries = await client._retry_with_backoff(  # pyright: ignore[reportPrivateUsage]
                "router", [{"role": "user", "content": "test"}]
            )

        # With max_retries=0, no attempts are made
        assert result is None
        assert exception is None
        assert retries == 0
        assert mock_complete.call_count == 0

    @pytest.mark.asyncio
    async def test_applies_exponential_backoff(self) -> None:
        """Should apply exponential backoff between retries."""
        config = create_test_config(max_retries=3, base_retry_delay=1.0)
        client = LLMClient(config)

        sleep_calls: list[float] = []

        async def mock_sleep(delay: float) -> None:
            sleep_calls.append(delay)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = litellm.exceptions.Timeout(
                message="timeout",
                model="test",
                llm_provider="ollama",
            )

            with patch("quilto.llm.client.asyncio.sleep", side_effect=mock_sleep):
                await client._retry_with_backoff(  # pyright: ignore[reportPrivateUsage]
                    "router", [{"role": "user", "content": "test"}]
                )

        # Should have 2 sleeps (before retry 2 and 3, not after last attempt)
        assert len(sleep_calls) == 2
        # First delay: 1.0 * 2^0 + jitter = ~1.0-1.5
        assert 1.0 <= sleep_calls[0] <= 1.5
        # Second delay: 1.0 * 2^1 + jitter = ~2.0-2.5
        assert 2.0 <= sleep_calls[1] <= 2.5


class TestCompleteCascade:
    """Tests for full error cascade (AC1, AC2, AC3)."""

    @pytest.mark.asyncio
    async def test_returns_on_primary_success(self) -> None:
        """Should return immediately when primary provider succeeds."""
        config = create_test_config(fallback_provider="anthropic")
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = "Success!"

            result = await client.complete_with_cascade("router", [{"role": "user", "content": "test"}])

        assert result == "Success!"
        assert mock_complete.call_count == 1

    @pytest.mark.asyncio
    async def test_tries_fallback_after_primary_fails(self) -> None:
        """Should try fallback provider after primary fails (AC2)."""
        config = create_test_config(max_retries=1, fallback_provider="anthropic")
        client = LLMClient(config)

        call_count = 0

        async def mock_complete(*args: Any, force_cloud: bool = False, **kwargs: Any) -> str:
            nonlocal call_count
            call_count += 1
            if not force_cloud:
                raise litellm.exceptions.Timeout(message="timeout", model="test", llm_provider="ollama")
            return "Fallback success!"

        with (
            patch.object(client, "complete", side_effect=mock_complete),
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await client.complete_with_cascade("router", [{"role": "user", "content": "test"}])

        assert result == "Fallback success!"
        assert call_count == 2  # 1 primary + 1 fallback

    @pytest.mark.asyncio
    async def test_graceful_degradation_returns_partial_result(self) -> None:
        """Should return PartialResult when all providers fail (AC3)."""
        config = create_test_config(max_retries=1, enable_graceful_degradation=True)
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = RuntimeError("total failure")

            with patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock):
                result = await client.complete_with_cascade("router", [{"role": "user", "content": "test"}])

        assert isinstance(result, PartialResult)
        assert result.success is False
        assert "total failure" in result.error_message
        assert result.error_type == "degraded"
        assert "ollama" in result.providers_attempted

    @pytest.mark.asyncio
    async def test_raises_when_degradation_disabled(self) -> None:
        """Should raise when graceful degradation is disabled."""
        config = create_test_config(max_retries=1, enable_graceful_degradation=False)
        client = LLMClient(config)

        with (
            patch.object(client, "complete", new_callable=AsyncMock) as mock_complete,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(RuntimeError, match="total failure"),
        ):
            mock_complete.side_effect = RuntimeError("total failure")
            await client.complete_with_cascade("router", [{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_raises_when_allow_degradation_false(self) -> None:
        """Should raise when allow_degradation=False is passed."""
        config = create_test_config(max_retries=1, enable_graceful_degradation=True)
        client = LLMClient(config)

        with (
            patch.object(client, "complete", new_callable=AsyncMock) as mock_complete,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(RuntimeError, match="total failure"),
        ):
            mock_complete.side_effect = RuntimeError("total failure")
            await client.complete_with_cascade(
                "router",
                [{"role": "user", "content": "test"}],
                allow_degradation=False,
            )

    @pytest.mark.asyncio
    async def test_tracks_all_providers_attempted(self) -> None:
        """PartialResult should track all providers attempted."""
        config = create_test_config(
            max_retries=1,
            fallback_provider="anthropic",
            enable_graceful_degradation=True,
        )
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = RuntimeError("failure")

            with patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock):
                result = await client.complete_with_cascade("router", [{"role": "user", "content": "test"}])

        assert isinstance(result, PartialResult)
        assert result.providers_attempted == ["ollama", "anthropic"]
        assert result.retry_count == 2  # 1 for each provider

    @pytest.mark.asyncio
    async def test_tracks_total_retries(self) -> None:
        """PartialResult should track total retry count across providers."""
        config = create_test_config(
            max_retries=3,
            fallback_provider="anthropic",
            enable_graceful_degradation=True,
        )
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = litellm.exceptions.Timeout(
                message="timeout",
                model="test",
                llm_provider="test",
            )

            with patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock):
                result = await client.complete_with_cascade("router", [{"role": "user", "content": "test"}])

        assert isinstance(result, PartialResult)
        assert result.retry_count == 6  # 3 for each provider


class TestCompleteStructuredCascade:
    """Tests for structured output with cascade (AC6)."""

    @pytest.mark.asyncio
    async def test_returns_validated_model_on_success(self) -> None:
        """Should return validated Pydantic model on success."""

        class ExpectedSchema(BaseModel):
            field: str

        config = create_test_config()
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"field": "value"}'))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            result = await client.complete_structured_with_cascade(
                "router",
                [{"role": "user", "content": "test"}],
                response_model=ExpectedSchema,
            )

        assert isinstance(result, ExpectedSchema)
        assert result.field == "value"

    @pytest.mark.asyncio
    async def test_schema_error_returns_partial_result(self) -> None:
        """Should return PartialResult when schema validation fails repeatedly."""

        class ExpectedSchema(BaseModel):
            field: str

        config = create_test_config(max_retries=1, enable_graceful_degradation=True)
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"wrong": "field"}'))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            with patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock):
                result = await client.complete_structured_with_cascade(
                    "router",
                    [{"role": "user", "content": "test"}],
                    response_model=ExpectedSchema,
                )

        assert isinstance(result, PartialResult)
        assert "ExpectedSchema" in result.error_message

    @pytest.mark.asyncio
    async def test_schema_error_skips_retry(self) -> None:
        """Schema validation errors should skip retry (permanent error)."""

        class ExpectedSchema(BaseModel):
            field: str

        config = create_test_config(max_retries=3, enable_graceful_degradation=True)
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"wrong": "field"}'))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            with patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock):
                result = await client.complete_structured_with_cascade(
                    "router",
                    [{"role": "user", "content": "test"}],
                    response_model=ExpectedSchema,
                )

        # Schema error is permanent, so only 1 attempt per provider
        assert isinstance(result, PartialResult)
        assert mock_acompletion.call_count == 1


class TestCompleteWithFallbackBackwardCompatibility:
    """Tests for backward compatibility of complete_with_fallback (AC6)."""

    @pytest.mark.asyncio
    async def test_returns_string_on_success(self) -> None:
        """Should return string (not PartialResult) on success."""
        config = create_test_config(fallback_provider="anthropic")
        client = LLMClient(config)

        with patch.object(client, "complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = "Success!"

            result = await client.complete_with_fallback("router", [{"role": "user", "content": "test"}])

        assert result == "Success!"
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_raises_on_all_failures(self) -> None:
        """Should raise exception (not return PartialResult) on all failures."""
        config = create_test_config(max_retries=1, enable_graceful_degradation=True)
        client = LLMClient(config)

        with (
            patch.object(client, "complete", new_callable=AsyncMock) as mock_complete,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(RuntimeError, match="total failure"),
        ):
            mock_complete.side_effect = RuntimeError("total failure")
            await client.complete_with_fallback("router", [{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_uses_fallback_provider(self) -> None:
        """Should still use fallback provider on primary failure."""
        config = create_test_config(max_retries=1, fallback_provider="anthropic")
        client = LLMClient(config)

        call_count = 0

        async def mock_complete(*args: Any, force_cloud: bool = False, **kwargs: Any) -> str:
            nonlocal call_count
            call_count += 1
            if not force_cloud:
                raise litellm.exceptions.Timeout(message="timeout", model="test", llm_provider="ollama")
            return "Fallback success!"

        with (
            patch.object(client, "complete", side_effect=mock_complete),
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await client.complete_with_fallback("router", [{"role": "user", "content": "test"}])

        assert result == "Fallback success!"
        assert call_count == 2
