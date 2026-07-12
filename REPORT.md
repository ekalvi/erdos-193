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

## Next steps suggested by the data
1. Finish the deep DFS bounds (running); try iterated-greedy/beam search to push the
   4-step lower bound well past 206 and look for self-similar structure in the
   record walks (the "finite certificate" idea from the programme notes).
2. Move the search class from primitive substitutions to S-adic sequences with
   slowly-growing directive complexity — the only substitutive-like class not
   killed by the PF-contraction argument.
3. Literature check: exact maxima (20 for ±eᵢ), and whether the PF-contraction
   observation about return displacements is already recorded.
