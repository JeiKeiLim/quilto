# Swealog — Research Paper Recommendations

**Created:** 2025-01-02
**Purpose:** Curated research papers for Swealog project development
**Status:** Active Research Phase
**Total Papers:** 28 PDFs (~58 MB) in `papers/` subdirectory

---

## TIER 1: CRITICAL PAPERS (Read These First)

### 1. Memory Architecture & Long-Term Context

#### MemGPT: Towards LLMs as Operating Systems
- **File:** `01-memgpt-towards-llms-as-operating-systems.pdf`
- **Authors:** Charles Packer et al.
- **Published:** October 2023 (updated February 2024)
- **Link:** https://arxiv.org/abs/2310.08560
- **Why essential:** Foundational paper for Swealog architecture. Solves managing personal history beyond context limits using hierarchical memory (main context + external storage). The dual-tier memory design directly maps to "raw logs + global user context" approach.
- **Key insight:** Virtual context management inspired by OS memory hierarchies

#### Lost in the Middle: How Language Models Use Long Contexts
- **File:** `02-lost-in-the-middle.pdf`
- **Authors:** Nelson F. Liu et al.
- **Published:** TACL 2024
- **Link:** https://arxiv.org/abs/2307.03172
- **Why essential:** Before implementing context strategy, understand the U-shaped performance curve. Information in the middle of context is poorly utilized. Impacts how to structure workout history retrieval.
- **Key insight:** Place important info at beginning/end of context, not middle

---

### 2. Multi-Agent Orchestration

#### Multi-Agent Collaboration Mechanisms: A Survey of LLMs
- **File:** `03-multi-agent-collaboration-survey.pdf`
- **Published:** January 2025
- **Link:** https://arxiv.org/html/2501.06322v1
- **Why essential:** Swealog has Orchestrator, Input, Analysis, Synthesize agents. This 35-page survey covers communication paradigms (memory, report, relay, debate) and coordination models.

#### LLM-Based Multi-Agent Systems for Software Engineering
- **File:** `27-multi-agent-systems-software-engineering-acm.pdf`
- **Published:** ACM TOSEM 2024
- **Link:** https://dl.acm.org/doi/10.1145/3712003
- **Why essential:** Covers orchestration patterns including "Centralized Planning, Decentralized Execution" - directly relevant to Orchestrator→Agent flow.

#### Anthropic's Multi-Agent Research System
- **File:** *(Technical blog - no PDF)*
- **Type:** Technical Blog
- **Link:** https://www.anthropic.com/engineering/multi-agent-research-system
- **Why essential:** Practical implementation of orchestrator-worker pattern. Shows how to decompose queries into subtasks for subagents.

---

### 3. Structured Data Extraction from Unstructured Text

#### Structured Information Extraction from Scientific Text with LLMs
- **File:** `04-structured-extraction-nature.pdf`
- **Published:** Nature Communications, February 2024
- **Link:** https://www.nature.com/articles/s41467-024-45563-x
- **Why essential:** Demonstrates fine-tuning LLMs for structured extraction with JSON outputs. Their approach to "messy text → structured records" is exactly the parsing problem.

#### Prompt Patterns for Structured Data Extraction from Unstructured Text
- **File:** `05-prompt-patterns-structured-extraction.pdf`
- **Published:** PLoP 2024
- **Why essential:** Practical prompt engineering patterns for Input Agent. Covers handling nested data and complex extraction workflows.

#### Learning to Extract Structured Entities Using Language Models
- **File:** `06-learning-structured-entities.pdf`
- **Published:** February 2024
- **Link:** https://arxiv.org/abs/2402.04437
- **Why essential:** Machine learning approach to structured entity extraction.

---

### 4. LLM-as-Judge Evaluation

#### LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluation Methods
- **File:** `07-llms-as-judges-survey.pdf`
- **Published:** December 2024
- **Link:** https://arxiv.org/abs/2412.05579
- **GitHub:** https://github.com/CSHaitao/Awesome-LLMs-as-Judges
- **Why essential:** Testing strategy mentions "LLM-as-judge" for evaluating insight quality. Covers methodology, biases (position, verbosity), and reliability measures.

#### A Survey on LLM-as-a-Judge
- **File:** `08-llm-as-judge-survey.pdf`
- **Published:** November 2024
- **Link:** https://arxiv.org/abs/2411.15594
- **Website:** https://llm-as-a-judge.github.io/
- **Why essential:** Companion paper focusing on building reliable LLM judge systems - addresses consistency and bias mitigation.

---

## TIER 2: HIGHLY RELEVANT (Read After Tier 1)

### Context Management Strategies

#### BOOOOKSCORE: A Systematic Exploration of Book-Length Summarization
- **File:** `09-booookscore-iclr2024.pdf`
- **Published:** ICLR 2024
- **Why relevant:** Hierarchical vs. incremental summarization for book-length documents. Useful for "daily → weekly → monthly summaries" approach.

#### Recursively Summarizing Enables Long-Term Dialogue Memory in LLMs
- **File:** `10-recursive-summarization-dialogue.pdf`
- **Link:** https://arxiv.org/abs/2308.15022
- **Why relevant:** Recursive summarization to maintain long-term memory in conversations. Relevant to Observation agent's "silent learning" pattern.

#### Beyond the Limits: A Survey of Techniques to Extend Context Length
- **File:** `11-beyond-the-limits-ijcai2024.pdf`
- **Published:** IJCAI 2024
- **Why relevant:** Covers sliding window, prompt compression, and context segmentation - relevant to context strategy without needing full RAG.

#### Found in the Middle: How Language Models Use Long Contexts Better
- **File:** `12-found-in-the-middle.pdf`
- **Link:** https://arxiv.org/abs/2403.04797
- **Why relevant:** Proposes Ms-PoE solution to "Lost in the Middle" problem.

#### Two Are Better than One: Context Window Extension with Multi-Grained Self-Injection
- **File:** `18-two-better-than-one-context-extension.pdf`
- **Link:** https://arxiv.org/abs/2410.19318
- **Why relevant:** SharedLLM with hierarchical architecture for context extension.

#### CoTHSSum: Structured Long-Document Summarization via CoT and Hierarchical Segmentation
- **File:** `22-cotHSSum-hierarchical-summarization.pdf`
- **Why relevant:** Chain-of-thought hierarchical summarization for long documents.

#### Retrieval-Augmented Generation for Large Language Models: A Survey
- **File:** `23-rag-survey-comprehensive.pdf`
- **Link:** https://arxiv.org/abs/2312.10997
- **Why relevant:** Comprehensive RAG survey - useful even if not doing full RAG, for understanding retrieval patterns.

---

### Personal AI & Knowledge Management

#### From Personal Knowledge Management to the Second Brain to the Personal AI Companion
- **File:** `28-personal-knowledge-management-ai-companion-acm.pdf`
- **Published:** ACM GROUP 2025
- **Link:** https://dl.acm.org/doi/10.1145/3688828.3699647
- **Why relevant:** Directly addresses the vision: evolution from PKM tools to AI companions that understand accumulated context.

#### Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory
- **File:** `13-mem0-production-ready-agents.pdf`
- **Published:** 2025
- **Link:** https://arxiv.org/abs/2504.19413
- **Why relevant:** Production-focused memory system. More practical than MemGPT for actual implementation.

#### A-Mem: Agentic Memory for LLM Agents
- **File:** `14-a-mem-agentic-memory.pdf`
- **Link:** https://arxiv.org/html/2502.12110v11
- **Why relevant:** Self-organizing, dynamic memory architecture for agents.

#### Cognitive Memory in Large Language Models
- **File:** `15-cognitive-memory-llms.pdf`
- **Link:** https://arxiv.org/html/2504.02441v1
- **Why relevant:** Explores cognitive memory models for LLMs.

#### HMT: Hierarchical Memory Transformer for Long Context Language Processing
- **File:** `17-hierarchical-memory-transformer.pdf`
- **Why relevant:** Hierarchical memory structure with multi-level context representations.

#### MemoRAG: Moving Towards Next-Gen RAG Via Memory-Inspired Knowledge Discovery
- **File:** `19-memoRAG-global-memory.pdf`
- **Link:** https://arxiv.org/abs/2409.05591
- **Why relevant:** Memory-enhanced retrieval augmentation.

#### HippoRAG: Neurobiologically Inspired Long-Term Memory for LLMs
- **File:** `20-hippoRAG-neurobiological-memory.pdf`
- **Link:** https://arxiv.org/abs/2405.14831
- **Why relevant:** Brain-inspired long-term memory architecture.

#### Human-Inspired Episodic Memory for Infinite Context LLMs
- **File:** `24-human-inspired-episodic-memory.pdf`
- **Link:** https://arxiv.org/abs/2407.09450
- **Why relevant:** Episodic memory approach for handling infinite context.

---

### Fitness Domain Specific

#### Using AI for Exercise Prescription in Personalised Health Promotion: Critical Evaluation of GPT-4
- **File:** `16-ai-exercise-prescription-gpt4.pdf`
- **Published:** Biology of Sport, March 2024
- **Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC10955739/
- **Why relevant:** Directly validates the problem. Shows GPT-4 lacks precision in addressing individual health conditions. This is the "devil press moment" problem academically confirmed.

#### An Automatic and Personalized Recommendation Modelling in Activity eCoaching
- **File:** `21-personalized-activity-coaching.pdf`
- **Published:** Nature Scientific Reports, 2023
- **Link:** https://www.nature.com/articles/s41598-023-37233-7
- **Why relevant:** Deep learning + ontology for personalized activity recommendations.

#### SmartFit: AI-Powered Personalized Fitness Recommender System
- **File:** *(Not downloaded - ResearchGate)*
- **Published:** April 2024
- **Link:** https://www.researchgate.net/publication/393381244_SMARTFIT_AI-POWERED_PERSONALIZED_FITNESS_RECOMMENDER_SYSTEM
- **Why relevant:** Similar concept - AI-powered personalized workout routines.

#### Virtual Fitness Trainer using Artificial Intelligence
- **File:** *(Not downloaded - ACM)*
- **Published:** ACM IC3-2024
- **Link:** https://dl.acm.org/doi/fullHtml/10.1145/3675888.3676056
- **Why relevant:** AI wellness coach providing personalized fitness experience.

---

## TIER 3: SUPPLEMENTARY (For Academic Paper Potential)

### Literature Review Resources

#### Agents in Software Engineering: Survey, Landscape, and Vision
- **File:** `25-agents-survey-landscape.pdf`
- **Link:** https://arxiv.org/abs/2409.09030
- **Why useful:** Survey of agents in software engineering context.

#### Large Language Model Agents: A Comprehensive Survey
- **File:** `26-lm-agents-comprehensive-survey.pdf`
- **Link:** https://arxiv.org/abs/2411.01538
- **Why useful:** Comprehensive taxonomy of LLM agents: reasoning, tool-augmented, multi-agent, memory-augmented.

#### Agent Memory Paper List
- **File:** *(GitHub repository)*
- **GitHub:** https://github.com/Shichun-Liu/Agent-Memory-Paper-List
- **Why useful:** Curated list from "Memory in the Age of AI Agents: A Survey" - great for related work section.

#### LLM-Agents-Papers Repository
- **File:** *(GitHub repository)*
- **GitHub:** https://github.com/AGI-Edgerunners/LLM-Agents-Papers
- **Why useful:** Comprehensive list of agent papers for literature review.

#### Awesome-LLM-as-a-Judge Repository
- **File:** *(GitHub repository)*
- **GitHub:** https://github.com/llm-as-a-judge/Awesome-LLM-as-a-judge
- **Why useful:** Curated list of LLM-as-Judge papers.

---

### Small/Local Model Performance

#### NuExtract Models (for structured extraction)
- NuExtract-v1.5 (3.8B, Phi-3.5-mini based)
- NuExtract-tiny-v1.5 (494M, Qwen2.5-0.5B based)
- **Why useful:** Worth testing for local parsing requirements.

---

## RECOMMENDED READING ORDER

| Priority | File | Paper | Focus |
|----------|------|-------|-------|
| 1 | `01-memgpt-towards-llms-as-operating-systems.pdf` | MemGPT | Architecture foundation |
| 2 | `02-lost-in-the-middle.pdf` | Lost in the Middle | Context positioning |
| 3 | `03-multi-agent-collaboration-survey.pdf` | Multi-Agent Survey | Agent orchestration |
| 4 | `04-structured-extraction-nature.pdf` | Structured Extraction | Parsing approach |
| 5 | `07-llms-as-judges-survey.pdf` | LLMs-as-Judges | Evaluation methodology |
| 6 | `16-ai-exercise-prescription-gpt4.pdf` | GPT-4 Exercise | Domain validation |
| 7 | `27-multi-agent-systems-software-engineering-acm.pdf` | Multi-Agent SE | Orchestration patterns |
| 8 | `28-personal-knowledge-management-ai-companion-acm.pdf` | PKM to AI Companion | Vision alignment |

---

## DOWNLOADED PAPERS (papers/ subdirectory)

**Total Size:** ~58 MB | **28 papers downloaded**

| # | Filename | Paper Title |
|---|----------|-------------|
| 01 | `01-memgpt-towards-llms-as-operating-systems.pdf` | MemGPT: Towards LLMs as Operating Systems |
| 02 | `02-lost-in-the-middle.pdf` | Lost in the Middle: How Language Models Use Long Contexts |
| 03 | `03-multi-agent-collaboration-survey.pdf` | Multi-Agent Collaboration Mechanisms: A Survey of LLMs |
| 04 | `04-structured-extraction-nature.pdf` | Structured Information Extraction from Scientific Text with LLMs (Nature) |
| 05 | `05-prompt-patterns-structured-extraction.pdf` | Prompt Patterns for Structured Data Extraction from Unstructured Text |
| 06 | `06-learning-structured-entities.pdf` | Learning to Extract Structured Entities Using Language Models |
| 07 | `07-llms-as-judges-survey.pdf` | LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluation Methods |
| 08 | `08-llm-as-judge-survey.pdf` | A Survey on LLM-as-a-Judge |
| 09 | `09-booookscore-iclr2024.pdf` | BOOOOKSCORE: A Systematic Exploration of Book-Length Summarization (ICLR 2024) |
| 10 | `10-recursive-summarization-dialogue.pdf` | Recursively Summarizing Enables Long-Term Dialogue Memory in LLMs |
| 11 | `11-beyond-the-limits-ijcai2024.pdf` | Beyond the Limits: Survey of Context Extension Techniques (IJCAI 2024) |
| 12 | `12-found-in-the-middle.pdf` | Found in the Middle: How Language Models Use Long Contexts Better via Ms-PoE |
| 13 | `13-mem0-production-ready-agents.pdf` | Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory |
| 14 | `14-a-mem-agentic-memory.pdf` | A-Mem: Agentic Memory for LLM Agents |
| 15 | `15-cognitive-memory-llms.pdf` | Cognitive Memory in Large Language Models |
| 16 | `16-ai-exercise-prescription-gpt4.pdf` | Using AI for Exercise Prescription in Personalised Health Promotion: Critical Evaluation of GPT-4 |
| 17 | `17-hierarchical-memory-transformer.pdf` | HMT: Hierarchical Memory Transformer for Long Context Language Processing |
| 18 | `18-two-better-than-one-context-extension.pdf` | Two Are Better than One: Context Window Extension with Multi-Grained Self-Injection |
| 19 | `19-memoRAG-global-memory.pdf` | MemoRAG: Moving Towards Next-Gen RAG Via Memory-Inspired Knowledge Discovery |
| 20 | `20-hippoRAG-neurobiological-memory.pdf` | HippoRAG: Neurobiologically Inspired Long-Term Memory for LLMs |
| 21 | `21-personalized-activity-coaching.pdf` | An Automatic and Personalized Recommendation Modelling in Activity eCoaching |
| 22 | `22-cotHSSum-hierarchical-summarization.pdf` | CoTHSSum: Structured Long-Document Summarization via CoT and Hierarchical Segmentation |
| 23 | `23-rag-survey-comprehensive.pdf` | Retrieval-Augmented Generation for Large Language Models: A Survey |
| 24 | `24-human-inspired-episodic-memory.pdf` | Human-Inspired Episodic Memory for Infinite Context LLMs |
| 25 | `25-agents-survey-landscape.pdf` | Agents in Software Engineering: Survey, Landscape, and Vision |
| 26 | `26-lm-agents-comprehensive-survey.pdf` | Large Language Model Agents: A Comprehensive Survey |
| 27 | `27-multi-agent-systems-software-engineering-acm.pdf` | LLM-Based Multi-Agent Systems for Software Engineering (ACM TOSEM) |
| 28 | `28-personal-knowledge-management-ai-companion-acm.pdf` | From Personal Knowledge Management to the Second Brain to the Personal AI Companion (ACM GROUP) |

---
