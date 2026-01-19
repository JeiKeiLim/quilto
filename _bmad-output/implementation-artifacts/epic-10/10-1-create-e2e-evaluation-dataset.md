# Story 10.1: Create E2E Evaluation Dataset

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Quilto developer**,
I want **an E2E evaluation dataset extending existing query test cases**,
So that **pairwise evaluation can compare Quilto responses to Claude baseline**.

## Background

Epic 10 introduces Agent Quality Evaluation Infrastructure using LLM-as-judge methodology to benchmark Quilto against Claude responses. This story creates the foundation: a versioned golden dataset with rubric criteria.

**Research Source:** `_bmad-output/planning-artifacts/research/technical-llm-agent-quality-evaluation-research-2026-01-19.md`

**Key Design Decisions (from research):**
- Pairwise comparison is more reliable than absolute scoring
- Position swap mandatory to mitigate ~40% inconsistency
- Versioned datasets treated as release artifacts
- Multi-criteria rubric: accuracy, completeness, conciseness, domain expertise

## Acceptance Criteria

1. **AC1: Directory Structure Created**
   - Given the tests directory
   - When the evaluation dataset is initialized
   - Then `tests/eval/` directory structure exists:
     ```
     tests/eval/
     ├── golden/
     │   └── v2026-01-XX.yaml         # Versioned test cases
     ├── rubric.yaml                   # Evaluation criteria
     └── README.md                     # Dataset documentation
     ```

2. **AC2: Existing Query Cases Extended**
   - Given the 10 existing query test cases in `tests/corpus/fitness/expected/query/`
   - When they are extended for E2E evaluation
   - Then each existing case is represented in the golden dataset
   - And each case includes: query, context_entries, rubric_criteria
   - And source reference points to original corpus file
   - And category is preserved (simple/complex/insufficient)

3. **AC3: 40 New Test Cases Added**
   - Given the evaluation requirements
   - When new test cases are created
   - Then 40 additional test cases exist covering:
     - **Retrieval strategy tests** (10 cases): date-range, keyword, pattern matching
     - **Multi-step reasoning tests** (10 cases): dependent queries, complex analysis
     - **Edge cases** (10 cases): ambiguous input, sparse data, out-of-domain hints
     - **Domain expertise tests** (10 cases): fitness terminology, exercise knowledge
   - And each case has human-validated expected behavior (not expected text)

4. **AC4: Rubric Criteria Defined**
   - Given the rubric.yaml file
   - When evaluation criteria are defined
   - Then these criteria exist:
     - `accuracy`: Factual correctness based on retrieved data
     - `completeness`: All aspects of query addressed
     - `conciseness`: No unnecessary verbosity
     - `domain_expertise`: Appropriate fitness terminology and knowledge
   - And each criterion has scoring guidance (what constitutes good/medium/poor)

5. **AC5: Dataset Version Tagged**
   - Given the golden dataset
   - When it is finalized
   - Then filename includes version date (e.g., `v2026-01-XX.yaml`)
   - And YAML frontmatter includes version, domain, case_count metadata
   - And README.md documents versioning strategy

6. **AC6: Test Case Format Supports Pairwise Evaluation**
   - Given each test case in the golden dataset
   - When it is structured for evaluation
   - Then format includes fields needed for pairwise LLM-as-judge:
     - `id`: Unique identifier
     - `category`: simple/complex/insufficient/retrieval/reasoning/edge/domain
     - `query`: The user query text
     - `context_entries`: List of entry dates to use as context
     - `rubric_criteria`: Which criteria apply to this case
     - `evaluation_hints`: What a good response should/shouldn't do
   - And format is YAML for readability and maintainability

## Tasks / Subtasks

- [x] Task 1: Create Directory Structure (AC: 1)
  - [x] Create `tests/eval/` directory
  - [x] Create `tests/eval/golden/` subdirectory
  - [x] Create `tests/eval/README.md` with dataset documentation

- [x] Task 2: Define Rubric Criteria (AC: 4)
  - [x] Create `tests/eval/rubric.yaml`
  - [x] Define `accuracy` criterion with scoring guidance
  - [x] Define `completeness` criterion with scoring guidance
  - [x] Define `conciseness` criterion with scoring guidance
  - [x] Define `domain_expertise` criterion with scoring guidance

- [x] Task 3: Extend Existing Query Cases (AC: 2, 6)
  - [x] Parse 10 existing JSON files from `tests/corpus/fitness/expected/query/`
  - [x] Convert each to golden dataset YAML format
  - [x] Add rubric_criteria mapping based on category
  - [x] Add evaluation_hints based on expected_analysis_points/expected_response_elements
  - [x] Add source reference to original file

- [x] Task 4: Create Retrieval Strategy Test Cases (AC: 3, 6)
  - [x] Create 10 test cases focusing on retrieval strategy:
    - 3x date-range queries (temporal context)
    - 3x keyword queries (exercise/activity specific)
    - 2x pattern matching queries (trends, patterns)
    - 2x mixed strategy queries

- [x] Task 5: Create Multi-Step Reasoning Test Cases (AC: 3, 6)
  - [x] Create 10 test cases requiring complex reasoning:
    - 3x queries with dependent sub-questions
    - 3x queries requiring analysis across multiple dates
    - 2x queries with implicit comparison requirements
    - 2x queries requiring correlation identification

- [x] Task 6: Create Edge Case Test Cases (AC: 3, 6)
  - [x] Create 10 edge case test cases:
    - 3x ambiguous input (could be interpreted multiple ways)
    - 3x sparse data scenarios (limited entries for analysis)
    - 2x out-of-domain hints (non-fitness elements mixed in)
    - 2x boundary cases (exact dates, edge of time ranges)

- [x] Task 7: Create Domain Expertise Test Cases (AC: 3, 6)
  - [x] Create 10 domain expertise test cases:
    - 3x fitness terminology (progressive overload, RPE, 1RM)
    - 3x exercise knowledge (muscle groups, movement patterns)
    - 2x training principles (recovery, periodization)
    - 2x nutrition-related if applicable

- [x] Task 8: Compile Golden Dataset (AC: 5)
  - [x] Combine all test cases into single YAML file
  - [x] Add YAML frontmatter with metadata
  - [x] Version with current date
  - [x] Validate total is 50 cases (10 extended + 40 new)

- [x] Task 9: Documentation and Validation
  - [x] Update README.md with complete documentation
  - [x] Document versioning strategy for future updates
  - [x] Validate YAML syntax
  - [x] Run `make check` to ensure no linting issues

## Dev Notes

### Project Identity

This story creates test infrastructure in `tests/eval/`. This is **test code**, not application code.

**Test rule:** Evaluation dataset is domain-agnostic infrastructure, but test cases are fitness-specific (Swealog domain).

### Directory Structure

```
tests/
├── corpus/                           # Existing test corpus
│   └── fitness/expected/query/       # 10 existing query cases (JSON)
└── eval/                             # NEW: E2E evaluation infrastructure
    ├── golden/
    │   └── v2026-01-XX.yaml          # 50 versioned test cases
    ├── rubric.yaml                   # Evaluation criteria definitions
    └── README.md                     # Dataset documentation
```

### Golden Dataset YAML Format

```yaml
# tests/eval/golden/v2026-01-XX.yaml
---
version: "2026-01-XX"
domain: "fitness"
case_count: 50
created_by: "Story 10.1"
---

test_cases:
  # Extended from existing corpus
  - id: "simple-bench-progression"
    category: "simple"
    source: "tests/corpus/fitness/expected/query/simple-bench-progression.json"
    query: "How has my bench press progressed?"
    context_entries: ["2019-01-29", "2019-02-01", "2019-03-12"]
    rubric_criteria: ["accuracy", "completeness", "domain_expertise"]
    evaluation_hints:
      should_mention: ["weight progression", "time span"]
      should_not: ["make up data", "guess weights"]

  # New retrieval strategy case
  - id: "retrieval-date-range-last-week"
    category: "retrieval"
    query: "What did I do last week?"
    context_entries: ["2019-03-04", "2019-03-06", "2019-03-08"]
    rubric_criteria: ["accuracy", "completeness"]
    evaluation_hints:
      should_mention: ["specific exercises from each day"]
      should_not: ["include entries outside date range"]
```

### Rubric Format

```yaml
# tests/eval/rubric.yaml
criteria:
  accuracy:
    description: "Factual correctness based on retrieved data"
    scoring:
      good: "All facts match logged data, no fabrication"
      medium: "Minor inaccuracies but core facts correct"
      poor: "Significant errors or hallucinated data"

  completeness:
    description: "All aspects of query addressed"
    scoring:
      good: "Answers all explicit and implicit questions"
      medium: "Addresses main question, misses nuances"
      poor: "Fails to answer core question"

  conciseness:
    description: "No unnecessary verbosity"
    scoring:
      good: "Direct, relevant response without padding"
      medium: "Some unnecessary elaboration"
      poor: "Excessive verbose or off-topic content"

  domain_expertise:
    description: "Appropriate fitness terminology and knowledge"
    scoring:
      good: "Uses correct terms, shows fitness understanding"
      medium: "Basic terminology, misses deeper insights"
      poor: "Incorrect terminology or fitness misconceptions"
```

### Test Case Categories Breakdown

| Category | Source | Count | Focus |
|----------|--------|-------|-------|
| simple | Extended from corpus | 3 | Basic single-question queries |
| complex | Extended from corpus | 4 | Multi-step or comparison queries |
| insufficient | Extended from corpus | 3 | Queries with data gaps |
| retrieval | NEW | 10 | Retrieval strategy effectiveness |
| reasoning | NEW | 10 | Multi-step reasoning quality |
| edge | NEW | 10 | Boundary and ambiguous cases |
| domain | NEW | 10 | Domain expertise demonstration |
| **Total** | | **50** | |

### Existing Query Test Case Mapping

| Existing File | Category | ID in Golden |
|--------------|----------|--------------|
| simple-bench-progression.json | simple | simple-bench-progression |
| simple-heaviest-deadlift.json | simple | simple-heaviest-deadlift |
| simple-september-frequency.json | simple | simple-september-frequency |
| complex-deadlift-squat-compare.json | complex | complex-deadlift-squat-compare |
| complex-push-vs-pull.json | complex | complex-push-vs-pull |
| complex-strongest-lift.json | complex | complex-strongest-lift |
| complex-q1-volume-trends.json | complex | complex-q1-volume-trends |
| insufficient-cardio-progress.json | insufficient | insufficient-cardio-progress |
| insufficient-year-comparison.json | insufficient | insufficient-year-comparison |
| insufficient-recovery-pattern.json | insufficient | insufficient-recovery-pattern |

### Context Entries Source

Context entries reference dates from the existing test corpus in `tests/corpus/fitness/entries/from_csv/`. These are real workout logs derived from Strong CSV data.

### Validation Commands

```bash
# During development
make check        # lint + typecheck

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('tests/eval/golden/v2026-01-XX.yaml'))"

# Before completion
make validate     # lint + format + typecheck + test
```

### References

- [Source: _bmad-output/planning-artifacts/research/technical-llm-agent-quality-evaluation-research-2026-01-19.md#Dataset-Creation-Workflow]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-10.1]
- [Source: tests/corpus/fitness/expected/query/] - 10 existing query test cases

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created `tests/eval/` directory structure with `golden/` subdirectory
- Created comprehensive `rubric.yaml` with 4 evaluation criteria (accuracy, completeness, conciseness, domain_expertise), each with scoring guidance and weights
- Extended 10 existing query test cases to golden format with rubric_criteria and evaluation_hints
- Created 10 retrieval strategy test cases covering date-range, keyword, pattern matching, and mixed strategies
- Created 10 multi-step reasoning test cases covering dependent queries, cross-date analysis, implicit comparisons, and correlations
- Created 10 edge case test cases covering ambiguous input, sparse data, out-of-domain hints, and boundary cases
- Created 10 domain expertise test cases covering fitness terminology (progressive overload, RPE, 1RM), exercise knowledge, training principles, and nutrition
- Compiled all 50 test cases into versioned golden dataset `v2026-01-19.yaml` with metadata
- Created README.md documenting dataset usage, versioning strategy, and test case format
- Validated YAML syntax and ran `make validate` (1741 tests passed)

### File List

- tests/eval/README.md (NEW)
- tests/eval/rubric.yaml (NEW)
- tests/eval/golden/v2026-01-19.yaml (NEW, MODIFIED during review)
- tests/eval/__init__.py (NEW - added during review)
- tests/eval/schema.py (NEW - added during review)
- tests/eval/test_eval_dataset.py (NEW - added during review)

### Change Log

- 2026-01-19: Created E2E evaluation dataset with 50 test cases for pairwise LLM-as-judge evaluation
- 2026-01-20: Code review fixes (see Senior Developer Review below)

## Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5
**Date:** 2026-01-20
**Outcome:** Approved with fixes applied

### Issues Found and Fixed

| Severity | Issue | Resolution |
|----------|-------|------------|
| HIGH | Inaccurate weights in `simple-bench-progression` evaluation hints (claimed 80/70/55kg, actual range 55-85kg) | Updated hints to accurately reflect corpus data |
| MEDIUM | `complex-push-vs-pull` context_entries not sorted chronologically | Sorted entries to `["2019-01-28", "2019-01-29", ...]` |
| MEDIUM | Missing validation schema for golden dataset | Added `tests/eval/schema.py` with Pydantic models |
| MEDIUM | No test coverage for dataset files | Added `tests/eval/test_eval_dataset.py` with 10 validation tests |

### Verification

- All 1751 tests pass (including 10 new evaluation dataset tests)
- `make check` passes (lint + typecheck)
- `make validate` passes (full validation)

