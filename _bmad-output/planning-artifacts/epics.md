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
