# Story 11.1: Implement JSON Schema Structured Output

## Status: done

## Context

The current `LLMClient.complete_structured()` uses basic JSON mode:
```python
response_format={"type": "json_object"}
```

This is insufficient for OpenRouter and OpenAI that support full JSON schema:
```python
response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "ModelName",
        "strict": True,
        "schema": { ... }
    }
}
```

**Problem observed:** JSON format validation failures when using `gpt-oss-120b` on OpenRouter (paid tier), while `:free` tier works better. The `json_object` mode is not properly enforced.

**Research sources:**
- [OpenRouter Structured Outputs Docs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [gpt-oss-120b Model Page](https://openrouter.ai/openai/gpt-oss-120b)

## Goal

Update `LLMClient` to use proper JSON schema structured output, improving reliability across all providers.

## Acceptance Criteria

1. **AC1:** `complete_structured()` uses `response_format.type = "json_schema"` with full schema for supported providers
2. **AC2:** Schema is auto-generated from Pydantic model via `model.model_json_schema()`
3. **AC3:** Falls back to `json_object` for Ollama (which doesn't support json_schema)
4. **AC4:** Provider detection uses `resolution.provider` from existing `resolve_model()` call
5. **AC5:** Fallback JSON extraction for malformed responses (strip markdown, single-line comments)
6. **AC6:** All existing tests pass, new tests for JSON schema mode
7. **AC7:** `make test-ollama` passes

## Technical Design

### Provider Support Matrix

| Provider | response_format Support | Implementation |
|----------|------------------------|----------------|
| OpenRouter | `json_schema` | Full schema |
| OpenAI | `json_schema` | Full schema |
| Ollama | `json_object` only | Simple mode |
| Anthropic | Not supported | Uses tool_use (out of scope) |
| Azure | `json_schema` | Full schema |

**Note:** Anthropic via litellm does NOT support `response_format` - it uses tool_use for structured output. This story excludes Anthropic from JSON schema mode.

### Key Implementation Points

1. **Provider detection:** Get `resolution.provider` from `self.resolve_model(agent, force_cloud)` at `client.py:164`
2. **Schema generation:** Use `response_model.model_json_schema()`
3. **Existing error handling:** Integrate with current `model_validate_json()` at `client.py:216`, don't replace
4. **Cascade inheritance:** `complete_structured_with_cascade()` calls `complete_structured()` - changes propagate automatically

### Helper Method: `_build_response_format()`

```python
def _build_response_format(
    self,
    response_model: type[BaseModel],
    provider: ProviderName,
    strict: bool = True
) -> dict[str, Any]:
    """Build provider-appropriate response_format."""
    # OpenRouter, OpenAI, Azure support full json_schema
    if provider in ("openrouter", "openai", "azure"):
        schema = response_model.model_json_schema()
        return {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "strict": strict,
                "schema": schema
            }
        }
    # Ollama and others - use simple json_object
    return {"type": "json_object"}
```

### Helper Method: `_extract_json()`

```python
def _extract_json(self, response: str) -> str:
    """Extract JSON from potentially malformed LLM response."""
    # Strip markdown code blocks
    if "```json" in response:
        response = response.split("```json")[1].split("```")[0]
    elif "```" in response:
        response = response.split("```")[1].split("```")[0]

    # Remove single-line comments only (block comments not supported)
    lines = [l for l in response.split('\n')
             if not l.strip().startswith('//')]
    response = '\n'.join(lines)

    # Find JSON boundaries
    start = response.find('{')
    end = response.rfind('}') + 1
    if start >= 0 and end > start:
        return response[start:end]

    return response
```

## Tasks

- [x] **Task 1:** Add `_build_response_format()` helper method
  - [x] 1.1: Get provider from `resolution.provider` (ProviderName type)
  - [x] 1.2: Generate JSON schema via `response_model.model_json_schema()`
  - [x] 1.3: Return `json_schema` for openrouter/openai/azure, `json_object` for ollama

- [x] **Task 2:** Add `_extract_json()` fallback helper
  - [x] 2.1: Strip markdown code blocks (```json and ```)
  - [x] 2.2: Remove single-line comments (//)
  - [x] 2.3: Find JSON object boundaries ({...})
  - [x] 2.4: Unit tests for extraction edge cases

- [x] **Task 3:** Update `complete_structured()` method
  - [x] 3.1: Call `resolve_model()` first to get `resolution.provider`
  - [x] 3.2: Use `_build_response_format(response_model, resolution.provider)`
  - [x] 3.3: Add fallback to `_extract_json()` on parse failure (wrap existing error handling)

- [x] **Task 4:** Verify cascade method behavior
  - [x] 4.1: Confirm `complete_structured_with_cascade()` inherits changes via `complete_structured()`
  - [x] 4.2: Integration test inherits via cascade method chain (no separate test needed)

- [x] **Task 5:** Add tests
  - [x] 5.1: Unit tests for `_build_response_format()` - verify json_schema for openrouter/openai/azure
  - [x] 5.2: Unit tests for `_build_response_format()` - verify json_object for ollama
  - [x] 5.3: Unit tests for `_extract_json()` - markdown stripping, comment removal, boundary detection
  - [x] 5.4: Integration test: structured response with mocked providers
  - [x] 5.5: Verify existing test at `test_llm_client.py:327` still passes

- [x] **Task 6:** Validate
  - [x] 6.1: `make check` passes
  - [x] 6.2: `make validate` passes (1810 passed, 96 skipped)
  - [x] 6.3: `make test-ollama` passes (1850 passed, 56 skipped, all tests pass with `[null]` normalization fix)

## File List

| File | Action | Purpose |
|------|--------|---------|
| `packages/quilto/quilto/llm/client.py` | Modify | Add JSON schema support, helper methods |
| `packages/quilto/tests/test_llm_client.py` | Modify | Add new tests for JSON schema mode |
| `packages/quilto/quilto/agents/models.py` | Modify | Add validator to normalize `[null]` to `None` |
| `packages/quilto/tests/test_clarifier.py` | Modify | Add tests for null options normalization |

## Implementation Notes

### Existing Code References

- `resolve_model()`: `client.py:82-141` - Returns `ModelResolution` with `provider: ProviderName`
- `complete_structured()`: `client.py:181-224` - Current implementation to modify
- `complete_structured_with_cascade()`: `client.py:394-482` - Inherits changes automatically
- Existing test: `test_llm_client.py:327` - Tests `response_format={"type": "json_object"}`

### Performance Consideration

`response_model.model_json_schema()` could be cached per model class to avoid repeated computation. Consider using `functools.lru_cache` if profiling shows this is a bottleneck (optional optimization).

### litellm Alternative

litellm has built-in `response_schema` parameter support. Investigate whether this can simplify implementation in future iteration.

## Out of Scope

- Anthropic structured output (requires tool_use, different pattern)
- Block comment removal (`/* */`) - only single-line comments supported
- Pydantic model schema flexibility changes
- instructor/outlines library integration
- Provider-specific retry strategies

## Dev Agent Record

### Implementation Summary

**Date:** 2026-01-20

**Files Modified:**
- `packages/quilto/quilto/llm/client.py:56-110` - Added `_build_response_format()` and `_extract_json()` helper methods
- `packages/quilto/quilto/llm/client.py:248-307` - Updated `complete_structured()` to use provider-aware format selection
- `packages/quilto/tests/test_llm_client.py:368-559` - Added 16 new tests for JSON schema mode
- `packages/quilto/quilto/agents/models.py` - Added `normalize_null_options` field validator to `ClarificationQuestion`
- `packages/quilto/tests/test_clarifier.py` - Added 3 tests for null options normalization

**Approach:**
1. Added `_build_response_format()` that returns `json_schema` format with full schema for openrouter/openai/azure, `json_object` for ollama/anthropic
2. Added `_extract_json()` fallback that strips markdown blocks, removes // comments, and finds JSON boundaries
3. Updated `complete_structured()` to resolve model first, build appropriate format, and use fallback extraction on parse failure
4. Cascade methods inherit changes automatically via their existing call to `complete_structured()`

**Tests Added:**
- TestBuildResponseFormat: 6 tests for provider-specific format selection
- TestExtractJson: 8 tests for markdown/comment/trailing comma extraction
- TestCompleteStructuredJsonSchema: 4 tests for integration with mocked providers

### Decisions Made

1. **Schema from Pydantic:** Used `response_model.model_json_schema()` directly without caching (per implementation notes, optimize later if needed)
2. **Anthropic falls back to json_object:** Since Anthropic uses tool_use for structured output (out of scope), it falls through to simple json_object mode
3. **Fallback extraction:** On initial parse failure, try `_extract_json()` cleanup before raising error
4. **Private method tests:** Added `# pyright: ignore[reportPrivateUsage]` comments for testing private helper methods
5. **`[null]` normalization:** LLMs sometimes return `[null]` instead of `null` for optional list fields. Added field validator to `ClarificationQuestion.options` that normalizes `[null]` → `None` and filters null values from mixed lists

## Completion Notes

### Acceptance Criteria Verification

| AC | Description | Status | Notes |
|----|-------------|--------|-------|
| AC1 | Uses `json_schema` for supported providers | ✅ | openrouter, openai, azure get full schema |
| AC2 | Auto-generates schema from Pydantic model | ✅ | Uses `model_json_schema()` |
| AC3 | Falls back to `json_object` for Ollama | ✅ | Also for anthropic |
| AC4 | Provider detection from `resolution.provider` | ✅ | Uses existing `resolve_model()` call |
| AC5 | Fallback JSON extraction | ✅ | Strips markdown, comments, finds boundaries |
| AC6 | All existing tests pass | ✅ | 25 original + 18 new LLM client + 3 clarifier tests |
| AC7 | `make test-ollama` passes | ✅ | All tests pass (with `[null]` normalization fix) |

### Test-Ollama Note

Initially, one test failed: `test_real_clarification_with_strength_patterns` - qwen2.5:7b returned `"options": [null]` instead of valid `null` or `list[str]`. This is LLM non-determinism where the model interpreted "no options" as `[null]` rather than `null`.

**Fix applied:** Added `normalize_null_options` field validator to `ClarificationQuestion` that normalizes `[null]` to `None`. The validator also filters out null values from mixed lists (e.g., `["a", null, "b"]` → `["a", "b"]`). All tests now pass.

### Code Review (2026-01-20)

**Reviewer:** Dev Agent (Code Review Workflow)

**Findings Fixed:**
1. **M1 (Medium):** Added trailing comma handling to `_extract_json()` - LLMs sometimes produce JSON5-style trailing commas (e.g., `{"a":1,}`) which fail JSON parsing. Added regex to strip trailing commas before closing braces/brackets.
2. **M2 (Medium):** Updated `_build_response_format()` docstring to explicitly mention Anthropic falls back to `json_object` mode (uses tool_use for structured output, out of scope).

**Tests Added:**
- `test_removes_trailing_commas`: Verifies trailing comma removal in simple objects
- `test_removes_trailing_commas_in_nested`: Verifies trailing comma removal in nested structures with arrays

**Final Test Count:** 1812 passed, 96 skipped (2 new tests added during review)
