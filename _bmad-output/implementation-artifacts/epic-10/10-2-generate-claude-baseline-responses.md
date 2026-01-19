# Story 10.2: Generate Claude Baseline Responses

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Quilto developer**,
I want **Claude responses generated for all 50 E2E test cases**,
So that **pairwise comparison has a high-quality baseline for evaluating Quilto agent quality**.

## Background

Story 10.1 created a golden dataset with 50 test cases in `tests/eval/golden/v2026-01-19.yaml`. Each test case includes:
- `id`: Unique identifier
- `category`: simple/complex/insufficient/retrieval/reasoning/edge/domain
- `query`: The user query text
- `context_entries`: List of entry dates to use as context
- `rubric_criteria`: Which criteria apply to this case
- `evaluation_hints`: What a good response should/shouldn't do

This story generates Claude responses for each test case, serving as baseline for pairwise LLM-as-judge evaluation (Story 10.3).

**Key Design Decisions:**
- Claude receives same context as Quilto (retrieved entries)
- Responses versioned with dataset version tag
- Generation script is idempotent (skips existing responses)
- Use LiteLLM directly for Claude API calls (test infrastructure, not framework code)
- Use `.env` loading from Story 9.1 for `ANTHROPIC_API_KEY`

## Acceptance Criteria

1. **AC1: Baseline Response Directory Created**
   - Given the `tests/eval/golden/` directory
   - When baseline generation is run
   - Then `tests/eval/golden/baseline_responses/` directory exists
   - And directory contains responses organized by version

2. **AC2: Generation Script Implemented**
   - Given a Python script `tests/eval/generate_baseline.py`
   - When script is run with `--dataset-version v2026-01-19`
   - Then Claude responses are generated for each test case
   - And responses are stored in JSON format with metadata
   - And script uses LiteLLM for Claude API calls
   - And script respects rate limits with appropriate delays

3. **AC3: Context Loading from Corpus**
   - Given a test case with `context_entries: ["2019-01-28", "2019-02-01"]`
   - When baseline generation runs
   - Then actual workout entry content is loaded from `tests/corpus/fitness/entries/from_csv/`
   - And content is formatted as context for Claude
   - And context format matches what Quilto Retriever provides

4. **AC4: Response Format Structured**
   - Given each baseline response
   - When stored as JSON
   - Then format includes:
     ```json
     {
       "test_case_id": "simple-bench-progression",
       "dataset_version": "v2026-01-19",
       "model": "openrouter/anthropic/claude-sonnet-4",
       "model_params": {"max_tokens": 1000, "temperature": 0.3},
       "generated_at": "2026-01-19T22:31:24.739535+00:00",
       "query": "How has my bench press progressed?",
       "context_entries": ["2019-01-29", "2019-02-01", "2019-03-12"],
       "context_provided": "<formatted entries>",
       "response": "<Claude's response text>"
     }
     ```
   - And responses are human-readable for manual inspection

5. **AC5: Idempotent Generation**
   - Given some baseline responses already exist
   - When script is run again
   - Then existing responses are skipped (not regenerated)
   - And only missing responses are generated
   - And `--force` flag regenerates all responses if needed

6. **AC6: All 50 Test Cases Have Responses**
   - Given the 50 test cases in the golden dataset
   - When baseline generation completes
   - Then all 50 test cases have corresponding baseline responses
   - And a validation script confirms completeness
   - And test coverage is 100%

7. **AC7: Prompt Design Matches Quilto Use Case**
   - Given the prompt template for Claude
   - When generating responses
   - Then system prompt explains Claude is answering fitness log queries
   - And context entries are clearly formatted
   - And Claude is instructed to answer based only on provided context
   - And prompt matches what a real user would experience from Quilto

## Tasks / Subtasks

- [x] Task 1: Create Directory Structure (AC: 1)
  - [x] Create `tests/eval/golden/baseline_responses/` directory
  - [x] Create `v2026-01-19/` subdirectory for versioned responses
  - [x] Directory populated with response files (no .gitkeep needed)

- [x] Task 2: Implement Context Loading and Prompt Template (AC: 3, 7)
  - [x] Create utility to load entry content by date from `tests/corpus/fitness/entries/from_csv/`
  - [x] Handle date format matching (YYYY-MM-DD)
  - [x] Format context entries as markdown (matching Quilto Retriever output format)
  - [x] Handle missing entries gracefully (log warning, continue)
  - [x] Create system prompt explaining fitness assistant use case
  - [x] Create user prompt template with query and context
  - [x] Ensure prompt instructs grounding responses in provided context only

- [x] Task 3: Add Pydantic Schema for Response (AC: 4)
  - [x] Add `BaselineResponse` model to `tests/eval/schema.py`
  - [x] Include: test_case_id, dataset_version, model, model_params, generated_at, query, context_entries, context_provided, response
  - [x] Validate response files on load

- [x] Task 4: Implement Generation Script (AC: 2, 4)
  - [x] Create `tests/eval/generate_baseline.py`
  - [x] Load `.env` using `dotenv` (consistent with Story 9.1 patterns)
  - [x] Parse CLI args: --dataset-version, --force, --dry-run, --cases
  - [x] Load golden dataset from YAML using existing `GoldenDataset` schema
  - [x] Call Claude via `litellm.acompletion` (model: `openrouter/anthropic/claude-sonnet-4`)
  - [x] Use `asyncio.Semaphore(2)` for controlled concurrency (2 concurrent requests max)
  - [x] Add `rich.progress` progress bar for generation status
  - [x] Save responses as validated JSON using `BaselineResponse` schema

- [x] Task 5: Implement Idempotency (AC: 5)
  - [x] Check for existing response files before generation
  - [x] Skip existing unless --force flag
  - [x] Log which cases are skipped vs generated
  - [x] Print summary at end: generated, skipped, failed counts

- [x] Task 6: Validate Completeness (AC: 6)
  - [x] Add `test_baseline_responses_complete()` to `tests/eval/test_eval_dataset.py`
  - [x] Test validates all 50 test cases have corresponding response JSON
  - [x] Test validates each response matches `BaselineResponse` schema
  - [x] Add --validate-only mode to generation script

- [x] Task 7: Update Module Exports
  - [x] Update `tests/eval/__init__.py` to export `BaselineResponse` schema
  - [x] Ensure `python -m tests.eval.generate_baseline` works correctly

- [x] Task 8: Run Generation and Verify
  - [x] Execute: `python -m tests.eval.generate_baseline --dataset-version v2026-01-19`
  - [x] Manually inspect 5-10 responses for quality
  - [x] Run `make validate` to ensure tests pass
  - [x] Commit generated responses to git

## Dev Notes

### Project Identity

This story creates test infrastructure in `tests/eval/`. This is **test code**, not application code.

- **Generation script**: `tests/eval/generate_baseline.py` (test infrastructure)
- **Baseline responses**: `tests/eval/golden/baseline_responses/` (test data, committed to git)
- **Schema extension**: `tests/eval/schema.py` (add `BaselineResponse` model)

### Directory Structure After Implementation

```
tests/eval/
├── __init__.py                             # Export BaselineResponse
├── golden/
│   ├── v2026-01-19.yaml                    # 50 test cases (Story 10.1)
│   └── baseline_responses/
│       └── v2026-01-19/
│           ├── simple-bench-progression.json
│           └── ... (50 response files total)
├── generate_baseline.py                    # NEW: Generation script
├── rubric.yaml
├── schema.py                               # MODIFIED: Add BaselineResponse
└── test_eval_dataset.py                    # MODIFIED: Add baseline tests
```

### BaselineResponse Schema

Add to `tests/eval/schema.py`:

```python
class ModelParams(BaseModel):
    """Parameters used for model generation."""
    max_tokens: int
    temperature: float

class BaselineResponse(BaseModel):
    """A baseline response from Claude for a test case."""
    test_case_id: str = Field(..., min_length=1)
    dataset_version: str
    model: str
    model_params: ModelParams
    generated_at: str  # ISO 8601 format
    query: str
    context_entries: list[str]
    context_provided: str
    response: str
```

### Complete Implementation Reference

```python
"""Generate Claude baseline responses for E2E evaluation."""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import litellm
from dotenv import load_dotenv
from rich.progress import Progress, TaskID

from tests.eval.schema import BaselineResponse, GoldenDataset, ModelParams, TestCase

logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
CORPUS_PATH = PROJECT_ROOT / "tests/corpus/fitness/entries/from_csv"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1000
TEMPERATURE = 0.3

SYSTEM_PROMPT = """You are a fitness assistant helping a user understand their workout history.
You have access to their logged workout entries provided below.

IMPORTANT:
- Base your response ONLY on the provided workout data
- If the data doesn't contain information to answer the question, say so clearly
- Use specific numbers and dates from the logs when relevant
- Be concise but complete
"""

def load_context_entries(dates: list[str]) -> str:
    """Load workout entries for given dates and format as context."""
    entries = []
    for date in dates:
        path = CORPUS_PATH / f"{date}.md"
        if path.exists():
            content = path.read_text().strip()
            entries.append(f"## Workout on {date}\n\n{content}")
        else:
            logger.warning("Missing entry for date: %s", date)
    return "\n\n---\n\n".join(entries)

async def generate_response(
    case: TestCase,
    dataset_version: str,
    semaphore: asyncio.Semaphore,
) -> BaselineResponse:
    """Generate a single Claude response with concurrency control."""
    context = load_context_entries(case.context_entries)

    async with semaphore:
        response = await litellm.acompletion(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"**Question:** {case.query}\n\n**My Workout Logs:**\n\n{context}"},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )

    return BaselineResponse(
        test_case_id=case.id,
        dataset_version=dataset_version,
        model=MODEL,
        model_params=ModelParams(max_tokens=MAX_TOKENS, temperature=TEMPERATURE),
        generated_at=datetime.now(timezone.utc).isoformat(),
        query=case.query,
        context_entries=case.context_entries,
        context_provided=context,
        response=response.choices[0].message.content or "",
    )
```

### API Key Configuration

Script uses `.env` loading (Story 9.1 pattern):

```bash
# .env (gitignored)
ANTHROPIC_API_KEY=sk-ant-...

# Run generation
python -m tests.eval.generate_baseline --dataset-version v2026-01-19
```

### CLI Interface

```bash
# Generate all baseline responses (with progress bar)
python -m tests.eval.generate_baseline --dataset-version v2026-01-19

# Force regeneration of all responses
python -m tests.eval.generate_baseline --dataset-version v2026-01-19 --force

# Dry run (show what would be generated)
python -m tests.eval.generate_baseline --dataset-version v2026-01-19 --dry-run

# Generate specific test cases only
python -m tests.eval.generate_baseline --dataset-version v2026-01-19 --cases simple-bench-progression,simple-heaviest-deadlift

# Validate existing responses only (no generation)
python -m tests.eval.generate_baseline --dataset-version v2026-01-19 --validate-only
```

### Test Validation

Add to `tests/eval/test_eval_dataset.py`:

```python
import pytest
from tests.eval.schema import BaselineResponse

@pytest.mark.skipif(
    not (Path("tests/eval/golden/baseline_responses/v2026-01-19")).exists(),
    reason="Baseline responses not yet generated"
)
def test_baseline_responses_complete() -> None:
    """Verify all test cases have valid baseline responses."""
    dataset = load_golden_dataset()
    responses_dir = Path("tests/eval/golden/baseline_responses/v2026-01-19")

    for case in dataset.test_cases:
        response_file = responses_dir / f"{case.id}.json"
        assert response_file.exists(), f"Missing baseline for {case.id}"

        # Validate schema
        data = json.loads(response_file.read_text())
        response = BaselineResponse.model_validate(data)
        assert response.test_case_id == case.id
```

### Cost Estimation

50 test cases with ~500 tokens input + ~500 tokens output each:
- Input: 50 × 500 = 25,000 tokens
- Output: 50 × 500 = 25,000 tokens
- Claude Sonnet: ~$3/M input, ~$15/M output
- **Estimated cost: ~$0.50 per full generation run**

### Critical Implementation Notes

1. **Concurrency Control**: Use `asyncio.Semaphore(2)` to limit concurrent API calls. Without this, you risk hitting rate limits.

2. **Progress Visibility**: Use `rich.progress` for user feedback during the ~30-75 second generation process.

3. **Schema Validation**: All responses must validate against `BaselineResponse` before saving. This catches malformed responses early.

4. **Idempotency**: Always check for existing files before generation. Default behavior is skip; --force overrides.

5. **Error Handling**: Log failures but continue generating other responses. Report failed cases in summary.

### References

- [epics.md#Story-10.2] - Story definition
- [tests/eval/golden/v2026-01-19.yaml] - 50 test cases
- [tests/eval/schema.py] - Existing schema to extend

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Created directory structure for baseline responses (directory populated with JSON files)
2. Implemented `BaselineResponse` and `ModelParams` Pydantic schemas in `tests/eval/schema.py`
3. Created full-featured generation script `tests/eval/generate_baseline.py` with:
   - Context loading from corpus files
   - System/user prompt templates for fitness assistant
   - Async generation with semaphore-controlled concurrency (2 concurrent)
   - Idempotency (skip existing, --force to regenerate)
   - CLI args: --dataset-version, --force, --dry-run, --cases, --validate-only, --verbose
   - Rich progress bar for generation status
   - Summary output (generated/skipped/failed counts)
4. Added 2 tests to `tests/eval/test_eval_dataset.py`:
   - `test_baseline_responses_complete()` - validates all 50 responses exist and match schema
   - `test_baseline_responses_have_content()` - validates responses contain actual content
5. Updated `tests/eval/__init__.py` to export new schemas
6. Used `openrouter/anthropic/claude-sonnet-4` via OpenRouter (project uses OpenRouter, not direct Anthropic API)
7. Generated all 50 baseline responses successfully
8. All eval tests pass: 12 tests in `tests/eval/test_eval_dataset.py`

### File List

- `tests/eval/golden/baseline_responses/v2026-01-19/*.json` (NEW - 50 files)
- `tests/eval/generate_baseline.py` (NEW)
- `tests/eval/schema.py` (MODIFIED - added ModelParams, BaselineResponse)
- `tests/eval/__init__.py` (MODIFIED - added exports)
- `tests/eval/test_eval_dataset.py` (MODIFIED - added TestBaselineResponseValidation)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED - status update)

