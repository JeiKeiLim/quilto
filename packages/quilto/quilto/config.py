"""Unified configuration for Quilto framework.

This module provides a unified configuration model that combines LLM
and observability settings in one place, with graceful degradation
for missing or disabled features.
"""

import logging
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, field_validator

from quilto.llm.config import LLMConfig
from quilto.observability.langfuse import LangfuseProvider
from quilto.observability.noop import NoOpProvider
from quilto.observability.provider import ObservabilityProvider

logger = logging.getLogger(__name__)

ObservabilityProviderName = Literal["langfuse", "noop"]


class ObservabilityConfig(BaseModel):
    """Observability configuration.

    Attributes:
        enabled: Whether observability is active. Defaults to False.
        provider: Observability backend. Currently only "langfuse" supported.
        sample_rate: Trace sampling rate (0.0-1.0). Defaults to 1.0 (100%).
        public_key: Langfuse public key. Falls back to LANGFUSE_PUBLIC_KEY env var.
        secret_key: Langfuse secret key. Falls back to LANGFUSE_SECRET_KEY env var.
        host: Langfuse host URL. Falls back to LANGFUSE_BASE_URL env var.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    provider: ObservabilityProviderName = "langfuse"
    sample_rate: float = 1.0
    public_key: str | None = None
    secret_key: str | None = None
    host: str | None = None

    @field_validator("sample_rate")
    @classmethod
    def validate_sample_rate(cls, v: float) -> float:
        """Validate sample_rate is between 0.0 and 1.0.

        Args:
            v: The sample_rate value.

        Returns:
            The validated sample_rate value.

        Raises:
            ValueError: If sample_rate is not between 0.0 and 1.0.
        """
        if not 0.0 <= v <= 1.0:
            raise ValueError("sample_rate must be between 0.0 and 1.0")
        return v


class QuiltoConfig(BaseModel):
    """Unified Quilto configuration.

    Combines LLM and observability settings in one config object.

    Attributes:
        llm: LLM provider configuration.
        observability: Observability provider configuration.
    """

    model_config = ConfigDict(extra="forbid")

    llm: LLMConfig = LLMConfig()
    observability: ObservabilityConfig = ObservabilityConfig()


def load_config(config_path: Path) -> QuiltoConfig:
    """Load unified Quilto configuration from a YAML file.

    Reads the YAML file and parses both LLM and observability settings.
    Environment variables override config file values for Langfuse credentials.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Validated QuiltoConfig instance.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If YAML parsing fails.
        pydantic.ValidationError: If config validation fails.

    Example:
        >>> config = load_config(Path("config.yaml"))
        >>> config.llm.default_provider
        'ollama'
        >>> config.observability.enabled
        True
    """
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)

    # Handle empty YAML file (yaml.safe_load returns None)
    if config_dict is None:
        config_dict = {}

    return load_config_from_dict(config_dict)


def load_config_from_dict(config_dict: dict[str, Any]) -> QuiltoConfig:
    """Load unified Quilto configuration from a dictionary.

    For programmatic configuration without a YAML file.

    Supports both unified format (with llm: and observability: keys)
    and old LLM-only format for backward compatibility.

    Environment variables override config file values for Langfuse credentials:
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_SECRET_KEY
    - LANGFUSE_BASE_URL

    Args:
        config_dict: Configuration dictionary.

    Returns:
        Validated QuiltoConfig instance.

    Raises:
        pydantic.ValidationError: If config validation fails.

    Example:
        >>> config = load_config_from_dict({
        ...     "llm": {"default_provider": "ollama"},
        ...     "observability": {"enabled": True}
        ... })
    """
    # Detect format: unified (has "llm" key) or old LLM-only
    if "llm" in config_dict:
        # Unified format
        llm_dict = config_dict.get("llm", {})
        obs_dict = config_dict.get("observability", {})
    else:
        # Old LLM-only format - treat entire dict as LLM config
        llm_dict = config_dict
        obs_dict = {}

    # Apply environment variable overrides for observability
    obs_dict = _apply_env_overrides(obs_dict)

    # Build and validate config
    return QuiltoConfig(
        llm=LLMConfig.model_validate(llm_dict),
        observability=ObservabilityConfig.model_validate(obs_dict),
    )


def _apply_env_overrides(obs_dict: dict[str, Any]) -> dict[str, Any]:
    """Apply environment variable overrides to observability config.

    Environment variables take precedence over config file values.

    Args:
        obs_dict: Observability configuration dictionary.

    Returns:
        Updated dictionary with environment variable overrides applied.
    """
    result = dict(obs_dict)

    # Override with environment variables if present
    if env_public_key := os.getenv("LANGFUSE_PUBLIC_KEY"):
        result["public_key"] = env_public_key

    if env_secret_key := os.getenv("LANGFUSE_SECRET_KEY"):
        result["secret_key"] = env_secret_key

    if env_host := os.getenv("LANGFUSE_BASE_URL"):
        result["host"] = env_host

    return result


def create_observability_provider(config: ObservabilityConfig) -> ObservabilityProvider:
    """Create an observability provider from configuration.

    Returns the appropriate provider based on configuration:
    - NoOpProvider if observability is disabled
    - NoOpProvider if credentials are missing (with warning)
    - LangfuseProvider if enabled with valid credentials

    Args:
        config: Observability configuration.

    Returns:
        An ObservabilityProvider instance (LangfuseProvider or NoOpProvider).

    Example:
        >>> config = ObservabilityConfig(enabled=True)
        >>> provider = create_observability_provider(config)
        >>> provider.is_enabled()  # Depends on credentials
    """
    # Return NoOpProvider if disabled
    if not config.enabled:
        return NoOpProvider()

    # Check for credentials (from config or environment).
    # Note: load_config() already applies env vars to config, but we check again here
    # to support direct ObservabilityConfig construction without load_config().
    public_key = config.public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = config.secret_key or os.getenv("LANGFUSE_SECRET_KEY")
    host = config.host or os.getenv("LANGFUSE_BASE_URL")

    # Return NoOpProvider with warning if credentials missing
    if not public_key or not secret_key:
        logger.warning(
            "Observability enabled but Langfuse credentials missing. "
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables. "
            "Falling back to NoOpProvider."
        )
        return NoOpProvider()

    # Create LangfuseProvider with credentials
    return LangfuseProvider(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )
