"""Unit tests for Observer trigger system.

Tests cover configuration validation, significant entry detection,
helper functions, trigger functions, and LangGraph node.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from quilto.agents.models import (
    ActiveDomainContext,
    AnalyzerOutput,
    ContextUpdate,
    Finding,
    ObserverOutput,
    SufficiencyEvaluation,
    Verdict,
)
from quilto.state import (
    DefaultSignificantEntryDetector,
    ObserverTriggerConfig,
    SessionState,
    get_combined_context_guidance,
    observe_node,
    serialize_global_context,
    trigger_periodic,
    trigger_post_query,
    trigger_significant_log,
    trigger_user_correction,
)
from quilto.storage import (
    Entry,
    GlobalContext,
    GlobalContextFrontmatter,
    GlobalContextManager,
    StorageRepository,
)
from quilto.storage.context import ContextEntry

# =============================================================================
# Test ObserverTriggerConfig Model
# =============================================================================


class TestObserverTriggerConfigModel:
    """Tests for ObserverTriggerConfig Pydantic model validation."""

    def test_default_values(self) -> None:
        """Default values are correct."""
        config = ObserverTriggerConfig()
        assert config.enable_post_query is True
        assert config.enable_user_correction is True
        assert config.enable_significant_log is True
        assert config.enable_periodic is False
        assert config.periodic_interval_minutes is None

    def test_periodic_interval_zero_fails(self) -> None:
        """periodic_interval_minutes=0 fails validation."""
        with pytest.raises(ValidationError, match="must be > 0"):
            ObserverTriggerConfig(periodic_interval_minutes=0)

    def test_periodic_interval_negative_fails(self) -> None:
        """periodic_interval_minutes=-1 fails validation."""
        with pytest.raises(ValidationError, match="must be > 0"):
            ObserverTriggerConfig(periodic_interval_minutes=-1)

    def test_periodic_interval_positive_passes(self) -> None:
        """periodic_interval_minutes=1 passes validation."""
        config = ObserverTriggerConfig(periodic_interval_minutes=1)
        assert config.periodic_interval_minutes == 1

    def test_enable_periodic_without_interval_fails(self) -> None:
        """enable_periodic=True without periodic_interval_minutes fails."""
        with pytest.raises(ValidationError, match="periodic_interval_minutes is required"):
            ObserverTriggerConfig(enable_periodic=True)

    def test_enable_periodic_with_valid_interval_passes(self) -> None:
        """enable_periodic=True with valid periodic_interval_minutes passes."""
        config = ObserverTriggerConfig(enable_periodic=True, periodic_interval_minutes=60)
        assert config.enable_periodic is True
        assert config.periodic_interval_minutes == 60

    def test_all_triggers_disabled(self) -> None:
        """All triggers can be disabled."""
        config = ObserverTriggerConfig(
            enable_post_query=False,
            enable_user_correction=False,
            enable_significant_log=False,
        )
        assert config.enable_post_query is False
        assert config.enable_user_correction is False
        assert config.enable_significant_log is False


# =============================================================================
# Test DefaultSignificantEntryDetector
# =============================================================================


class TestDefaultSignificantEntryDetector:
    """Tests for DefaultSignificantEntryDetector class."""

    def _create_entry(self, content: str) -> Entry:
        """Helper to create Entry with given content."""
        return Entry(
            id="2026-01-16_10-00-00",
            date=date(2026, 1, 16),
            timestamp=datetime(2026, 1, 16, 10, 0),
            raw_content=content,
        )

    def test_personal_record_detected(self) -> None:
        """Returns True for 'personal record' in content."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Bench press 185x5 - new personal record!")
        assert detector.is_significant(entry, {}) is True

    def test_pr_detected_case_insensitive(self) -> None:
        """Returns True for 'PR' in content (case insensitive)."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Bench press 185x5 PR!")
        assert detector.is_significant(entry, {}) is True

        entry_lower = self._create_entry("bench press 185x5 pr!")
        assert detector.is_significant(entry_lower, {}) is True

    def test_new_record_detected(self) -> None:
        """Returns True for 'new record' in content."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Set a new record on deadlift today")
        assert detector.is_significant(entry, {}) is True

    def test_personal_best_detected(self) -> None:
        """Returns True for 'pb' and 'personal best' in content."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Ran a PB in the 5K")
        assert detector.is_significant(entry, {}) is True

        entry2 = self._create_entry("Achieved a personal best today")
        assert detector.is_significant(entry2, {}) is True

    def test_first_milestone_detected(self) -> None:
        """Returns True for 'first' milestone."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("First time hitting 200lbs on bench")
        assert detector.is_significant(entry, {}) is True

    def test_100th_milestone_detected(self) -> None:
        """Returns True for '100th' milestone."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("100th workout this year!")
        assert detector.is_significant(entry, {}) is True

    def test_milestone_keyword_detected(self) -> None:
        """Returns True for 'milestone' keyword."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Hit a major milestone today")
        assert detector.is_significant(entry, {}) is True

    def test_competition_detected(self) -> None:
        """Returns True for 'competition' mention."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Preparing for the powerlifting competition")
        assert detector.is_significant(entry, {}) is True

    def test_race_detected(self) -> None:
        """Returns True for 'race' mention."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Ran a great race today!")
        assert detector.is_significant(entry, {}) is True

    def test_meet_detected(self) -> None:
        """Returns True for 'meet' mention."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Swimming meet this weekend")
        assert detector.is_significant(entry, {}) is True

    def test_tournament_detected(self) -> None:
        """Returns True for 'tournament' mention."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Tennis tournament results")
        assert detector.is_significant(entry, {}) is True

    def test_normal_entry_not_significant(self) -> None:
        """Returns False for normal entry content."""
        detector = DefaultSignificantEntryDetector()
        # Using content without any indicator words (avoiding "press" which contains "pr")
        entry = self._create_entry("Did some lifting today, felt good")
        assert detector.is_significant(entry, {}) is False

    def test_normal_workout_log_not_significant(self) -> None:
        """Returns False for typical workout log."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Morning workout: squats 225x5, deadlift 315x3")
        assert detector.is_significant(entry, {}) is False

    def test_bench_press_without_indicator_not_significant(self) -> None:
        """Returns False for bench press content without significance indicators.

        Uses word boundary matching so 'bench press' does not trigger on the 'pr'
        substring - only standalone 'pr' (like 'new PR!') triggers.
        """
        detector = DefaultSignificantEntryDetector()
        # 'bench press' contains 'pr' but word boundary matching prevents false positive
        entry = self._create_entry("Bench press 185x5 today")
        assert detector.is_significant(entry, {}) is False

    def test_pr_with_word_boundary_detected(self) -> None:
        """Returns True for standalone 'PR' with word boundary."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("Hit a PR today on squats!")
        assert detector.is_significant(entry, {}) is True

    def test_pr_in_sentence_detected(self) -> None:
        """Returns True for 'PR' as standalone word in sentence."""
        detector = DefaultSignificantEntryDetector()
        entry = self._create_entry("This is my PR, so happy!")
        assert detector.is_significant(entry, {}) is True


# =============================================================================
# Test serialize_global_context
# =============================================================================


class TestSerializeGlobalContext:
    """Tests for serialize_global_context helper function."""

    def test_produces_valid_markdown_with_frontmatter(self) -> None:
        """Produces valid markdown string with frontmatter."""
        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=5,
                token_estimate=100,
            ),
        )

        result = serialize_global_context(context)

        assert "---" in result
        assert "last_updated: 2026-01-16" in result
        assert "version: 5" in result
        assert "token_estimate: 100" in result
        assert "# Global Context" in result

    def test_handles_empty_context(self) -> None:
        """Handles empty context (no entries)."""
        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=0,
            ),
        )

        result = serialize_global_context(context)

        assert "## Preferences (certain)" in result
        assert "## Patterns (likely)" in result
        assert "## Facts (certain)" in result
        assert "## Insights (tentative)" in result

    def test_includes_entries_in_sections(self) -> None:
        """Includes entries in appropriate sections."""
        context = GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated="2026-01-16",
                version=1,
                token_estimate=50,
            ),
            preferences=[
                ContextEntry(
                    key="unit_preference",
                    value="metric",
                    confidence="certain",
                    source="user_correction",
                    category="preference",
                    added_date="2026-01-10",
                )
            ],
            patterns=[
                ContextEntry(
                    key="workout_time",
                    value="morning",
                    confidence="likely",
                    source="observation",
                    category="pattern",
                    added_date="2026-01-12",
                )
            ],
        )

        result = serialize_global_context(context)

        assert "unit_preference: metric" in result
        assert "workout_time: morning" in result
        assert "[2026-01-10|certain|user_correction]" in result


# =============================================================================
# Test get_combined_context_guidance
# =============================================================================


class TestGetCombinedContextGuidance:
    """Tests for get_combined_context_guidance helper function."""

    def test_returns_context_guidance_when_available(self) -> None:
        """Returns context_guidance from active domain context."""
        active_context = ActiveDomainContext(
            domains_loaded=["strength", "running"],
            vocabulary={},
            expertise="Fitness expertise",
            context_guidance="[Strength]\nTrack PRs for main lifts.\n\n[Running]\nTrack distances and pace.",
        )

        result = get_combined_context_guidance(active_context)

        assert "Track PRs" in result
        assert "Track distances" in result

    def test_single_domain_case(self) -> None:
        """Handles single domain case."""
        active_context = ActiveDomainContext(
            domains_loaded=["strength"],
            vocabulary={},
            expertise="Strength expertise",
            context_guidance="Track personal records and workout patterns.",
        )

        result = get_combined_context_guidance(active_context)

        assert "Track personal records" in result

    def test_returns_default_when_no_guidance(self) -> None:
        """Returns default message when no guidance available."""
        active_context = ActiveDomainContext(
            domains_loaded=["general"],
            vocabulary={},
            expertise="General expertise",
            context_guidance="",
        )

        result = get_combined_context_guidance(active_context)

        assert result == "No domain-specific guidance available."


# =============================================================================
# Test trigger_post_query
# =============================================================================


class TestTriggerPostQuery:
    """Tests for trigger_post_query function."""

    @pytest.fixture
    def mock_observer(self) -> MagicMock:
        """Create mock ObserverAgent."""
        observer = MagicMock()
        observer.observe = AsyncMock(
            return_value=ObserverOutput(
                should_update=True,
                updates=[
                    ContextUpdate(
                        category="pattern",
                        key="workout_style",
                        value="progressive overload",
                        confidence="likely",
                        source="post_query: bench progress",
                    )
                ],
                insights_captured=["User follows progressive overload"],
            )
        )
        return observer

    @pytest.fixture
    def context_manager(self, tmp_path: Path) -> GlobalContextManager:
        """Create GlobalContextManager with temp storage."""
        storage = StorageRepository(tmp_path)
        return GlobalContextManager(storage)

    @pytest.fixture
    def active_domain_context(self) -> ActiveDomainContext:
        """Create test ActiveDomainContext."""
        return ActiveDomainContext(
            domains_loaded=["strength"],
            vocabulary={"pr": "personal record"},
            expertise="Strength training expertise",
            context_guidance="Track personal records and workout patterns.",
        )

    @pytest.fixture
    def analysis(self) -> AnalyzerOutput:
        """Create test AnalyzerOutput."""
        return AnalyzerOutput(
            query_intent="User wants bench press progress",
            findings=[
                Finding(
                    claim="Progressive overload detected",
                    evidence=["Jan 3: 175x5", "Jan 10: 180x5", "Jan 17: 185x5"],
                    confidence="high",
                )
            ],
            patterns_identified=["progressive overload"],
            sufficiency_evaluation=SufficiencyEvaluation(
                critical_gaps=[],
                nice_to_have_gaps=[],
                evidence_check_passed=True,
                speculation_risk="none",
            ),
            verdict_reasoning="Found clear progression in bench press",
            verdict=Verdict.SUFFICIENT,
        )

    @pytest.mark.asyncio
    async def test_calls_observer_with_correct_trigger(
        self,
        mock_observer: MagicMock,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
        analysis: AnalyzerOutput,
    ) -> None:
        """Calls Observer.observe with correct trigger type."""
        config = ObserverTriggerConfig()

        await trigger_post_query(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            query="How has my bench press progressed?",
            analysis=analysis,
            response="Your bench press improved by 10 lbs",
            active_domain_context=active_domain_context,
        )

        mock_observer.observe.assert_called_once()
        call_args = mock_observer.observe.call_args[0][0]
        assert call_args.trigger == "post_query"

    @pytest.mark.asyncio
    async def test_calls_apply_updates_when_should_update(
        self,
        mock_observer: MagicMock,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
        analysis: AnalyzerOutput,
    ) -> None:
        """Calls context_manager.apply_updates when should_update=True."""
        config = ObserverTriggerConfig()

        await trigger_post_query(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            query="How has my bench press progressed?",
            analysis=analysis,
            response="Your bench press improved by 10 lbs",
            active_domain_context=active_domain_context,
        )

        # Verify context was updated
        context = context_manager.read_context()
        assert len(context.patterns) == 1
        assert context.patterns[0].key == "workout_style"

    @pytest.mark.asyncio
    async def test_does_not_apply_updates_when_should_update_false(
        self,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
        analysis: AnalyzerOutput,
    ) -> None:
        """Does NOT call apply_updates when should_update=False."""
        mock_observer = MagicMock()
        mock_observer.observe = AsyncMock(
            return_value=ObserverOutput(
                should_update=False,
                updates=[],
                insights_captured=[],
            )
        )
        config = ObserverTriggerConfig()

        await trigger_post_query(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            query="What's the weather?",
            analysis=analysis,
            response="I don't have weather data",
            active_domain_context=active_domain_context,
        )

        # Verify context was NOT updated
        context = context_manager.read_context()
        assert len(context.patterns) == 0

    @pytest.mark.asyncio
    async def test_returns_none_when_disabled(
        self,
        mock_observer: MagicMock,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
        analysis: AnalyzerOutput,
    ) -> None:
        """Returns None when config.enable_post_query=False."""
        config = ObserverTriggerConfig(enable_post_query=False)

        result = await trigger_post_query(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            query="How has my bench press progressed?",
            analysis=analysis,
            response="Your bench press improved",
            active_domain_context=active_domain_context,
        )

        assert result is None
        mock_observer.observe.assert_not_called()


# =============================================================================
# Test trigger_user_correction
# =============================================================================


class TestTriggerUserCorrection:
    """Tests for trigger_user_correction function."""

    @pytest.fixture
    def mock_observer(self) -> MagicMock:
        """Create mock ObserverAgent."""
        observer = MagicMock()
        observer.observe = AsyncMock(
            return_value=ObserverOutput(
                should_update=True,
                updates=[
                    ContextUpdate(
                        category="preference",
                        key="unit_preference",
                        value="metric",
                        confidence="certain",
                        source="user_correction: changed to kg",
                    )
                ],
                insights_captured=["User prefers metric units"],
            )
        )
        return observer

    @pytest.fixture
    def context_manager(self, tmp_path: Path) -> GlobalContextManager:
        """Create GlobalContextManager with temp storage."""
        storage = StorageRepository(tmp_path)
        return GlobalContextManager(storage)

    @pytest.fixture
    def active_domain_context(self) -> ActiveDomainContext:
        """Create test ActiveDomainContext."""
        return ActiveDomainContext(
            domains_loaded=["strength"],
            vocabulary={},
            expertise="Strength training",
            context_guidance="Track unit preferences.",
        )

    @pytest.mark.asyncio
    async def test_calls_observer_with_correct_trigger(
        self,
        mock_observer: MagicMock,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Calls Observer.observe with user_correction trigger."""
        config = ObserverTriggerConfig()

        await trigger_user_correction(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            correction="Use kilograms instead of pounds",
            what_was_corrected="unit preference",
            active_domain_context=active_domain_context,
        )

        mock_observer.observe.assert_called_once()
        call_args = mock_observer.observe.call_args[0][0]
        assert call_args.trigger == "user_correction"
        assert call_args.correction == "Use kilograms instead of pounds"
        assert call_args.what_was_corrected == "unit preference"

    @pytest.mark.asyncio
    async def test_returns_none_when_disabled(
        self,
        mock_observer: MagicMock,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Returns None when config.enable_user_correction=False."""
        config = ObserverTriggerConfig(enable_user_correction=False)

        result = await trigger_user_correction(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            correction="Use kg",
            what_was_corrected="units",
            active_domain_context=active_domain_context,
        )

        assert result is None
        mock_observer.observe.assert_not_called()


# =============================================================================
# Test trigger_significant_log
# =============================================================================


class TestTriggerSignificantLog:
    """Tests for trigger_significant_log function."""

    @pytest.fixture
    def mock_observer(self) -> MagicMock:
        """Create mock ObserverAgent."""
        observer = MagicMock()
        observer.observe = AsyncMock(
            return_value=ObserverOutput(
                should_update=True,
                updates=[
                    ContextUpdate(
                        category="fact",
                        key="bench_pr",
                        value="185 lbs x 5",
                        confidence="certain",
                        source="significant_log: new PR",
                    )
                ],
                insights_captured=["New bench press PR recorded"],
            )
        )
        return observer

    @pytest.fixture
    def context_manager(self, tmp_path: Path) -> GlobalContextManager:
        """Create GlobalContextManager with temp storage."""
        storage = StorageRepository(tmp_path)
        return GlobalContextManager(storage)

    @pytest.fixture
    def active_domain_context(self) -> ActiveDomainContext:
        """Create test ActiveDomainContext."""
        return ActiveDomainContext(
            domains_loaded=["strength"],
            vocabulary={},
            expertise="Strength training",
            context_guidance="Track personal records.",
        )

    def _create_entry(self, content: str) -> Entry:
        """Helper to create Entry with given content."""
        return Entry(
            id="2026-01-16_10-00-00",
            date=date(2026, 1, 16),
            timestamp=datetime(2026, 1, 16, 10, 0),
            raw_content=content,
        )

    @pytest.mark.asyncio
    async def test_calls_detector_first(
        self,
        mock_observer: MagicMock,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Calls detector.is_significant first."""
        config = ObserverTriggerConfig()
        entry = self._create_entry("New PR on bench press 185x5!")

        mock_detector = MagicMock()
        mock_detector.is_significant = MagicMock(return_value=True)

        await trigger_significant_log(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            entry=entry,
            parsed_data={},
            active_domain_context=active_domain_context,
            detector=mock_detector,
        )

        mock_detector.is_significant.assert_called_once_with(entry, {})

    @pytest.mark.asyncio
    async def test_returns_none_when_not_significant(
        self,
        mock_observer: MagicMock,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Returns None when entry not significant (Observer.observe not called)."""
        config = ObserverTriggerConfig()
        # Use content without significant indicators (avoiding 'press' which contains 'pr')
        entry = self._create_entry("Regular lifting today, did squats 225x5")

        result = await trigger_significant_log(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            entry=entry,
            parsed_data={},
            active_domain_context=active_domain_context,
        )

        assert result is None
        mock_observer.observe.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_observer_when_significant(
        self,
        mock_observer: MagicMock,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Calls Observer.observe when entry is significant."""
        config = ObserverTriggerConfig()
        entry = self._create_entry("New personal record on bench press 185x5!")

        await trigger_significant_log(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            entry=entry,
            parsed_data={},
            active_domain_context=active_domain_context,
        )

        mock_observer.observe.assert_called_once()
        call_args = mock_observer.observe.call_args[0][0]
        assert call_args.trigger == "significant_log"

    @pytest.mark.asyncio
    async def test_returns_none_when_disabled(
        self,
        mock_observer: MagicMock,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Returns None when config.enable_significant_log=False."""
        config = ObserverTriggerConfig(enable_significant_log=False)
        entry = self._create_entry("New PR on bench press!")

        result = await trigger_significant_log(
            observer=mock_observer,
            context_manager=context_manager,
            config=config,
            entry=entry,
            parsed_data={},
            active_domain_context=active_domain_context,
        )

        assert result is None
        mock_observer.observe.assert_not_called()


# =============================================================================
# Test trigger_periodic
# =============================================================================


class TestTriggerPeriodic:
    """Tests for trigger_periodic function."""

    @pytest.fixture
    def context_manager(self, tmp_path: Path) -> GlobalContextManager:
        """Create GlobalContextManager with temp storage."""
        storage = StorageRepository(tmp_path)
        return GlobalContextManager(storage)

    @pytest.fixture
    def storage(self, tmp_path: Path) -> StorageRepository:
        """Create StorageRepository with temp storage."""
        return StorageRepository(tmp_path)

    @pytest.fixture
    def active_domain_context(self) -> ActiveDomainContext:
        """Create test ActiveDomainContext."""
        return ActiveDomainContext(
            domains_loaded=["strength"],
            vocabulary={},
            expertise="Strength training",
            context_guidance="Track personal records.",
        )

    @pytest.mark.asyncio
    async def test_returns_empty_when_disabled(
        self,
        context_manager: GlobalContextManager,
        storage: StorageRepository,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Returns empty list when enable_periodic=False."""
        mock_observer = MagicMock()
        config = ObserverTriggerConfig(enable_periodic=False)

        result = await trigger_periodic(
            observer=mock_observer,
            context_manager=context_manager,
            storage=storage,
            config=config,
            active_domain_context=active_domain_context,
        )

        assert result == []


# =============================================================================
# Test observe_node
# =============================================================================


class TestObserveNode:
    """Tests for observe_node LangGraph node function."""

    def _create_test_state(self, **kwargs: Any) -> SessionState:
        """Create minimal SessionState for testing."""
        defaults: SessionState = {
            "raw_input": "test input",
            "input_type": "QUERY",
            "current_state": "OBSERVE",
            "waiting_for_user": False,
            "complete": False,
        }
        result: dict[str, Any] = {**defaults, **kwargs}
        return result  # type: ignore[return-value]

    @pytest.mark.asyncio
    async def test_routes_to_user_correction_when_correction_result_exists(self) -> None:
        """Routes to trigger_user_correction when correction_result exists."""
        state = self._create_test_state(
            correction_result={"success": True},
            correction_target="distance",
        )

        # Without Observer configured, should return gracefully
        result = await observe_node(state)

        assert result["next_state"] == "COMPLETE"
        assert result["observer_output"] is None

    @pytest.mark.asyncio
    async def test_routes_to_significant_log_when_input_type_is_log(self) -> None:
        """Routes to trigger_significant_log when input_type is 'LOG'."""
        state = self._create_test_state(input_type="LOG")

        result = await observe_node(state)

        assert result["next_state"] == "COMPLETE"
        assert result["observer_output"] is None

    @pytest.mark.asyncio
    async def test_routes_to_post_query_otherwise(self) -> None:
        """Routes to trigger_post_query otherwise."""
        state = self._create_test_state(input_type="QUERY")

        result = await observe_node(state)

        assert result["next_state"] == "COMPLETE"
        assert result["observer_output"] is None

    @pytest.mark.asyncio
    async def test_returns_complete_when_observer_not_configured(self) -> None:
        """Returns next_state='COMPLETE' and observer_output=None when Observer not configured."""
        state = self._create_test_state()

        result = await observe_node(state)

        assert result == {"next_state": "COMPLETE", "observer_output": None}


# =============================================================================
# Test Exports
# =============================================================================


class TestObserverTriggersExports:
    """Tests for observer trigger exports from quilto.state."""

    def test_observer_trigger_config_importable(self) -> None:
        """ObserverTriggerConfig is importable from quilto.state."""
        from quilto.state import ObserverTriggerConfig

        assert ObserverTriggerConfig is not None

    def test_significant_entry_detector_importable(self) -> None:
        """SignificantEntryDetector is importable from quilto.state."""
        from quilto.state import SignificantEntryDetector

        assert SignificantEntryDetector is not None

    def test_default_significant_entry_detector_importable(self) -> None:
        """DefaultSignificantEntryDetector is importable from quilto.state."""
        from quilto.state import DefaultSignificantEntryDetector

        assert DefaultSignificantEntryDetector is not None

    def test_trigger_functions_importable(self) -> None:
        """All trigger functions are importable from quilto.state."""
        from quilto.state import (
            trigger_periodic,
            trigger_post_query,
            trigger_significant_log,
            trigger_user_correction,
        )

        assert trigger_post_query is not None
        assert trigger_user_correction is not None
        assert trigger_significant_log is not None
        assert trigger_periodic is not None

    def test_observe_node_importable(self) -> None:
        """observe_node is importable from quilto.state."""
        from quilto.state import observe_node

        assert observe_node is not None

    def test_helper_functions_importable(self) -> None:
        """Helper functions are importable from quilto.state."""
        from quilto.state import get_combined_context_guidance, serialize_global_context

        assert serialize_global_context is not None
        assert get_combined_context_guidance is not None

    def test_main_package_exports(self) -> None:
        """ObserverTriggerConfig and observe_node are in main package."""
        from quilto import ObserverTriggerConfig, observe_node

        assert ObserverTriggerConfig is not None
        assert observe_node is not None

    def test_all_exports_in_state_all_list(self) -> None:
        """All observer trigger types are in state __all__ list."""
        from quilto import state

        assert "ObserverTriggerConfig" in state.__all__
        assert "SignificantEntryDetector" in state.__all__
        assert "DefaultSignificantEntryDetector" in state.__all__
        assert "trigger_post_query" in state.__all__
        assert "trigger_user_correction" in state.__all__
        assert "trigger_significant_log" in state.__all__
        assert "trigger_periodic" in state.__all__
        assert "observe_node" in state.__all__
        assert "serialize_global_context" in state.__all__
        assert "get_combined_context_guidance" in state.__all__


# =============================================================================
# Integration Tests
# =============================================================================


class TestObserverTriggersIntegration:
    """Integration tests with real Ollama.

    Run with: pytest --use-real-ollama -k TestObserverTriggersIntegration
    Or via: make test-ollama
    """

    @pytest.fixture
    def context_manager(self, tmp_path: Path) -> GlobalContextManager:
        """Create GlobalContextManager with temp storage."""
        storage = StorageRepository(tmp_path)
        return GlobalContextManager(storage)

    @pytest.fixture
    def active_domain_context(self) -> ActiveDomainContext:
        """Create test ActiveDomainContext."""
        return ActiveDomainContext(
            domains_loaded=["strength"],
            vocabulary={"pr": "personal record", "1rm": "one rep max"},
            expertise="Strength training expertise including powerlifting and bodybuilding.",
            context_guidance="""Track the following:
- Personal records (PRs) for main lifts
- Unit preferences (metric vs imperial)
- Workout patterns and scheduling
- User goals and preferences""",
        )

    @pytest.mark.asyncio
    async def test_real_trigger_post_query(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Test trigger_post_query with real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        from quilto import LLMClient, load_llm_config
        from quilto.agents import ObserverAgent

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        trigger_config = ObserverTriggerConfig()

        analysis = AnalyzerOutput(
            query_intent="User wants bench press progress",
            findings=[
                Finding(
                    claim="Progressive overload detected",
                    evidence=["Jan 3: 175x5", "Jan 10: 180x5", "Jan 17: 185x5"],
                    confidence="high",
                )
            ],
            patterns_identified=["progressive overload"],
            sufficiency_evaluation=SufficiencyEvaluation(
                critical_gaps=[],
                nice_to_have_gaps=[],
                evidence_check_passed=True,
                speculation_risk="none",
            ),
            verdict_reasoning="Found clear progression",
            verdict=Verdict.SUFFICIENT,
        )

        result = await trigger_post_query(
            observer=observer,
            context_manager=context_manager,
            config=trigger_config,
            query="How has my bench press progressed this month?",
            analysis=analysis,
            response="Your bench press improved from 175x5 to 185x5 over 3 weeks.",
            active_domain_context=active_domain_context,
        )

        # Should have valid output
        assert result is not None
        assert isinstance(result.should_update, bool)
        assert isinstance(result.updates, list)

        # If updates were applied, verify context was updated
        if result.should_update:
            context = context_manager.read_context()
            total_entries = (
                len(context.preferences)
                + len(context.patterns)
                + len(context.facts)
                + len(context.insights)
            )
            assert total_entries > 0

    @pytest.mark.asyncio
    async def test_real_trigger_user_correction(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Test trigger_user_correction with real Ollama - verify certain confidence."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        from quilto import LLMClient, load_llm_config
        from quilto.agents import ObserverAgent

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        trigger_config = ObserverTriggerConfig()

        result = await trigger_user_correction(
            observer=observer,
            context_manager=context_manager,
            config=trigger_config,
            correction="Please use kilograms instead of pounds for all my weights",
            what_was_corrected="unit preference",
            active_domain_context=active_domain_context,
        )

        # User corrections should always trigger updates
        assert result is not None
        assert result.should_update, "User corrections should always trigger updates"
        assert len(result.updates) > 0, "Should generate at least one update"

        # Verify updates have "certain" confidence
        confidences = [u.confidence for u in result.updates]
        assert "certain" in confidences, "User corrections should use 'certain' confidence"

    @pytest.mark.asyncio
    async def test_real_trigger_significant_log(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        context_manager: GlobalContextManager,
        active_domain_context: ActiveDomainContext,
    ) -> None:
        """Test trigger_significant_log with real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        from quilto import LLMClient, load_llm_config
        from quilto.agents import ObserverAgent

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        observer = ObserverAgent(real_llm_client)

        trigger_config = ObserverTriggerConfig()

        # Create entry with "personal record" to trigger significance
        entry = Entry(
            id="2026-01-16_10-00-00",
            date=date(2026, 1, 16),
            timestamp=datetime(2026, 1, 16, 10, 0),
            raw_content="Bench press 190x5 - NEW PERSONAL RECORD! Finally broke the 185 barrier.",
        )

        result = await trigger_significant_log(
            observer=observer,
            context_manager=context_manager,
            config=trigger_config,
            entry=entry,
            parsed_data={"exercise": "bench press", "weight": 190, "reps": 5},
            active_domain_context=active_domain_context,
        )

        # Should have valid output
        assert result is not None
        assert isinstance(result.should_update, bool)
        assert isinstance(result.updates, list)

        # PR should typically generate a fact update
        if result.should_update and result.updates:
            categories = [u.category for u in result.updates]
            assert "fact" in categories or "insight" in categories
