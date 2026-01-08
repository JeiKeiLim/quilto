# 14-a-mem-agentic-memory

**Source:** `14-a-mem-agentic-memory.pdf`

---

## **A-Mem: Agentic Memory for LLM Agents**

**Wujiang Xu** [1] **, Zujie Liang** [2] **, Kai Mei** [1] **, Hang Gao** [1] **, Juntao Tan** [1] **, Yongfeng Zhang** [1] _[,]_ [3]

1 2 3
Rutgers University Independent Researcher AIOS Foundation
```
              wujiang.xu@rutgers.edu

```

**Abstract**


While large language model (LLM) agents can effectively use external tools for
complex real-world tasks, they require memory systems to leverage historical
experiences. Current memory systems enable basic storage and retrieval but lack
sophisticated memory organization, despite recent attempts to incorporate graph
databases. Moreover, these systems’ fixed operations and structures limit their
adaptability across diverse tasks. To address this limitation, this paper proposes
a novel agentic memory system for LLM agents that can dynamically organize
memories in an agentic way. Following the basic principles of the Zettelkasten
method, we designed our memory system to create interconnected knowledge
networks through dynamic indexing and linking. When a new memory is added, we
generate a comprehensive note containing multiple structured attributes, including
contextual descriptions, keywords, and tags. The system then analyzes historical
memories to identify relevant connections, establishing links where meaningful
similarities exist. Additionally, this process enables memory evolution – as new
memories are integrated, they can trigger updates to the contextual representations
and attributes of existing historical memories, allowing the memory network to
continuously refine its understanding. Our approach combines the structured
organization principles of Zettelkasten with the flexibility of agent-driven decision
making, allowing for more adaptive and context-aware memory management.
Empirical experiments on six foundation models show superior improvement
against existing SOTA baselines.


**Code for Benchmark Evaluation** :
[https://github.com/WujiangXu/AgenticMemory](https://github.com/WujiangXu/AgenticMemory)


**Code for Production-ready Agentic Memory** :
[https://github.com/WujiangXu/A-mem-sys](https://github.com/WujiangXu/A-mem-sys)


**1** **Introduction**


Large Language Model (LLM) agents have demonstrated remarkable capabilities in various tasks,
with recent advances enabling them to interact with environments, execute tasks, and make decisions
autonomously [ 23, 33, 7 ]. They integrate LLMs with external tools and delicate workflows to improve
reasoning and planning abilities. Though LLM agent has strong reasoning performance, it still needs
a memory system to provide long-term interaction ability with the external environment [35].


Existing memory systems [ 25, 39, 28, 21 ] for LLM agents provide basic memory storage functionality.
These systems require agent developers to predefine memory storage structures, specify storage
points within the workflow, and establish retrieval timing. Meanwhile, to improve structured memory
organization, Mem0 [ 8 ], following the principles of RAG [ 9, 18, 30 ], incorporates graph databases for
storage and retrieval processes. While graph databases provide structured organization for memory
systems, their reliance on predefined schemas and relationships fundamentally limits their adaptability.
This limitation manifests clearly in practical scenarios - when an agent learns a novel mathematical
solution, current systems can only categorize and link this information within their preset framework,


Preprint.


Write

Interaction


Read



Interaction





Environment



LLM Agents Memory



Environment



**(a)** Traditional memory system.



**(b)** Our proposed agentic memory.



**Figure 1:** Traditional memory systems require predefined memory access patterns specified in the workflow,
limiting their adaptability to diverse scenarios. Contrastly, our A-M EM enhances the flexibility of LLM agents
by enabling dynamic memory operations.


unable to forge innovative connections or develop new organizational patterns as knowledge evolves.
Such rigid structures, coupled with fixed agent workflows, severely restrict these systems’ ability
to generalize across new environments and maintain effectiveness in long-term interactions. The
challenge becomes increasingly critical as LLM agents tackle more complex, open-ended tasks,
where flexible knowledge organization and continuous adaptation are essential. Therefore, _how to_
_design a flexible and universal memory system that supports LLM agents’ long-term interactions_
remains a crucial challenge.


In this paper, we introduce a novel agentic memory system, named as A-M EM, for LLM agents that
enables dynamic memory structuring without relying on static, predetermined memory operations.
Our approach draws inspiration from the Zettelkasten method [ 15, 1 ], a sophisticated knowledge
management system that creates interconnected information networks through atomic notes and
flexible linking mechanisms. Our system introduces an agentic memory architecture that enables
autonomous and flexible memory management for LLM agents. For each new memory, we construct
comprehensive notes, which integrates multiple representations: structured textual attributes including
several attributes and embedding vectors for similarity matching. Then A-M EM analyzes the historical
memory repository to establish meaningful connections based on semantic similarities and shared
attributes. This integration process not only creates new links but also enables dynamic evolution
when new memories are incorporated, they can trigger updates to the contextual representations of
existing memories, allowing the entire memories to continuously refine and deepen its understanding
over time. The contributions are summarized as:


- We present A-M EM, an agentic memory system for LLM agents that enables autonomous generation
of contextual descriptions, dynamic establishment of memory connections, and intelligent evolution
of existing memories based on new experiences. This system equips LLM agents with long-term
interaction capabilities without requiring predetermined memory operations.


- We design an agentic memory update mechanism where new memories automatically trigger two
key operations: link generation and memory evolution. Link generation automatically establishes
connections between memories by identifying shared attributes and similar contextual descriptions.
Memory evolution enables existing memories to dynamically adapt as new experiences are analyzed,
leading to the emergence of higher-order patterns and attributes.


- We conduct comprehensive evaluations of our system using a long-term conversational dataset, comparing performance across six foundation models using six distinct evaluation metrics, demonstrating
significant improvements. Moreover, we provide T-SNE visualizations to illustrate the structured
organization of our agentic memory system.


**2** **Related Work**


**2.1** **Memory for LLM Agents**


Prior works on LLM agent memory systems have explored various mechanisms for memory management and utilization [ 23, 21, 8, 39 ]. Some approaches complete interaction storage, which
maintains comprehensive historical records through dense retrieval models [ 39 ] or read-write memory
structures [ 24 ]. Moreover, MemGPT [ 25 ] leverages cache-like architectures to prioritize recent
information. Similarly, SCM [ 32 ] proposes a Self-Controlled Memory framework that enhances
LLMs’ capability to maintain long-term memory through a memory stream and controller mechanism.
However, these approaches face significant limitations in handling diverse real-world tasks. While
they can provide basic memory functionality, their operations are typically constrained by predefined
structures and fixed workflows. These constraints stem from their reliance on rigid operational


2


|Write<br>Conversation 1|Conversation 2|Col3|
|---|---|---|
|Can you help me implement a<br>custom cache system for my<br>web application? I need it to<br>handle both memory and disk<br>storage.|The cache system works<br>great, but we're seeing high<br>memory usage in<br>production. Can we modify<br>it to implement an LRU<br>eviction policy?|The cache system works<br>great, but we're seeing high<br>memory usage in<br>production. Can we modify<br>it to implement an LRU<br>eviction policy?|
||||





















**Figure 2:** Our A-M EM architecture comprises three integral parts in memory storage. During note construction,
the system processes new interaction memories and stores them as notes with multiple attributes. The link
generation process first retrieves the most relevant historical memories and then employs an LLM to determine
whether connections should be established between them. The concept of a ’box’ describes that related memories
become interconnected through their similar contextual descriptions, analogous to the Zettelkasten method.
However, our approach allows individual memories to exist simultaneously within multiple different boxes.
During the memory retrieval stage, we extract query embeddings using a text encoding model and search the
memory database for relevant matches. When related memory is retrieved, similar memories that are linked
within the same box are also automatically accessed.


patterns, particularly in memory writing and retrieval processes. Such inflexibility leads to poor
generalization in new environments and limited effectiveness in long-term interactions. Therefore, designing a flexible and universal memory system that supports agents’ long-term interactions remains
a crucial challenge.



**2.2** **Retrieval-Augmented Generation**


Retrieval-Augmented Generation (RAG) has emerged as a powerful approach to enhance LLMs
by incorporating external knowledge sources [ 18, 6, 10 ]. The standard RAG [ 37, 34 ] process
involves indexing documents into chunks, retrieving relevant chunks based on semantic similarity, and
augmenting the LLM’s prompt with this retrieved context for generation. Advanced RAG systems [ 20,
12 ] have evolved to include sophisticated pre-retrieval and post-retrieval optimizations. Building
upon these foundations, recent researches has introduced agentic RAG systems that demonstrate
more autonomous and adaptive behaviors in the retrieval process. These systems can dynamically
determine when and what to retrieve [ 4, 14 ], generate hypothetical responses to guide retrieval, and
iteratively refine their search strategies based on intermediate results [31, 29].


However, while agentic RAG approaches demonstrate agency in the retrieval phase by autonomously
deciding when and what to retrieve [ 4, 14, 38 ], our agentic memory system exhibits agency at a
more fundamental level through the autonomous evolution of its memory structure. Inspired by
the Zettelkasten method, our system allows memories to actively generate their own contextual
descriptions, form meaningful connections with related memories, and evolve both their content and
relationships as new experiences emerge. This fundamental distinction in agency between retrieval
versus storage and evolution distinguishes our approach from agentic RAG systems, which maintain
static knowledge bases despite their sophisticated retrieval mechanisms.


**3** **Methodolodgy**


Our proposed agentic memory system draws inspiration from the Zettelkasten method, implementing
a dynamic and self-evolving memory system that enables LLM agents to maintain long-term memory
without predetermined operations. The system’s design emphasizes atomic note-taking, flexible
linking mechanisms, and continuous evolution of knowledge structures.


3


**3.1** **Note Construction**


Building upon the Zettelkasten method’s principles of atomic note-taking and flexible organization,
we introduce an LLM-driven approach to memory note construction. When an agent interacts with its
environment, we construct structured memory notes that capture both explicit information and LLMgenerated contextual understanding. Each memory note _m_ _i_ in our collection _M_ = { _m_ 1 _, m_ 2 _, ..., m_ _N_ }
is represented as:
_m_ _i_ = { _c_ _i_ _, t_ _i_ _, K_ _i_ _, G_ _i_ _, X_ _i_ _, e_ _i_ _, L_ _i_ } (1)

where _c_ _i_ represents the original interaction content, _t_ _i_ is the timestamp of the interaction, _K_ _i_
denotes LLM-generated keywords that capture key concepts, _G_ _i_ contains LLM-generated tags for
categorization, _X_ _i_ represents the LLM-generated contextual description that provides rich semantic
understanding, and _L_ _i_ maintains the set of linked memories that share semantic relationships. To
enrich each memory note with meaningful context beyond its basic content and timestamp, we
leverage an LLM to analyze the interaction and generate these semantic components. The note
construction process involves prompting the LLM with carefully designed templates _P_ _s_ 1 :


_K_ _i_ _, G_ _i_ _, X_ _i_ ← LLM( _c_ _i_ ∥ _t_ _i_ ∥ _P_ _s_ 1 ) (2)


Following the Zettelkasten principle of atomicity, each note captures a single, self-contained unit of
knowledge. To enable efficient retrieval and linking, we compute a dense vector representation via a
text encoder [27] that encapsulates all textual components of the note:


_e_ _i_ = _f_ enc [ concat( _c_ _i_ _, K_ _i_ _, G_ _i_ _, X_ _i_ ) ] (3)


By using LLMs to generate enriched components, we enable autonomous extraction of implicit
knowledge from raw interactions. The multi-faceted note structure ( _K_ _i_, _G_ _i_, _X_ _i_ ) creates rich representations that capture different aspects of the memory, facilitating nuanced organization and
retrieval. Additionally, the combination of LLM-generated semantic components with dense vector
representations provides both context and computationally efficient similarity matching.


**3.2** **Link Generation**


Our system implements an autonomous link generation mechanism that enables new memory notes
to form meaningful connections without predefined rules. When the constrctd memory note _m_ _n_ is
added to the system, we first leverage its semantic embedding for similarity-based retrieval. For each
existing memory note _m_ _j_ ∈ _M_, we compute a similarity score:


_e_ _n_ ⋅ _e_ _j_
_s_ _n,j_ = (4)
∣ _e_ _n_ ∣∣ _e_ _j_ ∣


The system then identifies the top- _k_ most relevant memories:


_M_ _[n]_ near [=][ {] _[m]_ _j_ [∣] [rank][(] _[s]_ _n,j_ [)][ ≤] _[k, m]_ _j_ [∈] _[M]_ [}] (5)


Based on these candidate nearest memories, we prompt the LLM to analyze potential connections
based on their potential common attributes. Formally, the link set of memory _m_ _n_ update like:


_L_ _i_ ← LLM( _m_ _n_ ∥ _M_ _[n]_ near [∥] _[P]_ _s_ 2 [)] (6)


Each generated link _l_ _i_ is structured as: _L_ _i_ = { _m_ _i_ _, ..., m_ _k_ } . By using embedding-based retrieval
as an initial filter, we enable efficient scalability while maintaining semantic relevance. A-M EM
can quickly identify potential connections even in large memory collections without exhaustive
comparison. More importantly, the LLM-driven analysis allows for nuanced understanding of
relationships that goes beyond simple similarity metrics. The language model can identify subtle
patterns, causal relationships, and conceptual connections that might not be apparent from embedding
similarity alone. We implements the Zettelkasten principle of flexible linking while leveraging
modern language models. The resulting network emerges organically from memory content and
context, enabling natural knowledge organization.


**3.3** **Memory Evolution**


After creating links for the new memory, A-M EM evolves the retrieved memories based on their
textual information and relationships with the new memory. For each memory _m_ _j_ in the nearest


4


neighbor set _M_ _[n]_ near [, the system determines whether to update its context, keywords, and tags. This]
evolution process can be formally expressed as:


_m_ [∗] _j_ [←] [LLM][(] _[m]_ _n_ [∥] _[M]_ _[n]_ near [\] _[ m]_ _j_ [∥] _[m]_ _j_ [∥] _[P]_ _s_ 3 [)] (7)


The evolved memory _m_ [∗] _j_ [then replaces the original memory] _[ m]_ _j_ [in the memory set] _[ M]_ [. This]
evolutionary approach enables continuous updates and new connections, mimicking human learning
processes. As the system processes more memories over time, it develops increasingly sophisticated
knowledge structures, discovering higher-order patterns and concepts across multiple memories.
This creates a foundation for autonomous memory learning where knowledge organization becomes
progressively richer through the ongoing interaction between new experiences and existing memories.


**3.4** **Retrieve Relative Memory**


In each interaction, our A-M EM performs context-aware memory retrieval to provide the agent with
relevant historical information. Given a query text _q_ from the current interaction, we first compute its
dense vector representation using the same text encoder used for memory notes:


_e_ _q_ = _f_ enc ( _q_ ) (8)


The system then computes similarity scores between the query embedding and all existing memory
notes in _M_ using cosine similarity:


_e_ _q_ ⋅ _e_ _i_
_s_ _q,i_ = (9)
∣ _e_ _q_ ∣∣ _e_ _i_ ∣ _[,]_ [ where] _[ e]_ _[i]_ [ ∈] _[m]_ _[i]_ _[,]_ [ ∀] _[m]_ _[i]_ [ ∈] _[M]_


Then we retrieve the k most relevant memories from the historical memory storage to construct a
contextually appropriate prompt.


_M_ retrieved = { _m_ _i_ ∣rank( _s_ _q,i_ ) ≤ _k, m_ _i_ ∈ _M_ } (10)


These retrieved memories provide relevant historical context that helps the agent better understand
and respond to the current interaction. The retrieved context enriches the agent’s reasoning process
by connecting the current interaction with related past experiences stored in the memory system.


**4** **Experiment**


**4.1** **Dataset and Evaluation**


To evaluate the effectiveness of instruction-aware recommendation in long-term conversations,
we utilize the LoCoMo dataset [ 22 ], which contains significantly longer dialogues compared to
existing conversational datasets [ 36, 13 ]. While previous datasets contain dialogues with around
1K tokens over 4-5 sessions, LoCoMo features much longer conversations averaging 9K tokens
spanning up to 35 sessions, making it particularly suitable for evaluating models’ ability to handle
long-range dependencies and maintain consistency over extended conversations. The LoCoMo
dataset comprises diverse question types designed to comprehensively evaluate different aspects
of model understanding: (1) single-hop questions answerable from a single session; (2) multihop questions requiring information synthesis across sessions; (3) temporal reasoning questions
testing understanding of time-related information; (4) open-domain knowledge questions requiring
integration of conversation context with external knowledge; and (5) adversarial questions assessing
models’ ability to identify unanswerable queries. In total, LoCoMo contains 7,512 question-answer
pairs across these categories. Besides, we use a new dataset, named DialSim [ 16 ], to evaluate
the effectiveness of our memory system. It is question-answering dataset derived from long-term
multi-party dialogues. The dataset is derived from popular TV shows (Friends, The Big Bang Theory,
and The Office), covering 1,300 sessions spanning five years, containing approximately 350,000
tokens, and including more than 1,000 questions per session from refined fan quiz website questions
and complex questions generated from temporal knowledge graphs.


For comparison baselines, we compare to **LoCoMo** [ 22 ], **ReadAgent** [ 17 ], **MemoryBank** [ 39 ] and
**MemGPT** [ 25 ]. The detailed introduction of baselines can be found in Appendix A.1 For evaluation,
we employ two primary metrics: the F1 score to assess answer accuracy by balancing precision
and recall, and BLEU-1 [ 26 ] to evaluate generated response quality by measuring word overlap


5


**Table 1:** Experimental results on LoCoMo dataset of QA tasks across five categories (Multi Hop, Temporal,
Open Domain, Single Hop, and Adversial) using different methods. Results are reported in F1 and BLEU-1
(%) scores. The best performance is marked in bold, and our proposed method A-M EM (highlighted in gray)
demonstrates competitive performance across six foundation language models.







|Model Method|Col2|Category|Col4|Col5|Col6|Col7|Average|Col9|
|---|---|---|---|---|---|---|---|---|
|**Model**<br>**Method**|**Model**<br>**Method**|~~**Multi Hop**~~<br>**F1**<br>**BLEU**|~~**Temporal**~~<br>**F1**<br>**BLEU**|~~**Open Domain**~~<br>**F1**<br>**BLEU**|~~**Single Hop**~~<br>**F1**<br>**BLEU**|~~**Adversial**~~<br>**F1**<br>**BLEU**|~~**Ranking**~~<br>**F1**<br>**BLEU**|~~**Token**~~<br>**Length**|
|**GPT**<br>**4o-mini**<br>**4o**|LOCOMO<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|25.02<br>19.75<br>9.15<br>6.48<br>5.00<br>4.77<br>26.65<br>17.72<br>**27.02**<br>**20.09**|18.41<br>14.77<br>12.60<br>8.87<br>9.68<br>6.99<br>25.52<br>19.44<br>**45.85**<br>**36.67**|12.04<br>11.16<br>5.31<br>5.12<br>5.56<br>5.94<br>9.15<br>7.44<br>**12.14**<br>**12.00**|40.36<br>29.05<br>9.67<br>7.66<br>6.61<br>5.16<br>41.04<br>34.34<br>**44.65**<br>**37.06**|**69.23**<br>**68.75**<br>9.81<br>9.02<br>7.36<br>6.48<br>43.29<br>42.73<br>50.03<br>49.47|2.4<br>2.4<br>4.2<br>4.2<br>4.8<br>4.8<br>2.4<br>2.4<br>**1.2**<br>**1.2**|16,910<br>643<br>432<br>16,977<br>2,520|
|**GPT**<br>**4o-mini**<br>**4o**|~~L~~O~~C~~O~~M~~O<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|~~28.00~~<br>~~18.47~~<br>14.61<br>9.95<br>6.49<br>4.69<br>30.36<br>22.83<br>**32.86**<br>**23.76**|~~9.09~~<br>~~5.78~~<br>4.16<br>3.19<br>2.47<br>2.43<br>17.29<br>13.18<br>**39.41**<br>**31.23**|~~16.47~~<br>~~14.80~~<br>8.84<br>8.37<br>6.43<br>5.30<br>12.24<br>11.87<br>**17.10**<br>**15.84**|~~**61.56**~~<br>~~**54.19**~~<br>12.46<br>10.29<br>8.28<br>7.10<br>60.16<br>53.35<br>48.43<br>42.97|~~**52.61**~~<br>~~**51.13**~~<br>6.81<br>6.13<br>4.42<br>3.67<br>34.96<br>34.25<br>36.35<br>35.53|~~2.0~~<br>~~2.0~~<br>4.0<br>4.0<br>5.0<br>5.0<br>2.4<br>2.4<br>**1.6**<br>**1.6**|~~16,910~~<br>805<br>569<br>16,987<br>1,216|
|**Qwen2.5**<br>**1.5b**<br>**3b**|LOCOMO<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|9.05<br>6.55<br>6.61<br>4.93<br>11.14<br>8.25<br>10.44<br>7.61<br>**18.23**<br>**11.94**|4.25<br>4.04<br>2.55<br>2.51<br>4.46<br>2.87<br>4.21<br>3.89<br>**24.32**<br>**19.74**|9.91<br>8.50<br>5.31<br>12.24<br>8.05<br>6.21<br>13.42<br>11.64<br>**16.48**<br>**14.31**|11.15<br>8.67<br>10.13<br>7.54<br>13.42<br>11.01<br>9.56<br>7.34<br>**23.63**<br>**19.23**|40.38<br>40.23<br>5.42<br>27.32<br>36.76<br>34.00<br>31.51<br>28.90<br>**46.00**<br>**43.26**|3.4<br>3.4<br>4.6<br>4.6<br>2.6<br>2.6<br>3.4<br>3.4<br>**1.0**<br>**1.0**|16,910<br>752<br>284<br>16,953<br>1,300|
|**Qwen2.5**<br>**1.5b**<br>**3b**|~~L~~O~~C~~O~~M~~O<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|~~4.61~~<br>~~4.29~~<br>2.47<br>1.78<br>3.60<br>3.39<br>5.07<br>4.31<br>**12.57**<br>**9.01**|~~3.11~~<br>~~2.71~~<br>3.01<br>3.01<br>1.72<br>1.97<br>2.94<br>2.95<br>**27.59**<br>**25.07**|~~4.55~~<br>~~5.97~~<br>5.57<br>5.22<br>6.63<br>6.58<br>7.04<br>7.10<br>**7.12**<br>**7.28**|~~7.03~~<br>~~5.69~~<br>3.25<br>2.51<br>4.11<br>3.32<br>7.26<br>5.52<br>**17.23**<br>**13.12**|~~16.95~~<br>~~14.81~~<br>15.78<br>14.01<br>13.07<br>10.30<br>14.47<br>12.39<br>**27.91**<br>**25.15**|~~3.2~~<br>~~3.2~~<br>4.2<br>4.2<br>4.2<br>4.2<br>2.4<br>2.4<br>**1.0**<br>**1.0**|~~16,910~~<br>776<br>298<br>16,961<br>1,137|
|**Llama 3.2**<br>**1b**<br>**3b**|LOCOMO<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|11.25<br>9.18<br>5.96<br>5.12<br>13.18<br>10.03<br>9.19<br>6.96<br>**19.06**<br>**11.71**|7.38<br>6.82<br>1.93<br>2.30<br>7.61<br>6.27<br>4.02<br>4.79<br>**17.80**<br>**10.28**|11.90<br>10.38<br>12.46<br>11.17<br>15.78<br>12.94<br>11.14<br>8.24<br>**17.55**<br>**14.67**|12.86<br>10.50<br>7.75<br>6.03<br>17.30<br>14.03<br>10.16<br>7.68<br>**28.51**<br>**24.13**|51.89<br>48.27<br>44.64<br>40.15<br>52.61<br>47.53<br>49.75<br>45.11<br>**58.81**<br>**54.28**|3.4<br>3.4<br>4.6<br>4.6<br>2.0<br>2.0<br>4.0<br>4.0<br>**1.0**<br>**1.0**|16,910<br>665<br>274<br>16,950<br>1,376|
|**Llama 3.2**<br>**1b**<br>**3b**|~~L~~O~~C~~O~~M~~O<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|~~6.88~~<br>~~5.77~~<br>2.47<br>1.78<br>6.19<br>4.47<br>5.32<br>3.99<br>**17.44**<br>**11.74**|~~4.37~~<br>~~4.40~~<br>3.01<br>3.01<br>3.49<br>3.13<br>2.68<br>2.72<br>**26.38**<br>**19.50**|~~10.65~~<br>~~9.29~~<br>5.57<br>5.22<br>4.07<br>4.57<br>5.64<br>5.54<br>**12.53**<br>**11.83**|~~8.37~~<br>~~6.93~~<br>3.25<br>2.51<br>7.61<br>6.03<br>4.32<br>3.51<br>**28.14**<br>**23.87**|~~30.25~~<br>~~28.46~~<br>15.78<br>14.01<br>18.65<br>17.05<br>21.45<br>19.37<br>**42.04**<br>**40.60**|~~2.8~~<br>~~2.8~~<br>4.2<br>4.2<br>3.2<br>3.2<br>3.8<br>3.8<br>**1.0**<br>**1.0**|~~16,910~~<br>461<br>263<br>16,956<br>1,126|


with ground truth responses. Also, we report the average token length for answering one question.
Besides reporting experiment results with four additional metrics (ROUGE-L, ROUGE-2, METEOR,
and SBERT Similarity), we also present experimental outcomes using different foundation models
including DeepSeek-R1-32B [ 11 ], Claude 3.0 Haiku [ 2 ], and Claude 3.5 Haiku [ 3 ] in Appendix A.3.


**4.2** **Implementation Details**


For all baselines and our proposed method, we maintain consistency by employing identical system
prompts as detailed in Appendix B. The deployment of Qwen-1.5B/3B and Llama 3.2 1B/3B models
is accomplished through local instantiation using Ollama [1], with LiteLLM [2] managing structured
output generation. For GPT models, we utilize the official structured output API. In our memory
retrieval process, we primarily employ _k_ =10 for top- _k_ memory selection to maintain computational
efficiency, while adjusting this parameter for specific categories to optimize performance. The
detailed configurations of _k_ can be found in Appendix A.5. For text embedding, we implement the
all-minilm-l6-v2 model across all experiments.


**4.3** **Empricial Results**


**Performance Analysis.** In our empirical evaluation, we compared A-M EM with four competitive
baselines including LoCoMo [ 22 ], ReadAgent [ 17 ], MemoryBank [ 39 ], and MemGPT [ 25 ] on
the LoCoMo dataset. For non-GPT foundation models, our A-M EM consistently outperforms all
baselines across different categories, demonstrating the effectiveness of our agentic memory approach.
For GPT-based models, while LoCoMo and MemGPT show strong performance in certain categories
like Open Domain and Adversial tasks due to their robust pre-trained knowledge in simple fact
retrieval, our A-M EM demonstrates superior performance in Multi-Hop tasks achieves at least two
times better performance that require complex reasoning chains. In addition to experiments on
the LoCoMo dataset, we also compare our method on the DialSim dataset against LoCoMo and
MemGPT. A-M EM consistently outperforms all baselines across evaluation metrics, achieving an F1


1 `[https://github.com/ollama/ollama](https://github.com/ollama/ollama)`
2 `[https://github.com/BerriAI/litellm](https://github.com/BerriAI/litellm)`


6


**Table 2:** Comparison of different memory mechanisms across multiple evaluation metrics on DialSim [ 16 ].
Higher scores indicate better performance, with A-M EM showing superior results across all metrics.

|Method|F1 BLEU-1 ROUGE-L ROUGE-2 METEOR SBERT Similarity|
|---|---|
|LoCoMo<br>MemGPT<br>**A-MEM**|2.55<br>3.13<br>2.75<br>0.90<br>1.64<br>15.76<br>1.18<br>1.07<br>0.96<br>0.42<br>0.95<br>8.54<br>**3.45**<br>**3.37**<br>**3.54**<br>**3.60**<br>**2.05**<br>**19.51**|



**Table 3:** An ablation study was conducted to evaluate our proposed method against the GPT-4o-mini base model.
The notation ’w/o’ indicates experiments where specific modules were removed. The abbreviations LG and ME
denote the link generation module and memory evolution module, respectively.

|Col1|Col2|Col3|Category|Col5|Col6|
|---|---|---|---|---|---|
|~~**Method**~~|**Multi Hop**<br>**F1**<br>**BLEU-1**|**Temporal**<br>**F1**<br>**BLEU-1**|**Open Domain**<br>**F1**<br>**BLEU-1**|**Single Hop**<br>**F1**<br>**BLEU-1**|**Adversial**<br>**F1**<br>**BLEU-1**|
|w/o LG & ME<br>w/o ME<br>**A-MEM**|9.65<br>7.09<br>21.35<br>15.13<br>**27.02**<br>**20.09**|24.55<br>19.48<br>31.24<br>27.31<br>**45.85**<br>**36.67**|7.77<br>6.70<br>10.13<br>10.85<br>**12.14**<br>**12.00**|13.28<br>10.30<br>39.17<br>34.70<br>**44.65**<br>**37.06**|15.32<br>18.02<br>44.16<br>45.33<br>**50.03**<br>**49.47**|



score of 3.45 (a 35% improvement over LoCoMo’s 2.55 and 192% higher than MemGPT’s 1.18). The
effectiveness of A-M EM stems from its novel agentic memory architecture that enables dynamic and
structured memory management. Unlike traditional approaches that use static memory operations,
our system creates interconnected memory networks through atomic notes with rich contextual
descriptions, enabling more effective multi-hop reasoning. The system’s ability to dynamically
establish connections between memories based on shared attributes and continuously update existing
memory descriptions with new contextual information allows it to better capture and utilize the
relationships between different pieces of information.


**Cost-Efficiency Analysis.** A-M EM demonstrates significant computational and cost efficiency alongside strong performance. The system requires approximately 1,200 tokens per memory operation,
achieving an 85-93% reduction in token usage compared to baseline methods (LoCoMo and MemGPT
with 16,900 tokens) through our selective top-k retrieval mechanism. This substantial token reduction directly translates to lower operational costs, with each memory operation costing less than
$0.0003 when using commercial API services—making large-scale deployments economically viable.
Processing times average 5.4 seconds using GPT-4o-mini and only 1.1 seconds with locally-hosted
Llama 3.2 1B on a single GPU. Despite requiring multiple LLM calls during memory processing,
A-M EM maintains this cost-effective resource utilization while consistently outperforming baseline
approaches across all foundation models tested, particularly doubling performance on complex
multi-hop reasoning tasks. This balance of low computational cost and superior reasoning capability
highlights A-M EM ’s practical advantage for deployment in the real world.


**4.4** **Ablation Study**


To evaluate the effectiveness of the Link Generation (LG) and Memory Evolution (ME) modules, we
conduct the ablation study by systematically removing key components of our model. When both LG
and ME modules are removed, the system exhibits substantial performance degradation, particularly
in Multi Hop reasoning and Open Domain tasks. The system with only LG active (w/o ME) shows
intermediate performance levels, maintaining significantly better results than the version without
both modules, which demonstrates the fundamental importance of link generation in establishing
memory connections. Our full model, A-M EM, consistently achieves the best performance across
all evaluation categories, with particularly strong results in complex reasoning tasks. These results
reveal that while the link generation module serves as a critical foundation for memory organization,
the memory evolution module provides essential refinements to the memory structure. The ablation
study validates our architectural design choices and highlights the complementary nature of these
two modules in creating an effective memory system.


**4.5** **Hyperparameter Analysis**


We conducted extensive experiments to analyze the impact of the memory retrieval parameter k,
which controls the number of relevant memories retrieved for each interaction. As shown in Figure 3,
we evaluated performance across different k values (10, 20, 30, 40, 50) on five categories of tasks
using GPT-4o-mini as our base model. The results reveal an interesting pattern: while increasing
k generally leads to improved performance, this improvement gradually plateaus and sometimes
slightly decreases at higher values. This trend is particularly evident in Multi Hop and Open Domain


7


27.5


25.0


22.5


20.0


17.5


15.0


12.5



























14













47.5

























context retrieval for optimal performance.

|Col1|BLEU2-51.8|Col3|7|Col5|2|0.19|Col8|Col9|Col10|Col11|Col12|45.0<br>42.5<br>40.0<br>37.5<br>35.0|Col14|Col15|Col16|Col17|Col18|Col19|B<br>43.60|LE4U5-.10|8|Col23|Col24|Col25|Col26|Col27|Col28|Col29|Col30|12<br>10<br>8<br>6<br>50.0439|Col32|Col33|Col34|Col35|Col36|Col37|BLEU-1<br>10.2|Col39|Col40|12.2<br>9 1<br>9.61|Col42|Col43|4<br>0.5710.3|Col45|Col46|12.11<br>5<br>9.76|Col48|Col49|42.00|Col51|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|19.9<br>|1<br>|~~1~~|~~9.45~~|~~9.45~~||||20.09|20.09|2|0.15|0.15|0.15|0.15|0.15|0.15|0.15|0.15||3|5.85|5.85|~~3~~|~~6.44~~<br>|~~6.44~~<br>|~~36.67~~|~~36.67~~|3|5.76|5.76|5.76|5.76|5.76|5.76|5.76|~~7.38~~<br>|7.03|7.03|||||||||||||
|~~1~~|~~4.36~~||||||||||||||||||35.5||||||||||||||||||||||||||||||||
|1|0<br>**(**|2<br>**a)**|0<br>M|0<br>M|3<br> va<br>lt|0<br>lue<br>i|0<br>lue<br>i|0<br>p|~~F~~|5<br>~~1~~|0|0|0|0|0|0|0|0|10<br>**(**<br>44.55|10<br>**(**<br>44.55|0<br> T<br>cr<br>rf<br>d<br>|0<br> T<br>cr<br>rf<br>d<br>|3<br> va<br>m<br>ss<br>rm<br>-o<br>|0<br>lue<br>p<br> d<br>a<br>f<br>|0<br>lue<br>p<br> d<br>a<br>f<br>|0<br>al|~~F~~|5<br>~~1~~|0|0|0|0|0|0|0|1<br><br><br>~~.47~~|0<br>**(c**<br>|**)** <br>|2<br>O|0<br>p|0<br>p|3<br> va<br>n|0<br>lue<br>D|0<br>lue<br>D|4<br>m|0<br>a|0<br>a|5<br>|0|0|
|1|0<br>**(**|2<br>**a)**|0<br>M|0<br>M|3<br> va<br>lt|0<br>lue<br>i|0<br>lue<br>i||B|LE|U-1||||41.5|41.5|41.5|5|||||||||B|LE|U-1|~~43.~~|~~43.~~|~~43.~~|~~86~~<br>|~~86~~<br>|||7.7<br>4|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|6<br>7.24|
|1|0<br>**(**|2<br>**a)**|0<br>M|0<br>M|3<br> va<br>lt|0<br>lue<br>i|0<br>lue<br>i||~~33.6~~|~~33.6~~|~~33.6~~|~~7~~<br>38.1|~~7~~<br>38.1|~~7~~<br>38.1|5|5|~~3~~|~~4.32~~|37.|37.|37.|37.|37.|37.|37.||||~~39.1~~<br>|~~1~~<br><br>~~8.35~~|~~1~~<br><br>~~8.35~~||43.19|43.19|||||||||||||||||
|1|0<br>**(**|2<br>**a)**|0<br>M|0<br>M|3<br> va<br>lt|0<br>lue<br>i|0<br>lue<br>i|31.1|5<br>|5<br>||||3|2.12|2.12|||||||||||||||||||||||||||||||||||
|1|0<br>**(**|2<br>**a)**|0<br>M|0<br>M|3<br> va<br>lt|0<br>lue<br>i|0<br>lue<br>i|2|5.43|5.43|2|8.31|8.31|||||||||||||30.2<br>~~2~~|9<br>~~9.4~~|~~9~~|||||||||||||||||||||||
|1|0<br>**(**|2<br>**a)**|0<br>M|0<br>M|3<br> va<br>lt|0<br>lue<br>i|0<br>lue<br>i|2|5.43|5.43|2||||||||||||||||||||||||||||||||||||||||
|1|0<br>**(**|2<br>**a)**|0<br>M|0<br>M|3<br> va<br>lt|0<br>lue<br>i|0<br>lue<br>i||||||||||||||||||||||||||||||||||||||||||||
|1|0<br>**(**|2<br>**a)**|0<br>M|0<br>M|3<br> va<br>lt|0<br>lue<br>i|0<br>lue<br>i|1<br>y<br>es<br>res<br> c|0<br><br>re<br> g<br>h<br>o|0<br><br>re<br> g<br>h<br>o|2<br>**d)**<br>rie<br>n<br>ld<br>is|0<br> S<br>v<br>er<br>s,<br>te|0<br> S<br>v<br>er<br>s,<br>te|3<br> va<br>g<br> p<br>ly<br>u<br>t|0<br>lue<br>le<br>a<br> i<br>g<br>ac|0<br>lue<br>le<br>a<br> i<br>g<br>ac|4<br>H<br>m<br>p<br>es<br>o|0<br>op<br>e<br>ro<br>tin<br>ss|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|1<br>er<br>e<br>et<br>|0<br><br>e<br>b<br>w<br>te|**(e**<br>nt<br>y<br>e<br>|2<br>**)** <br> t<br> p<br>en<br>|0<br>A<br>as<br>ro<br> c<br>ie|k<br>d<br>k<br>v<br>o<br>s|v<br>v<br>c<br>i<br>n<br>,|30<br>alue<br>er<br>at<br>din<br>te<br> in|s<br>s<br>e<br>g<br>x<br>d|40<br>ari<br>go<br> r<br>t r<br>ic|al<br>rie<br>ich<br>ich<br>ati|5<br>s<br>e<br>n<br>n|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|0<br>w<br>r<br>e<br>g|
|1|0<br>**(**|2<br>**a)**|0<br>M|0<br>M|3<br> va<br>lt|0<br>lue<br>i|0<br>lue<br>i|1<br>y<br>es<br>res<br> c|0<br><br>re<br> g<br>h<br>o|0<br><br>re<br> g<br>h<br>o|2<br>**d)**<br>rie<br>n<br>ld<br>is|0<br> S<br>v<br>er<br>s,<br>te|0<br> S<br>v<br>er<br>s,<br>te|3<br> va<br>g<br> p<br>ly<br>u<br>t|0<br>lue<br>le<br>a<br> i<br>g<br>ac|0<br>lue<br>le<br>a<br> i<br>g<br>ac|4<br>H<br>m<br>p<br>es<br>o|0<br>op<br>e<br>ro<br>tin<br>ss|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|50<br><br>ter k<br>ve<br>g a<br>|ca|ca|g|o|o|o|o|o|o|o|o|o|o|o|o|o|o|o|o|o|o|o|o|o|o|



**Table 4:** Comparison of memory usage and retrieval time across different memory methods and scales.






|Memory Size|Method|Memory Usage (MB)|Retrieval Time (µs)|
|---|---|---|---|
|1,000|A-MEM<br>MemoryBank [39]<br>ReadAgent [17]|1.46<br>1.46<br>1.46|0.31 ± 0.30<br>0.24 ± 0.20<br>43.62 ± 8.47|
|10,000|A-MEM<br>MemoryBank [39]<br>ReadAgent [17]|14.65<br>14.65<br>14.65|0.38 ± 0.25<br>0.26 ± 0.13<br>484.45 ± 93.86|
|100,000|A-MEM<br>MemoryBank [39]<br>ReadAgent [17]|146.48<br>146.48<br>146.48|1.40 ± 0.49<br>0.78 ± 0.26<br>6,682.22 ± 111.63|
|1,000,000|A-MEM<br>MemoryBank [39]<br>ReadAgent [17]|1464.84<br>1464.84<br>1464.84|3.70 ± 0.74<br>1.91 ± 0.31<br>120,069.68 ± 1,673.39|



tasks. The observation suggests a delicate balance in memory retrieval - while larger k values provide
richer historical context for reasoning, they may also introduce noise and challenge the model’s
capacity to process longer sequences effectively. Our analysis indicates that moderate k values strike
an optimal balance between context richness and information processing efficiency.


**4.6** **Scaling Analysis**


To evaluate storage costs with accumulating memory, we examined the relationship between storage
size and retrieval time across our A-M EM system and two baseline approaches: MemoryBank [ 39 ]
and ReadAgent [ 17 ]. We evaluated these three memory systems with identical memory content
across four scale points, increasing the number of entries by a factor of 10 at each step (from 1,000 to
10,000, 100,000, and finally 1,000,000 entries). The experimental results reveal key insights about
our A-M EM system’s scaling properties: In terms of space complexity, all three systems exhibit
identical linear memory usage scaling ( _O_ ( _N_ ) ), as expected for vector-based retrieval systems. This
confirms that A-M EM introduces no additional storage overhead compared to baseline approaches.
For retrieval time, A-M EM demonstrates excellent efficiency with minimal increases as memory size
grows. Even when scaling to 1 million memories, A-M EM ’s retrieval time increases only from 0.31 _µ_ s
to 3.70 _µ_ s, representing exceptional performance. While MemoryBank shows slightly faster retrieval
times, A-M EM maintains comparable performance while providing richer memory representations
and functionality. Based on our space complexity and retrieval time analysis, we conclude that
A-M EM ’s retrieval mechanisms maintain excellent efficiency even at large scales. The minimal
growth in retrieval time across memory sizes addresses concerns about efficiency in large-scale
memory systems, demonstrating that A-M EM provides a highly scalable solution for long-term
conversation management. This unique combination of efficiency, scalability, and enhanced memory
capabilities positions A-M EM as a significant advancement in building powerful and long-term
memory mechanism for LLM Agents.


8


20


10


0


−10


−20



−20 −10 0 10 20



20


10


0


−10


−20


−20 −10 0 10 20



**(a)** Dialogue 1 **(b)** Dialogue 2

**Figure 4:** T-SNE Visualization of Memory Embeddings Showing More Organized Distribution with A-M EM
(blue) Compared to Base Memory (red) Across Different Dialogues. Base Memory represents A-M EM without
link generation and memory evolution.


**4.7** **Memory Analysis**


We present the t-SNE visualization in Figure 4 of memory embeddings to demonstrate the structural
advantages of our agentic memory system. Analyzing two dialogues sampled from long-term
conversations in LoCoMo [ 22 ], we observe that A-M EM (shown in blue) consistently exhibits
more coherent clustering patterns compared to the baseline system (shown in red). This structural
organization is particularly evident in Dialogue 2, where well-defined clusters emerge in the central
region, providing empirical evidence for the effectiveness of our memory evolution mechanism and
contextual description generation. In contrast, the baseline memory embeddings display a more
dispersed distribution, demonstrating that memories lack structural organization without our link
generation and memory evolution components. These visualization results validate that A-M EM
can autonomously maintain meaningful memory structures through dynamic evolution and linking
mechanisms. More results can be seen in Appendix A.4.


**5** **Conclusions**


In this work, we introduced A-M EM, a novel agentic memory system that enables LLM agents to
dynamically organize and evolve their memories without relying on predefined structures. Drawing
inspiration from the Zettelkasten method, our system creates an interconnected knowledge network
through dynamic indexing and linking mechanisms that adapt to diverse real-world tasks. The system’s core architecture features autonomous generation of contextual descriptions for new memories
and intelligent establishment of connections with existing memories based on shared attributes.
Furthermore, our approach enables continuous evolution of historical memories by incorporating
new experiences and developing higher-order attributes through ongoing interactions. Through
extensive empirical evaluation across six foundation models, we demonstrated that A-M EM achieves
superior performance compared to existing state-of-the-art baselines in long-term conversational
tasks. Visualization analysis further validates the effectiveness of our memory organization approach.
These results suggest that agentic memory systems can significantly enhance LLM agents’ ability to
utilize long-term knowledge in complex environments.


**6** **Limitations**


While our agentic memory system achieves promising results, we acknowledge several areas for
potential future exploration. First, although our system dynamically organizes memories, the quality
of these organizations may still be influenced by the inherent capabilities of the underlying language
models. Different LLMs might generate slightly different contextual descriptions or establish varying
connections between memories. Additionally, while our current implementation focuses on text-based
interactions, future work could explore extending the system to handle multimodal information, such
as images or audio, which could provide richer contextual representations.


9


**References**


[1] Sönke Ahrens. _How to Take Smart Notes: One Simple Technique to Boost Writing, Learning_
_and Thinking_ . Amazon, 2017. Second Edition.


[2] Anthropic. The claude 3 model family: Opus, sonnet, haiku. Anthropic, Mar 2024. Accessed
May 2025.


[3] Anthropic. Claude 3.5 sonnet model card addendum. Technical report, Anthropic, 2025.
Accessed May 2025.


[4] Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, and Hannaneh Hajishirzi. Self-rag: Learning
to retrieve, generate, and critique through self-reflection. _arXiv preprint arXiv:2310.11511_,
2023.


[5] Satanjeev Banerjee and Alon Lavie. Meteor: An automatic metric for mt evaluation with
improved correlation with human judgments. In _Proceedings of the acl workshop on intrinsic_
_and extrinsic evaluation measures for machine translation and/or summarization_, pages 65–72,
2005.


[6] Sebastian Borgeaud, Arthur Mensch, Jordan Hoffmann, Trevor Cai, Eliza Rutherford, Katie
Millican, George Bm Van Den Driessche, Jean-Baptiste Lespiau, Bogdan Damoc, Aidan Clark,
et al. Improving language models by retrieving from trillions of tokens. In _International_
_conference on machine learning_, pages 2206–2240. PMLR, 2022.


[7] Xiang Deng, Yu Gu, Boyuan Zheng, Shijie Chen, Sam Stevens, Boshi Wang, Huan Sun, and
Yu Su. Mind2web: Towards a generalist agent for the web. _Advances in Neural Information_
_Processing Systems_, 36:28091–28114, 2023.


[8] Khant Dev and Singh Taranjeet. mem0: The memory layer for ai agents. `[https://github.](https://github.com/mem0ai/mem0)`
`[com/mem0ai/mem0](https://github.com/mem0ai/mem0)`, 2024.


[9] Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody, Steven
Truitt, and Jonathan Larson. From local to global: A graph rag approach to query-focused
summarization. _arXiv preprint arXiv:2404.16130_, 2024.


[10] Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi Dai, Jiawei Sun,
and Haofen Wang. Retrieval-augmented generation for large language models: A survey. _arXiv_
_preprint arXiv:2312.10997_, 2023.


[11] Daya Guo, Dejian Yang, Haowei Zhang, Junxiao Song, Ruoyu Zhang, Runxin Xu, Qihao Zhu,
Shirong Ma, Peiyi Wang, Xiao Bi, et al. Deepseek-r1: Incentivizing reasoning capability in
llms via reinforcement learning. _arXiv preprint arXiv:2501.12948_, 2025.


[12] I. Ilin. Advanced rag techniques: An illustrated overview, 2023.


[13] Jihyoung Jang, Minseong Boo, and Hyounghun Kim. Conversation chronicles: Towards
diverse temporal and relational dynamics in multi-session conversations. _arXiv preprint_
_arXiv:2310.13420_, 2023.


[14] Zhengbao Jiang, Frank F Xu, Luyu Gao, Zhiqing Sun, Qian Liu, Jane Dwivedi-Yu, Yiming
Yang, Jamie Callan, and Graham Neubig. Active retrieval augmented generation. _arXiv preprint_
_arXiv:2305.06983_, 2023.


[15] David Kadavy. _Digital Zettelkasten: Principles, Methods, & Examples_ . Google Books, May
2021.


[16] Jiho Kim, Woosog Chay, Hyeonji Hwang, Daeun Kyung, Hyunseung Chung, Eunbyeol Cho,
Yohan Jo, and Edward Choi. Dialsim: A real-time simulator for evaluating long-term multi-party
dialogue understanding of conversational agents. _arXiv preprint arXiv:2406.13144_, 2024.


[17] Kuang-Huei Lee, Xinyun Chen, Hiroki Furuta, John Canny, and Ian Fischer. A human-inspired
reading agent with gist memory of very long contexts. _arXiv preprint arXiv:2402.09727_, 2024.


10


[18] Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman
Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, et al. Retrieval-augmented
generation for knowledge-intensive nlp tasks. _Advances in Neural Information Processing_
_Systems_, 33:9459–9474, 2020.


[19] Chin-Yew Lin. Rouge: A package for automatic evaluation of summaries. In _Text summarization_
_branches out_, pages 74–81, 2004.


[20] Xi Victoria Lin, Xilun Chen, Mingda Chen, Weijia Shi, Maria Lomeli, Rich James, Pedro
Rodriguez, Jacob Kahn, Gergely Szilvasy, Mike Lewis, et al. Ra-dit: Retrieval-augmented dual
instruction tuning. _arXiv preprint arXiv:2310.01352_, 2023.


[21] Zhiwei Liu, Weiran Yao, Jianguo Zhang, Liangwei Yang, Zuxin Liu, Juntao Tan, Prafulla K
Choubey, Tian Lan, Jason Wu, Huan Wang, et al. Agentlite: A lightweight library for building
and advancing task-oriented llm agent system. _arXiv preprint arXiv:2402.15538_, 2024.


[22] Adyasha Maharana, Dong-Ho Lee, Sergey Tulyakov, Mohit Bansal, Francesco Barbieri, and
Yuwei Fang. Evaluating very long-term conversational memory of llm agents. _arXiv preprint_
_arXiv:2402.17753_, 2024.


[23] Kai Mei, Zelong Li, Shuyuan Xu, Ruosong Ye, Yingqiang Ge, and Yongfeng Zhang. Aios: Llm
agent operating system. _arXiv e-prints, pp. arXiv–2403_, 2024.


[24] Ali Modarressi, Ayyoob Imani, Mohsen Fayyaz, and Hinrich Schütze. Ret-llm: Towards a
general read-write memory for large language models. _arXiv preprint arXiv:2305.14322_, 2023.


[25] Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G Patil, Ion Stoica,
and Joseph E Gonzalez. Memgpt: Towards llms as operating systems. _arXiv preprint_
_arXiv:2310.08560_, 2023.


[26] Kishore Papineni, Salim Roukos, Todd Ward, and Wei-Jing Zhu. Bleu: a method for automatic
evaluation of machine translation. In _Proceedings of the 40th annual meeting of the Association_
_for Computational Linguistics_, pages 311–318, 2002.


[27] Nils Reimers and Iryna Gurevych. Sentence-bert: Sentence embeddings using siamese bertnetworks. In _Proceedings of the 2019 Conference on Empirical Methods in Natural Language_
_Processing_ . Association for Computational Linguistics, 11 2019.


[28] Aymeric Roucher, Albert Villanova del Moral, Thomas Wolf, Leandro von Werra, and Erik
Kaunismäki. ‘smolagents‘: a smol library to build great agentic systems. `[https://github.](https://github.com/huggingface/smolagents)`
`[com/huggingface/smolagents](https://github.com/huggingface/smolagents)`, 2025.


[29] Zhihong Shao, Yeyun Gong, Yelong Shen, Minlie Huang, Nan Duan, and Weizhu Chen.
Enhancing retrieval-augmented large language models with iterative retrieval-generation synergy.
_arXiv preprint arXiv:2305.15294_, 2023.


[30] Zeru Shi, Kai Mei, Mingyu Jin, Yongye Su, Chaoji Zuo, Wenyue Hua, Wujiang Xu, Yujie Ren,
Zirui Liu, Mengnan Du, et al. From commands to prompts: Llm-based semantic file system for
aios. _arXiv preprint arXiv:2410.11843_, 2024.


[31] Harsh Trivedi, Niranjan Balasubramanian, Tushar Khot, and Ashish Sabharwal. Interleaving
retrieval with chain-of-thought reasoning for knowledge-intensive multi-step questions. _arXiv_
_preprint arXiv:2212.10509_, 2022.


[32] Bing Wang, Xinnian Liang, Jian Yang, Hui Huang, Shuangzhi Wu, Peihao Wu, Lu Lu, Zejun
Ma, and Zhoujun Li. Enhancing large language model with self-controlled memory framework.
_arXiv preprint arXiv:2304.13343_, 2023.


[33] Xingyao Wang, Boxuan Li, Yufan Song, Frank F Xu, Xiangru Tang, Mingchen Zhuge, Jiayi
Pan, Yueqi Song, Bowen Li, Jaskirat Singh, et al. Openhands: An open platform for ai software
developers as generalist agents. _arXiv preprint arXiv:2407.16741_, 2024.


[34] Zhiruo Wang, Jun Araki, Zhengbao Jiang, Md Rizwan Parvez, and Graham Neubig. Learning
to filter context for retrieval-augmented generation. _arXiv preprint arXiv:2311.08377_, 2023.


11


[35] Lilian Weng. Llm-powered autonomous agents. _lilianweng.github.io_, Jun 2023.


[36] J Xu. Beyond goldfish memory: Long-term open-domain conversation. _arXiv preprint_
_arXiv:2107.07567_, 2021.


[37] Wenhao Yu, Hongming Zhang, Xiaoman Pan, Kaixin Ma, Hongwei Wang, and Dong Yu.
Chain-of-note: Enhancing robustness in retrieval-augmented language models. _arXiv preprint_
_arXiv:2311.09210_, 2023.


[38] Zichun Yu, Chenyan Xiong, Shi Yu, and Zhiyuan Liu. Augmentation-adapted retriever improves
generalization of language models as generic plug-in. _arXiv preprint arXiv:2305.17331_, 2023.


[39] Wanjun Zhong, Lianghong Guo, Qiqi Gao, He Ye, and Yanlin Wang. Memorybank: Enhancing
large language models with long-term memory. In _Proceedings of the AAAI Conference on_
_Artificial Intelligence_, volume 38, pages 19724–19731, 2024.


12


**Contents**


**1** **Introduction** **1**


**2** **Related Work** **2**


2.1 Memory for LLM Agents . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2


2.2 Retrieval-Augmented Generation . . . . . . . . . . . . . . . . . . . . . . . . . . . 3


**3** **Methodolodgy** **3**


3.1 Note Construction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4


3.2 Link Generation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4


3.3 Memory Evolution . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4


3.4 Retrieve Relative Memory . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5


**4** **Experiment** **5**


4.1 Dataset and Evaluation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5


4.2 Implementation Details . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6


4.3 Empricial Results . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6


4.4 Ablation Study . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7


4.5 Hyperparameter Analysis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7


4.6 Scaling Analysis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8


4.7 Memory Analysis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9


**5** **Conclusions** **9**


**6** **Limitations** **9**


**A Experiment** **14**


A.1 Detailed Baselines Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14


A.2 Evaluation Metric . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14


A.3 Comparison Results . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15


A.4 Memory Analysis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16


A.5 Hyperparameters setting . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17


**B** **Prompt Templates and Examples** **19**


B.1 Prompt Template of Note Construction . . . . . . . . . . . . . . . . . . . . . . . . 19


B.2 Prompt Template of Link Generation . . . . . . . . . . . . . . . . . . . . . . . . . 19


B.3 Prompt Template of Memory Evolution . . . . . . . . . . . . . . . . . . . . . . . 20


B.4 Examples of Q/A with A-M EM . . . . . . . . . . . . . . . . . . . . . . . . . . . . 21


13


**APPENDIX**


**A** **Experiment**


**A.1** **Detailed Baselines Introduction**


**LoCoMo** [ 22 ] takes a direct approach by leveraging foundation models without memory mechanisms
for question answering tasks. For each query, it incorporates the complete preceding conversation
and questions into the prompt, evaluating the model’s reasoning capabilities.


**ReadAgent** [ 17 ] tackles long-context document processing through a sophisticated three-step methodology: it begins with episode pagination to segment content into manageable chunks, followed by
memory gisting to distill each page into concise memory representations, and concludes with interactive look-up to retrieve pertinent information as needed.


**MemoryBank** [ 39 ] introduces an innovative memory management system that maintains and efficiently retrieves historical interactions. The system features a dynamic memory updating mechanism
based on the Ebbinghaus Forgetting Curve theory, which intelligently adjusts memory strength
according to time and significance. Additionally, it incorporates a user portrait building system that
progressively refines its understanding of user personality through continuous interaction analysis.


**MemGPT** [ 25 ] presents a novel virtual context management system drawing inspiration from
traditional operating systems’ memory hierarchies. The architecture implements a dual-tier structure:
a main context (analogous to RAM) that provides immediate access during LLM inference, and an
external context (analogous to disk storage) that maintains information beyond the fixed context
window.


**A.2** **Evaluation Metric**


The F1 score represents the harmonic mean of precision and recall, offering a balanced metric that
combines both measures into a single value. This metric is particularly valuable when we need to
balance between complete and accurate responses:



where



F1 = 2 ⋅ [p][recision][ ⋅] [recall] (11)

precision + recall


true positives
precision = (12)
true positives + false positives


true positives
recall = (13)
true positives + false negatives



In question-answering systems, the F1 score serves a crucial role in evaluating exact matches between
predicted and reference answers. This is especially important for span-based QA tasks, where systems
must identify precise text segments while maintaining comprehensive coverage of the answer.


BLEU-1 [ 26 ] provides a method for evaluating the precision of unigram matches between system
outputs and reference texts:



BLEU-1 = _BP_ ⋅ exp
(



1
∑ _w_ _n_ log _p_ _n_ (14)

_n_ =1 )



1
∑



where



if _c_             - _r_
_BP_ = (15)
{ _e_ [1] [1][−] _[r]_ [/] _[c]_ if _c_ ≤ _r_


_p_ _n_ = [∑] _[i]_ [ ∑] _[k]_ [min][(] _[h]_ _[ik]_ _[, m]_ _[ik]_ [)] (16)

∑ _i_ ∑ _k_ _h_ _ik_


14


Here, _c_ is candidate length, _r_ is reference length, _h_ _ik_ is the count of n-gram i in candidate k, and _m_ _ik_
is the maximum count in any reference. In QA, BLEU-1 evaluates the lexical precision of generated
answers, particularly useful for generative QA systems where exact matching might be too strict.


ROUGE-L [ 19 ] measures the longest common subsequence between the generated and reference

texts.

_[β]_ [2] [)] _[R]_ _[l]_ _[P]_ _[l]_
ROUGE-L = [(][1][ +] (17)

_R_ _l_ + _β_ [2] _P_ _l_

_R_ _l_ = [LCS][(] _[X][,][ Y]_ [)] (18)

∣ _X_ ∣


[)]
_P_ _l_ = [LCS][(] _[X][,][ Y]_ (19)

∣ _Y_ ∣


where _X_ is reference text, _Y_ is candidate text, and LCS is the Longest Common Subsequence.


ROUGE-2 [19] calculates the overlap of bigrams between the generated and reference texts.


∑ bigram∈ref min(Count ref (bigram) _,_ Count cand (bigram))
ROUGE-2 = (20)

∑ bigram∈ref Count ref (bigram)


Both ROUGE-L and ROUGE-2 are particularly useful for evaluating the fluency and coherence of
generated answers, with ROUGE-L focusing on sequence matching and ROUGE-2 on local word
order.


METEOR [ 5 ] computes a score based on aligned unigrams between the candidate and reference texts,
considering synonyms and paraphrases.


METEOR = _F_ mean ⋅ (1 − Penalty) (21)

_F_ mean = [10] _R_ + _[P]_ [ ⋅] 9 _P_ _[R]_ (22)

Penalty = 0 _._ 5 ⋅ ( [ch] ~~_m_~~ [)] [3] (23)

where _P_ is precision, _R_ is recall, ch is number of chunks, and _m_ is number of matched unigrams.
METEOR is valuable for QA evaluation as it considers semantic similarity beyond exact matching,
making it suitable for evaluating paraphrased answers.


SBERT Similarity [ 27 ] measures the semantic similarity between two texts using sentence embeddings.


SBERT_Similarity = cos(SBERT( _x_ ) _,_ SBERT( _y_ )) (24)


_a_ ⋅ _b_
cos( _a, b_ ) = (25)
∥ _a_ ∥∥ _b_ ∥

SBERT( _x_ ) represents the sentence embedding of text. SBERT Similarity is particularly useful for
evaluating semantic understanding in QA systems, as it can capture meaning similarities even when
the lexical overlap is low.


**A.3** **Comparison Results**


Our comprehensive evaluation using ROUGE-2, ROUGE-L, METEOR, and SBERT metrics demonstrates that A-M EM achieves superior performance while maintaining remarkable computational
efficiency. Through extensive empirical testing across various model sizes and task categories, we
have established A-M EM as a more effective approach compared to existing baselines, supported by
several compelling findings. In our analysis of non-GPT models, specifically Qwen2.5 and Llama 3.2,
A-M EM consistently outperforms all baseline approaches across all metrics. The Multi-Hop category
showcases particularly striking results, where Qwen2.5-15b with A-M EM achieves a ROUGE-L
score of 27.23, dramatically surpassing LoComo’s 4.68 and ReadAgent’s 2.81 - representing a nearly
six-fold improvement. This pattern of superiority extends consistently across METEOR and SBERT


15


**Table 5:** Experimental results on LoCoMo dataset of QA tasks across five categories (Multi Hop, Temporal,
Open Domain, Single Hop, and Adversial) using different methods. Results are reported in ROUGE-2 and
ROUGE-L scores, abbreviated to RGE-2 and RGE-L. The best performance is marked in bold, and our proposed
method A-M EM (highlighted in gray) demonstrates competitive performance across six foundation language
models.







|Model Method|Col2|Category|Col4|Col5|Col6|Col7|
|---|---|---|---|---|---|---|
|**Model**<br>**Method**|**Model**<br>**Method**|~~**Multi Hop**~~<br>**RGE-2**<br>**RGE-L**|~~**Temporal**~~<br>**RGE-2**<br>**RGE-L**|~~**Open Domain**~~<br>**RGE-2**<br>**RGE-L**|~~**Single Hop**~~<br>**RGE-2**<br>**RGE-L**|~~**Adversial**~~<br>**RGE-2**<br>**RGE-L**|
|**GPT**<br>**4o-mini**<br>**4o**|LOCOMO<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|9.64<br>23.92<br>2.47<br>9.45<br>1.18<br>5.43<br>10.58<br>25.60<br>**10.61**<br>**25.86**|2.01<br>18.09<br>0.95<br>13.12<br>0.52<br>9.64<br>4.76<br>25.22<br>**21.39**<br>**44.27**|3.40<br>11.58<br>0.55<br>5.76<br>0.97<br>5.77<br>0.76<br>9.14<br>**3.42**<br>**12.09**|26.48<br>40.20<br>2.99<br>9.92<br>1.64<br>6.63<br>28.44<br>42.24<br>**29.50**<br>**45.18**|**60.46**<br>**69.59**<br>6.66<br>9.79<br>4.55<br>7.35<br>36.62<br>43.75<br>42.62<br>50.04|
|**GPT**<br>**4o-mini**<br>**4o**|~~L~~O~~C~~O~~M~~O<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|~~11.53~~<br>~~30.65~~<br>3.91<br>14.36<br>1.84<br>7.36<br>11.55<br>30.18<br>**12.76**<br>**31.71**|~~1.68~~<br>~~8.17~~<br>0.43<br>3.96<br>0.36<br>2.29<br>4.66<br>15.83<br>**9.82**<br>**25.04**|~~3.21~~<br>~~16.33~~<br>0.52<br>8.58<br>2.13<br>6.85<br>3.27<br>14.02<br>**6.09**<br>**16.63**|~~**45.42**~~<br>~~**63.86**~~<br>4.75<br>13.41<br>3.02<br>9.35<br>43.27<br>62.75<br>33.67<br>50.31|~~**45.13**~~<br>~~**52.67**~~<br>4.24<br>6.81<br>1.22<br>4.41<br>28.72<br>35.08<br>30.31<br>36.34|
|**Qwen2.5**<br>**1.5b**<br>**3b**|LOCOMO<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|1.39<br>9.24<br>0.74<br>7.14<br>1.51<br>11.18<br>1.16<br>11.35<br>**4.88**<br>**17.94**|0.00<br>4.68<br>0.10<br>2.81<br>0.14<br>5.39<br>0.00<br>7.88<br>**5.88**<br>**27.23**|3.42<br>10.59<br>3.05<br>12.63<br>1.80<br>8.44<br>2.87<br>14.62<br>**3.44**<br>**16.87**|3.25<br>11.15<br>1.47<br>7.88<br>5.07<br>13.72<br>2.18<br>9.82<br>**12.32**<br>**24.38**|35.10<br>43.61<br>20.73<br>27.82<br>29.24<br>36.95<br>23.96<br>31.69<br>**36.32**<br>**46.60**|
|**Qwen2.5**<br>**1.5b**<br>**3b**|~~L~~O~~C~~O~~M~~O<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|~~0.49~~<br>~~4.83~~<br>0.08<br>4.08<br>0.43<br>3.76<br>0.69<br>5.55<br>**2.91**<br>**12.42**|~~0.14~~<br>~~3.20~~<br>0.00<br>1.96<br>0.05<br>1.61<br>0.05<br>3.17<br>**8.11**<br>**27.74**|~~1.31~~<br>~~5.38~~<br>1.26<br>6.19<br>0.24<br>6.32<br>1.90<br>7.90<br>**1.51**<br>**7.51**|~~1.97~~<br>~~6.98~~<br>0.73<br>4.34<br>1.03<br>4.22<br>2.05<br>7.32<br>**8.80**<br>**17.57**|~~12.66~~<br>~~17.10~~<br>7.35<br>10.64<br>9.55<br>13.41<br>10.46<br>14.39<br>**21.39**<br>**27.98**|
|**Llama 3.2**<br>**1b**<br>**3b**|LOCOMO<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|2.51<br>11.48<br>0.53<br>6.49<br>2.96<br>13.57<br>1.82<br>9.91<br>**4.82**<br>**19.31**|0.44<br>8.25<br>0.00<br>4.62<br>0.23<br>10.53<br>0.06<br>6.56<br>**1.84**<br>**20.47**|1.69<br>13.06<br>5.47<br>14.29<br>4.01<br>18.38<br>2.13<br>11.36<br>**5.99**<br>**18.49**|2.94<br>13.00<br>1.19<br>8.03<br>6.41<br>17.66<br>2.00<br>10.37<br>**14.82**<br>**29.78**|39.85<br>52.74<br>34.52<br>45.55<br>41.15<br>53.31<br>38.59<br>50.31<br>**46.76**<br>**60.23**|
|**Llama 3.2**<br>**1b**<br>**3b**|~~L~~O~~C~~O~~M~~O<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|~~0.98~~<br>~~7.22~~<br>2.47<br>1.78<br>1.83<br>6.96<br>0.72<br>5.39<br>**6.02**<br>**17.62**|~~0.03~~<br>~~4.45~~<br>3.01<br>3.01<br>0.25<br>3.41<br>0.11<br>2.85<br>**7.93**<br>**27.97**|~~2.36~~<br>~~11.39~~<br>5.07<br>5.22<br>0.43<br>4.43<br>0.61<br>5.74<br>**5.38**<br>**13.00**|~~2.85~~<br>~~8.45~~<br>3.25<br>2.51<br>2.73<br>7.83<br>1.45<br>4.42<br>**16.89**<br>**28.55**|~~25.47~~<br>~~30.26~~<br>15.78<br>14.01<br>14.64<br>18.59<br>16.62<br>21.47<br>**35.48**<br>**42.25**|


scores. When examining GPT-based models, our results reveal an interesting pattern. While LoComo
and MemGPT demonstrate strong capabilities in Open Domain and Adversarial tasks, A-M EM
shows remarkable superiority in Multi-Hop reasoning tasks. Using GPT-4o-mini, A-M EM achieves a
ROUGE-L score of 44.27 in Multi-Hop tasks, more than doubling LoComo’s 18.09. This significant
advantage maintains consistency across other metrics, with METEOR scores of 23.43 versus 7.61
and SBERT scores of 70.49 versus 52.30. The significance of these results is amplified by A-M EM ’s
exceptional computational efficiency. Our approach requires only 1,200-2,500 tokens, compared to
the substantial 16,900 tokens needed by LoComo and MemGPT. This efficiency stems from two
key architectural innovations: First, our novel agentic memory architecture creates interconnected
memory networks through atomic notes with rich contextual descriptions, enabling more effective
capture and utilization of information relationships. Second, our selective top-k retrieval mechanism
facilitates dynamic memory evolution and structured organization. The effectiveness of these innovations is particularly evident in complex reasoning tasks, as demonstrated by the consistently
strong Multi-Hop performance across all evaluation metrics. Besides, we also show the experimental
results with different foundational models including DeepSeek-R1-32B [ 11 ], Claude 3.0 Haiku [ 2 ]
and Claude 3.5 Haiku [3].


**A.4** **Memory Analysis**


In addition to the memory visualizations of the first two dialogues shown in the main text, we present
additional visualizations in Fig.5 that demonstrate the structural advantages of our agentic memory
system. Through analysis of two dialogues sampled from long-term conversations in LoCoMo[ 22 ],
we observe that A-M EM (shown in blue) consistently produces more coherent clustering patterns
compared to the baseline system (shown in red). This structural organization is particularly evident
in Dialogue 2, where distinct clusters emerge in the central region, providing empirical support
for the effectiveness of our memory evolution mechanism and contextual description generation.
In contrast, the baseline memory embeddings exhibit a more scattered distribution, indicating that
memories lack structural organization without our link generation and memory evolution components.


16


**Table 6:** Experimental results on LoCoMo dataset of QA tasks across five categories (Multi Hop, Temporal,
Open Domain, Single Hop, and Adversial) using different methods. Results are reported in METEOR and
SBERT Similarity scores, abbreviated to ME and SBERT. The best performance is marked in bold, and our
proposed method A-M EM (highlighted in gray) demonstrates competitive performance across six foundation
language models.







|Model Method|Col2|Category|Col4|Col5|Col6|Col7|
|---|---|---|---|---|---|---|
|**Model**<br>**Method**|**Model**<br>**Method**|~~**Multi Hop**~~<br>**ME**<br>**SBERT**|~~**Temporal**~~<br>**ME**<br>**SBERT**|~~**Open Domain**~~<br>**ME**<br>**SBERT**|~~**Single Hop**~~<br>**ME**<br>**SBERT**|~~**Adversial**~~<br>**ME**<br>**SBERT**|
|**GPT**<br>**4o-mini**<br>**4o**|LOCOMO<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|15.81<br>47.97<br>5.46<br>28.67<br>3.42<br>21.71<br>15.79<br>49.33<br>**16.36**<br>**49.46**|7.61<br>52.30<br>4.76<br>45.07<br>4.07<br>37.58<br>13.25<br>61.53<br>**23.43**<br>**70.49**|8.16<br>35.00<br>3.69<br>26.72<br>4.21<br>23.71<br>4.59<br>32.77<br>**8.36**<br>**38.48**|40.42<br>57.78<br>8.01<br>26.78<br>5.81<br>20.76<br>41.40<br>58.19<br>**42.32**<br>**59.38**|**63.28**<br>**71.93**<br>8.38<br>15.20<br>6.24<br>13.00<br>39.16<br>47.24<br>45.64<br>53.26|
|**GPT**<br>**4o-mini**<br>**4o**|~~L~~O~~C~~O~~M~~O<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|~~16.34~~<br>~~53.82~~<br>7.86<br>37.41<br>3.22<br>26.23<br>16.64<br>55.12<br>**17.53**<br>**55.96**|~~7.21~~<br>~~32.15~~<br>3.76<br>26.22<br>2.29<br>23.49<br>12.68<br>35.93<br>**13.10**<br>**45.40**|~~8.98~~<br>~~**43.72**~~<br>4.42<br>30.75<br>4.18<br>24.89<br>7.78<br>37.91<br>**10.62**<br>38.87|~~**53.39**~~<br>~~**73.40**~~<br>9.36<br>31.37<br>6.64<br>23.90<br>52.14<br>72.83<br>41.93<br>62.47|~~**47.72**~~<br>~~**56.09**~~<br>5.47<br>12.34<br>2.93<br>10.01<br>31.15<br>39.08<br>32.34<br>40.11|
|**Qwen2.5**<br>**1.5b**<br>**3b**|LOCOMO<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|4.99<br>32.23<br>3.67<br>28.20<br>5.57<br>35.40<br>5.40<br>35.64<br>**9.49**<br>**43.49**|2.86<br>34.03<br>1.88<br>27.27<br>2.80<br>32.47<br>2.35<br>39.04<br>**11.92**<br>**61.65**|5.89<br>35.61<br>8.97<br>35.13<br>4.27<br>33.85<br>7.68<br>40.36<br>**9.11**<br>**42.58**|8.57<br>29.47<br>5.52<br>26.33<br>10.59<br>32.16<br>7.07<br>30.16<br>**19.69**<br>**41.93**|40.53<br>50.49<br>24.04<br>34.12<br>32.93<br>42.83<br>27.24<br>40.63<br>**40.64**<br>**52.44**|
|**Qwen2.5**<br>**1.5b**<br>**3b**|~~L~~O~~C~~O~~M~~O<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|~~2.00~~<br>~~24.37~~<br>1.78<br>21.10<br>2.37<br>17.81<br>3.74<br>24.31<br>**6.25**<br>**33.72**|~~1.92~~<br>~~25.24~~<br>1.69<br>20.78<br>2.22<br>21.93<br>2.25<br>27.67<br>**14.04**<br>**62.54**|~~3.45~~<br>~~25.38~~<br>4.43<br>25.15<br>3.86<br>20.65<br>6.44<br>29.59<br>**6.56**<br>**30.60**|~~6.00~~<br>~~21.28~~<br>3.37<br>18.20<br>3.99<br>16.26<br>6.24<br>22.40<br>**15.98**<br>**33.98**|~~16.67~~<br>~~23.14~~<br>10.46<br>17.39<br>15.49<br>20.77<br>13.19<br>20.83<br>**27.36**<br>**33.72**|
|**Llama 3.2**<br>**1b**<br>**3b**|LOCOMO<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|5.77<br>38.02<br>2.97<br>29.26<br>6.77<br>39.33<br>5.10<br>32.99<br>**9.01**<br>**45.16**|3.38<br>45.44<br>1.31<br>26.45<br>4.43<br>45.63<br>2.54<br>41.81<br>**7.50**<br>**54.79**|6.20<br>42.69<br>7.13<br>39.19<br>7.76<br>42.81<br>3.26<br>35.99<br>**8.30**<br>**43.42**|9.33<br>34.19<br>5.36<br>26.44<br>13.01<br>37.32<br>6.62<br>30.68<br>**22.46**<br>**47.07**|46.79<br>60.74<br>42.39<br>54.35<br>50.43<br>60.81<br>45.00<br>61.33<br>**53.72**<br>**68.00**|
|**Llama 3.2**<br>**1b**<br>**3b**|~~L~~O~~C~~O~~M~~O<br>READAGENT<br>MEMORYBANK<br>MEMGPT<br>**A-MEM**|~~3.69~~<br>~~27.94~~<br>1.21<br>17.40<br>3.84<br>25.06<br>2.78<br>22.06<br>**9.74**<br>**39.32**|~~2.96~~<br>~~20.40~~<br>2.33<br>12.02<br>2.73<br>13.65<br>2.21<br>14.97<br>**13.19**<br>**59.70**|~~6.46~~<br>~~32.17~~<br>3.39<br>19.63<br>3.05<br>21.08<br>3.63<br>23.18<br>**8.09**<br>**32.27**|~~6.58~~<br>~~22.92~~<br>2.46<br>14.63<br>6.35<br>22.02<br>3.47<br>17.81<br>**24.30**<br>**42.86**|~~29.02~~<br>~~35.74~~<br>14.37<br>21.25<br>17.14<br>24.39<br>20.50<br>26.87<br>**39.74**<br>**46.76**|


**Table 7:** Experimental results on LoCoMo dataset of QA tasks across five categories (Multi Hop, Temporal,
Open Domain, Single Hop, and Adversial) using different methods. Results are reported in F1 and BLEU-1 (%)
scores with different foundation models.




|Method|Category|Col3|Col4|Col5|Col6|
|---|---|---|---|---|---|
|**Method**|~~**Multi Hop**~~<br>**F1**<br>**BLEU-1**|~~**Temporal**~~<br>**F1**<br>**BLEU-1**|~~**Open Domain**~~<br>**F1**<br>**BLEU-1**|~~**Single Hop**~~<br>**F1**<br>**BLEU-1**|~~**Adversial**~~<br>**F1**<br>**BLEU-1**|
|**DeepSeek-R1-32B**|**DeepSeek-R1-32B**|**DeepSeek-R1-32B**|**DeepSeek-R1-32B**|**DeepSeek-R1-32B**|**DeepSeek-R1-32B**|
|LOCOMO<br>MEMGPT<br>**A-MEM**|8.58<br>6.48<br>8.28<br>6.25<br>**15.02**<br>**10.64**|4.79<br>4.35<br>5.45<br>4.97<br>**14.64**<br>**11.01**|12.96<br>12.52<br>10.97<br>9.09<br>**14.81**<br>**12.82**|10.72<br>8.20<br>11.34<br>9.03<br>**15.37**<br>**12.30**|21.40<br>20.23<br>**30.77**<br>**29.23**<br>27.92<br>27.19|
|**Claude 3.0 Haiku**|**Claude 3.0 Haiku**|**Claude 3.0 Haiku**|**Claude 3.0 Haiku**|**Claude 3.0 Haiku**|**Claude 3.0 Haiku**|
|LOCOMO<br>MEMGPT<br>**A-MEM**|4.56<br>3.33<br>7.65<br>6.36<br>**19.28**<br>**14.69**|0.82<br>0.59<br>1.65<br>1.26<br>**16.65**<br>**12.23**|2.86<br>3.22<br>7.41<br>6.64<br>**11.85**<br>**9.61**|3.56<br>3.24<br>8.60<br>7.29<br>**34.72**<br>**30.05**|3.46<br>3.42<br>7.66<br>7.37<br>**35.99**<br>**34.87**|
|**Claude 3.5 Haiku**|**Claude 3.5 Haiku**|**Claude 3.5 Haiku**|**Claude 3.5 Haiku**|**Claude 3.5 Haiku**|**Claude 3.5 Haiku**|
|LOCOMO<br>MEMGPT<br>**A-MEM**|11.34<br>8.21<br>8.27<br>6.55<br>**29.70**<br>**23.19**|3.29<br>2.69<br>3.99<br>2.76<br>**31.54**<br>**27.53**|3.79<br>3.58<br>4.71<br>4.48<br>**11.42**<br>**9.47**|14.01<br>12.57<br>16.52<br>14.89<br>**42.60**<br>**37.41**|7.37<br>7.12<br>5.64<br>5.45<br>**13.65**<br>**12.71**|



These visualizations validate that A-M EM can autonomously maintain meaningful memory structures
through its dynamic evolution and linking mechanisms.


**A.5** **Hyperparameters setting**


All hyperparameter k values are presented in Table 8. For models that have already achieved
state-of-the-art (SOTA) performance with k=10, we maintain this value without further tuning.


17


40


30


20


10


0


−10


−20


−30


30


20


10


0


−10


−20


−30



−20 0 20


**(a)** Dialogue 3


−20 0 20


**(d)** Dialogue 6







−40 −20 0 20 40


**(c)** Dialogue 5



−30 −20 −10 0 10 20 30


**(f)** Dialogue 8





20


10


0


−10


−20


−30−40 −20 0 20


**(b)** Dialogue 4


30


20


10


0


−10


−20


−30


−40


−20 0 20


**(e)** Dialogue 7


20


10


0


−10


−20



30


20


10


0


−10


−20


−30


30


20


10


0


−10


−20


−30





20


10


0


−10


−20


−30



−30 −20 −10 0 10 20 30


**(g)** Dialogue 9



−30
−30 −20 −10 0 10 20 30


**(h)** Dialogue 10



**Figure 5:** T-SNE Visualization of Memory Embeddings Showing More Organized Distribution with A-M EM
(blue) Compared to Base Memory (red) Across Different Dialogues. Base Memory represents A-M EM without
link generation and memory evolution.


**Table 8:** Selection of k values in retriever across specific categories and model choices.


Model Multi Hop Temporal Open Domain Single Hop Adversial


GPT-4o-mini 40 40 50 50 40

GPT-4o 40 40 50 50 40
Qwen2.5-1.5b 10 10 10 10 10
Qwen2.5-3b 10 10 50 10 10
Llama3.2-1b 10 10 10 10 10

Llama3.2-3b 10 20 10 10 10


18


**B** **Prompt Templates and Examples**


**B.1** **Prompt Template of Note Construction**





**B.2** **Prompt Template of Link Generation**





19


**B.3** **Prompt Template of Memory Evolution**


20


**B.4** **Examples of Q/A with A-M** **EM**





21


**NeurIPS Paper Checklist**


The checklist is designed to encourage best practices for responsible machine learning research,
addressing issues of reproducibility, transparency, research ethics, and societal impact. Do not remove
the checklist: **The papers not including the checklist will be desk rejected.** The checklist should
follow the references and follow the (optional) supplemental material. The checklist does NOT count
towards the page limit.


Please read the checklist guidelines carefully for information on how to answer these questions. For
each question in the checklist:


    - You should answer [Yes], [No], or [NA] .

    - [NA] means either that the question is Not Applicable for that particular paper or the
relevant information is Not Available.

    - Please provide a short (1–2 sentence) justification right after your answer (even for NA).


**The checklist answers are an integral part of your paper submission.** They are visible to the
reviewers, area chairs, senior area chairs, and ethics reviewers. You will be asked to also include it
(after eventual revisions) with the final version of your paper, and its final version will be published
with the paper.


The reviewers of your paper will be asked to use the checklist as one of the factors in their evaluation.
While "[Yes] " is generally preferable to "[No] ", it is perfectly acceptable to answer "[No] " provided a
proper justification is given (e.g., "error bars are not reported because it would be too computationally
expensive" or "we were unable to find the license for the dataset we used"). In general, answering
"[No] " or "[NA] " is not grounds for rejection. While the questions are phrased in a binary way, we
acknowledge that the true answer is often more nuanced, so please just use your best judgment and
write a justification to elaborate. All supporting evidence can appear either in the main paper or the
supplemental material, provided in appendix. If you answer [Yes] to a question, in the justification
please point to the section(s) where related material for the question can be found.


IMPORTANT, please:


    **Delete this instruction block, but keep the section heading “NeurIPS Paper Checklist"**,

    - **Keep the checklist subsection headings, questions/answers and guidelines below.**

    - **Do not modify the questions and only use the provided macros for your answers** .


1. **Claims**


Question: Do the main claims made in the abstract and introduction accurately reflect the
paper’s contributions and scope?

Answer: [Yes]

Justification: The abstract and the introduction summarizes our main contributions.

Guidelines:


       - The answer NA means that the abstract and introduction do not include the claims
made in the paper.

       - The abstract and/or introduction should clearly state the claims made, including the
contributions made in the paper and important assumptions and limitations. A No or
NA answer to this question will not be perceived well by the reviewers.

       - The claims made should match theoretical and experimental results, and reflect how
much the results can be expected to generalize to other settings.

       - It is fine to include aspirational goals as motivation as long as it is clear that these goals
are not attained by the paper.

2. **Limitations**


Question: Does the paper discuss the limitations of the work performed by the authors?

Answer: [Yes]

Justification: This paper cover a section of the limiations.


22


Guidelines:


    - The answer NA means that the paper has no limitation while the answer No means that
the paper has limitations, but those are not discussed in the paper.

   - The authors are encouraged to create a separate "Limitations" section in their paper.

    - The paper should point out any strong assumptions and how robust the results are to
violations of these assumptions (e.g., independence assumptions, noiseless settings,
model well-specification, asymptotic approximations only holding locally). The authors
should reflect on how these assumptions might be violated in practice and what the
implications would be.

    - The authors should reflect on the scope of the claims made, e.g., if the approach was
only tested on a few datasets or with a few runs. In general, empirical results often
depend on implicit assumptions, which should be articulated.

    - The authors should reflect on the factors that influence the performance of the approach.
For example, a facial recognition algorithm may perform poorly when image resolution
is low or images are taken in low lighting. Or a speech-to-text system might not be
used reliably to provide closed captions for online lectures because it fails to handle
technical jargon.

    - The authors should discuss the computational efficiency of the proposed algorithms
and how they scale with dataset size.

    - If applicable, the authors should discuss possible limitations of their approach to
address problems of privacy and fairness.

    - While the authors might fear that complete honesty about limitations might be used by
reviewers as grounds for rejection, a worse outcome might be that reviewers discover
limitations that aren’t acknowledged in the paper. The authors should use their best
judgment and recognize that individual actions in favor of transparency play an important role in developing norms that preserve the integrity of the community. Reviewers
will be specifically instructed to not penalize honesty concerning limitations.


3. **Theory assumptions and proofs**


Question: For each theoretical result, does the paper provide the full set of assumptions and
a complete (and correct) proof?


Answer: [NA]


Justification: N/A


Guidelines:


   - The answer NA means that the paper does not include theoretical results.

    - All the theorems, formulas, and proofs in the paper should be numbered and crossreferenced.

    - All assumptions should be clearly stated or referenced in the statement of any theorems.

    - The proofs can either appear in the main paper or the supplemental material, but if
they appear in the supplemental material, the authors are encouraged to provide a short
proof sketch to provide intuition.

    - Inversely, any informal proof provided in the core of the paper should be complemented
by formal proofs provided in appendix or supplemental material.

   - Theorems and Lemmas that the proof relies upon should be properly referenced.


4. **Experimental result reproducibility**


Question: Does the paper fully disclose all the information needed to reproduce the main experimental results of the paper to the extent that it affects the main claims and/or conclusions
of the paper (regardless of whether the code and data are provided or not)?


Answer: [Yes]


Justification: Both code and datasets are available.


Guidelines:


   - The answer NA means that the paper does not include experiments.


23


    - If the paper includes experiments, a No answer to this question will not be perceived
well by the reviewers: Making the paper reproducible is important, regardless of
whether the code and data are provided or not.

    - If the contribution is a dataset and/or model, the authors should describe the steps taken
to make their results reproducible or verifiable.

    - Depending on the contribution, reproducibility can be accomplished in various ways.
For example, if the contribution is a novel architecture, describing the architecture fully
might suffice, or if the contribution is a specific model and empirical evaluation, it may
be necessary to either make it possible for others to replicate the model with the same
dataset, or provide access to the model. In general. releasing code and data is often
one good way to accomplish this, but reproducibility can also be provided via detailed
instructions for how to replicate the results, access to a hosted model (e.g., in the case
of a large language model), releasing of a model checkpoint, or other means that are
appropriate to the research performed.

    - While NeurIPS does not require releasing code, the conference does require all submissions to provide some reasonable avenue for reproducibility, which may depend on the
nature of the contribution. For example

(a) If the contribution is primarily a new algorithm, the paper should make it clear how
to reproduce that algorithm.
(b) If the contribution is primarily a new model architecture, the paper should describe
the architecture clearly and fully.
(c) If the contribution is a new model (e.g., a large language model), then there should
either be a way to access this model for reproducing the results or a way to reproduce
the model (e.g., with an open-source dataset or instructions for how to construct
the dataset).
(d) We recognize that reproducibility may be tricky in some cases, in which case
authors are welcome to describe the particular way they provide for reproducibility.
In the case of closed-source models, it may be that access to the model is limited in
some way (e.g., to registered users), but it should be possible for other researchers
to have some path to reproducing or verifying the results.


5. **Open access to data and code**


Question: Does the paper provide open access to the data and code, with sufficient instructions to faithfully reproduce the main experimental results, as described in supplemental
material?


Answer: [Yes]


Justification: We provide the code link in the abstract.


Guidelines:


   - The answer NA means that paper does not include experiments requiring code.

    - Please see the NeurIPS code and data submission guidelines ( `[https://nips.cc/](https://nips.cc/public/guides/CodeSubmissionPolicy)`
`[public/guides/CodeSubmissionPolicy](https://nips.cc/public/guides/CodeSubmissionPolicy)` ) for more details.

    - While we encourage the release of code and data, we understand that this might not be
possible, so “No” is an acceptable answer. Papers cannot be rejected simply for not
including code, unless this is central to the contribution (e.g., for a new open-source
benchmark).

    - The instructions should contain the exact command and environment needed to run to
reproduce the results. See the NeurIPS code and data submission guidelines ( `[https:](https://nips.cc/public/guides/CodeSubmissionPolicy)`
`[//nips.cc/public/guides/CodeSubmissionPolicy](https://nips.cc/public/guides/CodeSubmissionPolicy)` ) for more details.

    - The authors should provide instructions on data access and preparation, including how
to access the raw data, preprocessed data, intermediate data, and generated data, etc.

    - The authors should provide scripts to reproduce all experimental results for the new
proposed method and baselines. If only a subset of experiments are reproducible, they
should state which ones are omitted from the script and why.

    - At submission time, to preserve anonymity, the authors should release anonymized
versions (if applicable).


24


    - Providing as much information as possible in supplemental material (appended to the
paper) is recommended, but including URLs to data and code is permitted.

6. **Experimental setting/details**


Question: Does the paper specify all the training and test details (e.g., data splits, hyperparameters, how they were chosen, type of optimizer, etc.) necessary to understand the
results?

Answer: [Yes]

Justification: We cover all the details in the paper.

Guidelines:


   - The answer NA means that the paper does not include experiments.

    - The experimental setting should be presented in the core of the paper to a level of detail
that is necessary to appreciate the results and make sense of them.

    - The full details can be provided either with the code, in appendix, or as supplemental
material.

7. **Experiment statistical significance**


Question: Does the paper report error bars suitably and correctly defined or other appropriate
information about the statistical significance of the experiments?

Answer: [No]

Justification: The experiments utilize the API of Large Language Models. Multiple calls
will significantly increase costs.

Guidelines:


   - The answer NA means that the paper does not include experiments.

    - The authors should answer "Yes" if the results are accompanied by error bars, confidence intervals, or statistical significance tests, at least for the experiments that support
the main claims of the paper.

    - The factors of variability that the error bars are capturing should be clearly stated (for
example, train/test split, initialization, random drawing of some parameter, or overall
run with given experimental conditions).

    - The method for calculating the error bars should be explained (closed form formula,
call to a library function, bootstrap, etc.)

   - The assumptions made should be given (e.g., Normally distributed errors).

    - It should be clear whether the error bar is the standard deviation or the standard error

of the mean.

    - It is OK to report 1-sigma error bars, but one should state it. The authors should
preferably report a 2-sigma error bar than state that they have a 96% CI, if the hypothesis
of Normality of errors is not verified.

    - For asymmetric distributions, the authors should be careful not to show in tables or
figures symmetric error bars that would yield results that are out of range (e.g. negative
error rates).

    - If error bars are reported in tables or plots, The authors should explain in the text how
they were calculated and reference the corresponding figures or tables in the text.

8. **Experiments compute resources**


Question: For each experiment, does the paper provide sufficient information on the computer resources (type of compute workers, memory, time of execution) needed to reproduce
the experiments?

Answer: [Yes]

Justification: It could be found in the experimental part.

Guidelines:


   - The answer NA means that the paper does not include experiments.

    - The paper should indicate the type of compute workers CPU or GPU, internal cluster,
or cloud provider, including relevant memory and storage.


25


    - The paper should provide the amount of compute required for each of the individual
experimental runs as well as estimate the total compute.

    - The paper should disclose whether the full research project required more compute
than the experiments reported in the paper (e.g., preliminary or failed experiments that
didn’t make it into the paper).


9. **Code of ethics**


Question: Does the research conducted in the paper conform, in every respect, with the
NeurIPS Code of Ethics `[https://neurips.cc/public/EthicsGuidelines](https://neurips.cc/public/EthicsGuidelines)` ?


Answer: [NA]


Justification: N/A


Guidelines:


    - The answer NA means that the authors have not reviewed the NeurIPS Code of Ethics.

    - If the authors answer No, they should explain the special circumstances that require a
deviation from the Code of Ethics.

    - The authors should make sure to preserve anonymity (e.g., if there is a special consideration due to laws or regulations in their jurisdiction).


10. **Broader impacts**


Question: Does the paper discuss both potential positive societal impacts and negative
societal impacts of the work performed?


Answer: [No]


Justification: We don’t discuss this aspect because we provide only the memory system for
LLM agents. Different LLM agents may create varying societal impacts, which are beyond
the scope of our work.


Guidelines:


    - The answer NA means that there is no societal impact of the work performed.

    - If the authors answer NA or No, they should explain why their work has no societal
impact or why the paper does not address societal impact.

    - Examples of negative societal impacts include potential malicious or unintended uses
(e.g., disinformation, generating fake profiles, surveillance), fairness considerations
(e.g., deployment of technologies that could make decisions that unfairly impact specific
groups), privacy considerations, and security considerations.

    - The conference expects that many papers will be foundational research and not tied
to particular applications, let alone deployments. However, if there is a direct path to
any negative applications, the authors should point it out. For example, it is legitimate
to point out that an improvement in the quality of generative models could be used to
generate deepfakes for disinformation. On the other hand, it is not needed to point out
that a generic algorithm for optimizing neural networks could enable people to train
models that generate Deepfakes faster.

    - The authors should consider possible harms that could arise when the technology is
being used as intended and functioning correctly, harms that could arise when the
technology is being used as intended but gives incorrect results, and harms following
from (intentional or unintentional) misuse of the technology.

    - If there are negative societal impacts, the authors could also discuss possible mitigation
strategies (e.g., gated release of models, providing defenses in addition to attacks,
mechanisms for monitoring misuse, mechanisms to monitor how a system learns from
feedback over time, improving the efficiency and accessibility of ML).


11. **Safeguards**


Question: Does the paper describe safeguards that have been put in place for responsible
release of data or models that have a high risk for misuse (e.g., pretrained language models,
image generators, or scraped datasets)?


Answer: [NA]


Justification: N/A


26


Guidelines:


    - The answer NA means that the paper poses no such risks.

    - Released models that have a high risk for misuse or dual-use should be released with
necessary safeguards to allow for controlled use of the model, for example by requiring
that users adhere to usage guidelines or restrictions to access the model or implementing
safety filters.

    - Datasets that have been scraped from the Internet could pose safety risks. The authors
should describe how they avoided releasing unsafe images.

    - We recognize that providing effective safeguards is challenging, and many papers do
not require this, but we encourage authors to take this into account and make a best
faith effort.


12. **Licenses for existing assets**


Question: Are the creators or original owners of assets (e.g., code, data, models), used in
the paper, properly credited and are the license and terms of use explicitly mentioned and
properly respected?


Answer: [Yes]


Justification: Their contribution has already been properly acknowledged and credited.


Guidelines:


    - The answer NA means that the paper does not use existing assets.

    - The authors should cite the original paper that produced the code package or dataset.

    - The authors should state which version of the asset is used and, if possible, include a
URL.

    - The name of the license (e.g., CC-BY 4.0) should be included for each asset.

    - For scraped data from a particular source (e.g., website), the copyright and terms of
service of that source should be provided.

    - If assets are released, the license, copyright information, and terms of use in the
package should be provided. For popular datasets, `paperswithcode.com/datasets`
has curated licenses for some datasets. Their licensing guide can help determine the
license of a dataset.

    - For existing datasets that are re-packaged, both the original license and the license of
the derived asset (if it has changed) should be provided.

    - If this information is not available online, the authors are encouraged to reach out to
the asset’s creators.


13. **New assets**


Question: Are new assets introduced in the paper well documented and is the documentation
provided alongside the assets?


Answer: [NA]


Justification: N/A


Guidelines:


    - The answer NA means that the paper does not release new assets.

    - Researchers should communicate the details of the dataset/code/model as part of their
submissions via structured templates. This includes details about training, license,
limitations, etc.

    - The paper should discuss whether and how consent was obtained from people whose
asset is used.

    - At submission time, remember to anonymize your assets (if applicable). You can either
create an anonymized URL or include an anonymized zip file.


14. **Crowdsourcing and research with human subjects**


Question: For crowdsourcing experiments and research with human subjects, does the paper
include the full text of instructions given to participants and screenshots, if applicable, as
well as details about compensation (if any)?


27


Answer: [NA]

Justification: N/A

Guidelines:


    - The answer NA means that the paper does not involve crowdsourcing nor research with
human subjects.

    - Including this information in the supplemental material is fine, but if the main contribution of the paper involves human subjects, then as much detail as possible should be
included in the main paper.

    - According to the NeurIPS Code of Ethics, workers involved in data collection, curation,
or other labor should be paid at least the minimum wage in the country of the data
collector.

15. **Institutional review board (IRB) approvals or equivalent for research with human**
**subjects**

Question: Does the paper describe potential risks incurred by study participants, whether
such risks were disclosed to the subjects, and whether Institutional Review Board (IRB)
approvals (or an equivalent approval/review based on the requirements of your country or
institution) were obtained?

Answer: [NA]

Justification: N/A

Guidelines:


    - The answer NA means that the paper does not involve crowdsourcing nor research with
human subjects.

    - Depending on the country in which research is conducted, IRB approval (or equivalent)
may be required for any human subjects research. If you obtained IRB approval, you
should clearly state this in the paper.

    - We recognize that the procedures for this may vary significantly between institutions
and locations, and we expect authors to adhere to the NeurIPS Code of Ethics and the
guidelines for their institution.

    - For initial submissions, do not include any information that would break anonymity (if
applicable), such as the institution conducting the review.

16. **Declaration of LLM usage**


Question: Does the paper describe the usage of LLMs if it is an important, original, or
non-standard component of the core methods in this research? Note that if the LLM is used
only for writing, editing, or formatting purposes and does not impact the core methodology,
scientific rigorousness, or originality of the research, declaration is not required.

Answer: [NA]

Justification: N/A

Guidelines:


    - The answer NA means that the core method development in this research does not
involve LLMs as any important, original, or non-standard components.

    - Please refer to our LLM policy ( `[https://neurips.cc/Conferences/2025/LLM](https://neurips.cc/Conferences/2025/LLM)` )
for what should or should not be described.


28


