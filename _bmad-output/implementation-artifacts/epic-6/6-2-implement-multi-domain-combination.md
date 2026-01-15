# Story 6.2: Implement Multi-Domain Combination

Status: done

## Story

As a **Quilto developer**,
I want **ActiveDomainContext that combines base + selected domains**,
so that **agents receive merged domain knowledge**.

## Background

Story 6.1 implemented `DomainSelector.build_active_context()` which builds `ActiveDomainContext` from selected domains. However, the epics describe a **base + selected** combination pattern that is NOT yet implemented:

**Current State (Story 6.1 delivered):**
- `DomainSelector` takes a list of `DomainModule` instances
- `build_active_context(selected_domains)` merges ONLY the selected domains
- No concept of a "base" domain separate from selected domains

**What This Story Delivers:**
- Support for a "base domain" that is ALWAYS included in the merged context
- Base domain provides common vocabulary, expertise, and rules shared across all queries
- Selected domains are merged ON TOP of the base domain
- Downstream agents receive comprehensive context combining both

**Use Case Example:**
- User asks "How has my bench press progressed this month?"
- Router selects: `["strength"]`
- Base domain: `general_fitness` (provides common fitness terminology, general workout patterns)
- Result: `ActiveDomainContext` merges general_fitness + strength

## Acceptance Criteria

1. **Given** a `base_domain: DomainModule | None` and `selected_domains` from Router
   **When** `DomainSelector.build_active_context()` is called
   **Then** base_domain vocabularies are applied FIRST
   **And** selected domain vocabularies are merged ON TOP (overriding conflicts)
   **And** expertise from base + selected are combined with appropriate labels
   **And** evaluation_rules from base + selected are combined

2. **Given** an input that matches "strength" domain with base_domain set to "general_fitness"
   **When** `DomainSelector.build_active_context(["strength"])` is called
   **Then** `ActiveDomainContext.domains_loaded` contains both "general_fitness" and "strength"
   **And** base domain's vocabulary keys are present unless overridden by strength
   **And** expertise shows both domain contributions with labels

3. **Given** `base_domain=None` (no base domain configured)
   **When** `DomainSelector.build_active_context()` is called
   **Then** behavior is identical to current Story 6.1 implementation (backward compatible)

4. **Given** base_domain IS a selected domain (overlap)
   **When** `DomainSelector.build_active_context(["general_fitness"])` is called
   **Then** base domain is NOT duplicated in the merged context
   **And** domain appears only once in `domains_loaded`

5. **Given** the resulting `ActiveDomainContext`
   **When** downstream agents (Planner, Analyzer) receive it
   **Then** they can access the merged vocabulary, expertise, and rules
   **And** no code changes are required in downstream agents

## Tasks / Subtasks

- [x] Task 1: Update DomainSelector to support base_domain (AC: #1, #3)
  - [x] 1.1: Add `base_domain: DomainModule | None = None` parameter to `DomainSelector.__init__()`
  - [x] 1.2: Store base_domain as instance variable
  - [x] 1.3: Update `build_active_context()` to build merge list: base_domain first (if set), then selected domains (excluding base if duplicated)
  - [x] 1.4: Pass `domains_to_merge` list (not `selected`) to all merge methods

- [x] Task 2: Handle base_domain in domains_loaded list (AC: #2, #4)
  - [x] 2.1: Add base_domain.name to `domains_loaded` FIRST if base_domain is set
  - [x] 2.2: Append selected_domains to `domains_loaded`, skipping base_domain.name if already present (deduplication)
  - [x] 2.3: Verify ordering: base_domain first, then selected domains (no duplicates)

- [x] Task 3: Update unit tests for base_domain (AC: #1, #2, #3, #4, #6)
  - [x] 3.1: Test `build_active_context` with base_domain + single selected domain
  - [x] 3.2: Test `build_active_context` with base_domain + multiple selected domains
  - [x] 3.3: Test `build_active_context` with base_domain=None (backward compatibility - identical to Story 6.1)
  - [x] 3.4: Test vocabulary merge order: base applied first, selected override conflicts
  - [x] 3.5: Test domains_loaded includes base_domain.name first
  - [x] 3.6: Test deduplication: when base_domain.name is in selected_domains, it appears only once in domains_loaded
  - [x] 3.7: Test expertise combination includes base_domain with label FIRST
  - [x] 3.8: Test vocabulary conflict warning is logged when base_domain and selected domain have same key

- [x] Task 4: Create integration tests with Swealog domains (AC: #5)
  - [x] 4.1: Add test to `tests/integration/test_domain_selector_integration.py` with general_fitness as base_domain, strength as selected (no @pytest.mark.ollama - uses mock or direct test)
  - [x] 4.2: Test merged context has vocabulary from both general_fitness and strength
  - [x] 4.3: Test merged context has expertise from both domains with correct labels
  - [x] 4.4: Test deduplication when general_fitness is both base AND selected

- [x] Task 5: Run validation
  - [x] 5.1: Run `make check` (lint + typecheck) - All changed files pass
  - [x] 5.2: Run `make validate` (full validation) - All tests pass
  - [x] 5.3: Run `make test-ollama` (integration tests with real Ollama) - All tests pass

## Dev Notes

### Key Architecture Decisions

**Location:** `packages/quilto/quilto/domain_selector.py` (modify existing file from Story 6.1)

**Pattern:** Extend existing `DomainSelector` class - do NOT create new class.

**Merge Strategy:**
1. Start with base_domain (if set)
2. Apply selected domains in order
3. Later domains override earlier for vocabulary conflicts (log warning)
4. Expertise and evaluation_rules are always concatenated, not replaced

### Implementation Pattern

**Changes to `__init__`:**
```python
def __init__(
    self,
    domains: Sequence[DomainModule],
    base_domain: DomainModule | None = None,  # NEW
) -> None:
    self.domains: dict[str, DomainModule] = {d.name: d for d in domains}
    self.base_domain = base_domain
```

**Changes to `build_active_context`:**
```python
def build_active_context(self, selected_domains: list[str]) -> ActiveDomainContext:
    selected = [self.domains[name] for name in selected_domains if name in self.domains]

    # CRITICAL: Build merge list with deduplication
    domains_to_merge: list[DomainModule] = []
    if self.base_domain is not None:
        domains_to_merge.append(self.base_domain)
    for d in selected:
        # Prevent double-merge if base_domain is also selected
        if self.base_domain is None or d.name != self.base_domain.name:
            domains_to_merge.append(d)

    # Build domains_loaded with deduplication
    domains_loaded: list[str] = []
    if self.base_domain is not None:
        domains_loaded.append(self.base_domain.name)
    for name in selected_domains:
        if name not in domains_loaded:
            domains_loaded.append(name)

    # Pass domains_to_merge (not selected) to ALL merge methods
    return ActiveDomainContext(
        domains_loaded=domains_loaded,
        vocabulary=self._merge_vocabularies(domains_to_merge),
        expertise=self._combine_expertise(domains_to_merge),
        evaluation_rules=self._combine_evaluation_rules(domains_to_merge),
        context_guidance=self._combine_context_guidance(domains_to_merge),
        clarification_patterns=self._combine_clarification_patterns(domains_to_merge),
        available_domains=self.get_domain_infos(),
    )
```

### Existing Merge Methods (Story 6.1) - NO CHANGES NEEDED

All merge methods already handle `list[DomainModule]` and work unchanged:
- `_merge_vocabularies()` - processes in order, logs conflicts (base first = can be overridden)
- `_combine_expertise()` - concatenates with domain labels (base label appears first)
- `_combine_evaluation_rules()` - extends list (base rules first)
- `_combine_context_guidance()` - concatenates with domain labels (base guidance first)
- `_combine_clarification_patterns()` - extends lists per gap type

**Key insight:** Just pass `domains_to_merge` instead of `selected` - ordering handles base-first semantics automatically.

### Export Status

**No new exports required.** `DomainSelector` is already exported from `quilto/__init__.py` (Story 6.1). This story only adds an optional parameter to the existing class.

### Backward Compatibility

**Critical:** Existing code using `DomainSelector(domains)` without base_domain MUST continue to work identically.

- `base_domain=None` is the default
- When `base_domain=None`, behavior matches Story 6.1 exactly
- All existing tests MUST pass without modification

### Test Strategy

**Unit tests (Task 3) - Add to `packages/quilto/tests/test_domain_selector.py`:**
- Create new `base_domain` fixture (or reuse `domain_a`)
- Test vocabulary merge order: base applied first, selected domain's values override on conflict
- Test `domains_loaded` ordering: base_domain.name first, then selected (deduplicated)
- Use `caplog` to verify warning logged on vocabulary conflict (both base-vs-selected and selected-vs-selected)
- Test backward compatibility: `base_domain=None` produces identical results to Story 6.1

**Integration tests (Task 4) - Add to `tests/integration/test_domain_selector_integration.py`:**
- Use actual Swealog domains: `general_fitness` as base, `strength` as selected
- NO `@pytest.mark.ollama` needed - these tests verify context building, not LLM behavior
- Test merged vocabulary contains keys from both domains
- Test deduplication when `general_fitness` appears as both base AND in selected_domains

**AC #5 Note:** Downstream agent compatibility (Planner, Analyzer) is verified implicitly - `ActiveDomainContext` structure is unchanged, only content varies. Existing agent tests provide coverage.

### Existing Code References

| File | Relevance |
|------|-----------|
| `packages/quilto/quilto/domain_selector.py` | Primary file to modify (~161 lines currently) |
| `packages/quilto/tests/test_domain_selector.py` | Add unit tests here (21 existing tests) |
| `packages/quilto/quilto/agents/models.py:312-337` | ActiveDomainContext (NO changes needed) |
| `packages/quilto/quilto/__init__.py` | DomainSelector already exported (NO changes needed) |
| `packages/swealog/swealog/domains/general_fitness.py` | Use as base_domain in integration tests |
| `packages/swealog/swealog/domains/strength.py` | Use as selected domain in integration tests |
| `tests/integration/test_domain_selector_integration.py` | Add integration tests here (12 existing tests)

### Story Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| 6-1 (done) | Upstream | DomainSelector class exists, build_active_context works |
| 6-3 (next) | Downstream | Mid-flow domain expansion will use updated DomainSelector |

### Common Mistakes to Avoid

| Mistake | Correct Pattern |
|---------|-----------------|
| Modifying ActiveDomainContext | No changes needed - already has all required fields |
| Creating new class | Extend existing DomainSelector |
| Breaking backward compatibility | `base_domain=None` must work identically to Story 6.1 |
| Duplicating base_domain in domains_loaded | Deduplicate if base is also selected |
| Not logging vocabulary conflicts | Use existing warning pattern from `_merge_vocabularies` |
| Double-merging base_domain | Check `d.name != self.base_domain.name` before adding to `domains_to_merge` |
| Adding new exports | Not needed - DomainSelector already exported |
| Passing `selected` to merge methods | Must pass `domains_to_merge` (includes base + deduplicated selected) |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Added `base_domain: DomainModule | None = None` parameter to `DomainSelector.__init__()`
- Updated `build_active_context()` to merge base_domain first, then selected domains on top
- Implemented deduplication to prevent base_domain from appearing twice when also selected
- Base domain vocabulary is applied first, selected domains override conflicts (with warning log)
- Expertise, evaluation_rules, context_guidance, and clarification_patterns are combined with base_domain first
- Added 14 new unit tests in `TestBaseDomainSupport` class covering all acceptance criteria
- Added 8 new integration tests in `TestBaseDomainWithSwealogDomains` class using general_fitness as base
- All 35 unit tests pass (21 existing + 14 new)
- All 20 integration tests pass (12 existing + 8 new)
- All 1198 tests pass with `make test-ollama`
- Backward compatibility verified: existing code without base_domain works identically

### File List

- `packages/quilto/quilto/domain_selector.py` - Modified: added base_domain parameter and merge logic
- `packages/quilto/tests/test_domain_selector.py` - Modified: added TestBaseDomainSupport test class (14 tests)
- `tests/integration/test_domain_selector_integration.py` - Modified: added TestBaseDomainWithSwealogDomains test class (8 tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Modified: updated story status

