# Story 12.4: Enhance Synthesizer for Detailed Responses

Status: done

## Story

As a **Quilto user**,
I want **responses to include reasoning, specific metrics, and log references**,
So that **I understand why recommendations are made based on my data**.

## Background

**Origin:** Dogfooding Iteration 1 Analysis (2026-01-24)
**Source:** `tests/eval/feedback/archive/iter-001/analysis.md` - Pattern 5: Response Lacks Detail
**Priority:** Medium | **Effort:** Small (1-2 hours)

**Problem Identified:**

Users consistently expect more detailed responses including:
- Reasoning (WHY this recommendation)
- Specific metrics (weights, distances, times from logs)
- Personalized analysis (not generic advice)

**User Feedback Quotes:**
- `fec3d15f`: "it would be better to give why it recommended this"
- `8e8e6d87`: "I was expecting more of analytic response"
- `14b9034b`: "Wish it told me about how much weight I could lift"
- `3ec25871`: "response could have been a bit more detail"

**Root Cause:** Synthesizer prompt prioritizes brevity over comprehensiveness. The current prompt focuses on concise responses but doesn't instruct the LLM to include reasoning or cite specific metrics from the analyzer's findings.

## Acceptance Criteria

1. **Given** a recommendation or insight response
   **When** Synthesizer generates output
   **Then** response includes WHY (reasoning based on log patterns)

2. **Given** analyzer findings with numeric data (weights, distances, times)
   **When** Synthesizer generates output
   **Then** specific metrics are cited with dates (e.g., "Your 5K on Jan 15 at 28:30...")

3. **Given** a query about user's fitness
   **When** Synthesizer generates output
   **Then** response references log evidence (not just generic advice)

4. **Given** multiple log entries in analyzer findings
   **When** Synthesizer generates output
   **Then** trends or patterns are mentioned (e.g., "Improved by 10% over 3 weeks")

5. **Given** `response_style="concise"`
   **When** Synthesizer generates output
   **Then** reasoning is still included but in abbreviated form (2-3 sentences)

6. **Given** `response_style="detailed"`
   **When** Synthesizer generates output
   **Then** full reasoning, all metrics, and comprehensive analysis is included

7. **Given** backward compatibility requirement
   **When** existing code calls Synthesizer
   **Then** no API changes required (prompt enhancement only)

## Tasks / Subtasks

- [x] Task 1: Review current Synthesizer prompt structure (AC: #1, #2, #3, #4)
  - [x] 1.1: Read `build_prompt()` in `packages/quilto/quilto/agents/synthesizer.py:147-237`
  - [x] 1.2: Verify `_format_analysis()` already formats findings with evidence (it does - lines 57-90)
  - [x] 1.3: Note insertion points: REASONING section after line 215, update style guidance lines 162-173

- [x] Task 2: Add REASONING REQUIREMENTS section to prompt (AC: #1)
  - [x] 2.1: Insert new section between RESPONSE STYLE GUIDANCE (line 215) and RESPONSE GUIDELINES (line 217)
  - [x] 2.2: Include good/bad example showing generic vs reasoned response
  - [x] 2.3: Exact text to add - see Dev Notes section below

- [x] Task 3: Add METRIC CITATION section to prompt (AC: #2, #3, #4)
  - [x] 3.1: Insert after REASONING REQUIREMENTS section
  - [x] 3.2: Include concrete examples with dates and percentages
  - [x] 3.3: Exact text to add - see Dev Notes section below

- [x] Task 4: Update style guidance for both concise and detailed (AC: #5, #6)
  - [x] 4.1: Lines 163-167: Change concise from "50-100 words" to "75-150 words", add reasoning requirement
  - [x] 4.2: Lines 169-173: Update detailed to emphasize full reasoning chain and trend analysis
  - [x] 4.3: Exact replacement text - see Dev Notes section below

- [x] Task 5: Add unit tests to `TestSynthesizerPromptBuilding` class (AC: #1, #2, #5, #6)
  - [x] 5.1: Add `test_prompt_includes_reasoning_requirements()` - assert "REASONING REQUIREMENTS" in prompt
  - [x] 5.2: Add `test_prompt_includes_metric_citation()` - assert "METRIC CITATION" in prompt
  - [x] 5.3: Add `test_concise_style_updated_word_count()` - assert "75-150 words" in prompt (NOT "50-100")
  - [x] 5.4: Add `test_detailed_style_includes_trend_analysis()` - assert "trend analysis" in prompt.lower()

- [x] Task 6: Run validation
  - [x] 6.1: Run `make check` (lint + typecheck)
  - [x] 6.2: Run `make validate` (full validation including unit tests)
  - [x] 6.3: Run `make test-ollama` (integration tests - verify existing tests still pass)

## Dev Notes

### Scope: Prompt-Only Changes

**Files to modify:**
- `packages/quilto/quilto/agents/synthesizer.py` - ONLY `build_prompt()` method (lines 147-237)
- `packages/quilto/tests/test_synthesizer.py` - Add 4 tests to existing `TestSynthesizerPromptBuilding` class

**NO changes needed to:**
- Model classes (SynthesizerInput, SynthesizerOutput)
- Exports (__init__.py)
- `_format_analysis()` (already includes evidence)
- `synthesize()` method

### Current Prompt Structure (synthesizer.py:147-237)

```python
# Line 162-167: CONCISE STYLE guidance (MODIFY)
# Line 169-173: DETAILED STYLE guidance (MODIFY)
# Line 214-215: RESPONSE STYLE GUIDANCE section
# Line 217-224: RESPONSE GUIDELINES section
# INSERT new sections between line 215 and 217
```

### Exact Code Changes

**1. Replace lines 163-167 (CONCISE STYLE):**
```python
    style_guidance = """CONCISE STYLE (target: 75-150 words):
- Direct answer with brief reasoning (2-3 sentences on WHY)
- Cite 1-2 key metrics with dates
- Quantify trends briefly
- Skip elaborate background but keep essential evidence"""
```

**2. Replace lines 169-173 (DETAILED STYLE):**
```python
    style_guidance = """DETAILED STYLE (target: 200-400 words):
- Full reasoning chain from evidence to conclusion
- All relevant metrics with dates
- Comprehensive trend analysis with percentages
- Nuanced interpretation connecting multiple log entries
- Personalized recommendations grounded in user's specific data"""
```

**3. Insert AFTER line 215 (`{style_guidance}`) and BEFORE line 217 (`=== RESPONSE GUIDELINES ===`):**
```python
=== REASONING REQUIREMENTS ===

CRITICAL: Responses MUST include reasoning, not just conclusions.

BAD: "You should focus on progressive overload."
GOOD: "Based on your Jan 3-10 bench logs (175→185 lbs), you're ready for progressive overload."

For every recommendation:
1. State WHAT you're recommending
2. Explain WHY based on specific log evidence
3. CITE metrics that support your reasoning (dates + values)

=== METRIC CITATION ===

When findings contain numeric data:
- ALWAYS cite specific values with dates
- ALWAYS quantify trends (percentages, differences)
- NEVER give generic advice when personalized data exists

Examples: "5K improved 28:30→26:45 (6%)", "Bench 175→185 lbs in 7 days"
```

### Unit Test Assertions (Add to TestSynthesizerPromptBuilding)

```python
def test_prompt_includes_reasoning_requirements(self) -> None:
    """Prompt includes REASONING REQUIREMENTS section."""
    # ... setup code same as existing tests ...
    prompt = synthesizer.build_prompt(synthesizer_input)
    assert "REASONING REQUIREMENTS" in prompt
    assert "CRITICAL: Responses MUST include reasoning" in prompt

def test_prompt_includes_metric_citation(self) -> None:
    """Prompt includes METRIC CITATION section."""
    # ... setup code ...
    prompt = synthesizer.build_prompt(synthesizer_input)
    assert "METRIC CITATION" in prompt
    assert "cite specific values with dates" in prompt

def test_concise_style_updated_word_count(self) -> None:
    """Concise style has updated word count (75-150, not 50-100)."""
    # ... setup code with response_style="concise" ...
    prompt = synthesizer.build_prompt(synthesizer_input)
    assert "75-150 words" in prompt
    assert "50-100 words" not in prompt  # Verify old target removed

def test_detailed_style_includes_trend_analysis(self) -> None:
    """Detailed style emphasizes trend analysis."""
    # ... setup code with response_style="detailed" ...
    prompt = synthesizer.build_prompt(synthesizer_input)
    assert "trend analysis" in prompt.lower()
    assert "full reasoning chain" in prompt.lower()
```

### Key Files

| File | Purpose | Lines to Modify |
|------|---------|-----------------|
| `packages/quilto/quilto/agents/synthesizer.py` | Update style guidance (163-173), insert REASONING + METRIC sections (after 215) | `build_prompt()` only |
| `packages/quilto/tests/test_synthesizer.py` | Add 4 tests to `TestSynthesizerPromptBuilding` class (lines 824-889) | Follow existing test pattern |

### Testing Strategy

**Unit Tests (4 new methods in `TestSynthesizerPromptBuilding` class):**

| Test Name | Assert Contains | Assert NOT Contains |
|-----------|-----------------|---------------------|
| `test_prompt_includes_reasoning_requirements` | "REASONING REQUIREMENTS" | - |
| `test_prompt_includes_metric_citation` | "METRIC CITATION" | - |
| `test_concise_style_updated_word_count` | "75-150 words" | "50-100 words" |
| `test_detailed_style_includes_trend_analysis` | "trend analysis" | - |

**Integration Tests:**
- Run `make test-ollama` - existing `TestSynthesizerIntegration` tests validate LLM still produces valid output
- No NEW integration tests needed (prompt changes don't require new integration testing)

### Previous Story Learnings (from 12.3)

1. **Prompt-only changes are low risk**: No API changes means guaranteed backward compatibility (AC #7)
2. **Word count targets are guidelines**: LLM may not hit exact targets - that's expected
3. **Test prompt content, not LLM output**: Unit tests check prompt TEXT contains required instructions - don't try to validate LLM actually follows them
4. **Run `make test-ollama` before marking done**: Verify no regressions (Story 12.3 had 18 pre-existing failures unrelated to that story)
5. **Follow existing test patterns**: Story 12.3 added tests to existing test classes, not new files

### Anti-Patterns to Avoid

| Mistake | Correct |
|---------|---------|
| Making response_style a new value | Keep existing "concise"/"detailed" values |
| Adding new fields to SynthesizerOutput | Use existing fields (response, key_points, evidence_cited) |
| Testing LLM output quality in unit tests | Test prompt TEXT contains required instructions |
| Requiring exact word counts | Word counts are targets/guidelines |
| Modifying `_format_analysis()` | It already formats findings with evidence correctly |
| Creating new test class | Add tests to existing `TestSynthesizerPromptBuilding` |
| Modifying `synthesize()` method | Only `build_prompt()` needs changes |

### Example Expected Output

**Query:** "How has my bench press progressed?"

**Current Output (too brief):**
```json
{
  "response": "Your bench press has improved over the past week. You increased from 175 to 185 lbs.",
  "key_points": ["Weight increase", "Consistent reps"],
  "evidence_cited": ["Jan 3 bench", "Jan 10 bench"],
  "confidence": "high"
}
```

**Expected Enhanced Output:**
```json
{
  "response": "Your bench press shows solid progressive overload. Starting at 175x5 on Jan 3rd, you've progressed to 185x5 by Jan 10th - a 10 lb (5.7%) increase in 7 days. This progression rate is sustainable because you maintained 5 reps throughout, indicating good form retention under heavier loads. To continue progressing, consider adding 5 lbs next session or increasing to 6 reps before adding weight.",
  "key_points": [
    "10 lb increase (175→185 lbs) in 7 days",
    "5.7% strength progression",
    "Consistent 5-rep sets indicate form retention"
  ],
  "evidence_cited": [
    "2026-01-03: bench 175x5",
    "2026-01-10: bench 185x5"
  ],
  "confidence": "high"
}
```

### Commit Message Template

```
Enhance Synthesizer prompt for detailed reasoning and metrics

Story 12.4: Updates Synthesizer prompt to generate more detailed responses:
- Adds REASONING REQUIREMENTS section mandating WHY explanations
- Adds METRIC CITATION section requiring specific values with dates
- Updates concise style target from 50-100 to 75-150 words
- Updates detailed style to emphasize comprehensive trend analysis

Evidence: Records fec3d15f, 8e8e6d87, 14b9034b, 3ec25871 requested more detail.
```

### References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-001/analysis.md` | Pattern 5: Response Lacks Detail |
| `packages/quilto/quilto/agents/synthesizer.py` | Current Synthesizer implementation |
| `_bmad-output/implementation-artifacts/epic-4/4-2-implement-synthesizer-agent.md` | Original Synthesizer story |
| `_bmad-output/planning-artifacts/epics.md#Story 12.4` | Story definition |

### Validation Checklist (Copy-Paste for Dev Agent)

```
- [ ] `make check` passes (lint + typecheck)
- [ ] `make validate` passes (unit tests)
- [ ] `make test-ollama` runs (note: may have pre-existing failures unrelated to this story)
- [ ] Prompt contains "REASONING REQUIREMENTS" section
- [ ] Prompt contains "METRIC CITATION" section
- [ ] Concise style shows "75-150 words" (NOT "50-100 words")
- [ ] Detailed style mentions "trend analysis"
- [ ] 4 new tests added to TestSynthesizerPromptBuilding
- [ ] All 4 new tests pass
- [ ] No changes to SynthesizerInput or SynthesizerOutput models
- [ ] No changes to _format_analysis() or synthesize() methods
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- All prompt-only changes implemented in `build_prompt()` method
- Existing tests updated to match new prompt content (concise: 75-150 words, detailed: full reasoning chain)
- 4 new tests added verifying REASONING REQUIREMENTS, METRIC CITATION, word count update, and trend analysis emphasis
- `make check` passed: lint + typecheck clean
- `make validate` passed: 1904 unit tests passed
- `make test-ollama` ran: 1930 passed, 18 failed (pre-existing Ollama timeout issues unrelated to this story)
- No changes to SynthesizerInput, SynthesizerOutput, `_format_analysis()`, or `synthesize()` methods

### File List

| File | Changes |
|------|---------|
| `packages/quilto/quilto/agents/synthesizer.py` | Updated `build_prompt()`: CONCISE STYLE (75-150 words), DETAILED STYLE (trend analysis), added REASONING REQUIREMENTS section, added METRIC CITATION section |
| `packages/quilto/tests/test_synthesizer.py` | Added 4 tests to `TestSynthesizerPromptBuilding`: reasoning_requirements, metric_citation, concise_word_count, detailed_trend_analysis; updated 2 existing tests for new prompt content |
