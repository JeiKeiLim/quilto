# Story 4.1: Implement Analyzer Agent

Status: done

<!-- Validated: 2026-01-13 - All issues from validate-create-story have been addressed -->

## Story

As a **Quilto developer**,
I want an **Analyzer agent that finds patterns and assesses sufficiency**,
so that **queries are answered only when evidence is sufficient**.

## Acceptance Criteria

1. **Given** retrieved entries and domain context
   **When** Analyzer processes them
   **Then** it produces `analysis` with findings and evidence

2. **Given** the Analyzer agent
   **When** it evaluates retrieved entries
   **Then** `sufficiency_evaluation` identifies gaps with severity (critical/nice_to_have)

3. **Given** the Analyzer agent output
   **When** the verdict is generated
   **Then** `verdict` is generated LAST (after all reasoning) to prevent premature commitment bias

4. **Given** entries that support a query
   **When** Analyzer finds patterns
   **Then** each finding includes claim, evidence references (dates/entries), and confidence level

5. **Given** entries that don't fully support a query
   **When** Analyzer identifies gaps
   **Then** gaps are classified as retrievable or non-retrievable with gap_type

6. **Given** entries requiring domain expertise outside current domains
   **When** Analyzer encounters them
   **Then** it sets `outside_current_expertise=True` with `suspected_domain` for expansion

7. **Given** the Analyzer agent
   **When** instantiated and used
   **Then** it follows the same LLMClient pattern as Router, Parser, Planner, and Retriever

## Tasks / Subtasks

- [x] Task 1: Create Analyzer Pydantic models (AC: #1, #2, #3, #4, #5, #6)
  - [x] 1.1: Define `Verdict` enum with values: `SUFFICIENT`, `INSUFFICIENT`, `PARTIAL`
  - [x] 1.2: Define `Finding` model
  - [x] 1.3: Define `SufficiencyEvaluation` model (per architecture Section 7.2)
  - [x] 1.4: Define `AnalyzerInput` model
  - [x] 1.5: Define `AnalyzerOutput` model

- [x] Task 2: Create AnalyzerAgent class (AC: #7)
  - [x] 2.1: Create `packages/quilto/quilto/agents/analyzer.py`
  - [x] 2.2: Define `AnalyzerAgent` class with `AGENT_NAME = "analyzer"`
  - [x] 2.3: Implement `__init__(self, llm_client: LLMClient)`
  - [x] 2.4: Add Google-style docstrings with examples

- [x] Task 3: Build Analyzer prompt with verdict-last instruction (AC: #1, #2, #3)
  - [x] 3.1: Implement `build_prompt(self, analyzer_input: AnalyzerInput) -> str`
  - [x] 3.2: Include critical instruction: "Generate verdict LAST after completing ALL analysis fields"
  - [x] 3.3: Include sufficiency criteria (evidence check, gap assessment, speculation test)
  - [x] 3.4: Inject domain expertise from `domain_context.expertise`
  - [x] 3.5: Inject available domains from `domain_context.available_domains`
  - [x] 3.6: Format entries for analysis (dates, raw content, domain_data)
  - [x] 3.7: Format retrieval summary using `_format_retrieval_summary`
  - [x] 3.8: Format global context summary using `_format_global_context`

- [x] Task 4: Implement analyze method (AC: #1, #4)
  - [x] 4.1: Implement `async def analyze(self, analyzer_input: AnalyzerInput) -> AnalyzerOutput`
  - [x] 4.2: Validate input is not empty
  - [x] 4.3: Call LLM with structured output to `AnalyzerOutput`
  - [x] 4.4: Return parsed result

- [x] Task 5: Implement sufficiency evaluation logic (AC: #2, #5, #6)
  - [x] 5.1: Prompt instructs LLM to identify gaps in evidence
  - [x] 5.2: Gap classification: TEMPORAL, TOPICAL, CONTEXTUAL, SUBJECTIVE, CLARIFICATION
  - [x] 5.3: Gap severity: `critical` vs `nice_to_have`
  - [x] 5.4: Domain gap detection: `outside_current_expertise=True` when needed

- [x] Task 6: Add helper methods
  - [x] 6.1: `_format_entries(self, entries: list[Any]) -> str`
  - [x] 6.2: `_format_retrieval_summary(self, summary: list[RetrievalAttempt]) -> str`
  - [x] 6.3: `_format_global_context(self, context: str | None) -> str`
  - [x] 6.4: `has_critical_gaps(self, evaluation: SufficiencyEvaluation) -> bool`
  - [x] 6.5: `needs_domain_expansion(self, evaluation: SufficiencyEvaluation) -> bool`
  - [x] 6.6: `get_all_gaps(self, evaluation: SufficiencyEvaluation) -> list[Gap]`

- [x] Task 7: Export from agents __init__.py
  - [x] 7.1: Add AnalyzerAgent to imports
  - [x] 7.2: Add AnalyzerInput, AnalyzerOutput, Finding, Verdict, SufficiencyEvaluation to imports
  - [x] 7.3: Update `__all__` list with all new exports (7 new items)

- [x] Task 8: Create comprehensive unit tests in `packages/quilto/tests/test_analyzer.py`
  - [x] 8.1: Test model validation for all new types
  - [x] 8.2: Test AnalyzerAgent instantiation
  - [x] 8.3: Test prompt building
  - [x] 8.4: Test public helper methods (private helpers tested via build_prompt)
  - [x] 8.5: Test analyze method with mock LLM
  - [x] 8.6: Test all exports importable from quilto.agents

- [x] Task 9: Check if manual_test.py update needed
  - [x] 9.1: Review `scripts/manual_test.py` for Analyzer support
  - [x] 9.2: Added AnalyzerAgent to manual testing (runs after Retriever for QUERY inputs)

- [x] Task 10: Run validation
  - [x] 10.1: Run `make check` (lint + typecheck) - PASSED
  - [x] 10.2: Run `make validate` (full validation) - PASSED (790 passed, 16 skipped)
  - [x] 10.3: Run `make test-ollama` (integration tests) - PASSED (802 passed, 4 skipped)

## Dev Notes

### Architecture Patterns

- **Location:** `packages/quilto/quilto/agents/analyzer.py` (Quilto framework, NOT Swealog)
- **Pattern:** Follow existing agent patterns from `planner.py` and `retriever.py`
- **Model Requirement:** HIGH tier - requires reasoning and pattern recognition
- **Circular Import:** Use `list[Any]` for entries to avoid circular import with storage.repository

### Critical Design: Verdict-Last Pattern

The Analyzer MUST generate the verdict LAST to prevent premature commitment bias. The **prompt** must explicitly instruct this order (Pydantic field order does NOT affect LLM output order):

```
CRITICAL: Complete ALL analysis in this order:
1. query_intent - What is the user really asking?
2. findings - What patterns and insights are in the data?
3. patterns_identified - High-level patterns observed
4. sufficiency_evaluation - Assess gaps and evidence quality
5. verdict_reasoning - Explain your assessment
6. verdict - ONLY AFTER completing all above

Do NOT decide the verdict before completing steps 1-5.
```

This prevents the LLM from:
1. Deciding "SUFFICIENT" early and then justifying it
2. Missing gaps because it already committed to a verdict
3. Anchoring on initial impressions

### Sufficiency Criteria (from architecture Section 7.2)

The prompt must include these three criteria for the LLM to evaluate:

| Criterion | Question |
|-----------|----------|
| Evidence check | For every claim, do I have supporting data? |
| Gap assessment | What's missing? Is it CRITICAL or NICE-TO-HAVE? |
| Speculation test | Am I connecting dots that exist, or inventing? |

### Sufficiency Standard

The Analyzer evaluates: **"Can I respond to this query without unacceptable speculation?"**

- **SUFFICIENT** = No critical gaps, all claims have evidence, speculation risk is none/low
- **PARTIAL** = Only nice_to_have gaps, can answer with noted limitations
- **INSUFFICIENT** = Critical gaps exist, speculation risk is high, cannot answer meaningfully

### SufficiencyEvaluation Model

The `SufficiencyEvaluation` model provides structured gap analysis:
- `critical_gaps: list[Gap]` - Gaps with severity="critical" that block answering
- `nice_to_have_gaps: list[Gap]` - Gaps with severity="nice_to_have" that would improve answer
- `evidence_check_passed: bool` - True if all findings have supporting evidence
- `speculation_risk: Literal["none", "low", "high"]` - Level of claims beyond available data

### Gap Classification Reference

Reuse existing `Gap` model from `agents.models`:
- `gap_type`: TEMPORAL, TOPICAL, CONTEXTUAL, SUBJECTIVE, CLARIFICATION
- `severity`: "critical" | "nice_to_have"
- `outside_current_expertise`: bool
- `suspected_domain`: str | None

### Finding Confidence Levels

- **high**: Multiple entries support the claim, clear pattern
- **medium**: Some evidence but not overwhelming
- **low**: Single entry or weak pattern, needs more data

### Project Structure Notes

- File: `packages/quilto/quilto/agents/analyzer.py`
- Tests: `packages/quilto/tests/test_analyzer.py` (follows existing pattern: test_router.py, test_planner.py, etc.)
- This is **Quilto framework** code (domain-agnostic)
- Uses same patterns as Router, Parser, Planner, Retriever

### Testing Standards (from project-context.md)

- **Boundary tests:** Test enum values, min_length=1 constraints
- **Empty vs None:** Test both `None` and `""` for optional string fields
- **ConfigDict:** Use `model_config = ConfigDict(strict=True)` for all models
- **All exports:** Verify importable from `quilto.agents`
- **Mock LLM:** Use mock_llm fixture for unit tests
- **Integration:** Run `make test-ollama` to verify with real LLM

### Previous Story Learnings (Epic 3)

From Epic 3 Retrospective:
1. **Clean agent separation pays off** - Single responsibility per agent
2. **Helper methods improve testability** - Keep logic separate from prompt
3. **manual_test.py must stay current** - Check if update needed

From Story 3-4:
1. **Boundary value tests are critical** - Test exact boundaries (ge=0, le=10)
2. **Literal types need validation tests** - Test valid and invalid values

### LLM Prompt Template

The prompt should follow this structure from agent-system-design.md (Section 7.2 and 12.5):

```
ROLE: You are an analytical agent that finds patterns and assesses information sufficiency.

TASK: Analyze retrieved entries to answer the query. Determine if you have enough information.

=== CRITICAL INSTRUCTIONS ===

1. Complete ALL analysis fields in this EXACT order:
   - query_intent (what is the user really asking)
   - findings (patterns and insights with evidence citations)
   - patterns_identified (high-level patterns)
   - sufficiency_evaluation (gaps and evidence quality)
   - verdict_reasoning (explain your assessment)
   - verdict (LAST - only after completing all above)

2. For each finding, cite specific evidence (dates, entry content)
3. Identify gaps that prevent full answer, classify as CRITICAL or NICE_TO_HAVE
4. Set outside_current_expertise=True when domain knowledge is missing

=== SUFFICIENCY CRITERIA ===

Apply these three tests:
1. Evidence check: For every claim, do I have supporting data?
2. Gap assessment: What's missing? Is it CRITICAL or NICE-TO-HAVE?
3. Speculation test: Am I connecting dots that exist, or inventing?

=== SUFFICIENCY VERDICTS ===

SUFFICIENT: No critical gaps, evidence_check_passed=true, speculation_risk=none/low
PARTIAL: Only nice_to_have gaps, can answer with noted limitations
INSUFFICIENT: Critical gaps exist OR speculation_risk=high

=== DOMAIN EXPERTISE ===

{domain_context.expertise}

=== AVAILABLE DOMAINS FOR EXPANSION ===

{domain_context.available_domains}

=== RETRIEVED ENTRIES ===

{formatted_entries}

=== RETRIEVAL SUMMARY ===

{formatted_retrieval_summary}

=== GLOBAL CONTEXT ===

{formatted_global_context}

=== INPUT ===

Query: {query}
Query type: {query_type}
Sub-query ID: {sub_query_id or "N/A"}

=== OUTPUT (JSON) ===

{AnalyzerOutput.model_json_schema()}
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 11.5 Analyzer Agent Interface]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 7.2 Question 2: How does Analyzer know "enough"?]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 12.5 Analyzer Prompt]
- [Source: packages/quilto/quilto/agents/planner.py] - Pattern reference
- [Source: packages/quilto/quilto/agents/models.py] - Existing models to reuse (Gap, GapType, etc.)
- [Source: _bmad-output/project-context.md#Common Mistakes to Avoid]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Implementation proceeded without issues.

### Completion Notes List

1. All Analyzer models created in `packages/quilto/quilto/agents/models.py`:
   - Verdict enum (SUFFICIENT, INSUFFICIENT, PARTIAL)
   - Finding model (claim, evidence, confidence)
   - SufficiencyEvaluation model (critical_gaps, nice_to_have_gaps, evidence_check_passed, speculation_risk)
   - AnalyzerInput/AnalyzerOutput models

2. AnalyzerAgent follows established patterns from Router, Parser, Planner, Retriever

3. Prompt implements verdict-last pattern as specified in architecture doc:
   - Forces LLM to complete all analysis before deciding verdict
   - Includes three sufficiency criteria (evidence check, gap assessment, speculation test)

4. Helper methods provide programmatic access to evaluation results:
   - has_critical_gaps(): Check for blocking gaps
   - needs_domain_expansion(): Check for outside_current_expertise gaps
   - get_all_gaps(): Combine gap lists

5. Updated manual_test.py to run Analyzer after Retriever for QUERY inputs

6. 60 unit tests + 2 integration tests (62 total) created for Analyzer

### File List

| File | Action | Description |
|------|--------|-------------|
| packages/quilto/quilto/agents/models.py | Modified | Added Verdict, Finding, SufficiencyEvaluation, AnalyzerInput, AnalyzerOutput |
| packages/quilto/quilto/agents/analyzer.py | Created | AnalyzerAgent with build_prompt, analyze, helper methods |
| packages/quilto/quilto/agents/__init__.py | Modified | Export new types (7 new exports) |
| packages/quilto/tests/test_analyzer.py | Created | 62+ tests (60 unit + 2 integration) |
| scripts/manual_test.py | Modified | Added run_analyzer for QUERY flow |

## Senior Developer Review (AI)

**Reviewer:** Amelia (Dev Agent) | **Date:** 2026-01-13

### Issues Found: 2 High, 4 Medium, 2 Low

#### Fixed Issues

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| HIGH-1 | `_format_entries` missing None handling for object attributes | Added explicit None check for date and raw_content |
| HIGH-2 | Story claimed 64 tests but only 62 exist | Corrected count to "62 tests" |
| MEDIUM-1 | `type: ignore[return-value]` code smell in analyzer.py:329 | Replaced with proper assertion |
| MEDIUM-3 | Missing edge case tests for `_format_entries` | Added 3 tests for None attribute values |

#### Accepted Issues (Low Priority)

| Severity | Issue | Reason |
|----------|-------|--------|
| MEDIUM-2 | sprint-status.yaml not in File List | Will be updated in next step |
| MEDIUM-4 | No runtime validation for entries type | Documented limitation acceptable |
| LOW-1 | Docstring import inconsistency | Minor style issue |
| LOW-2 | Helper functions vs fixtures | Existing pattern acceptable |

### Verification

- `make check` passes (lint + typecheck)
- All 65 tests pass (63 unit + 2 integration skipped)
- All acceptance criteria verified

