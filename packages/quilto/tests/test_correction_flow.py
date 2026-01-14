"""Tests for correction flow module.

Tests cover:
- CorrectionResult model validation
- process_correction orchestration function
- SessionState correction fields
- Parser prompt correction mode enhancements
- Integration with StorageRepository
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ValidationError
from quilto import CorrectionResult, process_correction
from quilto.agents import ParserAgent
from quilto.agents.models import InputType, ParserInput, ParserOutput, RouterOutput
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels
from quilto.state import SessionState
from quilto.storage import Entry, StorageRepository

# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for ParserAgent tests."""
    return LLMConfig(
        default_provider="ollama",  # type: ignore[arg-type]
        providers={
            "ollama": ProviderConfig(api_base="http://localhost:11434"),
        },
        tiers={
            "low": TierModels(ollama="qwen2.5:7b"),
            "medium": TierModels(ollama="qwen2.5:7b"),
        },
        agents={
            "parser": AgentConfig(tier="medium"),
        },
    )


def create_mock_parser_agent(response_json: dict[str, Any]) -> ParserAgent:
    """Create a mock ParserAgent that returns the given JSON response.

    Args:
        response_json: The JSON response to return from parse.

    Returns:
        Mocked ParserAgent instance.
    """
    from quilto.llm import LLMClient

    config = create_test_config()
    client = LLMClient(config)
    parser = ParserAgent(client)

    async def mock_parse(parser_input: ParserInput) -> ParserOutput:
        return ParserOutput.model_validate_json(json.dumps(response_json))

    parser.parse = AsyncMock(side_effect=mock_parse)  # type: ignore[method-assign]
    return parser


class StrengthSchema(BaseModel):
    """Schema for strength training domain (test data)."""

    exercise: str
    weight_kg: float | None = None
    reps: int | None = None


@pytest.fixture
def sample_router_output() -> RouterOutput:
    """Create a sample RouterOutput for correction tests."""
    return RouterOutput(
        input_type=InputType.CORRECTION,
        confidence=0.9,
        selected_domains=["strength"],
        domain_selection_reasoning="Correcting bench press weight",
        correction_target="bench weight recorded as 85",
        reasoning="User is correcting a previous entry",
    )


@pytest.fixture
def sample_entries() -> list[Entry]:
    """Create sample recent entries for correction tests."""
    return [
        Entry(
            id="2026-01-14_10-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 30, 0),
            raw_content="Bench pressed 85x5",
            parsed_data={"strength": {"exercise": "bench press", "weight_kg": 38.6}},
        ),
        Entry(
            id="2026-01-14_11-00-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 11, 0, 0),
            raw_content="Squatted 200x3",
            parsed_data={"strength": {"exercise": "squat", "weight_kg": 90.7}},
        ),
    ]


# =============================================================================
# Test CorrectionResult Model Validation
# =============================================================================


class TestCorrectionResultModel:
    """Tests for CorrectionResult Pydantic model."""

    def test_successful_correction_result(self) -> None:
        """Test valid successful CorrectionResult."""
        result = CorrectionResult(
            success=True,
            target_entry_id="2026-01-14_10-30-00",
            correction_delta={"weight_kg": 84.0},
            original_entry_id="2026-01-14_10-30-00",
        )

        assert result.success is True
        assert result.target_entry_id == "2026-01-14_10-30-00"
        assert result.correction_delta == {"weight_kg": 84.0}
        assert result.original_entry_id == "2026-01-14_10-30-00"
        assert result.error_message is None

    def test_failed_correction_result(self) -> None:
        """Test valid failed CorrectionResult."""
        result = CorrectionResult(
            success=False,
            error_message="Could not identify target entry",
        )

        assert result.success is False
        assert result.error_message == "Could not identify target entry"
        assert result.target_entry_id is None

    def test_success_true_requires_target_entry_id(self) -> None:
        """Test that success=True requires target_entry_id."""
        with pytest.raises(ValidationError, match="success=True requires target_entry_id"):
            CorrectionResult(
                success=True,
                target_entry_id=None,
            )

    def test_success_false_requires_error_message(self) -> None:
        """Test that success=False requires error_message."""
        with pytest.raises(ValidationError, match="success=False requires error_message"):
            CorrectionResult(
                success=False,
                error_message=None,
            )

    def test_success_with_empty_string_target_fails(self) -> None:
        """Test that success=True with empty string target_entry_id fails."""
        # Empty string is falsy and should be rejected
        with pytest.raises(ValidationError, match="success=True requires target_entry_id"):
            CorrectionResult(
                success=True,
                target_entry_id="",  # Empty string
            )

    def test_correction_delta_can_be_none(self) -> None:
        """Test that correction_delta can be None even on success."""
        result = CorrectionResult(
            success=True,
            target_entry_id="2026-01-14_10-30-00",
            correction_delta=None,
        )

        assert result.correction_delta is None

    def test_strict_mode_type_coercion(self) -> None:
        """Test strict mode rejects type coercion."""
        # Strict mode rejects string "True" instead of bool True
        with pytest.raises(ValidationError):
            CorrectionResult(
                success="True",  # type: ignore[arg-type]  # Should be bool
                target_entry_id="test",
            )


# =============================================================================
# Test process_correction Function
# =============================================================================


class TestProcessCorrection:
    """Tests for process_correction orchestration function."""

    @pytest.mark.asyncio
    async def test_happy_path_correction(
        self, tmp_path: Path, sample_router_output: RouterOutput, sample_entries: list[Entry]
    ) -> None:
        """Test successful correction flow."""
        # Create mock parser that returns correction output
        parser_response: dict[str, Any] = {
            "date": "2026-01-14",
            "timestamp": "2026-01-14T10:45:00",
            "tags": [],
            "domain_data": {"strength": {"exercise": "bench press", "weight_kg": 84.0}},
            "raw_content": "Actually that was 185 not 85",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
            "is_correction": True,
            "target_entry_id": "2026-01-14_10-30-00",
            "correction_delta": {"weight_kg": 84.0},
        }
        parser = create_mock_parser_agent(parser_response)
        storage = StorageRepository(tmp_path)

        # Create initial entry in storage
        initial_entry = Entry(
            id="2026-01-14_10-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 30, 0),
            raw_content="Bench pressed 85x5",
            parsed_data={"strength": {"exercise": "bench press", "weight_kg": 38.6}},
        )
        storage.save_entry(initial_entry)

        result = await process_correction(
            router_output=sample_router_output,
            parser_agent=parser,
            storage=storage,
            recent_entries=sample_entries,
            domain_schemas={"strength": StrengthSchema},
            vocabulary={"bp": "bench press"},
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
        )

        assert result.success is True
        assert result.target_entry_id == "2026-01-14_10-30-00"
        assert result.correction_delta == {"weight_kg": 84.0}

    @pytest.mark.asyncio
    async def test_raises_value_error_if_not_correction_type(self, tmp_path: Path, sample_entries: list[Entry]) -> None:
        """Test that ValueError is raised for non-CORRECTION input_type."""
        router_output = RouterOutput(
            input_type=InputType.LOG,  # Not CORRECTION
            confidence=0.9,
            selected_domains=["strength"],
            domain_selection_reasoning="Logging workout",
            reasoning="User is logging",
        )
        parser = create_mock_parser_agent({})
        storage = StorageRepository(tmp_path)

        with pytest.raises(ValueError, match="input_type=CORRECTION"):
            await process_correction(
                router_output=router_output,
                parser_agent=parser,
                storage=storage,
                recent_entries=sample_entries,
                domain_schemas={},
                vocabulary={},
            )

    @pytest.mark.asyncio
    async def test_returns_error_if_no_recent_entries(self, tmp_path: Path, sample_router_output: RouterOutput) -> None:
        """Test error result when recent_entries is empty."""
        parser = create_mock_parser_agent({})
        storage = StorageRepository(tmp_path)

        result = await process_correction(
            router_output=sample_router_output,
            parser_agent=parser,
            storage=storage,
            recent_entries=[],  # Empty
            domain_schemas={},
            vocabulary={},
        )

        assert result.success is False
        assert result.error_message == "No recent entries to correct"

    @pytest.mark.asyncio
    async def test_returns_error_if_parser_not_correction(
        self, tmp_path: Path, sample_router_output: RouterOutput, sample_entries: list[Entry]
    ) -> None:
        """Test error result when Parser doesn't identify correction."""
        parser_response: dict[str, Any] = {
            "date": "2026-01-14",
            "timestamp": "2026-01-14T10:45:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "Actually that was 185",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
            "is_correction": False,  # Parser didn't identify correction
            "target_entry_id": None,
            "correction_delta": None,
        }
        parser = create_mock_parser_agent(parser_response)
        storage = StorageRepository(tmp_path)

        result = await process_correction(
            router_output=sample_router_output,
            parser_agent=parser,
            storage=storage,
            recent_entries=sample_entries,
            domain_schemas={},
            vocabulary={},
        )

        assert result.success is False
        assert result.error_message == "Parser did not identify correction"

    @pytest.mark.asyncio
    async def test_returns_error_if_no_target_entry_id(
        self, tmp_path: Path, sample_router_output: RouterOutput, sample_entries: list[Entry]
    ) -> None:
        """Test error result when Parser can't identify target entry."""
        parser_response: dict[str, Any] = {
            "date": "2026-01-14",
            "timestamp": "2026-01-14T10:45:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "Actually that was 185",
            "confidence": 0.9,
            "extraction_notes": ["Could not identify target entry"],
            "uncertain_fields": [],
            "is_correction": True,
            "target_entry_id": None,  # No target identified
            "correction_delta": None,
        }
        parser = create_mock_parser_agent(parser_response)
        storage = StorageRepository(tmp_path)

        result = await process_correction(
            router_output=sample_router_output,
            parser_agent=parser,
            storage=storage,
            recent_entries=sample_entries,
            domain_schemas={},
            vocabulary={},
        )

        assert result.success is False
        assert result.error_message == "Could not identify target entry"

    @pytest.mark.asyncio
    async def test_calls_parser_with_correction_mode(
        self, tmp_path: Path, sample_router_output: RouterOutput, sample_entries: list[Entry]
    ) -> None:
        """Test that Parser is called with correction_mode=True."""
        parser_response: dict[str, Any] = {
            "date": "2026-01-14",
            "timestamp": "2026-01-14T10:45:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "Actually that was 185",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
            "is_correction": True,
            "target_entry_id": "2026-01-14_10-30-00",
            "correction_delta": {"weight_kg": 84.0},
        }
        parser = create_mock_parser_agent(parser_response)
        storage = StorageRepository(tmp_path)

        await process_correction(
            router_output=sample_router_output,
            parser_agent=parser,
            storage=storage,
            recent_entries=sample_entries,
            domain_schemas={"strength": StrengthSchema},
            vocabulary={"bp": "bench press"},
        )

        # Verify parser.parse was called with correction mode
        parser.parse.assert_called_once()  # type: ignore[union-attr]
        call_args: ParserInput = parser.parse.call_args[0][0]  # type: ignore[union-attr, reportUnknownMemberType]
        assert call_args.correction_mode is True  # pyright: ignore[reportUnknownMemberType]
        assert call_args.correction_target == "bench weight recorded as 85"  # pyright: ignore[reportUnknownMemberType]

    @pytest.mark.asyncio
    async def test_uses_reasoning_when_log_portion_is_none(
        self, tmp_path: Path, sample_entries: list[Entry]
    ) -> None:
        """Test that reasoning is used as fallback when log_portion is None."""
        router_output = RouterOutput(
            input_type=InputType.CORRECTION,
            confidence=0.9,
            selected_domains=["strength"],
            domain_selection_reasoning="Correcting entry",
            correction_target="bench weight",
            reasoning="Actually that was 185 not 85",  # This should be used
            log_portion=None,  # No log_portion
        )
        parser_response: dict[str, Any] = {
            "date": "2026-01-14",
            "timestamp": "2026-01-14T10:45:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "Actually that was 185 not 85",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
            "is_correction": True,
            "target_entry_id": "2026-01-14_10-30-00",
            "correction_delta": {"weight_kg": 84.0},
        }
        parser = create_mock_parser_agent(parser_response)
        storage = StorageRepository(tmp_path)

        await process_correction(
            router_output=router_output,
            parser_agent=parser,
            storage=storage,
            recent_entries=sample_entries,
            domain_schemas={"strength": StrengthSchema},
            vocabulary={},
        )

        # Verify parser received reasoning as raw_input
        parser.parse.assert_called_once()  # type: ignore[union-attr]
        call_args: ParserInput = parser.parse.call_args[0][0]  # type: ignore[union-attr, reportUnknownMemberType]
        assert call_args.raw_input == "Actually that was 185 not 85"  # pyright: ignore[reportUnknownMemberType]


# =============================================================================
# Test SessionState Correction Fields
# =============================================================================


class TestSessionStateCorrectionFields:
    """Tests for SessionState correction tracking fields."""

    def test_correction_fields_exist(self) -> None:
        """Test that correction fields can be set on SessionState."""
        state: SessionState = {
            "raw_input": "Actually that was 185",
            "input_type": "CORRECTION",
            "current_state": "ROUTE",
            "is_correction_flow": True,
            "correction_target": "bench weight recorded as 85",
            "correction_result": None,
        }

        assert state["is_correction_flow"] is True
        assert state["correction_target"] == "bench weight recorded as 85"
        assert state["correction_result"] is None

    def test_correction_result_as_dict(self) -> None:
        """Test storing CorrectionResult as dict in SessionState."""
        result = CorrectionResult(
            success=True,
            target_entry_id="2026-01-14_10-30-00",
            correction_delta={"weight_kg": 84.0},
        )

        state: SessionState = {
            "current_state": "DONE",
            "is_correction_flow": True,
            "correction_target": "bench weight",
            "correction_result": result.model_dump(),
        }

        correction_result = state["correction_result"]
        assert correction_result is not None
        assert correction_result["success"] is True
        assert correction_result["target_entry_id"] == "2026-01-14_10-30-00"

    def test_correction_fields_default_to_none(self) -> None:
        """Test that correction fields can be omitted (total=False)."""
        state: SessionState = {
            "raw_input": "How's my progress?",
            "current_state": "ROUTE",
        }

        assert state.get("is_correction_flow") is None
        assert state.get("correction_target") is None
        assert state.get("correction_result") is None


# =============================================================================
# Test Parser Prompt Correction Mode Enhancements
# =============================================================================


class TestParserCorrectionPrompt:
    """Tests for Parser prompt correction mode enhancements."""

    def test_prompt_includes_target_identification_section(self) -> None:
        """Test that prompt includes TARGET IDENTIFICATION section."""
        from quilto.llm import LLMClient

        config = create_test_config()
        client = LLMClient(config)
        parser = ParserAgent(client)

        parser_input = ParserInput(
            raw_input="Actually that was 185",
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            domain_schemas={"strength": StrengthSchema},
            vocabulary={},
            correction_mode=True,
            correction_target="bench weight recorded as 85",
        )

        prompt = parser.build_prompt(parser_input)

        assert "TARGET IDENTIFICATION" in prompt
        assert "bench weight recorded as 85" in prompt

    def test_prompt_includes_matching_instructions(self) -> None:
        """Test that prompt includes matching instructions."""
        from quilto.llm import LLMClient

        config = create_test_config()
        client = LLMClient(config)
        parser = ParserAgent(client)

        parser_input = ParserInput(
            raw_input="Actually that was 185",
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            domain_schemas={},
            vocabulary={},
            correction_mode=True,
            correction_target="yesterday's bench entry",
        )

        prompt = parser.build_prompt(parser_input)

        assert "Date matching" in prompt
        assert "Content matching" in prompt
        assert "Value matching" in prompt

    def test_prompt_includes_fallback_instructions(self) -> None:
        """Test that prompt includes fallback instructions for no match."""
        from quilto.llm import LLMClient

        config = create_test_config()
        client = LLMClient(config)
        parser = ParserAgent(client)

        parser_input = ParserInput(
            raw_input="Actually that was 185",
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            domain_schemas={},
            vocabulary={},
            correction_mode=True,
            correction_target="some entry",
        )

        prompt = parser.build_prompt(parser_input)

        assert "If no entry matches" in prompt
        assert "target_entry_id to null" in prompt

    def test_prompt_no_correction_section_when_not_correction_mode(self) -> None:
        """Test that correction section is absent when correction_mode=False."""
        from quilto.llm import LLMClient

        config = create_test_config()
        client = LLMClient(config)
        parser = ParserAgent(client)

        parser_input = ParserInput(
            raw_input="Bench pressed 185x5",
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            domain_schemas={},
            vocabulary={},
            correction_mode=False,
        )

        prompt = parser.build_prompt(parser_input)

        assert "CORRECTION MODE" not in prompt
        assert "TARGET IDENTIFICATION" not in prompt


# =============================================================================
# Test StorageRepository Correction Integration
# =============================================================================


class TestStorageRepositoryCorrectionIntegration:
    """Integration tests for correction with StorageRepository."""

    def test_correction_appends_to_raw_file(self, tmp_path: Path) -> None:
        """Test that correction appends with [correction] marker."""
        storage = StorageRepository(tmp_path)

        # Save original entry
        original = Entry(
            id="2026-01-14_10-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 30, 0),
            raw_content="Bench pressed 85x5",
            parsed_data={"strength": {"exercise": "bench press", "weight_kg": 38.6}},
        )
        storage.save_entry(original)

        # Save correction
        correction_entry = Entry(
            id="2026-01-14_10-45-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            raw_content="Correction: bench was 185, not 85",
        )
        correction = ParserOutput(
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            domain_data={},
            raw_content="Correction: bench was 185, not 85",
            confidence=0.9,
            is_correction=True,
            target_entry_id="2026-01-14_10-30-00",
            correction_delta={"weight_kg": 84.0},
        )
        storage.save_entry(correction_entry, correction=correction)

        # Verify raw file
        raw_path = tmp_path / "logs" / "raw" / "2026" / "01" / "2026-01-14.md"
        content = raw_path.read_text()

        assert "## 10:30" in content
        assert "## 10:45 [correction]" in content
        assert "Bench pressed 85x5" in content
        assert "Correction: bench was 185" in content

    def test_correction_updates_parsed_json(self, tmp_path: Path) -> None:
        """Test that correction updates parsed JSON with upsert."""
        storage = StorageRepository(tmp_path)

        # Save original entry
        original = Entry(
            id="2026-01-14_10-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 30, 0),
            raw_content="Bench pressed 85x5",
            parsed_data={"exercise": "bench press", "weight_kg": 38.6, "reps": 5},
        )
        storage.save_entry(original)

        # Save correction
        correction_entry = Entry(
            id="2026-01-14_10-45-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            raw_content="Correction: weight was 84kg",
        )
        correction = ParserOutput(
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            domain_data={},
            raw_content="Correction: weight was 84kg",
            confidence=0.9,
            is_correction=True,
            target_entry_id="2026-01-14_10-30-00",
            correction_delta={"weight_kg": 84.0},  # Only update weight
        )
        storage.save_entry(correction_entry, correction=correction)

        # Verify parsed JSON has upsert semantics
        parsed_path = tmp_path / "logs" / "parsed" / "2026" / "01" / "2026-01-14.json"
        parsed_data = json.loads(parsed_path.read_text())

        # Original fields preserved, weight updated
        assert parsed_data["2026-01-14_10-30-00"]["exercise"] == "bench press"
        assert parsed_data["2026-01-14_10-30-00"]["reps"] == 5
        assert parsed_data["2026-01-14_10-30-00"]["weight_kg"] == 84.0  # Updated

    def test_reading_corrected_entries(self, tmp_path: Path) -> None:
        """Test that reading entries returns updated data after correction."""
        storage = StorageRepository(tmp_path)

        # Save original entry
        original = Entry(
            id="2026-01-14_10-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 30, 0),
            raw_content="Bench pressed 85x5",
            parsed_data={"exercise": "bench press", "weight_kg": 38.6},
        )
        storage.save_entry(original)

        # Save correction
        correction_entry = Entry(
            id="2026-01-14_10-45-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            raw_content="Correction: weight was 84kg",
        )
        correction = ParserOutput(
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 45, 0),
            domain_data={},
            raw_content="Correction: weight was 84kg",
            confidence=0.9,
            is_correction=True,
            target_entry_id="2026-01-14_10-30-00",
            correction_delta={"weight_kg": 84.0},
        )
        storage.save_entry(correction_entry, correction=correction)

        # Read entries back
        entries = storage.get_entries_by_date_range(date(2026, 1, 14), date(2026, 1, 14))

        # Should have 2 entries (original + correction)
        assert len(entries) == 2

        # Original entry should have updated parsed_data
        original_entry = next(e for e in entries if e.id == "2026-01-14_10-30-00")
        assert original_entry.parsed_data is not None
        assert original_entry.parsed_data["weight_kg"] == 84.0


# =============================================================================
# Test Module Exports
# =============================================================================


class TestModuleExports:
    """Tests for module exports."""

    def test_correction_result_importable_from_quilto_flow(self) -> None:
        """Test CorrectionResult is importable from quilto.flow."""
        from quilto.flow import CorrectionResult as CR

        assert CR is not None

    def test_process_correction_importable_from_quilto_flow(self) -> None:
        """Test process_correction is importable from quilto.flow."""
        from quilto.flow import process_correction as pc

        assert callable(pc)

    def test_correction_result_importable_from_quilto(self) -> None:
        """Test CorrectionResult is importable from main quilto package."""
        from quilto import CorrectionResult as CR

        assert CR is not None

    def test_process_correction_importable_from_quilto(self) -> None:
        """Test process_correction is importable from main quilto package."""
        from quilto import process_correction as pc

        assert callable(pc)
