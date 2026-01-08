---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - '_bmad-output/swealog-project-context-v2.md'
  - '_bmad-output/swealog-bmad-context.md'
  - '_bmad-output/analysis/brainstorming-session-2025-12-31.md'
  - '_bmad-output/architecture-draft.md'
  - '_bmad-output/planning-artifacts/research/technical-swealog-foundational-research-2026-01-02.md'
  - '_bmad-output/research-questions.md'
workflowType: 'architecture'
project_name: 'swealog'
user_name: 'Jongkuk Lim'
date: '2026-01-02'
status: 'in-progress'
next_action: 'Complete Agent System Design (see agent-system-design.md)'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Core Philosophy:**
"Organization is output, not input" - Users write messy scribbles, agents handle structuring and insight extraction.

**Functional Requirements:**
1. Accept unstructured text input (any domain, any format)
2. Store raw notes preserving original content
3. Parse and extract structured data asynchronously (for app consumption)
4. Retrieve relevant context based on queries
5. Generate insights from accumulated history
6. Support optional domain expertise modules for enhanced extraction

**Non-Functional Requirements:**

| Requirement | Target |
|-------------|--------|
| Local-first | Must run on Ollama, no cloud dependency required |
| Hardware | MacBook (M1/M2/M3) |
| Parsing latency | < 5 seconds |
| Parsing accuracy | > 90% (requires test corpus validation) |
| Storage | Human-readable, git-friendly |
| LLM flexibility | Local default, cloud API option for comparison |

### Key Architectural Decisions

**1. Separate Raw Notes from Parsed Data**
- `raw/` → Human + agent readable (plain markdown)
- `parsed/` → App consumption (JSON)
- LLM agents read raw directly; parsed data serves applications

**2. Directory Structure**
```
logs/
├── raw/{YYYY}/{MM}/{YYYY-MM-DD}.md
└── parsed/{YYYY}/{MM}/{YYYY-MM-DD}.json
```

**3. Plain Markdown Format**
- Daily files with `## HH:MM` sections (server-generated timestamps)
- Multiple entries per day (append model)
- Mixed content types (domain logs + random notes)

**4. No Embeddings for v1**
- Data scale fits within context windows (~109k chars/year)
- Date/keyword retrieval + summarization sufficient
- Add embeddings later only if retrieval quality degrades

**5. Immediate Async Parsing**
- Save raw synchronously (user doesn't wait)
- Parse to JSON asynchronously in background
- Retry on transient failures; error state for persistent failures
- Applications handle missing JSON gracefully

**6. Storage Abstraction Layer**
- Define `StorageInterface` early
- File-based implementation for v1
- Database-ready for future multi-user scenarios
- Same logical structure, swappable backend

### Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Context management | Date-based retrieval + hierarchical summarization |
| LLM abstraction | Local (Ollama) default, cloud API for experimentation |
| Domain expertise | Optional plug-in modules (enhance, not require) |
| Error handling | Retry + error state + graceful fallback |
| Multi-user future | Storage interface abstraction |

### Testing Strategy

| Priority | Item |
|----------|------|
| High | Build test corpus (start 50-100, grow to 500+) |
| High | Define accuracy metrics (field-level F1 vs exact match) |
| Medium | Treat every parse failure as new test case |

---

## Technical Stack

### Confirmed Choices

| Area | Choice | Rationale |
|------|--------|-----------|
| Package Manager | **uv** | Fast, modern, handles packages + venvs |
| Python Version | **3.13** | Latest stable |
| Testing | **pytest** + pytest-asyncio | Standard, async support |
| Layout | **Flat** (`quilto/`) | Clean imports, package-ready |

### Linting & Formatting

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Ruff** | Linting + formatting | Replaces black, isort, flake8 |
| **Ruff pydocstyle** | Docstring enforcement | Google convention, strict (D100-D417) |
| **pyright** | Type checking | Strict mode |

```toml
[tool.ruff.lint]
select = ["E", "F", "W", "I", "D", "UP", "B", "SIM"]

[tool.ruff.lint.pydocstyle]
convention = "google"
```

**Docstring Policy:** Required for all functions, classes, and methods including private. Variable docstrings where necessary.

### LLM Integration

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **LLM Client** | litellm | Unified API for Ollama + cloud providers |
| **Async** | asyncio | Standard library, I/O bound operations |
| **Structured Output** | Pydantic | Validation, schema generation |

**litellm features used:**
- `api_base` for custom endpoints (local Ollama)
- `acompletion` for async calls
- Provider switching without code changes

```python
# Local
response = await litellm.acompletion(model="ollama/llama3.2", api_base="http://localhost:11434", ...)

# Cloud comparison
response = await litellm.acompletion(model="claude-sonnet-4-20250514", ...)
```

### CLI & Future Web

| Phase | Technology | Notes |
|-------|------------|-------|
| Phase 1 | **typer** + **rich** | CLI interface, beautiful output |
| Phase 2 | **FastAPI** | Web API, same async patterns |

### Repository Structure

**Phase 1: uv workspace monorepo**
```
swealog-workspace/
├── pyproject.toml              # Workspace root
├── packages/
│   ├── quilto/                 # Generic framework
│   │   ├── pyproject.toml
│   │   └── quilto/
│   └── swealog/                # Fitness app
│       ├── pyproject.toml
│       └── swealog/
```

**Naming:**
- **Quilto** - The open-source framework
- **Quiltr** - Future SaaS product name (reserved)

**Phase 2: Split when mature**
- Framework becomes standalone package
- Swealog depends on published framework

### Agent Framework Decision

**Status: DECIDED - LangGraph**

The agent system design revealed significant complexity requiring a framework:
- 13 states with 4 distinct cycles
- Human-in-the-loop (WAIT_USER state)
- Conditional routing based on verdicts
- Parallel execution (BOTH → PARSE + PLAN)
- 20+ field state management

**Decision:** Use **LangGraph** for orchestration with the following constraints:
- Use LangGraph core only, avoid langchain extras
- Keep agents as pure functions with clean interfaces
- Use LiteLLM directly in nodes (not LangChain wrappers)
- Test agents independently before graph integration

See: `_bmad-output/planning-artifacts/agent-system-design.md` (Sections 14-15)

### LLM Client Abstraction

**Status: DECIDED - Tiered Configuration**

LLM calls abstracted via tiered configuration for easy provider switching:
- Per-agent model tier configuration (low/medium/high)
- Support for Ollama, Anthropic, OpenAI, Azure, OpenRouter
- Automatic fallback on failure
- No code changes required to switch providers

See: `_bmad-output/planning-artifacts/agent-system-design.md` (Section 15)

---

## Next Steps

1. **Phase 4: Integration Design**
   - How agents interact with storage layer
   - How CLI/API triggers agent flows
   - Error handling and recovery

2. **Implementation**
   - Set up project skeleton with LangGraph + LiteLLM
   - Build core loop first (PLAN → RETRIEVE → ANALYZE → SYNTHESIZE → EVALUATE)
   - Add remaining agents incrementally

