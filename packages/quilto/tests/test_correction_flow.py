"""Tests for correction flow module.

Tests cover:
- CorrectionResult model validation
- process_correction orchestration function
- SessionState correction fields
- Parser prompt correction mode enhancements
- Integration with StorageRepository
- correction_node response generation (Story 19.1)
- _build_process_result correction_result extraction (Story 19.1)
- End-to-end correction flow with mock LLM (Story 19.1)
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ValidationError
from quilto import CorrectionResult, process_correction
from quilto.agents import ParserAgent
from quilto.agents.models import InputType, ParserInput, ParserOutput, RouterOutput
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels
from quilto.state import SessionState
from quilto.storage import Entry, StorageRepository

if TYPE_CHECKING:
    from quilto.session import Session

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
# Test CorrectionEdit Model (Story 21.1)
# =============================================================================


class TestCorrectionEditModel:
    """Tests for CorrectionEdit Pydantic model."""

    def test_correction_edit_creation(self) -> None:
        """Test creating a valid CorrectionEdit."""
        from quilto.flow.models import CorrectionEdit

        edit = CorrectionEdit(
            target_file=Path("raw/2026/01/2026-01-26.md"),
            section_start=12,
            section_end=18,
            original_content="## 18:33\n40 minutes at 8kph, 5km",
            new_content="## 18:33\n40 minutes at 8kph, 3km",
        )

        assert edit.target_file == Path("raw/2026/01/2026-01-26.md")
        assert edit.section_start == 12
        assert edit.section_end == 18
        assert "5km" in edit.original_content
        assert "3km" in edit.new_content

    def test_correction_edit_strict_mode(self) -> None:
        """Test CorrectionEdit strict mode rejects type coercion."""
        from quilto.flow.models import CorrectionEdit

        with pytest.raises(ValidationError):
            CorrectionEdit(
                target_file="raw/2026/01/2026-01-26.md",  # type: ignore[arg-type]  # Should be Path
                section_start=12,
                section_end=18,
                original_content="original",
                new_content="new",
            )


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

    def test_successful_correction_result_with_file_info(self) -> None:
        """Test CorrectionResult with modified_file and edited_lines (Story 21.1)."""
        result = CorrectionResult(
            success=True,
            target_entry_id="2026-01-14_10-30-00",
            correction_delta={"weight_kg": 84.0},
            original_entry_id="2026-01-14_10-30-00",
            modified_file=Path("raw/2026/01/2026-01-14.md"),
            edited_lines=(12, 18),
        )

        assert result.modified_file == Path("raw/2026/01/2026-01-14.md")
        assert result.edited_lines == (12, 18)

    def test_failed_correction_result(self) -> None:
        """Test valid failed CorrectionResult."""
        result = CorrectionResult(
            success=False,
            error_message="Could not identify target entry",
        )

        assert result.success is False
        assert result.error_message == "Could not identify target entry"
        assert result.target_entry_id is None
        assert result.modified_file is None
        assert result.edited_lines is None

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
            user_input="Actually that was 185 not 85",
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
                user_input="test input",
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
            user_input="test input",
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
            user_input="Actually that was 185",
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
            user_input="Actually that was 185",
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
            user_input="Actually that was 185",
        )

        # Verify parser.parse was called with correction mode
        parser.parse.assert_called_once()  # type: ignore[union-attr]
        call_args: ParserInput = parser.parse.call_args[0][0]  # type: ignore[union-attr, reportUnknownMemberType]
        assert call_args.correction_mode is True  # pyright: ignore[reportUnknownMemberType]
        assert call_args.correction_target == "bench weight recorded as 85"  # pyright: ignore[reportUnknownMemberType]

    @pytest.mark.asyncio
    async def test_uses_user_input_not_router_reasoning(self, tmp_path: Path, sample_entries: list[Entry]) -> None:
        """Test that Parser receives user_input, not Router reasoning.

        Story 19.1 fix: Previously, process_correction used
        router_output.log_portion or router_output.reasoning as raw_input.
        For CORRECTION, log_portion is null, so Parser received the
        Router's classification reasoning instead of user text.
        Now user_input is passed explicitly.
        """
        router_output = RouterOutput(
            input_type=InputType.CORRECTION,
            confidence=0.9,
            selected_domains=["strength"],
            domain_selection_reasoning="Correcting entry",
            correction_target="bench weight",
            reasoning="The statement explicitly revises previously logged data",
            log_portion=None,
        )
        parser_response: dict[str, Any] = {
            "date": "2026-01-14",
            "timestamp": "2026-01-14T10:45:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "I logged 5 sets but it should be 4",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
            "is_correction": True,
            "target_entry_id": "2026-01-14_10-30-00",
            "correction_delta": {"weight_kg": 84.0},
        }
        parser = create_mock_parser_agent(parser_response)
        storage = StorageRepository(tmp_path)

        user_text = "I logged 5 sets but it should be 4"
        await process_correction(
            router_output=router_output,
            parser_agent=parser,
            storage=storage,
            recent_entries=sample_entries,
            domain_schemas={"strength": StrengthSchema},
            vocabulary={},
            user_input=user_text,
        )

        # Verify parser received user_input, NOT Router reasoning
        parser.parse.assert_called_once()  # type: ignore[union-attr]
        call_args: ParserInput = parser.parse.call_args[0][0]  # type: ignore[union-attr, reportUnknownMemberType]
        assert call_args.raw_input == user_text  # pyright: ignore[reportUnknownMemberType]
        assert call_args.raw_input != router_output.reasoning  # pyright: ignore[reportUnknownMemberType]


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
        """Test that prompt includes matching instructions (updated in 21.4)."""
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

        # Story 21.4: Updated to MATCHING PRIORITY ORDER format
        assert "MATCHING PRIORITY ORDER" in prompt
        assert "EXACT TIME MATCH" in prompt
        assert "EXERCISE/ACTIVITY KEYWORD" in prompt
        assert "VALUE MATCH" in prompt

    def test_prompt_includes_fallback_instructions(self) -> None:
        """Test that prompt includes fallback instructions for no match (updated in 21.4)."""
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

        # Story 21.4: Updated to FAILURE GUIDANCE section
        assert "FAILURE GUIDANCE" in prompt
        assert "target_entry_id = null" in prompt

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
# Test StorageRepository Correction Integration (In-Place Editing)
# =============================================================================


class TestStorageRepositoryCorrectionIntegration:
    """Integration tests for in-place correction with StorageRepository.

    Note: Story 21.1 changed correction behavior from append-based to in-place editing.
    - Old behavior: save_entry() appended "## HH:MM [correction]" sections
    - New behavior: edit_raw_section() modifies original section in-place
    """

    def test_in_place_edit_modifies_raw_file(self, tmp_path: Path) -> None:
        """Test that in-place edit modifies raw file without [correction] marker."""
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

        # Use in-place edit (as correction flow now does)
        raw_path = tmp_path / "raw" / "2026" / "01" / "2026-01-14.md"
        storage.edit_raw_section(
            raw_path,
            start=0,
            end=2,  # Header + content
            new_content="## 10:30\nBench pressed 185x5 (corrected)\n",
        )

        # Verify raw file has corrected content, NO [correction] marker
        content = raw_path.read_text()
        assert "## 10:30" in content
        assert "[correction]" not in content
        assert "185x5 (corrected)" in content
        assert "Bench pressed 85" not in content  # Original "85x5" gone (not as substring of 185)

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

        # Save correction - this still updates parsed JSON
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
        parsed_path = tmp_path / "parsed" / "2026" / "01" / "2026-01-14.json"
        parsed_data = json.loads(parsed_path.read_text())

        # Original fields preserved, weight updated
        assert parsed_data["2026-01-14_10-30-00"]["exercise"] == "bench press"
        assert parsed_data["2026-01-14_10-30-00"]["reps"] == 5
        assert parsed_data["2026-01-14_10-30-00"]["weight_kg"] == 84.0  # Updated

    def test_in_place_edit_then_read_entries(self, tmp_path: Path) -> None:
        """Test that reading entries after in-place edit returns corrected content."""
        storage = StorageRepository(tmp_path)

        # Save original entry
        original = Entry(
            id="2026-01-14_10-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 30, 0),
            raw_content="Ran 5km in 30 minutes",
            parsed_data={"distance_km": 5},
        )
        storage.save_entry(original)

        # Edit raw section in-place (as new correction flow does)
        raw_path = tmp_path / "raw" / "2026" / "01" / "2026-01-14.md"
        storage.edit_raw_section(
            raw_path,
            start=0,
            end=2,
            new_content="## 10:30\nRan 3km in 30 minutes (corrected distance)\n",
        )

        # Update parsed JSON
        parsed_path = storage._get_parsed_path(date(2026, 1, 14))  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        storage._update_parsed_json(parsed_path, "2026-01-14_10-30-00", {"distance_km": 3})  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

        # Read entries back
        entries = storage.get_entries_by_date_range(date(2026, 1, 14), date(2026, 1, 14))

        # Should have 1 entry (no duplicate from old [correction] append)
        assert len(entries) == 1

        # Entry should have corrected raw_content and parsed_data
        entry = entries[0]
        assert entry.id == "2026-01-14_10-30-00"
        assert "3km" in entry.raw_content
        assert entry.parsed_data is not None
        assert entry.parsed_data["distance_km"] == 3

    def test_no_correction_marker_in_raw_file(self, tmp_path: Path) -> None:
        """Test that [correction] marker is NOT created after in-place edit."""
        storage = StorageRepository(tmp_path)

        # Save original entry
        original = Entry(
            id="2026-01-14_10-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 30, 0),
            raw_content="Original content",
            parsed_data={},
        )
        storage.save_entry(original)

        # Perform in-place edit
        raw_path = tmp_path / "raw" / "2026" / "01" / "2026-01-14.md"
        storage.edit_raw_section(
            raw_path,
            start=0,
            end=2,
            new_content="## 10:30\nCorrected content\n",
        )

        # Verify NO [correction] marker anywhere
        content = raw_path.read_text()
        assert "[correction]" not in content

    def test_surgical_edit_preserves_surrounding_content_integration(self, tmp_path: Path) -> None:
        """Integration test: surgical edit preserves byte-identical surrounding content (AC: #1-#4).

        Story 21.2: Verify that edit_raw_section() preserves surrounding content byte-for-byte.
        Creates raw file with 3 sections, edits middle section, verifies:
        - Leading section (## 08:00) is byte-identical after edit
        - Trailing section (## 18:00) is byte-identical after edit

        Uses content-based matching (not hardcoded indices) to be robust against
        different replacement line counts.
        """
        storage = StorageRepository(tmp_path)

        # Create raw file with 3 sections: 08:00, 12:00, 18:00
        raw_dir = tmp_path / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        original_content = (
            "## 08:00\nMorning workout - 30 min jog\n\n"
            "## 12:00\nLunch gym - bench press 60kg\n\n"
            "## 18:00\nEvening yoga - 45 min session\n"
        )
        raw_path = raw_dir / "2026-01-26.md"
        raw_path.write_text(original_content, encoding="utf-8")

        # Capture surrounding sections by content markers (robust to line count changes)
        middle_marker = "## 12:00"
        trailing_marker = "## 18:00"

        # Leading section: from start to just before middle marker
        middle_start_idx = original_content.find(middle_marker)
        leading_bytes_before = original_content[:middle_start_idx].encode("utf-8")

        # Trailing section: from trailing marker to end
        trailing_start_idx = original_content.find(trailing_marker)
        trailing_bytes_before = original_content[trailing_start_idx:].encode("utf-8")

        # Edit middle section (12:00) with different line count than original
        storage.edit_raw_section(
            raw_path,
            start=3,
            end=6,
            new_content="## 12:00\nLunch gym - bench press 80kg (corrected)\nAdditional notes here\n\n",
        )

        # Read modified content
        modified_content = raw_path.read_text(encoding="utf-8")

        # Verify leading section (## 08:00) is byte-identical
        middle_start_idx_after = modified_content.find(middle_marker)
        leading_bytes_after = modified_content[:middle_start_idx_after].encode("utf-8")
        assert leading_bytes_before == leading_bytes_after, (
            f"Leading section not preserved. Before: {leading_bytes_before!r}, After: {leading_bytes_after!r}"
        )

        # Verify trailing section (## 18:00) is byte-identical
        trailing_start_idx_after = modified_content.find(trailing_marker)
        trailing_bytes_after = modified_content[trailing_start_idx_after:].encode("utf-8")
        assert trailing_bytes_before == trailing_bytes_after, (
            f"Trailing section not preserved. Before: {trailing_bytes_before!r}, After: {trailing_bytes_after!r}"
        )

        # Additional verification: the edit actually happened
        assert "80kg (corrected)" in modified_content
        assert "Additional notes here" in modified_content
        assert "60kg" not in modified_content  # Old value gone

    def test_correction_reparse_removes_old_fields(self, tmp_path: Path) -> None:
        """Test that re-parse uses replace semantics, removing fields not in new output.

        Story 21.3 AC #4: If original entry has fields that the corrected re-parse
        doesn't include, those fields should be removed (replace, not merge).

        This tests the fix: correction flow uses _save_parsed_json() (assignment)
        instead of _update_parsed_json() (.update() merge).
        """
        storage = StorageRepository(tmp_path)

        # 1. Save original entry with notes field
        original = Entry(
            id="2026-01-14_10-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 30, 0),
            raw_content="Bench press 80kg, felt good",
            parsed_data={"exercise": "bench press", "weight_kg": 80, "notes": "felt good"},
        )
        storage.save_entry(original)

        # Verify original parsed data has notes
        parsed_path = storage._get_parsed_path(date(2026, 1, 14))  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        initial_data = json.loads(parsed_path.read_text())
        assert "notes" in initial_data["2026-01-14_10-30-00"]

        # 2. Simulate re-parse output after correction (no notes field)
        reparse_output = {"exercise": "bench press", "weight_kg": 85}  # notes field GONE

        # 3. Use _save_parsed_json (replace semantics) - this is what correction flow now uses
        storage._save_parsed_json(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
            parsed_path,
            "2026-01-14_10-30-00",
            reparse_output,
        )

        # 4. Verify the notes field is GONE (replace semantics)
        final_data = json.loads(parsed_path.read_text())
        entry_data = final_data["2026-01-14_10-30-00"]

        assert "notes" not in entry_data, (
            f"Field 'notes' should be removed by replace semantics, but found: {entry_data}"
        )
        assert entry_data["exercise"] == "bench press"
        assert entry_data["weight_kg"] == 85

    def test_reparse_only_updates_target_entry(self, tmp_path: Path) -> None:
        """Test that re-parsing only updates the target entry, not other entries.

        Story 21.3 AC #3: Other sections in the same raw file should have their
        parsed entries unchanged after correction.
        """
        storage = StorageRepository(tmp_path)

        # 1. Create 2 entries in the same day
        entry1 = Entry(
            id="2026-01-14_08-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 8, 30, 0),
            raw_content="Morning run 5km",
            parsed_data={"exercise": "running", "distance_km": 5, "time_of_day": "morning"},
        )
        entry2 = Entry(
            id="2026-01-14_18-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 18, 30, 0),
            raw_content="Evening run 3km",
            parsed_data={"exercise": "running", "distance_km": 3, "time_of_day": "evening"},
        )
        storage.save_entry(entry1)
        storage.save_entry(entry2)

        # 2. Capture first entry's parsed data (byte-identical comparison)
        parsed_path = storage._get_parsed_path(date(2026, 1, 14))  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        initial_data = json.loads(parsed_path.read_text())
        first_entry_before = json.dumps(initial_data["2026-01-14_08-30-00"], sort_keys=True)

        # 3. Simulate correcting the SECOND entry only (replace semantics)
        corrected_second = {"exercise": "running", "distance_km": 4, "time_of_day": "evening"}  # Changed 3→4
        storage._save_parsed_json(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
            parsed_path,
            "2026-01-14_18-30-00",  # Only update second entry
            corrected_second,
        )

        # 4. Read back and verify
        final_data = json.loads(parsed_path.read_text())

        # First entry should be byte-identical
        first_entry_after = json.dumps(final_data["2026-01-14_08-30-00"], sort_keys=True)
        assert first_entry_before == first_entry_after, (
            f"First entry was modified. Before: {first_entry_before}, After: {first_entry_after}"
        )

        # Second entry should reflect the correction
        assert final_data["2026-01-14_18-30-00"]["distance_km"] == 4
        assert final_data["2026-01-14_18-30-00"]["exercise"] == "running"


# =============================================================================
# Story 21.6: Correction Merge Integration Tests
# =============================================================================


class TestCorrectionMergeIntegration:
    """Integration tests for correction raw_content merge behavior.

    Story 21.6: Fix CORRECTION Raw Content Merge

    These tests require --use-real-ollama to validate actual LLM merge behavior.
    They test Parser.parse() directly with correction_mode=True, which is what
    the correction flow uses internally.
    """

    @pytest.mark.asyncio
    async def test_correction_flow_produces_merged_raw_content(
        self,
        tmp_path: Path,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
    ) -> None:
        """Integration test: Parser produces merged raw_content.

        Story 21.6 AC #1: Given correction "actually it was 20 minutes at 7.5kph"
        targeting "Ran treadmill for 35 minutes at 8kph", the Parser should
        output merged content like "Ran treadmill for 20 minutes at 7.5kph".

        Verifies:
        - raw_content contains "treadmill" (original activity preserved)
        - raw_content contains "20" (corrected value)
        - raw_content does NOT contain "actually" (literal replacement avoided)
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for merge behavior testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        llm_client = LLMClient(config)
        parser = ParserAgent(llm_client)

        # Create mock entries representing recent history
        class MockEntry:
            def __init__(self, entry_id: str, raw_content: str, parsed_data: dict[str, Any]) -> None:
                self.id = entry_id
                self.raw_content = raw_content
                self.parsed_data = parsed_data

        recent_entries = [
            MockEntry(
                entry_id="2026-01-26_10-30-00",
                raw_content="Ran treadmill for 35 minutes at 8kph",
                parsed_data={"cardio": {"activity": "treadmill", "duration_min": 35}},
            ),
        ]

        result = await parser.parse(
            ParserInput(
                raw_input="actually it was 20 minutes at 7.5kph",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={},  # Not needed for raw_content test
                vocabulary={},
                correction_mode=True,
                correction_target="the treadmill entry",
                recent_entries=recent_entries,
            )
        )

        # AC #1: raw_content should be merged, not literal
        assert result.raw_content != "actually it was 20 minutes at 7.5kph", (
            f"raw_content should be MERGED, not literal input. Got: {result.raw_content}"
        )

        # AC #1: Should preserve activity context from original
        activity_preserved = "treadmill" in result.raw_content.lower() or "ran" in result.raw_content.lower()
        assert activity_preserved, f"Activity context not preserved. Got: {result.raw_content}"

        # AC #1: Should have corrected duration
        assert "20" in result.raw_content, f"Corrected duration not in content. Got: {result.raw_content}"

        # AC #4: Should NOT contain literal correction phrase "actually"
        assert "actually" not in result.raw_content.lower(), (
            f"Contains literal correction phrase. Got: {result.raw_content}"
        )

    @pytest.mark.asyncio
    async def test_correction_preserves_unmodified_context(
        self,
        tmp_path: Path,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
    ) -> None:
        """Integration test: Parser preserves context not being changed.

        Story 21.6 AC #2: Given correction "it was 4 sets not 5" targeting
        "Did 5 sets of bench press at 80kg, felt strong", the merged content
        should preserve weight (80kg) and notes (felt strong).
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag for merge behavior testing")

        from quilto import load_llm_config
        from quilto.llm import LLMClient

        config = load_llm_config(integration_llm_config_path)
        llm_client = LLMClient(config)
        parser = ParserAgent(llm_client)

        class MockEntry:
            def __init__(self, entry_id: str, raw_content: str, parsed_data: dict[str, Any]) -> None:
                self.id = entry_id
                self.raw_content = raw_content
                self.parsed_data = parsed_data

        recent_entries = [
            MockEntry(
                entry_id="2026-01-26_18-30-00",
                raw_content="Did 5 sets of bench press at 80kg, felt strong",
                parsed_data={
                    "strength": {
                        "exercise": "bench press",
                        "weight_kg": 80,
                        "sets": 5,
                    }
                },
            ),
        ]

        result = await parser.parse(
            ParserInput(
                raw_input="it was 4 sets not 5",
                timestamp=datetime(2026, 1, 26, 20, 0, 0),
                domain_schemas={},
                vocabulary={},
                correction_mode=True,
                correction_target="the bench press entry",
                recent_entries=recent_entries,
            )
        )

        # AC #2: Preserve exercise type
        assert "bench press" in result.raw_content.lower(), f"Exercise type not preserved. Got: {result.raw_content}"

        # AC #2: Preserve weight
        assert "80" in result.raw_content, f"Weight not preserved. Got: {result.raw_content}"

        # AC #2: Have corrected sets (4, not 5 as original)
        assert "4" in result.raw_content, f"Corrected sets not in content. Got: {result.raw_content}"


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


# =============================================================================
# Test correction_node Response Generation (Story 19.1 - Tasks 5.3, 5.4)
# =============================================================================


class TestCorrectionNodeResponse:
    """Tests for correction_node setting StateKeys.RESPONSE.

    Story 19.1: Bug 2 fix - correction_node must set RESPONSE
    so the CLI displays feedback to the user.
    """

    @pytest.mark.asyncio
    async def test_correction_node_sets_response_on_success(self, tmp_path: Path) -> None:
        """Test that correction_node sets RESPONSE on successful correction."""
        from unittest.mock import MagicMock

        from quilto.domain import DomainModule
        from quilto.orchestration import StateKeys, correction_node
        from quilto.quilto import Quilto

        # Build mock domain
        domain = DomainModule(
            name="strength",
            description="Strength training",
            log_schema=StrengthSchema,
            vocabulary={"bp": "bench press"},
            expertise="Strength training expertise",
            response_evaluation_rules=[],
            context_management_guidance="",
            clarification_patterns={},
        )

        # Build Quilto with mocked LLM
        mock_llm = MagicMock()
        storage = StorageRepository(tmp_path)

        # Create an entry in storage for the correction to target
        entry = Entry(
            id="2026-01-14_10-30-00",
            date=date(2026, 1, 14),
            timestamp=datetime(2026, 1, 14, 10, 30, 0),
            raw_content="Bench pressed 85x5",
            parsed_data={"strength": {"exercise": "bench press", "weight_kg": 38.6}},
        )
        storage.save_entry(entry)

        q = Quilto(
            llm_client=mock_llm,
            storage=storage,
            domains=[domain],
            session_db_path=":memory:",
        )

        # Mock process_correction to return success
        import quilto.orchestration as orch_module

        success_result = CorrectionResult(
            success=True,
            target_entry_id="2026-01-14_10-30-00",
            correction_delta={"weight_kg": 84.0},
        )

        async def mock_process_correction(**kwargs: Any) -> CorrectionResult:  # type: ignore[no-untyped-def]
            return success_result

        original_fn = orch_module.process_correction
        orch_module.process_correction = mock_process_correction  # type: ignore[assignment]

        try:
            state = {
                StateKeys.QUILTO: q,
                StateKeys.USER_INPUT: "I logged 85 but it should be 185",
                StateKeys.ROUTER_OUTPUT: RouterOutput(
                    input_type=InputType.CORRECTION,
                    confidence=0.9,
                    selected_domains=["strength"],
                    domain_selection_reasoning="Correcting",
                    correction_target="bench weight",
                    reasoning="User is correcting",
                ).model_dump(),
                StateKeys.DOMAIN_CONTEXT: {
                    "domains_loaded": [],
                    "vocabulary": {"bp": "bench press"},
                    "expertise": "Strength training",
                },
                StateKeys.TRACES: [],
            }

            result = await correction_node(state)  # type: ignore[arg-type]

            assert StateKeys.RESPONSE in result
            assert result[StateKeys.RESPONSE] is not None
            assert len(result[StateKeys.RESPONSE]) > 0
            assert "2026-01-14_10-30-00" in result[StateKeys.RESPONSE]
        finally:
            orch_module.process_correction = original_fn  # type: ignore[assignment]

    @pytest.mark.asyncio
    async def test_correction_node_sets_response_on_failure(self, tmp_path: Path) -> None:
        """Test that correction_node sets RESPONSE on failed correction."""
        from unittest.mock import MagicMock

        from quilto.domain import DomainModule
        from quilto.orchestration import StateKeys, correction_node
        from quilto.quilto import Quilto

        domain = DomainModule(
            name="strength",
            description="Strength training",
            log_schema=StrengthSchema,
            vocabulary={},
            expertise="Strength training expertise",
            response_evaluation_rules=[],
            context_management_guidance="",
            clarification_patterns={},
        )

        mock_llm = MagicMock()
        storage = StorageRepository(tmp_path)

        q = Quilto(
            llm_client=mock_llm,
            storage=storage,
            domains=[domain],
            session_db_path=":memory:",
        )

        # Mock process_correction to return failure
        import quilto.orchestration as orch_module

        failure_result = CorrectionResult(
            success=False,
            error_message="Parser did not identify correction",
        )

        async def mock_process_correction(**kwargs: Any) -> CorrectionResult:  # type: ignore[no-untyped-def]
            return failure_result

        original_fn = orch_module.process_correction
        orch_module.process_correction = mock_process_correction  # type: ignore[assignment]

        try:
            state = {
                StateKeys.QUILTO: q,
                StateKeys.USER_INPUT: "I logged 85 but it should be 185",
                StateKeys.ROUTER_OUTPUT: RouterOutput(
                    input_type=InputType.CORRECTION,
                    confidence=0.9,
                    selected_domains=["strength"],
                    domain_selection_reasoning="Correcting",
                    correction_target="bench weight",
                    reasoning="User is correcting",
                ).model_dump(),
                StateKeys.DOMAIN_CONTEXT: {
                    "domains_loaded": [],
                    "vocabulary": {},
                    "expertise": "Strength training",
                },
                StateKeys.TRACES: [],
            }

            result = await correction_node(state)  # type: ignore[arg-type]

            assert StateKeys.RESPONSE in result
            assert "Could not process correction" in result[StateKeys.RESPONSE]
            assert "Parser did not identify correction" in result[StateKeys.RESPONSE]
        finally:
            orch_module.process_correction = original_fn  # type: ignore[assignment]

    @pytest.mark.asyncio
    async def test_correction_node_sets_response_on_exception(self, tmp_path: Path) -> None:
        """Test that correction_node sets RESPONSE when exception occurs."""
        from unittest.mock import MagicMock

        from quilto.domain import DomainModule
        from quilto.orchestration import StateKeys, correction_node
        from quilto.quilto import Quilto

        domain = DomainModule(
            name="strength",
            description="Strength training",
            log_schema=StrengthSchema,
            vocabulary={},
            expertise="Strength training expertise",
            response_evaluation_rules=[],
            context_management_guidance="",
            clarification_patterns={},
        )

        mock_llm = MagicMock()
        storage = StorageRepository(tmp_path)

        q = Quilto(
            llm_client=mock_llm,
            storage=storage,
            domains=[domain],
            session_db_path=":memory:",
        )

        # Mock process_correction to raise exception
        import quilto.orchestration as orch_module

        async def mock_process_correction(**kwargs: Any) -> CorrectionResult:  # type: ignore[no-untyped-def]
            raise RuntimeError("Storage unavailable")

        original_fn = orch_module.process_correction
        orch_module.process_correction = mock_process_correction  # type: ignore[assignment]

        try:
            state = {
                StateKeys.QUILTO: q,
                StateKeys.USER_INPUT: "Fix my entry",
                StateKeys.ROUTER_OUTPUT: RouterOutput(
                    input_type=InputType.CORRECTION,
                    confidence=0.9,
                    selected_domains=["strength"],
                    domain_selection_reasoning="Correcting",
                    correction_target="bench weight",
                    reasoning="User is correcting",
                ).model_dump(),
                StateKeys.DOMAIN_CONTEXT: {
                    "domains_loaded": [],
                    "vocabulary": {},
                    "expertise": "Strength training",
                },
                StateKeys.TRACES: [],
            }

            result = await correction_node(state)  # type: ignore[arg-type]

            assert StateKeys.RESPONSE in result
            assert "Could not process correction" in result[StateKeys.RESPONSE]
            assert "Storage unavailable" in result[StateKeys.RESPONSE]
        finally:
            orch_module.process_correction = original_fn  # type: ignore[assignment]


# =============================================================================
# Test _build_process_result includes correction_result (Story 19.1 - Task 5.5)
# =============================================================================


class TestBuildProcessResultCorrection:
    """Tests for _build_process_result correction_result extraction."""

    @pytest.fixture
    def session(self) -> "Session":
        """Create session for testing _build_process_result."""
        from quilto.session import Session
        from quilto.session.models import SessionConfig, SessionData
        from quilto.session.stores import SQLiteSessionStore

        store = SQLiteSessionStore(":memory:")
        config = SessionConfig()
        now = datetime.now()
        data = SessionData(session_id="test", created_at=now, updated_at=now)
        store.save(data)
        return Session(data, store, config)

    def test_correction_result_extracted_from_state(self, session: "Session") -> None:
        """Test that _build_process_result includes correction_result from state."""
        correction_data = {
            "success": True,
            "target_entry_id": "2026-01-14_10-30-00",
            "correction_delta": {"weight_kg": 84.0},
            "original_entry_id": "2026-01-14_10-30-00",
            "error_message": None,
        }
        state: dict[str, Any] = {
            "input_type": "correction",
            "response": "Corrected entry 2026-01-14_10-30-00",
            "confidence": None,
            "source_entry_ids": [],
            "parsed_data": None,
            "selected_domains": ["strength"],
            "clarify_questions": None,
            "correction_result": correction_data,
        }

        result = session._build_process_result(state)  # pyright: ignore[reportPrivateUsage]

        assert result.correction_result is not None
        assert result.correction_result["success"] is True
        assert result.correction_result["target_entry_id"] == "2026-01-14_10-30-00"
        assert result.correction_result["correction_delta"] == {"weight_kg": 84.0}
        assert result.input_type == "correction"

    def test_correction_result_none_when_not_correction(self, session: "Session") -> None:
        """Test that correction_result is None for non-correction inputs."""
        state: dict[str, Any] = {
            "input_type": "query",
            "response": "Your progress looks great",
            "confidence": 0.9,
            "source_entry_ids": [],
            "parsed_data": None,
            "selected_domains": ["strength"],
            "clarify_questions": None,
        }

        result = session._build_process_result(state)  # pyright: ignore[reportPrivateUsage]

        assert result.correction_result is None

    def test_correction_result_none_when_correction_failed(self, session: "Session") -> None:
        """Test that correction_result captures failure details."""
        correction_data = {
            "success": False,
            "target_entry_id": None,
            "correction_delta": None,
            "original_entry_id": None,
            "error_message": "Parser did not identify correction",
        }
        state: dict[str, Any] = {
            "input_type": "correction",
            "response": "Could not process correction: Parser did not identify correction",
            "confidence": None,
            "source_entry_ids": [],
            "parsed_data": None,
            "selected_domains": ["strength"],
            "clarify_questions": None,
            "correction_result": correction_data,
        }

        result = session._build_process_result(state)  # pyright: ignore[reportPrivateUsage]

        assert result.correction_result is not None
        assert result.correction_result["success"] is False
        assert result.correction_result["error_message"] == "Parser did not identify correction"
        assert result.response is not None
        assert "Could not process correction" in result.response


# =============================================================================
# Test End-to-End Correction with Mock LLM (Story 19.1 - Task 5.6)
# =============================================================================


class TestCorrectionEndToEnd:
    """End-to-end test verifying non-empty response for CORRECTION flow."""

    @pytest.mark.asyncio
    async def test_correction_flow_returns_non_empty_response(self, tmp_path: Path) -> None:
        """Test that a full correction flow produces a non-empty response.

        Mocks process_correction to simulate a successful correction and
        verifies that correction_node returns both RESPONSE and CORRECTION_RESULT.
        """
        from unittest.mock import MagicMock

        from quilto.domain import DomainModule
        from quilto.orchestration import StateKeys, correction_node
        from quilto.quilto import Quilto

        domain = DomainModule(
            name="strength",
            description="Strength training",
            log_schema=StrengthSchema,
            vocabulary={"bp": "bench press"},
            expertise="Strength training expertise",
            response_evaluation_rules=[],
            context_management_guidance="",
            clarification_patterns={},
        )

        mock_llm = MagicMock()
        storage = StorageRepository(tmp_path)

        # Pre-populate storage with entry to correct
        entry = Entry(
            id="2026-01-27_10-30-00",
            date=date(2026, 1, 27),
            timestamp=datetime(2026, 1, 27, 10, 30, 0),
            raw_content="5 sets of pull-ups",
            parsed_data={"strength": {"exercise": "pull-ups", "sets": 5}},
        )
        storage.save_entry(entry)

        q = Quilto(
            llm_client=mock_llm,
            storage=storage,
            domains=[domain],
            session_db_path=":memory:",
        )

        # Mock process_correction
        import quilto.orchestration as orch_module

        success_result = CorrectionResult(
            success=True,
            target_entry_id="2026-01-27_10-30-00",
            correction_delta={"sets": 4},
            original_entry_id="2026-01-27_10-30-00",
        )

        async def mock_process_correction(**kwargs: Any) -> CorrectionResult:  # type: ignore[no-untyped-def]
            return success_result

        original_fn = orch_module.process_correction
        orch_module.process_correction = mock_process_correction  # type: ignore[assignment]

        try:
            state = {
                StateKeys.QUILTO: q,
                StateKeys.USER_INPUT: "I logged 5 sets but it should have been 4 sets of pull-ups",
                StateKeys.ROUTER_OUTPUT: RouterOutput(
                    input_type=InputType.CORRECTION,
                    confidence=0.96,
                    selected_domains=["strength"],
                    domain_selection_reasoning="Correcting pull-up sets",
                    correction_target="Number of pull-up sets (should be 4 sets instead of 5)",
                    reasoning="The statement explicitly revises previously logged data",
                ).model_dump(),
                StateKeys.DOMAIN_CONTEXT: {
                    "domains_loaded": ["strength"],
                    "vocabulary": {"bp": "bench press"},
                    "expertise": "Strength training",
                },
                StateKeys.TRACES: [],
            }

            result = await correction_node(state)  # type: ignore[arg-type]

            # Verify non-empty response (AC #3)
            assert StateKeys.RESPONSE in result
            assert result[StateKeys.RESPONSE] != ""
            assert result[StateKeys.RESPONSE] is not None

            # Verify correction_result present
            assert StateKeys.CORRECTION_RESULT in result
            correction_result = result[StateKeys.CORRECTION_RESULT]
            assert correction_result["success"] is True
            assert correction_result["target_entry_id"] == "2026-01-27_10-30-00"
            assert correction_result["correction_delta"] == {"sets": 4}

            # Verify response content matches AC #4
            response = result[StateKeys.RESPONSE]
            assert "2026-01-27_10-30-00" in response
        finally:
            orch_module.process_correction = original_fn  # type: ignore[assignment]
