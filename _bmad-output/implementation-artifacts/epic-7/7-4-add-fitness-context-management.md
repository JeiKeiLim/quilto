# Story 7.4: Add Fitness Context Management

Status: done

## Story

As a **Swealog developer**,
I want **fitness-specific context management guidance**,
so that **Observer tracks fitness-relevant patterns**.

## Background

This is the fourth and final story in Epic 7 (Learning & Personalization). Stories 7.1-7.3 implemented the Observer agent, global context storage, and trigger system in Quilto. This story implements fitness-specific guidance for Swealog by:

1. **Enhancing `context_management_guidance`** in existing fitness domain modules (already have basic guidance - need enhancement)
2. **Creating fitness-specific SignificantEntryDetector** implementations
3. **Testing Observer's fitness context tracking** with real fitness data

**Key Characteristics:**
- **Domain-specific implementation:** This story is in Swealog (`packages/swealog/`), NOT Quilto
- **Enhances existing modules:** GeneralFitness, Strength, Running, Nutrition, Swimming already have `context_management_guidance`
- **Implements FR-A10:** Context management guidance for Observer (from architecture)

**Architecture Context:**
- Quilto provides: Observer, GlobalContextManager, trigger system, SignificantEntryDetector protocol
- Swealog provides: Fitness-specific guidance, fitness-specific significant entry detection
- Observer uses `context_management_guidance` from active domains to know what patterns to track

## Acceptance Criteria

1. **Given** Observer integration with fitness domains
   **When** Observer processes fitness logs using domain guidance
   **Then** it extracts fitness-relevant patterns (PRs, frequency, recovery)
   **And** generates context updates with appropriate category/confidence
   **And** domain `context_management_guidance` informs pattern prioritization
   **Note:** This AC is validated through ACs #2-8 comprehensive coverage

2. **Given** the GeneralFitness domain module
   **When** Observer uses its context_management_guidance
   **Then** guidance covers:
   - Workout frequency (days per week)
   - Activity type distribution (strength vs cardio ratio)
   - Effort level trends (average RPE over time)
   - General engagement patterns (consistency, gaps)
   - Flags for sudden intensity spikes, extended rest periods

3. **Given** the Strength domain module
   **When** Observer uses its context_management_guidance
   **Then** guidance covers:
   - Exercise PRs (weight × reps for major lifts)
   - Training frequency per muscle group
   - Volume progression (weekly tonnage trends)
   - Intensity patterns (average RPE trends)
   - Flags for strength drops, training gaps, high RPE streaks
   - Correlations: performance vs sleep, strength vs bodyweight

4. **Given** the Running domain module
   **When** Observer uses its context_management_guidance
   **Then** guidance covers:
   - Weekly mileage totals and trends
   - Average pace progression by workout type
   - Long run distance progression
   - Workout type balance (easy vs hard runs)
   - Flags for mileage spikes, consecutive hard days, pace declines
   - Correlations: pace vs heart rate, performance vs recovery

5. **Given** the Nutrition domain module
   **When** Observer uses its context_management_guidance
   **Then** guidance covers:
   - Average daily calories (rolling average)
   - Macro distribution patterns
   - Protein intake relative to goals
   - Meal timing consistency
   - Flags for calorie variance, fasting periods, low protein
   - Correlations: nutrition vs workout performance

6. **Given** the Swimming domain module
   **When** Observer uses its context_management_guidance
   **Then** guidance covers:
   - Weekly distance totals and trends
   - Stroke distribution (% freestyle vs others)
   - Equipment usage frequency
   - Pace progression per 100m
   - Flags for volume spikes, consecutive hard sessions, pace declines
   - Correlations: pace vs equipment, performance vs rest days

7. **Given** FitnessSignificantEntryDetector class
   **When** evaluating a fitness entry
   **Then** it detects:
   - PR indicators (personal record, new PR, beat PR)
   - Milestone completions (first 5K, 100th workout, marathon debut)
   - Competition/race mentions
   - Injury or pain mentions (for cautionary tracking)
   - Major weight milestones (for strength training)

8. **Given** Observer integration tests with fitness domains
   **When** running with real Ollama
   **Then** Observer correctly extracts fitness patterns
   **And** updates include appropriate fitness categories (fact/pattern/insight)
   **And** confidence levels are appropriate (tentative for first observation, certain for PRs)

## Tasks / Subtasks

### Group A: Review and Enhance Existing Guidance

- [x] Task 1: Review existing context_management_guidance (AC: #2-6)
  - [x] 1.1: Read current guidance in all 5 fitness domain modules
  - [x] 1.2: Document gaps or improvements needed based on AC requirements
  - [x] 1.3: Identify any missing pattern categories
  - **VERIFIED:** All 5 domain modules already satisfy AC requirements. No modifications needed.

- [x] Task 2: Enhance GeneralFitness context_management_guidance (AC: #2)
  - [x] 2.1: Ensure guidance includes: workout frequency, activity distribution, effort trends, engagement patterns
  - [x] 2.2: Add explicit flags section: sudden intensity spikes, extended rest periods, dramatic volume changes
  - [x] 2.3: Add correlations section if missing
  - **VERIFIED:** Existing guidance already covers all AC requirements.

- [x] Task 3: Enhance Strength context_management_guidance (AC: #3)
  - [x] 3.1: Ensure guidance includes: PRs for major lifts, muscle group frequency, volume progression, intensity patterns
  - [x] 3.2: Add explicit flags: strength drops >10%, training gaps >7 days, high RPE streaks
  - [x] 3.3: Add correlations: performance vs sleep, strength vs bodyweight
  - **VERIFIED:** Existing guidance already covers all AC requirements.

- [x] Task 4: Enhance Running context_management_guidance (AC: #4)
  - [x] 4.1: Ensure guidance includes: weekly mileage, pace by workout type, long run progression, workout balance
  - [x] 4.2: Add explicit flags: mileage spikes >10%, consecutive hard days, pace decline >10%
  - [x] 4.3: Add correlations: pace vs heart rate (cardiac drift), performance vs recovery
  - **VERIFIED:** Existing guidance already covers all AC requirements.

- [x] Task 5: Enhance Nutrition context_management_guidance (AC: #5)
  - [x] 5.1: Ensure guidance includes: daily calories, macro distribution, protein vs goals, meal timing
  - [x] 5.2: Add explicit flags: calorie variance >500, extended fasting, protein under target
  - [x] 5.3: Add correlations: nutrition vs workout performance, weekend vs weekday patterns
  - **VERIFIED:** Existing guidance already covers all AC requirements.

- [x] Task 6: Enhance Swimming context_management_guidance (AC: #6)
  - [x] 6.1: Ensure guidance includes: weekly distance, stroke distribution, equipment usage, pace per 100m
  - [x] 6.2: Add explicit flags: volume spikes >10%, consecutive hard sessions, pace decline
  - [x] 6.3: Add correlations: pace vs equipment, performance vs rest days, technique notes vs pace
  - **VERIFIED:** Existing guidance already covers all AC requirements.

### Group B: Fitness Significant Entry Detector

- [x] Task 7: Create FitnessSignificantEntryDetector class (AC: #7)
  - [x] 7.1: Create `packages/swealog/swealog/observer/__init__.py` with module docstring
  - [x] 7.2: Create `packages/swealog/swealog/observer/fitness_detector.py`
  - [x] 7.3: Import: `from quilto.state import SignificantEntryDetector, DefaultSignificantEntryDetector`, `from quilto.storage import Entry`
  - [x] 7.4: Implement `FitnessSignificantEntryDetector` class:
    - Extend DefaultSignificantEntryDetector with fitness-specific checks
    - Check for PR indicators: "new pr", "beat pr", "personal record", "pb", "personal best"
    - Check for weight milestones: "hit 200", "reached 300", "broke 100kg"
    - Check for distance milestones: "first 5k", "first marathon", "100 mile week"
    - Check for injury mentions: "injury", "pain", "hurt", "pulled", "strained"
  - [x] 7.5: Add comprehensive docstrings with Google style
  - [x] 7.6: Export in `__init__.py`

- [x] Task 8: Update swealog package exports
  - [x] 8.1: Edit `packages/swealog/swealog/__init__.py`
  - [x] 8.2: Import and export `FitnessSignificantEntryDetector`
  - [x] 8.3: Add to `__all__` list

### Group C: Unit Tests

- [x] Task 9: Create unit tests for FitnessSignificantEntryDetector (AC: #7)
  - [x] 9.1: Create `packages/swealog/tests/test_fitness_detector.py`
  - [x] 9.2: Test PR detection: "new PR on bench", "personal record deadlift", "pb 5k"
  - [x] 9.3: Test milestone detection: "first 5k", "100th workout", "marathon debut"
  - [x] 9.4: Test weight milestone: "hit 200lbs on squat", "broke 100kg deadlift"
  - [x] 9.5: Test injury detection: "slight pain in shoulder", "felt a pull in my hamstring"
  - [x] 9.6: Test negative cases: "bench press 185x5" (no PR mention), normal workout entries

### Group D: Integration Tests

- [x] Task 10: Create Observer integration tests with fitness domains (AC: #8)
  - [x] 10.1: Create `packages/swealog/tests/test_observer_fitness_integration.py`
  - [x] 10.2: Use fixtures: `use_real_ollama`, `llm_config_path` (from tests/conftest.py)
  - [x] 10.3: Skip if `--use-real-ollama` not provided (use `@pytest.mark.skipif` with `use_real_ollama` fixture)
  - [x] 10.4: Test Observer with Strength domain:
    - Provide bench press PR log entry
    - Verify Observer generates update with category="fact", key like "bench_press_pr"
    - Verify confidence is appropriate (certain for explicit PR mention)
  - [x] 10.5: Test Observer with combined fitness guidance:
    - Use trigger_post_query with GeneralFitness + Strength domains active
    - Verify combined guidance includes both domains' patterns
    - Verify Observer tracks patterns from both domains
  - [x] 10.6: Test Observer with Running domain:
    - Provide marathon completion entry
    - Verify Observer captures milestone

### Group E: Validation

- [x] Task 11: Run validation
  - [x] 11.1: Run `make check` (lint + typecheck) - PASSED (for swealog package)
  - [x] 11.2: Run `make test` (unit tests) - 386 tests passed
  - [x] 11.3: Run `make test-ollama` (integration tests with real Ollama) - 5 swealog tests passed

## Dev Notes

### Current context_management_guidance Review

All 5 fitness domain modules already have `context_management_guidance` defined:

**GeneralFitness:** (general_fitness.py:122-127)
```python
context_management_guidance=(
    "Track: workout frequency (days per week), activity type distribution "
    "(strength vs cardio ratio), effort level trends (average RPE over time), "
    "general engagement patterns (consistency, gaps). Flag: sudden intensity "
    "spikes, extended rest periods, dramatic volume changes."
),
```

**Strength:** (strength.py:224-231)
```python
context_management_guidance=(
    "Track: exercise PRs (weight × reps for major lifts), training frequency per "
    "muscle group, volume progression (weekly tonnage trends), intensity patterns "
    "(average RPE trends), exercise selection changes. "
    "Flag: sudden strength drops (>10% on major lifts), training gaps >7 days, "
    "persistent high RPE (>9 average over 2+ weeks), dramatic volume spikes. "
    "Correlate: performance vs sleep notes, strength trends vs bodyweight changes."
),
```

**Running:** (running.py:259-266)
```python
context_management_guidance=(
    "Track: weekly mileage totals and trends, average pace progression by workout type, "
    "long run distance progression, interval/tempo session frequency, rest day patterns. "
    "Flag: weekly mileage spikes (>10% increase), consecutive hard workout days, "
    "sudden pace declines (>10% slower), training gaps >7 days, workout type imbalance "
    "(too much intensity, not enough easy running). "
    "Correlate: pace vs heart rate (cardiac drift), performance vs sleep/recovery notes, "
    "injury mentions vs training load, race performance vs training volume."
),
```

**Nutrition:** (nutrition.py:197-203)
```python
context_management_guidance=(
    "Track: average daily calories (7-day rolling), macro distribution patterns, "
    "meal timing consistency, protein intake relative to goals, hydration frequency. "
    "Flag: significant calorie variance (>500 from average), extended fasting periods, "
    "protein consistently under target, irregular meal patterns. "
    "Correlate: nutrition vs workout performance, meal timing vs energy levels, "
    "weekend vs weekday eating patterns, travel/social impact on nutrition."
),
```

**Swimming:** (swimming.py:259-267)
```python
context_management_guidance=(
    "Track: weekly distance totals and trends, stroke distribution (% freestyle "
    "vs other strokes), equipment usage frequency, pace progression per 100m. "
    "Flag: weekly volume spikes (>10% increase), consecutive hard sessions, "
    "sudden pace declines (>5% slower per 100m), training gaps >7 days, "
    "excessive paddle usage (shoulder risk), imbalanced stroke training. "
    "Correlate: pace vs equipment (faster with fins, slower with paddles), "
    "performance vs rest days, technique notes vs pace improvement, "
    "open water performance vs pool times."
),
```

### Assessment

**Verification Required:** Review existing guidance against AC #2-6 requirements:

| Domain | Current Guidance Coverage | AC Requirements Gap? |
|--------|---------------------------|---------------------|
| GeneralFitness | workout frequency, activity distribution, effort trends, engagement, flags | ✓ Appears complete |
| Strength | PRs, frequency, volume, intensity, flags, correlations | ✓ Appears complete |
| Running | mileage, pace, long run, frequency, flags, correlations | ✓ Appears complete |
| Nutrition | calories, macros, timing, protein, flags, correlations | ✓ Appears complete |
| Swimming | distance, strokes, equipment, pace, flags, correlations | ✓ Appears complete |

**Recommendation:** Task Group A should VERIFY guidance covers AC requirements. If current guidance already satisfies requirements, mark tasks as complete with "verified existing guidance meets requirements" note rather than modifying working code.

### FitnessSignificantEntryDetector Design

Extends Quilto's DefaultSignificantEntryDetector with fitness-specific checks:

```python
import re
from typing import Any

from quilto.state import DefaultSignificantEntryDetector
from quilto.storage import Entry


class FitnessSignificantEntryDetector(DefaultSignificantEntryDetector):
    """Fitness-specific significant entry detector.

    Extends default detection with fitness-specific patterns:
    - Weight milestones (hit 200, broke 100kg)
    - Distance milestones (first 5k, first marathon)
    - Injury/pain mentions (for cautionary tracking)

    Note: DefaultSignificantEntryDetector already handles:
    - PR indicators (personal record, pb, pr)
    - Generic milestones (first, 100th, 1000th)
    - Events (competition, race, meet, tournament)
    """

    def is_significant(self, entry: Entry, parsed_data: dict[str, Any]) -> bool:
        """Check for fitness-specific significant patterns.

        Args:
            entry: The log entry to evaluate.
            parsed_data: Parsed domain data from the entry.

        Returns:
            True if the entry is significant, False otherwise.
        """
        # First check base implementation (PRs, milestones, events)
        if super().is_significant(entry, parsed_data):
            return True

        content_lower = entry.raw_content.lower()

        # Weight milestones (strength training)
        weight_patterns = [
            r"\bhit \d+",      # hit 200, hit 300
            r"\bbroke \d+",   # broke 100kg
            r"\breached \d+", # reached 200lbs
        ]
        if any(re.search(pat, content_lower) for pat in weight_patterns):
            return True

        # Distance milestones (running/swimming) - beyond what DefaultDetector handles
        distance_keywords = [
            "first 5k", "first 10k", "first marathon", "first half",
            "100 mile", "1000km", "marathon debut"
        ]
        if any(kw in content_lower for kw in distance_keywords):
            return True

        # Injury mentions (cautionary tracking)
        injury_keywords = ["injury", "injured", "pain", "hurt", "pulled", "strained"]
        if any(kw in content_lower for kw in injury_keywords):
            return True

        return False
```

### File Structure

```
packages/swealog/swealog/
├── __init__.py                    # Add FitnessSignificantEntryDetector export
├── domains/                        # EXISTING - Review/enhance guidance
│   ├── __init__.py
│   ├── general_fitness.py         # Review context_management_guidance
│   ├── strength.py                # Review context_management_guidance
│   ├── running.py                 # Review context_management_guidance
│   ├── nutrition.py               # Review context_management_guidance
│   └── swimming.py                # Review context_management_guidance
└── observer/                       # NEW
    ├── __init__.py                # Export FitnessSignificantEntryDetector
    └── fitness_detector.py        # FitnessSignificantEntryDetector class

packages/swealog/tests/
├── test_domains.py                # EXISTING
├── test_fitness_detector.py       # NEW - Unit tests for detector
└── test_observer_fitness_integration.py  # NEW - Integration tests
```

### Dependencies on Existing Code

| Component | Location | Usage |
|-----------|----------|-------|
| SignificantEntryDetector | `quilto.state` | Protocol to implement |
| DefaultSignificantEntryDetector | `quilto.state` | Base class to extend |
| Entry | `quilto.storage` | Entry model for detection |
| ObserverAgent | `quilto.agents` | For integration tests |
| trigger_post_query | `quilto.state` | For integration tests |
| trigger_significant_log | `quilto.state` | For integration tests with significant entries |
| GlobalContextManager | `quilto.storage` | For integration tests |
| ObserverTriggerConfig | `quilto.state` | For integration tests |
| ActiveDomainContext | `quilto.agents.models` | For integration tests |
| get_combined_context_guidance | `quilto.state` | To build combined guidance from domains |

### Common Mistakes to Avoid

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Modifying Quilto code for fitness-specific features | Keep fitness-specific code in Swealog | project-context.md |
| Using substring matching without word boundaries | Use regex `\b` for abbreviations like "pr" | Story 7.3 |
| Not exporting new classes in `__init__.py` | Always update `__all__` | project-context.md |
| Missing `py.typed` marker | Add if creating new typed package | project-context.md |
| Not checking for existing guidance before rewriting | Review existing, enhance if needed | This story |
| Creating test helpers that duplicate Quilto | Import from Quilto, don't duplicate | Architecture |
| Swealog `__init__.py` only exports GeneralFitness | Add FitnessSignificantEntryDetector to exports | Task 8 |
| Not using `use_real_ollama` fixture correctly | Check `tests/conftest.py` for fixture pattern | Story 7.1-7.3 |

### References

- [Source: packages/swealog/swealog/domains/general_fitness.py:122-127] Current GeneralFitness guidance
- [Source: packages/swealog/swealog/domains/strength.py:224-230] Current Strength guidance
- [Source: packages/swealog/swealog/domains/running.py:259-266] Current Running guidance
- [Source: packages/swealog/swealog/domains/nutrition.py:197-203] Current Nutrition guidance
- [Source: packages/swealog/swealog/domains/swimming.py:259-267] Current Swimming guidance
- [Source: packages/quilto/quilto/state/observer_triggers.py:132-170] DefaultSignificantEntryDetector
- [Source: packages/quilto/quilto/agents/observer.py:125-198] Observer prompt with context_management_guidance
- [Source: _bmad-output/planning-artifacts/epics.md:1054-1067] Story 7.4 acceptance criteria
- [Source: _bmad-output/planning-artifacts/epics.md:38-67] FR-A10: Context management guidance

### Story Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| 7-1 (done) | Upstream | ObserverAgent uses context_management_guidance |
| 7-2 (done) | Upstream | GlobalContextManager stores Observer updates |
| 7-3 (done) | Upstream | SignificantEntryDetector protocol defined |
| 1-4 (done) | Upstream | GeneralFitness domain module |
| 2-4 (done) | Upstream | Strength domain module |
| 2-5 (done) | Upstream | Nutrition domain module |
| 3-4 (done) | Upstream | Running domain module |
| 6-4 (done) | Upstream | Swimming domain module |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

1. **Tasks 1-6 (AC #2-6):** Reviewed all 5 fitness domain modules' `context_management_guidance`. All existing guidance already satisfies AC requirements with comprehensive coverage of:
   - Pattern tracking (frequency, PRs, volume, trends)
   - Flags for anomalies (spikes, drops, gaps)
   - Correlations (performance vs recovery, etc.)
   No modifications were needed.

2. **Task 7:** Created `FitnessSignificantEntryDetector` class extending `DefaultSignificantEntryDetector` with fitness-specific patterns:
   - Weight milestones: `hit \d+`, `broke \d+`, `reached \d+`
   - Distance milestones: `first 5k`, `first marathon`, `100 mile`, `marathon debut`
   - Injury tracking: `injury`, `injured`, `pain`, `hurt`, `pulled`, `strained`

3. **Task 8:** Exported `FitnessSignificantEntryDetector` from `swealog/__init__.py`

4. **Task 9:** Created 30 unit tests for FitnessSignificantEntryDetector covering all detection patterns and negative cases. All tests pass.

5. **Task 10:** Created 5 integration tests for Observer with fitness domains:
   - `test_observer_with_strength_pr` - PRs recorded as facts with certain confidence
   - `test_observer_with_combined_fitness_guidance` - multi-domain guidance merging
   - `test_observer_with_running_marathon` - milestone detection
   - `test_trigger_significant_log_with_fitness_detector` - injury detection triggers Observer
   - `test_trigger_post_query_with_fitness_domains` - full integration with context updates

6. All tests pass: 386 unit tests + 5 integration tests with Ollama

### File List

**Created:**
- `packages/swealog/swealog/observer/__init__.py` - Module export for observer subpackage
- `packages/swealog/swealog/observer/fitness_detector.py` - FitnessSignificantEntryDetector class
- `packages/swealog/tests/test_fitness_detector.py` - 30 unit tests
- `packages/swealog/tests/test_observer_fitness_integration.py` - 5 integration tests

**Modified:**
- `packages/swealog/swealog/__init__.py` - Added FitnessSignificantEntryDetector export

## Senior Developer Review (AI)

**Review Date:** 2026-01-16
**Reviewer:** Amelia (Dev Agent)
**Outcome:** APPROVED

### Findings Summary

| Severity | Count | Fixed |
|----------|-------|-------|
| HIGH | 0 | N/A |
| MEDIUM | 3 | 3 |
| LOW | 1 | 0 |

### Issues Fixed

1. **[M1] Lint failures (D301)**: Added `r"""` prefix to docstrings with backslashes in:
   - `packages/quilto/quilto/agents/models.py:938`
   - `packages/quilto/quilto/agents/observer.py:15`
   - `scripts/convert_obsidian.py:2`

2. **[M2] Lint failures (F401, E501)**: Fixed in `scripts/convert_obsidian.py`:
   - Removed unused imports (`shutil`, `datetime`)
   - Fixed line length in examples

3. **[M3] Missing `py.typed` marker**: Added `packages/swealog/swealog/observer/py.typed`

### Verification

- `make check`: PASSED (lint + typecheck)
- Unit tests: 30 passed
- Integration tests: 5 exist (skipped without Ollama flag)
- All 8 Acceptance Criteria verified against implementation
