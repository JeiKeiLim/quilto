# Project Identity: Quilto vs Swealog

**Created:** 2026-01-09 (Epic 1 Retrospective)
**Status:** Active Reference Document
**Purpose:** Clarify the distinction between Quilto (framework) and Swealog (application)

> **Note:** A concise version of this document is in `/CLAUDE.md` (auto-loaded by Claude Code).
> This document provides the full detailed reference.

---

## The Problem

AI agents and developers frequently conflate "Swealog" with the entire project. This leads to:
- Framework code being described as "Swealog-specific"
- Test data being fitness-only when it should be domain-agnostic
- Documentation using wrong terminology
- Architectural decisions being made for fitness instead of any domain

**This document exists to prevent that confusion.**

---

## Two Packages, Two Purposes

```
swealog-workspace/              # Repository name (historical)
├── packages/
│   ├── quilto/                 # THE FRAMEWORK (domain-agnostic)
│   │   ├── quilto/
│   │   │   ├── domain.py       # DomainModule interface
│   │   │   ├── llm/            # LLM client abstraction
│   │   │   ├── agents/         # All agents (Router, Parser, etc.)
│   │   │   └── storage/        # StorageRepository
│   │   └── tests/
│   │
│   └── swealog/                # ONE APPLICATION (fitness-specific)
│       ├── swealog/
│       │   └── domains/        # Fitness domain modules ONLY
│       │       ├── general_fitness.py
│       │       ├── strength.py
│       │       └── nutrition.py
│       └── tests/
│
└── tests/                      # Integration tests + test corpus
    └── corpus/                 # Test data (should be multi-domain!)
```

---

## Quilto (The Framework)

**What it is:** A domain-agnostic framework for building AI agents that extract insights from unstructured user notes.

**Key principle:** Quilto knows NOTHING about fitness. It handles ANY domain.

| Component | Location | Domain-Specific? |
|-----------|----------|------------------|
| DomainModule interface | `quilto/domain.py` | NO - defines interface |
| LLMClient | `quilto/llm/` | NO - works with any LLM |
| Router agent | `quilto/agents/router.py` | NO - classifies any input |
| Parser agent | `quilto/agents/parser.py` | NO - uses domain's schema |
| StorageRepository | `quilto/storage/` | NO - stores any data |
| All other agents | `quilto/agents/` | NO - domain-agnostic |

**When writing Quilto code, ask:** "Would this work for a cooking app? A journal app? A study tracker?"

If the answer is NO, the code doesn't belong in Quilto.

---

## Swealog (The Fitness Application)

**What it is:** A fitness logging application built on top of Quilto.

**Korean meaning:** 쇠 (iron) + 록 (record) = "Iron Log"
**English meaning:** Sweat + Log = "Sweat Log"

| Component | Location | Purpose |
|-----------|----------|---------|
| GeneralFitness domain | `swealog/domains/general_fitness.py` | Base fitness domain |
| Strength domain | `swealog/domains/strength.py` | Weight training specifics |
| Nutrition domain | `swealog/domains/nutrition.py` | Food/meal tracking |
| Running domain | `swealog/domains/running.py` | Cardio tracking |
| Swimming domain | `swealog/domains/swimming.py` | Pool workout tracking |

**Swealog contains ONLY:**
- Fitness domain module implementations
- Fitness-specific schemas (GeneralFitnessEntry, StrengthEntry, etc.)
- Fitness vocabulary (exercise names, abbreviations)
- Fitness expertise (training principles, recovery advice)

---

## Future: Quiltr (The SaaS Product)

**Reserved name:** Quiltr
**Status:** Future consideration
**Purpose:** Potential hosted/commercial version of Quilto

Not currently in development. Name reserved for potential future use.

---

## Decision Guide: Where Does This Code Go?

### Put it in QUILTO if:

- It's an agent (Router, Parser, Planner, etc.)
- It's infrastructure (storage, LLM client, config)
- It's a base class or interface (DomainModule)
- It would work for ANY domain application
- It's test infrastructure (fixtures, accuracy runner)

### Put it in SWEALOG if:

- It's a fitness domain module
- It defines fitness-specific schemas
- It contains exercise names or fitness vocabulary
- It has fitness expertise or evaluation rules
- It's fitness-specific configuration

### Put it in TESTS (root) if:

- It's integration tests spanning both packages
- It's test corpus data (should include NON-fitness domains!)
- It's shared test utilities

---

## Common Mistakes to Avoid

### Mistake 1: "Swealog Parser"
**Wrong:** "The Swealog parser extracts fitness data"
**Right:** "The Quilto Parser agent uses Swealog's GeneralFitness schema"

### Mistake 2: "Swealog framework"
**Wrong:** "The Swealog framework supports multiple domains"
**Right:** "The Quilto framework supports multiple domains; Swealog is a fitness application"

### Mistake 3: Fitness-only test data
**Wrong:** All test corpus entries are fitness workouts
**Right:** Test corpus includes fitness, journal, cooking, study entries (Epic 1.5)

### Mistake 4: Hardcoding fitness in agents
**Wrong:** Parser agent has special handling for "bench press"
**Right:** Parser agent uses domain.vocabulary for term normalization

---

## Terminology Quick Reference

| Term | Meaning |
|------|---------|
| **Quilto** | The open-source, domain-agnostic framework |
| **Swealog** | The fitness application built on Quilto |
| **Quiltr** | Reserved name for potential future SaaS product |
| **DomainModule** | Quilto interface that Swealog domains implement |
| **Framework code** | Lives in `packages/quilto/` |
| **Application code** | Lives in `packages/swealog/` |

---

## For AI Agents

When working on this codebase:

1. **Read this document first** when starting a session
2. **Check package location** before writing code
3. **Ask "is this domain-agnostic?"** for any Quilto code
4. **Use correct terminology** in documentation and comments
5. **Test with multiple domains** not just fitness

**If you catch yourself writing "Swealog" when you mean the framework, STOP and use "Quilto" instead.**

---

## References

- Architecture: `_bmad-output/planning-artifacts/architecture.md`
- Epics: `_bmad-output/planning-artifacts/epics.md`
- Project Context: `_bmad-output/swealog-project-context-v2.md`
- Dev Workflow: `_bmad-output/planning-artifacts/dev-workflow.md`
