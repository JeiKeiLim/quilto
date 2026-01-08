# 13-mem0-production-ready-agents

**Source:** `13-mem0-production-ready-agents.pdf`

---

#### **1. Introduction**

Human memory is a _foundation of intelligence_ —it shapes our identity, guides decision-making, and enables
us to learn, adapt, and form meaningful relationships (Craik and Jennings, 1992). Among its many roles,
memory is essential for communication: we recall past interactions, infer preferences, and construct evolving
mental models of those we engage with (Assmann, 2011). This ability to retain and retrieve information
over extended periods enables coherent, contextually rich exchanges that span days, weeks, or even months.
AI agents, powered by large language models (LLMs), have made remarkable progress in generating fluent,
contextually appropriate responses (Yu et al., 2024, Zhang et al., 2024). However, these systems are
fundamentally limited by their reliance on fixed context windows, which severely restrict their ability to
maintain coherence over extended interactions (Bulatov et al., 2022, Liu et al., 2023). This limitation stems
from LLMs’ lack of persistent memory mechanisms that can extend beyond their finite context windows.
While humans naturally accumulate and organize experiences over time, forming a continuous narrative


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


**Figure 1: Illustration of memory im-**
**portance in AI agents.** _Left_ : Without
persistent memory, the system forgets
critical user information (vegetarian,
dairy-free preferences) between sessions, resulting in inappropriate recommendations. _Right_ : With effective
memory, the system maintains these
dietary preferences across interactions,
enabling contextually appropriate suggestions that align with previously established constraints.


of interactions, AI systems cannot inherently persist information across separate sessions or after context
overflow. The absence of persistent memory creates a fundamental disconnect in human-AI interaction.
Without memory, AI agents forget user preferences, repeat questions, and contradict previously established
facts. Consider a simple example illustrated in Figure 1, where a user mentions being vegetarian and
avoiding dairy products in an initial conversation. In a subsequent session, when the user asks about dinner
recommendations, a system without persistent memory might suggest chicken, completely contradicting
the established dietary preferences. In contrast, a system with persistent memory would maintain this
critical user information across sessions and suggest appropriate vegetarian, dairy-free options. This common
scenario highlights how memory failures can fundamentally undermine user experience and trust.


Beyond conversational settings, memory mechanisms have been shown to dramatically enhance agent
performance in interactive environments (Majumder et al., Shinn et al., 2023). Agents equipped with
memory of past experiences can better anticipate user needs, learn from previous mistakes, and generalize
knowledge across tasks (Chhikara et al., 2023). Research demonstrates that memory-augmented agents
improve decision-making by leveraging causal relationships between actions and outcomes, leading to more
effective adaptation in dynamic scenarios (Rasmussen et al., 2025). Hierarchical memory architectures
(Packer et al., 2023, Sarthi et al., 2024) and agentic memory systems capable of autonomous evolution (Xu
et al., 2025) have further shown that memory enables more coherent, long-term reasoning across multiple
dialogue sessions.


Unlike humans, who dynamically integrate new information and revise outdated beliefs, LLMs effectively
“ _reset_ " once information falls outside their context window (Zhang, 2024, Timoneda and Vera, 2025). Even
as models like OpenAI’s GPT-4 (128K tokens) (Hurst et al., 2024), o1 (200K context) (Jaech et al., 2024),
Anthropic’s Claude 3.7 Sonnet (200K tokens) (Anthropic, 2025), and Google’s Gemini (at least 10M tokens)
(Team et al., 2024) push the boundaries of context length, these improvements merely delay rather than
solve the fundamental limitation. In practical applications, even these extended context windows prove
insufficient for two critical reasons. First, as meaningful human-AI relationships develop over weeks or
months, conversation history inevitably exceeds even the most generous context limits. Second, and perhaps
more importantly, real-world conversations rarely maintain thematic continuity. A user might mention dietary
preferences (being vegetarian), then engage in hours of unrelated discussion about programming tasks,
before returning to food-related queries about dinner options. In such scenarios, a full-context approach
would need to reason through mountains of irrelevant information, with the critical dietary preferences
potentially buried among thousands of tokens of coding discussions. Moreover, simply presenting longer
contexts does not ensure effective retrieval or utilization of past information, as attention mechanisms


2


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


degrade over distant tokens (Guo et al., 2024, Nelson et al., 2024). This limitation is particularly problematic
in high-stakes domains such as healthcare, education, and enterprise support, where maintaining continuity
and trust is crucial (Hatalis et al., 2023). To address these challenges, AI agents must adopt memory systems
that go beyond static context extension. A robust AI memory should selectively store important information,
consolidate related concepts, and retrieve relevant details when needed— _mirroring human cognitive processes_
(He et al., 2024). By integrating such mechanisms, we can develop AI agents that maintain consistent
personas, track evolving user preferences, and build upon prior exchanges. This shift will transform AI from
transient, forgetful responders into reliable, long-term collaborators, fundamentally redefining the future of
conversational intelligence.


In this paper, we address a fundamental limitation in AI systems: their inability to maintain coherent reasoning across extended conversations across different sessions, which severely restricts meaningful
long-term interactions with users. We introduce `Mem0` (pronounced as _mem-zero_ ), a novel memory architecture that dynamically captures, organizes, and retrieves salient information from ongoing conversations.
Building on this foundation, we develop `Mem0` _[g]_, which enhances the base architecture with graph-based
memory representations to better model complex relationships between conversational elements. Our
experimental results on the `LOCOMO` benchmark demonstrate that our approaches consistently outperform
existing memory systems—including memory-augmented architectures, retrieval-augmented generation
(RAG) methods, and both open-source and proprietary solutions—across diverse question types, while
simultaneously requiring significantly lower computational resources. Latency measurements further reveal
that `Mem0` operates with 91% lower response times than full-context approaches, striking an optimal balance
between sophisticated reasoning capabilities and practical deployment constraints. These contributions
represent a meaningful step toward AI systems that can maintain coherent, context-aware conversations over
extended durations—mirroring human communication patterns and opening new possibilities for applications
in personal tutoring, healthcare, and personalized assistance.

#### **2. Proposed Methods**


We introduce two memory architectures for AI agents. **(1)** `Mem0` implements a novel paradigm that extracts,
evaluates, and manages salient information from conversations through dedicated modules for memory
extraction and updation. The system processes a pair of messages between either two user participants or a
user and an assistant. **(2)** `Mem0` _[g]_ extends this foundation by incorporating graph-based memory representations, where memories are stored as directed labeled graphs with entities as nodes and relationships as edges.
This structure enables a deeper understanding of the connections between entities. By explicitly modeling
both entities and their relationships, `Mem0` _[g]_ supports more advanced reasoning across interconnected facts,
especially for queries that require navigating complex relational paths across multiple memories.


**2.1.** **`Mem0`**


Our architecture follows an incremental processing paradigm, enabling it to operate seamlessly within
ongoing conversations. As illustrated in Figure 2, the complete pipeline architecture consists of two phases:
_extraction_ and _update_ .


The **extraction phase** initiates upon ingestion of a new message pair ( _m_ _t_ −1, _m_ _t_ ), where _m_ _t_ represents the
current message and _m_ _t_ −1 the preceding one. This pair typically consists of a user message and an assistant
response, capturing a complete interaction unit. To establish appropriate context for memory extraction, the
system employs two complementary sources: `(1)` a conversation summary _S_ retrieved from the database that


3


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


**Figure 2:** Architectural overview of the `Mem0` system showing extraction and update phase. The extraction phase
processes messages and historical context to create new memories. The update phase evaluates these extracted
memories against similar existing ones, applying appropriate operations through a Tool Call mechanism. The database
serves as the central repository, providing context for processing and storing updated memories.


encapsulates the semantic content of the entire conversation history, and `(2)` a sequence of recent messages
{ _m_ _t_ − _m_, _m_ _t_ − _m_ +1, ..., _m_ _t_ −2 } from the conversation history, where _m_ is a hyperparameter controlling the recency
window. To support context-aware memory extraction, we implement an asynchronous summary generation
module that periodically refreshes the conversation summary. This component operates independently of the
main processing pipeline, ensuring that memory extraction consistently benefits from up-to-date contextual
information without introducing processing delays. While _S_ provides global thematic understanding across
the entire conversation, the recent message sequence offers granular temporal context that may contain
relevant details not consolidated in the summary. This dual contextual information, combined with the new
message pair, forms a comprehensive prompt _P_ = ( _S_, { _m_ _t_ − _m_, ..., _m_ _t_ −2 }, _m_ _t_ −1, _m_ _t_ ) for an extraction function
_ϕ_ implemented via an LLM. The function _ϕ_ ( _P_ ) then extracts a set of salient memories Ω = { _ω_ 1, _ω_ 2, ..., _ω_ _n_ }
specifically from the new exchange while maintaining awareness of the conversation’s broader context,
resulting in candidate facts for potential inclusion in the knowledge base.


Following extraction, the **update phase** evaluates each candidate fact against existing memories to
maintain consistency and avoid redundancy. This phase determines the appropriate memory management
operation for each extracted fact _ω_ _i_ ∈ Ω . Algorithm 1, mentioned in Appendix B, illustrates this process. For
each fact, the system first retrieves the top _s_ semantically similar memories using vector embeddings from the
database. These retrieved memories, along with the candidate fact, are then presented to the LLM through
a function-calling interface we refer to as a ‘tool call.’ The LLM itself determines which of four distinct
operations to execute: `ADD` for creation of new memories when no semantically equivalent memory exists;
`UPDATE` for augmentation of existing memories with complementary information; `DELETE` for removal of
memories contradicted by new information; and `NOOP` when the candidate fact requires no modification to
the knowledge base. Rather than using a separate classifier, we leverage the LLM’s reasoning capabilities
to directly select the appropriate operation based on the semantic relationship between the candidate fact
and existing memories. Following this determination, the system executes the provided operations, thereby
maintaining knowledge base coherence and temporal consistency.


4


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


**Figure 3:** Graph-based memory architecture of `Mem0` _[g]_ illustrating entity extraction and update phase. The extraction
phase uses LLMs to convert conversation messages into entities and relation triplets. The update phase employs conflict
detection and resolution mechanisms when integrating new information into the existing knowledge graph.


In our experimental evaluation, we configured the system with ‘ _m_ ’ = 10 previous messages for contextual
reference and ‘ _s_ ’ = 10 similar memories for comparative analysis. All language model operations utilized
`GPT-4o-mini` as the inference engine. The vector database employs dense embeddings to facilitate efficient
similarity search during the update phase.


**2.2.** **`Mem0`** _[g]_


The `Mem0` _[g]_ pipeline, illustrated in Figure 3, implements a graph-based memory approach that effectively
captures, stores, and retrieves contextual information from natural language interactions (Zhang et al.,
2022). In this framework, memories are represented as a directed labeled graph _G_ = ( _V_, _E_, _L_ ), where:


  - Nodes _V_ represent entities (e.g., Alice, San_Francisco)

  - Edges _E_ represent relationships between entities (e.g., lives_in)

  - Labels _L_ assign semantic types to nodes (e.g., Alice - Person, San_Francisco - City)


Each entity node _v_ ∈ _V_ contains three components: (1) an entity type classification that categorizes
the entity (e.g., Person, Location, Event), (2) an embedding vector _e_ _v_ that captures the entity’s semantic
meaning, and (3) metadata including a creation timestamp _t_ _v_ . Relationships in our system are structured as
triplets in the form ( _v_ _s_, _r_, _v_ _d_ ), where _v_ _s_ and _v_ _d_ are source and destination entity nodes, respectively, and _r_ is
the labeled edge connecting them.


The extraction process employs a two-stage pipeline leveraging LLMs to transform unstructured text into
structured graph representations. First, an _**entity extractor**_ module processes the input text to identify a set
of entities along with their corresponding types. In our framework, entities represent the key information
elements in conversations—including people, locations, objects, concepts, events, and attributes that merit
representation in the memory graph. The entity extractor identifies these diverse information units by
analyzing the semantic importance, uniqueness, and persistence of elements in the conversation. For instance,
in a conversation about travel plans, entities might include destinations (cities, countries), transportation
modes, dates, activities, and participant preferences—essentially any discrete information that could be
relevant for future reference or reasoning.


5


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


Next, a _**relationship generator**_ component derives meaningful connections between these entities,
establishing a set of relationship triplets that capture the semantic structure of the information. This LLMbased module analyzes the extracted entities and their context within the conversation to identify semantically
significant connections. It works by examining linguistic patterns, contextual cues, and domain knowledge to
determine how entities relate to one another. For each potential entity pair, the generator evaluates whether
a meaningful relationship exists and, if so, classifies this relationship with an appropriate label (e.g., ‘lives_in’,
‘prefers’, ‘owns’, ‘happened_on’). The module employs prompt engineering techniques that guide the LLM
to reason about both explicit statements and implicit information in the dialogue, resulting in relationship
triplets that form the edges in our memory graph and enable complex reasoning across interconnected
information. When integrating new information, `Mem0` _[g]_ employs a sophisticated storage and update strategy.
For each new relationship triple, we compute embeddings for both source and destination entities, then
search for existing nodes with semantic similarity above a defined threshold ‘ _t_ ’. Based on node existence,
the system may create both nodes, create only one node, or use existing nodes before establishing the
relationship with appropriate metadata. To maintain a consistent knowledge graph, we implement a _**conflict**_
_**detection**_ mechanism that identifies potentially conflicting existing relationships when new information
arrives. An LLM-based _**update resolver**_ determines if certain relationships should be obsolete, marking them
as invalid rather than physically removing them to enable temporal reasoning.


The memory retrieval functionality in `Mem0` _[g]_ implements a dual-approach strategy for optimal information
access. The entity-centric method first identifies key entities within a query, then leverages semantic similarity
to locate corresponding nodes in the knowledge graph. It systematically explores both incoming and outgoing
relationships from these anchor nodes, constructing a comprehensive subgraph that captures relevant
contextual information. Complementing this, the semantic triplet approach takes a more holistic view by
encoding the entire query as a dense embedding vector. This query representation is then matched against
textual encodings of each relationship triplet in the knowledge graph. The system calculates fine-grained
similarity scores between the query and all available triplets, returning only those that exceed a configurable
relevance threshold, ranked in order of decreasing similarity. This dual retrieval mechanism enables `Mem0` _[g]_ to
handle both targeted entity-focused questions and broader conceptual queries with equal effectiveness.


From an implementation perspective, the system utilizes Neo4j [1] as the underlying graph database. LLMbased extractors and update module leverage `GPT-4o-mini` with function calling capabilities, allowing for
structured extraction of information from unstructured text. By combining graph-based representations with
semantic embeddings and LLM-based information extraction, `Mem0` _[g]_ achieves both the structural richness
needed for complex reasoning and the semantic flexibility required for natural language understanding.

#### **3. Experimental Setup**


**3.1. Dataset**


The `LOCOMO` (Maharana et al., 2024) dataset is designed to evaluate long-term conversational memory in
dialogue systems. It comprises 10 extended conversations, each containing approximately 600 dialogues and
26000 tokens on average, distributed across multiple sessions. Each conversation captures two individuals
discussing daily experiences or past events. Following these multi-session dialogues, each conversation is
accompanied by 200 questions on an average with corresponding ground truth answers. These questions
are categorized into multiple types: single-hop, multi-hop, temporal, and open-domain. The dataset
originally included an adversarial question category, which was designed to test systems’ ability to recognize


1 `[https://neo4j.com/](https://neo4j.com/)`


6


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


unanswerable questions. However, this category was excluded from our evaluation because ground truth
answers were unavailable, and the expected behavior for this question type is that the agent should recognize
them as unanswerable.


**3.2. Evaluation Metrics**


Our evaluation framework implements a comprehensive approach to assess long-term memory capabilities
in dialogue systems, considering both response quality and operational efficiency. We categorize our metrics
into two distinct groups that together provide a holistic understanding of system performance.


**`(1)`** **Performance Metrics** Previous research in conversational AI (Goswami, 2025, Soni et al., 2024, Singh
et al., 2020) has predominantly relied on lexical similarity metrics such as **F1 Score** (F 1 ) and **BLEU-1** (B 1 ).
However, these metrics exhibit significant limitations when evaluating factual accuracy in conversational
contexts. Consider a scenario where the ground truth answer is ‘ _Alice was born in March_ ’ and a system
generates ‘ _Alice is born in July_ .’ Despite containing a critical factual error regarding the birth month, traditional
metrics would assign relatively high scores due to lexical overlap in the remaining tokens (‘ _Alice_,’ ‘ _born_,’ etc.).
This fundamental limitation can lead to misleading evaluations that fail to capture semantic correctness.
To address these shortcomings, we use **LLM-as-a-Judge** (J) as a complementary evaluation metric. This
approach leverages a separate, more capable LLM to assess response quality across multiple dimensions,
including factual accuracy, relevance, completeness, and contextual appropriateness. The judge model
analyzes the question, ground truth answer and the generated answer, providing a more nuanced evaluation
that aligns better with human judgment. Due to the stochastic nature of J evaluations, we conducted 10
independent runs for each method on the entire dataset and report the mean scores along with ± 1 standard
deviation. More details about the J is present in Appendix A.


**`(2)`** **Deployment Metrics** Beyond response quality, practical deployment considerations are crucial for realworld applications of long-term memory in AI agents. We systematically track **Token Consumption**, using
‘ `cl100k_base` ’ encoding from `tiktoken`, measuring the number of tokens extracted during retrieval that
serve as context for answering queries. For our memory-based models, these tokens represent the memories
retrieved from the knowledge base, while for RAG-based models, they correspond to the total number of
tokens in the retrieved text chunks. This distinction is important as it directly affects operational costs and
system efficiency—whether processing concise memory facts or larger raw text segments. We further monitor
**Latency**, (i) _search latency_ : which captures the total time required to search the memory (in memory-based
solutions) or chunk (in RAG-based solutions) and (ii) _total latency:_ time to generate appropriate responses,
consisting of both retrieval time (accessing memories or chunks) and answer generation time using the LLM.


The relationship between these metrics reveals important trade-offs in system design. For instance,
more sophisticated memory architectures might achieve higher factual accuracy but at the cost of increased
token consumption and latency. Our multi-dimensional evaluation methodology enables researchers and
practitioners to make informed decisions based on their specific requirements, whether prioritizing response
quality for critical applications or computational efficiency for real-time deployment scenarios.


**3.3. Baselines**


To comprehensively evaluate our approach, we compare against six distinct categories of baselines that
represent the current state of conversational memory systems. These diverse baselines collectively provide a


7


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


robust framework for evaluating the effectiveness of different memory architectures across various dimensions,
including factual accuracy, computational efficiency, and scalability to extended conversations. Where
applicable, unless otherwise specified, we set the temperature to 0 to ensure the runs are as reproducible as
possible.


**Established** **`LOCOMO`** **Benchmarks** We first establish a comparative foundation by evaluating previously
benchmarked methods on the `LOCOMO` dataset. These include five established approaches: LoCoMo (Maharana et al., 2024), ReadAgent (Lee et al., 2024), MemoryBank (Zhong et al., 2024), MemGPT (Packer et al.,
2023), and A-Mem (Xu et al., 2025). These established benchmarks not only provide direct comparison
points with published results but also represent the evolution of conversational memory architectures across
different algorithmic paradigms. For our evaluation, we select the metrics where `gpt-4o-mini` was used
for the evaluation. More details about these benchmarks are mentioned in Appendix C.


**Open-Source Memory Solutions** Our second category consists of promising open-source memory architectures such as LangMem [2] (Hot Path) that have demonstrated effectiveness in related conversational tasks but
have not yet been evaluated on the `LOCOMO` dataset. By adapting these systems to our evaluation framework,
we broaden the comparative landscape and identify potential alternative approaches that may offer competitive performance. We initialized the LLM with `gpt-4o-mini` and used `text-embedding-small-3` as the
embedding model.


**Retrieval-Augmented Generation (RAG)** As a baseline, we treat the entire conversation history as a
document collection and apply a standard RAG pipeline. We first segment each conversation into fixed-length
chunks (128, 256, 512, 1024, 2048, 4096, and 8192 tokens), where 8192 is the maximum chunk size
supported by our embedding model. All chunks are embedded using OpenAI’s `text-embedding-small-3`
to ensure consistent vector quality across configurations. At query time, we retrieve the top _k_ chunks by
semantic similarity and concatenate them as context for answer generation. Throughout our experiments we
set _k_ ∈ {1,2}: with _k_ =1 only the single most relevant chunk is used, and with _k_ =2 the two most relevant
chunks (up to 16384 tokens) are concatenated. We avoid _k_ - 2 since the average conversation length (26000
tokens) would be fully covered, negating the benefits of selective retrieval. By varying chunk size and _k_, we
systematically evaluate RAG performance on long-term conversational memory tasks.


**Full-Context Processing** We adopt a straightforward approach by passing the entire conversation history
within the context window of the LLM. This method leverages the model’s inherent ability to process
sequential information without additional architectural components. While conceptually simple, this approach
faces practical limitations as conversation length increases, eventually increasing token cost and latency.
Nevertheless, it establishes an important reference point for understanding the value of more sophisticated
memory mechanisms compared to direct processing of available context.


**Proprietary Models** We evaluate OpenAI’s memory [3] feature available in their ChatGPT interface, specifically
using `gpt-4o-mini` for consistency. We ingest entire `LOCOMO` conversations with a prompt (see Appendix A)
into single chat sessions, prompting memory generation with timestamps, participant names, and conversation


2 `[https://langchain-ai.github.io/langmem/](https://langchain-ai.github.io/langmem/)`
3 `[https://openai.com/index/memory-and-new-controls-for-chatgpt/](https://openai.com/index/memory-and-new-controls-for-chatgpt/)`


8


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


**Table 1:** Performance comparison of memory-enabled systems across different question types in the `LOCOMO` dataset.
Evaluation metrics include F1 score (F 1 ), BLEU-1 (B 1 ), and LLM-as-a-Judge score (J), with higher values indicating
better performance. A-Mem [∗] represents results from our re-run of A-Mem to generate LLM-as-a-Judge scores by setting
temperature as 0. `Mem0` _[g]_ indicates our proposed architecture enhanced with graph memory. **Bold** denotes the best
performance for each metric across all methods. (↑) represents higher score is better.

|Method|Single Hop<br>F1 ↑ B1 ↑ J ↑|Multi-Hop<br>F1 ↑ B1 ↑ J ↑|Open Domain<br>F1 ↑ B1 ↑ J ↑|Temporal<br>F1 ↑ B1 ↑ J ↑|
|---|---|---|---|---|
|LoCoMo<br>ReadAgent<br>MemoryBank<br>MemGPT<br>A-Mem<br>A-Mem*<br>LangMem<br>Zep<br>OpenAI|25.02<br>19.75<br>–<br>9.15<br>6.48<br>–<br>5.00<br>4.77<br>–<br>26.65<br>17.72<br>–<br>27.02<br>20.09<br>–<br>20.76<br>14.90<br>39.79 ± 0.38<br>35.51<br>26.86<br>62.23 ± 0.75<br>35.74<br>23.30<br>61.70 ± 0.32<br>34.30<br>23.72<br>63.79 ± 0.46|12.04<br>11.16<br>–<br>5.31<br>5.12<br>–<br>5.56<br>5.94<br>–<br>9.15<br>7.44<br>–<br>12.14<br>12.00<br>–<br>9.22<br>8.81<br>18.85 ± 0.31<br>26.04<br>**22.32**<br>47.92 ± 0.47<br>19.37<br>14.82<br>41.35 ± 0.48<br>20.09<br>15.42<br>42.92 ± 0.63|40.36<br>29.05<br>–<br>9.67<br>7.66<br>–<br>6.61<br>5.16<br>–<br>41.04<br>34.34<br>–<br>44.65<br>37.06<br>–<br>33.34<br>27.58<br>54.05 ± 0.22<br>40.91<br>33.63<br>71.12 ± 0.20<br>**49.56**<br>38.92<br>**76.60 ± 0.13**<br>39.31<br>31.16<br>62.29 ± 0.12|18.41<br>14.77<br>–<br>12.60<br>8.87<br>–<br>9.68<br>6.99<br>–<br>25.52<br>19.44<br>–<br>45.85<br>36.67<br>–<br>35.40<br>31.08<br>49.91 ± 0.31<br>30.75<br>25.84<br>23.43 ± 0.39<br>42.00<br>34.53<br>49.31 ± 0.50<br>14.04<br>11.25<br>21.71 ± 0.20|
|`Mem0`<br>`Mem0`_g_|**38.72**<br>**27.13**<br>**67.13 ± 0.65**<br>38.09<br>26.03<br>65.71 ± 0.45|**28.64**<br>21.58<br>**51.15 ± 0.31**<br>24.32<br>18.82<br>47.19 ± 0.67|47.65<br>38.72<br>72.93 ± 0.11<br>49.27<br>**40.30**<br>75.71 ± 0.21|48.93<br>**40.51**<br>55.51 ± 0.34<br>**51.55**<br>40.28<br>**58.13 ± 0.44**|



text. These generated memories are then used as complete context for answering questions about each
conversation, intentionally granting the OpenAI approach privileged access to all memories rather than
only question-relevant ones. This methodology accommodates the lack of external API access for selective
memory retrieval in OpenAI’s system for benchmarking.


**Memory Providers** We incorporate Zep (Rasmussen et al., 2025), a memory management platform designed
for AI agents. Using their platform version, we conduct systematic evaluations across the `LOCOMO` dataset,
maintaining temporal fidelity by preserving timestamp information alongside conversational content. This
temporal anchoring ensures that time-sensitive queries can be addressed through appropriately contextualized
memory retrieval, particularly important for evaluating questions that require chronological awareness.
This baseline represents an important commercial implementation of memory management specifically
engineered for AI agents.

#### **4. Evaluation Results, Analysis and Discussion.**


**4.1. Performance Comparison Across Memory-Enabled Systems**


Table 1 reports F 1, B 1 and J scores for our two architectures— `Mem0` and `Mem0` _[g]_ —against a suite of competitive
baselines, as mentioned in Section 3, on single - hop, multi - hop, open - domain, and temporal questions. Overall,
both of our models set new state - of - the - art marks in all the three evaluation metrics for most question types.


                               **Single-Hop Question Performance** Single hop queries involve locating a single factual span contained
within one dialogue turn. Leveraging its dense memories in natural language text, `Mem0` secures the strongest
results:F 1 =38.72, B 1 =27.13, and J=67.13. Augmenting the natural language memories with graph memory
( `Mem0` _[g]_ ) yields marginal performance drop compared to `Mem0`, indicating that relational structure provides
limited utility when the retrieval target occupies a single turn. Among the existing baselines, the full - context
`OpenAI` run attains the next - best J score, reflecting the benefits of retaining the entire conversation in context,
while LangMem and Zep both score around 8% relatively less against our models on J score. Previous `LOCOMO`


9


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


                                                                   benchmarks such as A-mem lag by more than 25 points in J, underscoring the necessity of fine grained,
structured memory indexing even for simple retrieval tasks.


**Multi-Hop Question Performance** Multi-hop queries require synthesizing information dispersed across
multiple conversation sessions, posing significant challenges in memory integration and retrieval. `Mem0` clearly
outperforms other methods with an F 1 score of 28.64 and a J score of 51.15, reflecting its capability to
efficiently retrieve and integrate disparate information stored across sessions. Interestingly, the addition
of graph memory in `Mem0` _[g]_ does not provide performance gains here, indicating potential inefficiencies
or redundancies in structured graph representations for complex integrative tasks compared to dense
natural language memory alone. Baselines like LangMem show competitive performances, but their scores
substantially trail those of `Mem0`, emphasizing the advantage of our refined memory indexing and retrieval
mechanisms for complex query processing.


**Open-Domain Performance** In open-domain settings, the baseline Zep achieves the highest F 1 (49.56) and
J (76.60) scores, edging out our methods by a narrow margin. In particular, Zep’s J score of 76.60 surpasses
`Mem0` _[g]_ ’s 75.71 by just 0.89 percentage points and outperforms `Mem0` ’s 72.93 by 3.67 points, highlighting a
consistent, if slight, advantage in integrating conversational memory with external knowledge. `Mem0` _[g]_ remains
a strong runner-up, with a J of 75.71 reflecting high factual retrieval precision, while `Mem0` follows with 72.93,
demonstrating robust coherence. These results underscore that although structured relational memories (as
in `Mem0` and `Mem0` _[g]_ ) substantially improve open-domain retrieval, Zep maintains a small but meaningful
lead.


**Temporal Reasoning Performance** Temporal reasoning tasks hinge on accurate modeling of event sequences, their relative ordering, and durations within conversational history. Our architectures demonstrate
substantial improvements across all metrics, with `Mem0` _[g]_ achieving the highest F 1 (51.55) and J (58.13),
suggesting that structured relational representations in addition to natural language memories significantly
aid in temporally grounded judgments. Notably, the base variant, `Mem0`, also provide a decent J score (55.51),
suggesting that natural language alone can aid in temporally grounded judgments. Among baselines, OpenAI
notably underperforms, with scores below 15%, primarily due to missing timestamps in most generated
memories despite explicit prompting in the OpenAI ChatGPT to extract memories with timestamps. Other
baselines such as A-Mem achieve respectable results, yet our models clearly advance the state-of-the-art,
emphasizing the critical advantage of accurately leveraging both natural language contextualization and
structured graph representations for temporal reasoning.


**4.2. Cross-Category Analysis**


The comprehensive evaluation across diverse question categories reveals that our proposed architectures,
`Mem0` and `Mem0` _[g]_, consistently achieve superior performance compared to baseline systems. For single-hop
queries, `Mem0` demonstrates particularly strong performance, benefiting from its efficient dense natural
language memory structure. Although graph-based representations in `Mem0` _[g]_ slightly lag behind in lexical
overlap metrics for these simpler queries, they significantly enhance semantic coherence, as demonstrated
by competitive J scores. This indicates that graph structures are more beneficial in scenarios involving
nuanced relational context rather than straightforward retrieval. For multi-hop questions, `Mem0` exhibits clear
advantages by effectively synthesizing dispersed information across multiple sessions, confirming that natural
language memories provide sufficient representational richness for these integrative tasks. Surprisingly, the


10


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


**Table 2:** Performance comparison of various baselines with proposed methods. Latency measurements show p50
(median) and p95 (95th percentile) values in seconds for both search time (time taken to fetch memories/chunks) and
total time (time to generate the complete response). Overall LLM-as-a-Judge score ( J ) represents the quality metric of
the generated responses on the entire `LOCOMO` dataset.


_**Latency (seconds)**_
_**Overall**_
_**Method**_
**Search** **Total** J


**chunk size** /
**K** **p50** **p95** **p50** **p95**
**memory tokens**



128 0.281 0.823 0.774 1.825 47.77 ± 0.23%

256 0.251 0.710 0.745 1.628 50.15 ± 0.16%

512 0.240 0.639 0.772 1.710 46.05 ± 0.14%

1024 0.240 0.723 0.821 1.957 40.74 ± 0.17%

2048 0.255 0.752 0.996 2.182 37.93 ± 0.12%

4096 0.254 0.719 1.093 2.711 36.84 ± 0.17%

8192 0.279 0.838 1.396 4.416 44.53 ± 0.13%


128 0.267 0.624 0.766 1.829 59.56 ± 0.19%

256 0.255 0.699 0.802 1.907 60.97 ± 0.20%

512 0.247 0.746 0.829 1.729 58.19 ± 0.18%

1024 0.238 0.702 0.860 1.850 50.68 ± 0.13%

2048 0.261 0.829 1.101 2.791 48.57 ± 0.22%

4096 0.266 0.944 1.451 4.822 51.79 ± 0.15%

8192 0.288 1.124 2.312 9.942 60.53 ± 0.16%



RAG



1


2



Full-context 26031 - - 9.870 17.117 **72.90** ± **0.19%**


A-Mem 2520 0.668 1.485 1.410 4.374 48.38 ± 0.15%
LangMem **127** 17.99 59.82 18.53 60.40 58.10 ± 0.21%
Zep 3911 0.513 0.778 1.292 2.926 65.99 ± 0.16%
OpenAI 4437 - - 0.466 0.889 52.90 ± 0.14%


`Mem0` 1764 **0.148** **0.200** **0.708** **1.440** 66.88 ± 0.15%
`Mem0` _[g]_ 3616 0.476 0.657 1.091 2.590 68.44 ± 0.17%


expected relational advantages of `Mem0` _[g]_ do not translate into better outcomes here, suggesting potential
overhead or redundancy when navigating more intricate graph structures in multi-step reasoning scenarios.


In temporal reasoning, `Mem0` _[g]_ substantially outperforms other methods, validating that structured
relational graphs excel in capturing chronological relationships and event sequences. The presence of explicit
relational context significantly enhances `Mem0` _[g]_ ’s temporal coherence, outperforming `Mem0` ’s dense memory
storage and highlighting the importance of precise relational representations when tracking temporally
sensitive information. Open-domain performance further reinforces the value of relational modeling. `Mem0` _[g]_,
benefiting from the relational clarity of graph-based memory, closely competes with the top-performing
baseline (Zep). This competitive result underscores `Mem0` _[g]_ ’s robustness in integrating external knowledge
through relational clarity, suggesting an optimal synergy between structured memory and open-domain
information synthesis.


11


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


**(a)** Comparison of _search_ latency at p50 (median) and p95 (95th percentile) across different memory methods ( `Mem0`, `Mem0` _[g]_, best
RAG variant, Zep, LangMem, and A-Mem). The bar heights represent J scores (left axis), while the line plots show search latency in
seconds (right axis scaled in log).


**(b)** Comparison of _total response_ latency at p50 and p95 across different memory methods ( `Mem0`, `Mem0` _[g]_, best RAG variant, Zep,
LangMem, OpenAI, full-context, and A-Mem). The bar heights represent J scores (left axis), and the line plots capture end-to-end
latency in seconds (right axis scaled in log).


**Figure 4: Latency Analysis of Different Memory Approaches.** These subfigures illustrate the J scores and latency
comparison of various selected methods from Table 2. Subfigure (a) highlights the _search/retrieval_ latency prior to
answer generation, while Subfigure (b) shows the _total_ latency (including LLM inference). Both plots overlay each
method’s J score for a holistic view of their accuracy and efficiency.


Overall, our analysis indicates complementary strengths of `Mem0` and `Mem0` _[g]_ across various task demands:
dense, natural-language-based memory offers significant efficiency for simpler queries, while explicit relational modeling becomes essential for tasks demanding nuanced temporal and contextual integration. These
findings reinforce the importance of adaptable memory structures tailored to specific reasoning contexts in
AI agent deployments.


12


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


**4.3. Performance Comparison of** **`Mem0`** **and** **`Mem0`** _[g]_ **Against RAG Approaches and Full-Context Model**


Comparisons in Table 2, focusing on the ‘Overall J’ column, reveal that both `Mem0` and `Mem0` _[g]_ consistently
outperform all RAG configurations, which vary chunk sizes (128–8192 tokens) and retrieve either one ( _k_ =1)
or two ( _k_ =2) chunks. Even the strongest RAG approach peaks at around 61% in the J metric, whereas
`Mem0` reaches 67%—about a 10% relative improvement—and `Mem0` _[g]_ reaches over 68%, achieving around
a 12% relative gain. These advances underscore the advantage of capturing only the most salient facts in
memory, rather than retrieving large chunk of original text. By converting the conversation history into
concise, structured representations, `Mem0` and `Mem0` _[g]_ mitigate noise and surface more precise cues to the
LLM, leading to better answers as evaluated by an external LLM (J).


Despite these improvements, a full-context method that ingests a chunk of roughly 26,000 tokens still
achieves the highest J score (approximately 73%). However, as shown in Figure 4b, it also incurs a very
high total p95 latency—around 17 seconds—since the model must read the entire conversation on every
query. By contrast, `Mem0` and `Mem0` _[g]_ significantly reduce token usage and thus achieve lower p95 latencies of
around 1.44 seconds (a 92% reduction) and 2.6 seconds (a 85% reduction), respectively over full-context
approach. Although the full-context approach can provide a slight accuracy edge, the memory-based systems
offer a more practical trade-off, maintaining near-competitive quality while imposing only a fraction of the
token and latency cost. As conversation length increases, full-context approaches suffer from exponential
growth in computational overhead (evident in Table 2 where total p95 latency increases significantly with
larger _k_ values or chunk sizes). This increase in input chunks leads to longer response times and higher
token consumption costs. In contrast, memory-focused approaches like `Mem0` and `Mem0` _[g]_ maintain consistent
performance regardless of conversation length, making them substantially more viable for production-scale
deployments where efficiency and responsiveness are critical.


**4.4. Latency Analysis**


Table 2 provides a comprehensive performance comparison of various retrieval and memory methodologies,
presenting median (p50) and tail (p95) latencies for both the search phase and total response generation
across the `LOCOMO` dataset. Our analysis reveals distinct performance patterns governed by architectural
choices. Memory-centric architectures demonstrate different performance characteristics. A-Mem, despite its
larger memory store, incurs substantial search overhead (p50: 0.668s), resulting in total median latencies of
1.410s. LangMem exhibits even higher search latencies (p50: 17.99s, p95: 59.82s), rendering it impractical
for interactive applications. Zep achieves moderate performance (p50 total: 1.292s). The full-context
baseline, which processes the entire conversation history without retrieval, fundamentally differs from
retrieval-based approaches. By passing the entire conversation context (26000 tokens) directly to the LLM, it
eliminates search overhead but incurs extreme total latencies (p50: 9.870s, p95: 17.117s). Similarly, the
OpenAI implementation does not perform memory search, as it processes manually extracted memories from
their playground. While this approach achieves impressive response generation times (p50: 0.466s, p95:
0.889s), it requires pre-extraction of relevant context, which is not reflected in the reported metrics.


Our proposed `Mem0` approach achieves the lowest search latency among all methods (p50: 0.148s, p95:
0.200s) as illustrated in Figure 4a. This efficiency stems from our selective memory retrieval mechanism
and infra improvements that dynamically identifies and retrieves only the most salient information rather
than fixed-size chunks. Consequently, `Mem0` maintains the lowest total median latency (0.708s) with
remarkably contained p95 values (1.440s), making it particularly suitable for latency-sensitive applications
such as interactive AI agents. The graph-enhanced `Mem0` _[g]_ variant introduces additional relational modeling
capabilities at a moderate latency cost, with search times (0.476s) still outperforming all existing memory


13


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


solutions and baselines. Despite this increase, `Mem0` _[g]_ maintains competitive total latencies (p50: 1.091s, p95:
2.590s) while achieving the highest J score (68.44%) across all methods—trailing only the computationally
prohibitive full-context approach. This performance profile demonstrates our methods’ ability to balance
response quality and computational efficiency, offering a compelling solution for production AI agents where
both factors are critical constraints.


**4.5. Memory System Overhead: Token Analysis and Construction Time**


                                                          We measure the average token budget required to materialise each system’s long term memory store.
`Mem0` encodes complete dialogue turns in a natural language representation and therefore occupies only **7k**
tokens per conversation on an average. Where as `Mem0` _[g]_ roughly doubles the footprint to **14k** tokens, due to
the introduction of graph memories which includes nodes and corresponding relationships. In stark contrast,
Zep’s memory graph consumes in excess of **600k** tokens. The inflation arises from Zep’s design choice to
cache a full abstractive summary at every node while also storing facts on the connecting edges, leading
to extensive redundancy across the graph. For perspective, supplying the _entire_ raw conversation context
to the language model—without any memory abstraction—amounts to roughly **26k** tokens on average, 20
times less relative to Zep’s graph. Beyond token inefficiency, our experiments revealed significant operational
bottlenecks with Zep. After adding memories to Zep’s system, we observed that immediate memory retrieval
attempts often failed to answer our queries correctly. Interestingly, re-running identical searches after a
delay of several hours yielded considerably better results. This latency suggests that Zep’s graph construction
involves multiple asynchronous LLM calls and extensive background processing, making the memory system
impractical for real-time applications. In contrast, `Mem0` graph construction completes in under a minute even
in worst-case scenarios, allowing users to immediately leverage newly added memories for query responses.


These findings highlight that Zep not only replicates identical knowledge fragments across multiple
nodes, but also introduces significant operational delays. Our architectures— `Mem0` and `Mem0` _[g]_ —preserve the
same information at a fraction of the token cost and with substantially faster memory availability, offering a
more memory-efficient and operationally responsive representation.

#### **5. Conclusion and Future Work**


We have introduced `Mem0` and `Mem0` _[g]_, two complementary memory architectures that overcome the intrinsic
limitations of fixed context windows in LLMs. By dynamically extracting, consolidating, and retrieving
compact memory representations, `Mem0` achieves state-of-the-art performance across single - hop and multi - hop
reasoning, while `Mem0` _[g]_ ’s graph - based extensions unlock significant gains in temporal and open - domain tasks.
On the `LOCOMO` benchmark, our methods deliver 5%, 11%, and 7% relative improvements in single-hop,
temporal, and multi-hop reasoning question types over best performing methods in respective question

                                         type and reduce p95 latency by over 91% compared to full context baselines—demonstrating a powerful
balance between precision and responsiveness. `Mem0` ’s dense memory pipeline excels at rapid retrieval
for straightforward queries, minimizing token usage and computational overhead. In contrast, `Mem0` _[g]_ ’s
structured graph representations provide nuanced relational clarity, enabling complex event sequencing
and rich context integration without sacrificing practical efficiency. Together, they form a versatile memory
toolkit that adapts to diverse conversational demands while remaining deployable at scale.


Future research directions include optimizing graph operations to reduce the latency overhead in `Mem0` _[g]_,
exploring hierarchical memory architectures that blend efficiency with relational representation, and developing more sophisticated memory consolidation mechanisms inspired by human cognitive processes.


14


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


Additionally, extending our memory frameworks to domains beyond conversational scenarios, such as procedural reasoning and multimodal interactions, would further validate their broader applicability. By addressing
the fundamental limitations of fixed context windows, our work represents a significant advancement toward
conversational AI systems capable of maintaining coherent, contextually rich interactions over extended
periods, much like their human counterparts.

#### **6. Acknowledgments**


We would like to express our sincere gratitude to Harsh Agarwal, Shyamal Anadkat, Prithvijit Chattopadhyay,
Siddesh Choudhary, Rishabh Jain, and Vaibhav Pandey for their invaluable insights and thorough reviews of
early drafts. Their constructive comments and detailed suggestions helped refine the manuscript, enhancing
both its clarity and overall quality. We deeply appreciate their generosity in dedicating time and expertise to
this work.

#### **References**


Anthropic. Model card and evaluations for claude models. Technical report, Anthropic, February 2025. URL

`[https://www.anthropic.com/news/claude-3-7-sonnet](https://www.anthropic.com/news/claude-3-7-sonnet)` .


Jan Assmann. Communicative and cultural memory. In _Cultural memories: The geographical point of view_,
pages 15–27. Springer, 2011.


Aydar Bulatov, Yury Kuratov, and Mikhail Burtsev. Recurrent memory transformer. _Advances in Neural_
_Information Processing Systems_, 35:11079–11091, 2022.


Prateek Chhikara, Jiarui Zhang, Filip Ilievski, Jonathan Francis, and Kaixin Ma. Knowledge-enhanced agents
for interactive text games. In _Proceedings of the 12th Knowledge Capture Conference 2023_, pages 157–165,
2023.


Fergus IM Craik and Janine M Jennings. Human memory. 1992.


Gaurav Goswami. Dissecting the metrics: How different evaluation approaches yield diverse results for
conversational ai. _Authorea Preprints_, 2025.


Tianyu Guo, Druv Pai, Yu Bai, Jiantao Jiao, Michael Jordan, and Song Mei. Active-dormant attention
heads: Mechanistically demystifying extreme-token phenomena in llms. In _NeurIPS 2024 Workshop on_
_Mathematics of Modern Machine Learning_, 2024.


Kostas Hatalis, Despina Christou, Joshua Myers, Steven Jones, Keith Lambert, Adam Amos-Binks, Zohreh
Dannenhauer, and Dustin Dannenhauer. Memory matters: The need to improve long-term memory in
llm-agents. In _Proceedings of the AAAI Symposium Series_, volume 2, pages 277–280, 2023.


Zihong He, Weizhe Lin, Hao Zheng, Fan Zhang, Matt W Jones, Laurence Aitchison, Xuhai Xu, Miao Liu,
Per Ola Kristensson, and Junxiao Shen. Human-inspired perspectives: A survey on ai long-term memory.
_arXiv preprint arXiv:2411.00489_, 2024.


Aaron Hurst, Adam Lerer, Adam P Goucher, Adam Perelman, Aditya Ramesh, Aidan Clark, AJ Ostrow, Akila
Welihinda, Alan Hayes, Alec Radford, et al. Gpt-4o system card. _arXiv preprint arXiv:2410.21276_, 2024.


15


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


Aaron Jaech, Adam Kalai, Adam Lerer, Adam Richardson, Ahmed El-Kishky, Aiden Low, Alec Helyar, Aleksander Madry, Alex Beutel, Alex Carney, et al. Openai o1 system card. _arXiv preprint arXiv:2412.16720_,
2024.


Kuang-Huei Lee, Xinyun Chen, Hiroki Furuta, John Canny, and Ian Fischer. A human-inspired reading
agent with gist memory of very long contexts. In _International Conference on Machine Learning_, pages
26396–26415. PMLR, 2024.


Lei Liu, Xiaoyan Yang, Yue Shen, Binbin Hu, Zhiqiang Zhang, Jinjie Gu, and Guannan Zhang. Think-inmemory: Recalling and post-thinking enable llms with long-term memory. _arXiv preprint arXiv:2311.08719_,
2023.


Adyasha Maharana, Dong-Ho Lee, Sergey Tulyakov, Mohit Bansal, Francesco Barbieri, and Yuwei Fang.
Evaluating very long-term conversational memory of llm agents. In _Proceedings of the 62nd Annual Meeting_
_of the Association for Computational Linguistics (Volume 1: Long Papers)_, pages 13851–13870, 2024.


Bodhisattwa Prasad Majumder, Bhavana Dalvi Mishra, Peter Jansen, Oyvind Tafjord, Niket Tandon, Li Zhang,
Chris Callison-Burch, and Peter Clark. Clin: A continually learning language agent for rapid task adaptation
and generalization. In _First Conference on Language Modeling_ .


Elliot Nelson, Georgios Kollias, Payel Das, Subhajit Chaudhury, and Soham Dan. Needle in the haystack for
memory based large language models. _arXiv preprint arXiv:2407.01437_, 2024.


Charles Packer, Vivian Fang, Shishir_G Patil, Kevin Lin, Sarah Wooders, and Joseph_E Gonzalez. Memgpt:
Towards llms as operating systems. 2023.


Preston Rasmussen, Pavlo Paliychuk, Travis Beauvais, Jack Ryan, and Daniel Chalef. Zep: A temporal
knowledge graph architecture for agent memory. _arXiv preprint arXiv:2501.13956_, 2025.


Parth Sarthi, Salman Abdullah, Aditi Tuli, Shubh Khanna, Anna Goldie, and Christopher D Manning. Raptor:
Recursive abstractive processing for tree-organized retrieval. In _The Twelfth International Conference on_
_Learning Representations_, 2024.


Noah Shinn, Federico Cassano, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. Reflexion: Language
agents with verbal reinforcement learning. _Advances in Neural Information Processing Systems_, 36:8634–
8652, 2023.


Prabhjot Singh, Prateek Chhikara, and Jasmeet Singh. An ensemble approach for extractive text summarization. In _2020 International Conference on Emerging Trends in Information Technology and Engineering_
_(ic-ETITE)_, pages 1–7. IEEE, 2020.


Arpita Soni, Rajeev Arora, Anoop Kumar, and Dheerendra Panwar. Evaluating domain coverage in lowresource generative chatbots: A comparative study of open-domain and closed-domain approaches using
bleu scores. In _2024 International Conference on Electrical Electronics and Computing Technologies (ICEECT)_,
volume 1, pages 1–6. IEEE, 2024.


Gemini Team, Petko Georgiev, Ving Ian Lei, Ryan Burnell, Libin Bai, Anmol Gulati, Garrett Tanzer, Damien
Vincent, Zhufeng Pan, Shibo Wang, et al. Gemini 1.5: Unlocking multimodal understanding across millions
of tokens of context. _arXiv preprint arXiv:2403.05530_, 2024.


Joan C Timoneda and Sebastián Vallejo Vera. Memory is all you need: Testing how model memory affects
llm performance in annotation tasks. _arXiv preprint arXiv:2503.04874_, 2025.


16


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, and Yongfeng Zhang. A-mem: Agentic memory for
llm agents. _arXiv preprint arXiv:2502.12110_, 2025.


Yangyang Yu, Haohang Li, Zhi Chen, Yuechen Jiang, Yang Li, Denghui Zhang, Rong Liu, Jordan W Suchow,
and Khaldoun Khashanah. Finmem: A performance-enhanced llm trading agent with layered memory and
character design. In _Proceedings of the AAAI Symposium Series_, volume 3, pages 595–597, 2024.


Jiarui Zhang. Guided profile generation improves personalization with large language models. In _Findings of_
_the Association for Computational Linguistics: EMNLP 2024_, pages 4005–4016, 2024.


Jiarui Zhang, Filip Ilievski, Kaixin Ma, Jonathan Francis, and Alessandro Oltramari. A study of zero-shot
adaptation with commonsense knowledge. In _AKBC_, 2022.


Zeyu Zhang, Xiaohe Bo, Chen Ma, Rui Li, Xu Chen, Quanyu Dai, Jieming Zhu, Zhenhua Dong, and JiRong Wen. A survey on the memory mechanism of large language model based agents. _arXiv preprint_
_arXiv:2404.13501_, 2024.


Wanjun Zhong, Lianghong Guo, Qiqi Gao, He Ye, and Yanlin Wang. Memorybank: Enhancing large language
models with long-term memory. In _Proceedings of the AAAI Conference on Artificial Intelligence_, volume 38,
pages 19724–19731, 2024.


17


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_

### **Appendix**

#### **A. Prompts**


In developing our LLM-as-a-Judge prompt, we adapt elements from the prompt released by Packer et al.
(2023).





18


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_





19


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_



20


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_

#### **B. Algorithm**


**Algorithm 1** Memory Management System: Update Operations


1: **Input:** Set of retrieved memories _F_, Existing memory store _M_ = { _m_ 1, _m_ 2, . . ., _m_ _n_ }

2: **Output:** Updated memory store _M_ [′]


3: **procedure** UpdateMemory( _F_, _M_ )

4: **for** each fact _f_ ∈ _F_ **do**

5: _operation_ ← ClassifyOperation( _f_, _M_ ) - Execute appropriate operation based on


classification

6: **if** _operation_ = ADD **then**

7: _id_ ← GenerateUniqueID()

8: _M_ ← _M_ ∪ {( _id_, _f_, "ADD")} - Add new fact with unique identifier

9: **else if** _operation_ = UPDATE **then**

10: _m_ _i_ ← FindRelatedMemory( _f_, _M_ )

11: **if** InformationContent( _f_ ) > InformationContent( _m_ _i_ ) **then**

12: _M_ ← ( _M_ \ { _m_ _i_ }) ∪ {( _id_ _i_, _f_, "UPDATE")} - Replace with richer information

13: **end if**

14: **else if** _operation_ = DELETE **then**

15: _m_ _i_ ← FindContradictedMemory( _f_, _M_ )

16: _M_ ← _M_ \ { _m_ _i_ } - Remove contradicted information

17: **else if** _operation_ = NOOP **then**

18: No operation performed - Fact already exists or is irrelevant

19: **end if**


20: **end for**


21: **return** _M_


22: **end procedure**


23: **function** ClassifyOperation( _f_, _M_ )

24: **if** ¬SemanticallySimilar( _f_, _M_ ) **then**

25: **return** ADD - New information not present in memory

26: **else if** Contradicts( _f_, _M_ ) **then**

27: **return** DELETE - Information conflicts with existing memory

28: **else if** Augments( _f_, _M_ ) **then**

29: **return** UPDATE - Enhances existing information in memory

30: **else**


31: **return** NOOP - No change required

32: **end if**


33: **end function**

#### **C. Selected Baselines**


**LoCoMo** The LoCoMo framework implements a sophisticated memory pipeline that enables LLM agents to
maintain coherent, long-term conversations. At its core, the system divides memory into short-term and
long-term components. After each conversation session, agents generate summaries (stored as short-term
memory) that distill key information from that interaction. Simultaneously, individual conversation turns are


21


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


transformed into ‘ _observations_ ’ - factual statements about each speaker’s persona and life events that are
stored in long-term memory with references to the specific dialog turns that produced them. When generating
new responses, agents leverage both the most recent session summary and selectively retrieve relevant
observations from their long-term memory. This dual-memory approach is further enhanced by incorporating
a temporal event graph that tracks causally connected life events occurring between conversation sessions.
By conditioning responses on retrieved memories, current conversation context, persona information, and
intervening life events, the system enables agents to maintain consistent personalities and recall important
details across conversations spanning hundreds of turns and dozens of sessions.


**ReadAgent** ReadAgent addresses the fundamental limitations of LLMs by emulating how humans process
lengthy texts through a sophisticated three-stage pipeline. First, in Episode Pagination, the system intelligently
segments text at natural cognitive boundaries rather than arbitrary cutoffs. Next, during Memory Gisting,
it distills each segment into concise summaries that preserve essential meaning while drastically reducing
token count—similar to how human memory retains the substance of information without verbatim recall.
Finally, when tasked with answering questions, the Interactive Lookup mechanism examines these gists
and strategically retrieves only the most relevant original text segments for detailed processing. This
human-inspired approach enables LLMs to effectively manage documents up to 20 times longer than their
normal context windows. By balancing global understanding through gists with selective attention to
details, ReadAgent achieves both computational efficiency and improved comprehension, demonstrating that
mimicking human cognitive processes can significantly enhance AI text processing capabilities.


**MemoryBank** The MemoryBank system enhances LLMs with long-term memory through a sophisticated
three-part pipeline. At its core, the Memory Storage component warehouses detailed conversation logs,
hierarchical event summaries, and evolving user personality profiles. When a new interaction occurs, the
Memory Retrieval mechanism employs a dual-tower dense retrieval model to extract contextually relevant
past information. The Memory Updating component, provides a human-like forgetting mechanism where
memories strengthen when recalled and naturally decay over time if unused. This comprehensive approach
enables AI companions to recall pertinent information, maintain contextual awareness across extended
interactions, and develop increasingly accurate user portraits, resulting in more personalized and natural
long-term conversations.


**MemGPT** The MemGPT system introduces an operating system-inspired approach to overcome the context
window limitations inherent in LLMs. At its core, MemGPT employs a sophisticated memory management
pipeline consisting of three key components: a hierarchical memory system, self-directed memory operations,
and an event-based control flow mechanism. The system divides available memory into ‘ _main context_ ’
(analogous to RAM in traditional operating systems) and ‘ _external context_ ’ (analogous to disk storage).
The main context—which is bound by the LLM’s context window—contains system instructions, recent
conversation history, and working memory that can be modified by the model. The external context stores
unlimited information outside the model’s immediate context window, including complete conversation
histories and archival data. When the LLM needs information not present in main context, it can initiate
function calls to search, retrieve, or modify content across these memory tiers, effectively ‘ _paging_ ’ relevant
information in and out of its limited context window. This OS-inspired architecture enables MemGPT to
maintain conversational coherence over extended interactions, manage documents that exceed standard
context limits, and perform multi-hop information retrieval tasks—all while operating with fixed-context


22


_Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory_


models. The system’s ability to intelligently manage its own memory resources provides the illusion of
infinite context, significantly extending what’s possible with current LLM technology.


**A-Mem** The A-Mem model introduces an agentic memory system designed for LLM agents. This system
dynamically structures and evolves memories through interconnected notes. Each note captures interactions
enriched with structured attributes like keywords, contextual descriptions, and tags generated by the
LLM. Upon creating a new memory, A-MEM uses semantic embeddings to retrieve relevant existing notes,
then employs an LLM-driven approach to establish meaningful links based on similarities and shared
attributes. Crucially, the memory evolution mechanism updates existing notes dynamically, refining their
contextual information and attributes whenever new relevant memories are integrated. Thus, memory
structure continually evolves, allowing richer and contextually deeper connections among memories. Retrieval
from memory is conducted through semantic similarity, providing relevant historical context during agent
interactions


23


