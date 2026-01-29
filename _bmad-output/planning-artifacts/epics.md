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

## Epic 14: Dogfooding Iteration 4

**Status: SKIPPED**

*Skipped on 2026-01-27: Epic 15 restructures orchestration entirely. Fixing issues in old architecture (query.py manual wiring) would be wasted effort. Do fresh dogfooding iteration after Epic 15 completes on new Quilto API.*

*Original stories preserved below for reference when creating post-Epic-15 dogfooding.*

**Source:** `tests/eval/feedback/archive/iter-003/analysis.md` + `human-review-iter-003.md`
**Analysis Date:** 2026-01-26
**Records Analyzed:** 16

**Auto-Analysis vs Human Review Discrepancy:**
| Metric | Auto-Analysis | Human Review |
|--------|---------------|--------------|
| Positive | 81% (13/16) | 50% correct |
| Mixed | 19% (3/16) | 25% partial |
| Negative | 0% | 25% wrong (false positives) |

**Key Findings (Human Review):**
- 5/6 Iteration 2 patterns **RESOLVED** by Epic 13 fixes
- 1/6 patterns **PARTIALLY RESOLVED** (Pattern 11: clarification questions generated but not blocking)
- **NEW Pattern 17 (CRITICAL):** Planner skips retrieval entirely for personalization queries (Records 13, 16)
- 4 records were false positives in auto-analysis (2, 3, 13, 16)
- Pattern 7 (Temporal Blindness) partially persists (Record 3)

**Quilto:** Planner retrieval enforcement, goal context passing, response language matching
**Swealog:** N/A (framework-level improvements)

---

### Story 14.1: Enforce Planner Retrieval for Personalization Queries

**Priority:** CRITICAL | **Effort:** Medium (2-4 hours)

**As a** Quilto user,
**I want** the system to always check my workout logs before giving personalized advice,
**So that** I get responses based on my actual data, not generic guidance.

**Acceptance Criteria:**

1. **Given** a recommendation or personalization query (e.g., "What should I focus on?", "How should I restart training?")
   **When** Planner generates next_action
   **Then** it MUST attempt retrieval before setting `next_action: clarify` or `next_action: synthesize`

2. **Given** Planner sets `next_action: clarify` without retrieval attempt
   **When** storage has workout logs available
   **Then** this is a BUG - Planner should have tried retrieval first

3. **Given** a query that could benefit from user data
   **When** Retriever returns entries (count > 0)
   **Then** Synthesizer response includes personalized insights from those entries

4. **Given** date-range retrieval returns 0 entries
   **When** Planner decides next action
   **Then** ONLY THEN may it fall back to clarify or generic synthesize

**Evidence:**
- Record `bca56fc1`: "요즘 운동 좀 쉬었는데 다시 시작하려면 어떤 강도로 해야할까" - Planner skipped retrieval, gave generic advice despite 19+ entries existing
- Record `ff8c098d`: "What should I focus on?" - Planner set `next_action: clarify` without attempting retrieval, Retriever shows 0 entries/0 strategies

**Root Cause:** Planner logic doesn't enforce "always try retrieval first" for recommendation/personalization queries.

**Files to Modify:**
- `packages/quilto/quilto/agents/planner.py` - Add logic to enforce retrieval before clarify/synthesize for personalization queries
- Planner prompt - Strengthen guidance: "For ANY query that could benefit from user data, ALWAYS attempt retrieval first"

---

### Story 14.2: Pass Goal Context to Synthesizer

**Priority:** High | **Effort:** Small (1-2 hours)

**As a** Quilto user,
**I want** my stated goals to be considered in the response,
**So that** recommendations are tailored to what I want to achieve.

**Acceptance Criteria:**

1. **Given** Router identifies a goal in `log_portion` (e.g., "I want to lose 5kg by summer")
   **When** Synthesizer generates a response
   **Then** the response incorporates the stated goal

2. **Given** input_type is BOTH with goal + query
   **When** Synthesizer receives context
   **Then** `log_portion` content is included in the context

3. **Given** query "What should I focus on?" with goal "lose 5kg by summer"
   **When** response is generated
   **Then** response mentions weight loss strategies, not generic balanced fitness

**Evidence:** Record `ff8c098d` - Router extracted "I want to lose 5kg by summer" but Synthesizer gave generic advice

---

### Story 14.3: Match Response Language to Query Language

**Priority:** Medium | **Effort:** Small (1-2 hours)

**As a** Quilto user,
**I want** responses in the same language I asked my question,
**So that** I can easily understand the answer.

**Acceptance Criteria:**

1. **Given** English query with Korean workout logs
   **When** Synthesizer generates response
   **Then** response is in English

2. **Given** Korean query with English workout logs
   **When** Synthesizer generates response
   **Then** response is in Korean

3. **Given** mixed language input
   **When** determining response language
   **Then** the language of the query (not logs) is used

**Evidence:** Record `39b8e450` - English query "check my shoulder workout frequency" received Korean response

---

### Story 14.4: Fix Evaluator Completeness Check

**Priority:** Low | **Effort:** Small (1-2 hours)

**As a** Quilto developer,
**I want** the Evaluator to correctly assess completeness,
**So that** valid responses are not incorrectly flagged as incomplete.

**Acceptance Criteria:**

1. **Given** request for "all entries from January"
   **When** response includes all stored entries for that period
   **Then** Evaluator marks completeness as "sufficient"

2. **Given** dates with no logged workouts in storage
   **When** response omits those dates
   **Then** Evaluator does not flag as "missing entries"

3. **Given** Retriever output with date range coverage
   **When** Evaluator checks completeness
   **Then** it validates against what exists in storage, not hypothetical entries

**Evidence:** Record `47d6c735` - Evaluator complained about "missing entries for 14, 16, 17, 18, 21" but those dates had no logs

---

### Story 14.5: Clarify Ambiguous Fitness Terms (Optional)

**Priority:** Low | **Effort:** Medium (2-4 hours)

**As a** Quilto user,
**I want** ambiguous fitness terms to be clarified,
**So that** responses match my intent.

**Acceptance Criteria:**

1. **Given** query with ambiguous term like "leg day"
   **When** Planner processes the query
   **Then** it considers asking clarification (strength training vs cardio with leg focus)

2. **Given** no dedicated leg strength training in logs
   **When** user asks about "last leg day"
   **Then** response acknowledges ambiguity or includes both interpretations

**Evidence:** Record `9edecb7c` - "what was my last leg day" returned stair climbing (cardio) instead of leg strength training

**Note:** This story is optional - the current response was technically correct, just potentially not matching user intent.

---

### Story 14.6: Analyze Feedback Dataset (Iteration 4)

**Priority:** Medium | **Effort:** Medium (2-4 hours)

**As a** Quilto developer,
**I want** to analyze feedback collected during Epic 14 implementation,
**So that** patterns are identified and improvement stories are generated for Epic 15.

**Acceptance Criteria:**

1. **Given** feedback records in `tests/eval/feedback/active/`
   **When** analysis is completed
   **Then** all records are reviewed with sentiment categorization

2. **Given** analyzed feedback records
   **When** patterns are identified
   **Then** analysis documents which Iteration 3 patterns persist vs resolved

3. **Given** iteration complete
   **When** archiving
   **Then** records move to `archive/iter-004/` with `analysis.md` and `stories-generated.md`

**Iteration 3 Patterns to Compare Against (Human Review):**
| # | Pattern | Severity | Fix Applied |
|---|---------|----------|-------------|
| 13 | Response Language Mismatch | Minor | Story 14.3 |
| 14 | Evaluator False Negative | Minor | Story 14.4 |
| 15 | Semantic Interpretation Ambiguity | Minor | Story 14.5 (optional) |
| 16 | Goal Context Loss | Moderate | Story 14.2 |
| **17** | **Planner Skips Retrieval** | **CRITICAL** | **Story 14.1** |

---

## Epic 15: Quilto Public API

*Single entry point for Quilto framework with LangGraph orchestration*

**Origin:** Epic 13 Retrospective + CRITICAL Design Document (2026-01-26)
**Design Session:** `_bmad-output/planning-artifacts/quilto-api-design-session.md`
**Architecture:** `_bmad-output/planning-artifacts/architecture.md` (Quilto Public API section)

**Problem Statement:**
- Swealog manually wires 6 agents (~400 lines in query.py)
- Observer infrastructure exists but is NEVER invoked (logs/logs/context/ is EMPTY)
- New agents added to Quilto don't propagate to apps
- Every Quilto application would have to copy the same orchestration code

**Solution:**
- `Quilto` class as single entry point
- `Session` for multi-round conversations with SQLite persistence
- LangGraph for internal orchestration (Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator → Observer)
- Observer triggers automatically on query completion

**Quilto:** Quilto class, Session management, ProcessResult models, ProgressHandler protocol
**Swealog:** Migration from manual wiring to Quilto API

---

### Story 15.1: Create Quilto Public API Models

**Priority:** High | **Effort:** Small (1-2 hours)

**As a** Quilto framework developer,
**I want** well-defined Pydantic models for the public API,
**So that** applications have a clear, type-safe contract for interacting with Quilto.

**Acceptance Criteria:**

1. **Given** a LOG input processed by Quilto
   **When** the result is returned
   **Then** `ProcessResult.parsed_data` contains the structured data

2. **Given** a QUERY input processed by Quilto
   **When** the result is returned
   **Then** `ProcessResult.response`, `confidence`, and `source_entry_ids` are populated

3. **Given** a query requiring clarification
   **When** the agent needs more information
   **Then** `ProcessResult.clarification_questions` contains `ClarificationQuestion` objects with optional options

4. **Given** debug mode enabled
   **When** processing completes
   **Then** `ProcessResult.debug` contains `ProcessDebug` with agent traces

**Files to Create:**
- `packages/quilto/quilto/models.py` - ProcessResult, ClarificationQuestion, ProcessDebug
- `packages/quilto/quilto/handlers.py` - ProgressHandler protocol

---

### Story 15.2: Implement Session Management with SQLite Storage

**Priority:** High | **Effort:** Medium (3-4 hours)

**As a** Quilto framework developer,
**I want** session management with SQLite persistence,
**So that** multi-round conversations are tracked and can survive process restarts.

**Acceptance Criteria:**

1. **Given** a new conversation
   **When** `q.create_session()` is called
   **Then** a new Session is created with unique ID and persisted to SQLite

2. **Given** an existing session ID
   **When** `session_manager.get_session(id)` is called
   **Then** the session is loaded from SQLite with full conversation history

3. **Given** a session with 25 conversation turns
   **When** a new turn is added
   **Then** oldest turns are pruned to keep first + last 19 (20 total)

4. **Given** clarification questions in agent response
   **When** the turn is stored
   **Then** questions (with options) are stored in turn metadata

**Package Structure:**
```
quilto/session/
├── manager.py     # SessionManager
├── session.py     # Session class
├── models.py      # SessionData, ConversationTurn, SessionConfig
└── stores/
    ├── base.py    # SessionStore protocol
    └── sqlite.py  # SQLiteSessionStore
```

---

### Story 15.3: Implement Quilto Class with LangGraph Orchestration

**Priority:** CRITICAL | **Effort:** Large (6-8 hours)

**As a** Quilto framework developer,
**I want** a Quilto class that orchestrates all agents via LangGraph,
**So that** applications have a single entry point and new agents automatically propagate.

**Acceptance Criteria:**

1. **Given** a Quilto instance configured with llm_client, storage, and domains
   **When** `q.create_session()` is called
   **Then** a new Session is returned, ready for processing

2. **Given** a session and user input
   **When** `session.process("text")` is called
   **Then** Router classifies input and appropriate flow executes (LOG/QUERY/CORRECTION)

3. **Given** a QUERY input
   **When** processed through the pipeline
   **Then** all agents run: Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator

4. **Given** Evaluator returns INSUFFICIENT verdict
   **When** retry limit not reached
   **Then** Planner re-plans and Retriever re-retrieves with updated instructions

5. **Given** Observer triggers enabled
   **When** query completes successfully
   **Then** Observer is invoked with post_query trigger

6. **Given** a ProgressHandler configured
   **When** agents execute
   **Then** handler methods are called (on_agent_start, on_agent_complete, on_stage)

**Public API:**
```python
from quilto import Quilto

q = Quilto(
    llm_client=llm_client,
    storage=storage,
    domains=[FitnessDomain()],
    progress_handler=MyUIHandler(),
)

session = q.create_session()
result = await session.process("How was my workout?")
```

---

### Story 15.4: Migrate Swealog to Use Quilto Public API

**Priority:** High | **Effort:** Medium (3-4 hours)

**As a** Swealog application developer,
**I want** to use Quilto's public API instead of manual agent wiring,
**So that** Swealog benefits from new Quilto features automatically.

**Acceptance Criteria:**

1. **Given** the Swealog FastAPI `/query` endpoint
   **When** a query is submitted
   **Then** it uses `Quilto.create_session().process()` internally

2. **Given** the Swealog CLI `auto` command
   **When** user input is processed
   **Then** it uses the same Quilto API

3. **Given** the migration is complete
   **When** `execute_query_pipeline()` is searched for
   **Then** it no longer exists in Swealog (moved to Quilto)

4. **Given** identical inputs before and after migration
   **When** processed through the system
   **Then** outputs are functionally equivalent

**Before (~400 lines):**
```python
router_agent = RouterAgent(llm_client)
planner = PlannerAgent(llm_client)
# ... 300+ more lines ...
```

**After (~50 lines):**
```python
from quilto import Quilto
q = Quilto(...)
session = q.create_session()
result = await session.process(request.text)
```

---

### Story 15.5: Verify Observer Integration and Context Population

**Priority:** High | **Effort:** Small (1-2 hours)

**As a** Quilto framework developer,
**I want** to verify Observer triggers work and context is populated,
**So that** users get personalized responses based on accumulated knowledge.

**Acceptance Criteria:**

1. **Given** a query processed through Quilto
   **When** the query completes successfully
   **Then** `trigger_post_query()` is invoked

2. **Given** Observer determines context should update
   **When** `should_update=True` in ObserverOutput
   **Then** `logs/logs/context/global-context.md` is updated

3. **Given** multiple queries over time
   **When** context accumulates
   **Then** preferences/patterns/facts sections grow

**Evidence of Problem:**
- `logs/logs/context/` directory is currently EMPTY despite Observer infrastructure existing
- This story validates the fix works

---

### Story 15.6: Analyze Feedback Dataset Post-Migration

**Priority:** Medium | **Effort:** Medium (2-3 hours)

**As a** Quilto framework developer,
**I want** to analyze user feedback after migrating to the new Quilto API,
**So that** we identify any new issues or regressions introduced by the architecture change.

**Acceptance Criteria:**

1. **Given** Epic 15 stories 15-1 through 15-5 are complete
   **When** this story begins
   **Then** the new Quilto API is fully functional

2. **Given** at least 10 new feedback records collected
   **When** analyzed
   **Then** patterns are identified and categorized

3. **Given** the analysis is complete
   **When** issues are found
   **Then** stories for Epic 16 are generated

4. **Given** Observer should now be working
   **When** checking logs/logs/context/
   **Then** global-context.md contains accumulated knowledge

5. **Given** skipped Epic 14 issues
   **When** reviewing feedback
   **Then** determine if those issues persist, resolved, or changed

**Archived To:** `tests/eval/feedback/archive/iter-004/`

---

## Epic 16: Clean Swealog Implementation

*Rewrite Swealog CLI as proper Quilto reference implementation*

**Origin:** Epic 15 Retrospective (2026-01-27)
**Source:** Story 15.6 analysis + retrospective discussion

**Problem Statement:**
- Story 15.4 only migrated QUERY flow to Quilto
- Swealog CLI still imports `RouterAgent`, `ParserAgent` directly
- Router runs twice (Swealog calls it, then Quilto calls it again)
- LOG and CORRECTION flows bypass Quilto entirely
- Observer never triggers for LOG inputs
- Half-migration created mixed architecture nightmare

**Solution:**
- Fix Quilto framework gaps (ProgressHandler output, Synthesizer bug, path doubling)
- Rewrite Swealog CLI to single `swealog` command
- All flows through `session.process(mode="auto")`
- Delete `ask_cmd.py`, `log_cmd.py`, simplify `auto_cmd.py`
- Feedback recording via ProgressHandler callbacks

**Target Architecture:**
```bash
# Before (mixed architecture):
swealog auto "text"   # Partial Quilto, Router called twice
swealog ask "query"   # Quilto for query only
swealog log "entry"   # Direct agent calls, bypasses Quilto

# After (clean architecture):
swealog "text"        # Everything through session.process(mode="auto")
swealog --session ID "follow-up"  # Multi-turn conversation
swealog import file.txt           # Batch import (separate command)
```

**Quilto:** ProgressHandler enhancement, Synthesizer fix, path fix
**Swealog:** Complete CLI rewrite as reference implementation

---

### Story 16.1: Add Agent Output to ProgressHandler Callback

**Priority:** HIGH | **Effort:** Small (1-2 hours)

**As a** Quilto framework developer,
**I want** `on_agent_complete` to receive the agent's output,
**So that** applications can capture full intermediate data for debugging and feedback.

**Acceptance Criteria:**

1. **Given** a ProgressHandler implementation
   **When** `on_agent_complete` is called
   **Then** it receives `(agent: str, elapsed: float, output: dict[str, Any])`

2. **Given** the Router agent completes
   **When** `on_agent_complete` is called
   **Then** `output` contains `input_type`, `selected_domains`, etc.

3. **Given** existing ProgressHandler implementations
   **When** the signature changes
   **Then** backwards compatibility is maintained (output is optional with default)

**Files to Modify:**
- `packages/quilto/quilto/handlers.py` - Update Protocol signature
- `packages/quilto/quilto/orchestration.py` - Pass output to callback

---

### Story 16.2: Fix Response Generation Failure

**Priority:** CRITICAL | **Effort:** Medium (2-3 hours)

**As a** Quilto framework developer,
**I want** to fix the Synthesizer error,
**So that** queries actually return useful responses.

**Acceptance Criteria:**

1. **Given** a query processed through Quilto
   **When** the Synthesizer runs
   **Then** it returns a valid response (not "I encountered an error")

2. **Given** the root cause is identified
   **When** the fix is applied
   **Then** feedback records show actual responses

3. **Given** debug mode enabled
   **When** Synthesizer fails
   **Then** the error is logged (not silently swallowed)

**Investigation Points:**
- Check if Analyzer output is malformed
- Check if LLM response parsing fails in synthesize_node
- Check for silent exceptions (like retrieval_history bug in 15.5)

**Files to Investigate:**
- `packages/quilto/quilto/orchestration.py` - analyze_node, synthesize_node
- `packages/quilto/quilto/agents/synthesizer.py` - SynthesizerAgent

---

### Story 16.3: Fix Path Doubling in Observer Context

**Priority:** LOW | **Effort:** Small (30 min)

**As a** Quilto framework developer,
**I want** Observer to write to the correct path,
**So that** context files are where expected.

**Acceptance Criteria:**

1. **Given** Observer updates context
   **When** `apply_updates()` is called
   **Then** file is written to `logs/context/global.md` (not `logs/logs/context/`)

2. **Given** StorageRepository initialized with `base_path="logs"`
   **When** context path is constructed
   **Then** no path doubling occurs

**Root Cause:**
- `StorageRepository` adds `/logs/` but `base_path` may already be set to `logs/`

**Files to Fix:**
- `packages/quilto/quilto/storage/repository.py` OR
- `packages/swealog/swealog/api/dependencies.py`

---

### Story 16.4: Implement Single `swealog` Command

**Priority:** HIGH | **Effort:** Medium (3-4 hours)

**As a** Swealog user,
**I want** a single `swealog` command for all inputs,
**So that** I don't need to choose between `auto`, `ask`, or `log`.

**Acceptance Criteria:**

1. **Given** any text input
   **When** `swealog "text"` is run
   **Then** Quilto classifies and processes appropriately (LOG/QUERY/BOTH/CORRECTION)

2. **Given** a multi-turn conversation
   **When** `swealog --session ID "follow-up"` is run
   **Then** conversation context is preserved

3. **Given** debug mode requested
   **When** `swealog --debug "text"` is run
   **Then** agent traces are displayed

4. **Given** the rewrite is complete
   **When** searching for direct agent imports
   **Then** Swealog CLI has no `from quilto.agents import ...`

**Files to Delete:**
- `packages/swealog/swealog/cli/ask_cmd.py`
- `packages/swealog/swealog/cli/log_cmd.py`

**Files to Simplify:**
- `packages/swealog/swealog/cli/auto_cmd.py` → rename to `main_cmd.py` (~100 lines)
- `packages/swealog/swealog/cli/app.py` - Single command registration
- `packages/swealog/swealog/cli/flows.py` - Delete `execute_log_flow()` (no longer needed)

**Target Implementation:**
```python
@app.command()
def main(
    text: str,
    session_id: str | None = None,
    debug: bool = False,
) -> None:
    quilto = create_quilto(debug=debug)
    session = quilto.get_session(session_id) if session_id else quilto.create_session()
    result = asyncio.run(session.process(text, mode="auto"))
    display_result(result)
```

---

### Story 16.5: Implement Feedback Recording via Callback

**Priority:** MEDIUM | **Effort:** Small (1-2 hours)
**Depends On:** Story 16.1

**As a** Swealog developer,
**I want** feedback recording to capture full agent outputs,
**So that** dogfooding analysis has complete data.

**Acceptance Criteria:**

1. **Given** a ProgressHandler that captures outputs
   **When** query completes
   **Then** all agent outputs are available for feedback recording

2. **Given** `--debug` flag used
   **When** feedback is recorded
   **Then** full intermediate outputs are stored (not just trace summaries)

3. **Given** the new callback signature (from 16.1)
   **When** feedback recorder implements ProgressHandler
   **Then** it receives output dict from each agent

**Files to Modify:**
- `packages/swealog/swealog/cli/feedback.py` - Implement ProgressHandler
- `packages/swealog/swealog/cli/main_cmd.py` - Pass handler to Quilto

---

### Story 16.6: Update Swealog Tests for New CLI

**Priority:** MEDIUM | **Effort:** Medium (2-3 hours)

**As a** Swealog developer,
**I want** tests updated for the single-command architecture,
**So that** CI validates the new design.

**Acceptance Criteria:**

1. **Given** the CLI rewrite (16.4) is complete
   **When** running `make validate`
   **Then** all tests pass

2. **Given** deleted command files (`ask_cmd.py`, `log_cmd.py`)
   **When** their tests are searched for
   **Then** tests are also deleted or migrated

3. **Given** the new `swealog` command
   **When** tested
   **Then** LOG, QUERY, BOTH, CORRECTION flows are all covered

**Files to Update:**
- `packages/swealog/tests/test_cli_ask.py` - DELETE
- `packages/swealog/tests/test_cli_log.py` - DELETE
- `packages/swealog/tests/test_cli_auto.py` - REWRITE for new command
- `packages/swealog/tests/test_cli_debug.py` - UPDATE for new structure

---

### Story 16.7: Review Batch Import Command

**Priority:** LOW | **Effort:** Small (1 hour)
**Status:** Optional - can defer

**As a** Swealog developer,
**I want** to decide if batch import stays as separate command,
**So that** the CLI design is consistent.

**Options:**
1. Keep `swealog import file.txt` as separate command (batch processing is special)
2. Add `swealog --batch file.txt` flag to main command
3. Keep as-is for now, revisit later

**Acceptance Criteria:**

1. **Given** batch import functionality
   **When** design decision is made
   **Then** document the rationale

2. **Given** the chosen approach
   **When** implemented (if any changes)
   **Then** batch import still works correctly

**Files to Review:**
- `packages/swealog/swealog/cli/import_cmd.py`

---

## Epic 17: Query Flow Fix & Framework Stability

*Fix critical bugs blocking query flow + improve framework reliability*

**Origin:** Epic 16 Retrospective (2026-01-28)
**Source:** Story 17.1 investigation + deep dive findings

**Problem Statement:**
- Query flow completely broken: "How was my workout this week?" returns error
- Two critical bugs identified:
  1. Storage path doubling: `--storage ./logs` looks in `./logs/logs/raw/`
  2. Enum validation: LangGraph serializes enums to strings, `strict=True` rejects them
- Four high-priority stability issues:
  - `eval_feedback[0]` type vulnerability
  - Silent Observer failures
  - Unprotected state dict access
  - Overly broad exception handling
- Technical debt: 140+ `# type: ignore` comments

**Solution:**
- Phase 1: Fix critical bugs blocking query flow
- Phase 2: Fix high-priority stability issues
- Phase 3: Address medium-priority robustness issues
- Phase 4: Clean up technical debt

**Quilto Only:** All fixes are in the Quilto framework
**Swealog:** No changes needed (proper Quilto consumer)

---

### Story 17.1: Query Flow Investigation

**Priority:** CRITICAL | **Effort:** Done | **Status:** Complete

**As a** Quilto framework developer,
**I want** to understand why query flow is completely broken,
**So that** we can fix the root causes, not just symptoms.

**Acceptance Criteria:**

1. **Given** the reproduction command
   **When** executed with debug logging
   **Then** full error chain is traced

2. **Given** ValidationError cascade
   **When** investigating orchestration.py
   **Then** root cause is identified (not just symptoms)

3. **Given** 0 entries retrieved
   **When** investigating storage path
   **Then** path doubling issue is confirmed

**Deliverables:**
- Investigation document: `_bmad-output/implementation-artifacts/epic-17/17-1-query-flow-investigation.md`
- Root causes documented
- Fix options analyzed
- Broader issues catalogued

---

### Story 17.2: Remove Storage Path Doubling

**Priority:** CRITICAL | **Effort:** Small (1 hour)

**As a** Quilto framework developer,
**I want** `--storage ./logs` to store in `./logs/`,
**So that** users get expected behavior.

**Acceptance Criteria:**

1. **Given** `StorageRepository(base_path=Path("logs"))`
   **When** `_get_raw_path()` is called
   **Then** returns `logs/raw/...` (not `logs/logs/raw/...`)

2. **Given** `StorageRepository(base_path=Path("."))`
   **When** `_get_parsed_path()` is called
   **Then** returns `parsed/...` (not `logs/parsed/...`)

3. **Given** existing data in `./logs/raw/`
   **When** Retriever searches with `--storage ./logs`
   **Then** entries are found

**Files to Modify:**
- `packages/quilto/quilto/storage/repository.py`
  - Line 48-50: `_ensure_directories()` - remove `/logs/`
  - Line 61-68: `_get_raw_path()` - remove `/logs/`
  - Line 79-86: `_get_parsed_path()` - remove `/logs/`
  - Line 371, 382: `get_global_context()`, `update_global_context()` - remove `/logs/`
  - Line 398: `get_storage_summary()` - remove `/logs/`

**Breaking Change:** Yes - existing code passing parent directory must now pass `logs/` directly

---

### Story 17.3: Remove strict=True from State-Crossing Models

**Priority:** CRITICAL | **Effort:** Small (30 min)

**As a** Quilto framework developer,
**I want** Pydantic models to accept string coercion for enums,
**So that** LangGraph state serialization doesn't break validation.

**Acceptance Criteria:**

1. **Given** `AnalyzerInput(query_type="insight")`
   **When** created with string instead of `QueryType.INSIGHT`
   **Then** Pydantic auto-coerces to enum (no ValidationError)

2. **Given** `AnalyzerOutput` from state dict
   **When** `model_validate(state["analyzer_output"])` is called
   **Then** `verdict: "insufficient"` coerces to `Verdict.INSUFFICIENT`

3. **Given** `RouterOutput` from state dict
   **When** re-validated
   **Then** `input_type: "query"` coerces to `InputType.QUERY`

**Files to Modify:**
- `packages/quilto/quilto/agents/models.py`
  - `RouterOutput` - remove `model_config = ConfigDict(strict=True)`
  - `AnalyzerInput` - remove `model_config = ConfigDict(strict=True)`
  - `AnalyzerOutput` - remove `model_config = ConfigDict(strict=True)`
  - `SynthesizerInput` - remove `model_config = ConfigDict(strict=True)`

**Rationale:** Enums are `str` subclasses (`class QueryType(str, Enum)`), so coercion is type-safe.

---

### Story 17.4: Fix eval_feedback Type Vulnerability

**Priority:** HIGH | **Effort:** Small (30 min)

**As a** Quilto framework developer,
**I want** `eval_feedback` access to be type-safe,
**So that** string vs list confusion doesn't cause subtle bugs.

**Acceptance Criteria:**

1. **Given** `eval_feedback` is a list
   **When** `eval_feedback[0]` is accessed
   **Then** returns first element correctly

2. **Given** `eval_feedback` is accidentally a string
   **When** accessed
   **Then** code handles gracefully (not returns first character)

3. **Given** `eval_feedback` is None or empty
   **When** accessed
   **Then** default value is used

**Files to Modify:**
- `packages/quilto/quilto/orchestration.py`
  - Line 365-367: Add type check before indexing
  - Line 974-975: Add type check before indexing

**Implementation:**
```python
# Before:
evaluation_feedback = eval_feedback[0] if eval_feedback else None

# After:
if isinstance(eval_feedback, list) and eval_feedback:
    evaluation_feedback = eval_feedback[0]
else:
    evaluation_feedback = None
```

---

### Story 17.5: Add Observer Error Propagation

**Priority:** HIGH | **Effort:** Small (1 hour)

**As a** Quilto framework developer,
**I want** Observer failures to be visible to applications,
**So that** context learning issues are detectable.

**Acceptance Criteria:**

1. **Given** Observer throws exception
   **When** `observe_node` catches it
   **Then** error is logged AND returned in state

2. **Given** Observer returns empty context
   **When** state is checked
   **Then** `observer_error` field indicates the issue

3. **Given** ProgressHandler is registered
   **When** Observer fails
   **Then** `on_agent_complete` is called with error info

**Files to Modify:**
- `packages/quilto/quilto/orchestration.py`
  - Lines 931-936: Return error state instead of empty dict

---

### Story 17.6: Protect State Dict Access

**Priority:** HIGH | **Effort:** Medium (1-2 hours)

**As a** Quilto framework developer,
**I want** all state dict access to use `.get()` with defaults,
**So that** missing keys cause graceful degradation, not crashes.

**Acceptance Criteria:**

1. **Given** `state["user_input"]` access
   **When** key is missing
   **Then** default value is used (not KeyError)

2. **Given** `state["_quilto"]` access
   **When** key is missing
   **Then** error is logged and handled gracefully

3. **Given** all direct `state["key"]` patterns
   **When** audited
   **Then** converted to `state.get("key", default)`

**Files to Modify:**
- `packages/quilto/quilto/orchestration.py`
  - Line 750: `state["user_input"]` → `state.get("user_input", "")`
  - Line 807: `state["_quilto"]` → with default
  - Line 871: `state["_quilto"]` → with default
  - Line 902: `state["user_input"]` → with default

---

### Story 17.7: Define State Key Constants

**Priority:** MEDIUM | **Effort:** Medium (2 hours)

**As a** Quilto framework developer,
**I want** state keys defined as constants,
**So that** typos are caught at compile time.

**Acceptance Criteria:**

1. **Given** a new `StateKeys` class or module
   **When** imported
   **Then** all keys are available as constants

2. **Given** all hardcoded state keys
   **When** replaced with constants
   **Then** no string literals for state keys in orchestration.py

3. **Given** a typo in key name
   **When** code is checked by pyright
   **Then** error is detected

**Files to Create/Modify:**
- `packages/quilto/quilto/orchestration.py`
  - Add `class StateKeys` or create separate module
  - Replace all string literals

---

### Story 17.8: Add Domain Context Validation Fallback

**Priority:** MEDIUM | **Effort:** Small (1 hour)

**As a** Quilto framework developer,
**I want** domain context validation to fail gracefully,
**So that** corrupted state doesn't crash the entire flow.

**Acceptance Criteria:**

1. **Given** corrupted `domain_context` dict in state
   **When** `ActiveDomainContext.model_validate()` fails
   **Then** default context is used with warning

2. **Given** validation failure
   **When** flow continues
   **Then** error is logged for debugging

**Files to Modify:**
- `packages/quilto/quilto/orchestration.py`
  - Lines 361, 501, 661, 761, 889: Wrap in try/except with fallback

---

### Story 17.9: Audit Type Ignore Comments

**Priority:** LOW | **Effort:** Medium (2-3 hours)

**As a** Quilto framework developer,
**I want** to reduce `# type: ignore` comments,
**So that** real type issues aren't hidden.

**Acceptance Criteria:**

1. **Given** orchestration.py type ignores
   **When** reviewed
   **Then** each is either fixed or documented with rationale

2. **Given** unnecessary type ignores
   **When** removed
   **Then** pyright passes without them

3. **Given** necessary type ignores
   **When** kept
   **Then** specific error code is used (e.g., `# type: ignore[arg-type]`)

**Files to Audit:**
- `packages/quilto/quilto/orchestration.py` - 15+ type ignores
- `packages/quilto/quilto/llm/client.py` - Several type ignores

---

### Story 17.10: Add Logging to Broad Exception Handlers

**Priority:** LOW | **Effort:** Small (30 min)

**As a** Quilto framework developer,
**I want** broad exception handlers to log what they catch,
**So that** unexpected errors are visible during development.

**Context:**
Issue 10 from Story 17.1 investigation identified `except Exception: pass` patterns that silently swallow all errors, making diagnosis difficult. Rather than narrowing exception types now (high effort, risk of missing edge cases), add logging to make errors visible during development.

**Acceptance Criteria:**

1. **Given** `llm/client.py` line 312 (fallback chain)
   **When** an exception is caught
   **Then** `logger.warning("...", exc_info=True)` logs the error

2. **Given** `llm/client.py` lines 386-410 (`_retry_with_backoff`)
   **When** an exception is caught
   **Then** error is logged with full traceback

3. **Given** `cli/app.py` line 55 (version check)
   **When** an exception is caught
   **Then** error is logged (not silently returning "unknown")

4. **Given** any broad exception handler
   **When** logging is added
   **Then** existing behavior is preserved (no functional change)

**Files to Modify:**
- `packages/quilto/quilto/llm/client.py`
- `packages/swealog/swealog/cli/app.py`

**Future Consideration:** Once log patterns are observed, consider narrowing to specific exception types in a future epic.

---

### Story 17.11: Verify Fixes with Dogfooding

**Priority:** HIGH | **Effort:** Medium (2 hours)
**Depends On:** 17.2, 17.3 (Critical fixes)

**As a** Swealog user,
**I want** the query flow to work correctly,
**So that** I can actually use the application.

**Acceptance Criteria:**

1. **Given** the reproduction command
   ```bash
   uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive "How was my workout this week?"
   ```
   **When** executed
   **Then** returns actual response (not "I encountered an error")

2. **Given** 12 entries in `./logs/raw/`
   **When** query is processed
   **Then** Retriever finds entries (not 0)

3. **Given** ValidationError was the symptom
   **When** query completes
   **Then** no ValidationError in logs

4. **Given** fresh dogfooding session
   **When** multiple queries tested
   **Then** feedback recorded for Epic 18 analysis

---

## Epic 18: Observability & Data Pipeline Fix

*Fix critical Analyzer failure + restore debug visibility + continue dogfooding*

**Source:** Story 17.11 Dogfooding - 3 bugs discovered
**Status:** Backlog

**Quilto:** Fix Analyzer data pipeline, improve debug output, fix type handling
**Swealog:** CLI debug output improvements

**FRs covered:** NFR-F8 (error cascade), observability

---

### Story 18.1: Fix Analyzer Silent Failure

**Priority:** CRITICAL | **Effort:** Medium (2-3 hours)

**As a** Swealog user,
**I want** the Synthesizer to use retrieved data correctly,
**So that** I don't see "no data" responses when data exists.

**Problem:**
- Retriever found 23 entries
- Synthesizer claims "no data"
- Analyzer output was empty `{}`

**Acceptance Criteria:**

1. **Given** Retriever finds N > 0 entries
   **When** Analyzer processes them
   **Then** Analyzer output is NOT empty `{}`

2. **Given** Analyzer returns empty output
   **When** Synthesizer receives state
   **Then** Synthesizer falls back to Retriever entries directly

3. **Given** Analyzer fails silently
   **When** state is checked
   **Then** `analyzer_error` field indicates the issue

4. **Given** full query flow with data
   **When** processed
   **Then** response reflects that data (not "no data")

**Files to Investigate:**
- `packages/quilto/quilto/orchestration.py` - analyze_node
- `packages/quilto/quilto/agents/analyzer.py` - Analyzer agent

---

### Story 18.2: Restore Debug Intermediate Output Printing

**Priority:** HIGH | **Effort:** Small (1-2 hours)

**As a** Swealog developer/user,
**I want** `--debug` to print intermediate agent outputs,
**So that** I can see what each agent received and returned.

**Problem:**
Current `--debug` only shows timing, not agent outputs:
```
ℹ  6042ms - type=query
ℹ  8245ms - action=retrieve
```

**Expected:**
```
[Router] input_type=QUERY, domains=[GeneralFitness], confidence=0.95
[Retriever] found 23 entries
[Analyzer] verdict=sufficient, findings=5
```

**Acceptance Criteria:**

1. **Given** `--debug` flag is set
   **When** each agent completes
   **Then** agent output is printed to terminal

2. **Given** Router/Planner/Retriever/Analyzer/Synthesizer completes
   **When** output is printed
   **Then** key fields are shown in readable format

**Files to Modify:**
- `packages/swealog/swealog/cli/run_cmd.py` - on_agent_complete callback

---

### Story 18.3: Fix Clarification Questions Type Mismatch

**Priority:** HIGH | **Effort:** Small (1 hour)

**As a** Swealog user,
**I want** clarification questions to work correctly,
**So that** the system can ask for missing information.

**Problem:**
```
AttributeError: 'str' object has no attribute 'get'
```
at `session.py:267` - LangGraph serializes questions as strings instead of dicts.

**Acceptance Criteria:**

1. **Given** `clarify_questions_raw` contains dict items
   **When** processed
   **Then** questions extracted correctly

2. **Given** `clarify_questions_raw` contains string items
   **When** processed
   **Then** no AttributeError, strings handled gracefully

**Files to Modify:**
- `packages/quilto/quilto/session/session.py` - `_build_process_result`

**Fix Pattern (from Story 17.4):**
```python
if isinstance(q, dict) and q.get("question"):
    # process dict
elif isinstance(q, str):
    # handle string case
```

---

### Story 18.4: Dogfooding Iteration 6

**Priority:** MEDIUM | **Effort:** Medium (2 hours)
**Depends On:** 18.1, 18.2, 18.3

**As a** Swealog user and developer,
**I want** to test the system after Epic 18 fixes,
**So that** I can discover any remaining issues.

**Acceptance Criteria:**

1. **Given** Stories 18.1-18.3 are complete
   **When** reproduction queries are run
   **Then** previously failing queries now work

2. **Given** `--debug` flag
   **When** query is processed
   **Then** intermediate agent outputs are visible

3. **Given** 10+ queries tested
   **When** dogfooding completes
   **Then** feedback recorded for next iteration

**Query Types to Test:**
- Factual, Insight, Temporal, Comparative
- Goal-related (was broken in 17.11)
- Korean queries
- Comprehensive analysis

---

## Epic 19: Dogfooding Fixes & Design Issues

*Fix broken CORRECTION flow + session DB design contradiction*

**Source:** iter-007 auto-dogfooding + Epic 18 retrospective
**Status:** Backlog

**Quilto:** Fix Parser correction handling, fix session DB default logic
**Swealog:** CLI session persistence fix

**FRs covered:** CORRECTION input type, session continuity

---

### Story 19.1: Fix CORRECTION Input Type Flow

**Priority:** HIGH | **Effort:** Medium (2-3 hours)

**As a** Swealog user,
**I want** to correct previously logged data,
**So that** my fitness records are accurate.

**Problem:**
- Router correctly identifies CORRECTION (0.96 confidence)
- Parser does not process the correction target
- `correction.success: false`, `error_message: "Parser did not identify correction"`
- `final_response: ""` - user receives no feedback

**Evidence:** `tests/eval/feedback/archive/iter-007/2026-01-28_54959ede.json`

**Acceptance Criteria:**

1. **Given** Router classifies input as CORRECTION
   **When** Parser receives the input with correction_target from Router
   **Then** Parser identifies the target entry and correction delta

2. **Given** Parser identifies a correction
   **When** correction is processed
   **Then** the target entry is updated in storage

3. **Given** a correction is processed (success or failure)
   **When** final_response is generated
   **Then** user receives feedback about what was corrected (not empty string)

4. **Given** input "I logged 5 sets but it should be 4"
   **When** processed as CORRECTION
   **Then** the matching entry's set count is updated from 5 to 4

**Files to Investigate:**
- Parser agent's correction-specific prompts/instructions
- How `correction_target` from Router is passed to Parser
- `packages/quilto/quilto/orchestration.py` - correction flow nodes

---

### Story 19.2: Fix Session DB Path Default Logic

**Priority:** MEDIUM | **Effort:** Small (1 hour)

**As a** Swealog user,
**I want** my conversation sessions to persist by default,
**So that** I can continue multi-turn conversations.

**Problem:**
At `packages/swealog/swealog/cli/app.py:319`:
```python
session_db_path = "quilto_sessions.db" if session_id else ":memory:"
```

Logical contradiction:
1. No `--session` → `:memory:` → session UUID generated → lost on exit
2. With `--session <id>` → `quilto_sessions.db` → session was never persisted

**Acceptance Criteria:**

1. **Given** no `--session` flag is provided
   **When** a new session is created
   **Then** session is persisted to `quilto_sessions.db` (not `:memory:`)

2. **Given** a session was created in a previous run
   **When** user provides `--session <id>` in a subsequent run
   **Then** the session is retrieved with full conversation history

3. **Given** user wants ephemeral mode
   **When** an explicit flag is provided (e.g., `--no-persist`)
   **Then** `:memory:` is used

**Files to Modify:**
- `packages/swealog/swealog/cli/app.py` - session_db_path logic

---

### Story 19.3: Dogfooding Iteration 8

**Priority:** MEDIUM | **Effort:** Medium (2 hours)
**Depends On:** 19.1, 19.2

**As a** Swealog user and developer,
**I want** to test the system after Epic 19 fixes,
**So that** I can verify CORRECTION flow and session persistence work correctly.

**Acceptance Criteria:**

1. **Given** Stories 19.1-19.2 are complete
   **When** CORRECTION queries are run
   **Then** previously failing corrections now work

2. **Given** a session is created without `--session` flag
   **When** user runs again with `--session <id>`
   **Then** conversation history is preserved

3. **Given** 10+ queries tested (including CORRECTION type)
   **When** dogfooding completes
   **Then** feedback recorded for next iteration

**Query Types to Test:**
- CORRECTION inputs (primary focus)
- Session continuity (multi-turn)
- QUERY, LOG (regression check)
- Mixed language (Korean + English)

---

## Epic 20: Session + Clarification

*Fix session continuation and verify clarification flow*

**Source:** Epic 19 Retrospective + iter-008 analysis
**Status:** In Progress (reopened 2026-01-29)

**Quilto:** Session continuation (load conversation history), clarification flow verification, context propagation to all agents
**Swealog:** CLI session resume behavior, feedback session_id recording

**FRs covered:** Session continuity, clarification question handling

**Key Insight:** Session persistence ≠ session continuation. Story 19.2 fixed persistence (saving to SQLite), but conversation history is not being used when resuming sessions.

**Reopened (2026-01-29):** Story 20.5 added as critical hotfix. Dogfooding revealed that `conversation_context` is only passed to Planner, not to other agents. When Planner skips retrieval expecting Synthesizer to use context, Synthesizer fails because it never received the context.

---

### Story 20.1: Fix Session Conversation Context

**Priority:** HIGH | **Effort:** Medium (2-3 hours)

**As a** Swealog user,
**I want** my conversation history to be used when resuming a session,
**So that** the system understands context from previous turns.

**Problem:**
- Session persists to SQLite (fixed in 19.2)
- But conversation history is not loaded/used when resuming
- Queries requiring previous context are treated as fresh starts

**Evidence:** `tests/eval/feedback/archive/iter-008-pre/2026-01-29_90c94c13.json`
- User resumed with `--session <id>`
- System didn't use previous conversation history
- Query "What? You didn't look at my previous logs?" treated as fresh start

**Acceptance Criteria:**

1. **Given** a session was created with conversation history
   **When** user resumes with `--session <id>`
   **Then** previous conversation context is loaded from SQLite

2. **Given** loaded conversation history
   **When** agents process the new query
   **Then** previous turns are included in agent context/prompts

3. **Given** a follow-up query like "What about that one?"
   **When** processed in resumed session
   **Then** "that one" correctly resolves from previous turn

4. **Given** a context-dependent query
   **When** no context is available (new session)
   **Then** system asks for clarification OR explains missing context

**Files to Investigate:**
- `packages/quilto/quilto/session/session.py` - conversation history storage/retrieval
- `packages/quilto/quilto/orchestration.py` - how conversation context is passed to agents
- Agent prompt templates - how to inject conversation history

---

### Story 20.2: Verify/Fix Clarification Flow + Session Resume

**Priority:** HIGH | **Effort:** Medium (2-3 hours)

**As a** Swealog user,
**I want** the clarification flow to work with session resume,
**So that** I can answer clarifying questions and continue the conversation.

**Problem:**
- Clarification flow hasn't been tested since session changes
- Expected behavior: Query → Clarification question → User answers → Continue with answer
- This flow should work via session resume

**Acceptance Criteria:**

1. **Given** a query that requires clarification
   **When** processed
   **Then** clarification question is returned with session ID

2. **Given** a clarification question was asked
   **When** user resumes session with answer
   **Then** original query continues with the clarification

3. **Given** clarification answer
   **When** flow continues
   **Then** response reflects both original query AND clarification answer

4. **Given** multiple clarification questions
   **When** answered sequentially
   **Then** all answers are incorporated

**Files to Investigate:**
- `packages/quilto/quilto/orchestration.py` - clarification node handling
- `packages/quilto/quilto/session/session.py` - state persistence for pending queries
- `packages/quilto/quilto/agents/clarifier.py` - clarification generation

---

### Story 20.3: Add Clarification to Automated Dogfooding Script

**Priority:** HIGH | **Effort:** Medium (2 hours)

**As a** developer,
**I want** the dogfooding script to test clarification flows,
**So that** clarification regressions are caught automatically.

**Approach:**
1. Send query that triggers clarification
2. Capture session ID from response
3. Resume session with clarification answer
4. Verify final response incorporates the answer

**Acceptance Criteria:**

1. **Given** a query designed to trigger clarification
   **When** run through automated script
   **Then** session ID is captured from response

2. **Given** captured session ID
   **When** script resumes with answer
   **Then** continuation is processed correctly

3. **Given** clarification test cases
   **When** added to dogfooding suite
   **Then** at least 2 clarification scenarios are covered

**Files to Create/Modify:**
- `tests/eval/dogfooding_script.py` (or similar) - add session resume capability
- Test cases for clarification scenarios

---

### Story 20.4: Dogfooding Iteration 9

**Priority:** MEDIUM | **Effort:** Medium (2 hours)
**Depends On:** 20.1, 20.2, 20.3

**As a** Swealog user and developer,
**I want** to test the system after Epic 20 fixes,
**So that** I can verify session continuation and clarification work correctly.

**Acceptance Criteria:**

1. **Given** Stories 20.1-20.3 are complete
   **When** session resume queries are run
   **Then** conversation context is correctly used

2. **Given** clarification scenarios
   **When** tested via automated script
   **Then** clarification flow completes successfully

3. **Given** 10+ queries tested
   **When** dogfooding completes
   **Then** target success rate >= 90%

**Query Types to Test:**
- **Focused (Session):** Context-dependent follow-ups requiring previous turn
- **Focused (Clarification):** Queries that trigger clarification, then answer via resume
- **General Regression:** LOG, QUERY (factual, insight, temporal), BOTH, multilingual

---

### Story 20.5: Fix Session Context Propagation to All Agents

**Priority:** CRITICAL | **Effort:** Medium (2-3 hours)
**Depends On:** None (hotfix)
**Added:** 2026-01-29 (Epic 20 Retrospective)

**As a** Swealog user resuming a session,
**I want** all agents to have access to my conversation history,
**So that** follow-up questions and clarification answers work correctly.

**Problem:**
- Session conversation context is only passed to Planner agent
- When Planner skips retrieval (`next_action: synthesize`) because answer is in context, Synthesizer cannot access that context
- Router misclassifies clarification answers as LOG (no context to understand follow-ups)
- Feedback JSON doesn't record session_id

**Evidence:** `tests/eval/feedback/active/2026-01-29_4f6d9897.json`
- User query: "Can you tell me which workout you recommended me earlier?"
- User ran with `--session 4dc30d9c-9d0a-4597-8191-a69dc88a15da`
- Planner reasoning: "This information is already present in the conversation context"
- Planner decision: `next_action: synthesize` (skip retrieval)
- Synthesizer response: "I don't have a record" (BUG: never received context)

**Root Cause:**
`orchestration.py` only passes `conversation_context` to `PlannerInput`. Other agents (Router, Analyzer, Synthesizer, Evaluator, Observer) don't receive it.

**Acceptance Criteria:**

1. **Given** conversation context exists in state
   **When** Router processes input
   **Then** RouterInput includes conversation_context

2. **Given** conversation context exists in state
   **When** Analyzer processes entries
   **Then** AnalyzerInput includes conversation_context

3. **Given** conversation context exists in state
   **When** Synthesizer generates response
   **Then** SynthesizerInput includes conversation_context

4. **Given** conversation context exists in state
   **When** Evaluator checks response
   **Then** EvaluatorInput includes conversation_context

5. **Given** conversation context exists in state
   **When** Observer updates global context
   **Then** ObserverInput includes conversation_context

6. **Given** a query like "What workout did you recommend earlier?"
   **When** Planner skips retrieval (next_action: synthesize)
   **Then** Synthesizer can answer from conversation context

7. **Given** feedback recording with `--session <id>`
   **When** session_id is provided via CLI
   **Then** session_id is recorded in feedback JSON

**Files to Modify:**
- `packages/quilto/quilto/agents/models.py` - Add conversation_context to 5 Input models
- `packages/quilto/quilto/orchestration.py` - Pass context in 5 node functions
- `packages/quilto/quilto/agents/router.py` - Update prompt
- `packages/quilto/quilto/agents/analyzer.py` - Update prompt
- `packages/quilto/quilto/agents/synthesizer.py` - Update prompt
- `packages/quilto/quilto/agents/evaluator.py` - Update prompt
- `packages/quilto/quilto/agents/observer.py` - Update prompt
- `packages/swealog/swealog/cli/feedback.py` - Add session_id to SessionMetadata
- `packages/swealog/swealog/cli/app.py` - Pass session_id to recording

---

## Epic 21: Correction Redesign

*Architectural change: edit raw markdown in-place, not create new entries*

**Source:** Epic 19 Retrospective + iter-008-pre user feedback
**Status:** Backlog

**Quilto:** Correction flow redesign, raw file editing, re-parsing
**Swealog:** None (all changes in Quilto)

**FRs covered:** CORRECTION semantics, raw file editing

**Key Insight:** Current CORRECTION creates a new entry, but user expectation is: modify the raw markdown file at the relevant section, then re-parse. This is an architectural change, not just a prompt fix.

**User Feedback:** "Ideal is that fix previous records in raw file... modify raw/2026-01-26.md at ## 18:33 part and run parser agent then give it to application so that it handles whether to update parsed file or not."

---

### Story 21.1: Redesign CORRECTION to Edit Raw Markdown In-Place

**Priority:** CRITICAL | **Effort:** Large (4-6 hours)

**As a** Swealog user,
**I want** corrections to modify the original raw entry,
**So that** my log files maintain accurate history without duplicates.

**Problem:**
- Current CORRECTION creates a new raw entry and new parsed entry
- User expects: modify existing raw file section, not create new file

**Current Flow:**
```
User: "Actually my run was 3km not 5km"
→ Creates new raw file (wrong!)
→ Creates new parsed entry (wrong!)
```

**Expected Flow:**
```
User: "Actually my run was 3km not 5km"
→ Identifies target entry (raw/2026-01-26.md, ## 18:33 section)
→ Modifies that section in-place
→ Re-parses the modified file
→ Updates parsed entry
```

**Acceptance Criteria:**

1. **Given** a CORRECTION request
   **When** target entry is identified
   **Then** the original raw file is located (not a new file created)

2. **Given** target raw file and section
   **When** correction is applied
   **Then** only the specific section is modified

3. **Given** correction applied to raw file
   **When** no new raw file is created
   **Then** existing file modification timestamp is updated

**Files to Modify:**
- `packages/quilto/quilto/orchestration.py` - correction_node logic
- `packages/quilto/quilto/agents/parser.py` - correction output format

---

### Story 21.2: Implement Surgical Edit (Preserve Surrounding Content)

**Priority:** HIGH | **Effort:** Medium (2-3 hours)
**Depends On:** 21.1

**As a** Swealog user,
**I want** corrections to only modify the relevant section,
**So that** other log entries in the same file are preserved.

**Problem:**
Raw files may contain multiple entries (e.g., multiple workout logs on same day). Correction must edit only the target section.

**Example:**
```markdown
# 2026-01-26

## 08:00 - Morning Run
Ran 5km in 30 minutes. Felt good.

## 18:33 - Evening Treadmill  ← ONLY EDIT THIS
40 minutes at 8kph
```

**Acceptance Criteria:**

1. **Given** raw file with multiple sections
   **When** correction targets one section
   **Then** only that section is modified

2. **Given** correction edit
   **When** applied
   **Then** surrounding markdown structure is preserved (headers, formatting)

3. **Given** section boundaries
   **When** edit is applied
   **Then** content before and after target section is unchanged

**Files to Modify:**
- Create utility function for surgical markdown section editing
- `packages/quilto/quilto/storage/` - file editing utilities

---

### Story 21.3: Re-Parse Modified Raw File After Correction

**Priority:** HIGH | **Effort:** Medium (2-3 hours)
**Depends On:** 21.2

**As a** Swealog user,
**I want** the parsed entry to update after raw file correction,
**So that** structured data reflects the correction.

**Flow:**
1. Raw file is modified (21.1, 21.2)
2. Parser re-parses the modified raw file
3. Parsed entry is updated (not created new)

**Acceptance Criteria:**

1. **Given** raw file has been corrected
   **When** re-parsing is triggered
   **Then** Parser processes the modified section

2. **Given** Parser output for corrected section
   **When** compared to existing parsed entry
   **Then** existing parsed entry is updated (not duplicated)

3. **Given** other sections in the same raw file
   **When** re-parsing runs
   **Then** their parsed entries are unchanged

**Files to Modify:**
- `packages/quilto/quilto/orchestration.py` - post-correction re-parse flow
- `packages/quilto/quilto/storage/` - parsed entry update logic

---

### Story 21.4: Improve Parser Correction Entry Matching

**Priority:** MEDIUM | **Effort:** Medium (2-3 hours)

**As a** Swealog user,
**I want** the Parser to reliably identify which entry to correct,
**So that** corrections target the right data.

**Problem:**
- Parser LLM sometimes returns `is_correction: false` despite correction context
- Entry matching fails because truncated content summaries don't give enough info
- Issue is intermittent (LLM-dependent)

**Options:**
1. **Improve prompt:** Include full raw_content (not truncated at 50 chars)
2. **Pre-matching heuristic:** Use fuzzy text matching to narrow candidates before LLM
3. **Simplify:** Always use most recent entry matching correction domain + date hints

**Acceptance Criteria:**

1. **Given** correction request mentioning specific details (e.g., "5 sets of pull-ups")
   **When** Parser processes with recent entries
   **Then** correct entry is matched >= 90% of the time

2. **Given** recent entries list
   **When** provided to Parser
   **Then** includes sufficient detail for matching (full content, not truncated)

3. **Given** ambiguous correction (multiple possible matches)
   **When** Parser cannot determine target
   **Then** clarification is requested (not silent failure)

**Files to Modify:**
- `packages/quilto/quilto/agents/parser.py` - correction prompt, entry formatting
- Potentially add pre-matching heuristic utility

---

### Story 21.5: Dogfooding Iteration 10

**Priority:** MEDIUM | **Effort:** Medium (2 hours)
**Depends On:** 21.1, 21.2, 21.3, 21.4

**As a** Swealog user and developer,
**I want** to test the CORRECTION redesign,
**So that** I can verify raw file editing works correctly.

**Acceptance Criteria:**

1. **Given** Stories 21.1-21.4 are complete
   **When** CORRECTION queries are run
   **Then** raw files are modified in-place (not new files created)

2. **Given** multi-section raw files
   **When** corrections are applied
   **Then** only target sections are modified

3. **Given** 10+ queries tested
   **When** dogfooding completes
   **Then** CORRECTION success rate >= 80%

**Query Types to Test:**
- **Focused (CORRECTION):** Various correction scenarios (value change, detail addition, removal)
- **Edge Cases:** Same-day multiple entries, ambiguous corrections
- **General Regression:** LOG, QUERY, BOTH, session resume, clarification

---

## Epic 22: Global Context / Observer Refinement

*Restrict Observer to user-stated info only*

**Source:** Epic 19 Retrospective + iter-008-pre user feedback
**Status:** Backlog

**Quilto:** Observer agent behavior, global context scope
**Swealog:** None (all changes in Quilto)

**FRs covered:** Global context management, user memory system

**Key Insight:** Observer should function like Claude/ChatGPT memory - only persist user preferences, goals, and behavioral insights. Never persist agent recommendations or per-session facts.

**User Feedback:** "Observer should only note something from me not from agents." and "Global context is supposed to be user's preference, goal, insights... Think of how Claude or ChatGPT manages user memory."

---

### Story 22.1: Observer Only Persists User-Stated Information

**Priority:** HIGH | **Effort:** Medium (2-3 hours)

**As a** Swealog user,
**I want** Observer to only save what I actually said,
**So that** my preferences aren't fabricated from agent suggestions.

**Problem:**
- Observer stores Synthesizer recommendations as user preferences
- Example: User asked about motivation → Synthesizer suggested "light workout" → Observer stored "User prefers light or mobility-focused workout"
- The user never stated this preference

**Acceptance Criteria:**

1. **Given** Synthesizer recommendation in response
   **When** Observer analyzes the interaction
   **Then** recommendation is NOT stored as user preference

2. **Given** user explicitly states preference (e.g., "I prefer morning workouts")
   **When** Observer processes
   **Then** preference IS stored in global context

3. **Given** agent-generated content vs user input
   **When** Observer decides what to persist
   **Then** clear distinction is made (only user input persisted)

**Files to Modify:**
- `packages/quilto/quilto/agents/observer.py` - prompt/logic to distinguish user vs agent content

---

### Story 22.2: Restrict Global Context Scope

**Priority:** HIGH | **Effort:** Medium (2-3 hours)

**As a** Swealog user,
**I want** global context to only contain preferences, goals, and insights,
**So that** it doesn't become a noisy fact dump.

**Problem:**
- Observer stores per-session facts like "run_2026-01-26: duration_minutes: 40"
- This belongs in structured storage (parsed entries), not global context
- Global context should be: preferences, stated goals, behavioral patterns

**Mental Model:**
```
CORRECT (global context):
- "User prefers outdoor running over treadmill"
- "User's goal: run 10km by March"
- "When user says 'run', they mean outdoor jogging"

WRONG (should NOT be in global context):
- "run_2026-01-26: duration_minutes: 40, distance_km: 5.33"
- "User did 3 sets of squats on Monday"
```

**Acceptance Criteria:**

1. **Given** correction or log interaction
   **When** Observer extracts facts
   **Then** per-session facts are NOT stored in global context

2. **Given** user states a preference or goal
   **When** Observer processes
   **Then** preference/goal IS stored in global context

3. **Given** behavioral pattern observed over multiple sessions
   **When** Observer identifies it
   **Then** pattern MAY be stored as insight (not raw facts)

**Files to Modify:**
- `packages/quilto/quilto/agents/observer.py` - context scope filtering
- Possibly add validation/filtering layer

---

### Story 22.3: Add Validation - Observer Cannot Store Unstated Facts

**Priority:** MEDIUM | **Effort:** Medium (2 hours)

**As a** developer,
**I want** validation that Observer only stores user-stated information,
**So that** hallucinated facts are prevented.

**Problem:**
- Observer hallucinated "3 km run on 2026-01-28; user reported feeling sluggish, possibly due to cold weather"
- None of this was in any user entry

**Acceptance Criteria:**

1. **Given** Observer output
   **When** validated
   **Then** all stored facts can be traced to user input

2. **Given** fact that doesn't appear in user input
   **When** Observer attempts to store it
   **Then** fact is filtered out with warning

3. **Given** Observer validation
   **When** implemented
   **Then** unit tests cover hallucination prevention

**Files to Modify:**
- `packages/quilto/quilto/agents/observer.py` - output validation
- Add unit tests for validation

---

### Story 22.4: Add Session ID to Feedback JSON

**Priority:** LOW | **Effort:** Small (30 minutes)

**As a** developer,
**I want** feedback JSON to include session ID,
**So that** I can correlate feedback with sessions.

**Acceptance Criteria:**

1. **Given** feedback is recorded
   **When** JSON is saved
   **Then** `session_id` field is included

2. **Given** session resume scenario
   **When** multiple feedback records exist
   **Then** they can be linked by session_id

**Files to Modify:**
- Feedback recording infrastructure (from Story 11.2)
- `packages/swealog/swealog/cli/` - callback that records feedback

---

### Story 22.5: Dogfooding Iteration 11

**Priority:** MEDIUM | **Effort:** Medium (2 hours)
**Depends On:** 22.1, 22.2, 22.3, 22.4

**As a** Swealog user and developer,
**I want** to test Observer behavior after refinements,
**So that** I can verify global context is clean.

**Acceptance Criteria:**

1. **Given** Stories 22.1-22.4 are complete
   **When** queries that triggered fabrication are re-run
   **Then** Observer no longer fabricates preferences

2. **Given** global context after multiple sessions
   **When** reviewed
   **Then** only preferences, goals, and insights are stored (no per-session facts)

3. **Given** 10+ queries tested
   **When** dogfooding completes
   **Then** target success rate >= 90%

**Query Types to Test:**
- **Focused (Observer):** Queries that previously triggered fabrication
- **Context Scope:** Verify corrections don't pollute global context
- **General Regression:** LOG, QUERY, BOTH, session resume, clarification, CORRECTION

---

## Future Epics

### Epic 23+: Continued Dogfooding Iterations

*Stories generated from Epic 22 dogfooding results*

**Status:** Backlog (depends on Epic 22 completion)

