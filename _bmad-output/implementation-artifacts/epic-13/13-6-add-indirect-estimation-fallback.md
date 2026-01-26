# Story 13.6: Add Indirect Estimation Fallback in Analyzer

Status: done

## Story

As a **Quilto user**,
I want **the system to provide indirect estimates when direct data is missing**,
So that **I get useful answers with appropriate disclaimers instead of "no data" responses**.

## Background

**Origin:** Dogfooding Iteration 3 (Epic 13)
**Source:** `tests/eval/feedback/archive/iter-002/analysis.md` - Pattern 12: Analyzer Should Attempt Indirect Estimation
**Priority:** Low | **Effort:** Medium (2-4 hours)
**Type:** Enhancement - Analyzer and Synthesizer prompt logic

**Key Evidence (Record `151de3d9`):**
- User query: "What is my 1RM bench press?"
- Retrieved entries: Only incline dumbbell press records (no direct bench press)
- Analyzer verdict: "insufficient" - stopped without attempting estimation
- User feedback: System should have tried indirect 1RM estimation and notified user it was indirect

**Current vs Desired Behavior:**

| Scenario | Current | Desired |
|----------|---------|---------|
| No direct data, related data exists | verdict="insufficient", no answer | verdict="partial", indirect estimate with disclaimers |
| No direct data, no related data | verdict="insufficient", no answer | verdict="insufficient", explain what data is needed |
| Direct data exists | Normal analysis | No change (don't regress) |

## Acceptance Criteria

1. **Given** query for bench press 1RM with only incline press data available
   **When** Analyzer finds no direct bench press records
   **Then** it attempts indirect estimation using incline press records and includes findings with `indirect_estimate: true`

2. **Given** indirect estimation is performed
   **When** Synthesizer generates response
   **Then** the response clearly states "This is an indirect estimate based on [related exercise]"
   **And** includes the methodology used (e.g., "Using 80% conversion from incline to flat bench...")

3. **Given** multiple related exercises in logs (e.g., incline press + dumbbell bench)
   **When** calculating indirect estimate
   **Then** the system combines information to provide a more informed estimate
   **And** notes which exercises were used in the calculation

4. **Given** insufficient data for even indirect estimation
   **When** no related exercises exist in the date range
   **Then** verdict remains "insufficient" (no change from current behavior)
   **And** response explains what data would be needed for estimation

5. **Given** direct data exists for the query
   **When** Analyzer processes entries
   **Then** direct calculation is used (no regression to indirect estimation unnecessarily)

6. **Given** Korean exercise names in logs (e.g., "인클라인 프레스")
   **When** Analyzer processes for English query
   **Then** exercise relationships are recognized cross-language

## Tasks / Subtasks

- [x] Task 1: Update Analyzer prompt for indirect estimation (AC: #1, #3, #4, #5, #6)
  - [x] 1.1: Add `=== INDIRECT ESTIMATION ===` section after `=== TEMPORAL RULES ===` (~line 340)
  - [x] 1.2: Add EXERCISE RELATIONSHIPS table with conversion factors and Korean names
  - [x] 1.3: Add REP-MAX CONVERSIONS with Brzycki formula reference
  - [x] 1.4: Add INDIRECT ESTIMATION RULES with clear when/how/what guidance
  - [x] 1.5: Add worked example showing calculation chain

- [x] Task 2: Add fields to Finding model (AC: #1, #2)
  - [x] 2.1: Add `indirect_estimate: bool = Field(default=False)` to Finding (models.py line 527)
  - [x] 2.2: Add `estimation_methodology: str | None = Field(default=None)` to Finding
  - [x] 2.3: Update Finding docstring with new attributes
  - **Note:** Finding already exported in `__init__.py` - no export changes needed

- [x] Task 3: Update Synthesizer prompt for indirect estimation disclosure (AC: #2, #3)
  - [x] 3.1: Add `=== INDIRECT ESTIMATION DISCLOSURE ===` section after `=== TEMPORAL AWARENESS ===` (~line 245)
  - [x] 3.2: Add required disclosure rules for indirect_estimate=true findings
  - [x] 3.3: Add example phrasing template

- [x] Task 4: Add unit tests for indirect estimation (AC: #1, #2, #4, #5)
  - [x] 4.1: Test Finding model accepts new fields with defaults
  - [x] 4.2: Test Analyzer prompt contains INDIRECT ESTIMATION section
  - [x] 4.3: Test Synthesizer prompt contains INDIRECT ESTIMATION DISCLOSURE section
  - [x] 4.4: Mock test: indirect_estimate=true finding processed correctly
  - **Pattern:** Reuse `create_mock_llm_client()` from test_analyzer.py:54-75

- [x] Task 5: Run validation
  - [x] 5.1: Run `make check` (lint + typecheck)
  - [x] 5.2: Run `make validate` (full validation)

## Dev Notes

### File Changes Summary

| File | Change | Location |
|------|--------|----------|
| `packages/quilto/quilto/agents/models.py` | Add 2 fields to Finding | Line 527 (after `confidence` field) |
| `packages/quilto/quilto/agents/analyzer.py` | Add INDIRECT ESTIMATION prompt section | After line ~340 (TEMPORAL RULES) |
| `packages/quilto/quilto/agents/synthesizer.py` | Add INDIRECT ESTIMATION DISCLOSURE section | After line ~245 (TEMPORAL AWARENESS) |
| `packages/quilto/tests/test_analyzer.py` | Add new test class | ~50 lines |
| `packages/quilto/tests/test_synthesizer.py` | Add new test methods | ~30 lines |

### Finding Model Update

Add after line 527 in `models.py`:

```python
class Finding(BaseModel):
    """A pattern or insight discovered by the Analyzer.

    Attributes:
        claim: The insight or finding text.
        evidence: References to specific entries/dates supporting the claim.
        confidence: Confidence level in this finding (high, medium, low).
        indirect_estimate: True if this finding is based on indirect estimation.
        estimation_methodology: Explanation of how indirect estimate was calculated.
    """
    model_config = ConfigDict(strict=True)

    claim: str = Field(min_length=1)
    evidence: list[str]
    confidence: Literal["high", "medium", "low"]
    indirect_estimate: bool = Field(default=False)
    estimation_methodology: str | None = Field(default=None)
```

### Analyzer Prompt Addition (after TEMPORAL RULES section)

```
=== INDIRECT ESTIMATION ===

When direct data is missing but RELATED data exists, attempt indirect estimation:

EXERCISE RELATIONSHIPS (strength training):
| Exercise A | Exercise B | A → B Factor | Korean |
|------------|-----------|--------------|--------|
| Incline Bench | Flat Bench | ×1.15-1.25 | 인클라인 프레스 |
| Dumbbell Press | Barbell Bench | ×0.90-0.95 | 덤벨 벤치프레스 |
| Close-Grip Bench | Wide-Grip Bench | ×1.05-1.10 | |
| Front Squat | Back Squat | ×1.20-1.30 | |

REP-MAX CONVERSIONS (Brzycki formula):
1RM = weight × (36 / (37 - reps))
Quick factors: 3 reps → ×1.08, 5 reps → ×1.15, 8 reps → ×1.26, 10 reps → ×1.33

INDIRECT ESTIMATION RULES:
1. Query asks for specific exercise data (e.g., "bench press 1RM")
2. AND no direct records exist in retrieved entries
3. AND related exercise records exist (e.g., incline press, dumbbell bench)
4. THEN:
   - Calculate indirect estimate using relationship factors
   - Set indirect_estimate=true
   - Set estimation_methodology with calculation explanation
   - Set confidence="low"
   - verdict can be "partial" (not "insufficient")

Example: Query "bench press 1RM?" with data "인클라인 프레스 50kg x 5회"
→ Incline 5RM=50kg → Incline 1RM=57.5kg (×1.15) → Flat bench 1RM≈69kg (×1.20)
→ Finding: claim="Estimated bench 1RM ~69kg", indirect_estimate=true, confidence="low"
```

### Synthesizer Prompt Addition (after TEMPORAL AWARENESS section)

```
=== INDIRECT ESTIMATION DISCLOSURE ===

When findings contain indirect_estimate=true:
1. State clearly this is an ESTIMATE, not actual recorded data
2. Include methodology from estimation_methodology field
3. Acknowledge uncertainty (confidence is typically "low")
4. Suggest what direct data would improve the estimate

NEVER present indirect estimates as definitive answers.
ALWAYS include methodology and acknowledge uncertainty.
```

### Edge Cases

| Case | Handling |
|------|----------|
| Query for running pace, have strength data only | No indirect estimation (unrelated domains) |
| Query for bench, have both direct and indirect data | Use direct data, ignore indirect |
| Multiple related exercises (incline + dumbbell) | Combine for better estimate, note both sources |
| Very old related data (>30 days) | Still estimate but note data age |

### Validation Checklist

Before marking complete:
- [x] `make check` passes
- [x] `make validate` passes
- [x] Finding model accepts new optional fields with defaults
- [x] Analyzer prompt contains INDIRECT ESTIMATION section
- [x] Synthesizer prompt contains INDIRECT ESTIMATION DISCLOSURE section
- [x] Tests verify prompt content changes
- [x] No regressions in existing tests

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Clean implementation with no debug issues.

### Completion Notes List

1. Added `=== INDIRECT ESTIMATION ===` section to Analyzer prompt with:
   - EXERCISE RELATIONSHIPS table with conversion factors (Incline→Flat, Dumbbell→Barbell, etc.) and Korean names
   - REP-MAX CONVERSIONS with Brzycki formula and quick factors
   - INDIRECT ESTIMATION RULES explaining when and how to estimate
   - Worked example showing calculation chain from "인클라인 프레스 50kg x 5회" to bench 1RM

2. Added two new fields to Finding model:
   - `indirect_estimate: bool = Field(default=False)` - marks finding as indirect estimate
   - `estimation_methodology: str | None = Field(default=None)` - explains calculation method

3. Added `=== INDIRECT ESTIMATION DISCLOSURE ===` section to Synthesizer prompt with:
   - Required disclosure rules for indirect estimates
   - Example phrasing template for user-facing responses

4. Added comprehensive unit tests:
   - 6 new tests for Finding model's new fields
   - 7 new tests for Analyzer prompt INDIRECT ESTIMATION section
   - 4 new tests for Synthesizer prompt INDIRECT ESTIMATION DISCLOSURE section
   - 1 mock integration test for indirect_estimate=true finding flow

5. All validations pass: `make validate` (1921 passed, 101 skipped)

### File List

| File | Change |
|------|--------|
| `packages/quilto/quilto/agents/models.py` | Added `indirect_estimate` and `estimation_methodology` fields to Finding model, updated docstring |
| `packages/quilto/quilto/agents/analyzer.py` | Added INDIRECT ESTIMATION prompt section with exercise relationships, rep-max conversions, rules, and example; updated output schema |
| `packages/quilto/quilto/agents/synthesizer.py` | Added INDIRECT ESTIMATION DISCLOSURE prompt section with rules and example phrasing; Updated `_format_analysis` to display indirect_estimate markers |
| `packages/quilto/tests/test_analyzer.py` | Added 14 new tests for Finding model fields and Analyzer prompt changes |
| `packages/quilto/tests/test_synthesizer.py` | Added 6 new tests for Synthesizer prompt INDIRECT ESTIMATION DISCLOSURE section and `_format_analysis` helper |

### Known Issues / Future Improvements

1. **Domain-specific exercise relationships**: The exercise relationship table is hard-coded in the prompt. Future iterations could make this configurable via domain modules.

2. **Cross-domain estimation**: Currently only supports strength training estimation. Similar patterns could be added for cardio (e.g., swim pace → running pace conversion) in future stories.

3. **Language-specific prompt patterns**: As noted in tech debt (4d8bfbb), embedding Korean vocabulary in prompts doesn't scale well. Consider extracting to domain configuration in future refactoring.
