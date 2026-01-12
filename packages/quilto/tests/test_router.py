"""Unit tests for RouterAgent.

Tests cover input classification (LOG/QUERY/BOTH/CORRECTION), domain selection,
RouterOutput validation, and input validation edge cases.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ValidationError
from quilto import load_llm_config
from quilto.agents import DomainInfo, InputType, RouterAgent, RouterInput, RouterOutput
from quilto.llm.client import LLMClient
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for RouterAgent tests.

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
            "router": AgentConfig(tier="low"),
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
        # Use model_validate_json to properly deserialize enums from JSON strings
        return response_model.model_validate_json(json.dumps(response_json))

    client.complete_structured = AsyncMock(side_effect=mock_complete_structured)  # type: ignore[method-assign]
    return client


def create_sample_domains() -> list[DomainInfo]:
    """Create sample domains for testing.

    Returns:
        List of test DomainInfo instances.
    """
    return [
        DomainInfo(
            name="strength",
            description="Strength training, weightlifting, resistance exercises",
        ),
        DomainInfo(
            name="running",
            description="Running, jogging, cardio activities",
        ),
        DomainInfo(
            name="nutrition",
            description="Food, diet, meal tracking, nutrition",
        ),
    ]


class TestInputTypeClassification:
    """Tests for LOG/QUERY/BOTH/CORRECTION classification."""

    @pytest.mark.asyncio
    async def test_log_classification_declarative(self) -> None:
        """Declarative statements are classified as LOG (AC: #1)."""
        response = {
            "input_type": "LOG",
            "confidence": 0.95,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Input mentions bench press",
            "reasoning": "Past tense declarative statement about exercise",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Bench pressed 185x5 today",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.LOG
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_query_classification_question_words(self) -> None:
        """Question words (why, how, what, when, which) classify as QUERY (AC: #2)."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.92,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Input asks about lifting progress",
            "reasoning": "Contains question word 'why'",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Why did my bench feel heavy today?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_query_classification_question_mark(self) -> None:
        """Question mark classifies as QUERY (AC: #2)."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.88,
            "selected_domains": ["running"],
            "domain_selection_reasoning": "Input about running progress",
            "reasoning": "Contains question mark",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="How's my running progress?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_both_classification_with_portions(self) -> None:
        """BOTH classification includes log_portion and query_portion (AC: #3)."""
        response = {
            "input_type": "BOTH",
            "confidence": 0.85,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Input about bench press",
            "log_portion": "Bench pressed 185x5 today, felt heavy.",
            "query_portion": "Why?",
            "reasoning": "Logs activity and asks question",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Bench pressed 185x5 today, felt heavy. Why?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.BOTH
        assert result.log_portion == "Bench pressed 185x5 today, felt heavy."
        assert result.query_portion == "Why?"

    @pytest.mark.asyncio
    async def test_correction_classification(self) -> None:
        """Correction language classifies as CORRECTION (AC: #4)."""
        response = {
            "input_type": "CORRECTION",
            "confidence": 0.91,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Correcting strength training entry",
            "correction_target": "The bench press weight from previous entry",
            "reasoning": "Contains correction language 'actually'",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Actually that was 185 not 85",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.CORRECTION
        assert result.correction_target is not None


class TestDomainSelection:
    """Tests for domain selection logic."""

    @pytest.mark.asyncio
    async def test_single_domain_match(self) -> None:
        """Single domain is selected when input matches one domain (AC: #5)."""
        response = {
            "input_type": "LOG",
            "confidence": 0.9,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Input is about weightlifting",
            "reasoning": "Declarative statement about exercise",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Did 5x5 squats at 225lbs",
                available_domains=create_sample_domains(),
            )
        )

        assert result.selected_domains == ["strength"]
        assert result.domain_selection_reasoning

    @pytest.mark.asyncio
    async def test_multiple_domain_match(self) -> None:
        """Multiple domains are selected when input matches several (AC: #5)."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.88,
            "selected_domains": ["running", "strength"],
            "domain_selection_reasoning": "Input compares running and lifting",
            "reasoning": "Question about multiple activities",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Compare my running progress with my lifting",
                available_domains=create_sample_domains(),
            )
        )

        assert "running" in result.selected_domains
        assert "strength" in result.selected_domains

    @pytest.mark.asyncio
    async def test_empty_available_domains_returns_empty_selection(self) -> None:
        """Empty available_domains results in empty selected_domains (AC: #5)."""
        response: dict[str, Any] = {
            "input_type": "LOG",
            "confidence": 0.9,
            "selected_domains": [],
            "domain_selection_reasoning": "No domains available to select",
            "reasoning": "Declarative statement",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Did some exercise today",
                available_domains=[],
            )
        )

        assert result.selected_domains == []

    @pytest.mark.asyncio
    async def test_domain_selection_reasoning_provided(self) -> None:
        """Domain selection includes reasoning explanation (AC: #5)."""
        response = {
            "input_type": "LOG",
            "confidence": 0.9,
            "selected_domains": ["nutrition"],
            "domain_selection_reasoning": "Input mentions eating and food",
            "reasoning": "Declarative statement about meal",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Had chicken and rice for lunch",
                available_domains=create_sample_domains(),
            )
        )

        assert result.domain_selection_reasoning == "Input mentions eating and food"

    @pytest.mark.asyncio
    async def test_no_domain_match_returns_empty(self) -> None:
        """No matching domain returns empty selection when domains exist (AC: #5)."""
        response: dict[str, Any] = {
            "input_type": "LOG",
            "confidence": 0.85,
            "selected_domains": [],
            "domain_selection_reasoning": "Input about cooking does not match available fitness domains",
            "reasoning": "Declarative statement",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        # Use fitness-related domains but input about cooking
        result = await router.classify(
            RouterInput(
                raw_input="Made pasta from scratch today",
                available_domains=create_sample_domains(),  # strength, running, nutrition
            )
        )

        # Nutrition could match but assuming LLM returns no match
        assert result.selected_domains == []
        assert result.domain_selection_reasoning

    @pytest.mark.asyncio
    async def test_uncertain_prefers_broader_selection(self) -> None:
        """When uncertain, broader domain selection is preferred (AC: #5)."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.75,
            "selected_domains": ["strength", "running", "nutrition"],
            "domain_selection_reasoning": "Input is ambiguous, selecting all available domains",
            "reasoning": "General fitness question",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="How can I improve my overall health?",
                available_domains=create_sample_domains(),
            )
        )

        # Should select multiple domains when uncertain
        assert len(result.selected_domains) >= 2
        assert "broader" in result.domain_selection_reasoning.lower() or len(result.selected_domains) > 1


class TestRouterOutput:
    """Tests for RouterOutput validation and constraints."""

    def test_confidence_below_zero_raises_validation_error(self) -> None:
        """Confidence < 0 raises ValidationError."""
        with pytest.raises(ValidationError):
            RouterOutput(
                input_type=InputType.LOG,
                confidence=-0.1,
                selected_domains=["test"],
                domain_selection_reasoning="test",
                reasoning="test",
            )

    def test_confidence_above_one_raises_validation_error(self) -> None:
        """Confidence > 1 raises ValidationError."""
        with pytest.raises(ValidationError):
            RouterOutput(
                input_type=InputType.LOG,
                confidence=1.1,
                selected_domains=["test"],
                domain_selection_reasoning="test",
                reasoning="test",
            )

    def test_valid_confidence_in_range(self) -> None:
        """Confidence in [0.0, 1.0] is valid."""
        output = RouterOutput(
            input_type=InputType.LOG,
            confidence=0.75,
            selected_domains=["test"],
            domain_selection_reasoning="test",
            reasoning="test",
        )
        assert output.confidence == 0.75

    def test_confidence_at_boundaries(self) -> None:
        """Confidence at 0.0 and 1.0 boundaries is valid."""
        output_zero = RouterOutput(
            input_type=InputType.LOG,
            confidence=0.0,
            selected_domains=[],
            domain_selection_reasoning="test",
            reasoning="test",
        )
        assert output_zero.confidence == 0.0

        output_one = RouterOutput(
            input_type=InputType.LOG,
            confidence=1.0,
            selected_domains=[],
            domain_selection_reasoning="test",
            reasoning="test",
        )
        assert output_one.confidence == 1.0

    def test_both_without_log_portion_raises_validation_error(self) -> None:
        """BOTH without log_portion raises ValidationError (AC: #8)."""
        with pytest.raises(ValidationError, match="log_portion and query_portion"):
            RouterOutput(
                input_type=InputType.BOTH,
                confidence=0.9,
                selected_domains=["test"],
                domain_selection_reasoning="test",
                query_portion="Why?",
                reasoning="test",
            )

    def test_both_without_query_portion_raises_validation_error(self) -> None:
        """BOTH without query_portion raises ValidationError (AC: #8)."""
        with pytest.raises(ValidationError, match="log_portion and query_portion"):
            RouterOutput(
                input_type=InputType.BOTH,
                confidence=0.9,
                selected_domains=["test"],
                domain_selection_reasoning="test",
                log_portion="Did something",
                reasoning="test",
            )

    def test_both_with_both_portions_succeeds(self) -> None:
        """BOTH with both portions is valid (AC: #8)."""
        output = RouterOutput(
            input_type=InputType.BOTH,
            confidence=0.9,
            selected_domains=["test"],
            domain_selection_reasoning="test",
            log_portion="Did something",
            query_portion="Why?",
            reasoning="test",
        )
        assert output.log_portion == "Did something"
        assert output.query_portion == "Why?"

    def test_correction_without_target_raises_validation_error(self) -> None:
        """CORRECTION without correction_target raises ValidationError (AC: #9)."""
        with pytest.raises(ValidationError, match="correction_target"):
            RouterOutput(
                input_type=InputType.CORRECTION,
                confidence=0.9,
                selected_domains=["test"],
                domain_selection_reasoning="test",
                reasoning="test",
            )

    def test_correction_with_target_succeeds(self) -> None:
        """CORRECTION with correction_target is valid (AC: #9)."""
        output = RouterOutput(
            input_type=InputType.CORRECTION,
            confidence=0.9,
            selected_domains=["test"],
            domain_selection_reasoning="test",
            correction_target="previous entry",
            reasoning="test",
        )
        assert output.correction_target == "previous entry"

    def test_both_with_empty_log_portion_raises_validation_error(self) -> None:
        """BOTH with empty string log_portion raises ValidationError (AC: #8)."""
        with pytest.raises(ValidationError, match="log_portion and query_portion"):
            RouterOutput(
                input_type=InputType.BOTH,
                confidence=0.9,
                selected_domains=["test"],
                domain_selection_reasoning="test",
                log_portion="",  # Empty string should fail
                query_portion="Why?",
                reasoning="test",
            )

    def test_both_with_empty_query_portion_raises_validation_error(self) -> None:
        """BOTH with empty string query_portion raises ValidationError (AC: #8)."""
        with pytest.raises(ValidationError, match="log_portion and query_portion"):
            RouterOutput(
                input_type=InputType.BOTH,
                confidence=0.9,
                selected_domains=["test"],
                domain_selection_reasoning="test",
                log_portion="Did something",
                query_portion="",  # Empty string should fail
                reasoning="test",
            )

    def test_correction_with_empty_target_raises_validation_error(self) -> None:
        """CORRECTION with empty string correction_target raises ValidationError (AC: #9)."""
        with pytest.raises(ValidationError, match="correction_target"):
            RouterOutput(
                input_type=InputType.CORRECTION,
                confidence=0.9,
                selected_domains=["test"],
                domain_selection_reasoning="test",
                correction_target="",  # Empty string should fail
                reasoning="test",
            )

    def test_log_without_portions_is_valid(self) -> None:
        """LOG input_type doesn't require portions."""
        output = RouterOutput(
            input_type=InputType.LOG,
            confidence=0.9,
            selected_domains=["test"],
            domain_selection_reasoning="test",
            reasoning="test",
        )
        assert output.log_portion is None
        assert output.query_portion is None

    def test_query_without_portions_is_valid(self) -> None:
        """QUERY input_type doesn't require portions."""
        output = RouterOutput(
            input_type=InputType.QUERY,
            confidence=0.9,
            selected_domains=["test"],
            domain_selection_reasoning="test",
            reasoning="test",
        )
        assert output.log_portion is None
        assert output.query_portion is None


class TestRouterInputValidation:
    """Tests for RouterInput validation."""

    @pytest.mark.asyncio
    async def test_empty_raw_input_raises_value_error(self) -> None:
        """Empty raw_input raises ValueError (AC: #7)."""
        response: dict[str, Any] = {
            "input_type": "LOG",
            "confidence": 0.9,
            "selected_domains": [],
            "domain_selection_reasoning": "test",
            "reasoning": "test",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        with pytest.raises(ValueError, match="empty or whitespace"):
            await router.classify(
                RouterInput(
                    raw_input="",
                    available_domains=[],
                )
            )

    @pytest.mark.asyncio
    async def test_whitespace_only_raw_input_raises_value_error(self) -> None:
        """Whitespace-only raw_input raises ValueError (AC: #7)."""
        response: dict[str, Any] = {
            "input_type": "LOG",
            "confidence": 0.9,
            "selected_domains": [],
            "domain_selection_reasoning": "test",
            "reasoning": "test",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        with pytest.raises(ValueError, match="empty or whitespace"):
            await router.classify(
                RouterInput(
                    raw_input="   \n\t  ",
                    available_domains=[],
                )
            )

    @pytest.mark.asyncio
    async def test_empty_raw_input_does_not_call_llm(self) -> None:
        """No LLM call is made for empty raw_input (AC: #7)."""
        response: dict[str, Any] = {
            "input_type": "LOG",
            "confidence": 0.9,
            "selected_domains": [],
            "domain_selection_reasoning": "test",
            "reasoning": "test",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        with pytest.raises(ValueError):
            await router.classify(
                RouterInput(
                    raw_input="",
                    available_domains=[],
                )
            )

        client.complete_structured.assert_not_called()  # type: ignore[union-attr]

    def test_empty_available_domains_is_valid(self) -> None:
        """Empty available_domains is a valid RouterInput."""
        router_input = RouterInput(
            raw_input="Some input",
            available_domains=[],
        )
        assert router_input.available_domains == []

    def test_session_context_is_optional(self) -> None:
        """session_context can be None."""
        router_input = RouterInput(
            raw_input="Some input",
            available_domains=[],
        )
        assert router_input.session_context is None


class TestRouterAgentPrompt:
    """Tests for RouterAgent prompt building."""

    def test_prompt_includes_domains(self) -> None:
        """Prompt includes available domain descriptions."""
        client = create_mock_llm_client({})
        router = RouterAgent(client)

        domains = [
            DomainInfo(name="strength", description="Strength training"),
            DomainInfo(name="running", description="Running activities"),
        ]
        router_input = RouterInput(raw_input="test", available_domains=domains)

        prompt = router.build_prompt(router_input)

        assert "strength: Strength training" in prompt
        assert "running: Running activities" in prompt

    def test_prompt_handles_empty_domains(self) -> None:
        """Prompt handles empty available_domains."""
        client = create_mock_llm_client({})
        router = RouterAgent(client)

        router_input = RouterInput(raw_input="test", available_domains=[])
        prompt = router.build_prompt(router_input)

        assert "(No domains available)" in prompt

    def test_prompt_includes_session_context(self) -> None:
        """Prompt includes session context when provided."""
        client = create_mock_llm_client({})
        router = RouterAgent(client)

        router_input = RouterInput(
            raw_input="test",
            available_domains=[],
            session_context="Previous message about running",
        )
        prompt = router.build_prompt(router_input)

        assert "Previous message about running" in prompt

    def test_prompt_handles_no_session_context(self) -> None:
        """Prompt handles None session_context."""
        client = create_mock_llm_client({})
        router = RouterAgent(client)

        router_input = RouterInput(raw_input="test", available_domains=[])
        prompt = router.build_prompt(router_input)

        assert "(No session context)" in prompt


class TestRouterAgentIntegration:
    """Integration tests with real LLM (skipped by default).

    Run with: pytest --use-real-ollama -k TestRouterAgentIntegration

    Uses llm-config.yaml from project root to match production config.
    """

    @pytest.mark.asyncio
    async def test_real_log_classification(self, use_real_ollama: bool, integration_llm_config_path: Path) -> None:
        """Test LOG classification with real LLM."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        router = RouterAgent(real_llm_client)

        result = await router.classify(
            RouterInput(
                raw_input="Bench pressed 185 pounds for 5 reps today",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.LOG
        assert result.confidence >= 0.7
        assert "strength" in result.selected_domains

    @pytest.mark.asyncio
    async def test_real_query_classification(self, use_real_ollama: bool, integration_llm_config_path: Path) -> None:
        """Test QUERY classification with real LLM."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        router = RouterAgent(real_llm_client)

        result = await router.classify(
            RouterInput(
                raw_input="How has my running pace improved this month?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7
        assert "running" in result.selected_domains


class TestQueryClassification:
    """Tests for QUERY input type classification and domain selection (AC: #1, #5)."""

    @pytest.mark.asyncio
    async def test_query_question_word_why(self) -> None:
        """QUERY with 'why' question word has confidence >= 0.7."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.85,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Question about strength training",
            "reasoning": "Contains question word 'why'",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Why did my bench press feel heavy today?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_query_question_word_how(self) -> None:
        """QUERY with 'how' question word has confidence >= 0.7."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.88,
            "selected_domains": ["running"],
            "domain_selection_reasoning": "Question about running performance",
            "reasoning": "Contains question word 'how'",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="How can I improve my 5k time?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_query_question_word_what(self) -> None:
        """QUERY with 'what' question word has confidence >= 0.7."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.9,
            "selected_domains": ["nutrition"],
            "domain_selection_reasoning": "Question about nutrition",
            "reasoning": "Contains question word 'what'",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="What should I eat before a workout?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_query_question_word_when(self) -> None:
        """QUERY with 'when' question word has confidence >= 0.7."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.82,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Question about timing of strength training",
            "reasoning": "Contains question word 'when'",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="When should I increase my deadlift weight?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_query_question_word_which(self) -> None:
        """QUERY with 'which' question word has confidence >= 0.7."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.86,
            "selected_domains": ["running"],
            "domain_selection_reasoning": "Question about running shoes",
            "reasoning": "Contains question word 'which'",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Which running shoes are best for marathons?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_query_question_mark_only(self) -> None:
        """QUERY with question mark (no question word) has confidence >= 0.7."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.78,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Question about bench press progress",
            "reasoning": "Contains question mark",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="My bench press improving?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_query_complex_multipart(self) -> None:
        """QUERY with complex multi-part question selects appropriate domains."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.84,
            "selected_domains": ["running", "nutrition"],
            "domain_selection_reasoning": "Question spans running performance and nutrition",
            "reasoning": "Multi-part question about performance and diet",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="What should I eat before running and how does it affect my pace?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7
        assert len(result.selected_domains) >= 1

    @pytest.mark.asyncio
    async def test_query_single_domain_selection(self) -> None:
        """QUERY about single topic selects one relevant domain."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.91,
            "selected_domains": ["nutrition"],
            "domain_selection_reasoning": "Question specifically about protein intake",
            "reasoning": "Question about diet",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="How much protein should I eat daily?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.selected_domains == ["nutrition"]

    @pytest.mark.asyncio
    async def test_query_no_domain_match(self) -> None:
        """QUERY about topic outside available domains returns empty selection (AC: #5)."""
        response: dict[str, Any] = {
            "input_type": "QUERY",
            "confidence": 0.85,
            "selected_domains": [],
            "domain_selection_reasoning": "Question about weather does not match fitness domains",
            "reasoning": "Question about weather",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="What will the weather be like tomorrow?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.selected_domains == []
        assert result.domain_selection_reasoning is not None

    @pytest.mark.asyncio
    async def test_query_confidence_threshold(self) -> None:
        """QUERY classification has confidence >= 0.7 for clear queries (AC: #1)."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.75,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Question about lifting",
            "reasoning": "Contains question word",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="How heavy should I lift?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_query_confidence_at_exact_boundary_0_7(self) -> None:
        """QUERY classification at exactly 0.7 confidence boundary (boundary test)."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.7,
            "selected_domains": ["running"],
            "domain_selection_reasoning": "Question about running",
            "reasoning": "Question at confidence boundary",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Is running good for me?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence == 0.7


class TestBothClassification:
    """Tests for BOTH input type with log and query portions (AC: #3)."""

    @pytest.mark.asyncio
    async def test_both_log_then_question(self) -> None:
        """BOTH with log statement followed by question extracts both portions."""
        response = {
            "input_type": "BOTH",
            "confidence": 0.88,
            "selected_domains": ["running"],
            "domain_selection_reasoning": "Input logs running activity and asks about progress",
            "log_portion": "Ran 5k today in 25 minutes.",
            "query_portion": "Is that good progress?",
            "reasoning": "Declarative statement followed by question",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Ran 5k today in 25 minutes. Is that good progress?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.BOTH
        assert result.log_portion == "Ran 5k today in 25 minutes."
        assert result.query_portion == "Is that good progress?"

    @pytest.mark.asyncio
    async def test_both_question_then_log(self) -> None:
        """BOTH with question followed by log statement extracts both portions."""
        response = {
            "input_type": "BOTH",
            "confidence": 0.85,
            "selected_domains": ["strength"],
            "domain_selection_reasoning": "Input asks about weight and logs bench press",
            "log_portion": "Bench pressed 200lbs for 3 reps.",
            "query_portion": "Should I increase the weight?",
            "reasoning": "Question followed by declarative statement",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Should I increase the weight? Bench pressed 200lbs for 3 reps.",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.BOTH
        assert result.log_portion is not None
        assert result.query_portion is not None

    @pytest.mark.asyncio
    async def test_both_interleaved(self) -> None:
        """BOTH with interleaved log and question content extracts both portions."""
        response = {
            "input_type": "BOTH",
            "confidence": 0.82,
            "selected_domains": ["nutrition"],
            "domain_selection_reasoning": "Input logs breakfast and asks about nutrition",
            "log_portion": "Had eggs and toast for breakfast, about 400 calories.",
            "query_portion": "Is that enough protein?",
            "reasoning": "Interleaved log and question",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Had eggs and toast for breakfast, about 400 calories. Is that enough protein?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.BOTH
        assert result.log_portion is not None
        assert result.query_portion is not None

    @pytest.mark.asyncio
    async def test_both_portion_preservation(self) -> None:
        """BOTH portion extraction preserves exact wording (AC: #3)."""
        response = {
            "input_type": "BOTH",
            "confidence": 0.9,
            "selected_domains": ["running"],
            "domain_selection_reasoning": "Running log with question about form",
            "log_portion": "Completed marathon in 4:15:32, personal best!",
            "query_portion": "How can I improve my form for next time?",
            "reasoning": "Log with follow-up question",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Completed marathon in 4:15:32, personal best! How can I improve my form for next time?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.BOTH
        assert result.log_portion == "Completed marathon in 4:15:32, personal best!"
        assert result.query_portion == "How can I improve my form for next time?"

    @pytest.mark.asyncio
    async def test_both_multi_domain_selection(self) -> None:
        """BOTH selects domains relevant to both portions (AC: #3)."""
        response = {
            "input_type": "BOTH",
            "confidence": 0.87,
            "selected_domains": ["strength", "nutrition"],
            "domain_selection_reasoning": "Log about lifting, question about nutrition",
            "log_portion": "Squatted 315lbs for 5 reps today.",
            "query_portion": "What should I eat to recover?",
            "reasoning": "Strength log with nutrition question",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Squatted 315lbs for 5 reps today. What should I eat to recover?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.BOTH
        assert "strength" in result.selected_domains
        assert "nutrition" in result.selected_domains

    @pytest.mark.asyncio
    async def test_both_confidence_score(self) -> None:
        """BOTH classification has appropriate confidence score."""
        response = {
            "input_type": "BOTH",
            "confidence": 0.83,
            "selected_domains": ["running"],
            "domain_selection_reasoning": "Running activity log and question",
            "log_portion": "Ran 10k this morning.",
            "query_portion": "Should I rest tomorrow?",
            "reasoning": "Log with question",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Ran 10k this morning. Should I rest tomorrow?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.BOTH
        assert 0.0 <= result.confidence <= 1.0


class TestMultiDomainSelection:
    """Tests for selecting multiple domains for complex queries (AC: #2, #4)."""

    @pytest.mark.asyncio
    async def test_two_domain_cross_query(self) -> None:
        """Cross-domain query selects 2 relevant domains."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.88,
            "selected_domains": ["running", "strength"],
            "domain_selection_reasoning": (
                "Query compares running with strength training. "
                "Running is selected for cardio aspect, strength for lifting."
            ),
            "reasoning": "Comparative question about two activities",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Compare my running progress with my lifting progress",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert len(result.selected_domains) == 2
        assert "running" in result.selected_domains
        assert "strength" in result.selected_domains

    @pytest.mark.asyncio
    async def test_three_domain_broad_query(self) -> None:
        """Broad/ambiguous query selects 3+ domains."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.75,
            "selected_domains": ["strength", "running", "nutrition"],
            "domain_selection_reasoning": (
                "Broad health question spans all domains. "
                "Strength for exercise, running for cardio, nutrition for diet."
            ),
            "reasoning": "General health question covering all domains",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="How can I improve my overall health and fitness?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert len(result.selected_domains) >= 3

    @pytest.mark.asyncio
    async def test_reasoning_mentions_each_domain(self) -> None:
        """Domain selection reasoning mentions each selected domain (AC: #4)."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.85,
            "selected_domains": ["nutrition", "strength"],
            "domain_selection_reasoning": (
                "Nutrition is relevant for diet aspect. Strength is relevant for muscle building."
            ),
            "reasoning": "Question about diet and muscle",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="How does my diet affect my muscle building?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert "nutrition" in result.selected_domains
        assert "strength" in result.selected_domains
        # Verify reasoning mentions both domains
        reasoning_lower = result.domain_selection_reasoning.lower()
        assert "nutrition" in reasoning_lower
        assert "strength" in reasoning_lower

    @pytest.mark.asyncio
    async def test_broader_selection_lower_confidence(self) -> None:
        """Lower confidence queries trigger broader domain selection."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.72,
            "selected_domains": ["strength", "running", "nutrition"],
            "domain_selection_reasoning": (
                "Ambiguous query could relate to multiple domains. Including all for comprehensive coverage."
            ),
            "reasoning": "Ambiguous fitness question",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="How am I doing overall?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        # Lower confidence should lead to broader selection
        assert len(result.selected_domains) >= 2

    @pytest.mark.asyncio
    async def test_uncertain_query_triggers_broader_selection(self) -> None:
        """Uncertain query prefers broader selection over missing domains (AC: #2)."""
        response = {
            "input_type": "QUERY",
            "confidence": 0.73,
            "selected_domains": ["running", "strength"],
            "domain_selection_reasoning": (
                "Query about performance could relate to running or strength. "
                "Selecting both to avoid missing relevant domain."
            ),
            "reasoning": "Uncertain which domain applies",
        }
        client = create_mock_llm_client(response)
        router = RouterAgent(client)

        result = await router.classify(
            RouterInput(
                raw_input="Why is my performance declining?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        # Should select multiple domains when uncertain
        assert len(result.selected_domains) >= 2


class TestRouterQueryIntegration:
    """Integration tests for QUERY/BOTH with real Ollama (AC: #7).

    Run with: pytest --use-real-ollama -k TestRouterQueryIntegration
    Or via: make test-ollama

    Uses llm-config.yaml from project root to match production config.
    """

    @pytest.mark.asyncio
    async def test_real_query_single_domain(self, use_real_ollama: bool, integration_llm_config_path: Path) -> None:
        """Test QUERY classification with single domain using real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        router = RouterAgent(real_llm_client)

        result = await router.classify(
            RouterInput(
                raw_input="How has my bench press progressed this month?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        assert result.confidence >= 0.7
        assert "strength" in result.selected_domains

    @pytest.mark.asyncio
    async def test_real_query_multi_domain(self, use_real_ollama: bool, integration_llm_config_path: Path) -> None:
        """Test QUERY classification with multiple domains using real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        router = RouterAgent(real_llm_client)

        result = await router.classify(
            RouterInput(
                raw_input="How does my running compare to my strength training progress?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        # Should select both running and strength domains for explicit comparison query
        assert len(result.selected_domains) >= 2
        # Both domains should be selected for "running compare to strength training"
        assert "running" in result.selected_domains, "Expected 'running' domain for comparison query"
        assert "strength" in result.selected_domains, "Expected 'strength' domain for comparison query"

    @pytest.mark.asyncio
    async def test_real_both_classification(self, use_real_ollama: bool, integration_llm_config_path: Path) -> None:
        """Test BOTH classification with portion extraction using real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        router = RouterAgent(real_llm_client)

        result = await router.classify(
            RouterInput(
                raw_input="Ran 5k today in 25 mins. Is that good progress?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.BOTH
        assert result.log_portion is not None
        assert result.query_portion is not None
        assert "running" in result.selected_domains

    @pytest.mark.asyncio
    async def test_real_multi_domain_query_selection(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test multi-domain query selection using real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        router = RouterAgent(real_llm_client)

        result = await router.classify(
            RouterInput(
                raw_input="How does my diet affect my strength training results?",
                available_domains=create_sample_domains(),
            )
        )

        assert result.input_type == InputType.QUERY
        # Should select both nutrition and strength domains for explicit diet+training query
        assert len(result.selected_domains) >= 2
        # Both domains should be selected for "diet affect strength training"
        assert "nutrition" in result.selected_domains, "Expected 'nutrition' domain for diet query"
        assert "strength" in result.selected_domains, "Expected 'strength' domain for training query"
