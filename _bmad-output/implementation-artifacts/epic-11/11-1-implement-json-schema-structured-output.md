# Story 11.1: Implement JSON Schema Structured Output

## Status: ready-for-dev

## Context

The current `LLMClient.complete_structured()` uses basic JSON mode:
```python
response_format={"type": "json_object"}
```

This is insufficient for OpenRouter and some providers that require full JSON schema:
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

1. **AC1:** `complete_structured()` uses `response_format.type = "json_schema"` with full schema
2. **AC2:** Schema is auto-generated from Pydantic model via `model.model_json_schema()`
3. **AC3:** Backward compatible - works with providers that only support `json_object`
4. **AC4:** Provider-specific handling if needed (detect provider, use appropriate format)
5. **AC5:** Fallback JSON extraction for malformed responses (strip markdown, comments)
6. **AC6:** All existing tests pass, new tests for JSON schema mode
7. **AC7:** `make test-ollama` passes

## Technical Design

### 1. Update `complete_structured()` signature

```python
async def complete_structured(
    self,
    agent: str,
    messages: list[dict[str, Any]],
    response_model: type[BaseModel],
    force_cloud: bool = False,
    strict_schema: bool = True,  # New param
    **kwargs: Any,
) -> BaseModel:
```

### 2. Build proper response_format

```python
def _build_response_format(
    self,
    response_model: type[BaseModel],
    provider: ProviderName,
    strict: bool = True
) -> dict[str, Any]:
    """Build provider-appropriate response_format."""
    schema = response_model.model_json_schema()

    # OpenRouter, OpenAI support full json_schema
    if provider in ("openrouter", "openai", "anthropic"):
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

### 3. Add JSON extraction fallback

```python
def _extract_json(self, response: str) -> str:
    """Extract JSON from potentially malformed LLM response."""
    # Strip markdown code blocks
    if "```json" in response:
        response = response.split("```json")[1].split("```")[0]
    elif "```" in response:
        response = response.split("```")[1].split("```")[0]

    # Remove single-line comments
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

### 4. Update complete_structured flow

```python
async def complete_structured(...) -> BaseModel:
    resolution = self.resolve_model(agent, force_cloud)
    response_format = self._build_response_format(
        response_model, resolution.provider, strict=strict_schema
    )

    response = await self.complete(
        agent=agent,
        messages=messages,
        force_cloud=force_cloud,
        response_format=response_format,
        **kwargs,
    )

    try:
        return response_model.model_validate_json(response)
    except Exception:
        # Fallback: try extracting JSON
        cleaned = self._extract_json(response)
        try:
            return response_model.model_validate_json(cleaned)
        except Exception as e:
            logger.error(...)
            raise ValueError(...) from e
```

## Tasks

- [ ] **Task 1:** Add `_build_response_format()` helper method
  - [ ] 1.1: Implement provider detection logic
  - [ ] 1.2: Generate JSON schema from Pydantic model
  - [ ] 1.3: Return appropriate format per provider

- [ ] **Task 2:** Add `_extract_json()` fallback helper
  - [ ] 2.1: Strip markdown code blocks
  - [ ] 2.2: Remove comments (// and /* */)
  - [ ] 2.3: Find JSON object boundaries
  - [ ] 2.4: Unit tests for extraction edge cases

- [ ] **Task 3:** Update `complete_structured()` method
  - [ ] 3.1: Use new `_build_response_format()`
  - [ ] 3.2: Add fallback to `_extract_json()` on parse failure
  - [ ] 3.3: Add `strict_schema` parameter

- [ ] **Task 4:** Update `complete_structured_with_cascade()`
  - [ ] 4.1: Same changes as Task 3 for cascade method
  - [ ] 4.2: Ensure retry logic works with new format

- [ ] **Task 5:** Add tests
  - [ ] 5.1: Unit tests for `_build_response_format()` per provider
  - [ ] 5.2: Unit tests for `_extract_json()` edge cases
  - [ ] 5.3: Integration test with OpenRouter (if available)
  - [ ] 5.4: Verify all existing tests pass

- [ ] **Task 6:** Validate
  - [ ] 6.1: `make check` passes
  - [ ] 6.2: `make validate` passes
  - [ ] 6.3: `make test-ollama` passes

## File List

| File | Action | Purpose |
|------|--------|---------|
| `packages/quilto/quilto/llm/client.py` | Modify | Add JSON schema support |
| `packages/quilto/tests/test_llm_client.py` | Modify | Add new tests |

## Out of Scope

- Changing Pydantic model schemas for flexibility
- Implementing instructor or outlines library integration
- Provider-specific retry strategies

## Dev Agent Record

_To be filled during implementation_

## Completion Notes

_To be filled upon completion_
