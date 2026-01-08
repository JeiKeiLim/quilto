---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ['_bmad-output/swealog-bmad-context.md']
session_topic: 'Swealog - Product Features, Technical Architecture, Cold Start Strategy'
session_goals: 'Feasibility validation and idea extraction - surface latent thoughts and validate buildability'
selected_approach: 'AI-Recommended Techniques'
techniques_used: ['Question Storming', 'Five Whys + First Principles', 'Constraint Mapping + Failure Analysis']
ideas_generated: ['Framework vision', 'Build-together approach', 'Academic paper potential', 'Testing strategy']
context_file: '_bmad-output/swealog-bmad-context.md'
session_status: 'completed'
---

# Brainstorming Session Results

**Facilitator:** Jongkuk Lim
**Date:** 2025-12-31
**Duration:** ~60 minutes
**Status:** Completed

---

## Session Overview

**Original Topic:** Swealog - Product Features, Technical Architecture, Cold Start Strategy
**Evolved Topic:** Generic framework for context-aware AI agents from unstructured user history

**Goals Achieved:**
- Extracted latent thoughts that couldn't be articulated before
- Validated feasibility through constraint mapping
- Discovered fundamental pivot from "fitness app" to "generic framework"
- Identified clear path forward with mitigations for failure modes

---

## Phase 1: Question Storming Results

### Questions Generated (40+)

**Product Features:**
- Why do users want to log in unstructured form?
- Why would users ditch existing tools for an AI-native logging app?
- Why focus on workout? Can we expand to other fields (tasting, etc.)?
- What is the interface - chat style or traditional logging UI with AI?
- How do users discover features if they have to ask? What if they don't know what to ask?

**Technical Architecture:**
- What framework to use? Python web framework? Native app?
- Which LLM? Local first then cloud? Or cloud-based from start?
- Is a small model enough to build this agent?

**Cold Start:**
- Should cold start interview be prefixed or dynamic questions?
- How will users feel getting asked bunch of questions before starting?
- Will users feel it's marketing scam? What makes them feel the agent understands them?

**Existential/Strategic:**
- Why can't this be a standalone framework like mem0 offered as SaaS?
- Why would people use this when knowledgeable users can DIY with Claude Code?
- Do people really think this is useful or needed? Who wants to try this?
- What happens if agent fails to recognize unstructured input?
- What do users expect after cold start? After 1 month?
- What makes users keep using this?

### Key Tensions Identified
1. **Cold start paradox:** Need context to be useful, but gathering context feels like work
2. **Product vs. platform:** Fitness app or general framework?
3. **DIY threat:** Technical users might just build it themselves
4. **Retention mystery:** What keeps users coming back?

---

## Phase 2: Five Whys + First Principles Results

### The Pivot Moment

User realized: "This isn't a fitness app. It's a general framework for unstructured history → AI agent analysis, with domain expertise injection."

### User's Background Context

**Current workflow:**
- Uses Obsidian daily for todo lists, meeting notes, progress notes
- Before agents: Would get lost, tired of organizing, always gave up
- After agents: Writes unstructured, asks AI agents (Claude, Copilot CLI, Gemini CLI) to find insights
- Built workflows: Daily note generation, monthly reports, annual reports, retrospectives
- Key insight: "I never did annual report on my own because I always get lazy... it was all possible because agents organize all my daily notes"

**Professional background:**
- PhD on automatic assessment of anaerobic workout using inertial sensors (uLift)
- Same problem domain, new approach (AI context instead of hardware sensors)
- Currently working in AI agent engineering

### The First Principle Discovered

**Before Agents:**
```
[User] → Must organize cleanly → So user can extract insights manually
              ↑
        THIS IS THE BURDEN (most people give up here)
```

**After Agents:**
```
[User] → Just write SOMETHING, however messy → [Agent extracts insights]
              ↑
        ONLY REQUIREMENT: Write it down
```

### Fundamental Truths

1. **Writing is the only prerequisite** - Not organizing, not structuring, not formatting
2. **Value emerges from accumulated mass** - No single note matters, the pile matters
3. **Organization is output, not input** - Agent's job to structure, synthesize, extract
4. **Effort threshold determines behavior** - Lower it enough and people actually do it

### The Vision Crystallized

**From:** "AI fitness app that remembers every rep"
**To:** "Framework for context-aware agents from unstructured history, with fitness as first domain"

### Architecture Vision

```
┌─────────────────────────────────────────────────┐
│           APPLICATIONS (built by user/others)    │
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

### GitHub Legacy Goal

An open-source framework for building context-aware AI agents from unstructured user history.
- First application: Fitness (deep domain knowledge from PhD)
- Second application: Obsidian workflow (already uses daily)
- Future: Others build whatever domains they care about

---

## Phase 3: Constraint Mapping + Failure Analysis Results

### Constraint Reality Check

| Constraint | Status | Reasoning |
|------------|--------|-----------|
| Language choice | **Deferred** | AI agent builds it, Python preferred but flexible |
| LLM costs | **Real** | Start local (Ollama), keep API compatibility |
| Context window limits | **Research needed** | Strategy matters more than raw limits |
| Storage format | **Research needed** | Leaning markdown, needs validation |
| Parsing accuracy | **Research needed** | Agent handles most; feedback loop for corrections |
| Solo developer | **Imagined** | AI agents write code via BMAD method |
| Limited time | **Imagined** | Good planning = implementation handled |
| Infrastructure budget | **Real** | Local macbook only for now |
| Ship quickly | **Soft** | Dogfooding important, not deadline-driven |
| Fitness first | **Soft** | Good starting point, not required |
| Generic foundation | **HARD REQUIREMENT** | This is the core - non-negotiable |
| Obsidian integration | **Nice to have** | Proves generalizability, not required |

### Failure Modes and Mitigations

| Failure Mode | Severity | Mitigation |
|--------------|----------|------------|
| **Framework too abstract** | HIGH | Build framework + fitness app TOGETHER - they grow as one |
| **Scope creep** | HIGH | Focus on how it works + performance first. SaaS/API later. |
| **Context strategy fails** | HIGH | Research needed; annual report success suggests it's solvable |
| **Local LLM not smart enough** | MEDIUM | Keep API compatibility; can upgrade later |
| **No dogfooding** | HIGH | User is highly motivated; fitness + Obsidian as test domains |

### Build-Together Approach

```
┌─────────────────────────────────────────────┐
│     WHAT YOU BUILD TOGETHER                 │
│                                             │
│  Framework ←──────────→ Fitness MVP         │
│     │                        │              │
│     │    (grow together)     │              │
│     ▼                        ▼              │
│  Generic abstractions    Concrete usage     │
│  informed by real use    validates the      │
│                          abstractions       │
└─────────────────────────────────────────────┘
```

Input options:
- Dedicated fitness app input, OR
- Obsidian vault (unstructured workout notes)

---

## Phase 4: Emerging Opportunities

### Testing Strategy (To Be Developed)

| Test Type | What It Validates |
|-----------|------------------|
| Unit tests | Parser extracts structured data correctly |
| Integration tests | Full pipeline: input → store → retrieval → insight |
| LLM-as-judge | Quality of insights, recommendations, accuracy |
| Dogfooding | Does it actually help with fitness? |

### Academic Paper Potential

**Potential contributions:**
- Novel framework for context-aware agents from unstructured personal data
- Evaluation methodology (LLM-as-judge for personal AI)
- Case study: fitness domain application
- Comparison: generic LLM vs. context-aware agent quality

**What it would take:**
- Clear problem statement and related work
- Formal framework description
- Evaluation metrics and methodology
- Empirical results (fitness domain as case study)
- Generalizable findings

**Potential venues:** CHI, IUI, UIST (HCI angle), or EMNLP/ACL workshops (NLP/agent angle)

---

## Open Questions for Next Sessions

### Agent Architecture (Priority: HIGH)
- When user writes messy log → what happens?
- When user asks "what should I do today?" → what happens?
- When user asks "show me my progress" → what happens?
- How does domain expertise (fitness) plug in?

### Research Questions (Priority: HIGH)
- Context window strategy for large history (how many days/notes?)
- Storage format (database vs. markdown?)
- Parsing accuracy and feedback loop design
- Local LLM capability requirements

### Scope Questions (Priority: MEDIUM)
- What's minimum viable framework?
- What's minimum viable fitness MVP?
- What defines "done" for v0.1?

---

## Session Outcomes Summary

### What We Started With
- Initial context document about "AI fitness app that remembers every rep"
- Unclear product direction (app? framework? platform?)
- Unexpressed thoughts that needed extraction

### What We Ended With
1. **Clear vision:** Generic framework for context-aware agents, with fitness as first domain
2. **First principle:** "Organization is output, not input"
3. **Build strategy:** Framework + app grow together
4. **Constraint clarity:** Few real constraints, many imagined ones
5. **Failure mitigations:** TDD with LLM-as-judge, dogfooding, build-together approach
6. **New opportunity:** Academic paper potential

### The One-Liner (Updated)

**Before:** "The AI that remembers every rep"
**After:** "A framework for AI agents that turn your messy notes into organized insights - starting with fitness"

---

## Next Steps

1. **Document:** Create updated project context reflecting evolved vision
2. **Research:** Investigate open questions (context strategy, storage, parsing)
3. **Architecture:** Deep dive on agent architecture and data flows
4. **Testing:** Define evaluation methodology and test cases
5. **Academic:** Explore paper framing if pursuing publication
