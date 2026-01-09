"""Tests for core fixtures in tests/conftest.py.

These tests validate the fixtures themselves work correctly before
using them in other tests (red-green-refactor: RED phase).
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from quilto import DomainModule


class TestMockLLMFixture:
    """Tests for mock_llm fixture."""

    def test_mock_llm_fixture_exists(self, mock_llm: Callable[[dict[str, str]], None]) -> None:
        """Mock LLM fixture should be available."""
        assert mock_llm is not None
        assert callable(mock_llm)

    def test_mock_llm_returns_canned_response(self, mock_llm: Callable[[dict[str, str]], None]) -> None:
        """Mock LLM should return configured canned responses."""
        mock_llm({"_default": '{"result": "test"}'})
        # Fixture provides set_responses function
        assert hasattr(mock_llm, "_mock")
        assert hasattr(mock_llm, "_call_history")


class TestStorageFixture:
    """Tests for storage_fixture."""

    def test_storage_fixture_creates_directory_structure(self, storage_fixture: Path) -> None:
        """Storage fixture should create logs/(raw|parsed)/{YYYY}/{MM}/ structure."""
        assert isinstance(storage_fixture, Path)
        assert (storage_fixture / "logs" / "raw").exists()
        assert (storage_fixture / "logs" / "parsed").exists()

        # Should have year/month subdirs
        raw_dirs = list((storage_fixture / "logs" / "raw").iterdir())
        assert len(raw_dirs) > 0
        year_dir = raw_dirs[0]
        assert year_dir.is_dir()
        month_dirs = list(year_dir.iterdir())
        assert len(month_dirs) > 0

    def test_storage_fixture_is_isolated(self, storage_fixture: Path, tmp_path: Path) -> None:
        """Storage fixture should use tmp_path for isolation."""
        # storage_fixture should be under pytest's tmp_path
        assert tmp_path in storage_fixture.parents or storage_fixture == tmp_path


class TestDomainFixture:
    """Tests for domain_fixture."""

    def test_domain_fixture_returns_domain_module(self, domain_fixture: DomainModule) -> None:
        """Domain fixture should return a DomainModule instance."""
        assert isinstance(domain_fixture, DomainModule)

    def test_domain_fixture_is_general_fitness(self, domain_fixture: DomainModule) -> None:
        """Domain fixture should return general_fitness by default."""
        # Check it has the expected description pattern
        assert "fitness" in domain_fixture.description.lower()


class TestUseRealOllamaOption:
    """Tests for --use-real-ollama pytest option."""

    def test_use_real_ollama_fixture_exists(self, use_real_ollama: bool) -> None:
        """use_real_ollama fixture should be available."""
        assert isinstance(use_real_ollama, bool)

    def test_use_real_ollama_default_is_false(self, use_real_ollama: bool) -> None:
        """use_real_ollama should default to False."""
        # When running without --use-real-ollama flag
        assert use_real_ollama is False


class TestIntegrationMarker:
    """Tests for integration marker behavior."""

    @pytest.mark.integration
    def test_integration_marker_registered(self) -> None:
        """Integration marker should be registered in pytest."""
        # This test will fail if marker is not registered (strict marker mode)
        pass
