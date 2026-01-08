---
status: 'complete'
created: '2026-01-02'
last_updated: '2026-01-04'
author: 'Jongkuk Lim + Winston (Architect Agent)'
purpose: 'Design the agent orchestration system for Swealog framework'
dependencies:
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/architecture-draft.md'
  - '_bmad-output/planning-artifacts/research/technical-swealog-foundational-research-2026-01-02.md'
next_action: 'Ready for implementation'
decisions_made:
  - 'Q1: Retrieval approach (Model C - Collaborative Loop)'
  - 'Q2: Sufficiency evaluation (structured output, verdict last)'
  - 'Q3: EXPAND vs CLARIFY decision logic'
  - 'Q4: Multi-question handling (Hybrid - Planner classifies dependency)'
  - 'Q5: Retry limit (2 retries, partial + gaps after limit)'
  - 'Q6: Log vs Query classification (automatic with hybrid handling)'
  - 'Q7: Global context format (markdown, periodic + event-triggered updates)'
  - 'Q8: Agent roster (9 agents - Router split from Planner for model flexibility)'
  - 'Q9: Framework vs Application separation (monorepo, two packages)'
  - 'Q10: DomainModule interface (data-driven configuration for agents)'
  - 'Q11: Multi-domain architecture (auto-selection, base + selected domains)'
  - 'Q12: Router classifies input AND selects relevant domains'
  - 'Q13: Domain context flow (traced through all agents)'
  - 'Q14: Mid-flow domain expansion (both Planner and Analyzer can request)'
  - 'Q15: Observer triggers (post-query, user correction, significant log)'
  - 'Q16: Agent interfaces revised with domain context'
  - 'Q17: State machine finalized (13 states, domain expansion, LOG/QUERY/BOTH flows)'
  - 'Q18: Agent prompts defined (all 9 agents, domain-agnostic templates)'
  - 'Q19: Framework decision (LangGraph for orchestration)'
  - 'Q20: LLM client abstraction (tiered config with provider flexibility)'
  - 'Q21: Storage abstraction (StorageRepository pattern)'
  - 'Q22: StorageRepository interface (6 methods)'
  - 'Q23: CLI/API triggers (2 endpoints + CLI import)'
  - 'Q24: Error handling (retry → fallback → degrade cascade)'
  - 'Q25: CORRECTION handling (LOG variant with append strategy, upsert semantics)'
  - 'Q26: Summarization deferred (small entries, Analyzer handles directly)'
  - 'Q27: Retry + domain expansion priority (expand first, then re-retrieve)'
  - 'Q28: Global context size management (2k tokens, configurable, archival strategy)'
---

# Agent System Design

## 1. Purpose & Context

This document captures the design process for Swealog's agent orchestration system. It is the **most critical architectural decision** for the project, as the agent system is the core of the framework.

### Why This Matters

Swealog's value proposition is:
> "Scribble messy notes → AI agents extract insights"

The agent system IS the product. Storage is solved. The question is: **how do agents work together to transform scattered notes into valuable insights?**

### Document Goals

1. Define what agents exist and their responsibilities
2. Map how agents communicate and hand off work
3. Design the state machine for query handling
4. Decide: custom implementation vs framework (LangGraph)
5. Create a design comprehensive enough for implementation

---

## 2. Background & Prior Work

### 2.1 Original Architecture Draft (10 Agents)

From `_bmad-output/architecture-draft.md`, the original proposal had 10 agents:

| Agent | Purpose |
|-------|---------|
| Orchestrator | Coordinates all agent interactions |
| Input | Parse unstructured input → structured frontmatter + raw storage |
| Context Retrieval | Fetch relevant entries/context for a query |
| Planner | Understand user intent, decide which agents to invoke |
| Clarification | Ask user to resolve ambiguous queries |
| Analysis | Process data, compute patterns, identify insights |
| Synthesize | Generate human-readable response |
| Evaluation | Quality check response before returning |
| Correction | Handle user corrections, update storage & context |
| Observation | Silently learn patterns, update global context |

### 2.2 Research Recommendation (4 Agents)

From `technical-swealog-foundational-research-2026-01-02.md`:

> "Begin with 4 consolidated agents (Orchestrator, Parser, Analyst, Coach) rather than 10, using centralized coordination."

**Rationale:** Simpler coordination, easier debugging, less token overhead.

### 2.3 Discussion Outcome (7 Agents Emerging)

From architecture session discussion, we identified these distinct roles:

| Agent | Responsibility |
|-------|---------------|
| Planner | Decompose query, decide strategy |
| Retriever | Fetch relevant entries, expand scope if needed |
| Summarizer | Condense retrieved context for analysis |
| Analyzer | Find patterns, identify reasons |
| Synthesizer | Generate user-facing response |
| Evaluator | Quality check, suggest improvements |
| Clarifier | Ask user for more context when stuck |

**Note:** Parser agent handles input separately (not part of query flow).

---

## 3. Query Flow Analysis

### 3.1 Example Query

> "Why did my bench press feel heavy last week?"

### 3.2 User's Mental Model of Flow

```
1. Retrieve from last week to a week before (could be two weeks)
2. Find out some reason for the chest exhaustion
   2.1. if there is no chest related context, try to fetch more history
   2.2. perhaps in this case if we stretch it to about a month and nothing comes,
        conclude as we don't have data here
   2.3. Agent asks further context to the user. sleep enough? unrecord chest
        workout? stress? etc.
   2.4. if user response with proper reason, update context to proper date or
        today's note and answer to the user
   2.5. if none, we conclude we don't have data and explain generic possible reason
3. if reason found from the previous notes, decide if it's enough to conclude or
   need further investigation.
   3.1. if further investigation is needed go for about a month data to see if
        there is something.
4. Synthesize the reason and response to the user
5. Evaluate the answer from the query by evaluation agent.
6. if not pass, evaluator agent gives reason and try to find better context
7. if pass, gives answer.
```

### 3.3 Flow Diagram

```
Query: "Why did bench press feel heavy last week?"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. RETRIEVAL AGENT                                          │
│    - Fetch last 1-2 weeks                                   │
│    - Filter for chest/bench related                         │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Chest context │
            │   found?      │
            └───────┬───────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
      YES                      NO
        │                       │
        ▼                       ▼
┌──────────────┐    ┌─────────────────────────────────┐
│ 3. ANALYZE   │    │ 2.1 Expand to 1 month           │
│    Is this   │    └─────────────────────────────────┘
│    enough?   │                    │
└──────┬───────┘            ┌───────┴───────┐
       │                    ▼               ▼
   ┌───┴───┐             FOUND          NOT FOUND
   ▼       ▼               │               │
  YES      NO              │               ▼
   │       │               │    ┌─────────────────────┐
   │       ▼               │    │ 2.3 ASK USER        │
   │  ┌─────────┐          │    │ "Sleep? Stress?     │
   │  │ 3.1     │          │    │  Unrecorded workout?"│
   │  │ Expand  │          │    └──────────┬──────────┘
   │  │ to month│          │               │
   │  └────┬────┘          │       ┌───────┴───────┐
   │       │               │       ▼               ▼
   │       ▼               │   USER GIVES      NO INFO
   │    MERGE              │   REASON             │
   │       │               │       │               ▼
   └───────┼───────────────┘       ▼         ┌─────────┐
           │               ┌───────────────┐ │ 2.5     │
           ▼               │ 2.4 UPDATE    │ │ Generic │
┌─────────────────────┐    │ context +     │ │ response│
│ 4. SYNTHESIS AGENT  │    │ answer        │ └────┬────┘
│    Generate response│◄───┴───────────────┘      │
└──────────┬──────────┘                           │
           │                                      │
           ▼                                      │
┌─────────────────────┐                           │
│ 5. EVALUATION AGENT │                           │
│    Quality check    │                           │
└──────────┬──────────┘                           │
           │                                      │
     ┌─────┴─────┐                                │
     ▼           ▼                                │
   PASS        FAIL                               │
     │           │                                │
     │           ▼                                │
     │    ┌─────────────┐                         │
     │    │ 6. RETRY    │                         │
     │    │ Better ctx  │──────┐                  │
     │    └─────────────┘      │                  │
     │                         │                  │
     ▼                         │                  │
┌─────────┐                    │                  │
│ 7. DONE │◄───────────────────┴──────────────────┘
│ Return  │
└─────────┘
```

### 3.4 Complexity Analysis

This flow exhibits:

| Pattern | Present? | Implication |
|---------|----------|-------------|
| Sequential steps | Yes | Simple pipeline could work |
| Conditional branches | Yes | Need if/else logic |
| Loops | Yes | Retry on evaluation failure |
| State tracking | Yes | Remember what we've tried |
| Human-in-the-loop | Yes | Async wait for user input |
| Parallel execution | Maybe | Fetch + analyze could overlap |

**Conclusion:** This is more complex than a simple pipeline. It's a **state machine with cycles and human interaction**.

---

## 4. Agent Definitions

### 4.1 Open Questions (To Be Answered)

Before defining agents, we need to answer:

| Question | Options | Impact |
|----------|---------|--------|
| Who owns the "enough context?" decision? | Analyzer? Separate agent? | Agent boundaries |
| Does Planner exist? | Yes (decompose complex queries) / No (simple routing) | Complexity |
| Who summarizes retrieved content? | Retriever includes summary? Separate Summarizer? | Token efficiency |
| How do agents hand off? | Direct call? Message passing? Shared state? | Implementation |
| Multi-question handling? | Planner decomposes? Sequential? Parallel? | UX |

### 4.2 Proposed Agent Roster (Draft)

| Agent | Responsibility | Input | Output |
|-------|---------------|-------|--------|
| **Router** | Classify query type, initial routing | Raw query | Query type + routing decision |
| **Planner** | Decompose complex queries, create execution plan | Query + type | List of sub-queries or single plan |
| **Retriever** | Fetch relevant entries, expand scope | Query + date range | Retrieved entries + metadata |
| **Summarizer** | Condense context for LLM consumption | Retrieved entries | Compressed context |
| **Analyzer** | Find patterns, assess sufficiency | Query + context | Analysis + "enough?" signal |
| **Synthesizer** | Generate user response | Query + analysis | Draft response |
| **Evaluator** | Quality check | Query + response + context | Pass/Fail + feedback |
| **Clarifier** | Request more info from user | Query + gap identified | Question for user |

**Separate from query flow:**

| Agent | Responsibility | Trigger |
|-------|---------------|---------|
| **Parser** | Raw input → structured JSON | On new entry |
| **Observer** | Pattern detection, context updates | Background / periodic |

### 4.3 Agent Consolidation Options

**Option A: 10 Agents (Original)**
- Fine-grained responsibilities
- More coordination overhead
- Easier to test individually

**Option B: 4 Agents (Research Recommendation)**
- Orchestrator (Router + Planner + coordination)
- Parser (input processing)
- Analyst (Retriever + Summarizer + Analyzer)
- Coach (Synthesizer + Evaluator)

**Option C: 6 Agents (Balanced)**
- Orchestrator (Router + Planner)
- Retriever (fetch + summarize)
- Analyzer (patterns + sufficiency)
- Synthesizer (response generation)
- Evaluator (quality check)
- Clarifier (human interaction)
- Parser (separate, input flow)

**Decision needed:** Which option best balances simplicity vs clarity of responsibility?

---

## 5. State Machine Design

> **Visual Diagram:** See `state-machine-diagram.md` for Mermaid diagrams that render in Obsidian, VS Code, or GitHub.

### 5.1 States Overview

**Entry States:**
| State | Purpose |
|-------|---------|
| ROUTE | Classify input type, select relevant domains |
| BUILD_CONTEXT | Framework builds ActiveDomainContext from selected domains |

**Query Flow States:**
| State | Purpose |
|-------|---------|
| PLAN | Create retrieval strategy, detect domain gaps |
| RETRIEVE | Fetch entries from storage |
| ANALYZE | Find patterns, assess sufficiency |
| SYNTHESIZE | Generate user-facing response |
| EVALUATE | Quality check response |
| CLARIFY | Generate questions for user |
| WAIT_USER | Human-in-the-loop pause |

**Domain Expansion:**
| State | Purpose |
|-------|---------|
| EXPAND_DOMAIN | Load additional domain(s) requested by Planner or Analyzer |

**Log Flow States:**
| State | Purpose |
|-------|---------|
| PARSE | Extract structured data using domain schemas |
| STORE | Save raw + parsed entry to storage |

**Terminal States:**
| State | Purpose |
|-------|---------|
| OBSERVE | Update global context (post-query or post-log) |
| COMPLETE | Session finished |

### 5.2 State Transitions

```
# Entry
ROUTE → BUILD_CONTEXT (always, domains selected)

# Branch by input type
BUILD_CONTEXT → PLAN (if QUERY)
BUILD_CONTEXT → PARSE (if LOG)
BUILD_CONTEXT → PLAN + PARSE (if BOTH, parallel)

# Query flow
PLAN → RETRIEVE (normal)
PLAN → EXPAND_DOMAIN (proactive domain gap)
PLAN → CLARIFY (non-retrievable gaps)
PLAN → SYNTHESIZE (already sufficient)

RETRIEVE → ANALYZE

ANALYZE → SYNTHESIZE (sufficient)
ANALYZE → PLAN (insufficient, re-plan with gaps)
ANALYZE → EXPAND_DOMAIN (gap.outside_current_expertise)

SYNTHESIZE → EVALUATE

EVALUATE → OBSERVE (pass)
EVALUATE → PLAN (fail, under retry limit)
EVALUATE → OBSERVE (fail, over limit, return partial)

# Domain expansion
EXPAND_DOMAIN → BUILD_CONTEXT (rebuild with new domains)

# Clarification
CLARIFY → WAIT_USER
WAIT_USER → ANALYZE (user provided info)
WAIT_USER → SYNTHESIZE (user declined)

# Log flow
PARSE → STORE
STORE → OBSERVE

# Terminal
OBSERVE → COMPLETE
```

### 5.3 State Definition

```python
class SessionState(BaseModel):
    """Full state for a query/log processing session."""

    # Input
    raw_input: str
    input_type: InputType

    # Domain state
    selected_domains: list[str]
    active_context: ActiveDomainContext | None = None
    domain_expansion_history: list[str] = []  # Domains added mid-flow

    # Query decomposition
    query: str | None = None  # Extracted query portion
    query_type: QueryType | None = None
    sub_queries: list[SubQuery] = []

    # Retrieval state
    retrieval_history: list[RetrievalAttempt] = []
    retrieved_entries: list[Entry] = []

    # Analysis state
    analysis: AnalyzerOutput | None = None
    gaps: list[Gap] = []

    # Response state
    draft_response: str | None = None
    evaluation: EvaluatorOutput | None = None
    retry_count: int = 0
    max_retries: int = 2

    # Log state (if LOG or BOTH)
    log_portion: str | None = None
    parsed_entry: ParserOutput | None = None

    # Clarification state
    clarification_questions: list[ClarificationQuestion] = []
    user_responses: dict[str, str] = {}  # gap_id → response

    # Control
    current_state: str
    waiting_for_user: bool = False

    # Output
    final_response: str | None = None
    complete: bool = False
```

### 5.4 Transition Conditions

| From | To | Condition |
|------|-----|-----------|
| ROUTE | BUILD_CONTEXT | Always (domains selected) |
| BUILD_CONTEXT | PLAN | input_type == QUERY |
| BUILD_CONTEXT | PARSE | input_type == LOG |
| BUILD_CONTEXT | PLAN + PARSE | input_type == BOTH |
| PLAN | RETRIEVE | Normal planning, no gaps |
| PLAN | EXPAND_DOMAIN | Query needs unloaded domain |
| PLAN | CLARIFY | Non-retrievable gaps exist |
| PLAN | SYNTHESIZE | Previous attempts sufficient |
| RETRIEVE | ANALYZE | Always |
| ANALYZE | SYNTHESIZE | verdict == SUFFICIENT |
| ANALYZE | PLAN | verdict == INSUFFICIENT |
| ANALYZE | EXPAND_DOMAIN | Any gap.outside_current_expertise == True |
| EXPAND_DOMAIN | BUILD_CONTEXT | Always (rebuild context) |
| CLARIFY | WAIT_USER | Always |
| WAIT_USER | ANALYZE | User provided info |
| WAIT_USER | SYNTHESIZE | User declined |
| SYNTHESIZE | EVALUATE | Always |
| EVALUATE | OBSERVE | verdict == PASS |
| EVALUATE | PLAN | verdict == FAIL AND retry_count < max_retries |
| EVALUATE | OBSERVE | verdict == FAIL AND retry_count >= max_retries |
| PARSE | STORE | Always |
| STORE | OBSERVE | Always |
| OBSERVE | COMPLETE | Always |

**Retry with Domain Expansion:**
If evaluation fails AND Analyzer previously identified domain gaps (`outside_current_expertise`), the retry loop includes domain expansion. Priority order:
1. Expand domains first (if gaps flagged)
2. Re-retrieve with expanded context
3. Re-analyze and synthesize

This ensures domain knowledge gaps are addressed before exhausting retry attempts.

### 5.5 CORRECTION Input Handling

CORRECTION is treated as a LOG variant with update semantics:

```
ROUTE → BUILD_CONTEXT → PARSE (correction mode) → STORE (upsert) → OBSERVE
```

#### Two Correction Scenarios

**Scenario A: Parser Error**
- User wrote correctly, Parser extracted incorrectly
- Raw content is already correct
- Only parsed data needs fixing

**Scenario B: User Typo**
- User made a typo in original input
- Both raw and parsed need fixing

#### Correction Strategy: Append

Rather than overwriting raw content, corrections are appended:

```markdown
## 10:30
I benched 185 today and also squated 200 felt good

## 10:45 [correction]
Correction: bench weight recorded as 85 → corrected to 185
```

**Rationale:**
- Preserves history (auditable)
- Git-friendly (diff shows what changed)
- Human-readable
- Observer can learn from correction patterns

#### Key Flow Differences from Standard LOG

| Aspect | Standard LOG | CORRECTION |
|--------|--------------|------------|
| Router output | `input_type: LOG` | `input_type: CORRECTION`, `correction_target` set |
| Parser mode | Create new entry | Find target + extract delta |
| Store action | Create | Upsert (append correction to raw, update parsed) |
| Observer trigger | `significant_log` | `user_correction` |

---

## 6. Open Design Questions

### 6.1 Critical Questions (Must Answer)

| # | Question | Options | Notes |
|---|----------|---------|-------|
| 1 | **How does Retriever decide what's relevant?** | Keyword match? Date range? LLM decides? | Core to system quality |
| 2 | **How does Analyzer know "enough"?** | Heuristic? LLM self-assessment? | Affects loop behavior |
| 3 | **What triggers EXPAND vs CLARIFY?** | Tried N expansions? Time limit? | User experience |
| 4 | **How to handle multi-question queries?** | Planner decomposes? Run parallel? | Complexity |
| 5 | **Retry limit?** | Fixed (3)? Configurable? | Balance quality vs latency |

### 6.2 Implementation Questions

| # | Question | Options | Notes |
|---|----------|---------|-------|
| 6 | **State persistence** | In-memory? File? Database? | For long-running queries |
| 7 | **Agent communication** | Function calls? Message queue? Shared state? | Architecture style |
| 8 | **Error handling** | Retry? Fallback? Fail fast? | Reliability |
| 9 | **Observability** | Logging? Tracing? Metrics? | Debugging |
| 10 | **Token budget** | Per agent? Total? None? | Cost control |

### 6.3 Framework Decision Factors

| Factor | Custom | LangGraph |
|--------|--------|-----------|
| State machine with cycles | Manual implementation | Built-in |
| Human-in-the-loop | Manual async handling | Built-in |
| Conditional branching | If/else in code | Graph edges |
| Debugging | Print statements | LangSmith integration |
| Learning curve | Python knowledge | LangGraph concepts |
| Dependency | None | langchain ecosystem |
| Flexibility | Full control | Framework constraints |

---

## 7. Design Decisions (Answered)

This section documents the decisions made through collaborative discussion.

### 7.1 Question 1: How does Retriever decide what's relevant?

**Decision: Model C - Collaborative Loop with LLM-driven retrieval**

#### Core Principles

1. **Fully agentic system** - No embeddings, no pre-filtering heuristics. The LLM makes judgment calls.
2. **Quality over efficiency** - Read all entries in scope rather than filtering. Notes are short; modern context windows can handle a full year.
3. **Divide and conquer for scale** - For large scopes (e.g., full year), parallelize with multiple agents processing chunks.

#### Agent Roles in Model C

| Agent | Responsibility | Does NOT do |
|-------|---------------|-------------|
| **Planner** | Query decomposition, retrieval strategy, parallelization, re-planning on feedback | Fetch data, analyze content |
| **Retriever** | Execute retrieval using storage tools, read all entries in scope | Decide strategy, judge sufficiency |
| **Analyzer** | Find patterns, assess sufficiency, identify specific gaps | Fetch data, decide next action |

#### The Collaborative Loop

```
Planner → Retriever → Analyzer
             ↑            ↓
             └── Planner ←┘
                (re-plan if gaps identified)
```

#### Why Model C is Best for Quality

| Dimension | Model C Strength |
|-----------|------------------|
| Completeness | Analyzer identifies gaps, Planner adjusts |
| Accuracy | Analyzer specializes in analysis only |
| Relevance | Feedback loop filters what doesn't help |
| Self-awareness | Explicit sufficiency check in the loop |

**Key insight:** The agent who needs the data (Analyzer) is the one who judges if it's enough.

---

### 7.2 Question 2: How does Analyzer know "enough"?

**Decision: Structured evaluation with verdict generated last**

#### The Sufficiency Standard

The Analyzer evaluates: "Can I respond to this query without unacceptable speculation?"

**Unacceptable speculation** = making claims the data doesn't support.

#### Analyzer Output Structure

```json
{
  "analysis": {
    "query_intent": "...",
    "findings": "...",
    "evidence": ["...", "..."]
  },
  "sufficiency_evaluation": {
    "gaps_identified": ["..."],
    "gap_severity": {
      "critical": [],
      "nice_to_have": []
    },
    "verdict": "SUFFICIENT | INSUFFICIENT"
  }
}
```

#### Critical: Verdict Generated Last

The verdict MUST be the final field generated. This ensures the LLM reasons through all evidence before concluding, avoiding premature commitment bias.

```
Good order (verdict last):
  query_intent → findings → evidence → gaps → severity → verdict

Bad order (verdict first):
  verdict → (now biased to justify the premature conclusion)
```

#### Sufficiency Criteria

| Criterion | Question |
|-----------|----------|
| Evidence check | For every claim, do I have supporting data? |
| Gap assessment | What's missing? Is it CRITICAL or NICE-TO-HAVE? |
| Speculation test | Am I connecting dots that exist, or inventing? |

**SUFFICIENT** = No critical gaps, can answer with evidence
**INSUFFICIENT** = Critical gaps exist, must specify what's missing

---

### 7.3 Question 3: What triggers EXPAND vs CLARIFY?

**Decision: Planner decides using LLM judgment with structured tracking**

#### Core Principle

**Always search before asking.** Never assume data doesn't exist without looking.

#### Decision Flow

```
Analyzer returns INSUFFICIENT with critical_gaps
                    ↓
Planner receives gaps + retrieval_history
                    ↓
For each gap:
    ├── Is it retrievable (could exist in notes)?
    │       ├── YES: Have we searched for it?
    │       │       ├── NO → EXPAND (search for it)
    │       │       └── YES, not found → CLARIFY (ask user)
    │       └── NO (only user knows) → CLARIFY
```

#### Gap Classification

| Gap Type | Category | Action |
|----------|----------|--------|
| Temporal | Retrievable | EXPAND first |
| Topical | Retrievable | EXPAND first |
| Contextual | Retrievable | EXPAND first |
| Subjective-past | Retrievable | EXPAND first (might be logged) |
| Subjective-present | Non-retrievable | CLARIFY |
| Query clarification | Non-retrievable | CLARIFY |

#### Planner State Tracking

```json
{
  "original_query": "...",
  "retrieval_history": [
    { "attempt": 1, "strategy": "date_range", "params": {...}, "result": "..." }
  ],
  "gaps_status": {
    "sleep_data": { "searched": true, "found": false },
    "prior_activity": { "searched": true, "found": true }
  },
  "clarifications_asked": []
}
```

#### Multiple Evidence Types: Parallel Retrieval

When Analyzer identifies multiple gaps, retrieve them in parallel:

```
Analyzer: gaps = [sleep, stress, prior_workouts]
                    ↓
Planner: "Retrieve all three types"
                    ↓
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
Retrieve sleep  Retrieve stress  Retrieve prior
    └───────────────┼───────────────┘
                    ↓
          Combined context
                    ↓
        Analyzer (full picture)
```

#### Domain Knowledge Injection

Planner uses domain expertise to anticipate needed evidence:

**Layer 1: Base knowledge** (in Planner prompt)
- Generic causal reasoning patterns

**Layer 2: Domain modules** (pluggable)
- Domain-specific expertise files (fitness, cooking, work, etc.)
- Loaded when query matches domain triggers

**Layer 3: Global context** (future - learned patterns)
- Personalized patterns learned from user's data over time
- Connects to the Observer agent / global context update feature

```
Single Swealog Deployment
         │
         ├── Domain Module: Fitness
         ├── Domain Module: Cooking
         ├── Domain Module: Work
         ├── Domain Module: Custom (user-defined)
         │
         └── Global Context (Layer 3)
             └── Learned patterns across all domains
```

This enables **one app, many domains, personalized over time**.

---

### 7.4 Question 4: How to handle multi-question queries?

**Decision: Hybrid approach - Planner classifies dependency and chooses strategy**

#### Dependency Classification

| Classification | Definition | Execution Strategy |
|----------------|------------|-------------------|
| **INDEPENDENT** | Sub-queries don't need each other's results | Parallel |
| **DEPENDENT** | One sub-query needs another's output | Sequential |
| **COUPLED** | Sub-queries share context tightly, really one question | Single pass |

#### Planner Classification Criteria

```
INDEPENDENT if:
  - Different subjects/topics
  - No causal relationship
  - Neither references the other's answer

DEPENDENT if:
  - Second question needs first's answer
  - Causal chain (why → how to fix)
  - Follow-up pattern (what happened → what to do about it)

COUPLED if:
  - Same subject, different angles
  - Comparison of related things
  - Questions share the same retrieval context
```

#### Example Classifications

| Query | Classification | Strategy |
|-------|---------------|----------|
| "Compare morning vs evening workouts" | INDEPENDENT | Parallel |
| "Why was bench heavy and how to fix it?" | DEPENDENT | Sequential |
| "What did I eat Tuesday and how much protein?" | COUPLED | Single pass |
| "Analyze my sleep, workouts, and nutrition this month" | INDEPENDENT | Parallel |
| "Why am I plateauing and what program should I try?" | DEPENDENT | Sequential |

#### Planner Output Structure

```json
{
  "query_analysis": {
    "sub_queries": [
      { "id": 1, "question": "Why was I tired last week?" },
      { "id": 2, "question": "What should I change?" }
    ],
    "dependencies": [
      { "from": 1, "to": 2, "reason": "fix requires understanding cause" }
    ],
    "execution_strategy": "SEQUENTIAL",
    "execution_order": [1, 2]
  }
}
```

#### Safety Net

Wrong classification affects efficiency or quality, but the Evaluator catches quality issues. Sequential when parallel is possible = slower but correct. The feedback loop mitigates risks.

---

### 7.5 Question 5: Retry limit?

**Decision: 2 retries (3 total attempts), return partial + gaps after limit**

#### Retry Flow

```
Synthesizer → Response → Evaluator
                             │
                      ┌──────┴──────┐
                      ▼             ▼
                    PASS          FAIL
                      │             │
                      ↓             ↓
                   DONE      retry_count < 2?
                                    │
                             ┌──────┴──────┐
                             ▼             ▼
                            YES           NO
                             │             │
                             ↓             ↓
                      Retry with      Return partial
                      feedback        + gaps
```

#### On Retry

Evaluator provides specific feedback:
- "Response lacks evidence for claim X"
- "Missing context about Y"
- "Speculation without data"

Planner uses feedback to:
- Expand retrieval targeting specific gaps
- Try different retrieval strategy
- Re-run analysis with new context

#### After Limit Reached

Return **partial answer + explicit gaps**:

```
"Here's what I can answer: [partial]
To improve this answer, I would need: [gaps]"
```

This approach is:
- **Honest** - doesn't pretend to have complete answer
- **Actionable** - user knows what's missing
- **Useful** - partial info is better than nothing

#### Rationale

| Factor | Decision |
|--------|----------|
| Diminishing returns | After 2-3 tries, unlikely to improve significantly |
| User experience | 3 attempts keeps response time reasonable |
| Cost | Bounds token usage |
| Quality | Partial + gaps is more valuable than forced complete answer |

---

### 7.6 Additional Decision: Log vs Query Classification

**Decision: Automatic classification with hybrid handling**

#### The Problem

User input could be:
- "Bench 185x5, felt heavy" → LOG
- "Why did my bench feel heavy?" → QUERY
- "Tired today, 4 hours sleep. Why am I always tired?" → BOTH

#### Classification Logic

```
Classifier analyzes input:
  - Has question words (why, how, what, when)? → QUERY
  - Has question mark? → QUERY
  - Declarative statement about past/present? → LOG
  - Contains both logging and question? → BOTH
  - Ambiguous? → Default to LOG
```

#### Flow

```
User Input
     │
     ▼
┌─────────────┐
│ Classifier  │
└──────┬──────┘
       │
  ┌────┼────┐
  ▼    ▼    ▼
 LOG  BOTH  QUERY
  │    │      │
  │    ├──────┤
  ▼    ▼      ▼
Parser      Planner
  │           │
  ▼           ▼
Store     Query Flow
```

If BOTH: Parse and store the log portion first, then trigger query flow.

#### CORRECTION as LOG Variant

CORRECTION inputs (e.g., "actually that was 185 not 85") flow through the LOG path with modifications:

1. **Router** identifies correction intent and extracts `correction_target` (natural language hint)
2. **Parser** operates in correction mode: finds target entry using hint + `recent_entries`, extracts delta
3. **Store** performs upsert: appends correction to raw markdown, updates parsed JSON
4. **Observer** triggers with `user_correction` to learn from the correction

This keeps the state machine simple while handling corrections naturally. See Section 5.5 for full details.

---

### 7.7 Additional Decision: Global Context Update

**Decision: Markdown format, periodic + event-triggered updates**

#### Format: Markdown (not JSON)

```markdown
---
last_updated: 2026-01-03
version: 12
---

# Global Context

## Structured Data

bench_pr: 205 lbs
squat_pr: 285 lbs
typical_workout_days: [Monday, Wednesday, Friday]
average_sleep: 6.5 hours

## Patterns Observed

- Low sleep (<6h) correlates with "heavy" workout mentions
- Morning workouts tend to have better perceived performance
- Recovery mentions increase after travel

## Notes

User started 5/3/1 program in November.
```

**Rationale:**
- Consistent with rest of system (markdown-based)
- LLM reads/writes markdown naturally
- Human readable (can view in Obsidian)
- Flexible for free-form observations

#### Update Triggers

| Trigger | When |
|---------|------|
| **Periodic** | Daily or weekly batch analysis |
| **Event-based** | After significant logs (e.g., new PR, major event) |
| **Query-informed** | When query reveals pattern worth remembering |

#### Observer Agent Flow

```
Observer (triggered):
  1. Read recent logs since last update
  2. Read current global context
  3. Identify new patterns or changes
  4. Generate updated context markdown
  5. Write to global context file
```

#### Context Size Management

**Target size:** ~2000 tokens (configurable via `max_global_context_tokens`)

**Growth strategy:**
- Observer consolidates related insights (e.g., multiple sleep observations → single pattern)
- Older tentative insights that aren't reinforced are pruned
- Certain facts (records, preferences) are retained indefinitely

**Future consideration:** If context grows beyond limit, implement archival to `global-context-archive.md` for historical reference while keeping active context lean.

---

### 7.8 Final Agent Roster

**Decision: 7 Query Flow Agents + 2 Separate Agents**

Splitting Router from Planner ensures robustness across model sizes and enables cost optimization.

**Note on Summarization:** The original design (Section 2.3) considered a dedicated Summarizer agent. This was deferred because individual log entries are expected to be small — Retriever fetches all entries in scope and Analyzer handles analysis directly. If entry sizes grow significantly, summarization can be added to Retriever's output or as a dedicated agent.

#### Query Flow Agents

| Agent | Role | Model Requirement |
|-------|------|-------------------|
| **Router** | Classify input as LOG/QUERY/BOTH | Low (simple task) |
| **Planner** | Decompose queries, strategize, re-plan on feedback | Medium-High |
| **Retriever** | Fetch entries from storage using tools | Low-Medium |
| **Analyzer** | Find patterns, assess sufficiency, identify gaps | High (reasoning) |
| **Synthesizer** | Generate user-facing response | Medium-High |
| **Evaluator** | Quality check, provide specific feedback | Medium-High |
| **Clarifier** | Request missing info from user | Medium |

#### Separate Flow Agents

| Agent | Role | Trigger |
|-------|------|---------|
| **Parser** | Raw input → structured entry with frontmatter | On LOG input |
| **Observer** | Learn patterns, update global context | Periodic + event-triggered |

#### Complete System Flow

```
User Input
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ ROUTER                                                        │
│   Classify: LOG / QUERY / BOTH                               │
└──────────────────────────────────────────────────────────────┘
     │
     ├─────────────────┬─────────────────┐
     ▼                 ▼                 ▼
    LOG              BOTH              QUERY
     │                 │                 │
     │          ┌──────┴──────┐          │
     ▼          ▼             ▼          │
   Parser    Parser        Planner ◄─────┘
     │          │             │
     ▼          │             ▼
   Store        │    ┌────────────────┐
     │          │    │ Query Flow:    │
     ▼          │    │ Planner        │
  Observer      │    │   ↓            │
  (async)       │    │ Retriever      │
                │    │   ↓            │
                │    │ Analyzer ──────┼──► gaps? → back to Planner
                │    │   ↓            │
                │    │ Synthesizer    │
                │    │   ↓            │
                │    │ Evaluator ─────┼──► fail? → back to Planner
                │    │   ↓            │
                │    │ Response       │
                │    └────────────────┘
                │             │
                └─────────────┘
```

#### Agent Responsibilities Summary

| Agent | Input | Output | Key Decisions |
|-------|-------|--------|---------------|
| **Router** | Raw user input | `{ type: LOG/QUERY/BOTH }` | Classification only |
| **Planner** | Query + context | Strategy, sub-queries, retrieval plan | Decomposition, parallelization, re-planning |
| **Retriever** | Planner instructions | Retrieved entries | Uses storage tools, reads all in scope |
| **Analyzer** | Query + entries | Analysis + sufficiency verdict (last) | Patterns, gaps, evidence check |
| **Synthesizer** | Query + analysis | Draft response | User-facing language |
| **Evaluator** | Query + response + context | PASS/FAIL + feedback | Quality check |
| **Clarifier** | Gap description | Question for user | Human-in-the-loop |
| **Parser** | Raw log text | Structured entry (frontmatter + body) | Extract metadata, dates, tags |
| **Observer** | Recent logs + current context | Updated global context | Pattern detection |

---

## 8. Domain Module Architecture

This section documents decisions made on 2026-01-04 regarding framework vs application separation and domain module design.

### 8.1 Framework vs Application Separation

**Decision: Monorepo with two packages**

The project is structured as a monorepo containing:

```
swealog-workspace/
├── pyproject.toml              # Workspace root
├── packages/
│   ├── quilto/                 # Generic framework
│   │   ├── pyproject.toml
│   │   └── quilto/
│   └── swealog/                # Fitness application
│       ├── pyproject.toml
│       └── swealog/
```

**Naming:**
- **Quilto** - The open-source framework
- **Quiltr** - Future SaaS product name (reserved)

**Key Principles:**
- Framework contains all generic agent code, interfaces, orchestration
- Application imports framework and provides domain modules
- Application configures framework with domain-specific knowledge
- Framework is domain-agnostic; all domain-specific logic lives in application

### 8.2 DomainModule Interface

**Decision: Data-driven configuration (Approach A)**

Domain modules provide configuration/context for agents, not behavior. Agents do the reasoning; domain modules provide knowledge.

```python
from pydantic import BaseModel, model_validator
from typing import Self

class DomainModule(BaseModel):
    """Domain configuration provided to the framework.

    Applications register one or more domain modules to customize
    how the framework parses, analyzes, and evaluates domain-specific content.
    """

    name: str | None = None
    """Identifier for this domain. If not provided, uses the class name."""

    description: str
    """Used by Router to auto-select relevant domain(s) for a given input.
    Write a clear description of what this domain covers so agents can match it.
    """

    log_schema: type[BaseModel]
    """Pydantic model defining structured output for parsed entries."""

    vocabulary: dict[str, str]
    """Term normalization mapping. E.g., {"bench": "bench press"}"""

    expertise: str = ""
    """Domain knowledge injected into agent prompts (Analyzer, Planner).
    Can include retrieval guidance, pattern recognition hints, domain principles."""

    response_evaluation_rules: list[str] = []
    """Rules for evaluating Synthesizer's response before returning to user.
    Each rule is a plain-language statement the Evaluator checks against.
    Example: "Never recommend exercises for injured body parts"
    """

    context_management_guidance: str = ""
    """Guidance for Observer agent on what patterns and metrics to track
    in the global context over time. E.g., personal records, rolling averages."""

    @model_validator(mode='after')
    def set_default_name(self) -> Self:
        if self.name is None:
            self.name = self.__class__.__name__
        return self
```

**Field Purpose Summary:**

| Field | Used By | Purpose |
|-------|---------|---------|
| `name` | Framework | Identifier, defaults to class name |
| `description` | Router | Auto-select relevant domains |
| `log_schema` | Parser | Structure for parsed entries |
| `vocabulary` | Parser, Retriever | Term normalization, keyword matching |
| `expertise` | Analyzer, Planner | Domain knowledge in prompts |
| `response_evaluation_rules` | Evaluator | Domain-specific quality checks |
| `context_management_guidance` | Observer | Long-term pattern tracking |

### 8.3 Multi-Domain Architecture

**Decision: Auto-selection with base domain support**

A single application can have multiple domain modules. The framework auto-selects relevant domain(s) for each input.

**Example - Fitness Application:**

```
Application: Fitness App
├── base_domain: GeneralFitnessModule  (always applied)
├── domains:
│   ├── StrengthModule
│   ├── RunningModule
│   └── SwimmingModule
```

**Application Configuration:**

```python
app = SwealogApp(
    base_domain=GeneralFitnessModule,  # Always applied (optional)
    domains=[StrengthModule, RunningModule, SwimmingModule],  # Auto-selected
)
```

**Why Multiple Domains:**

| Subdomain | Vocabulary | Schema | Expertise |
|-----------|-----------|--------|-----------|
| Strength | sets, reps, RPE | Exercise(weight, sets, reps) | Progressive overload, deload cycles |
| Running | pace, splits, distance | Run(distance, time, pace) | Mileage buildup, tapering |
| Swimming | laps, strokes, intervals | Swim(laps, stroke_type, time) | Pool vs open water |

A single monolithic domain module would struggle with diverse subdomains.

### 8.4 Domain Selection Mechanism

**Decision: Router performs auto-selection**

Router now has two responsibilities:
1. Classify input type: LOG / QUERY / BOTH
2. Select relevant domain(s) based on input matching against domain descriptions

**Router Output (updated):**

```python
class RouterOutput(BaseModel):
    input_type: InputType

    # Domain selection
    selected_domains: list[str]
    domain_selection_reasoning: str

    # If BOTH, split input
    log_portion: str | None = None
    query_portion: str | None = None
```

**Selection Flow:**

```
User Input: "Why was my run slow yesterday?"
    ↓
Router reads all domain descriptions:
    - StrengthModule: "Strength training including weightlifting..."
    - RunningModule: "Running, jogging, cardio activities..."
    - SwimmingModule: "Swimming workouts..."
    ↓
Router selects: ["running"]
    ↓
Framework combines: base_domain + selected_domains
```

### 8.5 Multi-Domain Combination

**Decision: Combine base + selected domains per query**

For each query, the framework combines:
- `base_domain` (always applied, if configured)
- `selected_domain(s)` (chosen by Router for this specific input)

**Combination Strategy:**

| Component | How Combined |
|-----------|-------------|
| `vocabulary` | Merge dicts (base + selected) |
| `expertise` | Concatenate with domain labels |
| `log_schema` | Each domain parses independently |
| `response_evaluation_rules` | Combine base + selected |
| `context_management_guidance` | Concatenate with domain labels |

**Example - Multi-Domain Query:**

```
Query: "Compare my running progress with my lifting"
    ↓
Router selects: ["running", "strength"]
    ↓
Combined context:
    vocabulary = {**base.vocab, **running.vocab, **strength.vocab}
    expertise = f"""
    ## General Fitness
    {base.expertise}

    ## Running
    {running.expertise}

    ## Strength Training
    {strength.expertise}
    """
    evaluation_rules = base.rules + running.rules + strength.rules
```

### 8.6 Schema Handling

**Decision: Each domain parses independently (Option A)**

When multiple domains are selected:
- Each domain's `log_schema` is applied independently
- Parser produces separate parsed outputs per domain
- This gives flexibility—domains can have completely different schemas

**Entry Storage:**

```python
class Entry(BaseModel):
    date: date
    timestamp: datetime
    raw_content: str
    parsed_data: dict | None = None  # Domain-specific, schema varies
    source_file: str
    domain: str | None = None  # Which domain parsed this
```

---

## 9. Design Tasks (To Complete)

### Phase 1: Agent Definition
- [x] Answer critical question 1 (Retrieval approach)
- [x] Answer critical question 2 (Sufficiency evaluation)
- [x] Answer critical question 3 (EXPAND vs CLARIFY)
- [x] Answer critical question 4 (Multi-question handling)
- [x] Answer critical question 5 (Retry limit)
- [x] Finalize agent roster (9 agents: 7 query flow + 2 separate)
- [x] Design DomainModule interface
- [x] Design multi-domain architecture
- [x] Trace domain context flow through all agents
- [x] Design mid-flow domain expansion (Planner + Analyzer)
- [x] Design Observer post-query integration
- [x] Revise agent interfaces with domain module changes
- [x] Define agent prompts (high-level structure)

### Phase 2: State Machine
- [x] Finalize state definition (update with domain expansion states)
- [x] Map all transitions with conditions
- [x] Define transition triggers
- [ ] Handle edge cases (timeouts, errors) - defer to implementation

### Phase 3: Framework Decision
- [x] Analyze system complexity (13 states, 4 cycles, HITL, parallel execution)
- [x] Research LangGraph patterns and best practices
- [x] Compare custom vs LangGraph for this use case
- [x] Make final decision: **LangGraph** (see Section 14)
- [x] Design LLM client abstraction (see Section 15)

### Phase 4: Integration Design
- [x] How agents interact with storage layer (see Section 16)
- [x] How domain modules inject expertise (see Section 8 + Section 11)
- [x] How CLI/API triggers agent flows (see Section 16)
- [x] Error handling and recovery (see Section 16)

---

## 10. Session Continuation Guide

### For Fresh Context

If continuing this design in a new session:

1. **Read these documents first:**
   - This document (`agent-system-design.md`)
   - `architecture.md` (storage decisions, tech stack)
   - `swealog-project-context-v2.md` (product vision)

2. **Current status:**
   - Storage architecture: DECIDED
   - Technical stack: DECIDED
   - Agent roster: DECIDED (9 agents, see Section 7.8)
   - Domain Module architecture: DECIDED (see Section 8)
   - Domain context flow: DECIDED (all agents, see Section 11)
   - Mid-flow domain expansion: DECIDED (Planner + Analyzer can request)
   - Observer design: DECIDED (post-query trigger, Claude-style memory)
   - Agent interfaces: REVISED (see Section 11)
   - State machine: FINALIZED (see Section 5 + state-machine-diagram.md)
   - Orchestration framework: DECIDED (LangGraph, see Section 14)
   - LLM client abstraction: DECIDED (tiered config, see Section 15)
   - **Storage layer integration: DECIDED (StorageRepository, see Section 16)**
   - **CLI/API design: DECIDED (2 endpoints + CLI import, see Section 16)**
   - **Error handling: DECIDED (retry cascade, see Section 16)**

3. **Next action:**
   - **Design phase complete — Ready for implementation**
   - Recommended: Run Implementation Readiness Review before coding

4. **Key context to remember:**
   - User prefers comprehensive design before implementation
   - LangGraph chosen for orchestration (cyclic graphs, HITL, checkpointing)
   - LLM calls abstracted via tiered config for easy provider switching
   - Framework is domain-agnostic; applications provide domain modules
   - Single application can have multiple domain modules (auto-selected)
   - No domain-specific examples in docs (avoid steering LLM toward specific domain)

### Key Decisions Already Made

| Decision | Choice | Document/Section |
|----------|--------|------------------|
| Storage format | Markdown raw + JSON parsed | architecture.md |
| Directory structure | `logs/(raw\|parsed)/{YYYY}/{MM}/{YYYY-MM-DD}` | architecture.md |
| LLM client | litellm | architecture.md |
| Async | asyncio | architecture.md |
| Package manager | uv | architecture.md |
| Monorepo | Yes, uv workspace | architecture.md |
| Framework/App separation | Monorepo with two packages | Section 8.1 |
| Domain Module interface | Data-driven configuration | Section 8.2 |
| Multi-domain support | Auto-selection + base domain | Section 8.3-8.4 |
| Domain combination | base + selected per query | Section 8.5 |
| Schema handling | Each domain parses independently | Section 8.6 |
| Orchestration framework | LangGraph | Section 14 |
| LLM abstraction | Tiered config with provider flexibility | Section 15 |
| **Storage abstraction** | **StorageRepository pattern** | **Section 16** |
| **CLI/API design** | **2 endpoints + CLI import** | **Section 16** |
| **Error handling** | **Retry → Fallback → Degrade** | **Section 16** |

### Principles to Follow

1. **"Boring technology"** - Prefer simple solutions that work
2. **"Organization is output, not input"** - Core philosophy
3. **User value first** - Every decision should serve the end user
4. **Dogfooding** - Design for founder's actual use (fitness + Obsidian)

---

## 11. Agent Interfaces (Revised)

This section defines the input/output contracts for each agent using Pydantic-style type definitions. These interfaces enable:
- Clear agent boundaries
- Type-safe communication
- Testable contracts
- Framework-agnostic implementation
- Domain context flow through the system

### 11.1 Shared Types

These types are shared across multiple agents:

```python
from datetime import date, datetime
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class InputType(str, Enum):
    """Classification of user input."""
    LOG = "log"           # Pure logging statement
    QUERY = "query"       # Question requiring answer
    BOTH = "both"         # Contains both logging and query
    CORRECTION = "correction"  # User correcting previous data


class QueryType(str, Enum):
    """Classification of query intent."""
    SIMPLE = "simple"           # Direct retrieval ("show me X")
    INSIGHT = "insight"         # Why/pattern questions
    RECOMMENDATION = "recommendation"  # What should I do
    COMPARISON = "comparison"   # Compare X vs Y
    CORRECTION = "correction"   # Fix previous data


class DependencyType(str, Enum):
    """Multi-question dependency classification."""
    INDEPENDENT = "independent"  # Can run in parallel
    DEPENDENT = "dependent"      # Sequential, later needs earlier
    COUPLED = "coupled"          # Really one question


class GapType(str, Enum):
    """Classification of missing information."""
    TEMPORAL = "temporal"        # Need different time range
    TOPICAL = "topical"          # Need different subject matter
    CONTEXTUAL = "contextual"    # Need related context
    SUBJECTIVE = "subjective"    # Only user knows (current state)
    CLARIFICATION = "clarification"  # Query itself is ambiguous


class Verdict(str, Enum):
    """Binary sufficiency/evaluation verdict."""
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    PASS = "pass"
    FAIL = "fail"


# ─────────────────────────────────────────────────────────────
# Domain Context Types
# ─────────────────────────────────────────────────────────────

class DomainInfo(BaseModel):
    """Minimal domain information for selection."""
    name: str
    description: str


class ActiveDomainContext(BaseModel):
    """Combined context from base + selected domains.

    Built by framework after Router selects domains.
    Passed to agents that need domain knowledge.
    """
    domains_loaded: list[str]
    vocabulary: dict[str, str]  # Term normalization mapping
    expertise: str              # Combined domain expertise (labeled sections)
    evaluation_rules: list[str] # Combined rules for Evaluator
    context_guidance: str       # Combined guidance for Observer

    # For domain expansion
    available_domains: list[DomainInfo]  # Domains not yet loaded


# ─────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────

class DateRange(BaseModel):
    """A date range for retrieval."""
    start: date
    end: date
    description: str | None = None  # e.g., "last week", "past month"


class Entry(BaseModel):
    """A single log entry from storage."""
    date: date
    timestamp: datetime
    raw_content: str
    domain_data: dict[str, Any] | None = None  # Keyed by domain name
    source_file: str


class RetrievalAttempt(BaseModel):
    """Record of a single retrieval attempt."""
    attempt_number: int
    strategy: str  # "date_range", "keyword", "topical"
    params: dict   # Strategy-specific parameters
    entries_found: int
    summary: str   # Brief description of what was found


class Gap(BaseModel):
    """An identified gap in available information."""
    description: str
    gap_type: GapType
    severity: Literal["critical", "nice_to_have"]
    searched: bool = False
    found: bool = False

    # Domain-related (for domain expansion)
    outside_current_expertise: bool = False
    suspected_domain: str | None = None  # Hint for Planner


class EvaluationFeedback(BaseModel):
    """Specific feedback from evaluation failure."""
    issue: str
    suggestion: str
    affected_claim: str | None = None
```

### 11.2 Router Agent Interface

**Purpose:** Classify raw user input and select relevant domains.

**Model Requirement:** Low (classification + matching)

```python
class RouterInput(BaseModel):
    """Input to Router agent."""
    raw_input: str
    session_context: str | None = None  # Recent conversation

    # All registered domains (for selection)
    available_domains: list[DomainInfo]


class RouterOutput(BaseModel):
    """Output from Router agent."""
    input_type: InputType
    confidence: float = Field(ge=0.0, le=1.0)

    # Domain selection
    selected_domains: list[str]  # Domain names to activate
    domain_selection_reasoning: str

    # If BOTH, split the input
    log_portion: str | None = None
    query_portion: str | None = None

    # If CORRECTION, identify what's being corrected
    correction_target: str | None = None

    reasoning: str  # Brief explanation of classification
```

**Classification Rules (embedded in prompt):**
- Has question words (why, how, what, when, which) → likely QUERY
- Has question mark → likely QUERY
- Declarative statement about action/event → likely LOG
- "Actually", "I meant", "that was wrong" → likely CORRECTION
- Contains both logging and questioning → BOTH

**Domain Selection (embedded in prompt):**
- Match input keywords/topics against domain descriptions
- Select all domains that are relevant (can be multiple)
- When uncertain, prefer broader selection over missing relevant domains

### 11.3 Planner Agent Interface

**Purpose:** Decompose queries, create retrieval strategy, detect domain gaps, re-plan on feedback.

**Model Requirement:** Medium-High (reasoning about strategy)

```python
class PlannerInput(BaseModel):
    """Input to Planner agent."""
    query: str
    query_type: QueryType | None = None

    # Domain context
    domain_context: ActiveDomainContext

    # Context from previous attempts (for re-planning)
    retrieval_history: list[RetrievalAttempt] = []
    gaps_from_analyzer: list[Gap] = []
    evaluation_feedback: EvaluationFeedback | None = None

    # Global context summary
    global_context_summary: str | None = None


class SubQuery(BaseModel):
    """A decomposed sub-query."""
    id: int
    question: str
    retrieval_strategy: str  # "date_range", "keyword", "topical"
    retrieval_params: dict   # Strategy-specific parameters


class PlannerOutput(BaseModel):
    """Output from Planner agent."""
    # Query analysis
    original_query: str
    query_type: QueryType

    # Decomposition (if complex query)
    sub_queries: list[SubQuery]
    dependencies: list[dict]  # {"from": 1, "to": 2, "reason": "..."}
    execution_strategy: DependencyType
    execution_order: list[int]  # Order of sub_query IDs

    # Retrieval instructions for Retriever
    retrieval_instructions: list[dict]

    # State tracking
    gaps_status: dict[str, dict]  # {"topic_x": {"searched": true, "found": false}}

    # Domain expansion (proactive)
    domain_expansion_request: list[str] | None = None
    expansion_reasoning: str | None = None

    # Action decision
    next_action: Literal["retrieve", "expand_domain", "clarify", "synthesize"]
    clarify_questions: list[str] | None = None

    reasoning: str
```

**Planning Logic:**
1. Check if query requires domains not currently loaded → request expansion
2. Classify query type
3. Check if decomposition needed (multiple questions)
4. For each gap from Analyzer:
   - If outside_current_expertise → check if domain expansion helps
   - If retrievable → plan retrieval
   - If non-retrievable → prepare clarification
5. Generate retrieval instructions
6. Track what's been searched

### 11.4 Retriever Agent Interface

**Purpose:** Execute retrieval using storage tools. Reads all entries in scope.

**Model Requirement:** Low-Medium (tool use, minimal judgment)

```python
class RetrieverInput(BaseModel):
    """Input to Retriever agent."""
    instructions: list[dict]  # From Planner's retrieval_instructions
    vocabulary: dict[str, str]  # For term normalization
    max_entries: int = 100  # Safety limit


class RetrieverOutput(BaseModel):
    """Output from Retriever agent."""
    entries: list[Entry]

    # Metadata about retrieval
    retrieval_summary: list[RetrievalAttempt]
    total_entries_found: int
    date_range_covered: DateRange | None = None

    # Warnings
    warnings: list[str] = []
    truncated: bool = False  # True if hit max_entries limit
```

**Tool Interface (Retriever calls these):**
```python
# Storage tools available to Retriever
def get_entries_by_date_range(start: date, end: date) -> list[Entry]: ...
def get_entries_by_keyword(keywords: list[str], date_range: DateRange | None) -> list[Entry]: ...
def get_entries_by_topic(topic: str, date_range: DateRange | None) -> list[Entry]: ...
```

**Term Normalization:**
Retriever uses vocabulary to expand search terms. For example, if vocabulary contains `{"pr": "personal record"}`, searching for "pr" also searches for "personal record".

### 11.5 Analyzer Agent Interface

**Purpose:** Find patterns, assess sufficiency, identify gaps. VERDICT GENERATED LAST.

**Model Requirement:** High (reasoning, pattern recognition)

```python
class AnalyzerInput(BaseModel):
    """Input to Analyzer agent."""
    query: str
    query_type: QueryType
    sub_query_id: int | None = None

    # Retrieved context
    entries: list[Entry]
    entries_summary: str | None = None  # Pre-summarized if large

    # Domain context
    domain_context: ActiveDomainContext

    # Additional context
    global_context: str | None = None
    retrieval_history: list[RetrievalAttempt] = []


class Finding(BaseModel):
    """A single finding from analysis."""
    claim: str
    evidence: list[str]  # References to specific entries/dates
    confidence: Literal["high", "medium", "low"]


class AnalyzerOutput(BaseModel):
    """Output from Analyzer agent. VERDICT IS LAST FIELD."""
    # Analysis (generated first)
    query_intent: str
    findings: list[Finding]
    patterns_identified: list[str]

    # Sufficiency evaluation (generated second)
    gaps_identified: list[Gap]  # Includes outside_current_expertise flag

    # Verdict (generated LAST - critical for avoiding bias)
    verdict: Verdict
    verdict_reasoning: str
```

**Critical Instruction:** The Analyzer prompt MUST instruct the model to generate fields in order, with `verdict` absolutely last. This prevents premature commitment bias.

**Domain Gap Detection:**
When Analyzer encounters data it cannot properly interpret with current expertise, it should:
1. Set `gap.outside_current_expertise = True`
2. Set `gap.suspected_domain` if it can identify which domain might help
3. The gap flows back to Planner for domain expansion decision

### 11.6 Synthesizer Agent Interface

**Purpose:** Generate user-facing response from analysis.

**Model Requirement:** Medium-High (natural language generation)

```python
class SynthesizerInput(BaseModel):
    """Input to Synthesizer agent."""
    query: str
    query_type: QueryType

    # From Analyzer
    analysis: AnalyzerOutput

    # Domain context (for terminology)
    vocabulary: dict[str, str]

    # For partial answers (after retry limit)
    is_partial: bool = False
    unanswered_gaps: list[Gap] = []

    # User preferences
    response_style: Literal["concise", "detailed"] = "concise"


class SynthesizerOutput(BaseModel):
    """Output from Synthesizer agent."""
    response: str  # The user-facing answer

    # Structured metadata
    key_points: list[str]
    evidence_cited: list[str]  # Dates/entries referenced

    # For partial answers
    gaps_disclosed: list[str] = []

    # Confidence signal
    confidence: Literal["high", "medium", "low"]
```

### 11.7 Evaluator Agent Interface

**Purpose:** Quality check response. Binary PASS/FAIL with specific feedback.

**Model Requirement:** Medium-High (critical assessment)

```python
class EvaluatorInput(BaseModel):
    """Input to Evaluator agent."""
    query: str
    response: str  # From Synthesizer

    # Context for fact-checking
    analysis: AnalyzerOutput
    entries_summary: str

    # Domain-specific evaluation rules
    evaluation_rules: list[str]

    # Retry context
    attempt_number: int = 1
    previous_feedback: list[EvaluationFeedback] = []


class EvaluationDimension(BaseModel):
    """Evaluation on a single dimension."""
    dimension: str  # "accuracy", "relevance", "safety", "completeness"
    verdict: Verdict
    reasoning: str
    issues: list[str] = []


class EvaluatorOutput(BaseModel):
    """Output from Evaluator agent."""
    # Dimension-level evaluation
    dimensions: list[EvaluationDimension]

    # Overall verdict
    overall_verdict: Verdict

    # If FAIL, specific feedback for retry
    feedback: list[EvaluationFeedback] = []

    # Recommendation
    recommendation: Literal["accept", "retry_with_feedback", "retry_with_more_context", "give_partial"]
```

**Evaluation Dimensions:**
1. **Accuracy:** Claims supported by evidence?
2. **Relevance:** Answers what user asked?
3. **Safety:** No harmful recommendations? (domain rules define "harmful")
4. **Completeness:** Addresses all parts of query?

**Domain Rules:**
Evaluator receives `evaluation_rules` from active domains. These are plain-language rules to check against. Example rules:
- "Do not make claims without supporting data"
- "Recommend consulting professionals for health/legal/financial advice"
- "Verify quantitative claims against historical data"

### 11.8 Clarifier Agent Interface

**Purpose:** Generate questions for user when information is missing.

**Model Requirement:** Medium (natural question generation)

```python
class ClarifierInput(BaseModel):
    """Input to Clarifier agent."""
    original_query: str
    gaps: list[Gap]  # From Analyzer, filtered to non-retrievable
    vocabulary: dict[str, str]  # For proper terminology

    # Context to avoid asking about things we could look up
    retrieval_history: list[RetrievalAttempt]

    # User interaction history (avoid re-asking)
    previous_clarifications: list[str] = []


class ClarificationQuestion(BaseModel):
    """A question to ask the user."""
    question: str
    gap_addressed: str  # Which gap this would fill
    options: list[str] | None = None  # Multiple choice if applicable
    required: bool = True


class ClarifierOutput(BaseModel):
    """Output from Clarifier agent."""
    questions: list[ClarificationQuestion]

    # Framing for user
    context_explanation: str  # Why we're asking

    # If user declines, what we can still do
    fallback_action: str
```

### 11.9 Parser Agent Interface

**Purpose:** Convert raw user input to structured entry. (Separate from query flow)

**Model Requirement:** Medium (structured extraction)

```python
class ParserInput(BaseModel):
    """Input to Parser agent."""
    raw_input: str
    timestamp: datetime

    # Domain schemas (from selected domains)
    domain_schemas: dict[str, type[BaseModel]]  # {"domain_name": SchemaClass}
    vocabulary: dict[str, str]  # For term normalization

    # Context for better extraction
    global_context: str | None = None
    recent_entries: list[Entry] = []

    # Correction mode (see Section 5.5)
    correction_mode: bool = False
    correction_target: str | None = None  # Natural language hint from Router


class ParserOutput(BaseModel):
    """Output from Parser agent."""
    # Metadata
    date: date
    timestamp: datetime
    tags: list[str] = []

    # Domain-specific parsed data (one per domain schema)
    domain_data: dict[str, Any]  # {"domain_name": parsed_model_instance}

    # Raw preservation
    raw_content: str

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_notes: list[str] = []  # Ambiguities, assumptions made

    # Fields that need user confirmation
    uncertain_fields: list[str] = []

    # Correction output (see Section 5.5)
    is_correction: bool = False
    target_entry_id: str | None = None  # Identified entry to update
    correction_delta: dict[str, Any] | None = None  # Fields that changed
```

**Multi-Domain Parsing:**
When multiple domains are selected, Parser applies each domain's schema independently. The output `domain_data` contains one entry per domain that successfully extracted data.

Example:
```python
# Input: "Had coffee and toast for breakfast, then went for a 5k run"
# Selected domains: ["nutrition", "cardio"]

parser_output.domain_data = {
    "nutrition": {"meal": "breakfast", "items": ["coffee", "toast"]},
    "cardio": {"activity": "run", "distance_km": 5.0}
}
```

### 11.10 Observer Agent Interface

**Purpose:** Learn patterns, update global context. Runs post-query and on significant events.

**Model Requirement:** Medium-High (pattern recognition, synthesis)

```python
class ObserverInput(BaseModel):
    """Input to Observer agent."""
    # Trigger context
    trigger: Literal["post_query", "user_correction", "significant_log"]

    # Query context (if post_query)
    query: str | None = None
    analysis: AnalyzerOutput | None = None
    response: str | None = None

    # Correction context (if user_correction)
    correction: str | None = None
    what_was_corrected: str | None = None

    # Log context (if significant_log)
    new_entry: Entry | None = None

    # Current state
    current_global_context: str

    # Domain guidance
    context_management_guidance: str


class ContextUpdate(BaseModel):
    """A single update to global context."""
    category: Literal["preference", "pattern", "fact", "insight"]
    key: str              # e.g., "unit_preference", "typical_schedule"
    value: str
    confidence: Literal["certain", "likely", "tentative"]
    source: str           # What triggered this


class ObserverOutput(BaseModel):
    """Output from Observer agent."""
    # Decision
    should_update: bool

    # Updates to apply
    updates: list[ContextUpdate]

    # What was learned (for logging)
    insights_captured: list[str]
```

**Trigger Types:**

| Trigger | When | What Observer Looks For |
|---------|------|------------------------|
| `post_query` | After every query completes | Patterns revealed during analysis, inferred preferences |
| `user_correction` | When user corrects data | Explicit preferences to remember |
| `significant_log` | After parsing notable entries | Milestones, new records, major events |

**Global Context Structure:**
```markdown
---
last_updated: 2026-01-04
version: 15
---

# Global Context

## Preferences (certain)
- unit_preference: metric
- response_style: concise

## Patterns (likely)
- typical_active_days: [Monday, Wednesday, Friday]
- usual_time_of_day: morning

## Facts (certain)
- records: {metric_a: value, metric_b: value}
- current_routine: description

## Insights (tentative)
- Observed correlation or pattern
- Another observation
```

---

## 12. Agent Prompt Structures

This section outlines the high-level structure for each agent's prompt. Full prompts will be developed during implementation. All prompts are domain-agnostic; domain-specific content is injected via placeholders.

### 12.1 Prompt Design Principles

1. **Role clarity:** Each prompt starts with clear role definition
2. **Input schema:** Explicitly show expected input format
3. **Output schema:** Define output JSON schema (Pydantic)
4. **Domain injection:** Domain expertise injected via placeholders, not hardcoded
5. **Few-shot examples:** Include 2-3 examples for ambiguous tasks (generic)
6. **Constraints:** Explicit boundaries (what NOT to do)
7. **Order matters:** For Analyzer, enforce verdict-last generation

### 12.2 Router Prompt

```
ROLE: You are an input classifier and domain selector for a personal logging system.

TASKS:
1. Classify the user's input type
2. Select relevant domain(s) for processing

=== CLASSIFICATION RULES ===

INPUT TYPES:
- LOG: Declarative statements recording activities, events, or observations
- QUERY: Questions seeking information, insights, or recommendations
- BOTH: Input that logs something AND asks a question
- CORRECTION: User fixing previously recorded information ("actually", "I meant", "that was wrong")

SIGNALS:
- Question words (why, how, what, when, which) → QUERY
- Question mark → QUERY
- Past tense declarative → LOG
- Correction language → CORRECTION

=== DOMAIN SELECTION ===

Available domains:
{available_domains_with_descriptions}

Select ALL domains that are relevant to the input. When uncertain, prefer broader selection.

=== INPUT ===
{raw_input}

Session context (recent messages):
{session_context}

=== OUTPUT (JSON) ===
{RouterOutput.model_json_schema()}
```

### 12.3 Planner Prompt

```
ROLE: You are a query strategist for a context-aware AI system.

TASK: Analyze the query and create an execution plan. Decide what to retrieve, whether domains need expansion, or if clarification is needed.

=== DOMAIN EXPERTISE ===
{domain_context.expertise}

=== VOCABULARY ===
{domain_context.vocabulary}

=== AVAILABLE DOMAINS (not loaded) ===
{available_domains_with_descriptions}

=== PLANNING RULES ===

1. ALWAYS search before asking the user
2. For gaps marked "retrievable" → plan retrieval
3. For gaps marked "non-retrievable" → prepare clarification
4. For gaps marked "outside_current_expertise" → request domain expansion
5. Track what has been searched to avoid redundant retrieval
6. If query mentions topics not covered by loaded domains → request expansion proactively

=== CONTEXT ===

Query: {query}
Query type: {query_type}
Previous retrieval attempts: {retrieval_history}
Gaps from Analyzer: {gaps_from_analyzer}
Evaluation feedback (if retry): {evaluation_feedback}
Global context: {global_context_summary}

=== OUTPUT (JSON) ===
{PlannerOutput.model_json_schema()}
```

### 12.4 Retriever Prompt

```
ROLE: You are a retrieval agent that fetches relevant entries from storage.

TASK: Execute the retrieval instructions using available tools. Fetch all entries in scope without pre-filtering.

=== VOCABULARY ===
Use this vocabulary to expand search terms:
{vocabulary}

Example: If vocabulary contains {"pr": "personal record"}, searching for "pr" should also match "personal record".

=== RETRIEVAL INSTRUCTIONS ===
{instructions}

=== TOOLS AVAILABLE ===
- get_entries_by_date_range(start, end) → Fetch all entries in date range
- get_entries_by_keyword(keywords, date_range?) → Search by keywords
- get_entries_by_topic(topic, date_range?) → Search by topic/category

=== RULES ===
1. Execute each instruction using appropriate tool
2. Apply vocabulary normalization to expand search terms
3. Do not filter or judge relevance - return all matches
4. Report warnings if no results found for an instruction
5. Respect max_entries limit

=== OUTPUT (JSON) ===
{RetrieverOutput.model_json_schema()}
```

### 12.5 Analyzer Prompt

```
ROLE: You are an analytical agent that finds patterns and assesses information sufficiency.

TASK: Analyze retrieved entries to answer the query. Determine if you have enough information.

=== DOMAIN EXPERTISE ===
{domain_context.expertise}

=== CRITICAL INSTRUCTION: GENERATION ORDER ===

You MUST generate your response in this EXACT order:
1. FIRST: Restate query intent
2. SECOND: List findings with evidence
3. THIRD: Identify patterns
4. FOURTH: Identify gaps and classify severity
5. LAST: Render verdict (SUFFICIENT or INSUFFICIENT)

The verdict MUST be the final field you generate. This prevents premature commitment.

=== GAP CLASSIFICATION ===

For each gap, determine:
- gap_type: TEMPORAL | TOPICAL | CONTEXTUAL | SUBJECTIVE | CLARIFICATION
- severity: "critical" (blocks answer) | "nice_to_have" (improves answer)
- outside_current_expertise: true if gap requires domain knowledge you don't have
- suspected_domain: if outside expertise, which available domain might help

=== SUFFICIENCY STANDARD ===

SUFFICIENT = You can answer without unacceptable speculation
INSUFFICIENT = Critical gaps exist that block a quality answer

Ask yourself: "For every claim I would make, do I have supporting evidence?"

=== INPUT ===

Query: {query}
Query type: {query_type}
Retrieved entries: {entries}
Global context: {global_context}
Retrieval history: {retrieval_history}
Currently loaded domains: {domain_context.domains_loaded}
Available domains: {domain_context.available_domains}

=== OUTPUT (JSON) ===
{AnalyzerOutput.model_json_schema()}
```

### 12.6 Synthesizer Prompt

```
ROLE: You are a response generation agent that creates user-facing answers.

TASK: Generate a clear, helpful response based on the analysis.

=== VOCABULARY ===
Use proper terminology from the domain:
{vocabulary}

=== INPUT ===

Query: {query}
Analysis findings: {analysis.findings}
Patterns identified: {analysis.patterns_identified}
Response style: {response_style}  # "concise" or "detailed"

Is partial answer: {is_partial}
Unanswered gaps (if partial): {unanswered_gaps}

=== RESPONSE GUIDELINES ===

1. Address what the user asked directly
2. Support claims with evidence (cite dates/entries)
3. Use domain-appropriate terminology
4. Match requested response style (concise vs detailed)
5. If partial: clearly state what you can answer and what remains unknown

=== IF PARTIAL ANSWER ===

Structure as:
"Here's what I can tell you: [answer based on available data]

To provide a more complete answer, I would need: [list gaps]"

=== OUTPUT (JSON) ===
{SynthesizerOutput.model_json_schema()}
```

### 12.7 Evaluator Prompt

```
ROLE: You are a quality assurance agent. Your job is to critically assess responses before they reach the user.

TASK: Evaluate the response on multiple dimensions. Be strict but fair.

=== EVALUATION DIMENSIONS ===

1. ACCURACY
   - Every claim must be supported by evidence
   - Speculation without data = FAIL
   - Check claims against the analysis findings

2. RELEVANCE
   - Response must address what the user actually asked
   - Tangential information without answering the question = FAIL

3. SAFETY
   - Apply domain-specific safety rules below
   - Harmful or dangerous recommendations = FAIL

4. COMPLETENESS
   - All parts of the query should be addressed
   - Missing major aspects = FAIL

=== DOMAIN SAFETY RULES ===
{evaluation_rules}

=== VERDICT LOGIC ===

- If ANY dimension is FAIL → overall_verdict = FAIL
- If ALL dimensions are PASS → overall_verdict = PASS

=== INPUT ===

Original query: {query}
Response to evaluate: {response}
Analysis findings: {analysis}
Available evidence: {entries_summary}
Attempt number: {attempt_number}
Previous feedback: {previous_feedback}

=== OUTPUT (JSON) ===
{EvaluatorOutput.model_json_schema()}

For any FAIL, provide specific, actionable feedback that can guide a retry.
```

### 12.8 Clarifier Prompt

```
ROLE: You are a clarification agent that requests missing information from users.

TASK: Generate clear, concise questions to fill information gaps.

=== VOCABULARY ===
{vocabulary}

=== INPUT ===

Original query: {original_query}
Gaps to address: {gaps}
What we've already searched: {retrieval_history}
Previous clarifications asked: {previous_clarifications}

=== RULES ===

1. Only ask about gaps that cannot be retrieved from stored data
2. Don't re-ask questions the user has already answered
3. Use domain-appropriate terminology
4. Keep questions concise and specific
5. Offer multiple-choice options when applicable
6. Explain WHY you're asking (context_explanation)

=== QUESTION GUIDELINES ===

Good: "What time did this happen?" (specific, actionable)
Bad: "Can you tell me more?" (vague, unhelpful)

Good: "Were you feeling tired or energized?" (options provided)
Bad: "How were you feeling?" (too open-ended)

=== OUTPUT (JSON) ===
{ClarifierOutput.model_json_schema()}
```

### 12.9 Parser Prompt

```
ROLE: You are a structured extraction agent that converts freeform logs into structured data.

TASK: Extract structured data from the user's input using the provided domain schemas.

=== VOCABULARY ===
Use this to normalize terms:
{vocabulary}

Example: If user writes "bp", normalize to "blood pressure" if vocabulary maps it.

=== DOMAIN SCHEMAS ===
Extract data according to these schemas:
{domain_schemas_description}

=== EXTRACTION RULES ===

1. PRESERVE raw input exactly in raw_content field
2. NORMALIZE terms using vocabulary
3. EXTRACT only what is explicitly stated or clearly implied
4. NEVER invent data that isn't in the input
5. Mark uncertain extractions in uncertain_fields
6. Set confidence based on extraction clarity
7. Add extraction_notes for ambiguities or assumptions

=== MULTI-DOMAIN EXTRACTION ===

If multiple domain schemas are provided, extract independently for each.
An input may match multiple domains (e.g., mentions both activity and meal).

=== INPUT ===

Raw input: {raw_input}
Timestamp: {timestamp}
Global context (for inference): {global_context}
Recent entries (for context): {recent_entries}

=== OUTPUT (JSON) ===
{ParserOutput.model_json_schema()}
```

### 12.10 Observer Prompt

```
ROLE: You are a learning agent that updates the user's global context based on new information.

TASK: Determine if anything from this session should be remembered in the global context.

=== TRIGGER ===
{trigger}  # post_query | user_correction | significant_log

=== DOMAIN GUIDANCE ===
What to track for the active domains:
{context_management_guidance}

=== CURRENT GLOBAL CONTEXT ===
{current_global_context}

=== SESSION DATA ===

# If post_query:
Query: {query}
Analysis: {analysis}
Response: {response}

# If user_correction:
Correction: {correction}
What was corrected: {what_was_corrected}

# If significant_log:
New entry: {new_entry}

=== UPDATE CATEGORIES ===

- preference: Explicit user preferences (units, style, etc.)
- pattern: Inferred behavioral patterns (typical schedule, habits)
- fact: Concrete facts (records, current routines, milestones)
- insight: Observed correlations or patterns

=== CONFIDENCE LEVELS ===

- certain: Explicitly stated or directly observed
- likely: Strong inference from multiple data points
- tentative: Possible pattern, needs more evidence

=== RULES ===

1. Only update if there's genuinely new information
2. Don't duplicate existing context entries
3. Update existing entries if new info supersedes old
4. Be conservative with "tentative" insights
5. Preferences from corrections are "certain"

=== OUTPUT (JSON) ===
{ObserverOutput.model_json_schema()}
```

### 12.11 Prompt Template Summary

| Agent | Key Injections | Critical Instructions |
|-------|---------------|----------------------|
| Router | available_domains | Select all relevant domains |
| Planner | expertise, vocabulary, available_domains | Search before asking, proactive domain expansion |
| Retriever | vocabulary | Expand terms, no filtering |
| Analyzer | expertise, available_domains | Verdict MUST be last |
| Synthesizer | vocabulary | Cite evidence, handle partial |
| Evaluator | evaluation_rules | Any FAIL = overall FAIL |
| Clarifier | vocabulary | Only ask non-retrievable |
| Parser | vocabulary, domain_schemas | Never invent data |
| Observer | context_management_guidance | Conservative updates |

---

## 14. Framework Decision: LangGraph

**Decision: Use LangGraph for agent orchestration**

### 14.1 Why LangGraph

The agent system design reveals significant complexity that favors a framework over custom implementation:

| Complexity Factor | Evidence |
|------------------|----------|
| **13 states** | ROUTE → BUILD_CONTEXT → PLAN/PARSE → ... → COMPLETE |
| **4 distinct cycles** | Analyze→Plan, Evaluate→Plan, Expand→Build, Clarify→Wait→Analyze |
| **Human-in-the-loop** | WAIT_USER with async continuation |
| **Conditional edges** | Based on verdicts (SUFFICIENT/INSUFFICIENT, PASS/FAIL) |
| **Parallel execution** | BOTH input type triggers PARSE + PLAN concurrently |
| **State mutation** | SessionState with 20+ fields tracked across transitions |

### 14.2 Comparison Summary

| Criterion | Custom | LangGraph | Winner |
|-----------|--------|-----------|--------|
| State machine with cycles | Manual (error-prone) | Built-in | LangGraph |
| Human-in-the-loop | Manual checkpoint/resume | Built-in `interrupt()` | LangGraph |
| Conditional routing | If/else chains | Declarative edges | LangGraph |
| Parallel execution | asyncio.gather | Built-in fan-out/fan-in | LangGraph |
| State persistence | Build from scratch | Built-in checkpointing | LangGraph |
| Debugging | Custom logging | LangSmith integration | LangGraph |
| Learning curve | Low (pure Python) | Medium (graph concepts) | Custom |
| Dependencies | Zero | langchain ecosystem | Custom |

### 14.3 LangGraph Patterns for Swealog

**Key patterns to use:**

1. **`interrupt()` for WAIT_USER** — No custom pause/resume logic needed
2. **Conditional edges with guards** — Route based on verdict + enforce retry limits
3. **TypedDict with `Annotated` reducers** — Handle 20+ field SessionState efficiently
4. **PostgresSaver for production** — Checkpoint persistence for long-running flows
5. **LiteLLM directly in nodes** — No LangChain LLM wrappers needed

**State definition pattern:**

```python
from typing import Annotated
from operator import add

class SessionState(TypedDict):
    # Accumulating fields
    retrieval_history: Annotated[list[RetrievalAttempt], add]
    retrieved_entries: Annotated[list[Entry], add]

    # Overwrite fields
    current_state: str
    retry_count: int
    verdict: Literal["SUFFICIENT", "INSUFFICIENT", "PENDING"]
```

**Cycle with safety guard:**

```python
def route_after_evaluate(state: SessionState) -> str:
    if state["retry_count"] >= state["max_retries"]:
        return "observe"  # Force exit
    if state["evaluation"]["overall_verdict"] == "PASS":
        return "observe"
    return "plan"  # Retry
```

### 14.4 Strategic Constraints

To mitigate LangGraph's downsides:

| Concern | Mitigation |
|---------|-----------|
| Dependency weight | Use LangGraph core only, avoid langchain extras |
| Framework lock-in | Keep agents as pure functions with clean interfaces |
| LiteLLM vs LangChain | Use LiteLLM directly in nodes (see Section 15) |
| Testing | Test agents independently before graph integration |

### 14.5 Anti-Patterns to Avoid

1. **Direct state mutation** — Return diffs only, let reducers merge
2. **No cycle limits** — Always enforce `max_retries` in routing
3. **Hidden LLM calls** — Each agent should be an explicit node
4. **Starting with all 9 agents** — Build core loop first, add incrementally

---

## 15. LLM Client Abstraction

**Decision: Tiered configuration with provider flexibility**

### 15.1 Design Goals

- Easy switching between local (Ollama) and cloud providers
- Per-agent model tier configuration
- Support for Azure OpenAI, OpenRouter, and other providers
- Automatic fallback on failure
- No code changes required to switch providers

### 15.2 Configuration Structure

```yaml
# config.yaml
llm:
  default_provider: "ollama"
  fallback_provider: "anthropic"  # Used on errors

  providers:
    ollama:
      api_base: "http://localhost:11434"

    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"

    openai:
      api_key: "${OPENAI_API_KEY}"

    azure:
      api_key: "${AZURE_OPENAI_API_KEY}"
      api_base: "https://your-resource.openai.azure.com/"
      api_version: "2024-06-01"

    openrouter:
      api_key: "${OPENROUTER_API_KEY}"
      api_base: "https://openrouter.ai/api/v1"

  tiers:
    low:
      ollama: "qwen2.5:7b"
      anthropic: "claude-3-haiku-20240307"
      openai: "gpt-4o-mini"
      azure: "gpt-4o-mini-deployment"
      openrouter: "anthropic/claude-3-haiku"

    medium:
      ollama: "qwen2.5:14b"
      anthropic: "claude-3-5-haiku-20241022"
      openai: "gpt-4o-mini"
      azure: "gpt-4o-mini-deployment"
      openrouter: "anthropic/claude-3.5-haiku"

    high:
      ollama: "qwen2.5:32b"
      anthropic: "claude-sonnet-4-20250514"
      openai: "gpt-4o"
      azure: "gpt-4o-deployment"
      openrouter: "anthropic/claude-sonnet-4-20250514"

  agents:
    router: { tier: "low" }
    retriever: { tier: "low" }
    parser: { tier: "medium" }
    clarifier: { tier: "medium" }
    planner: { tier: "high" }
    synthesizer: { tier: "medium" }
    evaluator: { tier: "high" }
    analyzer: { tier: "high" }
    observer: { tier: "medium" }

    # Override example:
    # evaluator: { tier: "high", provider: "anthropic" }
```

### 15.3 Client Interface

```python
class LLMClient:
    """Unified LLM client with provider abstraction."""

    def __init__(self, config: LLMConfig):
        self.config = config

    def resolve_model(self, agent: str, force_cloud: bool = False) -> ModelResolution:
        """Resolve provider and model for an agent."""
        agent_config = self.config.agents.get(agent, AgentConfig())

        if agent_config.provider:
            provider = agent_config.provider
        elif force_cloud:
            provider = self.config.fallback_provider
        else:
            provider = self.config.default_provider

        model = self.config.tiers[agent_config.tier][provider]
        return ModelResolution(provider=provider, model=model, ...)

    async def complete(
        self,
        agent: str,
        messages: list[dict],
        **kwargs,
    ) -> str:
        """Complete a chat request via litellm."""
        resolution = self.resolve_model(agent)
        response = await litellm.acompletion(
            model=resolution.litellm_model,
            messages=messages,
            api_base=resolution.api_base,
            api_key=resolution.api_key,
            **kwargs,
        )
        return response.choices[0].message.content

    async def complete_structured(
        self,
        agent: str,
        messages: list[dict],
        response_model: type[BaseModel],
        **kwargs,
    ) -> BaseModel:
        """Complete with Pydantic validation."""
        response = await self.complete(
            agent=agent,
            messages=messages,
            response_format={"type": "json_object"},
            **kwargs,
        )
        return response_model.model_validate_json(response)

    async def complete_with_fallback(
        self,
        agent: str,
        messages: list[dict],
        **kwargs,
    ) -> str:
        """Try default provider, fall back on failure."""
        try:
            return await self.complete(agent, messages, **kwargs)
        except Exception:
            if self.config.fallback_provider:
                return await self.complete(agent, messages, force_cloud=True, **kwargs)
            raise
```

### 15.4 Usage in Agents

```python
class AnalyzerAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def analyze(self, input: AnalyzerInput) -> AnalyzerOutput:
        messages = [
            {"role": "system", "content": ANALYZER_SYSTEM_PROMPT},
            {"role": "user", "content": self._format_input(input)},
        ]
        return await self.llm.complete_structured(
            agent="analyzer",
            messages=messages,
            response_model=AnalyzerOutput,
        )
```

### 15.5 Switching Providers

```yaml
# Development - local only
llm:
  default_provider: "ollama"
  fallback_provider: null

# Production - cloud primary
llm:
  default_provider: "anthropic"
  fallback_provider: "openai"

# Cost-optimized - OpenRouter
llm:
  default_provider: "openrouter"
  fallback_provider: null
```

---

## 16. Integration Design

This section documents Phase 4 decisions on how the agent system integrates with storage, CLI/API, and error handling.

### 16.1 Storage Abstraction (Q21)

**Decision: StorageRepository pattern**

A single `StorageRepository` class handles all storage operations. Agents never access files directly.

```python
class StorageRepository:
    def __init__(self, base_path: Path):
        self.base_path = base_path
```

**Benefits:**
- Single source of truth for file structure
- Easy to change storage layout without touching agents
- Testable (mock the repository)
- Future flexibility (swap filesystem for database)

### 16.2 StorageRepository Interface (Q22)

**Decision: 6 methods — date, glob, grep, save, context read/write**

```python
from pathlib import Path
from datetime import date
from typing import Optional

class StorageRepository:
    def __init__(self, base_path: Path): ...

    # === READ (date-based) ===
    def get_entries_by_date_range(
        self,
        start: date,
        end: date
    ) -> list[Entry]:
        """Fetch all entries between start and end dates."""
        ...

    # === READ (pattern-based / glob) ===
    def get_entries_by_pattern(
        self,
        pattern: str  # e.g., "2026/01/**/*.md"
    ) -> list[Entry]:
        """Fetch entries matching a glob pattern."""
        ...

    # === READ (content search / grep) ===
    def search_entries(
        self,
        keywords: list[str],
        date_range: Optional[DateRange] = None,
        match_all: bool = False  # AND vs OR
    ) -> list[Entry]:
        """Search entries containing keywords."""
        ...

    # === WRITE ===
    def save_entry(
        self,
        entry: Entry,
        correction: ParserOutput | None = None  # If correction mode
    ) -> None:
        """Save or update an entry (upsert semantics).

        For new entries: Creates raw markdown + parsed JSON files.

        For corrections (when correction is provided):
        - Appends correction note to raw markdown (preserves history)
        - Updates parsed JSON with correction_delta
        - Uses correction.target_entry_id to find target

        See Section 5.5 for correction flow details.
        """
        ...

    # === GLOBAL CONTEXT ===
    def get_global_context(self) -> str:
        """Read global context markdown."""
        ...

    def update_global_context(self, content: str) -> None:
        """Update global context markdown."""
        ...
```

**Rationale:**
- `get_entries_by_date_range`: Primary retrieval method
- `get_entries_by_pattern`: Flexible file matching (like glob)
- `search_entries`: Content search (like grep) — low implementation cost, high utility
- `save_entry`: Single write method for new entries
- `get_global_context` / `update_global_context`: Observer agent needs these

### 16.3 CLI/API Design (Q23)

**Decision: 2 API endpoints + CLI with import command**

#### API Endpoints

```
POST /input    {"text": "..."}   # Log or query (Router classifies)
GET  /context                    # Get global context
```

Minimal API surface. No separate `/import` endpoint — batch import is CLI-only.

#### CLI Commands

```bash
swealog "Why was my bench heavy?"   # Single input → POST /input
swealog                              # Interactive REPL
swealog import ./path/to/logs/       # Batch import (loops files → POST /input)
```

#### Batch Import Implementation

```python
def import_command(path: str):
    """CLI-only batch import."""
    for file in Path(path).glob("**/*.md"):
        content = file.read_text()
        api.post("/input", {"text": content})
    print(f"Imported {count} entries")
```

Reuses `/input` endpoint. No special batch logic in the API.

### 16.4 Error Handling (Q24)

**Decision: Retry → Fallback → Degrade cascade**

#### Error Categories

| Category | Examples |
|----------|----------|
| LLM failures | API timeout, rate limit, provider down |
| Malformed response | Invalid JSON, missing required fields |
| Storage failures | File not found, permission denied |
| Agent loops | Infinite Analyze→Plan cycles |

#### A. LLM Failure Cascade

```
1. Simple retry (same provider, up to 3 attempts)
     ↓ still failing
2. Fallback provider (if configured)
     ↓ still failing
3. Graceful degrade (return partial result + error message)
```

#### B. Malformed Response Handling

```
1. Retry with reminder ("respond in valid JSON")
     ↓ still malformed
2. Pydantic partial parsing (extract fields that exist)
     ↓ can't extract anything useful
3. Fail the step (propagate error)
```

#### C. Retry Configuration

```python
class RetryConfig(BaseModel):
    """Separated retry limits for independent tuning."""

    llm_retry: int = 3          # Same-provider retries
    fallback_enabled: bool = True
    parse_retry: int = 2        # Malformed response retries
    loop_max: int = 2           # Evaluate→Plan, Analyze→Plan cycles
```

Same defaults for now, but separating them allows independent tuning later.

#### D. Storage Failure Handling

| Error | Action |
|-------|--------|
| File not found | Return empty list (for reads), create directory (for writes) |
| Permission denied | Fail immediately, surface to user |
| Disk full | Fail immediately, surface to user |

Storage errors are generally non-recoverable — fail fast and inform user.

---

## 17. Appendix: Reference Material

### A. Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Architecture | `_bmad-output/planning-artifacts/architecture.md` | Storage, stack decisions |
| Original Draft | `_bmad-output/architecture-draft.md` | Initial 10-agent design |
| Research | `_bmad-output/planning-artifacts/research/technical-swealog-foundational-research-2026-01-02.md` | Memory, agents, evaluation research |
| Project Context | `_bmad-output/swealog-project-context-v2.md` | Vision, philosophy |

### B. Research Findings Summary

**From Memory Architecture research:**
- Tiered memory (hot/warm/cold) recommended
- Simple filesystem approaches can be effective
- Graph-based memory adds capability but complexity

**From Multi-Agent research:**
- Centralized orchestration recommended for v1
- Communication overhead is real concern
- Clear agent boundaries reduce conflicts

**From Evaluation research:**
- LLM-as-judge viable with proper prompting
- Binary evaluations more reliable than scales
- Multiple evaluators improve reliability

### C. Example Scenarios to Design For

1. **Simple query:** "Show me last week's workouts"
2. **Insight query:** "Why did my bench feel heavy?" (the example we analyzed)
3. **Recommendation query:** "What should I do today?"
4. **Multi-part query:** "Why was I tired last week and what should I change?"
5. **Correction:** "Actually that was 185 not 85 pounds"
6. **No data:** "How's my swimming progress?" (user never logged swimming)

---

*Document created: 2026-01-02*
*Last updated: 2026-01-04*
*Status: Complete — Ready for Implementation*
