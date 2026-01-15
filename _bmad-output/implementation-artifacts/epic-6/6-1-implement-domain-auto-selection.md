# Story 6.1: Implement Domain Auto-Selection

Status: done

## Story

As a **Quilto developer**,
I want **the framework to build ActiveDomainContext from Router's domain selections**,
so that **downstream agents receive merged domain knowledge without manual configuration**.

## Background

Router already outputs `selected_domains: list[str]` (Epic 2). The gap: **no component converts these names into a usable `ActiveDomainContext`** for downstream agents.

**Current State:**
- Router outputs `selected_domains: list[str]` (e.g., `["strength", "running"]`)
- `ActiveDomainContext` is a stub in models.py line 312-335
- No `DomainSelector` class exists to build context from selections

**What This Story Delivers:** `DomainSelector` class that bridges Router output → `ActiveDomainContext`.

## Acceptance Criteria

1. **Given** a list of `DomainModule` instances and `selected_domains` from Router
   **When** `DomainSelector.build_active_context()` is called
   **Then** it returns a properly populated `ActiveDomainContext`
   **And** vocabularies from all selected domains are merged
   **And** expertise strings from all selected domains are concatenated with domain labels
   **And** evaluation_rules from all selected domains are combined
   **And** clarification_patterns from all selected domains are merged

2. **Given** an input that spans multiple domains (e.g., "Compare my running with my lifting")
   **When** `DomainSelector.build_active_context()` is called with `["running", "strength"]`
   **Then** `ActiveDomainContext.domains_loaded` contains both domain names
   **And** vocabularies from both domains are accessible

3. **Given** an input that matches only one domain
   **When** `DomainSelector.build_active_context()` is called with `["strength"]`
   **Then** `ActiveDomainContext` contains only strength domain's merged data

4. **Given** empty `selected_domains` list (no domains matched)
   **When** `DomainSelector.build_active_context()` is called with `[]`
   **Then** `ActiveDomainContext` is created with empty/default values
   **And** the framework does not crash or error

5. **Given** `DomainModule` instances with optional fields (e.g., empty `response_evaluation_rules`)
   **When** `DomainSelector.build_active_context()` is called
   **Then** it handles missing/empty optional fields gracefully
   **And** no errors are raised

6. **Given** vocabulary conflicts (same key, different values) between domains
   **When** vocabularies are merged
   **Then** later domains override earlier domains (deterministic merge order)
   **And** a warning is logged about the conflict

## Tasks / Subtasks

- [x] Task 1: Create DomainSelector class (AC: #1, #4, #5, #6)
  - [x] 1.1: Create `packages/quilto/quilto/domain_selector.py`
  - [x] 1.2: Define `DomainSelector` class with constructor accepting `list[DomainModule]`
  - [x] 1.3: Implement `build_active_context(selected_domains: list[str]) -> ActiveDomainContext`
  - [x] 1.4: Implement `_merge_vocabularies(domains: list[DomainModule]) -> dict[str, str]` with conflict warning
  - [x] 1.5: Implement `_combine_expertise(domains: list[DomainModule]) -> str` with domain labels
  - [x] 1.6: Implement `_combine_evaluation_rules(domains: list[DomainModule]) -> list[str]`
  - [x] 1.7: Implement `_combine_context_guidance(domains: list[DomainModule]) -> str`
  - [x] 1.8: Implement `_combine_clarification_patterns(domains: list[DomainModule]) -> dict[str, list[str]]`
  - [x] 1.9: Implement `get_domain_infos() -> list[DomainInfo]` for Router input
  - [x] 1.10: Export `DomainSelector` from `quilto/__init__.py`

- [x] Task 2: Update ActiveDomainContext model (AC: #1)
  - [x] 2.1: Remove "stub" note from docstring in `models.py` (line ~312)
  - [x] 2.2: Add `clarification_patterns: dict[str, list[str]] = {}` field
  - [x] 2.3: Update docstring with proper documentation

- [x] Task 3: Create unit tests for DomainSelector (AC: #1, #2, #3, #4, #5, #6)
  - [x] 3.1: Create `packages/quilto/tests/test_domain_selector.py`
  - [x] 3.2: Test `build_active_context` with single domain
  - [x] 3.3: Test `build_active_context` with multiple domains
  - [x] 3.4: Test `build_active_context` with no matching domains (empty list)
  - [x] 3.5: Test vocabulary merging (no conflicts)
  - [x] 3.6: Test vocabulary merging with conflicts (warning logged via caplog)
  - [x] 3.7: Test expertise combination with domain labels
  - [x] 3.8: Test evaluation rules combination
  - [x] 3.9: Test `get_domain_infos()` returns correct `DomainInfo` list
  - [x] 3.10: Test domains with empty optional fields
  - [x] 3.11: Test clarification_patterns merging

- [x] Task 4: Create integration tests with Swealog domains (AC: #2, #3)
  - [x] 4.1: Add integration test: Router + DomainSelector end-to-end
  - [x] 4.2: Test with Swealog domains (strength, running, nutrition)
  - [x] 4.3: Test multi-domain query selection and context building
  - [x] 4.4: Test single domain query selection and context building
  - [x] 4.5: Tests use standard pytest without @pytest.mark.ollama (no real LLM required)

- [x] Task 5: Update manual_test.py (optional, for validation)
  - [x] 5.1: Add `DomainSelector` usage example in manual test flow
  - [x] 5.2: Show `ActiveDomainContext` being built from Router output

- [x] Task 6: Run validation
  - [x] 6.1: Run `make check` (lint + typecheck) - All changed files pass
  - [x] 6.2: Run `make validate` (full validation) - 1150 tests pass
  - [x] 6.3: Run `make test-ollama` (integration tests with real Ollama) - 1176 tests pass

## Dev Notes

### Key Architecture Decisions

**Location:** `packages/quilto/quilto/domain_selector.py` (new file in Quilto framework)

**Pattern:** Follow existing Quilto patterns - pure functions, type hints, Google-style docstrings.

**Critical:** Do NOT modify Router. Router's `selected_domains` output (Story 2-2) is correct. This story ONLY adds `DomainSelector` to consume that output.

### DomainSelector Implementation Pattern

```python
"""Domain selector for building ActiveDomainContext from DomainModules."""

import logging
from quilto.agents.models import ActiveDomainContext, DomainInfo
from quilto.domain import DomainModule

logger = logging.getLogger(__name__)


class DomainSelector:
    """Bridges Router's selected_domains → ActiveDomainContext for downstream agents."""

    def __init__(self, domains: list[DomainModule]) -> None:
        self.domains: dict[str, DomainModule] = {d.name: d for d in domains}

    def get_domain_infos(self) -> list[DomainInfo]:
        """Get DomainInfo list for Router input."""
        return [DomainInfo(name=d.name, description=d.description) for d in self.domains.values()]

    def build_active_context(self, selected_domains: list[str]) -> ActiveDomainContext:
        """Build merged context from selected domain names."""
        selected = [self.domains[name] for name in selected_domains if name in self.domains]
        return ActiveDomainContext(
            domains_loaded=selected_domains,
            vocabulary=self._merge_vocabularies(selected),
            expertise=self._combine_expertise(selected),
            evaluation_rules=self._combine_evaluation_rules(selected),
            context_guidance=self._combine_context_guidance(selected),
            clarification_patterns=self._combine_clarification_patterns(selected),
            available_domains=self.get_domain_infos(),
        )
```

### Merge Strategy Details

**Vocabulary conflicts (AC #6):**
- Process domains in list order
- Later domain's value wins
- Log warning: `logger.warning(f"Vocabulary conflict for '{key}': ...")`

**Expertise combination:**
```python
# Format: "[domain_name] expertise_text\n\n[domain_name] expertise_text"
parts = [f"[{d.name}] {d.expertise}" for d in domains if d.expertise]
return "\n\n".join(parts)
```

**Clarification patterns merge (Epic 5 added this to DomainModule):**
```python
def _combine_clarification_patterns(self, domains: list[DomainModule]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for domain in domains:
        for gap_type, questions in domain.clarification_patterns.items():
            if gap_type not in merged:
                merged[gap_type] = []
            merged[gap_type].extend(questions)
    return merged
```

### Empty Handling Rules

| Input | Result |
|-------|--------|
| `selected_domains=[]` | Empty `ActiveDomainContext` with defaults |
| Empty `vocabulary` | Skip in merge |
| Empty `expertise` | Skip in combination |
| Empty `evaluation_rules` | Results in `[]` |
| Empty `clarification_patterns` | Results in `{}` |

### ActiveDomainContext Updates (Task 2)

Current stub at `models.py:312-335` needs:
1. Remove "stub" docstring note
2. Add `clarification_patterns: dict[str, list[str]] = {}` field
3. Update docstring to reflect actual usage

### Test Strategy

**Unit tests (Task 3):**
- Create mock DomainModule fixtures with controlled vocabulary, expertise, etc.
- Use `caplog` fixture to verify warning logged on vocabulary conflict
- Test boundary cases: 0, 1, and 2+ domains

**Integration tests (Task 4):**
- Import actual Swealog domains (strength, running, nutrition)
- Test Router + DomainSelector end-to-end with `@pytest.mark.ollama`

### Existing Code References

| File | Relevance |
|------|-----------|
| `packages/quilto/quilto/agents/models.py:312-335` | ActiveDomainContext to update |
| `packages/quilto/quilto/domain.py` | DomainModule interface including `clarification_patterns` |
| `packages/quilto/quilto/agents/router.py` | Router outputs `selected_domains` |
| `packages/swealog/swealog/domains/strength.py` | Example domain with all fields populated |
| `packages/quilto/quilto/__init__.py` | Export DomainSelector here |

### Story Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| 2-2 (done) | Upstream | Router already outputs `selected_domains` |
| 5-4 (done) | Upstream | Added `clarification_patterns` to DomainModule |
| 6-2 (next) | Downstream | Multi-domain combination builds on DomainSelector |
| 6-3 (future) | Downstream | Mid-flow domain expansion uses DomainSelector |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug issues encountered.

### Completion Notes List

- Created `DomainSelector` class at `packages/quilto/quilto/domain_selector.py` (146 lines)
- Updated `ActiveDomainContext` in `models.py` with `clarification_patterns` field and updated docstring
- Exported `DomainSelector` from `quilto/__init__.py`
- Created 21 unit tests in `packages/quilto/tests/test_domain_selector.py`
- Created 12 integration tests in `tests/integration/test_domain_selector_integration.py`
- Refactored `scripts/manual_test.py` to use `DomainSelector` for vocabulary/context merging
- All 1176 tests pass with real Ollama integration

### Senior Developer Review (AI)

**Reviewer:** Amelia (Dev Agent) | **Date:** 2026-01-15

**Review Result:** APPROVED with fixes applied

**Issues Found and Fixed:**

1. **[HIGH] Type Annotation Error** (domain_selector.py:33)
   - Issue: `list[DomainModule]` parameter caused pyright error in manual_test.py due to list invariance
   - Fix: Changed to `Sequence[DomainModule]` for covariance (accepts domain subclasses)
   - Status: FIXED

**LOW Issues Acknowledged (Not Fixed - By Design):**

- `domains_loaded` includes unknown domain names passed to `build_active_context()` even when they don't exist in the selector. This is documented and tested behavior for transparency.

**Validation:**
- All 33 story tests pass (21 unit + 12 integration)
- Pyright: 0 errors
- Ruff: All checks passed

### File List

| File | Action | Description |
|------|--------|-------------|
| `packages/quilto/quilto/domain_selector.py` | Created | DomainSelector class implementation |
| `packages/quilto/quilto/agents/models.py` | Modified | Added clarification_patterns to ActiveDomainContext, updated docstring |
| `packages/quilto/quilto/__init__.py` | Modified | Exported DomainSelector |
| `packages/quilto/tests/test_domain_selector.py` | Created | 21 unit tests for DomainSelector |
| `tests/integration/test_domain_selector_integration.py` | Created | 12 integration tests with Swealog domains |
| `scripts/manual_test.py` | Modified | Refactored to use DomainSelector for domain merging |
