# Erdős Problem #193 — a conditional theorem

**Corrected status (2026-07-18): the 311,738-point construction is exact finite
evidence, but the claimed conditional theorem is not valid with Lemma R as
currently stated.**  The repository's own level-uniform cubic crowding bound
already implies the existence of some `C` on the fixed interval `1 <= r <= 10`,
so that formulation of Lemma R is too weak to imply connector availability.
Moreover, connector legality is global: far--far and near--far secants kill many
words missed by the radius-40 experiment.  The actual remaining hypothesis is a
uniform **reachable connector-survivor lemma**, or a sharp local bound plus a
separate uniform far-secant tail lemma.  See
`design/ORDERED-PATH-SAFETY-GATE.md` for the exact formulation and audit.

---

## Theorem (target)

There exists a finite set S ⊂ ℤ³ (here |S| = 124, all integer vectors with
coordinates in {−2,…,2}) and an infinite sequence of steps drawn from S whose
walk visits lattice points **no three of which are collinear**.

## The construction (one paragraph)

Fix the expansion matrix M = ((3,0,0),(0,0,−3),(0,3,−1)) — integer, determinant
27, all eigenvalue moduli exactly 3, inducing an irrational rotation
(arccos(−1/6)). Starting from a short hand-built triple-free walk W₀, each level
forms Wₖ₊₁ = (M·Wₖ) ⊔ Sₖ: blow the walk up by M (the images are the *anchors*),
then *stitch* each anchor-to-anchor gap with a short connector word from S,
chosen to keep the whole configuration triple-free. Because M is linear it
preserves non-collinearity, so the anchors inherit triple-freeness for free; only
the freshly stitched points can create a new collinear triple, and only at the
moment they are placed.  The finite levels are not nested point sets.  If every
level can be completed, however, they are arbitrarily long valid words over the
same finite step alphabet; König's lemma applied to the tree of valid prefixes
then supplies an infinite triple-free walk.

---

## The proof chain

Let cof(M) be the cofactor matrix and Ω(x,y,z) = (y−x)×(z−x) the exact
integer collinearity form (three points collinear ⟺ Ω = 0).

**L1 — Base [PROVEN].** A triple-free walk W₀ over S exists. Verified
instances up to 311,738 points; SHA-256 certified; an independent 80-line
verifier re-checks any of them. *(verify_walk.py, verify_parallel.py,
gate2-193-L8.txt.)*

**L2 — Inheritance [PROVEN].** Ω(Mx,My,Mz) = cof(M)·Ω(x,y,z), and cof(M) is
invertible over ℚ. Hence a triple that is non-collinear at the level where it is
created is non-collinear at **every** later level. Consequence: the only bad
events are exact collinear triples *at creation time*; completed levels are
frozen safe forever. *(Three lines of exact algebra; verified on millions of
real triples; hostile-panel confirmed.)*

**L3 — Availability [OPEN].** At every reachable stitch, a globally legal
connector word must exist.  The old ledgers inspected at most 200 words per
stitch, so the reported floors 317 / 180 / 271 are sampled extrapolations, not
exhaustive lower bounds.  Exact bottleneck replays show that far secants remove
51%--68% of the words surviving a radius-40 truncation.  Bounded local crowding
therefore does not imply L3 without a separate global tail theorem.

**L4′ — Reachable-state safety [THE OPEN HYPOTHESIS].**  Either prove directly
that `|D_s \ K(s,P)| >= 1` for every reachable stitch state and that a surviving
choice preserves the invariant, or prove a numerical sharp local-mask bound and
a uniform far-secant tail bound whose sum leaves at least one word.

**L5 — Induction and compactness [PROVEN, given L1–L4′].** L1 + L2 +
L3 + L4′ imply inductively that every finite level completes.  Their lengths
are unbounded and every level is a valid word over the same finite alphabet
`S`.  The rooted tree of all valid finite `S`-words is finitely branching and
has vertices at arbitrarily large depths, so König's infinity lemma gives an
infinite branch.  The conclusion is correct, but the former claim that the
levels themselves formed a nested limit was not.

**So: L1, L2, and the formal induction are proven.  L3/L4′ remain open and do
not follow from Lemma R as written.  The theorem holds conditional on the
reachable-state safety lemma, not on arbitrary bounded crowding alone.**

---

## The corrected remaining hypothesis

The previously advertised hypothesis was:

> **Old Lemma R (insufficient).** For the seed-193 construction orbit there is a
> level-independent constant C such that, for every level k, every centre q,
> and every radius r ∈ [1, 10],
>
>   c_k(q, r) := #{ walk points within Chebyshev distance r of q } ≤ C · r^d,
>
> with d = log λ / log 3 ≈ 1.10 (λ ≈ 3.36 the per-level point-growth).

Because the radius range is fixed and bounded away from zero, the claimed
level-uniform cubic crowding estimate below already implies this statement after
enlarging `C`.  It is therefore not availability-grade and cannot be the one
open lemma.

The required direct replacement is:

> **Lemma A (finitely certified safety selector).** Give a policy-independent
> concrete-history abstraction, a finitely represented invariant `G` containing
> the seed state, and a total selector `sigma` on `G`.  For every concrete legal
> history represented by `q in G`, `sigma(q)` is in the actual domain `D_s`, is
> outside the exact global killed-word set `K(s,P)`, and every sound abstract
> successor after inserting it is again in `G`.

Merely saying "reachable under a certified policy" is too close to circular
unless the policy, its domain, and the inductive closure check are supplied.
On exact histories the assertion that some legal continuation exists forever
is essentially the desired construction.  The proof-bearing object must
therefore be a finite invariant/selector certificate (or a separate analytic
lemma that implies the same closure condition).

A crowding route must instead state a sharp numerical bound (for example a
proved `c(q,4.44) <= 12` if that is the threshold used by the finite checker),
an exhaustive near-mask bound over all allowed local configurations, and a
uniform far-secant/tail bound.  If the near and tail bounds are `L_s,T_s`, the
checked inequality must be `L_s+T_s < |D_s|` or an exact stronger union bound.
No such package is currently proved.

The tail condition cannot be omitted even if the local numerical bound is made
very sharp.  For any finite step set and any fixed radius, a finite triple-free
set with radius-ball crowding at most two can be constructed that seals every
first step from an anchor using mutually remote secant pairs.  This broad-state
counterexample is not asserted reachable from the canonical seed, but it proves
that locality alone has no availability implication.

### What is PROVEN around Lemma R (the machinery)

All machine-verified / exact (design/lemma/):

- **Exact recursion identity.** Wₖ₊₁ = (M·Wₖ) ⊔ Sₖ is a genuine disjoint union
  (0 duplicate points, 0 interiors on anchors). So crowding splits exactly into a
  dilated-old part and a refill part. *(0 mismatches over 8,252 + 27,696 stitches.)*
- **Bounded distortion.** An invariant positive-definite form Q with MᵀQM = 9Q
  makes M a *quasi-similarity* of ratio 3 (distortion κ = 1.323 at all scales;
  σᵢ(Mʲ)/3ʲ ∈ [0.846, 1.182]). So the walk is quasi-self-similar, not wildly
  anisotropic.
- **Anisotropic contraction.** In M's singular-value metric the pull-back factor
  is φ = σ₁(M⁻¹)·σ₂(M⁻¹)^{d−1} = 0.351 < 1 — the renormalization contracts
  (the isotropic 4/9-based recursion diverged; this one does not).
- **Anchor separation.** min over nonzero integer v of |M·v|∞ = 3 — anchors are
  3-separated at every level, non-circular, exact.
- **Deep-tail collapse.** min|M³v|∞ = 24 > 2r for r ≤ 10 ⇒ any ball meets ≤ 1
  point born more than 3 levels back ⇒ the infinite recursion becomes a finite
  3-term bound, and only ≤ 4 adjacent birth-levels contribute to any ball.
- **Cross-scale transience (the "spool").** A coordinate u with u(Mp) = u(p)+1
  and bounded backslide (≥ −0.5, shrinking with level) proves the walk cannot
  self-approach *across scales* — the thread never tangles with far-away parts of
  itself.
- **Qualitative no-blow-up [full theorem].** The 3-separation packing bound gives
  a level-independent (cubic) crowding bound c_k(q,r) ≤ 1.1·g·(⌊2(r+4)/3⌋+1)³ for
  all k — proven, non-circular, finite-menu-certified over all 78,999,838 menu
  words. The walk **provably never densifies without limit.**
- **Box-dimension d ≈ 1.10**, measured level-stable across levels 5–8.

### Routes explored and closed

The investigations below remove several possible routes to a metric invariant.
They do not supply Lemma A, and the exact generation-2 menu-closure overlap does
not itself refute an ordered-path certificate because the realized walk chooses
only one connector per gap.

- **The OSC / Mauldin–Williams route is DEAD — the Open Set Condition provably
  FAILS on the connector menu-closure.** The intended proof of Lemma R was
  OSC ⟹ Ahlfors d-regularity ⟹ bounded crowding. But the menu-closure graph-directed
  system that Mauldin–Williams/Schief require has a genuine exact overlap already at
  generation 2: two *distinct* legal words reach the same anchor (−2, 2, 1) via
  *different* root connectors ((66,0,20,21) vs (5,20,21)), producing identical
  cylinders — the identity in the Bandt–Graf neighbour set, so the OSC fails
  (17,219,577 such type-correct pairs; explicit reconstructed witness). The mechanism:
  the closure's freedom is the union over *all* legal connectors per gap. The
  *realized* adaptive walk uses one connector per gap and is provably vertex-
  self-avoiding (Δ = Mᵍ(p_v − p_u); Δ = 0 ⟺ a repeated vertex, forbidden — a rigorous
  8,649-state closed carry-automaton certificate), so it dodges every such overlap.
  Net: MW on the closure certifies the wrong (blob) attractor, and MW on the realized
  sofic subsystem has separation hypothesis = Lemma R itself (circular).
  *(design/osc_decide/.)*

- **No better matrix — the crystallographic impossibility theorem.** One might hope
  to swap M for an expand-and-twist similarity M′ that *does* satisfy the separation
  screen. It cannot exist with the twist the construction needs: passing the
  absorbing-separation screen at every prime dividing the ratio r ⟺ SNF_ℤ(M′) = r·I
  ⟺ M′/r is a finite-order integral isometry ⟺ the twist angle is a rational multiple
  of π (Niven). So the *irrational* twist arccos(−1/6) the construction requires is
  fundamentally incompatible with the separation any OSC needs. Empirical seal: 0 of
  504 irrational-twist integer similarities (r = 2…12, incl. axis-free 3D-mixing
  quaternion rotations) pass at all primes; every rational-twist control passes.
  *(design/mprime/.)*

- **Information theory (cross-entropy / subword complexity) refuted.** The hope: two
  arcs stacking in one ball must have divergent step distributions, D(P_A‖P_B) ≥
  floor > 0, capping the stack count. The cross-entropy floor is provably **zero**:
  same-birth-level arcs are M-images of one identical base alphabet ⟹ identical step
  marginals ⟹ D = 0, and exactly-parallel laterally-offset lattice arcs are forced
  (min coexisting-pair angle 0.00°, the floor *decreasing* to 0 as stacking grows).
  They stay triple-free by integer lateral offset (cross ≥ 1, never 0). Subword
  complexity is near-maximal (p(8)/L = 0.989) in the load-bearing window; and a
  space-filling curve is linearly recurrent yet a blob — so low symbolic complexity
  provably does **not** imply low geometric crowding. Same wall, restated in
  information-theoretic language; the cross-entropy sub-hypothesis is refuted at 0.
  *(design/entropy/.)*

### Finite geometric evidence

- Crowding is level-stable to three decimals: mean c(·,4) = 4.13 / 4.11 / 4.10 /
  4.10 at levels 5–8; the growing observed maximum is an extreme-value artifact of
  sampling more points, not a distribution shift (full-distribution test).
- The renormalization density N₈₁ converges to a fixed point: 118.4 → 111.9 →
  109.8 → 109.4, geometrically, with the level-8 value predicted *before* the run.
- The ledgers report extrapolated availability floors 317 / 180 / 271 at levels
  5–7 after testing at most 200 words per stitch.  These are useful sampling
  signals, not certified floors.
- Under the causal inherited-tile pipeline, a fixed-before-run 18-probe audit
  learns an all-poisoned-atom owner radius 625 on L5–L6 and sees no L7/L8
  exceedance.  The same audit refutes a fixed shell-4 cutoff at two L7 probes:
  new shell-5 atoms uniquely kill 56 and 9 words.  This is finite evidence, not
  a uniform horizon or transfer theorem.
- At the causal L7 bottleneck, pinned D/A/B choices leave 111 target words and
  every one retains at least 1,153 / 1,505 short words at the next-tile guard.
  This is one incoming state, not safety-game closure.
- Purer-thread trend: bigger-twist matrices drive d monotonically toward 1.0
  (1.071 → 1.035 for m = 3…6), confirming the thread picture.

---

## Reproducibility

The exact construction and collinearity checks use integer arithmetic.  Empirical
dimension, regression, and sampled-availability statements must not be promoted
to exhaustive certificates.

| Claim | Artifact |
|---|---|
| Record walk, 311,738 pts, no 3 collinear | `gate2-193-L8.txt`, `verify_parallel.py` (SHA-256 c8cc3728…) |
| Inheritance algebra | `provenance193.py`, `PROOF-SKELETON.md` L2 |
| Exact recursion, contraction, refill | `design/lemma/recursion_decomp.py`, `taskC_geometry.py` |
| Anchor 3-separation, deep-tail, finite-menu check | `design/lemma/finite_menu_check.py` (79M words) |
| Qualitative no-blow-up (cubic, all k) | `design/lemma/refill/`, `design/lemma/bound1-deepshell-VERDICT.json` |
| Spool transience | `design/lemma/exclusion/` |
| Sampled availability/crowding correlation | gate ledgers `gate2-ledger-L{5,6,7}.json` |
| Exact global poison/shell audit | `design/salvage_gate.py`, `design/ORDERED-PATH-SAFETY-GATE.md` |
| Exact L7 two-gap backward cone | `design/l7_backward_cone.py`, `design/l7-backward-cone-summary.json` |
| Exact L7 three-gap lower bound | `design/l7_three_gap_gate.py`, `design/l7-three-gap-summary.json` |
| Exact bounded L7 four-gap probe | `design/l7_four_gap_probe.py`, `design/l7-four-gap-probe-summary.json` |
| Frozen-L7 robust early action | `design/l7_robust_d_selector.py`, `design/l7-robust-d-selector-summary.json` |
| Concrete robust-action successor edge | `design/l7_robust_successor_probe.py`, `design/l7-robust-successor-summary.json` |
| Exact inherited-tile witness/horizon audit | `design/inherited_tile_lifetime.py`, `design/inherited-tile-lifetime-summary.json` |
| Four-sentinel literal transition test | `design/pipeline_transition_stabilization.py`, `design/pipeline-transition-stabilization-summary.json` |
| Causal L7 target-to-guard macrotransition | `design/l7_pipeline_macrotransition.py`, `design/l7-pipeline-macrotransition-summary.json` |
| Dimension / regularity measurements | `design/lemma/dim/`, `design/tight/` |

## Honest summary

The repository contains a rigorously checked 311,738-point triple-free walk and
useful exact inheritance/geometry machinery.  It does **not** yet contain a valid
conditional reduction to the old Lemma R, because that lemma is too weak and the
claimed crowding-to-availability implication omits global secants.  The honest
conditional statement is: the scale-and-rotate induction succeeds if Lemma A,
the finitely certified connector-safety selector, is proved.  Once the finite
levels have unbounded length, König's lemma—not a nested geometric limit—extracts
the infinite walk.

The full-menu OSC overlap does not refute that ordered-path possibility, since
the realized path chooses one connector per gap.  Conversely, the current
accelerating/chiral experiments do not prove separation for the true complete
difference closure: their observed small-box signal is caused by prescaling, and
the untreated closure remains a separate obligation.

Exact finite poison tests leave legal words on the realized bottlenecks but show
that far secants remove most apparent local survivors, that small ordered states
do not stabilize, and that arbitrary triple-free point sets can jam the fixed
domains.  The first sound backward-cone computation exhausts all 811,250
unary-legal assignments to two earlier L7 path-neighbour connectors: none jams
the target, but the unique worst assignment leaves only 59 words.  A second
sound computation covers all 1.44 billion raw assignments in the corresponding
three-gap cone and proves a uniform floor of six by overapproximating every
possible third-choice poison effect.  These are useful bounded safety
certificates, not a fixed point across levels.  An unconditional theorem
therefore still needs a genuinely global reachable-state invariant or a
different construction.  A corrected four-gap probe now proves the 12 selected
most-pessimistic `(A,B)` slices safe for every compatible later choice, with
minimum 22, but does not cover the other slices.  The exact early-gap interface
has 17,821 classes for 17,837 legal words, so the most obvious quotient barely
compresses.  Choosing rather than universally quantifying the early gap is much
stronger: one pinned word gives a target-clean floor of 45 over all 865,674
base-compatible `(A,B)` pairs under the all-`C` overapproximation, and one
aligned successor retains 2,747 words after a distance-102 scheduler jump.
These remain frozen-future finite certificates: the early rank-433 word was
selected using the recorded completion through rank 16,789, so no causal
all-history or cross-level selector is proved.  Reordering the same recorded
walk into the causal inherited-tile pipeline removes that future oracle at the
tested L7 state and yields an exact 1,153-word target-to-guard floor.  Across
18 L5–L8 probes, the all-atom owner horizon learned on L5–L6 survives validation
and holdout, but a new shell-5 effect and completely novel literal L7/L8
transition codes show that neither fixed shell truncation nor exact-state reuse
has closed.  The plausible remaining route needs an exact current/age-one state
plus a typed deep endpoint/secant frontier with a proved common contraction or
strict arithmetic rank.  Numerical confidence
percentages are opinions and are not part of the mathematical result.
