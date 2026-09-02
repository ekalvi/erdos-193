# Novelty audit: Gaussian digit-sum phases in a coined quantum walk

**Audit date:** 2026-09-02

**Conclusion:** the broad quantum-walk idea is not novel. The exact four-phase model and
its numerical transport curve were not located in this search, but currently constitute
only a narrow, unverified candidate novelty.

## Claim being audited

The exploratory model applies

\[
C_t=D(i^{s_2(t)})H,\qquad D(u)=\operatorname{diag}(1,u),
\]

in a translation-invariant one-dimensional coined quantum walk. It also considers a
spatial version and uses the four-letter substitution

\[
\sigma(a)=a\,(a+1\bmod4)
\]

to derive dyadic block propagators

\[
B_{r+1}^{(a)}(k)=B_r^{(a+1)}(k)B_r^{(a)}(k).
\]

The audit distinguishes four possible claims:

1. using Thue--Morse/automatic sequences in quantum walks;
2. obtaining anomalous spreading or localization from those sequences;
3. exploiting substitution recursion for exponentially late quantum dynamics;
4. this exact four-phase coin family and its quantitative transport behavior.

## Search scope

Searches were run against OpenAlex, Crossref, the arXiv API, Google, and DuckDuckGo,
with citation chaining from the closest papers. Queries included combinations of:

- `Thue-Morse quantum walk`, `time-dependent coin`, `spatial coin`;
- `generalized/complex/cyclic/four-letter Thue-Morse quantum walk`;
- `i^popcount`, `i^{s_2(n)}`, `digit sum phase`, and `Prouhet-Thue-Morse`;
- `substitution quantum walk renormalization`, `morphic quantum drive`, and
  `recursive unitary propagator`.

Open-access full text was inspected for the closest works. This is a serious preliminary
audit, not a systematic-review guarantee: terminology and non-indexed literature could
still hide an exact match.

## Closest prior work

### Direct prior art on dynamic and static Thue--Morse coined walks

**N. Lo Gullo, C. V. Ambarish, T. Busch, L. Dell'Anna, and C. M. Chandrashekar,
“Dynamics and energy spectra of aperiodic discrete-time quantum walks,” Physical Review
E 96, 012111 (2017).**<br>
DOI: <https://doi.org/10.1103/PhysRevE.96.012111><br>
Preprint: <https://arxiv.org/abs/1611.04427>

This paper explicitly considers both:

- coins distributed by Fibonacci, Thue--Morse, and Rudin--Shapiro sequences across
  lattice positions; and
- a spatially homogeneous coin selected at each time according to those sequences.

It measures wave-packet spreading and survival behavior and reports mixed localized and
diffusing components for Thue--Morse walks. This anticipates the broad model class and
qualitative observations in the present experiment. Its coins are two real rotation coins
`C(theta_1)` and `C(theta_2)`, not the cyclic four-phase family used here.

**T. K. Bose, “Influence of generic quantum coins on the spreading and entanglement in
binary aperiodic quantum walks,” Quantum Information Processing 23 (2024).**<br>
DOI: <https://doi.org/10.1007/s11128-024-04306-z><br>
Preprint: <https://arxiv.org/abs/2307.06332>

This work studies dynamic and static binary Fibonacci, Thue--Morse, and Rudin--Shapiro
walks using generic complex `2 x 2` coin parameters. It maps localized, subdiffusive,
diffusive, and sub-ballistic regimes and coin--position entanglement. Consequently,
“generic phases plus Thue--Morse ordering tune spreading and entanglement” is already a
published result. It still uses two letters/two fixed coins, rather than
`s_2(t) mod 4` selecting four cyclic phase coins.

**T. Liu, Y. Hu, J. Zhao, M. Zhong, and P. Tong, “The entanglement of deterministic
aperiodic quantum walks,” Chinese Physics B 27, 120305 (2018).**<br>
DOI: <https://doi.org/10.1088/1674-1056/27/12/120305>

This studies coin--position entanglement for dynamic and static Thue--Morse and generalized
Fibonacci coin arrangements. It removes novelty from the entanglement aspect of the
experiment.

### Rigorous spatial Thue--Morse quantum walks

**J. Fillman, “Resolvent Methods for Quantum Walks with an Application to a Thue--Morse
Quantum Walk,” Interdisciplinary Information Sciences 23 (2017).**<br>
DOI: <https://doi.org/10.4036/iis.2017.a.04><br>
Preprint: <https://arxiv.org/abs/1704.07328>

Fillman studies a spatially inhomogeneous one-dimensional coined walk whose coins follow
the Thue--Morse subshift and develops rigorous dynamical/transport estimates using exact
renormalization of transfer matrices. Therefore neither “spatial Thue--Morse walk” nor
“rigorous renormalization may control its transport” is new.

### Earlier aperiodic and time-dependent coined walks

**P. Ribeiro, P. Milman, and R. Mosseri, “Aperiodic Quantum Random Walks,” Physical
Review Letters 93, 190503 (2004).**<br>
DOI: <https://doi.org/10.1103/PhysRevLett.93.190503><br>
Preprint: <https://arxiv.org/abs/quant-ph/0406071>

This introduces coins arranged in aperiodic sequences, obtains sub-ballistic spreading,
contrasts random diffusive behavior, and discusses experimental implementation.

**M. C. Bañuls et al., “Quantum walk with a time-dependent coin,” Physical Review A 73,
062304 (2006).**<br>
DOI: <https://doi.org/10.1103/PhysRevA.73.062304><br>
Preprint: <https://arxiv.org/abs/quant-ph/0510046>

This predates the present time-dependent-coin embedding and studies localization and
quasiperiodic behavior under such control.

### Thue--Morse quantum drives and recursive propagators

**C. R. de Oliveira, “Numerical Study of the Long-Time Behaviour of Quantum Systems
Driven by Thue-Morse Forces: Application to Two-Level Systems,” Europhysics Letters 31
(1995).**<br>
DOI: <https://doi.org/10.1209/0295-5075/31/2/001>

This already treats Thue--Morse-kicked quantum systems, efficient long-time algorithms,
and singular-continuous-like evolution in a two-level system.

**S. Nandy, A. Sen, and D. Sen, “Aperiodically Driven Integrable Systems and Their
Emergent Steady States,” Physical Review X 7, 031034 (2017).**<br>
DOI: <https://doi.org/10.1103/PhysRevX.7.031034><br>
Preprint: <https://arxiv.org/abs/1701.07596>

This exploits the recursive structure of a Thue--Morse unitary drive to study exponentially
late dynamics. It is direct prior art for recursive block propagation in quantum dynamics.

**S. Pilatowsky-Cameo et al., “Critically Slow Hilbert-Space Ergodicity in Quantum Morphic
Drives” (2025 preprint).**<br>
Preprint: <https://arxiv.org/abs/2502.06936>

For the binary Thue--Morse drive it uses

\[
A_{n+1}=B_nA_n,\qquad B_{n+1}=A_nB_n,
\]

and develops recursion for late-time channels. Its supplement gives the generic
substitution-word block formula and explicitly notes that extension to larger alphabets is
straightforward. The four-offset recursion in the present experiment is therefore a direct
specialization of known morphic-drive machinery, not a new renormalization principle.
Differentiating that product recursion in momentum to estimate walk moments may be a
useful implementation detail, but is mathematically routine and was not established by
this audit as independently publishable.

### Related modern transport results

**G. R. M. de Almeida et al., “Noise correlations behind superdiffusive quantum walks,”
Physical Review E 109, 064151 (2024).**<br>
DOI: <https://doi.org/10.1103/PhysRevE.109.064151>

This explicitly connects temporal/spatial correlations—including prior Thue--Morse
results—to transitions between localization, diffusion, and superdiffusion. Thus coherent
anomalous transport caused by a correlated deterministic schedule is not new in general.

**“Elucidating the Physical and Mathematical Properties of the Prouhet-Thue-Morse
Sequence in Quantum Computing,” Annalen der Physik (2026).**<br>
DOI: <https://doi.org/10.1002/andp.202500630><br>
Preprint: <https://arxiv.org/abs/2501.09610>

This discusses Prouhet--Thue--Morse states, gates, memory/error-correction ideas, and
quantum-chaos connections. It does not supply the exact coined walk found here, but it
precludes broad claims that connecting binary digit sums to quantum information is new.

## Claim-by-claim verdict

| Candidate claim | Verdict after audit |
|---|---|
| Thue--Morse scheduling of coined quantum walks | **Not novel** |
| Both temporal and spatial Thue--Morse coins | **Not novel** |
| Aperiodicity causing anomalous spreading/localization | **Not novel** |
| Coin--position entanglement under Thue--Morse schedules | **Not novel** |
| Recursive products at dyadic/substitution times | **Not novel** |
| Generalizing recursive morphic drives to four letters | **Not novel in principle** |
| Exact choice `C_t = D(i^popcount(t)) H` | **No exact match located** |
| Its crossover through `2^30` and proposed marginal law | **No exact match located; numerical observation only** |
| Momentum-differentiated four-block implementation | **Possibly unreported implementation, but routine** |
| Phase-walk experiment's connection to Erdős 193 non-collinearity | **No substantive connection; only a shared sequence** |

## Follow-up that genuinely uses non-collinearity

A subsequent direction maps each chord `A` to the Pauli generator
`G_A=A_x X+A_y Y+A_z Z`. The identity

\[
[G_A,G_B]=2i(A\times B)\cdot\sigma
\]

turns the theorem into an infinite finite-alphabet block-sum sequence for which every two
adjacent nonempty blocks have noncommuting aggregate generators; if independently
addressable, each pair generates `su(2)`. Searches for `noncommuting block sums`,
`persistently non-Abelian pulse sequence`, and related finite-alphabet quantum-control
phrases found no direct match.

This is a more faithful candidate novelty than the phase-modulated walk, but the Pauli
identity and controllability criterion themselves are elementary. Moreover, finite-prefix
diagnostics show that normalized commutator margins decay with block scale. It should be
presented as a new **mathematical corollary and research question**, not yet as a novel
quantum-control result. See [PAULI-NONCOMMUTATIVITY.md](PAULI-NONCOMMUTATIVITY.md).

## Bottom line

The phase-walk experiment should **not** be presented as the discovery of Thue--Morse quantum walks,
deterministic quantum localization, anomalous coherent diffusion, or recursive quantum
drives. All are established subjects.

The defensible statement is narrower:

> A preliminary search did not locate this exact four-phase, four-letter generalized
> Thue--Morse coin schedule or the particular long-scale variance crossover measured here.

That may be a new parameter point or model variant, but merely changing a binary drive to
four cyclic phases is normally incremental. Publication-level novelty would require at
least one result not inherited from generic morphic-drive theory—for example:

- a proved asymptotic transport law or new transport exponent;
- a new invariant/fixed set of the four-letter matrix recursion;
- a spectral theorem specific to the four-phase spatial walk;
- a demonstrated operational advantage over known binary Thue--Morse and random drives;
- or an experimentally robust effect unavailable in established models.

Until then, classify it as **interesting exploratory replication/extension with a narrowly
possibly novel exact instance**, not as a novel physics result.
