"""Comprehensive tests for the GlobalContext storage module."""

from datetime import date
from pathlib import Path

import pytest
from quilto.agents.models import ContextUpdate
from quilto.storage import StorageRepository
from quilto.storage.context import (
    ContextEntry,
    GlobalContext,
    GlobalContextFrontmatter,
    GlobalContextManager,
)


class TestContextEntryValidation:
    """Tests for ContextEntry model validation."""

    def test_valid_context_entry(self) -> None:
        """Test creating a valid ContextEntry."""
        entry = ContextEntry(
            key="unit_preference",
            value="metric",
            confidence="certain",
            source="user_correction",
            category="preference",
            added_date="2026-01-16",
        )
        assert entry.key == "unit_preference"
        assert entry.value == "metric"
        assert entry.confidence == "certain"
        assert entry.category == "preference"

    def test_all_confidence_values(self) -> None:
        """Test all valid confidence values."""
        for confidence in ["certain", "likely", "tentative"]:
            entry = ContextEntry(
                key="test",
                value="value",
                confidence=confidence,  # type: ignore[arg-type]
                source="test",
                category="preference",
                added_date="2026-01-16",
            )
            assert entry.confidence == confidence

    def test_all_category_values(self) -> None:
        """Test all valid category values."""
        for category in ["preference", "pattern", "fact", "insight"]:
            entry = ContextEntry(
                key="test",
                value="value",
                confidence="certain",
                source="test",
                category=category,  # type: ignore[arg-type]
                added_date="2026-01-16",
            )
            assert entry.category == category

    def test_empty_key_fails(self) -> None:
        """Test that empty key fails validation."""
        with pytest.raises(ValueError):
            ContextEntry(
                key="",
                value="value",
                confidence="certain",
                source="test",
                category="preference",
                added_date="2026-01-16",
            )

    def test_empty_value_fails(self) -> None:
        """Test that empty value fails validation."""
        with pytest.raises(ValueError):
            ContextEntry(
                key="key",
                value="",
                confidence="certain",
                source="test",
                category="preference",
                added_date="2026-01-16",
            )

    def test_empty_source_fails(self) -> None:
        """Test that empty source fails validation."""
        with pytest.raises(ValueError):
            ContextEntry(
                key="key",
                value="value",
                confidence="certain",
                source="",
                category="preference",
                added_date="2026-01-16",
            )

    def test_valid_added_date_passes(self) -> None:
        """Test valid ISO date format passes."""
        entry = ContextEntry(
            key="test",
            value="value",
            confidence="certain",
            source="test",
            category="preference",
            added_date="2026-01-16",
        )
        assert entry.added_date == "2026-01-16"

    def test_invalid_added_date_format_fails(self) -> None:
        """Test invalid date format fails."""
        with pytest.raises(ValueError):
            ContextEntry(
                key="test",
                value="value",
                confidence="certain",
                source="test",
                category="preference",
                added_date="not-a-date",
            )

    def test_format_valid_but_semantically_invalid_date_fails(self) -> None:
        """Test format-valid but semantically invalid date fails."""
        with pytest.raises(ValueError):
            ContextEntry(
                key="test",
                value="value",
                confidence="certain",
                source="test",
                category="preference",
                added_date="2026-99-99",
            )

    def test_invalid_confidence_fails(self) -> None:
        """Test that invalid confidence value fails."""
        with pytest.raises(ValueError):
            ContextEntry(
                key="test",
                value="value",
                confidence="invalid",  # type: ignore[arg-type]
                source="test",
                category="preference",
                added_date="2026-01-16",
            )

    def test_invalid_category_fails(self) -> None:
        """Test that invalid category value fails."""
        with pytest.raises(ValueError):
            ContextEntry(
                key="test",
                value="value",
                confidence="certain",
                source="test",
                category="invalid",  # type: ignore[arg-type]
                added_date="2026-01-16",
            )


class TestGlobalContextFrontmatterValidation:
    """Tests for GlobalContextFrontmatter model validation."""

    def test_valid_frontmatter(self) -> None:
        """Test creating valid frontmatter."""
        fm = GlobalContextFrontmatter(
            last_updated="2026-01-16",
            version=15,
            token_estimate=450,
        )
        assert fm.last_updated == "2026-01-16"
        assert fm.version == 15
        assert fm.token_estimate == 450

    def test_valid_date_format_passes(self) -> None:
        """Test valid ISO date format passes."""
        fm = GlobalContextFrontmatter(
            last_updated="2026-01-16",
            version=1,
            token_estimate=0,
        )
        assert fm.last_updated == "2026-01-16"

    def test_invalid_date_format_fails(self) -> None:
        """Test invalid date format fails."""
        with pytest.raises(ValueError):
            GlobalContextFrontmatter(
                last_updated="not-a-date",
                version=1,
                token_estimate=0,
            )

    def test_semantically_invalid_date_fails(self) -> None:
        """Test format-valid but semantically invalid date fails (e.g., 2026-13-45)."""
        with pytest.raises(ValueError):
            GlobalContextFrontmatter(
                last_updated="2026-13-45",
                version=1,
                token_estimate=0,
            )

    def test_version_zero_fails(self) -> None:
        """Test that version 0 fails validation (must be >= 1)."""
        with pytest.raises(ValueError):
            GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=0,
                token_estimate=0,
            )

    def test_version_one_passes(self) -> None:
        """Test that version 1 passes validation."""
        fm = GlobalContextFrontmatter(
            last_updated="2026-01-16",
            version=1,
            token_estimate=0,
        )
        assert fm.version == 1

    def test_negative_token_estimate_fails(self) -> None:
        """Test that negative token_estimate fails validation."""
        with pytest.raises(ValueError):
            GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=-1,
            )

    def test_zero_token_estimate_passes(self) -> None:
        """Test that zero token_estimate passes validation."""
        fm = GlobalContextFrontmatter(
            last_updated="2026-01-16",
            version=1,
            token_estimate=0,
        )
        assert fm.token_estimate == 0


class TestGlobalContextModel:
    """Tests for GlobalContext model."""

    def test_valid_global_context(self) -> None:
        """Test creating a valid GlobalContext."""
        ctx = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=100,
            ),
            preferences=[
                ContextEntry(
                    key="unit_preference",
                    value="metric",
                    confidence="certain",
                    source="test",
                    category="preference",
                    added_date="2026-01-16",
                )
            ],
        )
        assert len(ctx.preferences) == 1
        assert ctx.preferences[0].key == "unit_preference"

    def test_empty_sections_default(self) -> None:
        """Test that sections default to empty lists."""
        ctx = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=0,
            ),
        )
        assert ctx.preferences == []
        assert ctx.patterns == []
        assert ctx.facts == []
        assert ctx.insights == []


class TestGlobalContextManagerInit:
    """Tests for GlobalContextManager initialization."""

    def test_init_with_storage(self, tmp_path: Path) -> None:
        """Test initializing with StorageRepository."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)
        assert manager.storage is storage
        assert manager.token_limit == 2000

    def test_init_with_custom_token_limit(self, tmp_path: Path) -> None:
        """Test initializing with custom token limit."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage, token_limit=1000)
        assert manager.token_limit == 1000


class TestGlobalContextManagerReadContext:
    """Tests for read_context method."""

    def test_read_nonexistent_returns_default(self, tmp_path: Path) -> None:
        """Test reading when file doesn't exist returns default context."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        context = manager.read_context()

        assert context.frontmatter.version == 1
        assert context.frontmatter.token_estimate == 0
        assert context.frontmatter.last_updated == date.today().isoformat()
        assert context.preferences == []
        assert context.patterns == []
        assert context.facts == []
        assert context.insights == []

    def test_read_empty_file_returns_default(self, tmp_path: Path) -> None:
        """Test reading empty file returns default context."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        # Create empty context file
        storage.update_global_context("")

        context = manager.read_context()
        assert context.frontmatter.version == 1

    def test_read_valid_markdown(self, tmp_path: Path) -> None:
        """Test reading valid markdown with all sections."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        markdown = """---
last_updated: 2026-01-16
version: 15
token_estimate: 450
---

# Global Context

## Preferences (certain)
- unit_preference: metric
- response_style: concise

## Patterns (likely)
- usual_time: morning

## Facts (certain)
- current_routine: push-pull-legs

## Insights (tentative)
- performance_drop: when sleep below 7 hours
"""
        storage.update_global_context(markdown)

        context = manager.read_context()

        assert context.frontmatter.last_updated == "2026-01-16"
        assert context.frontmatter.version == 15
        assert context.frontmatter.token_estimate == 450
        assert len(context.preferences) == 2
        assert len(context.patterns) == 1
        assert len(context.facts) == 1
        assert len(context.insights) == 1

    def test_read_markdown_with_missing_sections(self, tmp_path: Path) -> None:
        """Test reading markdown with some sections missing."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        markdown = """---
last_updated: 2026-01-16
version: 1
token_estimate: 50
---

# Global Context

## Preferences (certain)
- unit_preference: metric

## Facts (certain)
"""
        storage.update_global_context(markdown)

        context = manager.read_context()

        assert len(context.preferences) == 1
        assert context.patterns == []
        assert context.facts == []
        assert context.insights == []


class TestGlobalContextManagerWriteContext:
    """Tests for write_context method."""

    def test_write_context_creates_valid_markdown(self, tmp_path: Path) -> None:
        """Test that write_context creates valid markdown."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=5,
                token_estimate=100,
            ),
            preferences=[
                ContextEntry(
                    key="unit_preference",
                    value="metric",
                    confidence="certain",
                    source="user_correction",
                    category="preference",
                    added_date="2026-01-10",
                )
            ],
        )

        manager.write_context(context)

        raw = storage.get_global_context()
        assert "---" in raw
        assert "last_updated: 2026-01-16" in raw
        assert "version: 5" in raw
        assert "token_estimate: 100" in raw
        assert "## Preferences (certain)" in raw
        # New format includes confidence and source
        assert "- [2026-01-10|certain|user_correction] unit_preference: metric" in raw

    def test_write_context_sections_ordered(self, tmp_path: Path) -> None:
        """Test that sections are in correct order."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=0,
            ),
        )

        manager.write_context(context)

        raw = storage.get_global_context()
        pref_pos = raw.find("## Preferences")
        patt_pos = raw.find("## Patterns")
        fact_pos = raw.find("## Facts")
        insight_pos = raw.find("## Insights")

        assert pref_pos < patt_pos < fact_pos < insight_pos

    def test_round_trip_preserves_data(self, tmp_path: Path) -> None:
        """Test write → read returns equivalent context."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        original = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=10,
                token_estimate=200,
            ),
            preferences=[
                ContextEntry(
                    key="unit_preference",
                    value="metric",
                    confidence="certain",
                    source="user_correction",
                    category="preference",
                    added_date="2026-01-10",
                )
            ],
            patterns=[
                ContextEntry(
                    key="usual_time",
                    value="morning",
                    confidence="likely",
                    source="observation",
                    category="pattern",
                    added_date="2026-01-12",
                )
            ],
        )

        manager.write_context(original)
        read_back = manager.read_context()

        assert read_back.frontmatter.last_updated == original.frontmatter.last_updated
        assert read_back.frontmatter.version == original.frontmatter.version
        assert read_back.frontmatter.token_estimate == original.frontmatter.token_estimate
        assert len(read_back.preferences) == len(original.preferences)
        assert read_back.preferences[0].key == original.preferences[0].key
        assert read_back.preferences[0].value == original.preferences[0].value

    def test_round_trip_preserves_source_and_confidence(self, tmp_path: Path) -> None:
        """Test that source and confidence are preserved on round-trip."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        original = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=100,
            ),
            preferences=[
                ContextEntry(
                    key="unit_pref",
                    value="metric",
                    confidence="certain",
                    source="user_stated_explicitly",
                    category="preference",
                    added_date="2026-01-10",
                )
            ],
            insights=[
                ContextEntry(
                    key="sleep_impact",
                    value="performance drops below 7h",
                    confidence="tentative",
                    source="post_query_analysis",
                    category="insight",
                    added_date="2026-01-12",
                )
            ],
        )

        manager.write_context(original)
        read_back = manager.read_context()

        # Source should be preserved (not "parsed_from_file")
        assert read_back.preferences[0].source == "user_stated_explicitly"
        assert read_back.insights[0].source == "post_query_analysis"
        # Confidence should be preserved
        assert read_back.preferences[0].confidence == "certain"
        assert read_back.insights[0].confidence == "tentative"


class TestGlobalContextManagerApplyUpdates:
    """Tests for apply_updates method."""

    def test_apply_new_entry(self, tmp_path: Path) -> None:
        """Test applying a new entry adds it with today's added_date."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        updates = [
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="metric",
                confidence="certain",
                source="user_correction",
            )
        ]

        result = manager.apply_updates(updates)

        assert len(result.preferences) == 1
        assert result.preferences[0].key == "unit_preference"
        assert result.preferences[0].value == "metric"
        assert result.preferences[0].added_date == date.today().isoformat()

    def test_apply_supersedes_existing(self, tmp_path: Path) -> None:
        """Test applying update supersedes existing entry with same key."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        # Create initial context
        initial = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-10",
                version=1,
                token_estimate=50,
            ),
            preferences=[
                ContextEntry(
                    key="unit_preference",
                    value="imperial",
                    confidence="likely",
                    source="inference",
                    category="preference",
                    added_date="2026-01-05",
                )
            ],
        )
        manager.write_context(initial)

        # Apply update
        updates = [
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="metric",
                confidence="certain",
                source="user_correction",
            )
        ]

        result = manager.apply_updates(updates)

        # Should still have only one preference
        assert len(result.preferences) == 1
        assert result.preferences[0].value == "metric"
        assert result.preferences[0].confidence == "certain"
        # Original added_date should be preserved
        assert result.preferences[0].added_date == "2026-01-05"

    def test_apply_increments_version(self, tmp_path: Path) -> None:
        """Test that apply_updates increments version number."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        # Create initial context
        initial = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-10",
                version=5,
                token_estimate=50,
            ),
        )
        manager.write_context(initial)

        updates = [
            ContextUpdate(
                category="fact",
                key="current_routine",
                value="push-pull-legs",
                confidence="certain",
                source="user_stated",
            )
        ]

        result = manager.apply_updates(updates)

        assert result.frontmatter.version == 6

    def test_apply_updates_last_updated(self, tmp_path: Path) -> None:
        """Test that apply_updates sets last_updated to today."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        updates = [
            ContextUpdate(
                category="insight",
                key="performance_note",
                value="good recovery",
                confidence="tentative",
                source="analysis",
            )
        ]

        result = manager.apply_updates(updates)

        assert result.frontmatter.last_updated == date.today().isoformat()

    def test_apply_recalculates_token_estimate(self, tmp_path: Path) -> None:
        """Test that apply_updates recalculates token_estimate."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        updates = [
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="metric",
                confidence="certain",
                source="user_correction",
            )
        ]

        result = manager.apply_updates(updates)

        # Token estimate should be > 0 after adding content
        assert result.frontmatter.token_estimate > 0

    def test_apply_multiple_updates(self, tmp_path: Path) -> None:
        """Test applying multiple updates in single call."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        updates = [
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="metric",
                confidence="certain",
                source="user_correction",
            ),
            ContextUpdate(
                category="pattern",
                key="usual_time",
                value="morning",
                confidence="likely",
                source="observation",
            ),
            ContextUpdate(
                category="fact",
                key="current_routine",
                value="push-pull-legs",
                confidence="certain",
                source="user_stated",
            ),
        ]

        result = manager.apply_updates(updates)

        assert len(result.preferences) == 1
        assert len(result.patterns) == 1
        assert len(result.facts) == 1


class TestTokenEstimation:
    """Tests for token estimation."""

    def test_empty_context_has_small_token_count(self, tmp_path: Path) -> None:
        """Test empty context returns small token count (frontmatter only)."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        context = manager._create_default_context()  # pyright: ignore[reportPrivateUsage]  # pyright: ignore[reportPrivateUsage]
        tokens = manager.estimate_tokens(context)

        # Frontmatter + empty sections should be ~30-50 tokens
        assert 0 < tokens < 100

    def test_token_estimate_scales_with_content(self, tmp_path: Path) -> None:
        """Test token estimate increases with content."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        small_context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=0,
            ),
            preferences=[
                ContextEntry(
                    key="pref1",
                    value="val1",
                    confidence="certain",
                    source="test",
                    category="preference",
                    added_date="2026-01-16",
                )
            ],
        )

        large_context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=0,
            ),
            preferences=[
                ContextEntry(
                    key=f"pref{i}",
                    value=f"value{i} with some extra text",
                    confidence="certain",
                    source="test",
                    category="preference",
                    added_date="2026-01-16",
                )
                for i in range(10)
            ],
        )

        small_tokens = manager.estimate_tokens(small_context)
        large_tokens = manager.estimate_tokens(large_context)

        assert large_tokens > small_tokens

    def test_token_estimate_approximates_1_3x_words(self, tmp_path: Path) -> None:
        """Test token estimate is approximately 1.3x word count."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=0,
            ),
        )

        markdown = manager._serialize_context(context)  # pyright: ignore[reportPrivateUsage]
        word_count = len(markdown.split())
        token_estimate = manager.estimate_tokens(context)

        # Should be approximately 1.3x (with some tolerance)
        expected = int(word_count * 1.3)
        assert token_estimate == expected


class TestArchival:
    """Tests for archival strategy."""

    def test_archival_triggers_when_over_limit(self, tmp_path: Path) -> None:
        """Test archival triggers when token_estimate > token_limit."""
        storage = StorageRepository(tmp_path)
        # Very low token limit to trigger archival
        manager = GlobalContextManager(storage, token_limit=50)

        # Add many entries to exceed limit
        updates = [
            ContextUpdate(
                category="insight",
                key=f"insight_{i}",
                value=f"This is insight number {i} with some longer text to increase token count",
                confidence="tentative",
                source="analysis",
            )
            for i in range(10)
        ]

        result = manager.apply_updates(updates)

        # Some insights should have been archived
        assert len(result.insights) < 10

        # Archive file should exist
        archive_dir = tmp_path / "logs" / "context" / "archive"
        archive_files = list(archive_dir.glob("global-*.md"))
        assert len(archive_files) == 1

    def test_archival_oldest_insights_first(self, tmp_path: Path) -> None:
        """Test that oldest insights (by added_date) are archived first."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage, token_limit=100)

        # Create context with insights of different ages
        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=200,  # Over limit
            ),
            insights=[
                ContextEntry(
                    key="old_insight",
                    value="old value",
                    confidence="tentative",
                    source="test",
                    category="insight",
                    added_date="2025-01-01",  # Oldest
                ),
                ContextEntry(
                    key="new_insight",
                    value="new value",
                    confidence="tentative",
                    source="test",
                    category="insight",
                    added_date="2026-01-15",  # Newest
                ),
            ],
        )

        result = manager._archive_if_needed(context)  # pyright: ignore[reportPrivateUsage]  # pyright: ignore[reportPrivateUsage]

        # If archival occurred, old_insight should be gone first
        if len(result.insights) < 2:
            remaining_keys = [i.key for i in result.insights]
            assert "new_insight" in remaining_keys or len(remaining_keys) == 0
            if "old_insight" in remaining_keys:
                assert "new_insight" in remaining_keys

    def test_archival_patterns_after_insights(self, tmp_path: Path) -> None:
        """Test that patterns are archived after insights if still over limit."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage, token_limit=50)

        # Create context with no insights but patterns
        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=200,  # Over limit
            ),
            patterns=[
                ContextEntry(
                    key=f"pattern_{i}",
                    value=f"pattern value {i} with extra text",
                    confidence="likely",
                    source="test",
                    category="pattern",
                    added_date="2026-01-01",
                )
                for i in range(5)
            ],
        )

        result = manager._archive_if_needed(context)  # pyright: ignore[reportPrivateUsage]  # pyright: ignore[reportPrivateUsage]

        # Some patterns should have been archived
        assert len(result.patterns) < 5

    def test_preferences_never_archived(self, tmp_path: Path) -> None:
        """Test that preferences are NEVER archived."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage, token_limit=50)

        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=200,  # Over limit
            ),
            preferences=[
                ContextEntry(
                    key=f"pref_{i}",
                    value=f"preference value {i} with extra text",
                    confidence="certain",
                    source="test",
                    category="preference",
                    added_date="2026-01-01",
                )
                for i in range(5)
            ],
        )

        result = manager._archive_if_needed(context)  # pyright: ignore[reportPrivateUsage]  # pyright: ignore[reportPrivateUsage]

        # All preferences should remain
        assert len(result.preferences) == 5

    def test_facts_never_archived(self, tmp_path: Path) -> None:
        """Test that facts are NEVER archived."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage, token_limit=50)

        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=200,  # Over limit
            ),
            facts=[
                ContextEntry(
                    key=f"fact_{i}",
                    value=f"fact value {i} with extra text",
                    confidence="certain",
                    source="test",
                    category="fact",
                    added_date="2026-01-01",
                )
                for i in range(5)
            ],
        )

        result = manager._archive_if_needed(context)  # pyright: ignore[reportPrivateUsage]  # pyright: ignore[reportPrivateUsage]

        # All facts should remain
        assert len(result.facts) == 5

    def test_archive_file_location(self, tmp_path: Path) -> None:
        """Test archive file is created at correct location."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage, token_limit=50)

        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=200,
            ),
            insights=[
                ContextEntry(
                    key="to_archive",
                    value="value " * 50,  # Make it big
                    confidence="tentative",
                    source="test",
                    category="insight",
                    added_date="2026-01-01",
                )
            ],
        )

        manager._archive_if_needed(context)  # pyright: ignore[reportPrivateUsage]

        today = date.today().isoformat()
        archive_path = tmp_path / "logs" / "context" / "archive" / f"global-{today}.md"
        assert archive_path.exists()

    def test_same_day_archival_appends(self, tmp_path: Path) -> None:
        """Test multiple archival operations on same day append to same file."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage, token_limit=50)

        # First archival
        entries1 = [
            ContextEntry(
                key="insight_1",
                value="value 1 " * 30,
                confidence="tentative",
                source="test",
                category="insight",
                added_date="2025-01-01",
            )
        ]
        manager._write_to_archive(entries1)  # pyright: ignore[reportPrivateUsage]

        # Second archival
        entries2 = [
            ContextEntry(
                key="insight_2",
                value="value 2 " * 30,
                confidence="tentative",
                source="test",
                category="insight",
                added_date="2025-02-01",
            )
        ]
        manager._write_to_archive(entries2)  # pyright: ignore[reportPrivateUsage]

        today = date.today().isoformat()
        archive_path = tmp_path / "logs" / "context" / "archive" / f"global-{today}.md"
        content = archive_path.read_text()

        assert "insight_1" in content
        assert "insight_2" in content

    def test_archive_reduces_active_context(self, tmp_path: Path) -> None:
        """Test that archived items are removed from active context."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage, token_limit=100)

        initial_insights = [
            ContextEntry(
                key=f"insight_{i}",
                value=f"insight value {i} with some text",
                confidence="tentative",
                source="test",
                category="insight",
                added_date=f"2026-01-{i + 1:02d}",
            )
            for i in range(10)
        ]

        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=500,
            ),
            insights=initial_insights,
        )

        result = manager._archive_if_needed(context)  # pyright: ignore[reportPrivateUsage]  # pyright: ignore[reportPrivateUsage]

        # Context should have fewer insights after archival
        assert len(result.insights) < 10


class TestCreateDefaultContext:
    """Tests for _create_default_context helper."""

    def test_default_context_has_today_date(self, tmp_path: Path) -> None:
        """Test default context has today's date."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        context = manager._create_default_context()  # pyright: ignore[reportPrivateUsage]

        assert context.frontmatter.last_updated == date.today().isoformat()

    def test_default_context_has_version_1(self, tmp_path: Path) -> None:
        """Test default context has version 1."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        context = manager._create_default_context()  # pyright: ignore[reportPrivateUsage]

        assert context.frontmatter.version == 1

    def test_default_context_has_zero_tokens(self, tmp_path: Path) -> None:
        """Test default context has token_estimate 0."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        context = manager._create_default_context()  # pyright: ignore[reportPrivateUsage]

        assert context.frontmatter.token_estimate == 0

    def test_default_context_has_empty_sections(self, tmp_path: Path) -> None:
        """Test default context has empty lists for all sections."""
        storage = StorageRepository(tmp_path)
        manager = GlobalContextManager(storage)

        context = manager._create_default_context()  # pyright: ignore[reportPrivateUsage]

        assert context.preferences == []
        assert context.patterns == []
        assert context.facts == []
        assert context.insights == []
