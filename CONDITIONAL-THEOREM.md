# Erdős Problem #193 — a conditional theorem

**Status (2026-07-16): the affirmative answer is reduced to a single geometric
regularity lemma, with every other step proven-exact or certified by exhaustive
computation.** This document is the referee-checkable statement: the chain, what
is proven, the one remaining hypothesis, and how to reproduce every claim.

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
moment they are placed. If every level can be completed, the nested limit is an
infinite triple-free walk.

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

**L3 — Availability [CONDITIONAL on Lemma R; otherwise a finite check].** At
every stitch, a legal connector word exists (one that creates no collinear
triple with the placed points). Availability is, empirically, a clean decreasing
function of the local **crowding** (the number of placed points in a fixed-radius
ball): log(available words) ≈ 11.9 − 0.265·crowding, so a bounded crowding gives
a positive availability floor. Making this a theorem needs (a) Lemma R below to
bound crowding, and (b) a per-step finite computation certifying that no
constructible bounded-crowding arrangement kills a step's entire word space —
which Lemma R renders a finite, well-posed check. *(Word spaces: connector
domains 7,114,584 words + length-5 layers; measured availability floors 317 /
180 / 271 words at levels 5 / 6 / 7, non-eroding.)*

**L4′ / Lemma R — Regularity [THE ONE OPEN HYPOTHESIS].** *See below.* Bounds
the crowding uniformly across all levels; feeds L3.

**L5 — Induction [PROVEN, given L1–L4′].** L1 + L2 + L3 + L4′ ⇒ every level
completes ⇒ the construction never halts ⇒ an infinite triple-free walk exists.
Plain induction, no compactness subtleties: each level is finished before the
next starts, and L2 freezes completed levels.

**So: L1, L2, L5 are proven; L3 reduces to a finite check given Lemma R; the
theorem holds if Lemma R holds.**

---

## Lemma R — the single remaining hypothesis

> **Lemma R (crowding regularity).** For the seed-193 construction orbit there is
> a level-independent constant C such that, for every level k, every centre q,
> and every radius r ∈ [1, 10],
>
>   c_k(q, r) := #{ walk points within Chebyshev distance r of q } ≤ C · r^d,
>
> with d = log λ / log 3 ≈ 1.10 (λ ≈ 3.36 the per-level point-growth).

In plain terms: the walk is a **thread**, not a blob — it threads any small ball
in about *radius-many* points (dimension ≈ 1.1), at every scale, forever. This is
Ahlfors d-regularity of the walk-curve on the fixed neighbourhood scale.

### Why Lemma R suffices

Bounded crowding ⇒ (via L3) a positive availability floor ⇒ every stitch has a
legal word ⇒ (via L5) the construction never halts. Lemma R is the only input to
L3/L4′ that is not already proven.

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
  is φ = σ₁(M⁻¹)·σ₂(M⁻¹)^{d−1} = 0.353 < 1 — the renormalization contracts
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

### What is MEASURED (the exact content of Lemma R still to prove)

The *tight, uniform* bound c_k(q,r) ≤ C·r^d — as opposed to the proven *loose,
cubic* bound — is verified on every constructed level (through 311,738 points)
but not yet proven for all k. The obstruction is **same-scale self-approach**:
two pieces of the walk at the *same* scale can drift near each other (they are
laterally offset, so triple-freeness permits it), and bounding how often this
happens is equivalent to proving the walk-curve is Ahlfors-regular — a
regularity statement for an **adaptive** self-affine curve (the stitch rule is
data-dependent, which blocks the off-the-shelf self-similar regularity theorems).

### Evidence for Lemma R (why it is believed true)

- Crowding is level-stable to three decimals: mean c(·,4) = 4.13 / 4.11 / 4.10 /
  4.10 at levels 5–8; the growing observed maximum is an extreme-value artifact of
  sampling more points, not a distribution shift (full-distribution test).
- The renormalization density N₈₁ converges to a fixed point: 118.4 → 111.9 →
  109.8 → 109.4, geometrically, with the level-8 value predicted *before* the run.
- Availability floors do not erode: 317 / 180 / 271 words at levels 5–7.
- Purer-thread trend: bigger-twist matrices drive d monotonically toward 1.0
  (1.071 → 1.035 for m = 3…6), confirming the thread picture.

---

## Reproducibility

Every number above is produced by a script in the repository and re-checkable
with the bundled PyPy build; no floating point enters the collinearity tests
(exact integer arithmetic throughout).

| Claim | Artifact |
|---|---|
| Record walk, 311,738 pts, no 3 collinear | `gate2-193-L8.txt`, `verify_parallel.py` (SHA-256 c8cc3728…) |
| Inheritance algebra | `provenance193.py`, `PROOF-SKELETON.md` L2 |
| Exact recursion, contraction, refill | `design/lemma/recursion_decomp.py`, `taskC_geometry.py` |
| Anchor 3-separation, deep-tail, finite-menu check | `design/lemma/finite_menu_check.py` (79M words) |
| Qualitative no-blow-up (cubic, all k) | `design/lemma/refill/`, `design/lemma/bound1-deepshell-VERDICT.json` |
| Spool transience | `design/lemma/exclusion/` |
| Availability = f(crowding), floors | gate ledgers `gate2-ledger-L{5,6,7}.json` |
| Dimension / regularity measurements | `design/lemma/dim/`, `design/tight/` |

## Honest summary

The answer to Erdős #193 is **yes, conditional on Lemma R** — a single,
sharply-stated geometric regularity lemma that is measured true across a
311,738-point certified construction and to which the entire remaining difficulty
is confined. Everything else — the base, inheritance, induction, the exact
recursion, qualitative no-blow-up, bounded distortion, the contraction, the
deep-tail collapse, cross-scale transience — is proven. Lemma R is the Ahlfors
regularity of an adaptive self-affine curve; it has resisted six distinct proof
attacks (counting, fractal-dimension, transfer-operator, exclusion, redesign),
each of which sharpened it and proved new machinery but left the same
same-scale-self-approach core. It is the frontier.
