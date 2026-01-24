# Story 12.5: Add Response Language Detection

Status: done

## Story

As a **Quilto user querying in Korean**,
I want **the final response in Korean**,
So that **the experience feels natural**.

## Background

**Origin:** Dogfooding Iteration 1 Analysis (2026-01-24)
**Source:** `tests/eval/feedback/archive/iter-001/analysis.md` - Pattern 6: Response Language Mismatch
**Priority:** Low | **Effort:** Small (1-2 hours)

**Problem Identified:**

Users querying in Korean receive responses in English. This creates a jarring experience where the system appears to not understand the user's language preference.

**User Feedback Quote (record `8e8e6d87`):**
> "The response language should have followed user's query language but it responded in English which middle output would actually be better in English but at least the final response should match with the query language."

**Root Cause:** Synthesizer lacks language detection/matching instruction. The prompt doesn't tell the LLM to match the response language to the query language.

**Design Decision:**

The simplest and most robust solution is to add a language matching instruction to the Synthesizer prompt. This follows the same pattern as Story 12.4 (prompt-only changes).

We do NOT need:
- External language detection library (over-engineering)
- Explicit language field in SynthesizerInput (API change)
- Multi-pass detection (complex)

Modern LLMs can detect query language and respond in kind when instructed explicitly. This is the same approach used by ChatGPT and other conversational AI.

## Acceptance Criteria

1. **Given** user query in Korean
   **When** Synthesizer generates response
   **Then** response is in Korean

2. **Given** user query in English
   **When** Synthesizer generates response
   **Then** response is in English

3. **Given** user query in mixed Korean/English
   **When** Synthesizer generates response
   **Then** response follows the dominant language of the query

4. **Given** backward compatibility requirement
   **When** existing code calls Synthesizer
   **Then** no API changes required (prompt enhancement only)

5. **Given** technical terms in domain vocabulary
   **When** Synthesizer generates response in non-English
   **Then** technical terms may remain in English (common practice for fitness terminology like "rep", "set", "PR")

## Tasks / Subtasks

- [x] Task 1: Review current Synthesizer prompt structure (AC: #1, #2, #3)
  - [x] 1.1: Read `build_prompt()` in `packages/quilto/quilto/agents/synthesizer.py:147-259`
  - [x] 1.2: Identify insertion point for language matching instruction (after RESPONSE GUIDELINES section)
  - [x] 1.3: Note the prompt already includes query text which LLM can use for language detection

- [x] Task 2: Add LANGUAGE MATCHING section to prompt (AC: #1, #2, #3, #5)
  - [x] 2.1: Insert new section after RESPONSE GUIDELINES (line 245) and before CONFIDENCE MAPPING (line 247)
  - [x] 2.2: Include clear instruction with examples
  - [x] 2.3: Exact text to add - see Dev Notes section below

- [x] Task 3: Add unit tests to `TestSynthesizerPromptBuilding` class (AC: #1, #2)
  - [x] 3.1: Add `test_prompt_includes_language_matching()` - assert "LANGUAGE MATCHING" in prompt
  - [x] 3.2: Add `test_prompt_includes_language_instruction()` - assert "respond in the same language" in prompt.lower()

- [x] Task 4: Run validation
  - [x] 4.1: Run `make check` (lint + typecheck) - PASSED
  - [x] 4.2: Run `make validate` (full validation including unit tests) - PASSED (1906 tests)
  - [x] 4.3: Run `make test-ollama` (integration tests - verify existing tests still pass) - PASSED (65 synthesizer tests)

## Dev Notes

### Scope: Prompt-Only Changes

**Files to modify:**
- `packages/quilto/quilto/agents/synthesizer.py` - ONLY `build_prompt()` method (lines 147-259)
- `packages/quilto/tests/test_synthesizer.py` - Add 2 tests to existing `TestSynthesizerPromptBuilding` class

**NO changes needed to:**
- Model classes (SynthesizerInput, SynthesizerOutput)
- Exports (__init__.py)
- `_format_analysis()`, `_format_vocabulary()`, `_format_gaps()`, `_get_confidence_from_verdict()`
- `synthesize()` method

### Current Prompt Structure (synthesizer.py:147-259)

```python
# build_prompt() method spans lines 147-259
# The f-string return starts at line 197
# Within the f-string template:
#   - RESPONSE GUIDELINES: ~line 239-245 in the f-string
#   - CONFIDENCE MAPPING: ~line 247-250 in the f-string
#   - OUTPUT: ~line 252-259 in the f-string
# INSERT new LANGUAGE MATCHING section between RESPONSE GUIDELINES and CONFIDENCE MAPPING
```

### Exact Code Changes

**1. In `packages/quilto/quilto/agents/synthesizer.py` `build_prompt()` method:**

Find this exact string in the f-string (lines 244-247):

```
5. If partial: clearly state what you can answer and what remains unknown

=== CONFIDENCE MAPPING ===
```

Replace with:

```
5. If partial: clearly state what you can answer and what remains unknown

=== LANGUAGE MATCHING ===

CRITICAL: Respond in the SAME LANGUAGE as the user's query.

- Korean query -> Korean response
- English query -> English response
- Mixed query -> Use the dominant language

Technical terms (rep, set, PR, 1RM) may remain in English even in non-English responses.

Example:
Query: "내 벤치프레스 기록이 어떻게 변했어?"
Response: "1월 3일 175파운드에서 1월 10일 185파운드로 10파운드(5.7%) 증가했습니다..."

=== CONFIDENCE MAPPING ===
```

### Unit Test Assertions (Add to TestSynthesizerPromptBuilding)

Add these 2 new tests after the existing `test_detailed_style_includes_trend_analysis` test (class ends at line 889, add after line 889):

```python
def test_prompt_includes_language_matching(self) -> None:
    """Prompt includes LANGUAGE MATCHING section."""
    client = create_mock_llm_client({})
    synthesizer = SynthesizerAgent(client)

    synthesizer_input = SynthesizerInput(
        query="How has my bench press progressed?",
        query_type=QueryType.INSIGHT,
        analysis=create_sample_analyzer_output_sufficient(),
        vocabulary=create_sample_vocabulary(),
    )
    prompt = synthesizer.build_prompt(synthesizer_input)

    assert "LANGUAGE MATCHING" in prompt

def test_prompt_includes_language_instruction(self) -> None:
    """Prompt includes instruction to match response language to query language."""
    client = create_mock_llm_client({})
    synthesizer = SynthesizerAgent(client)

    synthesizer_input = SynthesizerInput(
        query="내 벤치프레스 기록이 어떻게 변했어?",  # Korean query
        query_type=QueryType.INSIGHT,
        analysis=create_sample_analyzer_output_sufficient(),
        vocabulary=create_sample_vocabulary(),
    )
    prompt = synthesizer.build_prompt(synthesizer_input)

    assert "respond in the same language" in prompt.lower()
    assert "korean query -> korean response" in prompt.lower()
```

### Key Files

| File | Purpose | Location |
|------|---------|----------|
| `packages/quilto/quilto/agents/synthesizer.py` | Insert LANGUAGE MATCHING section in `build_prompt()` | Between "=== RESPONSE GUIDELINES ===" and "=== CONFIDENCE MAPPING ===" sections in the f-string (around line 246) |
| `packages/quilto/tests/test_synthesizer.py` | Add 2 tests to `TestSynthesizerPromptBuilding` class | After line 889 (end of class, before `TestSynthesizeMethod`) |

### Testing Strategy

**Unit Tests (2 new methods in `TestSynthesizerPromptBuilding` class):**

| Test Name | Assert Contains |
|-----------|-----------------|
| `test_prompt_includes_language_matching` | "LANGUAGE MATCHING" |
| `test_prompt_includes_language_instruction` | "respond in the same language" (case-insensitive) |

**Integration Tests:**
- Run `make test-ollama` - existing `TestSynthesizerIntegration` tests validate LLM still produces valid output
- No NEW integration tests needed (prompt changes don't require new integration testing)
- Manual testing recommended: Try Korean query in debug mode to verify response language

### Previous Story Learnings (from 12.4)

1. **Prompt-only changes are low risk**: No API changes means guaranteed backward compatibility (AC #4)
2. **LLM follows language instructions well**: Modern LLMs (including qwen2.5) understand language matching instructions
3. **Test prompt content, not LLM output**: Unit tests check prompt TEXT contains required instructions
4. **Run `make test-ollama` before marking done**: Verify no regressions
5. **Follow existing test patterns**: Add tests to existing test classes, not new files

### Anti-Patterns to Avoid

| Mistake | Correct |
|---------|---------|
| Adding language detection library | Use LLM's built-in capability |
| Adding `language` field to SynthesizerInput | Let LLM detect from query text |
| Testing LLM output language in unit tests | Test prompt TEXT contains required instructions |
| Forcing all terms to target language | Allow technical terms in English |
| Creating new test class | Add tests to existing `TestSynthesizerPromptBuilding` |

### Example Expected Output

**Query (Korean):** "내 벤치프레스 기록이 어떻게 변했어?"

**Expected Response (Korean):**
```json
{
  "response": "벤치프레스가 꾸준히 향상되고 있습니다. 1월 3일 175파운드(5회)에서 시작해서 1월 10일에는 185파운드(5회)까지 올렸습니다 - 7일 만에 10파운드(5.7%) 증가했네요. rep 수를 유지하면서 무게가 올랐기 때문에 좋은 progressive overload 패턴입니다.",
  "key_points": [
    "7일간 10파운드 증가 (175→185)",
    "5.7% 근력 향상",
    "5 rep 유지하며 폼 안정적"
  ],
  "evidence_cited": [
    "2026-01-03: bench 175x5",
    "2026-01-10: bench 185x5"
  ],
  "confidence": "high"
}
```

Note: Technical terms like "rep", "progressive overload", "bench" may remain in English - this is common practice and acceptable per AC #5.

### Project Structure Notes

- Aligns with Quilto framework location (`packages/quilto/`)
- Follows existing synthesizer.py structure and patterns
- Test file location follows project convention (`packages/quilto/tests/`)
- No conflicts with other Epic 12 stories (12.1-12.4 are all complete)

### References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-001/analysis.md` | Pattern 6: Response Language Mismatch |
| `packages/quilto/quilto/agents/synthesizer.py` | Current Synthesizer implementation |
| `_bmad-output/implementation-artifacts/epic-12/12-4-enhance-synthesizer-detail.md` | Previous story with similar prompt-only changes |
| `_bmad-output/planning-artifacts/epics.md#Story 12.5` | Story definition |

### Validation Checklist (Copy-Paste for Dev Agent)

```
- [ ] `make check` passes (lint + typecheck)
- [ ] `make validate` passes (unit tests)
- [ ] `make test-ollama` runs (note: may have pre-existing failures unrelated to this story)
- [ ] Prompt contains "LANGUAGE MATCHING" section
- [ ] Prompt contains "respond in the same language" instruction
- [ ] Prompt contains Korean/English example
- [ ] 2 new tests added to TestSynthesizerPromptBuilding
- [ ] All 2 new tests pass
- [ ] No changes to SynthesizerInput or SynthesizerOutput models
- [ ] No changes to synthesize() method
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug logs required for prompt-only changes

### Completion Notes List

1. Added LANGUAGE MATCHING section to Synthesizer prompt between RESPONSE GUIDELINES and CONFIDENCE MAPPING
2. Section includes:
   - Critical instruction to respond in same language as query
   - Language mapping rules (Korean->Korean, English->English, Mixed->Dominant)
   - Technical term exception (rep, set, PR, 1RM may remain English)
   - Korean example with bench press query/response
3. Added 2 unit tests to TestSynthesizerPromptBuilding class:
   - `test_prompt_includes_language_matching()` - Verifies "LANGUAGE MATCHING" in prompt
   - `test_prompt_includes_language_instruction()` - Verifies "respond in the same language" instruction
4. All validation passed:
   - `make check`: All checks passed, 0 errors
   - `make validate`: 1906 tests passed
   - `make test-ollama` (synthesizer): 65 tests passed including 3 real Ollama integration tests
5. No API changes - backward compatibility maintained (AC #4)

### File List

| File | Change |
|------|--------|
| `packages/quilto/quilto/agents/synthesizer.py` | Added LANGUAGE MATCHING section to `build_prompt()` (lines 246-261) |
| `packages/quilto/tests/test_synthesizer.py` | Added 2 tests to `TestSynthesizerPromptBuilding` class (lines 890-918) |
