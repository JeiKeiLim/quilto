"""Integration tests for Observer → context file creation flow.

Story: 15-5-verify-observer-integration
Tests AC #2 (context file creation), AC #3 (context accumulation), AC #4 (graceful handling).

Tests the Observer being invoked during query processing and verifying
context files are created correctly.
"""

from pathlib import Path

from quilto import ObserverTriggerConfig, StorageRepository
from quilto.agents import ContextUpdate, ObserverOutput
from quilto.storage.context import GlobalContextManager


class TestObserverContextFileCreation:
    """Test Observer updates are correctly written to context files (AC #2)."""

    def test_context_manager_creates_file_on_first_update(self, tmp_path: Path) -> None:
        """Test that GlobalContextManager creates context file on first update.

        AC: #2 - When apply_updates() is called, logs/context/global.md is created.
        """
        storage = StorageRepository(tmp_path)
        context_manager = GlobalContextManager(storage)

        # Create a context update
        updates = [
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="kilograms",
                confidence="certain",
                source="post_query: user explicit preference",
            )
        ]

        # Apply updates
        context_manager.apply_updates(updates)

        # Verify file exists
        context_path = tmp_path / "logs" / "context" / "global.md"
        assert context_path.exists(), f"Context file not created at {context_path}"

        # Verify content
        content = context_path.read_text()
        assert "unit_preference" in content
        assert "kilograms" in content
        assert "certain" in content.lower()

    def test_context_accumulates_across_updates(self, tmp_path: Path) -> None:
        """Test that multiple updates accumulate in context file.

        AC: #3 - Multiple queries accumulate context appropriately.
        """
        storage = StorageRepository(tmp_path)
        context_manager = GlobalContextManager(storage)

        # First update - preference
        first_updates = [
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="kilograms",
                confidence="certain",
                source="post_query: first query",
            )
        ]
        context_manager.apply_updates(first_updates)

        # Second update - fact
        second_updates = [
            ContextUpdate(
                category="fact",
                key="body_weight",
                value="75kg",
                confidence="certain",
                source="post_query: second query",
            )
        ]
        context_manager.apply_updates(second_updates)

        # Verify file has both
        context_path = tmp_path / "logs" / "context" / "global.md"
        content = context_path.read_text()

        assert "unit_preference" in content, "First update missing"
        assert "body_weight" in content, "Second update missing"
        assert "version: 3" in content, "Version should be 3 after two updates"

    def test_context_manager_supersedes_existing_key(self, tmp_path: Path) -> None:
        """Test that updating same key supersedes the old value.

        AC: #3 - Context updates work correctly (supersede logic).
        """
        storage = StorageRepository(tmp_path)
        context_manager = GlobalContextManager(storage)

        # First update
        first_updates = [
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="pounds",
                confidence="likely",
                source="post_query: initial guess",
            )
        ]
        context_manager.apply_updates(first_updates)

        # Second update with same key
        second_updates = [
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="kilograms",
                confidence="certain",
                source="post_query: user correction",
            )
        ]
        context_manager.apply_updates(second_updates)

        # Verify file has updated value
        context_path = tmp_path / "logs" / "context" / "global.md"
        content = context_path.read_text()

        # Should have kilograms, not pounds (superseded)
        assert "kilograms" in content
        # Only one unit_preference entry
        assert content.count("unit_preference") == 1

    def test_graceful_handling_empty_updates(self, tmp_path: Path) -> None:
        """Test that apply_updates with empty list doesn't raise errors.

        AC: #4 - Graceful handling when no updates to apply.
        Note: Current behavior creates file with empty sections, which is acceptable.
        """
        storage = StorageRepository(tmp_path)
        context_manager = GlobalContextManager(storage)

        # Apply empty updates - should not raise
        context_manager.apply_updates([])

        # File may or may not be created - either is acceptable
        # The key is that no exception is raised
        context_path = tmp_path / "logs" / "context" / "global.md"
        if context_path.exists():
            # If file exists, it should have valid structure
            content = context_path.read_text()
            assert "## Preferences" in content


class TestObserverTriggerConfig:
    """Test ObserverTriggerConfig behavior."""

    def test_default_config_enables_post_query(self) -> None:
        """Test that default config has post_query enabled.

        Post-query observation is enabled by default for context learning.
        """
        config = ObserverTriggerConfig()
        assert config.enable_post_query is True

    def test_config_can_disable_post_query(self) -> None:
        """Test that config can explicitly disable post_query."""
        config = ObserverTriggerConfig(enable_post_query=False)
        assert config.enable_post_query is False


class TestContextFileFormat:
    """Test the format of generated context files."""

    def test_context_file_has_yaml_frontmatter(self, tmp_path: Path) -> None:
        """Test that context file includes YAML frontmatter with metadata."""
        storage = StorageRepository(tmp_path)
        context_manager = GlobalContextManager(storage)

        updates = [
            ContextUpdate(
                category="preference",
                key="test_key",
                value="test_value",
                confidence="certain",
                source="test_source",
            )
        ]
        context_manager.apply_updates(updates)

        context_path = tmp_path / "logs" / "context" / "global.md"
        content = context_path.read_text()

        # Should have YAML frontmatter
        assert content.startswith("---"), "Should start with YAML frontmatter"
        assert "last_updated:" in content
        assert "version:" in content
        assert "token_estimate:" in content

    def test_context_file_has_sections(self, tmp_path: Path) -> None:
        """Test that context file includes all category sections."""
        storage = StorageRepository(tmp_path)
        context_manager = GlobalContextManager(storage)

        # Add one update to trigger file creation
        updates = [
            ContextUpdate(
                category="preference",
                key="test",
                value="test",
                confidence="certain",
                source="test",
            )
        ]
        context_manager.apply_updates(updates)

        context_path = tmp_path / "logs" / "context" / "global.md"
        content = context_path.read_text()

        # Should have all sections (even if empty)
        assert "## Preferences" in content
        assert "## Patterns" in content
        assert "## Facts" in content
        assert "## Insights" in content


class TestObserverOutputModels:
    """Test ObserverOutput model behavior."""

    def test_observer_output_should_update_false(self) -> None:
        """Test that Observer can return should_update=False.

        AC: #4 - Observer returns should_update=False when no insights.
        """
        output = ObserverOutput(
            should_update=False,
            updates=[],
            insights_captured=[],
        )
        assert output.should_update is False
        assert len(output.updates) == 0

    def test_observer_output_with_updates(self) -> None:
        """Test Observer output with context updates."""
        output = ObserverOutput(
            should_update=True,
            updates=[
                ContextUpdate(
                    category="preference",
                    key="test_key",
                    value="test_value",
                    confidence="certain",
                    source="test",
                )
            ],
            insights_captured=["Found a preference"],
        )
        assert output.should_update is True
        assert len(output.updates) == 1
        assert output.updates[0].key == "test_key"
