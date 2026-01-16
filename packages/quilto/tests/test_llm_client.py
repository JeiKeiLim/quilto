"""Unit tests for LLMClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel
from quilto.llm.client import LLMClient
from quilto.llm.config import (
    AgentConfig,
    LLMConfig,
    ProviderConfig,
    TierModels,
)


class SampleResponse(BaseModel):
    """Sample response model for structured completion tests."""

    message: str
    score: int


def create_test_config(
    default_provider: str = "ollama",
    fallback_provider: str | None = None,
) -> LLMConfig:
    """Create a test LLMConfig with all providers configured.

    Args:
        default_provider: Default provider to use.
        fallback_provider: Fallback provider for error recovery.

    Returns:
        Configured LLMConfig for testing.
    """
    return LLMConfig(
        default_provider=default_provider,  # type: ignore[arg-type]
        fallback_provider=fallback_provider,  # type: ignore[arg-type]
        providers={
            "ollama": ProviderConfig(api_base="http://localhost:11434"),
            "anthropic": ProviderConfig(api_key="anthropic_key"),
            "openai": ProviderConfig(api_key="openai_key"),
            "azure": ProviderConfig(
                api_key="azure_key",
                api_base="https://azure.openai.com",
                api_version="2024-01-01",
            ),
            "openrouter": ProviderConfig(
                api_key="openrouter_key",
                api_base="https://openrouter.ai/api/v1",
            ),
        },
        tiers={
            "low": TierModels(
                ollama="qwen2.5:7b",
                anthropic="claude-3-haiku-20240307",
                openai="gpt-4o-mini",
                azure="gpt-4o-mini-deployment",
                openrouter="anthropic/claude-3-haiku",
            ),
            "medium": TierModels(
                ollama="qwen2.5:14b",
                anthropic="claude-3-5-haiku-20241022",
                openai="gpt-4o-mini",
                azure="gpt-4o-mini-deployment",
                openrouter="anthropic/claude-3.5-haiku",
            ),
            "high": TierModels(
                ollama="qwen2.5:32b",
                anthropic="claude-sonnet-4-20250514",
                openai="gpt-4o",
                azure="gpt-4o-deployment",
                openrouter="anthropic/claude-sonnet-4-20250514",
            ),
        },
        agents={
            "router": AgentConfig(tier="low"),
            "parser": AgentConfig(tier="medium"),
            "analyzer": AgentConfig(tier="high"),
            "custom_anthropic": AgentConfig(tier="high", provider="anthropic"),
        },
    )


class TestResolveModel:
    """Test LLMClient.resolve_model method."""

    def test_resolves_correct_tier_for_agent(self) -> None:
        """Resolves correct model based on agent tier (AC: #1)."""
        config = create_test_config()
        client = LLMClient(config)

        # Low tier agent
        resolution = client.resolve_model("router")
        assert resolution.provider == "ollama"
        assert resolution.model == "qwen2.5:7b"

        # High tier agent
        resolution = client.resolve_model("analyzer")
        assert resolution.provider == "ollama"
        assert resolution.model == "qwen2.5:32b"

    def test_respects_agent_provider_override(self) -> None:
        """Agent-specific provider override is respected (AC: #1)."""
        config = create_test_config()
        client = LLMClient(config)

        resolution = client.resolve_model("custom_anthropic")
        assert resolution.provider == "anthropic"
        assert resolution.model == "claude-sonnet-4-20250514"

    def test_applies_ollama_prefix(self) -> None:
        """Ollama models get 'ollama/' prefix (AC: #2)."""
        config = create_test_config(default_provider="ollama")
        client = LLMClient(config)

        resolution = client.resolve_model("router")
        assert resolution.litellm_model == "ollama/qwen2.5:7b"

    def test_applies_azure_prefix(self) -> None:
        """Azure deployments get 'azure/' prefix."""
        config = create_test_config(default_provider="azure")
        client = LLMClient(config)

        resolution = client.resolve_model("router")
        assert resolution.litellm_model == "azure/gpt-4o-mini-deployment"

    def test_applies_openrouter_prefix(self) -> None:
        """OpenRouter models get 'openrouter/' prefix."""
        config = create_test_config(default_provider="openrouter")
        client = LLMClient(config)

        resolution = client.resolve_model("router")
        assert resolution.litellm_model == "openrouter/anthropic/claude-3-haiku"

    def test_no_prefix_for_anthropic(self) -> None:
        """Anthropic models have no prefix."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        resolution = client.resolve_model("router")
        assert resolution.litellm_model == "claude-3-haiku-20240307"

    def test_no_prefix_for_openai(self) -> None:
        """OpenAI models have no prefix."""
        config = create_test_config(default_provider="openai")
        client = LLMClient(config)

        resolution = client.resolve_model("router")
        assert resolution.litellm_model == "gpt-4o-mini"

    def test_includes_api_base_for_ollama(self) -> None:
        """API base is included for Ollama (AC: #2)."""
        config = create_test_config(default_provider="ollama")
        client = LLMClient(config)

        resolution = client.resolve_model("router")
        assert resolution.api_base == "http://localhost:11434"

    def test_includes_api_key_for_cloud_providers(self) -> None:
        """API key is included for cloud providers (AC: #3)."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        resolution = client.resolve_model("router")
        assert resolution.api_key == "anthropic_key"

    def test_uses_fallback_provider_when_force_cloud(self) -> None:
        """Uses fallback_provider when force_cloud=True (AC: #3)."""
        config = create_test_config(
            default_provider="ollama",
            fallback_provider="anthropic",
        )
        client = LLMClient(config)

        resolution = client.resolve_model("router", force_cloud=True)
        assert resolution.provider == "anthropic"
        assert resolution.model == "claude-3-haiku-20240307"
        assert resolution.api_key == "anthropic_key"

    def test_uses_default_agent_config_for_unknown_agent(self) -> None:
        """Unknown agents use default AgentConfig (medium tier)."""
        config = create_test_config(default_provider="ollama")
        client = LLMClient(config)

        resolution = client.resolve_model("unknown_agent")
        assert resolution.model == "qwen2.5:14b"  # medium tier

    def test_raises_on_missing_provider_model(self) -> None:
        """Raises ValueError when provider has no model for tier."""
        config = LLMConfig(
            default_provider="ollama",
            tiers={"low": TierModels(anthropic="model")},  # No ollama model
            agents={"test": AgentConfig(tier="low")},
        )
        client = LLMClient(config)

        with pytest.raises(ValueError, match=r"No model configured for provider 'ollama'.*anthropic"):
            client.resolve_model("test")


class TestComplete:
    """Test LLMClient.complete method."""

    @pytest.mark.asyncio
    async def test_calls_litellm_with_correct_params(self) -> None:
        """Complete calls litellm.acompletion with resolved params."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            messages = [{"role": "user", "content": "Hi"}]
            result = await client.complete("router", messages)

            assert result == "Hello!"
            mock_acompletion.assert_called_once()
            call_kwargs = mock_acompletion.call_args.kwargs
            assert call_kwargs["model"] == "claude-3-haiku-20240307"
            assert call_kwargs["messages"] == messages
            assert call_kwargs["api_key"] == "anthropic_key"

    @pytest.mark.asyncio
    async def test_includes_api_base_when_set(self) -> None:
        """Complete includes api_base when provider has it configured."""
        config = create_test_config(default_provider="ollama")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            await client.complete("router", [{"role": "user", "content": "Hi"}])

            call_kwargs = mock_acompletion.call_args.kwargs
            assert call_kwargs["api_base"] == "http://localhost:11434"

    @pytest.mark.asyncio
    async def test_passes_extra_kwargs(self) -> None:
        """Complete passes extra kwargs to litellm."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            await client.complete(
                "router",
                [{"role": "user", "content": "Hi"}],
                temperature=0.7,
                max_tokens=100,
            )

            call_kwargs = mock_acompletion.call_args.kwargs
            assert call_kwargs["temperature"] == 0.7
            assert call_kwargs["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_returns_empty_string_for_none_content(self) -> None:
        """Complete returns empty string when content is None."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            result = await client.complete("router", [{"role": "user", "content": "Hi"}])
            assert result == ""


class TestCompleteStructured:
    """Test LLMClient.complete_structured method."""

    @pytest.mark.asyncio
    async def test_parses_json_response(self) -> None:
        """Parses JSON response into Pydantic model."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"message": "Hello", "score": 95}'))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            result = await client.complete_structured(
                "router",
                [{"role": "user", "content": "Hi"}],
                response_model=SampleResponse,
            )

            assert isinstance(result, SampleResponse)
            assert result.message == "Hello"
            assert result.score == 95

    @pytest.mark.asyncio
    async def test_passes_json_response_format(self) -> None:
        """Passes response_format=json_object to litellm."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"message": "Hi", "score": 1}'))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            await client.complete_structured(
                "router",
                [{"role": "user", "content": "Hi"}],
                response_model=SampleResponse,
            )

            call_kwargs = mock_acompletion.call_args.kwargs
            assert call_kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_raises_on_invalid_json(self) -> None:
        """Raises ValueError on invalid JSON response."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="not valid json"))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            with pytest.raises(ValueError, match="LLM response failed schema validation"):
                await client.complete_structured(
                    "router",
                    [{"role": "user", "content": "Hi"}],
                    response_model=SampleResponse,
                )

    @pytest.mark.asyncio
    async def test_raises_on_schema_mismatch(self) -> None:
        """Raises ValueError when JSON doesn't match schema."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"wrong_field": "value"}'))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            with pytest.raises(ValueError, match="SampleResponse"):
                await client.complete_structured(
                    "router",
                    [{"role": "user", "content": "Hi"}],
                    response_model=SampleResponse,
                )


class TestCompleteWithFallback:
    """Test LLMClient.complete_with_fallback method."""

    @pytest.mark.asyncio
    async def test_returns_primary_response_on_success(self) -> None:
        """Returns response from primary provider when successful."""
        config = create_test_config(
            default_provider="ollama",
            fallback_provider="anthropic",
        )
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Primary"))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            result = await client.complete_with_fallback(
                "router",
                [{"role": "user", "content": "Hi"}],
            )

            assert result == "Primary"
            assert mock_acompletion.call_count == 1

    @pytest.mark.asyncio
    async def test_falls_back_on_error(self) -> None:
        """Falls back to fallback_provider on error (AC: #3)."""
        config = create_test_config(
            default_provider="ollama",
            fallback_provider="anthropic",
        )
        client = LLMClient(config)

        primary_error = Exception("Connection failed")
        fallback_response = MagicMock()
        fallback_response.choices = [MagicMock(message=MagicMock(content="Fallback"))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.side_effect = [primary_error, fallback_response]

            result = await client.complete_with_fallback(
                "router",
                [{"role": "user", "content": "Hi"}],
            )

            assert result == "Fallback"
            assert mock_acompletion.call_count == 2

    @pytest.mark.asyncio
    async def test_uses_fallback_provider_model(self) -> None:
        """Fallback uses fallback_provider's model."""
        # Set max_retries=1 to get simple primary->fallback behavior
        config = LLMConfig(
            default_provider="ollama",
            fallback_provider="anthropic",
            max_retries=1,
            base_retry_delay=0.01,
            providers={
                "ollama": ProviderConfig(api_base="http://localhost:11434"),
                "anthropic": ProviderConfig(api_key="anthropic_key"),
            },
            tiers={
                "low": TierModels(
                    ollama="qwen2.5:7b",
                    anthropic="claude-3-haiku-20240307",
                ),
            },
            agents={"router": AgentConfig(tier="low")},
        )
        client = LLMClient(config)

        primary_error = Exception("Connection failed")
        fallback_response = MagicMock()
        fallback_response.choices = [MagicMock(message=MagicMock(content="Fallback"))]

        with (
            patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_acompletion.side_effect = [primary_error, fallback_response]

            await client.complete_with_fallback(
                "router",
                [{"role": "user", "content": "Hi"}],
            )

            # Second call should use anthropic
            second_call_kwargs = mock_acompletion.call_args_list[1].kwargs
            assert second_call_kwargs["model"] == "claude-3-haiku-20240307"
            assert second_call_kwargs["api_key"] == "anthropic_key"

    @pytest.mark.asyncio
    async def test_raises_if_no_fallback_configured(self) -> None:
        """Raises original error if no fallback_provider configured."""
        config = create_test_config(
            default_provider="ollama",
            fallback_provider=None,
        )
        client = LLMClient(config)

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                await client.complete_with_fallback(
                    "router",
                    [{"role": "user", "content": "Hi"}],
                )

    @pytest.mark.asyncio
    async def test_raises_if_both_providers_fail(self) -> None:
        """Raises fallback error if both providers fail."""
        # Set max_retries=1 to get simple primary->fallback behavior
        config = LLMConfig(
            default_provider="ollama",
            fallback_provider="anthropic",
            max_retries=1,
            base_retry_delay=0.01,
            providers={
                "ollama": ProviderConfig(api_base="http://localhost:11434"),
                "anthropic": ProviderConfig(api_key="anthropic_key"),
            },
            tiers={
                "low": TierModels(
                    ollama="qwen2.5:7b",
                    anthropic="claude-3-haiku-20240307",
                ),
            },
            agents={"router": AgentConfig(tier="low")},
        )
        client = LLMClient(config)

        with (
            patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_acompletion.side_effect = [
                Exception("Primary failed"),
                Exception("Fallback failed"),
            ]

            with pytest.raises(Exception, match="Fallback failed"):
                await client.complete_with_fallback(
                    "router",
                    [{"role": "user", "content": "Hi"}],
                )
