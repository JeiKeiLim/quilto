# 06-learning-structured-entities

**Source:** `06-learning-structured-entities.pdf`

---

## **Learning to Extract Structured Entities Using Language Models**

**Haolun Wu** **[1, 2]** _[∗]_ **, Ye Yuan** **[1, 2]** _[∗]_ **, Liana Mikaelyan** **[3]** **, Alexander Meulemans** **[4]** **,**
**Xue Liu** **[1, 2]**, **James Hensman** **[3]**, **Bhaskar Mitra** **[3]**

1 McGill University, 2 Mila - Quebec AI Institute, 3 Microsoft Research, 4 ETH Zürich.

{haolun.wu, ye.yuan3}@mail.mcgill.ca,
xueliu@cs.mcgill.ca, ameulema@ethz.ch,
{lmikaelyan, jameshensman, bhaskar.mitra}@microsoft.com.



**Abstract**


Recent advances in machine learning have significantly impacted the field of information extraction, with Language Models (LMs) playing a pivotal role in extracting structured information from unstructured text. Prior works

typically represent information extraction as
triplet-centric and use classical metrics such
as precision and recall for evaluation. We
reformulate the task to be entity-centric, enabling the use of diverse metrics that can provide more insights from various perspectives.
We contribute to the field by introducing Structured Entity Extraction and proposing the Approximate Entity Set OverlaP (AESOP) metric, designed to appropriately assess model performance. Later, we introduce a new Multistage Structured Entity Extraction (MuSEE)
model that harnesses the power of LMs for
enhanced effectiveness and efficiency by decomposing the extraction task into multiple
stages. Quantitative and human side-by-side
evaluations confirm that our model outperforms
baselines, offering promising directions for future advancements in structured entity extraction. Our source code and datasets are avail
[able at https://github.com/microsoft/Structured-](https://github.com/microsoft/Structured-Entity-Extraction)
[Entity-Extraction.](https://github.com/microsoft/Structured-Entity-Extraction)


**1** **Introduction**

Information extraction refers to a broad family
of challenging natural language processing (NLP)
tasks that aim to extract structured information

from unstructured text (Cardie, 1997; Eikvil, 1999;
Chang et al., 2006; Sarawagi et al., 2008; Grishman, 2015; Niklaus et al., 2018; Nasar et al., 2018;
Wang et al., 2018; Martinez-Rodriguez et al., 2020).
Examples of information extraction tasks include:
_(i)_ Named-entity recognition (Li et al., 2020), _(ii)_ relation extraction (Kumar, 2017), _(iii)_ event extraction (Li et al., 2022), and _(iv)_ coreference resolution (Stylianou and Vlahavas, 2021; Liu et al.,
2023), as well as higher-order challenges, such as


_∗_ Equal contribution with random order.



Figure 1: Illustration of the structured entity extraction,
an entity-centric formulation of information extraction.
Given a text description as well as some predefined
schema containing all the candidates of entity types and
property keys, we aim to output a structured json for all
entities in the text with their information.


automated knowledge base (KB) and knowledge
graph (KG) construction from text (Weikum and
Theobald, 2010; Ye et al., 2022; Zhong et al., 2023).
The latter may in turn necessitate solving a combination of the former more fundamental extraction

tasks as well as require other capabilities like entity linking (Shen et al., 2014, 2021; Oliveira et al.,
2021; Sevgili et al., 2022).


Previous formulations and evaluations of informa
tion extraction have predominantly centered around
the extraction of _⟨_ _subject, relation, object_ _⟩_ triplets.
The conventional metrics used to evaluate tripletlevel extraction, such as recall and precision, however, might be insufficient to represent a model’s
understanding of the text from a holistic perspective. For example, consider a paragraph that mentions ten entities, where one entity is associated
with 10 relations as the subject, while each of the
other nine entities is associated with only 1 relation
as the subject. Imagine a system that accurately
predicts all ten triplets for the heavily linked entity
but overlooks the other entities. Technically, this
system achieves a recall of more than 50% (i.e.,
10 out of 19) and a precision of 100%. However,


when compared to another system that recognizes
one correct triplet for each of the ten entities and
achieves the same recall and precision, it becomes
evident that both systems, despite showing identical evaluation scores, offer significantly different
insights into the text comprehension. Moreover,
implementing entity-level normalization within traditional metrics is not always easy due to challenges like coreference resolution (Stylianou and
Vlahavas, 2021; Liu et al., 2023), particularly in
scenarios where multiple entities share the same
name or lack primary identifiers such as names.
Therefore, we advocate for alternatives that can
offer insights from diverse perspectives.


In this work, we propose _S_ tructured _E_ ntity
_E_ xtraction, an entity-centric formulation of (strict)
information extraction, which facilitates diverse
evaluations. We define a structured entity as a
named entity with associated properties and relationships with other named-entities. Fig. 1 shows
an illustration of the structured entity extraction.
Given a text description, we aim to first identify the
two entities “ _Bill Gates_ ” and “ _Microsoft_ ”. Then,
given some predefined schema on all possible entity types and property keys (referred to as a _strict_
setting in our scenario), the exact types, property
keys, property values on all identified entities in
the text are expected to be predicted, as well as the
relations between these two entities (i.e., _Bill Gates_
co-founded _Microsoft_ ). Such extracted structured
entities may be further linked and merged to automatically construct KBs from text corpora. Along
with this, we propose a new evaluation metric,
_A_ pproximate _E_ ntity _S_ et _O_ verla _P_ (AESOP), with
numerous variants for measuring the similarity between the predicted set of entities and the ground
truth set, which is more flexible to include different level of normalization (see default AESOP in
Sec. 3 and other variants in Appendix A).


In recent years, deep learning has garnered significant interest in the realm of information extrac
tion tasks. Techniques based on deep learning for
entity extraction have consistently outperformed
traditional methods that rely on features and kernel
functions, showcasing superior capability in feature extraction and overall accuracy (Yang et al.,
2022). Building upon these developments, our
study employs language models (LMs) to solve
structured entity extraction. We introduce a _Mu_ ltistage _S_ tructured _E_ ntity _E_ xtraction (MuSEE) model,



a novel architecture that enhances both effective
ness and efficiency. Our model decomposes the entire information extraction task into multiple stages,
enabling parallel predictions within each stage for
enhanced focus and accuracy. Additionally, we reduce the number of tokens needed for generation,
which further improves the efficiency for both training and inference. Human side-by-side evaluations
show similar results as our AESOP metric, which
not only further confirm our model’s effectiveness
but also validate the AESOP metric.


In summary, our main contributions are:


  - We introduce an entity-centric formulation of
the information extraction task within a strict

setting, where the schema for all possible entity types and property keys is predefined.

  - We propose an evaluation metric,
_A_ pproximate _E_ ntity _S_ et _O_ verla _P_ (AESOP), with more flexibility tailored for
assessing structured entity extraction.

  - We propose a new model leveraging the capabilities of LMs, improving the effectiveness
and efficiency for structured entity extraction.


**2** **Related work**


In this section, we first review the formulation of existing information extraction tasks and the metrics
used, followed by a discussion of current methods
for solving information extraction tasks.


Information extraction tasks are generally divided
into open and closed settings. Open information
extraction (OIE), first proposed by Banko et al.
(2007), is designed to derive relation triplets from
unstructured text by directly utilizing entities and
relationships from the sentences themselves, without adherence to a fixed schema. Conversely,
closed information extraction (CIE) focuses on extracting factual data from text that fits into a predetermined set of relations or entities, as detailed
by Josifoski et al. (2022). While open and closed
information extraction vary, both seek to convert
unstructured text into structured knowledge, which
is typically represented as triplets. These triplets
are useful for outlining relationships but offer limited insight at the entity level. It is often assumed
that two triplets refer to the same entity if their
subjects match. However, this assumption is not
always held. Additionally, the evaluation of these
tasks relies on precision, recall, and F 1 scores at the
triplet level. As previously mentioned, evaluating


solely on triplet metrics can yield misleading insights regarding the entity understanding. Thus, it
is essential to introduce a metric that assesses under
standing at the entity level through entity-level normalization. In this work, we introduce the AESOP

metric, which is elaborated on in Sec. 3.2.


Various strategies have been employed in existing
research to address the challenges of information
extraction. TextRunner (Yates et al., 2007) initially
spearheaded the development of unsupervised
methods. Recent progress has been made with the
use of manual annotations and Transformer-based

models (Vasilkovsky et al., 2022; Kolluru et al.,
2020a). Sequence generation approaches, like IMoJIE (Kolluru et al., 2020b) and GEN2OIE (Kolluru
et al., 2022), have refined open information extraction by converting it into a sequence-to-sequence
task (Cui et al., 2018). GenIE (Josifoski et al.,
2022) focuses on integrating named-entity recognition, relation extraction, and entity linking within
a closed setting where a knowledge base is provided. Recent work, PIVOINE (Lu et al., 2023),
focuses on improving the language model’s generality to various (or unseen) instructions for open
information extraction, whereas our focus is on designing a new model architecture for improving the
effectiveness and efficiency of language model’s
information extraction in a strict setting.


**3** **Structured Entity Extraction**

In this section, we first describe the structured entity extraction formulation, followed by detailing
the Approximate Entity Set OverlaP (AESOP) metric for evaluation. We would like to emphasize that
structured entity extraction is not an entirely new
task, but rather a novel entity-centric formulation
of information extraction.


**3.1** **Task Formulation**
Given a document _d_, the goal of structured entity
extraction is to generate a set of structured entities
_E_ = _{e_ 1 _, e_ 2 _, . . ., e_ _n_ _}_ that are mentioned in the document text. Each structured entity _e_ is a dictionary
of property keys _p ∈P_ and property values _v ∈V_,
and let _v_ _e,p_ be the value of property _p_ of entity
_e_ . In this work we consider only text properties
and hence _V_ is the set of all possible text property
values. If a property of an entity is common knowledge but does not appear in the input document, it
will not be considered in the structured entity extraction. Depending on the particular situation, the
property values could be other entities, although



this is not always the case.


So, the goal then becomes to learn a function
_f_ : _d →E_ _[′]_ = _{e_ _[′]_ 1 _[, e]_ _[′]_ 2 _[, . . ., e]_ _m_ _[′]_ _[}]_ [, and we expect]
the predicted set _E_ _[′]_ to be as close as possible to
the target set _E_, where the closeness is measured
by some similarity metric Ψ( _E_ _[′]_ _, E_ ) . Note that the
predicted set of entities _E_ _[′]_ and the ground-truth set
_E_ may differ in their cardinality, and our definition
of Ψ should allow for the case when _|E_ _[′]_ _| ̸_ = _|E|_ .
Finally, both _E_ _[′]_ and _E_ are unordered sets and hence
we also want to define Ψ to be order-invariant over
_E_ _[′]_ and _E_ . As we do not need to constrain _f_ to produce the entities in any strict order, it is reasonable
for Ψ to assume the most optimistic assignment of
_E_ _[′]_ with respect to _E_ . We denote _E_ _[⃗]_ _[′]_ and _E_ _[⃗]_ as some
arbitrary but fixed ordering over items in prediction
set _E_ _[′]_ and ground-truth set _E_ for allowing indexing.


**3.2** **Approximate Entity Set OverlaP (AESOP)**
**Metric**
We propose a formal definition of the Approximate
Entity Set OverlaP (AESOP) metric, which focuses
on the entity-level and more flexible to include
different level of normalization:



which is composed of two phases: _(i) optimal en-_
_tity assignment_ for obtaining the assignment matrix
**F** to let us know which entity in _E_ _[′]_ is matched with
which one in _E_, and _(ii) pairwise entity compar-_
_ison_ through _ψ_ ent ( _E_ _[⃗]_ _[′]_ _i_ _, E_ _[⃗]_ _j_ ), which is a similarity
measure defined between any two arbitrary entities _e_ _[′]_ and _e_ . We demonstrate the details of these

two phases in this section. We implement Ψ as
a linear sum [�] over individual pairwise entity
comparisons _ψ_ ent, and _µ_ is the maximum of the
sizes of the target set and the predicted set, i.e.,
_µ_ = max _{m, n}_ .

**Phase 1: Optimal Entity Assignment.** The optimal entity assignment is directly derived from a
matrix **F** _∈_ R _[m][×][n]_, which is obtained by solving
an assignment problem between _E_ _[′]_ and _E_ . Here,
the matrix **F** is a binary matrix where each element
**F** _i,j_ is 1 if the entity _E_ _[⃗]_ _i_ _[′]_ [is matched with the entity]
_⃗E_ _j_, and 0 otherwise. Before formulating the assignment problem, we first define a similarity matrix
**S** _∈_ R _[m][×][n]_ where each element **S** _i,j_ quantifies the
similarity between the _i_ -th entity in _E_ _[⃗]_ _[′]_ and the _j_ -th
entity in _E_ _[⃗]_ for the assignment phase. For practical



Ψ( _E_ _[′]_ _, E_ ) = [1]

_µ_



_m,n_
� **F** _i,j_ _· ψ_ ent ( _E_ _[⃗]_ _[′]_ _i_ _, E_ _[⃗]_ _j_ ) _,_ (1)

_i,j_


implementation, we ensure inclusion of the union
set of property keys from both the _i_ -th entity in _E_ _[⃗]_ _[′]_

and the _j_ -th entity in _E_ _[⃗]_ for each of these entities.
When a property key is absent, its corresponding
property value is set to be an empty string. The
similarity is then computed as a weighted average
of the Jaccard index (Murphy, 1996) for the list of
tokens of the property values associated the same
property key in both entities. The Jaccard index
involved empty strings is defined as zero in our
case. We assign a weight of 0 _._ 9 to the entity name,
while all other properties collectively receive a total
weight of 0 _._ 1 . This ensures that the entity name
holds the highest importance for matching, while
still acknowledging the contributions of other properties. It is worthy to notice that the weights values
0 _._ 9 and 0 _._ 1 are not universal standards. One can

tailor the choices of these weights values for specific requirements. Then the optimal assignment
matrix **F** is found by maximizing the following
equation:



_n_
� **F** _i,j_ _·_ **S** _i,j_ _,_ (2)

_j_ =1



properties. We define the score as zero for missing
properties.


It should be noted that while both **S** and _ψ_ ent are
used to calculate similarities between pairs of entities, they are not identical. During the entity assignment phase, it is more important to make sure the
entity names are aligned, while it is more acceptable to treat all properties equally without differentiation during the pairwise entity comparison. The
separation in the definitions of two similarity measures allows us to tailor our metric more precisely
to the specific requirements of each phase of the
process. The definition of similarity and different
variants for our proposed AESOP metric are elaborated in Appendix A. We discuss the relationship
between traditional metrics, such as precision and
recall, and AESOP in Appendix B.


**4** **Multi-stage Structured Entity**
**Extraction using Language**
**Models**


In this section, we elaborate on the methodology
for structured entity extraction using LMs. We
introduce a novel model architecture leveraging
LMs, _**MuSEE**_, for _**Mu**_ lti-stage _**S**_ tructured _**E**_ ntity
_**E**_ xtaction. MuSEE is built on an encoder-decoder

architecture, whose pipeline incorporates two pivotal enhancements to improve effectiveness and
efficiency: _(i) reducing output tokens_ through introducing additional special tokens where each can be
used to replace multiple tokens, and _(ii) multi-stage_
_parallel generation_ for making the model focus
on a sub-task at each stage where all predictions
within a stage can be processed parallelly.


**Reducing output tokens.** Our model condenses
the output by translating entity types and property
keys into unique, predefined tokens. Specifically,
for the entity type, we add prefix “ **ent_type_** ”,
while for each property key, we add prefix “ **pk_** ”.
By doing so, the type and each property key on
an entity is represented by a single token, which
significantly reduces the number of output tokens
during generation thus improving efficiency. For
instance, if the original entity type is “ _artificial_
_object_ ” which is decomposed into 4 tokens (i.e.,
“_ _art_ ”, “ _if_ ”, “ _ical_ ”, “_ _object_ ”) using the T5 tokenizer, now we only need one special token,
“ **ent_type_** _artifical_object_ ”, to represent the entire
sequence. All of these special tokens can be derived through the knowledge of some predefined
schema before the model training.



**F** = arg max
**F**



_m_
�


_i_ =1



subject to the following four constraints to ensure
one-to-one assignment between entities in the prediction set and the ground truth set: _(i)_ **F** _i,j_ _∈{_ 0 _,_ 1 _}_ ;
_(ii)_ [�] _[m]_ _i_ =1 **[F]** _[i,j]_ _[ ≤]_ [1] _[,][ ∀][j][ ∈{]_ [1] _[,]_ [ 2] _[, . . ., n][}]_ [;] _[ (iii)]_ [ �] _[n]_ _j_ =1 **[F]** _[i,j]_ _[ ≤]_

1 _, ∀i ∈{_ 1 _,_ 2 _, . . ., m}_ ; _(iv)_ [�] _[m]_ _i_ =1 � _nj_ =1 **[F]** _[i,j]_ [ = min] _[{][m, n][}]_ [.]
One can take an analogy of maximizing equation. 2
to the optimal flow in the Earth Mover’s Distance
(EMD). In EMD, the optimal flow is the one that
minimizes the entire “cost” of moving the dirt,
while in our case, the optimal assignment is the
one that maximizes the entire "similarity" in the
best possible way.

**Phase 2: Pairwise Entity Comparison.** After
obtaining the optimal entity assignment, we focus on the pairwise entity comparison. We define
_ψ_ ent ( _E_ _[⃗]_ _[′]_ _i_ _, E_ _[⃗]_ _j_ ) as a similarity metric between any
two arbitrary entities _e_ _[′]_ and _e_ from _E_ _[′]_ and _E_ .


The pairwise entity similarity function _ψ_ ent is defined as a linear average [�] over individual pairwise property similarity _ψ_ prop as follows:


_ψ_ ent ( _e_ _[′]_ _, e_ ) = � _ψ_ prop ( _v_ _e_ _′_ _,p_ _, v_ _e,p_ ) _,_ (3)

_p∈P_


where _ψ_ prop ( _v_ _e_ _′_ _,p_ _, v_ _e,p_ ) is defined as the Jaccard
index between the lists of tokens of the predicted
values and ground-truth values for corresponding


Figure 2: The pipeline of our proposed MuSEE model, which is built on an encoder-decoder architecture. The input
text only needs to be encoded once. The decoder is shared for all the three stages. All predictions within each stage
can be processed in batch, and teacher forcing enables parallelization even across stages during training.



**Multi-stage parallel generation.** In addition to
reducing the number of generated tokens, MuSEE
further decomposes the generation process into
three stages: _(i)_ identifying all entities, _(ii)_ determining entity types and property keys, and _(iii)_
predicting property values. To demonstrate this
pipeline more clearly, we use the same text shown
in Fig. 1 as an example to show the process of
structured entity extraction as follows:


**Stage 1: Entity Identification.**





**Stage 2: Type and property key prediction.**





**Stage 3: Property value prediction.**


Among the three stages depicted, _pred_ent_names_,
_pred_type_and_property_, and _pred_val_ are special
tokens to indicate the task. For each model prediction behavior, the first “ _⇒_ ” indicates inputting
the text into the encoder of MuSEE, while the sec


ond “ _⇒_ ” means inputting the encoded outputs into
the decoder. All tokens in blue are the prompt
tokens input into the decoder which do not need
to be predicted, while all tokens in **bold** are the
model predictions. For the stage 1, we emphasize
that MuSEE outputs a unique identifier for each
entity in the given text. Taking the example in
Fig. 1, the first stage outputs “ _Bill Gates_ ” only,
rather than both “ _Bill Gates_ ” and “ _Gates_ ”. This

requires the model implicitly learn how to do coreference resolution, namely learning that “ _Bill Gates_ ”
and “ _Gates_ ” are referring to the same entity. Therefore, our approach uses neither surface forms, as
the outputs of the first stage are unique identifiers,
nor the entity titles followed by entity linkings. For
stage 2, the MuSEE model predicts the entity types
and property keys, which are all represented by
special tokens. Hence, the prediction can be made
by sampling the token with highest probability over
the special tokens for entity types and property keys
only, rather than all tokens. Notice that we do not
need to predict the value for “ _type_ ” and “ _name_ ” in
stage 3, since the type can be directly derived from
the “ **ent_type_** ” special key itself, and the name is
obtained during stage 1. The tokens in the bracket
“{..}” are also part of the prompt tokens and are
obtained in different ways during training and inference. During training, these inputs are obtained
from the ground truth due to the teacher forcing
technique (Raffel et al., 2023). During inference,
they are obtained from the output predictions from
the previous stages. The full training loss is a sum
of three cross-entropy losses, one for each stage.
An illustration of our model’s pipeline is shown in
Fig. 2. More implementation details are elaborated
in Appendix C.
**Benefits for Training and Inference.** MuSEE’s
unique design benefits both training and inference.
In particular, each stage in MuSEE is finely tuned to


concentrate on a specific facet of the extraction process, thereby enhancing the overall effectiveness.
Most importantly, all predictions within the same
stage can be processed in batch thus largely improving efficiency. The adoption of a teacher forcing
strategy enables parallel training even across different stages, further enhancing training efficiency.
During inference, the model’s approach to breaking
down long sequences into shorter segments significantly reduces the generation time. It is also worthy
to mention that each text in the above three stages
needs to be encoded only once by the MuSEE’s
encoder, where the encoded output is repeatedly
utilized across different stages. This streamlined
approach ensures a concise and clear delineation
of entity information, facilitating the transformation of unstructured text into a manageable and
structured format.


**5** **Experiments**


In this section, we describe the datasets used in our
experiment, followed by the discussion of baseline
methods and training details.


**5.1** **Data**

In adapting the structured entity extraction, we repurpose the NYT (Riedel et al.,
2010), CoNLL 04 (Roth and Yih, 2004), and
REBEL (Huguet Cabot and Navigli, 2021)
datasets, which are originally developed for
relation extractions. For NYT and CoNLL 04,
since each entity in these two datasets has a
predefined type, we simply reformat them to our
entity-centric formulation by treating the subjects
as entities, relations as property keys, and objects
as property values. REBEL connects entities
identified in Wikipedia abstracts as hyperlinks,
along with dates and values, to entities in Wikidata
and extracts the relations among them. For entities
without types in the REBEL dataset, we categorize
their types as “ _unknown_ ”. Additionally, we
introduce a new dataset, named Wikidata-based.
The Wikidata-based dataset is crafted using an
approach similar to REBEL but with two primary
distinctions: _(i)_ property values are not necessarily
entities; _(ii)_ we simplify the entity types by
consolidating them into broader categories based
on the Wikidata taxonomy graph, resulting in less
specific types. The processes for developing the
Wikidata-based dataset is detailed in Appendix D.
The predefined schemas for NYT, CoNLL 04, and
REBEL are using all entity types and property keys



from these datasets. The details of the predefined
schema for Wikidata-based dataset are provided in
Appendix D. Comprehensive statistics for all four
datasets are available in Appendix E.


**5.2** **Baseline**

We benchmark our methodology against two distinct classes of baseline approaches. The first category considers adaptations from general seq2seq
task models: _(i)_ LM-JSON: this approach involves
fine-tuning pre-trained language models. The input
is a textual description, and the output is the string
format JSON containing all entities. The second
category includes techniques designed for different information extraction tasks, which we adapt
to address our challenge: _(ii)_ GEN2OIE (Kolluru
et al., 2022), which employs a two-stage generative model initially outputs relations for each sentence, followed by all extractions in the subsequent
stage; _(iii)_ IMoJIE (Kolluru et al., 2020b), an extension of CopyAttention (Cui et al., 2018), which
sequentially generates new extractions based on
previously extracted tuples; _(iv)_ GenIE (Josifoski
et al., 2022), an end-to-end autoregressive generative model using a bi-level constrained generation
strategy to produce triplets that align with a predefined schema for relations. GenIE is crafted for
the closed information extraction, so it includes
a entity linking step. However, in our strict setting, there is only a schema of entity types and
relations. Therefore, we repurpose GenIE for our
setting by maintaining the constrained generation
strategy and omitting the entity linking step. We
omit to compare our method with non-generative
models primarily due to the task differences.


**5.3** **Training**
We follow existing studies (Huguet Cabot and Navigli, 2021) to use the encoder-decoder architecture
in our experiment. We choose the T5 (Raffel et al.,
2023) series of LMs and employ the pre-trained
T5-Base (T5-B) and T5-Large (T5-L) as the base
models underlying every method discussed in section 5.2 and our proposed MuSEE. LM-JSON and
MuSEE are trained with the Low-Rank Adaptation (Hu et al., 2021), where _r_ = 16 and _α_ = 32 .
For GEN2OIE, IMoJIE, and GenIE, we follow all
training details of their original implementation.
For all methods, we employ a linear warm up and
the Adam optimizer (Kingma and Ba, 2017), tuning the learning rates between 3 _e_ -4 and 1 _e_ -4, and
weight decays between 1 _e_ -2 and 0. All experiments
are run on a NVIDIA A100 GPU.


It is worthy to mention that MuSEE can also build
upon the decoder-only architecture by managing
the KV cache and modifications to the position
encodings (Xiao et al., 2024), though this requires
additional management and is not the main focus
of this study.
**6** **Results**

In this section, we show the results for both quantitative and human side-by-side evaluation.
**6.1** **Quantitative Evaluation**


**Effectiveness comparison.** The overall effectiveness comparison is shown in Table 1. We report traditional metrics, including precision, recall, and F1
score, in addition to our proposed AESOP metric.
From the results, the MuSEE model consistently
outperforms other baselines in terms of AESOP
across all datasets. For instance, MuSEE achieves
the highest AESOP scores on REBEL with 55.24
(T5-B) and 57.39 (T5-L), on NYT with 81.33 (T5B) and 82.67 (T5-L), on CoNLL04 with 78.38 (T5B) and 79.87 (T5-L), and on the Wikidata-based
dataset with 46.95 (T5-B) and 50.94 (T5-L). These
scores significantly surpass those of the competing
models, indicating MuSEE’s stronger entity extraction capability. The other three traditional metrics further underscore the efficacy of the MuSEE
model. For instance, on CoNLL04, MuSEE (T5-B)
achieves a precision of 73.18, a recall of 60.28, and
a F1 score of 66.01, which surpass all the other
baselines. Similar improvements are observed on
REBEL, NYT, and Wikidata-based dataset. Nevertheless, while MuSEE consistently excels in the
AESOP metric, it does not invariably surpass the
baselines across all the traditional metrics of precision, recall, and F1 score. Specifically, within the
REBEL dataset, GenIE (T5-B) achieves the highest
precision at 57.55, and LM-JSON (T5-B) records
the best recall at 51.29. Furthermore, on the NYT
dataset, GenIE (T5-B) outperforms other models
in F1 score. These variances highlight the unique
insights provided by our adaptive AESOP metric,
which benefits from our entity-centric formulation.
We expand on this discussion in section 6.2.


As discussed in Sec. 4, our MuSEE model is centered around two main enhancements: reducing
output tokens and multi-stage parallel generation.
By simplifying output sequences, MuSEE tackles
the challenge of managing long sequences that often hinder baseline models, like LM-JSON, GenIE,
IMoJIE, thus reducing errors associated with sequence length. Additionally, by breaking down



the extraction process into three focused stages,
MuSEE efficiently processes each aspect of entity
extraction, leveraging contextual clues for more
accurate predictions. In contrast, GEN2OIE’s twostage approach, though similar, falls short because
it extracts relations first and then attempts to pair
entities with these relations. However, a single relation may exist among different pairs of entities,
which can lead to low performance with this approach. Supplemental ablation study is provided in
Appendix F.

**Efficiency comparison.** As shown in the last column of Table 1, we provide a comparison on the inference efficiency, measured in the number of samples the model can process per second. The MuSEE
model outperforms all baseline models in terms of
efficiency, processing 52.93 samples per second
with T5-B and 33.96 samples per second with T5L. It shows a 10x speed up compared to IMoJIE,
and a 5x speed up compared to the strongest baseline GenIE. This high efficiency can be attributed to
MuSEE’s architecture, specifically its multi-stage
parallel generation feature. By breaking down the
task into parallelizable stages, MuSEE minimizes
computational overhead, allowing for faster processing of each sample. The benefit of this design
can also be approved by the observation that the
other multi-stage model, GEN2OIE, shows the second highest efficiency.


To better illustrate our model’s strength, we show
the scatter plots comparing all models with various
backbones in Fig. 3 on the effectiveness and efficiency. We choose the Wikidata-based dataset and
the effectiveness is measured by AESOP. As depicted, our model outperforms all baselines with a
large margin. This advantage makes MuSEE particularly suitable for applications requiring rapid processing of large volumes of data, such as processing
web-scale datasets, or integrating into interactive
systems where response time is critical.

**Grounding check.** As the family of T5 models
are pre-trained on Wikipedia corpus (Raffel et al.,
2023), we are curious whether the models are extracting information from the given texts, or they
are leveraging their prior knowledge to generate
information that cannot be grounded to the given
description. We use T5-L as the backbone in this
experiment. We develop a simple approach to conduct this grounding check by perturbing the original test dataset with the following strategy. We
first systematically extract and categorize all enti

Table 1: Summary of results of different models. Each metric is shown in percentage (%). The last column shows
the inference efficiency, measured by the number of samples the model can process per second. The best is **bolded**,
and the second best is underlined . Our model has a statistical significance for _p ≤_ 0 _._ 01 compared to the best
baseline (labelled with *) based on the paired t-test.


|Model|REBEL<br>AESOP Precision Recall F1|NYT<br>AESOP Precision Recall F1|CoNLL04<br>AESOP Precision Recall F1|Wikidata-based<br>AESOP Precision Recall F1|samples<br>per sec|
|---|---|---|---|---|---|
|LM-JSON (T5-B)<br>GEN2OIE (T5-B)<br>IMoJIE (T5-B)<br>GenIE (T5-B)<br>**MuSEE (T5-B)**|41.91<br>38.33<br>**51.29**<br>43.87<br>44.52<br>35.23<br>40.28<br>37.56<br>46.11<br>34.10<br>48.61<br>40.08<br>48.82_∗_<br>**57.55**<br>38.70<br>46.28_∗_<br>**55.24**<br>56.93<br>42.31<br>**48.54**|66.33<br>73.10<br>52.66<br>61.22<br>67.04<br>72.08<br>53.02<br>61.14<br>63.86<br>72.28<br>48.99<br>58.40<br>79.41_∗_<br>87.68<br>**73.24**<br>**79.81**<br>**81.33**<br>**88.29**<br>72.21<br>79.44|68.80<br>61.63<br>48.04<br>53.99<br>68.39<br>62.35<br>42.20<br>50.26<br>63.68<br>52.00<br>42.62<br>46.85<br>74.74_∗_<br>72.49_∗_<br>59.39<br>65.29<br>**78.38**<br>**73.18**<br>**60.28**<br>**66.01**|36.98<br>43.95<br>29.82<br>35.53<br>37.07<br>40.87<br>28.37<br>33.55<br>37.08<br>41.61<br>28.23<br>33.64<br>40.60_∗_<br>50.27_∗_<br>**29.75**<br>37.38<br>**46.95**<br>**53.27**<br>29.33<br>**37.99**|19.08<br>28.21<br>5.36<br>10.19<br>**52.93**|
|LM-JSON (T5-L)<br>45.92<br>39.49<br>40.82<br>40.14<br>67.73<br>73.38<br>53.22<br>61.69<br>68.88<br>61.50<br>47.77<br>53.77<br>38.19<br>43.24<br>31.63<br>36.54<br>11.24<br>GEN2OIE (T5-L)<br>46.70<br>37.28<br>41.12<br>39.09<br>68.27<br>73.97<br>53.32<br>61.88<br>68.52<br>62.76<br>43.31<br>51.16<br>38.25<br>41.23<br>28.54<br>33.77<br>18.56<br>IMoJIE (T5-L)<br>48.13<br>38.55<br>**49.73**<br>43.43<br>65.72<br>73.46<br>50.03<br>59.52<br>67.31<br>53.00<br>43.44<br>47.75<br>38.18<br>41.74<br>30.10<br>34.98<br>3.73<br>GenIE (T5-L)<br>50.06_∗_<br>**58.00**<br>42.56<br>**49.09**<br>79.64_∗_<br>84.82_∗_<br>**75.69**<br>80.00<br>72.92_∗_<br>**77.75**<br>55.64_∗_<br>64.86<br>43.50_∗_<br>**54.05**<br>30.98<br>**39.38**<br>5.09<br>**MuSEE (T5-L)**<br>**57.39**<br>57.11<br>42.89<br>48.96<br>**82.67**<br>**89.43**<br>73.32<br>**80.60**<br>**79.87**<br>74.89<br>**60.72**<br>**67.08**<br>**50.94**<br>53.72<br>**31.12**<br>39.24<br>**33.96**|LM-JSON (T5-L)<br>45.92<br>39.49<br>40.82<br>40.14<br>67.73<br>73.38<br>53.22<br>61.69<br>68.88<br>61.50<br>47.77<br>53.77<br>38.19<br>43.24<br>31.63<br>36.54<br>11.24<br>GEN2OIE (T5-L)<br>46.70<br>37.28<br>41.12<br>39.09<br>68.27<br>73.97<br>53.32<br>61.88<br>68.52<br>62.76<br>43.31<br>51.16<br>38.25<br>41.23<br>28.54<br>33.77<br>18.56<br>IMoJIE (T5-L)<br>48.13<br>38.55<br>**49.73**<br>43.43<br>65.72<br>73.46<br>50.03<br>59.52<br>67.31<br>53.00<br>43.44<br>47.75<br>38.18<br>41.74<br>30.10<br>34.98<br>3.73<br>GenIE (T5-L)<br>50.06_∗_<br>**58.00**<br>42.56<br>**49.09**<br>79.64_∗_<br>84.82_∗_<br>**75.69**<br>80.00<br>72.92_∗_<br>**77.75**<br>55.64_∗_<br>64.86<br>43.50_∗_<br>**54.05**<br>30.98<br>**39.38**<br>5.09<br>**MuSEE (T5-L)**<br>**57.39**<br>57.11<br>42.89<br>48.96<br>**82.67**<br>**89.43**<br>73.32<br>**80.60**<br>**79.87**<br>74.89<br>**60.72**<br>**67.08**<br>**50.94**<br>53.72<br>**31.12**<br>39.24<br>**33.96**|LM-JSON (T5-L)<br>45.92<br>39.49<br>40.82<br>40.14<br>67.73<br>73.38<br>53.22<br>61.69<br>68.88<br>61.50<br>47.77<br>53.77<br>38.19<br>43.24<br>31.63<br>36.54<br>11.24<br>GEN2OIE (T5-L)<br>46.70<br>37.28<br>41.12<br>39.09<br>68.27<br>73.97<br>53.32<br>61.88<br>68.52<br>62.76<br>43.31<br>51.16<br>38.25<br>41.23<br>28.54<br>33.77<br>18.56<br>IMoJIE (T5-L)<br>48.13<br>38.55<br>**49.73**<br>43.43<br>65.72<br>73.46<br>50.03<br>59.52<br>67.31<br>53.00<br>43.44<br>47.75<br>38.18<br>41.74<br>30.10<br>34.98<br>3.73<br>GenIE (T5-L)<br>50.06_∗_<br>**58.00**<br>42.56<br>**49.09**<br>79.64_∗_<br>84.82_∗_<br>**75.69**<br>80.00<br>72.92_∗_<br>**77.75**<br>55.64_∗_<br>64.86<br>43.50_∗_<br>**54.05**<br>30.98<br>**39.38**<br>5.09<br>**MuSEE (T5-L)**<br>**57.39**<br>57.11<br>42.89<br>48.96<br>**82.67**<br>**89.43**<br>73.32<br>**80.60**<br>**79.87**<br>74.89<br>**60.72**<br>**67.08**<br>**50.94**<br>53.72<br>**31.12**<br>39.24<br>**33.96**|LM-JSON (T5-L)<br>45.92<br>39.49<br>40.82<br>40.14<br>67.73<br>73.38<br>53.22<br>61.69<br>68.88<br>61.50<br>47.77<br>53.77<br>38.19<br>43.24<br>31.63<br>36.54<br>11.24<br>GEN2OIE (T5-L)<br>46.70<br>37.28<br>41.12<br>39.09<br>68.27<br>73.97<br>53.32<br>61.88<br>68.52<br>62.76<br>43.31<br>51.16<br>38.25<br>41.23<br>28.54<br>33.77<br>18.56<br>IMoJIE (T5-L)<br>48.13<br>38.55<br>**49.73**<br>43.43<br>65.72<br>73.46<br>50.03<br>59.52<br>67.31<br>53.00<br>43.44<br>47.75<br>38.18<br>41.74<br>30.10<br>34.98<br>3.73<br>GenIE (T5-L)<br>50.06_∗_<br>**58.00**<br>42.56<br>**49.09**<br>79.64_∗_<br>84.82_∗_<br>**75.69**<br>80.00<br>72.92_∗_<br>**77.75**<br>55.64_∗_<br>64.86<br>43.50_∗_<br>**54.05**<br>30.98<br>**39.38**<br>5.09<br>**MuSEE (T5-L)**<br>**57.39**<br>57.11<br>42.89<br>48.96<br>**82.67**<br>**89.43**<br>73.32<br>**80.60**<br>**79.87**<br>74.89<br>**60.72**<br>**67.08**<br>**50.94**<br>53.72<br>**31.12**<br>39.24<br>**33.96**|LM-JSON (T5-L)<br>45.92<br>39.49<br>40.82<br>40.14<br>67.73<br>73.38<br>53.22<br>61.69<br>68.88<br>61.50<br>47.77<br>53.77<br>38.19<br>43.24<br>31.63<br>36.54<br>11.24<br>GEN2OIE (T5-L)<br>46.70<br>37.28<br>41.12<br>39.09<br>68.27<br>73.97<br>53.32<br>61.88<br>68.52<br>62.76<br>43.31<br>51.16<br>38.25<br>41.23<br>28.54<br>33.77<br>18.56<br>IMoJIE (T5-L)<br>48.13<br>38.55<br>**49.73**<br>43.43<br>65.72<br>73.46<br>50.03<br>59.52<br>67.31<br>53.00<br>43.44<br>47.75<br>38.18<br>41.74<br>30.10<br>34.98<br>3.73<br>GenIE (T5-L)<br>50.06_∗_<br>**58.00**<br>42.56<br>**49.09**<br>79.64_∗_<br>84.82_∗_<br>**75.69**<br>80.00<br>72.92_∗_<br>**77.75**<br>55.64_∗_<br>64.86<br>43.50_∗_<br>**54.05**<br>30.98<br>**39.38**<br>5.09<br>**MuSEE (T5-L)**<br>**57.39**<br>57.11<br>42.89<br>48.96<br>**82.67**<br>**89.43**<br>73.32<br>**80.60**<br>**79.87**<br>74.89<br>**60.72**<br>**67.08**<br>**50.94**<br>53.72<br>**31.12**<br>39.24<br>**33.96**|LM-JSON (T5-L)<br>45.92<br>39.49<br>40.82<br>40.14<br>67.73<br>73.38<br>53.22<br>61.69<br>68.88<br>61.50<br>47.77<br>53.77<br>38.19<br>43.24<br>31.63<br>36.54<br>11.24<br>GEN2OIE (T5-L)<br>46.70<br>37.28<br>41.12<br>39.09<br>68.27<br>73.97<br>53.32<br>61.88<br>68.52<br>62.76<br>43.31<br>51.16<br>38.25<br>41.23<br>28.54<br>33.77<br>18.56<br>IMoJIE (T5-L)<br>48.13<br>38.55<br>**49.73**<br>43.43<br>65.72<br>73.46<br>50.03<br>59.52<br>67.31<br>53.00<br>43.44<br>47.75<br>38.18<br>41.74<br>30.10<br>34.98<br>3.73<br>GenIE (T5-L)<br>50.06_∗_<br>**58.00**<br>42.56<br>**49.09**<br>79.64_∗_<br>84.82_∗_<br>**75.69**<br>80.00<br>72.92_∗_<br>**77.75**<br>55.64_∗_<br>64.86<br>43.50_∗_<br>**54.05**<br>30.98<br>**39.38**<br>5.09<br>**MuSEE (T5-L)**<br>**57.39**<br>57.11<br>42.89<br>48.96<br>**82.67**<br>**89.43**<br>73.32<br>**80.60**<br>**79.87**<br>74.89<br>**60.72**<br>**67.08**<br>**50.94**<br>53.72<br>**31.12**<br>39.24<br>**33.96**|


|Col1|Human Evaluation<br>Complete. Correct. Halluc.|Quantitative Metrics<br>AESOP Precision Recall F1|
|---|---|---|
|MuSEE prefer|61.75<br>59.32<br>57.13|61.28<br>45.33<br>37.24<br>40.57|



Figure 3: An overall effectiveness-and-efficiency comparison across models on Wikidata-based Dataset.
MuSEE strongly outperforms all baselines on both measures. The effectiveness is measured by AESOP.













|AESOP|AESOP|Col3|Col4|Col5|Col6|Col7|Col8|Col9|Col10|Col11|Col12|
|---|---|---|---|---|---|---|---|---|---|---|---|
|SON<br>OIE<br>oJIE<br>enIE<br>SEE<br>0<br>10<br>20<br>30<br>40<br>50<br><br>~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|
|SON<br>OIE<br>oJIE<br>enIE<br>SEE<br>0<br>10<br>20<br>30<br>40<br>50<br><br>~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed||||||
|SON<br>OIE<br>oJIE<br>enIE<br>SEE<br>0<br>10<br>20<br>30<br>40<br>50<br><br>~~Original~~<br>Perturbed||||||||||||
|SON<br>OIE<br>oJIE<br>enIE<br>SEE<br>0<br>10<br>20<br>30<br>40<br>50<br><br>~~Original~~<br>Perturbed||||||||||||
|SON<br>OIE<br>oJIE<br>enIE<br>SEE<br>0<br>10<br>20<br>30<br>40<br>50<br><br>~~Original~~<br>Perturbed||||||||||||
|SON<br>OIE<br>oJIE<br>enIE<br>SEE<br>0<br>10<br>20<br>30<br>40<br>50<br><br>~~Original~~<br>Perturbed||||||||||||
|SON<br>OIE<br>oJIE<br>enIE<br>SEE<br>0<br>10<br>20<br>30<br>40<br>50<br><br>~~Original~~<br>Perturbed||||||||||||


|F1 score|Col2|Col3|Col4|Col5|Col6|Col7|Col8|
|---|---|---|---|---|---|---|---|
|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|~~Original~~<br>Perturbed|
|||||||||
|||||||||
|||||||||
|||||||||


Figure 4: Grounding check across models on the
Wikidata-based dataset. MuSEE shows the least performance drop on the perturbed version of data compared
to other baselines.


ties and their respective properties, based on their
entity types. Then, we generate a perturbed version
of the dataset, by randomly modifying entity properties based on the categorization we built. We introduce controlled perturbations into the dataset by
selecting alternative property values from the same
category but different entities, and subsequently
replacing the original values in the texts. The experiment results from our grounding study on the
Wikidata-based dataset, as illustrated in Fig. 4, reveal findings regarding the performance of various
models under the AESOP and F1 score. Our model,
MuSEE, shows the smallest performance gap between the perturbed data and the original data compared to its counterparts, suggesting its stronger



Table 2: Percentage of samples preferred by humans
and metrics on MuSEE’s results when compared with
GenIE’s. The first three columns are for human evaluation. The next four columns are for quantitative metrics.

capability to understand and extract structured information from given texts.


**6.2** **Human Evaluation**
To further analyze our approach, we randomly select 400 test passages from the Wikidata-based
dataset, and generate outputs of our model MuSEE
and the strongest baseline GenIE. Human evaluators are presented with a passage and two randomly
flipped extracted sets of entities with properties.
Evaluators are then prompted to choose the output
they prefer or express no preference based on three
criteria, _Completeness_, _Correctness_, and _Halluci-_
_nations_ (details shown in Appendix G). Among all
400 passages, the output of MuSEE is preferred
61.75% on the completeness, 59.32% on the correctness, and 57.13% on the hallucinations. For a
complete comparison, we also report the percentage of samples preferred by quantitative metrics on
MuSEE’s results when compared with GenIE’s, as
summarized in Table 2. As shown, our proposed
AESOP metric aligns more closely with human
judgment than traditional metrics. These observations provide additional confirm to the quantitative
results evaluated using the AESOP metric that our
model significantly outperforms existing baselines
and illustrates the inadequacy of traditional metrics
due to their oversimplified assessment of extraction quality. Case study of the human evaluation is
shown in Appendix G.

**7** **Discussion and Conclusion**

We introduce Structured Entity Extraction (SEE),
an entity-centric formulation of information extraction in a strict setting. We then propose the
Approximate Entity Set OverlaP (AESOP) Met

ric, which focuses on the entity-level and more
flexible to include different level of normalization.
Based upon, we propose a novel model architecture, MuSEE, that enhances both effectiveness and
efficiency. Both quantitative evaluation and human
side-by-side evaluation confirm that our model outperforms baselines.


An additional advantage of our formulation is its
potential to address coreference resolution challenges, particularly in scenarios where multiple
entities share the same name or lack primary identifiers such as names. Models trained with prior
triplet-centric formulation cannot solve the above
challenges. However, due to a scarcity of relevant
data, we were unable to assess this aspect in our
current study.


**8** **Limitations**

The limitation of our work lies in the assumption
that each property possesses a single value. However, there are instances where a property’s value
might consist of a set, such as varying “names”.
Adapting our method to accommodate these scenarios presents a promising research direction.


**9** **Acknowledgement**


We would like to thank all reviewers for their professional review work, constructive comments, and
valuable suggestions on our manuscript. This work
is supported by the the MSR-Mila Research Grant.
We thank Compute Canada for the computing re
sources.


**References**


Michele Banko, Michael J. Cafarella, Stephen Soderland, Matt Broadhead, and Oren Etzioni. 2007. Open
information extraction from the web. In _Proceedings_
_of the 20th International Joint Conference on Artifical_
_Intelligence_, IJCAI’07, page 2670–2676, San Francisco,
CA, USA. Morgan Kaufmann Publishers Inc.


Claire Cardie. 1997. Empirical methods in information
extraction. _AI magazine_, 18(4):65–65.


Chia-Hui Chang, Mohammed Kayed, Moheb R Girgis, and Khaled F Shaalan. 2006. A survey of web
information extraction systems. _IEEE transactions on_
_knowledge and data engineering_, 18(10):1411–1428.


[Lei Cui, Furu Wei, and Ming Zhou. 2018. Neural open](http://arxiv.org/abs/1805.04270)
[information extraction.](http://arxiv.org/abs/1805.04270)


Line Eikvil. 1999. Information extraction from world
wide web-a survey. Technical report, Technical Report
945, Norweigan Computing Center.



Hady Elsahar, Pavlos Vougiouklis, Arslen Remaci,
Christophe Gravier, Jonathon Hare, Frederique Laforest,
[and Elena Simperl. 2018. T-REx: A large scale align-](https://aclanthology.org/L18-1544)
[ment of natural language with knowledge base triples.](https://aclanthology.org/L18-1544)
In _Proceedings of the Eleventh International Confer-_
_ence on Language Resources and Evaluation (LREC_
_2018)_, Miyazaki, Japan. European Language Resources
Association (ELRA).


Ralph Grishman. 2015. Information extraction. _IEEE_
_Intelligent Systems_, 30(5):8–15.


Edward J. Hu, Yelong Shen, Phillip Wallis, Zeyuan
Allen-Zhu, Yuanzhi Li, Shean Wang, Lu Wang, and
[Weizhu Chen. 2021. Lora: Low-rank adaptation of](http://arxiv.org/abs/2106.09685)
[large language models.](http://arxiv.org/abs/2106.09685)


Pere-Lluís Huguet Cabot and Roberto Navigli. 2021.
[REBEL: Relation extraction by end-to-end language](https://doi.org/10.18653/v1/2021.findings-emnlp.204)
[generation. In](https://doi.org/10.18653/v1/2021.findings-emnlp.204) _Findings of the Association for Compu-_
_tational Linguistics: EMNLP 2021_, pages 2370–2381,
Punta Cana, Dominican Republic. Association for Computational Linguistics.


Martin Josifoski, Nicola De Cao, Maxime Peyrard,
[Fabio Petroni, and Robert West. 2022. Genie: Gen-](http://arxiv.org/abs/2112.08340)
[erative information extraction.](http://arxiv.org/abs/2112.08340)


[Diederik P. Kingma and Jimmy Ba. 2017. Adam: A](http://arxiv.org/abs/1412.6980)
[method for stochastic optimization.](http://arxiv.org/abs/1412.6980)


Keshav Kolluru, Vaibhav Adlakha, Samarth Aggarwal,
[Mausam, and Soumen Chakrabarti. 2020a. Openie6:](http://arxiv.org/abs/2010.03147)
[Iterative grid labeling and coordination analysis for open](http://arxiv.org/abs/2010.03147)
[information extraction.](http://arxiv.org/abs/2010.03147)


Keshav Kolluru, Samarth Aggarwal, Vipul Rathore,
[Mausam, and Soumen Chakrabarti. 2020b. Imojie: Iter-](http://arxiv.org/abs/2005.08178)
[ative memory-based joint open information extraction.](http://arxiv.org/abs/2005.08178)


Keshav Kolluru, Muqeeth Mohammed, Shubham Mittal,
[Soumen Chakrabarti, and Mausam. 2022. Alignment-](https://doi.org/10.18653/v1/2022.acl-long.179)
[augmented consistent translation for multilingual open](https://doi.org/10.18653/v1/2022.acl-long.179)
[information extraction. In](https://doi.org/10.18653/v1/2022.acl-long.179) _Proceedings of the 60th An-_
_nual Meeting of the Association for Computational Lin-_
_guistics (Volume 1: Long Papers)_, pages 2502–2517,
Dublin, Ireland. Association for Computational Linguistics.


Shantanu Kumar. 2017. A survey of deep learning methods for relation extraction. _arXiv preprint_
_arXiv:1705.03645_ .


Jing Li, Aixin Sun, Jianglei Han, and Chenliang Li.
2020. A survey on deep learning for named entity
recognition. _IEEE Transactions on Knowledge and_
_Data Engineering_, 34(1):50–70.


Qian Li, Jianxin Li, Jiawei Sheng, Shiyao Cui, Jia Wu,
Yiming Hei, Hao Peng, Shu Guo, Lihong Wang, Amin
Beheshti, et al. 2022. A survey on deep learning event
extraction: Approaches and applications. _IEEE Trans-_
_actions on Neural Networks and Learning Systems_ .


Ruicheng Liu, Rui Mao, Anh Tuan Luu, and Erik Cambria. 2023. A brief survey on recent advances in coreference resolution. _Artificial Intelligence Review_, pages
1–43.


Keming Lu, Xiaoman Pan, Kaiqiang Song, Hongming
Zhang, Dong Yu, and Jianshu Chen. 2023. Pivoine: Instruction tuning for open-world information extraction.
_arXiv preprint arXiv:2305.14898_ .


Jose L Martinez-Rodriguez, Aidan Hogan, and Ivan
Lopez-Arevalo. 2020. Information extraction meets the
semantic web: a survey. _Semantic Web_, 11(2):255–335.


Allan H Murphy. 1996. The finley affair: A signal
event in the history of forecast verification. _Weather_
_and forecasting_, 11(1):3–20.


Zara Nasar, Syed Waqar Jaffry, and Muhammad Kamran
Malik. 2018. Information extraction from scientific
articles: a survey. _Scientometrics_, 117:1931–1990.


Christina Niklaus, Matthias Cetto, André Freitas, and
Siegfried Handschuh. 2018. A survey on open information extraction. In _Proceedings of the 27th International_
_Conference on Computational Linguistics_, pages 3866–
3878.


Italo L Oliveira, Renato Fileto, René Speck, Luís PF
Garcia, Diego Moussallem, and Jens Lehmann. 2021.
Towards holistic entity linking: Survey and directions.
_Information Systems_, 95:101624.


Colin Raffel, Noam Shazeer, Adam Roberts, Katherine
Lee, Sharan Narang, Michael Matena, Yanqi Zhou, Wei
Li, and Peter J. Liu. 2023. [Exploring the limits of](http://arxiv.org/abs/1910.10683)
[transfer learning with a unified text-to-text transformer.](http://arxiv.org/abs/1910.10683)


Sebastian Riedel, Limin Yao, and Andrew McCallum.
2010. Modeling relations and their mentions without
labeled text. In _Machine Learning and Knowledge Dis-_
_covery in Databases_, pages 148–163, Berlin, Heidelberg. Springer Berlin Heidelberg.


[Dan Roth and Wen-tau Yih. 2004. A linear program-](https://aclanthology.org/W04-2401)
[ming formulation for global inference in natural lan-](https://aclanthology.org/W04-2401)
[guage tasks. In](https://aclanthology.org/W04-2401) _Proceedings of the Eighth Conference_
_on Computational Natural Language Learning (CoNLL-_
_2004) at HLT-NAACL 2004_, pages 1–8, Boston, Massachusetts, USA. Association for Computational Linguistics.


Sunita Sarawagi et al. 2008. Information extraction.
_Foundations and Trends® in Databases_, 1(3):261–377.


Özge Sevgili, Artem Shelmanov, Mikhail Arkhipov,
Alexander Panchenko, and Chris Biemann. 2022. Neural entity linking: A survey of models based on deep
learning. _Semantic Web_, 13(3):527–570.


Wei Shen, Yuhan Li, Yinan Liu, Jiawei Han, Jianyong
Wang, and Xiaojie Yuan. 2021. Entity linking meets
deep learning: Techniques and solutions. _IEEE Trans-_
_actions on Knowledge and Data Engineering_ .


Wei Shen, Jianyong Wang, and Jiawei Han. 2014. Entity
linking with a knowledge base: Issues, techniques, and
solutions. _IEEE Transactions on Knowledge and Data_
_Engineering_, 27(2):443–460.


Nikolaos Stylianou and Ioannis Vlahavas. 2021. A neural entity coreference resolution review. _Expert Systems_
_with Applications_, 168:114466.



Bayu Distiawan Trisedya, Gerhard Weikum, Jianzhong
[Qi, and Rui Zhang. 2019. Neural relation extraction for](https://doi.org/10.18653/v1/P19-1023)
[knowledge base enrichment. In](https://doi.org/10.18653/v1/P19-1023) _Proceedings of the 57th_
_Annual Meeting of the Association for Computational_
_Linguistics_, pages 229–240, Florence, Italy. Association
for Computational Linguistics.


Michael Vasilkovsky, Anton Alekseev, Valentin Malykh, Ilya Shenbin, Elena Tutubalina, Dmitriy Salikhov, Mikhail Stepnov, Andrey Chertok, and Sergey
[Nikolenko. 2022. Detie: Multilingual open information](http://arxiv.org/abs/2206.12514)
[extraction inspired by object detection.](http://arxiv.org/abs/2206.12514)


Yanshan Wang, Liwei Wang, Majid Rastegar-Mojarad,
Sungrim Moon, Feichen Shen, Naveed Afzal, Sijia Liu,
Yuqun Zeng, Saeed Mehrabi, Sunghwan Sohn, et al.
2018. Clinical information extraction applications: a
literature review. _Journal of biomedical informatics_,
77:34–49.


Gerhard Weikum and Martin Theobald. 2010. From
information to knowledge: harvesting entities and relationships from web sources. In _Proceedings of the_
_twenty-ninth ACM SIGMOD-SIGACT-SIGART sympo-_
_sium on Principles of database systems_, pages 65–76.


Guangxuan Xiao, Yuandong Tian, Beidi Chen, Song
[Han, and Mike Lewis. 2024. Efficient streaming lan-](http://arxiv.org/abs/2309.17453)
[guage models with attention sinks.](http://arxiv.org/abs/2309.17453)


Yang Yang, Zhilei Wu, Yuexiang Yang, Shuangshuang
Lian, Fengjie Guo, and Zhiwei Wang. 2022. A survey of
information extraction based on deep learning. _Applied_
_Sciences_, 12(19):9691.


Alexander Yates, Michele Banko, Matthew Broadhead,
Michael Cafarella, Oren Etzioni, and Stephen Soderland.
[2007. TextRunner: Open information extraction on the](https://aclanthology.org/N07-4013)
[web. In](https://aclanthology.org/N07-4013) _Proceedings of Human Language Technolo-_
_gies: The Annual Conference of the North American_
_Chapter of the Association for Computational Linguis-_
_tics (NAACL-HLT)_, pages 25–26, Rochester, New York,
USA. Association for Computational Linguistics.


Hongbin Ye, Ningyu Zhang, Hui Chen, and Huajun
Chen. 2022. Generative knowledge graph construction:
A review. In _Proceedings of the 2022 Conference on_
_Empirical Methods in Natural Language Processing_,
pages 1–17.


Lingfeng Zhong, Jia Wu, Qian Li, Hao Peng, and Xindong Wu. 2023. A comprehensive survey on automatic knowledge graph construction. _arXiv preprint_
_arXiv:2302.05019_ .


**A** **Variants of AESOP**


The AESOP metric detailed in section 3.2 matches entities by considering all properties and normalizes
with the maximum of the sizes of the target set and the predicted set. We denote it as AESOP-MultiPropMax. In this section, we elaborate more variants of the AESOP metric in addition to section 3.2,
categorized based on two criteria: the definition of entity similarity used for entity assignment and the
normalization approach when computing the final metric value between _E_ _[′]_ and _E_ . These variants allow for
flexibility and adaptability to different scenarios and requirements in structured entity extraction.


**Variants Based on Entity Assignment.** The first category of variants is based on the criteria for
matching entities between the prediction _E_ _[′]_ and the ground-truth _E_ . We define three variants:


- **AESOP-ExactName** : Two entities are considered a match if their names are identical, disregarding
case sensitivity. This variant is defined as **S** _i,j_ = 1 if _v_ _e_ _′i_ _[,]_ [name] [ =] _[ v]_ _[e]_ _[j]_ _[,]_ [name] [, otherwise 0.]


- **AESOP-ApproxName** : Entities are matched based on the similarity of their “ _name_ ” property values.
This similarity can be measured using a text similarity metric, such as the Jaccard index.


- **AESOP-MultiProp** : Entities are matched based on the similarity of all their properties, with a much
higher weight given to the “ _entity name_ ” property due to its higher importance.


**Variants Based on Normalization.** The second category of variants involves different normalization
approaches for computing the final metric value through Eq. 1:


- **AESOP-Precision** : The denominator is the size of the predicted set _E_ _[′]_, i.e., _µ_ = _m_ .


- **AESOP-Recall** : The denominator is the size of the target set _E_, i.e., _µ_ = _n_ .


- **AESOP-Max** : The denominator is the maximum of the sizes of the target set and the predicted set, i.e.,
_µ_ = max _{m, n}_ .


Given these choices, we can obtain 3 _×_ 3 = 9 variants of the AESOP metric. To avoid excessive
complexity, we regard the AESOP-MultiProp-Max as default. For clarity, we illustrate the two phases of
computing the AESOP metric and its variants in Fig. 5. We also show that precision and recall are specific
instances of the AESOP metric in Appendix B.


Figure 5: An illustration of the AESOP metric, including optimal entity assignment (phase 1) and pairwise entity
comparison (phase 2), and overall metric computation with various similarity and normalization choices.


**B** **Relationship between Precision/Recall and AESOP**


In this section, we show the traditional metrics, precision and recall, are specific instances of the AESOP
metric. To calculate precision and recall, we use the following equations on the number of triplets, where
each triplet contains _subject_, _relation_, and _object_ .


[p][redicted tri][p][lets]
precision = [# of correctl][y] (4)

# of triplets in the prediction _[,]_


[p][redicted tri][p][lets]
recall = [# of correctl][y] _._ (5)

# of triplets in the target


In the framework of the AESOP metric, precision and recall are effectively equivalent to treating each
triplet as an entity, where the _subject_ as the entity name, and the _relation_ and _object_ form a pair of property
key and value. For optimal entity assignment (phase 1), precision and recall use the AESOP-MultiProp
variant but match entities based on the similarity of all their properties with a same weight. For pairwise
entity comparison (phase 2), the _ψ_ ent ( _e_ _[′]_ _, e_ ) (Eq. 3), can be defined as 1 if _v_ _[′]_ = _v_, otherwise 0, where _v_ _[′]_

and _v_ are the only property values in _e_ _[′]_ and _e_, respectively. For Eq. 1, [�] aggregation can be defined as a
linear sum, which principally results in how many triplets are correctly predicted in this case. If _µ_ in Eq. 1
is set as the number of triplets in the prediction, this corresponds to the calculation of precision. Similarly,
when _µ_ equals the number of triplets in the target, it corresponds to the calculation of recall.


**C** **Implementation Details of MuSEE**


In order to implement the approach of our MuSEE model, one may extend existing models with encoderdecoder architecture by integrating additional modules and processing steps specifically designed for
entity and property prediction tasks. Specifically, given a predefined schema, we first add all necessary
special tokens to customize the tokenizer as detailed before. The implementation of the generation process
involves three main stages: entity prediction, property key prediction, and property value prediction.


1. Entity Prediction: We first encode the input sequence using the encoder to obtain the hidden states
for the entire sequence. We generate a prompt “pred_ent_names” and transform it to token ids using
the tokenizer. This prompt, repeated for each sample in the batch, is concatenated with the encoded
input sequence and processed through the decoder to produce entity name predictions as a sequence
of tokens.


2. Property Key Prediction: For each predicted entity name, we generate prompts in the format
“pred_type_and_property [entity_name]”. These prompts are tokenized, padded to a fixed length, and
concatenated with the encoded input sequence. The concatenated sequences are then passed through
the decoder to predict entity types and property keys as a sequence of special tokens for entity types
and property keys. We achieve this by sampling the token with highest probability over all special
tokens for entity types and property keys, rather than training a separate classifier head.


3. Property Value Prediction: For each predicted entity and its corresponding property keys, we create
prompts in the format “pred_val [entity_name] [entity_type] [property_key]”. These prompts are
tokenized, padded, and concatenated with the encoded input sequence. The concatenated sequences
are processed by the decoder to generate property value predictions.


The training loss is a summation of the cross-entropy loss from each stage, and the training process can be
parallel as we elaborate in section 4.


**D** **Details of Wikidata-based Dataset**


We build a new Wikidata-based dataset. This dataset is inspired by methodologies employed in previous
works such as Wiki-NRE (Trisedya et al., 2019), T-REx (Elsahar et al., 2018), REBEL (Huguet Cabot
and Navigli, 2021), leveraging extensive information available on Wikipedia and Wikidata. The primary
objective centers around establishing systematic alignments between textual content in Wikipedia articles,
hyperlinks embedded within these articles, and their associated entities and properties as cataloged in
Wikidata. This procedure is divided into three steps: _(i) Parsing Articles:_ We commence by parsing
English Wikipedia articles from the dump file [1], focusing specifically on text descriptions and omitting
disambiguation and redirect pages. The text from each selected article is purified of Wiki markup to
extract plain text, and hyperlinks within these articles are identified as associated entities. Subsequently,
the text descriptions are truncated to the initial ten sentences, with entity selection confined to those


1 The version of the Wikipedia and Wikidata dump files utilized in our study are 20230720, representing the most recent
version available during the development of our work.


referenced within this truncated text. This approach ensures a more concentrated and manageable dataset.
_(ii) Mapping Wikidata IDs to English Labels:_ Concurrently, we process the Wikidata dump [1] file to
establish a mapping (termed as the _id-label map_ ) between Wikidata IDs and their corresponding English
labels. This mapping allows for efficient translation of Wikidata IDs to their English equivalents. _(iii)_
_Interconnecting Wikipedia articles with Wikidata properties:_ For each associated entity within the text
descriptions, we utilize Wikidatas API to ascertain its properties and retrieve their respective Wikidata
IDs. The previously established _id-label map_ is then employed to convert these property IDs into English
labels. Each entitys type is determined using the value associated with _instance of (P31)_ . Given the highly
specific nature of these entity types (e.g., _small city (Q18466176)_, _town (Q3957)_, _big city (Q1549591)_ ),
we implement a recursive merging process to generalize these types into broader categories, referencing
the _subclass of (P279)_ property. Specifically, we first construct a hierarchical taxonomy graph. Each node
within this graph structure represents an entity type, annotated with a count reflecting the total number
of entities it encompasses. Second, a priority queue are utilized, where nodes are sorted in descending
order based on their entity count. We determine whether the top _n_ nodes represent an ideal set of entity
types, ensuring the resulted entity types are not extremely specific. Two key metrics are considered for
this evaluation: the percentage of total entities encompassed by the top _n_ nodes, and the skewness of the
distribution of each entity type’s counts within the top _n_ nodes. If the distribution is skew, we then execute
a procedure of dequeuing the top node and enqueueing its child nodes back into the priority queue. This
iterative process allows for a dynamic exploration of the taxonomy, ensuring that the most representative
nodes are always at the forefront. Finally, our Wikidata-based dataset is refined to contain the top-10 (i.e.,
_n_ = 10 ) most prevalent entity types according to our hierarchical taxonomy graph and top-10 property
keys in terms of occurrence frequency, excluding entity name and type. The 10 entity types are _talk,_
_system, spatio-temporal entity, product, natural object, human, geographical feature, corporate body,_
_concrete object,_ and _artificial object_ . The 10 property keys are _capital, family name, place of death, part of,_
_location, country, given name, languages spoken, written or signed, occupation,_ and _named after_ .


**E** **Statistics of Datasets**


NYT is under the CC-BY-SA license. CoNLL 04 is under the Creative Commons Attribution
NonCommercial-ShareAlike 3 _._ 0 International License. REBEL is under the Creative Commons At
tribution 4 _._ 0 International License. The dataset statistics presented in Table 3 compare NYT, CoNLL 04,
REBEL, and Wikidata-based datasets. All datasets feature a minimum of one entity per sample, but they
differ in their average and maximum number of entities, with the Wikidata-based dataset showing a higher
mean of 3 _._ 84 entities. They also differ in the maximum number of entities, where REBEL has a max of
65 . Property counts also vary, with REBEL having a slightly higher average number of properties per
entity at 3 _._ 40.


Table 3: Statistics of all three datasets used in our paper.

Statistics NYT CoNLL04 REBEL Wikidata-based


# of Entity Min 1 1 1 1
# of Entity Mean 1.25 1.22 2.37 3.84
# of Entity Max 12 5 65 20
# of Property Min 3 3 2 2
# of Property Mean 3.19 3.02 3.40 2.80
# of Property Max 6 4 17 8
# of Training Samples 56,196 922 2,000,000 23,477
# of Testing Samples 5,000 288 5,000 4,947


**F** **Ablation Study**


The ablation study conducted on the MuSEE model, with the Wikidata-based dataset, serves as an
evaluation of the model’s core components: the introduction of special tokens and the Multi-stage parallel


|7500<br>5000<br>2500<br>0000<br>7500<br>5000<br>2500<br>0<br>human spatio-t cca e oor rt ni m pf ci p r oc r o ei t r aa tl ea l e o oe bb bj j n ot e i et dc ct y t y talk geograp nh ai tc ur al a lf e oa bt ju er ce t product system|Col2|Col3|Col4|Col5|Col6|Col7|Col8|Col9|Col10|Col11|Col12|Col13|Col14|Col15|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|human<br>artificial object<br>spatio-temporal entity<br>corporate body<br>concrete object<br>talk<br>geographical feature<br>natural object<br>product<br>system<br>0<br>2500<br>5000<br>7500<br>0000<br>2500<br>5000<br>7500|||||||||||||||
|human<br>artificial object<br>spatio-temporal entity<br>corporate body<br>concrete object<br>talk<br>geographical feature<br>natural object<br>product<br>system<br>0<br>2500<br>5000<br>7500<br>0000<br>2500<br>5000<br>7500|||||||||||||||
|human<br>artificial object<br>spatio-temporal entity<br>corporate body<br>concrete object<br>talk<br>geographical feature<br>natural object<br>product<br>system<br>0<br>2500<br>5000<br>7500<br>0000<br>2500<br>5000<br>7500|||||||||||||||
|human<br>artificial object<br>spatio-temporal entity<br>corporate body<br>concrete object<br>talk<br>geographical feature<br>natural object<br>product<br>system<br>0<br>2500<br>5000<br>7500<br>0000<br>2500<br>5000<br>7500|||||||||||||||
|human<br>artificial object<br>spatio-temporal entity<br>corporate body<br>concrete object<br>talk<br>geographical feature<br>natural object<br>product<br>system<br>0<br>2500<br>5000<br>7500<br>0000<br>2500<br>5000<br>7500|||||||||||||||
|human<br>artificial object<br>spatio-temporal entity<br>corporate body<br>concrete object<br>talk<br>geographical feature<br>natural object<br>product<br>system<br>0<br>2500<br>5000<br>7500<br>0000<br>2500<br>5000<br>7500|||||||||||||||
|human<br>artificial object<br>spatio-temporal entity<br>corporate body<br>concrete object<br>talk<br>geographical feature<br>natural object<br>product<br>system<br>0<br>2500<br>5000<br>7500<br>0000<br>2500<br>5000<br>7500|||||||||||||||
|human<br>artificial object<br>spatio-temporal entity<br>corporate body<br>concrete object<br>talk<br>geographical feature<br>natural object<br>product<br>system<br>0<br>2500<br>5000<br>7500<br>0000<br>2500<br>5000<br>7500|||||||||||||||
|human<br>artificial object<br>spatio-temporal entity<br>corporate body<br>concrete object<br>talk<br>geographical feature<br>natural object<br>product<br>system<br>0<br>2500<br>5000<br>7500<br>0000<br>2500<br>5000<br>7500|||||||||||||||


Figure 6: Frequency histogram of entity types in
Wikidata-based Dataset.



|2000<br>0000<br>8000<br>6000<br>4000<br>2000<br>0<br>given name family name country part of l wa ri n tt g eu na g oe r s sil s go pc noa ekti deo n, n capital named after place of death occupation|Col2|Col3|Col4|Col5|Col6|Col7|Col8|Col9|Col10|Col11|Col12|Col13|Col14|Col15|Col16|Col17|Col18|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|given name<br>family name<br>country<br>part of<br>location<br>languages spoken,<br> written or signed<br>capital<br>named after<br>place of death<br>occupation<br>0<br>2000<br>4000<br>6000<br>8000<br>0000<br>2000||||||||||||||||||
|given name<br>family name<br>country<br>part of<br>location<br>languages spoken,<br> written or signed<br>capital<br>named after<br>place of death<br>occupation<br>0<br>2000<br>4000<br>6000<br>8000<br>0000<br>2000||||||||||||||||||
|given name<br>family name<br>country<br>part of<br>location<br>languages spoken,<br> written or signed<br>capital<br>named after<br>place of death<br>occupation<br>0<br>2000<br>4000<br>6000<br>8000<br>0000<br>2000||||||||||||||||||
|given name<br>family name<br>country<br>part of<br>location<br>languages spoken,<br> written or signed<br>capital<br>named after<br>place of death<br>occupation<br>0<br>2000<br>4000<br>6000<br>8000<br>0000<br>2000||||||||||||||||||
|given name<br>family name<br>country<br>part of<br>location<br>languages spoken,<br> written or signed<br>capital<br>named after<br>place of death<br>occupation<br>0<br>2000<br>4000<br>6000<br>8000<br>0000<br>2000||||||||||||||||||
|given name<br>family name<br>country<br>part of<br>location<br>languages spoken,<br> written or signed<br>capital<br>named after<br>place of death<br>occupation<br>0<br>2000<br>4000<br>6000<br>8000<br>0000<br>2000||||||||||||||||||
|given name<br>family name<br>country<br>part of<br>location<br>languages spoken,<br> written or signed<br>capital<br>named after<br>place of death<br>occupation<br>0<br>2000<br>4000<br>6000<br>8000<br>0000<br>2000||||||||||||||||||
|given name<br>family name<br>country<br>part of<br>location<br>languages spoken,<br> written or signed<br>capital<br>named after<br>place of death<br>occupation<br>0<br>2000<br>4000<br>6000<br>8000<br>0000<br>2000||||||||||||||||||
|given name<br>family name<br>country<br>part of<br>location<br>languages spoken,<br> written or signed<br>capital<br>named after<br>place of death<br>occupation<br>0<br>2000<br>4000<br>6000<br>8000<br>0000<br>2000||||||||||||||||||


Figure 7: Frequency histogram of property keys in
Wikidata-based Dataset.



Table 4: Ablation study on Wikidata-based dataset. Each metric is shown in percentage (%).

|Model|AESOP-ExactName AESOP-ApproxName AESOP-MultiProp<br>Max Precision Recall Max Precision Recall Max Precision Recall|Col3|Col4|
|---|---|---|---|
|w/o Multi-stage (T5-B)<br>**MuSEE (T5-B)**|25.19<br>40.87<br>27.64<br>**44.95**<br>**50.63**<br>**58.99**|25.75<br>42.14<br>28.26<br>**45.75**<br>**51.57**<br>**60.10**|26.93<br>44.49<br>29.72<br>**46.95**<br>**53.00**<br>**61.75**|
|w/o Multi-stage (T5-L)<br>27.74<br>53.04<br>28.81<br>28.14<br>54.10<br>29.22<br>29.14<br>56.90<br>30.29<br>**MuSEE (T5-L)**<br>**49.35**<br>**57.97**<br>**59.63**<br>**49.89**<br>**58.69**<br>**60.35**<br>**50.94**<br>**60.11**<br>**61.68**|w/o Multi-stage (T5-L)<br>27.74<br>53.04<br>28.81<br>28.14<br>54.10<br>29.22<br>29.14<br>56.90<br>30.29<br>**MuSEE (T5-L)**<br>**49.35**<br>**57.97**<br>**59.63**<br>**49.89**<br>**58.69**<br>**60.35**<br>**50.94**<br>**60.11**<br>**61.68**|w/o Multi-stage (T5-L)<br>27.74<br>53.04<br>28.81<br>28.14<br>54.10<br>29.22<br>29.14<br>56.90<br>30.29<br>**MuSEE (T5-L)**<br>**49.35**<br>**57.97**<br>**59.63**<br>**49.89**<br>**58.69**<br>**60.35**<br>**50.94**<br>**60.11**<br>**61.68**|w/o Multi-stage (T5-L)<br>27.74<br>53.04<br>28.81<br>28.14<br>54.10<br>29.22<br>29.14<br>56.90<br>30.29<br>**MuSEE (T5-L)**<br>**49.35**<br>**57.97**<br>**59.63**<br>**49.89**<br>**58.69**<br>**60.35**<br>**50.94**<br>**60.11**<br>**61.68**|



generation. By comparing the performance of the full MuSEE model against its ablated version, where
only the special tokens feature is retained, we aim to dissect the individual contributions of these design
choices to the model’s overall efficacy. The ablated version simplifies the output format by eliminating
punctuation such as commas, double quotes, and curly brackets, and by converting all entity types and
property keys into special tokens. This is similar to the reducing output tokens discussed in Sec. 4. Results
from the ablation study, as shown in Table 4, reveal significant performance disparities between the
complete MuSEE model and its ablated counterpart, particularly when examining metrics across different
model sizes (T5-B and T5-L) and evaluation metrics. The full MuSEE model markedly outperforms
the ablated version across all metrics with notable improvements, underscoring the Multi-stage parallel
generation’s critical role in enhancing the model’s ability to accurately and comprehensively extract
entity-related information. These findings highlight the synergistic effect of the MuSEE model’s design
elements, demonstrating that both the Reducing output tokens and the Multi-stage parallel generation are
pivotal for achieving optimal performance in structured entity extraction tasks.


**G** **Human Evaluation Criteria and Case Study**


The details for the three human evaluation criteria are shown below:


  - _Completeness_ : Which set of entities includes all relevant entities and has the fewest missing important
entities? Which set of entities is more useful for further analysis or processing? Focus on the set that
contains less unimportant and/or irrelevant entities.

  - _Correctness_ : Which set of entities more correctly represents the information in the passage? Focus
on consistency with the context of the passage. Do extracted properties correctly represent each
entity or are there more specific property values available? Are property values useful?

  - _Hallucinations_ : Which set of entities contains less hallucinations? That is, are there any entities or
property values that do not exist or cannot be inferred from the text?


We provide a case study for the human evaluation analysis comparing the outputs of GenIE (T5-L) and


MuSEE (T5-L) given a specific text description. MuSEE accurately identifies seven entities, surpassing
GenIE’s two, thus demonstrating greater completeness. Additionally, we identify an error in GenIE’s
output where it incorrectly assigns _Bartolomeo Rastrelli_ ’s place of death as _Moscow_, in contrast to the
actual location, _Saint Petersburg_, which is not referenced in the text. This error by GenIE could stem
from hallucination, an issue not present in MuSEE’s output. In this example, it is evident that MuSEE
outperforms GenIE in terms of _completeness_, _correctness_, and resistance to _hallucinations_ .


**Text Description:** The ceremonial attire of Elizabeth, Catherine Palace, Tsarskoye Selo; fot. Ivonna
Nowicka Elizabeth or Elizaveta Petrovna (; ) reigned as Empress of Russia from 1741 until her
death in 1762. She remains one of the most popular Russian monarchs because of her decision
not to execute a single person during her reign, her numerous construction projects, and her strong
opposition to Prussian policies. The second-eldest daughter of Tsar Peter the Great (), Elizabeth lived
through the confused successions of her father’s descendants following her half-brother Alexei’s
death in 1718. The throne first passed to her mother Catherine I of Russia (), then to her nephew
Peter II, who died in 1730 and was succeeded by Elizabeth’s first cousin Anna (). After the brief rule
of Anna’s infant great-nephew, Ivan VI, Elizabeth seized the throne with the military’s support and
declared her own nephew, the future Peter III, her heir. During her reign Elizabeth continued the
policies of her father and brought about a remarkable Age of Enlightenment in Russia. Her domestic
policies allowed the nobles to gain dominance in local government while shortening their terms of
service to the state. She encouraged Mikhail Lomonosov’s foundation of the University of Moscow,
the highest-ranking Russian educational institution. Her court became one of the most splendid
in all Europe, especially regarding architecture: she modernised Russia’s roads, encouraged Ivan
Shuvalov’s foundation of the Imperial Academy of Arts, and financed grandiose Baroque projects of
her favourite architect, Bartolomeo Rastrelli, particularly in Peterhof Palace.


**GenIE (T5-L):**


{


"0": {


"entity name": "Bartolomeo Rastrelli",

"place of death": "Moscow",

"given name": "Bartolomeo",

"family name": "Rastrelli",

"languages spoken, written or signed": "Russian",

"country": "Russia",

"type": "human"

},

"1": {


"entity name": "Catherine I of Russia",

"given name": "Catherine",

"languages spoken, written or signed": "Russian",

"type": "human"

}

}


**MuSEE (T5-L):**


{


"0": {


"type": "human",

"entity name": "Peter the Great",

"given name": "Peter"

},

"1": {


"type": "human",

"entity name": "Bartolomeo Rastrelli",

"family name": "Rastrelli",

"given name": "Bartolomeo"

},

"2": {


"type": "human",

"entity name": "Catherine I of Russia",

"given name": "Catherine"

},

"3": {


"type": "human",

"entity name": "Peter III",

"given name": "Peter"

},

"4": {


"type": "human",

"entity name": "Ivan Shuvalov",

"family name": "Shuvalov",

"given name": "Ivan",

"languages spoken, written or signed": "Russian"

},

"5": {


"type": "concrete object",

"entity name": "Peterhof Palace",

"country": "Russia"

},

"6": {


"type": "human",

"entity name": "Mikhail Lomonosov",

"family name": "Lomonosov",

"given name": "Mikhail",

"languages spoken, written or signed": "Russian"

}

}


**H** **Metric Correlation Analysis**


We show the correlation analysis between AESOP metric variants across all models on all four datasets,
shown in Fig. 8, Fig. 9, Fig. 10, and Fig. 11, respectively. Specifically, we focus on the correlation analysis
of different variants based on entity assignment variants in Phase 1 of AESOP, as described in Sec. 3.
For Phase 2, the “Max” normalization method is employed by default. Observations for the other two
normalization variants are similar. In the associated figures, AESOP-MultiProp-Max is uniformly used as
the x-axis measure, while AESOP-ExactName-Max or AESOP-ApproxName-Max serve as the y-axis
metrics. The scatter plots in all figures tend to cluster near the diagonal, indicating a robust correlation
among the various metric variants we have introduced.


|Col1|Col2|Col3|Col4|REBEL|
|---|---|---|---|---|
||||||
||||||
||||||
||||LLM<br>|-JSON (T5B)<br>|
||||GE<br>IMoJ<br>Gen<br>MuS<br>LLM<br>|2OIE (T5B)<br>IE (T5B)<br>IE (T5B)<br>EE (T5B)<br>-JSON (T5L)<br>|
||||~~GE~~<br>IMoJ<br>Gen<br>|~~2OIE (T5L)~~<br>IE (T5L)<br>IE (T5L)<br>|


|set|Col2|Col3|Col4|Col5|
|---|---|---|---|---|
||||||
||||||
||||||
||||LLM<br>|-JSON (T5B)<br>|
||||GE<br>IMoJ<br>Gen<br>MuS<br>LLM<br>|2OIE (T5B)<br>IE (T5B)<br>IE (T5B)<br>EE (T5B)<br>-JSON (T5L)<br>|
||||~~GE~~<br>IMoJ<br>Gen<br>|~~2OIE (T5L)~~<br>IE (T5L)<br>IE (T5L)<br>|















Figure 8: Metric correlation analysis on the REBEL dataset.




|Col1|Col2|Col3|Col4|NYT|
|---|---|---|---|---|
||||||
||||||
||||||
||||LLM<br>GEN<br>IMoJ<br>Gen|-JSON (T5B)<br>2OIE (T5B)<br>IE (T5B)<br>IE (T5B)|
||||MuS<br>LLM<br>~~GEN~~<br>IMoJ<br>Gen<br>|EE (T5B)<br>-JSON (T5L)<br>~~2OIE (T5L)~~<br>IE (T5L)<br>IE (T5L)<br>|


|et|Col2|Col3|Col4|Col5|
|---|---|---|---|---|
||||||
||||||
||||||
||||LLM<br>GEN<br>IMoJ<br>Gen|-JSON (T5B)<br>2OIE (T5B)<br>IE (T5B)<br>IE (T5B)|
||||MuS<br>LLM<br>~~GEN~~<br>IMoJ<br>Gen<br>|EE (T5B)<br>-JSON (T5L)<br>~~2OIE (T5L)~~<br>IE (T5L)<br>IE (T5L)<br>|



Figure 9: Metric correlation analysis on the NYT dataset.


|Col1|Col2|Col3|Col4|CO|
|---|---|---|---|---|
||||||
||||||
||||||
|||||LLM-JS<br>GEN2O<br>|
|||||IMoJIE<br>GenIE (<br>MuSEE<br>LLM-JS<br>|
|||||~~GEN2~~<br>IMoJIE<br>GenIE (<br>|


|aset|Col2|Col3|Col4|Col5|Col6|
|---|---|---|---|---|---|
|||||||
|||||||
|||||||
|||||LLM-JS<br>GEN2O<br>|ON (T5B)<br>IE (T5B)<br>|
|||||IMoJIE<br>GenIE<br>MuSEE<br>LLM-JS<br>|(T5B)<br>(T5B)<br> (T5B)<br>ON (T5L)<br>|
|||||~~GEN2~~<br>IMoJIE<br>GenIE<br>|~~IE (T5L)~~<br> (T5L)<br>(T5L)<br>|















Figure 10: Metric correlation analysis on the CONLL04.




|Col1|Col2|Col3|Col4|Wikid|
|---|---|---|---|---|
||||||
||||||
||||||
|||||LLM-JS<br>|
|||||GEN2<br>IMoJIE<br>GenIE (<br>MuSEE<br>|
|||||LLM-J<br>~~GEN2O~~<br>IMoJIE<br>GenIE (<br>|


|Col1|Col2|Col3|Col4|Col5|Col6|
|---|---|---|---|---|---|
|||||||
|||||||
|||||LLM-JS<br>|ON (T5B)<br>|
|||||GEN2<br>IMoJIE<br>GenIE<br>MuSEE<br>|IE (T5B)<br> (T5B)<br>(T5B)<br> (T5B)<br>|
|||||LLM-J<br>~~GEN2O~~<br>IMoJIE<br>GenIE<br>|ON (T5L)<br>~~IE (T5L)~~<br> (T5L)<br>(T5L)<br>|



Figure 11: Metric correlation analysis on the Wikidata-based dataset.


