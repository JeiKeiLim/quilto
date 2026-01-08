# Swealog — Project Context (v2)

**Last Updated:** 2025-12-31
**Status:** Post-Brainstorming, Pre-Architecture
**Previous Version:** swealog-bmad-context.md (superseded)

---

## Project Identity

**Name:** Swealog (쇠록)
- Korean: 쇠 (iron) + 록 (record) — "Iron Log"
- English: Sweat + Log — "Sweat Log"

**Tagline (Updated):**
> "A framework for AI agents that turn your messy notes into organized insights"

**Type:** Open-source framework with fitness as first domain application

---

## The Core Insight

### The First Principle

**Before AI Agents:**
```
User must organize cleanly → So user can extract insights manually
         ↑
   THIS IS THE BURDEN (most people give up here)
```

**After AI Agents:**
```
User just writes SOMETHING → Agent extracts insights
         ↑
   ONLY REQUIREMENT: Write it down
```

### Fundamental Truths

1. **Writing is the only prerequisite** - Not organizing, not structuring, not formatting
2. **Value emerges from accumulated mass** - No single entry matters, the pile matters
3. **Organization is output, not input** - Agent's job to structure, synthesize, extract
4. **Effort threshold determines behavior** - Lower it enough and people actually do it

---

## Origin Story

### The Devil Press Moment (Fitness)

I did devil press for the first time. ChatGPT recommended 20kg each hand, 10 reps, 90 seconds rest. It was way too hard - the recommendation was for someone who does CrossFit regularly. But I do bodybuilding-style training. The AI didn't know me.

**Insight:** If an AI agent knew my workout style and history, it would have given proper suggestions.

### The Obsidian Revelation (Generalization)

I use Obsidian daily for notes, todos, meeting notes. Before agents, I'd get lost and give up organizing. Now I write messy notes and ask AI agents (Claude, Copilot CLI, Gemini) to find insights. I built workflows for daily notes, monthly reports, annual reports, retrospectives.

**Key realization:** "I never did annual reports on my own because I always get lazy... it was all possible because agents organize all my daily notes."

### The Connection

Both problems are the same pattern:
- Unstructured user input (workout logs, daily notes)
- AI agent that understands accumulated context
- Insights that emerge from the mass of data

**This isn't a fitness app. It's a general framework.**

---

## Vision

### What Swealog Is

An open-source framework for building context-aware AI agents from unstructured user history.

### Architecture Vision

```
┌─────────────────────────────────────────────────┐
│           APPLICATIONS (built on framework)      │
│   ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│   │ Obsidian │ │   CLI    │ │ Fitness App  │    │
│   │  Plugin  │ │   Tool   │ │              │    │
│   └──────────┘ └──────────┘ └──────────────┘    │
├─────────────────────────────────────────────────┤
│           DOMAIN MODULES (swappable)             │
│   ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│   │ Fitness  │ │  Notes/  │ │   Tasting    │    │
│   │ Expertise│ │  Journal │ │   Expertise  │    │
│   └──────────┘ └──────────┘ └──────────────┘    │
├─────────────────────────────────────────────────┤
│              CORE FRAMEWORK (Swealog)            │
│  ┌────────────┐ ┌────────────┐ ┌─────────────┐  │
│  │ Unstructured│ │  Context   │ │   Agent     │  │
│  │   Parser    │ │   Store    │ │  Extraction │  │
│  └────────────┘ └────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────┘
```

### Core Components (Preliminary)

| Component | Purpose |
|-----------|---------|
| **Unstructured Parser** | Accept messy text input, extract structure |
| **Context Store** | Persist accumulated history (format TBD) |
| **Agent Extraction** | Retrieve relevant context, generate insights |
| **Domain Module** | Inject domain expertise (fitness, notes, etc.) |

---

## Build Strategy

### The Build-Together Approach

```
Framework ←──────────→ Fitness MVP
    │                      │
    │   (grow together)    │
    ▼                      ▼
Generic abstractions   Concrete usage
informed by real use   validates the
                       abstractions
```

**Why this matters:**
- Framework without application = vaporware
- Application without framework = one-off project
- Building together = each informs the other

### First Applications

1. **Fitness MVP** - Primary dogfooding domain (founder's PhD expertise)
2. **Obsidian Integration** - Proves generalizability (founder's daily workflow)

---

## Constraints

### Real Constraints

| Constraint | Implication |
|------------|-------------|
| **Generic foundation required** | Core must be domain-agnostic |
| **Local-first (Ollama)** | Minimize API costs during development |
| **Local infrastructure** | Runs on macbook, no cloud dependencies |
| **API compatibility** | Can upgrade to cloud LLMs later |

### Soft Constraints

| Constraint | Status |
|------------|--------|
| Python preferred | Flexible - AI agent decides |
| Fitness first | Good starting point, not required |
| Ship quickly | Dogfooding important, not deadline-driven |
| Obsidian integration | Nice to have, proves generalizability |

### Not Actually Constraints

| Perceived Constraint | Reality |
|---------------------|---------|
| Solo developer | AI agents (BMAD + Claude Code) write code |
| Limited time | Good planning = implementation handled |
| Language choice | Can defer to architecture phase |

---

## Open Research Questions

### Priority: HIGH

| Question | Current Thinking |
|----------|-----------------|
| **Context window strategy** | How many days/notes fit in context? Strategy matters more than raw limits. Annual report success suggests solvable. |
| **Storage format** | Database vs. markdown? Leaning markdown (Obsidian-compatible). |
| **Parsing accuracy** | Agent handles most cases. Feedback loop for corrections (like AGENTS.md notes). |
| **Local LLM requirements** | What's minimum capability needed? Keep API compatibility for upgrades. |

### Priority: MEDIUM

| Question | Current Thinking |
|----------|-----------------|
| **Minimum viable framework** | What's the smallest useful core? |
| **Minimum viable fitness MVP** | What's the smallest useful application? |
| **What defines "done" for v0.1?** | TBD |

---

## Testing Strategy (To Be Developed)

| Test Type | What It Validates |
|-----------|------------------|
| **Unit tests** | Parser extracts structured data correctly |
| **Integration tests** | Full pipeline: input → store → retrieval → insight |
| **LLM-as-judge** | Quality of insights, recommendations, accuracy |
| **Dogfooding** | Does it actually help with fitness? |

---

## Academic Paper Potential

### Possible Contributions

- Novel framework for context-aware agents from unstructured personal data
- Evaluation methodology (LLM-as-judge for personal AI)
- Case study: fitness domain application
- Comparison: generic LLM vs. context-aware agent quality

### Requirements for Publication

- Clear problem statement and related work
- Formal framework description
- Evaluation metrics and methodology
- Empirical results (fitness domain as case study)
- Generalizable findings

### Potential Venues

- **HCI angle:** CHI, IUI, UIST
- **NLP/Agent angle:** EMNLP/ACL workshops

---

## Founder Context

- **PhD:** Automatic assessment of anaerobic workout using inertial sensors (uLift)
- **Same domain, new approach:** AI context instead of hardware sensors
- **Current role:** AI agent engineering
- **Daily workflow:** Obsidian + AI agents for notes, reports, retrospectives
- **Motivation:** Personal use (dogfooding) + technical legacy (GitHub) + potential academic contribution

---

## Next Steps

### Immediate (Document Phase)

1. ~~Capture brainstorming insights~~ (Done)
2. ~~Create updated project context~~ (This document)
3. Create research questions document
4. Create next steps roadmap

### Short-term (Research Phase)

1. Investigate context window strategies
2. Evaluate storage format options
3. Assess local LLM capabilities (Ollama models)
4. Define parsing accuracy requirements

### Medium-term (Architecture Phase)

1. Deep dive on agent architecture
2. Define data flows and interfaces
3. Design domain module system
4. Plan testing infrastructure

### Long-term (Build Phase)

1. Implement core framework
2. Build fitness MVP alongside
3. Dogfood extensively
4. Iterate based on real usage

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `swealog-bmad-context.md` | Original context (superseded by this document) |
| `brainstorming-session-2025-12-31.md` | Full brainstorming session transcript and insights |
| `research-questions.md` | TBD - Deep dive on open questions |
| `architecture.md` | TBD - Agent architecture design |
