"""Tests for quilto.config module - unified configuration loading."""

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from quilto.config import (
    ObservabilityConfig,
    QuiltoConfig,
    create_observability_provider,
    load_config,
    load_config_from_dict,
)
from quilto.observability.langfuse import LangfuseProvider
from quilto.observability.noop import NoOpProvider


@pytest.fixture
def sample_unified_config_yaml(tmp_path: Path) -> Path:
    """Create sample unified config file with both llm and observability."""
    config_content = """
llm:
  default_provider: ollama
  providers:
    ollama:
      api_base: "http://localhost:11434"
observability:
  enabled: true
  provider: langfuse
  sample_rate: 0.5
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def llm_only_config_yaml(tmp_path: Path) -> Path:
    """Create sample LLM-only config file (old format for backward compatibility)."""
    config_content = """
default_provider: ollama
providers:
  ollama:
    api_base: "http://localhost:11434"
"""
    config_file = tmp_path / "llm-config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def observability_disabled_yaml(tmp_path: Path) -> Path:
    """Create config file with observability disabled."""
    config_content = """
llm:
  default_provider: ollama
observability:
  enabled: false
"""
    config_file = tmp_path / "disabled-obs.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def env_cleanup() -> Generator[None]:
    """Clean up Langfuse environment variables after test."""
    # Store original values
    original_public = os.environ.get("LANGFUSE_PUBLIC_KEY")
    original_secret = os.environ.get("LANGFUSE_SECRET_KEY")
    original_host = os.environ.get("LANGFUSE_BASE_URL")

    yield

    # Restore original values
    if original_public is not None:
        os.environ["LANGFUSE_PUBLIC_KEY"] = original_public
    else:
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)

    if original_secret is not None:
        os.environ["LANGFUSE_SECRET_KEY"] = original_secret
    else:
        os.environ.pop("LANGFUSE_SECRET_KEY", None)

    if original_host is not None:
        os.environ["LANGFUSE_BASE_URL"] = original_host
    else:
        os.environ.pop("LANGFUSE_BASE_URL", None)


class TestObservabilityConfig:
    """Tests for ObservabilityConfig model."""

    def test_default_values(self) -> None:
        """Test ObservabilityConfig defaults to disabled."""
        config = ObservabilityConfig()

        assert config.enabled is False
        assert config.provider == "langfuse"
        assert config.sample_rate == 1.0
        assert config.public_key is None
        assert config.secret_key is None
        assert config.host is None

    def test_sample_rate_valid_boundaries(self) -> None:
        """Test sample_rate accepts boundary values 0.0 and 1.0."""
        config_zero = ObservabilityConfig(sample_rate=0.0)
        assert config_zero.sample_rate == 0.0

        config_one = ObservabilityConfig(sample_rate=1.0)
        assert config_one.sample_rate == 1.0

        config_mid = ObservabilityConfig(sample_rate=0.5)
        assert config_mid.sample_rate == 0.5

    def test_sample_rate_invalid_below_zero(self) -> None:
        """Test sample_rate rejects values below 0.0."""
        with pytest.raises(ValidationError) as exc_info:
            ObservabilityConfig(sample_rate=-0.1)

        assert "sample_rate must be between 0.0 and 1.0" in str(exc_info.value)

    def test_sample_rate_invalid_above_one(self) -> None:
        """Test sample_rate rejects values above 1.0."""
        with pytest.raises(ValidationError) as exc_info:
            ObservabilityConfig(sample_rate=1.1)

        assert "sample_rate must be between 0.0 and 1.0" in str(exc_info.value)

    def test_provider_noop_valid(self) -> None:
        """Test provider accepts 'noop' value."""
        config = ObservabilityConfig(provider="noop")
        assert config.provider == "noop"

    def test_provider_invalid_value(self) -> None:
        """Test provider rejects invalid values."""
        with pytest.raises(ValidationError):
            ObservabilityConfig(provider="invalid")  # type: ignore[arg-type]


class TestQuiltoConfig:
    """Tests for QuiltoConfig model."""

    def test_default_values(self) -> None:
        """Test QuiltoConfig has sensible defaults."""
        config = QuiltoConfig()

        assert config.llm.default_provider == "ollama"
        assert config.observability.enabled is False

    def test_with_custom_values(self) -> None:
        """Test QuiltoConfig accepts custom values."""
        from quilto.llm.config import LLMConfig

        config = QuiltoConfig(
            llm=LLMConfig(default_provider="openai"),
            observability=ObservabilityConfig(enabled=True, sample_rate=0.75),
        )

        assert config.llm.default_provider == "openai"
        assert config.observability.enabled is True
        assert config.observability.sample_rate == 0.75


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_parses_unified_format(self, sample_unified_config_yaml: Path) -> None:
        """Test load_config parses YAML with both llm and observability sections."""
        config = load_config(sample_unified_config_yaml)

        assert config.llm.default_provider == "ollama"
        assert config.llm.providers["ollama"].api_base == "http://localhost:11434"
        assert config.observability.enabled is True
        assert config.observability.provider == "langfuse"
        assert config.observability.sample_rate == 0.5

    def test_load_config_missing_observability_defaults_to_disabled(self, llm_only_config_yaml: Path) -> None:
        """Test load_config with old LLM-only format has observability disabled."""
        config = load_config(llm_only_config_yaml)

        assert config.llm.default_provider == "ollama"
        assert config.observability.enabled is False
        assert config.observability.provider == "langfuse"

    def test_load_config_backward_compatible_llm_only(self, llm_only_config_yaml: Path) -> None:
        """Test load_config works with old LLM-only config format."""
        config = load_config(llm_only_config_yaml)

        # LLM config should be parsed correctly
        assert config.llm.default_provider == "ollama"
        assert "ollama" in config.llm.providers

        # Observability should default to disabled
        assert config.observability.enabled is False

    def test_load_config_env_vars_override_file(self, sample_unified_config_yaml: Path, env_cleanup: None) -> None:
        """Test environment variables override config file values."""
        # Set environment variables
        os.environ["LANGFUSE_PUBLIC_KEY"] = "env-public-key"
        os.environ["LANGFUSE_SECRET_KEY"] = "env-secret-key"
        os.environ["LANGFUSE_BASE_URL"] = "https://env.langfuse.com"

        config = load_config(sample_unified_config_yaml)

        assert config.observability.public_key == "env-public-key"
        assert config.observability.secret_key == "env-secret-key"
        assert config.observability.host == "https://env.langfuse.com"

    def test_load_config_file_not_found(self, tmp_path: Path) -> None:
        """Test load_config raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")

    def test_load_config_invalid_raises_validation_error(self, tmp_path: Path) -> None:
        """Test load_config raises ValidationError for invalid config."""
        invalid_config = tmp_path / "invalid.yaml"
        invalid_config.write_text("""
llm:
  default_provider: ollama
observability:
  sample_rate: 2.0  # Invalid: must be 0.0-1.0
""")

        with pytest.raises(ValidationError) as exc_info:
            load_config(invalid_config)

        assert "sample_rate" in str(exc_info.value)


class TestLoadConfigFromDict:
    """Tests for load_config_from_dict function."""

    def test_unified_format(self) -> None:
        """Test load_config_from_dict with unified format."""
        config_dict: dict[str, Any] = {
            "llm": {"default_provider": "openai"},
            "observability": {"enabled": True, "sample_rate": 0.8},
        }

        config = load_config_from_dict(config_dict)

        assert config.llm.default_provider == "openai"
        assert config.observability.enabled is True
        assert config.observability.sample_rate == 0.8

    def test_old_llm_only_format(self) -> None:
        """Test load_config_from_dict with old LLM-only format."""
        config_dict: dict[str, Any] = {
            "default_provider": "ollama",
            "providers": {"ollama": {"api_base": "http://localhost:11434"}},
        }

        config = load_config_from_dict(config_dict)

        assert config.llm.default_provider == "ollama"
        assert config.observability.enabled is False

    def test_env_vars_override(self, env_cleanup: None) -> None:
        """Test environment variables override dict values."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "env-key"
        os.environ["LANGFUSE_SECRET_KEY"] = "env-secret"

        config_dict: dict[str, Any] = {
            "llm": {"default_provider": "ollama"},
            "observability": {
                "enabled": True,
                "public_key": "file-key",
                "secret_key": "file-secret",
            },
        }

        config = load_config_from_dict(config_dict)

        # Env vars should override file values
        assert config.observability.public_key == "env-key"
        assert config.observability.secret_key == "env-secret"


class TestCreateObservabilityProvider:
    """Tests for create_observability_provider function."""

    def test_disabled_returns_noop(self) -> None:
        """Test create_observability_provider returns NoOpProvider when disabled."""
        config = ObservabilityConfig(enabled=False)

        provider = create_observability_provider(config)

        assert isinstance(provider, NoOpProvider)
        assert provider.is_enabled() is False

    def test_enabled_with_credentials_returns_langfuse(self, env_cleanup: None) -> None:
        """Test create_observability_provider returns LangfuseProvider when enabled with credentials."""
        config = ObservabilityConfig(
            enabled=True,
            public_key="test-public",
            secret_key="test-secret",
            host="https://test.langfuse.com",
        )

        provider = create_observability_provider(config)

        assert isinstance(provider, LangfuseProvider)
        # Note: is_enabled() depends on actual Langfuse client initialization
        # which may fail without real credentials

    def test_enabled_missing_credentials_returns_noop(self, env_cleanup: None) -> None:
        """Test create_observability_provider returns NoOpProvider when credentials missing."""
        # Clear any environment variables
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)

        config = ObservabilityConfig(enabled=True)  # No credentials

        provider = create_observability_provider(config)

        assert isinstance(provider, NoOpProvider)

    def test_enabled_missing_public_key_returns_noop(self, env_cleanup: None) -> None:
        """Test returns NoOpProvider when only public_key is missing."""
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)

        config = ObservabilityConfig(
            enabled=True,
            secret_key="test-secret",  # Only secret, no public
        )

        provider = create_observability_provider(config)

        assert isinstance(provider, NoOpProvider)

    def test_enabled_missing_secret_key_returns_noop(self, env_cleanup: None) -> None:
        """Test returns NoOpProvider when only secret_key is missing."""
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)

        config = ObservabilityConfig(
            enabled=True,
            public_key="test-public",  # Only public, no secret
        )

        provider = create_observability_provider(config)

        assert isinstance(provider, NoOpProvider)

    def test_credentials_from_env_vars(self, env_cleanup: None) -> None:
        """Test credentials can come from environment variables."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "env-public"
        os.environ["LANGFUSE_SECRET_KEY"] = "env-secret"

        config = ObservabilityConfig(enabled=True)  # No credentials in config

        provider = create_observability_provider(config)

        # Should create LangfuseProvider since env vars have credentials
        assert isinstance(provider, LangfuseProvider)


class TestLoadConfigEdgeCases:
    """Tests for edge cases in config loading."""

    def test_load_config_empty_file(self, tmp_path: Path) -> None:
        """Test load_config handles empty YAML file gracefully."""
        empty_config = tmp_path / "empty.yaml"
        empty_config.write_text("")

        config = load_config(empty_config)

        # Should return defaults
        assert config.llm.default_provider == "ollama"
        assert config.observability.enabled is False
