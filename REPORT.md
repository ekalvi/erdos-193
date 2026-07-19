# Problem #193 computational programme — session report (2026-07-11)

Machine: Eriks-MBP (i7-7700HQ, 4 physical cores). All arithmetic exact (integer).
Code: `search193.py` (original program), `bnb193.py` (free-choice branch-and-bound),
`erdos193.py` (staged/sharded/checkpointed searcher + scientific controls).

## Validation
- Fast O(n²) collinearity checker agrees with the O(n³) oracle on 500+ random walks.
- Tribonacci + standard basis collides at step 7 (the `00` factor), as predicted.
- All five scientific controls pass (constant word, Tribonacci, Gerver–Ramsey-style
  prefix, oracle agreement, invariance under translation + unimodular maps).
- Every kept collision is independently re-verified via the cross-product test.
- Repeated vertices are reported as `RepeatedVertex`, not fabricated triples.

## Search results (random primitive substitutions, staged filtering)

| Shard | Alphabet | Radius | Trials | Primitive tested | Best safe prefix |
|---|---:|---:|---:|---:|---:|
| original run | 4 | 2 | 100k | ~50k | 18 |
| main | 4 | 2 | 10M | 5.15M | **27** |
| wide vectors | 4 | 3 | 5M | 2.60M | 24 |
| five letters | 5 | 2 | 5M | 2.54M | **39** |
| six letters | 6 | 2 | 5M | 2.48M | **46** |

Failure modes among each shard's kept top-100: 59–71% die on *adjacent* triples with
equally spaced indices (proportional-displacement adjacent blocks — the Abelian-square
mechanism), the rest on general-position triples. Wider step vectors barely help;
more letters help a lot. Both facts match the Abelian-square analysis (§2 of the
programme notes): the obstruction is combinatorial repetitiveness, not geometry.

## Free-choice walks (branch-and-bound, same legality predicate)

| Step set | |S| | Longest triple-free walk |
|---|---:|---:|
| {(-1,-2,2),(-2,0,1),(-1,1,2),(0,2,-1)} (best substitution candidate) | 4 | **≥ 224** (2M nodes → 206; 30M nodes → 224, budget-limited) |
| ±e₁, ±e₂, ±e₃ | 6 | **= 20** (exhaustive, true maximum) |
| (1,0,0),(0,1,0),(0,0,1),(1,1,1) | 4 | **= 14** (exhaustive) |
| tetrahedral (±1,±1,±1) even sign pattern | 4 | **= 7** (exhaustive) |

The ≥224 free walk vs. the 27-step substitution ceiling *on the same step set* is the
key comparison: geometry permits long triple-free walks; substitution structure kills
them an order of magnitude earlier.

Diminishing returns: 15× more search budget (2M → 30M nodes) improved the record by
only 18 steps (206 → 224). Suggestive of a genuine ceiling in the low hundreds for
this step set — but DFS explores in fixed depth-first order, so this needs
confirmation by randomized restarts / beam search before being trusted.

## Main structural finding: Pattern B is universal (and provably so)

For every top candidate in every shard, the return-word displacement profile shows:
rank R_m = 3 at all marker scales m = 1..8, while the normalized determinant

  δ_m = max |det(D₁,D₂,D₃)| / (‖D₁‖‖D₂‖‖D₃‖)

contracts monotonically, e.g. 0.7071 → 0.3008 → 0.1067 → 0.0423 (main-shard winner),
and 0.3545 → … → 0.0009 (radius-3 winner). This is exactly "Pattern B" of the
programme notes — but it is NOT a clue found by the search; it is forced:

> For a primitive substitution the incidence matrix has a strictly dominant Perron
> eigenvalue λ₁ (Perron–Frobenius). Parikh vectors of long factors align with the
> Perron eigenvector at rate ~|w|^(θ−1), θ = log|λ₂|/log λ₁ < 1, so ALL long return
> displacements become asymptotically parallel (not merely coplanar) and δ_m → 0.

Numerical check (main-shard winner): eigenvalue moduli 4, 2, 1.618, 0.618, so
|λ₂|/λ₁ = 0.5; observed δ-contraction ratios 0.43, 0.35, 0.40 — same scale.

Consequence: **"Pattern C" (recurrent full-rank return structure with normalized
determinants bounded away from zero) is impossible within the class of primitive
substitution fixed points.** The refined target conjecture —

> a uniformly recurrent collinearity-free displacement word cannot maintain a
> recurrent full-rank return substitution —

is therefore unfalsifiable-by-search inside this class for the quantitative
(normalized) form: the contraction always happens. The honest reformulations are:
(a) the *exact* rank-collapse question (integer determinants of level-k return
displacements hitting 0), which PF alignment makes plausible but does not prove —
the integer determinants can still grow while the normalized ones shrink; and
(b) whether *any* class escaping PF contraction (S-adic with unbounded directive
sequences, or genuinely non-substitutive words like the branch-and-bound walks)
can sustain triple-freeness. The ≥206 walk shows the geometric room exists.

## What is actually proven vs. evidence
Proven (by exhaustion, modulo code correctness): the three exact maxima above,
e.g. "the longest 3-collinear-free walk with steps ±eᵢ has exactly 20 steps."
Everything else is evidence. Novelty of the exact maxima needs a literature check
(they may exist in OEIS / no-three-in-line literature).

## Artifacts
- `results_100k.txt` — original program's full output.
- `results/*.json` — shard checkpoints (top-100 candidates each, with substitution,
  steps, disqualifier, return profiles, SHA-256 word hashes for reproducibility).
- `logs/*.log` — shard logs with throughput.
- `bnb193.py` output — exhaustive maxima; 26- and 124-vector sets still running.

## Addendum (2026-07-12): randomized probes, imbrication, amplification

**Ceiling was menu-specific, not universal.** Randomized-restart DFS and beam
probes (beam193.py): good-4 menu 226 / 166; main-shard winner 212 / 150; but the
radius-3 winner menu {(-1,3,-2),(-1,-1,3),(0,3,-1),(3,-3,-3)} reached **342**.
The 26-vector radius-1 set reached **9,862** in a 2M-node budget. Walk length
scales strongly with menu quality; nobody has optimized a menu yet.

**2D calibration:** with ±e1,±e2 the exact maximum is **3** (exhaustive);
random skewed 4-step menus reach 27 (exhaustive) and >=30 (budgeted). Same
~10x trivial-to-skewed ratio as 3D. (In 2D every menu is provably finite —
Gerver–Ramsey.)

**Imbricated (self-similar) constructions** (imbricate193.py, imbricate_seam.py):
walks self-similar under an expanding integer matrix M evade the PF no-go when
M has equal-modulus spectrum with irrational rotation
(M = diag(2, companion(l^2+l+4)), cos t = -1/4). With ~276 random menus the
irrational-rotation matrix hit **30**, beating 5.15M abelian candidates (27).
Structural theorem found en route: **adjacent identical tiles are always fatal**
(anchors 0, D, 2D collinear), so valid imbricated words are necessarily
square-free at the letter level; boundary square-freeness is equivalent to
seam checks already performed. Context-free tiles (one tile per letter) are
statistically doomed: measured seam compatibility ~7-10% per ordered pair with
~15+ occurring pairs needing to hold simultaneously.

**Anchor-guided amplification** (amplify193.py) replaces context-free tiles:
scale a verified walk by M (anchors inherit triple-freeness by linearity),
then stitch anchor-to-anchor with all placed points AND all future anchors as
obstacles (a stitch may never pre-poison a later target). First findings:
(a) the periodic matrix (M^3=2I, volume x2/level) densifies every level and
must eventually jam — ruled out; (b) for the modulus-2 irrational matrix,
random menus force stitches of length 9-16 across anchor gaps of 4-9 — the
menu's steps misalign with M's images, and stitching jams in congestion.

**Menu/matrix co-design** (design_menu.py): the fix is menus closed under
short M-decomposition — every M.s a sum of 2-3 menu steps — so walks grow
2-3x per level inside volume growth 8x and density FALLS per level (the
precondition any clearance-based finite certificate needs). The companion
form's -4 entry makes closure impossible at radius 3; the balanced conjugate
M_BAL = diag(2, [[0,-2],[2,-1]]) (same spectrum) is being searched now.

## Corrections after expert review (2026-07-12, round 3)

- The collinearity invariant is the CROSS PRODUCT Omega = (y-x) x (z-x), not a
  scalar triple determinant (det(x,y,z)=0 is coplanarity-with-origin, not
  collinearity). Our code (analyze_valuation.py, all legality checkers) already
  used Omega; earlier prose was wrong and is corrected here.
- Under x -> Mx the cross transforms by wedge^2 M = det(M) M^{-T}, NOT by
  det(M). For M = diag(3, [[0,-3],[3,-1]]), SNF(M) = diag(1,3,9), so valuation
  gains along the Smith filtration are 1, 2, 3 per level — not uniformly 3.
  This is consistent with (and helps explain) the observed flat v3 profile.
- The D>1 metric-collapse claim is overstated: a directional-packing argument
  proves min-height collapse only for mass dimension D>2 (height O(R^{1-D/2}));
  at our D ~ 1.3-1.5 the collapse is empirical + extreme-value-heuristic, and a
  deterministic threshold below D=2 needs incidence/regularity hypotheses.
- Bounded-tube status: rational tube direction is fully solved (quotient-fibre
  pigeonhole gives infinitely many points on one lattice line); rank-2
  directions confine infinitely many vertices to a rational plane; totally
  irrational + finite-step remains open and is close to the main problem. The
  tractable target: linearly recurrent bounded-tube walks.
- Certificate programme (corrected): state = (first-divergence level r and
  type tau, v3(Omega) - a_tau r, normalized residue 3^{-v3}Omega mod 3^q,
  residues of difference vectors). Global-router walks do not automatically
  certify (routing is not finite-state); the goal is to INFER a finite-state
  routing rule from successful levels and verify residue-graph closure.

## Stage-4 build log (2026-07-12 evening)

- Step 1 COMPLETE: length-<=4 connector word layer. 7,114,584 fully legal words
  (endpoint, menu, no repeated points, no internal collinear triples); word-level
  closure retains 124/124 steps in one round; word-weighted collar = 2,102 interior
  offsets, 21.3M multiplicity (collar_multiplicity4.json; full domains in local
  connector_domains4.pkl, 78MB, not committed).
- Census reweighted by word multiplicity (agent caveat 1): mean separated fraction
  0.9211, worst 0.9073 over 120 realized unresolved pairs (3k weighted samples each)
  — statistically unchanged from the uniform-Delta census (0.9221/0.9217).
- Next: Step 2 (reachable abstract state GFP), Step 3 (H-window event hypergraph,
  hierarchical template compression — the make-or-break), Step 4 (exact p_H via
  transfer matrices), Step 5 (LLL criterion ladder), Step 6 (joint GFP).

## Decoupling insight (2026-07-13 late)

Creation-time semantics (panel-confirmed) decouples levels: a completed level is
deterministically safe forever, so the certificate reduces to a PER-LEVEL existence
statement — "given any triple-free walk, a safe stitching of the next level exists" —
plus induction. With measured per-stitch bad mass ~0.4 < 1, this is potentially a greedy
counting argument; the multi-level LLL may be unnecessary. Remaining to verify:
worst-case conditional cross mass (running), triple-newborn events, and fatal-mass
invariance across all levels (the self-similarity argument).

## The complete per-stitch ledger (2026-07-14)

All event families measured on the certified walk:
own-line fatal mass 0.317 + realized cross damage ~0.10 + Markov future-tax 0.333
(inflict <= 3x average on later segments; words violating it have mass <= 1/3)
+ triple-newborn <= 0.028 (worst of 6 segments; median ~1e-3) = ~0.78 < 1.
=> At every stitch decision a safe word EXISTS by counting alone (~22% headroom).
Per-level routing existence + inheritance induction is the full proof skeleton;
remaining mathematics: scale-invariance of the constants, and hostile review.

## Next steps suggested by the data
1. Finish the deep DFS bounds (running); try iterated-greedy/beam search to push the
   4-step lower bound well past 206 and look for self-similar structure in the
   record walks (the "finite certificate" idea from the programme notes).
2. Move the search class from primitive substitutions to S-adic sequences with
   slowly-growing directive complexity — the only substitutive-like class not
   killed by the PF-contraction argument.
3. Literature check: exact maxima (20 for ±eᵢ), and whether the PF-contraction
   observation about return displacements is already recorded.

## Correction and ordered-path safety audit (2026-07-18)

The July 14 claim above that the per-stitch ledger gave a proof is withdrawn.
Its reported availability floors were extrapolated after testing at most 200
words per stitch, not exhaustive lower bounds.  More fundamentally, connector
legality is global: a candidate point can lie on a secant whose endpoints are
both far from its corridor.  Exact replay shows far secants remove 51--68% of
the apparent radius-40 survivors at the principal L5--L7 bottlenecks.  Bounded
local crowding therefore does not imply positive connector availability without
a separate uniform far-secant lemma.

The old Lemma R is also too weak.  It asks only for some constant `C` with
`c_k(q,r) <= C r^d` on the fixed interval `1 <= r <= 10`; the repository's
level-uniform cubic crowding bound already implies such a constant.  The real
remaining statement is a finite, policy-independent reachable-state invariant
with a total legal-word selector and universally checked successor closure, or
a sharp numerical near-mask theorem plus a uniform far-tail theorem whose union
still leaves a word.  Unbounded finite levels would then yield an infinite word
by König's lemma; the amplified point sets themselves are not nested.

The full connector-menu OSC remains refuted by its exact generation-2 overlap,
but that overlap is between alternative connector choices.  A realized path
chooses only one connector per gap, so it does not by itself refute an ordered-
path certificate.  Conversely, the accelerating/chiral small-box separation
signal was caused by prescaling and never covered the true 15,545-element
difference closure.

### Causal inherited-tile pipeline

To remove the global fragile-first cursor, inherited tiles are swept left to
right: place the next tile's fragile guard when it has one, then finish the
current tile in local `(domain size, gap index)` order.  At the L7 bottleneck
this gives exactly

```text
D3785, A3782, B3784, target3783, G3788, C3786.
```

The exact causal state before D has 36,589 points and no frozen future
connectors.  Pinned D8681/A1465/B425 choices remain sequentially legal and
leave 111 / 9,046 target words.  Every one of those 111 target choices leaves
at least 1,153 / 1,505 short words at G3788.  The unique floor target was
recomputed independently.  Pinned target26 leaves 350,509 / 453,015 words in
G's complete domain; choosing G0 leaves 1,887 / 2,570 words at C3786.  This is
an exact two-ply certificate at one incoming state, not closure over incoming
histories or levels.

### Exact lifetime and transition experiment

Eighteen middle-step-122 corridors with inherited signature `(123,122,123)`
were fixed before inspecting their poison results: L5--L6 train, four L7
validation probes, and three untouched L8 holdouts.  Every collision,
old--old--new secant, and old--new--new line witness was scanned against the
complete causal prefix with no endpoint cutoff.  Endpoint birth ages, owner
tiles, placement times, and factor-of-three spatial shells remain correlated.

Training fixes minimum owner radius 625 for both every killed word and every
poisoned atom.  No L7 or L8 probe exceeds it.  This is encouraging finite
evidence only: 625 is not a useful literal window, and 18 probes cannot prove a
uniform horizon.  More decisively, the training first-visible spatial horizon
of shell 4 fails in L7.  Gap 13,171 has one first-visible shell-5 atom uniquely
killing 56 words, with an age-0/age-0 shell-4/shell-5 witness; gap 21,115 has an
age-0 shell-5 point atom uniquely killing nine.  A scalar or fixed-cutoff deep
tail cannot absorb same-level outer-shell effects.

All 18 killed-word masks, poisoned-atom masks, and witness hashes are distinct.
A four-sentinel exact transition test freezes L5--L6 codes for the contiguous
four-tile factor, source poison, recorded action, successor, and whole edge.
Every corresponding L7 and L8 code is new.  Literal exact-state stabilization
therefore fails on this sample, although a coarser sound antichain/BDD/arithmetic
quotient remains possible.  The L8 successor has 1,898 / 2,570 full-domain
survivors; the other successor scans are explicitly limited to their exact
length-2--4 cores because the complete domains contain 298,775--501,044 words.

The plausible remaining analytic lemma is now sharply split.  Current and
age-one geometry must remain in an exact, noncontracting safety state.  The
age-at-least-two residual needs both endpoint and already formed secant
frontiers, including near--deep generation.  A scalar shell count is unsound;
the transition family needs a common Lyapunov function with joint contraction
or a strict integer/3-adic rank, followed by direct nonfatality of the resulting
poison masks.  The strongest obstruction is a reachable resonant secant cycle:
linear scaling preserves collinearity, so such a type can recur with unit
effect unless retained exactly or ruled out arithmetically.

Reproducible artifacts are `design/ORDERED-PATH-SAFETY-GATE.md`,
`design/inherited_tile_lifetime.py`,
`design/pipeline_transition_stabilization.py`, and
`design/l7_pipeline_macrotransition.py`, with compact JSON summaries beside
each checker.  None of these results is an unconditional solution.

## Shell-5 endpoint lineage and all-domain L8 closure (2026-07-18)

The two L7 shell-5 validation atoms were replayed with stable point identities.
Both are caused entirely by connector interiors born at L7: the gap-13,171
site atom has two age-zero endpoints, and the gap-21,115 line atom has one.
Consequently they cannot test contraction of an age-at-least-two residual with
data ending at L8; after one application of the enlarging matrix their three
images are only age-one anchors.

The initial transport test found zero effect for the carried old--old line and
the carried singleton point on the six actual child corridors and on all 838
L8 step-122 corridors.  That was a valid same-mode negative test but not a
sound source closure: an inherited endpoint can change roles.  It can collide
with a candidate site, lie on a line through two candidate sites, or form a
new secant with any point active in the current L8 prefix.

The corrected checker performs that complete endpoint-involving closure on all
92,731 recorded L8 pipeline prefixes and all 124 effective domains.  It indexes
all 311,738 final L8 points by exact primitive direction from each of the three
tagged endpoints and filters partners by their exact activation rank.  All
12,537,146 connector words are covered when converting the reached atoms to
action masks.  No endpoint or distance cutoff is used, and every recorded
chosen connector is independently checked against the tagged-source union.

The endpoint closure is nonzero on 64 corridors.  The two-endpoint source
affects 40 corridors and reaches a worst mask of 131,472 / 501,044 words; the
singleton affects 24 and reaches 11,453 / 501,044.  Channel memberships overlap:
the first source has 39 tagged--other secant corridors and six endpoint-on-line
corridors; the second has 22 and six.  There are no collisions or tagged--tagged
site effects.  The exact direct affine images never occur.  Thus the old line
or atom can disappear while its endpoint frontier reactivates as different
atoms.  Effects reach shell 6, owner radius 882, and mixed partner ages through
five, so neither distance shell nor the sampled owner-625 horizon is a
monotone transfer rank.

This is strong negative evidence against a mode-preserving or scalar shell
operator, but it is neutral on a properly typed deep residual: all tagged
endpoints are still in the required noncontracting age-zero/one state.  The
next proof step is an age-zero/one endpoint-frontier safety lemma with a total
selector.  The later selected-L9 precursor now performs a finite all-anchor
age-one-to-age-two promotion and finds 58 nonzero states, decisively refuting
literal inertness.  It remains falsification/design data, not a substitute for
the universal transition lemma, because current L9 connector interiors and
alternate histories are absent and all refined effectful states are
singletons.

Reproducible artifacts: `design/deep_incidence_lineage.py` and
`design/deep-incidence-lineage-summary.json`.  The canonical raw output and
current checker hashes are recorded in the compact summary.

## Exact frozen-L8 A-B-C-D-E policy transition (2026-07-18)

The ordered-path experiment now starts from the exact 250,697-point prefix
immediately before pipeline rank 67,010.  The first corridor A has 5,257
domain words, of which exactly 1,997 are legal against the entire prefix.  The
first-response checker scans every one with no endpoint cutoff.  Every A has a
B response; the minimum response count is 2,282.  No single B works for all A,
but a deterministic seven-node poison-predicate tree partitions all 1,997
actions into four B-compatible leaves of sizes 1,241, 206, 188, and 362.

Those four leaves are not depth-three states.  Exhaustively testing their
21,669 selected A,B histories shows that every history has a C response, but
the 1,241- and 362-action leaves have no uniform fixed B,C pair.  Exact
A-dependent C-poison predicates refine the selected policy to ten
response-compatible leaves.  Each leaf retains its full list of concrete A
indices and one fixed B and C; together they cover every A exactly once with
no unresolved history.  The overlapping 1,977-action B=8765 probe separately
requires eight C-response leaves, confirming that the refinement is real.

The ten leaves were then transported through the immediately following real
scheduler stitch: rank 67,013, gap 67,013, step type 19, with 6,736 D words.
For every exact history the complete poison was evaluated as

```text
BaseD(P) | UA(A) | UB(B) | UC(C) | XAB(A,B) | XAC(A,C) | XBC(B,C).
```

This is an equality, not a distance truncation.  It includes every old
endpoint pair in the 250,697-point prefix, every old point on a candidate
D--D line, and every mixed pair among A, B, and C.  Two independently selected
histories were checked again with a full `compute_poison` scan and sequential
legality predicate.

All 1,997 histories retain D.  More strongly, no new partition split is
needed: domain index 0, word `[0,3,4]`, is common to all ten leaves.  The
per-history survivor floor is 1,601; the ten common-response counts range from
283 to 796.  Mixed pair terms are genuinely necessary: their largest
increment beyond BaseD and the unary terms adds three atoms and kills 230 more
D words.  The canonical fourth-transition artifact has SHA-256
`61ce7ebd1fdff96fbf7df2fd741223f447515bab6f61b1741fec132653d44e01`.

The same exact policy was then swept through the next scheduler stitch E:
rank 67,014, gap 67,012, step type 17, with 35,751 domain words.  Its complete
poison identity has BaseE, four unary terms, and all six mixed pairs among
A,B,C,D.  Every one of the 1,997 histories retains E.  Again no predicate
split is required: each existing source leaf already has a common E word,
with 46--1,923 common words and a minimum per-history survivor count of 6,995.
Five distinct E responses serve the ten leaves.  Mixed-pair terms add as many
as six new atoms and 3,058 newly killed words beyond BaseE and the unaries.
Two complete full-history recomputations agree with the optimized union.  The
canonical fifth-transition artifact has SHA-256
`5218b498ece1d2affbf802ef295c23287752c407bdd464668854c1a9af846f10`.

This is strong finite evidence that the ten predicates capture something
strategy-relevant.  It is not transition congruence: the predicates were
learned at one prefix, and nothing yet proves that they are observable,
finite-state, or closed under other prefixes and levels.  The correct next
test is replay and future-trace refinement, not declaring the ten leaves an
inductive invariant.

The first future-trace refinement is exact but negative for finite-state
closure.  The two tagged L7 sources give 42 actual parent states and 146
actual L8 children, retaining every realized connector choice.  Sixty-one
children have full poison strictly beyond the direct endpoint/carried-line
mask, using 57 partner points, 24 born in L8.  The tested
`(mode,step,actual choice,direct mask)` projection is noncongruent in two
classes.  A birth/shell decomposition retains 94 exact descriptor-mask terms
(53 inherited-partner, 29 current-level, 12 direct), but every repeated child
class is zero-poison and all 42 enriched parent transitions are singletons.
This proves that partner joins cannot be omitted and supplies no nonzero
stabilization or contraction evidence.  Reproducible artifacts are
`design/far_secant_future_trace.py`,
`design/far-secant-future-trace-summary.json`,
`design/far_secant_birth_shell_trace.py`, and
`design/far-secant-birth-shell-trace-summary.json`.

## Centred far-secant frontier and exterior escape rank (2026-07-18)

The far-tail specification has been sharpened to an exact algebraic interface.
Relative to a pending anchor `a`, retain every centred endpoint `u=p-a` and
every old secant as a primitive Plücker pair
`(g,mu)=(canonprim(r-p),(p-a) cross g)`.  These objects decide all external
legality channels exactly: collision is `u=x`, an old point on a candidate
line is `u cross (y-x)=x cross (y-x)`, and a candidate site on an old secant is
`x cross g=mu`.  Recentring and cofactor transport give explicit exact
successor formulae; no independent endpoint streams are introduced.

There is also a real contraction component.  For the positive form Q with
`M^T Q M=9Q` and `R=Q^-1`, the line-offset ratio
`sqrt(mu^T R mu)/sqrt(g^T Q g)` expands by exactly three under common scaling,
independently of primitive gcd normalisation.  With a bounded synchronized
recentring digit it obeys the lower bound `h' >= 3(h-B)`, while a line that
hits a finite candidate corridor must satisfy a finite operator-norm bound
`h <= H_s`.  This can support an outward rank for the old-secant-to-site
channel.

The exact ghost-site calculation also sets a hard limit on what “contracting
shells” can mean.  A child query at `x'` pulls back to
`phi_c(x')=c+M^-1 x'`.  If `r=mu-phi_c(x') cross g` is the parent incidence
residual, then `r'=C r/t` up to canonical sign.  Hence the normalized residual
triples, while `r'=0` exactly when `r=0`.  Address tails shrink geometrically,
but the Boolean fact of lying on the line does not shrink at all.  Deep digits
may be discarded only after a discrete residual gap, a finite correlated
future-compatibility quotient, or promotion of every zero-residual recurrent
component.  Euclidean IFS contraction alone is not a tail proof.

Primitive direction size itself cannot supply the missing rank.  If
`T(g)=canonprim(Mg)` and `t=gcd(Mg)`, then `t` is exactly 1, 3, or 9 and
`||Tg||_Q=(3/t)||g||_Q`.  The inverse digit matrix `N=9M^-1` sends every
primitive vector with y nonzero modulo three to another primitive vector, and
`M N^j h=9N^(j-1)h`.  Hence `N^n(0,1,0)` gives arbitrarily long runs of
factor-one-third normalization.  A height, valuation, or fixed-modulus
direction counter is therefore not a uniform tail rank.

For a line that hits a candidate site at every synchronized stitch there is a
finite alternative.  Consecutive sites obey
`[x'-M(x-c)] cross Mg=0`.  A nonzero bracket forces the next primitive
direction into a finite selector set; each non-x orbit can hit each selector
direction only once.  Zero brackets form a finite direction-blind site graph.
If that graph is acyclic with longest path `L`, the continuous-effect lifetime
is at most `|V|+(|V|+1)L`.  This reduction does not cover empty-effect
intervals, births, or cursor jumps.  A graph cycle is only an
arbitrary-switching geometric obstruction unless its witness words are also
shown to avoid the carried line and to coexist in a legal ordered history.

For the x direction, the core-finiteness step is now an exact theorem and does
not require the observed phase graph.  Canonically orient the line by `e_1`
and write its integer lateral offset as `zeta=(y,z)`.  Under a child word prefix
`c`,

```text
zeta' = [0 -3; 3 -1] (zeta-c_perp).
```

Its exact norm satisfies `h(Bzeta)=3h(zeta)` and
`h(zeta)^2 >= (6/7)||zeta||_2^2`.  With connector length at most `m`, every
prefix and candidate site has `h<=C_m=2(m-1)sqrt(12/5)`.  Therefore
`D_m=3C_m/2` is forward invariant and contains every potentially effectful
x-line.  For the actual `m<=5` domains, its integer core lies in
`[-20,20]^2`, at most 1,681 offsets per phase.  This removes the x-direction
Diophantine-gap problem for synchronized ancestral transitions.

It does not supply transition closure.  The state still needs exact lateral
occupancy `0/1/2`, collision information, sequential connector insertions,
and honest endpoint coexistence to create new x-lines.  A jump to an unrelated
same-level corridor can also have an unbounded recentering and is not one of
these prefix controls.  For arbitrary primitive directions the core can still
be infinite: every `(g,0)` has zero offset ratio.

The exact phase correction is a Bellman barrier.  For a finite synchronized
phase graph, let `B_e` bound the recentering on `e:q->q'` and solve

```text
D_q = max_(e:q->q') (B_e + D_q'/3).
```

Then `delta_q=h-D_q` obeys `delta_q' >= 3 delta_q`.  Outside the Bellman core,
`ceiling(log_3(L/delta_q))` is a strict escape rank once `L` exceeds every
phase's adjusted effect threshold.  This is a theorem under the stated finite
synchronized phase graph, but it does not make the core finite.  A uniform
finite envelope still needs a gap saying every residual birth is either in a
finite promoted core or has `delta >= epsilon > 0`.  That Diophantine gap is
open.  The sharp finite observed `B_e/H_q/D_q` calculation described below is
now complete; it shows that the exterior mechanism works but that almost every
actual x-line effect lies in the core.

It is not the full tail lemma.  It does not control switching to unrelated
corridor centres, an arbitrarily remote endpoint lying on a candidate-internal
line, near-deep or deep-deep line birth, or the Boolean union over all
lineages.  Moreover, “a finite sound quotient exists” would be vacuous: a
one-state TOP abstraction with every atom poisoned is always sound.  The open
claim is the existence of a finite quotient precise enough to satisfy the
ranked envelope and still leave a legal connector in the safety greatest fixed
point.  The exact obligations and failure modes are stated in
`design/FAR-SECANT-RANK-LEMMA.md`.

## Exact x-parallel resonance audit (2026-07-18)

The x axis is the only rational projective direction periodic under a power of
the scale-and-rotate matrix, so it is the first resonance class that must be
promoted or ranked.  `design/x_axis_far_secant_resonance.py` exhaustively
scanned both exact stitch schedules on the pinned L5--L8 construction: 131,097
corridors per order, 124 effective domains, and 12,537,146 connector words,
with no endpoint or distance cutoff.  This audit covers the old--old--new
channel in which a candidate interior lies on an active x-parallel secant.

Closing every actual selected descendant of the 11,154 strict-effect seeds
through L8 gives 35,220 lineage nodes and 27,103 transitions:

```text
effect -> effect   3,002       effect -> zero   8,109
zero   -> effect      35       zero   -> zero  15,957.
```

The 35 zero-to-effect transitions are an exact counterexample to deleting a
line when its current mask is empty.  At periods one, two, and three the graph
has 12, 2, and 22 returns to the exact effect key `(parent step, relative
lateral offset, ordered site offsets, exact word mask)`.  Gate and pipeline
records pair exactly, leaving 18 physical returns.  Three physical period-three
returns also repeat the recorded connector action.  Physical line identity
does not split them: source and target are the same inherited line with the
same endpoint identities.

This refutes a strict residual DAG rank on the tested effect key, even after
adjoining the selected action.  It does not prove an infinite policy cycle,
because source and target have not been shown to have congruent future ordered
states.  Adding exact age separates this finite sample but introduces an
unbounded field.  Adding bounded lineage suffixes separates the short returns
without making the observed one-step phase relation congruent.  The honest
next state therefore needs the exact effect/offset data plus a monotone
age/contraction rank or an actual correlation-preserving lineage suffix.

The result is one-channel and finite-depth.  It omits non-x secants,
old-on-candidate-line defects, alternate choices, L9 and later levels, and the
union with all other poison.  None of the recorded chosen words is killed by
the complete x-line union, but that is not availability.  The compact artifact
is `design/x-axis-far-secant-resonance-summary.json`; two full runs agree after
removing the embedded elapsed-time field.

## Exact x-axis Bellman barrier and realized-node join (2026-07-18)

`design/x_axis_bellman_barrier.py` solves the rational interval Bellman
problem on the 124-step finite observed x-line phase graph.  Seventy-seven
steps have `H_q <= D_q`; 41 nonterminal steps and six observed-terminal steps
have `H_q > D_q`.  These are properties of the pinned observed graph, not a
universal phase quotient.

`design/x_axis_barrier_node_join.py` joins those barriers back to all 35,220
realized lineage nodes.  Only 47 of the 11,154 strict-effect nodes are outside
the Bellman core; 11,107 are inside.  Of the 24,066 latent nodes, 21,970 are
outside and 2,096 are inside.  Every one of the 13,826 recorded transitions
whose source is exterior remains exterior and has an exact strictly positive
lower bound on `delta_target-3 delta_source`; no exterior-to-core transition
is observed.  Thus the phase-adjusted escape theorem is behaving exactly as
designed on its stated block.

The obstruction is concentrated in the core.  All 36 effect-key return
sources and all six effect-and-selected-action return sources are core nodes.
This rules out the hope that a sharper exterior shell fit alone would absorb
the x resonance.  The next x-axis obligation is a universal finite promotion,
core escape theorem, or counterexample consisting of an unbounded compatible
bounded-core orbit.  The compact certificates are
`design/x-axis-bellman-barrier-summary.json` and
`design/x-axis-barrier-node-join-summary.json`.

The follow-up `design/x_axis_core_promotion_probe.py` collapses the observed
core by exact `(step, lateral offset)`.  Its 13,203 strict-or-latent core
occurrences become 1,312 geometric states: 748 strict and 564 latent.  The
combined killed-word mask is congruent on every state.  With the actual action
and ordered child slot retained, 13,277 transition occurrences become 5,542
distinct labelled edges and 1,645 whole-action bundles, with no observed
successor conflict.  The 36 effect-key return occurrences collapse to 15
geometric states and the six action returns to three.

The qualifier is decisive.  Strict-site and endpoint-collision roles disagree
inside 92 geometric classes, 575 classes merge multiple concrete endpoint
pairs, and the recorded lineage contains no singleton occupancy or new-line
birth edge.  It covers only 2,882 observed step/selected-word pairs, versus
12,537,146 words in the full domains.  Therefore this is a strong candidate
promotion coordinate, not a universal automaton.  Its compact certificate is
`design/x-axis-core-promotion-probe-summary.json`.

The full-domain follow-up is now complete.  Across all 12,537,146 words,
`design/x_axis_universal_bellman.py` scans 55,513,526 ordered slots and
deduplicates them only after retaining source step, child step, and exact
lateral prefix control.  The result has 236,572 edges.  An outward-rational
Bellman solve converges in 62 iterations, all edges have certified positive
postfixed slack, and none has zero slack.

The exact promoted integer core contains 53,216 states, 327--631 per step,
with coordinate box bound 15 and no interval fringe.  All 6,288 candidate-site
lateral classes lie inside it and none is exterior.  This is universal over
every action in the pinned domains for the synchronized carried x-line
channel, and it supplies the sharp finite realization of the phase-free
theorem above.

It still omits the decisive transitions: singleton occupancy, sequential
insertion births, collision provenance, and coexistence on one ordered path.
A chronological cursor jump to an unrelated anchor is also only a translation,
not the checked expanding recurrence, so an omitted far line can re-enter the
new frame immediately.  The next experiment is therefore occupancy/birth
closure together with a bounded ordered/tile cursor interface.  The compact
certificate is `design/x-axis-universal-bellman-summary.json`.

That first occupancy experiment is now complete, with an adverse verdict for
literal finite-state enumeration.  `design/x_axis_occupancy_birth_probe.py`
reconstructs 564 exact prefix occupancies over the 42 L7 and 146 L8 target gaps
for the recorded gate and pipeline schedules and for a counterfactual
left-to-right replay of the same pinned words.  It sequentially inserts the
selected connector points, asserts exact collisions and active-line hits, and
finds nine genuine transitions from a one-point fibre to a two-point
x-parallel secant.

For every one of 438 L7-to-L8 edge/schedule records, the target prefix is
exactly decomposed into transported source prefix, source action, late parent
completion, and prior child insertions.  There are zero transport or total
mismatches.  Late parent completion is nonempty in 73 gate, 67 pipeline, and
66 left-to-right records, while prior child insertions are nonempty in 128,
132, and all 146 respectively.  The bounded left-to-right cursor therefore
reduces one injection channel but does not eliminate chronological imports.

The proposed raw state does not stabilize on this finite horizon.  Every one
of the 126 L7 source/schedule full occupancy masks is unique already at
ancestry depth zero and path-window radius zero.  Conversely, retaining only
two-point active lines merges the states to 76 classes but yields two exact
state/action classes with different observed successors.  A radius-one path
window merely separates all 126 observations again.  These are finite
falsifiers of the literal-state and active-line-only quotients, not a proof
that no antichain, BDD, or birth-shell summary can close.  The compact
certificate is `design/x-axis-occupancy-birth-probe-summary.json`.

## Exact unrelated-cursor x-core injection census (2026-07-18)

`design/x_axis_cursor_jump_injection.py` closes the chronological channel that
the synchronized Bellman recurrence deliberately omits.  For consecutive
cursors in the recorded gate, inherited-tile pipeline, and left-to-right
orders, it inserts the predecessor word and projects the full placed inventory
onto the successor's exact promoted x-core.  The run checks 393,279 L5--L8
transitions and 189,394,231 successor-core cells, decomposing imported points
and active lines by birth, endpoint role, tile owner, and base-three address
shell.

The strongest tested key retains the exact lateral cursor translation, the
complete local/tile descriptors on both sides, signed tile jump, and every
capped `0/1/2` occupancy cell in the predecessor core.  It still fails
transition congruence.  Gate has 1,495 repeated classes and 1,140
noncongruent ones; pipeline has 3,149 and 2,736; left-to-right has 2,198 and
1,072.  Cross-level disagreements number 657, 1,608, and 641.  The maximum
number of distinct injected targets in one class is 14, 31, and 15.  Mod-81
phase refinement makes almost every state a singleton and still leaves nine
pipeline and four left-to-right noncongruences.

Reordering helps quantitatively without curing the state defect.  Injected
active x-lines total 11,610 for gate, 7,366 for pipeline, and 2,308 for
left-to-right.  Their maximum lateral jump is 20,318, 63, and eight
respectively, so bounded observed cursor motion alone is not enough.  Remote
occupancy and line births outside the predecessor core can enter the successor
core with different masks even when the tested local inventory and motion
agree.  This requires a correlated birth/address-shell import state or a
separate ranked tail lemma.

The census is exact for the three realized L5--L8 paths and refutes the tested
finite keys.  It is not a theorem that no other finite quotient exists, nor a
uniform tail bound or availability certificate.  The compact artifact is
`design/x-axis-cursor-jump-injection-summary.json`.

## Exact no-new-x-line alternate L5 (2026-07-18)

The x-channel can be simplified by forbidding connector points from entering
an already occupied yz fibre.  This condition must be enforced against the
whole current walk, not a local corridor: two points with the same yz
projection define an x-parallel secant regardless of their x coordinates.
`design/no_new_x_line_constructor.py` tests that policy on a coherent alternate
construction.  It begins with the pinned L4 anchors, follows the fragile-first
schedule, and chooses the first full-domain word whose interior projections
are mutually distinct and globally fresh and which is exactly legal against
the complete alternate prefix in three dimensions.

The selector completes all 2,457 L5 stitches and yields 8,260 triple-free
points.  The L4 anchor skeleton has 31 doubled yz fibres; the completed walk
has exactly the same 31, so no new x-parallel line is born.  Independent runs
are byte-identical.  Selected word lengths are 50 of length two, 1,469 of
length three, and 938 of length four.  The first domain word works at 1,160
stitches and the median first-survivor ordinal is two.  The hardest stitch
rejects 234 words by projection and exactly tests 2,221 projection-clean words
through its first survivor, at ordinal 2,455 of 6,736.

This result is deliberately narrower than an availability theorem.  The
smallest effective domain has 2,570 words, but only the first joint survivor
was sought, so the certified survivor count is merely one.  It does not cover
an audited L6 completion, alternate histories, or any non-x direction.  A
resumable L6 construction has selected all 8,259 stitches and committed a
28,737-point set with no new doubled yz fibre, but its independent
first-survivor replay and ordered-chain audit are still running; no terminal
certificate is asserted here.  Moreover, the 31 inherited
fibres cannot be removed by later connector choices because the lateral block
of the scale-and-rotate map is injective.  True x-channel elimination would
require beginning from a yz-injective seed and preserving freshness at every
level.  The compact certificate is
`design/no-new-x-line-constructor-summary.json`.

There is nevertheless a useful exact symbolic fact for policies that retain
x occupancies.  Order each capped occupancy map cellwise by `0<1<2`.  Word
legality in the x channel is downward closed, so checking the componentwise
maximal members of a correlated family is exactly equivalent to checking the
whole family.  The four-way prefix/action/late-parent/prior-child update is a
monotone two-threshold Boolean circuit.  This licenses antichain or BDD
compression, but does not license taking a cellwise join or a Cartesian
product of marginal histories.  A same-level finite moving window also cannot
close around a control cycle with nonzero physical drift without a separate
import oracle.  The missing step is therefore a correlated cursor-import
relation, not merely a larger local halo.

## Exact selected-horizon L9 age-two audit (2026-07-18)

`design/l9_anchor_age2_precursor.py` promotes the three tagged L7 connector
points through the actual `42 -> 146 -> 488` selected lineage and tests their
effect on 90 pending L9 domains against the complete 311,738-point L9 anchor
skeleton.  The domains contain 8,530,195 words in total, and all anchors are
eligible partners without an endpoint or distance cutoff.

Fifty-eight of 488 lineage states have nonzero tagged poison.  Thirty-nine
come from old--old source roles and 19 from the prior old--new source role.
Across distinct corridors the direct channel kills 4,130 word occurrences,
anchor-partner joins kill 219,776, and their exact union kills 223,786.
Partners born at L6, L7, and L8 all contribute.  An independent raw replay of
the largest 501,044-word domain exactly reproduces its 113,998-word positive
union.  Literal age-two incidence-inertness is therefore false.

The smallest residual under this tagged component is 2,413 / 2,570 words, but
it is not an availability floor.  The computation has not inserted any L9
connector interiors, so it omits their endpoint joins, the rest of the old
frontier, alternate connector histories, and the combined legality mask.
`design/l9_age2_transition_stabilization.py` also finds no useful finite-state
stabilization: the exact birth-mask and partner-identity refinements make every
one of the 58 nonzero states a singleton, while two repeated enriched L7-parent
classes remain noncongruent.  This is an exact obstruction and design trace,
not a contraction or transition quotient.  The compact certificates are
`design/l9-anchor-age2-precursor-summary.json` and
`design/l9-age2-transition-stabilization-summary.json`.

## Exact future-compatibility and translation CEGAR (2026-07-18)

`design/far_secant_future_compatibility_probe.py` retains two physical source
tokens, their actual L7/L8 connector choices, joint endpoint birth addresses,
and ordered child slots on the realized `42 -> 146 -> 488` tree.  It exactly
rescans 151 L8 step atoms over 3,751,509 words and reproduces every aggregate
channel.  This is a finite physical-token probe, not an all-line or all-action
closure.

The strongest witness has the same tested zero current mask,
birth/owner-shell key, and recorded word `[120,114,109]` in two L8 histories.
At the next slot one history has a near--deep site atom killing exactly 3,998
of 453,015 words; the other has zero.  The exact translation audit identifies
the difference.  With prefix `c=(2,2,-1)` and candidate site `(2,3,5)`, the
parent ghost is `(8/3,10/3,-2)`.  One tagged endpoint/partner line has zero
centred Pluecker residual there; the other has nonzero residual.

A one-bit exact-zero refinement separates that mask witness but is tied to
the observed query.  Exact centred endpoint, partner, direction, and moment
are sound for the token and make all 146 tested L8 states singleton.  The
result therefore identifies the missing geometry without demonstrating a
finite right congruence.  Compact certificates are
`design/far-secant-future-compatibility-probe-summary.json` and
`design/far-secant-translation-cegar-summary.json`.

## Exact non-x degenerate graph and all-iterate obstruction (2026-07-18)

The full-domain non-x scan checks all 12,537,146 words and 55,513,526 slots.
Its 34,520 candidate states have 4,774,988 direction-blind edges.  Requiring
an exact witness word whose full interior avoids the carried site removes only
56: the x-avoiding graph still has 4,774,932 edges and the same SCC structure,
namely 33,752 singletons and one cyclic component of size 768.

The canonical compatible two-cycle alternates the exact words
`[15,1,20,71]` and `[20,71,1,15]` at step type 1.  Both carry every line
through their listed sites and omit the carried site.  More strongly, for

```text
J(r,y,z)=(3y^2-yz+3z^2)/r^2,
```

the reveal direction `(3,-1,3)` has `J=11/3`, while the six selected-word
interior displacements have values `17/9,3,5,5,3,3`.  Since `J` is invariant
under forward and inverse projective transport, no iterate can meet a selected
interior.  The fixed-label carried-line countdown is clean for every cycle
count, superseding the finite 256-cycle check.  The inverse integer directions
`canonprim(N^(2n)(3,-1,3))` consequently have pairwise different reveal times
and infinitely many abstract line-effect right languages on this geometric
cycle.

This is not a realized-path counterexample.  It does not prove those inverse
directions are born as secants at the interface, nor that the two words are
globally legal and repeatable in one correlated ordered history.  It does
prove that the union of all menu actions cannot support the proposed strict
non-x lifetime rank.  A successful policy must exclude the recurrent action
cycle or prove its secant births unreachable.  The exact artifacts are
`design/nonx-degenerate-site-graph-summary.json`,
`design/nonx-cycle-invariant-certificate-summary.json`, and
`design/GHOST-LANGUAGE-AUTOMATON.md`.

Two bounded policy tests show that this repair is not empty.  An exact scan of
all selected L5--L8 connectors finds zero occurrences of either cycle word,
zero exact cycle macro edges, and no `n>=1` inverse-family entry secant among
630 chronological queries.  One `n=0` reveal secant occurs at L8 gap 43,702,
but the actual word `(20,21,5)` realizes neither edge.  Thus the named cycle is
absent from this one recorded history, not universally unreachable.

Independently, selecting the first intrinsically projection-clean fixed word
for each of the 124 step types leaves 34,520 vertices but only 1,321
direction-blind edges.  The graph is a DAG with an exact decreasing potential
of height two, giving a conditional continuous-effect bound of 250,742.  The
step-1 word `[5,20,21]` breaks the canonical cycle.  Exact chronological L5
replay shows that this parent-step-only policy is nevertheless false: its
step-20 word succeeds at gap 0 and fails at the immediately following scheduled
gap 2, where the first interior `(-14,6,16)` lies on the secant through
`(-6,6,8)` and `(-12,6,14)`.  The next action-filter CEGAR must retain many
words obeying the common acyclic potential and choose among them using actual
occupancy and full near/far poison.  Compact artifacts are
`design/nonx-cycle-realized-reachability-summary.json` and
`design/nonx-fixed-word-policy-probe-summary.json`, with the counterexample in
`design/fixed-policy-chronological-replay-summary.json`.

There is also an exact far-state obstruction **inside** those fixed actions.
The phase cycle `8 -> 16 -> 8` admits integer lattice lines `L_n` whose full
214-site masks at both phases are empty for `n` cycles and which then return to
the selected step-8 interior `(-2,-2,-2)`.  A projective quadratic invariant
proves the silence for every `n`, rather than extrapolating the 64-cycle replay.
Therefore the height-two potential controls only continuously effectful
candidate-to-candidate chains; it cannot replace exact direction/moment data
during a zero-mask interval.  No `L_n` is proved to be born from two placed
points in a globally legal path, so the remaining availability-grade target is
a reachable-birth exclusion or a quantitative first-return/tail envelope.  See
`design/LATENT-REENTRY-OBSTRUCTION.md` and
`design/nonx-latent-reentry-certificate-summary.json`.

## Exact x-projection coset reduction (2026-07-18)

For `B=[[0,-3],[3,-1]]`, the quotient `Z^2/BZ^2` is cyclic of order nine with
coordinate `q(y,z)=y-3z mod 9`.  Every connector prefix has a unique coarse
parent address and digit.  Equality of child yz fibres is exactly equality of
these complete addresses, so only the masks of the actual selected connector
words coexist.  For length-at-most-five domains, same-fibre conflicts pull
back to a parent Chebyshev radius at most seven.  New x-line avoidance is
therefore a finite-range projection CSP, not a far-tail problem.  The exact
full-cache scan sharpens the radius to five and finds 216,322 step-specific
unordered role masks.  Of 12,537,146 words, 6,755,766 have nonzero,
pairwise-distinct interior digits, and every step type has at least 2,000 such
words.  These are menu counts, not globally legal survivor counts.

This theorem is not availability.  A static radius-two cage occupying 25 yz
fibres kills the first interior of every connector word, even though generic x
coordinates can make the cage triple-free.  Reachability of that cage is not
claimed.  The remaining x obligation is a finite local safety/extension
theorem with future-gap capacity, not merely bounded projection multiplicity.

## Lattice-envelope action filters, chronological replay, and short-word no-go (2026-07-18)

The first multi-action repair of the height-two fixed-word pilot is now
falsified exactly.  The old common-potential scan retains 601 words across the
124 step types and eight words for the repeated step-20 corridor at L5 gaps 0
and 2.  All eight are legal at gap 0.  The correlated `8 x 8` continuation
matrix is nevertheless empty: every one of its 64 gap-2 entries is exactly
illegal, and anchor-only witnesses already cover all eight possible gap-2
responses.  Hence lookahead among those eight first choices cannot save that
specific common-potential region.  This does not rule out a different or
state-dependent action filter.

The exact lattice-envelope replacement starts from the necessary and
sufficient congruence description of `M Z^3` and its 780 candidate states.
Across all 12,537,146 domain words it retains 8,367,038 words whose exact
`T`-source effects are covered by their own interiors, and 10,252,458 words
whose surviving `T`-source edges follow one common strict order.  Both
whole-word arbitrary-switching unions are acyclic, and every parent step
retains words.  This is a finite theorem about contiguous direction-blind
candidate chains with the actual slots of each word kept correlated.  It is
not a chronological survivor bound and says nothing about silent zero-mask
lines, nondegenerate selector changes, newly born secants, unrelated-cursor
imports, or the union with all other global poison channels.

A chronological construction using the stricter zero-envelope channel and
requiring every proper interior to occupy a globally unused `(y,z)` fibre has
completed all 2,457 L5 stitches.  Its pinned checkpoint contains 8,268 placed
points.  The corrected independent checker rescanned every cache ordinal
through each stored winner, verified fast/reference agreement, and completed
the all-prior-direction scan of the natural-order chain.  The sealed summary
is `design/lattice-T-chronological-L5-summary.json`.  This is therefore an
exact terminal finite certificate, but not an all-level availability theorem.

A direction-only attempt to remove the two known latent spectra fails at the
inherited seed.  The exact pair-order census stops at its first witness after
559 pairs: seed anchors 30 and 33 have primitive direction `(3,-3,1)` and
`J=11/3`.  Thus `{11/3,348/275}` cannot simply be forbidden for every secant;
any such policy must promote exact inherited Pluecker lines or use a finer
moment-sensitive condition.  The result is in
`design/lattice-T-projective-spectrum-census-summary.json`.

The complete moment-aware diagnostic subsequently tested all `34,175,778`
unordered pairs.  It found 758 cone secants and 76 secants on the named exact
macro-direction rays; 61 of those 76 were born when a connector interior was
inserted, rather than inherited from the seed.  Hence the audited L5 orbit
does not satisfy a no-new-named-ray invariant either.  The 758 exact affine
Pluecker lines all have multiplicity one, as independently forced by the
no-three-collinear audit.  For the 246 inherited-seed cone lines, an exact
moment join against 352 actual L5 and 2,052 induced-L6 phase-line roles has
zero matches.  That finite zero does not cover the connector-born lines or a
two-edge cycle through selected L6 connector actions, which did not yet exist
when the diagnostic was frozen.  The compact certificate is
`design/lattice-T-projective-spectrum-diagnostic-summary.json`.  A
grandfathered-base/no-new-cone-birth controller remains a testable proposal;
its survivor condition and completeness for all latent families are open.

Restricting the substitution to short connectors does not provide an easier
closed system.  Independent forward and reverse enumerations reproduce 552
legal length-2 and 56,516 legal length-3 words.  The exact length-3 closure is
empty, and even the union of lengths 2 and 3 has empty greatest fixed point
after nine synchronous pruning rounds:

```text
124 -> 104 -> 84 -> 70 -> 56 -> 36 -> 20 -> 10 -> 2 -> 0.
```

Every finite selected substitution has a sink recurrent component, so any
closed policy here must use at least one length-4 or length-5 word in each such
core.  This does not exclude a mixed-length incidence matrix with
Perron--Frobenius growth exactly 3; that separate constrained search is open.

The zero-ghost obstruction is now quantitative.  The latent family has
primitive lattice spacing exactly scaled by `9^n` and returns after `n` phase
cycles with a killed-word fraction at least `1/15920`, independent of `n`.
For any one finite level, bounded diameter therefore gives a deterministic
maximum possible `n`; as level diameter grows, that cutoff grows too, so it is
not a uniform tail lemma.  The exact birth operator records connector
endpoints, every old--new and new--new line, carried old lines, and any
unrelated-cursor import.  A weighted LLL or a mask-valued shell transfer may
still be built on this operator, but at present neither route supplies a
uniform reachable-birth moment, an inductively closed transfer, or a positive
connector-survivor bound.  They are proof proposals, not completed lemmas.

The sealed generic ghost-transfer census now excludes a role-only contraction
shortcut.  In both frozen action channels, every accepted whole word has two
to five child roles.  The exact all-descendant first-moment kernels therefore
satisfy `2 <= rho <= 5`; no common positive weighted norm contracts them below
one.  By contrast, the continuously effectful 780-state lattice-`T` channel
has zero edges for the strict envelope and an ordered nilpotent kernel of
exponent at most 218.  This useful finite rank does not transport silent
Pluecker lines, charge old--new/new--new births, bound history-dependent
legality conditioning, or pay for unrelated cursor imports.  The exact
whole-word correlation commitments and these limitations are sealed in
`design/generic-ghost-transfer-census-summary.json`.

One exact owner-frame census now splits geometric poison by current distance
shell and L5 construction-rank cohort at a deterministically selected late
L5 stitch and its four actual ordered child corridors.  At the L5 parent,
the complete 16,392-word domain has 8,525 geometric survivors; far-only
witnesses kill 3,470 words that the radius-40 part does not.  The four
induced-L6 anchor-only frames have respectively
`13,836/15,920`, `6,232/6,736`, `1,694/2,570`, and `5,585/6,736`
survivors, with far-only kills `958,209,661,813`.  All endpoints and all three
external legality channels were scanned with no cutoff, and overlap was taken
by bitwise OR rather than summing witnesses.

This is deliberately labelled an **external-geometric owner-frame census**,
not a birth-transfer certificate.  Its L6 frames contain only the 8,268
scaled anchors, not earlier chronological L6 connector interiors; lower-level
births are collapsed into a seed cohort; terminal masks are counts plus hash
commitments rather than reconstructable bitsets; and the survivor counts are
not intersected with zero-`T` and fresh-yz policy masks.  The sealed v1 result
is `design/lattice-T-L5-L6-birth-shell-mask-summary.json`.  A fail-closed v2
must wait for a terminal independently audited L6 construction, then restore
the actual inverse-schedule prefixes, raw masks, recursive provenance, and
both ancestry and chronological transitions.

Canonical compact artifacts are
`design/potential-policy-two-stitch-matrix-summary.json`,
`design/nonx-lattice-envelope-action-probe-summary.json`,
`design/exact-length3-gfp-summary.json`, and
`design/FAR-SECANT-BIRTH-OPERATOR.md`.  The completed construction source is
`/tmp/lattice-T-chronological-L5-primary.json`; its repository audit checker is
`design/lattice_t_chronological_audit.py`; its sealed terminal summary is
`design/lattice-T-chronological-L5-summary.json`.

## Guarded recurrent families, short-return holonomy, and paused L6 audits (2026-07-18)

The first no-new-recurrent-family controller has a complete independent finite
certificate.  The guarded L5 construction starts with the exact 2,458-anchor
L4 skeleton, promotes its 246 existing affine lines on the two invariant cones
`J=11/3` and `J=348/275`, and rejects every otherwise legal connector that
would create another old--new or same-word new--new cone secant.  It completed
all 2,457 stitches.  The independent auditor rescanned every cache ordinal
through the stored winner, reproduced all 4,211 cone rejections, and checked
all 34,407,660 terminal pairs of the resulting 8,296-point path.  There are no
triples and no connector-involving target-cone pairs; the only 246 matches are
the inherited anchor--anchor pairs.  This is an exact finite validation of the
grandfathered-cone lemma, not evidence that the two cones exhaust recurrent
far lines.

A separate guarded L6 run starts from the ordinary independently audited
8,268-point primary L5 path, not from that guarded-L5 experiment.  It is paused
at 6,348 / 8,267 stitches with no obstruction.  Consequently the two positive
guard computations must not be presented as consecutive levels of one
realized guarded path.  Its independently reviewed auditor is fail-closed
until terminal constructor pins exist.

The exact short-return calculation explains why a finite two-cone claim would
be premature.  Preserving every accepted whole word, slot, prefix control, and
the correlated `8 -> 16 -> 8` role pair produces 746,496 exact pairs, 3,136
distinct affine return maps, and 2,094 fixed points.  Full-candidate reveals
produce 47,946 primitive guard polynomials, of which 47,942 are outside
`F11`, `F348`, the x-axis class, and the lateral-plane class.  A displayed
two-loop composition gives infinitely many exact affine fixed points.  The
census proves only an algebraic action-channel spectrum: it does not prove an
integral placed secant, chronological birth, repeatable legal controls, or a
connector kill.

The role-first follow-up is therefore intentionally line- and chronology-first.
It filters the abstract holonomy records through actual selected L5 words and
their actual L6 child gaps, then requires an exact physical secant birth,
Pluecker-moment compatibility, transported candidate incidence, and a raw
killed-word mask.  It explicitly rejects the unrelated guarded-L5 lineage and
is locked until the primary L6 audit is terminal.

The primary L6 constructor itself has completed all 8,267 stitches and placed
28,665 points.  Its independent first-survivor replay is complete with no
discrepancy; the natural-order all-pairs verifier is paused at point
8,233 / 28,665 after 33,887,028 checked pairs.  The reviewed birth-shell v2 is
now honestly scoped as a five-corridor census: it recomputes one exact L5
parent mask and four chronological L6 child masks, including same-corridor
before/after placement scans.  It does not claim a repeated-state quotient or
contraction.  A separate poison-blind matched-transition experiment is
prepared to select repeated ordered-factor/action classes before examining
their masks, then test exact source/successor congruence without accepting
singleton stabilization.  Static review required its source and successor
classes to use the identical full `(theta, F, actual_action)` key; it remains
unexecuted and fail-closed behind pending terminal/manifest pins.

All resume hashes and the fact that no proof job was left running are recorded
in `design/PAUSE-STATE-2026-07-18.md`.  The unconditional gap remains the same:
every reachable old--new/new--new birth and cursor import must be promoted or
strictly ranked, and the resulting exact mask union must retain a legal word
inside a successor-closed greatest fixed point.
