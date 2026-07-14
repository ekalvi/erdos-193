# Proof skeleton — Problem #193, affirmative answer

Status legend: [PROVEN] machine-verified or exact algebra · [MEASURED] holds with
margin on certified instances, needs promotion to all-instances theorem ·
[ROUTE] argument type identified, not yet written.

## Theorem (target)
There exists a finite set S ⊂ ℤ³ (|S| = 124, coordinates in ±2) and an infinite
sequence of steps from S whose walk contains no three collinear points.

## Chain

**L1 (Base) [PROVEN].** A triple-free walk W₀ exists (verified instances up to
28,271 steps; SHA-256 certified; standalone verifier).

**L2 (Inheritance) [PROVEN].** For the expansion matrix M (det 27, Smith 1/3/9,
irrational twist), Ω(Mx,My,Mz) = cof(M)·Ω(x,y,z) with cof(M) invertible over ℚ.
Hence any triple non-collinear at its creation-complete level remains
non-collinear at all later levels. Verified exactly on millions of real triples;
the algebra is three lines. (Hostile-panel confirmed, 2026-07-13.)

**L3 (Per-level existence) [MEASURED → to prove].**
Claim: given any walk the construction can reach, every segment admits a stitch
word that (a) avoids all lines through two existing points, (b) tolerates the
placements of earlier segments in the level, (c) inflicts at most 3× average
damage on later segments, and (d) avoids triple-newborn alignments.
Measured budget on certified instances: 0.317 + 0.10 + 0.333 + 0.028 ≈ 0.78 < 1.
Argument type: counting + averaging (Markov) over the word distribution; needs a
precise probability-space statement and a pointwise (not in-expectation)
simultaneity argument.
Known risk: the constants are instance-measurements; promotion needs L4.

**L4 (Scale-invariance of the ledger) [MEASURED → to prove].**
Claim: the L3 budget stays below 1 at every level.
Evidence: fatal mass flat (0.31–0.34) across levels 3–6; shell decomposition
(2026-07-14) shows the mass is LOCAL — 79% from contributors within distance 27,
91% within 81, decaying ~2× per 3-shell, ~0 beyond 3⁶.
Argument route: (i) local lemma — the distribution of walk geometry within a
bounded collar of a segment is level-invariant (construction recursion: a
segment's neighborhood at level k+1 is the M-image of a level-k neighborhood
plus bounded stitching); (ii) far-field lemma — contributions beyond the collar
are summably small (measured geometric decay; candidate mechanism: exact lattice
incidence thinning, related to the measured κ-statistics).

**L5 (Induction) [ROUTE].** L1 + L2 + L3 + L4 ⇒ the construction never halts ⇒
an infinite triple-free walk exists. Plain induction; no compactness subtleties
because each level is completed before the next begins and inheritance freezes
completed levels.

## Honest gaps, ranked
1. L4(i): state and prove the neighborhood-invariance lemma from the recursion.
2. L3: pointwise simultaneity of constraints (a)–(d) — the averaging argument
   gives existence in a mass sense; write it so a referee sees a single word
   satisfying all four.
3. L4(ii): far-field summability — measured decay must become a bound.
4. All constants are for THIS menu/matrix; the theorem is existential, so that
   is fine — but every lemma must be stated for this fixed (S, M).
5. Independent human review after the above.
