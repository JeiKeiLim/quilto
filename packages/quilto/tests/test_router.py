"""Unit tests for RouterAgent.

Tests cover input classification (LOG/QUERY/BOTH/CORRECTION), domain selection,
RouterOutput validation, and input validation edge cases.
"""

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ValidationError
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
    """

    @pytest.fixture
    def real_llm_client(self) -> LLMClient:
        """Create a real LLMClient for integration tests."""
        config = create_test_config()
        return LLMClient(config)

    @pytest.mark.asyncio
    async def test_real_log_classification(
        self,
        real_llm_client: LLMClient,
        use_real_ollama: bool,
    ) -> None:
        """Test LOG classification with real LLM."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag and running Ollama instance")

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
    async def test_real_query_classification(
        self,
        real_llm_client: LLMClient,
        use_real_ollama: bool,
    ) -> None:
        """Test QUERY classification with real LLM."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag and running Ollama instance")

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
