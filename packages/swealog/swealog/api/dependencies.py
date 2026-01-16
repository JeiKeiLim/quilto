"""FastAPI dependency injection for LLM client, storage, and domains."""

from functools import lru_cache
from pathlib import Path

from quilto import DomainModule, LLMClient, LLMConfig, StorageRepository, load_llm_config

from swealog.domains import (
    general_fitness,
    nutrition,
    running,
    strength,
    swimming,
)


class ConfigNotFoundError(Exception):
    """Raised when LLM configuration file is not found."""


@lru_cache
def get_llm_config() -> LLMConfig:
    """Load LLM configuration (cached).

    Returns:
        Loaded LLMConfig instance.

    Raises:
        ConfigNotFoundError: If config file does not exist.
    """
    config_path = Path("llm-config.yaml")
    if not config_path.exists():
        raise ConfigNotFoundError(f"LLM config not found: {config_path}")
    return load_llm_config(config_path)


def get_llm_client() -> LLMClient:
    """Get LLM client instance.

    Returns:
        Configured LLMClient.
    """
    config = get_llm_config()
    return LLMClient(config)


def get_storage() -> StorageRepository:
    """Get storage repository instance.

    Returns:
        StorageRepository configured with ./logs path.
    """
    storage_path = Path("logs")
    storage_path.mkdir(parents=True, exist_ok=True)
    return StorageRepository(base_path=storage_path)


def get_domains() -> list[DomainModule]:
    """Get all available domain modules.

    Returns:
        List of domain modules for fitness tracking.
    """
    return [
        general_fitness,
        strength,
        nutrition,
        running,
        swimming,
    ]
