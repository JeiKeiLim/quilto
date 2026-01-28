# Story 18.2: Restore Debug Intermediate Output Printing

Status: backlog

## Story

As a **Swealog developer/user**,
I want `--debug` to print intermediate agent outputs,
so that I can see what each agent received and returned.

## Problem Statement

**Source:** Story 17.11 Dogfooding - User feedback in `2026-01-28_14b9034b.json`

**User Feedback:**
> "I don't know if retrieval was succeeded because middle output wasn't printed in terminal."

**Current Behavior:**
```
ℹ  6042ms - type=query
ℹ  8245ms - action=retrieve
ℹ  4ms - 12 entries
```

**Expected Behavior:**
```
[Router] input_type=QUERY, domains=[GeneralFitness, Strength, Running], confidence=0.95
[Planner] strategy=date_range, start=2025-12-31, end=2026-01-26, query_type=insight
[Retriever] found 23 entries
[Analyzer] verdict=sufficient, findings=[...], patterns=[...]
[Synthesizer] response="Based on your 23 workout sessions..."
```

**Impact:** Essential for debugging - users can't see what's happening in the flow.

## Acceptance Criteria

1. **Given** `--debug` flag is set
   **When** each agent completes
   **Then** agent output is printed to terminal in readable format

2. **Given** Router completes
   **When** output is printed
   **Then** shows `input_type`, `selected_domains`, `confidence`

3. **Given** Planner completes
   **When** output is printed
   **Then** shows `retrieval_instructions`, `query_type`, `next_action`

4. **Given** Retriever completes
   **When** output is printed
   **Then** shows entry count and date range covered

5. **Given** Analyzer completes
   **When** output is printed
   **Then** shows `verdict`, finding count, pattern count

6. **Given** Synthesizer completes
   **When** output is printed
   **Then** shows response preview (first 200 chars)

## Tasks

- [ ] Task 1: Review current `on_agent_complete` callback in CLI
  - Location: `packages/swealog/swealog/cli/run_cmd.py`
  - Understand current output formatting
  - Identify where full `output` dict is available but not printed

- [ ] Task 2: Create agent output formatters
  - Router: `input_type`, `selected_domains`, `confidence`
  - Planner: `retrieval_instructions`, `query_type`, `next_action`
  - Retriever: `total_entries_found`, date range
  - Analyzer: `verdict`, `findings` count, `patterns_identified` count
  - Synthesizer: response preview (truncated to 200 chars)
  - Evaluator: `overall_verdict`, dimension summaries

- [ ] Task 3: Update `on_agent_complete` to print formatted output when `--debug`
  - Use rich console for formatting if available
  - Fall back to simple print if not

- [ ] Task 4: Test with various query types
  - Verify all agent outputs are visible
  - Verify formatting is readable

- [ ] Task 5: Run validation - `make check` during dev, `make validate` before commit

## Dev Notes

### Story 16.1 Context

Story 16.1 added `output: dict[str, Any]` parameter to `on_agent_complete` callback. The output is available but the CLI isn't printing it.

### Current Callback Signature

```python
async def on_agent_complete(
    self, agent_name: str, duration: float, output: dict[str, Any] | None = None
) -> None:
```

### Example Output Format

```python
def format_router_output(output: dict) -> str:
    return (
        f"[Router] input_type={output.get('input_type')}, "
        f"domains={output.get('selected_domains')}, "
        f"confidence={output.get('confidence', 0):.0%}"
    )
```

### Files to Modify

- `packages/swealog/swealog/cli/run_cmd.py` - CLI progress handler
- Possibly `packages/swealog/swealog/cli/utils.py` - output formatters

### References

- [Source: `tests/eval/feedback/archive/iter-005/analysis.md` - Issue 1]
- [Source: Story 16.1 - Add Agent Output to ProgressHandler Callback]
