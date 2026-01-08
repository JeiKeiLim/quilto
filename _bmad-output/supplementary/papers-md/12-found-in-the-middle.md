# 12-found-in-the-middle

**Source:** `12-found-in-the-middle.pdf`

---

### **Found in the Middle: How Language Models Use Long Contexts Better** **via Plug-and-Play Positional Encoding**

**Zhenyu Zhang** [1][ ♣] **Runjin Chen** [1] **Shiwei Liu** [2] **Zhewei Yao** [3] **Olatunji Ruwase** [3] **Beidi Chen** [4] **Xiaoxia Wu** [3][ ♠]

**Zhangyang Wang** [1][ ♠]



**Abstract**


This paper aims to overcome the “lost-in-themiddle” challenge of large language models
(LLMs). While recent advancements have successfully enabled LLMs to perform stable language modeling with up to 4 million tokens, the
persistent difficulty faced by most LLMs in identifying relevant information situated in the middle
of the context has not been adequately tackled. To
address this problem, this paper introduces Multiscale Positional Encoding (Ms-PoE) which is a
simple yet effective plug-and-play approach to enhance the capacity of LLMs to handle the relevant
information located in the middle of the context,
without fine-tuning or introducing any additional
overhead. Ms-PoE leverages the position indice
rescaling to relieve the long-term decay effect introduced by RoPE, while meticulously assigning
distinct scaling ratios to different attention heads
to preserve essential knowledge learned during
the pre-training step, forming a multi-scale context fusion from short to long distance. Extensive
experiments with a wide range of LLMs demonstrate the efficacy of our approach. Notably, MsPoE achieves an average accuracy gain of up to
3.8 on the Zero-SCROLLS benchmark over the

original LLMs. Code are available at [https:](https://github.com/VITA-Group/Ms-PoE)
[//github.com/VITA-Group/Ms-PoE](https://github.com/VITA-Group/Ms-PoE)


**1. Introduction**


Effective long-sequence reasoning in large language models (LLMs) is crucial for a wide range of applications (Re ´
et al., 2022; Li et al., 2023), from understanding extensive
texts (Tay et al., 2020; Krysci ´ nski et al. ´, 2021) and manag

♣ Work done during internship at Microsoft. 1 The University of Texas at Austin [2] University of Oxford [3] Microsoft
4 Carnegie Mellon University. ♠ Correspondence to: Xiaoxia Wu _<_ xiaoxiawu@microsoft.com _>_, Zhangyang Wang _<_ atlaswang@utexas.edu _>_ .


_Preprint._



_Figure 1._ The x-axis illustrates the placement of essential information within the prompt, ranging from start to end. The green bar
serves as a standard baseline, illustrating the “lost-in-the-middle”
phenomenon. We introduce our method, **M** ulti- **s** cale **Po** sition
**E** ncoding (Ms-PoE), which requires neither additional fine-tuning
nor increased memory usage. Instead, it involves a simple remapping of the position embedding depicted in Figure 2, which enables
the important information in the middle to be detected effectively
(brown bars). For more details, see Section 4.2 and Figure 5.


ing day-long conversations (Zhang et al., 2021; Zhong et al.,
2022) to code generation (Du et al., 2023; Zheng et al., 2023)
and science discoveries (Varadi et al., 2022; Song et al.,
2023b). Recent system support advancements (Dao, 2023;
Jacobs et al., 2023) have enabled training transformers for
any _L_ sequence length even with _O_ ( _L_ [2] ) computational complexity. This is exemplified by models such as MPT (Team,
2023) and Mistral (Jiang et al., 2024) pre-trained with se

Nevertheless, emerging research reveals the constrained efficacy of LLMs in managing tasks requiring long contextual
understanding. Particularly, Liu et al. (2023) demonstrated
a substantial degradation in LLMs’ performance when crucial information is positioned amidst a lengthy context, a
phenomenon they refer to as “lost-in-the-middle”. One ex
|Col1|Col2|Col3|Col4|Col5|Col6|Col7|Col8|Col9|Col10|Col11|
|---|---|---|---|---|---|---|---|---|---|---|
||||||||||||
|_ur_<br>n w<br>ve<br>eno<br>co<br>r in<br>g o<br> im<br>ow<br>g d<br>22<br>d s<br>23<br>co<br>y_ L_<br>exi<br>23<br>en<br>ve<br>ac<br>de<br>ub<br>l i<br>|||||||||||
|_ur_<br>n w<br>ve<br>eno<br>co<br>r in<br>g o<br> im<br>ow<br>g d<br>22<br>d s<br>23<br>co<br>y_ L_<br>exi<br>23<br>en<br>ve<br>ac<br>de<br>ub<br>l i<br>|||||||||||
|_ur_<br>n w<br>ve<br>eno<br>co<br>r in<br>g o<br> im<br>ow<br>g d<br>22<br>d s<br>23<br>co<br>y_ L_<br>exi<br>23<br>en<br>ve<br>ac<br>de<br>ub<br>l i<br>|||||||||||
|_ur_<br>n w<br>ve<br>eno<br>co<br>r in<br>g o<br> im<br>ow<br>g d<br>22<br>d s<br>23<br>co<br>y_ L_<br>exi<br>23<br>en<br>ve<br>ac<br>de<br>ub<br>l i<br>|||||||||||
|_ur_<br>n w<br>ve<br>eno<br>co<br>r in<br>g o<br> im<br>ow<br>g d<br>22<br>d s<br>23<br>co<br>y_ L_<br>exi<br>23<br>en<br>ve<br>ac<br>de<br>ub<br>l i<br>|_e_<br>i<br>s<br><br>di<br>c<br>f<br>p<br>n<br>a<br>)<br>c<br>b<br>bs<br> <br>ty<br>)<br>c<br>r<br>y<br>rs<br>s<br>n<br>|_1_<br>t<br>a<br>m<br>n<br>r<br> t<br>o<br> b<br>y<br>to<br>i<br>).<br> <br>s<br>.<br> a<br>e<br>th<br>o<br>t<br>ta<br>f<br>|_._ T<br>hin<br>s a<br>en<br>g (<br>eas<br>he<br>rta<br>ar<br>-lo<br> c<br>en<br> R<br>et<br>eq<br> T<br>nd<br>le<br>el<br>f L<br>an<br>nt<br>or<br>|he x<br> the<br>stan<br>on.<br>Ms-<br>ed m<br>posit<br>nt in<br>s). F<br>ng c<br>ode<br>ce d<br>ece<br>al., <br>uenc<br>his i<br> Mi<br>ngth<br>ess,<br>LM<br>ding<br>ial d<br>mati<br>|-axis ill<br>prompt,<br>dard ba<br>We intr<br>PoE), w<br>emory<br>ion emb<br>formati<br>or more<br>onvers<br>generat<br>iscove<br>nt syste<br>2023) h<br>e lengt<br>s exem<br>stral (J<br>s 16k a<br>emergi<br>s in ma<br>. Partic<br>egrada<br>on is p<br>|us<br> r<br>se<br>o<br>hi<br>u<br>e<br>o<br> d<br>at<br>i<br>ri<br><br>a<br>h<br>p<br>i<br>n<br>n<br>n<br>u<br>ti<br>o<br>|tra<br>an<br>lin<br>du<br>ch<br>sag<br>dd<br>n i<br>et<br>io<br>on<br>es<br>m s<br>ve<br>ev<br>lif<br>an<br>d<br>g r<br>ag<br>la<br>on<br>sit<br>|te<br>g<br>e<br>c<br> r<br>e<br>in<br>n<br>ai<br>n<br>(<br> (<br>u<br> <br>e<br>e<br>g<br>3<br>e<br>i<br>rl<br> i<br>i<br>|s<br>i<br>,<br>e<br>e<br>.<br>g<br>t<br>ls<br>s<br>D<br>V<br>p<br>e<br>n<br>d<br>e<br>2<br>s<br>n<br>y<br>n<br>o<br>|t<br>n<br>il<br>o<br>q<br>I<br> <br>h<br>,<br>(<br>u<br><br>p<br>n<br> <br> <br>t<br>k<br>e<br>g<br>, <br> <br>n<br>|

planation is about the use of rotary positional embedding
(RoPE) (Su et al., 2024), a prevalent positional encoding
technique used in open-source LLMs. As a relative position
embedding, RoPE incorporates a long-term decay property,
predisposing the model to prioritize current/nearby tokens
while paying less attention to further ones. Xiao et al. (2023)
identified a surprising trend attributed to the Softmax operation where attention scores are disproportionately allocated



1


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**



into initial tokens, irrespective of their relevance to the language modeling task. Despite the presence of considerable
redundancy in long-context inputs (Zhang et al., 2023), crucial information may be located across different positions.
The inclination of LLMs to overlook the middle section

presents a challenge for their applications, particularly in
the context of long-context reasoning. Several approaches
successfully extend pre-trained LLMs with context up to
extreme token length, either through sparse selection of
crucial tokens during generation (Xiao et al., 2023; Zhang
et al., 2023; Han et al., 2023) or by modifying positional
encoding (Chen et al., 2023c; Jin et al., 2024). _Nevertheless,_
_these approaches primarily aim to extend the context length_
_of LLMs and, consequently, fall short in addressing the_
_“lost-in-the-middle” problem when applied out-of-the-box._


Efforts have been made to enhance LLMs’ capacity to
capture vital information located within the middle of the
context. These include extra memory bank (Wang et al.,
2023), reordering the input context based on relevance
(Peysakhovich & Lerer, 2023; Chen et al., 2023d), enhancing the information searching and reflection ability
via attention strengthening tasks (Junqing et al., 2023; Xu
et al., 2023), splitting the input into short segments and
applying short-text models (Ivgi et al., 2023). For example, Peysakhovich & Lerer (2023) empirically discovered
that LLMs tend to emphasize more on the current window
while still paying more attention to the relevant text than distracting content. They subsequently introduced “attention
sorting” where the main idea is iteratively sorting documents
based on their attention scores, such that critical information
will likely be placed at the end, to fit the position-biased
nature of RoPE. Chen et al. (2023d) conducted parallel runs
of LLMs with different RoPE angles, thereby mitigating the
risk of overlooking crucial information through a weighted
sum of the outputs. These approaches usually require additional memory or multiple inference runs, which can be
expensive for LLMs.


In this paper, we aim to address the “lost-in-the-middle”
problem by reintroducing the concept of multi-scale features
from computer vision into the context of Transformer-based
LLMs. Multi-scale features, well-established in Inceptionstyle models (Szegedy et al., 2015; 2016; Guo et al., 2022),
utilize parallel employment of kernels with different sizes
to fuse multi-scale information, spanning short to long distances. Introducing multi-scale operations into LLMs intuitively can help compensate for crucial information located
in the middle, which might be easily overlooked by full
attention operation. Unlike modifying the attention module to form multi-scale attention, we choose to re-scale the
indices of positional encoding. This decision is grounded
not only in its effectiveness in easily adjusting the scale of
the context window by simply changing the position indices
(Chen et al., 2023c) but also in the potential of down-scaling



the position indices to relieve the long-term decay property
introduced by RoPE. However, this approach was initially
introduced to extend context windows, and its performance
regarding the “lost-in-the-middle” problem remains uncertain for several reasons: (i) Indice re-scaling forces position
embeddings of original context window to reside in a narrower region, leading to performance degradation in the
original context window as shown in Chen et al. (2023c).
(ii) Uniformly applying the same scaling ratio throughout
the entire model might be sub-optimal to preserve essential
knowledge learned during pre-training; (ii) Fine-tuning is
necessary for the original approach, albeit minimal. The
impact without fine-tuning remains unknown.


To this end, we systematically visit the position indices scaling regarding the “lost-in-the-middle” problem and counterintuitively discover that it is possible to slightly mitigate
the “lost-in-the-middle” issue if we carefully choose the
scaling ratio to be around 1.5-2. Additionally, we observe
that different attention heads exhibit varying sensitivity to
the position shift of the relevant document. Some attention
heads are “position-aware”, consistently capturing relevant
information even with position shifts, while others may occasionally capture position changes, and some heads are
completely insensitive to position changes. This highlights
the need to treat attention heads separately when re-scaling
position indices.


**Contribution.** Inspired by the above observations, we introduce Multi-scale Positional Encoding (Ms-PoE), a simple yet effective plug-and-play approach that can enhance
the long-context reasoning capability of pre-trained LLMs
without requiring fine-tuning or introducing any additional
overhead. Ms-PoE meticulously assigns distinct scaling
ratios to different attention heads, with the scaling factor
monotonically increasing from “position-aware” heads to
“position-unaware” heads. This enables us to improve longcontext ability by re-scaling position indices to shorter values while preserving essential knowledge acquired during
the pre-training phase. The efficacy of Ms-PoE is substantiated through extensive experiments. By simply re-scaling
the indices of positional encoding, Ms-PoE consistently enhances the performance of various LLMs including Llama2 (Touvron et al., 2023), StableBeluga (Mahan et al.) and
Vicuna (Chiang et al., 2023) on the ZeroSCROLLS benchmark (Shaham et al., 2023), achieving a notable average
accuracy gain of up to 3.8.


**2. Background and Related Works**


In this section, we provide a concise overview of the background knowledge and recent literature about the generative
inference process of Large Language Models (LLMs), their
abilities for long-context reasoning, and details of positional
encoding.



2


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**



**2.1. Generative Inference of LLMs**


The generative inference process in LLMs can be categorized into two distinct phases: ① Prefilling Stage: In this
initial phase, LLMs receive an input sequence containing
detailed instructions that define a specific generation goal.
Throughout this stage, intermediate Key and Value embeddings are generated at each layer and stored in memory, commonly referred to as the KV cache. ② Decoding Stage: This
phase involves retrieving embeddings from the KV cache
to generate new tokens. The decoding process is inherently
iterative, where each newly generated token serves as input
for the subsequent token generation. In real-world LLM
deployment, the cumulative length of input sequences and
the subsequently generated text can reach several thousand
or even millions of tokens, presenting significant challenges
for the LLMs’ long-context reasoning capability.


**2.2. Long Context Reasoning**


Two challenges lie ahead for LLMs in handling long-context
reasoning tasks. One is to extend the context window to
process sentences that exceed the pre-trained window length.
Another is the “lost-in-the-window” issue where LLMs will

likely overlook the information located in the middle of the

sentences.


The reason for the former challenge is that open-source
LLMs are usually pre-trained with fixed sequence lengths,
such as 4096 for Llama-2 (Touvron et al., 2023). When
the sequence length surpasses the predefined context length
used in pre-training, LLMs often suffer from performance
collapses and thus generate incoherent or fragmented text.
Recent efforts to address this issue can be broadly categorized into two streams. Recently, several works have been
proposed to address this issue, which can be broadly categorized into two streams. The first one explores from the
expansion of positional encoding, with notable contributions including PI (Chen et al., 2023c), CLEX (Chen et al.,
2023a), YaRN (Peng et al., 2023), Self-Extend (Jin et al.,
2024). On the other hand, some works modify the attention mechanism, such as StreamingLLM (Xiao et al., 2023),
LM-Inifinite (Han et al., 2023), H 2 O (Zhang et al., 2023),
TOVA (Oren et al., 2024), Zebra (Song et al., 2023a), and
Activation Beacon (Zhang et al., 2024). These approaches
have successfully expanded the contextual window with
minimal or no additional training overhead.


Despite the extended context window, LLMs still face a
significant challenge in long-context inference due to the
uneven utilization of lengthy inputs. Liu et al. (2023) conducted a pivotal investigation, revealing that LLMs tend to
overlook the middle portion of the input. This bias compromises the practical application of LLMs, as critical information may be located in the middle part of the input, leading
to unreliable outputs. To tackle this issue, Peysakhovich



& Lerer (2023) introduced ‘attention sorting’ to reorder inputs, placing critical information at the end. However, this
method’s reliance on potentially biased attention scores to
identify crucial content may compromise its reliability, and
the prerequisite knowledge of document count in inputs may
affect its effectiveness. Chen et al. (2023d) utilize Attention
Buckets, an ensemble approach that combines multiple forward processes with positional modifications. However, this
technique necessitates a considerably higher computational
cost. Other general approaches for enhancing long-context
reasoning include prompt compression (Jiang et al., 2023b),
retrieval augmentation (Xu et al., 2023), and inference refinement by constructing memory trees (Chen et al., 2023b)
while these approaches typically necessitate extra LLMs’
assistance or bring extra computational cost.


**2.3. Positional Encoding**


For effective processing of long contexts, LLMs necessitate
the explicit encoding of positional information. Common
techniques include absolute positional embedding and relative positional encoding. Absolute positional embedding
integrates word embeddings with an additional positional
vector based on the token’s absolute position, which can
be either fixed (Vaswani et al., 2017) or learnable (Devlin
et al., 2018; Lan et al., 2019; Clark et al., 2020; Radford
et al., 2019; 2018). In contrast, relative positional encoding,
increasingly popular in contemporary LLMs, encodes the
relative distances between tokens instead of their absolute

positions. Notable among these are Rotary Position Embedding (RoPE) (Su et al., 2024) that widely implemented in
models like Llama (Touvron et al., 2023), Falcon (Penedo
et al., 2023), Mistral (Jiang et al., 2023a), and ALiBi (Press
et al., 2021), which used in MPT (Team, 2023).


**RoPE.** The primary goal of RoPE (Su et al., 2024) is to
encode positional information such that the inner product
of the query and key embeddings inherently contains the
relative position information, that is:


_f_ ( **q** _m_ _, m_ ) _[T]_ _f_ ( **k** _n_ _, n_ ) = _g_ ( **q** _m_ _,_ **k** _n_ _, m −_ _n_ )


Here, _f_ is the positional encoding function applied to the
query and key embeddings at positions _m_ and _n_, respectively. To satisfy this condition, the function _f_ is defined as
a vector-valued complex function, as follows:


_f_ ( **x** _, m_ ) = **x** _e_ _[imθ]_

= [( _x_ 1 + _ix_ 2 ) _e_ _[imθ]_ [1] _,_ ( _x_ 3 + _ix_ 4 ) _e_ _[imθ]_ [2] _,_

_...,_ ( _x_ _l−_ 1 + _ix_ _l_ ) _e_ _[imθ]_ _[l/]_ [2] ] _[T]_


In this equation, _l_ represents the dimension of the embeddings, _θ_ _k_ = 10000 _[−]_ [2] _[k/l]_, and _i_ is the imaginary unit. For
calculating the attention score, RoPE considers the real
part of the product, specifically Re( _f_ ( **q** _m_ _, m_ ) _[T]_ _f_ ( **k** _n_ _, n_ )) .



3


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**























_**(Ms-PoE) Multi-Scale Positional Encoding**_






## **...**












|0|0<br>1 0<br>2 1 0<br>3 2 1 0|Col3|Col4|
|---|---|---|---|
|**1**|**1**|**1**|**1**|
|**2**|**1**<br>**0**|**1**<br>**0**|**1**<br>**0**|
|**3**|**2**<br>**1**|**2**<br>**1**|**2**<br>**1**|
|**4**|**3**<br>**2**|**0**<br>**1**|**0**<br>**1**|
|**5**|**4**<br>**3**|**1**<br>**2**|**0**|


|0|0<br>0.5 0<br>1 0.5 0<br>1.5 1 0.5 0|Col3|Col4|Col5|
|---|---|---|---|---|
|**0.5**|**0.5**|**0.5**|**0.5**|**0.5**|
|**1**|**0.5**<br>**0**|**0.5**<br>**0**|**0.5**<br>**0**|**0.5**<br>**0**|
|**1.5**|**1**<br>**0.**|**5**<br>**0**|**5**<br>**0**|**5**<br>**0**|
|**2**|**1.5**<br>**1**|**0.5**|**0**|**0**|
|**2.5**|**2**<br>**1.**|**5**<br>**1**|**0.5**|**0**|


|0|0<br>0<br>0|Col3|Col4|
|---|---|---|---|
|**0**|**0**|**0**|**0**|
||**0**|**0**|**0**|
|||||
|||**0**|**0**|
||||**0**|



_Figure 2._ Illustration of our Multi-scale Positional Encoding (MsPoE) framework. The top figure demonstrates the implementation
of Ms-PoE with various scaling ratios in different attention heads,
marked with different colors. The bottom figure shows the position
details of each head, in which the first matrix ( _r_ _i_ = 1 ) represents
the original RoPE.


This approach allows RoPE to effectively integrate relative positional information into the attention mechanism of
transformer models.


**3. Methodology**


In this section, we present the details of our Multi-Scale Positional Encoding (Ms-PoE) approach. Section 3.1 demonstrates that the context utilization of LLMs can be directly
enhanced by re-scaling the positional information without
incurring extra training costs. Then, Section 3.2 analyzes the
properties of various attention heads in LLMs. Section 3.3
outlines the detailed pipeline of Ms-PoE.


**3.1. Positional Re-scaling Improves Context Utilization**


Current LLMs tend to neglect information located in the
middle of the context, despite its potential relevance. This
“lost in the middle” phenomenon likely arises from two
contributing factors: (i) Casual Attention, where preceding tokens undergo a higher number of attention processes,
leading LLMs to disproportionately favor initial tokens.
This phenomenon has been demonstrated in recent research
which highlights the pivotal role of the initial tokens in
model generation (Han et al., 2023; Xiao et al., 2023), with
these starting tokens consistently accumulating higher attention scores (Zhang et al., 2023). (ii) The utilization of
RoPE (Su et al., 2024) introduces a long-term decay effect,
diminishing the attention score of distantly positioned yet
semantically meaningful tokens. The combination of these



factors contributes to LLMs neglecting the context in the
middle part. To tackle this issue and improve the context utilization of LLMs, a seemingly unreasonable yet remarkably
effective strategy is to down-scale positional information
(Song et al., 2023a). Formally, RoPE encodes the position
as _f_ ( **x** _, m_ ) = **x** _e_ _[imθ]_ . By substituting the position _m_ with
_mr_ [, we can force the long-distance tokens to reside in the]

shorted range, which can potentially alleviate the long-term
decay effects by a factor of _r_ . In the following sections,
we conduct experiments to evaluate how LLMs’ context
utilization responds to varying re-scaling ratios _r_ .


**Details.** Experiments are conducted using Llama-27B-Chat (Touvron et al., 2023) and Vicuna-7B (Chiang
et al., 2023) on the Multi-Document Question Answering
(MDQA) task (Liu et al., 2023). Each question includes ten
documents, with only one relevant to the question. By varying the position of the relevant document, we can evaluate
LLMs’ context utilization properties. For each position of
the key document, we calculate the accuracy over 500 samples. And results show in Figure 3 include both the **Average**
accuracy over the 10 documents as well as **Gap** accuracy,
_i.e._, the difference between the best and worst accuracy
when varying the positions of the relevant document.



Llama-2-7B-Chat Vicuna-7B


_Figure 3._ Results of the relationship between positional re-scaling
and context utilization. The upper curve illustrates the average
accuracy when placing the key document in various positions.
The bottom curve indicates the gap between the best and worst

accuracy.


**Results.** Figure 3 demonstrates that the gap accuracy can be
alleviated via appropriate positional re-scaling. Particularly,
we see that the Gap between the best and the worst accuracy
is greatly reduced when increasing the re-scaling ratio. An
enhanced average accuracy can be observed with a scaling
ratio equals near 1 _._ 5 . Additionally, changing the scaling
ratio also affects the favored zone of LLMs. With a small

scaling ratio (e.g., 0 _._ 5 ), LLMs tend to focus more on the
most recent part of the context, while with a large ratio (e.g.,
2 _._ 5), LLMs favour the beginning part.


**Improving context reasoning via positional re-scaling.**
Building upon this, we introduce a plug-and-play treatment
for RoPE by re-scaling the position of each token. This
approach seamlessly enhances the context utilization of
LLMs without requiring additional training or inference



4


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**



overhead. However, there is a trade-off in terms of LLMs favoring certain context regions. For instance, when _r_ = 0 _._ 5,
LLMs achieve peak accuracy when the relevant document
is located at the end of the input, while at the beginning
for _r_ = 1 _._ 5 . It remains challenging to decide which rescaling ratio to use, given that we lack prior knowledge
of the location of relevant information in real-world applications. Moreover, as the re-scaling ratio increases,
LLMs may face the positional out-of-distribution (O.O.D)
issue (Jin et al., 2024; Chen et al., 2023c), where many position values do not directly exist during pretraining (e.g.,
using 0 _._ 1 _,_ 0 _._ 2 _, ...,_ 0 _._ 9 for position when LLMs only recognize 1 _,_ 2 _, ...,_ 9 during pretraining), potentially reducing their
average reasoning ability. To tackle these challenges, we
investigate the head-wise properties of LLMs and propose a
multi-scale positional encoding approach.


**3.2. Position-Aware Head-Wise Re-scaling Ratio**


Inspired by recent works that leverage attention patterns
to identify most crucial tokens and optimize inference efficiency (Oren et al., 2024; Zhang et al., 2023; Ge et al.,
2023), we carry out a preliminary study to investigate the
interaction between attention patterns and token positions.


**Details.** We visualize the attention patterns of the most
recent query with results collected from Vicuna-7B on the
MDQA task, following (Oren et al., 2024). In the same input sample, we manually switch the position of the relevant
document from the beginning to the end and illustrate the
attention scores across different positions.


**Observation.** We observe the presence of “position-aware”
attention heads capable of capturing relevant information
even when its position is shifted. As an example, we select
the eighth attention head in the fifteenth layer, depicted in
the bottom of Figure 4, while consistent observations can
be drawn across different layers and input samples. Firstly,
most attention scores are near zero and can be ignored, consistent with other studies highlighting high sparsity in attention blocks (Zhang et al., 2023; Likhosherstov et al., 2021;
Edelman et al., 2022). For the remaining positions, these
“position-aware” attention heads can capture important information across positions, with attention patterns shifting as
the position of relevant tokens changes. However, for other
attention heads (upper subfigure in Figure 4), they fail to
capture relevant tokens and only attend to the beginning and
end words, contributing to the “lost-in-the-middle” issue.


Based on this observation, we devise a position-aware strategy to adaptively determine the re-scaling ratio via the inherent properties of different attention heads. For the “positionaware” attention heads, we assign a re-scaling ratio close to
one to avoid changing their functionality significantly, as altering them too much could degrade performance due to the
positional O.O.D issue. On the other heads, we condense



their position indices to a higher degree, providing more
opportunity to alleviate the persistent bias toward the beginning and recent tokens. To identify the properties of _n_ _h_
attention heads, we introduce a Position-Awareness Score
_S_ _P_ _∈_ **R** _[n]_ _[h]_ formulated as:



In Equation 1, _A_ represents the attention score vector of the
most recent query, and _α_ is a hyperparameter determining
the threshold of effective attention scores. In all experiments,
we default to using _α_ = 3, and the corresponding important
tokens are highlighted in Figure 4, which are shown in red.
In the spirit of numerous studies that investigate the outlier
properties in LLMs (Xiao et al., 2023; Lin et al., 2023; Yin
et al., 2023), we utilize _S_ _P_ to evaluate the ratio of effective
attention tokens, where a larger _S_ _P_ value implies better
positional awareness.


**3.3. Inference with Multi-Scale Positional Encoding**


**Algorithm 1** LLM Inference with Ms-PoE
**Require:** A pre-trained LLM _f_ ( _θ_ ) with positional encoding RoPE, input content _X_, generation length _l_, number
of attention heads _n_ _h_, number of layers _n_ _l_, re-scaling
ratios **r** = [ _r_ 1 _, r_ 2 _, . . ., r_ _n_ _h_ ], calculated in Equation 2.
**Ensure:** Generated text _T_ .


1: Set Prefilling = True;
2: **while** _i < l_ **do**

3: **if** Prefilling **then**
4: **for** k in 1, 2, ..., _n_ _l_ **do**
5: Get the last query _Q_ _l_ and all key _K_ in layer k;
6: _A_ = Softmax( _Q_ _l,∗_ ( _K_ _∗_ ) _[T]_ );
7: Calculate Position-Awareness Score _S_ **P** ( _A_ ) for
each head, with Equation 1;
8: # Initial re-scaling ratio in each layer
9: **r** _k_ = **r** [ _S_ **P** _._ argsort(reverse=True)];
10: Replace RoPE in layer k with Ms-PoE ( **r** _k_ );
11: **end for**

12: Prefilling = False;
13: **end if**

14: Generate _T_ with implemented Ms-PoE;
15: **end while**


The pipeline for utilizing Multi-Scale Positional Encoding
(Ms-PoE) in LLM inference is outlined in Algorithm 1.
Given a pre-trained LLM, we initially replace the original
rotary positional encoding with Ms-PoE. As illustrated in
Figure 2, Ms-PoE condenses the positional indices of RoPE
and employs different re-scaling ratios for each attention
head. The re-scaling ratios are assigned during the prefilling stage, where we first calculate the distribution of
attention scores for the most recent query and obtain the



_l_



_S_ _P_ = [1]

_l_



_l_
�



�( _A_ _i_ _≥_ _α_ [1] _l_

_i_ =1



_l_
� _A_ _i_ ) (1)


_i_ =1



5


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**


_Figure 4._ Visualization of attention pattern of the most recent query within two different attention heads. **Top:** Results of the 12th attention
head in the 15th layer. **Bottom:** Results of the 8th attention head in the 15th layer. The most recent query remains unchanged while
varying the position of the crucial document. More examples are reported in Figure 6 in the appendix.



corresponding position-awareness score for each attention
head. Larger re-scaling ratios are subsequently allocated
to attention heads exhibiting smaller position-awareness
scores. And the set of re-scaling ratios **r** defaults to a **linear**
range from **1** _._ **2** to **1** _._ **8** . For example, the _i_ th sorted-head
would be using re-scaling ratio


_r_ _i_ = 1 _._ 2 + ( _i −_ 1)(1 _._ 8 _−_ 1 _._ 2) _/_ ( _n_ _h_ _−_ 1) (2)


Once the re-scaling ratios are assigned, they remain fixed in
the subsequent decoding stage.


**4. Experiments**


The goal of this section is to demonstrate Ms-PoE, a plugand-play positional encoding capable of enhancing the context utilization of LLMs, and consequently improving the
quality of generation across diverse models and downstream
reasoning tasks. Our main results can be summarized below.


In Section 4.1, we demonstrate that Ms-PoE consistently
enhances reasoning over long contexts for a range of tasks
in the ZeroSCROLLS benchmarks (Shaham et al., 2023),
all without the need for additional training. Additionally,
Ms-PoE exhibits superior performance when compared to
other methods in the field, including PI (Chen et al., 2023c)
and Self-Extend (Jin et al., 2024). [1] Detailed results of these
comparisons are shown in Tables 1 and 2.


In section 4.2, we highlight that Ms-PoE improves the context utilization and achieves consistent improvement when
varying the position of critical information within the input
context, as shown in Figure 1 & 5.


1 Although the primary intention of PI is to extend sequence
lengths, not specifically to tackle the “lost-in-the-middle” problem,
we include it in our comparison for its related concept and its
approach to positional information handling.



In Section 4.3, we conduct multiple ablation studies to assess the effectiveness of Ms-PoE under different scaling
ratios and selection strategies. Results are reported in Table 3 & 4.


**4.1. Enhanced Generation Quality**


We empirically validate the ability of Ms-PoE to enhance
long-context reasoning with a noteworthy improvement up
to 13 _._ 4 without additional training overhead. Notably, our
approach surpasses other competitive baselines, demonstrating improvements from 2 _._ 64 to 43 _._ 72.


**Experimental Setup.** In our experiments, we select
seven representative LLMs, including Llama-2-chat-7B and
13B (Touvron et al., 2023), StableBeluga-7B and 13B (Mahan et al.), and Vicuna-7B (Chiang et al., 2023), along with
its longer-context version (Vicuna-7B-16K). To comprehensively evaluate the long-context reasoning abilities of
LLMs, we choose seven tasks from ZeroSCROLLS (Shaham et al., 2023), spanning all four task categories: ① Document Summarization (Government and SummScreenFD),
② Query-Based Summarization (QMSum and SQuALITY),
③ Question Answering (Qasper and NarrativeQA), and ④
Information Aggregation (BookSumSort). Furthermore, we
compare Ms-PoE with other competitive methods on additional generation tasks, including Multi-document Question
Answering (MDQA) and Key-Value Retrieval (Liu et al.,
2023).


**Main Results.** Table 1 summarizes the main results, yielding several key observations: (i) By simply substituting the
original positional encoding module with our Ms-PoE, the
performance of LLMs consistently improves across all tasks
without additional training, resulting in an average performance enhancement ranging from **0.6** to **3.8** ; (ii) These



6


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**


_Table 1._ Comparsion results on ZeroSCROLLS (Shaham et al., 2023) benchmarks. The evaluation metrics for various tasks are tailored
as follows: GovReport, SummScreenFD, QMSum, and SQuALITY utilize the geometric mean of Rouge-1/2/L scores. Qasper and
NarrativeQA are assessed through the F1 score, while BookSumSort employs the concordance index.

|Models|Methods|GovReport SummScreenFD QMSum SQuALITY Qasper NarrativeQA BookSumSort|Average|
|---|---|---|---|
|Llama-2-7B-Chat<br>Llama-2-7B-Chat|Baseline<br>Ours|16.8<br>14.1<br>15.2<br>19.5<br>21.9<br>14.4<br>3.1<br>**17.7 (+0.9)**<br>**14.2 (+0.1)**<br>**15.8 (+0.6)**<br>**19.9 (+0.4)**<br>**25.1 (+3.2)**<br>**17.7 (+3.3)**<br>**5.8 (+2.7)**<br>**1**|15.0<br>**6.6 (+1.6)**|
|Llama-2-13B-Chat<br>Llama-2-13B-Chat|Baseline<br>Ours|15.4<br>12.3<br>15.1<br>18.9<br>19.0<br>15.0<br>5.7<br>**16.5 (+1.1)**<br>**13.1 (+0.8)**<br>**15.5 (+0.4)**<br>**19.2 (+0.3)**<br>**20.8 (+1.8)**<br>**17.0 (+2.0)**<br>**5.9 (+0.2)**<br>**1**|14.5<br>**5.4 (+0.9)**|
|StableBeluga-7B<br>StableBeluga-7B|Baseline<br>Ours|14.9<br>13.8<br>14.7<br>17.9<br>28.1<br>16.8<br>9.2<br>**16.6 (+1.7)**<br>**14.2 (+0.4)**<br>**15.2 (+0.5)**<br>**18.7 (+0.8)**<br>**36.9 (+8.8)**<br>**18.0 (+1.2)**<br>**14.2 (+5.0)**<br>**1**|16.5<br>**9.1 (+2.6)**|
|StableBeluga-13B<br>StableBeluga-13B|Baseline<br>Ours|5.7<br>7.1<br>12.9<br>13.3<br>19.2<br>13.4<br>4.8<br>**7.4 (+1.7)**<br>**7.4 (+0.3)**<br>12.8 (-0.1)<br>13.2 (-0.1)<br>**20.8 (+1.6)**<br>13.4 (+0)<br>**5.6 (+0.8)**<br>**1**|10.9<br>**1.5 (+0.6)**|
|Vicuna-7B<br>Vicuna-7B|Baseline<br>Ours|16.2<br>13.7<br>15.1<br>18.9<br>24.3<br>13.7<br>3.3<br>**20.2 (+4.0)**<br>**14.5 (+1.8)**<br>**15.4 (+0.3)**<br>**19.8 (+0.9)**<br>**34.7 (+13.4)**<br>**16.2 (+2.5)**<br>**10.5 (+7.2)**<br>**1**|15.0<br>**8.8 (+3.8)**|
|Vicuna-7B-16K<br>Vicuna-7B-16K|Baseline<br>Ours|20.2<br>13.9<br>16.2<br>20.1<br>32.3<br>18.8<br>29.9<br>**21.4 (+1.2)**<br>**14.3 (+0.4)**<br>16.2 (+0)<br>**20.2 (+0.1)**<br>**37.8 (+5.5)**<br>**21.0 (+2.2)**<br>**43.3 (+13.4)**<br>**2**|21.6<br>**4.9 (+3.3)**|



improvements hold consistently across different model sizes
of 7 billion and 13 billion parameters; (iii) The efficacy
extends to LLMs with varying sequence lengths, such as
Vicuna-7B and its extended version, Vicuna-7B-16K, both
showing improvements from **3.3** to **3.8** .


_Table 2._ Comparsion results with other competitive methods on
MDQA and Key-Value Retrival. Results are reported in accuracy.












|Models|Methods|MDQA<br>1 3 5 7 10 Average|
|---|---|---|
|Vicuna-7B|Baseline<br>PI<br>Self-Extend<br>Ms-PoE|64.0<br>61.0<br>57.4<br>58.4<br>64.8<br>61.12<br>65.2<br>62.4<br>60.0<br>60.4<br>64.0<br>62.40<br>64.7<br>63.7<br>61.4<br>59.8<br>62.0<br>62.32<br>**65.6**<br>**64.2**<br>**63.0**<br>**65.2**<br>**67.2**<br>**65.04**|
|Models|Methods|Key-Value Retrival<br>1<br>15<br>30<br>40<br>50<br>Average|
|Vicuna-7B|Baseline<br>PI<br>Self-Extend<br>Ms-PoE|92.0<br>25.8<br>8.0<br>25.4<br>30.0<br>36.24<br>96.4<br>76.4<br>61.4<br>64.6<br>**57.8**<br>67.60<br>88.6<br>63.8<br>76.2<br>59.4<br>42.0<br>66.00<br>**97.0**<br>**83.4**<br>**75.0**<br>**86.6**<br>**57.8**<br>**79.96**|



**Outperform other competitive methods.** We conduct a
thorough comparison between Ms-PoE and other competitive methods, including Positional Interpolation (PI) (Chen
et al., 2023c) and Self-Extend (Jin et al., 2024), both of
which modify position indices without utilizing head-wise
properties. For PI, we employ the scaling ratio as the average value of our method while for Self-Extend, we set
the group size as 2 with the local window size as 1024 .
The results presented in Table 2 consistently showcase the
superiority of our approach over other baselines, demonstrating improvements of up to 3 _._ 92 and 43 _._ 72 for MDQA and
Key-Value Retrival, respectively. Such improvements might
come from two primary factors. Firstly, the incorporation
of head-wise properties offers a more adaptive strategy for
positional modification. Secondly, our approach enhances
the general context utilization ability. Notably, our approach
demonstrates superiority even when the core document or
key is positioned at the end of the input, surpassing other



_Figure 5._ Comparison results for the multi-document question answering (MDQA) and key-value retrieval (KV retrieval) tasks.
Each subfigure depicts the comparison when varying the position
of critical information from the beginning to the end. For Vicuna

baselines with improvements ranging from 2 _._ 4 to 27 _._ 8 . This
performance surpasses the recent work (Peysakhovich &
Lerer, 2023), which addresses the “lost-in-the-middle” effect by reordering key documents and placing them at the
end of the input. When the identified core document is
already located at the recent area, such method can not
gain further improvements, while our approach offers a


We assess the context utlization ability of our approaches
on two tasks, including multi-document question answering (MDQA) and key-value retrieval (KV retrieval) tasks
from (Liu et al., 2023). Such tasks provide a good input
structure and offers the flexibility to switch the position
of crusial information, thus evaluate the context utilization


**Experimental Setup.** In the MDQA task, each input sample comprises ten documents and one question, with only



7


|igu<br>we<br>ac<br>f c<br>B,<br>as<br>er<br>er<br>ect<br>nd<br>lre<br>ai<br>ine<br>.2.<br>W<br>n<br>ng<br>ro<br>tru<br>f c<br>bil<br>x<br>le|Col2|Col3|Col4|Col5|Col6|Col7|Col8|Col9|Col10|Col11|
|---|---|---|---|---|---|---|---|---|---|---|
|_igu_<br>we<br>ac<br>f c<br>B,<br>as<br>er<br>er<br>ect<br>nd<br>lre<br>ai<br>_ne_<br>**.2.**<br>W<br>n<br>ng<br>ro<br>tru<br>f c<br>bil<br>**x**<br>le|||||||||||
|_igu_<br>we<br>ac<br>f c<br>B,<br>as<br>er<br>er<br>ect<br>nd<br>lre<br>ai<br>_ne_<br>**.2.**<br>W<br>n<br>ng<br>ro<br>tru<br>f c<br>bil<br>**x**<br>le|||||||||||
|_igu_<br>we<br>ac<br>f c<br>B,<br>as<br>er<br>er<br>ect<br>nd<br>lre<br>ai<br>_ne_<br>**.2.**<br>W<br>n<br>ng<br>ro<br>tru<br>f c<br>bil<br>**x**<br>le|||||||||||
|_igu_<br>we<br>ac<br>f c<br>B,<br>as<br>er<br>er<br>ect<br>nd<br>lre<br>ai<br>_ne_<br>**.2.**<br>W<br>n<br>ng<br>ro<br>tru<br>f c<br>bil<br>**x**<br>le|||||||||||
|_igu_<br>we<br>ac<br>f c<br>B,<br>as<br>er<br>er<br>ect<br>nd<br>lre<br>ai<br>_ne_<br>**.2.**<br>W<br>n<br>ng<br>ro<br>tru<br>f c<br>bil<br>**x**<br>le|_re_<br>rin<br>h s<br>riti<br>ple<br>eli<br>for<br>er,<br> b<br> of<br>ad<br>n f<br>_-gr_<br>** S**<br>e a<br>tw<br> (M<br>m (<br>ctu<br>ru<br>ity<br>**per**<br>co|_5_<br>g<br>ub<br>ca<br>a<br>ne<br>m<br> 2<br>y<br> <br>y<br>u<br>_a_<br>**u**<br>s<br>o<br><br>L<br>r<br>si<br> o<br>**i**<br>m|_._ Comp<br>(MDQ<br>fgure<br>l infor<br>se refe<br>s with<br>ance<br>023),<br>reorde<br>the in<br> locat<br>rther i<br>_ined_ s<br>**perior**<br>sess th<br>tasks,<br>DQA)<br>iu et<br>e and<br>al info<br>f LL<br>**menta**<br>prises|arison<br>A) an<br> depict<br>mation<br>r to Fi<br> impr<br>surpa<br>whic<br>ring<br>put.<br>ed at<br>mpro<br>trateg<br>** Cont**<br>e con<br> inclu<br> and k<br>al., 2<br> offer<br>rmati<br>Ms.<br>**l Set**<br> ten d|r<br>d<br>s<br> f<br>gu<br>ov<br>ss<br>h<br>ke<br>W<br>th<br>v<br>y<br>**e**<br>te<br>di<br>e<br>02<br>s<br>o<br>**up**<br>o|e<br> k<br>th<br>r<br>r<br>e<br>e<br>a<br>y<br>h<br>e<br>e<br>t<br>**x**<br>x<br>n<br>y<br>3<br>t<br>n,<br>**.**<br>c|sul<br>ey<br>e c<br>om<br>e 1<br>m<br>s t<br>dd<br> d<br>en<br> r<br>me<br>o i<br>**t U**<br>t u<br>g<br>-v<br>).<br>he<br> th<br> In<br>um|ts<br>-<br>o<br> t<br>.<br>e<br>h<br>re<br>o<br> <br>e<br>n<br>m<br>**t**<br>tl<br>m<br>al<br><br> f<br>u<br> <br>|f<br>v<br><br>h<br>nt<br>e<br>s<br>c<br>t<br>c<br>t<br>p<br>**i**<br>i<br><br>u<br>S<br>e<br>s<br>th<br>e|o<br>al<br>m<br>e<br>s<br> <br>s<br>u<br>h<br>e<br>s,<br>r<br>**li**<br>z<br>ul<br>e<br>u<br><br> <br>e<br>nt|


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**



one document being relevant to the question. For the KV
retrieval tasks, there are 50 key-value pairs with one question querying the value of the chosen key. In both tasks, we
systematically switch the important document or key-value
pair from the beginning to the end and report the accuracy
of the generated context. All results are averaged across
500 samples. The **Gap** accuracy metric is employed to assess the context utilization ability of LLMs, defined as the
gap between the best and worst accuracy when varying the
position of important information.


**Main Results.** As depicted in Figure 5 and 1, Ms-PoE
demonstrates consistent improvement across different models, tasks and critical positions. Even when the important
information exists in the sweet region (beginning and end)
of the input, Ms-PoE achieves significant performance improvements ranging from 3% to 6%, highlighting its efficacy
in enhancing generation quality. Moreover, the “lost-in-themiddle” issue is notably alleviated, with Ms-PoE quantitatively reducing the gap accuracy by approximately 2% to
4%, showcasing improved context utilization.


**4.3. Ablation Study and More Investigation**


This section conducts a further evaluation of the effec
tiveness of Ms-PoE by addressing the following questions:
_Q1:_ How does the effectiveness of Ms-PoE relate to the
head-wise selection strategy of the scaling ratio? _Q2:_ How
does the model perform with different scaling ratios?


_**A1:**_ **Positional awareness metrics achieve superior per-**
**formance compared to other strategies.** For a set of
scaling ratios **r** _∈_ _R_ _[n]_ _[h]_, where _n_ _h_ is the number of attention
heads, and using scaling ratios linearly ranging from 1.2 to
1.8, we evaluate various strategies for assigning these ratios
to different attention heads. These strategies include: ①
Random, which randomly assigns the scaling ratios to each
head within each layer; ② Sequential, performing the
assignment based on the original head order; ③ Entropy,
where we follow metrics measuring the sparsity level of
attention scores (Tian et al., 2023). Larger entropy implies
less sparse attention scores, indicating the model attends to
more tokens rather than just the beginning and end words,
so we assign a scaling ratio near to 1, and vice versa for
larger ratios. Results in Table 3 demonstrate that the proposed position-awareness effectively captures the head-wise
properties of LLMs, enhancing performance when critical
information is located at various positions—beginning, middle, or end. This leads to an average accuracy gain of 3 _._ 2
(65.3 v.s. 62.1).


_**A2:**_ **Ablation study of the scaling ratios.** We first examined the effect of uniform scaling ratios across all heads on
model performance. Our findings, outlined in Table 4, indicate that adjusting the scaling ratio between 0 _._ 5 and 2 _._ 5 can



_Table 3._ Ablation results of different ordering metrics. Experiments are conducted on Multi-Documents Question Answering

|task with the Vicuna-7B|model.|Col3|
|---|---|---|
|Methods|Begin<br>Middle<br>End|Average|
|Baseline|64.0<br>57.4<br>64.8|62.1|
|Random<br>Sequential|64.5<br>55.0<br>65.5<br>60.5<br>54.5<br>58.5|61.7<br>57.8|
|Entropy|63.5<br>59.5<br>64.0|62.3|
|Position-Awareness|**65.6**<br>**63.0**<br>**67.2**|**65.3**|



_Table 4._ Ablation results of the condensing ratios. Experiments are
conducted on Multi-Documents Question Answering task with the

|Vicuna-7B model.|Col2|Col3|
|---|---|---|
|Scaling Ratio|Begin<br>Middle<br>End|Average|
|1|64.0<br>57.4<br>64.8|62.1|



0.5 56.0 51.0 68.0 58.3

1.5 65.2 60.0 64.0 63.1

2 61.5 59.0 62.5 61.0

2.5 59.5 57.5 57.0 58.0


significantly enhance generative performance and mitigate
the ”lost-in-the-middle” effect by 1 _._ 0% ( 63 _._ 1% _v.s._ 62 _._ 1% ),
particularly with a ratio of 1 _._ 5 . Further testing with an average ratio of 1 _._ 5 across all heads revealed that an optimal
range exists between 1 _._ 2 and 1 _._ 8, leading to an additional
2 _._ 2% ( 65 _._ 3% _v.s._ 63 _._ 1% ) accuracy improvement with our
approach, Ms-PoE. Based on these results, we established
these ratios as our experimental standard.


**5. Conclusion**


In this paper, we present a plug-and-play strategy designed
to address the “lost-in-the-middle” challenge observed in
LLMs. This challenge stems from the persistent bias exhibited by LLMs towards the beginning and local content
within the input, leading to the neglect of crucial information in the middle. Our investigation reveals the effects
of position indice rescaling and the head-wise positionawareness property, leading to the introduction of Multiscale Positional Encoding (Ms-PoE). This approach enhances the capability of LLMs to effectively capture information in the middle of the context without the need for

additional fine-tuning. Comprehensive experiments conducted on Zero-SCROLLS benchmarks, multi-document
question-answering tasks, and key-value retrieval tasks con


8


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**



firm the effectiveness of Ms-PoE.


**6. Impact Statement**


The introduction of Multi-scale Positional Encoding (MsPoE) offers a simple yet effective approach to tackling the
challenge of processing long contexts in large language
models (LLMs). This enhancement significantly improves
LLMs’ capabilities to understand and reason over extensive
textual contexts. Ms-PoE can potentially impact numerous fields where processing long-context data is crucial,
such as in analyzing vast amounts of case law or detailed
patient histories. However, as we advance the boundaries
of Machine Learning and Artificial Intelligence, making
them increasingly powerful and applicable, it comes with
potential challenges and problems that must be carefully
addressed. For instance, there is a risk of exacerbating existing biases within AI, as processing longer contexts could
amplify the biases present in the training data. Additionally, the misuse of predictive insights derived from LLMs
presents a significant worry. To mitigate these concerns, we
advocate for ongoing ethical evaluations and the development of guidelines to ensure that the applications of LLM
advancements contribute positively to society.


**7. Acknowledgements**


We thank Dr. Yuandong Tian for interesting discussions on
this work.


**References**


Chen, G., Li, X., Meng, Z., Liang, S., and Bing, L. Clex:
Continuous length extrapolation for large language models. _arXiv preprint arXiv:2310.16450_, 2023a.


Chen, H., Pasunuru, R., Weston, J., and Celikyilmaz,
A. Walking down the memory maze: Beyond context limit through interactive reading. _arXiv preprint_
_arXiv:2310.05029_, 2023b.


Chen, S., Wong, S., Chen, L., and Tian, Y. Extending
context window of large language models via positional
interpolation. _arXiv preprint arXiv:2306.15595_, 2023c.


Chen, Y., Lv, A., Lin, T.-E., Chen, C., Wu, Y., Huang, F.,
Li, Y., and Yan, R. Fortify the shortest stave in attention:
Enhancing context awareness of large language models
for effective tool use. _arXiv preprint arXiv:2312.04455_,
2023d.


Chiang, W.-L., Li, Z., Lin, Z., Sheng, Y., Wu, Z., Zhang,
H., Zheng, L., Zhuang, S., Zhuang, Y., Gonzalez, J. E.,
Stoica, I., and Xing, E. P. Vicuna: An open-source
chatbot impressing gpt-4 with 90%* chatgpt quality,



March 2023. URL [https://lmsys.org/blog/](https://lmsys.org/blog/2023-03-30-vicuna/)
[2023-03-30-vicuna/.](https://lmsys.org/blog/2023-03-30-vicuna/)


Clark, K., Luong, M.-T., Le, Q. V., and Manning, C. D. Electra: Pre-training text encoders as discriminators rather
than generators. _arXiv preprint arXiv:2003.10555_, 2020.


Dao, T. FlashAttention-2: Faster attention with better parallelism and work partitioning. 2023.


Devlin, J., Chang, M.-W., Lee, K., and Toutanova, K. Bert:
Pre-training of deep bidirectional transformers for language understanding. _arXiv preprint arXiv:1810.04805_,
2018.


Du, X., Liu, M., Wang, K., Wang, H., Liu, J., Chen, Y.,
Feng, J., Sha, C., Peng, X., and Lou, Y. Classeval: A
manually-crafted benchmark for evaluating llms on classlevel code generation. _arXiv preprint arXiv:2308.01861_,
2023.


Edelman, B. L., Goel, S., Kakade, S., and Zhang, C. Inductive biases and variable creation in self-attention mecha
nisms. In _International Conference on Machine Learning_,
pp. 5793–5831. PMLR, 2022.


Ge, S., Zhang, Y., Liu, L., Zhang, M., Han, J., and Gao,
J. Model tells you what to discard: Adaptive kv cache
compression for llms. _arXiv preprint arXiv:2310.01801_,
2023.


Guo, M.-H., Lu, C.-Z., Hou, Q., Liu, Z., Cheng, M.-M., and
Hu, S.-M. Segnext: Rethinking convolutional attention
design for semantic segmentation. _Advances in Neural_
_Information Processing Systems_, 35:1140–1156, 2022.


Han, C., Wang, Q., Xiong, W., Chen, Y., Ji, H., and Wang, S.
Lm-infinite: Simple on-the-fly length generalization for
large language models. _arXiv preprint arXiv:2308.16137_,
2023.


Ivgi, M., Shaham, U., and Berant, J. Efficient long-text
understanding with short-text models. _Transactions of_
_the Association for Computational Linguistics_, 11:284–
299, 2023.


Jacobs, S. A., Tanaka, M., Zhang, C., Zhang, M., Song,
S. L., Rajbhandari, S., and He, Y. Deepspeed ulysses:
System optimizations for enabling training of extreme
long sequence transformer models. _arXiv preprint_
_arXiv:2309.14509_, 2023.


Jiang, A. Q., Sablayrolles, A., Mensch, A., Bamford, C.,
Chaplot, D. S., Casas, D. d. l., Bressand, F., Lengyel, G.,
Lample, G., Saulnier, L., et al. Mistral 7b. _arXiv preprint_
_arXiv:2310.06825_, 2023a.



9


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**



Jiang, A. Q., Sablayrolles, A., Roux, A., Mensch, A., Savary,
B., Bamford, C., Chaplot, D. S., Casas, D. d. l., Hanna,
E. B., Bressand, F., et al. Mixtral of experts. _arXiv_
_preprint arXiv:2401.04088_, 2024.


Jiang, H., Wu, Q., Luo, X., Li, D., Lin, C.-Y., Yang, Y., and
Qiu, L. Longllmlingua: Accelerating and enhancing llms
in long context scenarios via prompt compression. _arXiv_
_preprint arXiv:2310.06839_, 2023b.


Jin, H., Han, X., Yang, J., Jiang, Z., Liu, Z., Chang, C.Y., Chen, H., and Hu, X. Llm maybe longlm: Selfextend llm context window without tuning. _arXiv preprint_
_arXiv:2401.01325_, 2024.


Junqing, H., Kunhao, P., Xiaoqun, D., Zhuoyang, S., Yibo,
L., Yuxin, L., Hao, W., Qianguo, S., Songxin, Z., Zejian, X., et al. Never lost in the middle: Improving large
language models via attention strengthening question answering. _arXiv preprint arXiv:2311.09198_, 2023.


Krysci ´ nski, W., Rajani, N., Agarwal, D., Xiong, C., and ´
Radev, D. Booksum: A collection of datasets for
long-form narrative summarization. _arXiv preprint_
_arXiv:2105.08209_, 2021.


Lan, Z., Chen, M., Goodman, S., Gimpel, K., Sharma, P.,
and Soricut, R. Albert: A lite bert for self-supervised
learning of language representations. _arXiv preprint_
_arXiv:1909.11942_, 2019.


Li, J., Wang, M., Zheng, Z., and Zhang, M. Loogle: Can
long-context language models understand long contexts?
_arXiv preprint arXiv:2311.04939_, 2023.


Likhosherstov, V., Choromanski, K., and Weller, A. On
the expressive power of self-attention matrices. _arXiv_
_preprint arXiv:2106.03764_, 2021.


Lin, J., Tang, J., Tang, H., Yang, S., Dang, X., and
Han, S. Awq: Activation-aware weight quantization
for llm compression and acceleration. _arXiv preprint_
_arXiv:2306.00978_, 2023.


Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., and Liang, P. Lost in the middle:
How language models use long contexts. _arXiv preprint_
_arXiv:2307.03172_, 2023.


Mahan, D., Carlow, R., Castricato, L., Cooper, N.,
and Laforte, C. Stable beluga models. URL

[https://huggingface.co/stabilityai/
StableBeluga2](https://huggingface.
co/stabilityai/StableBeluga2).


Oren, M., Hassid, M., Adi, Y., and Schwartz, R. Transformers are multi-state rnns. _arXiv preprint arXiv:2401.06104_,
2024.



Penedo, G., Malartic, Q., Hesslow, D., Cojocaru, R., Cappelli, A., Alobeidli, H., Pannier, B., Almazrouei, E., and
Launay, J. The RefinedWeb dataset for Falcon LLM:
outperforming curated corpora with web data, and web
data only. _arXiv preprint arXiv:2306.01116_, 2023. URL
[https://arxiv.org/abs/2306.01116.](https://arxiv.org/abs/2306.01116)


Peng, B., Quesnelle, J., Fan, H., and Shippole, E. Yarn:
Efficient context window extension of large language
models. _arXiv preprint arXiv:2309.00071_, 2023.


Peysakhovich, A. and Lerer, A. Attention sorting combats
recency bias in long context language models. _arXiv_
_preprint arXiv:2310.01427_, 2023.


Press, O., Smith, N. A., and Lewis, M. Train short, test
long: Attention with linear biases enables input length
extrapolation. _arXiv preprint arXiv:2108.12409_, 2021.


Radford, A., Narasimhan, K., Salimans, T., Sutskever, I.,
et al. Improving language understanding by generative
pre-training. 2018.


Radford, A., Wu, J., Child, R., Luan, D., Amodei, D.,
Sutskever, I., et al. Language models are unsupervised
multitask learners. _OpenAI blog_, 1(8):9, 2019.


Re, C., Dao, T., Fu, D., and Goel, K. Can longer sequences ´
help take the next leap in ai?, June 2022. URL [https:](https://hazyresearch.stanford.edu/blog/2022-06-09-longer-sequences-next-leap-ai)
[//hazyresearch.stanford.edu/blog/](https://hazyresearch.stanford.edu/blog/2022-06-09-longer-sequences-next-leap-ai)
[2022-06-09-longer-sequences-next-leap-ai](https://hazyresearch.stanford.edu/blog/2022-06-09-longer-sequences-next-leap-ai) .
Accessed: 2024-01-29.


Shaham, U., Ivgi, M., Efrat, A., Berant, J., and Levy, O.
Zeroscrolls: A zero-shot benchmark for long text understanding. _arXiv preprint arXiv:2305.14196_, 2023.


Song, K., Wang, X., Cho, S., Pan, X., and Yu, D. Zebra: Extending context window with layerwise grouped
local-global attention. _arXiv preprint arXiv:2312.08618_,
2023a.


Song, S. L., Kruft, B., Zhang, M., Li, C., Chen, S., Zhang,
C., Tanaka, M., Wu, X., Rasley, J., Awan, A. A., et al.
Deepspeed4science initiative: Enabling large-scale scientific discovery through sophisticated ai system technologies. _arXiv preprint arXiv:2310.04610_, 2023b.


Su, J., Ahmed, M., Lu, Y., Pan, S., Bo, W., and Liu, Y.
Roformer: Enhanced transformer with rotary position
embedding. _Neurocomputing_, 568:127063, 2024.


Szegedy, C., Liu, W., Jia, Y., Sermanet, P., Reed, S.,
Anguelov, D., Erhan, D., Vanhoucke, V., and Rabinovich,
A. Going deeper with convolutions. In _Proceedings_
_of the IEEE conference on computer vision and pattern_
_recognition_, pp. 1–9, 2015.



10


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**



Szegedy, C., Vanhoucke, V., Ioffe, S., Shlens, J., and Wojna,
Z. Rethinking the inception architecture for computer vision. In _Proceedings of the IEEE conference on computer_
_vision and pattern recognition_, pp. 2818–2826, 2016.


Tay, Y., Dehghani, M., Abnar, S., Shen, Y., Bahri, D., Pham,
P., Rao, J., Yang, L., Ruder, S., and Metzler, D. Long
range arena: A benchmark for efficient transformers. In
_International Conference on Learning Representations_,
2020.


Team, M. N. Introducing mpt-7b: A new standard for
open-source, commercially usable llms, 2023. URL www.
mosaicml.com/blog/mpt-7b . Accessed: 202305-05.


Tian, Y., Wang, Y., Zhang, Z., Chen, B., and Du, S. Joma:
Demystifying multilayer transformers via joint dynamics
of mlp and attention. _arXiv preprint arXiv:2310.00535_,
2023.


Touvron, H., Martin, L., Stone, K., Albert, P., Almahairi,
A., Babaei, Y., Bashlykov, N., Batra, S., Bhargava, P.,
Bhosale, S., et al. Llama 2: Open foundation and finetuned chat models. _arXiv preprint arXiv:2307.09288_,
2023.


Varadi, M., Anyango, S., Deshpande, M., Nair, S., Natassia,
C., Yordanova, G., Yuan, D., Stroe, O., Wood, G., Laydon,
A., et al. Alphafold protein structure database: massively
expanding the structural coverage of protein-sequence
space with high-accuracy models. _Nucleic acids research_,
50(D1):D439–D444, 2022.


Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones,
L., Gomez, A. N., Kaiser, Ł ., and Polosukhin, I. Attention is all you need. _Advances in neural information_
_processing systems_, 30, 2017.


Wang, W., Dong, L., Cheng, H., Liu, X., Yan, X., Gao, J.,
and Wei, F. Augmenting language models with long-term
memory. _arXiv preprint arXiv:2306.07174_, 2023.


Xiao, G., Tian, Y., Chen, B., Han, S., and Lewis, M. Efficient streaming language models with attention sinks.
_arXiv preprint arXiv:2309.17453_, 2023.


Xu, P., Ping, W., Wu, X., McAfee, L., Zhu, C., Liu, Z., Subramanian, S., Bakhturina, E., Shoeybi, M., and Catanzaro,
B. Retrieval meets long context large language models.
_arXiv preprint arXiv:2310.03025_, 2023.


Yin, L., Wu, Y., Zhang, Z., Hsieh, C.-Y., Wang, Y., Jia, Y.,
Pechenizkiy, M., Liang, Y., Wang, Z., and Liu, S. Outlier
weighed layerwise sparsity (owl): A missing secret sauce
for pruning llms to high sparsity, 2023.


11



Zhang, P., Liu, Z., Xiao, S., Shao, N., Ye, Q., and Dou,
Z. Soaring from 4k to 400k: Extending llm’s context
with activation beacon. _arXiv preprint arXiv:2401.03462_,
2024.


Zhang, Y., Ni, A., Mao, Z., Wu, C. H., Zhu, C., Deb, B.,
Awadallah, A. H., Radev, D., and Zhang, R. Summˆ n: A
multi-stage summarization framework for long input dialogues and documents. _arXiv preprint arXiv:2110.10150_,
2021.


Zhang, Z., Sheng, Y., Zhou, T., Chen, T., Zheng, L., Cai,
R., Song, Z., Tian, Y., Re, C., Barrett, C., et al. H ´ ~~2~~ o:
Heavy-hitter oracle for efficient generative inference of
large language models. _arXiv preprint arXiv:2306.14048_,
2023.


Zheng, Q., Xia, X., Zou, X., Dong, Y., Wang, S., Xue, Y.,
Wang, Z., Shen, L., Wang, A., Li, Y., Su, T., Yang, Z.,
and Tang, J. Codegeex: A pre-trained model for code
generation with multilingual evaluations on humaneval-x.
In _KDD_, 2023.


Zhong, M., Liu, Y., Xu, Y., Zhu, C., and Zeng, M. Dialoglm:
Pre-trained model for long dialogue understanding and
summarization. In _Proceedings of the AAAI Conference_
_on Artificial Intelligence_, volume 36, pp. 11765–11773,
2022.


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**


**A. More Experiment Results**


**A.1. Position-Aware Attention Heads**


_Figure 6._ Visualization of ”position-aware” attention heads. Each row contains the attention pattern for the same heads when varying the
key documents within the inputs.


12


**Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding**


Figure 6 illustrates the attention patterns of ”position-aware” heads. Each row represents the attention pattern of the same
head. As the key document is positioned from the beginning to the end, the attention peak gradually shifts, indicating
robust positional awareness. It’s important to note that we randomly selected 9 attention heads with these ”position-aware”
properties, and these results were validated with different input samples and layers.


13


