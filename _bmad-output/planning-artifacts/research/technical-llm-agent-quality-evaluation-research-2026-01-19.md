---
stepsCompleted: [1, 2, 3, 4, 5]
status: complete
inputDocuments:
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/agent-system-design.md'
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'LLM Agent Quality Evaluation'
research_goals: 'Understand E2E evaluation frameworks, LLM-as-judge patterns, baseline generation strategies, and multi-agent benchmarking approaches to build evaluation infrastructure for Quilto/Swealog'
user_name: 'Jongkuk Lim'
date: '2026-01-19'
web_research_enabled: true
source_verification: true
---

# Research Report: Technical - LLM Agent Quality Evaluation

**Date:** 2026-01-19
**Author:** Jongkuk Lim
**Research Type:** Technical

---

## Research Overview

This research investigates approaches for evaluating multi-agent LLM system quality, with focus on:
- End-to-end (E2E) evaluation over individual sub-agent testing
- LLM-as-judge evaluation methodology
- Using Claude Code responses as quality baseline
- Dataset generation strategies for evaluation
- Application to Quilto framework (raw markdown retrieval, not RAG)

---

## Technical Research Scope Confirmation

**Research Topic:** LLM Agent Quality Evaluation
**Research Goals:** Understand E2E evaluation frameworks, LLM-as-judge patterns, baseline generation strategies, and multi-agent benchmarking approaches to build evaluation infrastructure for Quilto/Swealog

**Technical Research Scope:**

| Area | Focus |
|------|-------|
| Architecture Analysis | LLM evaluation system design, judge pipeline patterns, evaluation orchestration |
| Implementation Approaches | LLM-as-judge prompt engineering, rubric design, bias mitigation |
| Technology Stack | RAGAS, DeepEval, LangSmith, Patronus, custom solutions |
| Integration Patterns | Baseline generation, synthetic dataset creation, regression testing |
| Performance Considerations | Evaluation cost/latency, batch vs real-time, scaling strategies |

**Specific Research Topics:**

1. LLM Evaluation Frameworks - RAGAS, DeepEval, LangSmith, Patronus comparison
2. LLM-as-Judge Patterns - Prompt templates, rubric design, avoiding biases
3. Baseline Generation - Claude response collection, synthetic data strategies
4. Multi-Agent Benchmarking - How others evaluate agent orchestration quality
5. Retrieval Evaluation - Measuring retrieval strategy quality (not just accuracy)
6. Prompt Regression Testing - Detecting quality regressions over time

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-01-19

---

## Technology Stack Analysis

### LLM Evaluation Frameworks

#### DeepEval
DeepEval is an open-source LLM evaluation framework developed by Confident AI, designed to integrate seamlessly into Python testing workflows. Often described as "Pytest for LLMs," it provides a unit-test-like interface for validating model outputs.

**Key Strengths:**
- 14+ LLM evaluation metrics (both for RAG and fine-tuning use cases)
- Self-explaining metrics that tell you why the score cannot be higher
- Full evaluation ecosystem with CI/CD integration
- Support for agentic workflows and LLM chatbot conversations
- Built-in red-teaming module for stress-testing guardrails (40+ attack types)

**Limitations:**
- LLM calls not greatly optimized, can hit throttling limits
- Cost spikes possible with cloud-based LLMs

_Source: [DeepEval vs Ragas](https://deepeval.com/blog/deepeval-vs-ragas), [Confident AI Blog](https://www.confident-ai.com/blog/greatest-llm-evaluation-tools-in-2025)_

#### RAGAS (Retrieval-Augmented Generation Assessment Suite)
RAGAS is an open-source evaluation framework specifically designed for RAG and agentic LLM applications. Provides a lightweight experimentation environment similar to using pandas for data analysis.

**Core Metrics:**
- Faithfulness, Contextual Relevancy, Answer Relevancy
- Contextual Recall, Contextual Precision
- Combined into overall RAG score

**Key Strengths:**
- Supports metrics for agentic workflows, tool use, SQL evaluation
- Multimodal extensions (Multimodal Faithfulness, Noise Sensitivity)
- Highly extensible with custom metrics
- Mentioned by OpenAI during Dev Day 2023

**Limitations:**
- Metrics are somewhat opaque (not self-explanatory)
- Lacks built-in observability, experiment tracking, or production monitoring
- Sometimes fails to extract statements from RAG responses

_Source: [DeepEval vs Ragas Comparison](https://deepeval.com/blog/deepeval-vs-ragas), [Medium - LLM Evaluation 2025](https://medium.com/@mahernaija/choosing-the-right-llm-evaluation-framework-in-2025-deepeval-ragas-giskard-langsmith-and-c7133520770c)_

#### Framework Comparison

| Feature | DeepEval | RAGAS |
|---------|----------|-------|
| **Focus** | Full evaluation ecosystem | RAG-specific metrics |
| **Explainability** | Self-explaining metrics | Opaque scores |
| **CI/CD Integration** | Native pytest integration | More code-centric |
| **Red Teaming** | Built-in support | No red teaming |
| **Flexibility** | Broader use cases | RAG-focused |

_Source: [Comet LLM Evaluation Frameworks](https://www.comet.com/site/blog/llm-evaluation-frameworks/)_

---

### Evaluation Platforms

#### LangSmith
From the LangChain team, LangSmith offers deep visibility into LLM-driven systems with tracing, debugging, monitoring, and evaluation capabilities.

**Key Strengths:**
- Full-stack tracing and debugging
- Captures each input, output, tool call, and step
- Agent tracing: Visualization for multi-step workflows
- Flexible retention: 14-day base or 400-day extended traces

**Best For:** Teams committed to LangChain ecosystem, Python-centric teams building complex agent applications.

**Limitations:**
- Best experience requires LangChain
- Per-seat pricing gets expensive at scale

_Source: [LangWatch Comparison](https://langwatch.ai/blog/langwatch-vs-langsmith-vs-braintrust-vs-langfuse-choosing-the-best-llm-evaluation-monitoring-tool-in-2025), [Braintrust vs LangSmith](https://blog.promptlayer.com/braintrust-vs-langsmith/)_

#### Braintrust
A managed LLM evaluation and observability platform with strong focus on evaluation workflows. Provides SDKs for TypeScript and Python.

**Key Strengths:**
- Unified platform for evaluation and monitoring
- Strong TypeScript/JavaScript support
- Collaborative, experiment-driven environment
- Custom database (Brainstore): up to 86x faster for full-text search

**Best For:** Framework-agnostic teams, cross-functional collaboration, early-stage experimentation.

_Source: [Braintrust Best LLM Evaluation Platforms 2025](https://www.braintrust.dev/articles/best-llm-evaluation-platforms-2025)_

#### Patronus AI
Enterprise-focused LLM evaluation platform with state-of-the-art hallucination detection and specialized models.

**Key Models:**
- **Lynx:** State-of-the-art hallucination detection for RAG (surpasses GPT-4o and Claude-3.5)
- **Glider:** Small language model judge for explainable, rubric-based scoring

**2025 Features:**
- First Multimodal LLM-as-a-Judge (MLLM-as-a-Judge)
- Automated agent failure detection across 15 error modes
- AI Guide for automated experimentation

**Impact:** Customers report 60x productivity boost, reducing agent debugging from 1 hour to 1 minute.

_Source: [Patronus AI Features](https://www.patronus.ai/product/features), [Patronus Multimodal Judge](https://www.patronus.ai/blog/announcing-the-first-multimodal-llm-as-a-judge)_

#### Langfuse
Open-source alternative to commercial platforms.

**Key Differentiator:** Free and easy to self-host, highly customizable.

_Source: [Langfuse Alternatives](https://langfuse.com/faq/all/best-braintrustdata-alternatives)_

---

### LLM-as-Judge Implementation Approaches

#### Types of LLM-as-Judge

| Type | Description | Use Case |
|------|-------------|----------|
| **Single Output** | Scores individual outputs based on custom criteria | Quality scoring |
| **Pairwise** | Chooses "winner" between multiple outputs | A/B comparison |

#### Best Practices (2025)

1. **Temperature Settings**
   - Use 0.1-0.2 for deterministic evaluation
   - 0.3-0.5 for multiple samples
   - Avoid >0.7 (too random)

2. **Scoring Scales**
   - Binary (Pass/Fail) most reliable
   - 3-point or 5-point with clear rubric acceptable
   - Avoid 10-point or 100-point without examples

3. **Few-Shot Examples**
   - Zero-shot: baseline accuracy
   - 1 example per score: +15-20% accuracy
   - 2-3 examples per score: +25-30% accuracy

4. **Mitigate Biases**
   - Position bias (~40% GPT-4 inconsistency): Evaluate both (A,B) and (B,A) orderings
   - Verbosity bias (~15% inflation): Reward conciseness explicitly

5. **Techniques to Improve Judges**
   - Chain-of-thought prompting
   - In-context learning
   - Position swapping (for pairwise)

**Agreement with Human Judgment:** Sophisticated judge models align with human judgment up to 85%, higher than human-to-human agreement (81%).

_Source: [Confident AI LLM-as-Judge Guide](https://www.confident-ai.com/blog/why-llm-as-a-judge-is-the-best-llm-evaluation-method), [Monte Carlo LLM-as-Judge Best Practices](https://www.montecarlodata.com/blog-llm-as-judge/), [Patronus LLM-as-Judge Tutorial](https://www.patronus.ai/llm-testing/llm-as-a-judge)_

---

### Multi-Agent Benchmarking

#### Major Benchmarks

| Benchmark | Focus | Key Features |
|-----------|-------|--------------|
| **MultiAgentBench** | Multi-agent collaboration/competition | Milestone-based KPIs, various topologies (star, chain, tree, graph) |
| **AgentBench** | LLM-as-Agent across environments | 8 environments, multi-turn open-ended generation |
| **ColBench** | Collaborative agents | Backend coding, frontend design with simulated human partners |
| **SOTOPIA-π** | Social interactions | Social appropriateness, ethical reasoning, cultural context |

#### Evaluation Dimensions (KDD 2025 Tutorial)

**What to Evaluate:**
- Agent behavior
- Capabilities
- Reliability
- Safety

**How to Evaluate:**
- Interaction modes
- Datasets and benchmarks
- Metric computation methods
- Tooling

_Source: [AgentBench GitHub](https://github.com/THUDM/AgentBench), [Evidently AI Agent Benchmarks](https://www.evidentlyai.com/blog/ai-agent-benchmarks), [KDD 2025 Tutorial](https://sap-samples.github.io/llm-agents-eval-tutorial/)_

---

### Synthetic Dataset Generation

#### Three Main Approaches

1. **Manual Test Case Writing** - High quality but labor-intensive
2. **Existing/Benchmark Data** - Readily available but may not match use case
3. **Synthetic Generation** - Scalable but requires quality control

#### When Synthetic Data is Useful

- Cold starts (no existing data)
- Adding variety
- Covering edge cases
- Adversarial testing
- RAG evaluation

#### Generation Techniques

| Technique | Description | Limitations |
|-----------|-------------|-------------|
| **Self-improvement** | Use model's own output | Limited by model capabilities, may amplify biases |
| **Distillation** | Generate from more advanced model | Only limited by best model available |

#### Tools for Synthetic Generation

1. **DeepEval Synthesizer** - Generate thousands of synthetic goldens in minutes
2. **Evidently AI Generator** - Build ground truth by generating queries from knowledge base
3. **RAGAS TestsetGenerator** - Generate synthetic RAG test sets from documents
4. **Hugging Face Synthetic Data Generator** - No-code approach

#### Challenges

- Ensuring diversity in generated samples
- Addressing bias and fairness issues
- Risk of amplifying biases in future models

_Source: [Evidently AI Synthetic Data](https://www.evidentlyai.com/llm-guide/llm-test-dataset-synthetic-data), [Confident AI Synthetic Data Guide](https://www.confident-ai.com/blog/the-definitive-guide-to-synthetic-data-generation-using-llms), [DeepEval Synthesizer Guide](https://deepeval.com/guides/guides-using-synthesizer)_

---

### Technology Stack Summary for Quilto/Swealog

**Recommended Evaluation Stack:**

| Component | Recommendation | Rationale |
|-----------|---------------|-----------|
| **Core Framework** | DeepEval | Pytest integration, self-explaining metrics, agentic support |
| **RAG Metrics** | RAGAS | Specialized retrieval metrics, works with DeepEval |
| **LLM-as-Judge** | Custom + Patronus Glider | Rubric-based scoring, small model efficiency |
| **Dataset Generation** | DeepEval Synthesizer or custom distillation | Scalable, quality control |
| **Observability** | Langfuse (open-source) | Self-hosted, customizable |

**Key Considerations for Quilto:**
- Raw markdown retrieval (not vector RAG) - need custom retrieval strategy metrics
- Multi-agent orchestration - need end-to-end evaluation, not just component testing
- Claude as baseline - pairwise LLM-as-judge comparing to Claude responses

---

## Integration Patterns Analysis

### CI/CD Pipeline Integration

#### DeepEval Pytest Integration

DeepEval provides native pytest integration, making LLM evaluation feel like standard unit testing.

**GitHub Actions Example:**
```yaml
- name: Run LLM Evaluations
  run: pytest tests/evaluation_tests.py
```

**Key Features:**
- Unit-test-style interface for defining custom evaluations
- Pass/fail criteria with configurable thresholds
- Regression testing to catch breaking changes
- Metrics caching for efficiency

_Source: [DeepEval CI/CD Documentation](https://deepeval.com/docs/evaluation-unit-testing-in-ci-cd), [Deepchecks CI/CD Guide](https://www.deepchecks.com/llm-evaluation/ci-cd-pipelines/)_

#### Best Practices for CI/CD Integration

| Practice | Description |
|----------|-------------|
| **Regression Testing** | Evaluate on same test cases every iteration |
| **Threshold-Based Gates** | Define quantitative "breaking change" thresholds |
| **Dataset Versioning** | Freeze evaluation datasets as release artifacts |
| **Parallel Execution** | Run evaluations in cloud for scalability |

**Operational Considerations:**
- Continuous evaluation can be resource-intensive
- Cloud-based solutions (AWS, GCP, Azure) provide scalable compute
- Consider evaluation costs in pipeline budget

_Source: [Arize AI CI/CD Guide](https://arize.com/blog/how-to-add-llm-evaluations-to-ci-cd-pipelines/), [Braintrust CI/CD Tools](https://www.braintrust.dev/articles/best-ai-evals-tools-cicd-2025)_

---

### Framework API Integration

#### DeepEval + RAGAS Integration

DeepEval provides direct imports for RAGAS metrics:

```python
from deepeval import evaluate
from deepeval.metrics.ragas import RagasMetric
from deepeval.test_case import LLMTestCase

metric = RagasMetric(threshold=0.5, model="gpt-3.5-turbo")
test_case = LLMTestCase(
    input="What if these shoes don't fit?",
    actual_output=actual_output,
    expected_output=expected_output,
    retrieval_context=retrieval_context
)

# Single evaluation
metric.measure(test_case)

# Bulk evaluation
evaluate([test_case], [metric])
```

**Available RAGAS Metrics in DeepEval:**
- `RAGASAnswerRelevancyMetric`
- `RAGASFaithfulnessMetric`
- `RAGASContextualRecallMetric`
- `RAGASContextualPrecisionMetric`

**DeepEval Advantages over Raw RAGAS:**
- JSON confineable (avoids NaN scores from invalid JSON)
- Metrics caching
- Native pytest integration
- First-class error handling

_Source: [DeepEval RAGAS Docs](https://deepeval.com/docs/metrics-ragas), [Haystack DeepEval Cookbook](https://haystack.deepset.ai/cookbook/rag_eval_deep_eval)_

---

### Agent Observability Integration

#### LangGraph Tracing Options

| Platform | LangGraph Support | Key Features |
|----------|------------------|--------------|
| **LangSmith** | Native (single env var) | Deep LangChain internals visibility |
| **Langfuse** | Via LangChain integration | Open-source, multi-turn support |
| **Braintrust** | Global callback handlers | Specialized trace processors |
| **Galileo** | Direct integration | Enterprise-focused, LLM providers |

**LangSmith Setup:**
```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=<your-api-key>
```

**Langfuse (Open-Source) Integration:**
- Debug, analyze, iterate on LangGraph applications
- Built-in persistence for error recovery
- Human-in-the-loop workflow support

_Source: [Langfuse LangGraph Guide](https://langfuse.com/guides/cookbook/example_langgraph_agents), [Braintrust Observability](https://www.braintrust.dev/articles/best-ai-observability-platforms-2025)_

#### OpenTelemetry Standardization (2025)

The industry is moving toward common semantic conventions for AI agent observability:
- Standardized metrics, traces, and logs across frameworks
- Support for IBM Bee Stack, CrewAI, AutoGen, LangGraph
- Framework-specific extensions within common standard

_Source: [OpenTelemetry AI Agent Observability](https://opentelemetry.io/blog/2025/ai-agent-observability/)_

---

### Dataset Versioning & Management

#### Best Practices

| Approach | Implementation |
|----------|---------------|
| **Freeze as Artifact** | Treat dataset like release artifact with tags |
| **Git-like Versioning** | Use DVC or LakeFS for data version control |
| **Tag with Run ID** | Store dataset tag (e.g., `eval/v2025-01-19`) with experiment |
| **Require DATA_REF** | Training/eval code must accept explicit dataset reference |

**Tools:**
- **DVC**: Open-source, Git-like interface for data versioning
- **LakeFS**: Data lake versioning at scale
- **W&B Artifacts**: Version prompts, datasets, embeddings with lineage
- **MLflow**: Experiment tracking with parameter/metric logging

_Source: [Braintrust LLMOps Platforms](https://www.braintrust.dev/articles/best-llmops-platforms-2025), [LakeFS MLOps Tools](https://lakefs.io/mlops/mlops-tools/)_

#### Platform-Specific Dataset Management

| Platform | Dataset Features |
|----------|-----------------|
| **Galileo** | Structured organization, automatic versioning, reference outputs |
| **LangSmith** | Test query datasets, regression test saves |
| **ZenML** | Full lineage tracing (model, prompt, dataset, logic → metrics) |
| **Confident AI** | Centralized storage, domain expert collaboration |

_Source: [Galileo LLM Evaluation Guide](https://galileo.ai/blog/llm-evaluation-step-by-step-guide)_

---

### Agent Evaluation Integration Patterns

#### End-to-End Agent Trajectory Evaluation

For multi-agent systems like Quilto, evaluate complete trajectories:

| Aspect | What to Evaluate |
|--------|-----------------|
| **Tool Selection** | Did agent choose correct tools? |
| **Action Sequence** | Was the action order optimal? |
| **Task Completion** | Did it achieve the goal? |
| **Failure Patterns** | Tool errors, planning breakdowns, infinite loops |

**Structured Output Integration:**
- Use Pydantic for structured agent outputs
- Easier scoring with validated schemas
- A/B testing agent configurations

_Source: [Langfuse Evaluation Roadmap](https://langfuse.com/blog/2025-11-12-evals)_

#### Testing vs Evaluation Distinction

| Concept | Traditional | LLM Applications |
|---------|-------------|------------------|
| **Testing** | `assert result == expected` | Binary pass/fail |
| **Evaluation** | N/A | Continuous quality scores |
| **LLM Reality** | Blend of both | Score meets threshold = pass |

In LLM applications, you "test" by "evaluating" with scoring functions. A test passes if the evaluation score meets your threshold.

_Source: [Langfuse Testing Guide](https://langfuse.com/blog/2025-10-21-testing-llm-applications)_

---

### Integration Architecture for Quilto/Swealog

**Proposed Integration Stack:**

```
┌─────────────────────────────────────────────────────┐
│                   CI/CD Pipeline                     │
│  (GitHub Actions / GitLab CI)                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │   DeepEval   │───▶│  pytest test_eval.py     │  │
│  │   + RAGAS    │    │  (pass/fail thresholds)  │  │
│  └──────────────┘    └──────────────────────────┘  │
│         │                                           │
│         ▼                                           │
│  ┌──────────────────────────────────────────────┐  │
│  │        Evaluation Dataset (Versioned)         │  │
│  │  - Synthetic (Claude distillation)            │  │
│  │  - Manual curated edge cases                  │  │
│  │  - Version tagged: eval/v2026-01-19          │  │
│  └──────────────────────────────────────────────┘  │
│         │                                           │
│         ▼                                           │
│  ┌──────────────────────────────────────────────┐  │
│  │           Langfuse (Observability)            │  │
│  │  - LangGraph traces                           │  │
│  │  - Agent trajectory visualization             │  │
│  │  - Failure pattern detection                  │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Key Integration Points:**
1. **DeepEval** in pytest for CI/CD gates
2. **Versioned datasets** with DVC or manual tagging
3. **Langfuse** for runtime observability (open-source, self-hosted)
4. **Pairwise LLM-as-judge** comparing Quilto output vs Claude baseline

---

## Architectural Patterns and Design

### Evaluation System Architecture Patterns

#### Core Evaluation Components

| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **Scorer** | Assigns numerical scores to outputs | Function that computes relevance, coherence, factuality |
| **Evaluator** | Orchestrates evaluation pipeline | Manages test cases, metrics, aggregation |
| **Judge Model** | LLM that assesses quality | Separate model from system under test |
| **Aggregator** | Combines multiple scores | Bradley-Terry, ELO rating, or weighted average |

**Non-Deterministic System Reality:**
LLM-based systems provide different outputs to the same inputs on repeated requests. This doesn't mean we cannot examine behavior, but we must think differently—evaluating across scenarios, not individual outputs.

_Source: [Martin Fowler GenAI Patterns](https://martinfowler.com/articles/gen-ai-patterns/), [Eugene Yan LLM Patterns](https://eugeneyan.com/writing/llm-patterns/)_

---

### LLM-as-Judge Pipeline Architectures

#### Direct Assessment Pattern (Point-wise)

```
Input → System Under Test → Response → Judge LLM → Score (1-5)
```

**Characteristics:**
- Individual quality score per response
- Simpler to implement
- Works well for absolute quality thresholds

**Spring AI Implementation Example:**
```
Generate Response → Evaluate Quality → Retry with Feedback → Repeat until threshold
```

_Source: [Spring AI LLM-as-Judge](https://spring.io/blog/2025/11/10/spring-ai-llm-as-judge-blog-post/)_

#### Pairwise Comparison Pattern (Your Use Case)

```
Input → System A (Quilto) → Response A ─┐
                                         ├→ Judge LLM → Winner (A/B/Tie)
Input → System B (Claude) → Response B ─┘
```

**Characteristics:**
- Comparative evaluation (better/worse than baseline)
- More reliable for subtle quality differences
- Requires position bias mitigation

**AlpacaEval Approach:**
For each instruction, outputs are generated with baseline model and test model. LLM evaluator rates quality in pairwise setup, calculating win-rate.

_Source: [Cameron Wolfe LLM-as-Judge](https://cameronrwolfe.substack.com/p/llm-as-a-judge), [Sebastian Raschka LLM Evaluation](https://magazine.sebastianraschka.com/p/llm-evaluation-4-approaches)_

#### Language Model Council (LMC) Architecture

**Multi-Judge Ensemble Pattern:**

```
┌─────────────────────────────────────────┐
│         Model Configuration              │
│  - Define "contestants" (models to test) │
│  - Define "judges" (evaluator models)    │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Unified API Integration          │
│  - OpenRouter for multi-provider access  │
│  - Single interface to diverse models    │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Peer Review Phase                │
│  - Anonymized responses (mitigate bias)  │
│  - Pairwise comparison by judges         │
│  - Score/rank based on criteria          │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Aggregation                      │
│  - Bradley-Terry or ELO rating          │
│  - Final leaderboard production          │
└─────────────────────────────────────────┘
```

_Source: [Language Model Council Medium](https://carlonuccio.medium.com/beyond-the-single-judge-democratizing-llm-evaluation-with-the-language-model-council-1c33888adcf9)_

---

### Themis Pipeline Architecture (Academic, 2025)

Complete LLM-as-Judge development pipeline:

| Phase | Components |
|-------|------------|
| **Prompt Design** | Scenario-dependent evaluation prompts via human-AI collaboration |
| **Data Construction** | Controlled instruction generation with data balancing |
| **Fine-tuning** | Multi-objective training for judge model |
| **Assessment** | Metric aggregation and calibration |

**Key Insights:**
- Prompt customization per scenario improves accuracy
- Data balancing prevents bias toward common cases
- Multi-objective training handles diverse evaluation criteria

_Source: [Themis Paper (ACM WWW 2025)](https://dl.acm.org/doi/10.1145/3701716.3715265)_

---

### JudgeLM Architecture (ICLR 2025 Spotlight)

**Scale & Performance:**
- 100K judge samples for training, 5K for validation
- Agreement exceeding 90% (surpasses human-to-human)
- GPT-4-generated high-quality judgments

**Bias Mitigation Techniques:**

| Bias Type | Mitigation |
|-----------|------------|
| **Position Bias** | Swap augmentation (evaluate both orderings) |
| **Knowledge Bias** | Reference support (provide ground truth context) |
| **Format Bias** | Reference drop (randomize format expectations) |

_Source: [JudgeLM GitHub](https://github.com/baaivision/JudgeLM)_

---

### Arena-as-a-Judge Pattern

**For Regression Testing:**
- Compare new model version vs baseline version
- Pairwise evaluation on same test set
- Calculate win-rate to detect regressions

**Metrics Calculated:**
- `candidate_model_win_rate`
- `baseline_model_win_rate`
- Judge explanations for scoring decisions

_Source: [Confident AI Arena-as-a-Judge](https://www.confident-ai.com/blog/llm-arena-as-a-judge-llm-evals-for-comparison-based-testing)_

---

### Scalability Architecture Patterns

#### Enterprise Evaluation Infrastructure

| Component | Scalability Approach |
|-----------|---------------------|
| **Compute** | Cloud platforms for thousands of concurrent tasks |
| **Data** | Automated collection, anonymization, real-time tracking |
| **Integration** | CI/CD pipelines validate every release |
| **Governance** | Results feed into AI governance frameworks |

**Key Practices:**
- Combine synthetic and real-world datasets
- Integrate evaluation into CI/CD pipelines
- Apply stress and adversarial testing

_Source: [LXT AI Agent Evaluation](https://www.lxt.ai/blog/ai-agent-evaluation/), [Kore AI Agent Evaluation](https://www.kore.ai/blog/ai-agents-evaluation)_

#### Multi-Provider Architecture

**Future-Proofing:**
- Support OpenAI, Anthropic, Google, local models
- Reduces vendor lock-in risk
- Enables model comparison across providers

_Source: [Netguru AI Agent Tech Stack](https://www.netguru.com/blog/ai-agent-tech-stack)_

---

### Guardrails Integration Pattern

**Semantic/Factuality Guardrails:**
```
LLM Output → Guardrail Evaluator → Pass/Fail
                    │
                    ├── Semantic relevance check
                    ├── Factuality verification
                    └── Hallucination detection
```

**Example:** For summary generation, validate if produced summary is semantically similar to input, or have another LLM verify accuracy.

_Source: [Eugene Yan LLM Patterns](https://eugeneyan.com/writing/llm-patterns/)_

---

### Recommended Architecture for Quilto/Swealog

**Pairwise Baseline Comparison System:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Evaluation Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌─────────────┐                        │
│  │ Test Query  │────▶│   Quilto    │────▶ Response A        │
│  │  Dataset    │     │   Agent     │                        │
│  └─────────────┘     └─────────────┘                        │
│         │                                                    │
│         │            ┌─────────────┐                        │
│         └───────────▶│   Claude    │────▶ Response B        │
│                      │  (Baseline) │      (Gold Standard)   │
│                      └─────────────┘                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Pairwise Judge                           │   │
│  │  ┌─────────────────────────────────────────────────┐ │   │
│  │  │ 1. Evaluate (A, B) ordering                     │ │   │
│  │  │ 2. Evaluate (B, A) ordering (position bias fix) │ │   │
│  │  │ 3. Aggregate: Only count consistent wins        │ │   │
│  │  └─────────────────────────────────────────────────┘ │   │
│  │                                                       │   │
│  │  Rubric:                                             │   │
│  │  - Accuracy (factual correctness)                    │   │
│  │  - Completeness (answered all aspects)               │   │
│  │  - Conciseness (no unnecessary verbosity)            │   │
│  │  - Domain expertise (fitness terminology)            │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Metrics & Reporting                      │   │
│  │  - Win rate: Quilto vs Claude                        │   │
│  │  - Per-category breakdown                             │   │
│  │  - Regression detection                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**
1. **Claude as baseline** - High-quality reference responses
2. **Pairwise comparison** - More reliable than absolute scoring
3. **Position swap** - Mitigate position bias (~40% inconsistency in GPT-4)
4. **Multi-criteria rubric** - Domain-specific evaluation criteria
5. **Consistent wins only** - Require agreement across both orderings

---

## Implementation Approaches and Technology Adoption

### Step-by-Step Implementation Workflow

#### Phase 1: Foundation (Observability First)

Everything begins with observability. Observability tools log inputs, outputs, latencies, and metadata, turning black-box LLMs into inspectable systems.

```
1. Integrate Langfuse/tracing into Quilto
2. Log all agent interactions (inputs, outputs, tool calls)
3. Establish baseline metrics before adding evaluation
```

_Source: [Langfuse Evaluation Roadmap](https://langfuse.com/blog/2025-11-12-evals)_

#### Phase 2: Dataset Creation

**The "5 D's" of Dataset Creation:**
1. **Defined Scope** - Align with specific tasks
2. **Diverse Coverage** - Happy path + edge cases + adversarial
3. **Domain Expertise** - Collaborate with fitness experts
4. **Data Quality** - Curated, annotated, versioned
5. **Documentation** - Clear labeling guidelines

**Dataset Strategies:**

| Strategy | Source | Use Case |
|----------|--------|----------|
| **Manual Curation** | Subject matter expertise | Critical examples, edge cases |
| **Production Sampling** | Tracing logs | Real-world usage patterns |
| **Synthetic Generation** | Claude distillation | Scale and coverage |

_Source: [Databricks LLM Evaluation](https://www.databricks.com/blog/best-practices-and-methods-llm-evaluation), [Kili Technology Dataset Guide](https://kili-technology.com/large-language-models-llms/how-to-build-llm-evaluation-datasets-for-your-domain-specific-use-cases)_

#### Phase 3: Evaluation Pipeline Setup

**DeepEval Integration:**

```python
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric

# Create test cases from your dataset
test_cases = [
    LLMTestCase(
        input=query,
        actual_output=quilto_response,
        expected_output=claude_response,  # baseline
        retrieval_context=retrieved_entries
    )
    for query, quilto_response, claude_response, retrieved_entries
    in dataset
]

# Run evaluation
evaluate(test_cases, [AnswerRelevancyMetric(threshold=0.7)])
```

**Best Practices:**
- Start with 3-5 core metrics (not more)
- At least one custom task-specific metric
- Automate early (integrate into PR workflow)
- Mix automated + LLM-as-judge + human review

_Source: [Confident AI Metrics Guide](https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation), [PromptLayer Eval Framework](https://blog.promptlayer.com/llm-eval-framework/)_

#### Phase 4: CI/CD Integration

```yaml
# .github/workflows/llm-eval.yml
name: LLM Evaluation
on: [pull_request]
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run LLM Evaluations
        run: pytest tests/eval/ --tb=short
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

**Continuous Evaluation (CE):**
- CI/CE/CD integration is indispensable for LLMOps
- Trigger evaluations on pull requests
- Track quality over time with versioned datasets

_Source: [Datadog LLM Eval Best Practices](https://www.datadoghq.com/blog/llm-evaluation-framework-best-practices/)_

---

### Dataset Creation Workflow for Quilto/Swealog

#### Golden Dataset Structure

```yaml
# tests/eval/dataset/v2026-01-19/golden.yaml
version: "2026-01-19"
domain: "fitness"
test_cases:
  - id: "query_001"
    category: "insight"
    input: "Why was my bench press weak last week?"
    context:
      date_range: "2026-01-06 to 2026-01-12"
      retrieved_entries:
        - "2026-01-08: Bench 80kg 3x5, felt tired"
        - "2026-01-07: Poor sleep 5hrs"
    baseline_response: |
      Your bench press may have felt weak due to insufficient
      sleep on January 7th (5 hours). Sleep deprivation impacts
      strength performance...
    evaluation_criteria:
      - must_mention: ["sleep", "recovery"]
      - accuracy: "factual reference to logged data"
      - completeness: "addresses the 'why' question"
```

#### Dataset Categories

| Category | Examples | Count Target |
|----------|----------|--------------|
| **Happy Path** | Common queries, typical logs | 50-100 |
| **Edge Cases** | Ambiguous input, sparse data | 30-50 |
| **Adversarial** | Malformed input, out-of-domain | 20-30 |
| **Domain-Specific** | Fitness terminology, complex exercises | 30-50 |

**Total Initial Target:** 130-230 curated test cases

_Source: [SuperAnnotate LLM Evaluation](https://www.superannotate.com/blog/llm-evaluation-guide)_

---

### Cost Optimization Strategies

#### Token Usage Optimization

**Key Insight:** Output tokens cost 3-5x more than input tokens.

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| **Prompt Compression** | 20-40% | Remove filler words, place instructions first |
| **Response Caching** | 60-80% | Cache identical evaluation prompts |
| **Model Routing** | 50-70% | Use cheaper models for simple evaluations |
| **Batch Evaluation** | 30-50% | Group similar test cases |

**For Evaluation Specifically:**
- Use `gpt-4o-mini` for routine evaluations
- Reserve `gpt-4o` or `claude` for complex/contested cases
- Cache baseline (Claude) responses - generate once, reuse

_Source: [Koombea LLM Cost Optimization](https://ai.koombea.com/blog/llm-cost-optimization), [SparkCo Token Strategies](https://sparkco.ai/blog/optimize-llm-api-costs-token-strategies-for-2025)_

#### Cost Metrics to Track

| Metric | Purpose |
|--------|---------|
| **Cost per query** | Overall evaluation expense |
| **Tokens per evaluation** | Efficiency tracking |
| **Cache hit rate** | Caching effectiveness |
| **Model usage mix** | Routing optimization |

---

### Team Workflow Integration

#### Development Workflow

```
Developer makes change
         │
         ▼
┌─────────────────────────────────────────┐
│  PR Created                              │
│  - Unit tests run                        │
│  - Lint/typecheck pass                   │
├─────────────────────────────────────────┤
│  LLM Evaluation (automated)              │
│  - Run against golden dataset            │
│  - Compare win-rate vs baseline          │
│  - Flag regressions (win-rate drops)     │
├─────────────────────────────────────────┤
│  Human Review (if needed)                │
│  - Review flagged failures               │
│  - Approve or request changes            │
└─────────────────────────────────────────┘
         │
         ▼
    Merge & Deploy
```

#### Skill Requirements

| Role | Skills Needed |
|------|--------------|
| **ML/LLM Engineer** | DeepEval, prompt engineering, evaluation metrics |
| **Domain Expert** | Fitness knowledge for dataset curation |
| **DevOps** | CI/CD integration, cost monitoring |

---

### Risk Assessment and Mitigation

| Risk | Mitigation |
|------|------------|
| **Baseline drift** | Version Claude responses, regenerate periodically |
| **Dataset bias** | Include adversarial cases, domain expert review |
| **Cost overrun** | Set budget alerts, use model routing |
| **Position bias in judge** | Always swap positions, require consistent wins |
| **Evaluation gaming** | Rotate evaluation prompts, blind testing |

---

## Technical Research Recommendations

### Implementation Roadmap for Quilto/Swealog

#### Phase 1: Foundation (Week 1-2)
- [ ] Integrate Langfuse for observability
- [ ] Create initial golden dataset (50 test cases)
- [ ] Set up DeepEval with basic metrics

#### Phase 2: Baseline Generation (Week 2-3)
- [ ] Generate Claude responses for all test cases
- [ ] Version and store baseline dataset
- [ ] Implement pairwise comparison logic

#### Phase 3: Evaluation Pipeline (Week 3-4)
- [ ] Build LLM-as-judge with position swap
- [ ] Create evaluation rubric (accuracy, completeness, conciseness, domain expertise)
- [ ] Integrate with pytest for CI/CD

#### Phase 4: Iteration (Ongoing)
- [ ] Expand dataset based on production logs
- [ ] Monitor win-rate trends
- [ ] Identify and fix systematic failures

### Technology Stack Recommendations

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Core Framework** | DeepEval | Pytest integration, agentic support |
| **Observability** | Langfuse | Open-source, LangGraph compatible |
| **Baseline Model** | Claude (Anthropic API) | High quality, your stated preference |
| **Judge Model** | GPT-4o-mini (cost) or Claude (quality) | Balance cost vs accuracy |
| **Dataset Storage** | Git + YAML/JSON | Versioned, reviewable |
| **CI/CD** | GitHub Actions | Already in use |

### Success Metrics and KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Win Rate vs Claude** | >40% initially, improve over time | Pairwise evaluation |
| **Evaluation Coverage** | 100% of query categories | Dataset audit |
| **Regression Detection** | <5% false negatives | Manual review of flagged PRs |
| **Evaluation Cost** | <$50/month | Token tracking |
| **Time to Evaluate** | <5 min per PR | CI/CD metrics |

### Key Takeaways

1. **Start with observability** - You can't improve what you can't measure
2. **Curate quality over quantity** - 100 excellent test cases > 1000 mediocre ones
3. **Claude as baseline is valid** - Pairwise comparison is more reliable than absolute scoring
4. **Position swap is mandatory** - 40% inconsistency without it
5. **Automate early** - Catch regressions before they ship
6. **Iterate continuously** - Evaluation is not a one-time project

---

## Research Summary

This technical research has covered:

1. **Technology Stack** - DeepEval, RAGAS, LangSmith, Patronus, Langfuse
2. **Integration Patterns** - CI/CD, pytest, dataset versioning, observability
3. **Architectural Patterns** - Pairwise comparison, LLM-as-judge, bias mitigation
4. **Implementation Approaches** - Step-by-step workflow, cost optimization, team integration

**Next Steps:**
1. Create Epic for "Agent Quality Evaluation Infrastructure"
2. Define stories for each implementation phase
3. Begin with Phase 1 (observability + initial dataset)

---

*Research completed: 2026-01-19*
*Total sources cited: 40+*
