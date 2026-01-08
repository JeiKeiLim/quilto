---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
workflowStatus: complete
completedDate: '2026-01-08'
inputDocuments:
  - '_bmad-output/swealog-project-context-v2.md'
  - '_bmad-output/swealog-bmad-context.md'
  - '_bmad-output/research-questions.md'
  - '_bmad-output/planning-artifacts/research/technical-swealog-foundational-research-2026-01-02.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/epics.md'
  - '_bmad-output/planning-artifacts/agent-system-design.md (2991 lines - COMPLETE)'
  - '_bmad-output/planning-artifacts/state-machine-diagram.md'
workflowType: 'prd'
lastStep: 4
documentCounts:
  projectContext: 2
  research: 2
  architecture: 1
  epics: 1
  agentDesign: 2
  brief: 0
mode: 'reverse-engineering'
agentSystemDesign:
  decisions: 28
  agents: 9
  states: 13
  cycles: 4
  framework: 'LangGraph'
  storageRepository: '6 methods'
relatedPRD: 'prd-swealog.md'
---

# Product Requirements Document - Quilto

**Author:** Jongkuk Lim
**Date:** 2026-01-06
**Mode:** Reverse-engineered from Architecture + Epics
**Related:** See `prd-swealog.md` for fitness application requirements

---

## Executive Summary

Quilto is an open-source Python framework for building AI-powered personal logging applications. It transforms the traditionally tedious process of organizing personal notes into an effortless experience where **organization is output, not input**.

Users of Quilto-based applications write messy, unstructured notes; the framework's 9-agent orchestration system handles parsing, categorization, retrieval, and insight generation automatically.

### What Makes This Special

**Quality through specialized agents:** A 9-agent collaborative system (Router, Planner, Retriever, Analyzer, Synthesizer, Evaluator, Clarifier, Parser, Observer) delivers insight quality that single-LLM approaches cannot match. Each agent is optimized for one responsibility.

**Domain-agnostic architecture:** Quilto provides the orchestration engine; applications provide domain modules. One framework powers fitness apps, cooking journals, work logs, or any personal data domain.

**Pluggable domain modules:** The `DomainModule` interface lets developers define vocabulary, schemas, expertise, and evaluation rules for any domain — no framework code changes required.

**Emergent understanding:** The Observer agent learns patterns that transcend individual notes — user goals, preferences, and behaviors. Applications built on Quilto get personalization "for free."

### Framework vs Application

| Layer | Name | Purpose |
|-------|------|---------|
| Framework | **Quilto** | Agent orchestration, state machine, storage abstraction, LLM client |
| Application | **Swealog** | Fitness domain modules, CLI experience (reference implementation) |

See `prd-swealog.md` for the fitness application requirements.

## Project Classification

**Technical Type:** Developer Framework (Python package)
**Domain:** AI/ML Systems
**Complexity:** Medium-High
**Project Context:** Greenfield — comprehensive design ready for implementation

---

## Success Criteria

### User Success

1. **Daily capture is effortless** — Thought-to-logged time under 10 seconds. No formatting, tagging, or friction.

2. **Trust as primary source** — Within 30 days, becomes the go-to tool for the domain, with 5+ logs per week.

3. **Insights feel accurate and useful** — Query responses cite verifiable data. Time to first useful insight within first week of use.

### Technical Success

1. **9-agent system works end-to-end** — 99%+ success rate with graceful recovery on transient failures.

2. **Domain modules are truly pluggable** — Fitness modules work without framework modifications.

3. **Domain agnosticism preserved** — CRITICAL: Every framework change passes the domain-agnostic test:
   - No domain-specific vocabulary in Quilto code
   - All domain knowledge injected via DomainModule interface
   - Agent prompts use `{domain_context}` placeholders only
   - Test suite passes with mock "absurd domain" (no fitness assumptions)

4. **Observer learns without regression** — Global context captures patterns; accuracy doesn't degrade over 30 days.

5. **Graceful degradation** — After 2 retry attempts with INSUFFICIENT verdict, returns partial answer + explicit gaps.

6. **Temporal hints never ignored** — Evaluator must flag responses that ignore user-provided temporal context (e.g., "last year", "in March"). This is a quality gate, not optional.

### Measurable Outcomes

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Thought-to-logged time | < 10 seconds | Timed sessions |
| Capture frequency | 5+ logs/week | Usage tracking |
| Time to first insight | Within week 1 | User feedback |
| Query citation accuracy | 100% verifiable | Audit 20 random queries |
| Agent loop success | 99%+ with recovery | Automated tests |
| Domain agnosticism | Mock domain passes | Test suite with "pet rock journal" domain |
| Observer regression | No degradation 30 days | Weekly accuracy audits |
| Temporal hint respect | 100% acknowledgment | Test: temporal hint + zero results → HITL triggered, not silent failure |

---

## Product Scope

### MVP — Swealog (Fitness)

- Core 9-agent orchestration loop
- Fitness domain modules (strength, running, nutrition)
- CLI interface for logging and querying
- Local markdown + JSON storage
- Ollama local LLM with cloud fallback
- **Success gate:** Daily personal use with trust

### Growth Features (Post-MVP)

- Additional domain modules (cooking, work, health)
- Enhanced Observer pattern learning
- API endpoints for external integrations
- Multi-domain query support

### Vision (Future — Pending MVP Validation)

- Unified platform for all personal notes
- Automatic domain detection and routing
- Single app for "everything messy"
- Decision point: Expand Swealog or build new apps on Quilto

### Architectural Principle

> **Domain agnosticism is non-negotiable.** Any change that fails the "would this work for cooking/work/any domain?" test belongs in the application layer, not Quilto.

---

## User Journeys

### Journey 1: The Devil Press Revelation (Origin Story)

Jongkuk is a software engineer who tracks his workouts and uses AI tools daily. One day, he asks ChatGPT for a workout recommendation. "Try devil press with 20kg dumbbells, EMOM style," it suggests confidently.

He tries it. It's brutal — far too heavy. He dials it back himself: 10kg each hand, 2-minute intervals. That works. When he asks ChatGPT why it gave bad advice, the answer is revealing: "That was designed for someone doing CrossFit-style training." But Jongkuk does bodybuilding-style workouts. The AI was smart, but it had no memory of him.

Meanwhile, his messy Obsidian notes work great with Claude Code for retrieval. Two ideas collide: AI needs persistent context, and messy notes + AI retrieval already works. Quilto is born from a personal need: "I want AI that remembers me."

**Requirements revealed:** Persistent user context, domain-specific expertise, historical pattern recognition, zero-friction input.

---

### Journey 2: Daily Swealog User

Jongkuk finishes bench press, opens his terminal:

```bash
swealog "bench 80kg 5x5 felt heavy today, slept bad last night"
```

Swealog responds with a structured card showing what it understood. No approval needed — just acknowledgment and edit availability if something's wrong.

Days later, planning next week's training:

```bash
swealog ask "why has my bench been stuck at 80kg?"
```

The delightful answer cites his sleep patterns, correlates "felt heavy" logs with poor sleep nights, and suggests a deload week. It references specific dates. The frustrating answer would be generic advice any LLM could give — unacceptable when the data exists.

**Requirements revealed:** Three input modes (auto/log/query), structured parse feedback, mandatory evidence citation, anti-generic quality gate, historical pattern detection.

**Clarification note:** "Structured card" display is application-level (Swealog), not Quilto. Quilto provides Parser output structure; application decides how to render it.

---

### Journey 3: Framework Developer (Alex Builds Cooklog)

Alex discovers Quilto and wants to build a cooking journal app. They create a CookingModule with vocabulary ("evoo" → "extra virgin olive oil"), a MealLog schema, and cooking expertise.

They type `cooklog "made pasta with evoo garlic and bp"` and get back a properly structured log with expanded vocabulary. A week later, they ask "what do I usually cook on weeknights?" and get personalized insights about their quick, garlic-forward preferences.

No Quilto framework code was touched. The domain-agnostic promise is real.

**Requirements revealed:** Clear DomainModule interface, zero domain references in Quilto core, domain module test harness, comprehensive documentation.

---

### Journey 4: Graceful Degradation (Edge Cases)

Jongkuk asks "how's my swimming progress?" but has never logged swimming. The system responds honestly: "I don't have any swimming data" with suggestions for how to start logging.

For partial data, the system uses what exists, acknowledges gaps, and suggests how to improve the analysis. After retry limits, it returns partial answers with explicit lists of what's missing.

The system never hallucinates or presents generic advice as personalized insight.

**Requirements revealed:** Honest gap acknowledgment, partial answer support, retry limit behavior, no hallucination policy.

---

### Journey 5: Deep Historical Search (The Lost Note)

Jongkuk remembers logging a shoulder rehab routine last year:

```bash
swealog ask "what was that shoulder rehab routine I did last year?"
```

**Correct behavior:** Planner extracts "last year" as temporal hint → Retriever searches 2025 → finds the February entry with the full PT band routine.

**If year-wide search still fails:** System asks for narrowing hints before giving up — "More specific time? Other keywords?" — using Clarifier for human-in-the-loop assistance.

**Requirements revealed:**
- Planner must extract temporal references from queries ("last year", "in March", "a few months ago")
- HITL hint request when extracted hints aren't sufficient
- Never ignore user-provided time context

---

### Journey Requirements Summary

| Capability | Source Journey |
|------------|----------------|
| Three input modes (auto/log/query) | Journey 2: Daily User |
| Structured parse feedback (app renders) | Journey 2: Daily User |
| Evidence citation mandatory | Journey 2: Daily User |
| Anti-generic quality gate | Journey 1: Origin, Journey 2: Daily User |
| DomainModule interface | Journey 3: Framework Developer |
| Domain-agnostic core | Journey 3: Framework Developer |
| Graceful degradation | Journey 4: Edge Cases |
| No hallucination policy | Journey 4: Edge Cases |
| Temporal hint extraction (Planner) | Journey 5: Deep Historical Search |
| HITL retrieval hints (Clarifier) | Journey 5: Deep Historical Search |

### Party Mode Feedback (Resolved)

1. ~~API consumer journey~~ — Quilto is SDK, not API service. Defer to Swealog PRD.
2. ~~Structured card fields~~ — Application-level concern. Quilto provides Parser output.
3. ~~"Never ignore temporal hints" as Evaluator rule~~ — Added to Technical Success #6
4. ~~Test case: temporal hint → zero results → HITL~~ — Added to Measurable Outcomes

---

## Innovation & Novel Patterns

### Core Innovation: Organization is Output

Quilto's founding philosophy: **AI should organize for you, not require organization from you.**

This isn't "AI-assisted organization" — it's **AI-driven organization**. The difference:

| Traditional Tools | AI-Assisted (hypothesis) | Quilto Philosophy |
|-------------------|--------------------------|-------------------|
| Tags, folders, structure required | Some structure helpful | Zero structure required |
| User does the work | AI helps with the work | AI does the work |
| Organization is input | Organization is partially output | Organization is fully output |

**"Your messiest thought is valid input."** — This principle shapes every design decision.

### Architectural Differentiation: Domain-Agnostic SDK

The second innovation layer: Quilto is an **open-source orchestration engine**, not a consumer product.

| Consumer Products | Quilto |
|-------------------|--------|
| Fixed domains | Pluggable DomainModule interface |
| Use their app | Build your own apps |
| Closed ecosystem | Open-source framework |

Developers can build fitness apps, cooking journals, work logs — any domain — without framework code changes. This market enables things closed products can't.

### Why Now: The Agentic AI Era

Local LLMs (Ollama) + multi-agent orchestration patterns have matured enough to make this philosophy viable:
- **Cost**: Local inference removes per-query economics
- **Quality**: Specialized agents match single-LLM quality through collaboration
- **Privacy**: Personal data stays local

### Validation Approach

1. **Philosophy validation**: Does "zero structure required" actually reduce friction vs. AI-assisted approaches?
2. **Developer resonance**: Do developers want a domain-agnostic SDK, or prefer building from scratch?
3. **Quality validation**: Do 9 specialized agents produce better insights than single-LLM?
4. **Competitive verification**: ✅ mem.ai analysis complete (see Competitive Positioning section)

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM quality insufficient for zero-structure input | Graceful degradation + HITL via Clarifier |
| "Organization is output" philosophy doesn't resonate | Swealog validates before framework expansion |
| Competitive moat unclear | SDK positioning (developer tool) vs. consumer products |
| Developers prefer building from scratch | Clear DomainModule value prop + documentation |

---

## Competitive Positioning

### Primary Competitor: mem.ai

mem.ai is a "self-organizing workspace" targeting consumers. Both tools aim to eliminate manual organization, but with different philosophies:

| Aspect | mem.ai | Quilto |
|--------|--------|--------|
| **Philosophy** | "AI helps you find well-captured notes" | "AI structures your barely-captured thoughts" |
| **Input expectation** | Quality + volume matters | "Messiest thought is valid input" |
| **Hidden requirement** | Substantial note collection needed | Domain module provides structure |
| **Target** | Consumer end-user | Developer building apps |
| **Architecture** | Closed SaaS product | Open-source SDK |

**Critical finding:** mem.ai's effectiveness "depends on the volume and quality of your notes." Quilto's Parser + DomainModule transforms low-quality input into structured data — that's the philosophy gap.

### Key Differentiators

| Differentiator | Why It Matters |
|----------------|----------------|
| **"Messiest input is valid"** | mem.ai needs quality; Quilto transforms garbage |
| **Domain vocabulary expansion** | "bp 80kg" → structured bench press log |
| **Pluggable DomainModule SDK** | Developers build any domain app |
| **Open source** | Transparency, customization, no vendor lock-in |
| **9-agent explainability** | Know *why* organization happened |
| **Observer for personalization** | Explicit pattern learning vs. black box |

*See `research/competitive-mem-ai-analysis.md` for detailed research.*

---

## Developer Tool Specific Requirements

### Project-Type Overview

Quilto is a **Python SDK** for building AI-powered personal logging applications. Developers install the package, implement `DomainModule` interfaces for their domain, and get the 9-agent orchestration system "for free."

**Target developer:** Python developers building domain-specific logging/journaling applications.

### Language & Distribution

| Aspect | MVP | Future |
|--------|-----|--------|
| **Language** | Python only | Other languages when requested |
| **Package manager** | Direct install (pip optional) | PyPI distribution |
| **Python version** | 3.13 (per Architecture decision) | Maintain compatibility |

**MVP note:** Package distribution (pip/PyPI) is not required for MVP. Direct installation from source is acceptable.

### Technical Stack (from Architecture)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Agent Framework** | LangGraph | Handles 13-state machine with 4 cycles, HITL, conditional routing |
| **LLM Client** | LiteLLM | Unified API for Ollama + cloud providers, async support |
| **CLI Framework** | Typer + Rich | Beautiful CLI output, easy command definition |
| **Retrieval Strategy** | Date/keyword (no embeddings v1) | Data scale fits context windows (~109k chars/year) |
| **Global Context** | ~2k tokens, markdown format | Archival strategy for size management |

*See `architecture.md` and `agent-system-design.md` for detailed rationale.*

### Installation Methods

**MVP (Swealog validation):**
```bash
git clone https://github.com/JeiKeiLim/quilto
cd quilto
pip install -e .  # or: pip install -r requirements.txt
```

**Post-MVP (public release):**
```bash
pip install quilto
```

### API Surface

The public API consists of:

| Interface | Purpose | Developer Implements |
|-----------|---------|---------------------|
| `DomainModule` | Domain vocabulary, schemas, expertise | Yes |
| `StorageRepository` | Data persistence abstraction | Optional (defaults provided) |
| `LLMClient` | Model provider abstraction | Optional (Ollama/cloud defaults) |

**Core principle:** Developers implement domain knowledge; Quilto handles orchestration.

### CLI Interface

No IDE integration planned. Quilto applications are CLI-based.

**Pattern:** Applications built on Quilto expose their own CLI (like `swealog`), not a Quilto CLI directly.

```bash
# Application-level CLI (Swealog example)
swealog "bench 80kg 5x5"           # auto mode
swealog log "felt tired today"     # explicit log
swealog ask "why is my bench stuck?" # query mode
```

### Documentation Strategy

| Type | Format | Notes |
|------|--------|-------|
| **API docs** | MkDocs | Auto-generated from docstrings |
| **Docstring style** | Google style | AI-agent friendly for generation |
| **Tutorials** | Markdown in docs/ | Quickstart, domain module creation |
| **Architecture** | Existing docs | agent-system-design.md, architecture.md |

**Open to alternatives:** If AI agents recommend a better documentation format than MkDocs, willing to switch.

### Code Examples

| Example | Purpose | Priority |
|---------|---------|----------|
| **Swealog** | Full reference implementation (fitness domain) | MVP |
| **Quickstart** | Minimal "hello world" domain module | Post-MVP |
| **5-minute demo** | Video/script showing log → query → insight | Post-MVP |
| **Domain templates** | Starter templates for common domains | Future |

### Implementation Considerations

**For MVP:**
- Focus on Swealog as the example — it validates the framework
- Documentation can be minimal (README + architecture docs exist)
- No PyPI distribution required

**Post-MVP (public release):**
- PyPI package with proper versioning
- MkDocs site with quickstart + API reference
- At least one non-fitness example domain
- Migration guide if API changes

### Skip Sections

Per project-type configuration, these sections are **not applicable**:
- ~~Visual design~~ (CLI-only)
- ~~Store compliance~~ (not an app store product)

---

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Platform MVP — build the orchestration foundation, validate with one domain.

**Core Thesis:** If Quilto works for fitness (Swealog), the domain-agnostic architecture is proven and can expand to any domain.

**Success Gate:** Daily personal use with trust within 30 days.

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- Journey 1: Origin Story (AI that remembers) ✅
- Journey 2: Daily Swealog User (log + query) ✅
- Journey 4: Graceful Degradation ✅
- Journey 5: Deep Historical Search ✅

**Must-Have Capabilities:**

| Component | MVP Scope |
|-----------|-----------|
| **Agent System** | All 9 agents operational (Router, Planner, Retriever, Analyzer, Synthesizer, Evaluator, Clarifier, Parser, Observer) |
| **Domain Modules** | Fitness: strength, running, nutrition (all 3) |
| **Input Modes** | Auto, log, query |
| **Storage** | Local markdown + JSON |
| **LLM** | Ollama (local) + cloud API fallback |
| **Interface** | CLI only |
| **Distribution** | Source install (no PyPI required) |

**Explicitly Deferred from MVP:**
- PyPI package distribution
- Non-fitness domain modules
- API endpoints
- Multi-domain queries
- IDE integration
- Documentation site (README + arch docs sufficient)

### Post-MVP Features

**Phase 2 — Growth (After MVP Validation):**

| Feature | Rationale |
|---------|-----------|
| Additional domain modules | Prove domain-agnostic claim (cooking, work, health) |
| Enhanced Observer learning | Deeper personalization patterns |
| PyPI distribution | Public release readiness |
| MkDocs documentation site | Developer onboarding |
| Quickstart examples | Lower barrier to entry |

**Phase 3 — Expansion (After Growth Validation):**

| Feature | Rationale |
|---------|-----------|
| API endpoints | External integrations |
| Multi-domain queries | "What did I eat before yesterday's workout?" |
| Automatic domain detection | Unified "everything messy" input |
| Domain templates | Accelerate community contributions |

### Risk Mitigation Strategy

**Technical Risks:**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 9-agent coordination complexity | Medium | LangGraph handles orchestration; graceful degradation after 2 retries |
| LLM quality for messy input | Medium | Parser + domain vocabulary + Evaluator quality gate |
| Observer learning regression | Low | Weekly accuracy audits; manual override via Clarifier |

**Market Risks:**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| "Organization is output" doesn't resonate | Low | Swealog validates with daily personal use |
| Developers prefer building from scratch | Medium | Clear DomainModule value prop + documentation |
| mem.ai or similar captures market | Low | Different target (SDK vs consumer), open source moat |

**Resource Risks:**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Solo developer bandwidth | High | MVP scope is lean; Swealog-only focus |
| Scope creep | Medium | PRD defines clear MVP boundaries |

### Minimum Viable Scope (If Further Cuts Needed)

If resources are more constrained than expected:

| Cut | Impact |
|-----|--------|
| Running + nutrition modules | Ship with strength only, add others in weeks |
| Cloud fallback | Ollama-only (requires local GPU) |
| Observer agent | Defer personalization, core loop still works |

**Absolute minimum:** 8 agents (no Observer) + strength module + CLI + Ollama = still validates the core thesis.

---

## Functional Requirements

### Input Processing

- FR1: Users can submit unstructured text input without any formatting requirements
- FR2: System can automatically detect input intent (log entry vs. query vs. ambiguous)
- FR3: Users can explicitly specify input mode (auto, log, query) to override detection
- FR4: Parser can expand domain vocabulary abbreviations (e.g., "bp" → "bench press")
- FR5: Parser can extract structured data from messy natural language input
- FR6: System can handle input in the user's natural speaking/typing style

### Agent Orchestration

- FR7: Router agent can classify incoming requests and route to appropriate workflow
- FR8: Planner agent can decompose queries into retrieval and analysis steps
- FR9: Planner agent can extract temporal hints from queries (e.g., "last year", "in March")
- FR10: Retriever agent can search historical data based on Planner specifications
- FR11: Analyzer agent can process retrieved data to identify patterns and insights
- FR12: Synthesizer agent can compose coherent responses from analyzed data
- FR13: Evaluator agent can assess response quality against defined criteria
- FR14: Evaluator agent can flag responses that ignore user-provided temporal context
- FR15: Clarifier agent can request human input when information is insufficient
- FR16: System can execute multi-agent workflows with state transitions
- FR17: System can retry failed agent operations up to configured limit

### Domain Module System

- FR18: Developers can implement DomainModule interface for any domain
- FR19: DomainModule can define domain-specific vocabulary and expansions
- FR20: DomainModule can define domain-specific data schemas
- FR21: DomainModule can provide domain expertise for agent prompts
- FR22: DomainModule can define domain-specific evaluation rules
- FR23: Framework can load and use domain modules without code changes
- FR24: Multiple domain modules can coexist in a single installation
- FR55: System can route input to appropriate domain module based on content

### Storage & Retrieval

- FR25: System can persist log entries to local markdown files
- FR26: System can persist structured data to local JSON files
- FR27: System can retrieve entries by semantic similarity (not just keyword)
- FR28: System can retrieve entries by temporal constraints (date ranges, relative time)
- FR29: System can retrieve entries by domain-specific criteria
- FR30: Developers can implement custom StorageRepository for alternative backends

### Query & Response

- FR31: System can generate responses that cite specific historical entries as evidence
- FR32: System can identify patterns across multiple historical entries
- FR33: System can correlate data across different entry types (e.g., sleep + performance)
- FR34: Responses must include verifiable references to source data
- FR35: System can provide structured parse feedback after log entry processing

### Quality & Evaluation

- FR36: Evaluator can detect generic responses that don't use personal data
- FR37: System can gracefully degrade after retry limit with partial answer + explicit gaps
- FR38: System can honestly acknowledge when requested data doesn't exist
- FR39: System can suggest how to improve future logging for better analysis
- FR40: System can trigger HITL when temporal hint search returns zero results

### Personalization (Observer)

- FR41: Observer agent can learn user patterns across log entries over time
- FR42: Observer can identify user goals and preferences from historical data
- FR43: Observer can provide global context to other agents for personalized responses
- FR44: Observer learning can persist across sessions
- FR45: Observer patterns must not degrade in accuracy over 30+ days of use

### Framework Extensibility

- FR46: Developers can configure LLM provider (Ollama local or cloud API)
- FR47: Developers can switch LLM providers without code changes
- FR48: Framework exposes DomainModule, StorageRepository, and LLMClient interfaces
- FR49: Applications built on Quilto expose their own CLI (framework doesn't dictate CLI)
- FR50: Framework can operate without network connectivity when using local LLM

### System Operations

- FR51: System can timeout agent operations and handle gracefully
- FR52: Developers can configure system settings via configuration file
- FR53: System can report errors with actionable context to users
- FR54: System can log agent decisions and state transitions for debugging

### User Data Management

- FR56: ~~Users can edit or delete previously logged entries~~ **[DEFERRED]** - Users can edit raw markdown files directly; Quilto reads files dynamically on queries
- FR57: ~~Users can view recent log entries without querying~~ **[DEFERRED]** - Users can query via ask command or browse raw files directly

### Onboarding

- FR58: ~~System can provide guidance for first-time users on how to log effectively~~ **[DEFERRED]** - Typer CLI provides `--help` by default; sufficient for MVP dogfooding

---

## Non-Functional Requirements

### Performance

**NFR1: Progress Visibility**
- System must display real-time progress indicators showing current agent activity
- Users must be able to see which agent is active and what operation is in progress
- Progress updates must occur at minimum every 30 seconds during long operations

**NFR2: Response Time Expectations**
- Log entry parsing: Target < 5 seconds (per Architecture NFR-F3), but variable based on LLM provider
- Query response: Variable (local: up to 10+ minutes, cloud: up to 5 minutes)
- System must never appear "stuck" — progress must always be visible
- Note: Hard latency guarantees are not enforceable due to LLM provider variability

**NFR3: Timeout Handling**
- Agent operations must have configurable timeouts
- Timeout behavior must be graceful (not crash, provide partial results if possible)

*Note: Hard performance targets are not appropriate for this system due to LLM variability between local (Ollama) and cloud providers.*

### Maintainability

**NFR4: Test Coverage**
- Minimum 80% code coverage for framework core
- All public API methods must have unit tests
- Agent orchestration flows must have integration tests
- Domain module interface must have contract tests

**NFR5: Code Documentation**
- All public APIs must have Google-style docstrings
- Docstrings must include: description, args, returns, raises, examples where appropriate
- Architecture decisions must be documented in architecture docs
- No undocumented public methods allowed

**NFR6: Code Quality**
- Code must pass configured linter (e.g., ruff, flake8)
- Type hints required for all public interfaces
- No TODO comments in released code without linked issue

### Integration

**NFR7: LLM Provider Flexibility**
- System must support switching between Ollama and cloud providers via configuration
- LLM provider changes must not require code modifications
- New LLM providers must be addable via LLMClient interface implementation

**NFR8: Storage Backend Flexibility**
- Default storage (markdown + JSON) must work without additional dependencies
- Alternative storage backends must be addable via StorageRepository interface

### Skipped Categories

The following NFR categories are **not applicable** for Quilto MVP:

| Category | Reason |
|----------|--------|
| **Security** | Local-first option; data stays on user's machine; developer's choice |
| **Scalability** | Single-user personal tool; not multi-tenant |
| **Accessibility** | CLI-only interface |
| **Reliability/Uptime** | Graceful degradation covered in FRs; no SLA needed for personal tool |

---

