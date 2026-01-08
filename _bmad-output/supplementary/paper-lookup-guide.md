# Swealog Research — Paper Lookup Guide

This document helps agents find relevant papers for the **Swealog** project.

---

## Project Context

### What is Swealog?

**Swealog** (쇠록 / "Iron Log" / "Sweat Log") is an open-source framework for building context-aware AI agents from unstructured user history.

### Core Philosophy

| Principle | Meaning |
|-----------|---------|
| **"Organization is output, not input"** | Users write messy notes → Agents structure and extract insights |
| **Value from accumulated mass** | No single entry matters; the pile of history matters |
| **Friction is the enemy** | Only requirement: "write something down" |

### The Problem (Origin Story)

**Generic AI fails without personal context.**

Example: ChatGPT recommended 20kg devil press (CrossFit exercise) to someone who does bodybuilding-style training. The recommendation was wrong because the AI didn't know the user's workout history and style.

**Insight:** An agent that accumulates and understands personal history would give contextually appropriate advice.

### Why These Papers?

We're researching how to build Swealog — specifically:

1. **Memory architecture** — How to manage user history beyond context limits
2. **Multi-agent orchestration** — How to coordinate Input, Analysis, and Synthesize agents
3. **Unstructured parsing** — How to turn messy user input into structured records
4. **Evaluation** — How to measure if agent insights are actually useful
5. **Domain validation** — Evidence that personalized AI is needed (fitness as first domain)

### Draft Architecture

```
User Input (messy text)
        ↓
┌─────────────────┐
│ Orchestrator    │ ← Routes requests
└────────┬────────┘
         ↓
┌────────┴────────┬─────────────────┐
↓                 ↓                 ↓
Input Agent    Analysis Agent   Synthesize Agent
(parse→JSON)   (find patterns)  (generate insights)
         ↓         ↓                 ↓
         └─────────┴─────────────────┘
                   ↓
         Storage (raw + structured + user context)
```

---

## How to Use This Guide

When asked a question about Swealog:
1. Identify the topic (memory? parsing? evaluation?)
2. Look up relevant paper numbers below
3. Read those papers from `papers-md/` directory
4. Synthesize insights specific to Swealog's needs

---

## By Topic

### Memory & Context Management

| Question | Papers | Notes |
|----------|--------|-------|
| How to manage context beyond LLM limits? | **01**, 13, 14 | 01=MemGPT (foundational), 13=Mem0 (production), 14=A-Mem (self-organizing) |
| Where should important info go in context? | **02**, 12 | 02=Lost in Middle (problem), 12=Found in Middle (solutions) |
| How to extend context window effectively? | 11, 17, 18 | 11=survey, 17=hierarchical transformer, 18=multi-grained injection |
| How to handle infinite/very long context? | 24, 15 | 24=episodic memory, 15=cognitive memory models |
| How to summarize long documents? | **09**, 10, 22 | 09=BOOOOKSCORE, 10=recursive, 22=CoT hierarchical |

### Multi-Agent Systems

| Question | Papers | Notes |
|----------|--------|-------|
| How do multi-agent LLM systems communicate? | **03** | Comprehensive survey on collaboration mechanisms |
| What orchestration patterns exist? | **27**, 03 | 27=centralized planning/decentralized execution |
| How to coordinate agents effectively? | 03, 25, 26 | 25-26=agent surveys with taxonomies |

### Structured Data Extraction

| Question | Papers | Notes |
|----------|--------|-------|
| How to parse unstructured text to JSON? | **04**, 05, 06 | 04=Nature (fine-tuning), 05=prompt patterns, 06=ML approach |
| What prompt patterns work for extraction? | **05** | PLoP 2024 — practical patterns |
| How to handle nested/complex structures? | 05, 04 | Both address complex extraction |

### RAG & Retrieval

| Question | Papers | Notes |
|----------|--------|-------|
| Overview of RAG approaches? | **23** | Comprehensive RAG survey |
| Memory-augmented retrieval? | **19**, 20 | 19=MemoRAG, 20=HippoRAG (brain-inspired) |
| How to retrieve from long-term memory? | 01, 13, 14, 19, 20 | Various memory architectures |

### Evaluation & Testing

| Question | Papers | Notes |
|----------|--------|-------|
| How to use LLM-as-judge? | **07**, 08 | 07=comprehensive survey, 08=reliability focus |
| What biases exist in LLM judges? | 07, 08 | Position bias, verbosity bias, etc. |
| How to evaluate agent quality? | 07, 08, 25 | 25 includes agent evaluation |

### Fitness & Personal AI

| Question | Papers | Notes |
|----------|--------|-------|
| Does GPT-4 fail at personalized fitness? | **16** | Confirms lack of precision for individual needs |
| How to personalize activity recommendations? | **21** | Deep learning + ontology approach |
| PKM to AI companion evolution? | **28** | Vision of personal AI systems |

---

## By Paper Number

| # | Title | Primary Topics |
|---|-------|----------------|
| 01 | MemGPT | Virtual context, hierarchical memory, OS-inspired LLM |
| 02 | Lost in the Middle | Context position bias, U-shaped attention |
| 03 | Multi-Agent Collaboration Survey | Agent communication, coordination paradigms |
| 04 | Structured Extraction (Nature) | Unstructured→JSON, fine-tuning for extraction |
| 05 | Prompt Patterns | Practical patterns for structured extraction |
| 06 | Learning Structured Entities | ML approach to entity extraction |
| 07 | LLMs-as-Judges Survey | LLM evaluation methodology, biases |
| 08 | LLM-as-a-Judge Survey | Reliable judge systems, consistency |
| 09 | BOOOOKSCORE | Book-length summarization, hierarchical vs incremental |
| 10 | Recursive Summarization | Long-term dialogue memory |
| 11 | Beyond the Limits | Context extension techniques survey |
| 12 | Found in the Middle | Solutions to position bias (Ms-PoE) |
| 13 | Mem0 | Production-ready agent memory |
| 14 | A-Mem | Self-organizing agentic memory |
| 15 | Cognitive Memory | Cognitive memory models for LLMs |
| 16 | GPT-4 Exercise Prescription | Fitness AI limitations, personalization gap |
| 17 | Hierarchical Memory Transformer | Multi-level context representations |
| 18 | Two Better Than One | Multi-grained self-injection for context |
| 19 | MemoRAG | Memory-inspired retrieval augmentation |
| 20 | HippoRAG | Neurobiologically-inspired LLM memory |
| 21 | Personalized Activity Coaching | DL + ontology for activity recommendations |
| 22 | CoTHSSum | Chain-of-thought hierarchical summarization |
| 23 | RAG Survey | Comprehensive RAG overview |
| 24 | Human-Inspired Episodic Memory | Episodic memory for infinite context |
| 25 | Agents in SE Survey | Agents in software engineering |
| 26 | LM Agents Comprehensive | LLM agent taxonomy |
| 27 | Multi-Agent SE (ACM) | Orchestration patterns for SE agents |
| 28 | PKM to AI Companion | Personal knowledge management evolution |

---

## Quick Lookup by Keyword

| Keyword | Papers |
|---------|--------|
| memory | 01, 13, 14, 15, 17, 19, 20, 24 |
| context | 01, 02, 11, 12, 17, 18, 24 |
| agent | 03, 25, 26, 27 |
| multi-agent | 03, 27 |
| orchestration | 03, 27 |
| parsing | 04, 05, 06 |
| extraction | 04, 05, 06 |
| structured | 04, 05, 06 |
| evaluation | 07, 08 |
| judge | 07, 08 |
| summarization | 09, 10, 22 |
| RAG | 19, 20, 23 |
| retrieval | 19, 20, 23 |
| fitness | 16, 21 |
| personalization | 16, 21, 28 |
| long-context | 02, 09, 11, 12, 17, 18, 24 |

---

## Reading Paths

### For Architecture Design
1. **01** (MemGPT) → 13 (Mem0) → 14 (A-Mem) → 03 (Multi-Agent Survey)

### For Context Strategy
1. **02** (Lost in Middle) → 12 (Found in Middle) → 11 (Beyond Limits)

### For Input Parsing
1. **04** (Nature extraction) → 05 (Prompt patterns) → 06 (ML approach)

### For Evaluation Design
1. **07** (LLM-as-Judges) → 08 (Reliability) → 16 (Fitness validation)

### For Academic Paper Writing
1. **28** (PKM vision) → 01 (MemGPT) → 16 (Problem validation) → 03 (Multi-agent)

---

## File Locations

- **PDFs:** `papers/[number]-[name].pdf`
- **Markdown:** `papers-md/[number]-[name].md`

Example: Paper 01 = `papers/01-memgpt-towards-llms-as-operating-systems.pdf`
