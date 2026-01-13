# Story 4.4: Add Fitness Expertise and Evaluation Rules

Status: done

## Story

As a **Swealog developer**,
I want **fitness-specific expertise and evaluation rules in domain modules**,
so that **fitness queries get domain-appropriate analysis and responses**.

## Acceptance Criteria

1. **Given** GeneralFitness, Strength, Nutrition, and Running domains
   **When** expertise and evaluation rules are enhanced
   **Then** Analyzer uses fitness knowledge (progressive overload, recovery, etc.)

2. **Given** domain modules with `response_evaluation_rules`
   **When** Evaluator checks response
   **Then** it applies domain-specific rules (e.g., "never recommend exercises for injured body parts")

3. **Given** `scripts/manual_test.py`
   **When** `get_evaluation_rules` function is called
   **Then** it correctly accesses `response_evaluation_rules` field (not `evaluation_rules`)

4. **Given** query flow through Analyzer
   **When** fitness-related query is analyzed
   **Then** domain expertise from `expertise` field is visible in the prompt

5. **Given** query flow through Evaluator
   **When** fitness response is evaluated
   **Then** domain safety rules from `response_evaluation_rules` are checked

6. **Given** multi-domain query (e.g., "compare running vs strength training")
   **When** domains are combined
   **Then** expertise is concatenated with domain labels and evaluation rules are merged

7. **Given** the existing domain modules
   **When** reviewed for completeness
   **Then** all four domains (GeneralFitness, Strength, Nutrition, Running) have comprehensive `expertise` and `response_evaluation_rules`

## Tasks / Subtasks

- [x] Task 1: Fix `get_evaluation_rules` function in manual_test.py (AC: #3)
  - [x] 1.1: Change `module.evaluation_rules` to `module.response_evaluation_rules`
  - [x] 1.2: Verify the fix works by running `python scripts/manual_test.py` with a QUERY input

- [x] Task 2: Review and enhance GeneralFitness domain expertise (AC: #1, #7)
  - [x] 2.1: Review current expertise in `packages/swealog/swealog/domains/general_fitness.py`
  - [x] 2.2: Ensure expertise covers: progressive overload, recovery principles, activity categorization
  - [x] 2.3: Verify `response_evaluation_rules` includes safety rules (no overtraining, injury prevention)

- [x] Task 3: Review and enhance Strength domain expertise (AC: #1, #7)
  - [x] 3.1: Review current expertise in `packages/swealog/swealog/domains/strength.py`
  - [x] 3.2: Ensure expertise covers: rep ranges (strength/hypertrophy/endurance), RPE/RIR scales, compound lifts, volume calculation, periodization
  - [x] 3.3: Verify `response_evaluation_rules` includes: no max effort without warmup, experience level consideration, overtraining flags

- [x] Task 4: Review and enhance Nutrition domain expertise (AC: #1, #7)
  - [x] 4.1: Review current expertise in `packages/swealog/swealog/domains/nutrition.py`
  - [x] 4.2: Ensure expertise covers: macro ratios, protein needs, meal timing, hydration
  - [x] 4.3: Verify `response_evaluation_rules` includes: no extreme calorie restriction, goal consideration, eating disorder awareness

- [x] Task 5: Review and enhance Running domain expertise (AC: #1, #7)
  - [x] 5.1: Review current expertise in `packages/swealog/swealog/domains/running.py`
  - [x] 5.2: Ensure expertise covers: pace zones, 10% rule, workout types, race distances
  - [x] 5.3: Verify `response_evaluation_rules` includes: mileage limits, injury prevention, environmental factors

- [x] Task 6: Verify integration with Analyzer agent (AC: #1, #4)
  - [x] 6.1: Confirm `AnalyzerAgent.build_prompt()` includes `domain_context.expertise` in the prompt (line 252 in analyzer.py)
  - [x] 6.2: Verify `ActiveDomainContext` correctly merges expertise from multiple domains (see `build_active_domain_context()` in manual_test.py)
  - [x] 6.3: Run `python scripts/manual_test.py --storage-dir ./data "How has my bench press progressed?"` and verify expertise appears in Analyzer output

- [x] Task 7: Verify integration with Evaluator agent (AC: #2, #5)
  - [x] 7.1: Confirm `EvaluatorAgent.build_prompt()` includes evaluation_rules via `_format_evaluation_rules()` (line 155 in evaluator.py)
  - [x] 7.2: Verify `get_evaluation_rules()` correctly accesses `response_evaluation_rules` (after fixing Task 1)
  - [x] 7.3: Run `python scripts/manual_test.py --storage-dir ./data "How has my bench press progressed?"` and verify rules appear in Evaluator output

- [x] Task 8: Test multi-domain combination (AC: #6)
  - [x] 8.1: Verify `build_active_domain_context()` in manual_test.py merges expertise with `" | "` separator AND domain labels (line 172)
  - [x] 8.2: Verify `get_evaluation_rules()` concatenates rules from multiple domains via `rules.extend()`
  - [x] 8.3: Run `python scripts/manual_test.py --storage-dir ./data "How does my running affect my strength gains?"` and verify multiple domain expertise/rules appear

- [x] Task 9: Add unit tests for domain integration (AC: #1-#7)
  - [x] 9.1: Create `packages/swealog/tests/test_domain_integration.py`
  - [x] 9.2: Test that each domain has non-empty `expertise` field
  - [x] 9.3: Test that each domain has non-empty `response_evaluation_rules` list
  - [x] 9.4: Test expertise and rules are accessible via domain module instances
  - [x] 9.5: Test multi-domain expertise merging

- [x] Task 10: Run validation
  - [x] 10.1: Run `make check` (lint + typecheck)
  - [x] 10.2: Run `make validate` (full validation)
  - [x] 10.3: Run `make test-ollama` (integration tests)

## Dev Notes

### Validation Summary (2026-01-14)

Story validated against source documents and codebase. Key findings:

| Item | Status | Details |
|------|--------|---------|
| Bug in `get_evaluation_rules()` | **CONFIRMED** | Line 502-504 uses `evaluation_rules` instead of `response_evaluation_rules` |
| Domain expertise fields | **GOOD** | All 4 domains have comprehensive expertise |
| Domain evaluation rules | **GOOD** | GeneralFitness: 4, Strength: 7, Nutrition: 7, Running: 8 rules |
| Analyzer integration | **VERIFIED** | `analyzer.py:252` includes `domain_context.expertise` |
| Evaluator integration | **VERIFIED** | `evaluator.py:155` includes rules via `_format_evaluation_rules()` |
| Multi-domain merge | **PARTIAL** | Expertise merged with `" | "` but **without domain labels** (AC #6 mentions labels) |

**Action Required:** Developer should decide if AC #6's "domain labels" requirement means adding labels like `[Strength] ...expertise... | [Running] ...expertise...` or if current implementation is sufficient.

### Architecture Patterns

- **Location:** Domain modules in `packages/swealog/swealog/domains/`
- **Integration Point 1:** Analyzer receives expertise via `ActiveDomainContext.expertise`
- **Integration Point 2:** Evaluator receives rules via `EvaluatorInput.evaluation_rules`
- **Bug Fix Required:** `manual_test.py` uses wrong field name `evaluation_rules` instead of `response_evaluation_rules`

### Current Domain Module State

All four domains already have `expertise` and `response_evaluation_rules` populated:

| Domain | Expertise Coverage | Rules Count |
|--------|-------------------|-------------|
| GeneralFitness | Progressive overload, recovery, activity categorization, RPE | 4 rules |
| Strength | Rep ranges, RPE/RIR, compound lifts, volume, periodization | 7 rules |
| Nutrition | Macros, protein needs, meal timing, hydration, estimation | 7 rules |
| Running | Pace zones, 10% rule, workout types, heart rate, race distances | 8 rules |

### Bug Fix: get_evaluation_rules()

**Current (buggy):**
```python
if hasattr(module, "evaluation_rules"):
    rules.extend(module.evaluation_rules)
```

**Fixed:**
```python
if hasattr(module, "response_evaluation_rules"):
    rules.extend(module.response_evaluation_rules)
```

### DomainModule Interface (from quilto/domain.py)

```python
class DomainModule(BaseModel):
    name: str
    description: str
    log_schema: type[BaseModel]
    vocabulary: dict[str, str]
    expertise: str = ""                          # For Analyzer/Planner
    response_evaluation_rules: list[str] = []    # For Evaluator
    context_management_guidance: str = ""        # For Observer
```

### Integration Verification

**Analyzer prompt includes expertise:**
```python
# In AnalyzerAgent.build_prompt()
=== DOMAIN EXPERTISE ===

{domain_context.expertise or "(No specific expertise defined)"}
```

**Evaluator prompt includes rules:**
```python
# In EvaluatorAgent.build_prompt()
=== DOMAIN SAFETY RULES ===
{rules_text}
```

### Multi-Domain Expertise Merging (from manual_test.py lines 152-172)

```python
expertise_parts: list[str] = []

for name in selected_domains:
    if name in domain_modules:
        module = domain_modules[name]
        expertise_parts.append(module.expertise)

# Merged with separator (line 172)
expertise=" | ".join(expertise_parts) if expertise_parts else "General fitness tracking"
```

**Note:** Currently merges expertise without domain labels. AC #6 mentions "expertise is concatenated with domain labels" - the current implementation does NOT include domain labels in the separator. Consider if this enhancement is needed or if the story AC should be clarified.

### Testing Strategy

1. **Unit tests:** Verify domain modules have non-empty expertise and rules
2. **Integration tests:** Run actual queries through the full pipeline
3. **Manual verification:** Use manual_test.py to observe expertise in prompts

### Project Structure Notes

- Domain modules are in **Swealog** (`packages/swealog/`) - fitness-specific
- Agent implementations are in **Quilto** (`packages/quilto/`) - framework code
- This story modifies Swealog domain modules and fixes Swealog's manual_test.py

### Previous Story Learnings (Story 4-1, 4-2, 4-3)

1. **Use ConfigDict(strict=True)** for all Pydantic models
2. **Field(min_length=1)** for required string fields
3. **Run `make test-ollama`** before marking story complete
4. **Verify all ACs against implementation** during code review

### Fitness Expertise Examples (for reference)

**Progressive Overload (GeneralFitness):**
- Gradually increasing stress on musculoskeletal system
- Methods: increase weight, reps, sets, or decrease rest

**RPE Scale (Strength):**
- 6 = easy, could do many more
- 7 = moderate, 3-4 reps left
- 8 = challenging, 2-3 reps left
- 9 = hard, 1 rep left
- 10 = maximum effort

**10% Rule (Running):**
- Don't increase weekly mileage by more than 10%
- Prevents overuse injuries

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.4]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 8 Domain Module Interface]
- [Source: packages/quilto/quilto/domain.py] - DomainModule interface
- [Source: packages/quilto/quilto/agents/analyzer.py] - Uses expertise
- [Source: packages/quilto/quilto/agents/evaluator.py] - Uses evaluation_rules
- [Source: packages/swealog/swealog/domains/] - All domain modules
- [Source: scripts/manual_test.py] - Integration point with bug

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Bug Fix (AC #3):** Fixed `get_evaluation_rules()` in `scripts/manual_test.py` - changed `module.evaluation_rules` to `module.response_evaluation_rules` at lines 502-504.

2. **Domain Labels (AC #6):** Enhanced `build_active_domain_context()` to add domain labels when merging expertise. Now outputs format: `[Strength] ...expertise... | [Running] ...expertise...` instead of just `...expertise... | ...expertise...`.

3. **Domain Review (AC #1, #7):** Verified all four domains have comprehensive expertise and evaluation rules:
   - GeneralFitness: 4 rules (overtraining, recovery, fitness level, injury prevention)
   - Strength: 7 rules (warmup, experience, overtraining, weight recs, deload, pain, recovery)
   - Nutrition: 7 rules (calorie restriction, goals, disordered eating, macros, food choices, culture, dietitian)
   - Running: 8 rules (mileage 10%, fitness level, overtraining, rest days, pain, environment, mileage buildup, injuries)

4. **Unit Tests (AC #1-#7):** Created `packages/swealog/tests/test_domain_integration.py` with 35 tests covering:
   - Domain expertise field presence and content
   - Domain evaluation rules field presence and safety coverage
   - DomainModule interface compliance
   - Multi-domain expertise merging with labels
   - Multi-domain evaluation rules merging
   - New: `get_evaluation_rules()` logic regression tests (3 tests added during code review)

5. **Validation:** All tests pass:
   - `make check`: lint + typecheck pass
   - `make validate`: All unit tests pass
   - `make test-ollama`: Integration tests pass

### Code Review Fixes Applied

1. **Added regression tests for `get_evaluation_rules()` bug** - 3 new tests in `TestGetEvaluationRulesLogic` class
2. **Strengthened vocabulary test** - Now validates both keys and values are non-empty strings
3. **Fixed weak assertion pattern** - Changed `"1-5"` to `"rep"` in strength expertise test

### File List

**Files Modified:**
- `scripts/manual_test.py` - Fixed `get_evaluation_rules()` bug AND added domain labels to expertise merging

**Files Created:**
- `packages/swealog/tests/test_domain_integration.py` - 35 unit tests for domain module integration (32 original + 3 code review fixes)

**Files Verified (read-only):**
- `packages/swealog/swealog/domains/general_fitness.py` - expertise and 4 rules confirmed
- `packages/swealog/swealog/domains/strength.py` - expertise and 7 rules confirmed
- `packages/swealog/swealog/domains/nutrition.py` - expertise and 7 rules confirmed
- `packages/swealog/swealog/domains/running.py` - expertise and 8 rules confirmed
- `packages/quilto/quilto/agents/analyzer.py:252` - expertise integration confirmed
- `packages/quilto/quilto/agents/evaluator.py:155` - evaluation rules integration confirmed
- `packages/quilto/quilto/domain.py` - DomainModule interface reference

