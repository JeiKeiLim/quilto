# Story 2.2: Implement Router Agent (LOG Classification)

Status: done

## Story

As a **Quilto developer**,
I want a **Router agent that classifies input as LOG/QUERY/BOTH/CORRECTION**,
So that **input flows to the correct processing path**.

## Acceptance Criteria

1. **Given** raw user input containing a declarative statement
   **When** Router processes it
   **Then** it returns `input_type: LOG` with confidence score >= 0.7
   **And** declarative statements recording activities, events, or observations are classified as LOG

2. **Given** raw user input containing question words (why, how, what, when, which) or question marks
   **When** Router processes it
   **Then** it returns `input_type: QUERY` with confidence score >= 0.7
   **And** questions seeking information, insights, or recommendations are classified as QUERY

3. **Given** raw user input that contains BOTH logging AND questioning
   **When** Router processes it
   **Then** it returns `input_type: BOTH`
   **And** `log_portion` contains the declarative statement portion
   **And** `query_portion` contains the question portion
   **And** both portions are correctly extracted from the original input

4. **Given** raw user input with correction language ("actually", "I meant", "that was wrong")
   **When** Router processes it
   **Then** it returns `input_type: CORRECTION`
   **And** `correction_target` identifies what's being corrected (natural language hint)

5. **Given** raw user input and a list of available domains
   **When** Router processes it
   **Then** it returns `selected_domains` matching input against domain descriptions
   **And** `domain_selection_reasoning` explains the selection
   **And** when uncertain, broader selection is preferred over missing relevant domains

6. **Given** Router is configured with model tier "low"
   **When** an LLM call is made
   **Then** the correct low-tier model is used via LLMClient

7. **Given** raw user input that is empty or whitespace-only
   **When** Router.classify() is called
   **Then** it raises `ValueError` with descriptive message
   **And** no LLM call is made

8. **Given** a RouterOutput with input_type BOTH
   **When** log_portion or query_portion is None/empty
   **Then** Pydantic model validation raises `ValueError`

9. **Given** a RouterOutput with input_type CORRECTION
   **When** correction_target is None/empty
   **Then** Pydantic model validation raises `ValueError`

## Tasks / Subtasks

- [x] Task 1: Create agents module structure (AC: #6)
  - [x] Create `packages/quilto/quilto/agents/` directory
  - [x] Create `__init__.py` with exports
  - [x] Create `router.py` for RouterAgent class
  - [x] Create `models.py` for shared agent types (InputType, DomainInfo, etc.)

- [x] Task 2: Define Router input/output models (AC: #1-5, #8, #9)
  - [x] Define `InputType` enum: LOG, QUERY, BOTH, CORRECTION
  - [x] Define `DomainInfo` model with name and description (for domain selection)
  - [x] Define `RouterInput` with raw_input, session_context, available_domains
  - [x] Define `RouterOutput` with input_type, confidence, selected_domains, domain_selection_reasoning, log_portion, query_portion, correction_target, reasoning
  - [x] Add strict Pydantic validation with `ConfigDict(strict=True)`
  - [x] Add `@model_validator` for RouterOutput to validate BOTH requires portions (AC: #8) and CORRECTION requires target (AC: #9)

- [x] Task 3: Implement RouterAgent class (AC: #1-7)
  - [x] Accept `llm_client: LLMClient` in constructor
  - [x] Implement `async classify(input: RouterInput) -> RouterOutput`
  - [x] Add validation for empty/whitespace raw_input at start of classify() (AC: #7)
  - [x] Build system prompt with classification rules and domain selection instructions
  - [x] Use `llm_client.complete_structured()` with RouterOutput schema
  - [x] Agent name should be "router" for tier resolution

- [x] Task 4: Implement classification prompt (AC: #1-4)
  - [x] Embed classification rules in system prompt
  - [x] Handle question word detection (why, how, what, when, which)
  - [x] Handle question mark detection
  - [x] Handle correction language detection
  - [x] Handle BOTH input type with portion extraction

- [x] Task 5: Implement domain selection logic (AC: #5)
  - [x] Format available domains with descriptions for LLM
  - [x] Include selection rules: match keywords/topics against descriptions
  - [x] Instruct LLM to prefer broader selection when uncertain

- [x] Task 6: Add comprehensive tests (AC: #1-9)
  - [x] Test LOG classification (declarative statements) (AC: #1)
  - [x] Test QUERY classification (questions, question marks) (AC: #2)
  - [x] Test BOTH classification with portion extraction (AC: #3)
  - [x] Test CORRECTION classification with target extraction (AC: #4)
  - [x] Test domain selection with single domain match (AC: #5)
  - [x] Test domain selection with multiple domain match (AC: #5)
  - [x] Test domain selection with empty available_domains list (AC: #5)
  - [x] Test confidence score is in valid range [0.0, 1.0]
  - [x] Test RouterOutput validation: BOTH requires log_portion and query_portion (AC: #8)
  - [x] Test RouterOutput validation: CORRECTION requires correction_target (AC: #9)
  - [x] Test empty raw_input raises ValueError (AC: #7)
  - [x] Test whitespace-only raw_input raises ValueError (AC: #7)
  - [x] Use mock_llm fixture for isolated testing
  - [x] Add integration test with `--use-real-ollama` pytest marker

- [x] Task 7: Export from quilto package (AC: all)
  - [x] Add RouterAgent to `quilto/agents/__init__.py`
  - [x] Add InputType, DomainInfo, RouterInput, RouterOutput to exports
  - [x] Update `quilto/__init__.py` with agent exports
  - [x] Verify `__all__` is complete

## Dev Notes

### Project Structure

**Location:** `packages/quilto/quilto/agents/`

```
packages/quilto/quilto/agents/
├── __init__.py       # Exports: RouterAgent, InputType, DomainInfo, RouterInput, RouterOutput
├── router.py         # RouterAgent class
└── models.py         # Shared agent types (InputType, DomainInfo, etc.)
```

**Test Location:** `packages/quilto/tests/test_router.py`

### Model Definitions

**From agent-system-design.md Section 11.2:**

```python
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator

class InputType(str, Enum):
    """Classification of user input type."""
    LOG = "LOG"
    QUERY = "QUERY"
    BOTH = "BOTH"
    CORRECTION = "CORRECTION"


class DomainInfo(BaseModel):
    """Domain information for Router domain selection."""
    model_config = ConfigDict(strict=True)

    name: str
    description: str


class RouterInput(BaseModel):
    """Input to Router agent."""
    model_config = ConfigDict(strict=True)

    raw_input: str
    session_context: str | None = None  # Recent conversation
    available_domains: list[DomainInfo]


class RouterOutput(BaseModel):
    """Output from Router agent."""
    model_config = ConfigDict(strict=True)

    input_type: InputType
    confidence: float = Field(ge=0.0, le=1.0)

    # Domain selection
    selected_domains: list[str]  # Domain names to activate
    domain_selection_reasoning: str

    # If BOTH, split the input
    log_portion: str | None = None
    query_portion: str | None = None

    # If CORRECTION, identify what's being corrected
    correction_target: str | None = None

    reasoning: str  # Brief explanation of classification

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "RouterOutput":
        """Validate that BOTH has portions and CORRECTION has target."""
        if self.input_type == InputType.BOTH:
            if not self.log_portion or not self.query_portion:
                raise ValueError(
                    "BOTH input_type requires both log_portion and query_portion"
                )
        if self.input_type == InputType.CORRECTION:
            if not self.correction_target:
                raise ValueError(
                    "CORRECTION input_type requires correction_target"
                )
        return self
```

### Router Prompt Template

**From agent-system-design.md Section 12.2:**

```
ROLE: You are an input classifier and domain selector for a personal logging system.

TASKS:
1. Classify the user's input type
2. Select relevant domain(s) for processing

=== CLASSIFICATION RULES ===

INPUT TYPES:
- LOG: Declarative statements recording activities, events, or observations
- QUERY: Questions seeking information, insights, or recommendations
- BOTH: Input that logs something AND asks a question
- CORRECTION: User fixing previously recorded information ("actually", "I meant", "that was wrong")

SIGNALS:
- Question words (why, how, what, when, which) → QUERY
- Question mark → QUERY
- Past tense declarative → LOG
- Correction language → CORRECTION

=== DOMAIN SELECTION ===

Available domains:
{available_domains_with_descriptions}

Select ALL domains that are relevant to the input. When uncertain, prefer broader selection.

=== INPUT ===
{raw_input}

Session context (recent messages):
{session_context}

=== OUTPUT (JSON) ===
{RouterOutput.model_json_schema()}
```

### RouterAgent Class Structure

```python
class RouterAgent:
    """Router agent for input classification and domain selection.

    Classifies raw user input as LOG/QUERY/BOTH/CORRECTION and
    selects relevant domains based on input content matching
    against domain descriptions.

    Attributes:
        llm_client: The LLM client for making inference calls.
    """

    AGENT_NAME = "router"  # Used for tier resolution (low tier)

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Router agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def _build_prompt(self, input: RouterInput) -> str:
        """Build the system prompt with classification rules."""
        ...

    async def classify(self, input: RouterInput) -> RouterOutput:
        """Classify input and select domains.

        Args:
            input: RouterInput with raw_input, session_context, available_domains.

        Returns:
            RouterOutput with classification and domain selection.

        Raises:
            ValueError: If raw_input is empty or whitespace-only.
        """
        if not input.raw_input or not input.raw_input.strip():
            raise ValueError("raw_input cannot be empty or whitespace-only")
        ...
```

### Classification Rules (Embedded in Prompt)

| Signal | Classification | Example |
|--------|---------------|---------|
| Question words (why, how, what, when, which) | QUERY | "Why did my bench feel heavy?" |
| Question mark | QUERY | "How's my progress?" |
| Past tense declarative | LOG | "Bench pressed 185x5 today" |
| "Actually", "I meant", "that was wrong" | CORRECTION | "Actually that was 185 not 85" |
| Both logging and questioning | BOTH | "Did 185 bench, why was it heavy?" |

### Domain Selection Rules (From agent-system-design.md Section 8.4)

1. Match input keywords/topics against domain descriptions
2. Select ALL domains that are relevant (can be multiple)
3. When uncertain, prefer broader selection over missing relevant domains

**Example:**
```
Input: "Compare my running progress with my lifting"
Available domains: [StrengthModule, RunningModule, SwimmingModule]
Selected: ["running", "strength"]
Reasoning: "Input mentions both running and lifting activities"
```

### Agent Tier Configuration

Router uses **low** tier (simple classification task):

```yaml
# In llm-config.yaml
agents:
  router:
    tier: low
```

The LLMClient handles tier resolution automatically when called with agent name "router".

### Integration with LLMClient

```python
# Usage pattern
from quilto import LLMClient, load_llm_config
from quilto.agents import RouterAgent, RouterInput, DomainInfo

config = load_llm_config(Path("llm-config.yaml"))
client = LLMClient(config)
router = RouterAgent(client)

input = RouterInput(
    raw_input="Bench pressed 185x5 today, felt heavy. Why?",
    available_domains=[
        DomainInfo(name="strength", description="Strength training..."),
        DomainInfo(name="running", description="Running activities..."),
    ]
)
output = await router.classify(input)
# output.input_type == InputType.BOTH
# output.log_portion == "Bench pressed 185x5 today, felt heavy."
# output.query_portion == "Why?"
# output.selected_domains == ["strength"]
```

### Testing Requirements

**Test Class Organization:**
```python
class TestInputTypeClassification:
    """Tests for LOG/QUERY/BOTH/CORRECTION classification."""

    async def test_log_classification_declarative(self, mock_llm): ...
    async def test_query_classification_question_words(self, mock_llm): ...
    async def test_query_classification_question_mark(self, mock_llm): ...
    async def test_both_classification_with_portions(self, mock_llm): ...
    async def test_correction_classification(self, mock_llm): ...


class TestDomainSelection:
    """Tests for domain selection logic."""

    async def test_single_domain_match(self, mock_llm): ...
    async def test_multiple_domain_match(self, mock_llm): ...
    async def test_no_domain_match_returns_empty(self, mock_llm): ...
    async def test_empty_available_domains_returns_empty_selection(self, mock_llm): ...
    async def test_uncertain_prefers_broader_selection(self, mock_llm): ...


class TestRouterOutput:
    """Tests for RouterOutput validation and constraints."""

    def test_confidence_below_zero_raises_validation_error(self): ...
    def test_confidence_above_one_raises_validation_error(self): ...
    def test_valid_confidence_in_range(self): ...
    def test_both_without_log_portion_raises_validation_error(self): ...
    def test_both_without_query_portion_raises_validation_error(self): ...
    def test_both_with_both_portions_succeeds(self): ...
    def test_correction_without_target_raises_validation_error(self): ...
    def test_correction_with_target_succeeds(self): ...


class TestRouterInputValidation:
    """Tests for RouterInput validation."""

    def test_empty_raw_input_raises_value_error(self): ...
    def test_whitespace_only_raw_input_raises_value_error(self): ...
    def test_empty_available_domains_is_valid(self): ...


class TestRouterIntegration:
    """Integration tests with real LLM (skipped by default).

    Run with: pytest --use-real-ollama -k TestRouterIntegration
    """

    @pytest.mark.skipif(
        not pytest.config.getoption("--use-real-ollama", default=False),
        reason="Requires --use-real-ollama flag"
    )
    async def test_real_log_classification(self, real_llm_client): ...

    @pytest.mark.skipif(
        not pytest.config.getoption("--use-real-ollama", default=False),
        reason="Requires --use-real-ollama flag"
    )
    async def test_real_query_classification(self, real_llm_client): ...
```

### Test Fixtures

Use existing `mock_llm` fixture from `tests/conftest.py`:

```python
@pytest.fixture
def mock_llm():
    """Provides a mock LLMClient that returns canned responses."""
    ...
```

For Router tests, configure mock to return valid RouterOutput JSON.

### Validation Commands

Run frequently during development:
```bash
# Quick validation
uv run ruff check . --fix && uv run pyright

# Full validation (before commits)
uv run ruff check . && uv run ruff format . && uv run pyright && uv run pytest
```

### Export Checklist

After implementation, verify exports:
```python
# packages/quilto/quilto/agents/__init__.py
from quilto.agents.models import DomainInfo, InputType, RouterInput, RouterOutput
from quilto.agents.router import RouterAgent

__all__ = [
    "DomainInfo",
    "InputType",
    "RouterAgent",
    "RouterInput",
    "RouterOutput",
]

# packages/quilto/quilto/__init__.py - add to existing exports
from quilto.agents import (
    DomainInfo,
    InputType,
    RouterAgent,
    RouterInput,
    RouterOutput,
)
```

### Previous Story Learnings (Story 2.1)

**Patterns to Follow:**
- Use `ConfigDict(strict=True)` for all Pydantic models
- Google-style docstrings for all public classes/methods
- Comprehensive test coverage with edge cases
- Export all public classes in `__all__`
- Test file organization by functionality

**Code Review Fixes Applied in 2.1:**
- Remove dead code (unused variables)
- Add validation for edge cases (empty inputs)
- Add boundary condition tests
- Validate parameters in public methods

### Architecture Compliance

**From architecture.md:**
- Router is low-tier agent (simple classification)
- Uses LiteLLM via LLMClient abstraction
- Returns structured Pydantic output
- Part of entry flow: ROUTE state

**State Machine Position (from state-machine-diagram.md):**
```
ROUTE → BUILD_CONTEXT (always, domains selected)
```
Router is the first agent in the pipeline, determining input type and selecting domains.

### Error Handling

| Error Case | Handling |
|------------|----------|
| LLM returns invalid JSON | LLMClient raises ValueError with details |
| Confidence below threshold | Still return result, caller decides action |
| No domains available | Return empty selected_domains list (valid case) |
| Empty raw_input | Raise ValueError immediately (in RouterAgent.classify) |
| Whitespace-only raw_input | Raise ValueError immediately (treated same as empty) |
| BOTH without portions | RouterOutput model_validator raises ValueError |
| CORRECTION without target | RouterOutput model_validator raises ValueError |

**Note:** Empty `available_domains` is a valid edge case - Router can still classify input type even without domains to select.

### References

- [Source: agent-system-design.md#11.2] Router Agent Interface
- [Source: agent-system-design.md#12.2] Router Prompt
- [Source: agent-system-design.md#8.4] Domain Selection Mechanism
- [Source: architecture.md#Agent-Framework-Decision] LangGraph decision
- [Source: project-context.md] Quilto vs Swealog separation
- [Source: 2-1-implement-storagerepository-interface.md] Previous story patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented RouterAgent with `classify()` method for input classification
- Created `InputType` enum with LOG, QUERY, BOTH, CORRECTION values
- Created `DomainInfo`, `RouterInput`, `RouterOutput` Pydantic models with strict validation
- Added `@model_validator` for type-specific field validation (BOTH requires portions, CORRECTION requires target)
- Implemented comprehensive system prompt with classification rules and domain selection instructions
- Empty/whitespace raw_input validated before LLM call (ValueError raised immediately)
- Made `build_prompt()` public for testability
- All 31 router tests pass (29 passed, 2 skipped integration tests)
- All 147 quilto package tests pass
- ruff check and pyright pass with 0 errors
- Exports added to `quilto/__init__.py` and `quilto/agents/__init__.py`

### Code Review Fixes Applied

**Review Date:** 2026-01-11
**Reviewer:** Amelia (Developer Agent)

**Issues Fixed:**
1. **H1 - py.typed marker**: Added `packages/quilto/quilto/agents/py.typed` for PEP 561 compliance
2. **H3 - Integration tests**: Created `packages/quilto/tests/conftest.py` with proper `--use-real-ollama` pytest hook
3. **H4 - Empty string validation**: Added tests for empty string cases (`test_both_with_empty_log_portion_raises_validation_error`, `test_both_with_empty_query_portion_raises_validation_error`, `test_correction_with_empty_target_raises_validation_error`)
4. **M1 - Missing test**: Added `test_uncertain_prefers_broader_selection` test
5. **M2 - Missing test**: Added `test_no_domain_match_returns_empty` test

**Test count increased:** 31 → 36 tests (34 passed, 2 skipped integration tests)

### File List

- `packages/quilto/quilto/agents/__init__.py` (created)
- `packages/quilto/quilto/agents/models.py` (created)
- `packages/quilto/quilto/agents/router.py` (created)
- `packages/quilto/quilto/agents/py.typed` (created - code review fix)
- `packages/quilto/quilto/__init__.py` (modified - added agent exports)
- `packages/quilto/tests/test_router.py` (created, updated with code review fixes)
- `packages/quilto/tests/conftest.py` (created - code review fix)
