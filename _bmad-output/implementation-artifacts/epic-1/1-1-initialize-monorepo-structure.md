# Story 1.1: Initialize Monorepo Structure

Status: done

## Story

As a **Quilto and Swealog developer**,
I want a **properly configured uv workspace with quilto and swealog packages**,
So that **I can develop both packages with shared tooling**.

## Acceptance Criteria

1. **Given** a fresh clone of the repository
   **When** I run `uv sync`
   **Then** both `quilto` and `swealog` packages are installed in development mode
   **And** `swealog` can import from `quilto`
   **And** ruff, pyright, and pytest are configured at workspace level

## Tasks / Subtasks

- [x] Task 1: Create workspace root pyproject.toml (AC: #1)
  - [x] 1.1 Create `pyproject.toml` at repository root with `[tool.uv.workspace]` configuration
  - [x] 1.2 Set `members = ["packages/*"]` to include all packages
  - [x] 1.3 Configure Python version `requires-python = ">=3.13"`
  - [x] 1.4 Add workspace-level dev dependencies: ruff, pyright, pytest, pytest-asyncio

- [x] Task 2: Create quilto package structure (AC: #1)
  - [x] 2.1 Create `packages/quilto/pyproject.toml` with package metadata
  - [x] 2.2 Create `packages/quilto/quilto/__init__.py` with version
  - [x] 2.3 Add quilto core dependencies: litellm, pydantic, langgraph
  - [x] 2.4 Ensure flat layout with `quilto/` source directory

- [x] Task 3: Create swealog package structure (AC: #1)
  - [x] 3.1 Create `packages/swealog/pyproject.toml` with package metadata
  - [x] 3.2 Create `packages/swealog/swealog/__init__.py` with version
  - [x] 3.3 Add quilto as workspace dependency using `{ workspace = true }`
  - [x] 3.4 Add swealog-specific dependencies: typer, rich

- [x] Task 4: Configure shared dev tooling (AC: #1)
  - [x] 4.1 Configure ruff in root pyproject.toml with lint rules ["E", "F", "W", "I", "D", "UP", "B", "SIM"]
  - [x] 4.2 Configure ruff pydocstyle with Google convention
  - [x] 4.3 Configure pyright in strict mode via pyrightconfig.json or pyproject.toml
  - [x] 4.4 Configure pytest with asyncio mode in pyproject.toml

- [x] Task 5: Validate workspace setup (AC: #1)
  - [x] 5.1 Run `uv sync` and verify no errors
  - [x] 5.2 Verify `uv run python -c "from quilto import __version__; print(__version__)"` works
  - [x] 5.3 Verify `uv run python -c "from swealog import __version__; print(__version__)"` works
  - [x] 5.4 Verify swealog can import quilto: `uv run python -c "import swealog; from quilto import __version__"`
  - [x] 5.5 Run `uv run ruff check .` and verify it runs (may have warnings on empty modules)
  - [x] 5.6 Run `uv run pyright` and verify it runs
  - [x] 5.7 Run `uv run pytest --collect-only` and verify pytest discovers test directories

## Dev Notes

### Architecture Compliance

This story implements architecture decisions from `_bmad-output/planning-artifacts/architecture.md`:

- **AR3**: uv workspace monorepo with two packages
- **Package Manager**: uv (fast, modern, handles packages + venvs)
- **Python Version**: 3.13 (latest stable)
- **Layout**: Flat layout (`quilto/`, `swealog/`) for clean imports

### Technical Stack Requirements

| Tool | Version/Config | Purpose |
|------|----------------|---------|
| uv | Latest | Package management, workspace |
| Python | >=3.13 | Runtime |
| ruff | Latest | Linting + formatting (replaces black, isort, flake8) |
| pyright | Strict mode | Type checking |
| pytest | + pytest-asyncio | Testing |

### Project Structure

```
swealog/                          # Repository root (workspace root)
├── pyproject.toml                # Workspace configuration
├── uv.lock                       # Shared lockfile (generated)
├── pyrightconfig.json            # Optional: pyright config
├── packages/
│   ├── quilto/                   # Generic agent framework
│   │   ├── pyproject.toml        # Package metadata
│   │   └── quilto/
│   │       └── __init__.py
│   └── swealog/                  # Fitness application
│       ├── pyproject.toml
│       └── swealog/
│           └── __init__.py
├── tests/                        # Existing test directory
│   ├── corpus/                   # Test corpus (exists)
│   └── fixtures/                 # Test fixtures (exists)
└── _bmad-output/                 # Planning artifacts (exists)
```

### Root pyproject.toml Template

```toml
[project]
name = "swealog-workspace"
version = "0.1.0"
description = "Swealog workspace root - agent framework + fitness app"
requires-python = ">=3.13"
readme = "README.md"

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
quilto = { workspace = true }
swealog = { workspace = true }

[dependency-groups]
dev = [
    "ruff>=0.8.0",
    "pyright>=1.1.390",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]

[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "D", "UP", "B", "SIM"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests", "packages/quilto/tests", "packages/swealog/tests"]
```

### quilto Package pyproject.toml Template

```toml
[project]
name = "quilto"
version = "0.1.0"
description = "Domain-agnostic agent framework for note processing"
requires-python = ">=3.13"
dependencies = [
    "litellm>=1.50.0",
    "pydantic>=2.10.0",
    "langgraph>=0.2.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["quilto"]
```

### swealog Package pyproject.toml Template

```toml
[project]
name = "swealog"
version = "0.1.0"
description = "Fitness logging application powered by Quilto framework"
requires-python = ">=3.13"
dependencies = [
    "quilto",
    "typer>=0.15.0",
    "rich>=13.9.0",
]

[tool.uv.sources]
quilto = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["swealog"]
```

### Naming Convention

- **Quilto** - The open-source framework (generic, domain-agnostic)
- **Swealog** - The fitness application (uses Quilto)
- **Quiltr** - Future SaaS product name (reserved, not implemented in MVP)

### Library Versions (Latest Stable as of 2026-01)

| Library | Version | Notes |
|---------|---------|-------|
| litellm | >=1.50.0 | Unified LLM API, Ollama + cloud providers |
| pydantic | >=2.10.0 | Validation, schema generation |
| langgraph | >=0.2.0 | Agent orchestration (use core only, avoid langchain extras) |
| typer | >=0.15.0 | CLI framework |
| rich | >=13.9.0 | Beautiful terminal output |

### Docstring Policy

From architecture: "Required for all functions, classes, and methods including private. Variable docstrings where necessary."

Use Google convention for docstrings.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Stack]
- [Source: _bmad-output/planning-artifacts/architecture.md#Repository Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#Linting & Formatting]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1]
- [Source: uv workspace docs - https://docs.astral.sh/uv/concepts/projects/workspaces/]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

- Story created via YOLO mode create-story workflow
- This is the first story in Epic 1 (Foundation & First Domain)
- No previous story context available (this is story 1.1)
- Existing tests/ directory with corpus/ and fixtures/ subdirectories detected

#### Implementation Notes (2026-01-08)

- Created uv workspace with `members = ["packages/*"]`
- Both packages (quilto, swealog) install successfully via `uv sync --all-packages`
- swealog correctly imports quilto as workspace dependency
- All dev tools (ruff, pyright, pytest) configured and passing
- Validation results:
  - `uv sync`: ✅ Installed 80 packages
  - `quilto import`: ✅ Returns 0.1.0
  - `swealog import`: ✅ Returns 0.1.0
  - `swealog imports quilto`: ✅ Confirmed
  - `ruff check .`: ✅ All checks passed
  - `pyright`: ✅ 0 errors, 0 warnings
  - `pytest --collect-only`: ✅ Runs (0 tests as expected - no test files yet)

### File List

Files created:
- `pyproject.toml` (workspace root)
- `packages/quilto/pyproject.toml`
- `packages/quilto/quilto/__init__.py`
- `packages/quilto/quilto/py.typed` (PEP 561 marker)
- `packages/quilto/tests/__init__.py`
- `packages/swealog/pyproject.toml`
- `packages/swealog/swealog/__init__.py`
- `packages/swealog/swealog/py.typed` (PEP 561 marker)
- `packages/swealog/tests/__init__.py`
- `pyrightconfig.json`
- `README.md`
- `.gitignore`

Files generated by uv:
- `uv.lock` (workspace lockfile)
- `.venv/` (virtual environment)

Existing files (no modification needed):
- `tests/corpus/` (test corpus directory with 98 fitness log entries)

## Senior Developer Review (AI)

**Reviewer:** Amelia (Dev Agent) | **Date:** 2026-01-08 | **Outcome:** APPROVED (after fixes)

### Issues Found & Fixed

| Severity | Issue | Resolution |
|----------|-------|------------|
| HIGH | Missing `py.typed` marker files | Created `packages/*/quilto/py.typed` and `packages/*/swealog/py.typed` |
| MEDIUM | Missing test directories | Created `packages/quilto/tests/` and `packages/swealog/tests/` with `__init__.py` |
| MEDIUM | README.md referenced but missing | Created `README.md` at project root |
| MEDIUM | tests/ not documented in File List | Updated File List |
| MEDIUM | No `.gitignore` | Created comprehensive `.gitignore` |
| MEDIUM | Incomplete ruff per-file-ignores | Added ignores for `__init__.py` (D104) and test files (D100, D103) |

### Issues Deferred (LOW)

- Missing `__all__` exports in `__init__.py` files
- pyrightconfig.json include pattern unconventional
- Missing `[project.license]` in pyproject.toml files

### Verification After Fixes

- `uv run ruff check .`: PASS
- `uv run pyright`: PASS (0 errors)
- `uv run pytest --collect-only`: PASS (0 tests expected)

## Change Log

- 2026-01-08: Code review completed - 6 issues fixed (1 HIGH, 5 MEDIUM), status → done
- 2026-01-08: Story 1.1 implemented - uv workspace monorepo structure with quilto and swealog packages
