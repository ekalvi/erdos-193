# erdos-193 — no-three-in-line walks in ℤ³

**Can an infinite walk on the integer grid, with steps from a fixed finite menu, avoid
ever placing three of its points on a common straight line?**
That is [Erdős Problem #193](https://www.erdosproblems.com/193) (Gerver–Ramsey, open
since 1979). This repository is a computational attack on it: a construction that builds
record walks, and a certificate programme working toward a proof that they can run forever.

🌐 **Visual introduction:** [erdos-193.q5m.io](https://erdos-193.q5m.io) — the proof
strategy in six diagrams, and an interactive demo with real coordinates.

## Headline results

| Result | Status |
|---|---|
| **311,737-step walk, no 3 collinear** (124-move menu) | verified (parallel) + SHA-256 c8cc3728…, `gate2-193-L8.txt` (level 8, proof-orbit constructor) |
| Affine laboratory `P_n=(W_n,W_{2n},W_{5n})` in ℤ⁹ | finite menu ≤378 proved; exact exhaustive prefix of 30,001 vertices has no collinear triple; infinite claim and projection to ℤ³ both open |
| Direct affine merge `R_n=W_n+9W_{2n}+81W_{5n}` in ℤ³ | finite menu ≤378 proved; exact exhaustive prefix of 30,001 vertices has no collinear triple; infinite claim open |
| 100,358-step walk (v1 record) | verified + SHA-256 c8477b01…, `gate-193-L7.txt` |
| 28,271-step walk (earlier record) | verified + SHA-256 certified, `amplified-193-28271.txt` |
| Exact maxima for small menus: **20** (±e₁,±e₂,±e₃), 14, 7; **3** in 2D | proven by exhaustive search |
| Universal availability: every one of 78,728 arithmetic states can steer in all 13 mod-3 directions | proven by exhaustion (1.22B transitions) |
| Exact global connector-poison audit | far secants remove 51–68% of apparent radius-40 survivors; a frozen-L7 robust early action has target-clean floor 45 and one exact successor retains 2,747 words |
| Five earlier proof strategies refuted with quantitative tombstones | documented in `REPORT.md` |

## Verify our record walk yourself (30 seconds)

No trust required — the verifier is standalone (~80 lines, stdlib only):

```bash
python3 verify_walk.py gate2-193-L8.txt
# VERIFIED: 311737 steps, 311738 vertices, no repeated vertex, no 3 collinear
# sha256(steps): c8cc3728a5dcb90a…
# (smaller/faster: python3 verify_walk.py amplified-193-28271.txt)
```

Works on any `amplified-*.txt` walk file in the repo.

## Reproduce things

Everything is deterministic (fixed seeds). [PyPy](https://pypy.org) is ~10–50× faster
than CPython here and strongly recommended for anything marked *(slow)*.

```bash
# sanity: the scientific controls must pass
python3 erdos193.py --controls

# rebuild the record walk from scratch (deterministic; hours under PyPy) (slow)
pypy3 amplify_rich.py 193 20 25000 3

# search random substitutions (the historical baseline the construction beat)
python3 erdos193.py --seed 1 --trials 100000 --output /tmp/demo.json

# exhaustive small-menu maxima (proves the "exactly 20" result)
pypy3 bnb193.py 2000000

# Stage-4 certificate computations (slow)
pypy3 step1_connectors4.py        # 7.1M legal connector words + closure
pypy3 np_hc_sidepass.py           # 1.22B transitions: availability + climb law
pypy3 np_hc_gpass.py              # successor-class tables (1.2 GB, local)
python3 step4_certify.py          # certified q̄ and LLL closure scan (needs numpy)

# exact ordered-path poison/state salvage gate (one low-priority core)
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    nice -n 15 python3 -B design/salvage_gate.py all

# exact 811,250-pair L7 backward-cone certificate (~2 minutes, one core)
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    nice -n 15 python3 -B design/l7_backward_cone.py

# sound overapproximation certificate for the 1.44B-assignment three-gap cone
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    nice -n 15 python3 -B design/l7_three_gap_gate.py

# robust frozen-L7 early action and its aligned concrete successor
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    nice -n 15 python3 -B design/l7_robust_d_selector.py
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    nice -n 15 python3 -B design/l7_robust_successor_probe.py

# independent affine-decimation route
clang++ -O3 -std=c++17 design/affine/check_affine_125.cpp -o /tmp/check_affine_125
nice -n 15 /tmp/check_affine_125 30000
clang++ -O3 -std=c++17 design/affine/check_weighted_merge.cpp -o /tmp/check_weighted_merge
nice -n 15 /tmp/check_weighted_merge 30000 9
nice -n 15 python3 -B design/affine/affine_recurrence.py
nice -n 15 python3 -B design/affine/c9_modular_gate.py --staged --mod243-depth 7
```

## What's in the repo

| File | What it is |
|---|---|
| `verify_walk.py` | **Start here** — standalone third-party verifier for any walk file |
| `amplified-*.txt` | Verified walk files (28,271 / 8,292 / …), plain step-index lists |
| `amplify_rich.py`, `amplify193.py` | The construction: enlarge by M, stitch anchor gaps, verify exactly |
| `search193.py`, `erdos193.py` | Exact-arithmetic core + the substitution-search baseline with controls |
| `bnb193.py`, `beam193.py`, `max2d_flat.py` | Exhaustive & randomized searches (exact maxima, 2D bounds) |
| `step1_connectors4.py`, `np_hc*.py`, `step4_certify*.py` | The certificate programme (Stage 4): word layer, state space, certified constants |
| `analyze_*.py`, `measure_dependency.py`, `provenance193.py` | Measurements: κ₃ spectra, divergence stratification, dependency structure |
| `design/` | Machine-generated design & hostile-review documents for the certificate |
| `design/ORDERED-PATH-SAFETY-GATE.md` | Corrected availability lemmas and exact scale-and-rotate salvage verdict |
| `design/l7_backward_cone.py` | Exhaustive sound two-connector replacement certificate at the L7 bottleneck |
| `design/l7_three_gap_gate.py` | Exact six-survivor lower bound for the three-connector L7 cone (`l7-three-gap-summary.json`) |
| `design/l7_four_gap_probe.py` | Exact first-12 slice of the four-connector L7 cone (`l7-four-gap-probe-summary.json`); bounded result, not the full cone |
| `design/l7_robust_d_selector.py` | Frozen-L7 early-action certificate: one precommitted D leaves a uniform target floor of 45 (`l7-robust-d-selector-summary.json`) |
| `design/l7_robust_successor_probe.py` | One action-aligned far-jump successor edge with 2,747 survivors (`l7-robust-successor-summary.json`) |
| `design/WEAK-ABELIAN-LIFT.md` | Exact word lift, literature check, and the dimension-three projection obstruction |
| `design/affine/` | Reproducible affine candidate, prefix checker, base-7 recurrence, and exact C=9 modular obstruction |
| `results/`, `collar_multiplicity4.json`, `wsw_sameword.pkl` | Data artifacts (large binaries are local-only, rebuildable) |
| `viz/` | The website ([erdos-193.q5m.io](https://erdos-193.q5m.io)) |
| `REPORT.md` | **The full research log** — every result, refutation and correction, in order |

## State of the proof programme (honest version)

The scale-and-rotate construction gives an exceptional verified finite walk, but
the old claimed reduction to bounded crowding is not valid: arbitrary bounded
crowding on a fixed radius interval is too weak, and connector legality includes
far secants.  An exact ordered-path poison game remains conceivable, but its
local states do not stabilize in L5–L8 and a scalar shell contraction is false.
The first exact backward-cone test exhausts 811,250 assignments to two earlier
path-neighbour connectors: none jams the target, but the worst legal assignment
leaves only 59 of 9,046 words.  Adding the third nearby connector creates 1.44
billion raw assignments; a sound all-third-effects overapproximation now proves
that entire frozen cone retains at least six words.  Adding the 47,467-word
geometrically intermediate gap 3785 gives 17,837 unary-legal early choices.  An
exact probe proves the 12 most pessimistic selected `(A,B)` slices non-jamming
for every compatible `C,D`, with minimum 22, but leaves most of the four-gap cone
unproved.  Its exact large-gap interface has 17,821 classes, so signature
quotienting gives only 16 pairwise merges.  The strategy-relevant quantifier is
now closed in this frozen cone: early word `(34,24,19,22,98)` leaves at least 45
target-clean words for every one of 865,674 base-compatible `(A,B)` pairs even
after unioning all `C` effects.  A concrete aligned continuation retains 2,747
words after the scheduler's Chebyshev-102 jump.  The early action was selected
using thousands of recorded future choices, however, so neither result is an
online selector or a cross-level invariant.  The next test changes to a bounded
inherited-tile guard schedule and asks for an action-labelled macrotransition.

The product candidate `P_n=(W_n,W_{2n},W_{5n})` in `Z^9` is only a
higher-dimensional test bed; no collinearity-faithful integer projection is
proved.  A direct weighted merge,
`R_n=W_n+9W_{2n}+81W_{5n}` in `Z^3`, is now an explicit dimension-correct
finite-menu candidate and has an exact clean prefix of 30,001 vertices.
Coefficients 3 through 8 all have exact counterexamples, so the `C=9` prefix is
evidence, not a stable projection theorem.  Its missing lemma is zero exclusion
for a projected base-7 defect system.  The coefficient-specific modular audit
compresses the first two filters to 12 and 360 correction states, but proves
their natural 26,244- and 787,320-state lifts are primitive; a fixed-modulus
zero-SCC proof is therefore closed.  See `design/affine/README.md` and
`design/WEAK-ABELIAN-LIFT.md`.

The scale-and-rotate orbit remains the much longer verified `Z^3` witness and
the route most directly supported by the 311,738-point construction.  Its open
gap is a global reachable-state availability invariant; literal local states
do not stabilize even under left-to-right replay.

## Background

- [Erdős Problem #193](https://www.erdosproblems.com/193) — problem statement and history
- Gerver & Ramsey, *On certain sequences of lattice points* (1979)
- Everything here is exact integer arithmetic — no floating point in any decision path.

---
Made in Canada 🇨🇦 by [ekalvi](https://github.com/ekalvi) · part of the [q5m](https://www.q5m.ai) family
