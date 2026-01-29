"""Tests for Parser correction content merge behavior.

Story 21.6: Fix CORRECTION Raw Content Merge.

This module tests that the Parser:
1. Receives full raw_content in correction mode (not truncated 80 chars)
2. Includes merge instructions in the prompt
3. Outputs merged content, not literal correction text

These are unit tests that mock the LLM - actual merge behavior validation
requires integration tests with real LLM (see test_correction_flow.py).
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel
from quilto.agents import ParserAgent
from quilto.agents.models import ParserInput


class StrengthSchema(BaseModel):
    """Schema for strength training domain (test data)."""

    exercise: str
    weight_kg: float | None = None
    reps: int | None = None
    sets: int | None = None


class CardioSchema(BaseModel):
    """Schema for cardio domain (test data)."""

    activity: str
    duration_min: int | None = None
    distance_km: float | None = None


class MockEntry:
    """Mock Entry object for testing."""

    def __init__(
        self,
        entry_id: str,
        entry_date: date,
        raw_content: str,
        parsed_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize mock entry.

        Args:
            entry_id: Entry ID in format YYYY-MM-DD_HH-MM-SS.
            entry_date: Date of the entry.
            raw_content: Raw markdown content.
            parsed_data: Domain-specific parsed data.
        """
        self.id = entry_id
        self.date = entry_date
        self.raw_content = raw_content
        self.parsed_data = parsed_data
        # Parse timestamp from entry_id
        date_str, time_str = entry_id.split("_")
        time_parts = time_str.split("-")
        self.timestamp = datetime(
            int(date_str[:4]),
            int(date_str[5:7]),
            int(date_str[8:10]),
            int(time_parts[0]),
            int(time_parts[1]),
            int(time_parts[2]),
        )


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    return MagicMock()


@pytest.fixture
def long_content_entry() -> MockEntry:
    """Create an entry with content longer than 80 characters.

    This tests that correction mode preserves full content.
    """
    return MockEntry(
        entry_id="2026-01-26_10-30-00",
        entry_date=date(2026, 1, 26),
        raw_content=(
            "Ran treadmill for 35 minutes at 8kph, felt really good today. "
            "This is my longest cardio session this week and I'm proud of the progress."
        ),
        parsed_data={"cardio": {"activity": "treadmill", "duration_min": 35}},
    )


@pytest.fixture
def recent_entries_for_merge() -> list[MockEntry]:
    """Create entries for merge testing."""
    return [
        MockEntry(
            entry_id="2026-01-26_10-30-00",
            entry_date=date(2026, 1, 26),
            raw_content="Ran treadmill for 35 minutes at 8kph",
            parsed_data={"cardio": {"activity": "treadmill", "duration_min": 35}},
        ),
        MockEntry(
            entry_id="2026-01-26_18-33-00",
            entry_date=date(2026, 1, 26),
            raw_content="Did 5 sets of bench press at 80kg, felt strong",
            parsed_data={
                "strength": {
                    "exercise": "bench press",
                    "weight_kg": 80,
                    "reps": 5,
                    "sets": 5,
                }
            },
        ),
    ]


# =============================================================================
# Task 4.2: Test prompt includes merge instructions
# =============================================================================


class TestCorrectionPromptMergeInstructions:
    """Tests that build_prompt includes MERGE RULES when correction_mode=True."""

    def test_correction_prompt_includes_merge_instructions(
        self, mock_llm_client: MagicMock, recent_entries_for_merge: list[MockEntry]
    ) -> None:
        """Verify build_prompt includes MERGE RULES section when correction_mode=True."""
        parser = ParserAgent(mock_llm_client)

        parser_input = ParserInput(
            raw_input="actually it was 20 minutes at 7.5kph",
            timestamp=datetime(2026, 1, 26, 20, 0, 0),
            domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
            vocabulary={},
            correction_mode=True,
            correction_target="the treadmill entry",
            recent_entries=recent_entries_for_merge,
        )

        prompt = parser.build_prompt(parser_input)

        # Verify merge rules section exists
        assert "=== CORRECTION MERGE RULES ===" in prompt
        assert "MERGE the correction INTO the original entry's raw_content" in prompt
        assert "PRESERVE all context from the original" in prompt
        assert "OUTPUT a complete standalone description" in prompt

    def test_correction_prompt_includes_merge_examples(
        self, mock_llm_client: MagicMock, recent_entries_for_merge: list[MockEntry]
    ) -> None:
        """Verify build_prompt includes MERGE EXAMPLES section when correction_mode=True."""
        parser = ParserAgent(mock_llm_client)

        parser_input = ParserInput(
            raw_input="actually it was 20 minutes at 7.5kph",
            timestamp=datetime(2026, 1, 26, 20, 0, 0),
            domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
            vocabulary={},
            correction_mode=True,
            correction_target="the treadmill entry",
            recent_entries=recent_entries_for_merge,
        )

        prompt = parser.build_prompt(parser_input)

        # Verify merge examples section exists
        assert "=== CORRECTION MERGE EXAMPLES ===" in prompt
        # Check specific examples
        assert "Ran treadmill for 20 minutes at 7.5kph" in prompt  # Example 1 correct
        assert "LOSES CONTEXT" in prompt  # Example 1 wrong explanation
        assert "Did 4 sets of bench press at 80kg" in prompt  # Example 2 correct

    def test_normal_mode_excludes_merge_instructions(self, mock_llm_client: MagicMock) -> None:
        """Verify build_prompt does NOT include MERGE RULES when correction_mode=False."""
        parser = ParserAgent(mock_llm_client)

        parser_input = ParserInput(
            raw_input="Ran treadmill for 35 minutes at 8kph",
            timestamp=datetime(2026, 1, 26, 20, 0, 0),
            domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
            vocabulary={},
            correction_mode=False,  # Normal mode
            recent_entries=[],
        )

        prompt = parser.build_prompt(parser_input)

        # Merge rules should NOT be present in normal mode
        assert "=== CORRECTION MERGE RULES ===" not in prompt
        assert "=== CORRECTION MERGE EXAMPLES ===" not in prompt

    def test_raw_content_instruction_mentions_merge(
        self, mock_llm_client: MagicMock, recent_entries_for_merge: list[MockEntry]
    ) -> None:
        """Verify OUTPUT section's raw_content instruction mentions merge behavior."""
        parser = ParserAgent(mock_llm_client)

        parser_input = ParserInput(
            raw_input="actually it was 20 minutes at 7.5kph",
            timestamp=datetime(2026, 1, 26, 20, 0, 0),
            domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
            vocabulary={},
            correction_mode=True,
            correction_target="the treadmill entry",
            recent_entries=recent_entries_for_merge,
        )

        prompt = parser.build_prompt(parser_input)

        # Check updated raw_content instruction
        assert "- raw_content: the MERGED content (in correction mode)" in prompt


# =============================================================================
# Task 4.3: Test Parser receives full raw_content
# =============================================================================


class TestCorrectionFullRawContent:
    """Tests that format_recent_entries preserves full content in correction mode."""

    def test_correction_mode_preserves_full_content(
        self, mock_llm_client: MagicMock, long_content_entry: MockEntry
    ) -> None:
        """Verify format_recent_entries does NOT truncate in correction mode."""
        parser = ParserAgent(mock_llm_client)

        result = parser.format_recent_entries([long_content_entry], correction_mode=True)

        # Full content should be present (not truncated at 80 chars)
        assert "progress" in result  # This word is beyond 80 chars
        assert "..." not in result  # No truncation marker

    def test_normal_mode_truncates_content(self, mock_llm_client: MagicMock, long_content_entry: MockEntry) -> None:
        """Verify format_recent_entries DOES truncate in normal mode (80 chars)."""
        parser = ParserAgent(mock_llm_client)

        result = parser.format_recent_entries([long_content_entry], correction_mode=False)

        # Content should be truncated at 80 chars
        assert "..." in result  # Truncation marker present
        assert "progress" not in result  # Word beyond 80 chars not present

    def test_prompt_contains_full_raw_content_in_correction_mode(
        self, mock_llm_client: MagicMock, long_content_entry: MockEntry
    ) -> None:
        """Verify build_prompt includes full raw_content when correction_mode=True."""
        parser = ParserAgent(mock_llm_client)

        parser_input = ParserInput(
            raw_input="actually it was 20 minutes",
            timestamp=datetime(2026, 1, 26, 20, 0, 0),
            domain_schemas={"cardio": CardioSchema},
            vocabulary={},
            correction_mode=True,
            correction_target="the treadmill entry",
            recent_entries=[long_content_entry],
        )

        prompt = parser.build_prompt(parser_input)

        # Full content should be in the prompt
        assert "progress" in prompt  # Word beyond 80 chars
        assert long_content_entry.raw_content in prompt

    def test_correction_mode_empty_entries_returns_no_entries(self, mock_llm_client: MagicMock) -> None:
        """Verify format_recent_entries returns placeholder for empty list in correction mode."""
        parser = ParserAgent(mock_llm_client)

        result = parser.format_recent_entries([], correction_mode=True)

        # Should return placeholder, not crash or return empty string
        assert result == "(No recent entries)"


# =============================================================================
# Task 4.4 & 4.5: Tests requiring LLM behavior
# =============================================================================


class TestCorrectionMergeBehaviorWithLLM:
    """Tests for actual merge behavior (require --use-real-ollama)."""

    @pytest.mark.asyncio
    async def test_correction_does_not_literal_replace(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        recent_entries_for_merge: list[MockEntry],
    ) -> None:
        """Verify output is merged, not literal correction text.

        This test validates that the Parser doesn't just output the user's
        correction text verbatim, but merges it with the original content.

        Skip if not using real LLM.
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for LLM behavior testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        client = LLMClient(config)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="actually it was 20 minutes at 7.5kph",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="the treadmill entry",
                recent_entries=recent_entries_for_merge,
            )
        )

        # raw_content should NOT be the literal correction text
        assert result.raw_content != "actually it was 20 minutes at 7.5kph", (
            f"raw_content should be MERGED, not literal input. Got: {result.raw_content}"
        )
        # Should contain the activity context from original
        assert "treadmill" in result.raw_content.lower() or "ran" in result.raw_content.lower(), (
            f"raw_content should preserve activity context. Got: {result.raw_content}"
        )
        # Should have the corrected values
        assert "20" in result.raw_content, f"raw_content should have corrected duration. Got: {result.raw_content}"

    @pytest.mark.asyncio
    async def test_correction_addition_appends_to_original(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
    ) -> None:
        """Verify addition case merges new info with original.

        Tests: "I also did stretching after" should append to original.
        Skip if not using real LLM.
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for LLM behavior testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        client = LLMClient(config)
        parser = ParserAgent(client)

        entries = [
            MockEntry(
                entry_id="2026-01-26_09-00-00",
                entry_date=date(2026, 1, 26),
                raw_content="Morning run 5km",
                parsed_data={"cardio": {"activity": "running", "distance_km": 5}},
            ),
        ]

        result = await parser.parse(
            ParserInput(
                raw_input="I also did stretching after",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={"cardio": CardioSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="the morning run",
                recent_entries=entries,
            )
        )

        # raw_content should contain both original content AND addition
        assert "run" in result.raw_content.lower() or "5km" in result.raw_content.lower(), (
            f"raw_content should preserve original run info. Got: {result.raw_content}"
        )
        assert "stretch" in result.raw_content.lower(), (
            f"raw_content should include stretching addition. Got: {result.raw_content}"
        )
