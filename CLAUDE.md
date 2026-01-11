# CLAUDE.md - Project Context for AI Agents

## Project Identity (CRITICAL)

This workspace contains **TWO packages** - do not conflate them:

| Package | Type | Location | Purpose |
|---------|------|----------|---------|
| **Quilto** | Framework | `packages/quilto/` | Domain-agnostic agent framework |
| **Swealog** | Application | `packages/swealog/` | Fitness app built on Quilto |

**Quilto** is the framework. **Swealog** is just one application.

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

### Common Mistakes

| Wrong | Right |
|-------|-------|
| "Swealog Parser" | "Quilto Parser agent" |
| "Swealog framework" | "Quilto framework" |
| Fitness-only test data | Multi-domain test data |

---

## Development Workflow

### Validate Frequently

Use `make` commands for consistent validation:

```bash
# Quick validation (run often during development)
make check        # lint + typecheck

# Full validation (before commits)
make validate     # lint + format + typecheck + test

# Test with real Ollama (requires running Ollama instance)
make test-ollama
```

Run `make help` to see all available commands.

### Testing Rules (MANDATORY)

1. **Unit tests**: Run `make validate` during development
2. **Integration tests**: Run `make test-ollama` at END of implementation AND during code review
   - Requires Ollama running locally (`ollama serve`)
   - Tests actual LLM behavior, not mocks
   - **Must pass before story is complete**

```bash
# Development cycle
make check          # Quick: lint + typecheck
make validate       # Full: lint + format + typecheck + unit tests

# Before marking story done (REQUIRED)
make test-ollama    # Integration tests with real Ollama

# Code review (REQUIRED)
make test-ollama    # Must run and pass during code review
```

### Pre-Review Checklist

Before requesting code review:
- [ ] `make check` passes (lint + typecheck)
- [ ] `make test-ollama` passes (integration tests)
- [ ] All new functions have Google-style docstrings
- [ ] All new classes exported in `__init__.py`
- [ ] Unit tests cover new functionality
- [ ] `py.typed` marker exists for typed packages

### Code Review Checklist

During code review (before marking story done):
- [ ] `make validate` passes
- [ ] `make test-ollama` passes (REQUIRED - verifies real LLM behavior)
- [ ] All acceptance criteria verified against implementation
- [ ] File list in story matches actual changed files

---

## Key Documents

| Document | Purpose |
|----------|---------|
| `_bmad-output/planning-artifacts/project-identity.md` | Full Quilto vs Swealog clarification |
| `_bmad-output/planning-artifacts/dev-workflow.md` | Complete development workflow |
| `_bmad-output/planning-artifacts/epics.md` | Epic and story definitions |
| `_bmad-output/planning-artifacts/architecture.md` | Architecture decisions |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Current sprint status |

---

## Technical Stack

- **Python:** 3.13+
- **Package Manager:** uv (workspace monorepo)
- **Linting:** ruff (formatting + linting)
- **Type Checking:** pyright (strict mode)
- **Testing:** pytest + pytest-asyncio
- **LLM Client:** litellm (supports Ollama + cloud providers)
- **Validation:** Pydantic v2

---

## Repository Structure

```
swealog-workspace/
├── packages/
│   ├── quilto/                 # FRAMEWORK (domain-agnostic)
│   │   ├── quilto/
│   │   │   ├── domain.py       # DomainModule interface
│   │   │   ├── llm/            # LLM client abstraction
│   │   │   └── ...
│   │   └── tests/
│   │
│   └── swealog/                # APPLICATION (fitness-specific)
│       ├── swealog/
│       │   └── domains/        # Fitness domains ONLY
│       └── tests/
│
├── tests/                      # Integration tests + corpus
│   └── corpus/                 # Test data (multi-domain!)
│
└── _bmad-output/               # Planning and implementation artifacts
    ├── planning-artifacts/
    └── implementation-artifacts/
```
