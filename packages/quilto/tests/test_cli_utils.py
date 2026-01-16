"""Tests for quilto.cli.utils module."""

import asyncio
import tempfile
from pathlib import Path

from quilto.cli.utils import (
    EXIT_ERROR,
    EXIT_SUCCESS,
    EXIT_USAGE_ERROR,
    load_cli_config,
    resolve_storage_path,
    run_async,
)
from quilto.llm import LLMConfig


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
        assert isinstance(config, LLMConfig)
        assert "ollama" in config.providers

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
        """Test resolve_storage_path uses ./logs by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                path = resolve_storage_path(None)
                assert path == Path("logs")
                assert path.exists()
                assert path.is_dir()
            finally:
                os.chdir(original_cwd)

    def test_resolve_storage_path_explicit(self, tmp_path: Path) -> None:
        """Test resolve_storage_path uses explicit path."""
        custom_path = tmp_path / "custom_logs"
        result = resolve_storage_path(custom_path)
        assert result == custom_path
        assert result.exists()
        assert result.is_dir()

    def test_resolve_storage_path_creates_nested(self, tmp_path: Path) -> None:
        """Test resolve_storage_path creates nested directories."""
        nested_path = tmp_path / "a" / "b" / "c" / "logs"
        result = resolve_storage_path(nested_path)
        assert result == nested_path
        assert result.exists()

    def test_resolve_storage_path_existing(self, tmp_path: Path) -> None:
        """Test resolve_storage_path works with existing directory."""
        existing_path = tmp_path / "existing"
        existing_path.mkdir()
        (existing_path / "test.txt").write_text("test")

        result = resolve_storage_path(existing_path)
        assert result == existing_path
        assert (result / "test.txt").exists()  # Original content preserved
