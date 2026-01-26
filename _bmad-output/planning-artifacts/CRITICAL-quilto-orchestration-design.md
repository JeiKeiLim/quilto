# Quilto Framework Public API Design

**Created:** 2026-01-26
**Source:** Epic 13 Retrospective
**Owner:** Jongkuk Lim (Project Lead)
**Status:** DESIGN REQUIRED

---

## Background

Quilto is a domain-agnostic agent framework. Swealog is a fitness app built on it.

**Currently broken:** Swealog manually imports and wires 6 agents (~300 lines). When we added ObserverAgent to Quilto, Swealog didn't get it automatically. The `logs/logs/context/` directory is empty - zero personalization.

This is wrong. Quilto must provide orchestration so applications just configure and call.

---

## Evidence of the Problem

1. **Observer never invoked:** `logs/logs/context/` directory is EMPTY despite Observer infrastructure existing
2. **Manual agent wiring:** `packages/swealog/swealog/api/routes/query.py` has ~300 lines manually orchestrating agents
3. **New agents don't propagate:** When Epic 7 added ObserverAgent to Quilto, Swealog didn't get it
4. **No retry loops:** Evaluator can say "insufficient" but pipeline doesn't retry Retriever with wider dates
5. **Code duplication:** Every Quilto application would have to copy the same orchestration code

---

## The Design Task

Design Quilto's public API for pipeline orchestration.

**Requirements:**
- Applications (like Swealog) configure and call ONE thing
- All agents (Router, Planner, Retriever, Analyzer, Synthesizer, Evaluator, Observer) run automatically
- Retry loops work (Evaluator insufficient → Retriever retries with wider dates)
- Observer triggers automatically (post_query, significant_log, etc.)
- New agents added to Quilto work without app changes
- Apps can customize behavior without reimplementing the pipeline

---

## Design Questions to Answer

1. **Entry point naming:** What is it called? (suggest options, not "QueryPipeline")
2. **Public API shape:** What does the API look like for a developer using Quilto?
3. **Configuration:** How does an app provide LLM client, storage, domains?
4. **Debugging/Logging hooks:** How does an app hook into the pipeline without reimplementing?
5. **Customization:** How does an app customize behavior (skip agents, add custom logic)?
6. **Return type:** What does the result look like?
7. **Package structure:** Where does this code live in `packages/quilto/quilto/`?

---

## Files to Read

| File | Purpose |
|------|---------|
| `packages/swealog/swealog/api/routes/query.py` | Current manual wiring - this logic moves INTO Quilto |
| `packages/quilto/quilto/state/observer_triggers.py` | Observer infrastructure that exists but isn't invoked |
| `packages/quilto/quilto/agents/` | All agents that need orchestration |
| `_bmad-output/planning-artifacts/architecture.md` | Current architecture to update |
| `_bmad-output/project-context.md` | Project rules and constraints |
| `CLAUDE.md` | Project structure (Quilto vs Swealog separation) |

---

## Expected Output

1. **Public API design** with code examples showing how Swealog would use it
2. **Internal architecture** - how orchestration works inside Quilto
3. **Migration path** - how to move from current Swealog implementation to new API
4. **Architecture.md update** - specific changes to document this decision
5. **Implementation stories** - epic to implement the decision

---

## Constraints

- This is Quilto's **PUBLIC API** - defines developer experience for all Quilto applications
- Swealog should NOT need code changes when Quilto adds new agents
- Must support: Observer auto-invocation, retry loops, error recovery
- Local-first (Ollama), but cloud API compatible
- Python 3.13+, async/await, Pydantic v2

---

## References

- Epic 13 Retrospective: `_bmad-output/implementation-artifacts/epic-13/epic-13-retro-2026-01-26.md`
- Current manual pipeline: `packages/swealog/swealog/api/routes/query.py`
- Observer triggers: `packages/quilto/quilto/state/observer_triggers.py`
- Observer agent: `packages/quilto/quilto/agents/observer.py`
