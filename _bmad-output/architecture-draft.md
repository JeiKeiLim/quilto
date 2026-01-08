# Swealog — Architecture Draft

**Created:** 2025-12-31
**Status:** Draft from Brainstorming Session
**Version:** 0.1

---

## Overview

Swealog is a framework for building context-aware AI agents from unstructured user history. This document captures the architecture decisions from the initial brainstorming session.

---

## Core Philosophy

### The First Principle

> **Organization is output, not input.**

- User writes messy, unstructured input
- Agent handles parsing, structuring, organizing
- Value emerges from accumulated mass, not individual entries

### Design Principles

1. **Raw is source of truth** - Preserve unstructured input, derive structure
2. **Domain-agnostic core** - Framework is generic, domain modules add expertise
3. **Composable agents** - Building blocks that can be mixed and matched
4. **Local-first** - Runs on local machine, no cloud dependencies required

---

## Storage Architecture

### Two Types of Storage

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                               │
│                                                                     │
│   ┌────────────────────────┐     ┌────────────────────────────────┐ │
│   │ GLOBAL USER CONTEXT    │     │ INDIVIDUAL ENTRIES             │ │
│   │ (user-context.md)      │     │ (logs/YYYY-MM-DD-HHMMSS.md)    │ │
│   │                        │     │                                │ │
│   │ - Cold start interview │     │ - YAML frontmatter (structured)│ │
│   │ - Agent observations   │     │ - Raw input below (preserved)  │ │
│   │ - User preferences     │     │                                │ │
│   │ - Learned patterns     │     │                                │ │
│   └────────────────────────┘     └────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Individual Entry Format

Each entry is a markdown file with YAML frontmatter:

```markdown
---
date: 2025-12-31
workout_type: chest
exercises:
  - name: bench press
    sets: 5
    reps: 5
    weight: 185
    unit: lbs
    notes: last set grinder
  - name: incline db press
    sets: 4
    reps: 10
    weight: 60
    unit: lbs
skipped:
  - flyes
physical_notes:
  - shoulder tight on warmup
energy: medium-low
parsed_at: 2025-12-31T15:30:00Z
---

Did chest today. Bench felt heavy, 185 for 5x5 but last set was a grinder.
Then incline db 60s for 4x10. Shoulder was tight on warmup.
Skipped flyes, didn't feel like it.
```

**Key Points:**
- Frontmatter contains structured data (for queries, display, charts)
- Raw input preserved below (for insight extraction, nuance)
- Single file = single source of truth
- Obsidian-compatible format
- Applications can derive DB from frontmatter if needed

### Global User Context Format

```markdown
---
# Optional auto-generated structured summary
training_style: bodybuilding
experience: intermediate
current_split: upper_lower
primary_goal: hypertrophy
known_limitations:
  - lower_back_sensitive
  - left_shoulder_impingement
last_updated: 2025-12-31
---

# Cold Start Interview (2025-12-31)

**Training background:** I've been doing bodybuilding-style training for about 5 years. Started with StrongLifts, moved to PPL, now doing modified upper/lower.

**Goals:** Main goal is hypertrophy, but want to maintain strength on big lifts. Not interested in competing.

**Injuries:** Lower back gets tweaky with heavy deadlifts. Left shoulder impingement - need thorough warmup for pressing.

**Current frequency:** 4 days per week, sometimes 5 if I feel good.

---

# Agent Observations

*Silently learned, visible to user, editable*

- 2025-12-15: Tends to skip isolation work when shoulder bothers them
- 2025-12-20: Bench has plateaued around 185 for 3 weeks
- 2025-12-28: Energy mentions are more frequent - possible accumulated fatigue
- 2025-12-30: Prefers concise feedback
```

**Key Points:**
- Follows same pattern: raw content + optional structured frontmatter
- Cold start interview preserved as-is
- Agent observations accumulated over time
- Silent learning but visible to user
- User can edit/correct anytime

---

## Agent Architecture

### Agent Categories

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT CATEGORIES                            │
│                                                                     │
│   ALWAYS PRESENT (Framework Core)                                   │
│   ├── Orchestrator - coordinates all agent interactions             │
│   ├── Input - parse unstructured input, store with frontmatter      │
│   └── Context Retrieval - fetch relevant data from storage          │
│                                                                     │
│   QUERY PIPELINE (composable for user queries)                      │
│   ├── Planner - understand intent, create execution plan            │
│   ├── Clarification - resolve ambiguous queries with user           │
│   ├── Analysis - process/compute over retrieved data                │
│   └── Synthesize - generate response for user                       │
│                                                                     │
│   QUALITY & LEARNING (optional, recommended)                        │
│   ├── Evaluation - check response quality before returning          │
│   ├── Correction - fix mistakes, update context to avoid repeats    │
│   └── Observation - silent pattern learning, update global context  │
│                                                                     │
│   FUTURE / APPLICATION LEVEL                                        │
│   └── Proactive Triggers - surface insights without user asking     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Descriptions

| Agent | Purpose | When Used |
|-------|---------|-----------|
| **Orchestrator** | Coordinates all agent interactions, manages flow | Always |
| **Input** | Parse unstructured input → structured frontmatter + raw storage | On data entry |
| **Context Retrieval** | Fetch relevant entries/context for a query | On query |
| **Planner** | Understand user intent, decide which agents to invoke | On query |
| **Clarification** | Ask user to resolve ambiguous queries | When needed |
| **Analysis** | Process data, compute patterns, identify insights | On query |
| **Synthesize** | Generate human-readable response | On query |
| **Evaluation** | Quality check response before returning | Optional |
| **Correction** | Handle user corrections, update storage & context | On feedback |
| **Observation** | Silently learn patterns, update global context | Background |

### Agent Flow: Write Entry

```
User Input (messy text)
        │
        ▼
┌───────────────┐
│ ORCHESTRATOR  │
└───────────────┘
        │
        ▼
┌───────────────┐     ┌─────────────────────────────────────┐
│ INPUT AGENT   │ ──▶ │ Parse with domain expertise         │
│               │     │ Create frontmatter + preserve raw   │
│               │     │ Store as markdown file              │
└───────────────┘     └─────────────────────────────────────┘
        │
        ▼
┌───────────────┐     ┌─────────────────────────────────────┐
│ OBSERVATION   │ ──▶ │ Check for patterns                  │
│ (background)  │     │ Update global context if needed     │
└───────────────┘     └─────────────────────────────────────┘
        │
        ▼
   Response to User
   (confirmation, quick insight, or silent)
```

### Agent Flow: Query

```
User Query ("What should I do today?")
        │
        ▼
┌───────────────┐
│ ORCHESTRATOR  │
└───────────────┘
        │
        ▼
┌───────────────┐     ┌─────────────────────────────────────┐
│ PLANNER       │ ──▶ │ Understand intent                   │
│               │     │ Create execution plan               │
│               │     │ Determine if clarification needed   │
└───────────────┘     └─────────────────────────────────────┘
        │
        ▼ (if ambiguous)
┌───────────────┐     ┌─────────────────────────────────────┐
│ CLARIFICATION │ ──▶ │ Ask user for specifics              │
│               │     │ Wait for response                   │
│               │     │ Return to Planner                   │
└───────────────┘     └─────────────────────────────────────┘
        │
        ▼
┌───────────────┐     ┌─────────────────────────────────────┐
│ CONTEXT       │ ──▶ │ Fetch relevant entries              │
│ RETRIEVAL     │     │ Fetch global context                │
│               │     │ Domain expertise: what's relevant?  │
└───────────────┘     └─────────────────────────────────────┘
        │
        ▼
┌───────────────┐     ┌─────────────────────────────────────┐
│ ANALYSIS      │ ──▶ │ Process retrieved data              │
│               │     │ Compute patterns, trends            │
│               │     │ Domain expertise: what matters?     │
└───────────────┘     └─────────────────────────────────────┘
        │
        ▼
┌───────────────┐     ┌─────────────────────────────────────┐
│ SYNTHESIZE    │ ──▶ │ Generate response                   │
│               │     │ Domain expertise: format, tone      │
└───────────────┘     └─────────────────────────────────────┘
        │
        ▼ (optional)
┌───────────────┐     ┌─────────────────────────────────────┐
│ EVALUATION    │ ──▶ │ Check quality                       │
│               │     │ Regenerate if poor                  │
└───────────────┘     └─────────────────────────────────────┘
        │
        ▼
   Response to User
```

### Agent Flow: Correction

```
User Feedback ("No, that was 185 not 85")
        │
        ▼
┌───────────────┐
│ ORCHESTRATOR  │
└───────────────┘
        │
        ▼
┌───────────────┐     ┌─────────────────────────────────────┐
│ CORRECTION    │ ──▶ │ Understand what to fix              │
│               │     │ Update storage (frontmatter + raw?) │
│               │     │ Update global context (avoid repeat)│
│               │     │ Confirm fix to user                 │
└───────────────┘     └─────────────────────────────────────┘
```

---

## Domain Expertise Injection

### Injection Points

| Agent | What Domain Expertise Provides |
|-------|-------------------------------|
| **Input** | Schema: what fields to extract, how to interpret domain language |
| **Planner** | Intents: what kinds of queries exist, what plans are valid |
| **Clarification** | Questions: common ambiguities, how to ask for clarity |
| **Context Retrieval** | Relevance: what data matters for which queries |
| **Analysis** | Patterns: what computations matter, what patterns to recognize |
| **Synthesize** | Format: domain language, tone, how to present information |
| **Evaluation** | Quality: what makes a good response in this domain |
| **Correction** | Fixes: common mistakes, how to update correctly |
| **Observation** | Learning: what patterns to track, what to remember |

### Example: Fitness Domain Module

```yaml
name: fitness
version: 0.1

schema:
  exercise_entry:
    required: [date, exercises]
    exercises:
      - name: string
        sets: number
        reps: number
        weight: number
        unit: enum[lbs, kg]
        notes: string (optional)
    optional: [workout_type, skipped, physical_notes, energy]

intents:
  - log_workout: "User wants to record a workout"
  - get_recommendation: "User wants suggestion for next workout"
  - show_progress: "User wants to see progress on exercise/muscle"
  - explain_plateau: "User wants to understand why stuck"
  - get_history: "User wants to see past workouts"

knowledge:
  - exercises.yaml  # exercise names, muscle groups, variations
  - rep_ranges.yaml # typical rep ranges for goals
  - patterns.yaml   # common training patterns to recognize

prompts:
  parser: "prompts/parse_workout.md"
  analysis: "prompts/analyze_fitness.md"
  synthesize: "prompts/fitness_response.md"
```

---

## Agent Packages

### Package Tiers

| Package | Agents Included | Use Case |
|---------|----------------|----------|
| **Minimal** | Orchestrator, Input, Context Retrieval, Synthesize | Simple storage + retrieval |
| **Standard** | Minimal + Planner, Clarification, Analysis | Intelligent queries |
| **Full** | Standard + Evaluation, Correction, Observation | Learning & quality |
| **Custom** | Pick and choose | Power users |

### Package Selection

```yaml
# Domain module specifies package or custom selection
package: full

# Or custom selection:
agents:
  required:
    - orchestrator
    - input
    - context_retrieval
  query:
    - planner
    - clarification
    - analysis
    - synthesize
  optional:
    - evaluation
    - correction
    - observation
```

### MVP Decision

**For fitness dogfooding: Full Package**

Rationale:
- Observation: core to "AI that learns" vision
- Correction: weights/exercises can be mistyped
- Evaluation: recommendation quality matters

---

## Framework vs Application Split

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FRAMEWORK (Swealog Core)                         │
│                                                                     │
│   Provides:                                                         │
│   - Agent "shells" (generic capabilities)                           │
│   - Orchestration logic                                             │
│   - Storage interface (read/write markdown with frontmatter)        │
│   - LLM interface (Ollama, API compatibility)                       │
│   - Agent packages (minimal, standard, full)                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DOMAIN MODULE                                    │
│                                                                     │
│   Provides:                                                         │
│   - Which agents to use (package or custom)                         │
│   - Schema for structured data                                      │
│   - Prompts for each agent                                          │
│   - Domain knowledge files                                          │
│   - Custom agents if needed                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    APPLICATION                                      │
│                                                                     │
│   Provides:                                                         │
│   - User interface (CLI, web, mobile)                               │
│   - Additional storage (DB sync from frontmatter)                   │
│   - Charts, visualizations                                          │
│   - Proactive triggers                                              │
│   - External integrations                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Open Questions (For Research Phase)

### Technical Research Needed

| Question | Impact | Notes |
|----------|--------|-------|
| Context window strategy | High | How to handle large history? RAG? Summarization? |
| Local LLM capabilities | High | Can Ollama models do parsing + analysis? |
| Storage performance | Medium | Markdown vs. DB for large datasets? |
| Parsing accuracy | Medium | Error rates, feedback loop design |

### Architecture Decisions Deferred

| Decision | When to Decide | Notes |
|----------|----------------|-------|
| Orchestrator implementation | Architecture phase | Option A (Planner is orchestrator) vs Option B (separate) |
| Proactive triggers | Post-MVP | Application level feature |
| Multi-LLM support | Post-MVP | Different models for different agents |

---

## Next Steps

1. **Research Phase:** Answer open questions (context strategy, LLM capabilities)
2. **Detailed Design:** Formal interfaces, data contracts between agents
3. **Domain Module:** Define fitness domain module completely
4. **Implementation:** Build framework + fitness MVP together
5. **Testing:** TDD with LLM-as-judge evaluation

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-31 | 0.1 | Initial draft from brainstorming session |
