# Adversarial audit of five-menu base-4 descent

**September 6, 2026. Independent AI research report, not human approval.**
Inputs: the supplied, read-only `return-blocks.md` checkpoint and the central
unit-step definitions. No rival new outputs were read. The construction is
Kalviainen's tagged g85 walk, using Cambie's offsets and Shallit's encoding,
on the Cambie–Kalviainen Gaussian source; this report does not reattribute it.

## 1. Exact verdict and scope

**The requested infinite-subsequence theorem remains unproved, and no infinite
five-displacement subsequence was found.** The naive pointwise descent lemma
is false, including after deleting duplicate parent indices. Its failure is
not a counterexample to an existential descent implication for hypothetical
infinite five-menu paths.

What was established here:

* Exact endpoint corrections, and a seven-vertex actual-Q witness taking a
  five-vector menu to six parent vectors, without any duplicate parents.
* A second witness with duplicate parents; deleting them still leaves six.
* Actual-Q witnesses against preserving five by phase thinning and by taking
  first/last selected points in each block. First and last both fail on one
  13-vertex witness.
* A **valid fixed-phase edge lemma**: when both endpoints have the same fixed
  phase modulo 4, their displacement determines their parent displacement.
  The missing part is obtaining such a path without increasing its menu or
  losing the required gap contraction.
* An infinite-complete escape test beyond the exhausted mod-4 family: among
  all 65,536 selectors `n_m=16m+a(q_m)`, exactly 200 have six displacement
  types, and the other 65,336 have eight. None has five. This is a restricted
  computer-assisted result, not an arbitrary-selector theorem.

The old B=16 obstruction is taken from the supplied AI-reviewed checkpoint,
not rerun or extrapolated. A fixed displacement menu gives some finite gap
bound, but not necessarily 16. Even proving the entire subsequence target
would be construction-specific and would **not** prove `s_*=6` globally.
There is no new bound on `s_*` or `d_*`, and no change to the separate original
Erdős 193 theorem or the manuscripts' review status.

## 2. Endpoint algebra: the correction really matters

Write `[r]_4` for the representative in `{0,1,2,3}` and put

```
δ = (0,1,-1,0),       d = (0,1,1+i,1),
c = (0,-1,-1+i,-i),   D = diag(2,2,4).
```

The binary definition immediately gives

\[
q_{4m+a}=[q_m+\delta_a]_4.
\]

The four unit directions in a substituted state block sum to
`i^r(1+i-i+1)=2i^r`; their prefix sums are `i^r d_a`. Summing complete blocks
and then the partial block proves, for every index (not just a prefix),

\[
z_{4m+a}=2z_m+i^{q_m}d_a,
\qquad Q_{4m+a}=DQ_m+R(q_m,a),
\]

where

\[
R(r,a)=\bigl(2i^r d_a+c_{[r+\delta_a]_4}-2c_r,
             4a+[r+\delta_a]_4-4r\bigr).
\]

The complex component is identified with two integer coordinates. All 16
corrections are:

| r | a=0 | a=1 | a=2 | a=3 |
|---|---|---|---|---|
| 0 | (0,0,0) | (1,0,5) | (2,1,11) | (2,0,12) |
| 1 | (1,0,-3) | (1,3,2) | (0,2,4) | (1,2,9) |
| 2 | (1,-1,-6) | (0,-3,-1) | (-1,-4,1) | (-1,-1,6) |
| 3 | (0,1,-9) | (0,0,-8) | (1,1,-2) | (0,-1,3) |

For an edge from `4m+a` to `4l+b`, its parent vector is exactly

\[
W=D^{-1}\bigl(V-R(q_l,b)+R(q_m,a)\bigr).                 \tag{1}
\]

In particular, this is not simply `D^{-1}V`. One actual fine label `(2,0,12)`
already has the following different images:

| Fine edge | Parent edge | Parent vector |
|---|---|---|
| 0 -> 3 | 0 -> 0 | (0,0,0) |
| 1 -> 4 | 0 -> 1 | (1,0,5) |
| 6 -> 9 | 1 -> 2 | (1,1,6) |
| 11 -> 14 | 2 -> 3 | (0,-1,1) |

Deleting the zero image leaves **three**, not one, parent labels for this
single fine label. Even decorating a label by its start and end phases does
not generally fix this: fine edges `2 -> 8` and `22 -> 28` both have vector
`(2,2,24)` and phase pair `(2,0)`, but their parent vectors are `(2,1,11)` and
`(0,-1,7)` respectively.

**A useful reduction of the decoration.** If `h_n=4n+q_n` and `t=h_n mod 16`,
then

\[
a=\lfloor t/4\rfloor,\qquad
r=[(t\bmod4)-\delta_a]_4.
\]

Thus the entire correction is a function `F(t)` of a **single height residue
modulo 16**. A fine vector of height `H` updates `t` to `t+H mod 16`. Formula
(1) becomes the explicit 16-state cocycle

\[
W=D^{-1}\bigl(V-F(t+H)+F(t)\bigr).                     \tag{2}
\]

This is a useful compact state space for a future obstruction, but not a
menu-preservation proof: one label may occur at several residue states.

## 3. Small exact counterexamples to pointwise descent

### 3.1 Five becomes six with no duplicate parents

Take the actual source indices

```
I = (0,4,8,12,22,26,32).
```

Their vertices are

```
(0,0,0), (3,0,17), (4,3,35), (4,0,48),
(5,2,89), (6,5,107), (8,7,131).
```

The consecutive fine vectors, in order, are

```
(3,0,17), (1,3,18), (0,-3,13),
(1,2,41), (1,3,18), (2,2,24).
```

Exactly five are distinct. Floor division gives

```
J = (0,1,2,3,5,6,8),
```

with consecutive vectors

```
(1,0,5), (1,1,6), (0,-1,1),
(1,3,10), (-1,-1,2), (2,1,11).
```

All six are distinct. The repeated fine vector `(1,3,18)` occurs at `4 -> 8`
and `22 -> 26`, with the **same child state pair `(1,3)`**; its two parent
vectors are `(1,1,6)` and `(-1,-1,2)`. Their correction differences are
`(-1,1,-6)` and `(3,5,10)` respectively, verifying (1) explicitly.

Seven selected vertices are the minimum possible number for a six-element
consecutive parent menu. This is not a claim that the final source index 32
or any other size parameter is optimal.

### 3.2 Actual duplicates do not repair the problem

Use

```
I = (4,13,14,15,16,26,35,36,37,38,39,40).
```

Its fine menu is exactly

```
{(2,0,36), (1,1,6), (0,-1,1), (1,0,5), (-1,5,42)}.
```

The raw parents are `(1,3,3,3,4,6,8,9,9,9,9,10)`. Removing repetitions leaves
`(1,3,4,6,8,9,10)`, whose six vectors are

```
(1,0,7), (1,0,5), (-1,2,7),
(2,1,11), (0,-1,1), (1,1,6).
```

For an increasing source path, floors are nondecreasing. Deleting duplicate
parents simply deletes zero parent edges: each remaining parent edge is
already the image of the original edge crossing between the two occupied
blocks. There is no further cancellation or relabelling that can merge the
six vectors above.

The gap estimate is actually favorable: every nonzero parent gap is at most
`ceil(B/4)` if the original gaps are at most B. **Menu cardinality, not gap
contraction, is the failed step in direct floor descent.**

## 4. Natural repairs: what works and what fails

### 4.1 Fixed-phase edges really do preserve the menu

**Lemma.** Fix `a in {0,1,2,3}`. Among edges with both endpoints congruent to
`a mod 4`, equality of fine displacement implies equality of parent
displacement. Consequently an already fixed-phase selected path has at most
as many parent labels as fine labels.

**Proof.** Put

\[
P_a(r)=2i^r d_a+c_{[r+\delta_a]_4},\qquad f_a(r)=[r+\delta_a]_4.
\]

For endpoints `4m+a,4l+a`, the fine vector has planar part
`4(z_l-z_m)+P_a(s)-P_a(r)` and height
`16(l-m)+f_a(s)-f_a(r)`. Its height modulo 16 determines the integer difference
`f_a(s)-f_a(r) in [-3,3]`. For fixed a, the residues of `P_a(r)` modulo 4,
ordered by `f_a(r)=0,1,2,3`, are

| a | Ordered planar residues |
|---|---|
| 0 | (0,0), (3,0), (3,1), (0,3) |
| 1 | (0,2), (1,0), (3,3), (2,3) |
| 2 | (2,2), (1,2), (1,3), (2,1) |
| 3 | (2,0), (3,2), (1,1), (0,1) |

For difference 1 the three planar differences are distinct; for difference
2 the two are distinct; for difference 3 there is only one. Negative
differences reverse these. Difference zero implies `r=s` and zero correction
difference. Therefore the fine vector determines the correction difference
in (1), proving the assertion. The checker independently checks all 16
ordered state pairs at each phase: exactly 13 residue bins, no ambiguity.

An already fixed-phase path with gaps at most B descends to gaps at most
`floor(B/4)`. This lemma does **not** say an arbitrary five-menu path can be
thinned to one phase with the same menu or a useful gap bound. Nor does it
ensure the resulting parent path is itself fixed-phase. □

### 4.2 Phase thinning can increase five to six

One actual five-menu path is

```
I = (0,1,12,13,25,36,48,49,60,61,73,88,100,111,112,124,135,147,148).
```

Its menu is

```
{(1,0,5), (3,0,43), (0,4,48), (0,-4,48), (-2,0,60)}.
```

Its phase-0 subsequence is

```
(0,12,36,48,60,88,100,112,124,148),
```

and has the six-element menu

```
{(4,0,48), (4,4,96), (0,-4,48),
 (-1,4,113), (0,4,48), (4,-4,96)}.
```

Here the original gaps are at most 15. This is a finite witness, consistent
with the old impossibility of an *infinite* five-menu path at that gap bound.
The checker also gives an independent phase-2 failure. It did **not** find a
path on which all four phase filters have six labels within the bounded
search. In particular this does not refute “some phase works” for a
hypothetical infinite path; that existential assertion remains open here.

### 4.3 Taking first or last selected points of blocks

Take

```
I = (2,3,4,11,12,27,28,35,36,37,38,39,40),
S = {(0,-1,1), (1,0,5), (1,1,30), (2,4,60), (1,1,6)}.
```

Retaining the **first** selected point of every occupied block gives

```
(2,4,11,12,27,28,35,36,40)
```

and exactly the six vectors

```
{(1,-1,6), (1,1,30), (0,-1,1),
 (2,4,60), (1,0,5), (3,1,18)}.
```

Retaining the **last** gives

```
(3,4,11,12,27,28,35,39,40)
```

and exactly the six vectors

```
{(1,0,5), (1,1,30), (0,-1,1),
 (2,4,60), (2,-1,13), (1,1,6)}.
```

Thus neither fine-level preprocessing preserves five. Moreover, if the
purpose of choosing representatives is merely to change the subsequent
floor path, it cannot help at all: every choice of one representative in
every occupied block gives the same list of parent indices.

### 4.4 Grouping loops at a correction state

Returning to the same full correction state cancels the endpoint terms:
a grouped parent edge is `D^{-1}(V_1+...+V_k)`. What is missing is a bound of
five on these **sums**, not the cancellation identity. Pigeonhole only gives
an infinitely recurring state; it gives neither bounded return lengths
along an arbitrary selected path nor five possible return sums.

For perspective, a residue automaton alone cannot supply such a rule. With
formal vectors `v=(1,0,1)` and `w=(0,1,16)`, the words `v w^k v^15` are first
returns to height residue 0 mod 16. They have distinct sums `(16,k,16+16k)`
for all k. **This is an abstract automaton example, not a path in Q** (and it
has collinear triples). It only rules out invoking a generic finite-state
pigeonhole argument without source-specific restrictions.

A separate bounded actual-Q search tested grouping at any of the 16 full
correction states: 500,000 DFS calls, at most 5,000 per starting index,
source endpoints at most 256, gaps at most 16, path length at most 64.
No six-loop-menu counterexample was found. This stronger full-state grouping
repair is therefore **not refuted here**, and it is certainly not proved.
The phase-loop counterexample above does refute the weaker phase-only version.

### 4.5 These are not just early-prefix accidents

All displayed actual-Q witnesses lie in `[0,148]`. They repeat with identical
fine and parent displacement data at indices translated by `256k` whenever
`q_k=0`: for `n<256`, `q_(256k+n)=q_n`, and for `m<64`,
`q_(64k+m)=q_m`. Summing the state blocks gives translated vertex copies at
both scales. Such k occur arbitrarily late by primitivity of the state
substitution. Thus a universal *local* lemma cannot be repaired merely by
excluding a finite initial source segment.

This still gives **no infinite five-menu path joining those copies**. It does
not refute an implication whose hypothesis is infinite extendability with
one fixed five-element menu, even after passing to tails.

## 5. A complete, genuinely richer escape test

Test exactly one retained vertex in every length-16 block, at an offset
chosen by the parent state:

\[
n_m=16m+a(q_m),\qquad a:\{0,1,2,3\}\to\{0,\ldots,15\}.
\]

These are strictly increasing. Their gaps are at most 31, so the old B=16
obstruction does not by itself dispose of the family. This is not a rerun of
the exhausted `(q_n,q_(n+1),n mod 4)` selectors or fixed edge recodings.

**Infinite displacement-menu completeness proof.** Twice iterating the exact
source identities gives, for `0<=a<16`,

\[
q_{16m+a}=[q_m+q_a]_4,\qquad z_{16m+a}=4z_m+i^{q_m}z_a.
\]

Define

\[
T_r(a)=\bigl(2i^r z_a+c_{[r+q_a]_4},\;4a+[r+q_a]_4\bigr).
\]

Every selected displacement, at a parent transition `r -> s`, is exactly

\[
E_{rs}=(8i^r,64)+T_s(a(s))-T_r(a(r)).                 \tag{3}
\]

The only parent transitions are the eight `s=r+1` or `s=r+2 mod 4`, and each
actually occurs infinitely often. Therefore the eight vectors in (3), with
coincidences removed, are **all and only** the infinite displacement menu.
There is no prefix-stabilization inference. The finite enumeration covers
all `16^4` offset functions, using this proved eight-edge completeness.

Result:

| Exact menu size | Number of offset functions |
|---|---:|
| 6 | 200 |
| 8 | 65,336 |
| Any other size | 0 |

For example, offsets `(0,0,15,15)` have exactly

```
{(7,0,65), (1,1,126), (-6,9,125),
 (-1,-8,65), (-1,-1,2), (0,-1,1)}.
```

Its maximum gap is 31 and it still needs six types. The checker additionally
compares (3) with independently built actual-Q coordinates for all 256
offset pairs at an actual occurrence of each of the eight transitions:
2,048 exact coordinate cross-checks. Runtime was about 0.1 seconds.

**Parent-review scope correction.** This family is different from the old
mod-4 selector family and is not disposed of by the gap-16 theorem alone.
However, it is already covered by the broader
[Gaussian-tag classification](gaussian-tags.md): the entire selected walk is
`W_m=8z_m+c'_r`, `H_m=64m+t'_r`, with `r=q_m` and
`(c'_r,t'_r)=T_r(a(r))`. Its all-pairs valuation identity is inherited from
`Q`. The prior analytic theorem therefore already supplies the six-step lower
bound for this whole family. The new value of the enumeration is the exact
200/65,336 menu histogram and coordinate checks, **not a newly excluded
construction class**. It does not classify selectors with memory, arbitrary
context, or other block-selection patterns.

## 6. Strongest next action and honest stopping point

**Pivot away from an undecorated pointwise menu-preservation lemma.** It is
exactly false, even on seven vertices and even arbitrarily late in the source.
Continue a descent attack only if it has a new invariant at the level of
**infinite extendability**, not an assumption that labels have unique parents.

The clean sufficient invariant for direct descent is this: among crossing
edges actually used by the path, each fine label has one correction difference
in (2), or more generally the union of all its resulting parent labels has
cardinality at most five. The fixed-phase lemma proves one concrete case.
A hypothetical path with this property keeps its menu budget and contracts
its gap bound to `ceil(B/4)`. To iterate, the invariant must be inherited or
re-established at every scale. Nothing here supplies that inheritance.

The compact 16-height-residue cocycle is the strongest useful algebraic
handoff. A next proof attempt should show that an infinite five-menu path's
recurrent residue/label structure forces a bounded-gap forbidden pattern, or
forces the above small parent-label union. Treating all finite paths alike
cannot achieve this: the exact counterexamples rule it out. Grouping at full
correction states remains a narrowly defined alternative, but it needs a
source-specific return-sum bound; the bounded unsuccessful search is not
support for such a theorem.

Stopped without increasing a gap cutoff, searching huge prefixes, claiming
finite positive evidence as infinity, or presenting method failure as
impossibility of the requested theorem. No substantive Python, packages,
network research, subprocess parallelism, or other agents were used.

## 7. Reproduction, bounded work, and files changed

From this isolated worktree, sequentially:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
mkdir -p .checkpoint-descent-adversary
node --max-old-space-size=128 \
  research/unit-step/explorations/descent-adversary-check.mjs \
  > .checkpoint-descent-adversary/check.jsonl
node --max-old-space-size=128 \
  research/unit-step/explorations/descent-adversary-block-selector.mjs \
  > .checkpoint-descent-adversary/block-selector.jsonl
```

The first checker generates the states by the alternating **binary** digit
sum, builds actual Q coordinates, validates all recurrence identities at
4,097 endpoints, verifies the residue tables, and finds the local witnesses.
Its first seven-vertex witness takes 53 DFS calls. Repair searches are capped
at 1,000,000 and 500,000 calls, respectively; the former is not an exhaustive
negative result. Deletion-minimization can introduce larger gaps, but retains
and checks the five-menu property. All final vector arithmetic is integral
and far inside JavaScript's exact integer range.

Observed runtime for the complete first checker was about 12 seconds; the
second below one second. The harness's inherited CPU affinity was verified
as core 2; native thread limits were 1. Both emit timestamps, code SHA-256, parameters, and
final outcomes. These deliberately bounded Node checks need no long-run
checkpoint mechanism; no computation exceeded 60 seconds. Each command is
idempotently rerunnable. Logs remain separate under the ignored checkpoint
directory and generated data are well under 1 MB. No exploration input,
manuscript, central checkpoint/problem file, or viz file was edited; no
commits, publication, or deployment occurred.

**New files only:**

* `research/unit-step/explorations/descent-adversary.md` — this report.
* `research/unit-step/explorations/descent-adversary-check.mjs` — exact endpoint,
  finite local witness, and bounded repair checks.
* `research/unit-step/explorations/descent-adversary-block-selector.mjs` —
  complete infinite-menu enumeration for state-dependent length-16 selectors.
