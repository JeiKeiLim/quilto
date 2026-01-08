# Swealog — Testing Strategy Draft

**Created:** 2025-12-31
**Status:** Draft from Brainstorming Session

---

## Overview

Testing an AI agent framework presents unique challenges: outputs are non-deterministic, quality is subjective, and the core value proposition ("better insights") is hard to measure. This document outlines the testing strategy.

---

## Test Layers

| Layer | What We Test | How | When |
|-------|-------------|-----|------|
| **Unit** | Individual agent logic | Traditional unit tests | Development |
| **Integration** | Agent-to-agent flow | Pipeline tests | Development |
| **LLM Evaluation** | Output quality | LLM-as-judge | Development + CI |
| **Regression** | Changes don't break things | Automated test suite | CI |
| **Dogfooding** | Real-world usefulness | Personal usage | Ongoing |

---

## Unit Testing

### What to Test

| Agent | Unit Tests |
|-------|-----------|
| **Input** | Storage format correct, frontmatter valid YAML |
| **Context Retrieval** | Fetches correct files, applies filters |
| **Planner** | Produces valid execution plan |
| **Orchestrator** | Calls agents in correct order |
| **Correction** | Updates storage correctly |

### Approach

- Standard unit testing (pytest or similar)
- Mock LLM responses for deterministic testing
- Test agent logic, not LLM quality

---

## Integration Testing

### What to Test

- Full pipeline: Input → Storage → Retrieval → Analysis → Synthesize
- Agent handoffs work correctly
- State management between agents
- Error handling when agent fails

### Example Scenarios

```
Scenario: Log and Query
1. User inputs messy workout log
2. Input agent parses and stores
3. User queries "what did I do yesterday?"
4. Full query pipeline returns correct answer

Scenario: Clarification Flow
1. User asks ambiguous question
2. Clarification agent asks for specifics
3. User provides clarification
4. Pipeline continues with clarified intent
```

---

## LLM Evaluation (LLM-as-Judge)

### Why It's Critical

For a system where AI generates output:
- Human review doesn't scale
- Exact match testing is too rigid
- Quality is often subjective/semantic

**LLM-as-judge evaluates whether AI output is "good enough."**

### What to Evaluate

| Agent | Evaluation Criteria |
|-------|-------------------|
| **Input (Parser)** | Did it extract the key information? Is the structure reasonable? |
| **Analysis** | Are the patterns/insights valid? |
| **Synthesize** | Is the response coherent? Does it answer the question? |
| **Observation** | Are the learned patterns accurate? |

### Approach (High Level)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM-AS-JUDGE PIPELINE                            │
│                                                                     │
│   Test Input                                                        │
│       │                                                             │
│       ▼                                                             │
│   Agent Under Test ──▶ Agent Output                                 │
│                              │                                      │
│                              ▼                                      │
│                      ┌───────────────┐                              │
│                      │ JUDGE LLM     │                              │
│                      │               │                              │
│                      │ Given:        │                              │
│                      │ - Input       │                              │
│                      │ - Output      │                              │
│                      │ - Criteria    │                              │
│                      │               │                              │
│                      │ Evaluate:     │                              │
│                      │ - Pass/Fail   │                              │
│                      │ - Score (1-5) │                              │
│                      │ - Reasoning   │                              │
│                      └───────────────┘                              │
│                              │                                      │
│                              ▼                                      │
│                      Test Result                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Open Questions

- Which LLM for judging? (Same as agent? Different? Stronger model?)
- How to handle judge inconsistency?
- What evaluation dataset to build?
- How to integrate into CI?

### Potential Academic Contribution

> Evaluation methodology for personal AI agents using LLM-as-judge could be a novel research contribution.

---

## Regression Testing

### Approach

- Capture known-good outputs as "golden" examples
- Re-run periodically, flag significant deviations
- Human review of flagged cases
- Not exact match - semantic similarity or LLM judgment

### What to Capture

- Input → Output pairs for key scenarios
- Edge cases that have been fixed
- Examples from real dogfooding usage

---

## Dogfooding

### Purpose

The ultimate test: **Does it actually help?**

### Success Metrics

| Metric | How to Measure |
|--------|---------------|
| **Consistent usage** | Used for 30+ days |
| **Better than ChatGPT** | Side-by-side comparison on same query |
| **Pattern detection** | AI catches something user didn't notice |
| **Reduced friction** | Logging feels easier than before |
| **Trusted recommendations** | User follows AI suggestions |

### Tracking

- Keep a dogfooding journal
- Note what works, what fails
- Capture examples of good/bad agent behavior
- Feed back into evaluation dataset

---

## Success Criteria

### Framework Success

- [ ] Agents can be composed into working pipeline
- [ ] Domain module can inject expertise
- [ ] Storage works (write, read, query)
- [ ] Full package runs end-to-end

### Fitness MVP Success

- [ ] Can log workouts via unstructured input
- [ ] Can retrieve insights from history
- [ ] Can get recommendations based on context
- [ ] Global context updates over time

### Dogfooding Success

- [ ] Actually used for 30+ days
- [ ] Gives better advice than generic ChatGPT
- [ ] Catches patterns user didn't notice
- [ ] Feels lower friction than alternatives

---

## Next Steps

1. **Build evaluation dataset** - Collect real input examples
2. **Design judge prompts** - Criteria for each agent type
3. **Implement basic test suite** - Unit + integration
4. **Set up CI pipeline** - Automated testing on changes
5. **Start dogfooding** - Generate real usage data

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-31 | 0.1 | Initial draft from brainstorming session |
