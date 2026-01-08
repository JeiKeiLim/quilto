"""Unit tests for LLM configuration models."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from quilto.llm.config import (
    DEFAULT_AGENT_CONFIGS,
    DEFAULT_TIER_MODELS,
    AgentConfig,
    LLMConfig,
    ModelResolution,
    ProviderConfig,
    TierModels,
    interpolate_env_vars,
)
from quilto.llm.loader import load_llm_config, load_llm_config_from_dict


class TestInterpolateEnvVars:
    """Test environment variable interpolation."""

    def test_interpolates_single_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Single environment variable is interpolated."""
        monkeypatch.setenv("TEST_KEY", "secret123")
        result = interpolate_env_vars("${TEST_KEY}")
        assert result == "secret123"

    def test_interpolates_multiple_vars(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Multiple environment variables are interpolated."""
        monkeypatch.setenv("VAR1", "hello")
        monkeypatch.setenv("VAR2", "world")
        result = interpolate_env_vars("${VAR1} ${VAR2}")
        assert result == "hello world"

    def test_preserves_text_without_vars(self) -> None:
        """Text without variables is preserved."""
        result = interpolate_env_vars("plain text")
        assert result == "plain text"

    def test_raises_on_missing_var(self) -> None:
        """Raises ValueError for missing environment variable."""
        with pytest.raises(ValueError, match="NONEXISTENT_VAR is not set"):
            interpolate_env_vars("${NONEXISTENT_VAR}")


class TestProviderConfig:
    """Test ProviderConfig model."""

    def test_accepts_all_optional_fields(self) -> None:
        """ProviderConfig accepts all fields as optional."""
        config = ProviderConfig()
        assert config.api_key is None
        assert config.api_base is None
        assert config.api_version is None

    def test_accepts_all_fields(self) -> None:
        """ProviderConfig accepts all fields."""
        config = ProviderConfig(
            api_key="key123",
            api_base="https://api.example.com",
            api_version="2024-01-01",
        )
        assert config.api_key == "key123"
        assert config.api_base == "https://api.example.com"
        assert config.api_version == "2024-01-01"

    def test_interpolates_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API key with ${VAR} is interpolated from environment."""
        monkeypatch.setenv("MY_API_KEY", "secret_value")
        config = ProviderConfig(api_key="${MY_API_KEY}")
        assert config.api_key == "secret_value"

    def test_raises_on_missing_env_var(self) -> None:
        """Raises ValueError when referenced env var is not set."""
        with pytest.raises(ValidationError) as exc_info:
            ProviderConfig(api_key="${MISSING_KEY}")
        assert "MISSING_KEY is not set" in str(exc_info.value)


class TestTierModels:
    """Test TierModels model."""

    def test_accepts_all_providers(self) -> None:
        """TierModels accepts models for all providers."""
        tier = TierModels(
            ollama="qwen2.5:7b",
            anthropic="claude-3-haiku-20240307",
            openai="gpt-4o-mini",
            azure="gpt-4o-mini-deployment",
            openrouter="anthropic/claude-3-haiku",
        )
        assert tier.ollama == "qwen2.5:7b"
        assert tier.anthropic == "claude-3-haiku-20240307"
        assert tier.openai == "gpt-4o-mini"
        assert tier.azure == "gpt-4o-mini-deployment"
        assert tier.openrouter == "anthropic/claude-3-haiku"

    def test_all_fields_optional(self) -> None:
        """All TierModels fields are optional."""
        tier = TierModels()
        assert tier.ollama is None
        assert tier.anthropic is None
        assert tier.openai is None
        assert tier.azure is None
        assert tier.openrouter is None


class TestAgentConfig:
    """Test AgentConfig model."""

    def test_defaults_to_medium_tier(self) -> None:
        """AgentConfig defaults to medium tier."""
        config = AgentConfig()
        assert config.tier == "medium"
        assert config.provider is None

    def test_accepts_tier_override(self) -> None:
        """AgentConfig accepts tier override."""
        config = AgentConfig(tier="high")
        assert config.tier == "high"

    def test_accepts_provider_override(self) -> None:
        """AgentConfig accepts provider override."""
        config = AgentConfig(tier="high", provider="anthropic")
        assert config.tier == "high"
        assert config.provider == "anthropic"

    def test_rejects_invalid_tier(self) -> None:
        """AgentConfig rejects invalid tier values."""
        with pytest.raises(ValidationError):
            AgentConfig(tier="invalid")  # type: ignore[arg-type]

    def test_rejects_invalid_provider(self) -> None:
        """AgentConfig rejects invalid provider values."""
        with pytest.raises(ValidationError):
            AgentConfig(provider="invalid")  # type: ignore[arg-type]


class TestModelResolution:
    """Test ModelResolution dataclass."""

    def test_stores_all_fields(self) -> None:
        """ModelResolution stores all fields correctly."""
        resolution = ModelResolution(
            provider="anthropic",
            model="claude-3-haiku-20240307",
            litellm_model="claude-3-haiku-20240307",
            api_base=None,
            api_key="key123",
        )
        assert resolution.provider == "anthropic"
        assert resolution.model == "claude-3-haiku-20240307"
        assert resolution.litellm_model == "claude-3-haiku-20240307"
        assert resolution.api_base is None
        assert resolution.api_key == "key123"


class TestLLMConfig:
    """Test LLMConfig model."""

    def test_defaults(self) -> None:
        """LLMConfig has sensible defaults."""
        config = LLMConfig()
        assert config.default_provider == "ollama"
        assert config.fallback_provider is None
        assert config.providers == {}

    def test_applies_default_tiers(self) -> None:
        """LLMConfig applies default tier models."""
        config = LLMConfig()
        assert "low" in config.tiers
        assert "medium" in config.tiers
        assert "high" in config.tiers
        assert config.tiers["low"].ollama == DEFAULT_TIER_MODELS["low"].ollama

    def test_applies_default_agents(self) -> None:
        """LLMConfig applies default agent configs."""
        config = LLMConfig()
        assert "router" in config.agents
        assert "analyzer" in config.agents
        assert config.agents["router"].tier == "low"
        assert config.agents["analyzer"].tier == "high"

    def test_custom_tiers_override_defaults(self) -> None:
        """Custom tier config overrides defaults."""
        custom_tier = TierModels(ollama="custom:model")
        config = LLMConfig(tiers={"low": custom_tier})
        assert config.tiers["low"].ollama == "custom:model"
        # medium and high still get defaults
        assert config.tiers["medium"].ollama == DEFAULT_TIER_MODELS["medium"].ollama

    def test_custom_agents_override_defaults(self) -> None:
        """Custom agent config overrides defaults."""
        custom_agent = AgentConfig(tier="low", provider="anthropic")
        config = LLMConfig(agents={"analyzer": custom_agent})
        assert config.agents["analyzer"].tier == "low"
        assert config.agents["analyzer"].provider == "anthropic"
        # Other agents still get defaults
        assert config.agents["router"].tier == "low"

    def test_accepts_all_providers(self) -> None:
        """LLMConfig accepts all provider types."""
        config = LLMConfig(
            default_provider="anthropic",
            fallback_provider="openai",
            providers={
                "ollama": ProviderConfig(api_base="http://localhost:11434"),
                "anthropic": ProviderConfig(api_key="key1"),
                "openai": ProviderConfig(api_key="key2"),
                "azure": ProviderConfig(api_key="key3", api_base="https://azure.com"),
                "openrouter": ProviderConfig(api_key="key4"),
            },
        )
        assert config.default_provider == "anthropic"
        assert len(config.providers) == 5

    def test_rejects_unconfigured_fallback_provider(self) -> None:
        """LLMConfig rejects fallback_provider not in providers."""
        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(
                default_provider="ollama",
                fallback_provider="anthropic",
                providers={"ollama": ProviderConfig(api_base="http://localhost:11434")},
            )
        assert "fallback_provider 'anthropic' is not configured" in str(exc_info.value)


class TestLoadLLMConfigFromDict:
    """Test load_llm_config_from_dict function."""

    def test_loads_minimal_config(self) -> None:
        """Loads minimal config with defaults applied."""
        config = load_llm_config_from_dict({})
        assert config.default_provider == "ollama"
        assert "low" in config.tiers
        assert "router" in config.agents

    def test_loads_full_config(self) -> None:
        """Loads full config from dict."""
        config = load_llm_config_from_dict(
            {
                "default_provider": "anthropic",
                "fallback_provider": "openai",
                "providers": {
                    "anthropic": {"api_key": "test_key"},
                    "openai": {"api_key": "openai_key"},
                },
                "tiers": {
                    "low": {"anthropic": "claude-3-haiku"},
                },
                "agents": {
                    "custom_agent": {"tier": "high"},
                },
            }
        )
        assert config.default_provider == "anthropic"
        assert config.fallback_provider == "openai"
        assert config.providers["anthropic"].api_key == "test_key"
        assert config.providers["openai"].api_key == "openai_key"
        assert config.tiers["low"].anthropic == "claude-3-haiku"
        assert config.agents["custom_agent"].tier == "high"


class TestLoadLLMConfig:
    """Test load_llm_config function."""

    def test_loads_yaml_file(self, tmp_path: Path) -> None:
        """Loads config from YAML file."""
        yaml_content = """
default_provider: anthropic
providers:
  anthropic:
    api_key: test_key
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)

        config = load_llm_config(config_file)
        assert config.default_provider == "anthropic"
        assert config.providers["anthropic"].api_key == "test_key"

    def test_loads_nested_llm_key(self, tmp_path: Path) -> None:
        """Loads config from nested 'llm' key in YAML."""
        yaml_content = """
llm:
  default_provider: openai
  providers:
    openai:
      api_key: openai_key
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)

        config = load_llm_config(config_file)
        assert config.default_provider == "openai"
        assert config.providers["openai"].api_key == "openai_key"

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_llm_config(tmp_path / "nonexistent.yaml")

    def test_interpolates_env_vars_in_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables in YAML are interpolated."""
        monkeypatch.setenv("TEST_ANTHROPIC_KEY", "secret_from_env")
        yaml_content = """
default_provider: anthropic
providers:
  anthropic:
    api_key: "${TEST_ANTHROPIC_KEY}"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)

        config = load_llm_config(config_file)
        assert config.providers["anthropic"].api_key == "secret_from_env"


class TestDefaultTierModels:
    """Test DEFAULT_TIER_MODELS constant."""

    def test_has_all_tiers(self) -> None:
        """DEFAULT_TIER_MODELS has all tier levels."""
        assert "low" in DEFAULT_TIER_MODELS
        assert "medium" in DEFAULT_TIER_MODELS
        assert "high" in DEFAULT_TIER_MODELS

    def test_low_tier_models(self) -> None:
        """Low tier has expected model values."""
        low = DEFAULT_TIER_MODELS["low"]
        assert low.ollama == "qwen2.5:7b"
        assert low.anthropic == "claude-3-haiku-20240307"
        assert low.openai == "gpt-4o-mini"

    def test_high_tier_models(self) -> None:
        """High tier has expected model values."""
        high = DEFAULT_TIER_MODELS["high"]
        assert high.ollama == "qwen2.5:32b"
        assert high.anthropic == "claude-sonnet-4-20250514"
        assert high.openai == "gpt-4o"


class TestDefaultAgentConfigs:
    """Test DEFAULT_AGENT_CONFIGS constant."""

    def test_has_all_agents(self) -> None:
        """DEFAULT_AGENT_CONFIGS has all expected agents."""
        expected_agents = [
            "router",
            "retriever",
            "parser",
            "clarifier",
            "planner",
            "synthesizer",
            "evaluator",
            "analyzer",
            "observer",
        ]
        for agent in expected_agents:
            assert agent in DEFAULT_AGENT_CONFIGS

    def test_agent_tiers(self) -> None:
        """Agents have correct tier assignments."""
        assert DEFAULT_AGENT_CONFIGS["router"].tier == "low"
        assert DEFAULT_AGENT_CONFIGS["parser"].tier == "medium"
        assert DEFAULT_AGENT_CONFIGS["analyzer"].tier == "high"
