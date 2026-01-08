# 26-lm-agents-comprehensive-survey

**Source:** `26-lm-agents-comprehensive-survey.pdf`

---

**Observation of freezing phenomenon in high-dimensional quantum correlation**
**dynamics**


Yue Fu, [1, 2,] _[ ∗]_ Wenquan Liu, [3,] _[ ∗]_ Yunhan Wang, [1, 4] Chang-Kui
Duan, [1, 4, 5] Bo Zhang, [6] Yeliang Wang, [2] and Xing Rong [1, 4, 5,] _[ †]_

_1_ _CAS Key Laboratory of Microscale Magnetic Resonance and School of Physical Sciences,_
_University of Science and Technology of China, Hefei 230026, China_
_2_ _School of Integrated Circuits and Electronics, Beijing Institute of Technology, Beijing 100081, China_
_3_ _Institution of Quantum Sensing, Zhejiang University, Hangzhou 310027, China_
_4_ _Hefei National Laboratory, University of Science and Technology of China, Hefei 230088, China_
_5_ _CAS Center for Excellence in Quantum Information and Quantum Physics,_
_University of Science and Technology of China, Hefei 230026, China_
_6_ _School of Physics, Beijing Institute of Technology, Beijing 100081, China_


Quantum information processing (QIP) based on high-dimensional quantum systems provides
unique advantages and new potentials where high-dimensional quantum correlations (QCs) play vital
roles. Exploring the resistance of QCs against noises is crucial as QCs are fragile due to complex and
unavoidable system-environment interactions. In this study, we investigate the performance of highdimensional QCs under local dephasing noise using a single nitrogen-vacancy center in diamond.
A freezing phenomenon in the high-dimensional quantum discord dynamics was observed, showing
discord is robust against local dephasing noise. Utilizing a robustness metric known as freezing
index, we found that the discord of qutrits outperforms their qubits counterpart when confronted
with dephasing noise. Furthermore, we developed a geometric picture to explain this intriguing
freezing phenomenon phenomenon. Our findings highlight the potential of utilizing discord as a
physical resource for advancing QIP in high-dimensional quantum settings.


**Introduction**


Quantum correlations (QCs), a major feature of quantum mechanics that cannot be explained by classical theory,
play essential roles in quantum information processing (QIP) with enhanced performances [1–5]. However, due to
the interactions with the environment, quantum systems are inevitably affected by various noises [6], which cause
degradation of QCs [7] and failure of QIP tasks. Several methods have been proposed and demonstrated to mitigate
this problem, including dynamical decoupling [8], decoherence-free subspace [9, 10], error correction codes [11], etc.
Meanwhile, exploring noise-robust quantum featurescite [12–14] and designing QIP algorithms based on them may
be a distinct pathway to deal with the noise issue [4]. For example, it has been found that quantum discord, a kind
of characterization for QCs [15, 16], can be frozen for a period when suffering dephasing noise [12, 17–20]. This
intriguing phenomenon shows the immunity of discord against the dephasing noise and has been studied intensively
in two-level qubit systems [21–24].
Recently, with the rapid advances in quantum technologies, there have been increasing explorations of utilizing highdimensional quantum systems to execute QIP tasks [25–28]. And thanks to the exponential expansion of the Hilbert
space, high-dimensional quantum systems presents unique advantages [29–31] and new potentials [32–35] over their
qubit counterparts in QIP. However, the noise issue remains and can be more sticky [36, 37]. Take the dynamical
decoupling method as an example, the increased dimension makes the design and implementation of decoupling
sequences more complicated [38–40]. And up to six _π_ pulses were performed to realize dynamical decoupling of single
qutrit in a recent experiment [41]. In this regard, exploring noise-robust quantum features may be a promising method

[42–45]. However, investigations into the dynamics of high-dimensional quantum correlations have so far been limited

[12, 46–49].
In this work, we investigate the dynamics of various quantum correlations between two qutrits under the onequtrit local dephasing noise, which is common in quantum systems composed by different spins. We first proposed
a geometric picture to show that the dynamics of high-dimensional quantum discord could be frozen and exhibit an
intriguing sudden transition phenomenon for a type of Bell-diagonal states. Then, working on two qutrits consisted
by the electron spin and the nuclear spin of a single nitrogen-vacancy (NV) center in diamond [50], this dynamical


_∗_ These authors contributed equally to this work.

_†_ [Electronic address: xrong@ustc.edu.cn](mailto:xrong@ustc.edu.cn)


2



(a) (b)


0 1 −𝜆 1



𝜆

















𝑐 0


FIG. 1: **QC dynamics of the Bell-diagonal states** _ρ_ BD _,_ 3 **under one-qutrit local dephasing noise.** (a) The quantum
discord presents a freezing phenomenon. (b) Geometric perspective of the freezing phenomenon. _c_ 0 _, c_ 2 _∈_ [0 _,_ 1] and _c_ 0 + _c_ 2 _≤_ 1
are the parameters of _ρ_ BD _,_ 3, _λ ∈_ [0 _,_ 1] characterizes the dephasing process. These parameters construct a parameter space in
the form of a triangular prism. The gray line _χ_ 1 and plane _χ_ 2 are the states with zero quantum discord. For other quantum
states, their minimal distance to _χ_ 1 and _χ_ 2 are defined as _d_ 1 and _d_ 2, respectively, and the quantum discord is min _{d_ 1 _, d_ 2 _}_ . The
pink surface shows the states with _d_ 1 = _d_ 2 . If the dephasing trajectory crosses the pink surface (blue dash line for example),
the quantum discord dynamics will present a sudden transition.


property was confirmed experimentally. Finally, we compared the goodness of this freezing behavior between qutrits
and qubits utilizing a measure called freezing index [49] since there exhibits a certain trade-off between the amount
of discord and the time that it could be frozen [51]. The results show that qutrits possess a larger freezing index than
qubits, demonstrating its potential in future high-dimensional QIP.


**Theory**


For a bipartite quantum system, the quantum discord between the two subsystems is defined as the minimum
Schatten 1-norm distance between the system state _ρ_ _AB_ and state _σ_ _AB_ within the set of quantum-classical states
_{ρ_ [q] _[−]_ [c] _}_ that has zero discord: _Q_ = min Here, we consider a family of two-qutrit
_σ_ _AB_ _∈{ρ_ [q] _[−]_ [c] _}_ _[||][ρ]_ _[AB]_ _[ −]_ _[σ]_ _[AB]_ _[||]_ [1] [ [][52][–][54][].]

Bell-diagonal states. They are the superposition of maximally entangled states given by [45]


_ρ_ BD _,_ 3 = _c_ 0 _|_ Ψ 00 _⟩⟨_ Ψ 00 _|_ + _c_ 1 _|_ Ψ 01 _⟩⟨_ Ψ 01 _|_ + _c_ 2 _|_ Ψ 02 _⟩⟨_ Ψ 02 _|,_ (1)



3 and _|_ Ψ 02 _⟩_ = ( _|_ 10 _⟩_ + _|_ 21 _⟩_ + _|_ 02 _⟩_ ) _/√_



with _|_ Ψ 00 _⟩_ = ( _|_ 00 _⟩_ + _|_ 11 _⟩_ + _|_ 22 _⟩_ ) _/√_



3, _|_ Ψ 01 _⟩_ = ( _|_ 01 _⟩_ + _|_ 12 _⟩_ + _|_ 20 _⟩_ ) _/√_



with _|_ Ψ 00 _⟩_ = ( _|_ 00 _⟩_ + _|_ 11 _⟩_ + _|_ 22 _⟩_ ) _/√_ 3, _|_ Ψ 01 _⟩_ = ( _|_ 01 _⟩_ + _|_ 12 _⟩_ + _|_ 20 _⟩_ ) _/√_ 3 and _|_ Ψ 02 _⟩_ = ( _|_ 10 _⟩_ + _|_ 21 _⟩_ + _|_ 02 _⟩_ ) _/√_ 3 in the

computational basis. Parameters _c_ 0 _, c_ 1 _, c_ 2 _∈_ [0 _,_ 1] and satisfy _c_ 0 + _c_ 1 + _c_ 2 = 1. The evolution of these states under
the local dephasing noise of the first qutrit can be written as











~~~~








_c_ 0 0 0 0 _c_ 0 _λ_ 0 0 0 _c_ 0 _λ_ [2]




















_ρ_ [deph] BD _,_ 3 [(] _[c]_ [0] _[,c]_ [2] _[,λ]_ [)=1]



3



0 _c_ 1 0 0 0 _c_ 1 _λ c_ 1 _λ_ [2] 0 0
0 0 _c_ 2 _c_ 2 _λ_ 0 0 0 _c_ 2 _λ_ [2] 0
0 0 _c_ 2 _λ_ _c_ 2 0 0 0 _c_ 2 _λ_ 0
_c_ 0 _λ_ 0 0 0 _c_ 0 0 0 0 _c_ 0 _λ_
0 _c_ 1 _λ_ 0 0 0 _c_ 1 _c_ 1 _λ_ 0 0
0 _c_ 1 _λ_ [2] 0 0 0 _c_ 1 _λ_ _c_ 1 0 0
0 0 _c_ 2 _λ_ [2] _c_ 2 _λ_ 0 0 0 _c_ 2 0
_c_ 0 _λ_ [2] 0 0 0 _c_ 0 _λ_ 0 0 0 _c_ 0



_,_ (2)



where _λ_ = exp [ _−_ ( _t/T_ 2 _[∗]_ [)] _[n]_ [] denotes the decay of the off-diagonal elements with] _[ T]_ _[ ∗]_ 2 [characterizing the dephasing of]
the first qutrit and _n_ being the noise-dependent stretch factor. Figure 1(a) shows a typical discord dynamics for
quantum states with the form shown in Eq. 2. Under the local dephasing noise, the discord can be frozen for a


3


## (a) (b)






## +1 #


## 0 # 𝜔 !" 𝜔 !$


## electron spin nuclear spin


## 0 #








## Polarization State preparation Evolution Measurement Laser






## MW RF




## 𝜌 + 𝜌 ++ 𝜌,


FIG. 2: **The NV center two-qutrit system and the experimental pulse sequence diagram.** (a) Left: in the ground
state of the NV center, the electron spin and the nuclear spin constitute a two-qutrit system. Right: the energy levels.
Transitions between different electron (nuclear) spin states can be controlled by microwave (radio frequency) pulses indicated
by purple (blue) arrows. (b) Polarization, state preparation, evolution under dephasing noise and measurement are displayed.
In the state preparation part, selective MW (purple) and RF (blue) pulses were performed to generate the Bell-diagonal state
_ρ_ BD _,_ 3 . The measurement part comprises various sequences to read out different elements of the density matrix (see supplemental
material for details).


period before a sudden transition happens and the discord decays to zero gradually [45]. This phenomenon shows
that discord is robust against the dephasing noise. The freezing phenomenon was first discovered in qubit systems
where corresponding theoretical explanations and experimental observations have been explored intensively. Below
we analyze the model in detail and geometrically elucidate the origin of this exotic phenomenon in the qutrit case.
As shown in Fig. 1(b), the state _ρ_ [deph] BD _,_ 3 [is specified by 3-parameters] _[ c]_ [0] _[, c]_ [2] [ and] _[ λ]_ [. The matrix is physical when]
_c_ 0 + _c_ 2 _≤_ 1, corresponds to the region of the triangular prism. We derived and calculated the set of quantum-classical
states with zero discord and found it contains two parts: the gray line _χ_ 1 where _c_ 0 = _c_ 2 = 1 _/_ 3, and the gray plane
_χ_ 2 where _λ_ = 0 (see supplemental material for details). For a point in the parameter space that corresponds to a
quantum state, _d_ 1 and _d_ 2 are utilized to denote the minimal distance of it to _χ_ 1 and _χ_ 2, respectively. The discord of
this state is min _{d_ 1 _, d_ 2 _}_ . The states that satisfy _d_ 1 = _d_ 2 are plotted by the pink surface in Fig. 1(b). Equation of
this surface is given in the supplementary information.
The sudden transition of the discord dynamics can be explained as follows. The evolution trajectory of _ρ_ BD _,_ 3
with given _c_ 0 and _c_ 2 under the one-qutrit local dephasing noise is a straight line that parallels the _λ_ -axis. The blue
dashed line in Fig. 1(b) with _c_ 0 = 0 _._ 3 and _c_ 2 = 0 _._ 7 is an example, which corresponds to the one used in Fig. 1(a).
The beginning part of this trajectory is above the pink surface, where _d_ 1 _< d_ 2 and _Q_ = _d_ 1 = [�] [2] _i_ =0 _[|][c]_ _[i]_ _[ −]_ [1] _[/]_ [3] _[|]_ [ (see]


4


supplemental material). The independence of _d_ 1 on _λ_ makes discord a constant in this part, corresponding to the
freezing interval shown by the discord dynamics in Fig. 1(a). After the trajectory crosses the pink surface, we have
_d_ 1 _> d_ 2 and _Q_ = _d_ 2 = _λ_ [2] + _√λ_ [4] + 8 _λ_ [2] . Thus the discord decays to zero smoothly as _λ_ approaches zero gradually.

The discord dynamics of other trajectories can be analyzed similarly. In general, the sudden transition will happen
whenever a dephasing trajectory crosses the pink surface.


**Experiment**


We experimentally investigate the sudden transition phenomenon utilizing a single NV center in diamond. Figure
2(a) shows the two-qutrit system constructed by the electron spin of the NV center and the nuclear spin of the [14] N
atom both with spin-1. With a static magnetic field applied along the NV symmetry axis, the Hamiltonian of this
two-qutrit spin system can be written as


_H_ NV = 2 _π_ ( _DS_ _z_ [2] [+] _[ ω]_ [e] _[S]_ _[z]_ [+] _[ PI]_ _z_ [2] [+] _[ ω]_ [n] _[I]_ _[z]_ [+] _[ A]_ [hf] _[S]_ _[z]_ _[I]_ _[z]_ [)] _[,]_ (3)



where _S_ _z_ ( _I_ _z_ ) is the spin-1 operator of the electron (nuclear) spin, _D_ = 2 _._ 87 GHz is the electronic zero-field splitting,
_P_ = _−_ 4 _._ 95 MHz represents the nuclear quadrupolar interaction, and _A_ hf = _−_ 2 _._ 16 MHz is the hyperfine coupling
constant. _ω_ e ( _ω_ n ) corresponds to the Zeeman frequency of the electron (nuclear) spin. The energy level structure of
the two-qutrit system is depicted in Fig. 2(a) right. The eigenlevels are denoted by _|m_ _S_ _⟩_ e _⊗|m_ _I_ _⟩_ n, with _m_ _S_ _, m_ _I_ = 0 _, ±_ 1
representing the states of the electron and nuclear spins, respectively. The state of the electron spin can be manipulated
by microwave (MW) pulses, which are labeled by the purple arrows in Fig. 2(a). The radio frequency (RF) pulses
labeled by blue arrows were performed to control the state of the nuclear spin. For simplicity, _|_ +1 _⟩_ e(n), _|_ 0 _⟩_ e(n), and
_|−_ 1 _⟩_ e(n) are hereafter labeled by _|_ 0 _⟩_, _|_ 1 _⟩_, and _|_ 2 _⟩_, respectively. And _|m_ _S_ _⟩_ e _⊗|m_ _I_ _⟩_ n is labeled as the corresponding
_|ij⟩_ with _i, j_ = 0 _,_ 1 _,_ 2.
Relaxation processes that cause the decoherence and energy dissipation of the NV center system can be characterized
by the dephasing time _T_ 2 _[∗]_ _,_ e(n) [and the longitudinal relaxation time] _[ T]_ [1] _[,]_ [e(n)] [, respectively.] In our experiment, the
diamond sample was isotopically purified with the concentration of [12] C atom exceeding 99 _._ 9%. For the electron spin,
the dephasing time is measured to berelaxation times of the electron spin and the nuclear spin, the dephasing time of the nuclear spin are all over one _T_ 2 _[∗]_ _,_ e [= 44] _[ ±]_ [ 2] _[ µ]_ [s on average (See supplemental material). The longitudinal]
millisecond [42]. For the timescale concerned in this experiment ( _<_ 100 _µ_ s), the influence of these noises is limited.
We omit them hereafter and only consider the dephasing noise of the electron spin. Therefore, the two-qutrit spin
system can be taken as governed by the one-qutrit local dephasing noise and follows the evolution in Eq. 2 after the
appropriate initial state was prepared.
Figure 2(b) shows the pulse sequence diagram for studying the dynamical behaviors of various QCs. It consists of
four parts: polarization, state preparation, evolution under the noise environment, and measurement. The NV center
was polarized into state _|_ 10 _⟩_ via a green laser pulse with the external magnetic field being 500 Gauss [56]. To prepare
the two-qutrit Bell-diagonal state, a MW pulse was performed to convert the polarized state _|_ 10 _⟩_ to _[√]_ ~~_c_~~ 0 ~~_|_~~ 10 _⟩_ + _[√]_ ~~_c_~~ 2 ~~_|_~~ 20 _⟩_ .
After a waiting time of _t_ wait = 200 _µ_ s, the system state evolved into the mixed state _ρ_ I = _c_ 0 _|_ 10 _⟩⟨_ 10 _|_ + _c_ 2 _|_ 20 _⟩⟨_ 20 _|_ due
to the dephasing. Then four selective RF pulses followed by the same waiting time were executed to prepare the NV
center into state _ρ_ II = _[c]_ 3 [0] [(] _[|]_ [10] _[⟩]_ [+] _[ |]_ [11] _[⟩]_ [+] _[ |]_ [12] _[⟩]_ [) (] _[⟨]_ [10] _[|]_ [ +] _[ ⟨]_ [11] _[|]_ [ +] _[ ⟨]_ [12] _[|]_ [) +] _[c]_ 3 [2] [(] _[|]_ [20] _[⟩]_ [+] _[ |]_ [21] _[⟩]_ [+] _[ |]_ [22] _[⟩]_ [)(] _[⟨]_ [20] _[|]_ [ +] _[ ⟨]_ [21] _[|]_ [ +] _[ ⟨]_ [22] _[|]_ [). Finally,]

selectively MW pulses were applied sequentially to eventually realize the Bell-diagonal state _ρ_ BD _,_ 3 (see Fig. 2(b)). The
selective pulses mentioned above correspond to transitions between different energy levels displayed in Fig. 2(a). The
state _ρ_ BD _,_ 3 with different parameters can be prepared by adjusting the time duration of the pulses. After the state
was prepared, the quantum system was left to evolve under the dephasing noise for a period of _t_ . In the final part, a
set of pulse sequences (dashed box in Fig. 2(b)) were executed to reconstruct the quantum state. More details about
the state preparation, the measurement, and the state reconstruction can be found in the supplementary information.
The quantity of various QCs was obtained from the measured density matrices of the two-qutrit system. To
ascertain the physical validity of the matrices, maximum likelihood estimation was applied to the experimental data

[57]. Due to imperfect polarization and statistical errors, the obtained density matrices may deviate slightly from
the form shown in Eq. 2. To accurately calculate the discord of these quantum states, we adopted the quantum
mutual information description [15] and utilized a numerical method [58]. We also explored the dynamics of quantum
entanglement under the same local dephasing noise. It is quantified by negativity defined as _N_ = ( _||ρ_ _[P T]_ _||_ 1 _−_ 1) _/_ 2 with
_PT_ representing partial transposition [59]. Details about the quantum mutual information description and calculation
of different kinds of QCs are included in the supplementary information.


5


_t_


_t_



( a )


( b ) _t_


_t_



_t_


_t_



_t_


_t_



_t_


_t_



2 0 4 0 6 0 8 0 1 0 0

_t_ ( µ s )


_t_



_t_


_t_



_t_


2 0 4 0 6 0 8 0 1 0 0
_t_ ( µ s )


FIG. 3: Experimental dynamics of high-dimensional quantum entanglement and quantum discord. The x-axis is the evolution
time under one-qutrit local dephasing noise. The y-axis is the quantity of entanglement (characterized by negativity) or discord.
The dots with error bars are experimental data, the lines show the simulation results. (a) Parameters _c_ 0 = 0 _._ 3 _, c_ 2 = 0 _._ 7. The
negativity decayed smoothly while the discord dynamics presented a sudden transition. The black dashed line presents the
ideal freezing dynamics of the discord without the influence of imperfect polarization. (b) Parameters _c_ 0 = 1 _, c_ 2 = 0. Both the
discord and entanglement decay smoothly to 0.


**Results**


Figure 3 (a) shows the experimental dynamics of high-dimensional quantum discord and quantum entanglement
with parameters _c_ 0 = 0 _._ 3 _, c_ 2 = 0 _._ 7. The dots with error bars are experimental data while the solid lines are simulation
results. In the top panel, the entanglement decays smoothly as the evolution time _t_ increases. In contrast, the discord
is almost a constant for _t_ ≲ 23 _µs_, which is consistent with the frozen part in Fig. 1 and shows the immunity of
discord against the dephasing noise. When _t_ ≳ 23 _µs_, the discord decays gradually to 0. Therefore, the dynamics of


6


the discord presented in the bottom panel agree well with the theoretical anticipation, and the freezing phenomenon
was observed experimentally. It is noticed that the experimental discord dynamics show a slight decay and deviate
from the ideal situation (the black dashed line) during the freezing interval. This is due to the imperfect polarization
of the spins [56, 60]. In our experiment, the polarization rate of the electron spin and the nuclear spin were 0.92(1)
and 0.98(1), respectively. Corresponding simulation results are plotted by the solid blue line and agree well with the
experiment.
The dynamics of entanglement and discord when _c_ 0 = 1 _, c_ 2 = 0 were also investigated. The evolution trajectory of
the Bell-diagonal state with these parameters corresponds to the red line in Fig. 1(b). This trajectory does not cross
the pink surface where _d_ 1 = _d_ 2, so the sudden transition shall not happen. The experimental results are depicted
in Fig. 3 (b). The dynamics of both discord and entanglement exhibit a gradual decay as the evolution time, _t_,
progresses. This behavior is in line with our theoretical predictions.
After experimental demonstrating the robustness of discord against the dephasing noise in qutrit system, we now
compare it with its qubit counterpart. It has shown that there is a certain trade-off between the amount of discord
and the time that it can be frozen [18]. This trade-off is vital when discord is utilized in QIP as the speedup of
QIP tasks depends severely on the quantity of quantum correlations [51]. To quantify the goodness of the freezing
behavior, the concept of freezing index was introduced [49]. When the freezing phenomenon starts from the beginning
of the dynamics and occurs solely once, the freezing index can be defined as:



_F_ =
�



_γ_ fin 1 _/_ 4
_Q_ _Q_ ( _γ_ ) _dγ_ (4)
� _γ_ ini �



where _γ_ := 1 _−λ_ is the parameterized time and _γ_ fin _−γ_ ini denotes the freezing interval. _Q_ ( _γ_ ) ( _Q_ ) is the time-dependent
(averaged) discord during the freezing interval when imperfect freezing was considered and the discord decays slowly
during the period.
We compare the freezing index of the two-qutrit system with the two-qubit system for Bell-diagonal states. The
qubit Bell-diagonal states are defined as _ρ_ BD _,_ 2 = _b_ 0 _|_ Φ 0 _⟩⟨_ Φ 0 _|_ + _b_ 1 _|_ Φ 1 _⟩⟨_ Φ 1 _|_ where _|_ Φ 0 _⟩_ and _|_ Φ 1 _⟩_ are qubit maximally
states, _b_ 0 _, b_ 1 _∈_ [0 _,_ 1] with _b_ 0 + _b_ 1 = 1. Fig. 4(a) illustrates the trade-off between the discord value and the freezing
interval. It can be seen that a longer freezing interval usually accompanies a smaller amount of discord for both qubits
and qutrits. And while the freezing interval of qubits is always longer than qutrits, the discord contained in qubit
states is smaller than that in qutrits. This trade-off is finally characterized by the freezing index given in Fig. 4(b).
It is clear that the freezing index of qutrits exceeds that for qubits consistently, showing qutrit Bell-diagonal states
are more potential than those of qubit for QIP when suffering local dephasing noise. The dot with error bars is the
experimental result, whose freezing index is bigger than the theoretical value of qubit states with the same parameter
_b_ 0 = _c_ 0 = 0 _._ 3. The distance between the experimental data and the theoretical value of the qutrit freezing index
comes mainly from imperfect polarization and other statistical errors.


**Conclusion**


We have conducted an in-depth investigation into the dynamics of high-dimensional QCs under the influence of local
dephasing noise. A freezing phenomenon in the high-dimensional quantum discord dynamics was observed, which is
consistent with the prediction of the geometric picture we proposed, while QE decays monotonously. Comparison
between this phenomenon and that in qubits shows qutrit Bell-diagonal states have a larger freezing index. Our work
demonstrates the potential of utilizing high-dimensional quantum discord to implement QIP tasks as dephasing noises
are common in most quantum systems. Besides, the behavior of high-dimensional quantum discord under other noises
could be explored. For example, whether quantum discord exhibits a sudden death under depolarization noise would
be an interesting issue.
We thank Zhu-Jun Zheng and Changyue Zhang for the helpful discussion. This work was supported by the National
Natural Science Foundation of China (Grants No. 12261160569, No. 12321004, and No. 12374462), the Chinese
Academy of Sciences (Grants No. XDC07000000 and No. GJJSTD20200001), Innovation Program for Quantum
Science and Technology (Grant No. 2021ZD0302200), Anhui Initiative in Quantum Information Technologies (Grant
No. AHY050000), and Hefei Comprehensive National Science Center, the Fundamental Research Funds for the Central
Universities (Grants No. 226-2023-00137 and No. 226-2023-00139). Y.F. acknowledges financial support from the
China Postdoctoral Science Foundation (Nos. 2023TQ0029, 2023M740262 and GZC20233415).


[1] R. Horodecki, P. Horodecki, M. Horodecki, and K. Horodecki, Quantum Entanglement, _Rev. Mod. Phys._ **81**, 865 (2009).


7


_b_ _b_



( a )


_b_ _b_



( b )


_b_ _b_



0 . 8


0 . 6


0 . 4


0 . 2


_b_ _b_



_b_ _b_



_b_ _b_



1 . 0


0 . 5


0 . 0


1 . 0


0 . 5


_b_ _b_



q u b i t
q u t r i t


q u b i t
q u t r i t


_b_ _b_



0 . 0
0 . 0 0 . 5 1 . 0


_b_ 0 o r _c_ 0 _b_



0 . 0
0 . 0 0 . 5 1 . 0


_b_ _b_ 0 o r _c_ 0



_b_ _b_


FIG. 4: **Freezing index comparison between qubit and qutrit.** (a) The amount of discord (upper part) and the freezing
interval (lower part) versus qubit parameter _b_ 0 or qutrit parameter _c_ 0 . (b) Freezing index versus _b_ 0 and _c_ 0 . The dot with error
bars is the experimental result.


[2] R. Uola, A. C. S. Costa, H. C. Nguyen, and O. G¨uhne, Quantum Steering, Rev. Mod. Phys. 92, 015001 (2020).

[3] A. Streltsov, Quantum Correlations Beyond Entanglement and Their Role in Quantum Information Theory (Springer,
New York, 2015).

[4] G. Adesso, T. R. Bromley, and M. Cianciaruso, Measures and Applications of Quantum Correlations, _J. Phys. A: Math._
_Theor._ **49**, 473001 (2016).

[5] D. Braun, G. Adesso, F. Benatti, R. Floreanini, U. Marzolino, M. W. Mitchell, and S. Pirandola, Quantum-Enhanced
Measurements without Entanglement, _Rev. Mod. Phys._ **90**, 035006 (2018).

[6] D. Suter and G. A. Alvarez, Colloquium: Protecting Quantum Information against Environmental Noise, [´] _Rev. Mod. Phys._
**88**, 041001 (2016).

[7] R. J. Lewis-Swan, A. Safavi-Naini, A. M. Kaufman, and A. M. Rey, Dynamics of Quantum Information, _Nat. Rev. Phys._
**1**, 627 (2019).

[8] P. Wang, C.-Y. Luan, M. Qiao, M. Um, J. Zhang, Y. Wang, X. Yuan, M. Gu, J. Zhang, and K. Kim, Single ion qubit with
estimated coherence time exceeding one hour, _Nat. Commun._ **12**, 233 (2021).

[9] C. Zhang, P. Yu, A. Jadbabaie, and N. R. Hutzler, Quantum-enhanced metrology for molecular symmetry violation using
decoherence-free subspaces, _Phys. Rev. Lett._ **131**, 193602 (2023).

[10] H.-R. Wang, D. Yuan, S.-Y. Zhang, Z. Wang, D.-L. Deng, and L. M. Duan, Embedding quantum many-body scars into
decoherence-free subspaces, _Phys. Rev. Lett._ **132**, 150401 (2024).

[11] N. Sundaresan, T. J. Yoder, Y. Kim, M. Li, E. H. Chen, G. Harper, T. Thorbeck, A. W. Cross, A. D. Corcoles, and M.
Takita, A. D. C´ _o_ rcoles, and M. Takita, Demonstrating multi-round subsystem quantum error correction using matching
and maximum likelihood decoders. _Nat. Commun._ **14**, 2852 (2023).

[12] L. Mazzola, J. Piilo, and S. Maniscalco, Sudden Transition between Classical and Quantum Decoherence, _Phys. Rev. Lett._
**104**, 200401 (2010).

[13] G. Karpat, Z. Gedik, Correlation dynamics of qubit-qutrit systems in a classical dephasing environment. Phys. Lett. A
375, 4166 (2011)

[14] E.G. Carnio, A. Buchleitner, M. Gessner, Robust asymptotic entanglement under multipartite collective dephasing. Phys.
Rev. Lett. 115, 010404 (2015)

[15] H. Ollivier and W. H. Zurek, Quantum Discord: A Measure of the Quantumness of Correlations, _Phys. Rev. Lett._ **88**,
017901 (2001).

[16] L. Henderson and V. Vedral, Quantum and Total Correlations, _J. Phys. A: Math. Gen._ **34**, 6899 (2001).

[17] K. Modi, A. Brodutch, H. Cable, T. Paterek, and V. Vedral, The Classical-Quantum Boundary for Correlations: Discord
and Related Measures, _Rev. Mod. Phys._ **84**, 1655 (2012).

[18] A. Bera, T. Das, D. Sadhukhan, S. Singha Roy, A. Sen(De), and U. Sen, Quantum discord and its allies: a review of recent
progress. _Rep. Prog. Phys._ **81**, 024001 (2018).

[19] G. De Chiara and A. Sanpera, Genuine Quantum Correlations in Quantum Many-Body Systems: A Review of Recent


8


Progress, _Rep. Prog. Phys._ **81**, 074002 (2018).

[20] B. Daki´ _c_, Y. O. Lipp, X. Ma, M. Ringbauer, S. Kropatschek, S. Barz, T. Paterek, V. Vedral, A. Zeilinger, C. Brukner et [ˇ]
al., Quantum Discord as Resource for Remote State Preparation, _Nat. Phys._ **8**, 666 (2012).

[21] J.-S. Xu, K. Sun, C.-F. Li, X.-Y. Xu, G.-C. Guo, E. Andersson, R. Lo Franco, and G. Compagno, Experimental Recovery
of Quantum Correlations in Absence of System-Environment Back-Action, _Nat. Commun._ **4**, 2851 (2013).

[22] R. Auccaise, L. C. C´eleri, D. O. Soares-Pinto, E. R. deAzevedo, J. Maziero, A. M. Souza, T. J. Bonagamba, R. S. Sarthour,
I. S. Oliveira, and R. M. Serra, Environment-Induced Sudden Transition in Quantum Discord Dynamics, _Phys. Rev. Lett._
**107**, 140403 (2011).

[23] J.-S. Xu, X.-Y. Xu, C.-F. Li, C.-J. Zhang, X.-B. Zou, and G.-C. Guo, Experimental Investigation of Classical and Quantum
Correlations under Decoherence, _Nat. Commun._ **1**, 7 (2010).

[24] H. Singh, Arvind, and K. Dorai, Experimentally Freezing Quantum Discord in a Dephasing Environment Using Dynamical
Decoupling, _EPL_ **118**, 50001 (2017).

[25] D. Cozzolino, B. Da Lio, D. Bacco, and L. K. Oxenlwe, High-Dimensional Quantum Communication: Benefits, Progress,
and Future Challenges, _Adv. Quantum Technol._ **2**, 1900038 (2019).

[26] Y. Wang, Z. Hu, B. C. Sanders and S. Kais, Qudits and High-Dimensional Quantum Computing, _Front. Phys._ **8**, 479
(2020).

[27] M. Erhard, M. Krenn, and A. Zeilinger, Advances in High-Dimensional Quantum Entanglement, _Nat. Rev. Phys._ **2**, 365
(2020).

[28] X.-M. Hu, Y. Guo, B.-H. Liu, C.-F. Li, and G.-C. Guo, Progress in Quantum Teleportation, _Nat. Rev. Phys._ **5**, 339 (2023).

[29] P. Hrmo, B. Wilhelm, L. Gerster, M. W. Van Mourik, M. Huber, R. Blatt, P. Schindler, T. Monz, and M. Ringbauer,
Native Qudit Entanglement in a Trapped Ion Quantum Processor, _Nat. Commun._ **14**, 2242 (2023).

[30] J. Wang, S. Paesani, Y. Ding, R. Santagati, P. Skrzypczyk, A. Salavrakos, J. Tura, R. Augusiak, L. Manˇcinska, D. Bacco
et al., Multidimensional Quantum Entanglement with Large-Scale Integrated Optics, _Science_ **360**, 285 (2018).

[31] Pei Liu, Ruixia Wang, Jing-Ning Zhang, Yingshan Zhang, Xiaoxia Cai, Huikai Xu, Zhiyuan Li, Jiaxiu Han, Xuegang Li,
Guangming Xue et al., Performing SU( _d_ ) Operations and Rudimentary Algorithms in a Superconducting Transmon Qudit
for _d_ = 3 and _d_ = 4, _Phys. Rev. X_ **13**, 021028 (2023).

[32] I. F. de Fuentes, T. Botzem, M. A. I. Johnson, A. Vaartjes, S. Asaad, V. Mourik, F. E. Hudson, K. M. Itoh, B. C. Johnson,
A. M. Jakob et al., Navigating the 16-Dimensional Hilbert Space of a High-Spin Donor Qudit with Electric and Magnetic
Fields, _Nat. Commun._ **15**, 1380 (2024).

[33] Y. Chi, J. Huang, Z. Zhang, J. Mao, Z. Zhou, X. Chen, C. Zhai, J. Bao, T. Dai, H. Yuan et al., A Programmable
Qudit-Based Quantum Processor, _Nat. Commun._ **13**, 1166 (2022).

[34] M. Ringbauer, M. Meth, L. Postler, R. Stricker, R. Blatt, P. Schindler, and T. Monz, A Universal Qudit Quantum Processor
with Trapped Ions, _Nat. Phys._ **18**, 1053 (2022).

[35] C. Reimer, S. Sciara, P. Roztocki, M. R. Islam, L. Cort´es, Y. Zhang, B. Fischer, S. Loranger, R. Kashyap, A. Cino et al.,
High-Dimensional One-Way Quantum Processing Implemented on _d_ -Level Cluster States _Nat. Phys._ **15**, 148-153 (2019).

[36] N. V. Vitanov, Dynamical rephasing of ensembles of qudits. _Phys. Rev. A_ **92**, 022314 (2015).

[37] A. Coladangelo and J. Stark, An Inherently Infinite-Dimensional Quantum Correlation, _Nat. Commun._ **11**, 3335 (2020).

[38] R. de J. Napolitano, F. F. Fanchini, A. H. da Silva, and B. Bellomo, Protecting operations on qudits from noise by
continuous dynamical decoupling. _Phys. Rev. Research_ **3**, 013235 (2021).

[39] A. Singh and U. Sinha, Entanglement protection in higher-dimensional systems. _Phys. Scr._ **97**, 085104 (2022).

[40] T. Kraft, C. Ritz, N. Brunner, M. Huber, and O. G¨uhne, Characterizing Genuine Multilevel Entanglement, _Phys. Rev._
_Lett._ **120**, 060502 (2018).

[41] Xinxing Yuan, Yue Li, Mengxiang Zhang, Chang Liu, Mingdong Zhu, Xi Qin, Nikolay V. Vitanov, Yiheng Lin, and
Jiangfeng Du, Preserving multilevel quantum coherence by dynamical decoupling. _Phys. Rev. A_ **106**, 022412 (2022).

[42] Y. Fu, W. Liu, X. Ye, Y. Wang, C. Zhang, C.-K. Duan, X. Rong, and J. Du, Experimental Investigation of Quantum
Correlations in a Two-Qutrit Spin System, _Phys. Rev. Lett._ **129**, 100501 (2022).

[43] M. Ali, Distillability Sudden Death in Qutrit-Qutrit Systems under Global and Multilocal Dephasing, _Phys. Rev. A_ **81**,
042303 (2010).

[44] W. Xiao, M.-Y. Zhen, and X.-W. Hou, Freezing of Geometric Discords for Two Qutrits in Environments, _Int. J. Quantum_
_Inform._ **20**, 2250019 (2022).

[45] F. A. C´ardenas-L´opez, S. Allende, and J. C. Retamal, Sudden Transition between Classical to Quantum Decoherence in
Bipartite Correlated Qutrit Systems, _Sci. Rep._ **7**, 44654 (2017).

[46] J. Maziero, L. C. C´eleri, R. M. Serra, and V. Vedral, Classical and Quantum Correlations under Decoherence, _Phys. Rev._
_A_ **80**, 044102 (2009).

[47] T. Werlang, S. Souza, F. F. Fanchini, and C. J. Villas Boas, Robustness of Quantum Discord to Sudden Death, _Phys. Rev._
_A_ **80**, 024103 (2009).

[48] M. D. Lang and C. M. Caves, Quantum Discord and the Geometry of Bell-Diagonal States, _Phys. Rev. Lett._ **105**, 150501
(2010).

[49] T. Chanda, A. K. Pal, A. Biswas, A. Sen(De), and U. Sen, Freezing of Quantum Correlations under Local Decoherence,
_Phys. Rev. A_ **91**, 062119 (2015).

[50] M. W. Doherty, N. B. Manson, P. Delaney, F. Jelezko, J. Wrachtrup, and L. C. L. Hollenberg, The Nitrogen-Vacancy
Colour Centre in Diamond, _Phys. Rep._ **528**, 1 (2013).

[51] Lectures on General Quantum Correlations and Their Applications. (Springer International Publishing, Cham, 2017).

[52] B. Daki´c, V. Vedral, and C. Brukner, Necessary and Sufficient Condition for Nonzero Quantum Discord, [ˇ] _Phys. Rev. Lett._


9


**105**, 190502 (2010).

[53] F. M. Paula, J. D. Montealegre, A. Saguia, T. R. De Oliveira, and M. S. Sarandy, Geometric Classical and Total Correlations
via Trace Distance, _Europhys. Lett._ **103**, 50008 (2013).

[54] L. Jakobczyk, A. Frydryszak, and P. Lugiewicz, _Phys. Lett. A_ **380**, 1535 (2016).

[55] G. Wolfowicz, F. J. Heremans, C. P. Anderson, S. Kanai, H. Seo, A. Gali, G. Galli, and D. D. Awschalom, Quantum
Guidelines for Solid-State Spin Defects, _Nat. Rev. Mater._ **6**, 906 (2021).

[56] V. Jacques, P. Neumann, J. Beck, M. Markham, D. Twitchen, J. Meijer, F. Kaiser, G. Balasubramanian, F. Jelezko, and
J. Wrachtrup, Dynamic Polarization of Single Nuclear Spins by Optical Pumping of Nitrogen-Vacancy Color Centers in
Diamond at Room Temperature, _Phys. Rev. Lett._ **102**, 057403 (2009).

[57] D. F. V. James, P. G. Kwiat, W. J. Munro, and A. G. White, Measurement of Qubits, _Phys. Rev. A_ **64**, 052312 (2001).

[58] R. Rossignoli, J. M. Matera, and N. Canosa, Measurements, Quantum Discord, and Parity in Spin-1 Systems, _Phys. Rev._
_A 86_ **473**, 022104 (2012).

[59] L. Derkacz and L. Jakobczyk, Entanglement versus Entropy for a Class of Mixed Two-Qutrit States, _Phys. Rev. A_ **76**,
042304 (2007).

[60] R. Fischer, A. Jarmola, P. Kehayias, and D. Budker, Optical Polarization of Nuclear Ensembles in Diamond, _Phys. Rev._
_B_ **87**, 125207 (2013).


10


**Supplementary Material**


**I.** **ZERO-DISCORD STATES IN THE PARAMETER SPACE**


In the main text, we elucidated that the ensemble of zero-discord states within the parameter space is bifurcated,
encompassing the line _χ_ 1 and the plane _χ_ 2 . Herein, we offer a meticulous exposition. The evolution of the two-qutrit
Bell-diagonal states, subject to the local dephasing noise of the first qutrit, is


_ρ_ [deph] BD [(] _[c]_ [0] _[, c]_ [2] _[, λ]_ [)]



_c_ 0 0 0 0 _c_ 0 _λ_ 0 0 0 _c_ 0 _λ_ [2]

0 _c_ 1 0 0 0 _c_ 1 _λ c_ 1 _λ_ [2] 0 0
0 0 _c_ 2 _c_ 2 _λ_ 0 0 0 _c_ 2 _λ_ [2] 0
0 0 _c_ 2 _λ_ _c_ 2 0 0 0 _c_ 2 _λ_ 0
_c_ 0 _λ_ 0 0 0 _c_ 0 0 0 0 _c_ 0 _λ_
0 _c_ 1 _λ_ 0 0 0 _c_ 1 _c_ 1 _λ_ 0 0
0 _c_ 1 _λ_ [2] 0 0 0 _c_ 1 _λ_ _c_ 1 0 0
0 0 _c_ 2 _λ_ [2] _c_ 2 _λ_ 0 0 0 _c_ 2 0
_c_ 0 _λ_ [2] 0 0 0 _c_ 0 _λ_ 0 0 0 _c_ 0




















= [1]

3




















_,_ (S1)



where _c_ 1 = 1 _−_ _c_ 0 _−_ _c_ 2 . The dynamics are characterized by three variables: _c_ 0, _c_ 2, and _λ_, which collectively
constitute a triangular prism-shaped parameter space, as illustrated in Figure 1 of the main text. The necessary and
sufficient criterion for the quantum discord (QD) of a biparticle quantum state _ρ_ _AB_ to vanish is that _ρ_ _AB_ belongs to
quantum-classical states [RefS52] with the form


_ρ_ q _−_ c = � _p_ _i_ _ρ_ _i_ _⊗|ϕ_ _i_ _⟩⟨ϕ_ _i_ _|._ (S2)


_i_


Here _p_ _i_ _≥_ 0 represents the probability associated with each state _|ϕ_ _i_ _⟩_ and satisfy [�] _i_ _[p]_ _[i]_ [ = 1,] _[ ⟨][ϕ]_ _[i]_ _[|][ϕ]_ _[j]_ _[⟩]_ [=] _[ δ]_ _[ij]_ [ ensures]
that the states _|ϕ_ _i_ _⟩_ are mutually exclusive, and _ρ_ _i_ denotes a density matrix of subsystem _A_ . A crucial property of
quantum-classical states is that there exists a von Neumann measurement on subsystem _B_, which leaves the state of
subsystem _A_ undisturbed. Therefore, the QD of quantum-classical states is 0.
The states in _χ_ 1 satisfy _c_ 0 = _c_ 2 = 1 _/_ 3 and can be written as




















1 0 0 0 _λ_ 0 0 0 _λ_ [2]

0 1 0 0 0 _λ λ_ [2] 0 0
0 0 1 _λ_ 0 0 0 _λ_ [2] 0

0 0 _λ_ 1 0 0 0 _λ_ 0

_λ_ 0 0 0 1 0 0 0 _λ_

0 _λ_ 0 0 0 1 _λ_ 0 0
0 _λ_ [2] 0 0 0 _λ_ 1 0 0
0 0 _λ_ [2] _λ_ 0 0 0 1 0
_λ_ [2] 0 0 0 _λ_ 0 0 0 1



_ρ_ _χ_ 1 = 9 [1]




















_._ (S3)


11


Supplementary Figure S1: **Numerical Results of Quantum Discord in The Parameter Space.** The numerical results
suggest that the quantum-classical states with zero QD contain two parts: the line _χ_ 1 where _c_ 0 = _c_ 2 = 1 _/_ 3 and the plane _χ_ 2
where _λ_ = 0.


They can be decomposed into _ρ_ _χ_ 1 = 3 [1] [(] _[ρ]_ [0] _[|][ϕ]_ [0] _[⟩⟨][ϕ]_ [0] _[|]_ [ +] _[ ρ]_ [1] _[|][ϕ]_ [1] _[⟩⟨][ϕ]_ [1] _[|]_ [ +] _[ ρ]_ [2] _[|][ϕ]_ [2] _[⟩⟨][ϕ]_ [2] _[|]_ [) with]



12


(S4)







_λ_ 1 _λ_
_λ_ [2] _λ_ 1





 _,_







_|ϕ_ 0 _⟩_ = ~~_√_~~ 13



 11


1




 _, ρ_ 0 = [1] 3



3



 _λ_ 1 _λ λ_ 1 _λ_ [2]

_λ_ [2] _λ_ 1





_−_ 1+ ~~_√_~~



_−_ 3i


2



_|ϕ_ 1 _⟩_ = ~~_√_~~ 13









_−_ 1+ 3i

2
1

_−_ 1 _−_ ~~_√_~~ 3i





 _,_



_−_ 1 _−_ ~~_√_~~



3i

2



_|ϕ_ 2 _⟩_ = ~~_√_~~ 13









_−_ 1 _−_ 3i


2
1

_−_ 1+ ~~_√_~~ 3i





 _,_



_−_ 1+ ~~_√_~~



_−_ 1+ 3i _λ_ 1 _−_ 1 _−_ 3i _λ_

2 2

_−_ 1 _−_ ~~_√_~~ 3i [2] _−_ 1+ ~~_√_~~ 3i



~~_√_~~ 3i _−_ 1 _−_ ~~_√_~~

_λ_ 1
2 2



~~_√_~~ 3i _−_ 1+ ~~_√_~~

_λ_
2 2



3i _λ_ [2]
2





 _,_



_ρ_ 1 = [1] 3







_−_ 1 _−_ ~~_√_~~
1

2

 _−_ 1+ ~~_√_~~ 3i _λ_ 1

2

_−_ 1 _−_ ~~_√_~~ 3i _−_ 1+ ~~_√_~~

_λ_ [2]

 2 2



~~_√_~~ 3i _−_ 1+ ~~_√_~~

_λ_ [2]
2 2



_−_ 1 _−_ ~~_√_~~



_−_ 1 _−_ 3i _λ_ 1 _−_ 1+ 3i _λ_

2 2

_−_ 1+ ~~_√_~~ 3i [2] _−_ 1 _−_ ~~_√_~~ 3i



_−_ ~~_√_~~ 3i _−_ 1+ ~~_√_~~

_λ_ 1
2 2



3i _λ_ 1
2

~~_√_~~ 3i _−_ 1 _−_ ~~_√_~~

_λ_
2 2



3i _λ_ [2]
2





 _._




_ρ_ 2 = 3 [1]







_−_ 1+ ~~_√_~~
1

2

 _−_ 1 _−_ ~~_√_~~ 3i _λ_ 1

2

_−_ 1+ ~~_√_~~ 3i _−_ 1 _−_ ~~_√_~~

_λ_ [2]

 2 2



~~_√_~~ 3i _−_ 1 _−_ ~~_√_~~

_λ_ [2]
2 2



3i _λ_ 1
2



The states in _χ_ 2 satisfy _λ_ = 0 and can be decomposed into




















_ρ_ _χ_ 2 = 3 [1]




















_c_ 0 0 0 0 0 0 0 0 0
0 _c_ 1 0 0 0 0 0 0 0
0 0 _c_ 2 0 0 0 0 0 0
0 0 0 _c_ 2 0 0 0 0 0
0 0 0 0 _c_ 0 0 0 0 0
0 0 0 0 0 _c_ 1 0 0 0
0 0 0 0 0 0 _c_ 1 0 0
0 0 0 0 0 0 0 _c_ 2 0
0 0 0 0 0 0 0 0 _c_ 0



= [1] 0 _[|][ϕ]_ 0 _[′]_ _[⟩⟨][ϕ]_ 0 _[′]_ _[|]_ [ +] _[ ρ]_ 1 _[′]_ _[|][ϕ]_ 1 _[′]_ _[⟩⟨][ϕ]_ 1 _[′]_ _[|]_ [ +] _[ ρ]_ 2 _[′]_ _[|][ϕ]_ 2 _[′]_ _[⟩⟨][ϕ]_ 2 _[′]_ _[|]_ [)] _[ .]_ (S5)

3 [(] _[ρ]_ _[′]_



with





 _, ρ_ _[′]_ 0 [=]



_c_ 0 0 0

 0 _c_ 2 0

 0 0 _c_ 1





 _,_



_|ϕ_ _[′]_ 0 _[⟩]_ [=]


_|ϕ_ _[′]_ 1 _[⟩]_ [=]


_|ϕ_ _[′]_ 2 _[⟩]_ [=]



 10


0




 00


1




 01


0






 _, ρ_ _[′]_ 1 [=]



_c_ 1 0 0

 0 _c_ 0 0

 0 0 _c_ 2





 _,_



(S6)





 _, ρ_ _[′]_ 2 [=]



_c_ 2 0 0

 0 _c_ 1 0

 0 0 _c_ 0



 _._



Hence, any quantum state residing within either _χ_ 1 or _χ_ 2 is categorized as a quantum-classical state, thereby possessing
a QD value of zero. Regarding other quantum states, analytically demonstrating their non-zero QD remains a
challenging task. Consequently, we resorted to numerical methods, and the outcomes presented in Fig. S1 suggest
that these states indeed exhibit a non-zero QD.


**II.** **EQUATION OF THE** _d_ 1 = _d_ 2 **SURFACE AND THE SUDDEN TRANSITION**


In this section, we derive the equation governing the surface _d_ 1 = _d_ 2 depicted in Fig. 1 of the main text and
demonstrate the occurrence of the sudden transition phenomenon.
Consider a Bell-diagonal state _ρ_ P = _ρ_ [deph] BD [(] _[c]_ [0] _[, c]_ [2] _[, λ]_ [), which represents a specific point P within the parameter space.]
The QD of this state is determined by the minimum of _d_ 1 and _d_ 2 . Here, _d_ 1 represents the minimum Schatten 1-norm
trace distance between _ρ_ P and any quantum state belonging to _χ_ 1, while _d_ 2 signifies the corresponding minimum


13


distance to quantum states in _χ_ 2 . We posit that the quantum state within _χ_ 1 (or _χ_ 2 ) that is closest to _ρ_ P is identified
by the intersection point of the perpendicular line extending from point P to the line _χ_ 1 (or plane _χ_ 2 ). The detailed
derivations underlying these assertions are outlined below.


  - Closest quantum state to _ρ_ P in the line _χ_ 1 .
A quantum state _σ_ 1 in _χ_ 1 has the form _σ_ 1 ( _λ_ _[′]_ ) = _ρ_ [deph] BD [(1] _[/]_ [3] _[,]_ [ 1] _[/]_ [3] _[, λ]_ _[′]_ [). The Schatten 1-norm trace of it to] _[ ρ]_ [P] [ can]
be calculated as


_||ρ_ P _−_ _σ_ 1 ( _λ_ _[′]_ ) _||_ 1 = _||ρ_ [deph] BD [(] _[c]_ [0] _[, c]_ [2] _[, λ]_ [)] _[ −]_ _[ρ]_ [deph] BD [(1] _[/]_ [3] _[,]_ [ 1] _[/]_ [3] _[, λ]_ _[′]_ [)] _[||]_ [1]

















������������������
















������������������



������������������

������������������



������������������������������������ 1





















=



������������������������������������



1

9



 33 _c_ 0 _cλ_ 0 _− −_ 1 _λ_ _[′]_ 33 _c_ 0 _cλ_ 0 _− −_ 1 _λ_ 33 _c_ 0 _cλ_ 0 _λ −−_ _λλ_ _[′]_ 00 00 00 00 00 00 

 3 _c_ 0 _λ_ [2] _−_ _λ_ _[′]_ [2] 3 _c_ 0 _λ −_ _λ_ _[′]_ 3 _c_ 0 _−_ 1 0 0 0 0 0 0 

1  0 0 0 3 _c_ 1 _−_ 1 3 _c_ 1 _λ −_ _λ_ _[′]_ 3 _c_ 1 _λ_ [2] _−_ _λ_ _[′]_ [2] 0 0 0 

= 9  00 00 00 33 _c_ 1 _cλ_ 1 _λ_ [2] _−−_ _λλ_ _[′][′]_ [2] 33 _c_ 1 _cλ_ 1 _− −_ 1 _λ_ _[′]_ 33 _c_ 1 _cλ_ 1 _− −_ 1 _λ_ _[′]_ 00 00 00 

 0 0 0 0 0 0 3 _c_ 2 _−_ 1 3 _c_ 2 _λ −_ _λ_ _[′]_ 3 _c_ 2 _λ_ [2] _−_ _λ_ _[′]_ [2] 
 

0 0 0 0 0 0 3 _c_ 2 _λ −_ _λ_ _[′]_ 3 _c_ 2 _−_ 1 3 _c_ 2 _λ −_ _λ_ _[′]_

������������������������������������  0 0 0 0 0 0 3 _c_ 2 _λ_ [2] _−_ _λ_ _[′]_ [2] 3 _c_ 2 _λ −_ _λ_ _[′]_ 3 _c_ 2 _−_ 1 ������������������������������������ 1

= _||ρ_ ˜( _c_ 0 _, λ, λ_ _[′]_ ) _||_ 1 + _||ρ_ ˜( _c_ 1 _, λ, λ_ _[′]_ ) _||_ 1 + _||ρ_ ˜( _c_ 2 _, λ, λ_ _[′]_ ) _||_ 1 _,_
(S7)

where



3 _c_ 0 _−_ 1 0 0 0 3 _c_ 0 _λ −_ _λ_ _[′]_ 0 0 0 3 _c_ 0 _λ_ [2] _−_ _λ_ _[′]_ [2]

0 3 _c_ 1 _−_ 1 0 0 0 3 _c_ 1 _λ −_ _λ_ _[′]_ 3 _c_ 1 _λ_ [2] _−_ _λ_ _[′]_ [2] 0 0
0 0 3 _c_ 2 _−_ 1 3 _c_ 2 _λ −_ _λ_ _[′]_ 0 0 0 3 _c_ 2 _λ_ [2] _−_ _λ_ _[′]_ [2] 0
0 0 3 _c_ 2 _λ −_ _λ_ _[′]_ 3 _c_ 2 _−_ 1 0 0 0 3 _c_ 2 _λ −_ _λ_ _[′]_ 0
3 _c_ 0 _λ −_ _λ_ _[′]_ 0 0 0 3 _c_ 0 _−_ 1 0 0 0 3 _c_ 0 _λ −_ _λ_ _[′]_

0 3 _c_ 1 _λ −_ _λ_ _[′]_ 0 0 0 3 _c_ 1 _−_ 1 3 _c_ 1 _λ −_ _λ_ _[′]_ 0 0
0 3 _c_ 1 _λ_ [2] _−_ _λ_ _[′]_ [2] 0 0 0 3 _c_ 1 _λ −_ _λ_ _[′]_ 3 _c_ 1 _−_ 1 0 0
0 0 3 _c_ 2 _λ_ [2] _−_ _λ_ _[′]_ [2] 3 _c_ 2 _λ −_ _λ_ _[′]_ 0 0 0 3 _c_ 2 _−_ 1 0
3 _c_ 0 _λ_ [2] _−_ _λ_ _[′]_ [2] 0 0 0 3 _c_ 0 _λ −_ _λ_ _[′]_ 0 0 0 3 _c_ 0 _−_ 1


3 _c_ 0 _−_ 1 3 _c_ 0 _λ −_ _λ_ _[′]_ 3 _c_ 0 _λ_ [2] _−_ _λ_ _[′]_ [2] 0 0 0 0 0 0
3 _c_ 0 _λ −_ _λ_ _[′]_ 3 _c_ 0 _−_ 1 3 _c_ 0 _λ −_ _λ_ _[′]_ 0 0 0 0 0 0
3 _c_ 0 _λ_ [2] _−_ _λ_ _[′]_ [2] 3 _c_ 0 _λ −_ _λ_ _[′]_ 3 _c_ 0 _−_ 1 0 0 0 0 0 0
0 0 0 3 _c_ 1 _−_ 1 3 _c_ 1 _λ −_ _λ_ _[′]_ 3 _c_ 1 _λ_ [2] _−_ _λ_ _[′]_ [2] 0 0 0
0 0 0 3 _c_ 1 _λ −_ _λ_ _[′]_ 3 _c_ 1 _−_ 1 3 _c_ 1 _λ −_ _λ_ _[′]_ 0 0 0
0 0 0 3 _c_ 1 _λ_ [2] _−_ _λ_ _[′]_ [2] 3 _c_ 1 _λ −_ _λ_ _[′]_ 3 _c_ 1 _−_ 1 0 0 0
0 0 0 0 0 0 3 _c_ 2 _−_ 1 3 _c_ 2 _λ −_ _λ_ _[′]_ 3 _c_ 2 _λ_ [2] _−_ _λ_ _[′]_ [2]



0 0 0 0 0 0 3 _c_ 2 _λ_ [2] _−_ _λ_ _[′]_ [2] 3 _c_ 2 _λ −_ _λ_ _[′]_ 3 _c_ 2 _−_ 1





















=



������������������������������������

������������������������������������



������������������������������������



1

9



0 0 0 0 0 0 3 _c_ 2 _λ −_ _λ_ _[′]_ 3 _c_ 2 _−_ 1 3 _c_ 2 _λ −_ _λ_ _[′]_



_ρ_ ˜( _c_ _i_ _, λ, λ_ _[′]_ )



 _._ (S8)





3 _c_ _i_ _λ −_ _λ_ _[′]_ 3 _c_ _i_ _−_ 1 3 _c_ _i_ _λ −_ _λ_ _[′]_



= [1]

9



3 _c_ _i_ _−_ 1 3 _c_ _i_ _λ −_ _λ_ _[′]_ 3 _c_ _i_ _λ_ [2] _−_ _λ_ _[′]_ [2]

 3 _c_ _i_ _λ −_ _λ_ _[′]_ 3 _c_ _i_ _−_ 1 3 _c_ _i_ _λ −_ _λ_ _[′]_

 3 _c_ _i_ _λ_ [2] _−_ _λ_ _[′]_ [2] 3 _c_ _i_ _λ −_ _λ_ _[′]_ 3 _c_ _i_ _−_ 1







3 _c_ _i_ _λ_ [2] _−_ _λ_ _[′]_ [2] 3 _c_ _i_ _λ −_ _λ_ _[′]_ 3 _c_ _i_ _−_ 1



Let us define the three eigenvalues of ˜ _ρ_ ( _c_ _i_ _, λ, λ_ _[′]_ ) as _ϵ_ _i,_ 1, _ϵ_ _i,_ 2, and _ϵ_ _i,_ 3 . Then, it follows that _ϵ_ _i,_ 1 + _ϵ_ _i,_ 2 + _ϵ_ _i,_ 3 =
Tr[˜ _ρ_ ( _c_ _i_ _, λ, λ_ _[′]_ )] = _c_ _i_ _−_ 1 _/_ 3. Additionally, _||ρ_ ˜( _c_ _i_ _, λ, λ_ _[′]_ ) _||_ 1 = [�] [3] _j_ =1 _[|][ϵ]_ _[i,j]_ _[| ≥|]_ [ �] [3] _j_ =1 _[ϵ]_ _[i,j]_ _[|]_ [ =] _[ |][c]_ _[i]_ _[ −]_ [1] _[/]_ [3] _[|]_ [ :=] _[ d]_ [min] _[,]_ [1] [.]
The quantum state that corresponds to the intersection point of the perpendicular line extending from point
P to the line _χ_ 1 is denoted as _σ_ 1 ( _λ_ ). The Schatten 1-norm trace distance between _σ_ 1 ( _λ_ ) and _ρ_ P is given by
_||ρ_ P _−σ_ 1 ( _λ_ ) _||_ 1 = [�] [2] _i_ =0 _[||][ρ]_ [˜][(] _[c]_ _[i]_ _[, λ, λ]_ [)] _[||]_ [1] [. The three eigenvalues of ˜] _[ρ]_ [(] _[c]_ _[i]_ _[, λ, λ]_ [) are ˜] _[ϵ]_ _[i,]_ [1] [ = (3] _[c]_ _[i]_ _[−]_ [1)(] _[λ]_ [2] _[−]_ [1)] _[/]_ [9 and ˜] _[ϵ]_ _[i,]_ [2] _[|]_ [3] [ =]

[(3 _c_ _i_ _−_ 1)( _λ_ [2] +2) _±_ ~~�~~ (3 _c_ _i_ _−_ 1) [2] _λ_ [2] (8 + _λ_ [2] )] _/_ 18. It is noteworthy that _|_ (3 _c_ _i_ _−_ 1)( _λ_ [2] +2) _| ≥|_ �(3 _c_ _i_ _−_ 1) [2] _λ_ [2] (8 + _λ_ [2] ) _|_ .



(3 _c_ _i_ _−_ 1) [2] _λ_ [2] (8 + _λ_ [2] )] _/_ 18. It is noteworthy that _|_ (3 _c_ _i_ _−_ 1)( _λ_ [2] +2) _| ≥|_ �



Consequently,of[(3 _||c_ _i_ _ρ_ ˜ _−_ ( _c_ 1)( _i_ _, λ, λλ_ [2] +2) _[′]_ ) _|| ||_ 1 _ρ_ ˜ _±_, as well as( _c_ ~~�~~ _i_ _, λ, λ_ (3 _c_ _i_ _−_ ) _||_ 1 _||_ 1) = _ρ_ [2] P _λ | −ϵ_ ˜ [2] _i,_ (8 + 1 _σ|_ 1 +( _λλ|_ ) _ϵ_ ˜ [2] _||_ _i,_ )] 21 _/|_, is attained when18. It is noteworthy that+ _|ϵ_ ˜ _i_ 3 _|_ = _|c_ _i_ _−_ 1 _/_ 3 _λ|_ = _[′]_ = _d λ_ min . Therefore, we have rigorously demonstrated _|_ _,_ (3 1 . This establishes that the minimum value _c_ _i_ _−_ 1)( _λ_ [2] +2) _| ≥|_ �(3 _c_ _i_ _−_ 1) [2] _λ_ [2] (8 + _λ_ [2] ) _|_ .
that the quantum state within the set _χ_ 1 that is closest to _ρ_ P corresponds precisely to the intersection point of
the perpendicular line extending from point P to the line _χ_ 1 .




- Closest quantum state to _ρ_ in the plane _χ_ 2 .

A quantum state _σ_ 2 in _χ_ 2 has the form _σ_ 2 ( _c_ _[′]_ 0 _[, c]_ 2 _[′]_ [) =] _[ ρ]_ [deph] BD [(] _[c]_ 0 _[′]_ _[, c]_ 2 _[′]_ _[,]_ [ 0). Similar to the transformation of Eq.(][S7][),]
the Schatten 1-norm trace of _σ_ 2 ( _c_ _[′]_ 0 _[, c]_ 2 _[′]_ [) to] _[ ρ]_ [P] [can be calculated as]


_||ρ_ P _−_ _σ_ 2 ( _c_ _[′]_ 0 _[, c]_ 2 _[′]_ [)] _[||]_ [1] [=] _[ ||][ρ]_ [deph] BD [(] _[c]_ [0] _[, c]_ [2] _[, λ]_ [)] _[ −]_ _[ρ]_ [deph] BD [(] _[c]_ 0 _[′]_ _[, c]_ 2 _[′]_ _[,]_ [ 0)] _[||]_ [1]



�����������������



_c_ 0 _−_ _c_ _[′]_ 0 _c_ 0 _λ_ _c_ 0 _λ_ 0 0 0 0 0 0

 _c_ 0 _λ_ _c_ 0 _−_ _c_ _[′]_ 0 _c_ 0 _λ_ 0 0 0 0 0 0 

 _c_ 0 _λ_ [2] _c_ 0 _λ_ _c_ 0 _−_ _c_ _[′]_ 0 0 0 0 0 0 0 

1  0 0 0 _c_ 1 _−_ _c_ _[′]_ 1 _c_ 1 _λ_ _c_ 1 _λ_ [2] 0 0 0 

= 3  0 0 0 _c_ 1 _λ_ _c_ 1 _−_ _c_ _[′]_ 1 _c_ 1 _λ_ 0 0 0 

 0 0 0 _c_ 1 _λ_ [2] _c_ 1 _λ_ _c_ 1 _−_ _c_ _[′]_ 1 0 0 0 
 
 0 0 0 0 0 0 _c_ 2 _−_ _c_ _[′]_ 2 _c_ 2 _λ_ _c_ 2 _λ_ [2] 
 

0 0 0 0 0 0 _c_ 2 _λ_ _c_ 2 _−_ _c_ _[′]_ 2 _c_ 2 _λ_

����������������������������������  0 0 0 0 0 0 _c_ 2 _λ_ [2] _c_ 2 _λ_ _c_ 2 _−_ _c_ _[′]_ 2 ���������������������������������� 1

= _||ρ_ ˜( _c_ 0 _, c_ _[′]_ 0 _[, λ]_ [)] _[||]_ [1] [+] _[ ||][ρ]_ [˜][(] _[c]_ [1] _[, c]_ _[′]_ 1 _[, λ]_ [)] _[||]_ [1] [+] _[ ||][ρ]_ [˜][(] _[c]_ [2] _[, c]_ _[′]_ 2 _[, λ]_ [)] _[||]_ [1] _[,]_



14


(S9)



_c_ 0 _−_ _c_ _[′]_ 0 _c_ 0 _λ_ _c_ 0 _λ_ [2] 0 0 0 0 0 0
_c_ 0 _λ_ _c_ 0 _−_ _c_ _[′]_ 0 _c_ 0 _λ_ 0 0 0 0 0 0
_c_ 0 _λ_ [2] _c_ 0 _λ_ _c_ 0 _−_ _c_ _[′]_ 0 0 0 0 0 0 0
0 0 0 _c_ 1 _−_ _c_ _[′]_ 1 _c_ 1 _λ_ _c_ 1 _λ_ [2] 0 0 0
0 0 0 _c_ 1 _λ_ _c_ 1 _−_ _c_ _[′]_ 1 _c_ 1 _λ_ 0 0 0
0 0 0 _c_ 1 _λ_ [2] _c_ 1 _λ_ _c_ 1 _−_ _c_ _[′]_ 1 0 0 0
0 0 0 0 0 0 _c_ 2 _−_ _c_ _[′]_ 2 _c_ 2 _λ_ _c_ 2 _λ_ [2]



0 0 0 0 0 0 _c_ 2 _λ_ _c_ 2 _−_ _c_ _[′]_ 2 _c_ 2 _λ_
0 0 0 0 0 0 _c_ 2 _λ_ [2] _c_ 2 _λ_ _c_ 2 _−_ _c_ _[′]_ 2



�����������������




















=



�����������������



1

3




















where



_c_ _i_ _λ_ _c_ _i_ _−_ _c_ _[′]_ _i_ _c_ _i_ _λ_
_c_ _i_ _λ_ [2] _c_ _i_ _λ_ _c_ _i_ _−_ _c_ _[′]_ _i_



˜
_ρ_ ( _c_ _i_ _, c_ _[′]_ _i_ _[, λ]_ [) =] [1]

3







_c_ _i_ _−_ _c_ _[′]_ _i_ _c_ _i_ _λ_ _c_ _i_ _λ_ [2]

 _c_ _i_ _λ_ _c_ _i_ _−_ _c_ _[′]_ _i_ _c_ _i_ _λ_

 _c_ _i_ _λ_ [2] _c_ _i_ _λ_ _c_ _i_ _−_



 _._ (S10)





The three eigenvalues of ˜ _ρ_ ( _c_ _i_ _, c_ _[′]_ _i_ _[, λ]_ [) are] _[ ν]_ _[i,]_ [1] [ =] _[ c]_ _[i]_ _[−][c]_ _[′]_ _i_ _[−][c]_ _[i]_ _[λ]_ [2] [, and] _[ ν]_ _[i,]_ [2] _[|]_ [3] [=] _[ c]_ _[i]_ _[−][c]_ _[′]_ _i_ [+] [1] 2 _[c]_ _[i]_ [(] _[λ]_ [2] _[±]_ _√_



_λ_ [4] + 8 _λ_ [2] ). Accordingly,



2
� _ν_ _i,_ 1 _|_ +


_i_ =0



2
� _|_ ( _ν_ _i,_ 2 _−_ _ν_ _i,_ 3 ) _|_ (S11)


_i_ =0



_||ρ_ P _−_ _σ_ 2 ( _c_ _[′]_ 0 _[, c]_ 2 _[′]_ [)] _[||]_ [1] [=]



2
� ( _|ν_ _i,_ 1 _|_ + _|ν_ _i,_ 2 _|_ + _|ν_ _i,_ 3 _|_ ) _≥|_


_i_ =0



2
� _|c_ _i_ �


_i_ =0



2
�



2
� _c_ _i_ _−_


_i_ =0



2
�



2
� _c_ _[′]_ _i_ _[−]_


_i_ =0



2
� _c_ _i_ _λ_ [2] _|_ +


_i_ =0



=
_|_



_λ_ [4] + 8 _λ_ [2] _|_ (S12)



= _λ_ [2] + ~~�~~ _λ_ [4] + 8 _λ_ [2] := _d_ min _,_ 2 _._ (S13)



It is noticed that when _c_ 0 = _c_ _[′]_ 0 [and] _[ c]_ [2] [=] _[ c]_ _[′]_ 2


_||ρ_ P _−_ _σ_ 2 ( _c_ 0 _, c_ 2 ) _||_ 1



= _λ_ [2] + [1]

2



2 �
�� _λ_ _−_ � _λ_ [4] + 8 _λ_ [2] ~~�~~ + 1
� � 2



��� _λ_ 2 + � _λ_ [4] + 8 _λ_ [2] � ~~�~~ �



= _λ_ [2] + � _λ_ [4] + 8 _λ_ [2] = _d_ min _,_ 2 (S14)



Therefore, we have proved that for any quantum states _σ_ 2 _∈_ _χ_ 2, the minimum value of _||ρ_ P _−_ _σ_ 2 ( _c_ _[′]_ 0 _[, c]_ 2 _[′]_ [)] _[||]_ [1] [is]
achieved when _c_ 0 = _c_ _[′]_ 0 _[, c]_ [2] [=] _[ c]_ _[′]_ 2 [. This minimum value corresponds precisely to the quantum state that lies at]
the intersection point of the perpendicular line extending from point P to the plane _χ_ 2 .



To sum up, we have calculated and demonstrated that _d_ 1 = [�] [3] _i_ =0 _[|][c]_ _[i]_ _[ −]_ [1] _[/]_ [3] _[|]_ [ and] _[ d]_ [2] [ =] _[ λ]_ [2] [ +] _√_



To sum up, we have calculated and demonstrated that _d_ 1 = [�] _i_ =0 _[|][c]_ _[i]_ _[ −]_ [1] _[/]_ [3] _[|]_ [ and] _[ d]_ [2] [ =] _[ λ]_ [2] [ +] _√λ_ [4] + 8 _λ_ [2] . Equation

of the _d_ 1 = _d_ 2 surface can be formulated as _λ√λ_ [2] + 8 + _λ_ [2] = _|_ 1 _−_ 3 _c_ 0 _|_ + _|_ 1 _−_ 3 _c_ 1 _|_ + _|_ 1 _−_ 3 _c_ 2 _|_ . For any quantum state

within the parameter space, its QD is min _{_ [�] [3] _i_ =0 _[|][c]_ _[i]_ _[ −]_ [1] _[/]_ [3] _[|][, λ]_ [2] [ +] _√λ_ [4] + 8 _λ_ [2] _}_ .



within the parameter space, its QD is min _{_ [�] _i_ =0 _[|][c]_ _[i]_ _[ −]_ [1] _[/]_ [3] _[|][, λ]_ [2] [ +] _√λ_ [4] + 8 _λ_ [2] _}_ .

It is noteworthy that _d_ 1 does not depend on _λ_ and _d_ 2 is independent of both _c_ 0 and _c_ 2 . The trajectory traced by
_ρ_ [deph] BD within the parameter space corresponds to a straight line that is parallel to the _λ_ -axis. In the region above the
_d_ 1 = _d_ 2 surface, where _d_ 1 is less than _d_ 2 and remains constant, the QD of _ρ_ [deph] BD remains unchanged. Conversely, in
the region below the _d_ 1 = _d_ 2 surface, where _d_ 2 is smaller than _d_ 1 and decays as _λ_ approaches 0, the QD of _ρ_ [deph] BD
gradually decreases. Therefore, the QD dynamics can exhibit a sudden transition whenever its trajectory intersects
the _d_ 1 = _d_ 2 surface.



**III.** **PREPARATION AND MEASUREMENT OF THE BELL-DIAGONAL STATE**


**A.** **Experiment setup**


The experimental setup consists of three parts: the microwave system, the optical system and the sample.


15


Supplementary Figure S2: **Dephasing times of the electron spin qutrit.** The dephasing time for the transition _|_ 0 _⟩_ e _→_
_|−_ 1 _⟩_ e ( _|_ 0 _⟩_ e _→|_ +1 _⟩_ e ) within the subspace of the nuclear spin state _|_ +1 _⟩_ n was measured via the Ramsey sequence. Corresponding
_ω_ = _ω_ _|_ 0 _⟩_ e _→|−_ 1 _⟩_ e + _δ_ ( _ω_ = _ω_ _|_ 0 _⟩_ e _→|_ +1 _⟩_ e + _δ_ ), respectively, where _δ_ = 10 kHz represents the detuning of the MW pulse. The Rabi
frequency of these MW pulses was calibrated to 0.2 MHz.


The microwave system generates and transmits microwave (MW) and radio-frequency (RF) pulses to manipulate the
NV center. The MW pulses used in our experiment were generated by an arbitrary wave generator (Keysight M8190A),
amplified by an amplifier (Mini-Circuits, ZVE-3W-183+) before being fed into a diplexer (Marki DPX0R5+DPX0508). The RF pulses were generated by another port of the arbitrary wave generator, amplified by an amplifier (Mini
Circuit LZY-22+), and then fed into the diplexer. Finally, the MW and RF pulses combined by the diplexer were fed
into a home-designed coplanar waveguide to manipulate the evolution of the NV center.
The optical system contains two components, the optic pumping component and the fluorescence collection component. The pumping component generates 532-nm laser pulses to initialize and readout the spin state of the NV
center. A polarizing beam splitter (PBS121) selects the S-polarized beam of the continuous 532-nm laser (generated
by MSL-III-532-150mW). The selected beam went through an acousto-optic modulator (ISOMET, AOMO 3200-121)
twice to obtain 532-nm laser pulses and to decrease the laser leakage. A quarter-wave plate (WPQ05ME-532) together with a mirror was utilized to change the polarization and transmission direction of the laser pulses so they can
pass through the acousto-optic modulator twice. Afterward, the laser pulses were coupled into an optical fiber via
a reflective collimator (F810FC-543) after the expansion of a beam expander (GBE05-A). The 532-nm laser pulses
were reflected by a dichroic mirror and a mirror. Finally, the laser pulses were focused to the sample by an oil object
(Olympus, PLAPON 60*O, NA 1.45). The fluorescence emitted by the sample went through the same oil object and
was collected by an avalanche photodiode (Perkin Elmer, SPCM-AQRH-14). The photon counting was processed by
a counter card.
The diamond was placed on a homemade coplanar waveguide in the confocal setup. The static magnetic field was
provided by a cylindrical permanent magnet ( _H_ = _D_ = 3 cm). A three-axis stage was utilized to adjust the position
of the magnet, such that the direction of the magnetic field is along the symmetry axis of the NV center. In our
experiment, the static magnetic field was _B ≈_ 500 G to effectively polarize the electron and nuclear spin with 0.92(1)
and 0.98(1) polarization rates, respectively.
The diamond sample utilized in this work was isotopically purified with the concentration of the [12] C atom exceeding
99.9%. The dephasing times of the electron spin qutrit were measured and the results are presented in Fig.S2. We
fitted the data to the function _A_ exp � _−_ ( _t/T_ 2 _[∗]_ _,_ e [)] _[n]_ [�] sin[ _ω_ _[′]_ ( _t −_ _t_ 0 )] + _y_ 0 . The results is _T_ 2 _[∗]_ [= 45(3)] _[ µs]_ [ for transition]
_|_ 0 _⟩_ e _→| −_ 1 _⟩_ e and _T_ 2 _[∗]_ [= 43(2)] _[ µs]_ [ for transition] _[ |]_ [0] _[⟩]_ [e] _[→|]_ [ + 1] _[⟩]_ [e] [.]


16


Supplementary Figure S3: **Diagram of the pulse sequence.** Four parts, polarization, state preparation, evolution under
the dephasing noise, and measurement are included. Information of the pulses is concluded in table S1. The matrices below
show the theoretical evolution of the two-qutrit system.


Supplementary Table S1: **Detailed information about the parameters of the MW and RF pulses used in the**
**process of the Bell-diagonal state preparation.**
step pulse frequency transition states pulse phase and rotation angle
I _ω_ e1 _|_ 10 _⟩↔|_ 20 _⟩_ Y, _α_ = 2 arccos ~~_[√]_~~ ~~_c_~~ 0



II


III



_ω_ n3 _|_ 10 _⟩↔|_ 11 _⟩_ Y, _θ_ 1 = 2 arccos
~~�~~

_ω_ n1 _|_ 20 _⟩↔|_ 21 _⟩_ Y, _θ_ 2 = 2 arccos
~~�~~

_ω_ n4 _|_ 11 _⟩↔|_ 12 _⟩_ Y, _θ_ 3 = 2 arccos
~~�~~

_ω_ n2 _|_ 21 _⟩↔|_ 22 _⟩_ Y, _θ_ 4 = 2 arccos
~~�~~

_ω_ e2 _|_ 00 _⟩↔|_ 10 _⟩_ -Y, _π_
_ω_ e3 _|_ 12 _⟩↔|_ 22 _⟩_ Y, _π_
_ω_ e1 _|_ 10 _⟩↔|_ 20 _⟩_ -Y, _π_
_ω_ e4 _|_ 02 _⟩↔|_ 12 _⟩_ Y, _π_


**B.** **Preparation of the Bell-Diagonal State**



1

3


1

3


1

2


1

2



The two cases of the Bell-diagonal states investigated in the experiment have the form _ρ_ BD = _c_ 0 _|_ Ψ 00 _⟩⟨_ Ψ 00 _|_ +
_c_ 1 _|_ Ψ 01 _⟩⟨_ Ψ 01 _|_ + _c_ 2 _|_ Ψ 02 _⟩⟨_ Ψ 02 _|_ with restrictions _c_ 0 + _c_ 1 + _c_ 2 = 1 and _c_ 1 = 0. The corresponding density matrix can be


17


Supplementary Figure S4: **Measurement pulse sequences of the Bell-diagonal state.** _ρ_ _f_ denotes the density matrix of
the prepared Bell-diagonal state. Π [X(Y)] _m,n_ [(hΠ] [X(Y)] _m,n_ [) denotes the selective] _[ π]_ [ (] _[π/]_ [2) pulse applied between state] _[ |][m][⟩]_ [and state] _[ |][n][⟩]_
along X (Y) axis. _n_ _j_ ( _j ∈_ [1 _,_ 21]) indicates the detected photoluminescence rate after applying these pulse sequences.


written as




















_ρ_ [exp] BD [=] [1]

3



_c_ 0 0 0 0 _c_ 0 0 0 0 _c_ 0

 0 0 0 0 0 0 0 0 0


 0 0 _c_ 2 _c_ 2 0 0 0 _c_ 2 0
 0 0 _c_ 2 _c_ 2 0 0 0 _c_ 2 0

 _c_ 0 0 0 0 _c_ 0 0 0 0 _c_ 0

 0 0 0 0 0 0 0 0 0

 0 0 0 0 0 0 0 0 0


0 0 _c_ 2 _c_ 2 0 0 0 _c_ 2 0

 _c_ 0 0 0 0 _c_ 0 0 0 0 _c_ 0



_._ (S15)



The electron (nuclear) spin corresponds to the first (second) qutrit and the states _|−_ 1 _⟩_ e _, |_ 0 _⟩_ e _, |_ +1 _⟩_ e ( _|−_ 1 _⟩_ n _, |_ 0 _⟩_ n _, |_ +1 _⟩_ n )
correspond to the _|_ 0 _⟩, |_ 1 _⟩, |_ 2 _⟩_ of the first (second) qutrit, respectively. MW and radio frequency (RF) pulses were
utilized to control the state of the electron spin and the nuclear spin, respectively.
As shown in Fig. S3, these states can be prepared following the procedures below.


(I) Apply a 532-nm laser pulse to polarize the two-qutrit system to state _|_ 10 _⟩_, as shown by the first density matrix
in Fig. S3.


(II) Apply a selective MW pulse with frequency _ω_ e1 to transfer the polarized state to state _[√]_ ~~_c_~~ 0 ~~_|_~~ 10 _⟩_ + _[√]_ ~~_c_~~ 2 ~~_|_~~ 20 _⟩_ . Then,
waiting a free evolution time of 200 _µ_ s, the coherence of the electron spin will be dissipated. The state will be
left with the form _ρ_ II = _c_ 0 _|_ 10 _⟩⟨_ 10 _|_ + _c_ 2 _|_ 20 _⟩⟨_ 20 _|_ as shown by the second-density matrix in Fig. S3.


(III) Apply four selective RF pulses of frequency _ω_ n3, _ω_ n1, _ω_ n4 and _ω_ n2 with appropriate time-duration in sequence.


18



The system will be prepared to state _ρ_ II as shown by the third-density matrix in Fig. S3,




















_ρ_ II = [1]

3



0 0 0 00 0 0 0 00 00 00 00 00


0 0 0 0 0 0 0 0 0

0 0 0 _c_ 0 _c_ 0 _c_ 0 0 0 0

0 0 0 _c_ 0 _c_ 0 _c_ 0 0 0 0

0 0 0 _c_ 0 _c_ 0 _c_ 0 0 0 0

0 0 0 0 0 0 _c_ 2 _c_ 2 _c_ 2


0 0 0 0 0 0 _c_ 2 _c_ 2 _c_ 2

0 0 0 0 0 0 _c_ 2 _c_ 2 _c_ 2



_._ (S16)



(IV) Apply four selective MW _π_ pulses with frequency _ω_ e2, _ω_ e3, _ω_ e1 and _ω_ e4 in sequence. The system will finally be
prepared to _ρ_ [exp] BD [as shown by the last density matrix in Fig.][ S3][.]


The Rabi frequency of the MW (RF) pulses was all set to 0.2 MHz (25 kHz). Details about which two energy levels
these pulses worked on, the phase, and the time duration (denoted by the rotation angle) of these pulses are given in
the table S1 below. Utilizing this method, the initial Bell-diagonal states in the blue and red trajectory of Figure 1
in the main text were prepared with fidelity 0.96(0.01) and 0.95(0.01), respectively.


**C.** **Measurement of the Dephased Bell-Diagonal States**


The final state of the two-qutrit system after an evolution of time duration _τ_ was measured via a set of pulse
sequences. It is noticed that we did not measure all the elements in the density matrix to reduce the experimental
complexity. Specifically, elements that are non-zero theoretically were all measured. Whereas, for elements that are
zero theoretically, we only measured a part of them. Experimental results of these elements were very close to zero,
showing this compromise is acceptable. The pulse sequences to measure the non-zero elements of the density matrix
were given in Fig. S4, where we relabeled _|_ 00 _⟩_, _|_ 01 _⟩_, _|_ 02 _⟩_, _|_ 10 _⟩_, _|_ 11 _⟩_, _|_ 12 _⟩_, _|_ 20 _⟩_, _|_ 21 _⟩_, and _|_ 22 _⟩_ as _|_ 1 _⟩_, _|_ 2 _⟩_, _|_ 3 _⟩_, _|_ 4 _⟩_, _|_ 5 _⟩_,
_|_ 6 _⟩_, _|_ 7 _⟩_, _|_ 8 _⟩_, and _|_ 9 _⟩_ for simplicity. With a normalized photoluminescence of different energy levels, all these elements
can be calculated.
We employed a maximum likelihood estimation (MLE) method to acquire the most possible physical state _ρ_ MLE

[RefS57]. After that, the QD of the _ρ_ MLE was obtained. Details about the maximum likelihood estimation and the
calculation of the QD were introduced in Ref. RefS42.


