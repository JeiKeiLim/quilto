# 17-hierarchical-memory-transformer

**Source:** `17-hierarchical-memory-transformer.pdf`

---

## **Accelerating Deep Neural Network guided MCTS using** **Adaptive Parallelism**



Tianxin Zu

zut@usc.edu
University of southern
California

USA



Viktor Prasanna

prasanna@usc.edu
University of southern
California

USA



[Yuan Meng](https://orcid.org/0000-0001-6468-8623) [∗]

ymeng643@usc.edu
University of southern
California

USA


**ABSTRACT**



[Qian Wang](https://orcid.org/0009-0003-6157-2459) [∗]

pwang649@usc.edu
University of southern
California

USA



Deep Neural Network guided Monte-Carlo Tree Search (DNNMCTS) is a powerful class of AI algorithms. In DNN-MCTS, a Deep
Neural Network model is trained collaboratively with a dynamic
Monte-Carlo search tree to guide the agent towards actions that
yields the highest returns. While the DNN operations are highly
parallelizable, the search tree operations involved in MCTS are
sequential and often become the system bottleneck. Existing MCTS
parallel schemes on shared-memory multi-core CPU platforms either exploit data parallelism but sacrifice memory access latency,
or take advantage of local cache for low-latency memory accesses
but constrain the tree search to a single thread. In this work, we
analyze the tradeoff of these parallel schemes and develop performance models for both parallel schemes based on the application
and hardware parameters. We propose a novel implementation that
addresses the tradeoff by adaptively choosing the optimal parallel
scheme for the MCTS component on the CPU. Furthermore, we propose an efficient method for searching the optimal communication
batch size as the MCTS component on the CPU interfaces with DNN
operations offloaded to an accelerator (GPU). Using a representative
DNN-MCTS algorithm - Alphazero on board game benchmarks,
we show that the parallel framework is able to adaptively generate
the best-performing parallel implementation, leading to a range of
1 _._ 5 × − 3 × speedup compared with the baseline methods on CPU
and CPU-GPU platforms.


**KEYWORDS**


monte-carlo tree search, deep learning, parallel computing


**1** **INTRODUCTION**


Deep Neural Network guided Monte Carlo Tree Search (DNNMCTS) methods have shown massive potential in modern AI benchmarks. For example, DNN-MCTS is the core in state-of-the-art algorithms, including Alphazero [ 14 ] in gaming, AlphaX [ 18 ] in neural
architecture search, CAPR [ 3 ] in recommendation systems, etc. In
traditional MCTS, an agent “looks ahead” the future scenarios by
constructing and traversing a partial search tree. In the search tree,
nodes correspond to states, and edges represent actions performed
by the agent. The key objective of an MCTS algorithm is guiding the
partial tree traversal so that the agent can focus on more important
nodes leading towards high rewards. To evaluate the importance of
nodes to be included in the partial tree, Monte-Carlo rollouts [ 4 ] are
adopted in traditional MCTS, where a possible outcome is sampled


∗ Both authors contributed equally to this research.



from the state by simulating from the state using an applicationspecific environment simulator. DNN-MCTS improves upon the
traditional MCTS by eliminating such Monte-Carlo rollouts. Instead of simulations, in DNN-MCTS [ 14 ], a node is evaluated using
a Deep Neural Network (DNN) trained on data sets collected online
through tree-based search. This not only enables high algorithm
performance without prior human knowledge but also replaces
sequential, application-specific simulation steps with dense tensor
operations, which leads to ample opportunities for parallelization
and hardware acceleration.

Training the DNN using MCTS is an extremely time-consuming
process. For example, a DNN-MCTS algorithm on the Go game
benchmark, AlphaGo Zero, was trained for 21 days [ 15 ]. Thus, enabling faster DNN-MCTS training is an important problem. In DNNMCTS, the DNN is collaboratively trained with the tree. Specifically,
data points collected during the MCTS tree-based search (with simulated final outcomes as ground truth) are used for updating the DNN
parameters; the value approximations returned by DNN inferences
are used for updating the tree nodes in the Monte Carlo search
tree during the tree-based search. In our initial experiments, the
tree-based search accounts for more than 85% of the total runtime

in an iteration of serial DNN-MCTS. A popular parallel algorithm
for accelerating the tree-based search process is tree-parallel DNNMCTS, it is widely adopted in many DNN-MCTS implementations
such as AlphaZero [15] and AlphaX [17].
In the tree-based search process of tree-parallel DNN-MCTS,
even though the independent DNN inferences from multiple nodes
can be executed in a data-parallel manner, it is challenging to obtain
linearly-scalable speedups wrt the number of processes allocated
to parallel workers. This is because multiple processes sharing the
same tree either require frequent synchronizations or are completely serialized to preserve the most up-to-date node parameters
for accurate node selection.

In this paper, we propose an adaptive-parallel methodology for
tree-parallel DNN-MCTS based on an analysis of tradeoffs between
two parallel implementations (local-tree and shared-tree). We target
the tree-based search process of DNN-MCTS, which involves intree operations and DNN inferences. We optimize the MCTS in-tree
operations on a shared-memory multi-core CPU architecture. Our
implementation support GPU accelerated DNN inferences. Our
contributions are:


  - We perform the tradeoff analysis between the two implementations (shared-tree and local-tree methods) and propose an acceleration methodology of adaptively selecting
the implementation given an arbitrary DNN-MCTS algorithm targeting a multi-core CPU.


  - We implement both local-tree and shared-tree parallel DNNMCTS as a single program template that allows compiletime adaptive selection of parallel implementations; the program template allows interfacing with existing high-level
libraries for simulating various benchmarks, and supports
offloading the DNN computations to accelerators.

  - We propose a design configuration workflow that decides
the optimal parallel method at compile time. This is achieved
using high-level performance models for two tree-parallel
DNN-MCTS implementations based on algorithm hyperparameters (e.g., tree fanout, tree depth), hardware specifications (e.g., number of threads, DDR bandwidth and
latency), and design-time profiling.

  - We utilize an efficient search method that determines the
best DNN-request-processing batch size in the design configuration workflow to fine-tune the DNN-MCTS performance on a CPU-GPU platform. This is achieved by overlapping DNN request transfers with in-tree operations and
minimizing the GPU wait time.

  - We successfully validated the proposed adaptive parallel
methodology by running the Gomoku board-game benchmark and achieved up to 3 × speedup than the baselines
using either parallel implementation alone.


**2** **BACKGROUND**

**2.1** **DNN-MCTS**


The complete DNN-MCTS training pipeline is an iterative process
composed of two stages: tree-based search and DNN training. The
tree-based search stage is guided by the DNN inference results on
a tree, and generates the datasets used for DNN training. The DNN
takes the current state _𝑠_ as the input, and outputs a value estimation
of _𝑠_ and a policy (i.e., the probabilities of taking each available action
from _𝑠_ ). Each node in the tree represents a certain environment
state. Each edge represents the action that transits from one state to
another, and tracks the visit counts and application-specific values
associated with the action. For example, in AlphaZero [ 14 ], each
edge maintains _𝑄_ ( _𝑠,𝑎_ ) - the expected reward (i.e. the Q value) for
taking action _𝑎_ from state _𝑠_ ; _𝑁_ ( _𝑠,𝑎_ ) - the number of times action _𝑎_
is taken from state _𝑠_ in all the iterations in a search stage; _𝑃_ ( _𝑠,_ - ) the policy returned by the DNN, which is the probability of taking
each action from the state _𝑠_ .

In the tree-based search stage, each iteration of the tree-based
search is composed of the following operations:


(1) **Node Selection:** The search starts from the current state
(root node of the tree) and traverses down the tree. At every
node traversed _𝑠_, the next edge is selected according to the
statistics stored in the search tree as follows:


_𝑎_ = _𝑎𝑟𝑔𝑚𝑥_ ( _𝑈_ ( _𝑠,𝑎_ )) _,_ where the UCT score



Yuan Meng, Qian Wang, Tianxin Zu, and Viktor Prasanna


(2) **Node Expansion & Evaluation:** When the tree traversal encounters an edge that was never visited before, the
search process adds a new successor node _𝑠_ [′], and initializes
_𝑄_ ( _𝑠_ [′] _,𝑎_ ) _, 𝑁_ ( _𝑠_ [′] _,𝑎_ ) to 0 for all its adjacent edges _𝑎_ . Accordingly, _𝑃_ ( _𝑠_ [′] _,_     - ) is derived from the DNN inference which
takes the new node _𝑠_ [′] as input; the DNN also outputs the
estimated reward value _𝑣_ ( _𝑠_ [′] _,_     - ).
(3) **Backup:** To synchronize the tree with the most recent node
evaluation, _𝑣_ ( _𝑠_ [′] _,_     - ) is propagated from the new leaf node
back to the root. At each tree level, the visit counts _𝑁_ is
incremented, and the state value _𝑄_ is accumulated using _𝑣_ .

After a fixed amount of iterations, the best move is picked at the root
node (i.e., the current state _𝑠_ _𝑡_ ) based on Equation 1. This generates a
training datapoint ( _𝑠_ _𝑡_ _,_ � _𝜋_ _𝑡_ _,𝑟_ ), where � _𝜋_ _𝑡_ is the action statistics at the
root, and _𝑟_ is the reward recorded at terminal states. These training
data points are later consumed by the DNN training stage.
In the DNN training stage, the DNN performs a stochastic gradient descent (SGD, [ 13 ]) using the data points generated in the
tree-based search state. For example, In AlphaZero [ 14 ], it updates
the DNN parameters _𝜃_ to minimizes the loss:

_𝑙_ = ∑︁ ( _𝑣_ _𝜃_ ( _𝑠_ _𝑡_ ) − _𝑟_ ) [2] −� _𝜋_ _𝑡_           - log [�] _𝑝_ � _𝜃_ ( _𝑠_ _𝑡_ ) [�] (2)

_𝑡_


where _𝑣_ _𝜃_ and _𝑝_ _𝜃_ are the value head and policy head of the DNN
output.
In our initial profiling of the sequential DNN-MCTS on Gomoku
benchmarks [ 16 ], the tree-based search stage account for more
than 85% of the complete training process. Therefore, there is a
critical need for parallelizing both the MCTS and DNN inference
processes in the tree-based search stage. _Our work focus on the_
_(variations of) Tree Parallelization [_ _2_ _,_ _8_ _]_ . This is recently the most
popular MCTS parallelization technique used in existing DNNMCTS implementations such as AlphaZero [ 14 ]. In Tree-Parallel
MCTS, after a worker traverses a certain node (path) during Node
Selection, a virtual loss _VL_ is subtracted from _𝑈_ of the traversed
edges to lower their weights, thus encouraging other workers to
take different paths. It also creates dependencies between workers
during the Node Selection. _VL_ is recovered later in the BackUp
phase. Note that _VL_ can either be a pre-defined constant value [ 2 ],
or a number tracking visit counts of child nodes [8].
In this work, we view the tree-based search stage as a composition of in-tree operations and DNN inference. The in-tree operations
are all the operations that access the tree in Node Selection, Node
Expansion, and BackUp phases, and the DNN inference refers to
Node Evaluation. Note that the target platform for in-tree operations is a multi-core CPU, and DNN inference may be executed on
the CPU or offloaded to an accelerator.


**2.2** **Related Work**


Other than tree-parallel MCTS targeted in this work, multiple other
parallel algorithms have been developed for high-throughput MCTS
and DNN-MCTS. Leaf-parallel MCTS [ 1 ] uses a single tree and creates multiple parallel node simulations at the same leaf node, but it
wastes parallelism due to the lack of diverse evaluation coverage
on different selected paths, which leads to algorithm performance
degrades [ 5 ]. Root-parallel MCTS [ 6 ] creates multiple trees at different workers and aggregates their statistics periodically, but still



_𝑈_ ( _𝑠,𝑎_ ) = _𝑄_ ( _𝑠,𝑎_ ) + _𝑐_ - _𝑃_ ( _𝑠,𝑎_ ) ·



~~√~~ Σ _𝑏_ _𝑁_ ( _𝑠,𝑏_ )

(1)
1 + _𝑁_ ( _𝑠,𝑎_ )



This leads the agents towards states with high reward values (exploitation), high policy-action probability, and low
visit counts (exploration). _𝑐_ is a pre-set constant controlling
the tradeoff between exploitation and exploration.


Accelerating Deep Neural Network guided MCTS using
Adaptive Parallelism


lets multiple workers visit repetitive states. The Speculated DNNMCTS [ 7 ] comply with the sequential in-tree operations, and uses
a speculative model in addition to the main model for faster node
evaluation. This preserves the decision-making quality of the sequential MCTS but introduces additional computations.
The original tree-Parallel MCTS [ 2 ] uses multiple workers to
share and modify the same tree, and uses mutex to avoid race conditions. However, the synchronization overhead can dominate the
memory-bound in-tree operations, making the achievable speedups
sub-optimal. [ 11 ] attempts to address this by developing a lock-free
tree-parallel method, but the agents trained cannot win against
root-parallel MCTS on hex game benchmarks without careful tuning of hyper-parameters. WU-UCT [ 8 ] puts multiple workers on
the same thread and executes them in a centralized manner using
a local tree, while parallelizing the node evaluations (simulations).
This avoids overheads from frequent thread-synchronizations, but
the speedup does not linearly scale up wrt allocated parallel resource when the sequential workers become the bottleneck [ 9, 10 ].
Overall, there are different tradeoffs wrt the execution speed of the
best-performing agents. Therefore, we are motivated to combine
the different advantages of a tree-Parallel MCTS with shared tree

[ 2 ] and local tree [ 8 ], and dynamically select between them to suit
different scenarios.


**(a) Shared-tree on multi-core system**


**(b) Execution timeline of the shared-tree method**


**Figure 1: Shared-tree method**


**3** **PARALLELIZATION SCHEMES AND**

**IMPLEMENTATION**

**3.1** **Parallelization Schemes**


Assume that we allocate _𝑁_ workers sharing the tree during the treebased search. We consider two methods to implement tree-parallel
MCTS on multi-core CPUs. These methods are characterized by
their usage of a local tree and a shared tree, respectively:



_3.1.1_ _Shared Tree._ The shared-tree method uses _𝑁_ threads in to
tal - it assigns each worker an individual thread. Each thread is
responsible for its own assigned worker’s in-tree operations and
DNN inference. The tree is stored in a shared memory (typically
DDR memory of the CPU), and nodes in the tree are distributed to
parallel workers as they access the tree. The shared-tree method
on a multi-core system is shown in Figure 1-(a). The in-tree operations by each work are protected with locks so that only one
worker can access a certain node at a time. The operation execution
timeline of the shared-tree method is shown in Figure 1-(b). All
workers start at a common root node, and the virtual loss applied
to the root children needs to be updated for all workers accessing
it. So, the time interval between consecutive workers involves the
overhead for communicating the root-level information through
share memory space (i.e., DDR), creating latency offsets between
workers. The main advantage of the shared-tree method is that intree operations are parallelized. The disadvantage is that the more
compute-intensive Node Evaluation process cannot fully utilize the
compute power provided by the parallel threads, since they need
to wait for the completion of in-tree operations by all workers, and
these in-tree operations are bounded by memory access latencies.


**(a) Local-tree on multi-core system**


**(b) Execution timeline of the local-tree method**


**Figure 2: Local-tree method**


_3.1.2_ _Local Tree._ The local-tree method uses _𝑁_ + 1 threads in total 
it uses a centralized master thread to manage the complete tree, and
it allocates _𝑁_ threads to execute the Node Evaluations for _𝑁_ work
ers (each thread is solely dedicated to the DNN inferences). The
complete tree is stored in the local memory of the master thread (e.g.,
cache memory). The master thread also manages a worker-thread
pool where the master thread communicates with each worker
thread through a FIFO (first-in-first-out) communication pipe. The
local-tree system is shown in Figure 2-(a). The master thread executes a _𝑤ℎ𝑖𝑙𝑒_ ( 1 ) loop; In each iteration, it selects new nodes to
send to worker threads, and checks for backup requests received


**Algorithm 1:** Adaptive Parallel DNN-MCTS


**1** **Function** main( _𝑓𝑙𝑎𝑔_𝑙𝑜𝑐𝑎𝑙_ ) **:**

**2** **for** ___ in training_episodes_ **do**

**3** Initialize _𝑒𝑛𝑣𝑖𝑟𝑜𝑛𝑚𝑒𝑛𝑡_


**4** Initialize _𝑑𝑎𝑡𝑎𝑠𝑒𝑡_


**5** **while** _not environment.terminal_ **do**


**6** **if** _𝑓𝑙𝑎𝑔_𝑙𝑜𝑐𝑎𝑙_ **then**

**7** _𝑎𝑝_ ← get_action_prior_l ( _𝑒𝑛𝑣𝑖𝑟𝑜𝑛𝑚𝑒𝑛𝑡_ )


**8** **else**


**9** _𝑎𝑝_ ← get_action_prior_s ( _𝑒𝑛𝑣𝑖𝑟𝑜𝑛𝑚𝑒𝑛𝑡_ )


**10** take action arg max ( _𝑎𝑝_ )

**11** _𝑟𝑒𝑤𝑎𝑟𝑑_ ← update ( _𝑒𝑛𝑣𝑖𝑟𝑜𝑛𝑚𝑒𝑛𝑡.𝑠𝑡𝑎𝑡𝑒_ )

**12** _𝑑𝑎𝑡𝑎𝑠𝑒𝑡_ .append ( _𝑒𝑛𝑣𝑖𝑟𝑜𝑛𝑚𝑒𝑛𝑡.𝑠𝑡𝑎𝑡𝑒_, _𝑎𝑝_, _𝑟𝑒𝑤𝑎𝑟𝑑_ )


**13** **for** ___ in SGD_iterations_ **do**

**14** batch ← sample( _𝑑𝑎𝑡𝑎𝑠𝑒𝑡_ )

**15** SGD_Train(batch)


from any worker in the worker-thread pool. The worker threads’
processes are completely independent of one another; they only
coordinate with the centralized master thread. The main advantage
of the local-tree method is that it can overlap the computation of
DNN inferences and in-tree operations by separating them into
different hardware resources (Figure 2-(b)); Also, for small-sized
trees that can fit in last-level cache, the memory access latencies in
in-tree operations are reduced compared to the shared-tree method.
The disadvantage is that all the in-tree operations are completely
serialized, leading to lower in-tree throughput.


**3.2** **Adaptive Parallelism: System Overview**


The local-tree and shared-tree methods have tradeoffs that suit different scenarios. The intuition is that when DNN inference throughput is the bottleneck, the local-tree method should be favored to
fully exploit the parallelism for independent Node Evaluations;
when the number of workers becomes large or the tree is very deep
such that the sequential in-tree operations become the bottleneck,
the shared-tree method should be utilized to parallelize the in-tree
operations between workers. In this work, we are motivated to
take the best of both works and develop a tree-parallel DNN-MCTS
implementation that is able to adaptively switch between the two
methods. This implementation is facilitated with an empirical model
to determine which method is best suited at compile time given an
arbitrary DNN-MCTS algorithm specification and multi-core CPU
device specification (later discussed in Section 4).
To support adaptive parallelism that enables switching between
the local-tree and shared-tree methods, we implement the DNNMCTS program as shown in Algorithm 1. The program is an iterative process of data collection (Algorithm 1, lines 3-12) and DNN
training (Algorithm 1, lines 13-15). Based on an input flag passed
to the main program (Algorithm 1, lines 6-9), it selects between the
shared-tree and local-tree methods, shown in Algorithm 2 and 3,
respectively.
In the shared-tree method, a pool of threads is spawned to execute all the in-tree operations and DNN inferences in parallel. When



Yuan Meng, Qian Wang, Tianxin Zu, and Viktor Prasanna


**Algorithm 2:** shared-tree based search


**1** **Function** get_action_prior_s( _𝑒𝑛𝑣𝑖𝑟𝑜𝑛𝑚𝑒𝑛𝑡_ ) **:**

**2** _𝑔𝑎𝑚𝑒_ ← copy( _𝑒𝑛𝑣𝑖𝑟𝑜𝑛𝑚𝑒𝑛𝑡_ )

**3** **for** ___ in num_playouts_ **do**

**4** add threadsafe_rollout( _𝑔𝑎𝑚𝑒_ ) to thread pool


**5** wait for threads to finish all work

**6** _𝑎𝑐𝑡𝑖𝑜𝑛_ _ _𝑝𝑟𝑖𝑜𝑟_ ← normalized root’s children list wrt visit

count


**7** **return** _𝑎𝑐𝑡𝑖𝑜𝑛_ _ _𝑝𝑟𝑖𝑜𝑟_


**8** **Function** threadsafe_rollout( _𝑔𝑎𝑚𝑒_ ) **:**

**9** _𝑛𝑜𝑑𝑒_ ← _𝑟𝑜𝑜𝑡_


**10** **while** _𝑛𝑜𝑑𝑒_ _is not leaf_ **do**

**11** _𝑛𝑜𝑑𝑒_ ← _𝑛𝑜𝑑𝑒_ ’s child with highest UCT score

**12** _𝑔𝑎𝑚𝑒_ execute the corresponding move


**13** obtain _𝑙𝑜𝑐𝑘_


**14** update _𝑛𝑜𝑑𝑒_ ’s UCT score with virtul loss


**15** release _𝑙𝑜𝑐𝑘_


**16** _𝑝𝑟𝑖𝑜𝑟𝑠_, _𝑣𝑎𝑙𝑢𝑒_ ← neural_network_simulate( _𝑔𝑎𝑚𝑒_ )

**17** _𝑛𝑜𝑑𝑒_ create children list according to _𝑝𝑟𝑖𝑜𝑟𝑠_


**18** obtain _𝑙𝑜𝑐𝑘_


**19** backup( _𝑛𝑜𝑑𝑒_, _𝑣𝑎𝑙𝑢𝑒_ )


**20** release _𝑙𝑜𝑐𝑘_


**21** **return**


a function is added to the thread pool (Algorithm 2, line 4), the input
of the function is sent to an available thread, and the function is
executed on the same thread. In the case of the shared-tree method,
the function executed by each thread is “threadsafe_rollout". It first
traverses the tree from root to leaf, performing node selection, then
performing node evaluation through “neural_network_simulate",
followed by node expansion and backup. During the virtual loss
update and backup, multiple threads may share write accesses to
the same nodes, so locks are used to ensure atomic accesses.
In the local-tree method, a centralized master thread is responsible for all the in-tree operations, and a thread pool is spawned to
execute all the DNN inferences asynchronously in parallel. Specifically, the master thread executes the “rollout_n_times" (Algorithm
3, line 6-17). It repeatedly performs node selection, expansion, and
backup, and assigns a “neural_network_simulate" function as node
evaluation request to the thread pool through a first-in-first-out
queue. When all the threads are occupied by DNN inferences in
the thread pool, the master thread waits until receiving a value for
backup. Otherwise, it continues with the in-tree operation loop to
generate node evaluation requests.


**3.3** **Accelerator-offloaded DNN Inference**


Our implementation also supports offloading the DNN inferences
onto a GPU. We utilize a dedicated accelerator queue for accumulating DNN inference task requests produced by the tree selection
process. When the queue size reaches a predetermined threshold,
all tasks are submitted together to the GPU for computation. Acceleration of DNN inferences is particularly important, especially


Accelerating Deep Neural Network guided MCTS using
Adaptive Parallelism


**Algorithm 3:** local-tree based search


**1** **Function** get_action_prior_l( _𝑔𝑜𝑚𝑜𝑘𝑢_ ) **:**

**2** rollout_n_times( _𝑔𝑜𝑚𝑜𝑘𝑢_, _𝑛𝑢𝑚_ _ _𝑝𝑙𝑎𝑦𝑜𝑢𝑡𝑠_ )

**3** _𝑎𝑐𝑡𝑖𝑜𝑛_ _ _𝑝𝑟𝑖𝑜𝑟_ ← normalized root’s children list wrt visit

count


**4** **return** _𝑎𝑐𝑡𝑖𝑜𝑛_ _ _𝑝𝑟𝑖𝑜𝑟_


**5** **Function** rollout_n_times( _𝑔𝑜𝑚𝑜𝑘𝑢, 𝑛𝑢𝑚_𝑝𝑙𝑎𝑦𝑜𝑢𝑡𝑠_ ) **:**

**6** **for** ___ in num_playouts_ **do**

**7** _𝑛𝑜𝑑𝑒_ ← _𝑟𝑜𝑜𝑡_


**8** **while** _𝑛𝑜𝑑𝑒_ _is not leaf_ **do**

**9** _𝑛𝑜𝑑𝑒_ ← _𝑛𝑜𝑑𝑒_ ’s child with highest UCT score

**10** _𝑔𝑎𝑚𝑒_ execute the corresponding move


**11** add neural_network_simulate( _𝑔𝑎𝑚𝑒_ ) to thread
pool

**12** **if** _number of tasks in thread pool_ ≥ _number of_

_threads_ **then**


**13** wait for a task to finish in the thread pool

**14** _𝑝𝑟𝑖𝑜𝑟𝑠_, _𝑣𝑎𝑙𝑢𝑒_ ← result of the task

**15** _𝑛𝑜𝑑𝑒_ create children list according to _𝑝𝑟𝑖𝑜𝑟𝑠_

**16** backup( _𝑛𝑜𝑑𝑒_, _𝑣𝑎𝑙𝑢𝑒_ )


**17** **return**


when the total latency of in-tree operations is relatively small. However, it does require careful tuning of the communication batch size
associated with the accelerator queue.
In the case of the shared-tree method, the communication batch
size is always set to the number of threads employed (i.e., thread
pool size). This is because the selection processes are parallel, resulting in the nearly simultaneous arrival of all inference tasks,
leaving only a small gap to wait for the inference queue to be full.
The case of the local-tree method necessitates empirical tuning
of the communication batch size. This is because the selection

processes on the master thread are sequential and lead to long
waiting times by the worker threads; submitting a small batch of
inference tasks before the worker threads reach full capacity can
help reduce accelerator waiting time, overlapping DNN inference
computation with in-tree operations. Our empirical exploration of
the communication batch size can be found in Section 4.2 and 5.2.


**4** **PERFORMANCE ANALYSIS FOR**

**ADAPTIVE PARALLELISM**

**4.1** **Performance Model**


In this section, we provide a theoretical analysis of the time performance to understand the tradeoff between the shared tree and
local tree methods. The main parallel parameters that affect their
performance include the number of threads, the latency of executing in-tree operations and inferences on each thread, and the data
access and/or data transfer latencies.
Assuming the complete tree-based search process is conducted
on a multi-core CPU with a thread pool size of _𝑁_, the amortized
latency for each iteration of the shared tree method on a multi-core



CPU can be estimated as:


_𝑇_ _𝑠ℎ𝑎𝑟𝑒𝑑_ _[𝐶𝑃𝑈]_ [≈] _[𝑇]_ [shared tree access] [ ×] _[ 𝑁]_ [+] _[𝑇]_ _[𝑠𝑒𝑙𝑒𝑐𝑡]_ [+] _[𝑇]_ _[𝑏𝑎𝑐𝑘𝑢𝑝]_ [+] _[𝑇]_ _𝐷𝑁𝑁_ _[𝐶𝑃𝑈]_ (3)


The _𝑇_ shared tree access refers to the latencies that occurred in multiple
threads accessing CPU-shared memory (DDR) as they traverse the
same node. For selection and backup in a shared tree, this overhead
is non-avoidable as all parallel workers start from the same root
node. The in-tree operations latency and the DNN inference latency
are summed up since they execute sequentially on each thread.
If we offload the batched DNN computations onto a GPU, the periteration latency can be estimated by replacing the DNN inference
execution time with _𝑇_ _[𝐺𝑃𝑈]_
_𝐷𝑁𝑁_ [, which contains the PCIe data transfer]
overhead and the actual computation time.


_𝑇_ _𝑠ℎ𝑎𝑟𝑒𝑑_ _[𝐶𝑃𝑈]_ [−] _[𝐺𝑃𝑈]_ ≈ _𝑇_ shared tree access × _𝑁_ + _𝑇_ _𝑠𝑒𝑙𝑒𝑐𝑡_ + _𝑇_ _𝑏𝑎𝑐𝑘𝑢𝑝_

+ _𝑇_ _𝐷𝑁𝑁_ _[𝐺𝑃𝑈]_ [(] _[𝑏𝑎𝑡𝑐ℎ]_ [=] _[ 𝑁]_ [)] (4)


The amortized latency for each iteration of the local tree method
on a multi-core CPU can be estimated as:


_𝑇_ _𝑙𝑜𝑐𝑎𝑙_ _[𝐶𝑃𝑈]_ [≈] _[𝑚𝑎𝑥]_ [((] _[𝑇]_ _[𝑠𝑒𝑙𝑒𝑐𝑡]_ [+] _[𝑇]_ _[𝑏𝑎𝑐𝑘𝑢𝑝]_ [) ×] _[ 𝑁,𝑇]_ _𝐷𝑁𝑁_ _[𝐶𝑃𝑈]_ [)] (5)


In the local tree method, the in-tree operations and DNN inferences are overlapped. Therefore, the per-iteration execution time is
bounded by either the DNN inference latency or the total latency
of the sequential in-tree operations.


_𝑇_ _𝑙𝑜𝑐𝑎𝑙_ _[𝐶𝑃𝑈]_ [−] _[𝐺𝑃𝑈]_ ≈ _𝑚𝑎𝑥_ {( _𝑇_ _𝑠𝑒𝑙𝑒𝑐𝑡_ + _𝑇_ _𝑏𝑎𝑐𝑘𝑢𝑝_ ) × _𝑁,_

_𝑇_ _𝑃𝐶𝐼𝑒_ _,𝑇_ _𝐷𝑁𝑁_ _[𝐺𝑃𝑈]_ − _𝑐𝑜𝑚𝑝𝑢𝑡𝑒_ [(] _[𝑏𝑎𝑡𝑐ℎ]_ [=] _[ 𝐵]_ [)}] (6)


For batched DNN computations on GPU, we select a (sub-)batch
size _𝐵_ _< 𝑁_ such that _[𝑁]_

_𝐵_ [CUDA streams [] [12] [] are initiated, each]
CUDA stream bulk-processes the node evaluation (DNN inference)
requests after _𝐵_ loop counts of in-tree operations. Therefore, the
timeline of the local Tree using a CPU-GPU platform can be visualized similarly to that depicted in Figure 5; The only differences
are (1) the _𝑁_ worker threads are replaced with _[𝑁]_ _𝐵_ [CUDA streams,]

and (2) the blue-colored pipe communication arrows appear every
_𝐵_ iterations (instead of 1 iteration) of in-tree operations.


**4.2** **Design Configuration Workflow**


To decide the parallel method and relevant design parameters (i.e.,
accelerator inference batch size) at compile time, we first obtain
_𝑇_ _[𝐶𝑃𝑈]_
_𝐷𝑁𝑁_ [,] _[ 𝑇]_ _[𝑠𝑒𝑙𝑒𝑐𝑡]_ [and] _[ 𝑇]_ _[𝑏𝑎𝑐𝑘𝑢𝑝]_ [of a single worker on a single thread by]
profiling their amortized execution time on the target CPU for one
iteration. The DNN for profiling is filled with random parameters
and inputs of the same dimensions defined by the target algorithm
and application. The _𝑇_ _𝑠𝑒𝑙𝑒𝑐𝑡_ and _𝑇_ _𝑏𝑎𝑐𝑘𝑢𝑝_ are measured on a synthetic tree constructed for one episode (i.e., multiple iterations)
with random-generated UCT scores, emulating the same fanout
and depth limit defined by the DNN-MCTS algorithm. These designtime profiled latencies will provide a close prediction for the actual
latencies at run time. We can also obtain _𝑇_ _𝐷𝑁𝑁_ _[𝐶𝑃𝑈]_ [−] _[𝐺𝑃𝑈]_ including
the computation and data migration latency. In our implementation, the tree is managed as a dynamically allocated array of node
structs that resides in the CPU DDR memory. Therefore, we estimate _𝑇_ shared tree access as the DDR access latency documented for
the target CPU device. These are plugged into the performance


models for _𝑇_ _[𝐶𝑃𝑈]_
_𝑠ℎ𝑎𝑟𝑒𝑑_ [and] _[ 𝑇]_ _𝑙𝑜𝑐𝑎𝑙_ _[𝐶𝑃𝑈]_ [at compile time to decide the optimal]
parallel method for an arbitrary DNN-MCTS algorithm on a CPU.
For exploring the design space on a CPU-GPU platform, an
additional parameter _𝐵_ (i.e., number of cuda streams, each processing a sub-batch) can affect the performance of the local tree
method. A naive method is to iterate over all the possible values for
_𝐵_ ( _𝐵_ ∈[ 1 _, 𝑁_ ]) and empirically run an episode to test the average
latency of each iteration. However, this makes the design space
exploration complexity linearly proportional to _𝑁_ and hard to scale
to very large multi-core and accelerator systems. To address this,
we make the following observations to equation 6:




- ( _𝑇_ _𝑠𝑒𝑙𝑒𝑐𝑡_ + _𝑇_ _𝑏𝑎𝑐𝑘𝑢𝑝_ ) remains constant or monotonically decreases with increasing _𝐵_ . This is because the Expand operation waits for a batch of inferences to complete the UCT
score of the newly added nodes before they can be traversed
in Backup and Selection. The higher the CUDA stream
batch size _𝐵_, the less frequently the nodes get available
to be traversed (the frequency of making new node-UCT
scores available is about once per _[𝑁]_ _𝐵_ [loop counts on the]

Master Thread). This (increasing _𝐵_ ) may in turn make the
total tree depths traversed by Selection and Backup smaller
due to less-frequent node insertions. Therefore, the first
term of equation 6 should be a constant or monotonically
decreasing sequence wrt _𝐵_ ∈{1 _, ..., 𝑁_ }.

- _𝑇_ _𝑃𝐶𝐼𝑒_ is the time for transferring a total of _𝑁_ data samples
(i.e., DNN inference requests) between the CPU and GPU
through a PCIe interconnection. It can be viewed as _[𝑁]_



_𝐵_
transfers, each transfer processes a batch of _𝐵_ data samples.
Each transfer is associated with a fixed communication and
kernel launch latency _𝐿_ . Therefore, _𝑇_ _𝑃𝐶𝐼𝑒_ can be modeled
as ( _[𝑁]_ [) ×] _[ 𝐿]_ [+] _𝑁_ [. Based on this model,] _[ 𝑇]_ _[𝑃𝐶𝐼𝑒]_ [is]



as ( _[𝑁]_ _𝐵_ [) ×] _[ 𝐿]_ [+] PCIe bandwidth _𝑁_ [. Based on this model,] _[ 𝑇]_ _[𝑃𝐶𝐼𝑒]_ [is]

expected to be a monotonically decreasing sequence wrt
_𝐵_ ∈[1 _, 𝑁_ ].

- _𝑇_ _[𝐺𝑃𝑈]_
_𝐷𝑁𝑁_ [(] _[𝑏𝑎𝑡𝑐ℎ]_ [=] _[ 𝐵]_ [)] [ is expected to monotonically increase]
with increasing _𝐵_ . This is because larger _𝐵_ leads to higher
computational workloads.

- Based on Equation 6, the element-wise maximum of two
monotonically decreasing sequences ( ( _𝑇_ _𝑠𝑒𝑙𝑒𝑐𝑡_ + _𝑇_ _𝑏𝑎𝑐𝑘𝑢𝑝_ )
and _𝑇_ _𝑃𝐶𝐼𝑒_ ) is also a monotonically decreasing sequence.
The element-wise maximum of this resulting monotonically decreasing sequence and a monotonically increasing
sequence ( _𝑇_ _𝐷𝑁𝑁_ _[𝐺𝑃𝑈]_ [(] _[𝑏𝑎𝑡𝑐ℎ]_ [=] _[ 𝐵]_ [)] [) should be a “V-sequence"]
which is a sequence that first monotonically decreases, then
monotonically increases wrt _𝐵_ .



Essentially, we want to search the design space of _𝐵_ and find its
value yielding the minimum execution time, i.e., arg min _𝐵_ _𝑇_ _𝑙𝑜𝑐𝑎𝑙_ _[𝐶𝑃𝑈]_ [−] _[𝐺𝑃𝑈]_ .
Based on the above observations, this enables us to exploit the
property of a “V-sequence", and develop an efficient algorithm to
determine _𝐵_ at design time. We achieve this by modeling the problem of finding the best-performing CUDA stream batch size _𝐵_ as
the problem of finding the minimum value of a “V-sequence" _𝑇_
( _𝑇_ is the array of per-iteration latency across different values of
_𝐵_ ∈{ 1 _, ..., 𝑁_ } ). Instead of testing every possible value for _𝐵_ ∈[ 1 _, 𝑁_ ],
we can sample a subset with a reduced complexity of _𝑂_ (log _𝑁_ ) as
shown in Algorithm 4. Note that this is the mirroring problem of



Yuan Meng, Qian Wang, Tianxin Zu, and Viktor Prasanna


finding the maximum value of a bitonic sequence in _𝑂_ (log _𝑁_ ) time
using binary search [19].


**Algorithm 4:** Exploring the optimal CUDA stream batch

size _𝐵_


**1** **Function** FindMin( _𝑇_ _, 𝑙𝑜, ℎ𝑖_ ) **:**

**2** **if** _𝑙𝑜_ == _ℎ𝑖_ **then**


**3** **return** _𝐵_ ← _𝑙𝑜_


**4** _𝑚𝑖𝑑_ = _[𝑙𝑜]_ [+] _[ℎ𝑖]_

~~2~~
**5** Test Run with _𝐵_ = _𝑚𝑖𝑑_ and _𝐵_ = _𝑚𝑖𝑑_ + 1


**6** Record amortized latency _𝑇_ [ _𝑚𝑖𝑑_ ] _,𝑇_ [ _𝑚𝑖𝑑_ + 1]

**7** **if** _𝑇_ [ _𝑚𝑖𝑑_ ] ≥ _𝑇_ [ _𝑚𝑖𝑑_ + 1] **then**

**8** **return** FindMin( _𝑇_, _𝑚𝑖𝑑_ + 1, _ℎ𝑖_ )


**9** **else**


**10** **return** FindMin( _𝑇_, _𝑙𝑜_, _𝑚𝑖𝑑_ )


Note that for each Test Run (Algorithm 4 line 5), we do not need
to run the DNN-MCTS until policy convergence; we only profile
the latency performance in a single move (i.e., get_action_prior
functions in Algorithm 2 and 3). This is because each move made
in the complete DNN-MCTS training loop has the same amount of
computations.


**5** **EVALUATION**

**5.1** **Experiment Setup**


**Benchmark and hyper-parameters:** We use the Gomoku game
benchmark [ 20 ] to evaluate the performance of our proposed method.
The board size (i.e., size of the input state to the policy/value network) is 15 × 15, the neural network is composed of 5 convolution
layers and 3 fully-connected layers; The tree size limit per move
is 1600 (i.e., The total number of selection-expansion-inferencebackup operations performed per agent-move is 1600).
**Hardware platform specifications:** We use the AMD Ryzen
Threadripper 3990X @ 2.2GHz as our target CPU platform. It has
64 cores (2 threads per core). The last-level cache size is 256 MB,
and has a 8 × 32-GB DDR4. The CPU is connected with a NVIDIA

RTX A6000 GPU through PCIe 4.0.
**Evaluation metrics:** We conduct experiments to evaluate both
the speed and parallel algorithm performance. The speed is measured through (1) the amortized per-worker-iteration latency in
the tree-based search stage (Section 5.3), obtained by running and
averaging all the 1600 iterations for making a move; and (2) the
overall training throughput (Section 5.4) in terms of processed samNumber of samples processed per episode
ples/second, obtained by ~~�~~ (Tree-based search time + DNN update time) .
Note that one sample is obtained by executing all 1600 rounds of
in-tree operations and DNN inferences in a move. The algorithm
performance (Section 5.5) is measured using the loss of the DNN
(Equation 2). The lower the loss, the more accurately the DNN is
able to predict the probability of winning at each state and action,
and the better the MCTS at guiding the moves toward the winning

state.


Accelerating Deep Neural Network guided MCTS using
Adaptive Parallelism


**5.2** **Design Exploration of Host-Accelerator**
**Communication Batch Size**


We show the performance obtained during the design configuration
process for choosing the CUDA stream batch size _𝐵_ in Figure 3,
specific to the local-tree method mapped to a CPU-GPU heterogeneous platform. We only perform this design exploration for
the cases when the available number of workers _𝑁_ ≥ 16. This is

because _𝑁_ ≥ 16 is the threshold where the shared-tree method
starts to outperform the local-tree method with full-batched (batch
size = _𝑁_ ) inferences on GPU (later discussed in Section, Figure 5),
and the question of whether choosing an alternative batch size could
help improve the local-tree performance arises. We can observe


**Figure 3: Design Exploration of Inference Batch Size**


that at smaller batch sizes, sub-batches of inferences are serialized, which hinders the performance. The extreme case is at batch
size = 1, where the serial inferences dominate the runtime, making
the amortized iteration latency high such that even changing _𝑁_
does not affect the performance. At larger batch sizes, inferences
are parallelized with a higher degree on the GPU, but the inference
request is made after waiting for all the serial in-tree operations to
complete on the master thread, leading to a large overhead. The
extreme case is at batch size = _𝑁_, the GPU waits for all the _𝑁_ before
it can start the computation; the _𝑁_ in-tree operations at the master
thread is a non-trivial overhead such that they contribute to higher
amortized latency at _𝑁_ = 64 compared to _𝑁_ = 16 or 32. Our design
exploration finds the balance point where there are enough inferences within each sub-batch to saturate GPU parallelism, while
enough requests are also made across sub-batches such that the
GPU computation can overlap with the computations on the CPU
master thread (i.e., GPU does not have to be idling and waiting for
CPU computation to finish). Based on our test runs, the optimal
batch sizes are 8 when _𝑁_ = 16, and 20 when _𝑁_ = 32 or 64.


**5.3** **Tree-based Search Iteration Latency**


We plot the amortized per-worker-iteration latency in the treebased search stage in Figure 4 and 5. Note that a worker iteration
is one round of Node Selection, Node Expansion, Node Evaluation
(DNN inference), and BackUp executed by one worker. In each
move, 1600 such worker-iteration are executed by all the _𝑁_ parallel
workers. We obtain the amortized per-worker-iteration latency by



dividing the total time for a move by 1600. The higher _𝑁_ is, due to
more parallelism exploited, the lower the total time for a move (and
the amortized per-worker-iteration latency) is. For the CPU-only


**Figure 4: Iteration latency, CPU-only**


implementation, each worker is assigned a separate CPU thread
for performing one node evaluation (i.e., DNN inference). In Figure
4, we observe that under different configurations (number of workers used), the optimal method can be different. Our method using
adaptive parallelism is able to always choose the optimal method,
achieving up to 1 _._ 5 × speedup compared to either the local tree or
the shared tree baselines on the CPU-only platform. For the CPU

**Figure 5: Iteration latency, CPU-GPU, batched inference**


GPU implementation, a communication buffer is used to collect a
batch of node evaluation requests before sending them to the GPU
for performing a batched DNN inference. In Figure 5, we observe
that if we set the buffer (batch) size, the amortized latency using
the local tree method gets higher as _𝑁_ increases over 16. At _𝑁_ = 16,
our implementation chooses the shared tree method. At _𝑁_ = 32
and 64, using the optimal batch size returned by Algorithm 4, the
local tree method combined with overlapped GPU inferences outperforms the shared tree method with full-batched GPU inferences.
Overall, on a CPU-GPU heterogeneous platform, our method using
the adaptive parallelism achieves up to 3 _._ 07 × speedup compared to
either the local tree or the shared tree baselines.


**5.4** **Throughput Analysis**


We plot the overall DNN-MCTS training throughput (processed
samples per second) for both the CPU-only and CPU-GPU platforms
in Figure 6, varying the number of workers used in the tree-based
search. The throughput numbers are obtained by applying the optimal parallel method and design configuration returned by our design configuration workflow. Overall, CPU-GPU implementations
show higher throughput compared to CPU-only implementations.
In the CPU-GPU implementations, the tree-based search process
produces samples and the training process (completely offloaded
to GPU) consumes samples. The training process execution time
is hidden by the tree-based search time, especially when there is
a small number of workers such that the in-tree operations and
DNN inferences become the bottleneck. As the number of work
ers increases, we observe near-linear improvements in throughput,
since the time spent producing the same number of samples for
training is reduced. When the number of agents increases above 16,
the tree-based search time is reduced to the extent that it is lower

than the training time. As a result, the throughput improvement
becomes less obvious. In the CPU-only implementations, given the


**Figure 6: Training throughput under optimal configurations**


limited number of available CPU hardware threads, we are able to
allocate 32 threads for conducting training on the CPU (these are
different threads than those used for DNN-MCTS parallel workers).
In contrast to GPU-accelerated training, CPU-based DNN training
now becomes the bottleneck even for a small number of DNN
MCTS workers. With a different number of workers allocated to
the tree-based search process, the compute power provided to the
training process is fixed (32 threads). Therefore, the throughput
improvements from increasing the number of DNN-MCTS workers
are not as scalable as the CPU-GPU implementations. Still, we are
able to adaptively choose the best-performing parallel method and
design configurations. The optimal methods used at different hardware platforms and available resources (i.e., number of workers)
are annotated in Figure 6.


**5.5** **Algorithm Performance**


We show the DNN loss over time as the measurement of parallel DNN-MCTS training algorithm performance in Figure 7. The



Yuan Meng, Qian Wang, Tianxin Zu, and Viktor Prasanna


experiments are conducted on the CPU-GPU platform using the
optimal parallel configurations for 4, 16, and 64 workers. As we
introduce parallel workers for the tree-based search, the algorithm
is modified. This is because in the serial tree search, every iteration accesses the most up-to-date tree information modified by the
previous iteration; while in the tree-parallel implementations, a
worker traversing the tree may not obtain the newest node UCT
scores because the node evaluation (i.e., DNN inference) of other
workers have not completed. The more parallel workers are used,
the higher the effect is from such obsolete-tree-information. As a
result, the training samples generated (states traversed and actions
taken based on tree search) in the parallel version are not the same
as the 1-worker serial baseline. Still, the converged loss is not negatively impacted by increasing parallelism, as shown in Figure 7.
Additionally, the convergence curve is steeper, meaning the time
taken to reach the same converged loss is reduced using the optimal
parallel configurations of our adaptive parallel implementations.


**Figure 7: DNN loss over time, using the optimal parallel meth-**
**ods returned by our Design Configuration across different**
**number of parallel workers**


**6** **CONCLUSION**


In this work, we proposed a novel implementation for DNN-MCTS
that adaptively chooses the optimal parallel scheme for the MCTS
component on the CPU. We also analyzed the performance on a
CPU-GPU platform and proposed an efficient method to search
for the optimal communication batch size interfacing the MCTS
component and DNN operations. By experimenting on a CPU-only
and CPU-GPU platform using a Gomoku game benchmark, we observed up to 1 _._ 5 × and 3 _._ 07 × speedup using our adaptive parallelism
compared to existing fixed-parallelism methods. Our method and
performance models are general and can also be adopted in the
context of many other types of accelerators for DNN inference and
training ( FPGAs, ASICS (e.g., TPUs), etc.) in the future.


Accelerating Deep Neural Network guided MCTS using
Adaptive Parallelism


**REFERENCES**


[1] Tristan Cazenave and Nicolas Jouandeau. 2007. On the parallelization of UCT.
In _Computer games workshop_ .

[2] Guillaume MJ-B Chaslot, Mark HM Winands, and HJVD Herik. 2008. Parallel
monte-carlo tree search. In _International Conference on Computers and Games_ .
Springer, 60–71.

[3] Jing Chen and Wenjun Jiang. 2019. Context-aware personalized POI sequence
recommendation. In _Smart City and Informatization: 7th International Conference,_
_iSCI 2019, Guangzhou, China, November 12–15, 2019, Proceedings 7_ . Springer,
197–210.

[4] Rémi Coulom. 2006. Efficient selectivity and backup operators in Monte-Carlo
tree search. In _International conference on computers and games_ . Springer, 72–83.

[5] Hideki Kato and Ikuo Takeuchi. 2010. Parallel monte-carlo tree search with simulation servers. In _2010 International Conference on Technologies and Applications_
_of Artificial Intelligence_ . IEEE, 491–498.

[6] Hideki Kato and Ikuo Takeuchi. 2010. Parallel monte-carlo tree search with simulation servers. In _2010 International Conference on Technologies and Applications_
_of Artificial Intelligence_ . IEEE, 491–498.

[7] Juhwan Kim, Byeongmin Kang, and Hyungmin Cho. 2021. SpecMCTS: Accelerating Monte Carlo Tree Search Using Speculative Tree Traversal. _IEEE Access_ 9
(2021), 142195–142205.

[8] Anji Liu, Jianshu Chen, Mingze Yu, Yu Zhai, Xuewen Zhou, and Ji Liu. 2020.
Watch the Unobserved: A Simple Approach to Parallelizing Monte Carlo
Tree Search. In _International Conference on Learning Representations_ . [https:](https://openreview.net/forum?id=BJlQtJSKDB)
[//openreview.net/forum?id=BJlQtJSKDB](https://openreview.net/forum?id=BJlQtJSKDB)

[9] Yuan Meng, Rajgopal Kannan, and Viktor Prasanna. 2022. Accelerating MonteCarlo Tree Search on CPU-FPGA Heterogeneous Platform. In _2022 32nd Inter-_
_national Conference on Field-Programmable Logic and Applications (FPL)_ . IEEE,
176–182.

[10] Yuan Meng, Rajgopal Kannan, and Viktor Prasanna. 2023. A Framework for
Monte-Carlo Tree Search on CPU-FPGA Heterogeneous Platform via on-chip



Dynamic Tree Management. In _Proceedings of the 2023 ACM/SIGDA International_
_Symposium on Field Programmable Gate Arrays_ . 235–245.

[11] S Ali Mirsoleimani, H Jaap van den Herik, Aske Plaat, and Jos Vermaseren. 2018.
A Lock-free Algorithm for Parallel MCTS.. In _ICAART (2)_ . 589–598.

[12] Nvidia. 2015. _CUDA streams_ [. https://developer.download.nvidia.com/CUDA/](https://developer.download.nvidia.com/CUDA/training/StreamsAndConcurrencyWebinar.pdf)
[training/StreamsAndConcurrencyWebinar.pdf](https://developer.download.nvidia.com/CUDA/training/StreamsAndConcurrencyWebinar.pdf)

[13] Herbert Robbins and Sutton Monro. 1951. A stochastic approximation method.
_The annals of mathematical statistics_ (1951), 400–407.

[14] Julian Schrittwieser, Ioannis Antonoglou, Thomas Hubert, Karen Simonyan,
Laurent Sifre, Simon Schmitt, Arthur Guez, Edward Lockhart, Demis Hassabis,
Thore Graepel, et al . 2020. Mastering atari, go, chess and shogi by planning with
a learned model. _Nature_ 588, 7839 (2020), 604–609.

[15] David Silver, Julian Schrittwieser, Karen Simonyan, Ioannis Antonoglou, Aja
Huang, Arthur Guez, Thomas Hubert, Lucas Baker, Matthew Lai, Adrian Bolton,
et al . 2017. Mastering the game of go without human knowledge. _nature_ 550,
7676 (2017), 354–359.

[16] Kuan Liang Tan, Chin Hiong Tan, Kay Chen Tan, and Arthur Tay. 2009. Adaptive
game AI for Gomoku. In _2009 4th International Conference on Autonomous Robots_
_and Agents_ . IEEE, 507–512.

[17] Linnan Wang, Yiyang Zhao, Yuu Jinnai, Yuandong Tian, and Rodrigo Fonseca.
2019. Alphax: exploring neural architectures with deep neural networks and
monte carlo tree search. _arXiv preprint arXiv:1903.11059_ (2019).

[18] Linnan Wang, Yiyang Zhao, Yuu Jinnai, Yuandong Tian, and Rodrigo Fonseca.
2020. Neural architecture search using deep neural networks and monte carlo
tree search. In _Proceedings of the AAAI Conference on Artificial Intelligence_, Vol. 34.
9983–9991.

[19] Louis F Williams Jr. 1976. A modification to the half-interval search (binary
search) method. In _Proceedings of the 14th annual Southeast regional conference_ .
95–101.

[20] Peizhi Yan and Yi Feng. 2018. A hybrid gomoku deep learning artificial intelligence. In _Proceedings of the 2018 Artificial Intelligence and Cloud Computing_
_Conference_ . 48–52.


