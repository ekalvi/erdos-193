# What looks promising in the Gaussian-phase coined quantum walk

> **Evidence status:** exploratory finite simulation and finite Monte Carlo integration.
> This study uses the Gaussian digit-sum phase sequence from the Erdős 193 construction,
> but it is not a consequence of the no-collinearity theorem. It establishes neither a
> new quantum phase of matter nor a quantum advantage. The subsequent
> [novelty audit](QUANTUM-WALK-NOVELTY-AUDIT.md) found extensive direct prior art for
> Thue--Morse quantum walks and recursive morphic drives; only the exact four-phase instance
> remains an unverified, narrow candidate novelty.
>
> **More direct route:** the separate [Pauli noncommutativity study](PAULI-NONCOMMUTATIVITY.md)
> uses the actual no-three-collinear property. It yields an all-scale finite-alphabet
> block-sum word in which every adjacent pair generates nonparallel Pauli axes.

## Quantum embedding tested

The simulation uses a standard one-dimensional two-state coined walk. At time `t`,

\[
 C_t=D(u_t)H,\qquad u_t=i^{s_2(t)},\qquad
 D(u)=\operatorname{diag}(1,u),
\]

followed by a conditional shift of the left and right coin components. Thus `u_t` is a
**relative coin phase**, not an unobservable global phase. The initial state is
\((|L\rangle+i|R\rangle)/\sqrt2\) at the origin.

Controls use a homogeneous coin, a period-four phase, binary Thue--Morse phases, and a
seeded random four-phase schedule. Further tests put the same sequence in space, rotate
the Hadamard axis instead of applying a one-sided phase, or combine space and time.
All evolutions remained normalized to within `8e-13` through 4,096 steps.

## Direct simulation: three distinct transport regimes

At 4,096 steps:

| model | fitted variance exponent | variance | participation ratio | return probability |
|---|---:|---:|---:|---:|
| homogeneous Hadamard | 2.0000 | 4,913,933 | 822.2 | 0.000155 |
| periodic time phase | 1.9999 | 532,748 | 342.3 | 0.00215 |
| Gaussian time phase | 1.3013 | 9,002 | 56.1 | 0.0489 |
| random time phase, one seed | 0.9968 | 4,946 | 86.2 | 0.00100 |
| Gaussian space--time phase | 0.9805 | 2,204 | 54.5 | 0.0497 |
| Gaussian spatial phase | -0.0433 | 26.7 | 2.68 | 0.586 |
| shifted Gaussian spatial phase | -0.0753 | 8.04 | 2.26 | 0.644 |
| random spatial phase, one seed | 0.0332 | 18.0 | 5.69 | 0.189 |
| periodic spatial phase | 2.0051 | 2,720,111 | 375.1 | negligible |

These exponents are finite-window effective slopes, not asymptotic critical exponents.
An independent 8,192-step run found:

- Gaussian time phase: variance `21,657.70`;
- Gaussian spatial phase: variance `13.87`, participation ratio `3.12`, and return
  probability `0.524`;
- homogeneous walk: ballistic, as expected.

The spatial result therefore survives one doubling in time, but random spatial phases
localize too. The result demonstrates deterministic confinement, not yet a mechanism
specific to the digit-sum sequence.

## Exact dyadic renormalization is the strongest lead for further analysis

The Gaussian word has a useful noncommutative block structure. This structure is a
four-letter specialization of known recursive morphic-drive machinery, not a novel
renormalization principle. Let
\(B_r^{(a)}(k)\) be the momentum-space propagator for a block of length \(2^r\), with all
phase labels offset by `a`. The second half of a digit-sum block is the first half with
one added to every label, so

\[
 \boxed{B_{r+1}^{(a)}(k)=B_r^{(a+1)}(k)B_r^{(a)}(k)}
 \qquad(a\bmod4).
\]

Differentiating the same recursion in momentum and using Parseval gives the position
moments without constructing the exponentially long real-space walk. This is an exact
renormalization identity; only the final momentum integral was sampled numerically.

Validation and scale extension:

- Through 4,096 steps, the RG variance agrees with direct simulation within the reported
  Monte Carlo uncertainty.
- At 8,192 steps, direct variance is `21,657.70` and RG gives `21,720.67`, a `0.29%`
  difference versus a conservative `0.51%` RG sampling error.
- With 131,072 momentum samples, the recursion was evaluated through
  \(2^{30}=1,073,741,824\) formal time steps.
- At that level, variance is approximately `1.158e10`, standard deviation `1.076e5`, and
  `variance/time = 10.79`. A homogeneous walk would have width proportional to the full
  billion-step time rather than roughly one hundred thousand sites.
- A fit over levels 23--30 gives an effective variance exponent `1.0858`; local slopes
  over the last levels are about `1.08--1.10`.
- A second independent 65,536-sample momentum integration gives exponent `1.0851` and
  agrees at level 30 within the combined sampling uncertainty.
- Sampled block unitarity error at level 30 is below `5.7e-7`; the level-30 variance has
  conservative Monte Carlo relative error about `1.7%` in the larger run.

The data rule out extrapolating the 4,096-step exponent `1.30`: the walk crosses toward a
much slower regime. They do **not** yet distinguish

\[
 \operatorname{Var}(X_t)\sim t^\beta\quad(\beta\text{ only slightly above }1)
\]

from marginal laws such as \(t(\log t)^\gamma\), or from persistent discrete-scale
oscillations. This ambiguity is mathematically interesting and is now accessible through
a four-matrix renormalization system.

## Promising directions, ranked

### 1. Hierarchically driven coherent diffusion — strongest

A deterministic four-phase drive changes a ballistic unitary walk into near-diffusive or
marginally superdiffusive transport without measurement or stochastic decoherence. The
exact block recursion makes this more than a numerical curiosity: spectral or dynamical
bounds may be provable by studying a finite nonlinear renormalization map on four
`2 x 2` unitary matrices and their derivatives.

Possible utility: an exactly reproducible benchmark for coherent transport, deterministic
noise emulation, or quantum-simulator calibration across many time scales.

### 2. Deterministic spatial localization — promising but less specific

The static Gaussian phase mask keeps most probability within only a few effective sites
through 8,192 steps and remains confined after shifting the sequence origin. This could
provide a four-phase, algorithmically generated alternative to sampled disorder in
photonic or cold-atom walk experiments. However, the random spatial control also
localizes, so the next question is whether the automatic sequence has distinctive
spectral type, critical states, robustness, or reproducibility benefits.

### 3. Deterministic space--time diffusion with high entanglement — engineering lead

The combined space--time schedule has effective exponent `0.98` at 4,096 steps and nearly
maximal coin--position entanglement (`0.994` bits). It may be useful when one wants a
fully specified coherent protocol that imitates diffusive spreading. This is an observed
behavior, not evidence of computational speedup.

### 4. Phase-axis control — weak lead

Conjugating the Hadamard coin by the Gaussian phase leaves transport close to ballistic
(`beta about 1.89`). The physical effect depends strongly on how the mathematical phase
is coupled into the coin. There is no embedding-independent “quantum consequence” of the
original sequence.

## Plausible experimental realization

The protocol needs only a Hadamard-like beam splitter, a conditional left/right shift,
and one of four relative phases `0`, `pi/2`, `pi`, `3pi/2` chosen from the binary digit sum
of a classical clock. Time-multiplexed photonic walks, synthetic-dimension cold-atom
walks, trapped-ion walks, or superconducting digital simulators can in principle supply
these operations. The spatial variant replaces the clocked modulator with a fixed
four-phase site mask.

This is an implementation observation, not an assessment that current hardware can
maintain coherence for thousands of ideal steps.

## Decisive next work

1. Extend the completed preliminary [novelty audit](QUANTUM-WALK-NOVELTY-AUDIT.md) with
   expert review and a systematic citation search focused on four-letter cyclic drives.
2. Analyze the four-block RG map analytically: invariant traces, fixed sets, Lyapunov
   growth of momentum derivatives, and rigorous upper/lower transport exponents.
3. Fit and discriminate `t^beta`, `t log(t)^gamma`, and log-periodic models using improved
   quadrature and higher precision beyond level 30.
4. For the spatial walk, compute finite-volume eigenstates, inverse participation ratios,
   transfer-matrix Lyapunov exponents, and sensitivity to phase and index perturbations.
5. Test multiple random seeds, initial coin states, and small phase/calibration errors.
6. Design a short-depth experimental discriminator: choose times and observables where
   Gaussian, periodic, and random controls differ by more than realistic error bars.

## Reproducible artifacts

- Direct simulator: `physics/coined_quantum_walk.py`
- Direct 4,096-step results: `results/coined-quantum-walk.json`
- Direct 8,192-step validation: `results/coined-quantum-walk-validation.json`
- Renormalization code: `physics/quantum_walk_rg.py`
- Primary level-30 RG result: `results/quantum-walk-rg.json`
- Independent RG replication: `results/quantum-walk-rg-replication.json`
- Generated reports: `physics/QUANTUM-WALK-RESULTS.md`,
  `physics/QUANTUM-WALK-VALIDATION.md`, `physics/QUANTUM-WALK-RG-RESULTS.md`, and
  `physics/QUANTUM-WALK-RG-REPLICATION.md`
- Durable logs and resumable checkpoints: `logs/coined-quantum-walk*` and
  `logs/quantum-walk-rg*`
