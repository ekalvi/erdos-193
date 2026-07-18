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
| Exact global connector-poison audit | far secants remove 51–68% of apparent radius-40 survivors; the causal tile pipeline has a one-state target-to-guard floor of 1,153, while an L7 shell-5 validation failure keeps the theorem open |
| Exact frozen-L8 ordered response | all 1,997 legal first actions extend through five stitches; 10 fixed-`B,C` leaves persist through common-leaf `D,E` responses, with per-history floors 1,601 and 6,995; finite-prefix result only |
| Exact shell-5 lineage transport | all 92,731 recorded L8 prefixes and 124 domains checked for three tagged endpoints: 64 cross-mode effects, zero direct-image recurrence, and no unconditional tail rank |
| Exact realized far-frontier trace | direct endpoint/line state is noncongruent in two classes; 94 birth/shell terms have no repeated nonzero child or enriched parent state, so contraction remains open |
| Exact x-parallel resonance audit | all 131,097 L5--L8 corridors per schedule and 12.54M domain words checked; 35 latent lines reactivate and 18 physical period-1--3 effect-key returns refute the tested strict rank |
| X-parallel far-line module | proved: every effectful synchronized lineage lies in a phase-free core of at most 1,681 integer offsets; observed 13,203 core occurrences compress to 1,312 states, but occupancy, births, and unrelated cursor jumps are not closed |
| Exact selected-horizon L9 age-two audit | 58 / 488 tagged states remain effectful and anchor joins dominate their poison, refuting age-two inertness; all nonzero refined states are singletons and current L9 connectors remain untreated |
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

# inherited-tile causal pipeline: lifetime, literal transition, macrotransition
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    nice -n 15 python3 -B design/inherited_tile_lifetime.py run \
    --output /tmp/inherited-tile-lifetime.json
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    nice -n 15 python3 -B design/pipeline_transition_stabilization.py \
    --output /tmp/pipeline-transition-stabilization.json
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    nice -n 15 python3 -B design/l7_pipeline_macrotransition.py

# shell-5 point identities and complete tagged-endpoint closure on recorded L8
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    nice -n 15 python3 -B design/deep_incidence_lineage.py run \
    --output /tmp/deep-incidence-lineage.json

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
| `design/inherited_tile_lifetime.py` | Exact 18-probe causal-pipeline witness audit: global atom/word masks, owner horizons, and correlated birth/shell provenance (`inherited-tile-lifetime-summary.json`) |
| `design/pipeline_transition_stabilization.py` | Four exact source/action/successor sentinels; literal L5–L6 transition codes do not recur at L7/L8 (`pipeline-transition-stabilization-summary.json`) |
| `design/l7_pipeline_macrotransition.py` | Causal one-state macrotransition: all 111 legal target words retain at least 1,153 short next-guard words (`l7-pipeline-macrotransition-summary.json`) |
| `design/deep_incidence_lineage.py` | Exact identities for the two L7 shell-5 atoms and prefix-aware all-124-domain L8 closure for their three endpoint images (`deep-incidence-lineage-summary.json`) |
| `design/l8_immediate_action_cegar.py` | Exact first-response sweep for 1,997 legal A actions on the frozen L8 prefix (`l8-immediate-action-cegar-summary.json`) |
| `design/l8_third_ply_closure.py` | Exact A-B-to-C sweep and ten-leaf fixed-B/fixed-C response refinement (`l8-third-ply-closure-summary.json`) |
| `design/l8_fourth_ply_transition.py` | Exact transition of those ten leaves through the next real D stitch (`l8-fourth-ply-transition-summary.json`) |
| `design/l8_fifth_ply_transition.py` | Exact transition of the same leaves through the next real E stitch (`l8-fifth-ply-transition-summary.json`) |
| `design/far_secant_future_trace.py` | Exact 42-parent/146-child realized-path trace and direct-frontier falsifier (`far-secant-future-trace-summary.json`) |
| `design/far_secant_birth_shell_trace.py` | Exact symbolic birth/shell mask split and one-generation quotient tests (`far-secant-birth-shell-trace-summary.json`) |
| `design/x_axis_far_secant_resonance.py` | Exact L5--L8 x-parallel latent-line and period-1--3 recurrence audit (`x-axis-far-secant-resonance-summary.json`) |
| `design/x_axis_bellman_barrier.py` | Exact Bellman barrier on the finite observed x-line phase graph (`x-axis-bellman-barrier-summary.json`) |
| `design/x_axis_barrier_node_join.py` | Exact realized-node join proving exterior escape and locating all observed returns in the core (`x-axis-barrier-node-join-summary.json`) |
| `design/x_axis_core_promotion_probe.py` | Exact observed core collapse and action-labelled congruence probe (`x-axis-core-promotion-probe-summary.json`) |
| `design/l9_anchor_age2_precursor.py` | Exact selected-horizon L9 anchor and age-two poison audit (`l9-anchor-age2-precursor-summary.json`) |
| `design/l9_anchor_age2_positive_mask_verifier.py` | Independent full-domain replay of the largest positive L9 age-two mask |
| `design/l9_age2_transition_stabilization.py` | Observed transition-refinement audit for the L9 tagged frontier (`l9-age2-transition-stabilization-summary.json`) |
| `design/FAR-SECANT-RANK-LEMMA.md` | Referee-grade far-frontier algebra, quotient/envelope obligations, and greatest-fixed-point target |
| `design/WEAK-ABELIAN-LIFT.md` | Exact word lift, literature check, and the dimension-three projection obstruction |
| `design/affine/` | Reproducible affine candidate, prefix checker, base-7 recurrence, and exact C=9 modular obstruction |
| `results/`, `collar_multiplicity4.json`, `wsw_sameword.pkl` | Data artifacts (large binaries are local-only, rebuildable) |
| `viz/` | The website ([erdos-193.q5m.io](https://erdos-193.q5m.io)) |
| `REPORT.md` | **The full research log** — every result, refutation and correction, in order |

## State of the proof programme (honest version)

The scale-and-rotate construction gives an exceptional verified finite walk, but
the old claimed reduction to bounded crowding is not valid: arbitrary bounded
crowding on a fixed radius interval is too weak, and connector legality includes
far secants.  An exact ordered-path poison game remains conceivable, but literal
local states do not stabilize and a scalar shell contraction is unsound.
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
online selector or a cross-level invariant.

The inherited-tile guard schedule removes that future oracle at the known L7
bottleneck.  Its causal state has 36,589 points before the early action; the
pinned D/A/B choices remain legal, leave 111 target words, and every one of
those targets leaves at least 1,153 / 1,505 short words at the next guard.  This
is a genuine two-ply certificate at one incoming state, not closure over all
incoming histories.  Separately, an 18-probe L5–L8 audit learns an all-poisoned-
atom owner radius of 625 on L5–L6 and sees no validation or holdout exceedance.
But its shell-4 cutoff fails at two L7 probes: new shell-5 atoms are uniquely
responsible for 56 and 9 killed words, including a same-level witness.  Every
tested exact mask is distinct, and neither L7 nor L8 matches the frozen L5–L6
literal source/action/successor codes.  The surviving proof target is therefore
a finite noncontracting current/age-one state plus a typed deep endpoint/secant
frontier with a proved common rank—not a fixed shell cutoff.

Following the two shell-5 atoms confirms why the endpoint frontier is
essential.  Both witnesses are born at L7, so they are age zero rather than a
deep tail.  At L8 their direct affine-image atoms never recur, yet the three
endpoint images generate different collision/secant/line atom checks at 64 of
92,731 recorded prefixes across the full set of 124 domains.  The worst one-
source mask kills 131,472 / 501,044 words, while the recorded chosen word stays
clean everywhere.  This is a complete finite result for three endpoints on one
history, not a uniform availability floor.  It refutes mode-preserving poison
transport and scalar shell decay; it does not test age-at-least-two contraction.

The ordered-path policy has also been pushed five exact stitches into a
selected frozen L8 state.  Of 5,257 A-domain words, 1,997 are legal.  Every one
has a B response; exact C-poison predicates refine the response policy to ten
fixed-B/fixed-C leaves covering all 1,997 actions.  At the immediately next
scheduler stitch, all ten leaves retain a common D word, `[0,3,4]`; every
individual history has at least 1,601 D survivors and every leaf has at least
283 common D responses.  At the following E stitch, every history again
survives with a per-history floor of 6,995 and every existing leaf already has
46--1,923 common E responses.  Thus two consecutive transitions preserve the
ten-state partition without refinement.  This is still one frozen prefix, not
a proof that those predicates are observable or closed at other prefixes or
levels.

The exact one-generation far trace explains why closure remains difficult.
Across 42 actual L7 parents and 146 actual L8 children, 61 full poison masks
strictly exceed the direct endpoint/carried-line masks because of joins with
other points; 24 of the 57 distinct partners are born during L8 itself.  A
birth/shell replay retains 94 exact descriptor commitments, but its only
repeated child classes have zero poison and all 42 enriched parent states are
singletons.  This is a concrete falsifier for an underspecified frontier, not
evidence of a finite nonzero quotient or a contracting tail.

The exact x-parallel audit then closes the most obvious rational resonance
class through L8.  Its selected-lineage graph contains 8,109 effect-to-zero
and 35 zero-to-effect transitions, so a presently empty poison mask cannot be
forgotten.  It also contains 12, 2, and 22 exact effect-key returns at periods
one, two, and three.  After identifying the gate/pipeline twins these are 18
physical returns; three period-three returns still repeat the recorded action.
This refutes a strict rank based only on step, lateral offset, exact x-poison
mask, and selected word.  It does not prove an infinite policy cycle or say
anything universal about non-x secants, alternate histories, or L9 and later.

The far-state specification now has an exact centred endpoint/primitive-line
frontier.  A cofactor-metric line-offset ratio expands by exactly three under a
common scale.  A finite phase-dependent Bellman barrier therefore gives a
strict escape rank outside its noncontracting core along synchronized
bounded-digit lineages.  The exact observed x-line join confirms this escape
on every one of 13,826 exterior transitions, with no exterior-to-core re-entry.
But 11,107 of 11,154 actual effect nodes and every observed short return lie in
the core.  The exterior theorem therefore works while leaving the main
resonance unresolved.  On this finite graph, 13,203 strict-or-latent core
occurrences collapse to 1,312 exact `(step, lateral offset)` states with
congruent combined poison and carried-line successors.  That is the first
credible promotion state, but it covers only recorded actions and inherited
endpoint pairs; it has no singleton occupancy or new-line births.  It does not
by itself prove a universal automaton.

For the fixed x direction, the algebra goes further than the observed graph.
Every length-at-most-five prefix has lateral norm at most a fixed `C`, and the
phase-free barrier `D=3C/2` is forward invariant.  Every candidate site lies
inside it, while positive-definiteness bounds its integer core by at most
1,681 offsets per corridor phase.  Thus x-line *geometry* is now uniformly
finite under synchronized parent-to-child controls.  What remains is the
ordered occupancy `0/1/2` and line-birth update, plus the interface for
same-level jumps to unrelated corridor centres.  The theorem does not control
old endpoints on candidate-internal lines or near-deep/deep-deep pair creation.

The first exact L9 selected-horizon continuation also removes a tempting
shortcut.  Promoting the three tagged L7 endpoints to age two yields nonzero
anchor-only poison in 58 of 488 actual lineage states; partners born at L6,
L7, and L8 all contribute, and joins with other L9 anchors dominate the direct
channel.  Refining by exact direct masks, birth-shell masks, and partner
identities gives no repeated nonzero state: all 58 are singletons, while two
repeated enriched-parent classes remain noncongruent.  This refutes age-two
inertness but proves neither contraction nor availability.  Current L9
connector interiors and their joins have not yet been inserted.

A finite all-poisoned state would be trivially sound, so the real open
requirement is an availability-grade quotient fine enough to leave a connector
in a safety greatest fixed point.  The immediate technical target is now a
full-domain x-core promotion with occupancy/birth closure, together with a
full current-L9 connector closure.

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
