# Story 24.3: Unified Config Loading

Status: done

## Story

As a **Quilto developer**,
I want **unified configuration**,
so that **LLM and observability settings are in one place**.

## Acceptance Criteria

1. **Given** new `quilto/config.py`
   **When** `load_config()` called
   **Then** loads both LLM and observability settings

2. **Given** config file structure
   **When** parsed
   **Then** supports:
   ```yaml
   llm:
     default_provider: ollama
     # ... existing LLM config
   observability:
     enabled: true
     provider: langfuse
     sample_rate: 1.0
   ```

3. **Given** environment variables
   **When** present
   **Then** `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` are used

4. **Given** `observability.enabled: false` or missing section
   **When** config loaded
   **Then** NoOpProvider is used (graceful degradation)

5. **Given** backward compatibility
   **When** old `llm.yaml` exists without observability
   **Then** config loads successfully with observability disabled

## Tasks / Subtasks

- [x] Task 1: Create unified config models (AC: #1, #2)
  - [x] Create `packages/quilto/quilto/config.py`
  - [x] Define `ObservabilityConfig` Pydantic model with fields: `enabled`, `provider`, `sample_rate`, `public_key`, `secret_key`, `host`
  - [x] Define `QuiltoConfig` Pydantic model with `llm: LLMConfig` and `observability: ObservabilityConfig`
  - [x] Set sensible defaults: `enabled=False`, `provider="langfuse"`, `sample_rate=1.0`

- [x] Task 2: Implement load_config function (AC: #1, #3, #5)
  - [x] Implement `load_config(config_path: Path) -> QuiltoConfig` function
  - [x] Handle nested `llm:` key (existing format) and new unified format
  - [x] Read environment variables for Langfuse credentials: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` (note: architecture says `LANGFUSE_HOST` but implementation uses `LANGFUSE_BASE_URL`)
  - [x] Environment variables override config file values (if both present)
  - [x] Handle missing observability section gracefully (default to disabled)

- [x] Task 3: Implement load_config_from_dict function (AC: #1)
  - [x] Implement `load_config_from_dict(config_dict: dict) -> QuiltoConfig` for programmatic config
  - [x] Reuse same parsing logic as load_config

- [x] Task 4: Implement create_observability_provider helper (AC: #4)
  - [x] Create helper function `create_observability_provider(config: ObservabilityConfig) -> ObservabilityProvider`
  - [x] If `enabled=False` or credentials missing, return `NoOpProvider()`
  - [x] If `enabled=True` with valid credentials, return `LangfuseProvider(...)`
  - [x] Log warning if enabled but credentials missing (then return NoOpProvider)

- [x] Task 5: Write unit tests
  - [x] Test: load_config() parses YAML correctly with both llm and observability sections
  - [x] Test: Missing observability section returns disabled config (`enabled=False`)
  - [x] Test: Environment variables override config file values
  - [x] Test: Invalid config file raises clear error (ValidationError)
  - [x] Test: Old LLM-only config works (backward compatibility)
  - [x] Test: create_observability_provider returns NoOpProvider when disabled
  - [x] Test: create_observability_provider returns LangfuseProvider when enabled with credentials

- [x] Task 6: Export from quilto package
  - [x] Update `packages/quilto/quilto/__init__.py` to export `QuiltoConfig`, `ObservabilityConfig`, `load_config`, `load_config_from_dict`, `create_observability_provider`
  - [x] Keep existing `load_llm_config` exports for backward compatibility

## Dev Notes

### Architecture Compliance

**Location:** `quilto/config.py` (top-level, as specified in architecture)

**Source:** [_bmad-output/planning-artifacts/architecture.md#Quilto Package Structure]
```
quilto/
├── config.py         # Unified config loading (LLM + observability)
```

### Story 24.1 and 24.2 Established Patterns

From previous Epic 24 stories, these patterns are established:

1. **Import Style:**
   ```python
   from collections.abc import Generator
   from typing import Any
   from pydantic import BaseModel, ConfigDict, field_validator
   ```

2. **Pydantic Model Pattern:**
   ```python
   class MyModel(BaseModel):
       model_config = ConfigDict(extra="forbid")
       field: str
   ```

3. **Docstring Style:** Google-style with Args/Returns sections

4. **Provider Creation:** `LangfuseProvider` accepts `public_key`, `secret_key`, `host` params and falls back to env vars

### Existing LLM Config Pattern (quilto/llm/loader.py)

The existing `load_llm_config` function handles:
- YAML loading with `yaml.safe_load`
- Nested `llm:` key detection
- Env var interpolation via `interpolate_env_vars` in ProviderConfig

**Reuse this pattern** - do not create conflicting approaches.

### Config File Structure

**New unified format (recommended):**
```yaml
llm:
  default_provider: ollama
  providers:
    ollama:
      api_base: "http://localhost:11434"
      timeout: 120.0
  tiers:
    low:
      ollama: "qwen2.5:7b"
  agents:
    router:
      tier: low

observability:
  enabled: true
  provider: langfuse  # Only "langfuse" or "noop" supported MVP
  sample_rate: 1.0
  # Credentials from env vars: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
```

**Old format (backward compatible - observability disabled):**
```yaml
default_provider: ollama
providers:
  ollama:
    api_base: "http://localhost:11434"
```

### Environment Variable Precedence

1. Explicit constructor params (highest)
2. Environment variables
3. Config file values
4. Defaults (lowest)

**Environment variables for Langfuse:**
- `LANGFUSE_PUBLIC_KEY` - Required for Langfuse
- `LANGFUSE_SECRET_KEY` - Required for Langfuse
- `LANGFUSE_BASE_URL` - Optional, defaults to `https://cloud.langfuse.com`

Note: Architecture says `LANGFUSE_HOST` but LangfuseProvider implementation (Story 24.2) uses `LANGFUSE_BASE_URL`. Use `LANGFUSE_BASE_URL` for consistency with implementation.

### Implementation Constraints

1. **Do NOT modify existing LLM config loading** - `load_llm_config` must continue working
2. **New `load_config` is additive** - Provides unified loading but doesn't replace existing
3. **Graceful degradation is mandatory** - Missing/invalid observability MUST NOT crash the app
4. **No circular imports** - config.py imports from llm/config.py and observability/, not vice versa

### Model Definitions

```python
# quilto/config.py
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator
from quilto.llm.config import LLMConfig

ObservabilityProviderName = Literal["langfuse", "noop"]

class ObservabilityConfig(BaseModel):
    """Observability configuration.

    Attributes:
        enabled: Whether observability is active. Defaults to False.
        provider: Observability backend. Currently only "langfuse" supported.
        sample_rate: Trace sampling rate (0.0-1.0). Defaults to 1.0 (100%).
        public_key: Langfuse public key. Falls back to LANGFUSE_PUBLIC_KEY env var.
        secret_key: Langfuse secret key. Falls back to LANGFUSE_SECRET_KEY env var.
        host: Langfuse host URL. Falls back to LANGFUSE_BASE_URL env var.
    """
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    provider: ObservabilityProviderName = "langfuse"
    sample_rate: float = 1.0
    public_key: str | None = None
    secret_key: str | None = None
    host: str | None = None

    @field_validator("sample_rate")
    @classmethod
    def validate_sample_rate(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("sample_rate must be between 0.0 and 1.0")
        return v


class QuiltoConfig(BaseModel):
    """Unified Quilto configuration.

    Combines LLM and observability settings in one config object.

    Attributes:
        llm: LLM provider configuration.
        observability: Observability provider configuration.
    """
    model_config = ConfigDict(extra="forbid")

    llm: LLMConfig = LLMConfig()
    observability: ObservabilityConfig = ObservabilityConfig()
```

### Project Structure Notes

**Files to Create:**
```
packages/quilto/quilto/config.py          # NEW - Unified config
packages/quilto/tests/test_config.py      # NEW - Unit tests
```

**Files to Modify:**
```
packages/quilto/quilto/__init__.py        # Add exports
```

**Do NOT Modify:**
```
packages/quilto/quilto/llm/config.py      # Keep existing
packages/quilto/quilto/llm/loader.py      # Keep existing
```

### Testing Requirements

**Location:** `packages/quilto/tests/test_config.py`

**Test Fixtures:**
```python
@pytest.fixture
def sample_unified_config_yaml(tmp_path: Path) -> Path:
    """Create sample unified config file."""
    config_content = """
llm:
  default_provider: ollama
  providers:
    ollama:
      api_base: "http://localhost:11434"
observability:
  enabled: true
  provider: langfuse
  sample_rate: 0.5
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return config_file
```

**Required Tests:**
1. `test_load_config_parses_unified_format()` - Both llm and observability parsed
2. `test_load_config_missing_observability_defaults_to_disabled()` - Graceful handling
3. `test_load_config_env_vars_override_file()` - Env var precedence
4. `test_load_config_invalid_raises_validation_error()` - Clear errors
5. `test_load_config_backward_compatible_llm_only()` - Old format works
6. `test_create_observability_provider_disabled_returns_noop()` - NoOpProvider when disabled
7. `test_create_observability_provider_enabled_returns_langfuse()` - LangfuseProvider when enabled
8. `test_create_observability_provider_missing_credentials_returns_noop()` - Graceful degradation
9. `test_observability_config_sample_rate_validation()` - Must be 0.0-1.0

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Quilto Package Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#LLM Observability]
- [Source: _bmad-output/planning-artifacts/prd-quilto.md#FR59-FR63, NFR9]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 24.3]
- [Source: packages/quilto/quilto/llm/config.py - LLMConfig model]
- [Source: packages/quilto/quilto/llm/loader.py - load_llm_config pattern]
- [Source: packages/quilto/quilto/observability/langfuse.py - LangfuseProvider]
- [Source: packages/quilto/quilto/observability/noop.py - NoOpProvider]
- [Source: Story 24.1 - Protocol patterns]
- [Source: Story 24.2 - LangfuseProvider implementation]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug issues encountered.

### Completion Notes List

- Created `quilto/config.py` with unified configuration loading for LLM and observability settings
- Implemented `ObservabilityConfig` Pydantic model with: `enabled`, `provider`, `sample_rate`, `public_key`, `secret_key`, `host`
- Implemented `QuiltoConfig` Pydantic model combining `LLMConfig` and `ObservabilityConfig`
- Implemented `load_config(path)` and `load_config_from_dict(dict)` functions
- Backward compatibility: Old LLM-only config format auto-detected and works with observability disabled
- Environment variable override: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` override config file values
- Implemented `create_observability_provider()` helper with graceful degradation (returns NoOpProvider when disabled or credentials missing)
- Added 23 unit tests covering all acceptance criteria
- Exported all new symbols from `quilto/__init__.py`
- All 1458 tests pass, 0 regressions

### Change Log

- 2026-01-30: Story 24.3 implementation complete - unified config loading with graceful degradation
- 2026-01-30: Code review PASSED - 4 issues found and fixed:
  - MEDIUM-1: Added test_langfuse_unit.py to File List (formatting-only change)
  - MEDIUM-2: Added clarifying comment for intentional dual env var lookup
  - MEDIUM-4: Exported ObservabilityProviderName type alias from quilto package
  - LOW-3: Added empty YAML file handling + test

### File List

- packages/quilto/quilto/config.py (NEW)
- packages/quilto/tests/test_config.py (NEW)
- packages/quilto/quilto/__init__.py (MODIFIED)
- packages/quilto/tests/observability/test_langfuse_unit.py (MODIFIED - formatting only)

