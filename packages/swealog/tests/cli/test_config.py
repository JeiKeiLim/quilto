"""Unit tests for CLI configuration and observability integration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from quilto.config import QuiltoConfig
from quilto.observability.langfuse import LangfuseProvider
from quilto.observability.noop import NoOpProvider
from swealog.cli.utils import load_cli_config


class TestLoadCliConfig:
    """Tests for load_cli_config function."""

    def test_load_cli_config_returns_quilto_config(self, tmp_path: Path) -> None:
        """Test that CLI config loader returns QuiltoConfig with llm and observability."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
llm:
  default_provider: ollama
  providers:
    ollama:
      api_base: "http://localhost:11434"
  tiers:
    low:
      ollama: "qwen2.5:7b"
    medium:
      ollama: "qwen2.5:7b"
    high:
      ollama: "qwen2.5:7b"
  agents:
    router:
      tier: low

observability:
  enabled: false
  provider: langfuse
"""
        )

        config = load_cli_config(config_file)

        assert isinstance(config, QuiltoConfig)
        assert config.llm is not None
        assert config.llm.default_provider == "ollama"
        assert config.observability is not None
        assert config.observability.enabled is False
        assert config.observability.provider == "langfuse"

    def test_load_cli_config_with_observability_enabled(self, tmp_path: Path) -> None:
        """Test loading config with observability enabled."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
llm:
  default_provider: ollama
  providers:
    ollama:
      api_base: "http://localhost:11434"
  tiers:
    low:
      ollama: "qwen2.5:7b"
    medium:
      ollama: "qwen2.5:7b"
    high:
      ollama: "qwen2.5:7b"
  agents:
    router:
      tier: low

observability:
  enabled: true
  provider: langfuse
  sample_rate: 0.5
"""
        )

        config = load_cli_config(config_file)

        assert config.observability.enabled is True
        assert config.observability.sample_rate == 0.5

    def test_load_cli_config_defaults_to_config_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that default config path is config.yaml."""
        # Change to a temp directory where no config.yaml exists
        monkeypatch.chdir(tmp_path)

        # This is a behavior test - we verify the default path is used
        # by checking that FileNotFoundError mentions the expected path
        with pytest.raises(FileNotFoundError) as exc_info:
            load_cli_config(None)  # Default path

        # Error should reference config.yaml (not llm-config.yaml)
        assert "config.yaml" in str(exc_info.value)

    def test_load_cli_config_backward_compatible_with_old_format(self, tmp_path: Path) -> None:
        """Test that old LLM-only format still works (backward compatibility)."""
        config_file = tmp_path / "config.yaml"
        # Old format without llm: wrapper
        config_file.write_text(
            """
default_provider: ollama
providers:
  ollama:
    api_base: "http://localhost:11434"
tiers:
  low:
    ollama: "qwen2.5:7b"
  medium:
    ollama: "qwen2.5:7b"
  high:
    ollama: "qwen2.5:7b"
agents:
  router:
    tier: low
"""
        )

        config = load_cli_config(config_file)

        assert isinstance(config, QuiltoConfig)
        assert config.llm.default_provider == "ollama"
        # Observability should have defaults
        assert config.observability.enabled is False


class TestObservabilityProviderCreation:
    """Tests for observability provider creation from config."""

    def test_noop_provider_when_disabled(self, tmp_path: Path) -> None:
        """Test that NoOpProvider is used when observability is disabled."""
        from quilto.config import ObservabilityConfig, create_observability_provider

        config = ObservabilityConfig(enabled=False)
        provider = create_observability_provider(config)

        assert isinstance(provider, NoOpProvider)
        assert provider.is_enabled() is False

    def test_noop_provider_when_credentials_missing(self, tmp_path: Path) -> None:
        """Test that NoOpProvider is used when credentials are missing (graceful degradation)."""
        from quilto.config import ObservabilityConfig, create_observability_provider

        # Clear env vars
        with patch.dict("os.environ", {}, clear=True):
            config = ObservabilityConfig(enabled=True, provider="langfuse")
            provider = create_observability_provider(config)

            assert isinstance(provider, NoOpProvider)

    def test_langfuse_provider_when_credentials_present(self) -> None:
        """Test that LangfuseProvider is created when credentials are present."""
        from quilto.config import ObservabilityConfig, create_observability_provider

        config = ObservabilityConfig(
            enabled=True,
            provider="langfuse",
            public_key="pk-test-123",
            secret_key="sk-test-456",
            host="https://cloud.langfuse.com",
        )
        provider = create_observability_provider(config)

        assert isinstance(provider, LangfuseProvider)


class TestQuiltoWithObservability:
    """Tests for Quilto instantiation with observability from config."""

    def test_quilto_accepts_config_parameter(self, tmp_path: Path) -> None:
        """Test that Quilto constructor accepts config parameter."""
        from quilto import LLMClient, Quilto, StorageRepository
        from quilto.config import QuiltoConfig

        # Create minimal config
        config = QuiltoConfig()

        # Create minimal dependencies
        llm_client = MagicMock(spec=LLMClient)
        storage = MagicMock(spec=StorageRepository)
        storage.base_path = tmp_path
        storage.get_storage_summary.return_value = {}

        # Should not raise
        quilto = Quilto(
            llm_client=llm_client,
            storage=storage,
            domains=[],
            config=config,
        )

        # Verify observability provider is set
        assert quilto.observability_provider is not None
        # With default config (observability disabled), should be NoOpProvider
        assert isinstance(quilto.observability_provider, NoOpProvider)

    def test_quilto_observability_provider_from_config(self, tmp_path: Path) -> None:
        """Test that Quilto creates observability provider from config."""
        from quilto import LLMClient, Quilto, StorageRepository
        from quilto.config import ObservabilityConfig, QuiltoConfig

        # Create config with observability enabled and credentials
        config = QuiltoConfig(
            observability=ObservabilityConfig(
                enabled=True,
                provider="langfuse",
                public_key="pk-test",
                secret_key="sk-test",
            )
        )

        llm_client = MagicMock(spec=LLMClient)
        storage = MagicMock(spec=StorageRepository)
        storage.base_path = tmp_path
        storage.get_storage_summary.return_value = {}

        quilto = Quilto(
            llm_client=llm_client,
            storage=storage,
            domains=[],
            config=config,
        )

        # Should have LangfuseProvider
        assert isinstance(quilto.observability_provider, LangfuseProvider)


class TestDebugObservabilityStatus:
    """Tests for observability status logging in debug mode."""

    def test_observability_provider_has_is_enabled_method(self) -> None:
        """Test that observability providers have is_enabled method."""
        noop = NoOpProvider()
        assert hasattr(noop, "is_enabled")
        assert noop.is_enabled() is False

    def test_langfuse_provider_is_enabled_returns_true(self) -> None:
        """Test that LangfuseProvider.is_enabled() returns True when initialized."""
        provider = LangfuseProvider(
            public_key="pk-test",
            secret_key="sk-test",
        )
        assert provider.is_enabled() is True
