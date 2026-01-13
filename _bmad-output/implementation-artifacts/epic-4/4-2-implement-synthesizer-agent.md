# Story 4.2: Implement Synthesizer Agent

Status: done

<!-- Validated: 2026-01-13 - All issues from validate-create-story have been addressed -->

## Story

As a **Quilto developer**,
I want a **Synthesizer agent that generates user-facing responses**,
so that **analysis results are communicated clearly**.

## Acceptance Criteria

1. **Given** query and analysis results
   **When** Synthesizer processes them
   **Then** it generates a natural language response

2. **Given** the Synthesizer agent
   **When** it generates a response
   **Then** response is grounded in evidence from analysis (cites dates/entries)

3. **Given** domain vocabulary
   **When** Synthesizer generates response
   **Then** domain expertise is reflected in tone and terminology

4. **Given** Synthesizer receives `is_partial=True`
   **When** retry limit was exceeded
   **Then** response clearly states what can be answered and lists unanswered gaps

5. **Given** the response_style parameter
   **When** set to "concise" or "detailed"
   **Then** the response length and depth matches the requested style

6. **Given** the Synthesizer output
   **When** returned
   **Then** it includes structured metadata: key_points, evidence_cited, confidence

7. **Given** the Synthesizer agent
   **When** instantiated and used
   **Then** it follows the same LLMClient pattern as Router, Parser, Planner, Retriever, and Analyzer

## Tasks / Subtasks

- [x] Task 1: Create Synthesizer Pydantic models (AC: #4, #5, #6)
  - [x] 1.1: Define `SynthesizerInput` model in `agents/models.py`
  - [x] 1.2: Define `SynthesizerOutput` model in `agents/models.py`

- [x] Task 2: Create SynthesizerAgent class (AC: #7)
  - [x] 2.1: Create `packages/quilto/quilto/agents/synthesizer.py`
  - [x] 2.2: Define `SynthesizerAgent` class with `AGENT_NAME = "synthesizer"`
  - [x] 2.3: Implement `__init__(self, llm_client: LLMClient)`
  - [x] 2.4: Add Google-style docstrings with examples

- [x] Task 3: Build Synthesizer prompt (AC: #1, #2, #3, #4, #5)
  - [x] 3.1: Implement `build_prompt(self, synthesizer_input: SynthesizerInput) -> str`
  - [x] 3.2: Implement `_format_analysis(analysis: AnalyzerOutput) -> str` helper
  - [x] 3.3: Implement `_format_vocabulary(vocabulary: dict[str, str]) -> str` helper
  - [x] 3.4: Implement `_format_gaps(gaps: list[Gap]) -> str` helper
  - [x] 3.5: Inject vocabulary for proper terminology
  - [x] 3.6: Format analysis findings for reference
  - [x] 3.7: Include response style guidance (concise vs detailed) with word count targets
  - [x] 3.8: Handle partial answer structure when `is_partial=True`

- [x] Task 4: Implement synthesize method (AC: #1, #6)
  - [x] 4.1: Implement `async def synthesize(self, synthesizer_input: SynthesizerInput) -> SynthesizerOutput`
  - [x] 4.2: Validate input is not empty
  - [x] 4.3: Call LLM with structured output to `SynthesizerOutput`
  - [x] 4.4: Return parsed result

- [x] Task 5: Export from agents __init__.py
  - [x] 5.1: Add SynthesizerAgent to imports
  - [x] 5.2: Add SynthesizerInput, SynthesizerOutput to imports
  - [x] 5.3: Update `__all__` list with all new exports (3 new items)

- [x] Task 6: Create comprehensive unit tests in `packages/quilto/tests/test_synthesizer.py` (~50-60 tests expected)
  - [x] 6.1: Test model validation for SynthesizerInput and SynthesizerOutput
    - [x] 6.1.1: Test Field(min_length=1) constraints for query and response
    - [x] 6.1.2: Test response_style Literal validation ("concise", "detailed")
    - [x] 6.1.3: Test confidence Literal validation ("high", "medium", "low")
    - [x] 6.1.4: Test is_partial default (False)
    - [x] 6.1.5: Test unanswered_gaps default (empty list)
    - [x] 6.1.6: Test gaps_disclosed default (empty list)
  - [x] 6.2: Test SynthesizerAgent instantiation
  - [x] 6.3: Test prompt building (normal, partial, concise vs detailed)
    - [x] 6.3.1: Test _format_analysis helper method
    - [x] 6.3.2: Test _format_vocabulary helper method
    - [x] 6.3.3: Test _format_gaps helper method (with empty and non-empty gaps)
    - [x] 6.3.4: Test build_prompt with concise style
    - [x] 6.3.5: Test build_prompt with detailed style
    - [x] 6.3.6: Test build_prompt with is_partial=True
  - [x] 6.4: Test synthesize method with mock LLM
  - [x] 6.5: Test all exports importable from quilto.agents

- [x] Task 7: Update manual_test.py
  - [x] 7.1: Add imports for SynthesizerAgent, SynthesizerInput, SynthesizerOutput
  - [x] 7.2: Add `run_synthesizer` function after `run_analyzer`
  - [x] 7.3: Integrate in QUERY flow: call Synthesizer after successful Analyzer run (~line 490)
  - [x] 7.4: Integrate in BOTH flow: call Synthesizer after successful Analyzer run (~line 538)

- [x] Task 8: Run validation
  - [x] 8.1: Run `make check` (lint + typecheck)
  - [x] 8.2: Run `make validate` (full validation)
  - [x] 8.3: Run `make test-ollama` (integration tests)

## Dev Notes

### Architecture Patterns

- **Location:** `packages/quilto/quilto/agents/synthesizer.py` (Quilto framework, NOT Swealog)
- **Pattern:** Follow existing agent patterns from `analyzer.py`
- **Model Requirement:** MEDIUM-HIGH tier - natural language generation

### SynthesizerInput Model (from agent-system-design.md Section 11.6)

**CRITICAL:** Use `model_config = ConfigDict(strict=True)` per project-context.md

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from quilto.agents.models import Gap, QueryType, AnalyzerOutput  # Reuse existing models

class SynthesizerInput(BaseModel):
    """Input to Synthesizer agent."""
    model_config = ConfigDict(strict=True)

    query: str = Field(min_length=1)  # Required, non-empty
    query_type: QueryType

    # From Analyzer
    analysis: AnalyzerOutput

    # Domain context (for terminology)
    vocabulary: dict[str, str]

    # For partial answers (after retry limit)
    is_partial: bool = False
    unanswered_gaps: list[Gap] = []  # Reuse Gap model from agents.models

    # User preferences
    response_style: Literal["concise", "detailed"] = "concise"
```

### SynthesizerOutput Model (from agent-system-design.md Section 11.6)

**CRITICAL:** Use `model_config = ConfigDict(strict=True)` per project-context.md

```python
class SynthesizerOutput(BaseModel):
    """Output from Synthesizer agent."""
    model_config = ConfigDict(strict=True)

    response: str = Field(min_length=1)  # The user-facing answer, REQUIRED non-empty

    # Structured metadata
    key_points: list[str]  # Main takeaways (2-5 points typically)
    evidence_cited: list[str]  # Dates/entries referenced (e.g., "2026-01-10 bench entry")

    # For partial answers
    gaps_disclosed: list[str] = []  # Empty if not partial

    # Confidence signal
    confidence: Literal["high", "medium", "low"]
```

### Confidence Level Mapping

Map from Analyzer verdict to Synthesizer confidence:

| Analyzer Verdict | Synthesizer Confidence | Rationale |
|------------------|------------------------|-----------|
| SUFFICIENT | high | All claims backed by evidence |
| PARTIAL | medium | Some gaps but answer is meaningful |
| INSUFFICIENT | low | Providing partial answer anyway (retry limit) |

### Response Style Guidelines

**Concise (default):**
- 2-4 sentences for simple queries (~50-100 words)
- Bullet points for multiple findings
- Direct answer without elaboration
- Focus on key insight, skip background

**Detailed:**
- Full context and explanation (~200-400 words)
- All supporting evidence listed with dates
- Nuanced interpretation of patterns
- Include relevant trends and comparisons

### Partial Answer Handling

When `is_partial=True`, response should be structured as:
```
"Here's what I can tell you: [answer based on available data]

To provide a more complete answer, I would need: [list gaps]"
```

### LLM Prompt Template (from agent-system-design.md Section 12.6)

```
ROLE: You are a response generation agent that creates user-facing answers.

TASK: Generate a clear, helpful response based on the analysis.

=== VOCABULARY ===
Use proper terminology from the domain:
{vocabulary}

=== INPUT ===

Query: {query}
Analysis findings: {analysis.findings}
Patterns identified: {analysis.patterns_identified}
Response style: {response_style}  # "concise" or "detailed"

Is partial answer: {is_partial}
Unanswered gaps (if partial): {unanswered_gaps}

=== RESPONSE GUIDELINES ===

1. Address what the user asked directly
2. Support claims with evidence (cite dates/entries)
3. Use domain-appropriate terminology
4. Match requested response style (concise vs detailed)
5. If partial: clearly state what you can answer and what remains unknown

=== IF PARTIAL ANSWER ===

Structure as:
"Here's what I can tell you: [answer based on available data]

To provide a more complete answer, I would need: [list gaps]"

=== OUTPUT (JSON) ===
{SynthesizerOutput.model_json_schema()}
```

### Example Output (for reference)

```json
{
  "response": "Your bench press has shown consistent improvement over the past month. Starting at 175 lbs on Jan 3rd, you've progressed to 185 lbs by Jan 10th, representing a 5.7% increase in working weight.",
  "key_points": [
    "10 lb increase in bench press (175 → 185 lbs)",
    "Progression occurred over 7 days",
    "Consistent rep range maintained (5 reps)"
  ],
  "evidence_cited": [
    "2026-01-03: bench 175x5",
    "2026-01-10: bench 185x5"
  ],
  "gaps_disclosed": [],
  "confidence": "high"
}
```

### Integration with Query Flow

The Synthesizer is called after Analyzer in the query flow:
```
Planner -> Retriever -> Analyzer -> Synthesizer -> Evaluator
```

State machine transition: `ANALYZE -> SYNTHESIZE` (from state-machine-diagram.md)

### Confidence Levels

- **high**: Analysis verdict is SUFFICIENT, all claims backed by evidence
- **medium**: Analysis verdict is PARTIAL, some gaps but answer is meaningful
- **low**: Analysis verdict is INSUFFICIENT but providing partial answer anyway (retry limit reached)

### Project Structure Notes

- File: `packages/quilto/quilto/agents/synthesizer.py`
- Tests: `packages/quilto/tests/test_synthesizer.py`
- This is **Quilto framework** code (domain-agnostic)
- Uses same patterns as Router, Parser, Planner, Retriever, Analyzer

### Testing Standards (from project-context.md)

- **Boundary tests:** Test Field min_length=1 constraints
- **Empty vs None:** Test both `None` and `""` for optional string fields
- **ConfigDict:** Use `model_config = ConfigDict(strict=True)` for all models
- **All exports:** Verify importable from `quilto.agents`
- **Mock LLM:** Use mock_llm fixture for unit tests
- **Integration:** Run `make test-ollama` to verify with real LLM

### Previous Story Learnings (Story 4-1: Analyzer)

From Story 4-1 implementation:
1. **Use ConfigDict(strict=True)** for all Pydantic models
2. **Field(min_length=1)** for required string fields
3. **Helper methods** improve testability - keep logic separate from prompt
4. **Format methods** for complex data structures (_format_findings, _format_gaps)
5. **Prompt structure** should guide LLM to produce well-structured output

**Apply to Synthesizer:**
- Create `_format_analysis(analysis: AnalyzerOutput) -> str` to format findings and patterns
- Create `_format_vocabulary(vocabulary: dict[str, str]) -> str` for term reference
- Create `_format_gaps(gaps: list[Gap]) -> str` for partial answer gap listing
- Use assertion pattern instead of `type: ignore` after `complete_structured` call:
  ```python
  result = await self.llm_client.complete_structured(...)
  assert isinstance(result, SynthesizerOutput), f"Expected SynthesizerOutput, got {type(result)}"
  return result
  ```

### manual_test.py Update Required

Add `run_synthesizer` function after `run_analyzer`:
```python
async def run_synthesizer(
    client: LLMClient,
    query: str,
    analyzer_output: AnalyzerOutput,
    planner_output: PlannerOutput,
    vocabulary: dict[str, str],
    response_style: Literal["concise", "detailed"] = "concise",
) -> tuple[dict[str, Any], SynthesizerOutput]:
    """Run Synthesizer agent and return results."""
    from quilto.agents import SynthesizerAgent, SynthesizerInput, SynthesizerOutput

    synthesizer = SynthesizerAgent(client)

    synthesizer_input = SynthesizerInput(
        query=query,
        query_type=planner_output.query_type,
        analysis=analyzer_output,
        vocabulary=vocabulary,
        is_partial=False,  # Set to True when retry limit exceeded
        response_style=response_style,
    )

    print_section("Synthesizer Input")
    print(f"Query: {query}")
    print(f"Query type: {planner_output.query_type.value}")
    print(f"Response style: {response_style}")
    print(f"Analyzer verdict: {analyzer_output.verdict.value}")

    print_section("Running Synthesizer...")
    output = await synthesizer.synthesize(synthesizer_input)

    result: dict[str, Any] = {
        "response": output.response,
        "key_points": output.key_points,
        "evidence_cited": output.evidence_cited,
        "confidence": output.confidence,
    }

    if output.gaps_disclosed:
        result["gaps_disclosed"] = output.gaps_disclosed

    return result, output
```

**Integration in process_input (QUERY flow):**

After `run_analyzer` succeeds in QUERY flow (~line 490):
```python
# Run Analyzer if retriever succeeded
if retriever_output is not None:
    try:
        domain_context = build_active_domain_context(selected_domains)
        analyzer_result, analyzer_output = await run_analyzer(...)
        print_section("Analyzer Output")
        print_json(analyzer_result)

        # NEW: Run Synthesizer after Analyzer
        try:
            vocabulary = get_merged_vocabulary(selected_domains)
            synthesizer_result, _ = await run_synthesizer(
                client, raw_input, analyzer_output, planner_output, vocabulary
            )
            print_section("Synthesizer Output")
            print_json(synthesizer_result)
        except Exception as e:
            print(f"\nSynthesizer ERROR: {e}")
    except Exception as e:
        print(f"\nAnalyzer ERROR: {e}")
```

Same pattern applies to BOTH flow (~line 538).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 11.6 Synthesizer Agent Interface]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 12.6 Synthesizer Prompt]
- [Source: packages/quilto/quilto/agents/analyzer.py] - Pattern reference
- [Source: packages/quilto/quilto/agents/models.py] - Existing models to reuse
- [Source: _bmad-output/project-context.md#Common Mistakes to Avoid]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. All tasks and subtasks completed successfully
2. 59 unit tests created covering model validation, prompt building, synthesize method, and exports
3. Integration tests pass with real Ollama (864 passed, 4 skipped)
4. `make check`, `make validate`, and `make test-ollama` all pass
5. SynthesizerAgent follows the same LLMClient pattern as Router, Parser, Planner, Retriever, and Analyzer
6. Confidence mapping: SUFFICIENT->high, PARTIAL->medium, INSUFFICIENT->low
7. Response styles implemented: concise (50-100 words), detailed (200-400 words)
8. Partial answer handling implemented with `is_partial=True` and `unanswered_gaps` support

### File List

| File | Action | Description |
|------|--------|-------------|
| packages/quilto/quilto/agents/models.py | Modified | Add SynthesizerInput, SynthesizerOutput models |
| packages/quilto/quilto/agents/synthesizer.py | Created | SynthesizerAgent with build_prompt, synthesize, helper methods |
| packages/quilto/quilto/agents/__init__.py | Modified | Export SynthesizerAgent, SynthesizerInput, SynthesizerOutput |
| packages/quilto/tests/test_synthesizer.py | Created | Comprehensive unit tests (59 tests) |
| scripts/manual_test.py | Modified | Add run_synthesizer, integrate in QUERY and BOTH flows |
| _bmad-output/implementation-artifacts/sprint-status.yaml | Modified | Update story status |
