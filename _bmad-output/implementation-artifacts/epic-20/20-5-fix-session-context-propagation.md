# Story 20.5: Fix Session Context Propagation to All Agents

Status: done

## Story

As a **Swealog user resuming a session**,
I want **all agents to have access to my conversation history**,
So that **follow-up questions and clarification answers work correctly**.

## Acceptance Criteria

1. **Given** conversation context exists in state
   **When** Router processes input
   **Then** RouterInput receives session_context AND Router can correctly classify follow-up queries

2. **Given** conversation context exists in state
   **When** Analyzer processes entries
   **Then** AnalyzerInput includes conversation_context AND Analyzer can resolve vague references

3. **Given** conversation context exists in state
   **When** Synthesizer generates response
   **Then** SynthesizerInput includes conversation_context AND Synthesizer can answer from context when Planner skips retrieval

4. **Given** conversation context exists in state
   **When** Evaluator checks response
   **Then** EvaluatorInput includes conversation_context AND Evaluator can validate context usage

5. **Given** conversation context exists in state
   **When** Observer updates global context
   **Then** ObserverInput includes conversation_context

6. **Given** a previous turn recommended a leg workout AND user asks "What workout did you recommend earlier?"
   **When** Planner decides `next_action: synthesize` (skip retrieval)
   **Then** Synthesizer correctly answers with the leg workout details

7. **Given** user runs CLI with `--session <id>`
   **When** feedback is recorded
   **Then** session_id appears in the feedback JSON

## Tasks / Subtasks

- [x] Task 1: Update Agent Input Models (AC: #1-5)
  - [x] 1.1: **RouterInput ALREADY has `session_context: str | None = None` (line 120)** - no new field needed, just pass value from orchestration
  - [x] 1.2: Add `conversation_context: str | None = None` to AnalyzerInput (after `global_context_summary` field, line ~597)
  - [x] 1.3: Add `conversation_context: str | None = None` to SynthesizerInput (after `response_style` field, line ~676)
  - [x] 1.4: Add `conversation_context: str | None = None` to EvaluatorInput (after `previous_feedback` field, add new field)
  - [x] 1.5: Add `conversation_context: str | None = None` to ObserverInput (after existing fields)
  - [x] 1.6: Note: PlannerInput already has `conversation_context` (line 370) - no change needed

- [x] Task 2: Update Orchestration Node Functions (AC: #1-5)
  - [x] 2.1: In route_node (line ~435), pass `state.get(StateKeys.CONVERSATION_CONTEXT)` to RouterInput's **existing** `session_context` field
  - [x] 2.2: In analyze_node (line ~652), read context and pass to AnalyzerInput's new `conversation_context` field
  - [x] 2.3: In synthesize_node (line ~770 area), read context and pass to SynthesizerInput's new `conversation_context` field
  - [x] 2.4: In evaluate_node (line ~866 area), read context and pass to EvaluatorInput's new `conversation_context` field
  - [x] 2.5: In observe_node (line ~1108 area), read context and pass to ObserverInput's new `conversation_context` field

- [x] Task 3: Update Agent Prompts (AC: #1-5, #6)
  - [x] 3.1: Router prompt (router.py) - use existing `session_context` field in prompt to classify follow-ups correctly
  - [x] 3.2: Analyzer prompt (analyzer.py) - add section to resolve vague references from conversation context
  - [x] 3.3: Synthesizer prompt (synthesizer.py) - **CRITICAL**: add instruction to answer from context when findings are empty but context has answer
  - [x] 3.4: Evaluator prompt (evaluator.py) - add section to validate response correctly uses context
  - [x] 3.5: Observer prompt (observer.py) - add section to distinguish session facts from preferences

- [x] Task 4: Fix Feedback Session ID Recording (AC: #7)
  - [x] 4.1: Add `session_id: str | None = None` field to SessionMetadata class (feedback.py line 52)
  - [x] 4.2: Update `_record_feedback_with_handler` signature to accept `session_id: str | None` (app.py line 199)
  - [x] 4.3: Pass session_id when creating SessionMetadata (app.py line 234)
  - [x] 4.4: Update call site in run_command to pass `session.session_id` (app.py line 374)

- [x] Task 5: Unit Tests (AC: #1-5, #7)
  - [x] 5.1: Test RouterInput accepts session_context (already exists - verify it's passed)
  - [x] 5.2: Test AnalyzerInput accepts conversation_context
  - [x] 5.3: Test SynthesizerInput accepts conversation_context
  - [x] 5.4: Test EvaluatorInput accepts conversation_context
  - [x] 5.5: Test ObserverInput accepts conversation_context
  - [x] 5.6: Test SessionMetadata includes session_id when provided

- [x] Task 6: Integration Test (AC: #6)
  - [x] 6.1: Create test in `packages/quilto/tests/test_context_propagation.py` for context-dependent query
  - [x] 6.2: Test scenario: Synthesizer prompt includes context answering instructions + Router prompt includes follow-up detection

- [ ] Task 7: Dogfooding Verification (manual - requires LLM)
  - [ ] 7.1: Re-run failing query: "Can you tell me which workout you recommended me earlier?" with `--session <id>`
  - [ ] 7.2: Verify response includes workout details from conversation context
  - [ ] 7.3: Verify clarification answers are NOT misclassified as LOG (Pattern 1 from iter-009)

## Dev Notes

### Problem Statement

**Evidence:** `tests/eval/feedback/active/2026-01-29_4f6d9897.json`
- Query: "Can you tell me which workout you recommended me earlier?"
- Session: `--session 4dc30d9c-9d0a-4597-8191-a69dc88a15da`
- Planner reasoning: "This information is already present in the conversation context"
- Planner decision: `next_action: synthesize` (skip retrieval)
- Synthesizer response: "I don't have a record of the specific workout"
- **BUG:** Planner sees context and skips retrieval, but Synthesizer never received the context

**Pattern Fix (iter-009 Pattern #1):** Router misclassifies clarification answers as LOG because it doesn't receive session context. Example: "Strength training for upper body" (clarification answer) → classified as LOG instead of continuation.

### Propagation Status

| Agent | Field Name | Current | Target |
|-------|------------|---------|--------|
| Router | `session_context` | EXISTS (line 120) | Pass from state |
| Planner | `conversation_context` | WORKING (line 370, 525) | No change |
| Analyzer | `conversation_context` | MISSING | Add field + pass |
| Synthesizer | `conversation_context` | MISSING | Add field + pass |
| Evaluator | `conversation_context` | MISSING | Add field + pass |
| Observer | `conversation_context` | MISSING | Add field + pass |

### Code Locations

**models.py (`packages/quilto/quilto/agents/models.py`):**
- RouterInput: line 108 (has `session_context` at line 120)
- AnalyzerInput: line 564
- SynthesizerInput: line 642
- EvaluatorInput: line 752
- ObserverInput: line 971
- PlannerInput: line 340 (has `conversation_context` at line 370)

**orchestration.py (`packages/quilto/quilto/orchestration.py`):**
- route_node: line 399 (creates RouterInput at line 435)
- plan_node: line 477 (creates PlannerInput at line 521, ALREADY passes context at line 525)
- analyze_node: line 621 (creates AnalyzerInput at line 652)
- synthesize_node: line 712 (creates SynthesizerInput in try block)
- evaluate_node: line 830 (creates EvaluatorInput at line 866)
- observe_node: line 1068 (creates ObserverInput at line 1108 area)

**Swealog CLI (`packages/swealog/swealog/cli/`):**
- feedback.py: SessionMetadata at line 52
- app.py: `_record_feedback_with_handler` at line 199, call site at line 374

### Implementation Pattern

**For orchestration node functions:**
```python
# 1. Read context from state (add near top of try block)
conversation_context = state.get(StateKeys.CONVERSATION_CONTEXT)

# 2. Pass to Input model
XxxInput(
    ...,
    conversation_context=conversation_context,  # or session_context for Router
)
```

**For Router specifically (uses existing field):**
```python
session_context = state.get(StateKeys.CONVERSATION_CONTEXT)
router_input = RouterInput(
    raw_input=user_input,
    available_domains=domain_infos,
    session_context=session_context,  # Existing field, just needs value
)
```

### Prompt Engineering Pattern

**For each agent prompt, add conditional section:**
```python
if input_data.conversation_context:
    prompt += f"""
## Previous Conversation
{input_data.conversation_context}

Use this context to understand follow-up queries and resolve vague references.
"""
```

**Synthesizer-specific instruction (CRITICAL):**
```
IMPORTANT: If findings are empty but conversation context contains the answer,
use the context to generate the response. Do NOT say "I don't have a record"
when the information is clearly present in the conversation context.
```

### Previous Story Intelligence

**Story 20.4 (iter-009) Key Finding:**
- Pattern 1: Router misclassifies clarification answers (MEDIUM) - **THIS STORY FIXES IT**
- Root cause: Router doesn't receive session context
- Example: "Strength training for upper body" (clarification answer) → classified as LOG

**Stories 20.1-20.3 Verified:**
- Session conversation context loads correctly when resuming ✓
- Context passes to Planner correctly ✓
- Gap: Other agents don't receive context (this story)

### Architecture Compliance

| Requirement | Status |
|-------------|--------|
| Quilto framework changes | All agent/orchestration code in `packages/quilto/` |
| Swealog app changes | Only CLI feedback recording in `packages/swealog/` |
| Backward compatibility | All new fields default to `None` |
| Type hints | Using `str | None` pattern |
| Field naming | Router uses `session_context`, others use `conversation_context` |

### Validation Commands

```bash
# Quick validation (run frequently)
make check

# Full validation (before commit)
make validate

# Run specific test file
uv run pytest packages/quilto/tests/test_orchestration.py -v

# Dogfooding verification
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive --session <id> "Can you tell me which workout you recommended me earlier?"
```

### References

- [Evidence: `tests/eval/feedback/active/2026-01-29_4f6d9897.json`]
- [Pattern #1: `tests/eval/feedback/archive/iter-009/analysis.md`]
- [Previous iteration: `_bmad-output/implementation-artifacts/epic-20/20-4-dogfooding-iteration-9.md`]
- [Epic source: `_bmad-output/planning-artifacts/epics.md`, Story 20.5, lines 3444-3509]
- [Project conventions: `_bmad-output/project-context.md`]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All tests pass: `make validate` - 2130 passed, 101 skipped

### Completion Notes List

1. **Task 1-2**: Added `conversation_context` field to AnalyzerInput, SynthesizerInput, EvaluatorInput, ObserverInput models. Updated orchestration nodes to pass context from state to all agents.

2. **Task 3**: Updated all agent prompts:
   - Router: Added FOLLOW-UP detection instructions using session_context
   - Analyzer: Added section to resolve vague references from context
   - Synthesizer: Added CRITICAL context-based answering instructions
   - Evaluator: Added section to validate context usage as valid evidence
   - Observer: Added section to distinguish session facts from global preferences

3. **Task 4**: Added `session_id` to SessionMetadata and updated CLI to pass it to feedback recording.

4. **Task 5-6**: Created comprehensive unit tests in `test_context_propagation.py` covering all agent input models and integration scenarios.

5. **Task 7**: Dogfooding verification requires manual LLM testing.

### File List

| File | Action |
|------|--------|
| `packages/quilto/quilto/agents/models.py` | Modified - added `conversation_context` to 4 Input models |
| `packages/quilto/quilto/orchestration.py` | Modified - pass context in 5 node functions |
| `packages/quilto/quilto/agents/router.py` | Modified - added follow-up detection instructions |
| `packages/quilto/quilto/agents/analyzer.py` | Modified - added `_format_conversation_context` method and prompt section |
| `packages/quilto/quilto/agents/synthesizer.py` | Modified - added CRITICAL context-based answering instructions |
| `packages/quilto/quilto/agents/evaluator.py` | Modified - added `_format_conversation_context` method and evaluation rules |
| `packages/quilto/quilto/agents/observer.py` | Modified - added context section in `_format_post_query_context` |
| `packages/swealog/swealog/cli/feedback.py` | Modified - added `session_id` to SessionMetadata |
| `packages/swealog/swealog/cli/app.py` | Modified - pass `session_id` to feedback recording |
| `packages/quilto/tests/test_context_propagation.py` | Created - 13 unit tests for context propagation |
| `packages/swealog/tests/cli/test_feedback.py` | Modified - added session_id tests |
| `packages/swealog/tests/test_cli_auto.py` | Modified - added session_id to mock sessions |
