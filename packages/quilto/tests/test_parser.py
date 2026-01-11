"""Unit tests for ParserAgent.

Tests cover structured data extraction, vocabulary normalization,
uncertainty handling, correction mode, and validation.
"""

import json
from datetime import date, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ValidationError
from quilto.agents.models import ParserInput, ParserOutput
from quilto.llm.client import LLMClient
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for ParserAgent tests.

    Returns:
        Configured LLMConfig for testing.
    """
    return LLMConfig(
        default_provider="ollama",  # type: ignore[arg-type]
        providers={
            "ollama": ProviderConfig(api_base="http://localhost:11434"),
        },
        tiers={
            "low": TierModels(ollama="qwen2.5:7b"),
            "medium": TierModels(ollama="qwen2.5:14b"),
        },
        agents={
            "parser": AgentConfig(tier="medium"),
        },
    )


def create_mock_llm_client(response_json: dict[str, Any]) -> LLMClient:
    """Create a mock LLMClient that returns the given JSON response.

    Args:
        response_json: The JSON response to return from complete_structured.

    Returns:
        Mocked LLMClient instance.
    """
    config = create_test_config()
    client = LLMClient(config)

    async def mock_complete_structured(
        agent: str,
        messages: list[dict[str, Any]],
        response_model: type[BaseModel],
        **kwargs: Any,
    ) -> BaseModel:
        return response_model.model_validate_json(json.dumps(response_json))

    client.complete_structured = AsyncMock(side_effect=mock_complete_structured)  # type: ignore[method-assign]
    return client


class StrengthSchema(BaseModel):
    """Schema for strength training domain (test data)."""

    exercise: str
    weight_kg: float | None = None
    reps: int | None = None
    sets: int | None = None


class NutritionSchema(BaseModel):
    """Schema for nutrition domain (test data)."""

    meal_type: str | None = None
    items: list[str] = []


class TestParserOutputValidation:
    """Tests for ParserOutput validation."""

    def test_confidence_below_zero_raises_validation_error(self) -> None:
        """Confidence < 0 raises ValidationError."""
        with pytest.raises(ValidationError):
            ParserOutput(
                date=date(2026, 1, 11),
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_data={},
                raw_content="test input",
                confidence=-0.1,
            )

    def test_confidence_above_one_raises_validation_error(self) -> None:
        """Confidence > 1 raises ValidationError."""
        with pytest.raises(ValidationError):
            ParserOutput(
                date=date(2026, 1, 11),
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_data={},
                raw_content="test input",
                confidence=1.1,
            )

    def test_confidence_boundary_zero_succeeds(self) -> None:
        """Confidence at 0.0 is valid."""
        output = ParserOutput(
            date=date(2026, 1, 11),
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_data={},
            raw_content="test input",
            confidence=0.0,
        )
        assert output.confidence == 0.0

    def test_confidence_boundary_one_succeeds(self) -> None:
        """Confidence at 1.0 is valid."""
        output = ParserOutput(
            date=date(2026, 1, 11),
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_data={},
            raw_content="test input",
            confidence=1.0,
        )
        assert output.confidence == 1.0

    def test_empty_raw_content_raises_validation_error(self) -> None:
        """Empty raw_content raises ValidationError (AC: #9)."""
        with pytest.raises(ValidationError, match="raw_content cannot be empty"):
            ParserOutput(
                date=date(2026, 1, 11),
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_data={},
                raw_content="",
                confidence=0.9,
            )

    def test_whitespace_only_raw_content_raises_validation_error(self) -> None:
        """Whitespace-only raw_content raises ValidationError (AC: #9)."""
        with pytest.raises(ValidationError, match="raw_content cannot be empty"):
            ParserOutput(
                date=date(2026, 1, 11),
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_data={},
                raw_content="   \n\t  ",
                confidence=0.9,
            )

    def test_domain_data_is_dict(self) -> None:
        """domain_data must be a dict (AC: #9)."""
        output = ParserOutput(
            date=date(2026, 1, 11),
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_data={"strength": {"exercise": "bench press"}},
            raw_content="test input",
            confidence=0.9,
        )
        assert isinstance(output.domain_data, dict)

    def test_domain_data_can_be_empty_dict(self) -> None:
        """domain_data can be empty dict (AC: #9)."""
        output = ParserOutput(
            date=date(2026, 1, 11),
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_data={},
            raw_content="test input",
            confidence=0.9,
        )
        assert output.domain_data == {}

    def test_domain_data_non_dict_raises_validation_error(self) -> None:
        """Non-dict domain_data raises ValidationError (AC: #9)."""
        with pytest.raises(ValidationError):
            ParserOutput(
                date=date(2026, 1, 11),
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_data=["not", "a", "dict"],  # type: ignore[arg-type]
                raw_content="test input",
                confidence=0.9,
            )

    def test_domain_data_string_raises_validation_error(self) -> None:
        """String domain_data raises ValidationError (AC: #9)."""
        with pytest.raises(ValidationError):
            ParserOutput(
                date=date(2026, 1, 11),
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_data="not a dict",  # type: ignore[arg-type]
                raw_content="test input",
                confidence=0.9,
            )


class TestParserInputValidation:
    """Tests for ParserInput validation."""

    def test_parser_input_requires_raw_input(self) -> None:
        """ParserInput requires raw_input field."""
        from quilto.agents.models import ParserInput

        with pytest.raises(ValidationError):
            ParserInput(
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={},
                vocabulary={},
            )  # type: ignore[call-arg]

    def test_parser_input_requires_timestamp(self) -> None:
        """ParserInput requires timestamp field."""
        from quilto.agents.models import ParserInput

        with pytest.raises(ValidationError):
            ParserInput(
                raw_input="test",
                domain_schemas={},
                vocabulary={},
            )  # type: ignore[call-arg]

    def test_parser_input_allows_empty_vocabulary(self) -> None:
        """ParserInput allows empty vocabulary."""
        from quilto.agents.models import ParserInput

        parser_input = ParserInput(
            raw_input="test",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={},
            vocabulary={},
        )
        assert parser_input.vocabulary == {}

    def test_parser_input_allows_empty_domain_schemas(self) -> None:
        """ParserInput allows empty domain_schemas."""
        from quilto.agents.models import ParserInput

        parser_input = ParserInput(
            raw_input="test",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={},
            vocabulary={},
        )
        assert parser_input.domain_schemas == {}

    def test_parser_input_correction_mode_defaults_false(self) -> None:
        """ParserInput correction_mode defaults to False."""
        from quilto.agents.models import ParserInput

        parser_input = ParserInput(
            raw_input="test",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={},
            vocabulary={},
        )
        assert parser_input.correction_mode is False

    def test_parser_input_accepts_domain_schemas_with_pydantic_models(self) -> None:
        """ParserInput accepts Pydantic model classes in domain_schemas."""
        from quilto.agents.models import ParserInput

        class TestSchema(BaseModel):
            field: str

        parser_input = ParserInput(
            raw_input="test",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={"test": TestSchema},
            vocabulary={},
        )
        assert "test" in parser_input.domain_schemas
        assert parser_input.domain_schemas["test"] is TestSchema


class TestParserBasicExtraction:
    """Tests for basic structured data extraction."""

    @pytest.mark.asyncio
    async def test_single_domain_extraction(self) -> None:
        """Parser extracts data for single domain schema (AC: #1)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": ["strength"],
            "domain_data": {
                "strength": {
                    "exercise": "bench press",
                    "weight_kg": 84.0,
                    "reps": 5,
                    "sets": 3,
                }
            },
            "raw_content": "Bench pressed 185x5 for 3 sets",
            "confidence": 0.95,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Bench pressed 185x5 for 3 sets",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={"strength": StrengthSchema},
                vocabulary={"bp": "bench press"},
            )
        )

        assert "strength" in result.domain_data
        assert result.domain_data["strength"]["exercise"] == "bench press"
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_multi_domain_extraction(self) -> None:
        """Parser extracts data for multiple domains independently (AC: #5)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": ["breakfast", "exercise"],
            "domain_data": {
                "nutrition": {"meal_type": "breakfast", "items": ["coffee", "toast"]},
                "strength": {"exercise": "run", "weight_kg": None, "reps": None},
            },
            "raw_content": "Had coffee and toast, then went for a run",
            "confidence": 0.88,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Had coffee and toast, then went for a run",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={
                    "nutrition": NutritionSchema,
                    "strength": StrengthSchema,
                },
                vocabulary={},
            )
        )

        assert "nutrition" in result.domain_data
        assert "strength" in result.domain_data

    @pytest.mark.asyncio
    async def test_raw_content_preserved(self) -> None:
        """Parser preserves raw content exactly (AC: #1)."""
        from quilto.agents import ParserAgent

        raw_input = "Bench pressed 185x5 for 3 sets"
        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {"strength": {"exercise": "bench press"}},
            "raw_content": raw_input,
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input=raw_input,
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={"strength": StrengthSchema},
                vocabulary={},
            )
        )

        assert result.raw_content == raw_input

    @pytest.mark.asyncio
    async def test_date_extracted_from_timestamp(self) -> None:
        """Parser extracts date from provided timestamp (AC: #2)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "Did some exercise",
            "confidence": 0.85,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Did some exercise",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={},
                vocabulary={},
            )
        )

        assert result.date == date(2026, 1, 11)
        assert result.timestamp == datetime(2026, 1, 11, 10, 30, 0)

    @pytest.mark.asyncio
    async def test_tags_extracted(self) -> None:
        """Parser extracts tags from content (AC: #2)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": ["strength", "upper body"],
            "domain_data": {"strength": {"exercise": "bench press"}},
            "raw_content": "Bench pressed 185x5",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Bench pressed 185x5",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={"strength": StrengthSchema},
                vocabulary={},
            )
        )

        assert "strength" in result.tags
        assert "upper body" in result.tags


class TestVocabularyNormalization:
    """Tests for vocabulary term normalization."""

    @pytest.mark.asyncio
    async def test_vocabulary_passed_to_prompt(self) -> None:
        """Vocabulary is included in LLM prompt (AC: #3)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {"strength": {"exercise": "bench press"}},
            "raw_content": "Did bp 185x5",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        vocabulary = {"bp": "bench press", "sq": "squat"}
        parser_input = ParserInput(
            raw_input="Did bp 185x5",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={"strength": StrengthSchema},
            vocabulary=vocabulary,
        )

        # Build prompt and check vocabulary is included
        prompt = parser.build_prompt(parser_input)
        assert "bp" in prompt
        assert "bench press" in prompt

    @pytest.mark.asyncio
    async def test_vocabulary_empty_still_works(self) -> None:
        """Empty vocabulary does not cause errors (AC: #3)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "Did some exercise",
            "confidence": 0.8,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Did some exercise",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={},
                vocabulary={},
            )
        )

        assert result is not None


class TestUncertaintyHandling:
    """Tests for uncertain field and confidence handling."""

    @pytest.mark.asyncio
    async def test_uncertain_fields_populated(self) -> None:
        """Uncertain fields are listed when extraction is uncertain (AC: #4)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {"strength": {"exercise": "bench press"}},
            "raw_content": "Did bench, not sure how many reps",
            "confidence": 0.6,
            "extraction_notes": ["Could not determine rep count"],
            "uncertain_fields": ["reps", "sets"],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Did bench, not sure how many reps",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={"strength": StrengthSchema},
                vocabulary={},
            )
        )

        assert "reps" in result.uncertain_fields
        assert "sets" in result.uncertain_fields

    @pytest.mark.asyncio
    async def test_extraction_notes_for_ambiguity(self) -> None:
        """Extraction notes explain ambiguities (AC: #4)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "Did some exercise",
            "confidence": 0.5,
            "extraction_notes": ["Input is too vague to extract specific data"],
            "uncertain_fields": ["exercise", "weight_kg"],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Did some exercise",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={"strength": StrengthSchema},
                vocabulary={},
            )
        )

        assert len(result.extraction_notes) > 0
        assert "vague" in result.extraction_notes[0].lower()

    @pytest.mark.asyncio
    async def test_confidence_reflects_clarity(self) -> None:
        """Confidence score reflects extraction quality (AC: #4)."""
        from quilto.agents import ParserAgent

        # Clear input should have high confidence
        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {"strength": {"exercise": "bench press", "weight_kg": 84.0, "reps": 5}},
            "raw_content": "Bench pressed 185lbs for 5 reps",
            "confidence": 0.95,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Bench pressed 185lbs for 5 reps",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={"strength": StrengthSchema},
                vocabulary={},
            )
        )

        assert result.confidence >= 0.8  # Clear input = high confidence

    @pytest.mark.asyncio
    async def test_confidence_in_valid_range(self) -> None:
        """Confidence is always in [0.0, 1.0] range (AC: #4)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "test",
            "confidence": 0.75,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="test",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={},
                vocabulary={},
            )
        )

        assert 0.0 <= result.confidence <= 1.0


class TestCorrectionMode:
    """Tests for correction mode parsing."""

    @pytest.mark.asyncio
    async def test_correction_mode_identifies_target(self) -> None:
        """Correction mode identifies target entry (AC: #8)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {"strength": {"exercise": "bench press", "weight_kg": 84.0}},
            "raw_content": "Actually that was 185 not 85",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
            "is_correction": True,
            "target_entry_id": "2026-01-11_08-30-00",
            "correction_delta": {"weight_kg": 84.0},
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Actually that was 185 not 85",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={"strength": StrengthSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="bench weight recorded as 85",
            )
        )

        assert result.is_correction is True
        assert result.target_entry_id == "2026-01-11_08-30-00"

    @pytest.mark.asyncio
    async def test_correction_delta_extracted(self) -> None:
        """Correction delta contains only changed fields (AC: #8)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {"strength": {"exercise": "bench press", "weight_kg": 84.0}},
            "raw_content": "Actually that was 185 not 85",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
            "is_correction": True,
            "target_entry_id": "2026-01-11_08-30-00",
            "correction_delta": {"weight_kg": 84.0},
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Actually that was 185 not 85",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={"strength": StrengthSchema},
                vocabulary={},
                correction_mode=True,
                correction_target="bench weight recorded as 85",
            )
        )

        assert result.correction_delta is not None
        assert "weight_kg" in result.correction_delta

    @pytest.mark.asyncio
    async def test_is_correction_flag_set(self) -> None:
        """is_correction flag is set when correction_mode is True (AC: #8)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "Actually that was 185",
            "confidence": 0.85,
            "extraction_notes": [],
            "uncertain_fields": [],
            "is_correction": True,
            "target_entry_id": None,
            "correction_delta": None,
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        result = await parser.parse(
            ParserInput(
                raw_input="Actually that was 185",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={},
                vocabulary={},
                correction_mode=True,
                correction_target="previous entry",
            )
        )

        assert result.is_correction is True


class TestParserAgentInputValidation:
    """Tests for ParserAgent.parse() input validation."""

    @pytest.mark.asyncio
    async def test_empty_raw_input_raises_value_error(self) -> None:
        """Empty raw_input raises ValueError (AC: #7)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "test",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        with pytest.raises(ValueError, match="empty or whitespace"):
            await parser.parse(
                ParserInput(
                    raw_input="",
                    timestamp=datetime(2026, 1, 11, 10, 30, 0),
                    domain_schemas={},
                    vocabulary={},
                )
            )

    @pytest.mark.asyncio
    async def test_whitespace_only_raw_input_raises_value_error(self) -> None:
        """Whitespace-only raw_input raises ValueError (AC: #7)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "test",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        with pytest.raises(ValueError, match="empty or whitespace"):
            await parser.parse(
                ParserInput(
                    raw_input="   \n\t  ",
                    timestamp=datetime(2026, 1, 11, 10, 30, 0),
                    domain_schemas={},
                    vocabulary={},
                )
            )

    @pytest.mark.asyncio
    async def test_empty_raw_input_does_not_call_llm(self) -> None:
        """No LLM call is made for empty raw_input (AC: #7)."""
        from quilto.agents import ParserAgent

        response: dict[str, Any] = {
            "date": "2026-01-11",
            "timestamp": "2026-01-11T10:30:00",
            "tags": [],
            "domain_data": {},
            "raw_content": "test",
            "confidence": 0.9,
            "extraction_notes": [],
            "uncertain_fields": [],
        }
        client = create_mock_llm_client(response)
        parser = ParserAgent(client)

        with pytest.raises(ValueError):
            await parser.parse(
                ParserInput(
                    raw_input="",
                    timestamp=datetime(2026, 1, 11, 10, 30, 0),
                    domain_schemas={},
                    vocabulary={},
                )
            )

        client.complete_structured.assert_not_called()  # type: ignore[union-attr]


class TestParserAgentPrompt:
    """Tests for ParserAgent prompt building."""

    def test_prompt_includes_domain_schemas(self) -> None:
        """Prompt includes domain schema descriptions."""
        from quilto.agents import ParserAgent

        client = create_mock_llm_client({})
        parser = ParserAgent(client)

        parser_input = ParserInput(
            raw_input="test",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={"strength": StrengthSchema},
            vocabulary={},
        )

        prompt = parser.build_prompt(parser_input)

        assert "strength" in prompt.lower()
        assert "exercise" in prompt.lower()

    def test_prompt_includes_vocabulary(self) -> None:
        """Prompt includes vocabulary mapping."""
        from quilto.agents import ParserAgent

        client = create_mock_llm_client({})
        parser = ParserAgent(client)

        parser_input = ParserInput(
            raw_input="test",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={},
            vocabulary={"bp": "bench press", "sq": "squat"},
        )

        prompt = parser.build_prompt(parser_input)

        assert "bp" in prompt
        assert "bench press" in prompt

    def test_prompt_handles_empty_vocabulary(self) -> None:
        """Prompt handles empty vocabulary gracefully."""
        from quilto.agents import ParserAgent

        client = create_mock_llm_client({})
        parser = ParserAgent(client)

        parser_input = ParserInput(
            raw_input="test",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={},
            vocabulary={},
        )

        prompt = parser.build_prompt(parser_input)

        assert prompt is not None  # Should not crash

    def test_prompt_includes_correction_mode_info(self) -> None:
        """Prompt includes correction mode when enabled."""
        from quilto.agents import ParserAgent

        client = create_mock_llm_client({})
        parser = ParserAgent(client)

        parser_input = ParserInput(
            raw_input="Actually that was 185",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={},
            vocabulary={},
            correction_mode=True,
            correction_target="bench weight recorded as 85",
        )

        prompt = parser.build_prompt(parser_input)

        assert "correction" in prompt.lower()
        assert "bench weight recorded as 85" in prompt

    def test_prompt_includes_global_context(self) -> None:
        """Prompt includes global context when provided."""
        from quilto.agents import ParserAgent

        client = create_mock_llm_client({})
        parser = ParserAgent(client)

        parser_input = ParserInput(
            raw_input="test",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={},
            vocabulary={},
            global_context="User prefers metric units",
        )

        prompt = parser.build_prompt(parser_input)

        assert "User prefers metric units" in prompt

    def test_prompt_includes_recent_entries(self) -> None:
        """Prompt includes recent entries when provided."""
        from quilto.agents import ParserAgent

        client = create_mock_llm_client({})
        parser = ParserAgent(client)

        # Create mock entry objects with expected attributes
        class MockEntry:
            def __init__(self, entry_id: str, entry_date: str, raw_content: str) -> None:
                self.id = entry_id
                self.date = entry_date
                self.raw_content = raw_content

        mock_entries = [
            MockEntry("2026-01-11_08-30-00", "2026-01-11", "Bench pressed 85x5"),
            MockEntry("2026-01-11_09-00-00", "2026-01-11", "Had breakfast"),
        ]

        parser_input = ParserInput(
            raw_input="test",
            timestamp=datetime(2026, 1, 11, 10, 30, 0),
            domain_schemas={},
            vocabulary={},
            recent_entries=mock_entries,
        )

        prompt = parser.build_prompt(parser_input)

        assert "2026-01-11_08-30-00" in prompt
        assert "Bench pressed 85x5" in prompt
        assert "2026-01-11_09-00-00" in prompt


class TestFormatRecentEntries:
    """Tests for format_recent_entries helper method."""

    def testformat_recent_entries_empty_list(self) -> None:
        """Empty entries list returns placeholder text."""
        from quilto.agents import ParserAgent

        client = create_mock_llm_client({})
        parser = ParserAgent(client)

        result = parser.format_recent_entries([])
        assert result == "(No recent entries)"

    def testformat_recent_entries_truncates_long_content(self) -> None:
        """Long raw_content is truncated to 50 chars."""
        from quilto.agents import ParserAgent

        client = create_mock_llm_client({})
        parser = ParserAgent(client)

        class MockEntry:
            def __init__(self) -> None:
                self.id = "test-id"
                self.date = "2026-01-11"
                self.raw_content = "A" * 100  # 100 chars

        result = parser.format_recent_entries([MockEntry()])

        assert "A" * 50 + "..." in result
        assert "A" * 51 not in result

    def testformat_recent_entries_handles_missing_attributes(self) -> None:
        """Entries with missing attributes use 'unknown' fallback."""
        from quilto.agents import ParserAgent

        client = create_mock_llm_client({})
        parser = ParserAgent(client)

        class PartialEntry:
            pass  # No attributes

        result = parser.format_recent_entries([PartialEntry()])

        assert "unknown" in result


class TestParserIntegration:
    """Integration tests with real LLM (skipped by default).

    Run with: pytest --use-real-ollama -k TestParserIntegration
    """

    @pytest.mark.asyncio
    async def test_real_fitness_extraction(self, use_real_ollama: bool) -> None:
        """Test fitness extraction with real LLM."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        from quilto.agents import ParserAgent

        config = create_test_config()
        real_llm_client = LLMClient(config)
        parser = ParserAgent(real_llm_client)

        result = await parser.parse(
            ParserInput(
                raw_input="Bench pressed 185 pounds for 5 reps, 3 sets today",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={"strength": StrengthSchema},
                vocabulary={"bp": "bench press"},
            )
        )

        assert result.confidence >= 0.5
        assert "strength" in result.domain_data
        assert result.raw_content == "Bench pressed 185 pounds for 5 reps, 3 sets today"

    @pytest.mark.asyncio
    async def test_real_multi_domain_extraction(self, use_real_ollama: bool) -> None:
        """Test multi-domain extraction with real LLM."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        from quilto.agents import ParserAgent

        config = create_test_config()
        real_llm_client = LLMClient(config)
        parser = ParserAgent(real_llm_client)

        result = await parser.parse(
            ParserInput(
                raw_input="Had eggs and coffee for breakfast, then did a 5k run",
                timestamp=datetime(2026, 1, 11, 10, 30, 0),
                domain_schemas={
                    "nutrition": NutritionSchema,
                    "strength": StrengthSchema,
                },
                vocabulary={},
            )
        )

        assert result.confidence >= 0.5
        assert result.raw_content == "Had eggs and coffee for breakfast, then did a 5k run"
