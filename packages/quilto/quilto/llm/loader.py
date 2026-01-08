"""LLM configuration loader for Quilto framework.

This module provides functions to load LLM configuration from
YAML files or dictionaries with environment variable interpolation.
"""

from pathlib import Path
from typing import Any

import yaml

from quilto.llm.config import LLMConfig


def load_llm_config(config_path: Path) -> LLMConfig:
    """Load LLM configuration from a YAML file.

    Reads the YAML file, interpolates environment variables in
    API key values, and validates with Pydantic.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Validated LLMConfig instance.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If YAML parsing fails.
        pydantic.ValidationError: If config validation fails.
        ValueError: If environment variable interpolation fails.

    Example:
        >>> config = load_llm_config(Path("config.yaml"))
        >>> config.default_provider
        'ollama'
    """
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)

    # Handle nested llm key if present
    if "llm" in config_dict:
        config_dict = config_dict["llm"]

    return load_llm_config_from_dict(config_dict)


def load_llm_config_from_dict(config_dict: dict[str, Any]) -> LLMConfig:
    """Load LLM configuration from a dictionary.

    For programmatic configuration without a YAML file.
    Environment variable interpolation happens during Pydantic
    validation for api_key fields.

    Args:
        config_dict: Configuration dictionary matching LLMConfig schema.

    Returns:
        Validated LLMConfig instance.

    Raises:
        pydantic.ValidationError: If config validation fails.
        ValueError: If environment variable interpolation fails.

    Example:
        >>> config = load_llm_config_from_dict({
        ...     "default_provider": "ollama",
        ...     "providers": {
        ...         "ollama": {"api_base": "http://localhost:11434"}
        ...     }
        ... })
    """
    return LLMConfig.model_validate(config_dict)
