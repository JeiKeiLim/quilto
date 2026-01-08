# System-Level Test Design: Quilto/Swealog

**Date:** 2026-01-04
**Author:** Jongkuk Lim
**Status:** Draft
**Mode:** System-Level (Phase 3 - Testability Review)

---

## Executive Summary

**Project:** Quilto (framework) + Swealog (fitness application)
**Architecture:** Python 3.13, uv monorepo, LangGraph orchestration, LiteLLM client, pytest

**Key Characteristics:**
- 9 agents with Pydantic I/O contracts
- 13-state state machine with 4 cycles
- StorageRepository abstraction (6 methods)
- 93 parser corpus inputs available

---

## Testability Assessment

### Controllability: PASS

| Aspect | Status | Evidence |
|--------|--------|----------|
| System state control | ✅ | StorageRepository abstraction with 6 methods enables complete state manipulation |
| External dependency mocking | ✅ | LiteLLM abstraction with tiered config allows provider switching without code changes |
| Error condition injection | ✅ | Error cascade (retry → fallback → degrade) is explicitly designed |
| Agent isolation | ✅ | Agents are pure functions with Pydantic I/O - testable independently |
| Domain modules | ✅ | Pluggable DomainModule interface enables test-specific configurations |

**Controllability Details:**
- `StorageRepository` provides: `get_entries_by_date_range`, `get_entries_by_pattern`, `search_entries`, `save_entry`, `get_global_context`, `update_global_context`
- LLM client fixture can toggle between mock responses and real Ollama via `--use-real-ollama` pytest flag
- File-based storage allows parallel test isolation with separate `base_path` directories

### Observability: CONCERNS

| Aspect | Status | Evidence |
|--------|--------|----------|
| State inspection | ✅ | SessionState Pydantic model exposes 20+ fields for validation |
| Result determinism | ⚠️ | LLM responses inherently non-deterministic; need seeded mock responses |
| NFR validation | ⚠️ | No structured logging defined; need observability for latency/accuracy |
| Test result clarity | ✅ | Pydantic validation provides clear success/failure with field-level errors |

**Recommendations:**
1. Add structured logging with trace IDs for debugging failed tests
2. Define accuracy metrics schema (field-level F1, exact match, partial credit)
3. Capture LLM response timing for latency validation

### Reliability: PASS with Recommendations

| Aspect | Status | Evidence |
|--------|--------|----------|
| Test isolation | ✅ | File-based storage + unique base_path per test = parallel-safe |
| Failure reproduction | ⚠️ | LLM non-determinism; need HAR-style response capture for debugging |
| Loose coupling | ✅ | Agents communicate via Pydantic models, not direct dependencies |
| State machine cycles | ⚠️ | 4 distinct cycles (Analyze→Plan, Evaluate→Plan, Expand→Build, Clarify→Wait) require careful test coverage |

**Recommendations:**
1. Create fixture for capturing LLM request/response pairs during test runs
2. Implement state snapshot fixtures for each of 13 states
3. Test cycle termination conditions explicitly (max retries, domain expansion limits)

---

## Architecturally Significant Requirements (ASRs)

### ASR-1: Parser Accuracy (NFR-F4)

| Attribute | Value |
|-----------|-------|
| Requirement | >90% parsing accuracy |
| Probability | 3 (High) - Core to product value |
| Impact | 3 (Critical) - Users lose trust if parsing fails |
| Score | **9 (Critical)** |
| Mitigation | Build test corpus (93 existing + target 500+), field-level F1 metrics |
| Owner | QA/Dev |
| Verification | Automated accuracy tests on corpus; 90% threshold gate |

### ASR-2: Parsing Latency (NFR-F3)

| Attribute | Value |
|-----------|-------|
| Requirement | <5 seconds parsing latency |
| Probability | 2 (Possible) - Depends on Ollama model/hardware |
| Impact | 2 (Degraded) - Poor UX but not blocking |
| Score | **4 (Medium)** |
| Mitigation | Performance benchmarks with timer assertions |
| Owner | Dev |
| Verification | pytest with `--timeout=5` on parser tests |

### ASR-3: Local-First Operation (NFR-F1)

| Attribute | Value |
|-----------|-------|
| Requirement | Must run on Ollama, no cloud dependency |
| Probability | 1 (Unlikely) - Architecture explicitly supports this |
| Impact | 3 (Critical) - Core value proposition |
| Score | **3 (Low-Medium)** |
| Mitigation | CI tests with Ollama; cloud-free integration suite |
| Owner | Dev |
| Verification | Integration tests using real Ollama on Mac hardware |

### ASR-4: State Machine Correctness

| Attribute | Value |
|-----------|-------|
| Requirement | 13 states, 4 cycles execute correctly |
| Probability | 2 (Possible) - Complex state transitions |
| Impact | 3 (Critical) - Wrong state = wrong behavior |
| Score | **6 (High)** |
| Mitigation | State transition tests for all 34 documented transitions |
| Owner | Dev |
| Verification | LangGraph state machine unit tests with mocked agents |

### ASR-5: LLM Provider Flexibility (NFR-F6)

| Attribute | Value |
|-----------|-------|
| Requirement | Switch between Ollama/Cloud without code changes |
| Probability | 1 (Unlikely) - LiteLLM abstraction designed for this |
| Impact | 2 (Degraded) - Limits experimentation |
| Score | **2 (Low)** |
| Mitigation | Contract tests for LLMClient interface |
| Owner | Dev |
| Verification | Same tests run with different provider configs |

---

## Test Levels Strategy

Based on Python/pytest stack and agent architecture:

### Recommended Test Distribution

| Level | Percentage | Purpose | Count Estimate |
|-------|------------|---------|----------------|
| Unit | 50% | Agent pure functions, Pydantic validation, utility functions | ~200-300 |
| Integration | 25% | Agent→Storage, Agent→LLM, multi-agent sequences | ~100-150 |
| E2E | 10% | Full query/log flows through LangGraph | ~40-60 |
| Accuracy | 15% | Parser corpus validation (input→expected output) | ~500+ corpus entries |

### Test Level Details

#### Unit Tests (~50%)
**When to use:**
- Pure agent functions (Router, Parser, Analyzer logic)
- Pydantic model validation (all 9 agent I/O contracts)
- Utility functions (date parsing, vocabulary normalization)
- Domain module configuration validation

**Characteristics:**
- Fast execution (<1 second per test)
- No external dependencies (mock LLM, mock storage)
- High coverage of edge cases
- Use pytest with parametrized tests

```python
# Example: Agent output validation
@pytest.mark.parametrize("input_text,expected_type", [
    ("I benched 185 today", InputType.LOG),
    ("Why was my bench heavy?", InputType.QUERY),
    ("I benched 185, why was it heavy?", InputType.BOTH),
])
async def test_router_classifies_input(input_text, expected_type, mock_llm):
    output = await router_agent(input_text, llm_client=mock_llm)
    assert output.input_type == expected_type
```

#### Integration Tests (~25%)
**When to use:**
- Agent→StorageRepository interactions
- Agent→LLMClient interactions with real Ollama (optional)
- Multi-agent sequences (Planner→Retriever→Analyzer)
- Domain context building

**Characteristics:**
- Moderate execution time (1-10 seconds)
- May use real Ollama with `--use-real-ollama` flag
- Tests component boundaries

```python
# Example: Agent-Storage integration
async def test_retriever_fetches_entries(storage_fixture, domain_fixture):
    # Seed storage
    await storage_fixture.save_entry(create_entry(date="2024-01-15"))

    # Execute retriever
    output = await retriever_agent(
        strategy=RetrievalStrategy(date_range=("2024-01-01", "2024-01-31")),
        storage=storage_fixture,
    )

    assert len(output.retrieved_entries) == 1
```

#### E2E Tests (~10%)
**When to use:**
- Critical user journeys (log entry → parse → store)
- Full query flows (query → plan → retrieve → analyze → synthesize → evaluate)
- State machine cycle tests (Evaluate→Plan retry loop)
- Human-in-the-loop flows (WAIT_USER state)

**Characteristics:**
- Slower execution (10-60 seconds)
- Tests complete LangGraph workflows
- Uses mock LLM by default, real Ollama with flag

```python
# Example: Full query flow
async def test_query_flow_with_sufficient_data(langgraph_fixture, mock_llm):
    # Setup: seed data
    await seed_entries(langgraph_fixture.storage, [
        create_strength_entry("2024-01-15", "bench 185x5"),
        create_strength_entry("2024-01-14", "bench 175x5"),
    ])

    # Execute full flow
    result = await langgraph_fixture.run(
        input="Why did my bench feel heavy last week?",
        llm_client=mock_llm,
    )

    assert result.complete
    assert "185" in result.final_response
```

#### Accuracy Tests (~15%)
**When to use:**
- Parser accuracy validation (NFR-F4: >90%)
- Vocabulary normalization coverage
- Domain schema extraction

**Corpus Structure (Domain-First):**
```
tests/
├── corpus/
│   ├── schemas/                     # Domain schema definitions
│   │   ├── fitness.yaml
│   │   └── tasks.yaml
│   │
│   ├── fitness/                     # Fitness domain
│   │   ├── ground_truth/
│   │   │   └── strong_workouts.csv  # Gold standard (real structured data)
│   │   ├── entries/
│   │   │   ├── from_csv/            # 93 synthesized from CSV (verifiable)
│   │   │   ├── human/               # Real human notes (future)
│   │   │   └── synthetic/           # Pure LLM-generated
│   │   └── expected/
│   │       ├── parser/              # Expected ParserOutput JSON
│   │       ├── query/               # Expected query responses
│   │       └── retrieval/           # Expected retrieval results
│   │
│   ├── multi_domain/                # Cross-domain test cases
│   │   ├── entries/
│   │   └── expected/parser/
│   │
│   ├── generic/                     # Domain-agnostic tests
│   │   ├── edge_cases/
│   │   └── multilingual/
│   │
│   └── variation_rules/             # Human-provided synthesis instructions
│       └── SYNTHESIS_RULES.md
│
└── fixtures/                        # Pytest fixtures
    ├── llm_responses/
    ├── state_snapshots/
    └── storage/
```

**Test Data Strategy:**
| Source | Location | Purpose |
|--------|----------|---------|
| From CSV (verifiable) | `entries/from_csv/` | **Primary accuracy** - 93 files with CSV ground truth |
| Human-written (future) | `entries/human/` | Expose LLM blind spots with real writing patterns |
| Pure synthetic | `entries/synthetic/` | Volume/stress only, NOT for accuracy metrics |

**Key insight:** `from_csv/` entries avoid LLM circular validation because expected output derives from real structured data (Strong CSV), not LLM generation.

**Metrics:**
- Field-level F1 (exercise name, weight, reps, sets)
- Exact match rate
- Partial credit for near-matches

---

## NFR Testing Approach

### Security: N/A (Local-only v1)

v1 is local-first with no auth/authz requirements. Future multi-user scenarios will require security testing.

### Performance

**Tool:** pytest with timing assertions + benchmarks

**Approach:**
- Parser latency: Each test asserts `< 5 seconds`
- Batch processing: Import 100 entries in `< 60 seconds`
- LLM response times captured for baseline

```python
# Example: Performance assertion
async def test_parser_latency(parser_fixture, sample_input, mock_llm):
    import time
    start = time.time()

    await parser_agent(sample_input, llm_client=mock_llm)

    elapsed = time.time() - start
    assert elapsed < 5.0, f"Parser took {elapsed}s, exceeds 5s limit"
```

### Reliability

**Approach:**
- Error cascade tests (retry → fallback → degrade)
- State recovery tests (LangGraph checkpoint/resume)
- Graceful degradation (missing JSON handled)

**Tests:**
- LLM timeout → retry 3x → fallback provider → degrade with error message
- Missing parsed JSON → application continues with raw only
- State machine cycle limits (max 2 retries before partial response)

### Maintainability

**Approach:**
- Strict code quality (Ruff, pyright strict, Google docstrings)
- Test coverage target: 80% for critical paths
- Pydantic contracts prevent interface drift

**Tools:**
- `ruff check --select E,F,W,I,D,UP,B,SIM`
- `pyright --strict`
- `pytest --cov --cov-fail-under=80`

---

## Test Environment Requirements

### Local Development

| Requirement | Details |
|-------------|---------|
| Python | 3.13 |
| Package manager | uv |
| Ollama | Required for `--use-real-ollama` tests |
| Hardware | MacBook M1/M2/M3 (NFR-F2) |

### CI Pipeline

| Stage | Tests | Parallelism |
|-------|-------|-------------|
| Unit | All unit tests | 4 workers |
| Integration (mock) | Mock LLM integration | 2 workers |
| Integration (Ollama) | Real Ollama integration | 1 worker (GPU bound) |
| E2E | Full workflow tests | 1 worker |
| Accuracy | Parser corpus | 4 workers |

---

## Testability Concerns

### Concern 1: LLM Non-Determinism

**Status:** ⚠️ CONCERNS

**Issue:** LLM responses vary between runs, making assertions fragile.

**Mitigation:**
1. Mock LLM with canned responses for unit/integration tests
2. Semantic assertions (contains expected concepts) for real LLM tests
3. Golden output files with tolerance for minor variations

### Concern 2: State Machine Complexity

**Status:** ⚠️ CONCERNS

**Issue:** 13 states with 4 cycles creates many possible paths.

**Mitigation:**
1. Enumerate all 34 state transitions from documentation
2. Create transition matrix tests (from-state, condition, to-state)
3. Use LangGraph visualization for coverage gaps

### Concern 3: Accuracy Metric Definition

**Status:** ⚠️ CONCERNS

**Issue:** "90% accuracy" not precisely defined (field-level vs entry-level).

**Mitigation:**
1. Define field-level F1 for: exercise_name, weight, reps, sets, notes
2. Define entry-level exact match for full ParserOutput
3. Create accuracy dashboard with breakdown by field

---

## Recommendations for Sprint 0

### 1. Test Infrastructure Setup

- [ ] Configure pytest + pytest-asyncio in `pyproject.toml`
- [ ] Create `conftest.py` with core fixtures:
  - `mock_llm` - Canned LLM responses
  - `storage_fixture` - Isolated file storage per test
  - `domain_fixture` - Test domain configurations
- [ ] Create `--use-real-ollama` pytest option

### 2. Parser Corpus Preparation

- [ ] Generate expected output JSON for 50-100 seed entries
- [ ] Define accuracy metrics schema (AccuracyResult Pydantic model)
- [ ] Create accuracy test runner with reporting

### 3. State Machine Test Scaffolding

- [ ] Create state transition matrix from agent-system-design.md
- [ ] Implement state snapshot fixtures for each of 13 states
- [ ] Create cycle termination tests (max retries, expansion limits)

### 4. CI Pipeline Configuration

- [ ] GitHub Actions workflow with:
  - Unit tests (all PRs)
  - Integration tests (all PRs)
  - Accuracy tests (nightly)
  - Ollama tests (manual trigger)

---

## LLM Mock Strategy

### Fixture Implementation

```python
# conftest.py
import pytest
from typing import AsyncGenerator

class MockLLMClient:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.call_log: list[dict] = []

    async def complete_structured(
        self,
        agent: str,
        messages: list[dict],
        response_model: type[BaseModel],
        **kwargs,
    ) -> BaseModel:
        self.call_log.append({"agent": agent, "messages": messages})

        if agent in self.responses:
            return response_model.model_validate_json(self.responses[agent])
        raise ValueError(f"No mock response for agent: {agent}")


@pytest.fixture
def mock_llm() -> MockLLMClient:
    return MockLLMClient(responses={
        "router": '{"input_type": "LOG", "confidence": 0.95}',
        "parser": '{"exercises": [{"name": "bench press", "weight": 185}]}',
        # ... more canned responses
    })


@pytest.fixture
async def llm_client(request, mock_llm) -> AsyncGenerator[LLMClient, None]:
    if request.config.getoption("--use-real-ollama", default=False):
        yield RealLLMClient(provider="ollama", api_base="http://localhost:11434")
    else:
        yield mock_llm


def pytest_addoption(parser):
    parser.addoption(
        "--use-real-ollama",
        action="store_true",
        default=False,
        help="Run tests with real Ollama instead of mocks",
    )
```

---

## Quality Gate Criteria

### Phase 4 Gate (Pre-Implementation)

- [ ] Unit test coverage ≥80% on critical paths
- [ ] All 34 state transitions tested
- [ ] Parser accuracy ≥90% on seed corpus (50+ entries)
- [ ] P0 tests 100% pass rate
- [ ] No high-risk (≥6) items unmitigated

### Release Gate

- [ ] Parser accuracy ≥90% on full corpus (500+ entries)
- [ ] Parsing latency <5s (p95)
- [ ] Integration tests pass with real Ollama
- [ ] All 8 epics have E2E coverage

---

## Appendix: Risk Summary

| Risk ID | Category | Description | Score | Status |
|---------|----------|-------------|-------|--------|
| ASR-1 | DATA | Parser accuracy <90% | 9 | Open |
| ASR-2 | PERF | Parsing latency >5s | 4 | Open |
| ASR-3 | TECH | Cloud dependency leak | 3 | Open |
| ASR-4 | TECH | State machine bugs | 6 | Open |
| ASR-5 | TECH | Provider lock-in | 2 | Open |

**High-Priority (≥6):** ASR-1, ASR-4 require immediate test coverage.

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `_bmad/bmm/testarch/test-design`
**Mode**: System-Level (Phase 3)
