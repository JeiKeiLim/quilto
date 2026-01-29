# Story 22.2: Restrict Global Context Scope

Status: done

## Story

As a **Swealog user**,
I want **global context to only contain preferences, goals, and insights**,
so that **it doesn't become a noisy fact dump**.

## Acceptance Criteria

1. **Given** correction or log interaction
   **When** Observer extracts facts
   **Then** per-session facts are NOT stored in global context

2. **Given** user states a preference or goal
   **When** Observer processes
   **Then** preference/goal IS stored in global context

3. **Given** behavioral pattern observed over multiple sessions
   **When** Observer identifies it
   **Then** pattern MAY be stored as insight (not raw facts)

4. **Given** category assignment
   **When** Observer generates update
   **Then** only "preference", "pattern", "fact" (if user-stated), or "insight" are used
   **And** per-session workout data is explicitly excluded

5. **Given** significant_log trigger
   **When** Observer processes
   **Then** only PRs, milestones, and user-stated facts are considered (not workout metrics)

## Tasks / Subtasks

- [x] Task 1: Add `GLOBAL CONTEXT SCOPE (CRITICAL)` section to Observer prompt (AC: #1, #4)
  - [x] 1.1: In `build_prompt()` after line 234 (end of `WHAT NOT TO PERSIST`), add new section
  - [x] 1.2: Define what BELONGS in global context: preferences, goals, behavioral insights, user-stated facts
  - [x] 1.3: Define what does NOT belong: per-session facts, workout metrics, entry-level data
  - [x] 1.4: Add mental model diagram (see Dev Notes)

- [x] Task 2: Update `CATEGORIES` section to clarify scope (AC: #4)
  - [x] 2.1: At lines 207-213, update category descriptions with scope guidance
  - [x] 2.2: "fact" category: Only facts explicitly stated by user, NEVER extracted from single workout
  - [x] 2.3: Add examples showing valid vs invalid category usage

- [x] Task 3: Update trigger-specific formatters with scope restrictions (AC: #1, #3, #5)
  - [x] 3.1: `_format_significant_log_context()` (lines 105-123): Add guidance excluding per-workout metrics; clarify PRs/milestones only
  - [x] 3.2: `_format_correction_context()` (lines 88-103): Add note that corrections update entries not global context; persist only if correction reveals preference

- [x] Task 4: Add scope examples to prompt (AC: #1, #2, #3, #4, #5)
  - [x] 4.1: Add BAD examples: `{"fact": "run_2026-01-26: duration_minutes: 40"}`, `{"fact": "bench pressed 100kg today"}`
  - [x] 4.2: Add GOOD examples: `{"preference": "prefers running in the morning"}`, `{"insight": "typically runs 3x/week based on stated routine"}`

- [x] Task 5: Add tests following Story 22.1 patterns (AC: #1-#5)
  - [x] 5.1: Add `TestGlobalContextScopeRestriction` class in `test_observer.py` (follow `TestUserVsAgentContentDistinction` at lines 938-1149)
  - [x] 5.2: `test_observer_prompt_contains_global_context_scope_section()` - verify section exists
  - [x] 5.3: `test_observer_prompt_excludes_per_session_facts()` - verify exclusion guidance
  - [x] 5.4: `test_observer_prompt_allows_user_stated_preferences()` - verify preference guidance
  - [x] 5.5: `test_observer_prompt_restricts_significant_log_to_milestones()` - verify trigger scope
  - [x] 5.6: `test_observer_prompt_correction_scope_guidance()` - verify correction formatter
  - [x] 5.7: `test_observer_prompt_category_fact_requires_user_stated()` - verify fact category scope
  - [x] 5.8: `test_observer_prompt_contains_mental_model_diagram()` - verify mental model present
  - [x] 5.9: `test_observer_prompt_contains_bad_examples()` and `test_observer_prompt_contains_good_examples()` - verify examples

- [x] Task 6: Run validation (AC: #1-#5)
  - [x] 6.1: `make check` - 0 lint/type errors
  - [x] 6.2: `make validate` - all tests pass

## Dev Notes

### Problem Statement

**Current (NOISE POLLUTION):**
```
Trigger: significant_log
Entry: "40 min run, felt good"
Observer: {"fact": "run_2026-01-26: duration_minutes: 40"}
```
This belongs in PARSED ENTRIES, not global context!

**Expected:**
```
Trigger: significant_log
Entry: "40 min run, felt good"
Observer: {"should_update": false}  -- No milestone, no user-stated preference
```

**Only persist when significant:**
```
Trigger: significant_log
Entry: "Hit new 5K PR: 22:30!"
Observer: {"fact": "5K PR: 22:30", "confidence": "certain", "source": "user stated '5K PR: 22:30'"}
```

### Mental Model (for Task 1.4)

```
GLOBAL CONTEXT (Observer manages):
├── Preferences (user-stated): "I prefer morning workouts"
├── Goals (user-stated): "Training for a marathon"
├── Insights (behavioral patterns): "User typically runs 3x/week"
└── Milestones (achievements): "5K PR: 22:30"

PARSED ENTRIES (Storage) - NOT global context:
├── Per-workout data: "40 min run, pace 5:30/km"
└── Corrections: "Changed duration from 40 to 45 min"
```

### Key Files

| File | Lines | Change |
|------|-------|--------|
| `packages/quilto/quilto/agents/observer.py` | 219-224 | Update `CATEGORIES` descriptions |
| `packages/quilto/quilto/agents/observer.py` | 247-268 | Add `GLOBAL CONTEXT SCOPE (CRITICAL)` section |
| `packages/quilto/quilto/agents/observer.py` | 88-108 | Update `_format_correction_context()` |
| `packages/quilto/quilto/agents/observer.py` | 110-135 | Update `_format_significant_log_context()` |
| `packages/quilto/tests/test_observer.py` | 1172-1357 | Add `TestGlobalContextScopeRestriction` class with 9 tests |

### Architecture Compliance

| Check | Status |
|-------|--------|
| Changes in Quilto (not Swealog) | ✅ Yes |
| Domain-agnostic | ✅ Yes |
| Follows Story 22.1 pattern | ✅ Yes - prompt-level fix with `(CRITICAL)` sections |
| No model changes needed | ✅ Yes - prompt enforcement only |

### Story 22.1 Implementation Reference

Story 22.1 added these sections to `build_prompt()`:
- `USER VS AGENT CONTENT (CRITICAL)` (lines 165-191)
- `SOURCE FIELD REQUIREMENTS (CRITICAL)` (lines 241-251)
- `WHAT NOT TO PERSIST (CRITICAL)` (lines 220-234)

Story 22.1 test patterns (reference for Task 5):
- Test class: `TestUserVsAgentContentDistinction` at `test_observer.py:938-1149`
- Helper: `create_mock_llm_client()` for mocking LLM responses
- Pattern: Build prompt with `ObserverInput`, assert section content exists

This story adds:
- `GLOBAL CONTEXT SCOPE (CRITICAL)` - after line 234
- Updates to existing `CATEGORIES` section (lines 207-213)
- Updates to trigger-specific formatters (lines 88-123)

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Filter in code | Fix at prompt level (source of truth) |
| Add runtime validation | Prompt enforcement is simpler |
| Complex category mapping | Clear examples in prompt |
| Vague scope descriptions | Explicit mental model + examples |

### Testing Patterns (from Story 22.1)

```python
class TestGlobalContextScopeRestriction:
    """Tests for global context scope restriction (Story 22.2)."""

    def test_observer_prompt_contains_global_context_scope_section(self) -> None:
        """Prompt includes GLOBAL CONTEXT SCOPE section."""
        client = create_mock_llm_client({"should_update": False})
        observer = ObserverAgent(client)
        prompt = observer.build_prompt(create_post_query_input())
        assert "GLOBAL CONTEXT SCOPE" in prompt
        assert "CRITICAL" in prompt
```

Where `create_post_query_input()` follows the pattern:
```python
ObserverInput(
    trigger="post_query",
    current_global_context="",
    context_management_guidance="Track preferences",
    query="test query",
    analysis={},
    response="test response",
)
```

### References

- `_bmad-output/planning-artifacts/epics.md:3774-3817` - Story 22.2 requirements
- `tests/eval/feedback/archive/iter-008/analysis.md` - Pattern 5 (per-session fact pollution)
- `_bmad-output/implementation-artifacts/epic-22/22-1-observer-only-persists-user-stated-info.md` - Implementation pattern
- `packages/quilto/tests/test_observer.py:938-1149` - TestUserVsAgentContentDistinction reference

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

(none)

### Completion Notes List

1. **Task 1 (GLOBAL CONTEXT SCOPE section)**: Added comprehensive `GLOBAL CONTEXT SCOPE (CRITICAL)` section to `build_prompt()` with:
   - Mental model diagram showing what BELONGS vs what does NOT belong in global context
   - Explicit scope examples showing BAD (per-session data) vs GOOD (user-stated preferences) patterns
   - Clear separation between global context items (preferences, goals, insights, milestones) and parsed entries

2. **Task 2 (CATEGORIES update)**: Updated `CATEGORIES` section descriptions to clarify:
   - "preference": User-stated preferences ONLY from explicit user statements
   - "pattern": Behavioral patterns user described
   - "fact": User-stated facts ONLY, NEVER extracted from single workout
   - "insight": Correlations derived from user-stated patterns

3. **Task 3 (Trigger formatters)**: Updated trigger-specific formatters:
   - `_format_correction_context()`: Added guidance that corrections primarily UPDATE ENTRIES, not global context; only persist if correction reveals preference
   - `_format_significant_log_context()`: Added SYSTEM ANALYSIS label clarifying per-workout data is NOT for persistence; restricted to user-stated PRs/milestones only

4. **Task 4 (Scope examples)**: BAD and GOOD examples integrated into GLOBAL CONTEXT SCOPE section

5. **Task 5 (Tests)**: Added `TestGlobalContextScopeRestriction` class with 9 tests:
   - `test_observer_prompt_contains_global_context_scope_section`
   - `test_observer_prompt_excludes_per_session_facts`
   - `test_observer_prompt_allows_user_stated_preferences`
   - `test_observer_prompt_restricts_significant_log_to_milestones`
   - `test_observer_prompt_correction_scope_guidance`
   - `test_observer_prompt_category_fact_requires_user_stated`
   - `test_observer_prompt_contains_mental_model_diagram`
   - `test_observer_prompt_contains_bad_examples`
   - `test_observer_prompt_contains_good_examples`

6. **Task 6 (Validation)**: All checks pass:
   - `make check`: 0 lint/type errors
   - `make validate`: 2221 passed, 112 skipped

### File List

| File | Change |
|------|--------|
| `packages/quilto/quilto/agents/observer.py` | Add `GLOBAL CONTEXT SCOPE (CRITICAL)` section with mental model + examples, update `CATEGORIES` with scope guidance, update `_format_correction_context()` and `_format_significant_log_context()` with scope restrictions |
| `packages/quilto/tests/test_observer.py` | Add `TestGlobalContextScopeRestriction` class with 9 tests verifying scope guidance in Observer prompt |

## Change Log

- 2026-01-30: Story 22.2 implemented - Added GLOBAL CONTEXT SCOPE (CRITICAL) section, updated CATEGORIES descriptions, updated trigger formatters with scope restrictions, added 9 tests
