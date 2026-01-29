"""Baseline and improved tests for Parser correction entry matching.

Story 21.4: Improve Parser Correction Entry Matching.

This module establishes baseline success rates for Parser correction mode
and tests improved matching behavior after prompt/format changes.

Baseline Results (Task 1.4 - Recorded 2026-01-29):
| Test Case                    | Baseline | Post-Improvement | Notes                                    |
|------------------------------|----------|------------------|------------------------------------------|
| Date/time matching (yesterday)| PASS     | PASS             | Correctly matched 2026-01-25_09-00-00    |
| Date/time matching (10:30)   | PASS     | PASS             | Correctly matched 2026-01-26_10-30-00    |
| Exercise matching (bench)    | PASS     | PASS             | Correctly matched 2026-01-26_18-33-00    |
| Exercise matching (running)  | FAIL     | PASS             | Now distinguishes running from treadmill |
| Value matching (5 sets)      | FAIL     | FAIL             | LLM still struggles with numeric matches |
| Value matching (3km)         | FAIL     | FAIL             | is_correction=false despite context      |
| Ambiguous handling           | PASS     | PASS             | Correctly returned null target           |
| **Overall Rate**             | **57%**  | **71%**          | Improvement: +14pp (Task 4 skipped)      |

Note: Tests require --use-real-ollama flag for LLM behavior validation.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any

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
# Baseline Test Fixtures
# =============================================================================


@pytest.fixture
def baseline_recent_entries() -> list[MockEntry]:
    """Create recent entries for baseline testing.

    Returns:
        List of mock entries representing recent workouts.
    """
    return [
        MockEntry(
            entry_id="2026-01-26_10-30-00",
            entry_date=date(2026, 1, 26),
            raw_content="40 minutes on the treadmill at 8kph. Felt good today.",
            parsed_data={"cardio": {"activity": "treadmill", "duration_min": 40}},
        ),
        MockEntry(
            entry_id="2026-01-26_18-33-00",
            entry_date=date(2026, 1, 26),
            raw_content="Bench press 80kg for 5 reps, 3 sets. New PR!",
            parsed_data={
                "strength": {
                    "exercise": "bench press",
                    "weight_kg": 80,
                    "reps": 5,
                    "sets": 3,
                }
            },
        ),
        MockEntry(
            entry_id="2026-01-25_09-00-00",
            entry_date=date(2026, 1, 25),
            raw_content="Morning run 3km in 20 minutes. Nice weather.",
            parsed_data={"cardio": {"activity": "running", "distance_km": 3}},
        ),
        MockEntry(
            entry_id="2026-01-25_17-45-00",
            entry_date=date(2026, 1, 25),
            raw_content="Squats 100kg 5x5. Legs are tired.",
            parsed_data={
                "strength": {
                    "exercise": "squat",
                    "weight_kg": 100,
                    "reps": 5,
                    "sets": 5,
                }
            },
        ),
    ]


@pytest.fixture
def ambiguous_entries() -> list[MockEntry]:
    """Create entries with multiple similar workouts for ambiguity testing.

    Returns:
        List of mock entries with multiple strength workouts on same day.
    """
    return [
        MockEntry(
            entry_id="2026-01-26_10-00-00",
            entry_date=date(2026, 1, 26),
            raw_content="Bench press 75kg for 5 reps, 3 sets. Warmup.",
            parsed_data={
                "strength": {
                    "exercise": "bench press",
                    "weight_kg": 75,
                    "reps": 5,
                    "sets": 3,
                }
            },
        ),
        MockEntry(
            entry_id="2026-01-26_11-30-00",
            entry_date=date(2026, 1, 26),
            raw_content="Bench press 80kg for 3 reps, 5 sets. Working sets.",
            parsed_data={
                "strength": {
                    "exercise": "bench press",
                    "weight_kg": 80,
                    "reps": 3,
                    "sets": 5,
                }
            },
        ),
    ]


# =============================================================================
# Baseline Tests - Task 1.2
# =============================================================================


class TestCorrectionBaselineDateTimeMatching:
    """Baseline tests for date/time matching in correction mode.

    Baseline Success Rate: 100% (2/2 PASS)
    Post-Improvement Rate: 100% (2/2 PASS)
    """

    @pytest.mark.asyncio
    async def test_correction_baseline_date_time_matching_yesterday(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        baseline_recent_entries: list[MockEntry],
    ) -> None:
        """Test correction matching by relative date reference.

        Tests: "fix yesterday's entry"
        Expected: Should match entry from 2026-01-25

        Baseline result: TBD
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for baseline testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        client = LLMClient(config)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Fix yesterday's morning run - it was actually 5km not 3km",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),  # "Today" is Jan 26
                domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="yesterday's morning run",
                recent_entries=baseline_recent_entries,
            )
        )

        # Record baseline behavior
        assert result.is_correction is True, "Parser should recognize correction mode"
        # Check if target_entry_id matches yesterday's run (2026-01-25_09-00-00)
        if result.target_entry_id == "2026-01-25_09-00-00":
            # BASELINE PASS: Parser correctly identified yesterday's run
            pass
        else:
            # BASELINE FAIL: Record actual behavior for analysis
            pytest.fail(
                f"Baseline date matching failed. "
                f"Expected: 2026-01-25_09-00-00, Got: {result.target_entry_id}. "
                f"Notes: {result.extraction_notes}"
            )

    @pytest.mark.asyncio
    async def test_correction_baseline_date_time_matching_specific_time(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        baseline_recent_entries: list[MockEntry],
    ) -> None:
        """Test correction matching by specific time reference.

        Tests: "the 10:30 workout"
        Expected: Should match entry 2026-01-26_10-30-00 (treadmill)

        Baseline result: TBD
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for baseline testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        client = LLMClient(config)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Fix the 10:30 workout - I actually did 45 minutes, not 40",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="the 10:30 workout",
                recent_entries=baseline_recent_entries,
            )
        )

        assert result.is_correction is True, "Parser should recognize correction mode"
        if result.target_entry_id == "2026-01-26_10-30-00":
            # BASELINE PASS
            pass
        else:
            pytest.fail(
                f"Baseline time matching failed. "
                f"Expected: 2026-01-26_10-30-00, Got: {result.target_entry_id}. "
                f"Notes: {result.extraction_notes}"
            )


class TestCorrectionBaselineExerciseMatching:
    """Baseline tests for exercise type matching in correction mode.

    Baseline Success Rate: 50% (1/2 PASS - bench PASS, running FAIL)
    Post-Improvement Rate: 100% (2/2 PASS - running now distinguishes from treadmill)
    """

    @pytest.mark.asyncio
    async def test_correction_baseline_exercise_matching_bench_press(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        baseline_recent_entries: list[MockEntry],
    ) -> None:
        """Test correction matching by exercise name.

        Tests: "fix the bench press entry"
        Expected: Should match entry 2026-01-26_18-33-00

        Baseline result: TBD
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for baseline testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        client = LLMClient(config)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Fix the bench press entry - it was 85kg not 80kg",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
                vocabulary={"bp": "bench press"},
                correction_mode=True,
                correction_target="the bench press entry",
                recent_entries=baseline_recent_entries,
            )
        )

        assert result.is_correction is True, "Parser should recognize correction mode"
        if result.target_entry_id == "2026-01-26_18-33-00":
            # BASELINE PASS
            pass
        else:
            pytest.fail(
                f"Baseline exercise matching failed. "
                f"Expected: 2026-01-26_18-33-00, Got: {result.target_entry_id}. "
                f"Notes: {result.extraction_notes}"
            )

    @pytest.mark.asyncio
    async def test_correction_baseline_exercise_matching_running(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        baseline_recent_entries: list[MockEntry],
    ) -> None:
        """Test correction matching by activity name (running).

        Tests: "fix the running entry"
        Expected: Should match entry 2026-01-25_09-00-00

        Baseline result: TBD
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for baseline testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        client = LLMClient(config)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Fix the running entry - distance was 5km",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="the running entry",
                recent_entries=baseline_recent_entries,
            )
        )

        assert result.is_correction is True, "Parser should recognize correction mode"
        if result.target_entry_id == "2026-01-25_09-00-00":
            # BASELINE PASS
            pass
        else:
            pytest.fail(
                f"Baseline exercise matching failed. "
                f"Expected: 2026-01-25_09-00-00, Got: {result.target_entry_id}. "
                f"Notes: {result.extraction_notes}"
            )


class TestCorrectionBaselineValueMatching:
    """Baseline tests for value-based matching in correction mode.

    Baseline Success Rate: 0% (0/2 PASS - both tests FAIL)
    Post-Improvement Rate: 0% (0/2 PASS - LLM still struggles with numeric value matching)
    Note: Value matching remains the weakest area; consider pre-matching heuristics in future.
    """

    @pytest.mark.asyncio
    async def test_correction_baseline_value_matching_sets(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        baseline_recent_entries: list[MockEntry],
    ) -> None:
        """Test correction matching by specific value (5 sets).

        Tests: "where I said 5 sets"
        Expected: Should match squat entry 2026-01-25_17-45-00 (5x5)

        Baseline result: TBD
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for baseline testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        client = LLMClient(config)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Fix the entry where I said 5 sets - it was actually 4 sets",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="where I said 5 sets",
                recent_entries=baseline_recent_entries,
            )
        )

        assert result.is_correction is True, "Parser should recognize correction mode"
        # Note: Both squat (5x5) and bench (3 sets) have sets - squat is unique with 5 sets
        if result.target_entry_id == "2026-01-25_17-45-00":
            # BASELINE PASS
            pass
        else:
            pytest.fail(
                f"Baseline value matching failed. "
                f"Expected: 2026-01-25_17-45-00, Got: {result.target_entry_id}. "
                f"Notes: {result.extraction_notes}"
            )

    @pytest.mark.asyncio
    async def test_correction_baseline_value_matching_distance(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        baseline_recent_entries: list[MockEntry],
    ) -> None:
        """Test correction matching by distance value.

        Tests: "the 3km run"
        Expected: Should match entry 2026-01-25_09-00-00

        Baseline result: TBD
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for baseline testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        client = LLMClient(config)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="The 3km run was actually 5km",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="the 3km run",
                recent_entries=baseline_recent_entries,
            )
        )

        assert result.is_correction is True, "Parser should recognize correction mode"
        if result.target_entry_id == "2026-01-25_09-00-00":
            # BASELINE PASS
            pass
        else:
            pytest.fail(
                f"Baseline value matching failed. "
                f"Expected: 2026-01-25_09-00-00, Got: {result.target_entry_id}. "
                f"Notes: {result.extraction_notes}"
            )


class TestCorrectionBaselineAmbiguousCase:
    """Baseline tests for ambiguous correction handling.

    Baseline Success Rate: 100% (1/1 PASS)
    Post-Improvement Rate: 100% (1/1 PASS)
    """

    @pytest.mark.asyncio
    async def test_correction_baseline_ambiguous_case(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        ambiguous_entries: list[MockEntry],
    ) -> None:
        """Test ambiguous correction handling (multiple possible matches).

        Tests: "fix my workout" with multiple bench press entries
        Expected: Should return target_entry_id=null with explanation

        Baseline result: TBD
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for baseline testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        client = LLMClient(config)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Fix my workout - I used the wrong weight",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={"cardio": CardioSchema, "strength": StrengthSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="my workout",
                recent_entries=ambiguous_entries,
            )
        )

        # For ambiguous cases, proper behavior is:
        # - is_correction=True (it IS a correction attempt)
        # - target_entry_id=None (can't determine which entry)
        # - extraction_notes should explain ambiguity
        if result.target_entry_id is None:
            # BASELINE PASS: Parser recognized ambiguity
            assert len(result.extraction_notes) > 0, "Parser should explain why target is ambiguous"
        else:
            # BASELINE FAIL: Parser picked one arbitrarily or failed entirely
            pytest.fail(
                f"Baseline ambiguous handling incorrect. "
                f"Expected: target_entry_id=None (ambiguous), Got: {result.target_entry_id}. "
                f"Notes: {result.extraction_notes}"
            )


# =============================================================================
# Unit Tests for format_recent_entries (Task 2 improvements)
# =============================================================================


class TestFormatRecentEntriesImproved:
    """Unit tests for improved format_recent_entries behavior."""

    def test_format_recent_entries_improved_output(self, baseline_recent_entries: list[MockEntry]) -> None:
        """Test improved format_recent_entries output format.

        Improved format: "- {entry_id} | {HH:MM} | {DOMAIN: key_values} | {summary_80chars}"
        """
        # Create a minimal mock client
        from unittest.mock import MagicMock

        from quilto.agents import ParserAgent

        mock_client = MagicMock()
        parser = ParserAgent(mock_client)

        result = parser.format_recent_entries(baseline_recent_entries)

        # Verify improved format
        lines = result.strip().split("\n")
        assert len(lines) == 4, "Should have 4 entries"

        # Check first entry (treadmill cardio)
        first_line = lines[0]
        assert "2026-01-26_10-30-00" in first_line
        assert "| 10:30 |" in first_line  # Time extracted
        assert "CARDIO:" in first_line  # Domain type
        assert "treadmill" in first_line  # Activity name

        # Check second entry (bench press strength)
        second_line = lines[1]
        assert "2026-01-26_18-33-00" in second_line
        assert "| 18:33 |" in second_line
        assert "STRENGTH:" in second_line
        assert "bench press" in second_line
        assert "80kg" in second_line

    def test_format_recent_entries_truncation(self) -> None:
        """Verify long content is truncated at 80 chars (improved from 50)."""
        from unittest.mock import MagicMock

        from quilto.agents import ParserAgent

        mock_client = MagicMock()
        parser = ParserAgent(mock_client)

        long_entry = MockEntry(
            entry_id="2026-01-26_10-00-00",
            entry_date=date(2026, 1, 26),
            raw_content="A" * 100,  # 100 character content
            parsed_data=None,
        )

        result = parser.format_recent_entries([long_entry])

        # Should truncate at 80 chars and add ...
        assert "A" * 80 + "..." in result
        assert "A" * 81 not in result


class TestHelperMethods:
    """Unit tests for helper methods added in Story 21.4."""

    def test_extract_time_from_entry_id_valid(self) -> None:
        """Test time extraction from valid entry ID."""
        from unittest.mock import MagicMock

        from quilto.agents import ParserAgent

        mock_client = MagicMock()
        parser = ParserAgent(mock_client)

        # Testing private method for unit test coverage
        result = parser._extract_time_from_entry_id("2026-01-26_10-30-45")  # pyright: ignore[reportPrivateUsage]
        assert result == "10:30"

    def test_extract_time_from_entry_id_invalid(self) -> None:
        """Test time extraction from invalid entry ID returns '??'."""
        from unittest.mock import MagicMock

        from quilto.agents import ParserAgent

        mock_client = MagicMock()
        parser = ParserAgent(mock_client)

        # Testing private method for unit test coverage
        result = parser._extract_time_from_entry_id("invalid-id")  # pyright: ignore[reportPrivateUsage]
        assert result == "??"

    def test_extract_domain_summary_strength(self) -> None:
        """Test domain summary extraction for strength domain."""
        from unittest.mock import MagicMock

        from quilto.agents import ParserAgent

        mock_client = MagicMock()
        parser = ParserAgent(mock_client)

        parsed_data = {
            "strength": {
                "exercise": "bench press",
                "weight_kg": 80,
                "reps": 5,
                "sets": 3,
            }
        }
        # Testing private method for unit test coverage
        result = parser._extract_domain_summary(parsed_data)  # pyright: ignore[reportPrivateUsage]

        assert "STRENGTH:" in result
        assert "bench press" in result
        assert "80kg" in result
        assert "5x3" in result

    def test_extract_domain_summary_cardio(self) -> None:
        """Test domain summary extraction for cardio domain."""
        from unittest.mock import MagicMock

        from quilto.agents import ParserAgent

        mock_client = MagicMock()
        parser = ParserAgent(mock_client)

        parsed_data = {"cardio": {"activity": "running", "distance_km": 5, "duration_min": 30}}
        # Testing private method for unit test coverage
        result = parser._extract_domain_summary(parsed_data)  # pyright: ignore[reportPrivateUsage]

        assert "CARDIO:" in result
        assert "running" in result
        assert "5km" in result
        assert "30min" in result

    def test_extract_domain_summary_none(self) -> None:
        """Test domain summary extraction with None parsed_data."""
        from unittest.mock import MagicMock

        from quilto.agents import ParserAgent

        mock_client = MagicMock()
        parser = ParserAgent(mock_client)

        # Testing private method for unit test coverage
        result = parser._extract_domain_summary(None)  # pyright: ignore[reportPrivateUsage]
        assert result == "UNKNOWN"

    def test_extract_domain_summary_empty(self) -> None:
        """Test domain summary extraction with empty parsed_data."""
        from unittest.mock import MagicMock

        from quilto.agents import ParserAgent

        mock_client = MagicMock()
        parser = ParserAgent(mock_client)

        # Testing private method for unit test coverage
        result = parser._extract_domain_summary({})  # pyright: ignore[reportPrivateUsage]
        assert result == "UNKNOWN"

    def test_extract_domain_summary_non_dict_domain_data(self) -> None:
        """Test domain summary extraction when domain value is not a dict.

        Edge case: parsed_data may have a domain key with a non-dict value
        (e.g., a string or list). Should return just the domain type.
        """
        from unittest.mock import MagicMock

        from quilto.agents import ParserAgent

        mock_client = MagicMock()
        parser = ParserAgent(mock_client)

        # Domain value is a string instead of dict
        parsed_data_string = {"strength": "bench press"}  # pyright: ignore[reportArgumentType]
        result = parser._extract_domain_summary(parsed_data_string)  # pyright: ignore[reportPrivateUsage]
        assert result == "STRENGTH"

        # Domain value is a list instead of dict
        parsed_data_list = {"nutrition": ["eggs", "toast"]}  # pyright: ignore[reportArgumentType]
        result = parser._extract_domain_summary(parsed_data_list)  # pyright: ignore[reportPrivateUsage]
        assert result == "NUTRITION"
