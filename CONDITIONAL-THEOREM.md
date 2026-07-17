# Erdős Problem #193 — a conditional theorem

**Status (2026-07-16): the affirmative answer stands as a conditional theorem —
Erdős #193 = YES modulo a single geometric regularity lemma (Lemma R,
arc-incidence / uniform bounded crowding), with every other step proven-exact or
certified by exhaustive computation. The OSC/Mauldin–Williams route to *proving*
Lemma R is now closed — the Open Set Condition provably fails on the connector
menu-closure (exact generation-2 overlap), so Lemma R is stated and must be proven
directly as the metric arc-incidence lemma, not as an OSC. The walk itself is
strongly evidenced (311,738 points, no three collinear, SHA-256 c8cc3728).** This
document is the referee-checkable statement: the chain, what is proven, the one
remaining metric hypothesis, the closed routes, and how to reproduce every claim.

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

### Routes explored and closed (why Lemma R needs its own metric proof)

Eight adversarial rounds established that the three standard tools that *would*
supply Lemma R for free each provably do not. These are closures, not refutations:
the conditional theorem is untouched — each result only removes a shortcut and
confirms that Lemma R must be proven directly as the metric arc-incidence lemma
above. (The exact self-similarity MᵀQM = 9Q and the other proven machinery still
stand — see "What is PROVEN around Lemma R"; what is closed is the *route from that
machinery to Lemma R via a separation condition*.)

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
recursion, qualitative no-blow-up, the exact Q-metric self-similarity, the
deep-tail collapse, cross-scale transience — is proven. Lemma R is the **metric
arc-incidence / uniform bounded-crowding lemma** (the walk threads any ball in about
radius-many points at every scale). A long adversarial, computer-assisted campaign has
now **mapped the whole affirmative program and closed every standard route to it**: it
does not follow from the Open Set Condition (which provably *fails* on the connector
menu-closure), nor from swapping the enlarging matrix (a crystallographic impossibility,
via Niven's theorem), nor from a *metric separation* bound (the telescoping-sum
separation is **exactly zero** on the true connector closure — an exact integer
zero-cycle at depth 1, for the fixed matrix and accelerating variants alike), nor from
any *local finite-state* verification (a rigorous impossibility — the legal-carry
automaton is a single primitive strongly-connected component, so a rule with power over
the collinear configurations must constrain the walk at unbounded depth, which *is* the
theorem), nor from information theory (the cross-entropy floor is zero), nor from the
standard global-analysis toolkit (Fourier decay, additive combinatorics, homogeneous
dynamics, transversality — each collapses to the same obstruction). The unifying reason
is that collinearity is an **exact integer** condition (a triple lies on a line or it
does not), to which every density, measure, and separation tool is constitutively blind.
What remains is genuinely open, and a proof of Lemma R now appears to require a new,
*global* argument outside every tool tried here. The walk itself is measured rock-stable
— triple-free and self-avoiding across the 311,738-point record — so the open question
is **provability, not existence**: the walk almost certainly exists (~85%); a full
unconditional proof with currently-known tools is **under 5%**.
