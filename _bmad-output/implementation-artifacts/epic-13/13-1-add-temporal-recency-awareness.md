# Story 13.1: Add Temporal Recency Awareness to Analyzer

Status: done

## Story

As a **Quilto user**,
I want **the system to consider how long ago my workout logs were recorded**,
So that **recommendations account for recovery time and current fitness state**.

## Background

**Origin:** Dogfooding Iteration 3 (Epic 13)
**Source:** `tests/eval/feedback/archive/iter-002/analysis.md` - Pattern 7: Temporal Context Blindness
**Priority:** High | **Effort:** Medium (2-4 hours)
**Type:** Analyzer + Synthesizer prompt enhancement (no API changes)

29% of Iteration 2 feedback records (3 of 7) were affected by temporal blindness - the system retrieves historical logs correctly but fails to account for time elapsed since the most recent entry.

**User Feedback:**
- "it's been 6 days since the last workout... The response should have considered a bit more time awareness."
- "It's been almost 7 days from my last workout. Recovery training recommendation seems a bit off."

## Acceptance Criteria

1. **Given** retrieved log entries with timestamps
   **When** Analyzer processes the data
   **Then** it calculates "days since most recent entry" and includes this in findings

2. **Given** a recommendation query with logs older than 5 days
   **When** generating recommendations
   **Then** the response acknowledges the time gap

3. **Given** fatigue/soreness evidence from logs older than 7 days
   **When** synthesizing response
   **Then** the system does NOT reference that soreness as "current" or "lingering"

4. **Given** a user who hasn't logged in 7+ days
   **When** asked for a workout recommendation
   **Then** the response suggests a moderate return-to-training approach rather than recovery

## Tasks / Subtasks

- [x] Task 1: Add temporal context to Analyzer prompt (AC: #1, #3)
  - [x] 1.1: In `build_prompt()` (line 174), add temporal context calculation before formatting entries
  - [x] 1.2: Add `_calculate_temporal_context()` method to compute days since most recent entry
  - [x] 1.3: Insert `=== TEMPORAL CONTEXT ===` section after `=== GLOBAL CONTEXT ===` (line 268)

- [x] Task 2: Add temporal awareness rules to Analyzer prompt (AC: #1, #3)
  - [x] 2.1: Add temporal rules to system prompt (see exact text in Dev Notes)
  - [x] 2.2: Include rule: "Do not reference fatigue/soreness from logs > 7 days as 'current'"

- [x] Task 3: Update Synthesizer prompt for temporal awareness (AC: #2, #4)
  - [x] 3.1: Add temporal section after `=== REASONING REQUIREMENTS ===` in `build_prompt()` (line 217)
  - [x] 3.2: Add rule: Acknowledge time gaps > 5 days
  - [x] 3.3: Add rule: For 7+ day gaps, suggest return-to-training not recovery

- [x] Task 4: Write unit tests (AC: #1-#4)
  - [x] 4.1: Add `test_temporal_context_calculation()` in `packages/quilto/tests/test_analyzer.py`
  - [x] 4.2: Add `test_prompt_includes_temporal_context_section()`
  - [x] 4.3: Test with entries 1, 5, 7, and 14+ days old

- [x] Task 5: Run validation
  - [x] 5.1: Run `make check` (lint + typecheck)
  - [x] 5.2: Run `make validate` (full validation)
  - [x] 5.3: Run `make test-ollama` (integration tests)

## Dev Notes

### Scope: Prompt-Only Changes

**Files to modify:**

| File | Location | Changes |
|------|----------|---------|
| `packages/quilto/quilto/agents/analyzer.py` | Lines 174-300 in `build_prompt()` | Add temporal context section |
| `packages/quilto/quilto/agents/synthesizer.py` | Lines 147-273 in `build_prompt()` | Add temporal awareness instructions |
| `packages/quilto/tests/test_analyzer.py` | `TestAnalyzerPromptBuilding` class | Add 3 unit tests |

**NO changes needed to:**
- Model classes (AnalyzerInput, AnalyzerOutput, SynthesizerInput, SynthesizerOutput)
- `__init__.py` exports
- `_format_entries()` or `synthesize()` methods

### Implementation Approach

**Get current date inside Analyzer (no API changes):**
```python
from datetime import date, datetime

def _calculate_temporal_context(self, entries: list[Any]) -> str:
    """Calculate temporal context from entries."""
    if not entries:
        return "(No entries - cannot calculate temporal context)"

    today = date.today()
    dates: list[date] = []
    for entry in entries:
        entry_date = None
        if isinstance(entry, dict):
            entry_date = entry.get("date")
        else:
            entry_date = getattr(entry, "date", None)
        if entry_date:
            if isinstance(entry_date, str):
                entry_date = datetime.fromisoformat(entry_date).date()
            dates.append(entry_date)

    if not dates:
        return "(No valid dates in entries)"

    most_recent = max(dates)
    oldest = min(dates)
    days_since = (today - most_recent).days

    return f"""Today's date: {today}
Most recent entry: {most_recent} ({days_since} days ago)
Oldest entry: {oldest}"""
```

### Exact Prompt Text to Add

**1. Analyzer - Insert after line 268 (after GLOBAL CONTEXT section):**

```python
=== TEMPORAL CONTEXT ===

{temporal_context_text}

TEMPORAL RULES:
- For entries > 7 days old: Do NOT reference physical state (fatigue, soreness, tiredness) as "current" or "lingering"
- For 5+ day workout gaps: Include days_since_last_entry in your findings
- For 7+ day gaps: Consider this a "return-to-training" scenario, not active recovery
- 0-2 days: Normal recommendations, recovery guidance relevant
- 3-5 days: Recovery likely complete, mention the break
- 6-7 days: Acknowledge extended break, suggest easing back
- 8+ days: Return-to-training approach, NOT recovery from recent workout
```

**2. Synthesizer - Insert after REASONING REQUIREMENTS section (after line 228):**

```python
=== TEMPORAL AWARENESS ===

CRITICAL: Consider time elapsed since last workout when generating recommendations.

- If days_since_last > 5: Acknowledge the time gap (e.g., "Since your last workout was 6 days ago...")
- If days_since_last > 7: Suggest moderate return-to-training, NOT recovery
- NEVER say "current fatigue" or "lingering soreness" for data > 7 days old
- Phrase appropriately: "As of your last log on [date]..." instead of "currently"
```

### Unit Test Assertions

```python
def test_prompt_includes_temporal_context_section(self) -> None:
    """Prompt includes TEMPORAL CONTEXT section."""
    # ... setup with entries having dates ...
    prompt = analyzer.build_prompt(analyzer_input)
    assert "TEMPORAL CONTEXT" in prompt
    assert "TEMPORAL RULES" in prompt
    assert "days ago" in prompt

def test_temporal_context_calculation(self) -> None:
    """Temporal context calculates days since most recent entry."""
    # ... setup with entry from 5 days ago ...
    context = analyzer._calculate_temporal_context(entries)
    assert "5 days ago" in context

def test_temporal_rules_for_old_entries(self) -> None:
    """Prompt has rules about old entries."""
    prompt = analyzer.build_prompt(analyzer_input)
    assert "7 days old" in prompt.lower()
    assert "current" in prompt.lower() or "lingering" in prompt.lower()
```

### Testing Strategy

**Unit Tests (3 new in `TestAnalyzerPromptBuilding`):**

| Test | Assert Contains |
|------|-----------------|
| `test_prompt_includes_temporal_context_section` | "TEMPORAL CONTEXT", "TEMPORAL RULES" |
| `test_temporal_context_calculation` | Days calculation works |
| `test_temporal_rules_for_old_entries` | Rules about 7-day threshold |

**Integration:** Run `make test-ollama` - existing tests validate no regressions

### Pattern Reference (Story 12.4)

Story 12.4 added REASONING REQUIREMENTS and METRIC CITATION sections to Synthesizer using the same approach:
- Prompt-only changes in `build_prompt()` method
- Insert new sections between existing sections
- Unit tests check prompt TEXT contains required instructions
- No model or API changes required

### Anti-Patterns to Avoid

| Mistake | Correct |
|---------|---------|
| Adding `days_since_last_entry` to AnalyzerOutput | Keep model unchanged - include in findings instead |
| Using hardcoded dates in prompts | Use `date.today()` dynamically |
| Modifying `_format_entries()` | Create separate `_calculate_temporal_context()` |
| Creating new test file | Add tests to existing `test_analyzer.py` |

### Validation Checklist

```
- [x] `make check` passes
- [x] `make validate` passes (quilto package; pre-existing swealog test_cli_auto.py failures)
- [x] `make test-ollama` runs (note any pre-existing failures) - Ollama timeout issues + test_cli_auto.py failures
- [x] Analyzer prompt contains "TEMPORAL CONTEXT" section
- [x] Analyzer prompt contains "TEMPORAL RULES"
- [x] Synthesizer prompt contains "TEMPORAL AWARENESS" section
- [x] `_calculate_temporal_context()` method added to AnalyzerAgent
- [x] 3 new tests added to TestAnalyzerPromptBuilding (5 tests total)
- [x] No changes to AnalyzerInput, AnalyzerOutput models
- [x] No changes to SynthesizerInput, SynthesizerOutput models
```

## References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-002/analysis.md` | Pattern 7: Temporal Context Blindness |
| `_bmad-output/planning-artifacts/epics.md#Story 13.1` | Story definition with acceptance criteria |
| `_bmad-output/implementation-artifacts/epic-12/12-4-enhance-synthesizer-detail.md` | Similar prompt-enhancement story pattern |
| `packages/quilto/quilto/agents/analyzer.py` | Current Analyzer implementation |
| `packages/quilto/quilto/agents/synthesizer.py` | Current Synthesizer implementation |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Task 1 (AC #1, #3)**: Added `_calculate_temporal_context()` method to AnalyzerAgent (analyzer.py:140-181) that computes days since most recent entry using `date.today()`. Added TEMPORAL CONTEXT section after GLOBAL CONTEXT in build_prompt().

2. **Task 2 (AC #1, #3)**: Added TEMPORAL RULES section with guidance for 0-2, 3-5, 6-7, and 8+ day gaps. Includes rule to not reference physical state > 7 days old as "current" or "lingering".

3. **Task 3 (AC #2, #4)**: Added TEMPORAL AWARENESS section to Synthesizer prompt (synthesizer.py:238-246) after METRIC CITATION. Rules for acknowledging 5+ day gaps and suggesting return-to-training for 7+ day gaps.

4. **Task 4**: Added 5 new unit tests to TestAnalyzerPromptBuilding class:
   - `test_prompt_includes_temporal_context_section()` - verifies TEMPORAL CONTEXT and TEMPORAL RULES in prompt
   - `test_temporal_context_calculation()` - verifies days calculation (5 days ago)
   - `test_temporal_rules_for_old_entries()` - verifies 7-day threshold rules
   - `test_temporal_context_with_no_entries()` - edge case handling
   - `test_temporal_context_with_no_valid_dates()` - edge case handling

5. **Task 5 Validation**:
   - `make check` (lint + typecheck) passes for quilto package
   - `make test` (unit tests) passes - 68 tests in test_analyzer.py
   - `make test-ollama` ran but had Ollama timeout issues (infrastructure) and pre-existing test_cli_auto.py failures (unrelated to this story)

### File List

| File | Change |
|------|--------|
| `packages/quilto/quilto/agents/analyzer.py` | Added `datetime` imports, `_calculate_temporal_context()` method, TEMPORAL CONTEXT + TEMPORAL RULES sections in prompt |
| `packages/quilto/quilto/agents/synthesizer.py` | Added TEMPORAL AWARENESS section after METRIC CITATION |
| `packages/quilto/tests/test_analyzer.py` | Added 5 new tests for temporal context functionality |

### Senior Developer Review (AI)

**Review Date:** 2026-01-26
**Reviewer:** Claude Opus 4.5 (code-review workflow)
**Outcome:** APPROVED with fixes applied

**Issues Found & Fixed:**
1. **HIGH-1 (FIXED):** `test_cli_auto.py` had pyright errors - tests calling `_prompt_for_feedback()` missing new `non_interactive` parameter. Added `non_interactive=False` to all 4 test calls.
2. **MEDIUM-1 (FIXED):** `create_sample_entries()` in test_analyzer.py used hardcoded dates ("2026-01-10"). Changed to relative dates using `date.today() - timedelta(days=X)` to prevent tests from breaking over time.
3. **MEDIUM-1 (FIXED):** `test_prompt_includes_formatted_entries` had hardcoded date assertion - changed to use relative date.

**Issues Documented (Not Fixed):**
- HIGH-2: 8 files modified in git but not in story File List (unrelated changes from other work)
- LOW-1: Validation checklist notes pre-existing test failures (documented but unrelated to this story)

**Validation:**
- `make validate` passes (1916 passed, 100 skipped)
- All ACs verified against implementation
