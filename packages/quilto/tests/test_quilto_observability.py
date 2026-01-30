"""Unit tests for Quilto observability integration.

Tests cover:
- Quilto accepts explicit observability provider override (AC #1)
- Quilto creates provider from config when enabled (AC #2)
- Quilto defaults to NoOpProvider when no config (AC #3)
- Quilto backward compatibility without config/observability params (AC #7)
- Quilto.flush() delegates to provider.flush() (AC #6)
- QuiltoGraph passes callback to LangGraph ainvoke (AC #4)
"""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel
from quilto import DomainModule, LLMClient, Quilto, StorageRepository
from quilto.config import ObservabilityConfig, QuiltoConfig
from quilto.observability.noop import NoOpProvider
from quilto.observability.provider import ObservabilityProvider

# =============================================================================
# Fixtures
# =============================================================================


class MockSchema(BaseModel):
    """Mock schema for testing."""

    value: str


@pytest.fixture
def temp_storage_dir() -> Generator[Path]:
    """Create a temporary directory for storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    client = MagicMock(spec=LLMClient)
    client.complete = AsyncMock(return_value='{"result": "ok"}')
    return client


@pytest.fixture
def mock_storage(temp_storage_dir: Path) -> StorageRepository:
    """Create a mock storage repository."""
    storage = StorageRepository(base_path=temp_storage_dir)
    return storage


@pytest.fixture
def mock_domain() -> DomainModule:
    """Create a mock domain module."""
    return DomainModule(
        name="test_domain",
        description="A test domain for unit testing",
        log_schema=MockSchema,
        vocabulary={"test": "testing term"},
        expertise="Test domain expertise",
        response_evaluation_rules=["Test responses should be accurate"],
        context_management_guidance="Test context guidance",
        clarification_patterns={},
    )


# =============================================================================
# Observability Provider Initialization Tests (AC #1, #2, #3, #7)
# =============================================================================


class TestQuiltoObservabilityInitialization:
    """Tests for Quilto observability provider initialization."""

    def test_quilto_accepts_explicit_provider(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #1: Quilto uses provided observability provider."""
        provider = NoOpProvider()

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
            observability=provider,
        )

        assert q.observability_provider is provider

    def test_quilto_creates_noop_from_disabled_config(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #2: Quilto creates NoOpProvider when observability disabled in config."""
        config = QuiltoConfig(observability=ObservabilityConfig(enabled=False))

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
            config=config,
        )

        assert isinstance(q.observability_provider, NoOpProvider)

    def test_quilto_creates_langfuse_from_enabled_config(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #2: Quilto creates LangfuseProvider when observability enabled with credentials."""
        config = QuiltoConfig(
            observability=ObservabilityConfig(
                enabled=True,
                public_key="pk-test-key",
                secret_key="sk-test-key",
            )
        )

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
            config=config,
        )

        # Should create LangfuseProvider
        from quilto.observability.langfuse import LangfuseProvider

        assert isinstance(q.observability_provider, LangfuseProvider)

    def test_quilto_falls_back_to_noop_without_credentials(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #2: Quilto falls back to NoOpProvider when credentials missing."""
        # Enabled but no credentials
        config = QuiltoConfig(observability=ObservabilityConfig(enabled=True))

        # Clear env vars to ensure no credentials are found
        with patch.dict("os.environ", {}, clear=True):
            q = Quilto(
                llm_client=mock_llm_client,
                storage=mock_storage,
                domains=[mock_domain],
                session_db_path=":memory:",
                config=config,
            )

        # Should fall back to NoOpProvider with warning
        assert isinstance(q.observability_provider, NoOpProvider)

    def test_quilto_defaults_to_noop_without_config(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #3: Quilto defaults to NoOpProvider when no config provided."""
        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
        )

        assert isinstance(q.observability_provider, NoOpProvider)

    def test_quilto_backward_compatible_without_observability_params(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #7: Existing code without config/observability params still works."""
        # This matches the old Quilto signature without config or observability
        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
        )

        # Should work and have NoOpProvider
        assert q.llm_client == mock_llm_client
        assert q.storage == mock_storage
        assert isinstance(q.observability_provider, NoOpProvider)

    def test_explicit_provider_takes_precedence_over_config(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #1: Explicit provider takes precedence over config-based creation."""
        # Config would create LangfuseProvider
        config = QuiltoConfig(
            observability=ObservabilityConfig(
                enabled=True,
                public_key="pk-test",
                secret_key="sk-test",
            )
        )

        # But explicit provider should win
        explicit_provider = NoOpProvider()

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
            config=config,
            observability=explicit_provider,
        )

        assert q.observability_provider is explicit_provider


# =============================================================================
# Flush Method Tests (AC #6)
# =============================================================================


class TestQuiltoFlush:
    """Tests for Quilto.flush() method."""

    def test_flush_calls_provider_flush(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #6: Quilto.flush() delegates to provider.flush()."""
        # Create mock provider
        mock_provider = MagicMock(spec=ObservabilityProvider)

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
            observability=mock_provider,
        )

        q.flush()

        mock_provider.flush.assert_called_once()

    def test_flush_with_noop_provider_succeeds(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """flush() should succeed with NoOpProvider (no-op)."""
        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
        )

        # Should not raise
        q.flush()


# =============================================================================
# QuiltoGraph Callback Integration Tests (AC #4)
# =============================================================================


class TestQuiltoGraphCallback:
    """Tests for QuiltoGraph passing callback to LangGraph."""

    @pytest.mark.asyncio
    async def test_quilto_graph_passes_callback_when_available(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #4: QuiltoGraph.ainvoke() passes callback to LangGraph when provider returns one."""
        # Create mock provider that returns a callback
        mock_callback = MagicMock()
        mock_provider = MagicMock(spec=ObservabilityProvider)
        mock_provider.get_langgraph_callback.return_value = mock_callback

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
            observability=mock_provider,
        )

        # Mock the compiled graph's ainvoke
        with patch("quilto.orchestration.StateGraph") as mock_state_graph:
            mock_compiled = MagicMock()

            captured_config: dict[str, Any] = {}

            async def capture_ainvoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
                if config:
                    captured_config.update(config)
                return {
                    "input_type": "query",
                    "response": "Test",
                    "selected_domains": [],
                }

            mock_compiled.ainvoke = capture_ainvoke
            mock_state_graph.return_value.compile.return_value = mock_compiled

            # Get graph (triggers creation)
            graph = q._get_graph()  # pyright: ignore[reportPrivateUsage]

            # Invoke the graph
            state: dict[str, Any] = {
                "user_input": "test",
                "mode": "auto",
            }
            await graph.ainvoke(state)

        # Verify callback was passed in config
        assert "callbacks" in captured_config
        assert mock_callback in captured_config["callbacks"]

    @pytest.mark.asyncio
    async def test_quilto_graph_skips_callback_when_none(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """AC #4: QuiltoGraph.ainvoke() works without callback when provider returns None."""
        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
            # NoOpProvider returns None for get_langgraph_callback
        )

        # Mock the compiled graph's ainvoke
        with patch("quilto.orchestration.StateGraph") as mock_state_graph:
            mock_compiled = MagicMock()

            captured_args: list[Any] = []
            captured_kwargs: dict[str, Any] = {}

            async def capture_ainvoke(state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
                captured_args.append(state)
                captured_kwargs.update(kwargs)
                return {
                    "input_type": "query",
                    "response": "Test",
                    "selected_domains": [],
                }

            mock_compiled.ainvoke = capture_ainvoke
            mock_state_graph.return_value.compile.return_value = mock_compiled

            # Get graph
            graph = q._get_graph()  # pyright: ignore[reportPrivateUsage]

            # Invoke the graph
            state: dict[str, Any] = {
                "user_input": "test",
                "mode": "auto",
            }
            await graph.ainvoke(state)

        # Verify no config was passed (or config without callbacks)
        # NoOpProvider.get_langgraph_callback() returns None, so no callbacks should be passed
        assert "config" not in captured_kwargs or "callbacks" not in captured_kwargs.get("config", {})


# =============================================================================
# Import Verification Tests
# =============================================================================


class TestObservabilityImports:
    """Tests for observability module imports."""

    def test_observability_provider_importable(self) -> None:
        """ObservabilityProvider should be importable from quilto.observability."""
        from quilto.observability import ObservabilityProvider

        assert ObservabilityProvider is not None

    def test_langfuse_provider_importable(self) -> None:
        """LangfuseProvider should be importable from quilto.observability."""
        from quilto.observability import LangfuseProvider

        assert LangfuseProvider is not None

    def test_noop_provider_importable(self) -> None:
        """NoOpProvider should be importable from quilto.observability."""
        from quilto.observability import NoOpProvider

        assert NoOpProvider is not None
