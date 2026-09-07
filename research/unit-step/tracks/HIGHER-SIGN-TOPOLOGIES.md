# Higher ± topologies: exact overlap quotient and subsequence search

**September 6, 2026. AI-assisted research checkpoint; no new 4- or 5-vector
construction.** This is a separate approach to the [joint minimum
problem](../JOINT-MINIMUM.md), not completion of one of the four handoffs.
No improvement of either minimum is claimed. The existing six-step draft
still awaits independent review.

## Outcome

Rather than enumerate successively longer periodic words, reduce the **entire
infinite sign-stream family**, including nonperiodic streams, to a small
finite quotient for each stated selector model.

1. Changing the signs alone, while retaining the four-state tags, does not
   evade the [existing six-vector obstruction](../../../design/SIGNED-GAUSSIAN-UNIT-STEP-OPTIMIZATION.md#optimality-inside-this-tag-scheme).
2. A genuinely different operation is to **retain a subsequence of vertices**:
   several old steps become one displacement. This inherits noncollinearity
   and is not a fixed relabeling of the old eight transitions.
3. For retaining every vertex whose state belongs to a fixed nonempty subset
   of the four states, all sign streams reduce to **1,080 exact cases**.
   With the existing Cambie tags, none has fewer than six displacements:

   | Number of retained states | Cases | Minimum distinct vectors |
   |---:|---:|---:|
   | 1 | 288 | 7 |
   | 2 | 432 | 6 |
   | 3 | 288 | 7 |
   | 4 | 72 | 6 |

4. A more flexible selector depends on binary phase as well as state. A joint
   constraint model chooses the low signs, tail carry class, retained points,
   and a menu of at most five vectors. For selectors retaining at least one
   vertex in each block, with positions determined by its tail state:

   | Block length | Low-sign possibilities | Result at budget 5 |
   |---:|---:|---|
   | 2 | 2 | Excluded; independently checked all 648 selector/graph assignments |
   | 4 | 4 | Excluded; independently checked all 810,000 assignments |
   | 8 | 8 | Excluded by boundary-first search; independent subset-mask reference agrees |
   | 16 | 16 | Excluded by boundary-first search; all 8,704 endpoint units complete |

**Follow-up:** the 8/16 rows were initially solver timeouts. They are now
superseded by the completed exact overlap search in §3a, not by treating a
longer timeout as evidence. The old solver outcomes remain archived.

The finite exclusions apply to exactly these selectors and fixed tags. They
are **not** global lower bounds on $s_*$ or $d_*$. No four- or five-vector
positive example emerged. The six-vector controls establish feasibility at
six within these classes, not a new improvement. The 16-position exclusion
has not been reproduced by a second full-size implementation or externally
reviewed; see the precise validation boundary below.

## 1. Collapse the higher-order sign topology

For an arbitrary infinite stream $\epsilon_j\in\{1,-1\}$, write

$$
 \sigma(n)=\sum_j\epsilon_j b_j(n)\pmod4,
 \quad u_n=i^{\sigma(n)},\quad z_n=\sum_{a<n}u_a.
$$

If $n$ has $k$ trailing ones, its state change is

$$
 \delta_k=\epsilon_k-\sum_{j<k}\epsilon_j\pmod4,
 \qquad \delta_{k+1}-\delta_k\equiv-\epsilon_{k+1}\pmod4.
$$

Thus the visited set $D=\{\delta_k:k\ge0\}$ is a connected, nonsingleton
subset of the four-cycle. There are exactly nine possibilities:

$$
 01,\ 12,\ 03,\ 23,\ 012,\ 013,\ 023,\ 123,\ 0123.
$$

Every one is realizable. The checker supplies an eventually periodic lasso
for each: a finite sign prefix and a cycle whose sign sum is zero modulo four.
It traverses all specified changes and never leaves them. This is a description
of infinite streams, not an extrapolation from finite curve prefixes.

For each $d\in D$, **every** transition $r\to r+d$ occurs. Fix a carry depth
producing $d$. Above its forced suffix, at least one sign occurs infinitely
often; choosing zero through three higher positions of that sign realizes all
four starting residues. The independent tests construct these indices as
arbitrarily large exact `BigInt` values and replay their bits directly.

Consequently the exact tail adjacency graph is determined by $D$, however
complicated its periodic or nonperiodic sign stream is. Superset graphs only
add displacement constraints, so the phase-selector feasibility search needs
only the four minimal graphs $01,12,03,23$.

## 2. Why three low signs suffice for all state-only returns

Fix the first three signs and let

$$
 B(r)_j=r+\sum_{a=0}^2\epsilon_a b_a(j)\pmod4,
 \qquad 0\le j<8.
$$

If $m$ of these signs are negative, their subset sums include every integer
from $-m$ through $3-m$. Hence **each eight-letter block contains every state**.
For a nonempty selected state set $A$, each block therefore contains a selected
vertex. A consecutive selected pair lies within one block or across one
boundary, hence within $B(r)B(s)$ for a tail transition $r\to s$.

There are $8$ low-sign choices, $9$ tail graphs, and $15$ nonempty choices of
$A$: $8\cdot9\cdot15=1,080$. No higher sign bits need enumeration. Every
catalogued pair is realized because every claimed tail transition occurs.
This establishes both directions of the reduction; it is not merely an
upper bound obtained from an overlarge language.

A return segment is summarized exactly by $(r,s,x,y,\ell)$: endpoint states,
Gaussian displacement, and index gap. Its vector in the current lift is

$$
 (2x+c_s^x-c_r^x,\ 2y+c_s^y-c_r^y,\ 4\ell+s-r),
 \quad (c_0,c_1,c_2,c_3)=(0,-1,-1+i,-i).
$$

Different return words with this same summary genuinely give the same spatial
vector. The table above counts these **vector overlaps**, not words, directions
up to scale, or projections onto the plane. Selecting a single state removes
all tag differences, but still leaves at least seven vectors in this class.

## 3. Phase-dependent selectors: positive-construction mechanism

Let $L=2^q$. For a block indexed by $n$ with tail state $r$, retain a nonempty
set $J_r\subseteq\{0,\ldots,L-1\}$ of its positions. This can retain several
vertices per block; it is not just one representative or a coarse fixed coding.

For each possible low-sign word, the solver computes the exact tagged points
inside each of the four block types. Required displacements are:

- internal gaps between successive members of $J_r$;
- the gap from $\max J_r$ to $\min J_s$ in the next block, for every allowed
  tail edge $r\to s$.

Boolean variables choose retained points and vector labels. A clause makes a
vector label mandatory whenever its endpoints are consecutive retained points
in the chosen topology. One pseudo-Boolean constraint permits at most five
labels. Low-sign and tail-graph choices are solved **jointly**, not by scanning
longer periodic rules one after another. A Boolean finite-domain formulation
was substantially faster than the initial mixed-integer SMT formulation, but
still timed out at $q=3,4$ in the first pass. The overlap-directed follow-up
below completes those two cases without using the timeouts as premises.

A satisfying model would be an **infinite** construction certificate, not just
a surviving finite prefix: choose an infinite tail realizing the graph; the
listed finite menu covers every internal segment and boundary forever. The
retained walk is a subsequence of the original tagged lift, so its vertices
remain distinct and triple-free under the existing signed-family argument.
Translate its first vertex to the origin. No claim of such a model at budget
five is made here.

The independent validator uses no SAT solver: it builds actual two-block state
words, sums Gaussian units, computes tagged chords, and checks every nonempty
selector assignment at $q=1,2$. It stops evaluating an assignment as soon as a
sixth distinct displacement is forced. It also independently reconstructs the
six-vector control.

## 3a. Completing the 8- and 16-position cases

The [overlap search](signed_phase_overlap.mjs) changes the branching variables:

1. Choose the first and last selected vertex of a block type.
2. Immediately add every boundary vector whose two block endpoints are now
   known, including self-edges. These are forced regardless of the interior
   path. Reject the entire family if a sixth distinct vector is required.
3. Only then generate increasing internal paths between these endpoints,
   retaining paths whose accumulated vector menu still has size at most five.
4. Assign opposite states early when the graph has opposite-state edges, so
   both directions constrain the menu before two more block paths are chosen.

This pruning is complete: every nonempty selector has unique first/last
positions and an increasing internal path; every added vector is mandatory in
any completion. A branch already requiring six labels cannot lead to a
five-label solution. For fixed earlier blocks and current endpoints, two
partial paths with the same current vertex and the same menu impose identical
future constraints, so optional memoization may retain just one. The 8-position
run also finishes with memoization **disabled**, with the same exclusion.

| Block size | Endpoint units | Completed result | One-core search time |
|---:|---:|---|---:|
| 8 | $8\cdot4\cdot36=1,152$ | No at-most-five-vector selector | about 2.5 s (1.6 s without memoization) |
| 16 | $16\cdot4\cdot136=8,704$ | No at-most-five-vector selector | about 345 s, across two resumed runs |

The 16-position run visited 1,946,847,878 search nodes, pruning entire groups
of selector assignments rather than forming their Cartesian product. All
endpoint units completed. These are exact finite selector exclusions via the
infinite-family reduction, not tests of a finite curve prefix.

The [independent subset-mask reference](check_signed_phase_overlap.mjs) for
block size eight enumerates each block's 255 subsets, combines whole subsets
in natural state order, and has no endpoint-first path generation, opposite-
state ordering, or memoization. Its pruned subtrees account for exactly
$32\cdot255^4=135,304,020,000$ assignments, all excluded, in about 14 seconds.
It shares the already independently checked geometric chord tables, but not
the new branching algorithm. No second full-size 16-position implementation
was run. Generic pruning tests additionally compare exact minima on synthetic
SAT and UNSAT instances against flat enumeration; Gaussian small cases and
six-vector witnesses provide negative and positive controls.

The exact minimum in each of these **fixed-tag, nonempty-block selector
classes** is six: the unselected alternating walk supplies the upper bound
at every block size, and these computations exclude at most five. This is
not an exact value for either global minimum.

## 4. Scope boundaries and next useful question

This investigation fixes Cambie's four planar tags and height $4n+\sigma(n)$.
It does **not** exclude changing those tags in the selected-vertex models,
selecting by unbounded history, allowing empty blocks and jumping over them,
using another curve construction, or another proof mechanism.

The useful unresolved positive search is now explicit: can a richer selector
or different tag geometry create a certified five-vector menu? The stated
nonempty-block model is excluded through length sixteen, but larger blocks,
empty-block jumps, and selectors depending on additional context remain open.
Do not infer an all-block-size theorem from these four completed sizes, or
present a smaller family restriction as a lower bound on $s_*$. The new search
branches on forced overlaps rather than multiplying all possible selectors.

The [public research timeline](../../../viz/progress.html#signed-selector-research)
summarizes these results as **computational evidence**, with the fixed-tag,
nonempty-block selector restriction and the outstanding second full-size
implementation check and external review for the 16-position case. It states
that the global minima remain open and points back to these artifacts. This
status entry does not publish a new threshold theorem or change the original
Erdős 193 proof; these exclusions must not be promoted to a global impossibility
result. Regression tests keep its counts and review caveats synchronized with
the saved search results.

## 5. Reproduction and retained evidence

From repository root, all one-core:

```sh
node research/unit-step/tracks/signed_return_topologies.mjs --write
node --test research/unit-step/tracks/signed_return_topologies.test.mjs
node research/unit-step/tracks/check_signed_phase_selector.mjs
node research/unit-step/tracks/signed_phase_overlap.mjs --q 3 --seconds 30 \
  --output research/unit-step/checks/signed-phase-overlap-8.json
node research/unit-step/tracks/signed_phase_overlap.mjs --q 4 --seconds 600 \
  --output research/unit-step/checks/signed-phase-overlap-16.json
node research/unit-step/tracks/check_signed_phase_overlap.mjs --q 3 --write
node --test research/unit-step/tracks/signed_phase_overlap.test.mjs

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
uv run --with z3-solver==4.15.4.0 python \
  research/unit-step/tracks/signed_phase_selector.py \
  --levels 1 2 3 4 --seconds 60 \
  --output research/unit-step/checks/signed-phase-selector.json
```

The phase-validator `--write` regenerates its small certificate. For the SAT
positive control, add `--levels 1 --budget 6`; it recovers the current six vectors.
The solver's timeouts are machine-dependent, so timings/unknown rows can change
on rerun; they are recorded outcomes, not deterministic impossibility facts.

- [Exact state-return catalogue](../checks/signed-return-topologies.json): compact
  row schema, all 1,080 cases, minima, explicit minimizing menus, source/result
  hashes, and infinite-tail witnesses.
- [Phase-selector solver outcomes](../checks/signed-phase-selector.json): model
  identity, pinned solver version, timeout, and separate outcomes at every level.
- [Independent phase check](../checks/signed-phase-independent.json): exhaustive
  small-selector counts and exact six-vector positive control.
- [Completed 8-position search](../checks/signed-phase-overlap-8.json) and
  [16-position search](../checks/signed-phase-overlap-16.json): complete endpoint
  unit counts, code/dependency identity, node/pruning totals, and scoped outcomes.
- [Independent 8-position reference](../checks/signed-phase-reference-8.json):
  complete assignment coverage per low-sign/tail-graph case.

Compatible completed work resumes from source/config-identity-checked,
checksum-validated atomic checkpoints under ignored `.checkpoint-signed-*`
directories. Interrupted active solver work can restart from its last completed
level; completed levels are not redone. The Python process handles SIGINT and
SIGTERM. The new Node overlap search checkpoints completed endpoint units;
its `--seconds` limit is not part of checkpoint identity, so increasing the
limit continues validated progress. Incomplete active units restart, never
count as excluded. The independent reference checkpoints whole topology cases.
Timestamped logs record build/search phases, limits, progress, resource use,
and final outcomes separately from these final artifacts.

Attribution: this exploration uses the Cambie–Kalviainen Gaussian/valuation
foundation, Kalviainen's signed family, and Cambie's offsets. A spatial witness
would imply a basis witness by Shallit's encoding. This note neither changes
manuscript bylines nor represents independent collaborator approval.
