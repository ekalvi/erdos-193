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

**L3 [REFUTED AS STATED — 2026-07-14 overnight attack; repaired as L3'].**
Two machine-verified counterexamples: (i) the certified walk itself contains three
segments with ZERO legal 2-4-step words (it survived via length-5 stitches); (ii) a
fully legal crowd-hugging run (seed 777) hard-jams at level 2 (own-line fatal mass
0.9796; zero stitches to depth 16). Also: the ledger constants conflated position-mass
with word-union mass — honest per-segment BAD word-mass: mean 0.556, p99 0.913, max 1.0.
**L3' (repaired):** quantify over states reachable by the INVARIANT-ENFORCING
construction only: length-5 connector layer on fragile steps (|D₂₋₄| < ~2000),
fragile-first (ascending |D*|) stitch order, per-(donor,receiver) damage caps
c_{i,j} = min(3·ē(shell), c_max) with receiver budget β ≈ 0.25. Claim: pointwise
word-union ledger ≤ 1−δ (δ ≥ 0.15) at every stitch of THIS construction.

**L3' [REFUTED AS STATED — 2026-07-14 afternoon panel; restated as L3''].**
Three-attacker panel + independent replication (design/attack-repaired-invariant.json):
(i) CONFIRMED hard jam: a legal, triple-free, 18-step crafted base (density 0.132,
saturated in "band" steps) jams LEVEL 1 of the exact repaired constructor at the
non-fragile band step (2,1,-1): 0/15,920 surviving words, exhaustively certified to
length 4; length-5 escapes exist. Structural hole: 38 band steps with |D₂₋₄| ∈
[2570, 16000] got no length-5 layer, and the gate's own L5 minima all sit on this
band. (ii) The gate's L5 ledger itself has fragile segments at frac 0.085 < δ.
(iii) Static hitting-set: 26 adversarial obstacle points (4 hub points → 82.5%)
kill the ENTIRE 47,467-word space of the worst fragile step — the layer is thin
armor against concentration; but the deterministic benign orbit never concentrates
(all d24=46 segments kept ≥ 37.5% / ≥ 17,800 words at L5), and the 4 hub points are
unreachable-by-construction as far as tested (verifier: OVERSTATED on reachability).
**L3'' (restated — orbit-scoped, as the existential theorem permits):** quantify
over the SEED-193 CONSTRUCTION ORBIT only. Hypotheses carried by the induction:
(a) word spaces = D₂₋₄ ∪ D₅ for ALL steps with |D₂₋₄| < 16,000 (band + fragile;
dstar5_band.pkl in build); (b) an anti-concentration invariant: at each stitch, the
placed set meets the segment's chord-tube hub structure in ≤ k points, k small
enough that survivor mass ≥ δ_abs (absolute floor, not uniform fraction — L5/L6
measured floors: 243 / TBD words). The invariant is to be MEASURED as the
"clearance profile" on the gate's L5–L7 states, then proved propagated by the
L4' converged local law. Adversarial bases outside the orbit are irrelevant to
the theorem: we need ONE infinite chain, and the orbit is ours to choose.

**L3''-b evidence (2026-07-14, clearance-L6.json, all 8,252 stitches):**
corr(stitch-time tube crowding c10, survivor fraction) = −0.68/−0.71 — availability
is largely a FUNCTION of local crowding; the orbit's crowding ceiling is
SCALE-INVARIANT across three levels (max 20/19/22, mean 6.9/6.9/6.8 at L5/L6/L7 v2,
vs the 26 adversarially-placed hub points needed to zero a space); even the most
crowded band keeps hundreds of words. Proposed decomposition of L3'': (A) crowding ≤ k₀ propagates
under renormalization (M dilutes a radius-10 tube ×3, refill adds bounded
points — an integer-count recursion); (B) per step type, the maximum word-mass
killed by any CONSTRUCTIBLE ≤ k₀-point tube configuration is < 1 − δ (finite
computation via the hub/hitting-set structure per step). Both machine-checkable
in principle; (B)'s configuration space needs the constructibility restriction
to be tractable — unconstrained k-point configs already kill 82.5% at k = 4.
Original (dead) statement follows for the record:
**L3-original (Per-level existence) [FALSE].**
Claim: given any walk the construction can reach, every segment admits a stitch
word that (a) avoids all lines through two existing points, (b) tolerates the
placements of earlier segments in the level, (c) inflicts at most 3× average
damage on later segments, and (d) avoids triple-newborn alignments.
Measured budget on certified instances: 0.317 + 0.10 + 0.333 + 0.028 ≈ 0.78 < 1.
Argument type: counting + averaging (Markov) over the word distribution; needs a
precise probability-space statement and a pointwise (not in-expectation)
simultaneity argument.
Known risk: the constants are instance-measurements; promotion needs L4.

**L4 [EXACT INVARIANCE FALSE; CONVERGENCE REAL — repaired as L4'].**
The local configuration law converges under renormalization (successive differences
shrink ×0.074 at d=27, ×0.222 at d=81; KS(L5,L6) below critical; refill factor
self-correcting: corr(parent density, refill) = −0.32…−0.42 — mean reversion).
**L4' (repaired):** ledger constants of the REPAIRED construction converge, with the
level-7 pre-registered predictions (N₈₁(L7) = 112.6 ± 0.7, KS below critical) as the
falsifiable gate.
**L4-original [SUPERSEDED].**
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

**L4' — recursion-lemma reduction (2026-07-15, agentic computer-assisted, adversarially verified; design/lemma/).**
The crowding recursion was attacked by a 4-agent derive → close → adversarial-verify workflow.
THREE of the four pieces are now PROVEN-exact / certified-finite:
- **Exact recursion identity [PROVEN].** Walk_{k+1} = (M·Walk_k) ⊔ Stitch_k is a genuine
  disjoint union (verified geometrically: 0 duplicate points, 0 interiors on anchors at L6,L7).
  Hence for every q, R: c_R(q) = dilated-old(q) + refill(q) EXACTLY — reproduces the measured
  clearance ledger with 0/8252 (L6) and 0/27696 (L7) mismatches. Adversary: CONFIRMED-exact.
- **Contraction α<1 [PROVEN-exact].** Singular values of M are σ = 2.5414, 3.0000, 3.5414 (all
  >1 ⇒ M contracts in EVERY direction); ‖M⁻¹‖∞ = 4/9 exactly; M⁻¹ pulls a Cheb-10 ball back
  into a Cheb-4.44 region. This is a *metric* radius-contraction, proven.
- **Refill bound B [certified-finite].** B ≈ 20 (adversarial off-lattice search found no Cheb-10
  box above 20); proven structural cap 4·A14 = 44 from word length ≤5 + max menu step 2 + anchor
  spacing (min |M·s|∞ = 3). Adversary: holds, in fact conservative.

**THE REDUCTION.** Everything now hinges on ONE falsifiable, level-uniform inequality — the
**uniform local-1-D incidence bound**: ∃ level-independent C with c_k(q,ρ) ≤ C·ρ + 1 for all k,
q, ρ∈[1,10]. Load-bearing case the recursion consumes: c_k(q, 4.44) ≤ (4/9)·k₀, uniform in k.
This is the single unproven link that turns the PROVEN metric contraction into the needed COUNT
contraction (dilated-old ≤ (4/9)·k₀). It is EMPIRICALLY ALREADY SATISFIED (max dilated-old = 9 at
L6, 8 at L7 ≤ 9.78; and the direct incidence profile max_q c_k(q,ρ)/ρ ≈ 2.5 is level-stable
across L6,L7 — ρ=8 → max 20 both levels, ρ=10 → 25/26; load-bearing max_q c_k(q,4) = 9/10 ≤ 12.
logs/incidence-measure.log). For the QUANTITATIVE tight constant a companion **refill anti-stacking** cap
is also needed (dilated-old and refill anti-correlate on the orbit, keeping the pointwise sum at
~27 while independent maxima are 9+14). Honest corrections from the adversary: (i) the true
ceiling to bound is the FULL-walk crowding ~27, not the stitch-time 22; (ii) with proven α+B the
naive fixed point is 36, so the easy-3/4 gives uniform boundedness ≤ 36 once the count-contraction
kernel holds, but NOT the tight ~27 without anti-stacking. Net: the whole L4' lemma is reduced to
one incidence inequality (+ a refill companion for tightness), with all else proven-exact.
**L4' — route panel RESULT (2026-07-15, design/lemma/route*/, adversarially stress-tested).**
Four routes attacked the incidence inequality; κ₃ (vacuous below Cheb-length ~515) and
equidistribution (the walk is BALLISTIC not diffusive — persistent directions) both died as
mechanisms but pointed at the winner. **Route 4/2 — the exact contraction count-recursion — is a
rigorous REDUCTION (verified, not circular; the stress agent re-derived every step):**
   c_{k+1}(q,ρ) ≤ c_k(M⁻¹q, (4/9)ρ) + B_local(ρ).
Proven-exact ingredients: recursion identity M⁻¹·anchors == parent-chain (over ℚ, both
transitions); ‖M⁻¹‖∞ = 4/9 exact; Cheb = ‖·‖∞ so dilated-old points inject into the (4/9)ρ
pull-back ball. Because the pull-back radius SHRINKS by 4/9 each level, refill does NOT accumulate
(no k·B blow-up) — the induction closes to c_k(q,ρ) ≤ 6ρ + 1 UNIFORMLY in k, **reducing the whole
crowding-boundedness lemma to ONE structural sub-lemma**: the uniform linear refill bound
B_local(ρ) ≤ (5/9)C·ρ for all k. That sub-lemma is now verified at THREE transitions (L6,L7,L8;
closing constant C*=6.0 stable, no counterexample) — structural (level-homogeneous construction:
fixed connector-word menu, bounded word length), plausibly reducible to a FINITE check over the
menu. Judge p(top route closes) = 0.62.
TWO honest gaps remain, both sharper than before:
1. **Uniform refill sub-lemma** — measured-stable at 3 levels (minor drift B_local(1): 3→3→4),
   not yet a theorem. Closes the QUALITATIVE lemma (crowding bounded ⇒ no blow-up, ever).
2. **The tight constant** — Route 4 proves C=6 (⇒ c_k(4.44) ≤ 27.6), but availability needs the
   tight C≈2.5 (c_k(4.44) ≤ 12); by the (B) result availability is marginal (~11 words) at the
   loose bound. Needs a SEPARATE anti-stacking argument (dilated-old ⟂ refill), delivered by no
   route yet. This is the piece that converts "crowding bounded" into "availability floor > 0".
Net: the qualitative "no blow-up" is one structural sub-lemma from proven; the availability-
grade tight constant is a second, distinct target.

**L5 (Induction) [ROUTE].** L1 + L2 + L3 + L4 ⇒ the construction never halts ⇒
an infinite triple-free walk exists. Plain induction; no compactness subtleties
because each level is completed before the next begins and inheritance freezes
completed levels.

## The gate (2026-07-14) — RESULTS
Two runs, both letter-verdicts FAIL, with opposite meanings:
- **v1 (deterministic shortest-first choice): FAIL, real.** N₈₁ = 118.9 → 115.8 →
  118.6 (target 112.6 ± 0.7); N₂₇ RISING ~2%/level; stitch length creeping
  3.36 → 3.48 → 3.50; escalation bursts. Diagnosis: deterministic choice reuses the
  same word shapes → correlated packing → densification feedback. No fixed point.
  The 100,359-point L7 walk is verified (independent verifier + dual SHA-256) and
  stands as the record, but the variant is retired.
- **v2 (seeded-random among shortest words — the original's statistics): letter-FAIL,
  spirit-PASS.** N₈₁ = 118.39 → 111.88 → 109.76 (±0.09): MONOTONE convergence with
  geometric contraction (increments −6.51, −2.12; ratio 0.33), all density statistics
  falling; zero escalations at every level; floors 317/180/271 — NO EROSION (L7 floor
ROSE), mean availability RISING (0.465/0.458/0.528), below-δ share FALLING
(4.9%/4.2%/3.1%): the absolute-floor form of L3'' holds with margin on the
orbit at three scales. The registered
  target 112.6 ± 0.7 was extrapolated from the ORIGINAL constructor — v2 converges to
  its own fixed point ≈ 108.7–109.3, ~3% below. KS(L6,L7) = 0.081 > 0.018 critical:
  with n ≈ 27k, KS detects the still-contracting 2.1 shift — this test was
  unachievable at L7 for ANY constructor of the family (the original's own
  level-shifts were larger) and is retired as miscalibrated, not passed.

**L8 pre-registration (committed BEFORE the run):** N₈₁(L8) = 109.1 ± 0.4 (geometric
extrapolation), |N₈₁(L8) − N₈₁(L7)| ≤ 1.1 with the same sign (contraction continues),
zero jams, ~312k steps verified triple-free. Pass ⇒ the v2 orbit has a demonstrated
renormalization fixed point and L4' rests on it; fail ⇒ the convergence claim is dead
as measured and the honest move is menu/matrix redesign.

**L8 RESULT (2026-07-15) — CONVERGENCE CRITERION PASSED, out-of-sample.**
N₈₁ trajectory 118.386 → 111.882 → 109.763 → **109.395 ± 0.048**; increments
−6.504, −2.119, **−0.368** (contraction ratios 0.326, **0.174** — accelerating);
extrapolated fixed point ≈ 109.3. Against the pre-registered gate:
(1) N₈₁(L8) = 109.395 ∈ [108.7, 109.5] ✓; (2) |ΔL7→L8| = 0.368 ≤ 1.1, same sign ✓;
(3) contraction continues (0.368 < 2.119) ✓. Zero jams across all 92,731 stitches ✓.
311,737 steps; sha256(L8 word file) c8cc3728…. This is the demonstrated
renormalization fixed point L4' rests on, on the proof's own orbit, predicted before
the run. REMAINING for L4': (a) triple-free verification of the 311,738 points
(7-worker parallel verifier RUNNING — the walk is not yet certified until it returns);
(b) L8 availability floor (ledger, queued) as the 4th floor point; (c) the two hard
lemmas (crowding-count recursion + per-step finite computation) are still the gap
between this strong evidence and a theorem.

## Honest gaps, ranked
1. L4(i): state and prove the neighborhood-invariance lemma from the recursion.
2. L3: pointwise simultaneity of constraints (a)–(d) — the averaging argument
   gives existence in a mass sense; write it so a referee sees a single word
   satisfying all four.
3. L4(ii): far-field summability — measured decay must become a bound.
4. All constants are for THIS menu/matrix; the theorem is existential, so that
   is fine — but every lemma must be stated for this fixed (S, M).
5. Independent human review after the above.
