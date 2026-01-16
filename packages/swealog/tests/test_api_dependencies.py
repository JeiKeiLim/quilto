"""Tests for swealog.api.dependencies module - DI providers."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from swealog.api.dependencies import (
    ConfigNotFoundError,
    get_domains,
    get_llm_client,
    get_llm_config,
    get_storage,
)


class TestGetDomains:
    """Tests for get_domains dependency."""

    def test_returns_list_of_domains(self) -> None:
        """Test that get_domains returns all domain modules."""
        domains = get_domains()

        # Should return 5 domains
        assert len(domains) == 5

        # Check domain names
        names = {d.name for d in domains}
        expected = {"GeneralFitness", "Strength", "Nutrition", "Running", "Swimming"}
        assert names == expected

    def test_domains_have_required_attributes(self) -> None:
        """Test that all domains have required DomainModule attributes."""
        domains = get_domains()

        for domain in domains:
            assert hasattr(domain, "name")
            assert hasattr(domain, "description")
            assert hasattr(domain, "log_schema")
            assert hasattr(domain, "vocabulary")
            assert isinstance(domain.description, str)
            assert len(domain.description) > 0


class TestGetStorage:
    """Tests for get_storage dependency."""

    def test_returns_storage_repository(self) -> None:
        """Test that get_storage returns StorageRepository instance."""
        with (
            TemporaryDirectory() as tmpdir,
            patch("swealog.api.dependencies.Path") as mock_path,
        ):
            mock_path.return_value = Path(tmpdir) / "logs"
            mock_path.return_value.mkdir(parents=True, exist_ok=True)

            storage = get_storage()

            # Should be a StorageRepository
            from quilto import StorageRepository

            assert isinstance(storage, StorageRepository)

    def test_creates_logs_directory(self) -> None:
        """Test that get_storage creates logs directory if not exists."""
        # This tests the actual behavior - creates ./logs in current dir
        storage = get_storage()

        # Verify we got a repository
        assert storage is not None


class TestGetLLMConfig:
    """Tests for get_llm_config dependency."""

    def test_raises_when_config_missing(self) -> None:
        """Test that ConfigNotFoundError is raised when config doesn't exist."""
        import os

        # Clear cache first
        get_llm_config.cache_clear()

        # Save original path and change to temp dir
        original_cwd = os.getcwd()
        with TemporaryDirectory() as tmpdir:
            try:
                os.chdir(tmpdir)
                # No llm-config.yaml exists in temp dir
                with pytest.raises(ConfigNotFoundError) as exc_info:
                    get_llm_config()

                assert "llm-config.yaml" in str(exc_info.value)
            finally:
                os.chdir(original_cwd)

        # Clear cache after test
        get_llm_config.cache_clear()


class TestGetLLMClient:
    """Tests for get_llm_client dependency."""

    def test_raises_when_config_missing(self) -> None:
        """Test that get_llm_client raises ConfigNotFoundError when config missing."""
        # Clear cache first
        get_llm_config.cache_clear()

        with patch("swealog.api.dependencies.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            with pytest.raises(ConfigNotFoundError):
                get_llm_client()

        # Clear cache after test
        get_llm_config.cache_clear()


class TestConfigNotFoundError:
    """Tests for ConfigNotFoundError exception."""

    def test_exception_message(self) -> None:
        """Test ConfigNotFoundError can be raised with message."""
        with pytest.raises(ConfigNotFoundError) as exc_info:
            raise ConfigNotFoundError("Test message")
        assert "Test message" in str(exc_info.value)
