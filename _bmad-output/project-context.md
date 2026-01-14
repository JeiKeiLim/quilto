---
project_name: 'swealog-workspace'
framework_name: 'quilto'
application_name: 'swealog'
user_name: 'Jongkuk Lim'
date: '2026-01-14'
sections_completed: ['project_identity', 'directory_conventions', 'development_workflow', 'dual_llm_support']
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Project Identity (CRITICAL)

This workspace contains **TWO packages** - do not conflate them:

| Package | Type | Location | Purpose |
|---------|------|----------|---------|
| **Quilto** | Framework | `packages/quilto/` | Domain-agnostic agent framework |
| **Swealog** | Application | `packages/swealog/` | Fitness app built on Quilto |

### Where Code Belongs

**QUILTO** (`packages/quilto/`) - Most code goes here:
- All agents (Router, Parser, Planner, Retriever, etc.)
- LLM client abstraction (`quilto/llm/`)
- Storage interface (`quilto/storage/`)
- DomainModule base class (`quilto/domain.py`)
- Any domain-agnostic functionality

**SWEALOG** (`packages/swealog/`) - Only fitness-specific:
- Fitness domain modules (`swealog/domains/`)
- Fitness schemas (GeneralFitnessEntry, etc.)
- Fitness vocabulary and expertise

**Test rule:** Ask "Would this work for a cooking app?" If NO, it doesn't belong in Quilto.

### Terminology

| Term | Meaning |
|------|---------|
| **Quilto** | The open-source, domain-agnostic framework |
| **Swealog** | The fitness application built on Quilto |
| **Quiltr** | Reserved name for potential future SaaS product |

### Common Mistakes to Avoid

| Wrong | Right |
|-------|-------|
| "Swealog Parser" | "Quilto Parser agent" |
| "Swealog framework" | "Quilto framework" |
| Fitness-only test data | Multi-domain test data |

---

## Directory Conventions

### Implementation Artifacts Structure

Story files and retrospectives are organized by epic:

```
_bmad-output/implementation-artifacts/
├── sprint-status.yaml              # Root level - tracks all epics
│
├── epic-1/                         # Epic 1: Foundation & First Domain
│   ├── 1-1-initialize-monorepo-structure.md
│   ├── 1-2-define-domainmodule-interface.md
│   ├── ...
│   └── retro-YYYY-MM-DD.md
│
├── epic-1.5/                       # Epic 1.5: Test Corpus
│   ├── 1.5-1-create-generic-edge-case-test-entries.md
│   ├── ...
│   └── retro-YYYY-MM-DD.md
│
├── epic-2/                         # Epic 2: Input & Storage
│   ├── 2-1-implement-storagerepository-interface.md
│   ├── ...
│   └── retro-YYYY-MM-DD.md
│
└── ...                             # Future epics follow same pattern
```

### Story File Naming Convention

**Pattern:** `{epic}-{story}-{slug}.md`

Examples:
- `1-1-initialize-monorepo-structure.md`
- `1.5-3-create-multi-domain-test-entries.md`
- `2-1-implement-storagerepository-interface.md`

### Retrospective File Naming Convention

**Pattern:** `retro-YYYY-MM-DD.md`

Location: Inside the epic directory it reviews.

### When Creating Stories

1. Determine the epic number from `sprint-status.yaml`
2. Create/verify the epic directory exists: `epic-{N}/`
3. Create story file inside that directory
4. Use the correct naming pattern

---

## Development Workflow

### Validate Frequently

Run these commands **constantly during development**, not just before review:

```bash
# Quick validation (run often)
uv run ruff check . --fix && uv run pyright

# Full validation (before commits)
uv run ruff check . && uv run ruff format . && uv run pyright && uv run pytest
```

### Pre-Review Checklist

Before requesting code review:
- [ ] `uv run ruff check .` passes
- [ ] `uv run pyright` passes (0 errors)
- [ ] All new functions have Google-style docstrings
- [ ] All new classes exported in `__init__.py`
- [ ] Unit tests cover new functionality
- [ ] `py.typed` marker exists for typed packages

---

## Technology Stack & Versions

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.13+ | Runtime |
| uv | latest | Package manager (workspace monorepo) |
| ruff | latest | Linting + formatting |
| pyright | strict mode | Type checking |
| pytest | 8.0+ | Testing |
| pytest-asyncio | 0.24+ | Async test support |
| litellm | latest | LLM client (Ollama + cloud) |
| Pydantic | 2.10+ | Validation |
| LangGraph | latest | Agent orchestration |

### Design Principle: Dual LLM Support

Quilto intentionally supports **both local and cloud LLM providers**. This is a feature, not a limitation.

| Mode | Provider | Trade-offs |
|------|----------|------------|
| **Local** | Ollama (qwen2.5:3b, 7b, etc.) | Privacy, no API costs, offline capability, lower quality |
| **Cloud** | OpenAI, Anthropic, etc. | Higher quality, larger context, requires API keys, costs money |

**Users choose based on their priorities:**
- Privacy-conscious users run everything locally
- Quality-focused users pay for cloud APIs
- Cost-sensitive users use local for development, cloud for production

The tiered model config (low/medium/high) in `llm-config.yaml` allows fine-grained control per agent.

---

## Critical Implementation Rules

### Code Style

- **Docstrings:** Google-style, required for all public functions/classes
- **Type hints:** Complete annotations, pyright strict mode
- **Imports:** Sorted by ruff (isort rules)

### Pydantic Patterns

- Use `ConfigDict(strict=True)` for models
- Use `field_validator` for custom validation
- Use modern type hints (`list[str]` not `List[str]`)

### Test Patterns

- Use `pytest.mark.asyncio` for async tests
- Use fixtures from `tests/conftest.py`
- Test corpus should include multiple domains (not just fitness)

### Common Mistakes to Avoid (Learned from Epic 1-2)

These mistakes recurred across multiple stories. Proactively check for them:

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Required string field without length check | `name: str = Field(min_length=1)` | Story 2-4 |
| Redundant `@field_validator` for range | Use `Field(ge=0, le=10)` instead | Story 2-4 |
| Missing boundary value tests | Always test exact boundaries (0.0, 1.0, 10.0) | Story 2-1, 2-2 |
| Missing `py.typed` marker | Add `py.typed` file in package root for PEP 561 | Story 2-2 |
| Empty string not tested separately from None | Test both `None` and `""` cases | Story 2-2 |
| Missing `__all__` in `__init__.py` | Export all public classes in `__all__` list | Story 1.5-8 |
| Both `Field()` AND `@field_validator` | Use only `Field(ge=, le=)` for range validation | Story 2-4 |

### Pre-Review Validation Checklist

Before requesting code review, verify:

- [ ] All required string fields use `Field(min_length=1)`
- [ ] Range validation uses `Field(ge=, le=)` not redundant validators
- [ ] Boundary value tests exist (test exact 0, 1, 10, etc.)
- [ ] `py.typed` marker exists in new typed packages
- [ ] All public classes are in `__all__`
- [ ] Tests cover both `None` and `""` for optional string fields
- [ ] `make test-ollama` passes (integration tests with real Ollama)

---

## Key Documents

| Document | Purpose |
|----------|---------|
| `_bmad-output/planning-artifacts/epics.md` | Epic and story definitions |
| `_bmad-output/planning-artifacts/architecture.md` | Architecture decisions |
| `_bmad-output/planning-artifacts/dev-workflow.md` | Complete development workflow |
| `_bmad-output/planning-artifacts/project-identity.md` | Detailed Quilto vs Swealog reference |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Current sprint status |
| `/CLAUDE.md` | Claude Code specific context |
