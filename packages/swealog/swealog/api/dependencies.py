"""FastAPI dependency injection for LLM client, storage, and domains."""

from functools import lru_cache
from pathlib import Path

from quilto import (
    DomainModule,
    LLMClient,
    LLMConfig,
    ObserverTriggerConfig,
    Quilto,
    StorageRepository,
    load_llm_config,
)

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
        StorageRepository with base path at current directory.
        StorageRepository creates logs/ subdirectories automatically.
    """
    return StorageRepository(base_path=Path("."))


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


def create_quilto(
    llm_client: LLMClient | None = None,
    storage: StorageRepository | None = None,
    domains: list[DomainModule] | None = None,
    debug: bool = False,
) -> Quilto:
    """Create Quilto instance with correct domains for Swealog.

    Uses stateless in-memory session storage matching current per-request behavior.

    Args:
        llm_client: LLM client. Uses get_llm_client() if not provided.
        storage: Storage repository. Uses get_storage() if not provided.
        domains: Domain modules. Uses get_domains() if not provided.
        debug: Enable debug mode with traces.

    Returns:
        Configured Quilto instance.
    """
    return Quilto(
        llm_client=llm_client or get_llm_client(),
        storage=storage or get_storage(),
        domains=domains or get_domains(),
        observer_config=ObserverTriggerConfig(enable_post_query=True),
        session_db_path=":memory:",  # Stateless per-request
        debug=debug,
    )
