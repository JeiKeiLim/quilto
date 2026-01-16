# Story 7.1: Implement Observer Agent

Status: done

## Story

As a **Quilto developer**,
I want an **Observer agent that learns patterns from user data**,
so that **the system improves personalization over time**.

## Background

This is the first story in Epic 7 (Learning & Personalization) and implements the Observer agent - one of the two "separate flow" agents (alongside Parser). Unlike the 7 query-flow agents that run during request processing, Observer runs asynchronously to update the global context based on patterns discovered in user data.

**Key Characteristics:**
- **Trigger-based execution:** Runs on post_query, user_correction, or significant_log events
- **Pattern recognition:** Identifies new patterns or changes from recent logs
- **Context updates:** Generates structured updates to the global context markdown
- **Size management:** Consolidates related insights to manage context size (~2k tokens target)
- **Conservative updates:** Prefers high-confidence updates over tentative speculation

**Architecture Context:**
- Observer is agent #9 in the 9-agent roster (7 query flow + Parser + Observer)
- Uses StorageRepository's `get_global_context()` and `update_global_context()` methods (already implemented in Story 2.1)
- Receives domain-specific `context_management_guidance` from DomainModule
- Outputs structured `ContextUpdate` objects that are applied to the global context file

## Acceptance Criteria

1. **Given** recent logs and current global context
   **When** Observer processes them
   **Then** it identifies new patterns or changes
   **And** generates updated global context markdown
   **And** consolidates related insights to manage size

2. **Given** the ObserverInput model
   **When** instantiated
   **Then** it validates all required fields:
   - `trigger`: Literal["post_query", "user_correction", "significant_log"]
   - `current_global_context`: str (existing context content)
   - `context_management_guidance`: str (from domain)
   **And** optional fields based on trigger type:
   - `query`, `analysis`, `response` for post_query
   - `correction`, `what_was_corrected` for user_correction
   - `new_entry` for significant_log

3. **Given** the ContextUpdate model
   **When** instantiated
   **Then** it validates all fields:
   - `category`: Literal["preference", "pattern", "fact", "insight"]
   - `key`: str (e.g., "unit_preference", "typical_schedule")
   - `value`: str
   - `confidence`: Literal["certain", "likely", "tentative"]
   - `source`: str (what triggered this update)

4. **Given** the ObserverOutput model
   **When** instantiated
   **Then** it validates all fields:
   - `should_update`: bool (whether context should be updated)
   - `updates`: list[ContextUpdate] (updates to apply)
   - `insights_captured`: list[str] (what was learned, for logging)

5. **Given** ObserverAgent.observe(input)
   **When** called with ObserverInput
   **Then** it returns ObserverOutput
   **And** calls LLMClient.complete_structured with AGENT_NAME="observer"
   **And** uses the correct model tier (medium-high for pattern recognition)

6. **Given** a post_query trigger with analysis containing patterns
   **When** Observer processes it
   **Then** it identifies patterns revealed during analysis
   **And** captures inferred preferences (e.g., user asked about metric → might prefer tracking that)
   **And** generates updates with appropriate confidence levels

7. **Given** a user_correction trigger
   **When** Observer processes it
   **Then** it treats the correction as explicit user preference
   **And** generates updates with "certain" confidence
   **And** records what was corrected for future reference

8. **Given** a significant_log trigger with a notable entry (e.g., new PR)
   **When** Observer processes it
   **Then** it identifies milestones, new records, or major events
   **And** generates updates with appropriate category ("fact" for records)

9. **Given** Observer with context_management_guidance
   **When** building the prompt
   **Then** guidance is injected into the system prompt
   **And** Observer follows domain-specific pattern tracking instructions

10. **Given** existing global context with related insights
    **When** Observer generates new updates
    **Then** it consolidates related insights rather than duplicating
    **And** updates supersede old values for the same key

## Tasks / Subtasks

- [x] Task 1: Create ObserverInput, ContextUpdate, ObserverOutput models (AC: #2, #3, #4)
  - [x] 1.1: Add models to `packages/quilto/quilto/agents/models.py` under a new `# Observer Models` section comment
  - [x] 1.2: Use `Literal` types (NOT Enums) for trigger, category, confidence - matches existing `severity: Literal["critical", "nice_to_have"]` in Gap model
  - [x] 1.3: Define `ContextUpdate` with:
    - `category: Literal["preference", "pattern", "fact", "insight"]`
    - `key: str = Field(min_length=1)` - REQUIRED per project-context.md
    - `value: str = Field(min_length=1)` - REQUIRED per project-context.md
    - `confidence: Literal["certain", "likely", "tentative"]`
    - `source: str = Field(min_length=1)` - REQUIRED per project-context.md
  - [x] 1.4: Define `ObserverInput` with:
    - `trigger: Literal["post_query", "user_correction", "significant_log"]`
    - `current_global_context: str` (allow empty string for new users)
    - `context_management_guidance: str = Field(min_length=1)` - REQUIRED
    - Optional: `query: str | None = None`, `response: str | None = None`
    - Use `analysis: Any | None = None` and `new_entry: Any | None = None` to avoid circular imports
    - Optional: `correction: str | None = None`, `what_was_corrected: str | None = None`
  - [x] 1.5: Define `ObserverOutput` with:
    - `should_update: bool`
    - `updates: list[ContextUpdate] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]`
    - `insights_captured: list[str] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]`
  - [x] 1.6: Add `@model_validator(mode="after")` to ObserverInput:
    - `post_query` requires: query, analysis, response all non-None
    - `user_correction` requires: correction, what_was_corrected all non-None
    - `significant_log` requires: new_entry non-None
  - [x] 1.7: Use `ConfigDict(strict=True)` for all models
  - [x] 1.8: Add comprehensive docstrings following Gap/Finding patterns in models.py

- [x] Task 2: Create ObserverAgent class (AC: #1, #5)
  - [x] 2.1: Create `packages/quilto/quilto/agents/observer.py`
  - [x] 2.2: Implement `ObserverAgent.__init__(self, llm_client: LLMClient)`
  - [x] 2.3: Set `AGENT_NAME = "observer"` class constant
  - [x] 2.4: Implement `async def observe(self, observer_input: ObserverInput) -> ObserverOutput`
  - [x] 2.5: Add runtime validation: `if not observer_input.context_management_guidance.strip(): raise ValueError("context_management_guidance cannot be empty or whitespace-only")` - follows ClarifierAgent.clarify() pattern
  - [x] 2.6: Call `self.llm_client.complete_structured()` with response_model=ObserverOutput
  - [x] 2.7: Add type assertion after LLM call: `assert isinstance(result, ObserverOutput)` - matches clarifier.py:318

- [x] Task 3: Implement build_prompt method (AC: #9)
  - [x] 3.1: Create `build_prompt(self, observer_input: ObserverInput) -> str`
  - [x] 3.2: Format current global context for prompt
  - [x] 3.3: Format trigger-specific context (query/correction/entry)
  - [x] 3.4: Inject context_management_guidance
  - [x] 3.5: Add rules for conservative updates
  - [x] 3.6: Define output JSON schema matching ObserverOutput

- [x] Task 4: Implement trigger-specific handling (AC: #6, #7, #8)
  - [x] 4.1: Create `_format_post_query_context()` for post_query trigger
  - [x] 4.2: Create `_format_correction_context()` for user_correction trigger
  - [x] 4.3: Create `_format_significant_log_context()` for significant_log trigger
  - [x] 4.4: Include domain-specific pattern recognition based on context_management_guidance

- [x] Task 5: Implement consolidation logic (AC: #10)
  - [x] 5.1: Add guidance in prompt for consolidating related insights
  - [x] 5.2: Add rules for superseding old values with same key
  - [x] 5.3: Add guidance on confidence level transitions (tentative → likely → certain)

- [x] Task 6: Update package exports (AC: all)
  - [x] 6.1: Add imports to `packages/quilto/quilto/agents/__init__.py`:
    - `from quilto.agents.observer import ObserverAgent`
    - `from quilto.agents.models import ContextUpdate, ObserverInput, ObserverOutput` (alphabetical order)
  - [x] 6.2: Add to `__all__` list (alphabetical): `"ContextUpdate"`, `"ObserverAgent"`, `"ObserverInput"`, `"ObserverOutput"`
  - [x] 6.3: Update module docstring to include ObserverAgent description

- [x] Task 7: Create unit tests (AC: #2, #3, #4, #5)
  - [x] 7.1: Create `packages/quilto/tests/test_observer.py` (NOT in agents/ subdirectory - see existing test files)
  - [x] 7.2: Add imports: `from unittest.mock import AsyncMock`, `import pytest`, `from pydantic import ValidationError`
  - [x] 7.3: Create `create_test_config()` helper returning LLMConfig (copy pattern from test_clarifier.py:28-45)
  - [x] 7.4: Create `create_mock_llm_client(response_json)` helper (copy pattern from test_clarifier.py:48-69)
  - [x] 7.5: Test ContextUpdate validation:
    - All Literal values for category: "preference", "pattern", "fact", "insight"
    - All Literal values for confidence: "certain", "likely", "tentative"
    - Empty `key` fails `Field(min_length=1)`
    - Empty `value` fails `Field(min_length=1)`
    - Empty `source` fails `Field(min_length=1)`
  - [x] 7.6: Test ObserverInput validation:
    - All Literal values for trigger: "post_query", "user_correction", "significant_log"
    - Empty `current_global_context` is valid (new user)
    - Empty `context_management_guidance` fails `Field(min_length=1)`
    - Whitespace-only `context_management_guidance` passes Pydantic but fails runtime check
    - `post_query` without query/analysis/response fails model_validator
    - `user_correction` without correction/what_was_corrected fails model_validator
    - `significant_log` without new_entry fails model_validator
  - [x] 7.7: Test ObserverOutput validation:
    - `should_update` accepts True/False
    - `updates` defaults to empty list
    - `insights_captured` defaults to empty list
  - [x] 7.8: Test ObserverAgent.build_prompt() includes all required sections
  - [x] 7.9: Test ObserverAgent.observe() with mock LLMClient returns ObserverOutput
  - [x] 7.10: Test ObserverAgent.observe() raises ValueError for whitespace-only context_management_guidance

- [x] Task 8: Create integration tests (AC: #1, #6, #7, #8)
  - [x] 8.1: Add class `TestObserverIntegration` with docstring explaining how to run
  - [x] 8.2: Use fixtures: `use_real_ollama: bool`, `integration_llm_config_path: Path` (from conftest.py)
  - [x] 8.3: Add skip guard: `if not use_real_ollama: pytest.skip("Requires --use-real-ollama flag")`
  - [x] 8.4: Test post_query trigger with real LLM - verify returns ObserverOutput
  - [x] 8.5: Test user_correction trigger with real LLM - verify confidence is "certain"
  - [x] 8.6: Test significant_log trigger with real LLM - verify identifies facts
  - [x] 8.7: Verify output structure: `should_update` is bool, `updates` is list, `insights_captured` is list

- [x] Task 9: Run validation
  - [x] 9.1: Run `make check` (lint + typecheck)
  - [x] 9.2: Run `make test` (unit tests)
  - [x] 9.3: Run `make test-ollama` (integration tests with real Ollama)

## Dev Notes

### Pattern Reference

Follow the exact pattern established in `clarifier.py`:

```python
"""Observer agent for learning patterns and updating global context.

This module provides the ObserverAgent class which learns patterns
from user data and updates the global context for personalization.
"""

from quilto.agents.models import (
    ContextUpdate,
    ObserverInput,
    ObserverOutput,
)
from quilto.llm import LLMClient


class ObserverAgent:
    """Observer agent for learning patterns and updating global context.

    Runs asynchronously to update the global context based on patterns
    discovered in user data. Triggered by post_query, user_correction,
    or significant_log events.

    Attributes:
        llm_client: The LLM client for making inference calls.

    Example:
        >>> from quilto import LLMClient, load_llm_config
        >>> from quilto.agents import ObserverAgent, ObserverInput
        >>> config = load_llm_config(Path("llm-config.yaml"))
        >>> client = LLMClient(config)
        >>> observer = ObserverAgent(client)
        >>> input = ObserverInput(
        ...     trigger="post_query",
        ...     query="How has my bench press progressed?",
        ...     analysis=analyzer_output,
        ...     response="Your bench press improved by 10 lbs...",
        ...     current_global_context="# Global Context\n...",
        ...     context_management_guidance="Track PRs, workout patterns..."
        ... )
        >>> output = await observer.observe(input)
        >>> if output.should_update:
        ...     print(f"Captured: {output.insights_captured}")
    """

    AGENT_NAME = "observer"

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Observer agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    # ... implementation follows
```

### Key Design Decisions

**Trigger Types:**
| Trigger | When | What Observer Looks For |
|---------|------|------------------------|
| `post_query` | After every query completes | Patterns revealed during analysis, inferred preferences |
| `user_correction` | When user corrects data | Explicit preferences to remember |
| `significant_log` | After parsing notable entries | Milestones, new records, major events |

**Confidence Levels:**
- `certain`: User explicitly stated (corrections, direct preferences)
- `likely`: Strong pattern from multiple data points
- `tentative`: Initial observation, needs reinforcement

**Context Categories:**
- `preference`: User preferences (unit_preference, response_style)
- `pattern`: Behavioral patterns (typical_active_days, usual_time_of_day)
- `fact`: Objective facts (records, current_routine)
- `insight`: Correlations and observations (sleep_performance_correlation)

**Global Context Format:**
```markdown
---
last_updated: 2026-01-16
version: 15
---

# Global Context

## Preferences (certain)
- unit_preference: metric
- response_style: concise

## Patterns (likely)
- typical_active_days: [Monday, Wednesday, Friday]
- usual_time_of_day: morning

## Facts (certain)
- records: {bench_press: 185x5, squat: 225x5}
- current_routine: push-pull-legs

## Insights (tentative)
- Performance tends to drop when sleep is below 7 hours
- Best workouts on Wednesday evenings
```

### Common Mistakes to Avoid

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Missing model_validator for trigger-specific fields | Add validation to ensure query/analysis/response for post_query | agent-system-design.md |
| Using AnalyzerOutput/Entry type directly (circular import) | Use `Any` type annotation with comment: `# AnalyzerOutput at runtime` | models.py line 475 |
| Not handling empty global context | Allow empty string for new users | Practical requirement |
| Overly aggressive updates | Be conservative, prefer tentative for new observations | agent-system-design.md |
| Creating Enums for Literal values | Use `Literal["a", "b"]` directly, NOT new Enum classes | Gap.severity pattern |
| Missing `Field(min_length=1)` on required strings | Always use `Field(min_length=1)` for required string fields | project-context.md |
| Test file in wrong location | Put in `tests/test_observer.py`, NOT `tests/agents/` | existing test structure |
| Missing runtime whitespace check | Add `if not field.strip(): raise ValueError()` in agent method | clarifier.py:293-294 |
| Missing pyright ignore on Field defaults | Add `# pyright: ignore[reportUnknownVariableType]` for list defaults | models.py:775 |

### File Structure

```
packages/quilto/quilto/agents/
├── __init__.py          # Add Observer exports
├── models.py            # Add Observer models (new section at end)
├── router.py
├── planner.py
├── retriever.py
├── analyzer.py
├── synthesizer.py
├── evaluator.py
├── clarifier.py
├── parser.py
└── observer.py          # NEW

packages/quilto/tests/
├── __init__.py
├── conftest.py          # Contains fixtures: use_real_ollama, integration_llm_config_path
├── test_router.py
├── test_planner.py
├── test_retriever.py
├── test_analyzer.py
├── test_synthesizer.py
├── test_evaluator.py
├── test_clarifier.py    # Reference for test patterns
├── test_parser.py
└── test_observer.py     # NEW (NOT in agents/ subdirectory)
```

### Project Structure Notes

- Observer lives in Quilto (domain-agnostic framework), not Swealog
- Uses StorageRepository methods for global context (already implemented)
- Domain-specific guidance comes from DomainModule.context_management_guidance
- Story 7.4 will add fitness-specific context management in Swealog

### Model Implementation Reference

Add to `models.py` after the Clarifier Models section:

```python
# =============================================================================
# Observer Models
# =============================================================================


class ContextUpdate(BaseModel):
    """A single update to global context.

    Attributes:
        category: Update category (preference, pattern, fact, insight).
        key: Unique identifier for this context entry.
        value: The value to store.
        confidence: Confidence level (certain, likely, tentative).
        source: What triggered this update.

    Example:
        >>> update = ContextUpdate(
        ...     category="preference",
        ...     key="unit_preference",
        ...     value="metric",
        ...     confidence="certain",
        ...     source="user_correction: changed lbs to kg"
        ... )
    """

    model_config = ConfigDict(strict=True)

    category: Literal["preference", "pattern", "fact", "insight"]
    key: str = Field(min_length=1)
    value: str = Field(min_length=1)
    confidence: Literal["certain", "likely", "tentative"]
    source: str = Field(min_length=1)


class ObserverInput(BaseModel):
    """Input to Observer agent.

    Attributes:
        trigger: What triggered this observation.
        current_global_context: Current context content (empty for new users).
        context_management_guidance: Domain guidance on what to track.
        query: Query text (required for post_query).
        analysis: AnalyzerOutput (required for post_query). Uses Any to avoid circular import.
        response: Response text (required for post_query).
        correction: Correction text (required for user_correction).
        what_was_corrected: Description of correction (required for user_correction).
        new_entry: Entry object (required for significant_log). Uses Any to avoid circular import.

    Example:
        >>> observer_input = ObserverInput(
        ...     trigger="user_correction",
        ...     current_global_context="# Global Context\n...",
        ...     context_management_guidance="Track PRs, preferences...",
        ...     correction="Actually I ran 5km not 3km",
        ...     what_was_corrected="distance"
        ... )
    """

    model_config = ConfigDict(strict=True)

    trigger: Literal["post_query", "user_correction", "significant_log"]
    current_global_context: str  # Allow empty for new users
    context_management_guidance: str = Field(min_length=1)

    # post_query fields
    query: str | None = None
    analysis: Any | None = None  # AnalyzerOutput at runtime, Any to avoid circular import
    response: str | None = None

    # user_correction fields
    correction: str | None = None
    what_was_corrected: str | None = None

    # significant_log fields
    new_entry: Any | None = None  # Entry at runtime, Any to avoid circular import

    @model_validator(mode="after")
    def validate_trigger_fields(self) -> "ObserverInput":
        """Validate trigger-specific required fields.

        Returns:
            The validated ObserverInput instance.

        Raises:
            ValueError: If required fields for trigger type are missing.
        """
        if self.trigger == "post_query":
            if self.query is None or self.analysis is None or self.response is None:
                raise ValueError("post_query trigger requires query, analysis, and response")
        elif self.trigger == "user_correction":
            if self.correction is None or self.what_was_corrected is None:
                raise ValueError("user_correction trigger requires correction and what_was_corrected")
        elif self.trigger == "significant_log":
            if self.new_entry is None:
                raise ValueError("significant_log trigger requires new_entry")
        return self


class ObserverOutput(BaseModel):
    """Output from Observer agent.

    Attributes:
        should_update: Whether context should be updated.
        updates: List of updates to apply.
        insights_captured: What was learned (for logging).

    Example:
        >>> output = ObserverOutput(
        ...     should_update=True,
        ...     updates=[update1, update2],
        ...     insights_captured=["User prefers metric units"]
        ... )
    """

    model_config = ConfigDict(strict=True)

    should_update: bool
    updates: list[ContextUpdate] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
    insights_captured: list[str] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
```

### References

- [Source: _bmad-output/planning-artifacts/agent-system-design.md:1980-2065] ObserverInput/Output interfaces
- [Source: _bmad-output/planning-artifacts/agent-system-design.md:2412-2466] Observer prompt structure
- [Source: _bmad-output/planning-artifacts/agent-system-design.md:973-998] Observer trigger types and context management
- [Source: _bmad-output/planning-artifacts/epics.md:1006-1019] Story 7.1 acceptance criteria
- [Source: packages/quilto/quilto/agents/clarifier.py] Pattern reference for agent implementation
- [Source: packages/quilto/quilto/agents/models.py:254-276] Gap model - Literal type pattern reference
- [Source: packages/quilto/quilto/agents/models.py:475] Any type for circular import avoidance
- [Source: packages/quilto/quilto/agents/models.py:775] pyright ignore pattern for Field defaults
- [Source: packages/quilto/quilto/storage/repository.py:365-384] get_global_context() and update_global_context() methods
- [Source: packages/quilto/tests/test_clarifier.py:28-69] Test helper patterns (create_test_config, create_mock_llm_client)
- [Source: packages/quilto/tests/test_clarifier.py:959-1025] Integration test pattern with fixtures

### Story Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| 2-1 (done) | Upstream | StorageRepository with get_global_context/update_global_context |
| 1-3 (done) | Upstream | LLMClient abstraction with tiered config |
| 4-1 (done) | Pattern reference | AnalyzerOutput used in post_query trigger |
| 5-3 (done) | Pattern reference | Correction flow patterns for user_correction trigger |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- All 10 acceptance criteria implemented and tested
- 50 unit tests pass, 3 integration tests pass with real Ollama
- ObserverAgent follows ClarifierAgent pattern with build_prompt, trigger-specific formatting
- Models use Literal types (not Enums) per project conventions
- Context consolidation rules and confidence level guidance in prompt

### Code Review Fixes Applied

- Removed unnecessary `r` prefix from docstrings in `observer.py:15` and `models.py:938`
- Added test for whitespace-only guidance passing Pydantic (proves runtime check is needed)
- Added test for invalid trigger value validation
- Strengthened integration test for user_correction to always assert updates with "certain" confidence

### File List

- `packages/quilto/quilto/agents/models.py` - Added ContextUpdate, ObserverInput, ObserverOutput models (lines 902-1020)
- `packages/quilto/quilto/agents/observer.py` - NEW: ObserverAgent class with observe(), build_prompt(), trigger handlers
- `packages/quilto/quilto/agents/__init__.py` - Added Observer exports and updated docstring
- `packages/quilto/tests/test_observer.py` - NEW: 50 unit tests + 3 integration tests
