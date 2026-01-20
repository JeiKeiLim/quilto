# Story 10.3: Implement Pairwise LLM-as-Judge

Status: done

## Story

As a **Quilto developer**,
I want **a pairwise LLM-as-judge evaluation with position swap**,
So that **Quilto vs Claude comparison is unbiased and reliable**.

## Background

Stories 10.1 and 10.2 established the evaluation infrastructure:
- 50 E2E test cases in `tests/eval/golden/v2026-01-19.yaml`
- Claude baseline responses in `tests/eval/golden/baseline_responses/v2026-01-19/`
- Rubric with 4 criteria: accuracy, completeness, conciseness, domain_expertise
- Existing schemas: `GoldenDataset`, `TestCase`, `BaselineResponse`, `Rubric` in `tests/eval/schema.py`

**Research Source:** `_bmad-output/planning-artifacts/research/technical-llm-agent-quality-evaluation-research-2026-01-19.md`

**Key Design Decisions (from research):**
- Pairwise comparison is more reliable than absolute scoring
- Position swap mandatory: evaluate both (Quilto, Claude) and (Claude, Quilto) orderings
- Only count **consistent wins** where both orderings agree
- Anonymized responses (Response A / Response B) to reduce bias
- Multi-criteria rubric scoring with weighted aggregation

## Acceptance Criteria

1. **AC1: Pairwise Evaluation Module Created**
   - Given the `tests/eval/` directory
   - When the pairwise evaluator is implemented
   - Then `tests/eval/pairwise_judge.py` exists with:
     - `PairwiseEvaluator` class for orchestrating evaluations
     - `JudgeResult` Pydantic schema for individual judgment
     - `PairwiseResult` Pydantic schema for combined position-swapped result
   - And evaluation uses LiteLLM for judge LLM calls

2. **AC2: Position Swap Implemented**
   - Given a test case with Quilto and Claude responses
   - When evaluation runs
   - Then judge is called twice: (Quilto=A, Claude=B) and (Claude=A, Quilto=B)
   - And responses are anonymized as "Response A" and "Response B"
   - And order is randomized for first call (to avoid systematic bias)
   - And both orderings are logged with full reasoning

3. **AC3: Consistent Win Counting**
   - Given two judgments from position-swapped evaluations
   - When determining the winner
   - Then only **consistent wins** are counted:
     - Quilto wins if both orderings say Quilto is better
     - Claude wins if both orderings say Claude is better
     - **Tie** if orderings disagree (inconsistent)
   - And inconsistency rate is tracked as a metric

4. **AC4: Multi-Criteria Rubric Scoring**
   - Given the rubric from `tests/eval/rubric.yaml`
   - When judge evaluates responses
   - Then each criterion receives a score (1-5) based on rubric guidance
   - And final score uses weighted aggregation per rubric weights
   - And judge provides reasoning for each criterion score
   - And criterion profiles from rubric.yaml are respected per category

5. **AC5: Judge Prompt Engineering**
   - Given the evaluation prompt template
   - When judge LLM is called
   - Then system prompt explains the evaluation task clearly
   - And rubric criteria are included with scoring guidance
   - And evaluation_hints from test case inform judgment
   - And structured output (JSON) is enforced
   - And judge uses chain-of-thought before scoring

6. **AC6: Quilto Response Generation**
   - Given a test case with context_entries
   - When generating Quilto response for comparison
   - Then actual Quilto agent pipeline is invoked via `execute_query_pipeline()`
   - And same context entries are provided as in baseline generation
   - And response is captured for pairwise comparison
   - And generation errors are handled gracefully (mark as failed, don't crash)

7. **AC7: Evaluation Runner CLI**
   - Given `tests/eval/run_evaluation.py`
   - When CLI is executed
   - Then it supports: `--dataset-version`, `--cases`, `--judge-model`, `--dry-run`, `--verbose`, `--output-dir`
   - And progress is shown via rich progress bar
   - And results are saved to `tests/eval/results/{version}/{timestamp}.json`
   - And summary statistics are printed (win rate, tie rate, inconsistency rate)

8. **AC8: DeepEval Custom Metric Integration**
   - Given the pairwise evaluation logic
   - When wrapped as DeepEval custom metric
   - Then `PairwiseComparisonMetric` class extends `BaseMetric`
   - And can be used in pytest with `evaluate()` function
   - And threshold can be set for pass/fail (e.g., win_rate >= 0.4)

## Tasks / Subtasks

- [x] Task 1: Create Pydantic Schemas (AC: 1)
  - [x] Add `CriterionScore` schema to `tests/eval/schema.py`
  - [x] Add `JudgeResult` schema (winner, criterion_scores, reasoning, raw_output)
  - [x] Add `PairwiseResult` schema (test_case_id, responses, judgments, final_winner, is_consistent)
  - [x] Add `EvaluationMetrics` schema (totals, win/tie/inconsistency rates, per_category)
  - [x] Add `EvaluationRun` schema (version, timestamp, judge_model, results, metrics)
  - [x] Update `tests/eval/__init__.py` exports

- [x] Task 2: Implement Judge Prompt Engineering (AC: 5)
  - [x] Create `_build_judge_system_prompt()` that loads rubric.yaml criteria
  - [x] Create `_build_judge_user_prompt()` with anonymized responses
  - [x] Include evaluation_hints from test case
  - [x] Require chain-of-thought reasoning before scores
  - [x] Enforce JSON structured output format

- [x] Task 3: Implement PairwiseEvaluator Class (AC: 1, 2, 3)
  - [x] Create `tests/eval/pairwise_judge.py`
  - [x] Implement `__init__(judge_model, max_concurrent=2)` with semaphore
  - [x] Implement `evaluate_pair()` method for single (A, B) judgment
  - [x] Implement `evaluate_with_swap()` with random first position
  - [x] Implement `determine_winner()` with consistent win logic
  - [x] Parse JSON response from judge, retry on malformed response (max 2 retries)

- [x] Task 4: Implement Quilto Response Generation (AC: 6)
  - [x] Create `generate_quilto_response()` helper in pairwise_judge.py
  - [x] Use `execute_query_pipeline()` from `swealog.api.routes.query`
  - [x] Create test StorageRepository pointing to corpus directory
  - [x] Load domains from `swealog.api.dependencies.get_domains()`
  - [x] Reuse `load_context_entries()` from `generate_baseline.py`
  - [x] Handle generation errors gracefully (return None, log error)
  - [x] Add optional caching with `--cache-quilto-responses` flag

- [x] Task 5: Implement Multi-Criteria Scoring (AC: 4)
  - [x] Load rubric.yaml using existing `Rubric` schema
  - [x] Apply criterion_profiles based on test case category
  - [x] Calculate weighted aggregate score per response
  - [x] Include per-criterion breakdown in JudgeResult

- [x] Task 6: Implement Evaluation Runner CLI (AC: 7)
  - [x] Create `tests/eval/run_evaluation.py`
  - [x] Parse CLI args: --dataset-version, --cases, --judge-model, --dry-run, --verbose, --output-dir
  - [x] Load golden dataset and baseline responses (reuse generate_baseline.py patterns)
  - [x] Generate Quilto responses for each case
  - [x] Run pairwise evaluation with position swap
  - [x] Save results to `tests/eval/results/{version}/{timestamp}.json`
  - [x] Print summary: win rate, tie rate, inconsistency rate, per-category breakdown

- [x] Task 7: Implement DeepEval Custom Metric (AC: 8)
  - [x] Create `tests/eval/metrics.py`
  - [x] Implement `PairwiseComparisonMetric(BaseMetric)`
  - [x] Override `measure()` method (sync wrapper for async)
  - [x] Support threshold parameter for pass/fail
  - [x] Add pytest test using the metric

- [x] Task 8: Add Tests and Validation
  - [x] Add unit tests for `PairwiseEvaluator` class with mock judge
  - [x] Add test for consistent win logic
  - [x] Add test for position swap correctness
  - [x] Add integration test with mock LLM responses
  - [x] Run `make validate` to ensure all tests pass

- [x] Task 9: Documentation and Module Exports
  - [x] Update `tests/eval/__init__.py` with new exports
  - [x] Update `tests/eval/README.md` with evaluation usage instructions
  - [x] Document judge model recommendations (cost vs quality)

## Dev Notes

### Project Identity

This story creates test infrastructure in `tests/eval/`. This is **test code**, not framework code.

### Directory Structure After Implementation

```
tests/eval/
├── __init__.py                             # Export new schemas and classes
├── golden/
│   ├── v2026-01-19.yaml                    # 50 test cases (Story 10.1)
│   └── baseline_responses/v2026-01-19/     # Claude responses (Story 10.2)
├── results/                                # NEW: Evaluation results
│   └── v2026-01-19/
│       └── 2026-01-XX_HH-MM-SS.json        # Timestamped results
├── generate_baseline.py                    # Story 10.2 (reuse load_context_entries)
├── pairwise_judge.py                       # NEW: Core evaluation logic
├── run_evaluation.py                       # NEW: CLI runner
├── metrics.py                              # NEW: DeepEval custom metric
├── rubric.yaml                             # Story 10.1
├── schema.py                               # MODIFIED: Add new schemas
└── test_eval_dataset.py                    # MODIFIED: Add evaluation tests
```

### New Pydantic Schemas (Add to schema.py)

```python
from typing import Literal

class CriterionScore(BaseModel):
    """Score for a single rubric criterion."""
    criterion: Literal["accuracy", "completeness", "conciseness", "domain_expertise"]
    score: int = Field(..., ge=1, le=5)
    reasoning: str

class JudgeResult(BaseModel):
    """Result from a single judge evaluation."""
    winner: Literal["A", "B", "Tie"]
    criterion_scores_a: list[CriterionScore]
    criterion_scores_b: list[CriterionScore]
    aggregate_score_a: float
    aggregate_score_b: float
    reasoning: str
    raw_output: str  # Full judge response for debugging

class PairwiseResult(BaseModel):
    """Result from position-swapped pairwise evaluation."""
    test_case_id: str
    quilto_response: str | None  # None if generation failed
    claude_response: str
    judgment_ab: JudgeResult | None  # None if evaluation failed
    judgment_ba: JudgeResult | None
    final_winner: Literal["quilto", "claude", "tie", "error"]
    is_consistent: bool
    quilto_aggregate: float | None
    claude_aggregate: float | None
    error_message: str | None = None

class EvaluationMetrics(BaseModel):
    """Aggregate metrics for an evaluation run."""
    total_cases: int
    quilto_wins: int
    claude_wins: int
    ties: int
    errors: int
    consistent_count: int
    inconsistent_count: int
    win_rate: float  # quilto_wins / (total - errors)
    tie_rate: float
    inconsistency_rate: float
    per_category: dict[str, dict[str, int]]

class EvaluationRun(BaseModel):
    """Complete evaluation run results."""
    version: str
    timestamp: str
    judge_model: str
    judge_params: ModelParams
    results: list[PairwiseResult]
    metrics: EvaluationMetrics
```

### CRITICAL: Quilto Response Generation

**There is NO `Orchestrator` class.** Use the actual API from `swealog.api.routes.query`:

```python
# CORRECT implementation for Quilto response generation
import asyncio
from pathlib import Path
from quilto import LLMClient, StorageRepository, load_llm_config
from swealog.api.routes.query import execute_query_pipeline
from swealog.api.dependencies import get_domains
from tests.eval.generate_baseline import load_context_entries  # REUSE existing

async def generate_quilto_response(
    query: str,
    context_dates: list[str],
) -> str | None:
    """Generate Quilto response using actual agent pipeline.

    Args:
        query: The user query.
        context_dates: List of dates for context (from test case).

    Returns:
        Quilto's synthesized response string, or None on error.
    """
    try:
        # Load LLM config (uses llm-config.yaml from project root)
        config = load_llm_config(Path("llm-config.yaml"))
        llm_client = LLMClient(config)

        # Create storage pointing to test corpus
        # NOTE: StorageRepository expects base_path/logs/raw/ structure
        # Test corpus is at tests/corpus/fitness/entries/from_csv/
        # May need custom adapter - see "Storage Compatibility" section below
        storage = StorageRepository(base_path=Path("tests/corpus/fitness"))

        # Get all fitness domains
        domains = get_domains()

        # Execute full pipeline
        result = await execute_query_pipeline(
            query=query,
            llm_client=llm_client,
            storage=storage,
            domains=domains,
        )

        return result["response"]

    except Exception as e:
        logger.error("Quilto generation failed for query '%s': %s", query[:50], e)
        return None
```

### Storage Compatibility Note

StorageRepository expects `base_path/logs/raw/YYYY/MM/YYYY-MM-DD.md` structure.
Test corpus uses flat `entries/from_csv/YYYY-MM-DD.md`.

**Options:**
1. Create symlink: `tests/corpus/fitness/logs/raw/` -> nested date structure
2. Create custom `EvaluationStorageAdapter` that maps paths
3. Pre-load context using `load_context_entries()` and inject into pipeline

**Recommended:** Investigate during Task 4. May need to mock the Retriever to use pre-loaded context.

### Reuse Existing Code from generate_baseline.py

```python
# REUSE these - do NOT reimplement:
from tests.eval.generate_baseline import (
    load_context_entries,  # Loads corpus markdown files by date
    load_golden_dataset,   # Loads and validates GoldenDataset
    get_response_path,     # Gets path to baseline response JSON
    CORPUS_PATH,           # tests/corpus/fitness/entries/from_csv
    GOLDEN_DIR,            # tests/eval/golden
    BASELINE_DIR,          # tests/eval/golden/baseline_responses
)
```

### Position Swap with Randomization

```python
import random

async def evaluate_with_swap(
    self,
    test_case: TestCase,
    quilto_response: str,
    claude_response: str,
) -> PairwiseResult:
    """Evaluate with both orderings, randomizing first position."""

    # Randomize first evaluation order to avoid systematic bias
    quilto_first = random.choice([True, False])

    if quilto_first:
        judgment_ab = await self.evaluate_pair(test_case, quilto_response, claude_response)
        judgment_ba = await self.evaluate_pair(test_case, claude_response, quilto_response)
    else:
        judgment_ba = await self.evaluate_pair(test_case, claude_response, quilto_response)
        judgment_ab = await self.evaluate_pair(test_case, quilto_response, claude_response)

    # Determine consistent winner
    # judgment_ab: winner="A" means Quilto wins
    # judgment_ba: winner="B" means Quilto wins (positions swapped)
    quilto_wins_ab = judgment_ab.winner == "A"
    quilto_wins_ba = judgment_ba.winner == "B"

    if quilto_wins_ab and quilto_wins_ba:
        final_winner = "quilto"
        is_consistent = True
    elif not quilto_wins_ab and not quilto_wins_ba:
        final_winner = "claude"
        is_consistent = True
    else:
        final_winner = "tie"  # Inconsistent
        is_consistent = False

    return PairwiseResult(
        test_case_id=test_case.id,
        quilto_response=quilto_response,
        claude_response=claude_response,
        judgment_ab=judgment_ab,
        judgment_ba=judgment_ba,
        final_winner=final_winner,
        is_consistent=is_consistent,
        quilto_aggregate=(judgment_ab.aggregate_score_a + judgment_ba.aggregate_score_b) / 2,
        claude_aggregate=(judgment_ab.aggregate_score_b + judgment_ba.aggregate_score_a) / 2,
    )
```

### JSON Parsing with Retry

```python
import json
import re

def parse_judge_response(raw: str) -> dict | None:
    """Parse JSON from judge response, handling common issues."""
    # Try direct JSON parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object in response
    brace_match = re.search(r"\{[\s\S]*\}", raw)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None
```

### CLI Interface

```bash
# Run evaluation on all 50 test cases
python -m tests.eval.run_evaluation --dataset-version v2026-01-19

# Run on specific cases
python -m tests.eval.run_evaluation --dataset-version v2026-01-19 --cases simple-bench-progression,complex-push-vs-pull

# Use different judge model
python -m tests.eval.run_evaluation --dataset-version v2026-01-19 --judge-model gpt-4o-mini

# Custom output directory
python -m tests.eval.run_evaluation --dataset-version v2026-01-19 --output-dir ./my-results

# Dry run
python -m tests.eval.run_evaluation --dataset-version v2026-01-19 --dry-run

# Verbose
python -m tests.eval.run_evaluation --dataset-version v2026-01-19 --verbose
```

### DeepEval Custom Metric (Correct API)

```python
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class PairwiseComparisonMetric(BaseMetric):
    """Custom DeepEval metric for pairwise evaluation against Claude baseline."""

    def __init__(self, threshold: float = 0.4, judge_model: str = "gpt-4o-mini"):
        self.threshold = threshold
        self.judge_model = judge_model
        self._evaluator = PairwiseEvaluator(judge_model=judge_model)
        self.score: float = 0.0
        self.reason: str = ""

    def measure(self, test_case: LLMTestCase) -> float:
        """Synchronous wrapper for async evaluation.

        Returns:
            1.0 if Quilto wins, 0.5 if tie, 0.0 if Claude wins.
        """
        import asyncio
        baseline = test_case.expected_output or ""
        quilto = test_case.actual_output or ""

        async def _run():
            result = await self._evaluator.evaluate_with_swap(
                test_case=self._convert_test_case(test_case),
                quilto_response=quilto,
                claude_response=baseline,
            )
            if result.final_winner == "quilto":
                return 1.0, "Quilto wins consistently"
            elif result.final_winner == "tie":
                return 0.5, "Tie (inconsistent orderings)"
            else:
                return 0.0, "Claude wins consistently"

        self.score, self.reason = asyncio.run(_run())
        return self.score

    def is_successful(self) -> bool:
        return self.score >= self.threshold

    @property
    def __name__(self) -> str:
        return "PairwiseComparisonMetric"
```

### Cost Estimation

Per evaluation run (50 test cases):
- **Quilto generation**: 50 × ~1000 tokens = 50k tokens (Ollama local = free)
- **Judge calls**: 50 × 2 (swap) × ~1500 tokens = 150k tokens
- **gpt-4o-mini**: ~$0.15 per run
- **gpt-4o**: ~$1.50 per run
- **claude-sonnet-4**: ~$0.45 per run

**Recommendation:** `gpt-4o-mini` for routine evaluations, `claude-sonnet-4` for final validation.

### Critical Implementation Notes

1. **Position Swap Mandatory:** Research shows ~40% inconsistency without it.

2. **Consistent Wins Only:** Disagreeing orderings = tie.

3. **Anonymization:** Always "Response A" / "Response B" to judge.

4. **JSON Retry:** Parse with fallback, retry malformed (max 2 attempts).

5. **Quilto Pipeline:** Use `execute_query_pipeline()`, not direct LLM calls.

6. **Error Handling:** Mark failures as error, continue processing.

7. **Reuse Code:** `load_context_entries()`, `load_golden_dataset()` from generate_baseline.py.

### Validation Commands

```bash
make check        # lint + typecheck
make validate     # lint + format + typecheck + test
pytest tests/eval/test_pairwise_judge.py -v
make test-ollama  # Integration tests
```

### References

- [Source: _bmad-output/planning-artifacts/research/technical-llm-agent-quality-evaluation-research-2026-01-19.md#LLM-as-Judge-Implementation-Approaches]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-10.3]
- [Source: tests/eval/golden/v2026-01-19.yaml] - 50 test cases
- [Source: tests/eval/rubric.yaml] - Evaluation criteria
- [Source: tests/eval/generate_baseline.py] - LLM calls and context loading patterns
- [Source: packages/swealog/swealog/api/routes/query.py] - execute_query_pipeline() API
- [Source: packages/swealog/swealog/api/dependencies.py] - get_domains(), get_llm_client()

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Pydantic Schemas (AC1)**: Added 6 new schemas to `tests/eval/schema.py`:
   - `CriterionScore`: Individual rubric criterion score with reasoning
   - `JudgeResult`: Complete judgment from single evaluation with criterion scores
   - `PairwiseResult`: Combined result from position-swapped evaluation
   - `CategoryMetrics`: Per-category breakdown of wins/ties/errors
   - `EvaluationMetrics`: Aggregate metrics including win/tie/inconsistency rates
   - `EvaluationRun`: Complete evaluation run with all results and metadata

2. **Position Swap (AC2)**: Implemented in `PairwiseEvaluator.evaluate_with_swap()`:
   - Randomizes first evaluation order to avoid systematic bias
   - Runs both (Quilto=A, Claude=B) and (Claude=A, Quilto=B) orderings
   - Logs both judgments with full reasoning

3. **Consistent Win Logic (AC3)**: Only counts wins where both orderings agree:
   - Quilto wins only if A wins in AB and B wins in BA
   - Claude wins only if B wins in AB and A wins in BA
   - Tie if orderings disagree (inconsistent) or both say Tie
   - Tracks inconsistency rate as metric

4. **Multi-Criteria Scoring (AC4)**:
   - Loads rubric.yaml with criterion weights (accuracy=1.5, completeness=1.0, etc.)
   - Applies criterion_profiles based on test case category
   - Calculates weighted aggregate scores using `_calculate_weighted_score()`

5. **Judge Prompt Engineering (AC5)**:
   - System prompt includes all criteria with scoring guidance
   - User prompt anonymizes responses as "Response A" / "Response B"
   - Includes evaluation_hints from test case
   - Requires JSON output with chain-of-thought reasoning

6. **Quilto Response Generation (AC6)**:
   - Uses `execute_query_pipeline()` from swealog API
   - Creates temporary StorageRepository with proper nested structure
   - Handles errors gracefully (returns None, logs error)
   - Optional caching via `--cache-quilto-responses` flag

7. **CLI Runner (AC7)**: Full CLI in `run_evaluation.py`:
   - All required flags: --dataset-version, --cases, --judge-model, --dry-run, --verbose, --output-dir
   - Rich progress bar during evaluation
   - Results saved to `tests/eval/results/{version}/{timestamp}.json`
   - Summary table with win/tie/inconsistency rates and per-category breakdown

8. **DeepEval Integration (AC8)**: `PairwiseComparisonMetric` class:
   - Extends `BaseMetric` from deepeval
   - Sync `measure()` wraps async evaluation
   - Async `a_measure()` for native async usage
   - Configurable threshold (default 0.4)

9. **Tests**: 22 unit tests in `test_pairwise_judge.py` covering:
   - JSON parsing (direct, code block, embedded)
   - Weighted score calculation
   - Prompt building
   - Position swap with mock judge
   - Schema validation
   - DeepEval PairwiseComparisonMetric (conditionally skipped if deepeval not installed)
   - All tests pass with `make validate`

### File List

**Files CREATED:**
- `tests/eval/pairwise_judge.py` - Core PairwiseEvaluator class (~565 lines)
- `tests/eval/run_evaluation.py` - CLI runner script (441 lines)
- `tests/eval/metrics.py` - DeepEval custom metric (~225 lines)
- `tests/eval/results/.gitkeep` - Results directory
- `tests/eval/test_pairwise_judge.py` - Unit tests (~490 lines)

**Files MODIFIED:**
- `tests/eval/schema.py` - Added CriterionScore, JudgeResult, PairwiseResult, CategoryMetrics, EvaluationMetrics, EvaluationRun + `__test__ = False` to prevent pytest collection warning
- `tests/eval/__init__.py` - Export new schemas and classes with documentation for dynamic export pattern
- `tests/eval/README.md` - Comprehensive evaluation documentation

### Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5
**Date:** 2026-01-20

**Issues Found & Fixed:**
1. **H1 (FIXED):** PytestCollectionWarning for `TestCase` class - Added `__test__ = False` to prevent pytest from trying to collect it as a test class
2. **M1 (FIXED):** Temp directory cleanup - Changed `tempfile.mkdtemp()` to `tempfile.TemporaryDirectory()` context manager to ensure proper cleanup
3. **M2 (VERIFIED):** `.gitkeep` exists in results directory
4. **M3 (FIXED):** Format string error potential in `a_measure()` and `measure()` when aggregates are `None` - Added null checks before formatting
5. **M4 (FIXED):** Missing DeepEval metric tests - Added `TestPairwiseComparisonMetric` class with two tests
6. **L1 (NOTED):** Hardcoded tie threshold of 0.3 - Low priority, documented for future improvement
7. **L2 (FIXED):** Dynamic export pattern documentation - Added explanatory comments to `__init__.py`

**Validation:**
- `make check` passes (lint + typecheck)
- `make validate` passes (1773 passed, 44 skipped)
- All acceptance criteria verified against implementation
