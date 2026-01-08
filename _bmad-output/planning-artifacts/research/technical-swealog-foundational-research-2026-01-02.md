---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - '_bmad-output/swealog-project-context-v2.md'
  - '_bmad-output/architecture-draft.md'
  - '_bmad-output/research-questions.md'
  - '_bmad-output/testing-strategy-draft.md'
  - '_bmad-output/academic-framing-draft.md'
  - '_bmad-output/supplementary/paper-recommendations.md'
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Swealog Foundational Research'
research_goals: 'Broad foundational research to inform architecture decisions for context-aware AI agent framework'
user_name: 'Jongkuk Lim'
date: '2026-01-02'
web_research_enabled: true
source_verification: true
---

# Swealog Foundational Research Report

**Date:** 2026-01-02
**Author:** Jongkuk Lim
**Research Type:** Technical (Foundational)
**Purpose:** Inform architecture decisions - NOT validate a fixed design

---

## Executive Summary

*[To be completed after all research streams]*

---

## Table of Contents

1. [Research Overview & Methodology](#research-overview--methodology)
2. [Stream 1: Memory Architecture & Long-Term Context](#stream-1-memory-architecture--long-term-context)
3. [Stream 2: Multi-Agent System Design Patterns](#stream-2-multi-agent-system-design-patterns)
4. [Stream 3: Unstructured Text Parsing Approaches](#stream-3-unstructured-text-parsing-approaches)
5. [Stream 4: Context Positioning & Retrieval Strategies](#stream-4-context-positioning--retrieval-strategies)
6. [Stream 5: LLM-as-Judge Evaluation Methodology](#stream-5-llm-as-judge-evaluation-methodology)
7. [Stream 6: Local/Small LLM Capabilities](#stream-6-localsmall-llm-capabilities)
8. [Stream 7: Storage Architecture Options](#stream-7-storage-architecture-options)
9. [Stream 8: Fitness Domain Validation](#stream-8-fitness-domain-validation)
10. [Synthesis: Architecture Implications](#synthesis-architecture-implications)
11. [Open Questions for Architecture Phase](#open-questions-for-architecture-phase)
12. [Sources & References](#sources--references)

---

## Research Overview & Methodology

### Research Context

Swealog aims to be a framework for building context-aware AI agents from unstructured user history. The core philosophy is **"Organization is output, not input"** - users write messy notes, agents handle structuring and insight extraction.

### Why This Research

Before committing to an architecture, we need to understand:
- What approaches exist for each technical challenge
- What tradeoffs each approach carries
- What recent developments might change our thinking
- What's actually achievable with current technology (especially local LLMs)

### Research Methodology

1. **Literature Synthesis**: 28 papers already collected, organized by topic
2. **Web Research**: Current developments, implementations, benchmarks (2024-2026)
3. **Cross-Reference**: Multiple sources for critical claims
4. **Swealog Lens**: Every finding evaluated for Swealog implications

### Key Questions to Answer

| Stream | Core Question |
|--------|--------------|
| Memory Architecture | How do we manage months/years of user history within LLM context limits? |
| Multi-Agent Design | How should agents communicate and coordinate? |
| Text Parsing | How do we reliably convert messy input to structured data? |
| Context Positioning | Where should information go in context for best utilization? |
| Evaluation | How do we measure if agent outputs are actually good? |
| Local LLMs | What's achievable without cloud API dependency? |
| Storage | What storage format best serves our needs? |
| Domain Validation | Is there evidence that personalized fitness AI is needed/valuable? |

---

## Stream 1: Memory Architecture & Long-Term Context

### 1.1 The Problem Space

Unlike humans, who dynamically integrate new information and revise outdated beliefs, LLMs effectively "reset" once information falls outside their context window. Even as models push context boundaries (GPT-4: 128K tokens, Claude 3.7 Sonnet: 200K tokens, Gemini: 10M+ tokens), these improvements merely delay rather than solve the fundamental limitation.

**For Swealog's use case**: A user's fitness history spanning months or years (workout logs, subjective notes, performance trends) can easily exceed any context window. We need a strategy that:
- Preserves longitudinal patterns over extended timeframes
- Enables efficient retrieval of relevant history for current context
- Supports incremental updates without expensive reprocessing

### 1.2 Approach Survey

Current approaches fall into several categories:

| Approach | Mechanism | Strengths | Weaknesses |
|----------|-----------|-----------|------------|
| Extended Context Windows | Larger transformer attention | Simple, no external systems | Still finite, expensive, doesn't solve integration |
| RAG | Retrieve relevant passages | Scalable, external knowledge | Encodes passages in isolation |
| Virtual Context Management | OS-like memory tiers | Unlimited capacity, active management | Complex, requires agent to manage |
| Graph-Based Memory | Knowledge graphs + retrieval | Captures relationships, multi-hop reasoning | Higher complexity, extraction overhead |
| Hierarchical Summarization | Progressive condensation | Reduces token cost | Loses detail, irreversible |

### 1.3 MemGPT: Virtual Context Management

**Paper**: "MemGPT: Towards LLMs as Operating Systems" (Packer et al., 2023) - now evolved into Letta framework.

**Core Concept**: Treat the LLM like an operating system with hierarchical memory tiers, providing the illusion of extended virtual memory via paging between physical memory and disk.

**Architecture**:
- **Core Memory**: Immediate context (always in context window)
- **Conversational Memory**: Recent interactions (swapped in/out as needed)
- **Archival Memory**: Long-term storage (external, retrieved on demand)

**Key Innovation**: The agent actively manages what remains in its immediate context versus what gets stored externally. This requires the LLM to have "memory management functions" it can call.

**Recent Status (2024-2025)**: MemGPT is now part of Letta, an open-source agent framework. In benchmarks on the LOCOMO dataset, a simple filesystem-based Letta agent achieved **74.0% accuracy** with GPT-4o mini.

### 1.4 Mem0: Production-Ready Memory

**Paper**: "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory" (April 2025)

**Architecture**: A two-phase memory pipeline:
1. **Extraction Phase**: Ingests latest exchange + rolling summary + recent messages, uses LLM to extract candidate memories
2. **Consolidation**: Merges, updates, or creates new memory entries
3. **Retrieval**: Selective retrieval based on current query context

**Mem0g Variant**: Enhanced version using graph-based memory representations:
- Entity Extractor identifies entities as nodes
- Relations Generator infers labeled edges
- Enables complex relational reasoning across time

**Benchmark Results (LOCOMO)**:
- Mem0: 66.9% accuracy, 1.4s latency
- **26% relative improvement** over OpenAI Memory on LLM-as-Judge metric
- **91% reduction in p95 latency** (1.44s vs 17.12s for full-context)
- **90% reduction in token consumption** (~1.8K vs 26K tokens)

**Note**: Letta contested these results, achieving 74.0% with simpler approach.

### 1.5 RAG-Based Approaches

**Comprehensive Survey**: "Retrieval-Augmented Generation for Large Language Models: A Survey" categorizes RAG into three paradigms:

**Naive RAG**: Index → Retrieve → Generate
- Chunks encoded in isolation
- Struggles with multi-hop reasoning

**Advanced RAG**: Adds pre/post-retrieval optimization
- Pre-retrieval: Query rewriting, expansion
- Post-retrieval: Re-ranking, context compression

**Modular RAG**: Flexible component composition
- Search module for various data sources
- Memory module for iterative self-enhancement
- Routing for optimal query pathways

**HippoRAG** (NeurIPS 2024): Neurobiologically-inspired approach
- Mimics hippocampal indexing theory
- Uses LLM for OpenIE → KG construction
- Personalized PageRank for single-step multi-hop retrieval
- **20% improvement** over standard RAG on multi-hop QA
- **10-20x cheaper, 6-13x faster** than iterative methods like IRCoT

### 1.6 Hierarchical Summarization

**Approach**: Progressive condensation from detailed logs → weekly summaries → monthly summaries → yearly trends.

**Benefits**:
- Dramatically reduces token requirements
- Enables quick overview of long periods
- Natural for fitness domain (workout details → weekly patterns → training phases)

**Limitations**:
- Irreversible information loss
- May miss important details
- Summarization quality depends on LLM capability

**Relevant Paper**: BOOOOKSCORE (ICLR 2024) evaluated summarization coherence - useful for validating summary quality.

### 1.7 Hybrid Approaches

**Emerging Best Practice**: Combine multiple strategies:

1. **Short-term**: Full conversation history in context
2. **Medium-term**: RAG retrieval of recent relevant entries
3. **Long-term**: Hierarchical summaries + graph-based relational memory

**A-MEM (Agentic Memory)**: Proposes agents that actively decide what to remember vs forget, similar to human memory consolidation.

### 1.8 Current State of the Art (2024-2026)

**Key Findings**:
- No single approach dominates; hybrid strategies emerging
- Graph-based approaches (Mem0g, HippoRAG) excel at relational reasoning
- Simple filesystem approaches can be surprisingly effective (Letta benchmark)
- Trade-off between complexity and maintainability is real

**Benchmark Controversies**: Significant disagreement on methodology - Mem0 and Letta report conflicting results on same dataset.

### 1.9 Swealog Implications

**Recommended Architecture Direction**:
1. **Tiered Memory System** (inspired by MemGPT/Letta):
   - Hot: Current session context
   - Warm: Recent days/weeks via RAG
   - Cold: Hierarchical summaries for historical patterns

2. **Graph Enhancement** (if complexity justified):
   - Entity extraction from workout logs
   - Relationship tracking (exercises, muscle groups, progressions)
   - Enables queries like "What exercises improved my squat last time?"

3. **Selective Retrieval**: Don't retrieve everything - use query-driven selection to minimize token cost

**Open Questions for Architecture**:
- What granularity of summarization preserves enough detail?
- Should Swealog use explicit knowledge graph or simpler keyword-based retrieval?
- How to handle memory consolidation (when to merge/prune)?

---

## Stream 2: Multi-Agent System Design Patterns

### 2.1 Communication Paradigms

**Key Insight**: Communication between agents is the cornerstone of coordination. System-level failures often stem from inter-agent interaction complexities rather than individual agent limitations.

**Survey Framework** (from "Beyond Self-Talk: A Communication-Centric Survey of LLM-Based Multi-Agent Systems", Feb 2025):

| Level | Components |
|-------|------------|
| System-Level | Architecture, goals, protocols |
| Internal | Strategies, paradigms, objects, content |

**Communication Challenges**:
1. **State Staleness**: Without fine-grained synchronization, agents may reason on outdated peer contributions
2. **Conflict Resolution**: Parallel proposals often overlap or contradict, requiring arbitration
3. **Information Overload**: Too much inter-agent chatter can overwhelm context windows

### 2.2 Coordination Models

**Three Fundamental Architectures** (from "Multi-Agent Collaboration Mechanisms: A Survey of LLMs", Jan 2025):

**1. Centralized Control**
- Hierarchical coordination with central controller
- Task allocation and decision integration
- Two strategies: explicit controller systems OR differentiation-based (prompts guide meta-agent to assume sub-roles)
- **Pros**: Clear authority, easier debugging
- **Cons**: Single point of failure, bottleneck

**2. Decentralized Cooperation**
- Peer-to-peer agent interactions
- Emergent coordination through local rules
- **Pros**: Scalable, fault-tolerant
- **Cons**: Harder to predict, potential conflicts

**3. Hybrid Architectures**
- Combines centralized oversight with decentralized execution
- **Pros**: Balances control and flexibility
- **Cons**: More complex to implement

**Collaboration Types**:
- **Cooperation**: Agents work toward shared goals
- **Competition**: Agents challenge each other (useful for adversarial testing)
- **Coopetition**: Mix of both (e.g., debate then consensus)

### 2.3 Orchestration Patterns

**Core Components Framework** (Springer survey):
1. **Profile**: Agent identity and capabilities
2. **Perception**: Input processing and understanding
3. **Self-Action**: Individual task execution
4. **Mutual Interaction**: Inter-agent communication
5. **Evolution**: Learning and adaptation over time

**Emerging Protocols**:
- **Google's A2A (Agent-to-Agent)**: Open standard for universal agent interoperability with enterprise-grade auth
- **Anthropic's MCP (Model Context Protocol)**: Standard for connecting AI assistants to data sources

**Pattern Examples**:

| Pattern | Flow | Use Case |
|---------|------|----------|
| Rewrite-Retrieve-Read | Query → Rewrite → Retrieve → Generate | Improved retrieval accuracy |
| Generate-Read | Query → Generate content → Read | When retrieval not available |
| Demonstrate-Search-Predict (DSP) | Few-shot → Search → Predict | Complex reasoning chains |
| ITER-RETGEN | Retrieve → Read → Retrieve → Read (iterative) | Multi-hop questions |

### 2.4 Current Implementations

**Notable Frameworks**:

| Framework | Key Innovation | Status |
|-----------|---------------|--------|
| **MetaGPT** (ICLR 2024) | Meta-programming integrating human workflows | Active development |
| **AutoAgents** (IJCAI 2024) | Dynamic agent generation per task | Research stage |
| **CoALA** (TMLR 2024) | Modular memory + action space | Framework design |
| **LangGraph** | State machine orchestration | Production-ready |
| **CrewAI** | Role-based agent teams | Popular for simple flows |

**Practical Considerations**:
- Simple flows often don't need full multi-agent complexity
- Debugging multi-agent systems is significantly harder
- Token costs multiply with each agent interaction

### 2.5 Swealog Implications

**Recommended Architecture Direction**:

For Swealog's 10-agent draft architecture, consider:

**1. Centralized Orchestration** (recommended for v1):
- Single orchestrator agent manages workflow
- Specialized agents called as needed
- Clearer debugging and control flow
- Easier to reason about failures

**2. Communication Protocol**:
- Structured message passing (JSON schema)
- Clear request/response patterns
- Avoid open-ended agent dialogue (token expensive)

**3. Agent Specialization**:
- **Parser Agent**: Text → structured data
- **Analyst Agent**: Pattern recognition
- **Query Agent**: User interaction
- **Memory Agent**: Storage management

**Anti-Patterns to Avoid**:
- Agents that chat with each other extensively
- Unclear ownership of decisions
- Lack of observability into agent reasoning

**Open Questions for Architecture**:
- Do we need 10 agents or can roles be consolidated?
- How to handle agent failures gracefully?
- Should agents share memory or have isolated contexts?

---

## Stream 3: Unstructured Text Parsing Approaches

### 3.1 The Parsing Challenge

**The Core Problem**: Swealog's philosophy is "organization is output, not input" - users write messy notes, agents handle structuring. This requires reliably converting freeform text like:

```
"Did 5x5 squats at 185, felt heavy today. Back was a bit tight from yesterday's deadlifts. Skipped cardio."
```

Into structured data:

```json
{
  "exercises": [{"name": "squat", "sets": 5, "reps": 5, "weight": 185, "unit": "lbs"}],
  "subjective": {"difficulty": "heavy", "issues": ["back tightness"]},
  "skipped": ["cardio"],
  "context": ["affected by previous day deadlifts"]
}
```

**Challenges**:
- Abbreviations and shorthand ("5x5" = 5 sets of 5 reps)
- Implied context ("felt heavy" = subjective difficulty, not weight)
- Missing units (185 could be lbs or kg)
- Multi-statement inputs with different information types

### 3.2 Prompt Engineering Patterns

**Research Source**: "Prompt Patterns for Structured Data Extraction from Unstructured Text" (PLoP 2024)

**Key Patterns Identified**:

| Pattern | Description | Best For |
|---------|-------------|----------|
| **Semantic Extractor** | Interprets meaning beyond literal text | Understanding context, synonyms |
| **Adaptive Attribute Extractor** | Dynamically infers schema from content | Variable data structures |
| **Pattern Matcher** | Exact template matching (regex-like) | Consistent formats |
| **Constraint Specifier** | Explicit extraction boundaries | Precise requirements |
| **Output Automator** | Deterministic validation layer | Consistency checks |

**Best Practices** (from multiple sources):

1. **Enforce JSON Output**: Use structured output modes (OpenAI JSON mode, Anthropic tool use)
2. **Pydantic Validation**: Define schemas for automatic validation
3. **Few-Shot Examples**: Include 2-3 examples in prompt
4. **Explicit Constraints**: Specify allowed values, formats, ranges

**Example Prompt Structure**:
```
Extract workout data from user input.

Schema: {pydantic_model.schema()}

Examples:
Input: "bench 3x8 at 135"
Output: {"exercises": [{"name": "bench press", "sets": 3, "reps": 8, "weight": 135}]}

Input: "{user_input}"
Output:
```

### 3.3 Fine-Tuning Approaches

**When to Consider Fine-Tuning** (Nature Communications, Feb 2024):
- LLMs fine-tuned on a few hundred examples can extract scientific information and format in user-defined schemas
- Particularly useful when domain-specific terminology is extensive
- Can improve consistency for edge cases

**Trade-offs**:
- Requires training data collection
- Model version lock-in
- May not generalize to novel inputs as well as prompting

**Recommendation**: Start with prompting, consider fine-tuning only if:
- Extraction accuracy consistently below threshold
- Specific domain terms frequently misunderstood
- Sufficient training data available (300+ examples)

### 3.4 Small Model Capabilities

**Current State** (2025):
- Structured output support in Ollama for Mistral, Llama 3.1+, Qwen 2.5
- Tool calling functionality available in local models
- 7B-8B parameter models can handle basic extraction tasks

**Practical Limitations**:
- Complex nested schemas may degrade performance
- Hallucination rates higher than large models
- May require more explicit few-shot examples

**Hallucination Rates** (Vectara LLM Leaderboard, March 2025):
- Best models (Gemini 2.0 Flash): 0.7%
- Top 25 models: 0.7% - 2.6%
- Local models typically higher

### 3.5 Error Handling & Feedback Loops

**Critical Insight**: LLMs will make mistakes. Design for graceful degradation.

**Strategies**:

1. **Schema Validation**: Immediate rejection of malformed output
2. **Confidence Signals**: Ask model to indicate certainty
3. **Human-in-the-Loop**: Flag low-confidence extractions for review
4. **Feedback Incorporation**: Learn from corrections over time

**Error Types to Handle**:
- Missing required fields → prompt for clarification or use defaults
- Invalid values → range check, ask for confirmation
- Conflicting information → flag for user resolution
- Complete parse failure → store raw text, retry later

### 3.6 Swealog Implications

**Recommended Approach**:

1. **Schema-First Design**:
   - Define Pydantic models for all data types (WorkoutLog, Subjective, Goal)
   - Use schema as prompt constraint
   - Validate all outputs programmatically

2. **Tiered Extraction**:
   - **Tier 1 (fast)**: Local model for simple, well-formatted inputs
   - **Tier 2 (accurate)**: Cloud API for complex or ambiguous inputs
   - **Tier 3 (fallback)**: Store raw with metadata, extract later

3. **Progressive Enhancement**:
   - Start with core fields (exercise, sets, reps, weight)
   - Add subjective parsing as second pass
   - Build complexity incrementally

4. **Domain-Specific Vocabulary**:
   - Build exercise name mapping (bench = bench press)
   - Handle common abbreviations
   - Consider user-specific aliases

**Open Questions for Architecture**:
- How much parsing to do synchronously vs async?
- Should parsing agent request clarification from user?
- How to handle parsing confidence thresholds?

---

## Stream 4: Context Positioning & Retrieval Strategies

### 4.1 Lost in the Middle Problem

**Foundational Research**: "Lost in the Middle: How Language Models Use Long Contexts" (Liu et al., TACL 2024)

**Key Finding**: Performance is highest when relevant information occurs at the **beginning or end** of input context, and significantly degrades when models must access information in the **middle** of long contexts.

**The U-Shaped Curve**:
```
Performance
    ↑
High ████                    ████
     ████                    ████
     ████                    ████
Low  ████ ████████████████████ ████
    Beginning    Middle      End
          Position in Context
```

**Why This Matters for Swealog**:
- When providing historical context to an agent, position affects utilization
- Simply dumping all retrieved context may waste the middle portions
- Strategic ordering of information becomes important

### 4.2 Solutions & Mitigations

**1. Position-Agnostic Decompositional Training (ASM QA)**
- Paper: "Never Lost in the Middle" (2023)
- Approach: Train models to search and reflect regardless of position
- Result: **98.5% accuracy** on synthetic retrieval tasks (vs ~60% for base models)
- Model: Ziya-Reader
- **Limitation**: Requires specialized training

**2. Attention Calibration ("Found-in-the-Middle")**
- Collaboration: UW, MIT, Google
- Finding: LLMs have inherent attention bias toward beginning/end tokens
- Solution: Calibration mechanism to reweight attention
- Result: **Up to 15 percentage point improvement** on NaturalQuestions
- **Advantage**: Can be applied to existing models

**3. IN2 Training (FILM-7B)**
- Microsoft + Peking University
- Approach: "INformation-INtensive" second-phase training
- Base Model: Mistral-7B → FILM-7B
- Result: Better retrieval from 32K context, improved summarization
- **Caveat**: Problem not completely solved

**4. Practical Mitigations (No Retraining)**

| Strategy | Implementation | Effectiveness |
|----------|---------------|---------------|
| Important info at edges | Place key context at start and end | High |
| Re-ranking retrieved chunks | Most relevant first and last | Medium-High |
| Context compression | Summarize less-relevant middle sections | Medium |
| Chunking strategy | Smaller, focused chunks | Medium |
| Query reformulation | Multiple retrieval passes | Medium |

### 4.3 Query-Driven Retrieval

**Principle**: Don't retrieve everything - retrieve what's relevant to the current query.

**Strategies**:

**1. Semantic Similarity Search**
- Embed query and documents
- Retrieve top-k by cosine similarity
- **Pros**: Fast, straightforward
- **Cons**: May miss semantically related but differently worded content

**2. Hybrid Search**
- Combine keyword (BM25) + semantic (embedding)
- Weighted combination or reciprocal rank fusion
- **Pros**: Catches both exact matches and semantic relevance
- **Cons**: More complex, requires tuning

**3. Query Expansion**
- Reformulate query before retrieval
- Generate related questions
- **Pros**: Better recall
- **Cons**: Higher token cost

**4. Multi-Step Retrieval**
- Initial broad retrieval → rerank → focused retrieval
- Iterative refinement based on partial results
- **Pros**: Higher precision
- **Cons**: Higher latency, more API calls

### 4.4 Swealog Implications

**Recommended Strategies**:

1. **Position-Aware Context Assembly**:
   - Most recent/relevant data at beginning
   - User profile and preferences at end (always visible)
   - Historical summaries in middle (acceptable to partially miss)

2. **Chunk Size Optimization**:
   - Smaller chunks (200-500 tokens) for better relevance matching
   - Include metadata (date, exercise type) for filtering

3. **Two-Phase Retrieval**:
   - Phase 1: Broad keyword-based filter (fast)
   - Phase 2: Semantic ranking of filtered results

4. **Context Budget Management**:
   - Define maximum context allocation per query type
   - Prioritize recent data over historical
   - Use summaries for historical context

**Open Questions for Architecture**:
- How to segment workout logs for optimal chunk size?
- Should we implement re-ranking or keep retrieval simple for v1?
- How to balance recency vs relevance?

---

## Stream 5: LLM-as-Judge Evaluation Methodology

### 5.1 Why LLM-as-Judge

**The Evaluation Challenge**: For Swealog, measuring "good" output is inherently subjective:
- Is this workout recommendation appropriate for the user's goals?
- Does this insight accurately reflect the user's training patterns?
- Is the coaching advice safe and effective?

**Why Traditional Metrics Fall Short**:
- BLEU/ROUGE measure textual similarity, not quality
- Ground truth is expensive or impossible to obtain at scale
- Human evaluation doesn't scale for iteration

**LLM-as-Judge Advantages**:
- Can evaluate nuanced qualities (helpfulness, accuracy, safety)
- Scales to thousands of evaluations
- Consistent criteria application
- Lower cost than human annotation

### 5.2 Methodology Overview

**Evaluation Types** (from survey literature):

| Type | Mechanism | Best For |
|------|-----------|----------|
| **Pointwise** | Rate single output on criteria | Absolute quality assessment |
| **Pairwise** | Compare two outputs | Relative preference |
| **Listwise** | Rank multiple outputs | Comparative evaluation |
| **Reference-Based** | Compare to ground truth | Factual accuracy |
| **Reference-Free** | Evaluate without reference | Open-ended quality |

**Standard Criteria**:
- **Helpfulness**: Does it address the user's need?
- **Accuracy**: Is the information correct?
- **Relevance**: Is it on-topic?
- **Harmlessness**: Is it safe?
- **Coherence**: Is it well-structured?

### 5.3 Known Biases & Mitigations

**Critical Biases**:

| Bias | Description | Magnitude |
|------|-------------|-----------|
| **Position Bias** | Prefers first or last in comparisons | ~40% inconsistency when swapped |
| **Verbosity Bias** | Prefers longer, more formal responses | ~15% score inflation |
| **Self-Enhancement** | Favors outputs from same/similar model | ~5-7% boost |
| **Scoring Bias** | Sensitive to rubric presentation | Variable |

**Mitigation Strategies**:

**1. Position Bias**
- **Swap Test**: Run evaluation twice with order flipped
- Only trust judgment if consistent across both orderings
- Use positional debiasing in prompts

**2. Verbosity Bias**
- Explicit instruction to ignore length
- Focus rubric on substance not form
- Penalize unnecessary verbosity

**3. Self-Enhancement Bias**
- Use different model as judge than generator
- Multiple judge models with majority vote
- Mix of model families (Claude + GPT + Gemini)

**4. General Best Practices**
- **Binary evaluations** (Pass/Fail) more reliable than numeric scales
- **Chain-of-thought** reasoning improves alignment with humans
- **Few-shot examples** with boundary cases
- **Multiple iterations** with statistical aggregation

### 5.4 Practical Implementation

**Recommended Approach**:

**1. Create Gold Standard Test Set**
- 30-50 examples labeled by humans
- Include edge cases and failure modes
- Use for calibration and prompt tuning

**2. Prompt Structure**:
```
You are evaluating a fitness coaching response.

Criteria:
1. Safety: Does the recommendation avoid injury risk?
2. Personalization: Does it reflect user's history/goals?
3. Actionability: Can the user implement this?

Response to evaluate:
{response}

User context:
{context}

Evaluate each criterion as PASS or FAIL with reasoning.
```

**3. Scoring Guidelines**:
- Prefer binary (Pass/Fail) or 3-point scales
- Avoid 10-point or 100-point scales
- Always require reasoning before score

**4. Human-in-the-Loop**:
- For expert domains: 60-68% agreement with human experts
- Hybrid workflows essential for high-stakes evaluations
- Periodic recalibration against human judgments

### 5.5 Swealog Implications

**Evaluation Framework Design**:

1. **Automated Quality Gates**:
   - Safety check (no dangerous exercise recommendations)
   - Coherence check (structured, complete response)
   - Relevance check (addresses user query)

2. **Layered Evaluation**:
   - **Layer 1**: Deterministic checks (schema validation, constraint checks)
   - **Layer 2**: LLM-as-judge for quality dimensions
   - **Layer 3**: Periodic human review for calibration

3. **Evaluation Dimensions for Swealog**:

| Dimension | Description | Evaluation Method |
|-----------|-------------|------------------|
| **Safety** | No injury risk recommendations | LLM judge + rules |
| **Accuracy** | Correct interpretation of user data | Reference-based |
| **Personalization** | Reflects user history/preferences | LLM judge |
| **Actionability** | User can implement | LLM judge |
| **Coherence** | Well-structured response | LLM judge |

4. **Bias Mitigation for Swealog**:
   - Different model for evaluation than generation
   - Binary Pass/Fail for critical dimensions (safety)
   - Aggregate multiple evaluations for uncertainty

**Open Questions for Architecture**:
- How to balance evaluation cost vs coverage?
- Which dimensions require human review?
- How to handle disagreement between judges?

---

## Stream 6: Local/Small LLM Capabilities

### 6.1 Current Local Model Landscape

**2025 State of Local LLMs**: "The landscape of local language model deployment has dramatically evolved, with Ollama establishing itself as the de facto standard for running LLMs on consumer and enterprise hardware."

**Major Local Inference Tools**:

| Tool | Strengths | Limitations |
|------|-----------|-------------|
| **Ollama** | Simple CLI, model library, OpenAI-compatible API | Single-user focus, max 4 parallel requests |
| **vLLM** | High throughput, production serving | More complex setup |
| **LocalAI** | OpenAI API drop-in replacement | Less mature |
| **LM Studio** | GUI, easy model management | Desktop focus |
| **llama.cpp** | Efficient, portable | Lower-level |

**Popular Models for Local Use**:
- Llama 3.3/3.2 (7B-8B)
- Mistral 7B
- Qwen 2.5 (7B)
- Gemma 2 (9B)
- Phi-4 (14B)
- DeepSeek-R1 (8B)

**Hardware Recommendations**:
- 1-3B models: CPU-only possible, 8GB RAM minimum
- 7-8B models: GPU recommended, 16GB VRAM or 32GB RAM
- "4-bit quantized 7B often performs better than 8-bit 3B"

### 6.2 Benchmarks & Performance

**Speed Benchmarks** (via ollama-benchmark):
- Typical throughput: 20-50 tokens/second on consumer GPU
- CPU-only: 5-15 tokens/second
- Latency varies significantly by model and quantization

**Quality vs Size Trade-offs**:

| Model Size | Good For | Struggles With |
|------------|----------|----------------|
| 1-3B | Simple classification, basic extraction | Complex reasoning, nuance |
| 7-8B | Structured extraction, summarization | Multi-step reasoning |
| 13-14B | Most tasks, good balance | Very complex tasks |
| 30B+ | Production quality | Resource intensive |

**Concurrency Limitations**:
- Ollama designed for single-instance use
- 1-2 concurrent users typically max out the system
- vLLM needed for high-concurrency production

### 6.3 Structured Output Capabilities

**Current Support** (2025):
- Ollama has official structured outputs capability
- Tool calling works with: Mistral, Llama 3.1+, Llama 3.2, Qwen 2.5
- JSON mode available for most models

**Practical Experience**:
- "If you need structured outputs with Ollama, you need to manually write extra Pydantic models or custom parsing logic"
- Smaller models may produce malformed JSON more frequently
- Few-shot examples critical for consistency

**Validation Approach**:
```python
from pydantic import BaseModel

class WorkoutExtraction(BaseModel):
    exercises: list[Exercise]
    notes: str | None

# Use schema in prompt, validate response
response = model.generate(prompt + schema.model_json_schema())
parsed = WorkoutExtraction.model_validate_json(response)
```

### 6.4 Speed vs Quality Tradeoffs

**The Core Trade-off**:

```
Quality ↑
         │        ◆ GPT-4/Claude
         │      ◆ Llama 70B
         │    ◆ Phi-4 (14B)
         │  ◆ Llama 8B
         │ ◆ Qwen 7B
         │◆ Phi-2 (3B)
         └──────────────────→ Speed/Cost ↑
```

**Strategic Considerations**:

| Scenario | Recommended Approach |
|----------|---------------------|
| Real-time parsing | Local 7-8B, fallback to cloud |
| Batch processing | Local, accept higher latency |
| Complex reasoning | Cloud API only |
| Cost-sensitive | Local for volume, cloud for quality |

**Hybrid Strategy**:
1. Route simple tasks to local model
2. Route complex/ambiguous to cloud
3. Use local for drafts, cloud for final

### 6.5 Swealog Implications

**Recommended Local LLM Strategy**:

1. **Tiered Model Deployment**:
   - **Tier 1 (Local Fast)**: Qwen 2.5 7B or Llama 3.3 8B for:
     - Simple workout log parsing
     - Classification tasks
     - Routine queries
   - **Tier 2 (Local Quality)**: Phi-4 14B for:
     - Complex extraction
     - Summarization
   - **Tier 3 (Cloud)**: Claude/GPT-4 for:
     - Analysis and insights
     - Multi-step reasoning
     - Evaluation/judging

2. **Fallback Mechanism**:
   - Attempt local parsing first
   - If validation fails, retry with cloud
   - Log failure patterns for improvement

3. **Quantization Strategy**:
   - Use Q4_K_M quantization for good quality/speed balance
   - Consider Q8 for evaluation tasks where quality critical

4. **Privacy-First Option**:
   - All parsing can be local-only if user prefers
   - Cloud used only for opt-in features

**Open Questions for Architecture**:
- What's the minimum acceptable local model quality?
- How to route between local and cloud efficiently?
- Should users be able to configure local model preference?

---

## Stream 7: Storage Architecture Options

### 7.1 File-Based Storage

**The Markdown/YAML Approach** (from project context):
- Human-readable format
- Git-friendly (version control, diffs)
- Simple to implement
- No database dependencies

**Proposed Structure**:
```
data/
├── raw/
│   └── 2026-01-02.md        # Daily raw input
├── parsed/
│   └── 2026-01-02.json      # Structured extraction
├── summaries/
│   ├── weekly/
│   │   └── 2026-W01.md
│   └── monthly/
│       └── 2026-01.md
└── profile.yaml              # User preferences
```

**Advantages**:
- Transparent: Users can inspect and edit their data
- Portable: Easy to backup, migrate, sync
- Simple: No database management
- LLM-Friendly: Can feed files directly to context

**Disadvantages**:
- Query limitations: No SQL-style queries
- Scale concerns: File system performance with thousands of files
- Concurrency: File locking issues
- Index management: Need separate search index

### 7.2 Database Options

**SQLite**:
- Single file database
- ACID compliant
- Full SQL support
- Excellent for read-heavy workloads
- Built into Python

**Use Cases**:
- Structured workout data
- Search indexes
- Metadata storage
- Query history

**Example Schema**:
```sql
CREATE TABLE workouts (
    id INTEGER PRIMARY KEY,
    date DATE,
    raw_input TEXT,
    parsed_json JSON,
    embedding BLOB,  -- for vector search
    created_at TIMESTAMP
);

CREATE TABLE exercises (
    id INTEGER PRIMARY KEY,
    workout_id INTEGER,
    name TEXT,
    sets INTEGER,
    reps INTEGER,
    weight REAL,
    FOREIGN KEY (workout_id) REFERENCES workouts(id)
);
```

**Vector Database Options**:

| Option | Type | Best For |
|--------|------|----------|
| **SQLite + sqlite-vec** | Embedded | Simple vector search |
| **ChromaDB** | Embedded | Python-native, easy setup |
| **LanceDB** | Embedded | Fast, columnar format |
| **Qdrant** | Server/Embedded | Production-grade |
| **Pinecone** | Cloud | Managed, scalable |

### 7.3 Hybrid Approaches

**Recommended Pattern**: Combine file-based and database storage

```
┌─────────────────────────────────────────────┐
│                  User Data                   │
├─────────────────┬───────────────────────────┤
│   File System   │      SQLite Database      │
├─────────────────┼───────────────────────────┤
│ • Raw input     │ • Structured exercises    │
│ • Summaries     │ • Vector embeddings       │
│ • Exports       │ • Query indexes           │
│ • Human-readable│ • Metadata                │
└─────────────────┴───────────────────────────┘
```

**Sync Strategy**:
- Files are source of truth for raw/summary data
- Database is derived index for fast queries
- Rebuild database from files if needed

**Simon Willison's Approach** (from web research):
- LLM tool logs all prompts/responses to SQLite
- Schema validation with Pydantic
- datasette-extract plugin for structured data extraction to database tables

### 7.4 Swealog Implications

**Recommended Storage Architecture**:

1. **Primary Storage (Files)**:
   - Raw user input: Markdown files by date
   - Summaries: Markdown files by period
   - User profile: YAML file
   - Git-trackable for version history

2. **Index Storage (SQLite)**:
   - Parsed workout data (structured JSON)
   - Vector embeddings for semantic search
   - Exercise taxonomy/mapping
   - Query logs and metadata

3. **Separation of Concerns**:
   - Files = Human interface + LLM context
   - Database = Machine queries + fast retrieval

4. **Data Flow**:
   ```
   User Input → Parse → File (raw)
                     → Database (structured)
                     → Embeddings (vectors)

   Query → Database → Retrieve relevant
                    → Load from files
                    → Assemble context
   ```

**Open Questions for Architecture**:
- Should parsed data live in files or only database?
- How to handle schema migrations?
- Backup and export formats?

---

## Stream 8: Fitness Domain Validation

### 8.1 Evidence of the Problem

**Market Context** (2024-2025):
- Global AI in fitness and wellness market: $9.8 billion (2024) → projected $46 billion (2034)
- Over 50% of people would use AI for personal training
- 1 in 3 US millennials prefer personalized products and services

**The Personalization Gap**:
From GPT-4 fitness study (Paper 16):
- "AI-generated exercise prescriptions lacked precision in addressing individual health conditions and goals"
- "Often prioritizing excessive safety over effectiveness of training"
- "The model's potential to fine-tune recommendations through ongoing interaction was not fully satisfying"

**Key Limitations of Current AI Fitness Tools**:
1. Generic recommendations not tailored to individual history
2. No consideration of accumulated fatigue or recovery
3. Lack of adaptation to real-time biometrics
4. Missing context from previous sessions
5. One-shot interaction vs continuous relationship

### 8.2 Existing Solutions

**Current Landscape**:

| Solution Type | Examples | Strengths | Limitations |
|--------------|----------|-----------|-------------|
| **Wearable Apps** | Fitbit, Garmin, Whoop | Real-time data | Generic recommendations |
| **AI Coaches** | FitGPT, workout apps | Conversational | No memory, no personalization |
| **Programming Apps** | TrainerRoad, Juggernaut | Periodization | Rigid templates |
| **Human Coaches** | Personal trainers | True personalization | Expensive, not scalable |

**Paper 21 (Personalized Activity Coaching)**:
- Combines deep learning + ontology for personalized recommendations
- Uses time-series forecasting + classification
- Generates recommendations via semantic rules
- **Key insight**: Hybrid approach (data-driven + rule-based) overcomes limitations of each alone

**Notable Research Finding**:
"Solely data-driven recommendation technology with ML/DL suffers from insufficient data, high computing overhead, lack of interpretability, re-training, personalization, and cold-start problem"

### 8.3 Gaps in Current Approaches

**Identified Gaps**:

1. **Context Memory Gap**:
   - Current AI tools don't remember previous sessions
   - No accumulation of user-specific patterns
   - Each interaction starts fresh

2. **Holistic Understanding Gap**:
   - Sleep, stress, nutrition not integrated
   - No understanding of life context
   - Missing subjective feedback loop

3. **Progression Intelligence Gap**:
   - Static programs vs adaptive progressions
   - No learning from user's response to training
   - Generic periodization

4. **Safety vs Effectiveness Gap**:
   - AI tends toward overly conservative recommendations
   - Lacks ability to push users appropriately
   - Missing personalized risk assessment

5. **Expert Domain Knowledge Gap**:
   - 60-68% agreement between LLM judges and human experts in specialized domains
   - Complex exercise prescription requires nuanced judgment
   - Edge cases need human oversight

### 8.4 Swealog Implications

**Validation of Core Value Proposition**:

The research confirms Swealog's key hypotheses:
1. **Memory matters**: Existing tools lack longitudinal context - this is the core differentiator
2. **Unstructured input is realistic**: Users don't want to fill forms - natural language is preferred
3. **Personalization is valued**: Strong market demand for individualized recommendations
4. **Hybrid approach is necessary**: Pure ML or pure rules insufficient

**Domain-Specific Considerations**:

1. **Safety Requirements**:
   - Exercise recommendations carry injury risk
   - Need conservative fallback behavior
   - Clear escalation for medical conditions

2. **Expert Knowledge Integration**:
   - Build in exercise science principles
   - Consider periodization models
   - Recovery and adaptation patterns

3. **Subjective Data Value**:
   - "Felt heavy", "back tight" = valuable signals
   - Sleep quality, stress affect performance
   - RPE (Rate of Perceived Exertion) matters

4. **Temporal Patterns**:
   - Training history informs current recommendations
   - Progressive overload requires memory
   - Deload weeks based on accumulated fatigue

**Open Questions for Architecture**:
- How to incorporate exercise science constraints?
- What safety checks are non-negotiable?
- How to validate recommendations against best practices?

---

## Synthesis: Architecture Implications

### Key Findings Summary

| Stream | Key Finding | Confidence |
|--------|------------|------------|
| Memory Architecture | Hybrid tiered approach (MemGPT-style) with graph enhancement for relations | High |
| Multi-Agent Design | Start with centralized orchestration, avoid over-engineering | High |
| Text Parsing | Schema-first with Pydantic, tiered local/cloud fallback | High |
| Context Positioning | Position-aware assembly, important at edges | Medium-High |
| LLM-as-Judge | Binary evaluations, multi-model judges, calibration required | Medium |
| Local LLMs | 7-8B models viable for parsing, cloud needed for reasoning | High |
| Storage | Hybrid files (human) + SQLite (machine) | Medium-High |
| Fitness Domain | Strong validation of core value proposition, safety critical | High |

### Architecture Decision Points

Based on research, the following decisions should be made during architecture phase:

**Decision 1: Memory Architecture**
- **Option A**: Simple RAG with summaries (simpler, lower capability)
- **Option B**: Tiered memory à la MemGPT (moderate complexity, proven approach)
- **Option C**: Full graph-based memory (highest capability, highest complexity)
- **Recommendation**: Start with Option B, add graph enhancement later if needed

**Decision 2: Agent Architecture**
- **Option A**: Single agent with multiple capabilities (simplest)
- **Option B**: 3-4 specialized agents with orchestrator (balanced)
- **Option C**: 10-agent architecture as drafted (most complex)
- **Recommendation**: Start with Option B, consolidate roles

**Decision 3: Local vs Cloud**
- **Option A**: Cloud-only (simplest, highest quality, highest cost)
- **Option B**: Local-first with cloud fallback (balanced)
- **Option C**: Local-only (privacy-focused, lower quality)
- **Recommendation**: Option B with user configuration

**Decision 4: Storage**
- **Option A**: Files only (simplest, limited queries)
- **Option B**: SQLite only (structured, less human-readable)
- **Option C**: Hybrid files + SQLite (balanced)
- **Recommendation**: Option C

### Recommended Approaches

**For MVP/v1**:

1. **Memory**: Tiered system with:
   - Session context (hot)
   - Recent weeks via simple RAG (warm)
   - Monthly/yearly summaries (cold)

2. **Agents**: 4 core agents:
   - Orchestrator (routes queries, manages workflow)
   - Parser (text → structured data)
   - Analyst (patterns, insights)
   - Coach (recommendations)

3. **Parsing**:
   - Pydantic schemas for all data types
   - Local Ollama (Qwen 2.5 7B) for basic parsing
   - Cloud fallback for failures

4. **Storage**:
   - Markdown files for raw input and summaries
   - SQLite for structured workout data
   - ChromaDB or sqlite-vec for embeddings

5. **Evaluation**:
   - Binary Pass/Fail for safety checks
   - LLM-as-judge for quality dimensions
   - Human review for calibration set

### Trade-offs to Consider

| Decision | Trade-off |
|----------|-----------|
| Graph memory | Higher capability vs higher complexity |
| More agents | Better specialization vs more coordination overhead |
| Local LLM | Privacy + cost vs quality |
| File storage | Transparency vs query efficiency |
| Strict validation | Data quality vs user friction |

---

## Open Questions for Architecture Phase

### Technical Questions

1. **Memory Granularity**: What level of detail should summaries preserve?
2. **Agent Boundaries**: Which agent owns which decisions?
3. **Failure Modes**: How to handle parsing failures gracefully?
4. **Concurrency**: How to handle simultaneous queries?
5. **Schema Evolution**: How to migrate data as schemas change?

### Domain Questions

6. **Safety Constraints**: What recommendations are prohibited?
7. **Expert Review**: When does human expert review trigger?
8. **Personalization Limits**: How far should AI deviate from general guidelines?

### Research Questions

9. **Benchmarking**: How to measure Swealog's performance objectively?
10. **User Studies**: What evaluation captures user value?

---

## Sources & References

### Papers (from collection)

**Memory Architecture**:
- Paper 01: MemGPT: Towards LLMs as Operating Systems (Packer et al., 2023)
- Paper 13: Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory (2025)
- Paper 14: A-MEM: Agentic Memory
- Paper 20: HippoRAG: Neurobiologically Inspired Long-Term Memory (NeurIPS 2024)
- Paper 23: Retrieval-Augmented Generation for Large Language Models: A Survey

**Context & Retrieval**:
- Paper 02: Lost in the Middle: How Language Models Use Long Contexts (Liu et al., TACL 2024)
- Paper 12: Found in the Middle (Attention Calibration)

**Multi-Agent Systems**:
- Paper 03: Multi-Agent Collaboration Survey

**Structured Extraction**:
- Paper 05: Prompt Patterns for Structured Data Extraction (PLoP 2024)
- Paper 04: Structured Information Extraction (Nature Communications, 2024)

**Evaluation**:
- Paper 07: LLMs as Judges Survey
- Paper 08: LLM-as-Judge Survey
- Paper 09: BOOOOKSCORE (ICLR 2024)

**Fitness Domain**:
- Paper 16: Using AI for Exercise Prescription: GPT-4 Evaluation (Biology of Sport, 2024)
- Paper 21: Personalized Activity Coaching with Deep Learning and Ontology (Scientific Reports, 2023)

### Web Sources

**Memory Systems**:
- [Mem0 AI Memory Benchmark](https://mem0.ai/blog/benchmarked-openai-memory-vs-langmem-vs-memgpt-vs-mem0-for-long-term-memory-here-s-how-they-stacked-up)
- [Letta Filesystem Benchmarking](https://www.letta.com/blog/benchmarking-ai-agent-memory)
- [Mem0 Research](https://mem0.ai/research)

**Multi-Agent Systems**:
- [Communication-Centric Survey (Feb 2025)](https://arxiv.org/html/2502.14321v1)
- [Multi-Agent Collaboration Mechanisms Survey (Jan 2025)](https://arxiv.org/html/2501.06322v1)
- [LLM-Based Multi-Agent Systems ACM Survey](https://dl.acm.org/doi/10.1145/3712003)

**Structured Extraction**:
- [Simon Willison: LLM Schemas (Feb 2025)](https://simonwillison.net/2025/Feb/28/llm-schemas/)
- [LlamaIndex Structured Extraction](https://docs.llamaindex.ai/en/stable/use_cases/extraction/)

**Context Positioning**:
- [Lost in the Middle (Stanford)](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf)
- [Found in the Middle (MarkTechPost)](https://www.marktechpost.com/2024/06/27/solving-the-lost-in-the-middle-problem-in-large-language-models-a-breakthrough-in-attention-calibration/)

**LLM-as-Judge**:
- [Cameron Wolfe: LLM as a Judge](https://cameronrwolfe.substack.com/p/llm-as-a-judge)
- [LLM-as-Judge Best Practices](https://mer.vin/2025/11/llm-as-a-judge-best-practices-for-consistent-evaluation/)
- [Arize LLM as a Judge Primer](https://arize.com/llm-as-a-judge/)

**Local LLMs**:
- [Best Ollama Models 2025](https://collabnix.com/best-ollama-models-in-2025-complete-performance-comparison/)
- [Ollama Benchmark GitHub](https://github.com/aidatatools/ollama-benchmark)
- [Ollama vs vLLM (Red Hat)](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)

**Fitness Domain**:
- [AI in Fitness 2025 (Orangesoft)](https://orangesoft.co/blog/ai-in-fitness-industry)
- [AI Fitness Trends 2025 (3DLook)](https://3dlook.ai/content-hub/ai-in-fitness-industry/)

---

## Executive Summary

This foundational research report synthesizes findings from 28 academic papers and extensive web research across 8 technical streams to inform Swealog's architecture decisions.

**Core Validated Hypothesis**: There is strong evidence that personalized, memory-aware AI fitness coaching fills a significant gap in current solutions. The "organization is output, not input" philosophy aligns with both user preferences and technical feasibility.

**Key Technical Recommendations**:

1. **Memory**: Implement tiered memory architecture (hot/warm/cold) inspired by MemGPT, starting without graph complexity but designing for future enhancement.

2. **Agents**: Begin with 4 consolidated agents (Orchestrator, Parser, Analyst, Coach) rather than 10, using centralized coordination.

3. **Parsing**: Use Pydantic schema-first design with local LLM (7-8B) for basic extraction and cloud fallback for complex cases.

4. **Storage**: Hybrid approach with Markdown files (human-readable, git-friendly) and SQLite (structured queries, vector search).

5. **Evaluation**: Implement LLM-as-judge with binary safety checks, multi-model evaluation, and periodic human calibration.

6. **Local LLMs**: Ollama with Qwen 2.5 7B or Llama 3.3 8B provides adequate capability for parsing tasks with appropriate fallback strategies.

**Research Confidence**: High confidence in memory architecture, parsing approach, and domain validation. Medium confidence in optimal agent count and evaluation methodology - these should be validated during implementation.

**Next Step**: Proceed to architecture phase with these research findings as input, making explicit decisions on the identified decision points.

---

*Research conducted: 2026-01-02*
*Status: Complete*
