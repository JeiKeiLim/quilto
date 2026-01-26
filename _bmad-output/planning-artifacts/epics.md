---
stepsCompleted: [1, 2, 3, 4]
status: complete
inputDocuments:
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/agent-system-design.md'
  - '_bmad-output/planning-artifacts/state-machine-diagram.md'
projectStructure: 'dual-project (framework + application)'
frameworkName: 'quilto'
applicationName: 'swealog'
futureSaasName: 'quiltr'
---

# Swealog - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Swealog, decomposing the requirements from the Architecture and Agent System Design documents into implementable stories.

**Project Structure:** Monorepo with two packages
- `packages/quilto/` - Generic agent framework (domain-agnostic)
- `packages/swealog/` - Fitness application using the framework

**Naming:**
- **Quilto** - The open-source framework
- **Quiltr** - Future SaaS product name (if applicable)

## Requirements Inventory

### Functional Requirements

**Framework (22 requirements):**
- FR-F1: Accept unstructured text input (any domain, any format)
- FR-F2: Store raw notes preserving original content
- FR-F3: Parse and extract structured data asynchronously
- FR-F4: Retrieve relevant context based on queries
- FR-F5: Generate insights from accumulated history
- FR-F6: Support pluggable domain expertise modules
- FR-F7: Classify input as LOG/QUERY/BOTH/CORRECTION (Router)
- FR-F8: Decompose complex queries with dependency classification (Planner)
- FR-F9: Fetch entries using storage tools (Retriever)
- FR-F10: Analyze patterns and assess sufficiency with verdict-last (Analyzer)
- FR-F11: Generate user-facing responses (Synthesizer)
- FR-F12: Quality check responses with specific feedback (Evaluator)
- FR-F13: Request missing info - human-in-the-loop (Clarifier)
- FR-F14: Extract structured data using domain schemas (Parser)
- FR-F15: Learn patterns and update global context (Observer)
- FR-F16: Auto-select relevant domains for each input
- FR-F17: Combine base + selected domain contexts
- FR-F18: Support mid-flow domain expansion
- FR-F19: Handle corrections with append strategy
- FR-F20: Provide StorageRepository abstraction (6 methods)
- FR-F21: Expose `/input` and `/query` API endpoints
- FR-F22: Support CLI with import command

**Application (10 requirements):**
- FR-A1: Provide GeneralFitness base domain module
- FR-A2: Provide Strength subdomain (sets, reps, RPE, weight)
- FR-A3: Provide Running subdomain (pace, splits, distance)
- FR-A4: Provide Nutrition subdomain (meals, calories, macros) [MVP]
- FR-A5: Provide Swimming subdomain (laps, strokes, intervals) [Post-MVP]
- FR-A6: Define domain-specific log schemas
- FR-A7: Define domain vocabularies for term normalization
- FR-A8: Define domain expertise for agent prompts
- FR-A9: Define response evaluation rules per domain
- FR-A10: Define context management guidance for Observer

### NonFunctional Requirements

- NFR-F1: Local-first (Ollama, no cloud dependency required)
- NFR-F2: Hardware: MacBook M1/M2/M3
- NFR-F3: Parsing latency < 5 seconds
- NFR-F4: Parsing accuracy > 90%
- NFR-F5: Human-readable, git-friendly storage (markdown + JSON)
- NFR-F6: LLM flexibility (local default, cloud option)
- NFR-F7: 2 retries before returning partial + gaps
- NFR-F8: Error cascade: Retry → Fallback → Graceful degrade
- NFR-F9: Global context ~2k tokens with archival strategy

### Additional Requirements

**Architecture Decisions (already made):**
- AR1: Separate raw/ and parsed/ directories
- AR2: Directory structure: logs/(raw|parsed)/{YYYY}/{MM}/{YYYY-MM-DD}
- AR3: uv workspace monorepo with two packages
- AR4: LangGraph for agent orchestration
- AR5: LiteLLM for unified LLM API
- AR6: Tiered model config (low/medium/high) per agent
- AR7: 13-state state machine with 4 cycles
- AR8: 9 agents: 7 query flow + 2 separate (Parser, Observer)

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR-F1 | Epic 2 | Accept unstructured text input |
| FR-F2 | Epic 2 | Store raw notes |
| FR-F3 | Epic 2 | Parse and extract structured data |
| FR-F4 | Epic 3 | Retrieve relevant context |
| FR-F5 | Epic 4 | Generate insights |
| FR-F6 | Epic 1 | Support pluggable domain modules |
| FR-F7 | Epic 2, 3 | Classify input (Router) |
| FR-F8 | Epic 3 | Decompose complex queries (Planner) |
| FR-F9 | Epic 3 | Fetch entries (Retriever) |
| FR-F10 | Epic 4 | Analyze patterns (Analyzer) |
| FR-F11 | Epic 4 | Generate responses (Synthesizer) |
| FR-F12 | Epic 4 | Quality check (Evaluator) |
| FR-F13 | Epic 5 | Request missing info (Clarifier) |
| FR-F14 | Epic 2 | Extract structured data (Parser) |
| FR-F15 | Epic 7 | Learn patterns (Observer) |
| FR-F16 | Epic 6 | Auto-select domains |
| FR-F17 | Epic 6 | Combine domain contexts |
| FR-F18 | Epic 6 | Mid-flow domain expansion |
| FR-F19 | Epic 5 | Handle corrections |
| FR-F20 | Epic 2 | StorageRepository abstraction |
| FR-F21 | Epic 8 | API endpoints |
| FR-F22 | Epic 8 | CLI with import command |
| FR-A1 | Epic 1 | GeneralFitness base domain |
| FR-A2 | Epic 2 | Strength subdomain |
| FR-A3 | Epic 3 | Running subdomain |
| FR-A4 | Epic 2 | Nutrition subdomain [MVP] |
| FR-A5 | Epic 6 | Swimming subdomain [Post-MVP] |
| FR-A6 | Epic 2 | Domain-specific log schemas |
| FR-A7 | Epic 2 | Domain vocabularies |
| FR-A8 | Epic 4 | Domain expertise for prompts |
| FR-A9 | Epic 4 | Response evaluation rules |
| FR-A10 | Epic 7 | Context management guidance |

## Epic List

### Epic 1: Foundation & First Domain
*Framework skeleton + DomainModule interface validated with GeneralFitness + Test corpus and accuracy infrastructure*

**Quilto:** Monorepo setup, package structure, DomainModule interface, LLM client abstraction (tiered config), basic project tooling (ruff, pyright, pytest), test fixtures (mock_llm, storage_fixture)

**Swealog:** GeneralFitness base domain module (validates the interface works), test corpus generation from Strong CSV ground truth, synthetic test data with variations, accuracy test runner with exercise equivalence mapping

**FRs covered:** FR-F6, FR-A1 + AR3, AR5, AR6, NFR-F4 (accuracy validation infrastructure)

---

### Epic 1.5: Test Corpus (Domain-Agnostic Test Data)
*Comprehensive test data proving Quilto is truly domain-agnostic*

**Added from:** Epic 1 Retrospective (2026-01-09) - identified gap in test coverage

**Quilto:** Generic edge case entries, multilingual test corpus, multi-domain test entries with expected outputs, retrieval and query flow expected outputs

**Non-Fitness Domains:** Journal/diary entries, recipe/cooking logs, study/learning notes, meeting notes - proves framework handles ANY domain

**FRs covered:** NFR-F4 (parsing accuracy validation across domains), FR-F1 (any domain, any format)

**Rationale:** Epic 1 created fitness-only test data. Quilto claims to be domain-agnostic but had zero non-fitness test coverage. This epic ensures the framework is validated against diverse domains before implementation continues.

---

### Epic 2: Input & Storage
*Logging flow + Strength and Nutrition domain parsing*

**Quilto:** Router agent (LOG classification), Parser agent, StorageRepository (6 methods), raw/parsed directory structure, async parsing

**Swealog:** Strength domain schema + vocabulary, Nutrition domain schema + vocabulary, fitness-specific parsing

**FRs covered:** FR-F1, FR-F2, FR-F3, FR-F7, FR-F14, FR-F20, FR-A2, FR-A4, FR-A6, FR-A7 + AR1, AR2

---

### Epic 3: Query & Retrieval
*Query flow + fitness-aware retrieval*

**Quilto:** Router agent (QUERY/BOTH classification), Planner agent (query decomposition, dependency classification), Retriever agent, state machine foundation

**Swealog:** Fitness retrieval patterns, Running domain module

**FRs covered:** FR-F4, FR-F7, FR-F8, FR-F9, FR-A3

**Testing Note (ASR-4 Mitigation):**
- State machine has 13 states and 34 transitions (see state-machine-diagram.md)
- This epic introduces state machine foundation - must include state transition tests
- Create transition matrix test covering all 34 documented transitions
- Test cycle termination conditions (max retries, domain expansion limits)
- Risk score: 6 (High) - state machine bugs cause wrong behavior

---

### Epic 4: Analysis & Response
*Insight generation + fitness expertise*

**Quilto:** Analyzer agent (verdict-last pattern), Synthesizer agent, Evaluator agent, retry loop (2 retries → partial + gaps)

**Swealog:** Fitness expertise prompts, domain-specific evaluation rules

**FRs covered:** FR-F5, FR-F10, FR-F11, FR-F12, FR-A7, FR-A8 + NFR-F7

---

### Epic 5: Human-in-the-Loop
*Clarification & corrections + fitness context*

**Quilto:** Clarifier agent, WAIT_USER state, correction flow (append strategy, upsert semantics)

**Swealog:** Fitness-specific clarification patterns

**FRs covered:** FR-F13, FR-F19

---

### Epic 6: Domain Intelligence
*Multi-domain system + Swimming domain [Post-MVP]*

**Quilto:** Domain auto-selection, multi-domain combination (base + selected), mid-flow domain expansion (Planner + Analyzer can request)

**Swealog:** Swimming domain module [Post-MVP], cross-domain query handling

**FRs covered:** FR-F16, FR-F17, FR-F18, FR-A5

---

### Epic 7: Learning & Personalization
*Observer system + fitness pattern learning*

**Quilto:** Observer agent, global context (markdown format, ~2k tokens), periodic + event-triggered updates, archival strategy

**Swealog:** PR tracking, workout pattern detection, context management guidance

**FRs covered:** FR-F15, FR-A9 + NFR-F9

---

### Epic 8: Interface Layer
*CLI/API + Swealog commands*

**Quilto:** Typer CLI framework, FastAPI endpoints (`/input`, `/query`), batch import support, error cascade (retry → fallback → degrade)

**Swealog:** Fitness-specific CLI commands, batch import for historical logs

**FRs covered:** FR-F21, FR-F22 + NFR-F8

---

## Epic 1: Foundation & First Domain

*Framework skeleton + DomainModule interface validated with GeneralFitness*

### Story 1.1: Initialize Monorepo Structure

As a **Quilto and Swealog developer**,
I want a **properly configured uv workspace with quilto and swealog packages**,
So that **I can develop both packages with shared tooling**.

**Acceptance Criteria:**

**Given** a fresh clone of the repository
**When** I run `uv sync`
**Then** both `quilto` and `swealog` packages are installed in development mode
**And** `swealog` can import from `quilto`
**And** ruff, pyright, and pytest are configured at workspace level

---

### Story 1.2: Define DomainModule Interface

As a **Quilto developer**,
I want a **clear DomainModule interface with Pydantic validation**,
So that **application developers can define domain-specific configuration**.

**Acceptance Criteria:**

**Given** I create a class inheriting from `DomainModule`
**When** I define `description`, `log_schema`, `vocabulary`, and `expertise`
**Then** Pydantic validates all fields correctly
**And** optional fields (`response_evaluation_rules`, `context_management_guidance`) have sensible defaults
**And** `name` defaults to class name if not provided

---

### Story 1.3: Implement LLM Client Abstraction

As a **Quilto developer**,
I want a **tiered LLM configuration that abstracts provider details**,
So that **applications can switch between Ollama and cloud providers without code changes**.

**Acceptance Criteria:**

**Given** a configuration with tiered models (low/medium/high)
**When** I request an LLM call with a tier
**Then** the correct model is used based on configuration
**And** Ollama works with `api_base` override
**And** cloud providers work when API keys are configured

---

### Story 1.4: Create GeneralFitness Base Domain

As a **Swealog developer**,
I want a **GeneralFitness base domain module**,
So that **the DomainModule interface is validated with a real implementation**.

**Acceptance Criteria:**

**Given** the GeneralFitness domain module is defined
**When** I instantiate it
**Then** all DomainModule fields are populated
**And** `description` covers general fitness activities
**And** `log_schema` defines basic fitness entry structure
**And** `vocabulary` includes common fitness terms

---

### Story 1.5: Generate Expected Parser Outputs from Ground Truth

As a **Swealog developer**,
I want **expected ParserOutput JSON generated from Strong CSV**,
So that **Parser accuracy can be validated against real structured data (NFR-F4)**.

**Acceptance Criteria:**

**Given** the 93 synthesized entries in `tests/corpus/fitness/entries/from_csv/`
**When** I run the corpus generation script
**Then** each entry has matching expected JSON in `tests/corpus/fitness/expected/parser/`
**And** expected outputs are derived from `strong_workouts.csv` (not LLM-generated)
**And** field mapping covers exercise, weight, reps, sets, date
**And** `exercise_equivalences.yaml` is created in `tests/corpus/` with all unique exercises from CSV (~25-30 entries)
**And** each equivalence entry starts with the CSV exercise name as the canonical form

**Notes:**
- `exercise_equivalences.yaml` is test infrastructure, not application code
- Used for semantic comparison of exercise names during accuracy testing
- Variants (Korean names, abbreviations) are added incrementally as test failures reveal them

---

### Story 1.6: Generate Synthetic Test Data with Variations

As a **Swealog developer**,
I want **synthetic test entries with controlled variations**,
So that **Parser handles edge cases, multiple domains, and writing styles**.

**Acceptance Criteria:**

**Given** variation rules in `tests/corpus/variation_rules/`
**When** I generate synthetic entries with human-provided patterns
**Then** entries cover: edge cases (typos, minimal, verbose), multilingual (Korean/English), multi-domain scenarios
**And** each synthetic entry has human-validated expected output
**And** synthetic data is stored in `entries/synthetic/` (separate from `from_csv/`)
**And** synthetic entries are NOT used for primary accuracy metrics
**And** at least 50 synthetic entries are generated for initial edge case coverage

**Notes:**
- Volume target: 50 synthetic entries in Epic 1, grow toward 500+ total corpus over time
- Current corpus: 93 from_csv + 50 synthetic = 143 entries after Epic 1
- Synthetic entries test Parser robustness, not accuracy metrics
- Corpus growth continues in later epics as new domains/edge cases emerge

---

### Story 1.7: Create Test Fixtures and Accuracy Runner

As a **Swealog developer**,
I want **pytest fixtures and an accuracy test runner**,
So that **I can run parser accuracy tests locally with semantic exercise name comparison**.

**Acceptance Criteria:**

**Given** pytest is configured in the monorepo (Story 1.1)
**When** I run the accuracy test suite
**Then** `conftest.py` provides core fixtures: `mock_llm`, `storage_fixture`, `domain_fixture`
**And** accuracy runner loads expected JSON from `tests/corpus/fitness/expected/parser/`
**And** accuracy runner uses `exercise_equivalences.yaml` for exercise name comparison
**And** numeric fields (weight, reps, sets) use exact match comparison
**And** test output reports field-level accuracy (per field) and entry-level accuracy (all fields correct)
**And** `--use-real-ollama` pytest option is available for integration testing

**Notes:**
- `mock_llm` fixture returns canned responses; depends on LLMClient interface from Story 1.3
- `storage_fixture` provides isolated file storage per test; depends on StorageRepository from Story 2.1 (can stub initially)
- Accuracy runner is test infrastructure, not application code

**Dependencies & Sequencing:**
- This story creates test *infrastructure* (scaffolding)
- Full accuracy tests cannot run until Parser agent exists (Story 2.3, Epic 2)
- Expected sequence: Create fixtures → Epic 2 delivers Parser → Run accuracy tests
- `storage_fixture` can use a stub implementation initially, replaced with real StorageRepository after Story 2.1

---

## Epic 1.5: Test Corpus (Domain-Agnostic Test Data)

*Comprehensive test data proving Quilto is truly domain-agnostic*

**Origin:** Epic 1 Retrospective (2026-01-09) identified that all test data was fitness-specific, despite Quilto being a domain-agnostic framework. This epic ensures comprehensive test coverage across multiple domains.

**Directory Structure to Populate:**
```
tests/corpus/
├── generic/
│   ├── edge_cases/          # Story 1.5-1
│   └── multilingual/        # Story 1.5-2
├── multi_domain/
│   ├── entries/             # Story 1.5-3
│   └── expected/parser/     # Story 1.5-4
└── fitness/
    ├── entries/human/       # Story 1.5-7
    └── expected/
        ├── retrieval/       # Story 1.5-5
        └── query/           # Story 1.5-6
```

### Story 1.5-1: Create Generic Edge Case Test Entries

As a **Quilto developer**,
I want **generic edge case test entries that are domain-agnostic**,
So that **Parser robustness is validated across malformed, empty, and unicode inputs**.

**Acceptance Criteria:**

**Given** the `tests/corpus/generic/edge_cases/` directory
**When** I create edge case entries
**Then** entries cover: empty input, whitespace-only, unicode edge cases (emoji, RTL, special chars)
**And** entries cover: extremely long input, extremely short input, malformed markdown
**And** entries cover: injection attempts (SQL-like, prompt injection patterns)
**And** each entry has human-validated expected output (may be empty/error for invalid inputs)
**And** at least 20 edge case entries are created

**Notes:**
- These are NOT fitness-specific - they test Parser's general robustness
- Expected outputs may indicate "unparseable" or return empty structure
- Focus on inputs that could break parsing logic

---

### Story 1.5-2: Create Generic Multilingual Test Corpus

As a **Quilto developer**,
I want **multilingual test entries beyond Korean/English fitness**,
So that **Parser handles diverse languages and scripts correctly**.

**Acceptance Criteria:**

**Given** the `tests/corpus/generic/multilingual/` directory
**When** I create multilingual entries
**Then** entries cover: pure English, pure Korean, Korean-English mixed
**And** entries cover: entries with numbers in different formats (1,000 vs 1.000 vs 1000)
**And** entries cover: date formats (YYYY-MM-DD, MM/DD/YYYY, Korean date format)
**And** entries are domain-agnostic (not fitness-specific)
**And** each entry has human-validated expected output
**And** at least 15 multilingual entries are created

**Notes:**
- Focus on language/script handling, not domain-specific parsing
- Test number/date normalization across locales
- Can include simple journal-style entries

---

### Story 1.5-3: Create Multi-Domain Test Entries

As a **Quilto developer**,
I want **test entries for non-fitness domains**,
So that **Quilto proves it handles ANY domain, not just fitness**.

**Acceptance Criteria:**

**Given** the `tests/corpus/multi_domain/entries/` directory
**When** I create multi-domain entries
**Then** entries cover at least 3 non-fitness domains:
  - Personal journal / diary entries (mood, daily reflections)
  - Recipe / cooking logs (ingredients, cooking time, notes)
  - Study / learning notes (topics, duration, comprehension)
**And** each domain has at least 10 entries with varying complexity
**And** entries include: minimal, verbose, mixed-language variations
**And** total of at least 30 non-fitness entries are created

**Example Domains:**
- **Journal:** "Felt anxious today. Meeting with boss went better than expected. Need to remember to breathe."
- **Cooking:** "Made kimchi jjigae - 300g pork belly, 1 cup aged kimchi, 30 min simmer. Too salty."
- **Study:** "Studied calculus 2 hours. Integration by parts finally clicked. Review chain rule tomorrow."

---

### Story 1.5-4: Create Multi-Domain Expected Parser Outputs

As a **Quilto developer**,
I want **expected parser outputs for non-fitness entries**,
So that **accuracy can be measured for any domain**.

**Acceptance Criteria:**

**Given** the multi-domain entries from Story 1.5-3
**When** I create expected outputs in `tests/corpus/multi_domain/expected/parser/`
**Then** each entry has matching expected JSON
**And** expected outputs are human-validated (not LLM-generated)
**And** schemas are defined for each test domain (Journal, Cooking, Study)
**And** schemas are stored in `tests/corpus/schemas/` alongside existing schemas

**Schema Examples:**
```python
class JournalEntry(BaseModel):
    mood: str | None = None
    topics: list[str] = []
    date: str | None = None

class CookingEntry(BaseModel):
    dish_name: str
    ingredients: list[str] = []
    cooking_time_minutes: int | None = None
    notes: str | None = None

class StudyEntry(BaseModel):
    subject: str
    duration_minutes: int | None = None
    topics: list[str] = []
    notes: str | None = None
```

---

### Story 1.5-5: Create Retrieval Expected Outputs

As a **Quilto developer**,
I want **expected outputs for Retriever agent testing**,
So that **retrieval accuracy can be validated (Epic 3 preparation)**.

**Acceptance Criteria:**

**Given** the `tests/corpus/fitness/expected/retrieval/` directory
**When** I create retrieval test cases
**Then** test cases define: input query, date range, expected entries returned
**And** test cases cover: date-based retrieval, keyword-based retrieval, pattern matching
**And** test cases use existing fitness entries from `from_csv/` and `synthetic/`
**And** at least 15 retrieval test cases are created
**And** format is JSON with `query`, `strategy`, `expected_entry_ids` fields

**Example:**
```json
{
  "query": "bench press workouts last week",
  "strategy": {
    "type": "date_range",
    "start": "2019-01-21",
    "end": "2019-01-28",
    "keywords": ["bench press", "벤치프레스"]
  },
  "expected_entry_ids": ["2019-01-23", "2019-01-25", "2019-01-28"]
}
```

---

### Story 1.5-6: Create Query Flow Expected Outputs

As a **Quilto developer**,
I want **expected outputs for end-to-end query testing**,
So that **full query flow accuracy can be validated (Epic 3-4 preparation)**.

**Acceptance Criteria:**

**Given** the `tests/corpus/fitness/expected/query/` directory
**When** I create query test cases
**Then** test cases define: input query, expected analysis points, expected response elements
**And** test cases cover: simple queries, complex multi-part queries, queries with insufficient data
**And** test cases use existing fitness entries as context
**And** at least 10 query test cases are created
**And** format allows fuzzy matching (key points, not exact text)

**Example:**
```json
{
  "query": "How has my bench press progressed?",
  "context_entries": ["2019-01-23", "2019-02-15", "2019-03-10"],
  "expected_analysis_points": [
    "weight_progression_identified",
    "rep_range_noted",
    "time_span_mentioned"
  ],
  "expected_response_elements": [
    "mentions_starting_weight",
    "mentions_current_weight",
    "provides_trend_assessment"
  ]
}
```

---

### Story 1.5-7: Create Human-Curated Fitness Entries

As a **Swealog developer**,
I want **human-written fitness entries beyond CSV-derived data**,
So that **Parser handles natural human writing styles not captured in structured export**.

**Acceptance Criteria:**

**Given** the `tests/corpus/fitness/entries/human/` directory
**When** I create human-curated entries
**Then** entries are written naturally (not derived from CSV structure)
**And** entries cover writing styles not in `from_csv/`: stream-of-consciousness, very casual, highly detailed
**And** entries include context that CSV lacks: feelings, environment, interruptions
**And** each entry has human-validated expected output
**And** at least 15 human-curated fitness entries are created

**Examples:**
- "Started with bench but shoulder felt off so switched to machines. Did some chest flies 15kg each hand, maybe 4 sets? Lost count. Finished with stretching."
- "오늘 컨디션 별로였는데 그래도 데드 쳤음. 140으로 시작해서 160까지 올렸다가 마지막에 힘빠져서 140으로 마무리. 총 6세트인가 7세트 한 듯"

---

### Story 1.5-8: Create Non-Fitness Domain Module for Testing

As a **Quilto developer**,
I want **a simple non-fitness DomainModule for testing**,
So that **domain-agnostic framework behavior can be validated with real code**.

**Acceptance Criteria:**

**Given** the Quilto framework with DomainModule interface
**When** I create a test domain module
**Then** `JournalDomain` module is created in `tests/domains/` (not in packages/)
**And** module defines: description, log_schema (JournalEntry), vocabulary, expertise
**And** module is usable by accuracy runner for multi-domain parsing tests
**And** module demonstrates DomainModule works for non-fitness use cases
**And** tests verify JournalDomain instantiates correctly and validates entries

**Notes:**
- This is TEST code, not application code (lives in tests/, not packages/)
- Proves DomainModule interface is truly domain-agnostic
- Can be used as template for future domain implementations

**Example:**
```python
class JournalDomain(DomainModule):
    """Test domain for personal journal entries."""

journal_domain = JournalDomain(
    description="Personal journal and diary entries including mood, reflections, and daily notes.",
    log_schema=JournalEntry,
    vocabulary={
        "felt": "feeling",
        "stressed": "stress",
        "happy": "happiness",
    },
    expertise="Emotional awareness, daily reflection patterns, mood tracking over time.",
)
```

---

## Epic 2: Input & Storage

*Logging flow + Strength domain parsing*

### Story 2.1: Implement StorageRepository Interface

As a **Quilto developer**,
I want a **StorageRepository with 6 core methods**,
So that **agents can read/write entries without knowing file structure**.

**Acceptance Criteria:**

**Given** a configured `base_path`
**When** I call `get_entries_by_date_range`, `get_entries_by_pattern`, `search_entries`, `save_entry`, `get_global_context`, `update_global_context`
**Then** each method works with the `logs/(raw|parsed)/{YYYY}/{MM}/{YYYY-MM-DD}` structure
**And** raw files are markdown, parsed files are JSON

---

### Story 2.2: Implement Router Agent (LOG Classification)

As a **Quilto developer**,
I want a **Router agent that classifies input as LOG/QUERY/BOTH/CORRECTION**,
So that **input flows to the correct processing path**.

**Acceptance Criteria:**

**Given** raw user input
**When** Router processes it
**Then** it returns `input_type` with confidence score
**And** LOG inputs are declarative statements
**And** QUERY inputs contain question words or question marks
**And** BOTH inputs are correctly split into `log_portion` and `query_portion`

---

### Story 2.3: Implement Parser Agent

As a **Quilto developer**,
I want a **Parser agent that extracts structured data from raw input**,
So that **entries can be stored in both raw and parsed formats**.

**Acceptance Criteria:**

**Given** a LOG input and active domain context
**When** Parser processes it
**Then** raw content is stored as markdown with timestamp header
**And** parsed JSON is generated using domain's `log_schema`
**And** parsing happens asynchronously (user doesn't wait)

---

### Story 2.4: Create Strength Domain Module

As a **Swealog developer**,
I want a **Strength subdomain with schema and vocabulary**,
So that **strength training logs are parsed correctly**.

**Acceptance Criteria:**

**Given** input like "bench 185x5 felt heavy"
**When** parsed with Strength domain
**Then** schema extracts exercise, weight, reps, and notes
**And** vocabulary normalizes "bench" → "bench press"
**And** parsed JSON includes all structured fields

---

### Story 2.5: Create Nutrition Domain Module

As a **Swealog developer**,
I want a **Nutrition subdomain with schema and vocabulary**,
So that **food and meal logs are parsed correctly**.

**Acceptance Criteria:**

**Given** input like "lunch: chicken salad ~500cal, protein shake 30g protein"
**When** parsed with Nutrition domain
**Then** schema extracts meal_type, food_items, calories, and macros (protein, carbs, fat)
**And** vocabulary normalizes common terms ("cal" → "calories", "g protein" → "grams protein")
**And** parsed JSON includes all structured fields
**And** optional fields (macros) are handled gracefully when not provided

---

## Epic 3: Query & Retrieval

*Query flow + fitness-aware retrieval*

### Story 3.1: Extend Router for QUERY/BOTH Classification

As a **Quilto developer**,
I want **Router to handle QUERY and BOTH input types with domain selection**,
So that **queries are routed correctly with relevant domains identified**.

**Acceptance Criteria:**

**Given** a query input and list of available domains
**When** Router processes it
**Then** it returns `selected_domains` based on input matching domain descriptions
**And** `domain_selection_reasoning` explains the choice
**And** BOTH inputs have both `log_portion` and `query_portion` extracted

---

### Story 3.2: Implement Planner Agent

As a **Quilto developer**,
I want a **Planner agent that decomposes queries and creates retrieval strategies**,
So that **complex queries are handled systematically**.

**Acceptance Criteria:**

**Given** a query with domain context
**When** Planner processes it
**Then** it classifies multi-question dependency (INDEPENDENT/DEPENDENT/COUPLED)
**And** creates sub-queries with execution order
**And** defines retrieval strategy (date range, keywords, topical)

---

### Story 3.3: Implement Retriever Agent

As a **Quilto developer**,
I want a **Retriever agent that fetches entries using StorageRepository**,
So that **relevant context is gathered for analysis**.

**Acceptance Criteria:**

**Given** Planner's retrieval strategy
**When** Retriever executes it
**Then** entries are fetched via StorageRepository methods
**And** retrieval attempts are logged with results
**And** all entries in scope are returned (no pre-filtering)

---

### Story 3.4: Create Running Domain Module

As a **Swealog developer**,
I want a **Running subdomain with schema and vocabulary**,
So that **running/cardio logs are parsed and retrieved correctly**.

**Acceptance Criteria:**

**Given** input like "ran 5k in 25:30, felt good"
**When** parsed with Running domain
**Then** schema extracts distance, time, pace, and notes
**And** vocabulary normalizes "ran" → "running", "5k" → "5 kilometers"

---

## Epic 4: Analysis & Response

*Insight generation + fitness expertise*

### Story 4.1: Implement Analyzer Agent

As a **Quilto developer**,
I want an **Analyzer agent that finds patterns and assesses sufficiency**,
So that **queries are answered only when evidence is sufficient**.

**Acceptance Criteria:**

**Given** retrieved entries and domain context
**When** Analyzer processes them
**Then** it produces `analysis` with findings and evidence
**And** `sufficiency_evaluation` identifies gaps with severity (critical/nice_to_have)
**And** `verdict` is generated LAST (after all reasoning)

---

### Story 4.2: Implement Synthesizer Agent

As a **Quilto developer**,
I want a **Synthesizer agent that generates user-facing responses**,
So that **analysis results are communicated clearly**.

**Acceptance Criteria:**

**Given** query and analysis results
**When** Synthesizer processes them
**Then** it generates a natural language response
**And** response is grounded in evidence from analysis
**And** domain expertise is reflected in tone and terminology

---

### Story 4.3: Implement Evaluator Agent with Retry Loop

As a **Quilto developer**,
I want an **Evaluator agent that quality-checks responses**,
So that **users receive accurate, well-supported answers**.

**Acceptance Criteria:**

**Given** query, response, and context
**When** Evaluator checks it
**Then** it returns PASS/FAIL verdict with specific feedback
**And** on FAIL, feedback identifies issues and suggestions
**And** retry loop runs up to 2 times before returning partial + gaps

---

### Story 4.4: Add Fitness Expertise and Evaluation Rules

As a **Swealog developer**,
I want **fitness-specific expertise and evaluation rules in domain modules**,
So that **fitness queries get domain-appropriate analysis and responses**.

**Acceptance Criteria:**

**Given** GeneralFitness and Strength domains
**When** expertise and evaluation rules are added
**Then** Analyzer uses fitness knowledge (progressive overload, recovery, etc.)
**And** Evaluator checks domain-specific rules (e.g., "never recommend exercises for injured body parts")

---

## Epic 5: Human-in-the-Loop

*Clarification & corrections + fitness context*

### Story 5.1: Implement Clarifier Agent

As a **Quilto developer**,
I want a **Clarifier agent that requests missing information from users**,
So that **the system asks rather than guesses when stuck**.

**Acceptance Criteria:**

**Given** gaps identified by Analyzer as non-retrievable
**When** Clarifier processes them
**Then** it generates clear, specific questions for the user
**And** questions reference the original query context
**And** system transitions to WAIT_USER state

---

### Story 5.2: Implement WAIT_USER State

As a **Quilto developer**,
I want a **WAIT_USER state that pauses for user input**,
So that **human-in-the-loop interactions are handled correctly**.

**Acceptance Criteria:**

**Given** system is in WAIT_USER state
**When** user provides response
**Then** response is incorporated into session state
**And** flow resumes at Analyzer (if info provided) or Synthesizer (if declined)
**And** user can decline to answer

---

### Story 5.3: Implement Correction Flow

As a **Quilto developer**,
I want a **correction flow that handles user corrections**,
So that **mistakes in logs can be fixed with audit trail**.

**Acceptance Criteria:**

**Given** Router classifies input as CORRECTION
**When** Parser processes it in correction mode
**Then** target entry is identified from correction hint
**And** correction is appended to raw markdown (not overwritten)
**And** parsed JSON is updated (upsert semantics)

---

### Story 5.4: Add Fitness Clarification Patterns

As a **Swealog developer**,
I want **fitness-specific clarification patterns**,
So that **clarifying questions are contextually appropriate for fitness**.

**Acceptance Criteria:**

**Given** a fitness query with missing context
**When** Clarifier generates questions
**Then** questions reference fitness-specific factors (sleep, stress, prior workouts)
**And** questions use fitness terminology appropriately

---

## Epic 6: Domain Intelligence

*Multi-domain system + Swimming domain*

### Story 6.1: Implement Domain Auto-Selection

As a **Quilto developer**,
I want **Router to auto-select relevant domains based on input**,
So that **the right domain expertise is applied without user configuration**.

**Acceptance Criteria:**

**Given** user input and list of available domains
**When** Router processes it
**Then** it matches input against domain descriptions
**And** returns `selected_domains` list
**And** selection works for single and multi-domain queries

---

### Story 6.2: Implement Multi-Domain Combination

As a **Quilto developer**,
I want **ActiveDomainContext that combines base + selected domains**,
So that **agents receive merged domain knowledge**.

**Acceptance Criteria:**

**Given** base_domain and selected_domains
**When** framework builds ActiveDomainContext
**Then** vocabularies are merged (base + selected)
**And** expertise is concatenated with domain labels
**And** evaluation_rules are combined

---

### Story 6.3: Implement Mid-Flow Domain Expansion

As a **Quilto developer**,
I want **Planner and Analyzer to request domain expansion**,
So that **queries can access additional domains when needed**.

**Acceptance Criteria:**

**Given** a query that needs unloaded domain knowledge
**When** Planner or Analyzer identifies the gap
**Then** gap is marked with `outside_current_expertise=True`
**And** system transitions to EXPAND_DOMAIN state
**And** flow resumes with expanded ActiveDomainContext

---

### Story 6.4: Create Swimming Domain Module

As a **Swealog developer**,
I want a **Swimming subdomain with schema and vocabulary**,
So that **swimming workouts are parsed and analyzed correctly**.

**Acceptance Criteria:**

**Given** input like "swam 40 laps freestyle, 30 min"
**When** parsed with Swimming domain
**Then** schema extracts laps, stroke_type, time
**And** vocabulary normalizes stroke names
**And** cross-domain queries (e.g., "compare running vs swimming cardio") work

---

## Epic 7: Learning & Personalization

*Observer system + fitness pattern learning*

### Story 7.1: Implement Observer Agent

As a **Quilto developer**,
I want an **Observer agent that learns patterns from user data**,
So that **the system improves personalization over time**.

**Acceptance Criteria:**

**Given** recent logs and current global context
**When** Observer processes them
**Then** it identifies new patterns or changes
**And** generates updated global context markdown
**And** consolidates related insights to manage size

---

### Story 7.2: Implement Global Context Storage

As a **Quilto developer**,
I want **global context stored as markdown with size management**,
So that **personalization persists across sessions**.

**Acceptance Criteria:**

**Given** global context file
**When** Observer updates it
**Then** format is markdown with YAML frontmatter
**And** size stays within ~2k tokens (configurable)
**And** archival strategy moves old insights to archive file

---

### Story 7.3: Implement Observer Triggers

As a **Quilto developer**,
I want **Observer to trigger on specific events**,
So that **context updates happen at appropriate times**.

**Acceptance Criteria:**

**Given** the trigger configuration
**When** events occur (post-query, user correction, significant log)
**Then** Observer is triggered appropriately
**And** periodic batch updates are supported
**And** triggers are configurable per application

---

### Story 7.4: Add Fitness Context Management

As a **Swealog developer**,
I want **fitness-specific context management guidance**,
So that **Observer tracks fitness-relevant patterns**.

**Acceptance Criteria:**

**Given** fitness domain modules with context_management_guidance
**When** Observer processes fitness logs
**Then** it tracks PRs, workout frequency, recovery patterns
**And** correlations (sleep vs performance) are identified
**And** guidance informs what patterns to prioritize

---

## Epic 8: Interface Layer

*CLI/API + Swealog commands*

### Story 8.1: Implement Typer CLI Framework

As a **Quilto developer**,
I want a **Typer-based CLI framework**,
So that **applications can expose command-line interfaces**.

**Acceptance Criteria:**

**Given** the quilto CLI module
**When** application extends it
**Then** base commands are available
**And** rich output formatting works
**And** applications can add custom commands

---

### Story 8.2: Implement FastAPI Endpoints

As a **Quilto developer**,
I want **FastAPI endpoints for /input and /query**,
So that **applications can be accessed via HTTP API**.

**Acceptance Criteria:**

**Given** the quilto API module
**When** application mounts it
**Then** POST /input accepts raw text and returns confirmation
**And** POST /query accepts query and returns response
**And** async processing is supported

---

### Story 8.3: Implement Batch Import

As a **Quilto developer**,
I want **CLI import command for batch operations**,
So that **historical data can be imported efficiently**.

**Acceptance Criteria:**

**Given** a file or directory of historical logs
**When** import command is run
**Then** entries are processed through /input endpoint
**And** progress is displayed
**And** errors are collected and reported at end

---

### Story 8.4: Implement Error Cascade

As a **Quilto developer**,
I want **error handling with retry → fallback → degrade cascade**,
So that **the system fails gracefully**.

**Acceptance Criteria:**

**Given** an LLM failure
**When** error cascade is triggered
**Then** same-provider retry happens (up to 3 attempts)
**And** fallback provider is tried (if configured)
**And** graceful degradation returns partial result + error message

---

### Story 8.5: Create Swealog CLI Commands

As a **Swealog developer**,
I want **fitness-specific CLI commands**,
So that **users can interact with Swealog via terminal**.

**Acceptance Criteria:**

**Given** the swealog CLI
**When** user runs commands
**Then** `swealog log "bench 185x5"` logs an entry
**And** `swealog ask "why was my bench heavy?"` runs a query
**And** `swealog import ~/fitness-logs/` imports historical data

---

## Epic 9: CLI Developer Experience

*--debug flag and .env configuration support*

**Status:** Done

---

## Epic 10: Agent Quality Evaluation Infrastructure

*E2E evaluation system with LLM-as-judge comparing Quilto responses to Claude baseline*

**Research Source:** `research/technical-llm-agent-quality-evaluation-research-2026-01-19.md`

**Quilto:** DeepEval integration, pairwise evaluation pipeline, LLM-as-judge with position swap, pytest CI/CD integration

**Swealog:** Fitness-specific evaluation dataset, domain-appropriate rubric criteria

**Success Metrics:**
- Win rate vs Claude: >40% initially, improve over time
- Evaluation coverage: 100% of query categories
- Evaluation cost: <$50/month
- CI evaluation time: <5 min per PR

**Known Issue to Address:** Retrieval strategy should try date-range first, keyword fallback (Planner orchestration fix)

---

### Story 10.1: Create E2E Evaluation Dataset

As a **Quilto developer**,
I want **an E2E evaluation dataset extending existing query test cases**,
So that **pairwise evaluation can compare Quilto responses to Claude baseline**.

**Acceptance Criteria:**

**Given** the existing 10 query test cases in `tests/corpus/fitness/expected/query/`
**When** I extend them for E2E evaluation
**Then** a new `tests/eval/` directory is created with versioned golden dataset
**And** each case includes: query, context_entries, rubric criteria
**And** 40 additional test cases are created covering: retrieval strategy, multi-step reasoning, edge cases
**And** total of 50 E2E test cases exist (10 extended + 40 new)
**And** format is YAML with source reference to original corpus where applicable

**Dataset Structure:**
```
tests/eval/
├── golden/
│   ├── v2026-01-19.yaml           # 50 versioned test cases
│   └── baseline_responses/         # Claude responses (Story 10.2)
└── rubric.yaml                     # Evaluation criteria definitions
```

---

### Story 10.2: Generate Claude Baseline Responses

As a **Quilto developer**,
I want **Claude responses generated for all 50 E2E test cases**,
So that **pairwise comparison has a high-quality baseline**.

**Acceptance Criteria:**

**Given** the 50 E2E test cases from Story 10.1
**When** I run the baseline generation script
**Then** Claude responses are generated for each test case
**And** responses are stored in `tests/eval/golden/baseline_responses/`
**And** responses are versioned with dataset version tag
**And** generation script is idempotent (skips existing responses)
**And** Claude receives same context as Quilto would (retrieved entries)

---

### Story 10.3: Implement Pairwise LLM-as-Judge

As a **Quilto developer**,
I want **a pairwise LLM-as-judge evaluation with position swap**,
So that **Quilto vs Claude comparison is unbiased and reliable**.

**Acceptance Criteria:**

**Given** a test case with Quilto response and Claude baseline
**When** LLM-as-judge evaluates them
**Then** evaluation runs twice: (Quilto, Claude) and (Claude, Quilto) ordering
**And** only consistent wins are counted (both orderings agree)
**And** rubric covers: accuracy, completeness, conciseness, domain expertise
**And** judge returns: winner (A/B/Tie), scores per criterion, reasoning
**And** DeepEval custom metric wraps the pairwise logic

**Bias Mitigation:**
- Position swap mandatory (40% inconsistency without it)
- Anonymized responses (Response A / Response B)
- Consistent wins only counting

---

### Story 10.4: Integrate Evaluation with pytest CI/CD

As a **Quilto developer**,
I want **automated E2E evaluation running on PRs via GitHub Actions**,
So that **quality regressions are caught before merge**.

**Acceptance Criteria:**

**Given** the pairwise evaluation from Story 10.3
**When** a PR is opened
**Then** GitHub Actions runs `pytest tests/eval/`
**And** evaluation reports win-rate vs Claude baseline
**And** PR fails if win-rate drops below threshold (configurable)
**And** evaluation cost is tracked and reported
**And** results are cached to avoid re-running unchanged tests

**CI/CD Configuration:**
```yaml
# .github/workflows/llm-eval.yml
- pytest tests/eval/ --tb=short
- Report win-rate in PR comment
- Fail if regression detected
```

---

### Story 10.5: Fix Retrieval Strategy Priority

As a **Quilto developer**,
I want **Planner to instruct date-range retrieval first with keyword fallback**,
So that **queries with temporal context retrieve correctly**.

**Acceptance Criteria:**

**Given** a query with temporal context (e.g., "last week", "in January")
**When** Planner generates retrieval instructions
**Then** strategy prioritizes date-range search first
**And** falls back to keyword search if date-range returns insufficient results
**And** retrieval strategy priority is configurable
**And** E2E evaluation includes test cases validating this behavior

**Root Cause:** This is a Planner orchestration issue, not Retriever issue. Planner generates `retrieval_instructions` that Retriever executes.

**Files to Modify:**
- Planner agent prompt/logic
- Possibly `PlannerOutput` schema for strategy priority

---

## Epic 11: Dogfooding Iteration 1

*Continuous improvement cycle through real-world usage feedback*

**Origin:** Epic 10 Retrospective (2026-01-20) - Restructured from "LLM Client Reliability"

**Rationale:**
- Original Epic 11 had only 1 story (JSON schema fix) - too narrow
- Epic 10 retrospective revealed gap between unit tests and real LLM behavior
- Dogfooding feedback loop provides continuous improvement mechanism
- Iterative pattern: collect feedback → analyze → fix → repeat

**Quilto:** Feedback recording infrastructure, retrieval priority investigation

**Swealog:** CLI feedback prompts, user feedback collection

**Iteration Pattern:**
```
┌─────────────────────────────────────────────────────────────┐
│  DOGFOODING ITERATION CYCLE                                 │
├─────────────────────────────────────────────────────────────┤
│  1. User runs: swealog auto "..."                           │
│  2. Quilto generates response                               │
│  3. Swealog prompts: "How was this response?"               │
│  4. User provides natural language feedback                 │
│  5. System records: query + intermediate outputs + feedback │
│  6. Collect until sufficient dataset                        │
│  7. Analyze dataset → Generate improvement stories          │
│  8. Implement fixes                                         │
│  9. Archive iteration, start next cycle                     │
└─────────────────────────────────────────────────────────────┘
```

**Feedback Storage Structure:**
```
tests/eval/feedback/
├── active/                    # Current collection
│   └── YYYY-MM-DD_query-id.json
├── archive/
│   ├── iter-001/             # Completed iterations
│   │   ├── records/
│   │   ├── analysis.md
│   │   └── stories-generated.md
│   └── iter-002/
└── README.md
```

**Success Metrics:**
- Feedback collection rate: >80% of dogfooding sessions
- Issue detection: Find issues not caught by unit tests
- Iteration velocity: Complete iteration cycle within 1-2 weeks

---

### Story 11.1: Implement JSON Schema Structured Output

As a **Quilto developer**,
I want **proper JSON schema support for OpenRouter structured output**,
So that **LLM responses reliably parse into Pydantic models**.

**Acceptance Criteria:**

**Given** an LLM call requiring structured output
**When** using OpenRouter providers
**Then** JSON schema is properly formatted for the provider
**And** response parsing handles edge cases gracefully
**And** retry logic handles malformed responses

**Background:** Independent fix identified before Epic 11 restructuring. High priority as it affects all agent outputs.

---

### Story 11.2: Implement Feedback Recording Infrastructure

As a **Quilto developer**,
I want **feedback recording after swealog auto responses**,
So that **real-world usage quality can be tracked and improved**.

**Acceptance Criteria:**

**Given** a completed `swealog auto` response
**When** `--debug` flag is active
**Then** system prompts user for feedback ("How was this response?")
**And** user can provide natural language feedback or skip
**And** system records to `tests/eval/feedback/active/`:
  - Original query
  - All intermediate outputs (Router, Planner, Retriever, Analyzer, Synthesizer)
  - Final response
  - User feedback
  - Timestamp and session metadata
**And** feedback format is JSON for easy analysis

**Storage Format:**
```json
{
  "id": "2026-01-20_abc123",
  "timestamp": "2026-01-20T15:30:00Z",
  "query": "what did I eat last week?",
  "intermediate_outputs": {
    "router": { ... },
    "planner": { ... },
    "retriever": { ... },
    "analyzer": { ... },
    "synthesizer": { ... }
  },
  "final_response": "Based on your logs...",
  "user_feedback": "Retrieved wrong dates, showed this week instead of last week",
  "feedback_sentiment": "negative"
}
```

---

### Story 11.3: Investigate Retrieval Priority Bug

As a **Quilto developer**,
I want **to investigate why retrieval still tries term search before date-range**,
So that **temporal queries retrieve correctly in real usage**.

**Acceptance Criteria:**

**Given** Story 10.5 implemented retrieval strategy priority
**When** investigating the bug with real LLM inference
**Then** root cause is identified (prompt effectiveness, LLM behavior, etc.)
**And** fix is verified with real Ollama (not just mocked tests)
**And** feedback records from 11.2 provide evidence of the issue

**Background:** Epic 10 retrospective revealed that despite Story 10.5 unit tests passing, real usage shows term search still attempted before date-range for temporal queries.

**Investigation Areas:**
- Is Planner actually generating date_range first in `retrieval_instructions`?
- Is the priority prompt guidance strong enough?
- Does real LLM behavior differ from mocked test expectations?

---

### Story 11.4: Analyze Feedback Dataset

As a **Quilto developer**,
I want **to analyze collected feedback with Mary (Analyst)**,
So that **patterns are identified and improvement stories are generated**.

**Acceptance Criteria:**

**Given** sufficient feedback records in `tests/eval/feedback/active/`
**When** Mary and Jongkuk Lim analyze the dataset
**Then** patterns are identified:
  - Which query types get poor feedback?
  - Which intermediate step correlates with quality issues?
  - Are there domain-specific patterns?
**And** improvement stories are generated for next iteration
**And** analysis is documented in `analysis.md`
**And** iteration is archived to `archive/iter-001/`
**And** new iteration begins with fresh `active/` directory

**Analysis Outputs:**
- `archive/iter-001/analysis.md` - Findings and patterns
- `archive/iter-001/stories-generated.md` - Stories for next epic
- Recommendations for Epic 12 scope

---

## Epic 12: Dogfooding Iteration 2

*Improvements derived from Iteration 1 feedback analysis (9 records)*

**Origin:** Story 11.4 Analysis (2026-01-24)
**Analyst:** Mary (Business Analyst) + Jongkuk Lim
**Source:** `tests/eval/feedback/archive/iter-001/analysis.md`

**Key Findings from Iteration 1:**
- Clarification questions never trigger (over-corrected from previous fix)
- Planner skips user logs for recommendation queries (wrong retrieval strategy)
- LLM timeout too long (600s default), malformed JSON causes crashes
- Responses lack detail (brevity prioritized over comprehensiveness)
- Response language doesn't match query language

**Quilto:** Clarifier trigger logic, Planner retrieval strategy, LLM timeout/retry config, Synthesizer prompt
**Swealog:** N/A (framework-level improvements)

---

### Story 12.1: Fix Clarification Trigger Logic

**Priority:** High | **Effort:** Medium (2-4 hours)

**As a** Quilto user,
**I want** the system to ask clarification questions only when truly necessary,
**So that** I'm not over-prompted but critical gaps are addressed.

**Acceptance Criteria:**
1. **Given** Analyzer identifies SUBJECTIVE/CLARIFICATION gaps with severity=critical
   **When** Retriever found 0 relevant entries for the query
   **Then** flow transitions to CLARIFY state

2. **Given** Analyzer identifies critical gaps
   **When** Retriever found relevant entries (count > 0)
   **Then** flow skips CLARIFY and proceeds to Synthesize with available data

3. **Given** no critical non-retrievable gaps
   **When** processing completes
   **Then** no clarification questions are asked

**Evidence:** All 9 iteration 1 records had no clarification. Records `e16dbc36` had critical SUBJECTIVE gaps but went to Synthesize.

---

### Story 12.2: Improve Planner Retrieval Strategy Selection

**Priority:** High | **Effort:** Medium (2-4 hours)

**As a** Quilto user,
**I want** queries about my fitness to always check my logs first,
**So that** responses are personalized rather than generic.

**Acceptance Criteria:**
1. **Given** a recommendation or insight query
   **When** Planner creates retrieval strategy
   **Then** DATE_RANGE is always included as priority 1 strategy

2. **Given** topical/keyword strategy returns 0 entries
   **When** DATE_RANGE fallback is available
   **Then** automatically try DATE_RANGE before concluding "no data"

**Evidence:** Records `e16dbc36` (marathon query) retrieved 0 entries despite running logs existing.

---

### Story 12.3: Add LLM Timeout and Retry Configuration

**Priority:** Medium | **Effort:** Small (1-2 hours)

**As a** Quilto developer,
**I want** configurable LLM timeout with smart retry behavior,
**So that** the system doesn't hang and handles intermittent failures gracefully.

**Acceptance Criteria:**
1. **Given** `LLMConfig`
   **When** timeout is not specified
   **Then** default is 45 seconds (not litellm's 600s default)

2. **Given** LLM returns malformed JSON (JSONDecodeError, ValidationError)
   **When** schema_retry_count < max_schema_retries (default: 2)
   **Then** retry same provider (treat as TRANSIENT, not PERMANENT)

3. **Given** malformed JSON after max_schema_retries exhausted
   **When** fallback provider is configured
   **Then** try fallback provider before degradation

**Evidence:** Records `f89c6142`, `e16dbc36_190829` had malformed JSON from OpenRouter.

---

### Story 12.4: Enhance Synthesizer for Detailed Responses

**Priority:** Medium | **Effort:** Small (1-2 hours)

**As a** Quilto user,
**I want** responses to include reasoning, specific metrics, and log references,
**So that** I understand why recommendations are made based on my data.

**Acceptance Criteria:**
1. **Given** a recommendation response
   **When** Synthesizer generates output
   **Then** response includes WHY (reasoning based on log patterns)

2. **Given** logs with numeric data
   **When** Synthesizer generates output
   **Then** specific metrics are cited with dates

**Evidence:** Records `fec3d15f`, `8e8e6d87`, `14b9034b`, `3ec25871` all requested more detail.

---

### Story 12.5: Add Response Language Detection

**Priority:** Low | **Effort:** Small (1-2 hours)

**As a** Quilto user querying in Korean,
**I want** the final response in Korean,
**So that** the experience feels natural.

**Acceptance Criteria:**
1. **Given** user query in Korean
   **When** Synthesizer generates response
   **Then** response is in Korean

2. **Given** user query in English
   **When** Synthesizer generates response
   **Then** response is in English

**Evidence:** Record `8e8e6d87` - Korean query got English response.

---

### Story 12.6: Analyze Feedback Dataset (Iteration 2)

**Priority:** Medium | **Effort:** Medium (2-4 hours)

**As a** Quilto developer,
**I want** to analyze feedback collected during Epic 12 implementation,
**So that** patterns are identified and improvement stories are generated for Epic 13.

**Acceptance Criteria:**
1. **Given** feedback records in `tests/eval/feedback/active/`
   **When** analysis is completed
   **Then** all records are reviewed with sentiment categorization

2. **Given** analyzed feedback records
   **When** patterns are identified
   **Then** analysis documents which issues persist vs resolved

3. **Given** identified patterns
   **When** improvement stories are generated
   **Then** each story has user story format, acceptance criteria, effort, and priority

4. **Given** iteration complete
   **When** archiving
   **Then** records move to `archive/iter-002/` with analysis.md and stories-generated.md

5. **Given** generated stories
   **When** Epic 13 is scoped
   **Then** priority stories are added to epics.md and sprint-status.yaml

**Dev Notes:**
- Follow same methodology as Story 11.4
- Compare against Iteration 1 to measure improvement
- Focus on: Did 12.1-12.5 fixes resolve the identified patterns?
- Archive to `tests/eval/feedback/archive/iter-002/`

---

## Epic 13: Dogfooding Iteration 3

*Improvements derived from Iteration 2 feedback analysis (7 records)*

**Origin:** Story 12.6 Analysis (2026-01-26)
**Analyst:** Mary (Dev Agent) + Jongkuk Lim
**Source:** `tests/eval/feedback/archive/iter-002/analysis.md`

**Key Findings from Iteration 2:**
- All 6 Iteration 1 patterns RESOLVED by Stories 12.1-12.5
- 6 NEW patterns identified requiring fixes
- Most critical: Temporal recency unawareness (29% of records affected)

**Quilto:** Temporal awareness, retrieval simplification, conversation context, clarification routing
**Swealog:** N/A (framework-level improvements)

---

### Story 13.1: Add Temporal Recency Awareness to Analyzer

**Priority:** High | **Effort:** Medium (2-4 hours)

**As a** Quilto user,
**I want** the system to consider how long ago my workout logs were recorded,
**So that** recommendations account for recovery time and current fitness state.

**Acceptance Criteria:**

1. **Given** retrieved log entries with timestamps
   **When** Analyzer processes the data
   **Then** it calculates "days since most recent entry" and includes this in findings

2. **Given** a recommendation query with logs older than 5 days
   **When** generating recommendations
   **Then** the response acknowledges the time gap

3. **Given** fatigue/soreness evidence from logs older than 7 days
   **When** synthesizing response
   **Then** the system does NOT reference that soreness as "current" or "lingering"

4. **Given** a user who hasn't logged in 7+ days
   **When** asked for a workout recommendation
   **Then** the response suggests a moderate return-to-training approach rather than recovery

**Evidence:** Records `14b9034b`, `4d876936`, `7e6d1d9a` - Users received recovery recommendations despite 6-7 day workout gaps

---

### Story 13.2: Simplify Retrieval with Storage Awareness

**Priority:** High | **Effort:** Medium-Large (4-6 hours)

**As a** Quilto developer,
**I want** retrieval to use date-range strategy with storage awareness and LLM-based relevance filtering,
**So that** Planner makes informed decisions and we eliminate keyword matching edge cases.

**Acceptance Criteria:**

**Part A: Storage Awareness (enables smart date-range selection)**

1. **Given** `StorageRepository`
   **When** `get_storage_summary()` is called
   **Then** it returns: date range with logs (first_date, last_date), entry count per month

2. **Given** Planner generates retrieval instructions
   **When** processing a query
   **Then** Planner first calls storage summary to know what dates have data

3. **Given** storage summary shows logs exist from 2026-01-01 to 2026-01-20
   **When** user asks "what did I do last month?"
   **Then** Planner generates date range within available data (not guessing blindly)

**Part B: Date-Range Only (remove keyword/topical)**

4. **Given** any query requiring context retrieval
   **When** Retriever executes
   **Then** only DATE_RANGE strategy is used (keyword and topical strategies removed)

5. **Given** Planner generates retrieval instructions
   **When** instructions are created
   **Then** only date_range strategy is specified (no keyword/topical instructions)

6. **Given** RetrieverAgent code
   **When** reviewing implementation
   **Then** `_execute_keyword()`, `_execute_topical()`, and `expand_terms()` are removed

**Part C: LLM-Based Relevance Filtering**

7. **Given** date-range returns entries
   **When** Analyzer processes them
   **Then** Analyzer filters entries by query relevance (LLM-based filtering replaces keyword pre-filtering)

8. **Given** a query for "bench press 1RM"
   **When** logs in date range contain "벤치 프레스 60kg"
   **Then** Analyzer identifies and uses that entry (no keyword matching required)

**Rationale:**
- Architecture decision: ~109k chars/year fits in context window
- Original design intent: "Date-based retrieval + hierarchical summarization"
- Keyword retrieval introduced infinite edge cases (Korean spacing, synonyms, abbreviations)
- Storage awareness enables Planner to make informed date-range decisions
- LLM-based filtering at Analyzer is more robust than regex/keyword matching

**Evidence:** Record `151de3d9` - Keyword search failed due to Korean spacing; this architectural change eliminates such issues entirely

**Files to Modify:**
- `packages/quilto/quilto/storage/repository.py` - Add `get_storage_summary()` method
- `packages/quilto/quilto/storage/models.py` - Add `StorageSummary` model
- `packages/quilto/quilto/agents/planner.py` - Call storage summary, only generate date_range instructions
- `packages/quilto/quilto/agents/retriever.py` - Remove keyword/topical methods
- `packages/quilto/quilto/agents/analyzer.py` - Add relevance filtering guidance to prompt

---

### Story 13.3: Implement Conversation Context for Multi-Turn Queries

**Priority:** Medium | **Effort:** Medium (2-4 hours)

**As a** Quilto user,
**I want** the system to remember context from my previous message,
**So that** I don't have to repeat information in follow-up questions.

**Acceptance Criteria:**

1. **Given** user states "I'd like to run a full marathon"
   **When** user immediately follows with "How do I do?"
   **Then** the system understands "do" refers to running a marathon

2. **Given** a LOG-type input that could be a goal statement
   **When** user's next message is a vague question
   **Then** Planner incorporates the previous message context

3. **Given** multi-turn conversation context
   **When** generating retrieval instructions
   **Then** context from previous turns informs date range and Analyzer's relevance filtering

**Evidence:** Record `8628f945` - Marathon context lost between "I'd like to run a full marathon" and "How do I do?"

---

### Story 13.4: Fix Clarification Flow Routing

**Priority:** Medium | **Effort:** Small (1-2 hours)

**As a** Quilto user,
**I want** the system to actually ask clarification questions when needed,
**So that** I can provide missing information for better responses.

**Acceptance Criteria:**

1. **Given** Planner sets `next_action: "clarify"` with `clarify_questions` populated
   **When** the flow processes this output
   **Then** the Clarifier agent is invoked to ask the user

2. **Given** Planner generates clarification questions
   **When** the flow does not route to Clarifier
   **Then** an error is logged indicating routing failure

3. **Given** a vague query like "How do I do?"
   **When** Planner identifies critical subjective gaps
   **Then** the user receives the clarification questions before a response is generated

**Evidence:** Record `8628f945` - Planner generated clarify_questions but they were never asked to user

---

### Story 13.5: Improve Intent Classification for Goal Statements

**Priority:** Medium | **Effort:** Small (1-2 hours)

**As a** Quilto user,
**I want** goal statements like "I want to run a marathon" to be treated as implicit queries,
**So that** I receive guidance without needing to explicitly ask a question.

**Acceptance Criteria:**

1. **Given** input "I'd like to run a full marathon"
   **When** Router classifies input_type
   **Then** it is classified as BOTH (log of goal + implicit query for guidance)

2. **Given** input starting with "I want to..." or "I'd like to..."
   **When** no explicit question is present
   **Then** Router includes query_portion with the implied question

3. **Given** a goal-statement LOG without follow-up
   **When** processing completes
   **Then** the response offers guidance related to the goal

**Evidence:** Record `8628f945` - "I'd like to run a full marathon" was treated as LOG only

---

### Story 13.6: Add Indirect Estimation Fallback in Analyzer

**Priority:** Low | **Effort:** Medium (2-4 hours)

**As a** Quilto user,
**I want** the system to provide indirect estimates when direct data is missing,
**So that** I get useful answers with appropriate disclaimers.

**Acceptance Criteria:**

1. **Given** query for bench press 1RM with only incline press data available
   **When** Analyzer finds no direct bench press records
   **Then** it attempts indirect estimation using related exercises

2. **Given** indirect estimation is performed
   **When** Synthesizer generates response
   **Then** the response clearly states "This is an indirect estimate based on..."

3. **Given** multiple related exercises in logs
   **When** calculating indirect 1RM
   **Then** the system combines information

4. **Given** insufficient data for even indirect estimation
   **When** verdict is "insufficient"
   **Then** the response explains what data would be needed

**Evidence:** Record `151de3d9` - System said "I don't have enough information" instead of attempting indirect estimation

---

### Story 13.7: Analyze Feedback Dataset (Iteration 3)

**Priority:** Medium | **Effort:** Medium (2-4 hours)

**As a** Quilto developer,
**I want** to analyze feedback collected during Epic 13 implementation,
**So that** patterns are identified and improvement stories are generated for Epic 14.

**Acceptance Criteria:**

1. **Given** feedback records in `tests/eval/feedback/active/`
   **When** analysis is completed
   **Then** all records are reviewed with sentiment categorization (positive/mixed/negative)

2. **Given** analyzed feedback records
   **When** patterns are identified
   **Then** analysis documents which Iteration 2 patterns persist vs resolved (comparing to the 6 patterns from iter-002)

3. **Given** identified patterns
   **When** improvement stories are generated
   **Then** each story has: user story format, acceptance criteria, effort estimate, and priority

4. **Given** iteration complete
   **When** archiving
   **Then** records move to `archive/iter-003/` with `analysis.md` and `stories-generated.md`

5. **Given** generated stories
   **When** Epic 14 is scoped
   **Then** priority stories are added to `epics.md` and `sprint-status.yaml`

**Dev Notes:**
- Follow same methodology as Story 11.4 and 12.6
- Compare against Iteration 2 patterns (6 new patterns identified)
- Focus on: Did Stories 13.1-13.6 fixes resolve the identified patterns?
- Archive to `tests/eval/feedback/archive/iter-003/`
- This completes the dogfooding iteration cycle for Epic 13

**Iteration 2 Patterns to Compare Against:**
| # | Pattern | Severity | Fix Applied |
|---|---------|----------|-------------|
| 7 | Temporal Context Blindness | High | Story 13.1 |
| 8 | Keyword Retrieval Misses Exact Matches | High | Story 13.2 |
| 9 | Context Loss in Multi-Turn Conversations | Medium | Story 13.3 |
| 10 | Ambiguous LOG vs QUERY Classification | Medium | Story 13.5 |
| 11 | Clarification Questions Generated But Not Asked | Medium | Story 13.4 |
| 12 | Analyzer Should Attempt Indirect Estimation | Low | Story 13.6 |

---

## Future Epics (Iteration Pattern)

### Epic 14: Dogfooding Iteration 4

*Stories generated from Epic 13 feedback analysis*

**Status:** Backlog (depends on Epic 13 analysis)

