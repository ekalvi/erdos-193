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
- **Finite synchronized x-line core [full theorem].**  For an x-parallel line,
  the exact integer lateral offset obeys `z' = B(z-c)` and its invariant norm
  expands by three.  Every length-at-most-five connector prefix has norm at
  most `C`, so `D=3C/2` is a phase-free forward-invariant barrier.  Every
  candidate site lies inside it and the positive-definite norm leaves at most
  1,681 integer offsets per corridor phase.  This proves finiteness of x-line
  geometry only; singleton occupancy, new-line births, collision data, and
  unrelated same-level cursor jumps remain open.
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
- Exact lineage enrichment shows that both shell-5 counterexamples are born at
  L7, hence are age-zero source terms.  Their three endpoint images were then
  checked against every one of the 92,731 recorded L8 pipeline prefixes and
  all 124 effective connector domains.  The direct affine-image atoms never
  recur, but the endpoints generate different poison atoms at 64 corridors,
  including mixed secants reaching shell 6 and owner radius 882.  This is a
  finite source-transport certificate, not an age-at-least-two tail theorem.
- At the causal L7 bottleneck, pinned D/A/B choices leave 111 target words and
  every one retains at least 1,153 / 1,505 short words at the next-tile guard.
  This is one incoming state, not safety-game closure.
- At one frozen 250,697-point L8 prefix, all 1,997 exact legal first actions
  have replies.  Exact C-poison predicates give ten fixed-B/fixed-C response
  leaves, and the same fourth word `[0,3,4]` works across all ten leaves at the
  actual next stitch.  The per-history fourth-response floor is 1,601.  At the
  immediately following fifth stitch, every history again survives; every
  existing leaf has a common response, with a per-history floor of 6,995 and
  no new predicate split.  This is an exact five-stitch finite policy
  transition, not cross-prefix or cross-level closure.
- The exact one-generation far trace retains 42 realized L7 parents, 146 L8
  children, and every actual connector choice.  In 61 children the full mask
  strictly exceeds the direct endpoint/carried-line mask.  A birth/shell replay
  keeps 94 exact descriptor commitments, but only zero-poison child classes
  repeat and all 42 enriched parent transitions are singletons.  This is a
  finite falsifier for an underspecified frontier, not a finite quotient or
  contraction theorem.
- The exact L5--L8 x-parallel audit scans all 131,097 corridors per schedule
  against 12,537,146 effective domain words.  Its selected-lineage closure has
  35 zero-to-effect reactivations and 18 physical effect-key returns of periods
  one through three; three period-three returns also repeat the recorded
  action.  This refutes current-mask forgetting and a strict rank on the tested
  effect/action key.  It is not a universal quotient, policy cycle, or tail
  theorem.
- The exact observed x-axis Bellman join puts only 47 of 11,154 strict-effect
  nodes outside the noncontracting core.  Every one of 13,826 recorded
  exterior-source transitions stays exterior with a certified factor-three
  escape margin, but all 36 effect-key and all six effect/action return sources
  lie in the core.  This validates the exterior theorem on the finite orbit
  while leaving universal core promotion open.
- Collapsing all 13,203 observed strict-or-latent core occurrences by exact
  `(step, lateral offset)` gives 1,312 geometric states.  Their combined poison
  and actual-action/slot carried successors are congruent on this trace.  The
  artifact has no singleton occupancy or new-line births and covers only 2,882
  observed step/action pairs, so this is a candidate promotion coordinate, not
  a universal automaton.
- The full-domain synchronized x-line scan covers all 12,537,146 actions and
  55,513,526 ordered slots.  Its 236,572 exact prefix edges all satisfy a
  rational postfixed barrier.  The resulting integer core has 53,216 states,
  and all 6,288 candidate lateral classes lie inside it.  This closes carried
  x-line geometry for every domain action, but not occupancy, line births,
  whole-word coexistence, or chronological jumps to unrelated anchors.
- The first exact occupancy/birth smoke test reconstructs 564 pinned cursor
  states and 438 L7-to-L8 transport decompositions.  All identities pass and
  nine insertion-driven x-line births occur.  However, all 126 tested L7
  full-occupancy schedule states are distinct, while deleting singleton cells
  gives two noncongruent state/action classes.  This refutes both literal-state
  stabilization on this horizon and the active-line-only shortcut; it does not
  refute a symbolic monotone quotient.
- For the x channel, componentwise-maximal occupancy antichains preserve
  uniform connector availability exactly, and the four-way occupancy update is
  an exact monotone Boolean circuit.  Conversely, a finite moving window cannot
  update without an import oracle around any same-level abstract cycle with
  nonzero net drift.  These are theorems; existence of the required correlated
  import relation is still open.
- The full realized L5--L8 cursor census tests 393,279 transitions.  Exact
  jump, both local/tile phases, and complete predecessor-core capped occupancy
  still give 1,140 gate, 2,736 pipeline, and 1,072 left-to-right noncongruent
  repeated classes.  This refutes those local Markov states, not all possible
  finite address/shell quotients.
- Non-x primitive direction height is not a rank: the exact `t=9`
  normalization branch admits arbitrarily long factor-one-third runs.  For a
  lineage that poisons a candidate at every synchronized stitch, nondegenerate
  site changes do fall into a finite selector set; only the finite
  direction-blind site graph remains.  The exhaustive graph is not acyclic:
  its x-avoiding 4,774,932-edge refinement has a 768-state SCC.  An exact
  quadratic-form invariant proves its canonical two-word carried-line cycle is
  clean for every iterate and has infinitely many abstract future reveal
  languages.  Reachable secant births and globally legal correlated repetition
  are not proved, so this rejects an arbitrary-switching rank rather than the
  ordered-path strategy.  Empty-mask intervals, births, and unrelated cursors
  remain outside the reduction.
- The canonical cycle is absent from every selected L5--L8 word/address chain;
  its only recorded reveal-direction secant uses a different actual word.  A
  separate one-fixed-word-per-step pilot reduces the direction-blind union to
  a 1,321-edge DAG of height two.  These are exact finite policy signals, not
  a proof that the cycle stays unreachable.  In fact exact L5 chronological
  replay rejects the context-free fixed policy at the second scheduled stitch:
  its first new point lies on an old--old secant.
- The old multi-action common-potential repair is also false on that second
  stitch.  Its full-cache census retains 601 words overall but only eight for
  the repeated step-20 corridor.  All eight work at the first stitch, while
  the exact correlated `8 x 8` response matrix at the second stitch is empty;
  anchor-only witnesses kill every response.  This rejects that frozen action
  region, not every larger or state-dependent controller.
- The exact lattice-`T` replacement retains 8,367,038 zero-envelope and
  10,252,458 ordered-envelope words.  Their whole-word arbitrary-switching
  unions are acyclic on the finite lattice envelope, preserving actual slot
  correlation.  This controls only contiguous direction-blind
  candidate-to-candidate chains.  Silent zero-mask intervals, nondegenerate
  selectors, births, unrelated-cursor imports, and complete global poison are
  outside the certificate.
- A chronological L5 construction using the strict zero-envelope channel and
  globally unused yz fibres completes all 2,457 stitches and contains 8,268
  points.  Its independent audit has rescanned every cache ordinal through
  the selected winner and verified the full natural-order point stream, so it
  is an exact terminal finite certificate.  It remains one finite orbit, not
  a safety invariant or an all-level survivor theorem.  A stronger proposal
  forbidding secant directions with `J` in `{11/3,348/275}` is already
  incompatible with the inherited seed: anchors 30 and 33 have `J=11/3`.
  The complete 34,175,778-pair diagnostic finds 758 cone secants and 76 named
  macro-ray secants, including 61 connector-born named-ray pairs.  Its exact
  moment join finds no inherited cone line in the tested actual L5 or induced
  L6 named roles; connector-born roles and selected L6 actions remain open.
  A proved conditional repair is to grandfather a finite base and forbid every
  later old--new and new--new birth on the two entire invariant cones.  The
  cone equations are preserved by `M`, so this freezes those populations, but
  availability under the added global guard and exhaustiveness of the two
  cones are unproved.
- That conditional guard now has one exact independent finite test.  A guarded
  L5 path completes all 2,457 stitches; its auditor reproduces all 4,211 guard
  rejections and checks all 34,407,660 terminal pairs, leaving only the 246
  inherited anchor--anchor cone pairs and no triple.  This validates the
  grandfathering mechanism on one orbit, not uniform availability.  A
  separate guarded L6 path from the ordinary primary L5 base is paused at
  6,348 / 8,267 stitches, so the two positive computations are not consecutive
  levels of one guarded history.
- The exact correlated `8 -> 16 -> 8` holonomy census prevents treating those
  two cones as exhaustive: 3,136 affine return maps and 2,094 fixed points
  yield 47,942 primitive full-candidate guard polynomials outside the four
  known classes.  These are abstract action-channel candidates, not proved
  chronological secants.  The fail-closed role-first checker must still show
  an actual selected role, physical line birth, Pluecker compatibility, and
  killed-word mask before any such polynomial becomes a reachable obstruction.
- The exact short-word GFP is empty.  There are 552 legal length-2 words and
  56,516 legal length-3 words, but even their union prunes
  `124 -> 104 -> 84 -> 70 -> 56 -> 36 -> 20 -> 10 -> 2 -> 0`.
  Consequently every recurrent closed policy must use length 4 or 5.  A
  mixed-length policy with Perron--Frobenius growth exactly 3 remains open.
- The exact ghost-site pullback contracts addresses by one third but sends the
  normalized nonzero incidence residual to three times itself and preserves
  zero residual exactly.  Thus a shell transfer can rank positive residuals
  only after a discrete gap; recurrent exact incidences need a finite
  correlated future-compatibility quotient or explicit promotion.
- The common height-two policy potential does not repair zero-mask re-entry.
  Under its pinned fixed actions, exact integer lattice lines can remain
  invisible through arbitrarily many `8 -> 16 -> 8` phase cycles and then hit
  a selected interior.  This proves infinite geometric right-language
  complexity, but not reachable secant births in a legal ordered history.
- The same latent family has exact primitive spacing proportional to `9^n`
  and a level-independent positive reveal weight.  Bounded diameter gives a
  deterministic cutoff at each fixed finite level, but the cutoff grows with
  the construction and is not a uniform tail bound.  The exact birth operator
  shows what must be charged; a weighted LLL or mask-valued shell transfer is
  still only a proposed route because no uniform reachable-birth envelope or
  inductive availability inequality has been proved.
- The exact generic whole-word transfer census rules out replacing that
  envelope by average descendant branching: both all-descendant kernels obey
  `2 <= rho <= 5`.  The continuously effectful lattice-`T` subkernel is zero
  for the strict envelope and nilpotent of exponent at most 218 for the
  ordered envelope, but silent ghosts, line births, legality conditioning, and
  coefficient-one cursor imports are outside those finite kernels.
- The first exact translation CEGAR witness has identical tested zero current
  masks and birth/owner shells but produces 3,998 versus zero killed words one
  recorded slot later.  Exact centred endpoint/partner Pluecker data explains
  the split; retaining it makes all 146 tested L8 states singleton.  This
  repairs that finite transition without supplying finite-index evidence.
- A constrained alternate L5 selector now chooses only projection-fresh words
  that also pass exact global 3D legality.  It completes all 2,457 stitches and
  8,260 points, preserving exactly the 31 doubled yz fibres inherited from L4
  and creating no x-line.  This is one reproducible finite orbit, not a
  survivor floor or non-x tail theorem.  A separately committed L6 prefix is
  now construction-complete at 8,259 stitches and 28,737 points, but its
  independent first-survivor and ordered-chain audit is still running; it is
  not yet a terminal finite certificate.
- The selected-horizon L9 age-two audit follows the actual `42 -> 146 -> 488`
  tagged lineage against every L9 anchor and finds 58 nonzero states.  Anchor
  joins dominate the direct poison and partners born at L6, L7, and L8 all
  contribute.  Every nonzero state is a singleton under the finest tested
  observed refinements, so this refutes age-two inertness without proving a
  finite transition quotient.  Current L9 connector interiors are omitted.
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
| Exact shell-5 endpoint lineage and all-domain L8 source closure | `design/deep_incidence_lineage.py`, `design/deep-incidence-lineage-summary.json` |
| Exact frozen-L8 A-B-C-D-E response transition | `design/l8_immediate_action_cegar.py`, `design/l8_third_ply_closure.py`, `design/l8_fourth_ply_transition.py`, `design/l8_fifth_ply_transition.py` and their compact summaries |
| Exact realized far-frontier and birth/shell traces | `design/far_secant_future_trace.py`, `design/far_secant_birth_shell_trace.py` and their compact summaries |
| Exact x-parallel latent-line and recurrence audit | `design/x_axis_far_secant_resonance.py`, `design/x-axis-far-secant-resonance-summary.json` |
| Exact observed x-axis Bellman barrier and realized-node join | `design/x_axis_bellman_barrier.py`, `design/x_axis_barrier_node_join.py` and their compact summaries |
| Exact observed x-axis core-promotion collapse | `design/x_axis_core_promotion_probe.py`, `design/x-axis-core-promotion-probe-summary.json` |
| Exact all-action synchronized x-line core | `design/x_axis_universal_bellman.py`, `design/x-axis-universal-bellman-summary.json` |
| Exact realized-word x-line occupancy/birth smoke test | `design/x_axis_occupancy_birth_probe.py`, `design/x-axis-occupancy-birth-probe-summary.json` |
| Exact unrelated-cursor x-core injection census | `design/x_axis_cursor_jump_injection.py`, `design/x-axis-cursor-jump-injection-summary.json` |
| Exact no-new-x-line alternate L5 construction | `design/no_new_x_line_constructor.py`, `design/no-new-x-line-constructor-summary.json` |
| Exact ghost/future compatibility CEGAR | `design/far_secant_future_compatibility_probe.py`, `design/far_secant_translation_cegar.py` and their compact summaries |
| Exact full-domain non-x graph and all-iterate cycle certificate | `design/nonx_degenerate_site_graph.py`, `design/nonx_cycle_invariant_certificate.py`, their compact summaries, and `design/GHOST-LANGUAGE-AUTOMATON.md` |
| Recorded non-x cycle reachability, acyclic fixed-word pilot, and chronological falsifier | `design/nonx_cycle_realized_reachability.py`, `design/nonx_fixed_word_policy_probe.py`, `design/fixed_policy_chronological_replay.py` and their compact summaries |
| Exact common-potential second-stitch falsifier | `design/potential_policy_chronological_rescue.py`, `design/potential_policy_two_stitch_matrix.py` and their compact summaries |
| Exact lattice-`T` whole-word action envelopes | `design/nonx_scc_core_action_probe.py`, `design/nonx-lattice-envelope-action-probe-summary.json` |
| Strict zero-`T`, fresh-yz L5 construction and pending audit | `design/lattice_t_chronological_replay.py`, `design/lattice_t_chronological_audit.py` |
| Exact length-3 and length-at-most-3 GFP no-go | `design/exact_length3_gfp.py`, `design/exact-length3-gfp-summary.json` |
| Exact latent re-entry under the fixed policy | `design/nonx_latent_reentry_certificate.py`, `design/nonx-latent-reentry-certificate-summary.json`, `design/LATENT-REENTRY-OBSTRUCTION.md` |
| Exact far-birth operator and proposed reachable envelope | `design/FAR-SECANT-BIRTH-OPERATOR.md` |
| Exact x-projection coset address | `design/X-PROJECTION-COSET-ADDRESS.md`, `design/x_projection_coset_address.py` |
| Exact selected-horizon L9 age-two poison and stabilization audit | `design/l9_anchor_age2_precursor.py`, `design/l9_anchor_age2_positive_mask_verifier.py`, `design/l9_age2_transition_stabilization.py` and their compact summaries |
| Far-secant frontier algebra and safety-game obligations | `design/FAR-SECANT-RANK-LEMMA.md` |
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
has closed.  Following the two shell-5 witnesses confirms the sharper failure:
their direct atoms disappear at L8, yet their endpoints switch roles and create
156 atom occurrences on 64 recorded corridors (channel memberships overlap),
with one source-only mask killing 131,472 of 501,044 words.  Thus a vanished
poison mask cannot be discarded; the noncontracting state must retain endpoint
and secant frontiers and close them under mixed-pair generation.  The exact
future trace sharpens this: a direct state is noncongruent even with the actual
connector choice, while the enriched birth/shell state has no repeated nonzero
child or parent transition from which to infer stabilization.  The plausible
remaining route also has a concrete resonance obstruction: the exact
x-parallel graph contains latent reactivation and short returns even after the
effect mask and, in three physical cases, the selected action repeat.  Those
returns demand a finer lineage phase, exact promotion, or a non-strict
contraction; they are not evidence for an infinite policy cycle.  The plausible
exterior Bellman rank is exact on every observed exterior transition, but
11,107 / 11,154 actual effect nodes and every observed return source are in its
core.  The first L9 continuation also falsifies age-two inertness and finds no
repeated effectful refined state.  The route therefore needs a finite universal
promotion or other control of the bounded core.  For synchronized carried
x-lines this part is now exact: the all-action module has a 53,216-state core.
Exact finite replay now supplies the occupancy and birth equations, but not a
stabilizing quotient: every tested literal occupancy state is unique and the
active-line-only quotient is noncongruent.  A symbolic monotone occupancy state
and the interface for chronological jumps to unrelated anchors remain open.
The full cursor census now rules out the most natural version of that
interface: exact jump and complete local core occupancy still do not determine
the imported mask.  Pipeline and left-to-right orders reduce imports but do
not restore congruence, so an exterior birth/address-shell state or a genuine
tail rank is required.
The alternate no-new-x-line L5 orbit shows that one coherent policy can avoid
all new x-line births while remaining globally legal, but it certifies only one
survivor at the worst stitch and starts with 31 inherited x-lines.  Extending
that policy through a fully audited L6 certificate, or restarting it from a
yz-injective seed, remains a construction obligation; neither option controls
non-x secants.  The lateral quotient `Z^2/BZ^2 ~= Z/9Z` does prove that new
x-fibre collisions are a bounded-range CSP, but a 25-fibre local cage shows
that bounded projection multiplicity alone cannot guarantee a connector.
For non-x lines, the full-domain degenerate graph contains a 768-state SCC and
an all-iterate clean geometric two-cycle.  A policy must exclude that cycle or
prove its inverse-direction secant births unreachable; a full-menu strict
lifetime rank is impossible.
The route also needs a full current-L9
connector closure, before a typed residual contraction can support
availability.  Numerical confidence
percentages are opinions and are not part of the mathematical result.
