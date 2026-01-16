"""Unit tests for ObserverAgent.

Tests cover model validation, prompt building, observe execution,
trigger-specific handling, and exports.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ValidationError
from quilto import load_llm_config
from quilto.agents import (
    ContextUpdate,
    ObserverAgent,
    ObserverInput,
    ObserverOutput,
)
from quilto.llm.client import LLMClient
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for ObserverAgent tests.

    Returns:
        Configured LLMConfig for testing.
    """
    return LLMConfig(
        default_provider="ollama",  # type: ignore[arg-type]
        providers={
            "ollama": ProviderConfig(api_base="http://localhost:11434"),
        },
        tiers={
            "high": TierModels(ollama="qwen2.5:14b"),
        },
        agents={
            "observer": AgentConfig(tier="high"),
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


# =============================================================================
# Test ContextUpdate Model (Task 7.5)
# =============================================================================


class TestContextUpdateModel:
    """Tests for ContextUpdate Pydantic model validation."""

    def test_context_update_valid_preference(self) -> None:
        """ContextUpdate accepts valid preference data."""
        update = ContextUpdate(
            category="preference",
            key="unit_preference",
            value="metric",
            confidence="certain",
            source="user_correction: changed lbs to kg",
        )
        assert update.category == "preference"
        assert update.key == "unit_preference"
        assert update.value == "metric"
        assert update.confidence == "certain"
        assert update.source == "user_correction: changed lbs to kg"

    def test_context_update_valid_pattern(self) -> None:
        """ContextUpdate accepts valid pattern data."""
        update = ContextUpdate(
            category="pattern",
            key="typical_active_days",
            value="Monday, Wednesday, Friday",
            confidence="likely",
            source="post_query: workout frequency analysis",
        )
        assert update.category == "pattern"
        assert update.confidence == "likely"

    def test_context_update_valid_fact(self) -> None:
        """ContextUpdate accepts valid fact data."""
        update = ContextUpdate(
            category="fact",
            key="bench_press_pr",
            value="185 lbs x 5 reps",
            confidence="certain",
            source="significant_log: new PR recorded",
        )
        assert update.category == "fact"

    def test_context_update_valid_insight(self) -> None:
        """ContextUpdate accepts valid insight data."""
        update = ContextUpdate(
            category="insight",
            key="sleep_performance_correlation",
            value="Performance drops when sleep below 7 hours",
            confidence="tentative",
            source="post_query: sleep pattern analysis",
        )
        assert update.category == "insight"
        assert update.confidence == "tentative"

    def test_context_update_all_category_values(self) -> None:
        """ContextUpdate accepts all valid category Literal values."""
        for category in ["preference", "pattern", "fact", "insight"]:
            update = ContextUpdate(
                category=category,  # type: ignore[arg-type]
                key="test_key",
                value="test_value",
                confidence="certain",
                source="test_source",
            )
            assert update.category == category

    def test_context_update_all_confidence_values(self) -> None:
        """ContextUpdate accepts all valid confidence Literal values."""
        for confidence in ["certain", "likely", "tentative"]:
            update = ContextUpdate(
                category="preference",
                key="test_key",
                value="test_value",
                confidence=confidence,  # type: ignore[arg-type]
                source="test_source",
            )
            assert update.confidence == confidence

    def test_context_update_empty_key_fails(self) -> None:
        """ContextUpdate with empty key fails min_length=1."""
        with pytest.raises(ValidationError):
            ContextUpdate(
                category="preference",
                key="",
                value="metric",
                confidence="certain",
                source="test",
            )

    def test_context_update_empty_value_fails(self) -> None:
        """ContextUpdate with empty value fails min_length=1."""
        with pytest.raises(ValidationError):
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="",
                confidence="certain",
                source="test",
            )

    def test_context_update_empty_source_fails(self) -> None:
        """ContextUpdate with empty source fails min_length=1."""
        with pytest.raises(ValidationError):
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="metric",
                confidence="certain",
                source="",
            )

    def test_context_update_invalid_category_fails(self) -> None:
        """ContextUpdate with invalid category fails."""
        with pytest.raises(ValidationError):
            ContextUpdate(
                category="invalid",  # type: ignore[arg-type]
                key="test_key",
                value="test_value",
                confidence="certain",
                source="test",
            )

    def test_context_update_invalid_confidence_fails(self) -> None:
        """ContextUpdate with invalid confidence fails."""
        with pytest.raises(ValidationError):
            ContextUpdate(
                category="preference",
                key="test_key",
                value="test_value",
                confidence="invalid",  # type: ignore[arg-type]
                source="test",
            )


# =============================================================================
# Test ObserverInput Model (Task 7.6)
# =============================================================================


class TestObserverInputModel:
    """Tests for ObserverInput Pydantic model validation."""

    def test_observer_input_valid_post_query(self) -> None:
        """ObserverInput accepts valid post_query trigger."""
        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="# Global Context\n...",
            context_management_guidance="Track PRs, workout patterns, preferences",
            query="How has my bench press progressed?",
            analysis={"findings": ["Progressive overload detected"]},
            response="Your bench press improved by 10 lbs",
        )
        assert observer_input.trigger == "post_query"
        assert observer_input.query == "How has my bench press progressed?"

    def test_observer_input_valid_user_correction(self) -> None:
        """ObserverInput accepts valid user_correction trigger."""
        observer_input = ObserverInput(
            trigger="user_correction",
            current_global_context="# Global Context\n...",
            context_management_guidance="Track PRs, preferences",
            correction="Actually I ran 5km not 3km",
            what_was_corrected="distance",
        )
        assert observer_input.trigger == "user_correction"
        assert observer_input.correction == "Actually I ran 5km not 3km"

    def test_observer_input_valid_significant_log(self) -> None:
        """ObserverInput accepts valid significant_log trigger."""
        observer_input = ObserverInput(
            trigger="significant_log",
            current_global_context="# Global Context\n...",
            context_management_guidance="Track PRs, milestones",
            new_entry={"type": "workout", "activity": "bench press", "sets": "185x5"},
        )
        assert observer_input.trigger == "significant_log"
        assert observer_input.new_entry is not None

    def test_observer_input_all_trigger_values(self) -> None:
        """ObserverInput accepts all valid trigger Literal values."""
        for trigger in ["post_query", "user_correction", "significant_log"]:
            # Provide required fields based on trigger
            kwargs: dict[str, Any] = {
                "trigger": trigger,
                "current_global_context": "",
                "context_management_guidance": "guidance",
            }
            if trigger == "post_query":
                kwargs.update({"query": "test", "analysis": {}, "response": "test"})
            elif trigger == "user_correction":
                kwargs.update({"correction": "test", "what_was_corrected": "test"})
            else:
                kwargs.update({"new_entry": {}})

            observer_input = ObserverInput(**kwargs)
            assert observer_input.trigger == trigger

    def test_observer_input_empty_current_global_context_valid(self) -> None:
        """ObserverInput with empty current_global_context is valid (new user)."""
        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="Track preferences",
            query="How am I doing?",
            analysis={},
            response="Looking good",
        )
        assert observer_input.current_global_context == ""

    def test_observer_input_empty_context_management_guidance_fails(self) -> None:
        """ObserverInput with empty context_management_guidance fails min_length=1."""
        with pytest.raises(ValidationError):
            ObserverInput(
                trigger="post_query",
                current_global_context="",
                context_management_guidance="",
                query="test",
                analysis={},
                response="test",
            )

    def test_observer_input_post_query_missing_query_fails(self) -> None:
        """ObserverInput post_query without query fails model_validator."""
        with pytest.raises(ValidationError, match="post_query trigger requires query"):
            ObserverInput(
                trigger="post_query",
                current_global_context="",
                context_management_guidance="guidance",
                analysis={},
                response="test",
            )

    def test_observer_input_post_query_missing_analysis_fails(self) -> None:
        """ObserverInput post_query without analysis fails model_validator."""
        with pytest.raises(ValidationError, match="post_query trigger requires"):
            ObserverInput(
                trigger="post_query",
                current_global_context="",
                context_management_guidance="guidance",
                query="test",
                response="test",
            )

    def test_observer_input_post_query_missing_response_fails(self) -> None:
        """ObserverInput post_query without response fails model_validator."""
        with pytest.raises(ValidationError, match="post_query trigger requires"):
            ObserverInput(
                trigger="post_query",
                current_global_context="",
                context_management_guidance="guidance",
                query="test",
                analysis={},
            )

    def test_observer_input_user_correction_missing_correction_fails(self) -> None:
        """ObserverInput user_correction without correction fails model_validator."""
        with pytest.raises(ValidationError, match="user_correction trigger requires"):
            ObserverInput(
                trigger="user_correction",
                current_global_context="",
                context_management_guidance="guidance",
                what_was_corrected="distance",
            )

    def test_observer_input_user_correction_missing_what_was_corrected_fails(self) -> None:
        """ObserverInput user_correction without what_was_corrected fails."""
        with pytest.raises(ValidationError, match="user_correction trigger requires"):
            ObserverInput(
                trigger="user_correction",
                current_global_context="",
                context_management_guidance="guidance",
                correction="I ran 5km",
            )

    def test_observer_input_significant_log_missing_new_entry_fails(self) -> None:
        """ObserverInput significant_log without new_entry fails model_validator."""
        with pytest.raises(ValidationError, match="significant_log trigger requires"):
            ObserverInput(
                trigger="significant_log",
                current_global_context="",
                context_management_guidance="guidance",
            )

    def test_observer_input_whitespace_guidance_passes_pydantic(self) -> None:
        """ObserverInput with whitespace-only guidance passes Pydantic min_length."""
        # Whitespace-only strings have length > 0, so Pydantic accepts them.
        # Runtime check in ObserverAgent.observe() catches this.
        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="   \n\t  ",
            query="test",
            analysis={},
            response="test",
        )
        # Should pass Pydantic validation
        assert observer_input.context_management_guidance == "   \n\t  "

    def test_observer_input_invalid_trigger_fails(self) -> None:
        """ObserverInput with invalid trigger value fails validation."""
        with pytest.raises(ValidationError):
            ObserverInput(
                trigger="invalid_trigger",  # type: ignore[arg-type]
                current_global_context="",
                context_management_guidance="guidance",
            )


# =============================================================================
# Test ObserverOutput Model (Task 7.7)
# =============================================================================


class TestObserverOutputModel:
    """Tests for ObserverOutput Pydantic model validation."""

    def test_observer_output_should_update_true(self) -> None:
        """ObserverOutput accepts should_update=True."""
        output = ObserverOutput(
            should_update=True,
            updates=[
                ContextUpdate(
                    category="preference",
                    key="test",
                    value="test",
                    confidence="certain",
                    source="test",
                )
            ],
            insights_captured=["Discovered user preference"],
        )
        assert output.should_update is True
        assert len(output.updates) == 1
        assert len(output.insights_captured) == 1

    def test_observer_output_should_update_false(self) -> None:
        """ObserverOutput accepts should_update=False."""
        output = ObserverOutput(should_update=False)
        assert output.should_update is False
        assert output.updates == []
        assert output.insights_captured == []

    def test_observer_output_updates_default_empty(self) -> None:
        """ObserverOutput updates defaults to empty list."""
        output = ObserverOutput(should_update=True)
        assert output.updates == []

    def test_observer_output_insights_captured_default_empty(self) -> None:
        """ObserverOutput insights_captured defaults to empty list."""
        output = ObserverOutput(should_update=True)
        assert output.insights_captured == []

    def test_observer_output_with_multiple_updates(self) -> None:
        """ObserverOutput accepts multiple updates."""
        updates = [
            ContextUpdate(
                category="preference",
                key="unit_preference",
                value="metric",
                confidence="certain",
                source="correction",
            ),
            ContextUpdate(
                category="pattern",
                key="typical_schedule",
                value="MWF mornings",
                confidence="likely",
                source="post_query",
            ),
        ]
        output = ObserverOutput(
            should_update=True,
            updates=updates,
            insights_captured=["User prefers metric", "Workouts on MWF"],
        )
        assert len(output.updates) == 2
        assert len(output.insights_captured) == 2


# =============================================================================
# Test ObserverAgent Instantiation (Task 7.8)
# =============================================================================


class TestObserverAgentInstantiation:
    """Tests for ObserverAgent class instantiation."""

    def test_observer_agent_creates_with_llm_client(self) -> None:
        """ObserverAgent creates successfully with LLMClient."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)
        assert observer.llm_client is client

    def test_observer_agent_name_constant(self) -> None:
        """ObserverAgent has correct AGENT_NAME constant."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)
        assert observer.AGENT_NAME == "observer"
        assert ObserverAgent.AGENT_NAME == "observer"


# =============================================================================
# Test Prompt Building (Task 7.8)
# =============================================================================


class TestObserverPromptBuilding:
    """Tests for ObserverAgent.build_prompt method."""

    def test_prompt_includes_current_global_context(self) -> None:
        """Prompt includes the current global context."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="# Global Context\n## Preferences\n- units: metric",
            context_management_guidance="Track preferences and patterns",
            query="How is my progress?",
            analysis={},
            response="Great progress!",
        )
        prompt = observer.build_prompt(observer_input)

        assert "# Global Context" in prompt
        assert "units: metric" in prompt

    def test_prompt_includes_context_management_guidance(self) -> None:
        """Prompt includes domain context management guidance."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="Track PRs, workout patterns, user preferences",
            query="How is my progress?",
            analysis={},
            response="Great progress!",
        )
        prompt = observer.build_prompt(observer_input)

        assert "Track PRs, workout patterns, user preferences" in prompt

    def test_prompt_includes_post_query_context(self) -> None:
        """Prompt includes query, analysis, and response for post_query."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="guidance",
            query="How has my bench press progressed?",
            analysis={"findings": ["Progressive overload"]},
            response="Your bench improved by 10 lbs",
        )
        prompt = observer.build_prompt(observer_input)

        assert "How has my bench press progressed?" in prompt
        assert "Progressive overload" in prompt
        assert "Your bench improved by 10 lbs" in prompt

    def test_prompt_includes_correction_context(self) -> None:
        """Prompt includes correction details for user_correction."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        observer_input = ObserverInput(
            trigger="user_correction",
            current_global_context="",
            context_management_guidance="guidance",
            correction="Actually I ran 5km not 3km",
            what_was_corrected="distance",
        )
        prompt = observer.build_prompt(observer_input)

        assert "Actually I ran 5km not 3km" in prompt
        assert "distance" in prompt
        assert "certain" in prompt.lower()  # Should mention certain confidence for corrections

    def test_prompt_includes_significant_log_context(self) -> None:
        """Prompt includes entry details for significant_log."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        observer_input = ObserverInput(
            trigger="significant_log",
            current_global_context="",
            context_management_guidance="guidance",
            new_entry={"activity": "bench press", "weight": "185 lbs", "reps": 5},
        )
        prompt = observer.build_prompt(observer_input)

        assert "bench press" in prompt
        assert "185 lbs" in prompt

    def test_prompt_includes_confidence_levels(self) -> None:
        """Prompt includes guidance on confidence levels."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="guidance",
            query="test",
            analysis={},
            response="test",
        )
        prompt = observer.build_prompt(observer_input)

        assert "certain" in prompt.lower()
        assert "likely" in prompt.lower()
        assert "tentative" in prompt.lower()

    def test_prompt_includes_categories(self) -> None:
        """Prompt includes guidance on categories."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="guidance",
            query="test",
            analysis={},
            response="test",
        )
        prompt = observer.build_prompt(observer_input)

        assert "preference" in prompt.lower()
        assert "pattern" in prompt.lower()
        assert "fact" in prompt.lower()
        assert "insight" in prompt.lower()

    def test_prompt_includes_consolidation_rules(self) -> None:
        """Prompt includes rules for consolidating updates."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="guidance",
            query="test",
            analysis={},
            response="test",
        )
        prompt = observer.build_prompt(observer_input)

        assert "consolidat" in prompt.lower()
        assert "supersede" in prompt.lower()

    def test_prompt_handles_empty_global_context(self) -> None:
        """Prompt handles empty global context gracefully."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="guidance",
            query="test",
            analysis={},
            response="test",
        )
        prompt = observer.build_prompt(observer_input)

        assert "empty - new user" in prompt.lower()


# =============================================================================
# Test Observe Method (Task 7.9, 7.10)
# =============================================================================


class TestObserveMethod:
    """Tests for ObserverAgent.observe method."""

    @pytest.mark.asyncio
    async def test_observe_returns_observer_output(self) -> None:
        """Test observe returns ObserverOutput with mock LLMClient."""
        response: dict[str, Any] = {
            "should_update": True,
            "updates": [
                {
                    "category": "preference",
                    "key": "unit_preference",
                    "value": "metric",
                    "confidence": "certain",
                    "source": "user_correction: changed units",
                }
            ],
            "insights_captured": ["User prefers metric units"],
        }
        client = create_mock_llm_client(response)
        observer = ObserverAgent(client)

        result = await observer.observe(
            ObserverInput(
                trigger="user_correction",
                current_global_context="",
                context_management_guidance="Track preferences",
                correction="Use kg not lbs",
                what_was_corrected="units",
            )
        )

        assert isinstance(result, ObserverOutput)
        assert result.should_update is True
        assert len(result.updates) == 1
        assert result.updates[0].key == "unit_preference"
        assert result.insights_captured == ["User prefers metric units"]

    @pytest.mark.asyncio
    async def test_observe_with_no_updates(self) -> None:
        """Test observe returns should_update=False when no insights."""
        response: dict[str, Any] = {
            "should_update": False,
            "updates": [],
            "insights_captured": [],
        }
        client = create_mock_llm_client(response)
        observer = ObserverAgent(client)

        result = await observer.observe(
            ObserverInput(
                trigger="post_query",
                current_global_context="",
                context_management_guidance="Track patterns",
                query="What's the weather?",
                analysis={},
                response="I don't have weather data",
            )
        )

        assert result.should_update is False
        assert result.updates == []

    @pytest.mark.asyncio
    async def test_observe_whitespace_only_guidance_raises_value_error(self) -> None:
        """Test observe raises ValueError for whitespace-only guidance."""
        client = create_mock_llm_client({})
        observer = ObserverAgent(client)

        with pytest.raises(ValueError, match="empty or whitespace"):
            await observer.observe(
                ObserverInput(
                    trigger="post_query",
                    current_global_context="",
                    context_management_guidance="   \n\t  ",
                    query="test",
                    analysis={},
                    response="test",
                )
            )

    @pytest.mark.asyncio
    async def test_observe_calls_llm_with_correct_agent_name(self) -> None:
        """Test observe calls LLM with AGENT_NAME='observer'."""
        response: dict[str, Any] = {
            "should_update": False,
            "updates": [],
            "insights_captured": [],
        }
        client = create_mock_llm_client(response)
        observer = ObserverAgent(client)

        await observer.observe(
            ObserverInput(
                trigger="post_query",
                current_global_context="",
                context_management_guidance="guidance",
                query="test",
                analysis={},
                response="test",
            )
        )

        # Verify the agent name was passed
        call_args = client.complete_structured.call_args  # type: ignore[union-attr]
        assert call_args[1]["agent"] == "observer"


# =============================================================================
# Test Exports (Task 7)
# =============================================================================


class TestObserverExports:
    """Tests for observer exports from quilto.agents."""

    def test_observer_agent_importable(self) -> None:
        """ObserverAgent is importable from quilto.agents."""
        from quilto.agents import ObserverAgent

        assert ObserverAgent is not None

    def test_context_update_importable(self) -> None:
        """ContextUpdate is importable from quilto.agents."""
        from quilto.agents import ContextUpdate

        assert ContextUpdate is not None

    def test_observer_input_importable(self) -> None:
        """ObserverInput is importable from quilto.agents."""
        from quilto.agents import ObserverInput

        assert ObserverInput is not None

    def test_observer_output_importable(self) -> None:
        """ObserverOutput is importable from quilto.agents."""
        from quilto.agents import ObserverOutput

        assert ObserverOutput is not None

    def test_all_exports_in_all_list(self) -> None:
        """All observer types are in __all__ list."""
        from quilto import agents

        assert "ObserverAgent" in agents.__all__
        assert "ContextUpdate" in agents.__all__
        assert "ObserverInput" in agents.__all__
        assert "ObserverOutput" in agents.__all__


# =============================================================================
# Integration Tests (Task 8)
# =============================================================================


class TestObserverIntegration:
    """Integration tests with real Ollama.

    Run with: pytest --use-real-ollama -k TestObserverIntegration
    Or via: make test-ollama
    """

    @pytest.mark.asyncio
    async def test_real_post_query_observation(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real observation with post_query trigger."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        result = await observer.observe(
            ObserverInput(
                trigger="post_query",
                current_global_context="# Global Context\n## Preferences\n- units: lbs",
                context_management_guidance="""Track the following:
- User unit preferences (metric vs imperial)
- Workout patterns (typical days, times)
- Personal records (PRs) for exercises
- User goals and preferences""",
                query="How has my bench press progressed this month?",
                analysis={
                    "findings": [
                        "Jan 3: bench 175x5",
                        "Jan 10: bench 180x5",
                        "Jan 17: bench 185x5",
                    ],
                    "patterns": ["Progressive overload detected"],
                },
                response="Your bench press has improved by 10 lbs this month, "
                "going from 175x5 to 185x5. Great progressive overload!",
            )
        )

        # Should have valid output structure
        assert isinstance(result.should_update, bool)
        assert isinstance(result.updates, list)
        assert isinstance(result.insights_captured, list)

    @pytest.mark.asyncio
    async def test_real_user_correction_observation(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real observation with user_correction trigger - verify certain confidence."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        result = await observer.observe(
            ObserverInput(
                trigger="user_correction",
                current_global_context="# Global Context\n## Preferences\n- units: lbs",
                context_management_guidance="""Track the following:
- User unit preferences (metric vs imperial)
- Explicit user corrections should be treated with high confidence""",
                correction="Please use kilograms instead of pounds",
                what_was_corrected="unit preference",
            )
        )

        # Should have valid output structure
        assert isinstance(result.should_update, bool)
        assert isinstance(result.updates, list)
        assert isinstance(result.insights_captured, list)

        # For explicit corrections, LLM should generate updates with certain confidence
        # This is a key behavioral requirement per AC #7
        assert result.should_update, (
            "User corrections should always trigger updates - LLM should recognize "
            "explicit preference change"
        )
        assert len(result.updates) > 0, (
            "User corrections should generate at least one update"
        )
        confidences = [u.confidence for u in result.updates]
        assert "certain" in confidences, (
            "User corrections should generate 'certain' confidence updates"
        )

    @pytest.mark.asyncio
    async def test_real_significant_log_observation(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real observation with significant_log trigger - verify identifies facts."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        result = await observer.observe(
            ObserverInput(
                trigger="significant_log",
                current_global_context="# Global Context\n## Facts\n- bench_pr: 180 lbs",
                context_management_guidance="""Track the following:
- Personal records (PRs) - these are facts with certain confidence
- Milestones like 100th workout, first marathon, etc.
- Major achievements""",
                new_entry={
                    "type": "workout",
                    "date": "2026-01-17",
                    "activity": "bench press",
                    "sets": [
                        {"weight": "185 lbs", "reps": 5},
                        {"weight": "190 lbs", "reps": 3},
                    ],
                    "notes": "New PR! Beat previous 180 lbs record",
                },
            )
        )

        # Should have valid output structure
        assert isinstance(result.should_update, bool)
        assert isinstance(result.updates, list)
        assert isinstance(result.insights_captured, list)

        # For PRs, should typically have fact category updates
        if result.should_update and result.updates:
            categories = [u.category for u in result.updates]
            # PRs are typically recorded as facts
            assert "fact" in categories or "insight" in categories
