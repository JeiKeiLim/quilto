"""LLM configuration models for Quilto framework.

This module defines Pydantic models for configuring LLM providers,
tier-based model selection, and per-agent settings.
"""

import os
import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

ProviderName = Literal["ollama", "anthropic", "openai", "azure", "openrouter"]
TierName = Literal["low", "medium", "high"]


def interpolate_env_vars(value: str) -> str:
    """Interpolate environment variables in a string.

    Replaces ${VAR_NAME} patterns with the corresponding environment
    variable value.

    Args:
        value: String potentially containing ${VAR_NAME} patterns.

    Returns:
        String with environment variables interpolated.

    Raises:
        ValueError: If referenced environment variable is not set.
    """
    pattern = r"\$\{([^}]+)\}"
    matches = re.findall(pattern, value)
    result = value
    for var_name in matches:
        env_value = os.environ.get(var_name)
        if env_value is None:
            raise ValueError(f"Environment variable {var_name} is not set")
        result = result.replace(f"${{{var_name}}}", env_value)
    return result


class ProviderConfig(BaseModel):
    """Provider-specific settings.

    Attributes:
        api_key: API key for the provider. Supports ${ENV_VAR} interpolation.
        api_base: Base URL for API calls. Required for Ollama and Azure.
        api_version: API version. Required for Azure.
    """

    model_config = ConfigDict(extra="forbid")

    api_key: str | None = None
    api_base: str | None = None
    api_version: str | None = None

    @field_validator("api_key", mode="after")
    @classmethod
    def interpolate_api_key(cls, v: str | None) -> str | None:
        """Interpolate environment variables in api_key.

        Args:
            v: The api_key value.

        Returns:
            The interpolated api_key value.
        """
        if v is None:
            return None
        if "${" in v:
            return interpolate_env_vars(v)
        return v


class TierModels(BaseModel):
    """Model mappings for a single tier across all providers.

    Each field specifies the model name to use for that provider
    at this tier level.

    Attributes:
        ollama: Ollama model name (e.g., "qwen2.5:7b").
        anthropic: Anthropic model name (e.g., "claude-3-haiku-20240307").
        openai: OpenAI model name (e.g., "gpt-4o-mini").
        azure: Azure deployment name (e.g., "gpt-4o-mini-deployment").
        openrouter: OpenRouter model path (e.g., "anthropic/claude-3-haiku").
    """

    model_config = ConfigDict(extra="forbid")

    ollama: str | None = None
    anthropic: str | None = None
    openai: str | None = None
    azure: str | None = None
    openrouter: str | None = None


class AgentConfig(BaseModel):
    """Per-agent tier and optional provider override.

    Attributes:
        tier: Model tier to use for this agent.
        provider: Optional provider override. If set, uses this provider
            instead of the default.
    """

    model_config = ConfigDict(extra="forbid")

    tier: TierName = "medium"
    provider: ProviderName | None = None


@dataclass
class ModelResolution:
    """Result of resolving a model for an agent.

    Attributes:
        provider: The resolved provider name.
        model: The raw model name from tier config.
        litellm_model: The model name formatted for litellm (with prefix).
        api_base: API base URL if applicable.
        api_key: API key if applicable.
    """

    provider: ProviderName
    model: str
    litellm_model: str
    api_base: str | None
    api_key: str | None


# Default tier models based on architecture spec
DEFAULT_TIER_MODELS: dict[TierName, TierModels] = {
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
}

# Default agent tier assignments based on architecture spec
DEFAULT_AGENT_CONFIGS: dict[str, AgentConfig] = {
    "router": AgentConfig(tier="low"),
    "retriever": AgentConfig(tier="low"),
    "parser": AgentConfig(tier="medium"),
    "clarifier": AgentConfig(tier="medium"),
    "planner": AgentConfig(tier="high"),
    "synthesizer": AgentConfig(tier="medium"),
    "evaluator": AgentConfig(tier="high"),
    "analyzer": AgentConfig(tier="high"),
    "observer": AgentConfig(tier="medium"),
}


class LLMConfig(BaseModel):
    """Root LLM configuration.

    Configures default provider, fallback, provider credentials,
    tier-based model selection, per-agent settings, and error cascade options.

    Attributes:
        default_provider: Provider to use by default.
        fallback_provider: Provider to use on errors (if configured).
        providers: Provider-specific configurations keyed by provider name.
        tiers: Model mappings per tier (low, medium, high).
        agents: Per-agent configuration keyed by agent name.
        max_retries: Maximum retry attempts per provider for transient errors.
        base_retry_delay: Base delay in seconds for exponential backoff.
        enable_graceful_degradation: If True, return PartialResult instead of
            raising when all providers fail.
    """

    model_config = ConfigDict(extra="forbid")

    default_provider: ProviderName = "ollama"
    fallback_provider: ProviderName | None = None
    providers: dict[ProviderName, ProviderConfig] = {}
    tiers: dict[TierName, TierModels] = {}
    agents: dict[str, AgentConfig] = {}
    max_retries: int = 3
    base_retry_delay: float = 1.0
    enable_graceful_degradation: bool = True

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max_retries is non-negative.

        Args:
            v: The max_retries value.

        Returns:
            The validated max_retries value.

        Raises:
            ValueError: If max_retries is negative.
        """
        if v < 0:
            raise ValueError("max_retries must be >= 0")
        return v

    @field_validator("base_retry_delay")
    @classmethod
    def validate_base_retry_delay(cls, v: float) -> float:
        """Validate base_retry_delay is positive.

        Args:
            v: The base_retry_delay value.

        Returns:
            The validated base_retry_delay value.

        Raises:
            ValueError: If base_retry_delay is not positive.
        """
        if v <= 0:
            raise ValueError("base_retry_delay must be > 0")
        return v

    @model_validator(mode="after")
    def apply_defaults_and_validate(self) -> "LLMConfig":
        """Apply default tier models, agent configs, and validate provider references.

        Returns:
            Self with defaults applied for missing tiers and agents.

        Raises:
            ValueError: If fallback_provider is set but not configured in providers.
        """
        # Apply default tier models for missing tiers
        for tier_name, default_models in DEFAULT_TIER_MODELS.items():
            if tier_name not in self.tiers:
                self.tiers[tier_name] = default_models

        # Apply default agent configs for missing agents
        for agent_name, default_config in DEFAULT_AGENT_CONFIGS.items():
            if agent_name not in self.agents:
                self.agents[agent_name] = default_config

        # Validate fallback_provider is configured if set
        if self.fallback_provider and self.fallback_provider not in self.providers:
            raise ValueError(
                f"fallback_provider '{self.fallback_provider}' is not configured in providers. "
                f"Configured providers: {list(self.providers.keys())}"
            )

        return self
