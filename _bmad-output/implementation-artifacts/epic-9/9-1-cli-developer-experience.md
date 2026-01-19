# Story 9.1: CLI Developer Experience Improvements

Status: ready-for-dev

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

- [ ] Task 1: Add python-dotenv dependency (AC: 3, 4)
  - [ ] Add `python-dotenv>=1.0.0` to swealog/pyproject.toml dependencies
  - [ ] Run `uv sync` to update lockfile

- [ ] Task 2: Implement .env auto-loading (AC: 3, 4)
  - [ ] Import `load_dotenv` from `dotenv` in `cli/app.py`
  - [ ] Call `load_dotenv()` in the app callback (runs before any command)
  - [ ] Verify it's silent when no .env file exists

- [ ] Task 3: Create DebugLogger helper (AC: 5)
  - [ ] Create `cli/debug.py` module
  - [ ] Create `DebugLogger` class with methods:
    - `log_agent_start(agent_name: str, input_summary: str)`
    - `log_agent_end(agent_name: str, output_summary: str, elapsed: float)`
  - [ ] Use rich formatting (cyan for agent name, dim for timing)
  - [ ] Export from `cli/__init__.py`

- [ ] Task 4: Add --debug flag to log command (AC: 1, 5)
  - [ ] Add `--debug` / `-d` flag to `log_cmd.py`
  - [ ] Wrap RouterAgent.classify() with debug logging
  - [ ] Wrap ParserAgent.parse() with debug logging
  - [ ] Pass debug flag through get_dependencies or as parameter

- [ ] Task 5: Add --debug flag to ask command (AC: 2, 5)
  - [ ] Add `--debug` / `-d` flag to `ask_cmd.py`
  - [ ] Modify `execute_query_pipeline()` to accept optional debug callback
  - [ ] Or: Create CLI-specific wrapper that adds debug logging around pipeline
  - [ ] Log all 6 agents in sequence with timing

- [ ] Task 6: Write unit tests (AC: 1-5)
  - [ ] Test .env loading with temp .env file
  - [ ] Test .env missing doesn't error
  - [ ] Test --debug flag produces expected output patterns
  - [ ] Test debug output includes agent names and timing
  - [ ] Use CliRunner with captured output

- [ ] Task 7: Update CLI help text
  - [ ] Add examples showing --debug usage
  - [ ] Document .env file support in help or README

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

TBD

### Completion Notes List

TBD

### File List

TBD
