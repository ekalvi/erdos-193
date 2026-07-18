# Ordered-path poisoned-word safety gate

**Status: finite exact audit, not an unconditional proof.**  This note corrects
the availability gap in `CONDITIONAL-THEOREM.md` and records the smallest exact
test of the proposed ordered-path safety game on the realized L5--L8
scale-and-rotate construction.

The audit has a split verdict:

- **Keep** the 311,738-point scale-and-rotate walk as a construction orbit and
  test corpus.  Every target stitch checked below has globally legal words.
- **Reject** arbitrary bounded crowding, a radius-40 truncation, explicit local
  state enumeration, and a scalar shell contraction as proofs of indefinite
  availability.
- **Still open:** a direction-sensitive poison-mask CEGAR game with a new
  same-scale/age-one invariant and a contracting argument only for the genuinely
  deep residual.

All counts below are exact integer computations unless explicitly labeled
sampled or conjectural.

## 1. The actual remaining lemmas

Let `P[k,t]` be the exact set present immediately before stitch `t` at level
`k`.  It contains every transformed parent anchor and the interiors of exactly
the connector words already chosen in the construction's stitch order.  Let
`i=order[k][t]`, let `s=parent_word[k][i]`, and let `D_s` be the ordered
connector domain actually loaded by `gate_run.load_domains()`.

For `w in D_s`, let `I_s(w)` be its interior lattice points, translated so that
the pending start anchor is zero.  Define

```text
K(s,P) = {w in D_s : w is not exactly legal against P}.
```

Here exact legality includes collision, old--old--new collinearity,
old--new--new collinearity, and the domain's endpoint and all-new constraints.

The direct availability lemma that would actually finish the construction is:

> **Lemma A (finitely certified safety selector).**  Specify a concrete-history
> abstraction independent of the proposed policy, a finitely represented safe
> invariant `G`, and a total selector `sigma:G -> union_s D_s`.  The seed lies
> in `G`; for every concrete legal history represented by `q in G`, the selected
> word belongs to the pending domain and is outside `K(s,P)`; and every sound
> abstract successor after inserting it lies in `G`.

Lemma A may instead be certified as a greatest fixed point of the safety game
in Section 3.  It cannot be replaced by the statement that some unspecified
constant bounds local crowding.  Nor is "reachable under the certified policy"
by itself a certificate: without a finite total selector and an independently
checked closure condition, that phrase can hide the infinite continuation it
is meant to prove.

A crowding-based proof would require the following explicit package:

> **Lemma R-sharp.**  Give a numerical, level-uniform local bound strong enough
> for a finite availability calculation, for example a proved bound of the
> form `c_k(q,4.44) <= 12` if that exact threshold is what the calculation uses.

> **Lemma L (near-mask bound).**  Exhaustively and exactly prove, over the
> constructible local configurations allowed by R-sharp, a step-specific bound
> `|K_<=R(s,P)| <= L_s`.

> **Lemma T (uniform far-secant tail).**  Without truncating either endpoint,
> prove `|K(s,P) \ K_<=R(s,P)| <= T_s` for every reachable state, with
> `L_s + T_s < |D_s|`; or prove the sharper direct intersection statement
> `|D_s \ K(s,P)| >= 1`.

Lemma T must include secants whose two old endpoints are far away and secants
with one near and one far endpoint.  It must also include an old point on a line
through two proposed connector interiors.

This is logically unavoidable, not just suggested by the data.  For any finite
step set `S`, endpoints `A,B` with `B-A` not in `S`, and fixed radius `R`, one can
build a finite triple-free obstacle set with `c(q,R) <= 2` that blocks every
first step from `A`: for each `A+s`, choose a fresh integer line through that
candidate and put two mutually remote old points on it.  The lines and points
can be chosen inductively outside all old secants and more than `2R` apart.
Every candidate first point then lies on a far old--old secant while fixed-radius
crowding stays at most two.  Thus even a very sharp local bound cannot replace
Lemma T or an orbit-specific reachability invariant.

The Lemma R currently written in `CONDITIONAL-THEOREM.md` says only that there
is some `C` with `c_k(q,r) <= C r^d` for `1 <= r <= 10`.  The repository already
claims a level-uniform cubic crowding bound.  On this compact radius interval
that bound automatically supplies some finite `C`.  Thus the stated Lemma R is
too weak to be the open availability hypothesis: it is already implied by the
claimed qualitative bound, while Lemma A is not.

The advertised availability floors 317/180/271 do not repair this.  The gate
ledgers tested at most 200 connector words per stitch and extrapolated.  They
are sampled estimates, not exhaustive lower bounds.

## 2. Exact finite poison atoms

For a fixed step type `s`, construct the following finite atom universe in
pending-anchor-relative coordinates.

- A **site atom** `p_x` for every candidate interior offset `x`.  It is poisoned
  when `A+x` is occupied or lies on a secant through two points of `P`.
- A **line atom** `l_(u,m)` for every geometric line through two candidate
  interiors.  Its canonical key is primitive direction `u` and integer moment
  `m=x cross u`.  It is poisoned when an old point has the same moment.

Each word is the set `C_s(w)` of its site and line atoms.  For the prevalidated
connector domains,

```text
w is killed  <=>  C_s(w) intersects Poison_s(P).
```

The relevant atom universes are small:

| Step | Words in the actual domain | Sites | Lines | Line directions |
|---:|---:|---:|---:|---:|
| 0 | 2,570 | 122 | 907 | 62 |
| 1 or 122 | 9,046 | 174 | 1,978 | 94 |
| 115 | 15,920 | 214 | 2,872 | 109 |
| 4 or 20 | 47,467 | 252 | 4,198 | 145 |

This is an exact monotone representation.  Fatal poison masks satisfy the
monotone CNF

```text
AND over w in D_s  (OR over a in C_s(w)  z_a).
```

Its minimal satisfying assignments form the fatal antichain.  A BDD, SAT
solver, or antichain package can manipulate that object without enumerating all
subsets of the atom universe.

## 3. Proposed abstract state and transition

A sound abstract stitch state has the form

```text
q = (cursor, ordered_factor, ancestry, near_poison,
     far_poison_by_type_birth_shell, residual_rank).
```

The components are:

1. `cursor`: level, stitch-order position, pending path segment, step type, and
   normalized pending endpoints.  The fixed fragile-first schedule is nonlocal,
   so path position alone is not a transition cursor.
2. `ordered_factor`: one contiguous factor around the pending segment in the
   **single realized parent path**.  Every gap records its step type and one of
   `unfilled`, `pending`, or `filled(actual connector word)`.  Future choices
   are not read from the completed pickle and address streams are never made
   independent after a bounded prefix.
3. `ancestry`: the actual owner chain `(parent segment, slot in chosen word)`
   needed to relate this factor to older levels and to the stitch schedule.
4. `near_poison`: the exact finite site/line atom mask generated by witnesses in
   the chosen near corridor.
5. `far_poison_by_type_birth_shell`: exact projected atom masks, not just
   counts, indexed by collision/old--old--new/old--new--new type, endpoint birth
   ages, and 3-adic spatial shell.  Cross-shell old--old pairs are retained as
   paired types.
6. `residual_rank`: a still-unproved finite summary or decreasing rank for
   shells/ancestry too deep to retain explicitly.

Given `q`, an action is a word `w` whose atom clause is disjoint from the union
of all poison components.  The exact transition:

1. inserts the interiors of `w`;
2. records `filled(w)` in the realized ordered factor;
3. advances the actual stitch cursor;
4. recenters at the next corridor;
5. projects **every** old point and old--old secant onto the next corridor's
   finite atom universe; and
6. abstracts the result, with any omitted geometry overapproximated by the
   residual component.

For a sound overapproximating transition relation `Post#`, define

```text
Phi(X) = {q : there exists w in D_s with C_s(w) disjoint from Poison(q)
               and Post#(q,w) is a subset of X}.
G      = greatest fixed point of Phi.
```

An unconditional certificate consists of a finite representation of `G`, a
proof that the seed state belongs to `G`, and a checked total witness action for
every state/BDD region in `G`.  Its concretization obligation is universal:
the action must be legal for every concrete history represented by the region,
and the sound abstract successor set must remain in `G`.  Checking only the
single history already generated by that selector would be circular.

## 4. Soundness of the poison model

Assume `P` is triple-free and a connector-domain word is internally legal.
Any new failure after inserting the word falls into exactly one of these cases:

- three old points: impossible by the invariant;
- two old points and one connector point: the connector point's site atom is
  poisoned by their secant;
- one old point and two connector points: their line atom is poisoned by that
  old point;
- three connector points: excluded by exact domain construction;
- a repeated point: recorded by a site atom or excluded internally.

Therefore disjointness from the complete poison mask is equivalent to exact
legality.  No locality assumption occurs in this argument.  The implementation
scans all placed points for every candidate site direction and every candidate
line direction.  A far--far or near--far old pair is included in precisely the
same way as a near pair.  Shells and birth levels are only attributions of an
already exact global mask.

This also explains the gap in `taskD_badlines.py`: truncating old endpoints at
`D=40` changes the poison mask.  Empirical negligibility cannot justify that
change; a separate uniform Lemma T is required.

## 5. Is the state space finite?

The poison mask for one fixed corridor type is finite, but the proposed state is
not yet level-uniformly finite.  The next corridor can be far away in path order,
and its poison mask depends on global geometry not recoverable from the current
corridor mask.

Across every one of the 131,097 actual L5--L8 stitches:

| Realized path half-window | Unique states | Repeated classes | Participants in repeats |
|---:|---:|---:|---:|
| 2 | 127,172 | 2,306 | 6,231 |
| 4 | 131,044 | 32 | 85 |
| 8 | 131,097 | 0 | 0 |

At half-window 2, adding the exact radius-40 placed-point cloud makes all 6,231
participants unique.  This is finite evidence of state growth, not a proof that
no finite quotient exists.

A contraction/ranking theorem is therefore still needed.  A plausible form is
a typed inequality

```text
deep_post <= source(ordered same-scale state, action) + T(deep_pre),
```

with a checked spectral radius below one for `T`.  It must operate on projected
line/site masks or sound capacities, include bilinear cross-shell secants, and
separate current/age-one geometry from the deep tail.

A scalar fatal-mass transfer does not work.  In one exact matched local state at
L5--L8, outer-shell kills disappear and then reappear: L6 has 877 first kills in
shell 5 after zero in shell 4; L7 has 1,085 and 1,125 in shells 4 and 5 after
only 10 in shell 3.  The L7 shell-5 and L8 shell-4 blocks are generated entirely
by points of birth age one.  Deep-birth contraction can address only a small
residual; a noncontracting same-scale/parent invariant is still missing.

The exact bottleneck attribution makes that split sharper.  Current- or
parent-age witnesses cover all 465 far-only L5 kills, all 1,181 far-only L6
kills, and 522 of 568 far-only L7 kills.  Only 46 L7 kills, 8.1% of its far-only
total, are uniquely deep.  A contraction theorem may therefore dispose of a
deep residual, but the main state must handle ages zero and one without
contraction.  The shell code now sorts endpoints by corridor distance before
selecting the first repeated primitive direction, making the threshold routine
correct without a hidden ordering assumption.  On the certified triple-free
replay bases the old order was already harmless: a direction bucket can contain
at most two old points.  The independent distance-sorted rerun leaves all
headline near/global/shell counts unchanged.  Correlated `first_*` provenance
fields now distinguish witnesses attaining that threshold from exact
any-witness memberships.

## 6. The decisive finite experiment

`design/salvage_gate.py` replays the exact gate2 pickles, constructs exact
site/line atoms, computes global and `D=40` masks, attributes tail increments by
first shell and birth shell, hashes the masks, cross-checks the production
legality core, solves small fatal-cover instances, and scans ordered-state
stabilization.

Run it with one low-priority core:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    nice -n 15 python3 -B design/salvage_gate.py all
```

The exact target results are:

| Actual stitch | Domain | `D=40` survivors | Global survivors | Unique far kills | Minimum extra arbitrary atoms to fatality |
|---|---:|---:|---:|---:|---:|
| L5 `i=1173`, step 1 | 9,046 | 919 | 454 | 465 | 22 exact |
| L6 `i=8006`, step 115 | 15,920 | 1,891 | 710 | 1,181 | 23 exact |
| L7 `i=3783`, step 122 | 9,046 | 830 | 262 | 568 | 15 exact |
| L8 `i=0`, step 0 | 2,570 | 2,276 | 1,779 | 497 | 20--32; 32 found before timeout |

The far fractions of the apparent local survivors at the first three
bottlenecks are 50.6%, 62.5%, and 68.4%.  Near--far cross pairs dominate many
of these kills.

Two normalized states with the same step-4 domain and the same tested local
ordered context have global killed-mask sizes 17,966 and 19,237, with symmetric
difference 7,991.  They still share 24,870 legal actions, so this is an
abstraction counterexample, not an availability counterexample.

The state scan now tests both the constructor's fragile-first schedule and an
exact left-to-right replay of the same realized connector choices.  The latter
replay is sound: at every stitch its placed set is a subset of the verified
final triple-free level, so the recorded connector remains legal.  Changing
the schedule does **not** reveal a repeated literal local state:

| Replay schedule | Half-window 2 | Half-window 4 | Half-window 8 | Repeated half-window-2 states after exact `D=40` cloud |
|---|---:|---:|---:|---:|
| fragile-first | 127,172 / 131,097 unique | 131,044 / 131,097 | 131,097 / 131,097 | 0 of 6,231 |
| path order | 130,643 / 131,097 unique | 131,097 / 131,097 | 131,097 / 131,097 | 0 of 823 |

Thus path ordering actually leaves fewer repeated contexts in this literal
representation.  This is an exact finite result about the tested fingerprint,
not a theorem that every coarser poison quotient is infinite.  It rejects the
specific hope that merely switching to a contiguous stitch schedule makes the
actual-word plus exact-local-cloud state stabilize on L5--L8.

Two exact negative controls pass:

- A committed, constructor-reachable 56-point state kills all 15,920 words in
  the length-at-most-4 step-115 domain.  An exhaustively found length-5 word
  escapes.  Thus the fixed menu is not safe over arbitrary legal parent walks.
- Starting from the actual 70,334-point L7 bottleneck state, 20 sequentially
  legal lattice points yield a triple-free 70,354-point set with zero survivors
  among all 9,046 pending words.  This completion is not known to be realizable
  by earlier connector choices, so it does not refute the ordered-path game.
- A separate exact 327-point `probe777` state has no legal first menu step: one
  of the 124 candidates is occupied and the other 123 lie on old--old secants.
  It therefore has no connector of **any** length.  This state is far denser than
  the seed-193 orbit and is another broad-state, not canonical-orbit,
  counterexample.

The actual gate2 replay domain is `connector_domains4.pkl` plus
`dstar5_fragile.pkl`.  It does **not** include `dstar5_band.pkl`; any theorem or
experiment that enlarges the menu must say so explicitly.

An exact current-corridor mask does compress well but is not a transition
quotient.  For the 9,046-word step-1/122 domain, the raw connector trie has
19,182 nodes, while reduced live-word MDDs have 533 nodes at L5 and 510 at L7.
After central-inversion normalization, the two killed masks have Jaccard
0.9257, but their survivor sets have intersection only 23 and Jaccard 0.0332.
Worse, the may-poison union of seven individually safe, genuinely reached
normalized states has no common action.  Coverage antichains and MDDs are
therefore useful exact query representations; merging their roots without
provenance and transition congruence is unsound.

### Exact two-gap backward cone

`design/l7_backward_cone.py` performs the first sound replacement experiment
under the constructor's fragile-first schedule.  It targets L7 segment 3783
and varies only its two already-placed realized-path neighbours 3782 and 3784,
freezing every other pre-target choice.  Crucially it first removes the four
actual connector interiors and recomputes the base poison.  Retaining the old
points and merely adding new poison would be monotone but would not model
connector replacement.  Gap 3784 would be a future choice under left-to-right
order, so this certificate must not be silently transferred to that schedule.

| Quantity | Exact result |
|---|---:|
| Fixed-base points after removal | 70,330 |
| Target survivors before replacements | 1,251 |
| Unary-legal choices for gaps 3782 / 3784 | 649 / 1,250 |
| Raw pairs | 811,250 |
| Globally triple-free replacement pairs | 767,711 |
| Fatal target pairs | 0 |
| Minimum target survivors | 59 |
| Median target survivors | 487 |

The unique minimum occurs at domain indices `(1534,1969)`, words
`(102,112,53,102)` and `(106,59,101,103)`.  Its placed-set SHA-256 is
`8ed6459f1b4ff3caea4e4a4a2a3fdc322331b2824829b89a9fd51147a3c8201d`.
An independent production-core replay checks all 9,046 target words and again
finds 59.  Those residual words have exact arbitrary-atom cover distance nine.
The full result, survivor indices, input hashes and timings are in
`design/l7-backward-cone-summary.json`.

This proves a bounded UNSAT statement: no assignment in that two-gap cone is
fatal.  It is not a safety-game fixed point.  The old realized state had 262
survivors and atom-distance 15, but removing the two old connectors resurrects
989 words; hence the old 15-atom cover is only a search heuristic for a
replacement CEGAR, not a sound monotone starting state.  Because the complete
replacement union with every frozen pre-target point is triple-free, its
prefixes in fragile-first order are triple-free as well.  The cone is therefore
reachable in the legal-choice game, although the replacement words need not be
selected by the constructor's deterministic policy.

## 7. Strongest obstruction and next gate

The strongest obstruction is not the generation-2 OSC overlap.  That overlap
is between alternative choices in the full menu closure; the realized walk
chooses one word per gap.  It therefore does not refute an ordered-path
certificate.

The strongest obstruction is that the exact corridor poison mask is not a
Markov state.  The fixed schedule jumps nonlocally, same-scale and immediately
inherited geometry regenerates distant poison, and exact local contexts show no
observed stabilization.  A finite quotient risks having to remember the whole
realized ancestry, which would merely restate the theorem.

Simply increasing connector length does not remove this obstruction.  Length
five escapes the committed 56-point fixed-domain jam, but a sealed first step
defeats every finite or unbounded detour.  An adaptive-length theorem would need
a controlled invariant and a well-founded routing rank that prevents sealed
states and proves termination; word count alone supplies neither.

The next CEGAR gate, adding gap 3786, is now closed exactly.  Gaps 3782, 3784
and 3786 are the three schedule-consecutive step-123 stitches at ranks
8,828--8,830.  Removing all three actual connectors leaves 70,328 base points,
1,324 target survivors, and exact unary domain sizes 649, 1,288 and 1,728--or
1,444,455,936 raw assignments.

`design/l7_three_gap_gate.py` proves this whole cone non-jamming without
enumerating the triple product.  For a choice `x`, let `U_x` be its exact unary
target poison and let `Q_xy` be target-site poison from cross-choice secants.
The exact target mask is

```text
M(a,b,c) = U_a union U_b union U_c
           union Q_ab union Q_ac union Q_bc.
```

For every one of the 789,797 exactly compatible `(a,b)` pairs, the checker uses

```text
T_A(a) = union over all c of (U_c union Q_ac),
T_B(b) = union over all c of (U_c union Q_bc).
```

The two unions may use different `c` choices and include choices globally
incompatible with `(a,b)`, so `T_A union T_B` is a sound overapproximation of
every actual third-choice effect.  Even then, at least **six** target words
remain for every compatible pair.  The tight pair has domain indices
`(1386,2029)` and its immune target indices are
`1220,2177,2508,8241,8242,8771`.  A fresh full-state `compute_poison` check on
the recorded choices exactly matches the unary/pair decomposition and returns
the known 262 survivors.  The compatibility relation, overapproximation mask
streams, base mask, unary masks, checker dependencies and effective domains are
bound by SHA-256 in `design/l7-three-gap-summary.json`.

This is stronger than an UNSAT search: it supplies a uniform finite lower bound
throughout this frozen cone.  It still does not quantify over earlier connector
choices outside the cone or produce a cross-level quotient.

### Exact bounded four-gap probe

`design/l7_four_gap_probe.py` adds gap 3785, completing the contiguous path
window 3782--3786.  This gap is geometrically only Chebyshev distance 12 from
the target, is scheduled much earlier (rank 433), and has 17,837 unary-legal
choices in its 47,467-word domain.  Removing all four recorded connectors
leaves 70,325 fixed-base points and 1,394 target survivors.

The natural exact interface for the large-domain choice records its target
mask, its target cross-mask against each of 277 possible other sites, forbidden
other sites, and forbidden other-site pairs.  A first implementation
accidentally unioned only three of its four interior points; the corrected
source-level run gives 17,821 full interfaces for 17,837 choices: 17,805
singletons and 16 doubletons.  Thus exact quotienting is sound but supplies
negligible compression.

For the 100 compatible `(A,B)` states with the smallest sound all-`C` residual,
there are 3,221 coarse-zero `(A,B,D)` cores.  The checker exactly discharges all
505 cores belonging to the first 12 states: 171 are incompatible, and 318,319
compatible-`C` assignments cover the remaining 334.  Every legal four-gap
assignment in those 12 slices leaves a target word; the minimum exact count is
22.  The source-level run completed in 238.37 seconds with all expected counts
and hashes asserted.  The other 2,716 coarse-zero cores in this 100-state census,
and the remaining compatible `(A,B)` states, are unproved.  A separate bounded
countersearch found an independently replayed 15-survivor assignment but no
fatal one; that search is evidence, not a lower bound.

This does not lift the three-gap floor of six to the whole four-gap cone, and a
fatal four-gap assignment would refute only all-choice robustness.  The player
controls the early choice.  The strategy-relevant block gate is therefore

```text
there exists D such that, for every compatible later A,B,C,
there exists a legal target word.
```

A positive `D` would give a robust early block action.  Failure for every `D`
would close that stronger block-policy route, not cooperative existence.

### Exact robust early action and one concrete successor

`design/l7_robust_d_selector.py` closes that finite gate.  The pinned early
choice is candidate-list index 2,950, effective-domain index 8,681,

```text
D* = (34,24,19,22,98).
```

For every one of the 865,674 unary-legal, base-compatible `(A,B)` pairs, the
checker produces a set `S_AB` of at least **45** target words whose target atoms
remain clean after unioning the effects of every one of the 1,802 unary-legal
`C` choices.  Compatibility of `C` with the prior state is deliberately not
assumed.  The precise conclusion is conditional on the antecedent: if
`base+A+B+C+D*` is a valid distinct triple-free placed state, every word in
`S_AB` is a legal target extension.  It is not a claim that every `C` makes the
prior state legal.  A recorded `(A,B,C)` continuation supplies an asserted
non-vacuity witness.  The revised checker completed from pinned inputs in
173.255 seconds with zero sound cores and uniform floor 45.

The action is still future-aware: `D*` is scheduled at rank 433, while the
target is rank 16,790, and the finite base freezes all other intervening choices
to the recorded L7 completion.  It is an offline precommitment for this cone,
not an online all-history selector.

`design/l7_robust_successor_probe.py` tests one action-labelled edge from the
tight state.  It chooses the least exactly legal `C` (domain index 0), then the
first exactly legal member of the certified 45-word set (target index 26).  The
fragile-first scheduler jumps next to segment 3806, whose corridor is translated
by `(102,-54,75)`, Chebyshev distance 102.  The exact global successor scan
leaves **2,747 / 9,046** words, and the recorded successor action remains legal.
This is one concrete edge, not a uniform successor floor or abstract closure.

### Next architecture: a bounded inherited-tile pipeline

The fragile-first scheduler itself forces an unbounded cursor and makes the
next edge nonlocal.  The inherited parent-word tiling suggests a cleaner
schedule.  At this bottleneck, tile 1124 contains gaps 3782--3784 with steps
`(123,122,123)`, while tile 1125 contains gaps 3785--3787 with steps
`(20,123,70)`.  Process tiles left-to-right: first place the locally fragile
guard in the next tile, then finish the current tile in local fragile-first
order.  Here that order is `D(3785), A(3782), B(3784), target(3783)`; `C(3786)`
remains absent, so the all-`C` floor 45 is stronger than this schedule needs.

The candidate macrostate retains four actual inherited tiles, their ancestry
and filled/pending words, the guard phase, exact age-zero/one poison masks for
every active corridor, and a typed direction/residue/birth-shell frontier for
older witnesses.  The smallest genuine transition gate is then

```text
D*;
for every compatible A,B:
    choose a legal target W and a legal next-tile guard G at gap 3788
    whose abstract successor remains in the retained region.
```

Before synthesizing that QBF/BDD transition, replay the recorded L5--L8 words
under the pipeline and measure each exact poison witness's first-hit and
last-hit tile lag.  Freeze all horizons, canonicalization and action codebooks
using L5--L6 only; use L7 for validation and untouched L8 as holdout.  Growing
witness lag or new holdout masks outside the trained horizon would decisively
show that the bounded cursor has not bounded causal memory.  Even a successful
holdout remains evidence until every abstract transition and its total action
is checked.

A reachable fatal assignment in a larger cone would be a decisive counterexample
to all-choice robustness for that frozen cone, but not necessarily to a
controlled selector.  Stable positive transition bounds under an explicit
causal selector would be the first concrete evidence for a usable ordered-path
invariant.  Until those bounds close under successors and an arithmetic
deep-tail rank closes the omitted history, the scale-and-rotate construction
remains an exceptional finite record and a plausible heuristic, not an
unconditional solution.
