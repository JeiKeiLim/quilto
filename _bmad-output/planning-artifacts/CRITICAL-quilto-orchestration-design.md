# CRITICAL: Quilto Framework Orchestration Design

**Created:** 2026-01-26
**Source:** Epic 13 Retrospective
**Owner:** Jongkuk Lim (Project Lead)
**Status:** OPEN - Requires Architecture Decision

---

## Issue Summary

Quilto currently provides individual agents but **no orchestration layer**. Applications (like Swealog) must manually import and wire all agents, defeating the purpose of a framework.

This is the **most important design decision** in this project as it defines Quilto's public API.

---

## Current State

Swealog's `execute_query_pipeline()` in `packages/swealog/swealog/api/routes/query.py`:

```python
from quilto.agents import (
    AnalyzerAgent,
    EvaluatorAgent,
    PlannerAgent,
    RetrieverAgent,
    SynthesizerAgent,
)
# Note: ObserverAgent is NEVER imported

async def execute_query_pipeline(...):
    # Swealog manually creates each agent
    router_agent = RouterAgent(llm_client)
    planner = PlannerAgent(llm_client)
    retriever = RetrieverAgent(llm_client)
    analyzer = AnalyzerAgent(llm_client)
    synthesizer = SynthesizerAgent(llm_client)
    evaluator = EvaluatorAgent(llm_client)

    # Swealog manually orchestrates the sequence (~300 lines)
    router_output = await router_agent.classify(...)
    planner_output = await planner.plan(...)
    # ... etc
```

**Problems with this approach:**
1. Swealog is doing Quilto's job (orchestration)
2. Every Quilto application must copy ~300 lines of pipeline code
3. When Quilto adds new agents (Observer), applications don't get them automatically
4. Quilto is just a bag of agents, not a framework

---

## Evidence of Impact

### Observer Never Invoked
- `packages/quilto/quilto/agents/observer.py` - EXISTS
- `packages/quilto/quilto/state/observer_triggers.py` - EXISTS with `trigger_post_query()`, etc.
- `logs/logs/context/` directory - EMPTY (no global context ever written)
- **Result:** Zero personalization despite Observer infrastructure existing

### Retrieval Retry Loop Missing
- Evaluator can return `verdict: insufficient`
- But pipeline doesn't loop back to Retriever with expanded dates
- **Result:** Missing data that might exist with wider date range

### JSON Parse Errors Not Retried
- LLM returns malformed JSON
- Pipeline fails instead of retrying
- **Result:** Recoverable errors become hard failures

---

## Design Decision Required

### Option A: Quilto as Framework (Automatic Orchestration)

```python
# What Quilto SHOULD provide:
from quilto import QueryPipeline

# Application code (Swealog) - simple
pipeline = QueryPipeline(llm_client, storage, domains)
result = await pipeline.run(query)

# Everything automatic:
# - Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator
# - Observer triggers (post_query, significant_log, etc.)
# - Retry loops when Evaluator says insufficient
# - JSON parse error recovery
# - Global context reading/writing
```

**Pros:**
- Applications just configure and call
- New agents automatically included
- No code duplication
- True framework behavior

**Cons:**
- Less flexibility for custom pipelines
- Quilto must handle all edge cases

### Option B: Quilto as Toolkit (Apps Build Pipelines)

```python
# Current approach:
from quilto.agents import RouterAgent, PlannerAgent, ...

# Application must wire everything manually (~300 lines)
# Must remember to add new agents like Observer
```

**Pros:**
- Maximum flexibility
- Applications control everything

**Cons:**
- Code duplication across applications
- New agents require manual integration
- Not a framework, just a library
- **Defeats stated project goals**

---

## Recommendation

**Option A (Framework)** aligns with the project's stated goals:
- Quilto is described as a "domain-agnostic agent framework"
- Swealog should be able to use Quilto "without single modification of code" for new features
- The current state contradicts this design intent

---

## Implementation Considerations

If Option A is chosen, Quilto needs:

1. **Pipeline Orchestration Class**
   ```python
   # packages/quilto/quilto/pipeline.py
   class QueryPipeline:
       def __init__(self, llm_client, storage, domains, config=None): ...
       async def run(self, query) -> PipelineResult: ...
   ```

2. **Move orchestration logic FROM Swealog INTO Quilto**
   - `execute_query_pipeline()` logic moves to Quilto
   - Swealog becomes thin wrapper

3. **Automatic Observer Integration**
   - `trigger_post_query()` called after successful queries
   - `trigger_significant_log()` called after log parsing
   - Global context automatically updated

4. **Retry Loop Implementation**
   - Evaluator insufficient → expand date range → retry Retriever
   - Configurable max retries

5. **Error Recovery**
   - JSON parse errors → retry LLM call
   - Configurable retry policy

---

## Questions to Answer

1. Should Quilto provide one standard pipeline or allow custom pipeline composition?
2. How much configuration should applications be able to override?
3. Should the pipeline be sync, async, or both?
4. How should the pipeline expose intermediate outputs for debugging?
5. Should LangGraph be used internally, or keep it as direct function calls?

---

## Files Affected

If implementing Option A:

| File | Change |
|------|--------|
| `packages/quilto/quilto/pipeline.py` | NEW - Pipeline orchestration |
| `packages/quilto/quilto/__init__.py` | Export QueryPipeline |
| `packages/swealog/swealog/api/routes/query.py` | Simplify to use QueryPipeline |
| `packages/swealog/swealog/cli/auto_cmd.py` | Simplify to use QueryPipeline |

---

## Next Steps

1. **Schedule dedicated architecture discussion** - not part of regular sprint
2. **Review architecture.md** for original design intent
3. **Make decision** on Option A vs Option B
4. **If Option A:** Create epic for Quilto Pipeline implementation
5. **Update public API documentation**

---

## References

- Epic 13 Retrospective: `_bmad-output/implementation-artifacts/epic-13/epic-13-retro-2026-01-26.md`
- Current pipeline: `packages/swealog/swealog/api/routes/query.py`
- Observer triggers: `packages/quilto/quilto/state/observer_triggers.py`
- Observer agent: `packages/quilto/quilto/agents/observer.py`
- Architecture doc: `_bmad-output/planning-artifacts/architecture.md`
