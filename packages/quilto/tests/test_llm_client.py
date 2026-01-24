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
    async def test_passes_default_timeout_to_litellm(self) -> None:
        """Complete passes default timeout (45s) to litellm (AC: #1)."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            await client.complete("router", [{"role": "user", "content": "Hi"}])

            call_kwargs = mock_acompletion.call_args.kwargs
            assert call_kwargs["timeout"] == 45.0

    @pytest.mark.asyncio
    async def test_passes_custom_timeout_to_litellm(self) -> None:
        """Complete passes custom timeout to litellm (AC: #2)."""
        config = LLMConfig(
            default_provider="anthropic",
            timeout=90.0,
            providers={"anthropic": ProviderConfig(api_key="anthropic_key")},
            tiers={"low": TierModels(anthropic="claude-3-haiku-20240307")},
            agents={"router": AgentConfig(tier="low")},
        )
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            await client.complete("router", [{"role": "user", "content": "Hi"}])

            call_kwargs = mock_acompletion.call_args.kwargs
            assert call_kwargs["timeout"] == 90.0

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

    @pytest.mark.asyncio
    async def test_passes_timeout_through(self) -> None:
        """Complete_structured passes timeout to litellm via complete()."""
        config = LLMConfig(
            default_provider="anthropic",
            timeout=120.0,
            providers={"anthropic": ProviderConfig(api_key="anthropic_key")},
            tiers={"low": TierModels(anthropic="claude-3-haiku-20240307")},
            agents={"router": AgentConfig(tier="low")},
        )
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
            assert call_kwargs["timeout"] == 120.0


class TestBuildResponseFormat:
    """Test LLMClient._build_response_format method."""

    def test_returns_json_schema_for_openrouter(self) -> None:
        """Returns json_schema format for OpenRouter provider (AC: #1)."""
        config = create_test_config(default_provider="openrouter")
        client = LLMClient(config)

        response_format = client._build_response_format(SampleResponse, "openrouter")  # pyright: ignore[reportPrivateUsage]

        assert response_format["type"] == "json_schema"
        assert response_format["json_schema"]["name"] == "SampleResponse"
        assert response_format["json_schema"]["strict"] is True
        assert "schema" in response_format["json_schema"]
        # Schema should have properties for message and score
        schema = response_format["json_schema"]["schema"]
        assert "properties" in schema
        assert "message" in schema["properties"]
        assert "score" in schema["properties"]

    def test_returns_json_schema_for_openai(self) -> None:
        """Returns json_schema format for OpenAI provider (AC: #1)."""
        config = create_test_config(default_provider="openai")
        client = LLMClient(config)

        response_format = client._build_response_format(SampleResponse, "openai")  # pyright: ignore[reportPrivateUsage]

        assert response_format["type"] == "json_schema"
        assert response_format["json_schema"]["name"] == "SampleResponse"

    def test_returns_json_schema_for_azure(self) -> None:
        """Returns json_schema format for Azure provider (AC: #1)."""
        config = create_test_config(default_provider="azure")
        client = LLMClient(config)

        response_format = client._build_response_format(SampleResponse, "azure")  # pyright: ignore[reportPrivateUsage]

        assert response_format["type"] == "json_schema"
        assert response_format["json_schema"]["name"] == "SampleResponse"

    def test_returns_json_object_for_ollama(self) -> None:
        """Returns json_object format for Ollama provider (AC: #3)."""
        config = create_test_config(default_provider="ollama")
        client = LLMClient(config)

        response_format = client._build_response_format(SampleResponse, "ollama")  # pyright: ignore[reportPrivateUsage]

        assert response_format == {"type": "json_object"}

    def test_returns_json_object_for_anthropic(self) -> None:
        """Returns json_object format for Anthropic (not supported)."""
        config = create_test_config(default_provider="anthropic")
        client = LLMClient(config)

        response_format = client._build_response_format(SampleResponse, "anthropic")  # pyright: ignore[reportPrivateUsage]

        assert response_format == {"type": "json_object"}

    def test_strict_false_disables_strict_mode(self) -> None:
        """Strict=False disables strict schema validation."""
        config = create_test_config(default_provider="openai")
        client = LLMClient(config)

        response_format = client._build_response_format(SampleResponse, "openai", strict=False)  # pyright: ignore[reportPrivateUsage]

        assert response_format["json_schema"]["strict"] is False


class TestExtractJson:
    """Test LLMClient._extract_json method."""

    def test_extracts_from_markdown_json_block(self) -> None:
        """Extracts JSON from ```json code block (AC: #5)."""
        config = create_test_config()
        client = LLMClient(config)

        response = '```json\n{"message": "Hello", "score": 1}\n```'
        extracted = client._extract_json(response)  # pyright: ignore[reportPrivateUsage]

        assert extracted == '{"message": "Hello", "score": 1}'

    def test_extracts_from_plain_markdown_block(self) -> None:
        """Extracts JSON from ``` code block (AC: #5)."""
        config = create_test_config()
        client = LLMClient(config)

        response = '```\n{"message": "Hello", "score": 1}\n```'
        extracted = client._extract_json(response)  # pyright: ignore[reportPrivateUsage]

        assert extracted == '{"message": "Hello", "score": 1}'

    def test_removes_single_line_comments(self) -> None:
        """Removes single-line // comments (AC: #5)."""
        config = create_test_config()
        client = LLMClient(config)

        response = '{\n// This is a comment\n"message": "Hello",\n"score": 1\n}'
        extracted = client._extract_json(response)  # pyright: ignore[reportPrivateUsage]

        assert "//" not in extracted
        assert '"message": "Hello"' in extracted

    def test_finds_json_boundaries(self) -> None:
        """Finds JSON object boundaries from surrounding text (AC: #5)."""
        config = create_test_config()
        client = LLMClient(config)

        response = 'Here is the response:\n{"message": "Hello", "score": 1}\nEnd of response'
        extracted = client._extract_json(response)  # pyright: ignore[reportPrivateUsage]

        assert extracted == '{"message": "Hello", "score": 1}'

    def test_returns_original_when_no_json(self) -> None:
        """Returns original string when no JSON found."""
        config = create_test_config()
        client = LLMClient(config)

        response = "This is not JSON at all"
        extracted = client._extract_json(response)  # pyright: ignore[reportPrivateUsage]

        assert extracted == response

    def test_handles_nested_json(self) -> None:
        """Handles nested JSON objects correctly."""
        config = create_test_config()
        client = LLMClient(config)

        response = '{"outer": {"inner": "value"}, "score": 1}'
        extracted = client._extract_json(response)  # pyright: ignore[reportPrivateUsage]

        assert extracted == '{"outer": {"inner": "value"}, "score": 1}'

    def test_removes_trailing_commas(self) -> None:
        """Removes trailing commas before closing braces/brackets (AC: #5)."""
        config = create_test_config()
        client = LLMClient(config)

        response = '{"message": "Hello", "score": 1,}'
        extracted = client._extract_json(response)  # pyright: ignore[reportPrivateUsage]

        assert extracted == '{"message": "Hello", "score": 1}'

    def test_removes_trailing_commas_in_nested(self) -> None:
        """Removes trailing commas in nested structures."""
        config = create_test_config()
        client = LLMClient(config)

        response = '{"outer": {"inner": "value",}, "items": [1, 2,],}'
        extracted = client._extract_json(response)  # pyright: ignore[reportPrivateUsage]

        assert extracted == '{"outer": {"inner": "value"}, "items": [1, 2]}'


class TestCompleteStructuredJsonSchema:
    """Test complete_structured with JSON schema mode."""

    @pytest.mark.asyncio
    async def test_uses_json_schema_for_openrouter(self) -> None:
        """Uses json_schema format for OpenRouter (AC: #1, #4)."""
        config = create_test_config(default_provider="openrouter")
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
            assert call_kwargs["response_format"]["type"] == "json_schema"
            assert call_kwargs["response_format"]["json_schema"]["name"] == "SampleResponse"

    @pytest.mark.asyncio
    async def test_uses_json_object_for_ollama(self) -> None:
        """Uses json_object format for Ollama (AC: #3)."""
        config = create_test_config(default_provider="ollama")
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
    async def test_extracts_json_from_markdown_on_parse_failure(self) -> None:
        """Falls back to _extract_json on parse failure (AC: #5)."""
        config = create_test_config(default_provider="ollama")
        client = LLMClient(config)

        # Response with markdown wrapper
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='```json\n{"message": "Hello", "score": 95}\n```'))
        ]

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
    async def test_raises_original_error_when_extraction_fails(self) -> None:
        """Raises original error when extraction doesn't help."""
        config = create_test_config(default_provider="ollama")
        client = LLMClient(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="completely invalid"))]

        with patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response

            with pytest.raises(ValueError, match="LLM response failed schema validation"):
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


class TestSchemaRetryBehavior:
    """Test schema retry behavior in _retry_structured_with_backoff (AC: #3, #4, #5)."""

    @pytest.mark.asyncio
    async def test_json_decode_error_triggers_retry(self) -> None:
        """JSONDecodeError triggers schema retry up to max_schema_retries (AC: #3)."""
        config = LLMConfig(
            default_provider="anthropic",
            max_retries=3,
            max_schema_retries=2,
            base_retry_delay=0.01,
            providers={"anthropic": ProviderConfig(api_key="anthropic_key")},
            tiers={"low": TierModels(anthropic="claude-3-haiku-20240307")},
            agents={"router": AgentConfig(tier="low")},
        )
        client = LLMClient(config)

        # First call fails with invalid JSON, second succeeds
        mock_response_invalid = MagicMock()
        mock_response_invalid.choices = [MagicMock(message=MagicMock(content="not valid json"))]

        mock_response_valid = MagicMock()
        mock_response_valid.choices = [MagicMock(message=MagicMock(content='{"message": "Hi", "score": 1}'))]

        with (
            patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_acompletion.side_effect = [mock_response_invalid, mock_response_valid]

            result = await client.complete_structured_with_cascade(
                "router",
                [{"role": "user", "content": "Hi"}],
                response_model=SampleResponse,
                allow_degradation=False,
            )

            assert isinstance(result, SampleResponse)
            assert result.message == "Hi"
            # Should have been called twice (1 fail + 1 success)
            assert mock_acompletion.call_count == 2

    @pytest.mark.asyncio
    async def test_validation_error_triggers_retry(self) -> None:
        """ValidationError triggers schema retry up to max_schema_retries (AC: #3)."""
        config = LLMConfig(
            default_provider="anthropic",
            max_retries=3,
            max_schema_retries=2,
            base_retry_delay=0.01,
            providers={"anthropic": ProviderConfig(api_key="anthropic_key")},
            tiers={"low": TierModels(anthropic="claude-3-haiku-20240307")},
            agents={"router": AgentConfig(tier="low")},
        )
        client = LLMClient(config)

        # First call returns wrong schema, second succeeds
        mock_response_wrong = MagicMock()
        mock_response_wrong.choices = [MagicMock(message=MagicMock(content='{"wrong": "schema"}'))]

        mock_response_valid = MagicMock()
        mock_response_valid.choices = [MagicMock(message=MagicMock(content='{"message": "Hi", "score": 1}'))]

        with (
            patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_acompletion.side_effect = [mock_response_wrong, mock_response_valid]

            result = await client.complete_structured_with_cascade(
                "router",
                [{"role": "user", "content": "Hi"}],
                response_model=SampleResponse,
                allow_degradation=False,
            )

            assert isinstance(result, SampleResponse)
            assert result.message == "Hi"
            # Should have been called twice (1 fail + 1 success)
            assert mock_acompletion.call_count == 2

    @pytest.mark.asyncio
    async def test_schema_retries_exhausted_triggers_fallback(self) -> None:
        """After max_schema_retries exhausted, fallback is tried (AC: #4)."""
        config = LLMConfig(
            default_provider="ollama",
            fallback_provider="anthropic",
            max_retries=1,
            max_schema_retries=2,
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

        # Primary fails twice with invalid JSON (exhausts schema retries), fallback succeeds
        mock_response_invalid = MagicMock()
        mock_response_invalid.choices = [MagicMock(message=MagicMock(content="not json"))]

        mock_response_valid = MagicMock()
        mock_response_valid.choices = [MagicMock(message=MagicMock(content='{"message": "Fallback", "score": 42}'))]

        with (
            patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
        ):
            # 2 fails on primary (exhaust schema retries), 1 success on fallback
            mock_acompletion.side_effect = [
                mock_response_invalid,
                mock_response_invalid,
                mock_response_valid,
            ]

            result = await client.complete_structured_with_cascade(
                "router",
                [{"role": "user", "content": "Hi"}],
                response_model=SampleResponse,
                allow_degradation=False,
            )

            assert isinstance(result, SampleResponse)
            assert result.message == "Fallback"
            # Primary called twice (exhaust retries) + fallback once
            assert mock_acompletion.call_count == 3

    @pytest.mark.asyncio
    async def test_schema_retries_separate_from_connection_retries(self) -> None:
        """Schema retries are separate from connection retries (AC: #5)."""
        config = LLMConfig(
            default_provider="anthropic",
            max_retries=3,  # Connection retries
            max_schema_retries=2,  # Schema retries
            base_retry_delay=0.01,
            providers={"anthropic": ProviderConfig(api_key="anthropic_key")},
            tiers={"low": TierModels(anthropic="claude-3-haiku-20240307")},
            agents={"router": AgentConfig(tier="low")},
        )
        client = LLMClient(config)

        # First call returns invalid JSON (triggers schema retry counter)
        # Second call succeeds
        mock_response_invalid = MagicMock()
        mock_response_invalid.choices = [MagicMock(message=MagicMock(content="invalid"))]

        mock_response_valid = MagicMock()
        mock_response_valid.choices = [MagicMock(message=MagicMock(content='{"message": "Hi", "score": 1}'))]

        with (
            patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_acompletion.side_effect = [mock_response_invalid, mock_response_valid]

            result = await client.complete_structured_with_cascade(
                "router",
                [{"role": "user", "content": "Hi"}],
                response_model=SampleResponse,
                allow_degradation=False,
            )

            assert isinstance(result, SampleResponse)
            # Should succeed on second call (schema retry worked)
            assert mock_acompletion.call_count == 2

    @pytest.mark.asyncio
    async def test_schema_retries_disabled_when_zero(self) -> None:
        """Schema retries disabled when max_schema_retries=0, immediately trigger fallback."""
        config = LLMConfig(
            default_provider="ollama",
            fallback_provider="anthropic",
            max_retries=1,
            max_schema_retries=0,  # Disabled
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

        # Primary fails with invalid JSON, immediately goes to fallback
        mock_response_invalid = MagicMock()
        mock_response_invalid.choices = [MagicMock(message=MagicMock(content="not json"))]

        mock_response_valid = MagicMock()
        mock_response_valid.choices = [MagicMock(message=MagicMock(content='{"message": "Fallback", "score": 1}'))]

        with (
            patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
        ):
            # 1 fail on primary (no schema retries), 1 success on fallback
            mock_acompletion.side_effect = [mock_response_invalid, mock_response_valid]

            result = await client.complete_structured_with_cascade(
                "router",
                [{"role": "user", "content": "Hi"}],
                response_model=SampleResponse,
                allow_degradation=False,
            )

            assert isinstance(result, SampleResponse)
            assert result.message == "Fallback"
            # Primary once (no retry) + fallback once
            assert mock_acompletion.call_count == 2


class TestIsSchemaError:
    """Test LLMClient._is_schema_error method."""

    def test_detects_json_decode_error(self) -> None:
        """Detects json.JSONDecodeError as schema error."""
        import json as json_module

        config = create_test_config()
        client = LLMClient(config)

        error = json_module.JSONDecodeError("Expecting value", "", 0)
        assert client._is_schema_error(error) is True  # pyright: ignore[reportPrivateUsage]

    def test_detects_validation_error(self) -> None:
        """Detects pydantic ValidationError as schema error."""
        from pydantic import ValidationError as PydanticValidationError

        config = create_test_config()
        client = LLMClient(config)

        try:
            SampleResponse(message="hi", score="not_an_int")  # type: ignore[arg-type]
        except PydanticValidationError as error:
            assert client._is_schema_error(error) is True  # pyright: ignore[reportPrivateUsage]

    def test_detects_schema_validation_valueerror(self) -> None:
        """Detects ValueError with 'schema validation' message as schema error."""
        config = create_test_config()
        client = LLMClient(config)

        error = ValueError("LLM response failed schema validation for SampleResponse")
        assert client._is_schema_error(error) is True  # pyright: ignore[reportPrivateUsage]

    def test_detects_validation_error_valueerror(self) -> None:
        """Detects ValueError with 'validation error' message as schema error."""
        config = create_test_config()
        client = LLMClient(config)

        error = ValueError("Validation error in response")
        assert client._is_schema_error(error) is True  # pyright: ignore[reportPrivateUsage]

    def test_rejects_other_errors(self) -> None:
        """Does not detect unrelated errors as schema errors."""
        config = create_test_config()
        client = LLMClient(config)

        error = RuntimeError("Connection timeout")
        assert client._is_schema_error(error) is False  # pyright: ignore[reportPrivateUsage]

        error2 = ValueError("Some other value error")
        assert client._is_schema_error(error2) is False  # pyright: ignore[reportPrivateUsage]


class TestSchemaRetryLogging:
    """Test logging for schema retry behavior (Task 8.5)."""

    @pytest.mark.asyncio
    async def test_schema_retry_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Logging shows schema retry attempts distinctly from connection retries."""
        import logging

        config = LLMConfig(
            default_provider="anthropic",
            max_retries=3,
            max_schema_retries=2,
            base_retry_delay=0.01,
            providers={"anthropic": ProviderConfig(api_key="anthropic_key")},
            tiers={"low": TierModels(anthropic="claude-3-haiku-20240307")},
            agents={"router": AgentConfig(tier="low")},
        )
        client = LLMClient(config)

        # First call fails with invalid JSON, second succeeds
        mock_response_invalid = MagicMock()
        mock_response_invalid.choices = [MagicMock(message=MagicMock(content="not valid json"))]

        mock_response_valid = MagicMock()
        mock_response_valid.choices = [MagicMock(message=MagicMock(content='{"message": "Hi", "score": 1}'))]

        with (
            patch("quilto.llm.client.litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
            patch("quilto.llm.client.asyncio.sleep", new_callable=AsyncMock),
            caplog.at_level(logging.WARNING, logger="quilto.llm.client"),
        ):
            mock_acompletion.side_effect = [mock_response_invalid, mock_response_valid]

            await client.complete_structured_with_cascade(
                "router",
                [{"role": "user", "content": "Hi"}],
                response_model=SampleResponse,
                allow_degradation=False,
            )

            # Should log schema retry warning
            assert any("Schema error" in record.message for record in caplog.records)
            assert any("retry" in record.message.lower() for record in caplog.records)
