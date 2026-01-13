# Story 4.3: Implement Evaluator Agent with Retry Loop

Status: done

## Story

As a **Quilto developer**,
I want an **Evaluator agent that quality-checks responses**,
so that **users receive accurate, well-supported answers**.

## Acceptance Criteria

1. **Given** query, response, and context
   **When** Evaluator checks it
   **Then** it returns PASS/FAIL verdict with specific feedback

2. **Given** the Evaluator agent
   **When** it evaluates a response
   **Then** it checks four dimensions: accuracy, relevance, safety, completeness

3. **Given** a FAIL verdict
   **When** issues are identified
   **Then** feedback includes specific, actionable suggestions for retry

4. **Given** the retry loop
   **When** Evaluator returns FAIL
   **Then** retry loop runs up to 2 times before returning partial + gaps

5. **Given** domain-specific evaluation rules
   **When** Evaluator checks response
   **Then** it applies the rules from `evaluation_rules` list

6. **Given** ANY dimension fails
   **When** overall verdict is computed
   **Then** overall_verdict = FAIL (strict AND logic)

7. **Given** the Evaluator agent
   **When** instantiated and used
   **Then** it follows the same LLMClient pattern as Router, Parser, Planner, Retriever, Analyzer, and Synthesizer

8. **Given** EvaluatorInput model
   **When** entries_summary is provided
   **Then** it must be a non-empty string (Field(min_length=1))

9. **Given** the evaluate method
   **When** query or response is empty/whitespace
   **Then** it raises ValueError with descriptive message

## Tasks / Subtasks

- [x] Task 1: Create Evaluator Pydantic models (AC: #1, #2, #3, #5, #6, #8)
  - [x] 1.1: Define `EvaluationDimension` model in `agents/models.py`
    - `dimension`: Literal["accuracy", "relevance", "safety", "completeness"]
    - `verdict`: Verdict (only SUFFICIENT/INSUFFICIENT valid for dimension-level)
    - `reasoning`: str = Field(min_length=1)
    - `issues`: list[str] = Field(default_factory=list)
  - [x] 1.2: Define `EvaluatorInput` model in `agents/models.py`
    - `query`: str = Field(min_length=1)
    - `response`: str = Field(min_length=1)
    - `analysis`: AnalyzerOutput
    - `entries_summary`: str = Field(min_length=1) **NEW AC #8**
    - `evaluation_rules`: list[str]
    - `attempt_number`: int = Field(default=1, ge=1)
    - `previous_feedback`: list[EvaluationFeedback] = Field(default_factory=list)
  - [x] 1.3: Define `EvaluatorOutput` model in `agents/models.py`
    - `dimensions`: list[EvaluationDimension]
    - `overall_verdict`: Verdict
    - `feedback`: list[EvaluationFeedback] = Field(default_factory=list)
    - `recommendation`: Literal["accept", "retry_with_feedback", "retry_with_more_context", "give_partial"]

- [x] Task 2: Create EvaluatorAgent class (AC: #7)
  - [x] 2.1: Create `packages/quilto/quilto/agents/evaluator.py`
  - [x] 2.2: Define `EvaluatorAgent` class with `AGENT_NAME = "evaluator"`
  - [x] 2.3: Implement `__init__(self, llm_client: LLMClient)`
  - [x] 2.4: Add Google-style docstrings with examples

- [x] Task 3: Build Evaluator prompt (AC: #1, #2, #5, #6)
  - [x] 3.1: Implement `build_prompt(self, evaluator_input: EvaluatorInput) -> str`
  - [x] 3.2: Implement `_format_analysis(analysis: AnalyzerOutput) -> str` helper
  - [x] 3.3: Implement `_format_evaluation_rules(rules: list[str]) -> str` helper
  - [x] 3.4: Implement `_format_previous_feedback(feedback: list[EvaluationFeedback]) -> str` helper
  - [x] 3.5: Include four evaluation dimensions with clear PASS/FAIL criteria
  - [x] 3.6: Include verdict logic: ANY FAIL = overall FAIL

- [x] Task 4: Implement evaluate method (AC: #1, #6, #9)
  - [x] 4.1: Implement `async def evaluate(self, evaluator_input: EvaluatorInput) -> EvaluatorOutput`
  - [x] 4.2: Validate query is not empty/whitespace (raise ValueError per AC #9)
  - [x] 4.3: Validate response is not empty/whitespace (raise ValueError per AC #9)
  - [x] 4.4: Call LLM with structured output to `EvaluatorOutput`
  - [x] 4.5: Use assertion pattern: `assert isinstance(result, EvaluatorOutput)`
  - [x] 4.6: Return parsed result

- [x] Task 5: Add helper methods
  - [x] 5.1: `is_passed(self, output: EvaluatorOutput) -> bool`
    - Returns True if overall_verdict == Verdict.SUFFICIENT
  - [x] 5.2: `get_failed_dimensions(self, output: EvaluatorOutput) -> list[EvaluationDimension]`
    - Returns dimensions where verdict == Verdict.INSUFFICIENT
  - [x] 5.3: `get_all_issues(self, output: EvaluatorOutput) -> list[str]`
    - Aggregates all issues from all failed dimensions into flat list
  - [x] 5.4: `should_retry(self, output: EvaluatorOutput, attempt_number: int, max_retries: int = 2) -> bool`
    - Returns True if NOT passed AND attempt_number < max_retries

- [x] Task 6: Export from agents __init__.py
  - [x] 6.1: Add EvaluatorAgent to imports
  - [x] 6.2: Add EvaluatorInput, EvaluatorOutput, EvaluationDimension to imports
  - [x] 6.3: Update `__all__` list with all new exports (4 new items)

- [x] Task 7: Create comprehensive unit tests in `packages/quilto/tests/test_evaluator.py` (~60-70 tests expected)
  - [x] 7.1: Test model validation for EvaluationDimension, EvaluatorInput, EvaluatorOutput
    - [x] 7.1.1: Test Field(min_length=1) constraints for query, response, entries_summary, reasoning
    - [x] 7.1.2: Test dimension Literal validation ("accuracy", "relevance", "safety", "completeness")
    - [x] 7.1.3: Test recommendation Literal validation ("accept", "retry_with_feedback", "retry_with_more_context", "give_partial")
    - [x] 7.1.4: Test Verdict reuse for dimension.verdict and overall_verdict
    - [x] 7.1.5: Test attempt_number default (1) and validation (ge=1)
    - [x] 7.1.6: Test previous_feedback default (empty list via default_factory)
    - [x] 7.1.7: Test boundary values: attempt_number=0 (should fail), attempt_number=1 (should pass)
    - [x] 7.1.8: Test empty string "" for query/response/entries_summary (should fail min_length=1)
  - [x] 7.2: Test EvaluatorAgent instantiation
  - [x] 7.3: Test prompt building
    - [x] 7.3.1: Test _format_analysis helper method
    - [x] 7.3.2: Test _format_evaluation_rules helper method (empty and non-empty rules)
    - [x] 7.3.3: Test _format_previous_feedback helper method (first attempt, retry)
    - [x] 7.3.4: Test _format_entries_summary helper method (formats context for prompt)
    - [x] 7.3.5: Test build_prompt includes all four dimensions
    - [x] 7.3.6: Test build_prompt with retry context (attempt_number > 1)
    - [x] 7.3.7: Test build_prompt includes evaluation_rules in output
  - [x] 7.4: Test helper methods
    - [x] 7.4.1: Test is_passed with all PASS dimensions
    - [x] 7.4.2: Test is_passed with one FAIL dimension
    - [x] 7.4.3: Test is_passed with all FAIL dimensions
    - [x] 7.4.4: Test get_failed_dimensions returns only INSUFFICIENT dimensions
    - [x] 7.4.5: Test get_failed_dimensions with no failures returns empty list
    - [x] 7.4.6: Test get_all_issues aggregates from all failed dimensions
    - [x] 7.4.7: Test get_all_issues returns empty list when no failures
    - [x] 7.4.8: Test should_retry returns True when FAIL and attempt < max
    - [x] 7.4.9: Test should_retry returns False when PASS
    - [x] 7.4.10: Test should_retry returns False when attempt >= max_retries
  - [x] 7.5: Test evaluate method with mock LLM
    - [x] 7.5.1: Test ValueError raised for empty query
    - [x] 7.5.2: Test ValueError raised for whitespace-only query
    - [x] 7.5.3: Test ValueError raised for empty response
    - [x] 7.5.4: Test ValueError raised for whitespace-only response
    - [x] 7.5.5: Test successful evaluation returns EvaluatorOutput
  - [x] 7.6: Test all exports importable from quilto.agents
    - [x] 7.6.1: Test EvaluatorAgent importable
    - [x] 7.6.2: Test EvaluatorInput importable
    - [x] 7.6.3: Test EvaluatorOutput importable
    - [x] 7.6.4: Test EvaluationDimension importable

- [x] Task 8: Update scripts/manual_test.py
  - [x] 8.1: Add imports for EvaluatorAgent, EvaluatorInput, EvaluatorOutput, EvaluationDimension
    - Location: After SynthesizerOutput import (~line 71)
  - [x] 8.2: Add `get_evaluation_rules(selected_domains: list[str]) -> list[str]` helper
    - Returns merged evaluation_rules from selected domain modules
    - Falls back to DEFAULT_EVALUATION_RULES if domains have no rules
  - [x] 8.3: Add `build_entries_summary(entries: list[Any]) -> str` helper
    - Summarizes retrieved entries for evaluator context
  - [x] 8.4: Add `run_evaluator` function after `run_synthesizer` (~line 467)
  - [x] 8.5: Add `run_retry_loop` function implementing the evaluation loop with max 2 retries
  - [x] 8.6: Integrate in QUERY flow: call evaluator after Synthesizer
    - Location: After `synthesizer_result, _ = await run_synthesizer(...)` (~line 548-554)
  - [x] 8.7: Integrate in BOTH flow: call evaluator after Synthesizer
    - Location: After `synthesizer_result, _ = await run_synthesizer(...)` (~line 606-615)
  - [x] 8.8: Update script docstring to mention Evaluator agent

- [x] Task 9: Run validation
  - [x] 9.1: Run `make check` (lint + typecheck)
  - [x] 9.2: Run `make validate` (full validation)
  - [x] 9.3: Run `make test-ollama` (integration tests)

## Dev Notes

### Architecture Patterns

- **Location:** `packages/quilto/quilto/agents/evaluator.py` (Quilto framework, NOT Swealog)
- **Pattern:** Follow existing agent patterns from `analyzer.py` and `synthesizer.py`
- **Model Requirement:** MEDIUM-HIGH tier - critical quality assessment

### EvaluatorInput Model (from agent-system-design.md Section 11.7)

**CRITICAL:** Use `model_config = ConfigDict(strict=True)` per project-context.md

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from quilto.agents.models import AnalyzerOutput, EvaluationFeedback, Verdict

class EvaluatorInput(BaseModel):
    """Input to Evaluator agent."""
    model_config = ConfigDict(strict=True)

    query: str = Field(min_length=1)  # Required, non-empty
    response: str = Field(min_length=1)  # From Synthesizer, non-empty

    # Context for fact-checking
    analysis: AnalyzerOutput
    entries_summary: str = Field(min_length=1)  # Summary of retrieved entries (AC #8)

    # Domain-specific evaluation rules
    evaluation_rules: list[str]

    # Retry context
    attempt_number: int = Field(default=1, ge=1)
    previous_feedback: list[EvaluationFeedback] = Field(default_factory=list)
```

### EvaluationDimension Model

```python
class EvaluationDimension(BaseModel):
    """Evaluation on a single dimension."""
    model_config = ConfigDict(strict=True)

    dimension: Literal["accuracy", "relevance", "safety", "completeness"]
    verdict: Verdict  # Reuse existing Verdict enum (SUFFICIENT=PASS, INSUFFICIENT=FAIL)
    reasoning: str = Field(min_length=1)
    issues: list[str] = Field(default_factory=list)
```

**Note on Verdict reuse:** The existing `Verdict` enum has values `SUFFICIENT`, `INSUFFICIENT`, `PARTIAL`. For evaluator dimensions:
- `SUFFICIENT` = dimension passed
- `INSUFFICIENT` = dimension failed
- `PARTIAL` is not used for dimension-level verdicts (only for overall_verdict if needed)

### EvaluatorOutput Model

```python
class EvaluatorOutput(BaseModel):
    """Output from Evaluator agent."""
    model_config = ConfigDict(strict=True)

    # Dimension-level evaluation
    dimensions: list[EvaluationDimension]

    # Overall verdict - ANY dimension FAIL = overall FAIL
    overall_verdict: Verdict

    # If FAIL, specific feedback for retry
    feedback: list[EvaluationFeedback] = Field(default_factory=list)

    # Recommendation for what to do next
    recommendation: Literal[
        "accept",              # All passed, return response
        "retry_with_feedback", # FAIL but retryable with feedback
        "retry_with_more_context",  # Need more context (re-retrieve)
        "give_partial"         # Over retry limit, return partial answer
    ]
```

### Evaluation Dimensions (from agent-system-design.md Section 11.7)

| Dimension | Question | FAIL if |
|-----------|----------|---------|
| **Accuracy** | Claims supported by evidence? | Speculation without data, claim not in analysis |
| **Relevance** | Answers what user asked? | Tangential information without answering |
| **Safety** | No harmful recommendations? | Violates domain evaluation_rules |
| **Completeness** | Addresses all parts of query? | Missing major aspects of query |

### Verdict Logic

**CRITICAL:** This is strict AND logic:
- If **ANY** dimension verdict is `INSUFFICIENT` → `overall_verdict = INSUFFICIENT`
- If **ALL** dimension verdicts are `SUFFICIENT` → `overall_verdict = SUFFICIENT`

### Retry Loop Logic (for manual_test.py)

```python
async def run_retry_loop(
    client: LLMClient,
    query: str,
    synthesizer_input: SynthesizerInput,
    evaluator_input_base: dict,  # Base inputs without attempt_number/previous_feedback
    max_retries: int = 2,
) -> tuple[SynthesizerOutput, EvaluatorOutput]:
    """Run evaluation loop with retry on FAIL.

    Flow:
    1. Synthesize response
    2. Evaluate response
    3. If FAIL and attempt < max_retries: retry with feedback
    4. If FAIL and attempt >= max_retries: return partial answer
    5. If PASS: return response
    """
    synthesizer = SynthesizerAgent(client)
    evaluator = EvaluatorAgent(client)

    attempt_number = 1
    previous_feedback: list[EvaluationFeedback] = []

    while attempt_number <= max_retries + 1:  # +1 for initial attempt
        # Generate response
        if attempt_number == 1:
            synth_output = await synthesizer.synthesize(synthesizer_input)
        else:
            # Re-synthesize with feedback context
            # (In full implementation, feedback would modify synthesizer prompt)
            synth_output = await synthesizer.synthesize(synthesizer_input)

        # Evaluate response
        eval_input = EvaluatorInput(
            **evaluator_input_base,
            response=synth_output.response,
            attempt_number=attempt_number,
            previous_feedback=previous_feedback,
        )
        eval_output = await evaluator.evaluate(eval_input)

        # Check result
        if evaluator.is_passed(eval_output):
            return synth_output, eval_output

        # Collect feedback for next attempt
        previous_feedback.extend(eval_output.feedback)
        attempt_number += 1

    # Over retry limit - return partial answer
    # Mark synthesizer input as partial for final attempt
    synthesizer_input_partial = SynthesizerInput(
        **synthesizer_input.model_dump(),
        is_partial=True,
        unanswered_gaps=...,  # Extract from analysis
    )
    final_output = await synthesizer.synthesize(synthesizer_input_partial)
    return final_output, eval_output
```

### State Machine Transitions (from state-machine-diagram.md)

```
SYNTHESIZE → EVALUATE       # Always
EVALUATE → OBSERVE          # verdict == PASS
EVALUATE → PLAN             # verdict == FAIL, retry_count < max
EVALUATE → OBSERVE          # verdict == FAIL, retry_count >= max (partial)
```

### LLM Prompt Template (from agent-system-design.md Section 12.7)

```
ROLE: You are a quality assurance agent. Your job is to critically assess responses before they reach the user.

TASK: Evaluate the response on multiple dimensions. Be strict but fair.

=== EVALUATION DIMENSIONS ===

1. ACCURACY
   - Every claim must be supported by evidence
   - Speculation without data = FAIL
   - Check claims against the analysis findings

2. RELEVANCE
   - Response must address what the user actually asked
   - Tangential information without answering the question = FAIL

3. SAFETY
   - Apply domain-specific safety rules below
   - Harmful or dangerous recommendations = FAIL

4. COMPLETENESS
   - All parts of the query should be addressed
   - Missing major aspects = FAIL

=== DOMAIN SAFETY RULES ===
{evaluation_rules}

=== VERDICT LOGIC ===

- If ANY dimension is INSUFFICIENT → overall_verdict = INSUFFICIENT
- If ALL dimensions are SUFFICIENT → overall_verdict = SUFFICIENT

=== INPUT ===

Original query: {query}
Response to evaluate: {response}
Analysis findings: {analysis}
Available evidence: {entries_summary}
Attempt number: {attempt_number}
Previous feedback: {previous_feedback}

=== OUTPUT (JSON) ===
{EvaluatorOutput.model_json_schema()}

For any INSUFFICIENT verdict, provide specific, actionable feedback that can guide a retry.
```

### Example Output (for reference)

```json
{
  "dimensions": [
    {
      "dimension": "accuracy",
      "verdict": "SUFFICIENT",
      "reasoning": "All claims about bench press progression are supported by the cited dates and weights.",
      "issues": []
    },
    {
      "dimension": "relevance",
      "verdict": "SUFFICIENT",
      "reasoning": "Response directly addresses the user's question about bench press progress.",
      "issues": []
    },
    {
      "dimension": "safety",
      "verdict": "SUFFICIENT",
      "reasoning": "No harmful recommendations. Response is purely informational.",
      "issues": []
    },
    {
      "dimension": "completeness",
      "verdict": "INSUFFICIENT",
      "reasoning": "User asked about progression but response doesn't mention rep counts or volume trends.",
      "issues": ["Missing volume analysis", "No mention of rep ranges over time"]
    }
  ],
  "overall_verdict": "INSUFFICIENT",
  "feedback": [
    {
      "issue": "Response lacks volume analysis",
      "suggestion": "Include how total volume (sets x reps x weight) has changed",
      "affected_claim": null
    }
  ],
  "recommendation": "retry_with_feedback"
}
```

### Integration with Query Flow

The Evaluator is called after Synthesizer in the query flow:
```
Planner -> Retriever -> Analyzer -> Synthesizer -> Evaluator
                                          ↑___________|  (retry loop)
```

### Project Structure Notes

- File: `packages/quilto/quilto/agents/evaluator.py`
- Tests: `packages/quilto/tests/test_evaluator.py`
- This is **Quilto framework** code (domain-agnostic)
- Uses same patterns as Router, Parser, Planner, Retriever, Analyzer, Synthesizer

### Testing Standards (from project-context.md)

- **Boundary tests:** Test Field min_length=1, ge=1 constraints
- **Empty vs None:** Test both `None` and `""` for optional string fields
- **ConfigDict:** Use `model_config = ConfigDict(strict=True)` for all models
- **All exports:** Verify importable from `quilto.agents`
- **Mock LLM:** Use mock_llm fixture for unit tests
- **Integration:** Run `make test-ollama` to verify with real LLM

### Previous Story Learnings (Story 4-1 and 4-2)

From Story 4-1 (Analyzer) and 4-2 (Synthesizer):

1. **Use ConfigDict(strict=True)** for all Pydantic models
2. **Field(min_length=1)** for required string fields
3. **Helper methods** improve testability - keep logic separate from prompt
4. **Format methods** for complex data structures (_format_analysis, _format_gaps)
5. **Prompt structure** should guide LLM to produce well-structured output
6. **Use assertion pattern** instead of `type: ignore` after `complete_structured` call:
   ```python
   result = await self.llm_client.complete_structured(...)
   assert isinstance(result, EvaluatorOutput), f"Expected EvaluatorOutput, got {type(result)}"
   return result
   ```

### Existing EvaluationFeedback Model (already in models.py)

```python
class EvaluationFeedback(BaseModel):
    """Specific feedback from evaluation failure."""
    model_config = ConfigDict(strict=True)

    issue: str
    suggestion: str
    affected_claim: str | None = None
```

This model already exists and should be **reused** in EvaluatorOutput.feedback.

### Recommendation Logic

| Condition | Recommendation |
|-----------|---------------|
| All dimensions SUFFICIENT | "accept" |
| FAIL + attempt < max_retries + 1 | "retry_with_feedback" |
| FAIL + accuracy issues suggest missing data | "retry_with_more_context" |
| FAIL + attempt >= max_retries + 1 | "give_partial" |

### manual_test.py Update Required

Add `run_evaluator` function after `run_synthesizer`:
```python
async def run_evaluator(
    client: LLMClient,
    query: str,
    response: str,
    analyzer_output: AnalyzerOutput,
    entries_summary: str,
    evaluation_rules: list[str],
    attempt_number: int = 1,
    previous_feedback: list[EvaluationFeedback] | None = None,
) -> tuple[dict[str, Any], EvaluatorOutput]:
    """Run Evaluator agent and return results."""
    from quilto.agents import EvaluatorAgent, EvaluatorInput, EvaluatorOutput

    evaluator = EvaluatorAgent(client)

    evaluator_input = EvaluatorInput(
        query=query,
        response=response,
        analysis=analyzer_output,
        entries_summary=entries_summary,
        evaluation_rules=evaluation_rules,
        attempt_number=attempt_number,
        previous_feedback=previous_feedback or [],
    )

    print_section("Evaluator Input")
    print(f"Query: {query}")
    print(f"Response length: {len(response)} chars")
    print(f"Attempt: {attempt_number}")
    print(f"Evaluation rules: {len(evaluation_rules)} rules")

    print_section("Running Evaluator...")
    output = await evaluator.evaluate(evaluator_input)

    result: dict[str, Any] = {
        "overall_verdict": output.overall_verdict.value,
        "recommendation": output.recommendation,
        "dimensions": [
            {
                "dimension": d.dimension,
                "verdict": d.verdict.value,
                "reasoning": d.reasoning[:100] + "..." if len(d.reasoning) > 100 else d.reasoning,
            }
            for d in output.dimensions
        ],
    }

    if output.feedback:
        result["feedback"] = [
            {"issue": f.issue, "suggestion": f.suggestion}
            for f in output.feedback
        ]

    return result, output
```

### Default Evaluation Rules for Testing

Since Story 4-4 adds fitness-specific rules, use generic defaults for now:
```python
DEFAULT_EVALUATION_RULES = [
    "Do not make claims without supporting data",
    "Acknowledge uncertainty when evidence is limited",
    "Never provide medical, legal, or financial advice without disclaimers",
]
```

### Helper Methods Implementation

```python
def is_passed(self, output: EvaluatorOutput) -> bool:
    """Check if evaluation passed.

    Args:
        output: EvaluatorOutput from evaluation.

    Returns:
        True if overall_verdict is SUFFICIENT.
    """
    return output.overall_verdict == Verdict.SUFFICIENT


def get_failed_dimensions(self, output: EvaluatorOutput) -> list[EvaluationDimension]:
    """Get all dimensions that failed.

    Args:
        output: EvaluatorOutput from evaluation.

    Returns:
        List of EvaluationDimension with INSUFFICIENT verdict.
    """
    return [d for d in output.dimensions if d.verdict == Verdict.INSUFFICIENT]


def get_all_issues(self, output: EvaluatorOutput) -> list[str]:
    """Aggregate all issues from failed dimensions.

    Args:
        output: EvaluatorOutput from evaluation.

    Returns:
        Flat list of all issue strings from failed dimensions.
    """
    failed = self.get_failed_dimensions(output)
    issues: list[str] = []
    for dim in failed:
        issues.extend(dim.issues)
    return issues


def should_retry(
    self,
    output: EvaluatorOutput,
    attempt_number: int,
    max_retries: int = 2,
) -> bool:
    """Determine if evaluation should trigger a retry.

    Args:
        output: EvaluatorOutput from evaluation.
        attempt_number: Current attempt number (1-based).
        max_retries: Maximum number of retries allowed.

    Returns:
        True if evaluation failed AND attempt_number < max_retries.
    """
    return not self.is_passed(output) and attempt_number < max_retries
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.3]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 11.7 Evaluator Agent Interface]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 12.7 Evaluator Prompt]
- [Source: _bmad-output/planning-artifacts/state-machine-diagram.md#Transition Table]
- [Source: packages/quilto/quilto/agents/synthesizer.py] - Pattern reference
- [Source: packages/quilto/quilto/agents/analyzer.py] - Pattern reference
- [Source: packages/quilto/quilto/agents/models.py] - Existing models (EvaluationFeedback, Verdict)
- [Source: _bmad-output/project-context.md#Common Mistakes to Avoid]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **All 9 tasks completed successfully**
2. **Validation results:**
   - `make check`: PASSED (lint + typecheck)
   - `make validate`: PASSED (923 tests passed, 22 skipped)
   - `make test-ollama`: PASSED (941 tests passed, 4 skipped - 14 minutes with real Ollama)
3. **Total tests created:** ~75 unit tests in test_evaluator.py
4. **Integration tests:** 3 tests with real Ollama LLM
5. **Pyright compatibility note:** Used `# pyright: ignore[reportUnknownVariableType]` comments for `list[EvaluationFeedback]` with `Field(default_factory=list)` due to known pyright issue with Pydantic
6. **All acceptance criteria verified against implementation**

### File List

Files created/modified:
- `packages/quilto/quilto/agents/models.py` - Added EvaluationDimension, EvaluatorInput, EvaluatorOutput (3 new Pydantic models), added field_validator for PARTIAL verdict rejection (code review fix)
- `packages/quilto/quilto/agents/evaluator.py` - NEW FILE: EvaluatorAgent class with all methods
- `packages/quilto/quilto/agents/__init__.py` - Added 4 new exports (EvaluatorAgent, EvaluatorInput, EvaluatorOutput, EvaluationDimension)
- `packages/quilto/tests/test_evaluator.py` - NEW FILE: 75 comprehensive unit tests (76 after code review fix)
- `scripts/manual_test.py` - Added run_evaluator, run_retry_loop, get_evaluation_rules, build_entries_summary, integration in QUERY/BOTH flows

## Senior Developer Review (AI)

**Review Date:** 2026-01-14
**Reviewer:** Claude Opus 4.5 (Code Review Agent)

### Issues Found and Fixed

| Severity | Issue | Resolution |
|----------|-------|------------|
| MEDIUM | `EvaluationDimension.verdict` allowed PARTIAL but story spec says only SUFFICIENT/INSUFFICIENT | Added `field_validator` to reject PARTIAL verdict with descriptive error message |
| LOW | Missing test for PARTIAL verdict rejection | Added `test_evaluation_dimension_partial_verdict_fails` test |

### Issues Noted (Not Fixed - By Design)

| Severity | Issue | Reason |
|----------|-------|--------|
| MEDIUM | `run_retry_loop` doesn't use feedback to improve synthesizer | Intentionally deferred - feedback integration comes in later story |
| MEDIUM | `pyright: ignore` comments for `default_factory=list` | Necessary workaround for known pyright/Pydantic compatibility issue |

### Validation Results

- `make check`: ✅ PASSED
- `make test-ollama`: ✅ PASSED (941 tests, 4 skipped)
- All 9 ACs verified against implementation: ✅
- All tasks marked [x] verified: ✅

### Recommendation

**APPROVED** - Story meets all acceptance criteria. Code review fixes applied.
