"""Unit tests for clarification_patterns feature.

Tests cover DomainModule field, ClarifierInput model, ClarifierAgent prompt building,
and backward compatibility.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ConfigDict
from quilto import DomainModule, load_llm_config
from quilto.agents import (
    ClarifierAgent,
    ClarifierInput,
    Gap,
    GapType,
)
from quilto.llm.client import LLMClient
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels

# =============================================================================
# Test Fixtures
# =============================================================================


class DummyLogSchema(BaseModel):
    """Minimal log schema for DomainModule tests."""

    model_config = ConfigDict(strict=True)
    note: str = ""


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for Clarifier tests.

    Returns:
        Configured LLMConfig for testing.
    """
    return LLMConfig(
        default_provider="ollama",  # type: ignore[arg-type]
        providers={
            "ollama": ProviderConfig(api_base="http://localhost:11434"),
        },
        tiers={
            "medium": TierModels(ollama="qwen2.5:7b"),
        },
        agents={
            "clarifier": AgentConfig(tier="medium"),
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


def create_subjective_gap() -> Gap:
    """Create a subjective gap for testing.

    Returns:
        Gap with gap_type SUBJECTIVE.
    """
    return Gap(
        description="Current energy level unknown",
        gap_type=GapType.SUBJECTIVE,
        severity="critical",
    )


def create_clarification_gap() -> Gap:
    """Create a clarification gap for testing.

    Returns:
        Gap with gap_type CLARIFICATION.
    """
    return Gap(
        description="Query is ambiguous",
        gap_type=GapType.CLARIFICATION,
        severity="critical",
    )


# =============================================================================
# Test DomainModule clarification_patterns Field (Task 7.2, 7.3)
# =============================================================================


class TestDomainModuleClarificationPatterns:
    """Tests for DomainModule clarification_patterns field."""

    def test_domain_module_with_empty_clarification_patterns(self) -> None:
        """DomainModule accepts empty clarification_patterns (default)."""
        domain = DomainModule(
            description="Test domain",
            log_schema=DummyLogSchema,
            vocabulary={},
        )
        assert domain.clarification_patterns == {}

    def test_domain_module_with_clarification_patterns(self) -> None:
        """DomainModule accepts clarification_patterns dict."""
        patterns = {
            "SUBJECTIVE": ["How are you feeling?", "What's your energy level?"],
            "CLARIFICATION": ["Which exercise?", "What time period?"],
        }
        domain = DomainModule(
            description="Test domain",
            log_schema=DummyLogSchema,
            vocabulary={},
            clarification_patterns=patterns,
        )
        assert domain.clarification_patterns == patterns
        assert len(domain.clarification_patterns["SUBJECTIVE"]) == 2
        assert len(domain.clarification_patterns["CLARIFICATION"]) == 2

    def test_domain_module_with_single_gap_type_pattern(self) -> None:
        """DomainModule accepts single gap type in clarification_patterns."""
        patterns = {
            "SUBJECTIVE": ["How do you feel?"],
        }
        domain = DomainModule(
            description="Test domain",
            log_schema=DummyLogSchema,
            vocabulary={},
            clarification_patterns=patterns,
        )
        assert domain.clarification_patterns == patterns
        assert "SUBJECTIVE" in domain.clarification_patterns
        assert "CLARIFICATION" not in domain.clarification_patterns

    def test_domain_module_backward_compatibility_without_field(self) -> None:
        """DomainModule works without explicitly passing clarification_patterns."""

        class TestDomain(DomainModule):
            """Test domain without clarification_patterns."""

        domain = TestDomain(
            description="Test domain",
            log_schema=DummyLogSchema,
            vocabulary={"test": "testing"},
        )
        # Should still work and have default empty dict
        assert domain.clarification_patterns == {}
        assert domain.description == "Test domain"
        assert domain.vocabulary == {"test": "testing"}


# =============================================================================
# Test ClarifierInput clarification_patterns Field (Task 7.4)
# =============================================================================


class TestClarifierInputClarificationPatterns:
    """Tests for ClarifierInput clarification_patterns field."""

    def test_clarifier_input_with_empty_patterns(self) -> None:
        """ClarifierInput accepts empty clarification_patterns (default)."""
        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
        )
        assert clarifier_input.clarification_patterns == {}

    def test_clarifier_input_with_patterns(self) -> None:
        """ClarifierInput accepts clarification_patterns dict."""
        patterns = {
            "SUBJECTIVE": ["How's your energy?"],
            "CLARIFICATION": ["Which workout?"],
        }
        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
            clarification_patterns=patterns,
        )
        assert clarifier_input.clarification_patterns == patterns

    def test_clarifier_input_backward_compatibility(self) -> None:
        """ClarifierInput works without clarification_patterns."""
        clarifier_input = ClarifierInput(
            original_query="Test query",
            gaps=[],
            vocabulary={"test": "testing"},
        )
        # Should have default empty dict
        assert clarifier_input.clarification_patterns == {}
        # Other fields should work normally
        assert clarifier_input.original_query == "Test query"
        assert clarifier_input.vocabulary == {"test": "testing"}


# =============================================================================
# Test ClarifierAgent build_prompt with patterns (Task 7.5, 7.6)
# =============================================================================


class TestClarifierAgentBuildPromptWithPatterns:
    """Tests for ClarifierAgent.build_prompt with clarification_patterns."""

    def test_prompt_includes_clarification_patterns(self) -> None:
        """Prompt includes clarification_patterns when provided."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        patterns = {
            "SUBJECTIVE": [
                "How's your energy level right now?",
                "Did you sleep well last night?",
            ],
            "CLARIFICATION": [
                "Which specific exercise are you asking about?",
            ],
        }
        clarifier_input = ClarifierInput(
            original_query="How should I adjust my workout?",
            gaps=[create_subjective_gap()],
            vocabulary={},
            clarification_patterns=patterns,
        )
        prompt = clarifier.build_prompt(clarifier_input)

        # Check patterns are included
        assert "SUBJECTIVE gaps" in prompt
        assert "How's your energy level right now?" in prompt
        assert "Did you sleep well last night?" in prompt
        assert "CLARIFICATION gaps" in prompt
        assert "Which specific exercise are you asking about?" in prompt
        # Check the section header
        assert "DOMAIN-SPECIFIC PATTERNS" in prompt

    def test_prompt_handles_empty_patterns_gracefully(self) -> None:
        """Prompt handles empty clarification_patterns gracefully."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
            clarification_patterns={},
        )
        prompt = clarifier.build_prompt(clarifier_input)

        # Should have placeholder for no patterns
        assert "(No domain-specific patterns provided)" in prompt
        # Section header should still be present
        assert "DOMAIN-SPECIFIC PATTERNS" in prompt

    def test_prompt_with_single_gap_type_pattern(self) -> None:
        """Prompt correctly formats single gap type pattern."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        patterns = {
            "SUBJECTIVE": ["How are you feeling today?"],
        }
        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
            clarification_patterns=patterns,
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "SUBJECTIVE gaps" in prompt
        assert "How are you feeling today?" in prompt
        # CLARIFICATION shouldn't be in patterns section since not provided
        # (though it appears elsewhere in the prompt for gap type guidance)

    def test_prompt_with_multiple_questions_per_gap_type(self) -> None:
        """Prompt formats multiple questions per gap type correctly."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        patterns = {
            "SUBJECTIVE": [
                "Energy level?",
                "Sleep quality?",
                "Stress level?",
                "Motivation?",
            ],
        }
        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
            clarification_patterns=patterns,
        )
        prompt = clarifier.build_prompt(clarifier_input)

        # All questions should be present
        assert "Energy level?" in prompt
        assert "Sleep quality?" in prompt
        assert "Stress level?" in prompt
        assert "Motivation?" in prompt


# =============================================================================
# Test _format_clarification_patterns Helper
# =============================================================================


class TestFormatClarificationPatternsHelper:
    """Tests for ClarifierAgent._format_clarification_patterns method."""

    def test_format_empty_patterns(self) -> None:
        """_format_clarification_patterns handles empty dict."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        result = clarifier._format_clarification_patterns({})  # pyright: ignore[reportPrivateUsage]
        assert result == "(No domain-specific patterns provided)"

    def test_format_single_gap_type(self) -> None:
        """_format_clarification_patterns formats single gap type."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        patterns = {"SUBJECTIVE": ["How are you?", "Energy level?"]}
        result = clarifier._format_clarification_patterns(patterns)  # pyright: ignore[reportPrivateUsage]

        assert "For SUBJECTIVE gaps" in result
        assert "How are you?" in result
        assert "Energy level?" in result

    def test_format_multiple_gap_types(self) -> None:
        """_format_clarification_patterns formats multiple gap types."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        patterns = {
            "SUBJECTIVE": ["How are you?"],
            "CLARIFICATION": ["Which one?"],
        }
        result = clarifier._format_clarification_patterns(patterns)  # pyright: ignore[reportPrivateUsage]

        assert "For SUBJECTIVE gaps" in result
        assert "How are you?" in result
        assert "For CLARIFICATION gaps" in result
        assert "Which one?" in result


# =============================================================================
# Integration Tests with Real Ollama
# =============================================================================


class TestClarifierPatternsIntegration:
    """Integration tests for clarification_patterns with real Ollama.

    Run with: pytest --use-real-ollama -k TestClarifierPatternsIntegration
    Or via: make test-ollama
    """

    @pytest.mark.asyncio
    async def test_real_clarification_with_fitness_patterns(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real clarification with fitness-specific patterns."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        clarifier = ClarifierAgent(real_llm_client)

        # Fitness-specific patterns
        patterns = {
            "SUBJECTIVE": [
                "How's your energy level right now - feeling fresh or fatigued?",
                "How well did you sleep last night?",
                "On a scale of 1-10, how motivated are you?",
            ],
            "CLARIFICATION": [
                "Which specific workout are you asking about?",
                "What time period should I focus on?",
            ],
        }

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="Should I do my workout today?",
                gaps=[
                    Gap(
                        description="Current energy and readiness level unknown",
                        gap_type=GapType.SUBJECTIVE,
                        severity="critical",
                    )
                ],
                vocabulary={"rpe": "rate of perceived exertion"},
                clarification_patterns=patterns,
            )
        )

        # Should have valid output
        assert result.context_explanation is not None
        assert len(result.context_explanation) > 0
        assert result.fallback_action is not None
        assert len(result.fallback_action) > 0
        # Should generate at least one question
        assert len(result.questions) >= 1
        assert len(result.questions) <= 3

    @pytest.mark.asyncio
    async def test_real_clarification_with_strength_patterns(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real clarification with strength-specific patterns."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        clarifier = ClarifierAgent(real_llm_client)

        # Strength-specific patterns
        patterns = {
            "SUBJECTIVE": [
                "Any lingering soreness from previous workouts?",
                "Are any joints or muscles feeling tight?",
                "Did your warm-up sets feel smooth or heavy?",
            ],
            "CLARIFICATION": [
                "Which specific lift (squat, bench, deadlift)?",
                "What rep range - strength (1-5), hypertrophy (6-12)?",
            ],
        }

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="How much weight should I use today?",
                gaps=[
                    Gap(
                        description="Which exercise and current physical state unknown",
                        gap_type=GapType.CLARIFICATION,
                        severity="critical",
                    ),
                    Gap(
                        description="Current physical readiness unknown",
                        gap_type=GapType.SUBJECTIVE,
                        severity="critical",
                    ),
                ],
                vocabulary={"rpe": "rate of perceived exertion", "pr": "personal record"},
                clarification_patterns=patterns,
            )
        )

        # Should have valid output
        assert result.context_explanation is not None
        assert result.fallback_action is not None
        # Should generate questions for the gaps
        assert len(result.questions) >= 1
        assert len(result.questions) <= 3

    @pytest.mark.asyncio
    async def test_real_clarification_without_patterns(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real clarification without patterns still works."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        clarifier = ClarifierAgent(real_llm_client)

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="How am I doing?",
                gaps=[
                    Gap(
                        description="Query is vague - what aspect?",
                        gap_type=GapType.CLARIFICATION,
                        severity="critical",
                    )
                ],
                vocabulary={},
                # No clarification_patterns - should still work
            )
        )

        # Should still produce valid output
        assert result.context_explanation is not None
        assert result.fallback_action is not None
        assert len(result.questions) >= 1
