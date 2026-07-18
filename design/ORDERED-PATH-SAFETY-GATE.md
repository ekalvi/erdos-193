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

## 8. Inherited-tile pipeline experiment

The proposed pipeline has now been replayed exactly on the recorded L5--L8
construction.  A tile has a guard only when it contains a gap whose original
length-2--4 domain has size below 2,000.  The schedule bootstraps tile 0's guard
when present; while sweeping tile `t`, it places tile `t+1`'s guard and then the
remaining gaps of tile `t` in `(domain size, gap index)` order.  Recorded words
are revealed only after their pipeline action.  Every replay prefix is legal
because it is a subset of the exactly verified completed level.

### Exact causal L7 macrotransition

At the known bottleneck the schedule ranks are exactly

```text
D3785, A3782, B3784, target3783, G3788, C3786.
```

The causal state before `D` has 36,589 points and contains no recorded future
connectors; the earlier frozen-cone base had 70,325.  The already discovered
choices `D8681`, `A1465`, and `B425` are sequentially legal in this causal
state.  They leave 111 of the target's 9,046 words.  For **every** one of those
111 target words, at least 1,153 of the next guard's 1,505 length-2--4 words
remain exactly legal.  The unique floor action, target index 3,056, was
recomputed by an independent full poison scan.  On the pinned target index 26,
350,509 of the guard's complete 453,015-word domain survive; choosing guard
index 0 then leaves 1,887 of 2,570 words at `C3786`.

This proves a two-ply `for every target, there exists a guard` statement only
at one concrete incoming state with pinned `D/A/B`.  It does not quantify over
alternative incoming histories, and the `C` check is only for the pinned
target/guard trajectory.  It is therefore not a safety-game closure result.

### Fixed-before-run 18-probe lifetime audit

Every probe is the middle step-122 gap of an actual inherited tile with ordered
signature `(123,122,123)`.  The split was fixed before inspecting the poison
results, though it was not cryptographically committed as a preregistration:

- train: L5 gaps 523, 989 and all nine matching L6 gaps;
- validate: L7 gaps 1,932, 13,171, 21,115, and 3,783;
- untouched holdout: L8 gaps 19,872, 49,039, and 65,694.

For every candidate site and candidate-interior line, the checker scans the
complete placed set.  It records collision, old--old--new, and old--new--new
witnesses with correlated endpoint birth age, 3-adic distance shell, owner
tile options, and placement time.  Boundary anchors retain both adjacent owner
tiles.  There is no radius or endpoint cutoff.  The independent L5 reference
mask agrees exactly with `compute_poison`.

The result is mixed:

| Split | Probes | Survivor range / 9,046 | Maximum word / atom owner radius | Maximum first-visible shell |
|---|---:|---:|---:|---:|
| L5 train | 2 | 1,367--2,516 | 101 / 101 | 3 |
| L6 train | 9 | 1,238--2,311 | 625 / 625 | 4 |
| L7 validate | 4 | 403--1,763 | 342 / 342 | **5** |
| L8 holdout | 3 | 849--1,513 | 61 / 61 | 3 |

The L5--L6 training horizon of 625 owner tiles reproduces every killed-word
mask **and every poisoned-atom mask** at all L7 and L8 probes: no validation or
holdout atom requires a larger minimum owner radius.  This is encouraging
finite evidence for an owner-coordinate frontier, but 625 is not a practical
literal window and the sample cannot prove a level-uniform horizon.

The spatial-shell test fails on validation.  Training first sees shells only
through 4.  L7 gap 13,171 has one genuinely first-visible shell-5 atom that
uniquely accounts for 56 killed words; its correlated any-witness type includes
an age-0/age-0 secant with endpoints in shells 4 and 5.  L7 gap 21,115 has one
first-visible shell-5 atom uniquely accounting for nine words, generated by an
age-0 point on a line through two proposed interiors.  Thus a fixed shell-4
cutoff is unsound, and deep-birth contraction cannot absorb all new outer-shell
effects because one failure is explicitly same-level.  The absence of a
shell-5 failure in the three L8 holdouts does not undo the L7 counterexample.

All 18 killed-word masks, poisoned-atom masks, and correlated witness-stream
hashes are distinct.  A separate four-sentinel source/action/successor check
freezes exact codes at L5--L6.  Neither L7 nor L8 matches any training code for
the four-tile ordered factor, source poison, recorded action, state/action,
successor factor, successor poison, or whole transition.  This refutes literal
exact-code stabilization on the tested orbit, not a coarser sound BDD,
antichain, or arithmetic quotient.  Three successor checks cover only their
exact length-2--4 subdomains because the full domains have 298,775--501,044
words; L8's full successor retains 1,898 / 2,570 words.

### What a contracting transfer lemma would have to prove

A scalar transfer operator on shell kill counts is not sound.  Collinearity
does not weaken with distance, shell masks overlap, and near--deep secants are
created bilinearly.  A viable split must keep current and age-one geometry in
the noncontracting safety state, and represent the genuinely deep residual by
both endpoint and already formed secant frontiers.  Conditional on an exact
near state/action `sigma`, a possible triangular form is

```text
E' <= e_sigma + A_sigma E
L' <= ell_sigma + B_sigma L + C_sigma E,
```

where `C_sigma E` includes every near--deep secant.  If deep endpoints are
decomposed independently, an additional cross-component bilinear term is
unavoidable unless the joint pair frontier is carried in `L`.

The referee-grade missing statement is therefore a **deep residual transfer
lemma**: exhibit a finite exact type set for all age-at-least-two endpoints and
their secants relative to every active corridor; prove that every recurrent
noncontracting type is promoted into the retained state; and give either a
common Lyapunov function with joint contraction for every selected transition
or a strict integer/3-adic rank.  The resulting fixed-point poison mask must
still miss a connector word in every safe near state.  Separate empirical
spectral radii are insufficient for a switched system.

The strongest likely obstruction is an exact resonant secant cycle.  Linear
scaling preserves collinearity, so a projected deep incidence can recur with
unit effect at successive generations.  Such a mode forces joint spectral
radius at least one unless it is retained exactly or ruled out arithmetically.
Searching the ancestry-matched incidence graph for those cycles is now more
decisive than fitting another scalar shell-decay curve.

Artifacts: `inherited_tile_lifetime.py`,
`inherited-tile-lifetime-summary.json`,
`pipeline_transition_stabilization.py`,
`pipeline-transition-stabilization-summary.json`,
`l7_pipeline_macrotransition.py`, and
`l7-pipeline-macrotransition-summary.json`.

## 9. Exact shell-5 lineage and endpoint-incidence closure

The two validation failures above have now been identity-enriched and followed
one generation.  The unique first-visible shell-5 atoms are exactly:

- L7 gap 13,171, site atom 905 at offset `(3,0,4)`, with a single attaining
  old--old witness formed by `connector:L7:G12291:I1` and
  `connector:L7:G12324:I2`; its atom belongs to 154 / 9,046 words and is the
  first-visible obstruction for 56;
- L7 gap 21,115, line atom 611 with direction `(2,1,1)` and relative moment
  `(-4,1,7)`, with attaining endpoint `connector:L7:G19950:I2`; its atom
  belongs to 18 words and is the first-visible obstruction for nine.

All three endpoints are born at L7.  Therefore these are age-zero source
effects, not deep residuals.  At L8 they are inherited anchors of age one; the
L5--L8 lineage data do not observe their promotion to age two.  Section 10's
later selected-L9 precursor now does observe that promotion, but only against
the initial anchor skeleton.

The exact successor audit indexes all 311,738 final L8 points by primitive
direction from each tagged endpoint.  A point's activation is `-1` for an
inherited anchor and the exact inherited-tile pipeline rank of its connector
for an L8 interior.  Thus, before a stitch of rank `r`, the active partner set
is represented exactly by entries with activation `< r`.  For every one of
the 92,731 recorded L8 stitches and its actual effective domain among all 124
step types, the checker includes all failures involving a tagged endpoint:

```text
candidate site equals tagged endpoint;
tagged endpoint lies on a line through two candidate interiors;
candidate site lies on a secant through tagged endpoint and any active point.
```

There is no endpoint or distance cutoff.  All 12,537,146 domain words are
covered when converting the reached atoms to exact killed-word masks.  Every
recorded chosen word avoids the resulting tagged-source union.

The result is not zero.  The pair source affects 40 corridors: 39 have a
tagged--other old--old channel and six have an endpoint-on-candidate-line
channel, with overlap.  Its worst union kills 131,472 / 501,044 words at L8
gap 41,266.  The singleton source affects 24 corridors: 22 tagged--other and
six endpoint-on-line; its worst union kills 11,453 / 501,044 words.  Together
the sources affect 64 distinct corridors and leave 92,667 with zero effect.
There are no tagged-endpoint collisions and no tagged--tagged site effects.

The exact direct affine image of neither original candidate atom appears at
any L8 stitch.  The carried old--old line itself is inert through L8.  Yet the
endpoints generate new atoms with other points and with other candidate-line
geometries.  The singleton even retains its old--new--new *mode* on six
different domains although its original line atom vanishes.  Hence

```text
current poison mask becomes empty  does not imply  endpoint can be forgotten.
```

The new effects reach spatial shell 6 and minimum owner radii 882 and 710;
their mixed partners have ages through five.  This is an exact instance of the
`C_sigma E` regeneration term.  It refutes a scalar distance-shell transfer, a
literal owner-625 window, and any mode-preserving atom transition.  It does not
refute a correctly typed deep contraction because the tagged endpoints are
still age one and belong in the retained noncontracting state.

The next theorem obligation therefore precedes the deep-tail lemma:

> **Age-zero/one endpoint-frontier lemma.**  For every safe retained ordered
> state, give a finite sound representation of all current/parent endpoints;
> close it under collision, endpoint-on-candidate-line, and every secant with
> an active point; and prove that a legal action leading to another retained
> state remains after the union of those exact action masks.

Only after that lemma closes can an age-at-least-two endpoint/secant rank be
used in a sound safety proof.  The subsequent selected-L9 precursor performs
the first finite all-anchor promotion of these three age-one types and finds
58 nonzero age-two states, so literal inertness is false.  It still omits the
current L9 connector interiors and makes every refined nonzero state a
singleton.  The next decisive residual experiment must therefore add the
actual current-level connector joins or establish a universal bounded-core
automaton; an active compatible core SCC would be the genuine resonant-cycle
obstruction.

Artifact: `deep_incidence_lineage.py` and
`deep-incidence-lineage-summary.json`.  The canonical raw output is pinned by
SHA-256 in the compact summary.  This is a complete certificate only for the
three tagged endpoints on the single recorded L8 history; it says nothing
universal about alternate connector choices, other endpoints, or L9.

## 10. Exact five-stitch policy extension and the far-frontier interface

The exact frozen-L8 policy experiment now covers five consecutive scheduler
actions.  The quantifier certified by the first three checkers is

```text
for each of four source leaves L, choose fixed B_L;
partition L by exact C-poison predicates into ten total leaves R;
for each R, choose fixed C_R;
for every exact A in R, P+A+B_L+C_R is legal.
```

The ten refined leaves cover all 1,997 legal A actions exactly once.  The next
real stitch is D at rank/gap 67,013, step type 19.  Its exact poison equality is

```text
Q_D = BaseD | UA | UB | UC | XAB | XAC | XBC.
```

Every component was computed without a distance cutoff and the union was
checked against two full-history scans.  All 1,997 histories have a D response;
indeed one word, `[0,3,4]`, is common to all ten leaves.  No D-predicate split
is needed, the minimum individual survivor count is 1,601, and the minimum
common response count in a leaf is 283.  This is an exact transition of the
finite partition at one frozen prefix, not proof that its predicates are
future observables or form an invariant.

The following stitch is E at rank 67,014, gap 67,012, step type 17.  Its exact
poison equality is

```text
Q_E = BaseE | UA | UB | UC | UD
            | XAB | XAC | XAD | XBC | XBD | XCD.
```

All 1,997 selected histories retain E.  Each existing leaf has a common E
response, so no E-predicate split is needed; the common-response counts range
from 46 to 1,923 and the minimum individual survivor count is 6,995.  Five
selected E words serve the ten leaves.  Two full-history recomputations verify
the optimized union.  This is a second exact frozen-prefix transition, not an
inductive state closure.

For the remaining far problem, centre geometry at the pending anchor `a`.
Retain endpoints `u=p-a` and old secants as primitive line pairs

```text
g = canonprim(r-p),       mu = (p-a) cross g.
```

They decide all external poison exactly:

```text
collision:                    u = x;
old point on candidate line:  u cross (y-x) = x cross (y-x);
candidate site on old secant: x cross g = mu.
```

The recenter and scale rules are exact and preserve endpoint correlation.  In
the invariant cofactor metric, the line-offset ratio expands by exactly three
under common scaling and satisfies `h' >= 3(h-B)` under a bounded synchronized
recentring digit.  On a finite synchronized phase graph, the Bellman barrier
`D_q=max(B_e+D_q'/3)` makes `h-D_q` expand by at least three and gives a strict
escape rank outside the resulting core.  This is a theorem-level component of
the far transfer, but only for the old-secant-to-site channel.  Finiteness of
the core, a uniform positive gap for new births, endpoint-on-line effects,
unrelated centres, and pair birth remain open.

The exact realized-path trace shows that those omissions are active, not merely
formal.  Among 146 L8 children of 42 actual L7 parents, 61 full tagged-endpoint
masks strictly exceed the direct endpoint/carried-line mask through joins with
other points.  The tested direct projection remains noncongruent even after
retaining the actual connector choice.  A correlated birth/shell replay has 94
exact descriptor commitments, but every repeated child class is zero-poison
and all 42 enriched parent transition states are singletons.  Thus the current
one-generation data refutes an underspecified frontier while supplying no
nonzero stabilization, `sig_2`, or contraction certificate.

The exact x-parallel audit exhibits the corresponding resonance obstruction.
Across all 131,097 L5--L8 corridors per schedule it finds 35 transitions from
a latent zero-effect line back to an effectful line.  Its actual selected
descendant paths have 12, 2, and 22 exact effect-key returns at periods one,
two, and three.  Identifying gate/pipeline twins leaves 18 physical returns;
three period-three returns also repeat the selected action and the same
physical inherited line.  Thus neither current-mask forgetting nor a strict
rank on `(step, lateral offset, exact x-mask, action)` is sound.  These are
finite projected cycles, not a universal policy cycle: a useful state still
needs honest lineage phase or a contraction/promotion proof.

The sharp finite Bellman computation confirms the exterior mechanism and
isolates the obstruction.  All 13,826 recorded transitions from an exterior
x-line node stay exterior with a certified positive
`delta_target-3 delta_source` margin.  Yet 11,107 of the 11,154 strict-effect
nodes and every effect-key or effect/action return source lie in the core.
Thus the next x-axis certificate is a finite universal core promotion or an
honest core-escape theorem, not another exterior shell fit.

The observed core already has a clean candidate coordinate.  Collapsing all
13,203 strict-or-latent occurrences by `(step, lateral offset)` leaves 1,312
geometric states with congruent combined masks.  Retaining the actual word and
ordered slot also makes all observed carried-line successors congruent.  But
this graph contains no singleton occupancy or line-birth edges and samples
only 2,882 step/action pairs out of the full 12,537,146 words.  The next exact
gate is therefore the all-action prefix-control graph, its finite integer core,
and ordered occupancy-`0/1/2` insertion transitions with collision data.

For x-parallel geometry, finiteness of that integer core is now proved without
sampling.  If connector length is at most `m`, every prefix has invariant
lateral norm at most `C_m=2(m-1)sqrt(12/5)`, and `D_m=3C_m/2` is a phase-free
forward-invariant barrier.  Candidate sites lie inside `C_m`; positive
definiteness leaves at most 1,681 integer offsets for the actual `m<=5`
domains.  This theorem covers synchronized ancestral prefix controls only.
The occupancy/birth transition, exact collisions, and unrelated same-level
cursor jumps remain the proof obligation.

The first selected L9 horizon also falsifies literal age-two inertness.  The
three tagged L7 endpoints have nonzero anchor-only poison in 58 of 488 actual
lineage states, and joins with other L9 anchors dominate the direct channel.
Partners born at L6, L7, and L8 all contribute.  Exact birth-mask and
partner-identity refinements make all 58 nonzero states singleton rather than
producing a repeated effectful quotient.  This audit has not inserted the L9
connector interiors, so it is neither full poison nor availability.

The required certificate must be availability-grade.  A one-state TOP type
with every atom poisoned is already a finite sound quotient, so bare quotient
existence proves nothing.  The useful object must be finite, universally
transition-sound for its selected policy, and precise enough that the combined
near/promoted/tail mask still leaves a connector at every state in a safety
greatest fixed point.  `FAR-SECANT-RANK-LEMMA.md` records the full quantified
obligations.

Artifacts: `l8_immediate_action_cegar.py`,
`l8_third_ply_closure.py`, `l8_fourth_ply_transition.py`,
`l8_fifth_ply_transition.py`, `far_secant_future_trace.py`,
`far_secant_birth_shell_trace.py`, `x_axis_far_secant_resonance.py`,
`x_axis_bellman_barrier.py`, `x_axis_barrier_node_join.py`,
`x_axis_core_promotion_probe.py`,
`l9_anchor_age2_precursor.py`, `l9_anchor_age2_positive_mask_verifier.py`,
`l9_age2_transition_stabilization.py`, their compact JSON summaries, and
`FAR-SECANT-RANK-LEMMA.md`.
