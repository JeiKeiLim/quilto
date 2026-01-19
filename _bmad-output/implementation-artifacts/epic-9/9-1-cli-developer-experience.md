# Story 9.1: CLI Developer Experience Improvements

Status: done

## Story

As a **Swealog developer dogfooding Quilto**,
I want **debug output and easy API key management**,
So that **I can effectively debug agent behavior and quickly switch between local and cloud providers**.

## Background

From Epic 8 Retrospective (2026-01-19):

> "manual_test.py was more helpful. I didn't know how to use swealog and it showed application level verbosity which is good in general but this phase, I was hoping more of debug level verbosity so that I would know what went wrong or well." - Jongkuk Lim

The CLI is optimized for end users (clean success/error messages), but the primary current user is the developer. Debug mode is needed to expose framework internals during dogfooding.

## Acceptance Criteria

1. **AC1: Debug Flag for Log Command**
   - Given `swealog log --debug "bench 185x5"`
   - When the command executes
   - Then Router agent input/output is displayed
   - And Parser agent input/output is displayed
   - And timing per agent is shown
   - And the normal success message still appears at the end

2. **AC2: Debug Flag for Ask Command**
   - Given `swealog ask --debug "how's my bench progress?"`
   - When the command executes
   - Then all pipeline agents are shown: Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator
   - And each agent shows: name, input summary, output summary, execution time
   - And the normal response panel still appears at the end

3. **AC3: .env File Auto-Loading**
   - Given a `.env` file exists in the current directory
   - When any swealog CLI command runs
   - Then environment variables from `.env` are loaded before config parsing
   - And `${VAR_NAME}` interpolation in llm-config.yaml works with .env variables

4. **AC4: .env File Optional**
   - Given NO `.env` file exists
   - When any swealog CLI command runs
   - Then no error occurs (silent skip)
   - And commands work normally

5. **AC5: Debug Output Format**
   - Given debug mode is enabled
   - When agent output is displayed
   - Then format matches:
   ```
   [Router] input: "bench 185x5"
   [Router] output: input_type=LOG, domains=[strength], confidence=0.92
   [Router] time: 0.8s
   ```

## Tasks / Subtasks

- [x] Task 1: Add python-dotenv dependency (AC: 3, 4)
  - [x] Add `python-dotenv>=1.0.0` to swealog/pyproject.toml dependencies
  - [x] Run `uv sync` to update lockfile

- [x] Task 2: Implement .env auto-loading (AC: 3, 4)
  - [x] Import `load_dotenv` from `dotenv` in `cli/app.py`
  - [x] Call `load_dotenv()` in the app callback (runs before any command)
  - [x] Verify it's silent when no .env file exists

- [x] Task 3: Create DebugLogger helper (AC: 5)
  - [x] Create `cli/debug.py` module
  - [x] Create `DebugLogger` class with methods:
    - `log_agent_start(agent_name: str, input_summary: str)`
    - `log_agent_end(agent_name: str, output_summary: str, elapsed: float)`
  - [x] Use rich formatting (cyan for agent name, dim for timing)
  - [x] Export from `cli/__init__.py`

- [x] Task 4: Add --debug flag to log command (AC: 1, 5)
  - [x] Add `--debug` / `-d` flag to `log_cmd.py`
  - [x] Wrap RouterAgent.classify() with debug logging
  - [x] Wrap ParserAgent.parse() with debug logging
  - [x] Pass debug flag through get_dependencies or as parameter

- [x] Task 5: Add --debug flag to ask command (AC: 2, 5)
  - [x] Add `--debug` / `-d` flag to `ask_cmd.py`
  - [x] Modify `execute_query_pipeline()` to accept optional debug callback
  - [x] Or: Create CLI-specific wrapper that adds debug logging around pipeline
  - [x] Log all 6 agents in sequence with timing

- [x] Task 6: Write unit tests (AC: 1-5)
  - [x] Test .env loading with temp .env file
  - [x] Test .env missing doesn't error
  - [x] Test --debug flag produces expected output patterns
  - [x] Test debug output includes agent names and timing
  - [x] Use CliRunner with captured output

- [x] Task 7: Update CLI help text
  - [x] Add examples showing --debug usage
  - [x] Document .env file support in help or README

## Dev Notes

### Project Identity

This story modifies **Swealog** CLI (the application), not Quilto framework.

**Location:** `packages/swealog/swealog/cli/`

### File Structure

```
packages/swealog/swealog/cli/
├── __init__.py       # Export DebugLogger
├── app.py            # Add load_dotenv() call
├── debug.py          # NEW: DebugLogger helper
├── log_cmd.py        # Add --debug flag
├── ask_cmd.py        # Add --debug flag
└── ...
```

### Dependencies

Add to swealog/pyproject.toml:
```toml
dependencies = [
    # ... existing ...
    "python-dotenv>=1.0.0",
]
```

### Code Patterns

**.env Loading (app.py):**
```python
from dotenv import load_dotenv

@app.callback()
def main(
    version: bool = typer.Option(...),
) -> None:
    """Swealog - AI-powered fitness logging."""
    # Load .env file if present (silent if missing)
    load_dotenv()
```

**DebugLogger (debug.py):**
```python
"""Debug logging utilities for CLI commands."""

import time
from contextlib import contextmanager
from collections.abc import Generator
from typing import Any

from rich.console import Console

console = Console()


class DebugLogger:
    """Logger for debug output in CLI commands."""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    @contextmanager
    def agent(self, name: str, input_summary: str) -> Generator[None, None, None]:
        """Context manager for logging agent execution.

        Args:
            name: Agent name (e.g., "Router", "Parser").
            input_summary: Brief description of input.

        Yields:
            None. Logs start/end if debug enabled.
        """
        if not self.enabled:
            yield
            return

        console.print(f"[cyan][{name}][/cyan] input: {input_summary}")
        start = time.perf_counter()
        yield
        elapsed = time.perf_counter() - start
        console.print(f"[cyan][{name}][/cyan] [dim]time: {elapsed:.2f}s[/dim]")

    def log_output(self, name: str, output_summary: str) -> None:
        """Log agent output.

        Args:
            name: Agent name.
            output_summary: Brief description of output.
        """
        if self.enabled:
            console.print(f"[cyan][{name}][/cyan] output: {output_summary}")
```

**Usage in log_cmd.py:**
```python
from swealog.cli.debug import DebugLogger

@run_async
async def log(
    text: Annotated[str, typer.Argument(...)],
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Show debug output")] = False,
    # ... other options ...
) -> None:
    """Log a fitness entry."""
    dbg = DebugLogger(enabled=debug)

    # ... setup ...

    with dbg.agent("Router", f'"{text[:50]}..."'):
        router_output = await router.classify(router_input)
    dbg.log_output("Router", f"type={router_output.input_type.value}, domains={router_output.selected_domains}")

    with dbg.agent("Parser", f"domains={router_output.selected_domains}"):
        parser_output = await parser.parse(parser_input)
    dbg.log_output("Parser", f"date={parser_output.date}, fields={len(parser_output.domain_data)}")
```

### Example .env File

```
# Cloud API Keys
OPENAI_API_KEY=sk-proj-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional overrides
SWEALOG_STORAGE_PATH=./my-logs
```

### Example llm-config.yaml with .env

```yaml
default_provider: openai
fallback_provider: ollama

providers:
  openai:
    api_key: "${OPENAI_API_KEY}"
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
  ollama:
    api_base: http://localhost:11434
```

### Validation Commands

```bash
# During development
make check        # lint + typecheck

# Before completion
make validate     # lint + format + typecheck + test

# Integration testing
make test-ollama
```

### References

- Epic 8 Retrospective: `_bmad-output/implementation-artifacts/epic-8/retro-2026-01-19.md`
- Existing CLI: `packages/swealog/swealog/cli/`
- Config with env interpolation: `packages/quilto/quilto/llm/config.py:18-41`
- manual_test.py output format (reference for debug verbosity)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

- Added `python-dotenv>=1.0.0` to swealog package dependencies
- Implemented `.env` auto-loading in CLI app callback (silent when missing)
- Created `DebugLogger` class in `cli/debug.py` with context manager API
- Added `--debug` / `-d` flag to both `log` and `ask` commands
- Modified `execute_query_pipeline()` to accept optional debug callback for timing all 6 agents
- Created comprehensive test suite in `test_cli_debug.py` (14 tests)
- Updated existing tests in `test_cli_log.py` to include `confidence` attribute in mocks
- CLI help text automatically shows examples via docstrings

### Change Log

- 2026-01-19: Implemented Story 9.1 - CLI Developer Experience (--debug + .env)

### File List

**New Files:**
- `packages/swealog/swealog/cli/debug.py` - DebugLogger helper class
- `packages/swealog/tests/test_cli_debug.py` - Unit tests for debug functionality

**Modified Files:**
- `packages/swealog/pyproject.toml` - Added python-dotenv dependency
- `packages/swealog/swealog/cli/__init__.py` - Export DebugLogger
- `packages/swealog/swealog/cli/app.py` - Added load_dotenv() call
- `packages/swealog/swealog/cli/log_cmd.py` - Added --debug flag with debug logging
- `packages/swealog/swealog/cli/ask_cmd.py` - Added --debug flag with debug callback
- `packages/swealog/swealog/api/routes/query.py` - Added debug_callback parameter to execute_query_pipeline
- `packages/swealog/tests/test_cli_log.py` - Added confidence attribute to router mocks
- `uv.lock` - Updated lockfile (auto-generated from uv sync)

### Known Limitations

- **AC3 .env interpolation**: Tests verify .env is loaded but do not verify ${VAR_NAME} interpolation works in llm-config.yaml. This depends on the quilto config module which handles interpolation. The .env loading is verified but end-to-end interpolation testing would require llm-config.yaml setup.

### Senior Developer Review (AI)

**Date:** 2026-01-19
**Reviewer:** Claude Opus 4.5 (adversarial review)

**Issues Found & Fixed:**
- H1: Fixed AC5 output format - changed DebugLogger to print input→output→time (was input→time→output)
- H2: Added tests for _DebugTimer class in query pipeline (4 new tests)
- H3: Added confidence to Router output in ask command pipeline
- M1: Added uv.lock to File List
- M2: Created DebugCallback type alias in query.py for cleaner signatures
- M3: Fixed weak test assertion (OR→AND) in test_no_debug_flag_no_debug_output
- M4: Documented .env interpolation test limitation above

**Tests:** All 18 tests pass (14 debug + 4 timer tests)
