# Swealog — Research Questions

**Created:** 2025-12-31
**Status:** Open - Needs Investigation
**Priority:** Complete before Architecture Phase

---

## Overview

These questions emerged from the brainstorming session and need investigation before we can finalize the architecture. Each question includes current thinking, research approach, and decision criteria.

---

## 1. Context Window Strategy

### The Question

How do we handle large amounts of user history (weeks, months, years of logs) within LLM context limits?

### Current Thinking

- User successfully did annual report from 365 days of Obsidian notes using Claude
- This suggests the problem is solvable with good strategy
- Strategy might matter more than raw context window size

### Research Approaches

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **RAG (Retrieval)** | Store embeddings, retrieve relevant chunks | Scales infinitely | Requires embedding infrastructure |
| **Summarization layers** | Daily → Weekly → Monthly summaries | Compact, hierarchical | Loses detail |
| **Sliding window** | Most recent N entries + key historical | Simple | May miss patterns |
| **Query-driven retrieval** | Fetch based on user's current question | Efficient | Requires good query understanding |
| **Hybrid** | Combination of above | Flexible | Complex |

### Questions to Answer

1. How many days of raw workout logs fit in Ollama's context? (Quantitative test)
2. What context length does a typical insight query need?
3. Does summarization lose critical detail for fitness recommendations?
4. What's the simplest approach that works for MVP?

### Decision Criteria

- Must work with local Ollama models (limited context)
- Must support at least 30 days of history for meaningful patterns
- Should degrade gracefully (more history = slower but works)

---

## 2. Storage Format

### The Question

Should we use database, markdown files, or something else for persistent storage?

### Current Thinking

- Leaning toward markdown (Obsidian-compatible)
- But need to validate performance and query capabilities

### Options Analysis

| Format | Pros | Cons |
|--------|------|------|
| **Markdown files** | Human-readable, Obsidian-compatible, git-friendly, portable | No indexing, slow search at scale |
| **SQLite** | Fast queries, single file, structured | Less human-readable, schema required |
| **JSON files** | Structured, portable | Verbose, harder to read |
| **Hybrid (MD + SQLite index)** | Best of both | More complexity |

### Questions to Answer

1. How fast is grep/ripgrep on 1 year of daily markdown logs?
2. Do we need structured queries (e.g., "all bench press entries")?
3. Is Obsidian compatibility a real requirement or nice-to-have?
4. What's the migration path if we start simple and need to scale?

### Decision Criteria

- Must be local-first (no cloud database)
- Should support eventual Obsidian integration
- Must handle 1+ years of daily entries
- Prefer simplicity for MVP

---

## 3. Parsing Accuracy & Feedback Loop

### The Question

How do we handle cases where the AI misparses unstructured input? How does the system learn from corrections?

### Current Thinking

- AI will get it right most of the time
- Users can provide feedback to correct errors
- Corrections could be stored as notes (like AGENTS.md approach)

### Scenarios to Handle

| Scenario | Example | Handling |
|----------|---------|----------|
| **Obvious parse** | "Bench 185x5x5" → 5 sets of 5 at 185 | Auto-parse |
| **Ambiguous parse** | "Did 5 on bench" → 5 reps? 5 sets? 5 lbs? | Clarify or guess + confirm |
| **Failed parse** | Random notes mixed with workout | Ask or skip |
| **Wrong parse** | AI thinks "135" is reps not weight | User corrects |

### Questions to Answer

1. What's the acceptable error rate for MVP? (10%? 5%? 1%?)
2. Should corrections be explicit ("fix this") or implicit (re-statement)?
3. How are corrections stored and used for future parsing?
4. Do we need a "confirm parsed entry" step, or trust by default?

### Decision Criteria

- Friction of correction must be lower than friction of structured input
- Corrections should improve future parsing (learning)
- Must not lose user data even if parse fails

---

## 4. Local LLM Capabilities

### The Question

What's the minimum LLM capability needed for Swealog to work? Can Ollama models handle it?

### Required Capabilities

| Capability | Importance | Notes |
|------------|------------|-------|
| **Unstructured → Structured parsing** | CRITICAL | Extract exercise, sets, reps, weight from messy text |
| **Context understanding** | CRITICAL | Remember previous entries in conversation |
| **Pattern recognition** | HIGH | Notice trends across entries |
| **Fitness domain knowledge** | MEDIUM | Know what exercises are, reasonable weights, etc. |
| **Recommendation generation** | MEDIUM | Suggest next workout, modifications |

### Models to Evaluate

| Model | Size | Pros | Cons |
|-------|------|------|------|
| **Llama 3.2 (3B)** | Small | Fast, local | May lack nuance |
| **Llama 3.1 (8B)** | Medium | Good balance | Slower |
| **Mistral (7B)** | Medium | Good at structured output | |
| **Phi-3** | Small | Microsoft-backed | Less tested |
| **Qwen 2.5** | Various | Strong at reasoning | |

### Questions to Answer

1. Can 3B model reliably parse workout entries? (Test with real messy logs)
2. What's the speed/quality tradeoff at different sizes?
3. Do we need different models for different tasks? (Parse vs. insight)
4. What's the fallback if local model fails? (API call? Error?)

### Decision Criteria

- Must run on macbook (M1/M2/M3)
- Parsing accuracy > 90% on typical entries
- Response time < 5 seconds for parsing
- Keep API compatibility for optional cloud upgrade

---

## 5. Domain Expertise Injection

### The Question

How does domain-specific knowledge (fitness, notes, tasting) plug into the generic framework?

### Current Thinking

- Domain module provides specialized prompts, schemas, and knowledge
- Core framework is domain-agnostic
- Fitness module is first implementation

### Domain Module Components (Preliminary)

| Component | Purpose | Example (Fitness) |
|-----------|---------|-------------------|
| **Schema** | Structure for parsed entries | Exercise, sets, reps, weight, RPE |
| **Prompts** | Domain-specific instructions | "Interpret RPE as 1-10 scale" |
| **Knowledge** | Domain facts | Exercise names, muscle groups, typical rep ranges |
| **Insights** | Domain-specific analysis | "Your bench plateau might be due to..." |

### Questions to Answer

1. What's the interface between core framework and domain module?
2. How much domain knowledge is needed vs. emergent from LLM?
3. Should domain modules be code, config, or prompts?
4. How do we test domain module quality?

### Decision Criteria

- Easy to create new domain modules
- Domain modules should be declarative if possible
- Must not require framework changes to add new domain

---

## Research Plan

### Phase 1: Quick Experiments (Before Architecture)

1. **Context capacity test:** How many workout log entries fit in Llama 3.2 3B context?
2. **Parsing accuracy test:** Feed 20 real messy workout logs to local model, measure accuracy
3. **Storage speed test:** Grep 365 markdown files vs. SQLite query

### Phase 2: Deeper Investigation (During Architecture)

1. RAG prototype if context limits are hit
2. Feedback loop design if error rate is high
3. Domain module interface design

### Phase 3: Validation (After MVP)

1. Dogfooding results inform all of the above
2. Academic evaluation methodology if pursuing paper

---

## Notes

*Add research findings here as they emerge*

---
