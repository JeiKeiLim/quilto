# Story 11.2: Implement Feedback Recording Infrastructure

Status: done

## Story

As a **Swealog developer**,
I want **feedback recording after swealog auto responses**,
So that **real-world usage quality can be tracked and improved through dogfooding iterations**.

## Acceptance Criteria

1. **AC1:** After a completed `swealog auto` response (QUERY or BOTH flows only), when `--debug` flag is active, system prompts user for feedback ("How was this response?")
2. **AC2:** User can provide natural language feedback or skip (press Enter with no input)
3. **AC3:** System records to `tests/eval/feedback/active/`:
   - Original query
   - Input type (LOG, QUERY, BOTH, CORRECTION)
   - All intermediate outputs (Router, Planner, Retriever, Analyzer, Synthesizer, Evaluator - last evaluation)
   - Final response
   - User feedback (empty string if skipped)
   - Timestamp, config path, storage path, and debug flag metadata
4. **AC4:** Feedback format is JSON for easy analysis and parsing
5. **AC5:** Feedback file naming follows pattern: `{YYYY-MM-DD}_{short-hash}.json` where hash is first 8 chars of SHA256(query)
6. **AC6:** All existing tests pass, new unit tests for feedback infrastructure
7. **AC7:** `make test-ollama` passes (integration tests with real Ollama)

## Tasks / Subtasks

- [x] **Task 1:** Create feedback storage directory structure (AC: 3, 4)
  - [x] 1.1: Create `tests/eval/feedback/active/` directory with `.gitkeep`
  - [x] 1.2: Create `tests/eval/feedback/archive/` directory with `.gitkeep`
  - [x] 1.3: Add `tests/eval/feedback/README.md` documenting:
    - Dogfooding iteration cycle (from epics.md)
    - Feedback JSON schema fields
    - Archive process when iteration completes
    - How to analyze collected feedback

- [x] **Task 2:** Define Pydantic schema for FeedbackRecord (AC: 3, 4)
  - [x] 2.1: Create `packages/swealog/swealog/cli/feedback.py` with FeedbackRecord model
  - [x] 2.2: Define IntermediateOutputs model with:
    - router: dict[str, Any] (from RouterOutput.model_dump())
    - planner: dict[str, Any] (from PlannerOutput.model_dump())
    - retriever: dict[str, Any] (from RetrieverOutput.model_dump())
    - analyzer: dict[str, Any] (from AnalyzerOutput.model_dump())
    - synthesizer: dict[str, Any] (from SynthesizerOutput.model_dump())
    - evaluator: dict[str, Any] (last EvaluatorOutput.model_dump(), may be after retry)
  - [x] 2.3: Add SessionMetadata model:
    - timestamp: datetime
    - input_type: Literal["LOG", "QUERY", "BOTH", "CORRECTION"]
    - config_path: str | None
    - storage_path: str | None
    - debug_enabled: bool = True
  - [x] 2.4: Add field for feedback_sentiment: str | None (for future auto-classification)
  - [x] 2.5: Unit tests for FeedbackRecord validation in `packages/swealog/tests/cli/test_feedback.py`

- [x] **Task 3:** Create FeedbackRecorder utility class (AC: 3, 4, 5)
  - [x] 3.1: Add `record()` method that writes JSON to `tests/eval/feedback/active/`
  - [x] 3.2: Generate file name as `{YYYY-MM-DD}_{short-hash}.json` where hash is first 8 chars of SHA256(query)
  - [x] 3.3: Handle duplicate queries: append timestamp seconds to hash if file exists (e.g., `2026-01-20_a1b2c3d4_153045.json`)
  - [x] 3.4: Add `get_feedback_dir()` method that returns Path to `tests/eval/feedback/active/` (relative to project root)
  - [x] 3.5: Unit tests for FeedbackRecorder in `packages/swealog/tests/cli/test_feedback.py`

- [x] **Task 4:** Modify execute_query_pipeline to collect intermediate outputs (AC: 3)
  - [x] 4.1: Add optional `collect_outputs: bool = False` parameter to `execute_query_pipeline()` at line 98
  - [x] 4.2: When enabled, store all agent outputs in returned dict as `intermediate_outputs` key
  - [x] 4.3: Store router_output from auto_cmd separately (router runs before pipeline in auto flow)
  - [x] 4.4: Ensure backward compatibility (existing callers unaffected, default False)
  - [x] 4.5: Unit tests for intermediate output collection

- [x] **Task 5:** Add feedback prompt to auto_cmd after QUERY/BOTH flows (AC: 1, 2)
  - [x] 5.1: Add `_prompt_for_feedback(debug: bool) -> str | None` helper in `auto_cmd.py`
  - [x] 5.2: Use `typer.prompt()` with empty string as default (allows skipping with Enter)
  - [x] 5.3: Only prompt when `--debug` flag is active AND flow is QUERY or BOTH
  - [x] 5.4: Display prompt after response is shown (after `_display_query_result()`), before command exits
  - [x] 5.5: Return None if debug=False, empty string if user skips, otherwise user input
  - [x] 5.6: Unit tests for feedback prompt in `packages/swealog/tests/cli/test_auto.py` (mock typer.prompt)

- [x] **Task 6:** Integrate feedback recording into auto command (AC: 1, 2, 3)
  - [x] 6.1: Pass `collect_outputs=True` to `execute_query_pipeline()` when debug mode is active
  - [x] 6.2: Capture router_output from auto_cmd for intermediate_outputs.router
  - [x] 6.3: After user feedback, create FeedbackRecord with:
    - id from `generate_feedback_id(query)`
    - query text
    - intermediate_outputs from pipeline result + router_output
    - final_response
    - user_feedback (empty string if skipped)
    - session metadata (timestamp, input_type, config_path, storage_path, debug_enabled)
  - [x] 6.4: Call `FeedbackRecorder.record()` to persist
  - [x] 6.5: Handle skip case (empty feedback) - still record but with empty feedback field
  - [x] 6.6: Integration tests in `packages/swealog/tests/cli/test_auto.py` for full flow

- [x] **Task 7:** Update exports and validation (AC: 6, 7)
  - [x] 7.1: Export FeedbackRecord, FeedbackRecorder, IntermediateOutputs, SessionMetadata, generate_feedback_id in `cli/__init__.py`
  - [x] 7.2: Add exports to `__all__` list in `cli/__init__.py`
  - [x] 7.3: Run `make check` - ensure lint/typecheck passes
  - [x] 7.4: Run `make validate` - all unit tests pass
  - [x] 7.5: Run `make test-ollama` - integration tests pass (1873 passed, 1 pre-existing failure)

## Dev Notes

### Architecture Compliance

This story adds feedback infrastructure to the **Swealog** package (not Quilto):
- Feedback collection is application-specific behavior
- CLI commands live in `packages/swealog/swealog/cli/`
- Storage destination `tests/eval/feedback/` is in the test infrastructure

### Existing Code References

| File | Purpose | Key Lines |
|------|---------|-----------|
| `packages/swealog/swealog/cli/auto_cmd.py` | Auto command to modify | Lines 101-137 (QUERY flow), 113-137 (BOTH flow) |
| `packages/swealog/swealog/cli/debug.py` | DebugLogger pattern to follow | Lines 64-129 |
| `packages/swealog/swealog/api/routes/query.py` | Query pipeline to modify | `execute_query_pipeline()` lines 93-245, add param at line 98 |
| `packages/swealog/swealog/cli/__init__.py` | Export list to update | Lines 37-66 `__all__` list |
| `tests/eval/schema.py` | Pydantic patterns for evaluation | Full file - follow ConfigDict, Field patterns |

### FeedbackRecorder Implementation

```python
import json
from datetime import datetime
from pathlib import Path

class FeedbackRecorder:
    """Utility class for recording user feedback to disk.

    Writes FeedbackRecord instances as JSON files to the feedback directory.
    Handles duplicate queries by appending timestamp suffix.
    """

    def __init__(self, feedback_dir: Path | None = None) -> None:
        """Initialize the feedback recorder.

        Args:
            feedback_dir: Directory for feedback files. Defaults to
                tests/eval/feedback/active/ relative to project root.
        """
        if feedback_dir is None:
            # Find project root (contains pyproject.toml)
            feedback_dir = self._find_project_root() / "tests" / "eval" / "feedback" / "active"
        self._feedback_dir = feedback_dir

    def _find_project_root(self) -> Path:
        """Find project root by looking for pyproject.toml."""
        current = Path.cwd()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent
        return Path.cwd()  # Fallback

    def record(self, feedback: "FeedbackRecord") -> Path:
        """Write feedback record to disk.

        Args:
            feedback: The FeedbackRecord to persist.

        Returns:
            Path to the created feedback file.
        """
        self._feedback_dir.mkdir(parents=True, exist_ok=True)
        file_path = get_unique_feedback_path(self._feedback_dir, feedback.id)
        file_path.write_text(
            feedback.model_dump_json(indent=2),
            encoding="utf-8"
        )
        return file_path
```

### Feedback Record Schema

```python
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Any, Literal

class IntermediateOutputs(BaseModel):
    """Intermediate agent outputs from query pipeline.

    All fields store model_dump() output from respective agent outputs.
    These are dicts, not typed models, for flexibility and JSON serialization.
    """
    model_config = ConfigDict(strict=True)

    router: dict[str, Any]        # RouterOutput.model_dump()
    planner: dict[str, Any]       # PlannerOutput.model_dump()
    retriever: dict[str, Any]     # RetrieverOutput.model_dump()
    analyzer: dict[str, Any]      # AnalyzerOutput.model_dump()
    synthesizer: dict[str, Any]   # SynthesizerOutput.model_dump()
    evaluator: dict[str, Any]     # Last EvaluatorOutput.model_dump() (may be after retry)

class SessionMetadata(BaseModel):
    """Session context for the feedback record."""
    model_config = ConfigDict(strict=True)

    timestamp: datetime
    input_type: Literal["LOG", "QUERY", "BOTH", "CORRECTION"]
    config_path: str | None = None
    storage_path: str | None = None
    debug_enabled: bool = True

class FeedbackRecord(BaseModel):
    """Complete feedback record for dogfooding analysis.

    Records user feedback after a swealog auto response for quality tracking.
    Stored in tests/eval/feedback/active/ as JSON files.
    """
    model_config = ConfigDict(strict=True)

    id: str = Field(..., min_length=1)  # {YYYY-MM-DD}_{short-hash}
    query: str = Field(..., min_length=1)
    intermediate_outputs: IntermediateOutputs
    final_response: str
    user_feedback: str  # Empty string if skipped
    session: SessionMetadata
    feedback_sentiment: str | None = None  # Future: auto-classify
```

### Query Pipeline Modification

The `execute_query_pipeline()` function in `packages/swealog/swealog/api/routes/query.py:93` needs to optionally return intermediate outputs.

**Important:** Router runs in `auto_cmd.py` BEFORE calling `execute_query_pipeline()`, so router_output must be captured separately in auto_cmd and merged with pipeline outputs.

```python
async def execute_query_pipeline(
    query: str,
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
    debug_callback: DebugCallback | None = None,
    collect_outputs: bool = False,  # NEW parameter
) -> dict[str, Any]:
    """Execute the full query pipeline.

    Args:
        query: The user's query text.
        llm_client: LLM client for agents.
        storage: Storage repository for entries.
        domains: Available domain modules.
        debug_callback: Optional callback for debug logging.
        collect_outputs: If True, include intermediate_outputs in result.

    Returns:
        Dict with response, sources, confidence, is_partial.
        If collect_outputs=True, also includes intermediate_outputs dict
        (excluding router - that runs before pipeline in auto flow).
    """
    # ... existing code at lines 117-239 ...

    # Build result at end (modify existing lines 240-245):
    result = {
        "response": final_response,
        "sources": sources,
        "confidence": confidence,
        "is_partial": is_partial,
    }

    if collect_outputs:
        # Note: router_output not available here - captured in auto_cmd.py
        result["intermediate_outputs"] = {
            "planner": planner_output.model_dump(),
            "retriever": retriever_output.model_dump(),
            "analyzer": analysis.model_dump(),
            "synthesizer": synthesizer_output.model_dump(),
            "evaluator": evaluation.model_dump(),  # Last evaluation (may be after retry)
        }

    return result
```

**In auto_cmd.py:** Merge router_output with pipeline intermediate_outputs:

```python
# In QUERY or BOTH flow, after execute_query_pipeline returns:
if debug and "intermediate_outputs" in result:
    result["intermediate_outputs"]["router"] = router_output.model_dump()
```

### Feedback Prompt Implementation

```python
def _prompt_for_feedback(debug: bool) -> str | None:
    """Prompt user for feedback if debug mode is active.

    Returns:
        User feedback string or None if debug disabled.
        Empty string if user skipped.
    """
    if not debug:
        return None

    print()  # Blank line before prompt
    return typer.prompt(
        "How was this response? (press Enter to skip)",
        default="",
        show_default=False,
    )
```

### File Naming Convention

Pattern: `{YYYY-MM-DD}_{short-hash}.json`

Example: `2026-01-20_a1b2c3d4.json`

Hash is first 8 characters of SHA256 of the query string, ensuring uniqueness while being human-readable.

**Duplicate Handling:** If file already exists (same query same day), append timestamp seconds:
- First: `2026-01-20_a1b2c3d4.json`
- Duplicate: `2026-01-20_a1b2c3d4_153045.json` (HHMMss)

```python
import hashlib
from datetime import datetime
from pathlib import Path

def generate_feedback_id(query: str) -> str:
    """Generate unique ID for feedback record.

    Args:
        query: The query string to hash.

    Returns:
        ID in format YYYY-MM-DD_xxxxxxxx where x is first 8 chars of SHA256.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    query_hash = hashlib.sha256(query.encode()).hexdigest()[:8]
    return f"{date_str}_{query_hash}"


def get_unique_feedback_path(base_dir: Path, feedback_id: str) -> Path:
    """Get unique file path, handling duplicates.

    Args:
        base_dir: Directory to write feedback files.
        feedback_id: Base ID from generate_feedback_id().

    Returns:
        Unique path (appends timestamp if needed).
    """
    base_path = base_dir / f"{feedback_id}.json"
    if not base_path.exists():
        return base_path

    # Append timestamp for uniqueness
    timestamp = datetime.now().strftime("%H%M%S")
    return base_dir / f"{feedback_id}_{timestamp}.json"
```

### Project Structure Notes

Storage location for feedback:
```
tests/eval/feedback/
├── active/                    # Current collection (not gitignored)
│   ├── .gitkeep
│   └── 2026-01-20_abc12345.json
├── archive/                   # Completed iterations (not gitignored)
│   └── .gitkeep
└── README.md                  # Documentation
```

Note: Feedback files should be committed to track dogfooding progress. They are test artifacts, not runtime data.

### Testing Strategy

1. **Unit tests** in `packages/swealog/tests/cli/test_feedback.py`:
   - FeedbackRecord validation (empty query rejected, empty feedback allowed)
   - IntermediateOutputs validation (all fields required)
   - SessionMetadata validation (input_type literal enforcement)
   - FeedbackRecorder.record() (file creation, naming, duplicate handling)
   - generate_feedback_id() (hash generation, format validation)
   - get_unique_feedback_path() (duplicate path generation)

2. **Unit tests** in `packages/swealog/tests/cli/test_auto.py`:
   - _prompt_for_feedback() with mocked typer.prompt
   - Returns None when debug=False
   - Returns empty string when user presses Enter
   - Returns user input when provided

3. **Integration tests** in `packages/swealog/tests/cli/test_auto.py`:
   - Full auto command QUERY flow with mocked LLM and typer.prompt
   - Full auto command BOTH flow with mocked LLM and typer.prompt
   - Verify feedback file is created in correct location
   - Verify feedback file contains all required fields
   - Verify skip case (empty feedback) still records file

### Previous Story Intelligence

From Story 11.1:
- JSON schema structured output is now working for OpenRouter/OpenAI
- `[null]` normalization was added to ClarificationQuestion
- Trailing comma handling was added to _extract_json()

These changes mean intermediate outputs should serialize cleanly to JSON without issues.

### Git Intelligence

Recent commits show:
- Story 11.1 added helper methods `_build_response_format()` and `_extract_json()` to LLMClient
- Story 10.5 fixed retrieval strategy priority in Planner
- Story 10.4 added pytest integration for evaluation

The feedback infrastructure builds on these foundations.

### References

- [Source: epics.md#Story-11.2] Acceptance criteria and rationale
- [Source: architecture.md#CLI-&-Future-Web] CLI uses typer + rich
- [Source: project-context.md#Development-Workflow] Validate with make commands
- [Source: story-11-1] Previous story learnings on JSON handling

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- All 7 tasks completed successfully
- 22 unit tests in `test_feedback.py` for feedback models
- 11 additional tests in `test_cli_auto.py` for feedback prompt/record integration
- 3 additional tests in `test_api_routes.py` for collect_outputs parameter
- `make check`: passes (lint + typecheck)
- `make test-ollama`: 1888 passed, 56 skipped, 0 failed (28:06 runtime)
- Feedback infrastructure is fully functional and ready for dogfooding

### Code Review Notes (2026-01-20)

**Issues Found and Fixed:**
1. Task 5.6 was marked complete but tests were missing - Added 4 tests for `_prompt_for_feedback()` in `test_cli_auto.py`
2. Task 6.6 was marked complete but tests were missing - Added 7 integration tests for feedback flow in `test_cli_auto.py`
3. Task 4.5 tests for `collect_outputs` were missing - Added 3 tests in `test_api_routes.py`
4. Story incorrectly referenced `tests/cli/test_auto.py` which didn't exist - Tests added to existing `test_cli_auto.py`

**Known Issue (Not Fixed - Architectural):**
- Router is executed twice: once in `auto_cmd.py` for classification, and again inside `execute_query_pipeline()`. This is a performance issue but requires larger architectural change to fix.

### File List

| File | Action | Purpose |
|------|--------|---------|
| `tests/eval/feedback/active/.gitkeep` | Create | Directory for active feedback collection |
| `tests/eval/feedback/archive/.gitkeep` | Create | Directory for completed iteration archives |
| `tests/eval/feedback/README.md` | Create | Documentation for feedback collection process |
| `packages/swealog/swealog/cli/feedback.py` | Create | FeedbackRecord, FeedbackRecorder, IntermediateOutputs, SessionMetadata, generate_feedback_id, get_unique_feedback_path |
| `packages/swealog/swealog/cli/__init__.py` | Modify | Export new classes in `__all__` |
| `packages/swealog/swealog/api/routes/query.py` | Modify | Add `collect_outputs` parameter to `execute_query_pipeline()` |
| `packages/swealog/swealog/cli/auto_cmd.py` | Modify | Add `_prompt_for_feedback()`, `_record_feedback()`, integrate FeedbackRecorder |
| `packages/swealog/tests/cli/__init__.py` | Create | CLI tests package init |
| `packages/swealog/tests/cli/test_feedback.py` | Create | 22 unit tests for FeedbackRecord, FeedbackRecorder, IntermediateOutputs, SessionMetadata |
| `packages/swealog/tests/test_cli_auto.py` | Modify | Added 11 tests for feedback prompt/record (TestPromptForFeedback, TestRecordFeedback, TestAutoCommandFeedbackIntegration) |
| `packages/swealog/tests/test_api_routes.py` | Modify | Added 3 tests for collect_outputs parameter (TestExecuteQueryPipelineCollectOutputs) |
