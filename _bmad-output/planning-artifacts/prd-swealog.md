---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
workflowStatus: complete
completedDate: '2026-01-08'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd-quilto.md'
  - '_bmad-output/swealog-project-context-v2.md'
  - '_bmad-output/planning-artifacts/epics.md'
workflowType: 'prd'
lastStep: 1
mode: 'reverse-engineering'
projectStatus: 'greenfield'
fitnessDomains: ['strength', 'running', 'nutrition']
frameworkPRD: 'prd-quilto.md'
documentCounts:
  frameworkPRD: 1
  projectContext: 1
  epics: 1
---

# Product Requirements Document - Swealog

**Author:** Jongkuk Lim
**Date:** 2026-01-08
**Mode:** Reverse-engineered from Epics + Project Context
**Framework:** Built on Quilto (see `prd-quilto.md`)

---

## Executive Summary

Swealog is a CLI fitness logging app for lifters who want **AI insights grounded in their actual training history**.

### The Problem

You finish a heavy bench session and want to track it. Your options:
- **Spreadsheets**: Tedious. You stop after a week.
- **Fitness apps (Strong, etc.)**: Structured input required. Friction kills consistency.
- **Notes app**: Messy. Good luck finding that PR from 6 months ago.
- **Ask ChatGPT**: Generic advice. It doesn't know you train bodybuilding-style, not CrossFit.

**The real problem:** AI assistants give bad advice because they have no memory of you.

### The Solution

Log your workouts in natural language. Ask questions. Get answers that cite YOUR data.

```bash
swealog "bench 80kg 5x5 felt heavy, slept bad"
swealog ask "why is my bench stuck at 80kg?"
```

**The answer cites your logs:** "Your bench has stalled during weeks when you logged 'felt heavy' — which correlates with poor sleep notes. Consider a deload week."

### What Makes Swealog Special

| Feature | Why It Matters |
|---------|----------------|
| **Domain vocabulary** | "bp 80kg 5x5" → structured bench press log |
| **Personal context** | Insights reference YOUR history, not generic advice |
| **Zero friction** | Type naturally, AI handles structure |

### Framework Validation

Swealog is the first application built on **Quilto**, validating the domain-agnostic framework with a real domain. If it works for fitness, Quilto works for anything.

## Project Classification

**Technical Type:** CLI Application (Python)
**Domain:** Fitness / Strength Training
**Complexity:** Medium
**Target User:** Serious lifters who want data-driven training insights
**Project Status:** Greenfield — first implementation on Quilto

---

## Success Criteria

### User Success

1. **Daily capture is effortless** — Logging a workout takes <10 seconds of typing
2. **Trust as primary log** — Within 30 days, prefer Swealog over spreadsheets/notes for fitness tracking
3. **Insights feel accurate** — Queries return answers that match what you remember from your training
4. **Vocabulary just works** — "bp 80kg" is understood without explaining it's bench press

### Technical Success

1. **Fitness parsing accuracy** — >90% field extraction from natural language workout logs
2. **Domain vocabulary** — Common abbreviations (bp, dl, sq, ohp) expand correctly
3. **Structured schemas** — Strength/running/nutrition logs parse into correct schema fields
4. **CLI responsiveness** — Log command returns confirmation within expected LLM latency

### Framework Validation Success

1. **Quilto abstraction holds** — Fitness domain implemented without framework code changes
2. **DomainModule interface sufficient** — Strength, Running, Nutrition modules all fit the interface
3. **Zero domain leakage** — No fitness-specific code in `packages/quilto/`

### Measurable Outcomes

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Parsing accuracy | >90% fields correct | Test corpus from Strong CSV |
| Daily use | 30+ days consecutive | Personal dogfooding log |
| Vocabulary coverage | 50+ fitness terms | Term expansion tests |
| Query satisfaction | "Useful" 80%+ of time | LLM-as-judge + personal assessment |

---

## Product Scope

### MVP — Minimum Viable Product

**What must work:**
- `swealog log "..."` — Natural language workout logging
- `swealog ask "..."` — Query historical data with evidence-cited answers
- **Strength domain** — Sets, reps, weight, RPE parsing
- **Running domain** — Distance, time, pace parsing
- **Nutrition domain** — Basic food/calorie logging
- Local storage (markdown + JSON)
- Ollama + cloud LLM support

**What can be manual:**
- Import from existing logs (batch import deferred if needed)
- Error correction (manual edit of files acceptable)

### Growth Features (Post-MVP)

- `swealog import ~/logs/` — Batch import historical data
- PR tracking and celebration
- Cross-domain correlation (sleep vs performance)
- Enhanced Observer personalization

### Vision (Future)

- Multiple users / shared household data
- Mobile companion (voice logging)
- Obsidian plugin integration
- Community domain modules

---

## User Journeys

### Journey 1: First Workout Log

**Persona:** New user, just installed Swealog, finished a strength session.

**Scenario:**
```bash
$ swealog "bench 80kg 5x5, ohp 40kg 3x8, felt strong today"
```

**Expected behavior:**
1. Router classifies as LOG
2. Parser expands vocabulary: "bench" → "bench press", "ohp" → "overhead press"
3. Parser extracts structured data: exercise, weight, sets, reps, notes
4. Raw markdown saved with timestamp
5. Parsed JSON saved with structured fields
6. CLI confirms: "Logged: Bench Press 80kg 5x5, Overhead Press 40kg 3x8"

**Success moment:** "It understood 'ohp' without me explaining."

**Requirements revealed:**
- FR-S1: CLI accepts natural language input
- FR-S2: Vocabulary expansion for fitness abbreviations
- FR-S3: Structured feedback on what was parsed

---

### Journey 2: Daily User — Log and Query

**Persona:** 2-week user, consistent daily logging, wants to check progress.

**Scenario:**
```bash
$ swealog "squat 100kg 3x5, legs felt heavy"
✓ Logged: Squat 100kg 3x5

$ swealog ask "how has my squat progressed this month?"
```

**Expected response:**
> Your squat has progressed from 90kg to 100kg over 3 weeks.
> - Week 1: 90kg 3x5 (Jan 1, 3, 5)
> - Week 2: 95kg 3x5 (Jan 8, 10, 12)
> - Week 3: 100kg 3x5 (Jan 15, today)
>
> You've added 10kg in 3 weeks — solid linear progression.
> Note: You logged "legs felt heavy" today. Consider a deload if this persists.

**Success moment:** "It cited my actual logs and noticed the pattern."

**Requirements revealed:**
- FR-S4: Query responses cite specific log entries
- FR-S5: Pattern detection across time
- FR-S6: Contextual suggestions based on notes

---

### Journey 3: Messy Input Handling

**Persona:** Rushed user, types minimal shorthand.

**Scenario:**
```bash
$ swealog "bp 80 5x5 dl 120 1x5"
```

**Expected behavior:**
1. Parser handles missing units (assumes kg from user history)
2. Parser handles multiple exercises in one line
3. Structured output: Bench Press 80kg 5x5, Deadlift 120kg 1x5

**Success moment:** "It figured out what I meant even with lazy input."

**Requirements revealed:**
- FR-S7: Handle abbreviated/minimal input
- FR-S8: Infer missing units from user context
- FR-S9: Parse multiple exercises per input

---

### Journey 4: Nutrition Logging

**Persona:** User tracking food alongside workouts.

**Scenario:**
```bash
$ swealog "lunch: chicken salad ~500cal, protein shake 30g protein"
```

**Expected behavior:**
1. Router classifies as LOG
2. Domain auto-selection: Nutrition (not Strength/Running)
3. Parser extracts: meal type, food items, calories, macros
4. Stored with nutrition schema

**Success moment:** "Same command works for food, not just workouts."

**Requirements revealed:**
- FR-S10: Multi-domain support (strength, running, nutrition)
- FR-S11: Auto-domain selection based on content
- FR-S12: Nutrition-specific schema (calories, macros)

---

### Journey 5: Cross-Domain Query

**Persona:** Curious user, wants correlations.

**Scenario:**
```bash
$ swealog ask "do I lift better on days I eat more protein?"
```

**Expected response:**
> Looking at your logs from the past month:
> - High protein days (>150g): Average RPE 7.2, "felt strong" in 4/6 sessions
> - Low protein days (<100g): Average RPE 8.1, "felt tired" in 3/5 sessions
>
> There's a correlation between higher protein intake and better perceived performance.
> Note: This is based on 11 data points — keep logging for stronger conclusions.

**Success moment:** "It connected food logs to workout performance."

**Requirements revealed:**
- FR-S13: Cross-domain query capability
- FR-S14: Correlation analysis across entry types
- FR-S15: Confidence/sample size acknowledgment

---

## Functional Requirements

### Input & CLI

- FR-S1: Users can log workouts via `swealog log "..."` or `swealog "..."` (auto mode)
- FR-S2: Users can query history via `swealog ask "..."`
- FR-S3: CLI displays structured parse feedback after logging
- FR-S7: System handles abbreviated/minimal input gracefully
- FR-S8: System infers missing units from user history or defaults
- FR-S9: System parses multiple exercises in single input

### Domain Modules

- FR-S10: Swealog provides Strength, Running, and Nutrition domain modules
- FR-S11: System auto-selects domain based on input content
- FR-S12: Each domain has appropriate schema (strength: sets/reps/weight, running: distance/time/pace, nutrition: calories/macros)

### Vocabulary & Parsing

- FR-S2: Strength vocabulary expands common abbreviations (bp→bench press, dl→deadlift, sq→squat, ohp→overhead press)
- FR-S16: Running vocabulary handles pace/distance variations (5k, 10k, half marathon)
- FR-S17: Nutrition vocabulary handles common food terms and units

### Query & Insights

- FR-S4: Query responses cite specific log entries with dates
- FR-S5: System detects patterns across time (progression, plateaus)
- FR-S6: System provides contextual suggestions based on logged notes
- FR-S13: System supports cross-domain queries
- FR-S14: System can correlate data across different domains
- FR-S15: System acknowledges confidence/sample size in analysis

### Data Management

- FR-S18: ~~Users can view recent logs via `swealog history` or similar~~ **[DEFERRED]** - Users can query via `swealog ask` or browse raw files directly
- FR-S19: Users can correct/edit logged entries (via Quilto correction flow)
- FR-S20: System stores raw markdown and parsed JSON per Quilto storage spec

---

## Non-Functional Requirements

### Performance

**NFR-S1: Parsing Latency**
- Workout parsing completes within LLM response time (no additional delay)
- User sees confirmation immediately after LLM processes

**NFR-S2: Query Response**
- Progress visibility during long queries (show agent activity)
- No hard time limit due to LLM variability

### Quality

**NFR-S3: Parsing Accuracy**
- >90% field extraction accuracy on test corpus
- Measured against Strong CSV ground truth + synthetic variations

**NFR-S4: Vocabulary Coverage**
- 50+ fitness terms in initial vocabulary
- Expandable via domain module configuration

### Maintainability

**NFR-S5: Test Coverage**
- Domain modules have unit tests for schema validation
- Vocabulary expansion has test coverage
- Integration tests for CLI commands

**NFR-S6: Code Documentation**
- Domain modules documented with Google-style docstrings
- CLI commands have help text

---

## Project Type: CLI Application

### CLI Commands

| Command | Description |
|---------|-------------|
| `swealog "..."` | Auto mode — system detects log vs query |
| `swealog log "..."` | Explicit log mode |
| `swealog ask "..."` | Explicit query mode |
| `swealog history` | View recent logs |
| `swealog import <path>` | Batch import (Growth feature) |

### Technology Stack

- **Language:** Python 3.10+
- **CLI Framework:** Typer (via Quilto)
- **LLM:** Ollama (local) or cloud API (configurable)
- **Storage:** Markdown + JSON (via Quilto StorageRepository)

### Distribution

- MVP: Source install (`pip install -e .`)
- Post-MVP: PyPI package (`pip install swealog`)

---

## Relationship to Quilto

Swealog is an **application** built on the **Quilto framework**.

| Layer | What It Provides |
|-------|------------------|
| **Quilto (framework)** | 9-agent orchestration, DomainModule interface, storage abstraction, CLI framework |
| **Swealog (application)** | Fitness domain modules (Strength, Running, Nutrition), fitness vocabulary, CLI commands |

### What Swealog Implements

From Quilto's DomainModule interface:
- `description` — Fitness domain descriptions
- `log_schema` — Strength/running/nutrition schemas
- `vocabulary` — Fitness term expansions
- `expertise` — Fitness knowledge for agent prompts
- `response_evaluation_rules` — Fitness-specific quality checks
- `context_management_guidance` — What patterns Observer should track

### What Swealog Inherits

From Quilto (no implementation needed):
- All 9 agents (Router, Planner, Retriever, Analyzer, Synthesizer, Evaluator, Clarifier, Parser, Observer)
- State machine orchestration
- Storage repository
- LLM client abstraction
- Graceful degradation

---

## Skipped Sections

| Section | Reason |
|---------|--------|
| Domain Requirements (Step 5) | Fitness is not a regulated domain |
| Innovation (Step 6) | Innovation is at framework level (see prd-quilto.md) |

---

## Summary

**Swealog** is a CLI fitness logging app that validates the Quilto framework with a real domain.

| Aspect | Summary |
|--------|---------|
| **Problem** | AI assistants give generic fitness advice |
| **Solution** | Natural language logging + personalized queries |
| **Domains** | Strength, Running, Nutrition |
| **Success gate** | Daily personal use with trust within 30 days |
| **Framework validation** | DomainModule interface works for fitness |

**Documents:**
- Framework PRD: `prd-quilto.md`
- Application PRD: `prd-swealog.md` (this document)
- Epics: `epics.md`

