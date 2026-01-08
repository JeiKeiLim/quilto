# Story 1.3: Implement LLM Client Abstraction

Status: done

## Story

As a **Quilto developer**,
I want a **tiered LLM configuration that abstracts provider details**,
So that **applications can switch between Ollama and cloud providers without code changes**.

## Acceptance Criteria

1. **Given** a configuration with tiered models (low/medium/high)
   **When** I request an LLM call for an agent with an assigned tier
   **Then** the correct model is selected based on the agent's tier configuration

2. **Given** Ollama is configured as a provider
   **When** I make an LLM call using Ollama
   **Then** the `api_base` override is applied correctly
   **And** the model is prefixed with `ollama/` for litellm

3. **Given** a cloud provider (anthropic/openai/azure/openrouter) is configured
   **When** API keys are set via environment variables
   **Then** the provider credentials are resolved and used for LLM calls
   **And** fallback to another provider works on failure (if configured)

## Tasks / Subtasks

- [x] Task 1: Create LLM configuration models (AC: #1, #2, #3)
  - [x] 1.1 Create `packages/quilto/quilto/llm/` module directory
  - [x] 1.2 Create `packages/quilto/quilto/llm/config.py` with Pydantic models:
    - `ProviderConfig` - Provider-specific settings (api_key, api_base, api_version)
    - `TierModels` - Model mappings per tier (ollama, anthropic, openai, azure, openrouter)
    - `AgentConfig` - Per-agent tier and optional provider override
    - `LLMConfig` - Root config with default_provider, fallback_provider, providers, tiers, agents
    - `ModelResolution` - Dataclass returned by resolve_model (provider, model, litellm_model, api_base, api_key)
  - [x] 1.3 Support environment variable interpolation for API keys (e.g., `${ANTHROPIC_API_KEY}`)
  - [x] 1.4 Provide sensible defaults for tier models based on architecture spec

- [x] Task 2: Create LLMClient class (AC: #1, #2, #3)
  - [x] 2.1 Create `packages/quilto/quilto/llm/client.py` with `LLMClient` class
  - [x] 2.2 Implement `resolve_model(agent: str, force_cloud: bool = False) -> ModelResolution` method
    - Returns ModelResolution with provider, model, litellm_model, api_base, api_key
    - Applies correct litellm prefix per provider (ollama/, azure/, openrouter/, none for anthropic/openai)
    - Respects agent-specific provider override
    - Falls back to default_provider (or fallback_provider if force_cloud=True)
  - [x] 2.3 Implement `complete(agent: str, messages: list[dict], **kwargs) -> str` method
    - Uses litellm.acompletion with resolved model and credentials
    - Returns response content as string
  - [x] 2.4 Implement `complete_structured(agent: str, messages: list[dict], response_model: type[BaseModel], **kwargs) -> BaseModel` method
    - Calls complete with response_format={"type": "json_object"}
    - Parses and validates response with Pydantic model
  - [x] 2.5 Implement `complete_with_fallback(agent: str, messages: list[dict], **kwargs) -> str` method
    - Tries default provider first
    - Falls back to fallback_provider on error (if configured)

- [x] Task 3: Create configuration loader (AC: #3)
  - [x] 3.1 Create `packages/quilto/quilto/llm/loader.py`
  - [x] 3.2 Implement `load_llm_config(config_path: Path) -> LLMConfig`
    - Load from YAML file
    - Interpolate environment variables
    - Validate with Pydantic
  - [x] 3.3 Implement `load_llm_config_from_dict(config_dict: dict) -> LLMConfig`
    - For programmatic configuration

- [x] Task 4: Export LLM module from quilto package (AC: #1, #2, #3)
  - [x] 4.1 Create `packages/quilto/quilto/llm/__init__.py` exporting `LLMClient`, `LLMConfig`, `ModelResolution`, `load_llm_config`
  - [x] 4.2 Update `packages/quilto/quilto/__init__.py` to re-export LLM components
  - [x] 4.3 Ensure `from quilto import LLMClient, LLMConfig` works

- [x] Task 5: Write unit tests for LLM configuration (AC: #1, #3)
  - [x] 5.1 Create `packages/quilto/tests/test_llm_config.py`
  - [x] 5.2 Test: LLMConfig validates provider configurations correctly
  - [x] 5.3 Test: Tier models are properly defined for all providers
  - [x] 5.4 Test: AgentConfig tier/provider override works
  - [x] 5.5 Test: Environment variable interpolation works (mock os.environ)
  - [x] 5.6 Test: YAML config loading and validation

- [x] Task 6: Write unit tests for LLMClient (AC: #1, #2, #3)
  - [x] 6.1 Create `packages/quilto/tests/test_llm_client.py`
  - [x] 6.2 Test: `resolve_model` returns correct provider/model for each tier (AC: #1)
  - [x] 6.3 Test: `resolve_model` respects agent-specific provider override (AC: #1)
  - [x] 6.4 Test: `resolve_model` applies correct litellm prefix for Ollama (AC: #2)
  - [x] 6.5 Test: `resolve_model` uses fallback_provider when force_cloud=True (AC: #3)
  - [x] 6.6 Test: `complete` calls litellm with correct parameters (mock litellm)
  - [x] 6.7 Test: `complete_structured` parses JSON response into Pydantic model
  - [x] 6.8 Test: `complete_with_fallback` falls back on error (AC: #3)
  - [x] 6.9 Test: `complete_with_fallback` raises if no fallback configured

- [x] Task 7: Create mock_llm fixture for testing (AC: #1, #2, #3)
  - [x] 7.1 Create `packages/quilto/tests/conftest.py` (or extend existing)
  - [x] 7.2 Implement `mock_llm` fixture that patches litellm.acompletion
  - [x] 7.3 Support canned responses based on agent name
  - [x] 7.4 Document usage for downstream story tests

- [x] Task 8: Validate integration (AC: #1, #2, #3)
  - [x] 8.1 Run `uv run ruff check packages/quilto/`
  - [x] 8.2 Run `uv run pyright packages/quilto/`
  - [x] 8.3 Run `uv run pytest packages/quilto/tests/test_llm_*.py -v`

## Dev Notes

### Architecture Compliance

This story implements the LLM Client Abstraction defined in:
- `_bmad-output/planning-artifacts/agent-system-design.md` (Section 15)
- Architecture decision AR5: LiteLLM for unified LLM API
- Architecture decision AR6: Tiered model config (low/medium/high) per agent
- Non-functional requirement NFR-F6: LLM flexibility (local default, cloud option)

### LLMClient Interface Specification

From agent-system-design.md Section 15.3:

```python
class LLMClient:
    """Unified LLM client with provider abstraction."""

    def __init__(self, config: LLMConfig):
        self.config = config

    def resolve_model(self, agent: str, force_cloud: bool = False) -> ModelResolution:
        """Resolve provider and model for an agent."""
        agent_config = self.config.agents.get(agent, AgentConfig())

        if agent_config.provider:
            provider = agent_config.provider
        elif force_cloud:
            provider = self.config.fallback_provider
        else:
            provider = self.config.default_provider

        model = self.config.tiers[agent_config.tier][provider]
        return ModelResolution(provider=provider, model=model, ...)

    async def complete(
        self,
        agent: str,
        messages: list[dict],
        **kwargs,
    ) -> str:
        """Complete a chat request via litellm."""
        resolution = self.resolve_model(agent)
        response = await litellm.acompletion(
            model=resolution.litellm_model,
            messages=messages,
            api_base=resolution.api_base,
            api_key=resolution.api_key,
            **kwargs,
        )
        return response.choices[0].message.content

    async def complete_structured(
        self,
        agent: str,
        messages: list[dict],
        response_model: type[BaseModel],
        **kwargs,
    ) -> BaseModel:
        """Complete with Pydantic validation."""
        response = await self.complete(
            agent=agent,
            messages=messages,
            response_format={"type": "json_object"},
            **kwargs,
        )
        return response_model.model_validate_json(response)

    async def complete_with_fallback(
        self,
        agent: str,
        messages: list[dict],
        **kwargs,
    ) -> str:
        """Try default provider, fall back on failure."""
        try:
            return await self.complete(agent, messages, **kwargs)
        except Exception:
            if self.config.fallback_provider:
                return await self.complete(agent, messages, force_cloud=True, **kwargs)
            raise
```

### Configuration Structure

From agent-system-design.md Section 15.2:

```yaml
# config.yaml
llm:
  default_provider: "ollama"
  fallback_provider: "anthropic"  # Used on errors

  providers:
    ollama:
      api_base: "http://localhost:11434"

    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"

    openai:
      api_key: "${OPENAI_API_KEY}"

    azure:
      api_key: "${AZURE_OPENAI_API_KEY}"
      api_base: "https://your-resource.openai.azure.com/"
      api_version: "2024-06-01"

    openrouter:
      api_key: "${OPENROUTER_API_KEY}"
      api_base: "https://openrouter.ai/api/v1"

  tiers:
    low:
      ollama: "qwen2.5:7b"
      anthropic: "claude-3-haiku-20240307"
      openai: "gpt-4o-mini"
      azure: "gpt-4o-mini-deployment"
      openrouter: "anthropic/claude-3-haiku"

    medium:
      ollama: "qwen2.5:14b"
      anthropic: "claude-3-5-haiku-20241022"
      openai: "gpt-4o-mini"
      azure: "gpt-4o-mini-deployment"
      openrouter: "anthropic/claude-3.5-haiku"

    high:
      ollama: "qwen2.5:32b"
      anthropic: "claude-sonnet-4-20250514"
      openai: "gpt-4o"
      azure: "gpt-4o-deployment"
      openrouter: "anthropic/claude-sonnet-4-20250514"

  agents:
    router: { tier: "low" }
    retriever: { tier: "low" }
    parser: { tier: "medium" }
    clarifier: { tier: "medium" }
    planner: { tier: "high" }
    synthesizer: { tier: "medium" }
    evaluator: { tier: "high" }
    analyzer: { tier: "high" }
    observer: { tier: "medium" }

    # Override example:
    # evaluator: { tier: "high", provider: "anthropic" }
```

### Agent Tier Assignments

| Agent | Tier | Rationale |
|-------|------|-----------|
| router | low | Simple classification task |
| retriever | low | Straightforward retrieval |
| parser | medium | Structured extraction needs good reasoning |
| clarifier | medium | Question generation |
| planner | high | Complex query decomposition |
| synthesizer | medium | Response generation |
| evaluator | high | Quality judgment requires nuance |
| analyzer | high | Pattern recognition, sufficiency assessment |
| observer | medium | Pattern learning |

### LiteLLM Model Naming Convention

LiteLLM uses prefixed model names for different providers:
- Ollama: `ollama/<model>` (e.g., `ollama/qwen2.5:7b`)
- Anthropic: `<model>` (e.g., `claude-3-haiku-20240307`)
- OpenAI: `<model>` (e.g., `gpt-4o-mini`)
- Azure: `azure/<deployment>` (e.g., `azure/gpt-4o-mini-deployment`)
- OpenRouter: `openrouter/<provider>/<model>` (e.g., `openrouter/anthropic/claude-3-haiku`)

The `resolve_model` method should return a `litellm_model` field with the correctly prefixed model name.

### Environment Variable Interpolation

Config values like `${ANTHROPIC_API_KEY}` should be interpolated from environment variables at load time. If the env var is not set and the provider is used, raise a clear error.

### Implementation Notes

1. **Async Methods**: All completion methods should be async to support concurrent agent execution
2. **litellm Dependency**: Already in pyproject.toml from Story 1.1
3. **Error Handling**: Log errors clearly before fallback attempts
4. **Type Hints**: Use modern Python 3.13 type hints throughout
5. **Pydantic v2**: Use ConfigDict, field_validator as needed

### Project Structure After This Story

```
packages/quilto/
├── pyproject.toml
├── quilto/
│   ├── __init__.py      # Exports: __version__, DomainModule, LLMClient, LLMConfig
│   ├── py.typed
│   ├── domain.py        # From Story 1.2
│   └── llm/             # NEW
│       ├── __init__.py  # Exports: LLMClient, LLMConfig, load_llm_config
│       ├── config.py    # LLMConfig, ProviderConfig, TierModels, AgentConfig
│       ├── client.py    # LLMClient class
│       └── loader.py    # load_llm_config, load_llm_config_from_dict
└── tests/
    ├── __init__.py
    ├── conftest.py      # NEW/UPDATED: mock_llm fixture
    ├── test_domain.py   # From Story 1.2
    ├── test_llm_config.py  # NEW
    └── test_llm_client.py  # NEW
```

### Testing Strategy

1. **Configuration Tests** (test_llm_config.py):
   - Pydantic model validation
   - Default values
   - Environment variable interpolation
   - YAML loading

2. **Client Tests** (test_llm_client.py):
   - Model resolution logic (mock LLMConfig, no actual LLM calls)
   - Completion methods (mock litellm.acompletion)
   - Fallback behavior
   - Structured output parsing

3. **Integration Tests** (future stories):
   - Actual Ollama calls with `--use-real-ollama` flag
   - Covered in Story 1.7 test infrastructure

### Previous Story Context (1.2)

From Story 1.2 completion:
- `DomainModule` class implemented with Pydantic validation
- quilto package structure established
- Test patterns established (pytest, ruff, pyright)

### Technical Constraints

1. **Python 3.13+**: Use modern type hints (`list[str]` not `List[str]`)
2. **Pydantic 2.10+**: Use v2 API (`ConfigDict`, `field_validator`)
3. **litellm 1.50+**: Already in dependencies
4. **Google Docstrings**: Required for all public classes and methods
5. **Strict Pyright**: Must pass with 0 errors
6. **Async/Await**: Completion methods must be async

### Example Usage

```python
from quilto import LLMClient, LLMConfig, load_llm_config

# Load from YAML file
config = load_llm_config(Path("config.yaml"))
client = LLMClient(config)

# Simple completion
response = await client.complete(
    agent="analyzer",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Analyze this data..."},
    ],
)

# Structured completion
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    findings: list[str]
    verdict: str

result = await client.complete_structured(
    agent="analyzer",
    messages=[...],
    response_model=AnalysisResult,
)

# With fallback
response = await client.complete_with_fallback(
    agent="parser",
    messages=[...],
)
```

### References

- [Source: _bmad-output/planning-artifacts/agent-system-design.md#15. LLM Client Abstraction]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#15.2 Configuration Structure]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#15.3 Client Interface]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Stack]
- [LiteLLM Documentation - https://docs.litellm.ai/]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- ruff check: 0 errors after auto-fix
- pyright: 0 errors (type ignores for litellm library types)
- pytest: 78 tests passing (59 LLM tests + 19 existing tests) after code review fixes

### Completion Notes List

- Story created via YOLO mode create-story workflow
- This is story 3 of 7 in Epic 1 (Foundation & First Domain)
- Previous story 1.2 established DomainModule interface
- LLMClient enables all agent implementations (Stories 2.2, 2.3, etc.)
- Story 1.7 (test fixtures) depends on mock_llm fixture from this story
- Implemented tiered LLM config with 5 providers (ollama, anthropic, openai, azure, openrouter)
- Added DEFAULT_TIER_MODELS and DEFAULT_AGENT_CONFIGS for sensible defaults
- Created mock_llm, mock_llm_json, mock_llm_error fixtures for downstream testing
- All acceptance criteria satisfied with comprehensive test coverage

### Code Review Fixes (2026-01-08)

1. **Re-exported all LLM types from quilto/__init__.py** - Added AgentConfig, ProviderConfig, TierModels, load_llm_config_from_dict to top-level exports for API consistency
2. **Improved mock_llm fixture documentation and matching** - Clarified that matching is based on model name patterns, added exact match priority and improved docstrings
3. **Added graceful error handling for complete_structured** - Now logs error details and wraps exceptions in ValueError with schema context
4. **Improved resolve_model error messages** - Error messages now include available tiers and configured providers for the tier
5. **Added validation for fallback_provider** - LLMConfig now validates that fallback_provider is configured in providers at load time
6. **Added 3 new tests** - test_rejects_unconfigured_fallback_provider, test_raises_on_invalid_json, test_raises_on_schema_mismatch

### File List

Files created:
- `packages/quilto/quilto/llm/__init__.py`
- `packages/quilto/quilto/llm/config.py`
- `packages/quilto/quilto/llm/client.py`
- `packages/quilto/quilto/llm/loader.py`
- `packages/quilto/tests/test_llm_config.py`
- `packages/quilto/tests/test_llm_client.py`
- `packages/quilto/tests/conftest.py`

Files modified:
- `packages/quilto/quilto/__init__.py`

## Change Log

- 2026-01-08: Implemented LLM Client Abstraction (Story 1.3) - All tasks complete
