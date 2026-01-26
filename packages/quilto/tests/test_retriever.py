"""Unit tests for RetrieverAgent.

Tests cover model validation, DATE_RANGE strategy execution,
multi-instruction processing, warning generation,
and integration with real storage.

Note: KEYWORD and TOPICAL strategies were removed in Story 13.2.
Analyzer performs LLM-based relevance filtering instead.
"""

from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from quilto.agents import (
    RetrievalAttempt,
    RetrieverInput,
    RetrieverOutput,
)
from quilto.agents.retriever import RetrieverAgent
from quilto.storage.models import DateRange, Entry
from quilto.storage.repository import StorageRepository

# =============================================================================
# Test RetrievalAttempt Model (Task 9)
# =============================================================================


class TestRetrievalAttempt:
    """Tests for RetrievalAttempt model validation."""

    def test_valid_attempt(self) -> None:
        """RetrievalAttempt accepts all valid fields."""
        attempt = RetrievalAttempt(
            attempt_number=1,
            strategy="date_range",
            params={"start_date": "2026-01-01", "end_date": "2026-01-07"},
            entries_found=5,
            summary="Retrieved 5 entries from 2026-01-01 to 2026-01-07",
        )
        assert attempt.attempt_number == 1
        assert attempt.strategy == "date_range"
        assert attempt.params == {"start_date": "2026-01-01", "end_date": "2026-01-07"}
        assert attempt.entries_found == 5
        assert attempt.summary == "Retrieved 5 entries from 2026-01-01 to 2026-01-07"

    def test_required_fields(self) -> None:
        """RetrievalAttempt requires all fields."""
        with pytest.raises(ValidationError):
            RetrievalAttempt(
                attempt_number=1,
                strategy="date_range",
                params={},
                entries_found=5,
                # missing summary
            )  # type: ignore[call-arg]

    def test_attempt_number_minimum(self) -> None:
        """RetrievalAttempt attempt_number must be >= 1."""
        with pytest.raises(ValidationError):
            RetrievalAttempt(
                attempt_number=0,  # invalid, must be >= 1
                strategy="date_range",
                params={},
                entries_found=0,
                summary="Test",
            )

    def test_attempt_number_boundary_one(self) -> None:
        """RetrievalAttempt attempt_number=1 is valid."""
        attempt = RetrievalAttempt(
            attempt_number=1,
            strategy="date_range",
            params={},
            entries_found=0,
            summary="Test",
        )
        assert attempt.attempt_number == 1

    def test_entries_found_minimum(self) -> None:
        """RetrievalAttempt entries_found must be >= 0."""
        with pytest.raises(ValidationError):
            RetrievalAttempt(
                attempt_number=1,
                strategy="date_range",
                params={},
                entries_found=-1,  # invalid, must be >= 0
                summary="Test",
            )

    def test_entries_found_boundary_zero(self) -> None:
        """RetrievalAttempt entries_found=0 is valid."""
        attempt = RetrievalAttempt(
            attempt_number=1,
            strategy="date_range",
            params={},
            entries_found=0,
            summary="Test",
        )
        assert attempt.entries_found == 0

    def test_strategy_min_length(self) -> None:
        """RetrievalAttempt strategy must have min_length=1."""
        with pytest.raises(ValidationError):
            RetrievalAttempt(
                attempt_number=1,
                strategy="",  # invalid, empty string
                params={},
                entries_found=0,
                summary="Test",
            )

    def test_summary_min_length(self) -> None:
        """RetrievalAttempt summary must have min_length=1."""
        with pytest.raises(ValidationError):
            RetrievalAttempt(
                attempt_number=1,
                strategy="date_range",
                params={},
                entries_found=0,
                summary="",  # invalid, empty string
            )

    def test_expansion_tier_default(self) -> None:
        """RetrievalAttempt expansion_tier defaults to 0."""
        attempt = RetrievalAttempt(
            attempt_number=1,
            strategy="date_range",
            params={},
            entries_found=0,
            summary="Test",
        )
        assert attempt.expansion_tier == 0


# =============================================================================
# Test RetrieverInput Model (Task 9)
# =============================================================================


class TestRetrieverInput:
    """Tests for RetrieverInput model validation."""

    def test_default_max_entries(self) -> None:
        """RetrieverInput max_entries defaults to 100."""
        input_model = RetrieverInput(
            instructions=[],
        )
        assert input_model.max_entries == 100

    def test_custom_max_entries(self) -> None:
        """RetrieverInput accepts custom max_entries."""
        input_model = RetrieverInput(
            instructions=[],
            max_entries=50,
        )
        assert input_model.max_entries == 50

    def test_max_entries_minimum(self) -> None:
        """RetrieverInput max_entries must be >= 1."""
        with pytest.raises(ValidationError):
            RetrieverInput(
                instructions=[],
                max_entries=0,  # invalid, must be >= 1
            )

    def test_max_entries_boundary_one(self) -> None:
        """RetrieverInput max_entries=1 is valid."""
        input_model = RetrieverInput(
            instructions=[],
            max_entries=1,
        )
        assert input_model.max_entries == 1

    def test_empty_instructions_valid(self) -> None:
        """RetrieverInput accepts empty instructions list."""
        input_model = RetrieverInput(
            instructions=[],
        )
        assert input_model.instructions == []

    def test_full_input(self) -> None:
        """RetrieverInput accepts all fields."""
        input_model = RetrieverInput(
            instructions=[
                {
                    "strategy": "date_range",
                    "params": {"start_date": "2026-01-01"},
                    "sub_query_id": 1,
                }
            ],
            max_entries=200,
        )
        assert len(input_model.instructions) == 1
        assert input_model.max_entries == 200


# =============================================================================
# Test RetrieverOutput Model (Task 9)
# =============================================================================


class TestRetrieverOutput:
    """Tests for RetrieverOutput model validation."""

    def test_empty_entries_valid(self) -> None:
        """RetrieverOutput accepts empty entries list."""
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=0,
        )
        assert output.entries == []
        assert output.retrieval_summary == []
        assert output.total_entries_found == 0

    def test_truncated_flag(self) -> None:
        """RetrieverOutput truncated flag works correctly."""
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=150,
            truncated=True,
        )
        assert output.truncated is True

    def test_truncated_default_false(self) -> None:
        """RetrieverOutput truncated defaults to False."""
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=0,
        )
        assert output.truncated is False

    def test_warnings_default_empty(self) -> None:
        """RetrieverOutput warnings defaults to empty list."""
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=0,
        )
        assert output.warnings == []

    def test_warnings_with_values(self) -> None:
        """RetrieverOutput accepts warning messages."""
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=0,
            warnings=["Warning 1", "Warning 2"],
        )
        assert output.warnings == ["Warning 1", "Warning 2"]

    def test_total_entries_found_minimum(self) -> None:
        """RetrieverOutput total_entries_found must be >= 0."""
        with pytest.raises(ValidationError):
            RetrieverOutput(
                entries=[],
                retrieval_summary=[],
                total_entries_found=-1,  # invalid
            )

    def test_total_entries_found_boundary_zero(self) -> None:
        """RetrieverOutput total_entries_found=0 is valid."""
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=0,
        )
        assert output.total_entries_found == 0

    def test_date_range_covered_optional(self) -> None:
        """RetrieverOutput date_range_covered is optional."""
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=0,
            date_range_covered=None,
        )
        assert output.date_range_covered is None

    def test_date_range_covered_with_value(self) -> None:
        """RetrieverOutput accepts date_range_covered."""
        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 7))
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=0,
            date_range_covered=date_range,
        )
        assert output.date_range_covered == date_range

    def test_strategies_used_default_empty(self) -> None:
        """RetrieverOutput strategies_used defaults to empty list."""
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=0,
        )
        assert output.strategies_used == []

    def test_strategies_used_with_values(self) -> None:
        """RetrieverOutput accepts strategies_used list."""
        output = RetrieverOutput(
            entries=[],
            retrieval_summary=[],
            total_entries_found=0,
            strategies_used=["date_range"],
        )
        assert output.strategies_used == ["date_range"]


# =============================================================================
# Test RetrieverAgent Constants
# =============================================================================


class TestRetrieverAgentConstants:
    """Tests for RetrieverAgent class constants."""

    def test_agent_name_constant(self) -> None:
        """RetrieverAgent has correct AGENT_NAME constant."""
        mock_storage = MagicMock(spec=StorageRepository)
        retriever = RetrieverAgent(mock_storage)
        assert retriever.AGENT_NAME == "retriever"
        assert RetrieverAgent.AGENT_NAME == "retriever"


# =============================================================================
# Test DATE_RANGE Strategy (Task 10)
# =============================================================================


class TestRetrieverDateRange:
    """Tests for DATE_RANGE strategy execution."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage repository."""
        mock = MagicMock(spec=StorageRepository)
        return mock

    @pytest.fixture
    def sample_entries(self) -> list[Entry]:
        """Create sample entries for testing."""
        return [
            Entry(
                id="2026-01-01_10-00-00",
                date=date(2026, 1, 1),
                timestamp=datetime(2026, 1, 1, 10, 0, 0),
                raw_content="Bench press 3x5 at 135lbs",
            ),
            Entry(
                id="2026-01-02_10-00-00",
                date=date(2026, 1, 2),
                timestamp=datetime(2026, 1, 2, 10, 0, 0),
                raw_content="Squat 3x5 at 185lbs",
            ),
        ]

    @pytest.mark.asyncio
    async def test_date_range_retrieval(
        self, mock_storage: MagicMock, sample_entries: list[Entry]
    ) -> None:
        """DATE_RANGE strategy retrieves entries by date range."""
        mock_storage.get_entries_by_date_range.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-07",
                        },
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        mock_storage.get_entries_by_date_range.assert_called_once_with(
            date(2026, 1, 1), date(2026, 1, 7)
        )
        assert len(result.entries) == 2
        assert result.total_entries_found == 2
        assert len(result.retrieval_summary) == 1
        assert result.retrieval_summary[0].strategy == "date_range"
        assert result.retrieval_summary[0].entries_found == 2

    @pytest.mark.asyncio
    async def test_date_range_empty_result(self, mock_storage: MagicMock) -> None:
        """DATE_RANGE strategy handles empty results with warning."""
        mock_storage.get_entries_by_date_range.return_value = []

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-07",
                        },
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=False,
            )
        )

        assert len(result.entries) == 0
        assert result.total_entries_found == 0
        assert "returned 0 entries" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_date_range_missing_start_date(self, mock_storage: MagicMock) -> None:
        """DATE_RANGE strategy warns on missing start_date."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"end_date": "2026-01-07"},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert "Missing required param 'start_date'" in result.warnings[0]
        mock_storage.get_entries_by_date_range.assert_not_called()

    @pytest.mark.asyncio
    async def test_date_range_missing_end_date(self, mock_storage: MagicMock) -> None:
        """DATE_RANGE strategy warns on missing end_date."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01"},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert "Missing required param 'end_date'" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_date_range_invalid_date_format(self, mock_storage: MagicMock) -> None:
        """DATE_RANGE strategy warns on invalid date format."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "invalid",
                            "end_date": "2026-01-07",
                        },
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert "Invalid date format" in result.warnings[0]


# =============================================================================
# Test Unknown Strategy Handling
# =============================================================================


class TestRetrieverUnknownStrategy:
    """Tests for unknown strategy handling (keyword/topical removed in Story 13.2)."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage repository."""
        mock = MagicMock(spec=StorageRepository)
        return mock

    @pytest.mark.asyncio
    async def test_keyword_strategy_warns(self, mock_storage: MagicMock) -> None:
        """KEYWORD strategy is no longer supported and generates warning."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["bench"]},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert any("Unknown strategy" in w for w in result.warnings)
        assert any("only 'date_range' is supported" in w for w in result.warnings)
        mock_storage.search_entries.assert_not_called()

    @pytest.mark.asyncio
    async def test_topical_strategy_warns(self, mock_storage: MagicMock) -> None:
        """TOPICAL strategy is no longer supported and generates warning."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "topical",
                        "params": {"topics": ["progress"]},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert any("Unknown strategy" in w for w in result.warnings)
        mock_storage.search_entries.assert_not_called()


# =============================================================================
# Test Multi-Instruction Processing (Task 10)
# =============================================================================


class TestRetrieverMultiInstruction:
    """Tests for multi-instruction processing."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage repository."""
        mock = MagicMock(spec=StorageRepository)
        return mock

    @pytest.mark.asyncio
    async def test_multiple_date_range_instructions(
        self, mock_storage: MagicMock
    ) -> None:
        """Multiple date_range instructions are processed in order."""
        entries1 = [
            Entry(
                id="entry1",
                date=date(2026, 1, 1),
                timestamp=datetime(2026, 1, 1, 10, 0, 0),
                raw_content="Entry 1",
            ),
        ]
        entries2 = [
            Entry(
                id="entry2",
                date=date(2026, 1, 2),
                timestamp=datetime(2026, 1, 2, 10, 0, 0),
                raw_content="Entry 2",
            ),
        ]
        mock_storage.get_entries_by_date_range.side_effect = [entries1, entries2]

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-01",
                        },
                        "sub_query_id": 1,
                    },
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-02",
                            "end_date": "2026-01-02",
                        },
                        "sub_query_id": 2,
                    },
                ],
            )
        )

        assert len(result.retrieval_summary) == 2
        assert result.retrieval_summary[0].attempt_number == 1
        assert result.retrieval_summary[1].attempt_number == 2
        assert result.total_entries_found == 2

    @pytest.mark.asyncio
    async def test_deduplication(self, mock_storage: MagicMock) -> None:
        """Duplicate entries are deduplicated by ID."""
        shared_entry = Entry(
            id="shared-entry",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 0, 0),
            raw_content="Shared entry",
        )
        mock_storage.get_entries_by_date_range.return_value = [shared_entry]

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-01",
                        },
                        "sub_query_id": 1,
                    },
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-01",
                        },
                        "sub_query_id": 2,
                    },
                ],
            )
        )

        # Only one entry in result despite two queries returning it
        assert len(result.entries) == 1
        assert result.entries[0].id == "shared-entry"


# =============================================================================
# Test Limits and Warnings (Task 10)
# =============================================================================


class TestRetrieverLimits:
    """Tests for limits and warning generation."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage repository."""
        mock = MagicMock(spec=StorageRepository)
        return mock

    @pytest.mark.asyncio
    async def test_max_entries_truncation(self, mock_storage: MagicMock) -> None:
        """Results are truncated when exceeding max_entries."""
        entries = [
            Entry(
                id=f"entry{i}",
                date=date(2026, 1, 1),
                timestamp=datetime(2026, 1, 1, i, 0, 0),
                raw_content=f"Entry {i}",
            )
            for i in range(10)
        ]
        mock_storage.get_entries_by_date_range.return_value = entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-01",
                        },
                        "sub_query_id": 1,
                    }
                ],
                max_entries=5,
            )
        )

        assert len(result.entries) == 5
        assert result.total_entries_found == 10
        assert result.truncated is True
        assert "truncated" in result.warnings[-1].lower()

    @pytest.mark.asyncio
    async def test_unknown_strategy_warning(self, mock_storage: MagicMock) -> None:
        """Unknown strategy generates warning and is skipped."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "unknown_strategy",
                        "params": {},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert any("Unknown strategy" in w for w in result.warnings)
        assert len(result.retrieval_summary) == 0


# =============================================================================
# Test Date Range Coverage Calculation
# =============================================================================


class TestRetrieverDateRangeCoverage:
    """Tests for date_range_covered calculation."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage repository."""
        mock = MagicMock(spec=StorageRepository)
        return mock

    @pytest.mark.asyncio
    async def test_date_range_covered_calculated(
        self, mock_storage: MagicMock
    ) -> None:
        """date_range_covered is calculated from returned entries."""
        entries = [
            Entry(
                id="entry1",
                date=date(2026, 1, 3),
                timestamp=datetime(2026, 1, 3, 10, 0, 0),
                raw_content="Entry 1",
            ),
            Entry(
                id="entry2",
                date=date(2026, 1, 5),
                timestamp=datetime(2026, 1, 5, 10, 0, 0),
                raw_content="Entry 2",
            ),
            Entry(
                id="entry3",
                date=date(2026, 1, 1),
                timestamp=datetime(2026, 1, 1, 10, 0, 0),
                raw_content="Entry 3",
            ),
        ]
        mock_storage.get_entries_by_date_range.return_value = entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-07",
                        },
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert result.date_range_covered is not None
        assert result.date_range_covered.start == date(2026, 1, 1)
        assert result.date_range_covered.end == date(2026, 1, 5)

    @pytest.mark.asyncio
    async def test_date_range_covered_none_for_empty(
        self, mock_storage: MagicMock
    ) -> None:
        """date_range_covered is None when no entries returned."""
        mock_storage.get_entries_by_date_range.return_value = []

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-07",
                        },
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert result.date_range_covered is None


# =============================================================================
# Integration Tests (Task 11)
# =============================================================================


class TestRetrieverIntegration:
    """Integration tests with real StorageRepository."""

    @pytest.fixture
    def storage_with_entries(self, tmp_path: Path) -> StorageRepository:
        """Create storage with sample entries."""
        storage = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Entry for Jan 1
        (raw_dir / "2026-01-01.md").write_text(
            "## 10:00\nBench press 3x5 at 135lbs. Hit a new PR today!\n\n"
            "## 14:00\nAte chicken salad for lunch. High protein.\n"
        )

        # Entry for Jan 2
        (raw_dir / "2026-01-02.md").write_text(
            "## 09:00\nSquat 3x5 at 185lbs. Good progress on squat.\n"
        )

        # Entry for Jan 3
        (raw_dir / "2026-01-03.md").write_text(
            "## 11:00\nRest day. Feeling tired but recovery is important.\n"
        )

        return storage

    @pytest.mark.asyncio
    async def test_real_date_range(
        self, storage_with_entries: StorageRepository
    ) -> None:
        """Integration test: DATE_RANGE retrieval with real storage."""
        retriever = RetrieverAgent(storage_with_entries)

        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-02",
                        },
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        # Should find entries from Jan 1 and Jan 2
        assert len(result.entries) == 3  # 2 on Jan 1, 1 on Jan 2
        assert result.total_entries_found == 3
        assert result.retrieval_summary[0].entries_found == 3


# =============================================================================
# Test Progressive Expansion (Task 8: Story 3-5)
# =============================================================================


class TestRetrieverProgressiveExpansion:
    """Tests for progressive date range expansion (AC: #3, #4)."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage repository."""
        mock = MagicMock(spec=StorageRepository)
        return mock

    @pytest.fixture
    def sample_entry(self) -> Entry:
        """Create a sample entry for testing."""
        return Entry(
            id="2026-01-01_10-00-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 0, 0),
            raw_content="Bench press 3x5 at 135lbs",
        )

    @pytest.mark.asyncio
    async def test_expansion_stops_when_entries_found(
        self, mock_storage: MagicMock, sample_entry: Entry
    ) -> None:
        """Progressive expansion stops when entries are found (AC: #3)."""
        mock_storage.get_entries_by_date_range.side_effect = [[], [sample_entry]]

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-02",
                        },
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=True,
            )
        )

        assert len(result.retrieval_summary) == 2
        assert result.retrieval_summary[0].expansion_tier == 0
        assert result.retrieval_summary[1].expansion_tier == 1
        assert result.entries == [sample_entry]
        assert not result.expansion_exhausted

    @pytest.mark.asyncio
    async def test_expansion_tiers_7_14_30_90(
        self, mock_storage: MagicMock, sample_entry: Entry
    ) -> None:
        """Expansion tiers are 7, 14, 30, 90 days (AC: #3)."""
        mock_storage.get_entries_by_date_range.side_effect = [
            [],  # tier 0: original
            [],  # tier 1: 7 days
            [],  # tier 2: 14 days
            [sample_entry],  # tier 3: 30 days
        ]

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-02",
                        },
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=True,
            )
        )

        assert len(result.retrieval_summary) == 4
        assert result.retrieval_summary[0].expansion_tier == 0
        assert result.retrieval_summary[1].expansion_tier == 1
        assert result.retrieval_summary[2].expansion_tier == 2
        assert result.retrieval_summary[3].expansion_tier == 3
        assert "30 days" in result.retrieval_summary[3].summary

    @pytest.mark.asyncio
    async def test_expansion_exhausted(self, mock_storage: MagicMock) -> None:
        """Expansion exhaustion is properly signaled."""
        mock_storage.get_entries_by_date_range.return_value = []

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-02",
                        },
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=True,
            )
        )

        assert result.expansion_exhausted is True
        assert any("Progressive expansion exhausted" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_expansion_disabled_no_expansion(
        self, mock_storage: MagicMock
    ) -> None:
        """When enable_progressive_expansion=False, no expansion occurs."""
        mock_storage.get_entries_by_date_range.return_value = []

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-02",
                        },
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=False,
            )
        )

        assert len(result.retrieval_summary) == 1
        assert result.retrieval_summary[0].expansion_tier == 0
        assert result.expansion_exhausted is False

    @pytest.mark.asyncio
    async def test_explicit_date_no_expansion(self, mock_storage: MagicMock) -> None:
        """When explicit_date=true, no expansion occurs (AC: #6)."""
        mock_storage.get_entries_by_date_range.return_value = []

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-02",
                            "explicit_date": True,
                        },
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=True,
            )
        )

        assert len(result.retrieval_summary) == 1
        assert result.expansion_exhausted is False


# =============================================================================
# Test Cross-Language Retrieval (Story 13.2)
# =============================================================================


class TestRetrieverLanguageMismatch:
    """Integration tests for cross-language retrieval (AC: #7)."""

    @pytest.fixture
    def storage_with_korean_entry(self, tmp_path: Path) -> StorageRepository:
        """Create storage with Korean entry."""
        storage = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Entry with Korean content
        (raw_dir / "2026-01-01.md").write_text(
            "## 10:00\n벤치프레스 55kg 10x5 완료. 오늘 기분 좋음!\n"
        )

        return storage

    @pytest.mark.asyncio
    async def test_korean_entry_english_query_with_date_range(
        self, storage_with_korean_entry: StorageRepository
    ) -> None:
        """Date-range retrieval finds Korean entry regardless of query language."""
        retriever = RetrieverAgent(storage_with_korean_entry)

        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-01",
                        },
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        # Should find the Korean entry
        assert len(result.entries) == 1
        assert "벤치프레스" in result.entries[0].raw_content


# =============================================================================
# Test Priority Execution (Story 10.5)
# =============================================================================


class TestRetrieverPriorityExecution:
    """Tests for retrieval instruction priority execution."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage repository."""
        mock = MagicMock(spec=StorageRepository)
        return mock

    @pytest.fixture
    def sample_entries(self) -> list[Entry]:
        """Create sample entries for testing."""
        return [
            Entry(
                id="entry1",
                date=date(2026, 1, 1),
                timestamp=datetime(2026, 1, 1, 10, 0, 0),
                raw_content="Entry 1 from first date range",
            ),
            Entry(
                id="entry2",
                date=date(2026, 1, 2),
                timestamp=datetime(2026, 1, 2, 10, 0, 0),
                raw_content="Entry 2 from second date range",
            ),
        ]

    @pytest.mark.asyncio
    async def test_priority_1_executes_before_priority_2(
        self, mock_storage: MagicMock, sample_entries: list[Entry]
    ) -> None:
        """Priority 1 instruction executes before priority 2."""
        mock_storage.get_entries_by_date_range.side_effect = [
            [sample_entries[0]],
            [sample_entries[1]],
        ]

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-02",
                            "end_date": "2026-01-02",
                        },
                        "sub_query_id": 2,
                        "priority": 2,
                    },
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-01",
                        },
                        "sub_query_id": 1,
                        "priority": 1,
                    },
                ],
                enable_progressive_expansion=False,
            )
        )

        # Priority 1 (second in list) executes first
        assert result.entries[0].id == "entry1"
        assert result.entries[1].id == "entry2"

    @pytest.mark.asyncio
    async def test_strategies_used_populated(
        self, mock_storage: MagicMock, sample_entries: list[Entry]
    ) -> None:
        """strategies_used field is populated correctly."""
        mock_storage.get_entries_by_date_range.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-02",
                        },
                        "sub_query_id": 1,
                    },
                ],
                enable_progressive_expansion=False,
            )
        )

        assert "date_range" in result.strategies_used
        assert len(result.strategies_used) == 1
