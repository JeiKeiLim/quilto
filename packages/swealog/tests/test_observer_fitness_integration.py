"""Integration tests for Observer with fitness domains.

These tests verify Observer correctly extracts fitness patterns using
domain-specific context_management_guidance. Run with:
    make test-ollama
or:
    pytest --use-real-ollama -k TestObserverFitnessIntegration
"""

from datetime import date, datetime
from pathlib import Path

import pytest
from quilto import load_llm_config
from quilto.agents import ObserverAgent, ObserverInput
from quilto.agents.models import (
    ActiveDomainContext,
    AnalyzerOutput,
    Finding,
    SufficiencyEvaluation,
    Verdict,
)
from quilto.llm.client import LLMClient
from quilto.state import (
    ObserverTriggerConfig,
    get_combined_context_guidance,
    serialize_global_context,
    trigger_post_query,
    trigger_significant_log,
)
from quilto.storage import Entry, GlobalContext, GlobalContextManager, StorageRepository
from swealog.domains import general_fitness, running, strength
from swealog.observer import FitnessSignificantEntryDetector


def create_mock_global_context() -> GlobalContext:
    """Create empty GlobalContext for tests.

    Returns:
        Empty GlobalContext instance.
    """
    return GlobalContext.model_validate(
        {
            "frontmatter": {
                "last_updated": "2026-01-15",
                "version": 1,
                "token_estimate": 0,
            },
            "preferences": [],
            "patterns": [],
            "facts": [],
            "insights": [],
        }
    )


def build_strength_guidance() -> str:
    """Build combined context guidance including Strength domain.

    Returns:
        Combined context management guidance string.
    """
    active_context = ActiveDomainContext(
        domains_loaded=["Strength"],
        vocabulary={},
        expertise="Strength training expertise.",
        context_guidance=f"[Strength]: {strength.context_management_guidance}",
    )
    return get_combined_context_guidance(active_context)


def build_combined_fitness_guidance() -> str:
    """Build combined context guidance from GeneralFitness + Strength.

    Returns:
        Combined context management guidance string.
    """
    guidance_parts = [
        f"[GeneralFitness]: {general_fitness.context_management_guidance}",
        f"[Strength]: {strength.context_management_guidance}",
    ]
    active_context = ActiveDomainContext(
        domains_loaded=["GeneralFitness", "Strength"],
        vocabulary={},
        expertise="General fitness and strength training expertise.",
        context_guidance="\n\n".join(guidance_parts),
    )
    return get_combined_context_guidance(active_context)


def build_running_guidance() -> str:
    """Build combined context guidance including Running domain.

    Returns:
        Combined context management guidance string.
    """
    active_context = ActiveDomainContext(
        domains_loaded=["Running"],
        vocabulary={},
        expertise="Running and cardio expertise.",
        context_guidance=f"[Running]: {running.context_management_guidance}",
    )
    return get_combined_context_guidance(active_context)


class TestObserverFitnessIntegration:
    """Integration tests with real Ollama for fitness domain observation.

    These tests verify AC #8:
    - Observer correctly extracts fitness patterns
    - Updates include appropriate fitness categories (fact/pattern/insight)
    - Confidence levels are appropriate
    """

    @pytest.mark.asyncio
    async def test_observer_with_strength_pr(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test Observer with Strength domain PR entry (AC: #8).

        Given: Bench press PR log entry with explicit PR mention
        When: Observer processes with Strength domain guidance
        Then: Observer generates update with category="fact" for PR
        And: Confidence is "certain" for explicit PR mention
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        guidance = build_strength_guidance()
        context = create_mock_global_context()
        serialized_context = serialize_global_context(context)

        result = await observer.observe(
            ObserverInput(
                trigger="significant_log",
                current_global_context=serialized_context,
                context_management_guidance=guidance,
                new_entry={
                    "type": "strength",
                    "date": "2026-01-15",
                    "exercises": [
                        {
                            "name": "bench press",
                            "sets": [
                                {"weight": "225 lbs", "reps": 5, "rpe": 8},
                            ],
                        }
                    ],
                    "notes": "New PR! Beat my previous 220lbs record.",
                },
            )
        )

        # Verify valid output structure
        assert isinstance(result.should_update, bool)
        assert isinstance(result.updates, list)

        # For explicit PR mention, should generate updates
        assert result.should_update, (
            "Observer should recognize explicit PR mention and generate updates"
        )
        assert len(result.updates) > 0, (
            "PR entries should generate at least one update"
        )

        # Check that at least one update is a fact with certain confidence
        categories = [u.category for u in result.updates]
        confidences = [u.confidence for u in result.updates]

        assert "fact" in categories, (
            "PRs should be recorded as facts (certain information about achievement)"
        )
        assert "certain" in confidences, (
            "Explicit PR mentions should have 'certain' confidence"
        )

    @pytest.mark.asyncio
    async def test_observer_with_combined_fitness_guidance(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test Observer with combined GeneralFitness + Strength guidance (AC: #8).

        Given: Post-query with combined domain guidance active
        When: Observer processes with multiple domain guidance
        Then: Combined guidance includes patterns from both domains
        And: Observer tracks patterns appropriately
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        guidance = build_combined_fitness_guidance()
        context = create_mock_global_context()
        serialized_context = serialize_global_context(context)

        # Verify combined guidance includes both domains
        assert "GeneralFitness" in guidance
        assert "Strength" in guidance
        assert "workout frequency" in guidance  # GeneralFitness pattern
        assert "exercise PRs" in guidance  # Strength pattern

        result = await observer.observe(
            ObserverInput(
                trigger="post_query",
                current_global_context=serialized_context,
                context_management_guidance=guidance,
                query="How consistent has my training been this week?",
                analysis={
                    "findings": [
                        "Monday: Bench press 185x5x3",
                        "Tuesday: Rest day",
                        "Wednesday: Squat 225x5x3",
                        "Thursday: Rest day",
                        "Friday: Deadlift 315x5x3",
                    ],
                    "patterns": ["Training 3 days per week", "Major lifts covered"],
                },
                response="You trained 3 days this week with good coverage of major "
                "compound lifts. Consistent Monday-Wednesday-Friday schedule.",
            )
        )

        # Verify valid output structure
        assert isinstance(result.should_update, bool)
        assert isinstance(result.updates, list)

        # This query reveals training patterns - should generate pattern updates
        if result.should_update:
            categories = [u.category for u in result.updates]
            # Training frequency/consistency is typically a pattern
            assert "pattern" in categories or "insight" in categories, (
                "Training consistency observations should generate pattern/insight updates"
            )

    @pytest.mark.asyncio
    async def test_observer_with_running_marathon(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test Observer with Running domain marathon milestone (AC: #8).

        Given: Marathon completion entry
        When: Observer processes with Running domain guidance
        Then: Observer captures milestone
        And: Update has appropriate category (fact for achievement)
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        guidance = build_running_guidance()
        context = create_mock_global_context()
        serialized_context = serialize_global_context(context)

        result = await observer.observe(
            ObserverInput(
                trigger="significant_log",
                current_global_context=serialized_context,
                context_management_guidance=guidance,
                new_entry={
                    "type": "running",
                    "date": "2026-01-15",
                    "distance": 42.2,
                    "distance_unit": "km",
                    "duration_minutes": 240,
                    "pace": "5:41 min/km",
                    "workout_type": "race",
                    "notes": "First marathon! Finished in 4 hours flat. Amazing experience.",
                },
            )
        )

        # Verify valid output structure
        assert isinstance(result.should_update, bool)
        assert isinstance(result.updates, list)

        # First marathon is a major milestone - should generate updates
        assert result.should_update, (
            "First marathon is a significant milestone - should generate updates"
        )
        assert len(result.updates) > 0, (
            "Marathon milestone should generate at least one update"
        )

        # Marathon completion is a fact (achievement)
        categories = [u.category for u in result.updates]
        assert "fact" in categories or "insight" in categories, (
            "Marathon completion should be recorded as fact or insight"
        )

    @pytest.mark.asyncio
    async def test_trigger_significant_log_with_fitness_detector(
        self, use_real_ollama: bool, integration_llm_config_path: Path, tmp_path: Path
    ) -> None:
        """Test trigger_significant_log with FitnessSignificantEntryDetector (AC: #8).

        Given: Entry with injury mention
        When: Using FitnessSignificantEntryDetector
        Then: Entry is detected as significant
        And: Observer processes and tracks cautionary pattern
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        storage = StorageRepository(tmp_path)
        context_manager = GlobalContextManager(storage)

        trigger_config = ObserverTriggerConfig(
            enable_significant_log=True,
        )

        active_context = ActiveDomainContext(
            domains_loaded=["Strength"],
            vocabulary={},
            expertise="Strength training expertise.",
            context_guidance=f"[Strength]: {strength.context_management_guidance}",
        )

        entry = Entry(
            id="2026-01-15_001",
            date=date(2026, 1, 15),
            timestamp=datetime(2026, 1, 15, 10, 0, 0),
            raw_content="Bench press 185x5x3. Felt some shoulder pain on last set, "
            "stopped early. Need to watch this.",
        )

        detector = FitnessSignificantEntryDetector()

        result = await trigger_significant_log(
            observer=observer,
            context_manager=context_manager,
            config=trigger_config,
            entry=entry,
            parsed_data={},
            active_domain_context=active_context,
            detector=detector,
        )

        # Detector should flag this as significant (injury mention)
        assert result is not None, (
            "Entry with injury mention should be detected as significant"
        )

        # Observer should process and potentially flag injury pattern
        assert isinstance(result.should_update, bool)
        assert isinstance(result.updates, list)

    @pytest.mark.asyncio
    async def test_trigger_post_query_with_fitness_domains(
        self, use_real_ollama: bool, integration_llm_config_path: Path, tmp_path: Path
    ) -> None:
        """Test trigger_post_query with fitness domain guidance (AC: #8).

        Given: Post-query trigger with fitness analysis
        When: Using trigger_post_query helper
        Then: Observer receives combined guidance
        And: Updates are applied to GlobalContext
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        storage = StorageRepository(tmp_path)
        context_manager = GlobalContextManager(storage)

        trigger_config = ObserverTriggerConfig(
            enable_post_query=True,
        )

        active_context = ActiveDomainContext(
            domains_loaded=["GeneralFitness", "Strength"],
            vocabulary={},
            expertise="General fitness and strength expertise.",
            context_guidance=build_combined_fitness_guidance(),
        )

        analysis = AnalyzerOutput(
            query_intent="User wants weekly training summary",
            findings=[
                Finding(
                    claim="User trained 4 days this week",
                    evidence=["Mon: bench", "Wed: squat", "Fri: deadlift", "Sat: OHP"],
                    confidence="high",
                ),
                Finding(
                    claim="PR on squat",
                    evidence=["Squat 315x5 - new PR"],
                    confidence="high",
                ),
            ],
            patterns_identified=["Consistent training schedule"],
            sufficiency_evaluation=SufficiencyEvaluation(
                critical_gaps=[],
                nice_to_have_gaps=[],
                evidence_check_passed=True,
                speculation_risk="none",
            ),
            verdict_reasoning="Found consistent training with PR",
            verdict=Verdict.SUFFICIENT,
        )

        result = await trigger_post_query(
            observer=observer,
            context_manager=context_manager,
            config=trigger_config,
            query="How am I doing this week?",
            analysis=analysis,
            response="Great week! You hit a PR on squat and trained consistently.",
            active_domain_context=active_context,
        )

        # Should have valid result
        assert result is not None
        assert isinstance(result.should_update, bool)

        # If updates were generated, they should be applied
        if result.should_update and result.updates:
            context = context_manager.read_context()
            # Context should have been updated (version incremented)
            assert context.frontmatter.version >= 1
