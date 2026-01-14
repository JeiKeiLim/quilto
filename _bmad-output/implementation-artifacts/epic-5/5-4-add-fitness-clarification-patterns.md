# Story 5.4: Add Fitness Clarification Patterns

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Swealog developer**,
I want **fitness-specific clarification patterns**,
so that **clarifying questions are contextually appropriate for fitness**.

## Acceptance Criteria

1. **Given** a fitness query with missing context
   **When** Clarifier generates questions using fitness domain context
   **Then** questions reference fitness-specific factors (sleep, stress, prior workouts, recovery, nutrition)

2. **Given** the ClarifierAgent receives domain vocabulary and expertise
   **When** it builds clarification questions
   **Then** questions use fitness terminology appropriately from the vocabulary

3. **Given** the fitness domain modules (GeneralFitness, Strength, Running, Nutrition)
   **When** clarification_patterns are defined
   **Then** each domain has patterns like:
   - SUBJECTIVE gaps → "How are you feeling today?", "What's your energy level?"
   - CLARIFICATION gaps → "Which specific exercise are you asking about?", "What time period?"

4. **Given** the DomainModule interface
   **When** `clarification_patterns` field is added
   **Then** it is an optional field with sensible defaults (empty dict)
   **And** existing domain modules continue to work without modification

5. **Given** the ClarifierAgent receives clarification_patterns
   **When** building the prompt
   **Then** it incorporates domain-specific question patterns as examples/guidance
   **And** generated questions are more domain-appropriate

6. **Given** fitness-specific clarification patterns
   **When** tested with fitness queries
   **Then** questions are relevant to fitness context (not generic questions)
   **And** questions help gather actionable fitness information

## Tasks / Subtasks

- [x] Task 1: Add `clarification_patterns` field to DomainModule interface (AC: #4)
  - [x] 1.1: Update `packages/quilto/quilto/domain.py`
  - [x] 1.2: Add `clarification_patterns: dict[str, list[str]] = {}` field after `context_management_guidance`
  - [x] 1.3: Add docstring explaining the pattern structure: `{gap_type: [example_questions]}`
  - [x] 1.4: Ensure backward compatibility (empty dict default)
  - [x] 1.5: Verify `DomainModule` is already exported in `quilto.__init__.py` (no change needed)

- [x] Task 2: Update ClarifierAgent to use clarification_patterns (AC: #5)
  - [x] 2.1: Update `packages/quilto/quilto/agents/models.py` - add `clarification_patterns` to `ClarifierInput`
  - [x] 2.2: Update `packages/quilto/quilto/agents/clarifier.py` - `build_prompt()` method
  - [x] 2.3: Add `_format_clarification_patterns()` helper method
  - [x] 2.4: Inject patterns into prompt as domain-specific examples
  - [x] 2.5: Group patterns by gap type (SUBJECTIVE, CLARIFICATION)

- [x] Task 3: Add clarification_patterns to GeneralFitness domain (AC: #1, #3, #6)
  - [x] 3.1: Update `packages/swealog/swealog/domains/general_fitness.py`
  - [x] 3.2: Add SUBJECTIVE patterns: energy level, sleep quality, stress level, motivation
  - [x] 3.3: Add CLARIFICATION patterns: time period, specific activity, workout type
  - [x] 3.4: Ensure patterns use fitness-appropriate terminology

- [x] Task 4: Add clarification_patterns to Strength domain (AC: #1, #2, #3)
  - [x] 4.1: Update `packages/swealog/swealog/domains/strength.py`
  - [x] 4.2: Add SUBJECTIVE patterns: fatigue level, soreness, joint discomfort, warm-up quality
  - [x] 4.3: Add CLARIFICATION patterns: specific lift, rep range intent, equipment available

- [x] Task 5: Add clarification_patterns to Running domain (AC: #1, #2, #3)
  - [x] 5.1: Update `packages/swealog/swealog/domains/running.py`
  - [x] 5.2: Add SUBJECTIVE patterns: breathing comfort, leg heaviness, hydration, temperature feel
  - [x] 5.3: Add CLARIFICATION patterns: distance vs time goal, terrain type, race preparation

- [x] Task 6: Add clarification_patterns to Nutrition domain (AC: #1, #2, #3)
  - [x] 6.1: Update `packages/swealog/swealog/domains/nutrition.py`
  - [x] 6.2: Add SUBJECTIVE patterns: hunger level, satiety, food cravings, digestive comfort
  - [x] 6.3: Add CLARIFICATION patterns: meal timing, portion estimation, macro focus

- [x] Task 7: Create comprehensive unit tests
  - [x] 7.1: Create `packages/quilto/tests/test_clarification_patterns.py`
  - [x] 7.2: Test DomainModule with clarification_patterns field (including empty dict default)
  - [x] 7.3: Test backward compatibility (domain without clarification_patterns works)
  - [x] 7.4: Test ClarifierInput accepts clarification_patterns
  - [x] 7.5: Test ClarifierAgent.build_prompt() includes patterns when provided
  - [x] 7.6: Test ClarifierAgent.build_prompt() handles empty patterns gracefully

- [x] Task 8: Create integration tests
  - [x] 8.1: Test Clarifier with GeneralFitness patterns produces fitness-appropriate questions
  - [x] 8.2: Test Clarifier with Strength patterns produces strength-specific questions
  - [x] 8.3: Test Clarifier with no patterns still produces valid questions

- [x] Task 9: Run validation
  - [x] 9.1: Run `make check` (lint + typecheck) - passed on packages
  - [x] 9.2: Run `make validate` (full validation) - 1102 tests pass
  - [x] 9.3: Run `make test-ollama` (integration tests with real Ollama) - 3/3 pass

## Dev Notes

### Architecture Patterns

- **Quilto changes:** `packages/quilto/quilto/domain.py` (DomainModule interface), `packages/quilto/quilto/agents/clarifier.py` (ClarifierAgent), `packages/quilto/quilto/agents/models.py` (ClarifierInput)
- **Swealog changes:** `packages/swealog/swealog/domains/*.py` (all 4 fitness domain modules)
- **Pattern:** Domain-specific configuration injected into framework agents
- **Location rule:** DomainModule interface is Quilto (framework), clarification_patterns content is Swealog (application)

### clarification_patterns Field Design

The `clarification_patterns` field is a dictionary mapping gap types to example questions:

```python
clarification_patterns: dict[str, list[str]] = {
    "SUBJECTIVE": [
        "How are you feeling right now - energized or tired?",
        "On a scale of 1-10, what's your current energy level?",
    ],
    "CLARIFICATION": [
        "Which specific exercise or activity are you asking about?",
        "What time period should I focus on (today, this week, this month)?",
    ],
}
```

**Key design decisions:**
1. Keys are gap type names (string, not GapType enum) for flexibility
2. Values are example questions that guide the LLM
3. Empty dict means no domain-specific patterns (use generic)
4. Patterns supplement, not replace, the Clarifier's judgment

### ClarifierAgent Enhancement

Update `build_prompt()` to include domain-specific patterns:

```python
def _format_clarification_patterns(self, patterns: dict[str, list[str]]) -> str:
    """Format clarification patterns for the prompt.

    Args:
        patterns: Gap type to example questions mapping. Keys should be
            uppercase strings like "SUBJECTIVE", "CLARIFICATION".

    Returns:
        Formatted string with domain-specific example questions.
    """
    if not patterns:
        return "(No domain-specific patterns provided)"

    lines: list[str] = []
    for gap_type, examples in patterns.items():
        # Display gap_type as-is (expected to be uppercase in patterns dict)
        lines.append(f"For {gap_type} gaps, consider questions like:")
        for example in examples:
            lines.append(f"  - {example}")
        lines.append("")

    return "\n".join(lines).strip()
```

**Prompt enhancement location:** Add after `=== QUESTION GUIDELINES ===` section:

```
=== DOMAIN-SPECIFIC PATTERNS ===
{clarification_patterns_text}

Use these patterns as inspiration. Adapt them to the specific context.
```

### ClarifierInput Model Update

Add to `packages/quilto/quilto/agents/models.py`:

```python
class ClarifierInput(BaseModel):
    """Input for ClarifierAgent."""
    model_config = ConfigDict(strict=True)

    original_query: str = Field(min_length=1)
    gaps: list[Gap]
    vocabulary: dict[str, str]
    retrieval_history: list[RetrievalAttempt]
    previous_clarifications: list[str] = []
    # NEW FIELD
    clarification_patterns: dict[str, list[str]] = {}
```

### Fitness Domain Patterns

**GeneralFitness (base domain):**
```python
clarification_patterns={
    "SUBJECTIVE": [
        "How's your energy level right now - feeling fresh or fatigued?",
        "How well did you sleep last night (roughly)?",
        "Are you dealing with any stress or life factors affecting your training?",
        "On a scale of 1-10, how motivated are you for today's workout?",
    ],
    "CLARIFICATION": [
        "Which specific workout or activity are you asking about?",
        "What time period should I focus on - today, this week, or longer?",
        "Are you asking about a specific type of exercise (cardio, strength, flexibility)?",
    ],
}
```

**Strength domain:**
```python
clarification_patterns={
    "SUBJECTIVE": [
        "How does your body feel today - any lingering soreness from previous workouts?",
        "Are any joints or muscles feeling off or tight?",
        "Did your warm-up sets feel smooth or did something feel heavy?",
        "How's your grip strength feeling today?",
    ],
    "CLARIFICATION": [
        "Which specific lift are you asking about (squat, bench, deadlift, etc.)?",
        "What rep range are you targeting - strength (1-5), hypertrophy (6-12), or endurance (12+)?",
        "Do you have access to your usual equipment, or are you working with substitutes?",
        "Are you comparing to a recent session or your all-time PR?",
    ],
}
```

**Running domain:**
```python
clarification_patterns={
    "SUBJECTIVE": [
        "How did your breathing feel during the run - comfortable or labored?",
        "Did your legs feel fresh or heavy?",
        "Were you well-hydrated before and during?",
        "How did the temperature/weather affect your run?",
    ],
    "CLARIFICATION": [
        "Are you focusing on distance, time, or pace for this run?",
        "What type of terrain - road, trail, or track?",
        "Is this training for a specific race or event?",
        "Should I compare to your recent runs or your best times?",
    ],
}
```

**Nutrition domain:**
```python
clarification_patterns={
    "SUBJECTIVE": [
        "How hungry are you feeling right now?",
        "Are you experiencing any food cravings?",
        "How did your last meal make you feel - satisfied or still hungry?",
        "Any digestive issues or food sensitivities to consider?",
    ],
    "CLARIFICATION": [
        "Which meal are you asking about (breakfast, lunch, dinner, snack)?",
        "Are you tracking specific macros (protein, carbs, fat) or total calories?",
        "What's your current nutritional goal (muscle gain, fat loss, maintenance)?",
        "Should I focus on timing (pre/post workout) or just daily totals?",
    ],
}
```

### DomainModule Field Addition

**Location:** `packages/quilto/quilto/domain.py`

**Add after `context_management_guidance` field (line 71):**

```python
clarification_patterns: dict[str, list[str]] = {}
"""Example questions for clarification, grouped by gap type.

Maps gap type names (SUBJECTIVE, CLARIFICATION) to example questions
that guide the Clarifier agent in asking domain-appropriate questions.

Example:
    clarification_patterns = {
        "SUBJECTIVE": ["How are you feeling today?"],
        "CLARIFICATION": ["Which exercise are you asking about?"],
    }
"""
```

**Update docstring:** Add `clarification_patterns` to the class docstring's Attributes section.

### Testing Standards (from project-context.md)

- **ConfigDict:** All models use `model_config = ConfigDict(strict=True)`
- **Required string fields:** Use `Field(min_length=1)` for required non-empty strings
- **Boundary tests:** Test empty dict, single pattern, multiple patterns
- **Backward compatibility:** Test domains without clarification_patterns field still work
- **All exports:** Verify importable from appropriate packages

### Existing Test Patterns to Follow

| Test Pattern | Reference | Apply To |
|--------------|-----------|----------|
| Model validation tests | `tests/test_router.py` | ClarifierInput with patterns |
| Domain module tests | `packages/swealog/tests/test_domains.py` | Domain clarification_patterns |
| Clarifier tests | `packages/quilto/tests/test_clarifier.py` | build_prompt with patterns |

### Key Implementation Notes

1. **Backward compatibility is critical:** All existing domain modules must continue working without modification. The clarification_patterns field has an empty dict default.

2. **Prompt injection point:** The patterns go in the Clarifier prompt AFTER the question guidelines and BEFORE the output format. They serve as domain-specific examples.

3. **Gap type keys:** Use UPPERCASE string keys ("SUBJECTIVE", "CLARIFICATION") in clarification_patterns dict. Note: GapType enum uses lowercase values (`subjective`, `clarification`) but the prompt displays them uppercase. Use uppercase keys for pattern matching in the prompt formatting.

4. **Pattern granularity:** Patterns should be specific enough to guide the LLM but generic enough to apply to various contexts within the domain.

5. **No enforcement:** Patterns are suggestions, not constraints. The Clarifier can still generate questions outside these patterns if contextually appropriate.

### Common Mistakes to Avoid (from project-context.md)

| Mistake | Correct Pattern |
|---------|-----------------|
| Required string without length check | Use `Field(min_length=1)` |
| Missing `__all__` in `__init__.py` | Export all public classes in `__all__` list |
| Both `Field()` AND `@field_validator` for range | Use only `Field(ge=, le=)` |
| Missing boundary value tests | Test empty dict, single pattern, multiple patterns |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.4]
- [Source: packages/quilto/quilto/domain.py] - DomainModule interface
- [Source: packages/quilto/quilto/agents/clarifier.py] - ClarifierAgent implementation
- [Source: packages/quilto/quilto/agents/models.py] - ClarifierInput model
- [Source: packages/swealog/swealog/domains/general_fitness.py] - GeneralFitness domain
- [Source: packages/swealog/swealog/domains/strength.py] - Strength domain
- [Source: packages/swealog/swealog/domains/running.py] - Running domain
- [Source: packages/swealog/swealog/domains/nutrition.py] - Nutrition domain
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 12.8 Clarifier Prompt]
- [Source: _bmad-output/project-context.md#Common Mistakes to Avoid]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

1. Added `clarification_patterns: dict[str, list[str]] = {}` field to DomainModule in `packages/quilto/quilto/domain.py`
2. Added `clarification_patterns` field to ClarifierInput in `packages/quilto/quilto/agents/models.py`
3. Added `_format_clarification_patterns()` helper method to ClarifierAgent in `packages/quilto/quilto/agents/clarifier.py`
4. Updated `build_prompt()` to include a `=== DOMAIN-SPECIFIC PATTERNS ===` section with formatted patterns
5. Added fitness-specific clarification patterns to all 4 domain modules (GeneralFitness, Strength, Running, Nutrition)
6. Created comprehensive unit tests in `packages/quilto/tests/test_clarification_patterns.py` covering:
   - DomainModule field with empty/populated patterns and backward compatibility
   - ClarifierInput with patterns
   - ClarifierAgent.build_prompt() with patterns inclusion
   - _format_clarification_patterns() helper method
7. Integration tests with real Ollama pass (3/3 tests pass)
8. All 1102 unit tests pass
9. Pre-existing lint issues in `scripts/convert_obsidian.py` are not related to this story

### File List

**Quilto (Framework) - Modified:**
- `packages/quilto/quilto/domain.py` - Add `clarification_patterns` field to DomainModule
- `packages/quilto/quilto/agents/models.py` - Add `clarification_patterns` to ClarifierInput
- `packages/quilto/quilto/agents/clarifier.py` - Update `build_prompt()` with pattern formatting

**Swealog (Application) - Modified:**
- `packages/swealog/swealog/domains/general_fitness.py` - Add clarification_patterns
- `packages/swealog/swealog/domains/strength.py` - Add clarification_patterns
- `packages/swealog/swealog/domains/running.py` - Add clarification_patterns
- `packages/swealog/swealog/domains/nutrition.py` - Add clarification_patterns

**Tests - Created:**
- `packages/quilto/tests/test_clarification_patterns.py` - Unit tests for clarification patterns

