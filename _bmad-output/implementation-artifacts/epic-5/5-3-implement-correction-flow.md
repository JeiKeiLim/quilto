# Story 5.3: Implement Correction Flow

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Quilto developer**,
I want a **correction flow that handles user corrections**,
so that **mistakes in logs can be fixed with audit trail**.

## Acceptance Criteria

1. **Given** Router classifies input as CORRECTION
   **When** the correction flow is triggered
   **Then** Parser processes the input in correction mode (correction_mode=True, correction_target set)

2. **Given** Parser in correction mode with correction_target hint
   **When** Parser processes the correction input
   **Then** it identifies the target entry from recent_entries using the correction_target hint

3. **Given** Parser has identified the target entry
   **When** it extracts the correction
   **Then** ParserOutput includes:
   - `is_correction = True`
   - `target_entry_id` set to the identified entry's ID
   - `correction_delta` containing ONLY the fields that are changing
   - `domain_data` containing the full corrected data

4. **Given** StorageRepository.save_entry receives a correction
   **When** it processes the correction (correction parameter with is_correction=True)
   **Then** correction note is appended to raw markdown (not overwritten)
   **And** raw file format: `## HH:MM [correction]\n{correction_content}`

5. **Given** StorageRepository.save_entry receives a correction with correction_delta
   **When** it updates the parsed JSON
   **Then** it uses upsert semantics (update existing entry with correction_delta)
   **And** original parsed data is preserved, only delta fields are updated

6. **Given** a correction is processed
   **When** the flow completes
   **Then** Observer is triggered with `trigger="user_correction"` (not "significant_log")
   **And** Observer learns from the correction pattern

7. **Given** the correction flow implementation
   **When** integrated with the state module
   **Then** SessionState includes correction-related fields for tracking

## Tasks / Subtasks

- [x] Task 1: Create correction flow orchestration function (AC: #1, #6)
  - [x] 1.1: Create `packages/quilto/quilto/flow/correction.py`
  - [x] 1.2: Implement `async def process_correction(router_output: RouterOutput, parser_agent: ParserAgent, storage: StorageRepository, recent_entries: list[Entry], domain_schemas: dict[str, type[BaseModel]], vocabulary: dict[str, str]) -> CorrectionResult`
  - [x] 1.3: Define `CorrectionResult` model with: success, target_entry_id, correction_delta, error_message
  - [x] 1.4: Add Google-style docstrings with examples
  - [x] 1.5: Export from `quilto.flow` package

- [x] Task 2: Create CorrectionResult and related models (AC: #3, #7)
  - [x] 2.1: Create `packages/quilto/quilto/flow/models.py`
  - [x] 2.2: Define `CorrectionResult` Pydantic model with fields: success, target_entry_id, correction_delta, original_entry_id, error_message
  - [x] 2.3: Use `ConfigDict(strict=True)` per project conventions
  - [x] 2.4: Add field validation (success=True requires target_entry_id)

- [x] Task 3: Add correction tracking fields to SessionState (AC: #7)
  - [x] 3.1: Update `packages/quilto/quilto/state/session.py`
  - [x] 3.2: Add fields: `correction_target: str | None`, `correction_result: dict[str, Any] | None`
  - [x] 3.3: Add `is_correction_flow: bool` flag for routing decisions
  - [x] 3.4: Update exports in `quilto.state.__init__.py`

- [x] Task 4: Implement correction flow logic (AC: #1, #2, #3)
  - [x] 4.1: In `process_correction`, validate `router_output.input_type == InputType.CORRECTION`
  - [x] 4.2: Check `recent_entries` is not empty (error if empty)
  - [x] 4.3: Build ParserInput with `correction_mode=True`, `correction_target=router_output.correction_target`
  - [x] 4.4: Call `parser_agent.parse(parser_input)` with correction-mode ParserInput
  - [x] 4.5: Validate ParserOutput has `is_correction=True` and `target_entry_id`
  - [x] 4.6: If validation fails, return error CorrectionResult
  - [x] 4.7: Create Entry object with correction content
  - [x] 4.8: Call `storage.save_entry(entry, correction=parser_output)`
  - [x] 4.9: Return success CorrectionResult with correction_delta

- [x] Task 5: Enhance target entry identification in Parser prompt (AC: #2)
  - [x] 5.1: Update `packages/quilto/quilto/agents/parser.py` - `build_prompt` method
  - [x] 5.2: Add detailed correction mode instructions for target identification
  - [x] 5.3: Include instructions: "Match correction_target hint against recent_entries"
  - [x] 5.4: Include instructions: "Use entry date, content keywords, and exercise names for matching"
  - [x] 5.5: Include fallback: "If no match found, set target_entry_id to null with explanation"

- [x] Task 6: Verify StorageRepository correction handling (AC: #4, #5)
  - [x] 6.1: Review existing `save_entry` method in `repository.py`
  - [x] 6.2: Verify raw markdown append format: `## HH:MM [correction]\n{content}`
  - [x] 6.3: Verify `_update_parsed_json` performs upsert correctly
  - [x] 6.4: Add integration tests for correction scenarios

- [x] Task 7: Create flow package structure (AC: #1)
  - [x] 7.1: Create `packages/quilto/quilto/flow/__init__.py`
  - [x] 7.2: Export CorrectionResult, process_correction
  - [x] 7.3: Add `__all__` with all public exports
  - [x] 7.4: Update `packages/quilto/quilto/__init__.py` with flow module

- [x] Task 8: Create comprehensive unit tests
  - [x] 8.1: Create `packages/quilto/tests/test_correction_flow.py`
  - [x] 8.2: Test `CorrectionResult` model validation (success requires target_entry_id)
  - [x] 8.3: Test `process_correction` happy path with mock Parser and Storage
  - [x] 8.4: Test `process_correction` with target not found (error case)
  - [x] 8.5: Test `process_correction` with Parser returning is_correction=False (error case)
  - [x] 8.6: Test SessionState correction fields work correctly
  - [x] 8.7: Test Parser prompt includes correction mode section when correction_mode=True
  - [x] 8.8: Test StorageRepository.save_entry with correction parameter

- [x] Task 9: Create integration tests
  - [x] 9.1: Test full correction flow: Router→Parser→Storage
  - [x] 9.2: Test correction appends to raw file correctly
  - [x] 9.3: Test correction updates parsed JSON with upsert
  - [x] 9.4: Test reading corrected entries returns updated data

- [x] Task 10: Run validation
  - [x] 10.1: Run `make check` (lint + typecheck)
  - [x] 10.2: Run `make validate` (full validation)
  - [x] 10.3: Run `make test-ollama` (integration tests with real Ollama)

## Dev Notes

### Architecture Patterns

- **Location:** `packages/quilto/quilto/flow/correction.py` (NEW flow module - currently does not exist)
- **Pattern:** Orchestration function coordinating Parser + Storage for correction flow
- **Framework:** Domain-agnostic - works with any domain that has corrections

**VERIFICATION:** The `quilto.flow` package does not exist yet. This story creates it from scratch:
```
packages/quilto/quilto/flow/   # CREATE THIS DIRECTORY
├── __init__.py                # New
├── models.py                  # New (CorrectionResult)
└── correction.py              # New (process_correction)
```

### Correction Flow Overview (from agent-system-design.md Section 5.5)

CORRECTION is treated as a LOG variant with update semantics:

```
ROUTE → BUILD_CONTEXT → PARSE (correction mode) → STORE (upsert) → OBSERVE
```

The Router identifies correction intent via language patterns ("actually", "I meant", "that was wrong") and extracts `correction_target` (natural language hint about what's being corrected).

### Two Correction Scenarios

**Scenario A: Parser Error**
- User wrote correctly, Parser extracted incorrectly
- Raw content is already correct
- Only parsed data needs fixing

**Scenario B: User Typo**
- User made a typo in original input
- Both raw and parsed need fixing

The correction flow handles BOTH scenarios by:
1. Appending correction to raw markdown (preserving history)
2. Updating parsed JSON with correction delta

### Raw Markdown Correction Format

Per architecture Section 5.5:

```markdown
## 10:30
I benched 185 today and also squated 200 felt good

## 10:45 [correction]
Correction: bench weight recorded as 85 → corrected to 185
```

**Key:** The `[correction]` marker distinguishes correction entries from regular entries.

### StorageRepository Already Implements Correction (Verify Only)

The `StorageRepository.save_entry` method already has correction handling at `repository.py:269-318`.

**CRITICAL VERIFICATION CHECKLIST for Task 6:**

| Aspect | Expected (from spec) | Actual (in code) | Status |
|--------|---------------------|------------------|--------|
| Raw format | `## HH:MM [correction]\n{content}` | `\n\n## {time_str} [correction]\n{entry.raw_content}` (line 294) | ✅ Match |
| Upsert semantics | Update existing with delta | `existing[entry_id].update(correction_delta)` (line 360) | ✅ Match |
| Target entry ID | From `correction.target_entry_id` | `correction.target_entry_id or entry.id` (line 312) | ✅ Match |
| File appending | Append (not overwrite) | Uses `raw_path.open("a", ...)` (line 295) | ✅ Match |

**Existing code paths (verified):**
- `save_entry()`: lines 269-318 - handles both new entries and corrections
- `_update_parsed_json()`: lines 340-363 - performs upsert with correction_delta
- `_parse_raw_file()`: lines 88-150 - parses `[correction]` marker in section header (line 114)

**Task 6 is VERIFICATION** - run integration tests to confirm existing implementation works correctly.

### CorrectionResult Model

```python
from pydantic import BaseModel, ConfigDict, model_validator

class CorrectionResult(BaseModel):
    """Result of correction flow processing."""
    model_config = ConfigDict(strict=True)

    success: bool
    target_entry_id: str | None = None
    correction_delta: dict[str, Any] | None = None
    original_entry_id: str | None = None  # ID before correction (for audit)
    error_message: str | None = None

    @model_validator(mode="after")
    def validate_success_requires_target(self) -> "CorrectionResult":
        """Success requires target_entry_id."""
        if self.success and not self.target_entry_id:
            raise ValueError("success=True requires target_entry_id")
        if not self.success and not self.error_message:
            raise ValueError("success=False requires error_message")
        return self
```

### process_correction Function Signature

```python
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from quilto.agents import ParserAgent, RouterOutput
from quilto.storage import StorageRepository, Entry

async def process_correction(
    router_output: RouterOutput,
    parser_agent: ParserAgent,
    storage: StorageRepository,
    recent_entries: list[Entry],
    domain_schemas: dict[str, type[BaseModel]],
    vocabulary: dict[str, str],
    timestamp: datetime | None = None,  # Defaults to datetime.now() for Entry creation
) -> CorrectionResult:
    """Process a correction request through Parser and Storage.

    Args:
        router_output: RouterOutput with input_type=CORRECTION and correction_target.
        parser_agent: ParserAgent instance for extraction.
        storage: StorageRepository for saving corrected entry.
        recent_entries: Recent entries for target identification.
        domain_schemas: Domain schemas for parsing.
        vocabulary: Vocabulary for term normalization.
        timestamp: Override timestamp (defaults to now).

    Returns:
        CorrectionResult indicating success/failure with details.

    Raises:
        ValueError: If router_output.input_type is not CORRECTION.

    Example:
        >>> result = await process_correction(
        ...     router_output=router_output,
        ...     parser_agent=parser,
        ...     storage=storage,
        ...     recent_entries=recent,
        ...     domain_schemas={"strength": StrengthSchema},
        ...     vocabulary={"bp": "bench press"},
        ... )
        >>> if result.success:
        ...     print(f"Corrected entry: {result.target_entry_id}")
    """
```

### SessionState Correction Fields

**CURRENT STATE:** `session.py` (lines 71-83) has clarification fields but NO correction fields.

Add these fields to `SessionState` TypedDict at `packages/quilto/quilto/state/session.py`:

```python
class SessionState(TypedDict, total=False):
    # ... existing fields (lines 49-83) ...

    # Correction tracking (Story 5-3) - ADD AFTER LINE 83
    is_correction_flow: bool  # True if input_type == CORRECTION
    correction_target: str | None  # Natural language hint from Router
    correction_result: dict[str, Any] | None  # CorrectionResult.model_dump()
```

**Location:** Insert after line 83 (after `complete: bool`)

### Parser Correction Mode Enhancement

**CURRENT STATE:** Parser already has correction mode at `parser.py:127-142`:
```python
# Existing code (lines 127-142)
correction_section = ""
if parser_input.correction_mode:
    correction_section = f"""
=== CORRECTION MODE ===

This is a CORRECTION to a previous entry.
Correction target hint: {parser_input.correction_target or "Not specified"}

IMPORTANT:
- Set is_correction = true
- Identify which entry from recent_entries is being corrected
- Set target_entry_id to the identified entry's ID
- Set correction_delta to ONLY the fields that are changing
- The domain_data should contain the full corrected data
"""
```

**ENHANCEMENT NEEDED (Task 5):** Add these TARGET IDENTIFICATION instructions AFTER the existing IMPORTANT section:

```
=== TARGET IDENTIFICATION ===

Given the correction_target hint: "{correction_target}"

Match against recent_entries using:
1. Date matching: Does the hint mention a date or time? (e.g., "yesterday", "10:30 entry")
2. Content matching: Does the hint mention specific exercises, foods, or activities?
3. Value matching: Does the hint reference specific numbers that appear in entries?

Entry format in recent_entries: "{entry_id}, {date}, {content_summary}"

If multiple entries could match:
- Select the most recent one
- Note the ambiguity in extraction_notes

If no entry matches:
- Set target_entry_id to null
- Set is_correction to false
- Add explanation to extraction_notes
```

**File location:** `packages/quilto/quilto/agents/parser.py`, method `build_prompt()`, around line 142

### process_correction Implementation Pseudocode

```python
async def process_correction(...) -> CorrectionResult:
    # 1. Validate inputs
    if router_output.input_type != InputType.CORRECTION:
        raise ValueError("router_output must have input_type=CORRECTION")
    if not recent_entries:
        return CorrectionResult(success=False, error_message="No recent entries to correct")

    # 2. Build ParserInput with correction mode
    parser_input = ParserInput(
        raw_input=router_output.raw_input,  # or appropriate field
        timestamp=timestamp or datetime.now(),
        domain_schemas=domain_schemas,
        vocabulary=vocabulary,
        recent_entries=recent_entries,
        correction_mode=True,
        correction_target=router_output.correction_target,
    )

    # 3. Call Parser
    parser_output = await parser_agent.parse(parser_input)

    # 4. Validate Parser identified the correction
    if not parser_output.is_correction:
        return CorrectionResult(success=False, error_message="Parser did not identify correction")
    if not parser_output.target_entry_id:
        return CorrectionResult(success=False, error_message="Could not identify target entry")

    # 5. Create Entry for storage
    entry = Entry(
        id=f"{parser_output.date}_{timestamp.strftime('%H-%M-%S')}",
        date=parser_output.date,
        timestamp=timestamp,
        raw_content=parser_output.raw_content,
        parsed_data=parser_output.domain_data,
    )

    # 6. Save with correction (triggers append + upsert)
    storage.save_entry(entry, correction=parser_output)

    # 7. Return success
    return CorrectionResult(
        success=True,
        target_entry_id=parser_output.target_entry_id,
        correction_delta=parser_output.correction_delta,
        original_entry_id=parser_output.target_entry_id,
    )
```

### Observer Integration (Story 5-3 vs Story 7-x)

This story ensures the correction flow sets up proper trigger data for Observer, but **Observer agent implementation is Epic 7**. The flow should:

1. Return correction metadata that can be passed to Observer
2. Use `trigger="user_correction"` (not "significant_log")
3. Include `what_was_corrected` in session state for later Observer call

**ObserverInput fields for corrections (from agent-system-design.md Section 11.9):**
```python
class ObserverInput(BaseModel):
    trigger: Literal["post_query", "user_correction", "significant_log"]
    correction: str | None = None  # The correction content
    what_was_corrected: str | None = None  # Description of what changed
```

**CorrectionResult should include data for Observer:**
- `correction_delta` → becomes `what_was_corrected` description
- Original `raw_content` → becomes `correction` field

Full Observer integration happens in Epic 7.

### Entry Model Reference

The `Entry` model is defined at `packages/quilto/quilto/storage/models.py`:

```python
class Entry(BaseModel):
    id: str  # Format: "{YYYY-MM-DD}_{HH}-{MM}-{SS}"
    date: date
    timestamp: datetime
    raw_content: str
    parsed_data: dict[str, Any] | None = None
```

**Usage in process_correction:**
- `recent_entries: list[Entry]` parameter provides entries for target identification
- Access entry ID via `entry.id` for matching against `correction_target`
- Get entries from storage via `StorageRepository.get_entries_by_date_range()`

### Testing Standards (from project-context.md)

- **ConfigDict:** Use `model_config = ConfigDict(strict=True)` for all models
- **Required string fields:** Use `Field(min_length=1)` for required non-empty strings
- **Boundary tests:** Test empty correction_target, empty recent_entries, None values
- **All exports:** Verify importable from `quilto.flow` and `quilto.state`
- **Mock patterns:** Use existing mock_llm fixture pattern from other agent tests

### Implementation Checklist

Before implementation, verify these patterns from existing code:

| Pattern | Reference File | Method/Class | Apply To |
|---------|---------------|--------------|----------|
| Async flow function | None (new pattern) | N/A | Create `process_correction` |
| Model validation | `agents/models.py` | `RouterOutput.validate_type_specific_fields()` | `CorrectionResult` validation |
| Storage correction | `storage/repository.py` | `save_entry()`, `_update_parsed_json()` | Verify existing implementation |
| Parser correction mode | `agents/parser.py` | `build_prompt()` lines 127-142 | Enhance target identification |
| State TypedDict | `state/session.py` | `SessionState` class | Add correction fields after line 83 |

### Test Reference Patterns

Use existing test patterns from the codebase:

| Test Pattern | Reference | Apply To |
|--------------|-----------|----------|
| Model validation tests | `tests/test_router.py` | CorrectionResult model tests |
| Storage correction tests | `tests/test_repository.py` | Correction flow integration tests |
| Mock LLM fixture | `tests/conftest.py::mock_llm` | Unit tests for process_correction |
| Parser tests | `tests/test_parser.py` | Parser enhancement tests |
| State tests | `tests/test_state.py` | SessionState correction field tests |

**CRITICAL:** Run `make test-ollama` after implementation to verify correction flow works with real LLM.

### Error Handling Patterns

`process_correction` should handle these error cases:

| Error Case | Handling | CorrectionResult |
|------------|----------|------------------|
| `router_output.input_type != CORRECTION` | Raise `ValueError` immediately | N/A |
| Parser returns `is_correction=False` | Return error result | `success=False, error_message="Parser did not identify correction"` |
| Parser returns `target_entry_id=None` | Return error result | `success=False, error_message="Could not identify target entry"` |
| Storage write fails | Let exception propagate | N/A (caller handles) |
| Empty `recent_entries` list | Return error result | `success=False, error_message="No recent entries to correct"` |

### Common Mistakes to Avoid

From project-context.md and previous stories:

| Mistake | Correct Pattern |
|---------|-----------------|
| Storing Pydantic model directly in SessionState | Use `.model_dump()` for JSON serialization |
| Missing `__all__` in `__init__.py` | Export all public classes in `__all__` list |
| Using `Field()` AND `@field_validator` for range | Use only `Field(ge=, le=)` |
| Required string without length check | Use `Field(min_length=1)` |
| Missing boundary value tests | Test None, empty string, empty list cases |

### Previous Story Learnings (Story 5-1, 5-2)

From Story 5-1 (Clarifier):
1. `filter_non_retrievable_gaps` pattern - similar filtering might be needed
2. MAX constant for limits enforced via post-processing

From Story 5-2 (WAIT_USER):
1. SessionState stores Pydantic models as dicts via `.model_dump()`
2. State routing functions follow simple `route_after_X` pattern
3. LangGraph integration uses `interrupt()` (not needed for correction flow)

### Relationship to Other Stories

- **Story 5-1 (done):** ClarifierAgent - separate human-in-the-loop path
- **Story 5-2 (done):** WAIT_USER state - human response handling
- **Story 5-3 (this):** Correction flow - LOG variant with upsert
- **Story 5-4 (next):** Fitness clarification patterns - domain-specific

### Key Flow Differences from Standard LOG

| Aspect | Standard LOG | CORRECTION |
|--------|--------------|------------|
| Router output | `input_type: LOG` | `input_type: CORRECTION`, `correction_target` set |
| Parser mode | Create new entry | Find target + extract delta |
| Store action | Create | Upsert (append correction to raw, update parsed) |
| Observer trigger | `significant_log` | `user_correction` |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.3]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 5.5 CORRECTION Input Handling]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 7.6 CORRECTION as LOG Variant]
- [Source: packages/quilto/quilto/agents/router.py] - CORRECTION classification
- [Source: packages/quilto/quilto/agents/parser.py] - Correction mode in prompt
- [Source: packages/quilto/quilto/agents/models.py] - RouterOutput, ParserInput, ParserOutput with correction fields
- [Source: packages/quilto/quilto/storage/repository.py] - save_entry with correction parameter
- [Source: packages/quilto/quilto/state/session.py] - SessionState TypedDict pattern
- [Source: _bmad-output/project-context.md#Common Mistakes to Avoid]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **CorrectionResult Model**: Created with strict validation ensuring success=True requires target_entry_id and success=False requires error_message
2. **process_correction Function**: Orchestrates correction flow with proper error handling for all edge cases
3. **Parser Enhancement**: Added TARGET IDENTIFICATION section with matching instructions (date, content, value matching)
4. **SessionState Fields**: Added is_correction_flow, correction_target, correction_result fields
5. **StorageRepository Verification**: Confirmed existing implementation handles corrections correctly (append to raw, upsert parsed)
6. **Test Coverage**: 28 comprehensive tests covering model validation, flow orchestration, state fields, parser prompts, and storage integration

### Code Review Fixes Applied

1. **Timezone-aware timestamp**: Changed `datetime.now()` to `datetime.now(UTC)` for consistency
2. **Added test for reasoning fallback**: New test `test_uses_reasoning_when_log_portion_is_none` verifies the `log_portion or reasoning` fallback path

### Validation Results

- `make check`: All lint and typecheck passed
- `make validate`: 659 unit tests passed
- `make test-ollama`: 1109 integration tests passed, 4 skipped (18:02)

### File List (Actual)

**New files:**
- `packages/quilto/quilto/flow/__init__.py` - Package exports (CorrectionResult, process_correction)
- `packages/quilto/quilto/flow/models.py` - CorrectionResult model with validation
- `packages/quilto/quilto/flow/correction.py` - process_correction orchestration function
- `packages/quilto/tests/test_correction_flow.py` - 28 comprehensive unit tests

**Modified files:**
- `packages/quilto/quilto/state/session.py` - Added correction tracking fields (is_correction_flow, correction_target, correction_result)
- `packages/quilto/quilto/agents/parser.py` - Enhanced target identification in build_prompt() with TARGET IDENTIFICATION section
- `packages/quilto/quilto/__init__.py` - Added flow module exports (CorrectionResult, process_correction)

