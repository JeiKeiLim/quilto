"""Unit tests for RetrieverAgent.

Tests cover model validation, strategy execution (DATE_RANGE, KEYWORD, TOPICAL),
vocabulary expansion, multi-instruction processing, warning generation,
and integration with real storage.
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
from quilto.agents.retriever import RetrieverAgent, expand_terms
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
            expanded_terms=["bench", "bench press"],
        )
        assert attempt.attempt_number == 1
        assert attempt.strategy == "date_range"
        assert attempt.params == {"start_date": "2026-01-01", "end_date": "2026-01-07"}
        assert attempt.entries_found == 5
        assert attempt.summary == "Retrieved 5 entries from 2026-01-01 to 2026-01-07"
        assert attempt.expanded_terms == ["bench", "bench press"]

    def test_required_fields(self) -> None:
        """RetrievalAttempt requires all fields except expanded_terms."""
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

    def test_expanded_terms_default_empty(self) -> None:
        """RetrievalAttempt expanded_terms defaults to empty list."""
        attempt = RetrievalAttempt(
            attempt_number=1,
            strategy="date_range",
            params={},
            entries_found=0,
            summary="Test",
        )
        assert attempt.expanded_terms == []


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

    def test_vocabulary_default_empty_dict(self) -> None:
        """RetrieverInput vocabulary defaults to empty dict."""
        input_model = RetrieverInput(
            instructions=[],
        )
        assert input_model.vocabulary == {}

    def test_custom_vocabulary(self) -> None:
        """RetrieverInput accepts custom vocabulary."""
        input_model = RetrieverInput(
            instructions=[],
            vocabulary={"pr": "personal record", "bench": "bench press"},
        )
        assert input_model.vocabulary == {"pr": "personal record", "bench": "bench press"}

    def test_full_input(self) -> None:
        """RetrieverInput accepts all fields."""
        input_model = RetrieverInput(
            instructions=[{"strategy": "date_range", "params": {"start_date": "2026-01-01"}, "sub_query_id": 1}],
            vocabulary={"pr": "personal record"},
            max_entries=200,
        )
        assert len(input_model.instructions) == 1
        assert input_model.vocabulary == {"pr": "personal record"}
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


# =============================================================================
# Test expand_terms Function
# =============================================================================


class TestExpandTerms:
    """Tests for expand_terms vocabulary expansion function."""

    def test_no_expansion_without_vocabulary(self) -> None:
        """Terms are unchanged when vocabulary is empty."""
        terms = ["bench", "squat"]
        result = expand_terms(terms, {})
        assert set(result) == {"bench", "squat"}

    def test_no_expansion_with_non_matching_vocabulary(self) -> None:
        """Terms pass through unchanged when vocabulary has no matching entries."""
        terms = ["running", "cycling"]
        vocabulary = {"pr": "personal record", "bench": "bench press"}
        result = expand_terms(terms, vocabulary)
        # Only original terms, no expansions
        assert set(result) == {"running", "cycling"}

    def test_expansion_with_vocabulary(self) -> None:
        """Terms are expanded using vocabulary."""
        terms = ["pr", "bench"]
        vocabulary = {"pr": "personal record", "bench": "bench press"}
        result = expand_terms(terms, vocabulary)
        assert "pr" in result
        assert "personal record" in result
        assert "bench" in result
        assert "bench press" in result

    def test_reverse_lookup(self) -> None:
        """Terms trigger reverse lookup (full form -> abbreviation)."""
        terms = ["personal record"]
        vocabulary = {"pr": "personal record"}
        result = expand_terms(terms, vocabulary)
        assert "personal record" in result
        assert "pr" in result

    def test_case_insensitive_lookup(self) -> None:
        """Vocabulary lookup is case-insensitive."""
        terms = ["PR", "BENCH"]
        vocabulary = {"pr": "personal record", "bench": "bench press"}
        result = expand_terms(terms, vocabulary)
        # Original terms preserved
        assert "PR" in result
        assert "BENCH" in result
        # Expansions added
        assert "personal record" in result
        assert "bench press" in result

    def test_semantic_expansion_false(self) -> None:
        """semantic_expansion=False uses exact matches only."""
        terms = ["bench"]
        vocabulary = {"bench": "bench press", "incline bench": "incline bench press"}
        result = expand_terms(terms, vocabulary, semantic_expansion=False)
        assert "bench" in result
        assert "bench press" in result
        # Should NOT include incline variations with semantic_expansion=False
        assert "incline bench" not in result

    def test_semantic_expansion_true(self) -> None:
        """semantic_expansion=True includes partial matches."""
        terms = ["bench"]
        vocabulary = {"bench": "bench press", "incline bench": "incline bench press"}
        result = expand_terms(terms, vocabulary, semantic_expansion=True)
        assert "bench" in result
        assert "bench press" in result
        # Should include partial matches
        assert "incline bench press" in result
        assert "incline bench" in result

    def test_deduplication(self) -> None:
        """Expanded terms are deduplicated."""
        terms = ["bench", "bench", "press"]
        vocabulary = {"bench": "bench press"}
        result = expand_terms(terms, vocabulary)
        # No duplicates - result should equal its deduplicated form
        assert len(result) == len(set(result))
        # Verify expected terms are present
        assert "bench" in result
        assert "bench press" in result
        assert "press" in result


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
    async def test_date_range_retrieval(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """DATE_RANGE strategy retrieves entries by date range."""
        mock_storage.get_entries_by_date_range.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-07"},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        mock_storage.get_entries_by_date_range.assert_called_once_with(date(2026, 1, 1), date(2026, 1, 7))
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
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-07"},
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=False,  # Disable expansion to test base behavior
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
                        "params": {"end_date": "2026-01-07"},  # missing start_date
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
                        "params": {"start_date": "2026-01-01"},  # missing end_date
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
                        "params": {"start_date": "invalid", "end_date": "2026-01-07"},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert "Invalid date format" in result.warnings[0]


# =============================================================================
# Test KEYWORD Strategy (Task 10)
# =============================================================================


class TestRetrieverKeyword:
    """Tests for KEYWORD strategy execution."""

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
        ]

    @pytest.mark.asyncio
    async def test_keyword_retrieval(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """KEYWORD strategy retrieves entries by keywords."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["bench", "press"]},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        mock_storage.search_entries.assert_called_once()
        assert len(result.entries) == 1
        assert result.retrieval_summary[0].strategy == "keyword"

    @pytest.mark.asyncio
    async def test_vocabulary_expansion(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """KEYWORD strategy expands terms using vocabulary."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["pr"]},
                        "sub_query_id": 1,
                    }
                ],
                vocabulary={"pr": "personal record"},
            )
        )

        # Check that expanded terms include both original and expansion
        call_args = mock_storage.search_entries.call_args
        keywords_used = call_args[0][0]  # First positional arg
        assert "pr" in keywords_used
        assert "personal record" in keywords_used

        # Check expanded_terms in attempt
        assert "pr" in result.retrieval_summary[0].expanded_terms
        assert "personal record" in result.retrieval_summary[0].expanded_terms

    @pytest.mark.asyncio
    async def test_vocabulary_expansion_reverse_lookup(
        self, mock_storage: MagicMock, sample_entries: list[Entry]
    ) -> None:
        """KEYWORD strategy does reverse vocabulary lookup."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["personal record"]},
                        "sub_query_id": 1,
                    }
                ],
                vocabulary={"pr": "personal record"},
            )
        )

        # Check that reverse lookup added the abbreviation
        call_args = mock_storage.search_entries.call_args
        keywords_used = call_args[0][0]
        assert "pr" in keywords_used
        assert "personal record" in keywords_used

    @pytest.mark.asyncio
    async def test_semantic_expansion_false(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """KEYWORD strategy with semantic_expansion=False uses exact matches."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["bench"], "semantic_expansion": False},
                        "sub_query_id": 1,
                    }
                ],
                vocabulary={"bench": "bench press", "incline bench": "incline bench press"},
            )
        )

        call_args = mock_storage.search_entries.call_args
        keywords_used = call_args[0][0]
        assert "bench" in keywords_used
        assert "bench press" in keywords_used
        # Should NOT include incline variations
        assert "incline bench" not in keywords_used

    @pytest.mark.asyncio
    async def test_semantic_expansion_true(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """KEYWORD strategy with semantic_expansion=True includes partial matches."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["bench"], "semantic_expansion": True},
                        "sub_query_id": 1,
                    }
                ],
                vocabulary={"bench": "bench press", "incline bench": "incline bench press"},
            )
        )

        call_args = mock_storage.search_entries.call_args
        keywords_used = call_args[0][0]
        # Should include incline variations with semantic expansion
        assert "incline bench press" in keywords_used

    @pytest.mark.asyncio
    async def test_expanded_terms_in_attempt(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """KEYWORD strategy records expanded_terms in RetrievalAttempt."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["pr", "bench"]},
                        "sub_query_id": 1,
                    }
                ],
                vocabulary={"pr": "personal record", "bench": "bench press"},
            )
        )

        attempt = result.retrieval_summary[0]
        assert "pr" in attempt.expanded_terms
        assert "personal record" in attempt.expanded_terms
        assert "bench" in attempt.expanded_terms
        assert "bench press" in attempt.expanded_terms

    @pytest.mark.asyncio
    async def test_keyword_missing_keywords(self, mock_storage: MagicMock) -> None:
        """KEYWORD strategy warns on missing keywords param."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {},  # missing keywords
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert "Missing required param 'keywords'" in result.warnings[0]
        mock_storage.search_entries.assert_not_called()

    @pytest.mark.asyncio
    async def test_keyword_with_date_range(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """KEYWORD strategy respects optional date_range param."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {
                            "keywords": ["bench"],
                            "date_range": {"start": "2026-01-01", "end": "2026-01-07"},
                        },
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        call_args = mock_storage.search_entries.call_args
        date_range_arg = call_args[1].get("date_range")
        assert date_range_arg is not None
        assert date_range_arg.start == date(2026, 1, 1)
        assert date_range_arg.end == date(2026, 1, 7)


# =============================================================================
# Test TOPICAL Strategy (Task 10)
# =============================================================================


class TestRetrieverTopical:
    """Tests for TOPICAL strategy execution."""

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
                raw_content="Made good progress on bench press today",
            ),
        ]

    @pytest.mark.asyncio
    async def test_topical_retrieval(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """TOPICAL strategy retrieves entries by topics."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "topical",
                        "params": {"topics": ["progress", "trend"]},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        mock_storage.search_entries.assert_called_once()
        assert len(result.entries) == 1
        assert result.retrieval_summary[0].strategy == "topical"

    @pytest.mark.asyncio
    async def test_related_terms_included(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """TOPICAL strategy includes related_terms in search."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "topical",
                        "params": {
                            "topics": ["progress"],
                            "related_terms": ["improvement", "gains"],
                        },
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        call_args = mock_storage.search_entries.call_args
        keywords_used = call_args[0][0]
        assert "progress" in keywords_used
        assert "improvement" in keywords_used
        assert "gains" in keywords_used

    @pytest.mark.asyncio
    async def test_topical_missing_topics(self, mock_storage: MagicMock) -> None:
        """TOPICAL strategy warns on missing topics param."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "topical",
                        "params": {},  # missing topics
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert "Missing required param 'topics'" in result.warnings[0]
        mock_storage.search_entries.assert_not_called()

    @pytest.mark.asyncio
    async def test_topical_with_vocabulary(self, mock_storage: MagicMock, sample_entries: list[Entry]) -> None:
        """TOPICAL strategy expands topics using vocabulary."""
        mock_storage.search_entries.return_value = sample_entries

        retriever = RetrieverAgent(mock_storage)
        await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "topical",
                        "params": {"topics": ["pr"]},
                        "sub_query_id": 1,
                    }
                ],
                vocabulary={"pr": "personal record"},
            )
        )

        call_args = mock_storage.search_entries.call_args
        keywords_used = call_args[0][0]
        assert "pr" in keywords_used
        assert "personal record" in keywords_used


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
    async def test_multiple_instructions(self, mock_storage: MagicMock) -> None:
        """Multiple instructions are processed in order."""
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
        mock_storage.get_entries_by_date_range.return_value = entries1
        mock_storage.search_entries.return_value = entries2

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-01"},
                        "sub_query_id": 1,
                    },
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["workout"]},
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
        # Same entry returned by both queries
        shared_entry = Entry(
            id="shared-entry",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 0, 0),
            raw_content="Shared entry",
        )
        mock_storage.get_entries_by_date_range.return_value = [shared_entry]
        mock_storage.search_entries.return_value = [shared_entry]

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-01"},
                        "sub_query_id": 1,
                    },
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["shared"]},
                        "sub_query_id": 2,
                    },
                ],
            )
        )

        # Only one entry in result despite two queries returning it
        assert len(result.entries) == 1
        assert result.entries[0].id == "shared-entry"

    @pytest.mark.asyncio
    async def test_order_preservation(self, mock_storage: MagicMock) -> None:
        """Entry order is preserved (first occurrence wins)."""
        entry1 = Entry(
            id="entry1",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 0, 0),
            raw_content="Entry 1",
        )
        entry2 = Entry(
            id="entry2",
            date=date(2026, 1, 2),
            timestamp=datetime(2026, 1, 2, 10, 0, 0),
            raw_content="Entry 2",
        )
        mock_storage.get_entries_by_date_range.return_value = [entry1]
        mock_storage.search_entries.return_value = [entry2]

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-01"},
                        "sub_query_id": 1,
                    },
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["entry"]},
                        "sub_query_id": 2,
                    },
                ],
            )
        )

        # Order from instructions is preserved
        assert result.entries[0].id == "entry1"
        assert result.entries[1].id == "entry2"


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
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-01"},
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
        assert "10" in result.warnings[-1]
        assert "5" in result.warnings[-1]

    @pytest.mark.asyncio
    async def test_max_entries_boundary_exact(self, mock_storage: MagicMock) -> None:
        """Exactly max_entries does not trigger truncation."""
        entries = [
            Entry(
                id=f"entry{i}",
                date=date(2026, 1, 1),
                timestamp=datetime(2026, 1, 1, i, 0, 0),
                raw_content=f"Entry {i}",
            )
            for i in range(5)
        ]
        mock_storage.get_entries_by_date_range.return_value = entries

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-01"},
                        "sub_query_id": 1,
                    }
                ],
                max_entries=5,
            )
        )

        assert len(result.entries) == 5
        assert result.truncated is False
        # No truncation warning
        assert not any("truncated" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_empty_result_warning(self, mock_storage: MagicMock) -> None:
        """Empty result generates warning."""
        mock_storage.get_entries_by_date_range.return_value = []

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-01"},
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=False,  # Disable expansion to test base behavior
            )
        )

        assert any("returned 0 entries" in w for w in result.warnings)

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
        # No retrieval attempt recorded for unknown strategy
        assert len(result.retrieval_summary) == 0

    @pytest.mark.asyncio
    async def test_missing_required_param_warning(self, mock_storage: MagicMock) -> None:
        """Missing required param generates warning."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {},  # missing start_date and end_date
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert any("Missing required param" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_invalid_date_format_warning(self, mock_storage: MagicMock) -> None:
        """Invalid date format generates warning."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "not-a-date", "end_date": "2026-01-01"},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert any("Invalid date format" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_all_instructions_fail(self, mock_storage: MagicMock) -> None:
        """When all instructions fail, empty entries with warnings returned."""
        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "unknown_strategy",
                        "params": {},
                        "sub_query_id": 1,
                    },
                    {
                        "strategy": "date_range",
                        "params": {},  # missing required params
                        "sub_query_id": 2,
                    },
                    {
                        "strategy": "keyword",
                        "params": {},  # missing keywords
                        "sub_query_id": 3,
                    },
                ],
            )
        )

        # No entries returned
        assert len(result.entries) == 0
        assert result.total_entries_found == 0
        # All three instructions generated warnings
        assert len(result.warnings) == 3
        assert any("Unknown strategy" in w for w in result.warnings)
        assert any("Missing required param" in w for w in result.warnings)


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
    async def test_date_range_covered_calculated(self, mock_storage: MagicMock) -> None:
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
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-07"},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert result.date_range_covered is not None
        assert result.date_range_covered.start == date(2026, 1, 1)
        assert result.date_range_covered.end == date(2026, 1, 5)

    @pytest.mark.asyncio
    async def test_date_range_covered_none_for_empty(self, mock_storage: MagicMock) -> None:
        """date_range_covered is None when no entries returned."""
        mock_storage.get_entries_by_date_range.return_value = []

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-07"},
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

        # Create raw markdown files with entries
        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Entry for Jan 1
        (raw_dir / "2026-01-01.md").write_text(
            "## 10:00\nBench press 3x5 at 135lbs. Hit a new PR today!\n\n"
            "## 14:00\nAte chicken salad for lunch. High protein.\n"
        )

        # Entry for Jan 2
        (raw_dir / "2026-01-02.md").write_text("## 09:00\nSquat 3x5 at 185lbs. Good progress on squat.\n")

        # Entry for Jan 3
        (raw_dir / "2026-01-03.md").write_text("## 11:00\nRest day. Feeling tired but recovery is important.\n")

        return storage

    @pytest.mark.asyncio
    async def test_real_date_range(self, storage_with_entries: StorageRepository) -> None:
        """Integration test: DATE_RANGE retrieval with real storage."""
        retriever = RetrieverAgent(storage_with_entries)

        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-02"},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        # Should find entries from Jan 1 and Jan 2
        assert len(result.entries) == 3  # 2 on Jan 1, 1 on Jan 2
        assert result.total_entries_found == 3
        assert result.retrieval_summary[0].entries_found == 3

    @pytest.mark.asyncio
    async def test_real_keyword_search(self, storage_with_entries: StorageRepository) -> None:
        """Integration test: KEYWORD retrieval with real storage."""
        retriever = RetrieverAgent(storage_with_entries)

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

        # Should find the bench press entry
        assert len(result.entries) >= 1
        assert any("bench" in e.raw_content.lower() for e in result.entries)

    @pytest.mark.asyncio
    async def test_real_keyword_with_vocabulary(self, storage_with_entries: StorageRepository) -> None:
        """Integration test: KEYWORD with vocabulary expansion."""
        retriever = RetrieverAgent(storage_with_entries)

        vocab_result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["pr"]},
                        "sub_query_id": 1,
                    }
                ],
                vocabulary={"pr": "personal record"},
            )
        )

        # Should find the entry with "PR" in it
        assert len(vocab_result.entries) >= 1
        assert any("pr" in e.raw_content.lower() for e in vocab_result.entries)

    @pytest.mark.asyncio
    async def test_real_topical_search(self, storage_with_entries: StorageRepository) -> None:
        """Integration test: TOPICAL retrieval with real storage."""
        retriever = RetrieverAgent(storage_with_entries)

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

        # Should find entries mentioning progress
        assert len(result.entries) >= 1
        assert any("progress" in e.raw_content.lower() for e in result.entries)

    @pytest.mark.asyncio
    async def test_real_empty_search(self, storage_with_entries: StorageRepository) -> None:
        """Integration test: Handle empty search results."""
        retriever = RetrieverAgent(storage_with_entries)

        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["nonexistent_term_xyz"]},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        assert len(result.entries) == 0
        assert any("returned 0 entries" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_real_multi_instruction(self, storage_with_entries: StorageRepository) -> None:
        """Integration test: Multiple instructions with real storage."""
        retriever = RetrieverAgent(storage_with_entries)

        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["bench"]},
                        "sub_query_id": 1,
                    },
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["squat"]},
                        "sub_query_id": 2,
                    },
                ],
            )
        )

        # Should find both bench and squat entries
        assert len(result.retrieval_summary) == 2
        assert any("bench" in e.raw_content.lower() for e in result.entries)
        assert any("squat" in e.raw_content.lower() for e in result.entries)

    @pytest.mark.asyncio
    async def test_real_deduplication(self, storage_with_entries: StorageRepository) -> None:
        """Integration test: Deduplication with real storage."""
        retriever = RetrieverAgent(storage_with_entries)

        # Both searches should find the bench entry
        dedup_result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["bench"]},
                        "sub_query_id": 1,
                    },
                    {
                        "strategy": "keyword",
                        "params": {"keywords": ["135lbs"]},
                        "sub_query_id": 2,
                    },
                ],
            )
        )

        # Entry IDs should be unique
        entry_ids = [e.id for e in dedup_result.entries]
        assert len(entry_ids) == len(set(entry_ids))  # No duplicates


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
    async def test_expansion_stops_when_entries_found(self, mock_storage: MagicMock, sample_entry: Entry) -> None:
        """Progressive expansion stops when entries are found (AC: #3)."""
        # First call returns empty, second returns entries
        mock_storage.get_entries_by_date_range.side_effect = [[], [sample_entry]]

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-02"},
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=True,
            )
        )

        # Should have 2 attempts (tier 0 empty + tier 1 found)
        assert len(result.retrieval_summary) == 2
        assert result.retrieval_summary[0].expansion_tier == 0
        assert result.retrieval_summary[1].expansion_tier == 1
        assert result.entries == [sample_entry]
        assert not result.expansion_exhausted

    @pytest.mark.asyncio
    async def test_expansion_tiers_7_14_30_90(self, mock_storage: MagicMock, sample_entry: Entry) -> None:
        """Expansion tiers are 7, 14, 30, 90 days (AC: #3)."""
        # All calls return empty until tier 3 (30 days)
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
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-02"},
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=True,
            )
        )

        # Should have 4 attempts (tiers 0, 1, 2, 3)
        assert len(result.retrieval_summary) == 4
        assert result.retrieval_summary[0].expansion_tier == 0
        assert result.retrieval_summary[1].expansion_tier == 1
        assert result.retrieval_summary[2].expansion_tier == 2
        assert result.retrieval_summary[3].expansion_tier == 3
        # Tier 3 summary should mention 30 days
        assert "30 days" in result.retrieval_summary[3].summary

    @pytest.mark.asyncio
    async def test_expansion_exhausted_triggers_fallback(self, mock_storage: MagicMock) -> None:
        """Expansion exhaustion triggers term search fallback (AC: #4)."""
        # All date range calls return empty
        mock_storage.get_entries_by_date_range.return_value = []
        # Keyword fallback also returns empty
        mock_storage.search_entries.return_value = []

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-02",
                            "keywords": ["bench"],
                        },
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=True,
            )
        )

        assert result.expansion_exhausted is True
        assert any("Progressive expansion exhausted" in w for w in result.warnings)
        # Should have keyword fallback attempt
        assert any(a.strategy == "keyword" for a in result.retrieval_summary)

    @pytest.mark.asyncio
    async def test_expansion_disabled_no_expansion(self, mock_storage: MagicMock) -> None:
        """When enable_progressive_expansion=False, no expansion occurs."""
        mock_storage.get_entries_by_date_range.return_value = []

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-02"},
                        "sub_query_id": 1,
                    }
                ],
                enable_progressive_expansion=False,
            )
        )

        # Only one attempt, no expansion
        assert len(result.retrieval_summary) == 1
        assert result.retrieval_summary[0].expansion_tier == 0
        assert result.expansion_exhausted is False
        # Should have normal empty warning
        assert any("returned 0 entries" in w for w in result.warnings)

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
                enable_progressive_expansion=True,  # Would expand, but explicit_date blocks it
            )
        )

        # Only one attempt, no expansion due to explicit_date
        assert len(result.retrieval_summary) == 1
        assert result.expansion_exhausted is False

    @pytest.mark.asyncio
    async def test_expansion_tier_logged_in_attempt(self, mock_storage: MagicMock, sample_entry: Entry) -> None:
        """Expansion tier is correctly logged in RetrievalAttempt (AC: #3)."""
        # Return entries on tier 2 (14 days)
        mock_storage.get_entries_by_date_range.side_effect = [
            [],  # tier 0
            [],  # tier 1
            [sample_entry],  # tier 2
        ]

        retriever = RetrieverAgent(mock_storage)
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-02"},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        # Verify expansion_tier is correctly set
        for i, attempt in enumerate(result.retrieval_summary):
            assert attempt.expansion_tier == i
        # Last attempt should have "Expanded to 14 days" in summary
        assert "14 days" in result.retrieval_summary[2].summary

    @pytest.mark.asyncio
    async def test_keyword_strategy_no_expansion(self, mock_storage: MagicMock) -> None:
        """Keyword strategy does not trigger progressive expansion (AC: #5, #7)."""
        mock_storage.search_entries.return_value = []

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
                enable_progressive_expansion=True,  # Should be ignored for keyword
            )
        )

        # Only one attempt for keyword strategy
        assert len(result.retrieval_summary) == 1
        assert result.retrieval_summary[0].strategy == "keyword"
        assert result.retrieval_summary[0].expansion_tier == 0
        assert result.expansion_exhausted is False


class TestRetrieverLanguageMismatch:
    """Integration tests for cross-language retrieval (AC: #7)."""

    @pytest.fixture
    def storage_with_korean_entry(self, tmp_path: Path) -> StorageRepository:
        """Create storage with Korean entry."""
        storage = StorageRepository(tmp_path)

        # Create raw markdown files with Korean content
        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Entry with Korean content
        (raw_dir / "2026-01-01.md").write_text("## 10:00\n벤치프레스 55kg 10x5 완료. 오늘 기분 좋음!\n")

        return storage

    @pytest.mark.asyncio
    async def test_korean_entry_english_query_with_date_range(
        self, storage_with_korean_entry: StorageRepository
    ) -> None:
        """Date-range retrieval finds Korean entry regardless of query language (AC: #7)."""
        retriever = RetrieverAgent(storage_with_korean_entry)

        # Date range will find the entry regardless of language
        result = await retriever.retrieve(
            RetrieverInput(
                instructions=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2026-01-01", "end_date": "2026-01-01"},
                        "sub_query_id": 1,
                    }
                ],
            )
        )

        # Should find the Korean entry
        assert len(result.entries) == 1
        assert "벤치프레스" in result.entries[0].raw_content
