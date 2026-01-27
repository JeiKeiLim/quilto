"""Common CLI utilities for async handling, config loading, and exit codes."""

import asyncio
from collections.abc import Callable, Coroutine
from functools import wraps
from pathlib import Path
from typing import Any

from quilto import DomainModule, LLMClient, StorageRepository
from quilto.llm import LLMConfig, load_llm_config

from swealog.domains import general_fitness, nutrition, running, strength, swimming

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE_ERROR = 2


def run_async[T, **P](func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, T]:
    """Decorator to run async function in sync context for Typer commands.

    Args:
        func: An async function to wrap.

    Returns:
        A sync wrapper that runs the async function in an event loop.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def load_cli_config(config_path: Path | None = None) -> LLMConfig:
    """Load LLM configuration from file.

    Args:
        config_path: Path to config file. Defaults to ./llm-config.yaml

    Returns:
        Loaded LLMConfig instance.
    """
    if config_path is None:
        config_path = Path("llm-config.yaml")
    return load_llm_config(config_path)


def resolve_storage_path(storage_path: Path | None = None) -> Path:
    """Resolve storage base directory path.

    Args:
        storage_path: Explicit base path. Defaults to current directory.
            StorageRepository will create logs/ subdirectories automatically.

    Returns:
        Resolved base Path for StorageRepository.
    """
    if storage_path is None:
        storage_path = Path(".")
    return storage_path


def get_dependencies(
    config_path: Path | None = None,
    storage_path: Path | None = None,
) -> tuple[LLMClient, StorageRepository, list[DomainModule]]:
    """Initialize shared CLI dependencies.

    Args:
        config_path: Optional path to llm-config.yaml.
        storage_path: Optional path to storage directory.

    Returns:
        Tuple of (LLMClient, StorageRepository, list of domains).
    """
    config = load_cli_config(config_path)
    llm_client = LLMClient(config)
    storage = StorageRepository(resolve_storage_path(storage_path))
    domains: list[DomainModule] = [general_fitness, strength, nutrition, running, swimming]
    return llm_client, storage, domains
