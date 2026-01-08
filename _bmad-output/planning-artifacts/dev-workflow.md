# Quilto & Swealog Development Workflow

**Created:** 2026-01-09 (Epic 1 Retrospective)
**Status:** Active
**Applies to:** All developers (human and AI agents) working on Quilto framework or Swealog application

---

## Project Structure Reminder

This workspace contains TWO packages:

| Package | Type | Purpose |
|---------|------|---------|
| **Quilto** (`packages/quilto/`) | Framework | Domain-agnostic agent framework |
| **Swealog** (`packages/swealog/`) | Application | Fitness app built on Quilto |

**Important:** Most code belongs in Quilto (the framework). Swealog only contains fitness-specific domain modules and configurations.

See: `_bmad-output/planning-artifacts/project-identity.md` for full clarification.

---

## Core Principle

**Validate early, validate often.** Don't wait until code review to discover issues.

---

## During Development

### Run Validation Frequently

Developers should run formatting, linting, and tests **as often as possible** during development - not just at the end.

**Recommended frequency:**
- After completing each logical unit of work (function, class, file)
- Before committing any changes
- When switching between tasks or taking breaks

**Quick validation commands:**

```bash
# Format and lint (fast - run constantly)
uv run ruff check . --fix
uv run ruff format .

# Type check (medium - run frequently)
uv run pyright

# Tests (slower - run after meaningful changes)
uv run pytest tests/ -v

# Full validation (before commits)
uv run ruff check . && uv run pyright && uv run pytest
```

**Why this matters:**
- Catches issues immediately while context is fresh
- Prevents accumulation of small issues into large problems
- Reduces code review cycles
- Builds muscle memory for quality code

---

## Pre-Review Checklist

Before requesting code review, verify ALL items pass:

### Required Checks

- [ ] **Formatting:** `uv run ruff format .` produces no changes
- [ ] **Linting:** `uv run ruff check .` passes with 0 errors
- [ ] **Type checking:** `uv run pyright` passes with 0 errors
- [ ] **Tests:** `uv run pytest` passes (all tests green)

### Code Quality

- [ ] **Docstrings:** All new public functions/classes have Google-style docstrings
- [ ] **Type hints:** All new functions have complete type annotations
- [ ] **Exports:** All new public classes are exported in `__init__.py`
- [ ] **py.typed:** Typed packages have `py.typed` marker file

### Test Coverage

- [ ] **Unit tests:** New functionality has corresponding tests
- [ ] **Edge cases:** Tests cover error conditions and edge cases
- [ ] **Test naming:** Tests have descriptive names explaining what they verify

---

## Common Issues (From Epic 1)

These issues appeared repeatedly in code reviews. Watch for them:

| Issue | Prevention |
|-------|------------|
| Missing type annotations | Run `pyright` frequently |
| Missing docstrings | Check all public functions before review |
| Missing `__init__.py` exports | Review module structure after adding classes |
| Missing `py.typed` marker | Add when creating new typed packages |
| Incomplete test coverage | Write tests alongside implementation |

---

## Git Workflow

### Commit Guidelines

1. **Run full validation before committing:**
   ```bash
   uv run ruff check . && uv run pyright && uv run pytest
   ```

2. **Write meaningful commit messages:**
   - First line: imperative mood, max 50 chars
   - Body: explain WHY, not just WHAT

3. **Keep commits focused:**
   - One logical change per commit
   - Don't mix refactoring with feature work

### Branch Strategy

- Feature branches from `main`
- PR required for all changes
- Code review required before merge

---

## Story Workflow

### Starting a Story

1. Read the full story file (acceptance criteria, dev notes)
2. Understand dependencies and technical constraints
3. Plan approach before coding

### During Implementation

1. **Validate frequently** (see above)
2. Mark tasks complete in story file as you go
3. Update Dev Notes with discoveries/decisions

### Completing a Story

1. Run full validation suite
2. Complete pre-review checklist (all items checked)
3. Update story status to "review"
4. Request code review (fresh context, different LLM recommended)

### After Code Review

1. Address all HIGH and MEDIUM issues
2. Document any deferred items with justification
3. Re-run validation after fixes
4. Update story status to "done"

---

## Validation Commands Reference

```bash
# Individual tools
uv run ruff check .           # Linting only
uv run ruff check . --fix     # Linting with auto-fix
uv run ruff format .          # Formatting
uv run pyright                # Type checking
uv run pytest                 # All tests
uv run pytest tests/ -v       # Verbose test output
uv run pytest -x              # Stop on first failure
uv run pytest --tb=short      # Shorter tracebacks

# Package-specific
uv run pytest packages/quilto/tests/ -v    # Quilto tests only
uv run pytest packages/swealog/tests/ -v   # Swealog tests only
uv run ruff check packages/quilto/         # Lint quilto only
uv run pyright packages/quilto/            # Type check quilto only

# Full validation (recommended before commits)
uv run ruff check . && uv run ruff format . && uv run pyright && uv run pytest

# Quick validation (during development)
uv run ruff check . --fix && uv run pyright
```

---

## IDE Integration (Recommended)

Configure your IDE to run validation on save:

### VS Code

Add to `.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit"
    }
  },
  "python.analysis.typeCheckingMode": "strict"
}
```

### PyCharm

- Enable "Reformat code on save"
- Configure ruff as external tool
- Enable type checking inspections

---

## Troubleshooting

### "pyright finds errors but ruff doesn't"

These tools check different things:
- **ruff:** Style, imports, common bugs (faster, less strict)
- **pyright:** Type correctness (slower, more thorough)

Both must pass.

### "Tests pass locally but fail in CI"

Common causes:
- Missing `__init__.py` files
- Import order issues
- Path-dependent tests
- Missing test fixtures

Run tests from project root: `uv run pytest tests/ -v`

### "Ruff auto-fix changed too much"

Review changes with `git diff` before committing. Ruff's auto-fix is usually correct but verify import reorganizations.

---

## Summary

1. **Validate early, validate often** - Don't wait for code review
2. **Complete the checklist** - Every item, every time
3. **Write tests alongside code** - Not as an afterthought
4. **Document decisions** - In story Dev Notes section

Following this workflow reduces code review cycles and improves code quality.
