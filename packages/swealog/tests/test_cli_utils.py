"""Tests for swealog.cli.utils module."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

from quilto import DomainModule, LLMClient, StorageRepository
from quilto.config import QuiltoConfig
from swealog.cli.utils import (
    EXIT_ERROR,
    EXIT_SUCCESS,
    EXIT_USAGE_ERROR,
    get_dependencies,
    load_cli_config,
    resolve_storage_path,
    run_async,
)


class TestExitCodes:
    """Tests for exit code constants."""

    def test_exit_success(self) -> None:
        """Test EXIT_SUCCESS is 0."""
        assert EXIT_SUCCESS == 0

    def test_exit_error(self) -> None:
        """Test EXIT_ERROR is 1."""
        assert EXIT_ERROR == 1

    def test_exit_usage_error(self) -> None:
        """Test EXIT_USAGE_ERROR is 2."""
        assert EXIT_USAGE_ERROR == 2


class TestRunAsync:
    """Tests for run_async decorator."""

    def test_run_async_basic(self) -> None:
        """Test run_async runs async function synchronously."""

        @run_async
        async def async_func() -> str:
            return "result"

        result = async_func()
        assert result == "result"

    def test_run_async_with_args(self) -> None:
        """Test run_async passes arguments correctly."""

        @run_async
        async def async_func_with_args(x: int, y: str) -> str:
            return f"{x}-{y}"

        result = async_func_with_args(42, "test")
        assert result == "42-test"

    def test_run_async_with_kwargs(self) -> None:
        """Test run_async passes kwargs correctly."""

        @run_async
        async def async_func_with_kwargs(*, name: str = "default") -> str:
            return name

        result = async_func_with_kwargs(name="custom")
        assert result == "custom"

    def test_run_async_preserves_docstring(self) -> None:
        """Test run_async preserves function docstring."""

        @run_async
        async def documented_func() -> None:
            """Original docstring."""

        assert documented_func.__doc__ == "Original docstring."

    def test_run_async_with_await(self) -> None:
        """Test run_async handles actual async operations."""

        @run_async
        async def async_with_await() -> str:
            await asyncio.sleep(0.001)
            return "awaited"

        result = async_with_await()
        assert result == "awaited"


class TestLoadCliConfig:
    """Tests for load_cli_config function."""

    def test_load_cli_config_with_path(self, tmp_path: Path) -> None:
        """Test load_cli_config loads from specified path."""
        config_path = tmp_path / "llm-config.yaml"
        # Use the correct schema matching llm-config.yaml
        config_content = """
default_provider: ollama

providers:
  ollama:
    api_base: http://localhost:11434

agents:
  router:
    tier: low

tiers:
  low:
    ollama: qwen2.5:7b
  medium:
    ollama: qwen2.5:7b
  high:
    ollama: qwen2.5:7b
"""
        config_path.write_text(config_content)

        config = load_cli_config(config_path)
        assert isinstance(config, QuiltoConfig)
        assert "ollama" in config.llm.providers

    def test_load_cli_config_default_path(self) -> None:
        """Test load_cli_config uses default path when none specified."""
        import contextlib

        # This test just checks the function doesn't crash without a path
        # The actual file may or may not exist
        with contextlib.suppress(FileNotFoundError):
            load_cli_config(None)


class TestResolveStoragePath:
    """Tests for resolve_storage_path function."""

    def test_resolve_storage_path_default(self) -> None:
        """Test resolve_storage_path uses current directory by default."""
        path = resolve_storage_path(None)
        assert path == Path(".")

    def test_resolve_storage_path_explicit(self, tmp_path: Path) -> None:
        """Test resolve_storage_path uses explicit path."""
        custom_path = tmp_path / "custom_logs"
        result = resolve_storage_path(custom_path)
        assert result == custom_path

    def test_resolve_storage_path_existing(self, tmp_path: Path) -> None:
        """Test resolve_storage_path returns path as-is."""
        existing_path = tmp_path / "existing"
        result = resolve_storage_path(existing_path)
        assert result == existing_path


class TestGetDependencies:
    """Tests for get_dependencies helper function."""

    def test_get_dependencies_returns_tuple(self, tmp_path: Path) -> None:
        """Test get_dependencies returns correct tuple structure."""
        config_path = tmp_path / "llm-config.yaml"
        config_content = """
default_provider: ollama
providers:
  ollama:
    api_base: http://localhost:11434
tiers:
  low:
    ollama: qwen2.5:7b
  medium:
    ollama: qwen2.5:7b
  high:
    ollama: qwen2.5:7b
"""
        config_path.write_text(config_content)
        storage_path = tmp_path / "logs"

        llm_client, storage, domains, config = get_dependencies(config_path, storage_path)

        assert isinstance(llm_client, LLMClient)
        assert isinstance(storage, StorageRepository)
        assert isinstance(domains, list)
        assert len(domains) == 5  # 5 fitness domains
        assert all(isinstance(d, DomainModule) for d in domains)
        assert isinstance(config, QuiltoConfig)

    def test_get_dependencies_creates_storage_subdirectories(self, tmp_path: Path) -> None:
        """Test get_dependencies creates logs subdirectories via StorageRepository."""
        config_path = tmp_path / "llm-config.yaml"
        config_content = """
default_provider: ollama
providers:
  ollama:
    api_base: http://localhost:11434
tiers:
  low:
    ollama: qwen2.5:7b
  medium:
    ollama: qwen2.5:7b
  high:
    ollama: qwen2.5:7b
"""
        config_path.write_text(config_content)
        storage_path = tmp_path

        _llm_client, storage, _domains, _config = get_dependencies(config_path, storage_path)

        # StorageRepository creates subdirectories directly under base_path
        assert (storage.base_path / "raw").exists()
        assert (storage.base_path / "parsed").exists()
        assert (storage.base_path / "context").exists()

    def test_get_dependencies_returns_all_five_domains(self, tmp_path: Path) -> None:
        """Test get_dependencies returns all 5 fitness domains."""
        config_path = tmp_path / "llm-config.yaml"
        config_content = """
default_provider: ollama
providers:
  ollama:
    api_base: http://localhost:11434
tiers:
  low:
    ollama: qwen2.5:7b
  medium:
    ollama: qwen2.5:7b
  high:
    ollama: qwen2.5:7b
"""
        config_path.write_text(config_content)
        storage_path = tmp_path / "logs"

        _llm_client, _storage, domains, _config = get_dependencies(config_path, storage_path)

        domain_names = {d.name for d in domains}
        expected_names = {"GeneralFitness", "Strength", "Nutrition", "Running", "Swimming"}
        assert domain_names == expected_names

    def test_get_dependencies_uses_default_storage_path(self) -> None:
        """Test get_dependencies uses default storage path when None."""
        with (
            patch("swealog.cli.utils.load_cli_config") as mock_load,
            patch("swealog.cli.utils.LLMClient"),
            patch("swealog.cli.utils.StorageRepository"),
            patch("swealog.cli.utils.resolve_storage_path") as mock_resolve,
        ):
            mock_config = MagicMock()
            mock_config.llm = MagicMock()  # QuiltoConfig has .llm attribute
            mock_load.return_value = mock_config
            mock_resolve.return_value = Path(".")

            get_dependencies(config_path=Path("test.yaml"), storage_path=None)

            mock_resolve.assert_called_once_with(None)
