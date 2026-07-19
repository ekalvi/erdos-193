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
| X-parallel far-line module | proved and exhaustively instantiated over all 12.54M actions: 236,572 prefix edges, 53,216 promoted integer states, and every candidate lateral class internal; an exact occupancy smoke test finds real births but no literal-state stabilization |
| Exact unrelated-cursor import census | 393,279 L5--L8 transitions and 189.4M successor-core cells checked; exact jump + local phase + complete predecessor-core occupancy is noncongruent in every tested order, so a global address/tail state is required |
| Exact no-new-x-line alternate L5 | all 2,457 stitches completed with exact global legality, producing 8,260 points and zero new doubled yz fibres; this is one finite orbit, not an all-level availability theorem |
| No-new-x-line alternate L6 | construction has selected all 8,259 stitches and committed 28,737 points with zero new doubled yz fibres; independent first-survivor and ordered-chain audit still pending |
| Exact translation-normalized future CEGAR | the same tested zero mask/shell state leads to 3,998 versus zero next-slot kills; exact partner/Pluecker data repairs the witness but makes all 146 tested L8 states singleton |
| Exact full-domain non-x recurrence obstruction | the 4,774,932-edge x-avoiding graph has a 768-state SCC; an exact two-word cycle is carried-line-clean for every iterate and has infinitely many abstract future reveal languages, while realized birth/repeatability remains open |
| Exact policy-level non-x pilots | that cycle is absent from the selected L5--L8 address chains; one fixed intrinsic-clean word per step yields a 1,321-edge DAG of height 2, but exact chronological replay rejects that fixed policy at its second L5 stitch |
| Exact common-potential action falsifier | the old height-two region has only 601 words in total and eight for the repeated step-20 corridor; its exact correlated `8 x 8` two-stitch response matrix is empty at the second L5 stitch |
| Exact lattice-`T` action census | 8,367,038 zero-envelope and 10,252,458 ordered-envelope words give acyclic arbitrary-switching unions for contiguous direction-blind candidate chains; they do not control silent re-entry, cursor imports, line births, or global poison |
| Strict zero-`T`, no-new-yz L5 construction | exact independent terminal certificate: all 2,457 first-survivor choices and the complete 8,268-point natural-order chain are verified; this is one finite orbit, not an all-level availability theorem |
| Primary strict zero-`T`, no-new-yz L6 | all 8,267 first-survivor choices and 28,665 points constructed; independent firstness replay is complete, while the natural-order audit is paused at point 8,233 / 28,665 with no failure |
| Independently audited two-cone guarded L5 | all 2,457 stitches and 34,407,660 terminal pairs checked; 4,211 guard rejections reproduced, zero connector-born guarded-cone secants, and zero triples; two cones and one finite orbit only |
| Two-cone guarded L6 continuation | 6,348 / 8,267 stitches completed without obstruction from the ordinary audited L5 base; paused with a separate fail-closed auditor prepared |
| Exact short-return affine holonomy | 746,496 correlated `8 -> 16 -> 8` role pairs give 3,136 maps, 2,094 fixed points, and 47,942 additional abstract guard polynomials; reachability, secant birth, and availability remain unproved |
| Two-spectrum birth exclusion | refuted at the seed: anchor pair 30/33 already has `J=11/3`, so a direction-only ban on `{11/3,348/275}` cannot be imposed without exact inherited-line promotion |
| Exact short-connector closure | all 552 legal length-2 and 56,516 legal length-3 words have empty greatest fixed point after nine pruning rounds; every recurrent closed policy must use length 4 or 5, while mixed-length Perron growth exactly 3 remains open |
| Exact latent non-x re-entry | under the same fixed actions, an explicit family of integer lattice lines has zero full candidate mask for arbitrarily many `8 -> 16 -> 8` cycles and then reappears; no reachable placed-point birth is proved |
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
| `design/x_axis_universal_bellman.py` | All-action synchronized x-line barrier and exact 53,216-state integer core (`x-axis-universal-bellman-summary.json`) |
| `design/x_axis_occupancy_birth_probe.py` | Exact L7--L8 x-line occupancy, sequential-birth, four-way cursor-injection, and CEGAR smoke test (`x-axis-occupancy-birth-probe-summary.json`) |
| `design/x_axis_cursor_jump_injection.py` | Exact L5--L8 unrelated-cursor injection masks and state-congruence falsifier (`x-axis-cursor-jump-injection-summary.json`) |
| `design/no_new_x_line_constructor.py` | Exact globally legal alternate L5 constrained to create no new x-parallel lines (`no-new-x-line-constructor-summary.json`) |
| `design/far_secant_future_compatibility_probe.py` | Exact `42 -> 146 -> 488` physical-token future refinement and 3,998-vs-zero mask witness (`far-secant-future-compatibility-probe-summary.json`) |
| `design/far_secant_translation_cegar.py` | Exact centred Pluecker/ghost explanation of that witness (`far-secant-translation-cegar-summary.json`) |
| `design/nonx_degenerate_site_graph.py` | Full-domain non-x selector and direction-blind SCC census (`nonx-degenerate-site-graph-summary.json`) |
| `design/nonx_cycle_invariant_certificate.py` | All-iterate invariant certificate for the canonical non-x cycle (`nonx-cycle-invariant-certificate-summary.json`) |
| `design/nonx_cycle_realized_reachability.py` | Exact L5--L8 selected-address and secant reachability test for that cycle (`nonx-cycle-realized-reachability-summary.json`) |
| `design/nonx_fixed_word_policy_probe.py` | One-word-per-step acyclic direction-blind policy pilot (`nonx-fixed-word-policy-probe-summary.json`) |
| `design/fixed_policy_chronological_replay.py` | Exact second-stitch global-legality counterexample to the context-free fixed-word pilot (`fixed-policy-chronological-replay-summary.json`) |
| `design/potential_policy_two_stitch_matrix.py` | Exact empty `8 x 8` second-stitch response matrix for the old 601-word common-potential region (`potential-policy-two-stitch-matrix-summary.json`) |
| `design/nonx_scc_core_action_probe.py` | Exact full-cache lattice-`T` zero/ordered envelope action census (`nonx-lattice-envelope-action-probe-summary.json`) |
| `design/lattice_t_chronological_replay.py`, `design/lattice_t_chronological_audit.py` | Strict zero-`T`, globally fresh-yz L5 construction and completed independent terminal audit (`lattice-T-chronological-L5-summary.json`) |
| `design/lattice_t_projective_spectrum_census.py`, `design/lattice_t_projective_spectrum_diagnostic.py` | Exact seed refutation and complete 34,175,778-pair cone/ray/Pluecker diagnostic |
| `design/generic_ghost_transfer_census.py` | Exact whole-word role branching and finite lattice-`T` transfer census (`generic-ghost-transfer-census-summary.json`) |
| `design/lattice_t_l5_cone_guard_audit.py` | Independent exact guarded-L5 firstness and all-pairs certificate (`lattice-T-L5-cone-guard-audit-summary.json`) |
| `design/lattice_t_l6_continuation.py`, `design/lattice_t_l6_audit.py` | Resumable primary chronological L6 constructor and independently pinned terminal auditor |
| `design/lattice_t_l6_cone_birth_guard.py`, `design/lattice_t_l6_cone_guard_audit.py` | Separate no-new-two-cone L6 selector and fail-closed independent auditor |
| `design/lattice_t_short_return_holonomy.py` | Exact correlated short-return affine/guard census (`lattice-T-short-return-holonomy-zero-8-16-summary.json`) |
| `design/lattice_t_role_first_holonomy_reachability.py` | Fail-closed actual-lineage role/Pluecker reachability filter, pending terminal L6 pins |
| `design/lattice_t_birth_shell_transition_v2.py` | Reviewed five-corridor chronological raw-mask census, pending terminal L6 pins |
| `design/ordered_path_matched_transition_experiment.py` | Poison-blind matched-state and exact source/successor experiment, prepared but unrun |
| `design/PAUSE-STATE-2026-07-18.md` | Exact paused checkpoints, hashes, scope, and resume gates |
| `design/lattice_t_birth_shell_mask_experiment.py` | Exact finite external-geometric L5/induced-L6 owner-frame shell census (`lattice-T-L5-L6-birth-shell-mask-summary.json`); not chronological L6 transfer |
| `design/exact_length3_gfp.py` | Independent forward/reverse exact GFP certificate for length 3 and for lengths 2-or-3 (`exact-length3-gfp-summary.json`) |
| `design/nonx_latent_reentry_certificate.py` | Exact all-depth zero-mask/re-entry obstruction to the common-potential core (`nonx-latent-reentry-certificate-summary.json`) |
| `design/FAR-SECANT-BIRTH-OPERATOR.md` | Exact birth/transport equations, zero-ghost spacing obstruction, and the still-conjectural reachable-birth envelope |
| `design/LATENT-REENTRY-OBSTRUCTION.md` | Minimal exact carried-line state, infinite latent countdown, and reachable-birth boundary |
| `design/GHOST-LANGUAGE-AUTOMATON.md` | Exact correlated ghost language, infinite-carry obstruction, and availability-grade birth-gap alternatives |
| `design/X-PROJECTION-COSET-ADDRESS.md` | Exact `Z^2/BZ^2` address and finite-range x-birth CSP |
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
same-level jumps to unrelated corridor centres.

The all-action computation now instantiates this module sharply.  It scans all
12,537,146 words and 55,513,526 ordered slots, yielding 236,572 exact prefix
edges.  A rational postfixed barrier holds on every edge.  Its promoted core
has 53,216 `(step, lateral offset)` states, 327--631 per step, and all 6,288
candidate lateral classes lie inside it.  This proves the synchronized carried
x-line channel is finite for every domain action, but it still does not track
whether a cell contains zero, one, or two points or how chronological cursor
jumps inject cells.  The module also does not control
old endpoints on candidate-internal lines or near-deep/deep-deep pair creation.

The first exact occupancy promotion is a falsification test, not a closure
claim.  It reconstructs 564 cursor states under the recorded gate and pipeline
schedules and a counterfactual left-to-right order, replays every selected word
sequentially, and checks 438 source-to-child decompositions.  All identities
and collision assertions pass, and nine insertions genuinely promote an
x-fibre from one point to a poisoning two-point line.  But every one of the 126
tested L7 full occupancy states is distinct before adding ancestry or a path
window.  Erasing the singleton cells is unsound: the resulting active-line-only
projection has two exact state/action classes with different successors.
Left-to-right order reduces late-parent injection but does not produce a
repeated full state.  Thus literal enumeration of the finite core is not the
promised quotient; the remaining target is a monotone symbolic occupancy
summary together with an exact rule for what unrelated cursor motion imports.

The full cursor-import census shows that this rule cannot be a Markov update
of the obvious local state.  Across the gate, inherited-tile pipeline, and
left-to-right schedules it checks 393,279 consecutive cursor transitions and
189,394,231 successor-core cells.  Even after retaining the exact lateral
jump, both detailed local/tile phases, and the complete capped occupancy of
the predecessor's 53,216-state core, repeated states have different injected
point/line masks: 1,140 gate, 2,736 pipeline, and 1,072 left-to-right classes
are noncongruent.  Pipeline and left-to-right order sharply reduce injections
and jump size, but do not close the state.  This is finite-path evidence, not a
universal impossibility theorem; it does prove that the tested local quotient
needs a global birth/address-shell import component rather than a larger halo.

There is now also a constructive way to avoid the birth part of this x-channel
on one complete level.  Starting from the pinned L4 anchors, an alternate
fragile-first L5 selector requires every proposed interior point to use an
empty yz fibre and then subjects the word to the exact global 3D legality
test.  It completes all 2,457 gaps, yielding a triple-free 8,260-point walk,
while preserving exactly the 31 doubled yz fibres already present among the
anchors and creating none.  Two deterministic runs agree byte-for-byte.  The
least effective domain has 2,570 words, but the computation stops at the first
survivor: at the hardest stitch that survivor is word 2,455.  Consequently
this proves no useful survivor floor and says nothing about non-x secants.  A
resumable L6 continuation has now selected all 8,259 stitches and committed a
28,737-point, no-new-x construction; the independent first-survivor replay and
ordered-chain audit are still running, so it is not yet a terminal certificate.
The exact lateral quotient
`Z^2/BZ^2 ~= Z/9Z` also shows that projection collisions form a finite-range
CSP; a 25-fibre cage shows why locality alone still gives no availability.
The L5 result does show that x-line birth avoidance
is compatible with one coherent realized construction, rather than merely
with independent per-gap replacements.

The first exact L9 selected-horizon continuation also removes a tempting
shortcut.  Promoting the three tagged L7 endpoints to age two yields nonzero
anchor-only poison in 58 of 488 actual lineage states; partners born at L6,
L7, and L8 all contribute, and joins with other L9 anchors dominate the direct
channel.  Refining by exact direct masks, birth-shell masks, and partner
identities gives no repeated nonzero state: all 58 are singletons, while two
repeated enriched-parent classes remain noncongruent.  This refutes age-two
inertness but proves neither contraction nor availability.  Current L9
connector interiors and their joins have not yet been inserted.

The far-token CEGAR test now exposes one exact missing transition variable.
Two L8 states with the same tested zero poison and birth/owner-shell key lead,
after the same recorded word, to 3,998 versus zero killed words.  Exact centred
endpoint/partner Pluecker data explains the split but makes all 146 tested L8
states singleton.  The full non-x direction-blind graph is also cyclic: its
4,774,932 x-avoiding edges contain a 768-state SCC.  A quadratic-form invariant
proves the canonical two-word carried-line cycle is clean for every iterate
and yields infinitely many abstract future reveal languages.  This refutes a
full-menu strict lifetime rank, not the ordered policy: reachable births and
globally legal correlated repetition remain unproved.  On the actual selected
L5--L8 histories, neither cycle word nor macro edge occurs; the lone matching
reveal secant is followed by a different word.  A separate fixed-word pilot
chooses one intrinsic-clean word per step and leaves a 1,321-edge DAG of height
two.  Exact chronological replay then falsifies using those 124 words as a
context-free policy: the first word succeeds at L5 gap 0, but the identical
step-20 word at gap 2 puts its first interior on the secant through anchors
`(-6,6,8)` and `(-12,6,14)`.  The DAG therefore remains a candidate **common
action filter**, not a fixed controller.  The larger old common-potential
filter does not repair this: it retains 601 words over all step types but only
eight at this step-20 corridor, and the exact correlated `8 x 8` matrix has no
legal second-stitch response for any first choice.  This is a falsifier for
that particular action region, not for every state-dependent filter.

The replacement lattice-`T` census is exact and much larger.  It retains
8,367,038 zero-envelope words and 10,252,458 common-ordered-envelope words;
each whole-word arbitrary-switching union is acyclic on the exact finite
lattice envelope.  What this proves is limited to contiguous,
direction-blind candidate-to-candidate chains with same-word correlation.
It does not control silent lines, nondegenerate selector changes, births,
unrelated-cursor imports, or the union with complete global poisoning.
A strict zero-envelope plus globally fresh-yz chronological run nevertheless
completed all 2,457 L5 stitches and stored an 8,268-point construction.  A
separate pinned audit has now rescanned every ordinal through the stored
winner and verified the complete natural-order chain, so this is an exact
terminal finite certificate.  It is still only one orbit, not a uniform
survivor floor or an inductive safety policy.  A proposed direction-only ban
on the two known latent projective spectra fails already among its inherited
anchors: pair 30/33 has `J=11/3`.

The completed follow-up scans all `34,175,778` unordered pairs of that audited
path.  Exactly 758 secants lie on the two named invariant cones, and 76 have
one of the finitely possible named macro-orbit directions at this diameter;
61 of those 76 are connector-born.  Thus even the sharper named-ray exclusion
is not an invariant already satisfied by this L5 path.  All 758 affine lines
are distinct.  An exact Pluecker join finds no inherited-seed cone line in any
of the 352 actual L5 or 2,052 induced-L6 named phase roles.  This last zero is
finite and moment-sensitive: connector-born line roles, selected L6 actions,
other latent families, and all later levels remain untreated.  A policy that
grandfathers the finite base lines and forbids only future cone births is still
a candidate, not a proved availability theorem.

No uniformly short closed substitute is available.  Independent forward and
reverse enumeration finds 552 legal length-2 and 56,516 legal length-3 words,
but their combined child-step greatest fixed point is empty after nine rounds.
Thus every recurrent closed policy for these domains must use a length-4 or
length-5 connector.  A mixed-length substitution whose incidence matrix has
Perron--Frobenius growth exactly 3 is not ruled out and has not been found.

The old common potential is also not a far-tail theorem.  Its selected actions
contain a `step 8 -> step 16 -> step 8` affine cycle with explicit integer
lattice lines `L_n` whose complete candidate masks stay empty for `n` cycles
and then hit a selected interior.  Thus continuously effectful chains have a
height-two rank while silent carried lines still have infinitely many future
languages.  The certificate does **not** show that any `L_n` is a secant of a
reachable safe walk; the sharpened open lemma is a uniform exclusion or
contraction bound for those births, closed under cursor imports.

The primitive direction spacing of this ghost family is exactly proportional
to `9^n`.  That supplies a deterministic cutoff for any one bounded finite
level: sufficiently large `n` cannot be realized by two points in that finite
walk.  The walk diameter grows with the level, however, so no level-uniform
cutoff follows.  The exact endpoint/secant birth operator identifies every
old--new, new--new, carried, and cursor-import term that a proof must charge.
A weighted local-lemma argument or a mask-valued shell transfer built on that
operator remains a proposed route; no uniform birth moment, closed transfer,
or availability inequality has been proved.

The exact generic transfer census rules out one tempting version of that
route.  For both frozen lattice-`T` action channels, every whole connector has
two to five child roles, so the all-descendant first-moment kernel satisfies
`2 <= rho <= 5`; it cannot contract in any common positive weighted norm.
The finite `T` contact channel itself is much better--zero for the strict
envelope and nilpotent of exponent at most 218 for the ordered envelope--but
that statement excludes silent ghosts, line births, legality conditioning,
and coefficient-one cursor imports.  Prescribed-address decay is therefore
real but insufficient once actual branching and global poisoning are restored.

The first exact shell split is correspondingly modest but informative.  At
one deterministic late L5 stitch, far-only geometric witnesses kill 3,470 of
16,392 words; in its four actual ordered child corridors, evaluated against
the induced L6 anchors, the far-only counts are 958, 209, 661, and 813.  The
scan uses every endpoint and overlap-aware unions.  It is not yet a transfer
test: those L6 frames omit prior chronological L6 interiors, recursive birth
levels are collapsed, policy masks are not intersected, and only mask hashes
and counts are sealed.  The terminal result is therefore an exact finite
owner-frame census, while a chronological raw-mask v2 waits on the terminal
L6 audit.

A finite all-poisoned state would be trivially sound, so the real open
requirement is an availability-grade quotient fine enough to leave a connector
in a safety greatest fixed point.  The immediate technical target is now to
finish the independent audits of the constrained constructions and turn the
lattice-`T` action census into a successor-closed selector, while preserving
the exact birth and cursor-import channels.  A full current-L9 connector
closure and an exact cursor-import relation remain necessary.  A
componentwise-maximal occupancy
antichain is exact for uniform x-channel availability, but its correlated
cursor transfer has not yet been proved finite.

A contracting address shell is useful only in a qualified sense.  The exact
ghost-site pullback shrinks address tails by one third, and every positive
normalized incidence residual expands by three.  But zero residual—an exact
line hit—persists exactly, with full Boolean poison weight.  Therefore a sound
tail operator must promote or rule out every recurrent zero-incidence class
and make the remaining Boolean transfer nilpotent; a scalar decay fit to the
observed fatal-mass profile is evidence, not a proof.

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

The first inductive recurrent-family guard has now passed an independently
audited finite level.  Starting with the 2,458 L4 anchors, the guarded L5
selector rejected every connector that would create a new secant on either
`J=11/3` or `J=348/275`.  It completed all 2,457 stitches; the independent
auditor reproduced all 4,211 guard rejections and scanned all 34,407,660 final
pairs.  Exactly 246 guarded-cone pairs remain, all inherited anchor--anchor
pairs.  This validates the grandfathering mechanism for those two cones, but
not their exhaustiveness or uniform connector availability.  A separate
guarded L6 continuation from the ordinary primary L5 base is paused at
6,348 / 8,267 stitches without a jam.

The reason two cones cannot be advertised as the far theorem is now exact.
The correlated strict-zero `8 -> 16 -> 8` holonomy census contains 3,136
affine return maps, 2,094 fixed points, and 47,942 primitive full-candidate
guard polynomials outside the four previously named classes.  Those extra
polynomials are algebraic candidates, not proved chronological secants.  The
next filter therefore retains actual selected words, slots, child gaps,
endpoint births, Pluecker moments, and raw killed-word masks before declaring
any one reachable.  The exact paused state and hashes are recorded in
`design/PAUSE-STATE-2026-07-18.md`.

## Background

- [Erdős Problem #193](https://www.erdosproblems.com/193) — problem statement and history
- Gerver & Ramsey, *On certain sequences of lattice points* (1979)
- Everything here is exact integer arithmetic — no floating point in any decision path.

---
Made in Canada 🇨🇦 by [ekalvi](https://github.com/ekalvi) · part of the [q5m](https://www.q5m.ai) family
