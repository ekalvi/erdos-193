# Return-block selectors of the six-step Gaussian walk

**Independent return-blocks track, September 6, 2026. Computer-assisted restricted
obstructions, not a solution of the minimum problem.** Base:
`aaf038f31f1433fc083360177efe8a67b67e5cb1`.

## 1. Verdict and exact scope

**No construction beating six was found.** The following are new restricted
results, with finite exhaustive steps explicitly identified below.

1. **Arbitrary selectors with gaps at most 16 cannot beat six.** If
   `n_0 < n_1 < ...` is any infinite sequence of indices of the specified
   Gaussian walk and `n_{j+1}-n_j <= 16` for every `j`, then its consecutive
   displacement set has at least six elements. No finite-state, periodicity,
   or local-dependence assumption is made on the selector. The statement also
   holds when the gap bound is only eventual, and after discarding any prefix.
2. **Every nonempty phase/transition selector needs at least six.** Let
   `q_n = sigma(n)` and retain exactly those vertices for which
   `(q_n,q_{n+1},n mod 4)` belongs to a chosen set `S`. There are exactly 20
   possible triples, hence 1,048,575 nonempty selectors. Every such selector
   has bounded gaps (a common proved bound is 511), and every one has at
   least six actual return displacements. Six is attained by retaining all
   vertices. Thus six is the exact minimum **in this selector family**.
3. **Complete state-union return menus.** For every nonempty
   `S subset {0,1,2,3}`, the selector `q_n in S` has exactly six or seven
   displacement types. The minimum six is attained precisely by
   `{0,2}`, `{1,3}`, and all four states. Exact enumeration uses substitution
   factor coverage, not presumed stabilization of a prefix.

Claims 1 and 2 are computer-assisted finite obstructions plus elementary
infinite recurrence arguments. Claim 3 is a finite exact factor calculation
with a proved completeness bound. They concern the particular existing
Gaussian walk, not all walks in `Z^3`. In particular they do **not** prove
`s_* >= 6`, `d_* >= 6`, or equality of the two minima.

### Prior inputs and attribution

The source is Kalviainen's six-step draft, using Cambie's offsets and Shallit's
basis encoding, built on the Cambie–Kalviainen Gaussian construction. The
four-uniform generator is already recorded in
[`design/UNIT-STEP-CONSEQUENCES.md`](../../../design/UNIT-STEP-CONSEQUENCES.md).
The prior read-only `A-SIX-STEP-AUDIT.md` was consulted for its explicit source
and tagging identities; it is an AI audit, not human approval. No manuscript
or prior audit was edited. The new obstruction arguments below use just the
explicit walk and its substitution; they do not assume its triple-avoidance
proof. Triple avoidance matters only when interpreting a successful
subsequence as a possible construction.

The original Erdős 193 theorem remains distinct and already settled. This
track addresses only the fixed-step-menu follow-up.

## 2. Definitions, proofs, and exact finite steps

### 2.1 The source and recurrence

Put

\[
q_n=\left[\sum_{j\ge0}(-1)^j b_j(n)\right]_4\in\{0,1,2,3\},
\qquad z_n=\sum_{t<n}i^{q_t},
\]

\[
(c_0,c_1,c_2,c_3)=(0,-1,-1+i,-i),\qquad
Q_n=(\Re(2z_n+c_{q_n}),\Im(2z_n+c_{q_n}),4n+q_n).
\]

The state word is the fixed point beginning in 0 of

\[
\mu(r)=r\,(r+1)\,(r-1)\,r\pmod4.
\]

Indeed `q_(4n+j) = q_n + (0,1,-1,0)_j mod 4`, directly from the binary
formula. Every `mu^2(r)` contains all four states. The only adjacent state
pairs are `r -> r+1` and `r -> r+2`: the increment follows from the number
of trailing binary ones, giving changes 1 and 2 respectively for even and
odd trailing-one counts. Each of the eight pairs occurs in the fixed point
(as can also be checked at indices at most 21).

The six increments, in the transition order `01,12,23,30,02/13,20/31`, are

\[
(1,0,5),(0,3,5),(-1,-2,5),(0,-1,1),(1,1,6),(-1,-1,2).
\]

**Recurring translated blocks.** The state block `mu^5(0)` of length 1024
occurs at indices `1024k` whenever `q_k=0`. Such `k` are arbitrarily large,
since every aligned block `mu^2(r)` contains 0. If a state block
`q_t,...,q_(t+L)` equals `q_0,...,q_L`, then

\[
Q_{t+j}-Q_t=Q_j-Q_0\qquad(0\le j\le L).
\]

This follows by summing the identical unit states and cancelling the
identical endpoint tags; heights differ just by the constant `4t`.
Thus the source contains arbitrarily late translated copies of the entire
finite configuration used in the next obstruction.

### 2.2 Arbitrary gap-16 selectors: finite certificate and infinite conclusion

Form the directed acyclic graph with starting vertices `0,...,15`, and an
edge `n -> n+d`, labelled by the **full integer vector** `Q_(n+d)-Q_n`, for
`0 <= n < 512` and `1 <= d <= 16`. Endpoints through 527 are included.
The graph's displacement universe has 544 distinct vectors.

**Exhaustive finite result:** no path starting at any of `0,...,15` reaches
512 while using at most five distinct labels. In fact the largest index
reachable under this label budget is 334. The maxima for the 16 starts are

```
start:  0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
max:  169 328 328 167 328 329 330 334 334 331 331 331 169 328 328 167
```

Two implementations independently give this result:

- JavaScript: states from the base-4 recurrence, vertices from the tagged
  Gaussian formula, memoized DFS for menus of size below five. It visits
  35,561,089 DFS calls.
- C++: states from the alternating **binary-digit sum**, vertices from the
  six-entry **transition table**, DFS with **no memoization**. It visits
  42,138,404 DFS calls.

Here is the exhaustive recursion, with `M` the labels already used:

```
search(n, M):
    if n >= 512: succeed
    for d = 1,...,16:
        v = Q[n+d] - Q[n]
        if v in M: search(n+d, M)
        else if |M| < 5: search(n+d, M union {v})
    fail
```

Every allowed continuation takes exactly one listed branch, and no listed
branch violates the gap or menu-size constraints. Induction on `512-n`
therefore proves the search complete. In the JavaScript version the pair
`(n,M)` determines all future choices, so caching a failed pair is sound.
The independent C++ version does not require this optimization. Arithmetic
is integral and comfortably within exact integer ranges. In particular,
vectors are not merged merely because they point in proportional directions.

**Infinite consequence.** Suppose an infinite subsequence had all gaps at
most 16 and a menu of at most five vectors. Choose an occurrence starting at
`t` of the above recurring 1024-state block after the first selected index.
The first selected index at least `t` is `t+j` with `0 <= j <= 15`: its
predecessor is below `t`, and the intervening gap is at most 16. Continue the
selected indices until first reaching at least `t+512`; the endpoint is at
most `t+527`. Translation identifies this segment with a forbidden graph
path. This is a contradiction. Taking `t` later also covers any eventual
gap bound or arbitrary finite prefix modification.

**What this actually forces:** any infinite five-menu subsequence, if one
exists, has infinitely many index gaps at least 17. Since a gap `d` has
height `4d+q_m-q_n >= 4d-3`, its menu must include a vector of height at
least 65. This is a restriction on subsequences of this `Q`, not a
coordinate-invariant restriction on arbitrary five-step constructions.

### 2.3 All phase/transition selectors: a finite family with a proved gap bound

Let `t_n=(q_n,q_(n+1),n mod 4)`. Its 20-symbol alphabet is

\[
\begin{aligned}
\mathcal A={}&\{(r,r+1,p):r\in\mathbb Z/4,\ p\in\{0,2,3\}\}\\
 &\cup\{(r,r+2,p):r\in\mathbb Z/4,\ p\in\{1,3\}\}.
\end{aligned}
\]

All additions in these triples are modulo 4. The induced substitution is

\[
\theta(r,s,p)=
 (r,r+1,0)\ (r+1,r-1,1)\ (r-1,r,2)\ (r,s,3).
\]

It follows from the source recurrence, not from agreement of finite
prefixes. Starting at `(0,1,0)` gives exactly `t_n`.
Every `theta^4(a)` contains all 20 letters. The checker verifies this finite
incidence statement for all 20 starting letters. Consequently, for any
nonempty `S subset A`, every aligned 256-letter block contains a selected
vertex. Consecutive selected vertices are therefore separated by at most
`2*256-1=511`. All 20 letters really occur, and the substitution is primitive.

For each of the `2^20-1` nonempty masks the checker scans the exact source
prefix and accumulates actual displacement vectors between consecutive
selected vertices. It stops only on finding six distinct vectors. Every
mask stops by vertex **727** (the maximum is achieved by the single letter
`(1,3,3)`, mask 32768 in the checker's ordering). Thus each mask has a
finite, actual witness against a five-vector menu. This is an exhaustive
negative certificate, not a positive inference from the number of vectors
observed in a prefix.

Primitivity also puts copies of every witnessing finite factor arbitrarily
far out in the decorated word: any factor occurs in an iterate of the
initial letter, and every sufficiently high iterate of every letter then
contains it. The same witnesses consequently obstruct every tail of each
selector. No unobserved return word could remove the six already proved.
The full selector has exactly the existing six-vector menu, establishing
optimality within this family.

As a redundant cross-check, all `2^16-1=65,535` nonempty selectors based only
on `(q_n,n mod 4)` were also enumerated; all six-vector witnesses end by
343. This smaller family is contained in the 20-symbol family.

### 2.4 Exact returns for all unions of states

For a nonempty state set `S`, every `mu^2(r)` contains a selected state, so
all return gaps are at most 31. A return including both endpoint states
therefore has length at most 32. Every such factor of the infinite state
word lies within `mu^3(ab)` for some actual adjacent state pair `ab`, since
`|mu^3(a)|=64` and a factor this short meets at most two consecutive aligned
blocks. Conversely, each of the eight blocks `mu^3(ab)` is an actual factor
of the source. Enumerating all consecutive selected endpoints within those
eight blocks therefore gives **all and only** the actual return
vectors, with no prefix-stabilization assumption.

The complete count and exact maximum-gap table is:

| Selected states | Distinct displacement count | Exact maximum gap |
|---|---:|---:|
| Any singleton | 7 | 7 |
| `{0,1}`, `{1,2}`, `{2,3}`, `{0,3}` | 7 | 3 |
| `{0,2}`, `{1,3}` | 6 | 3 |
| Any three states | 7 | 2 |
| All four states | 6 | 1 |

The full vector lists for all 15 sets are emitted by the checker. In
particular, returns to state 0 have exactly

\[
\{(0,-2,12),(0,2,12),(2,0,12),(-2,0,20),
  (-2,-2,24),(-2,2,24),(-2,0,28)\}.
\]

The even-state selector `{0,2}` has exactly

\[
\{(-1,-1,2),(-1,-3,6),(1,1,6),(1,3,10),(-2,0,12),(2,0,12)\},
\]

and the odd-state selector `{1,3}` has exactly

\[
\{(-1,-1,2),(1,-1,6),(1,1,6),(-1,1,10),(0,-2,12),(0,2,12)\}.
\]

These proper subsequences inherit avoidance from the existing construction
but do not improve its step count. Translating the first retained vertex
to zero handles a selector that does not retain index 0.

## 3. Reproduction and evidence limits

Run from the repository root, sequentially; no dependencies are installed.
All calculation is exact. Observed runtimes on the pinned CPU were about
1.5 seconds for the selector checker, 18 seconds for JavaScript gap-16 DFS,
and 2.5 seconds for C++ gap-16 DFS, excluding compilation. Each gap checker
atomically checkpoints completed starting positions with code/config
identity; interruption restarts only the unfinished starting position.
Progress logs and checkpoints stay outside proof artifacts in the ignored
`.checkpoint-return-blocks/` directory.

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p .checkpoint-return-blocks

node research/unit-step/explorations/return-blocks-check.mjs \
  > .checkpoint-return-blocks/selectors.jsonl

node --max-old-space-size=256 \
  research/unit-step/explorations/return-blocks-gap-check.mjs 16 512 \
  > .checkpoint-return-blocks/gap16.jsonl

src=research/unit-step/explorations/return-blocks-gap-verify.cpp
g++ -O2 -std=c++17 -Wall -Wextra -pedantic \
  -DSOURCE_SHA=\"$(sha256sum "$src" | cut -d' ' -f1)\" \
  "$src" -o .checkpoint-return-blocks/gap-verify
.checkpoint-return-blocks/gap-verify 16 512 \
  > .checkpoint-return-blocks/gap16-verify.log
```

The substantive assertions are the finite search completeness arguments
and the substitution recurrence/coverage arguments above, together with
the exhaustive checker outputs. These are computer-assisted results, not
Lean certification or independent human approval. The two gap searches
use different state generators, coordinate implementations, and search
optimizations. No large chord test or fixed edge recoding was rerun.

## 4. Implications for the actual minima

**No new bound on `d_*` or `s_*` follows.** The established inequality
`4 <= d_* <= s_*` remains, with the existing six-step upper bound having its
previous manuscript/review status. A successful five-step *subsequence*
would still prove `s_* <= 5` and hence `d_* <= 5`; this track has not
constructed one or ruled them all out. The negative results above only
exclude the stated return schemes for this particular six-step walk.

In particular, a fixed finite menu for a subsequence automatically gives a
finite gap bound: if its largest height is `H`, then every gap satisfies
`4d-3 <= H`, hence `d <= floor((H+3)/4)`. Thus proving the gap obstruction
for **all** finite bounds would settle the entire subsequence loophole.
The proved case `B=16` does not justify that universal extrapolation.

## 5. Strongest next attack and stopping reason

The strongest next attack is a **scale-uniform return obstruction**: use the
base-4 substitution to relate a hypothetical five-menu selected path to a
coarser one and reduce its maximal gap. Such a descent must track the
selected endpoints inside substitution blocks and their state tags;
ordinary grouping at multiples of four does not preserve the five-vector
menu automatically. No such descent is proved here. This is the explicit
missing step between a bounded-gap obstruction and excluding every
finite-menu subsequence.

For a construction search, one must leave the entire 20-symbol
phase/transition family and allow gaps at least 17 infinitely often.
Larger contexts or selectors with their own memory remain open. The parity
selectors demonstrate that genuine vertex deletion can preserve six
rather than necessarily increasing the menu, but they offer no five-step
witness.

Stopped after obtaining and independently checking the restricted
obstructions, rather than escalating an arbitrary gap cutoff or treating
finite positive evidence as an infinite theorem. The planned 12–18 minute
research budget is respected; no rival new outputs were read, and there
were no commits, manuscript/central-checkpoint/site edits, or package
installations.

### Files changed

All are new files:

- `research/unit-step/explorations/return-blocks.md` — this report.
- `research/unit-step/explorations/return-blocks-check.mjs` — exhaustive
  phase/transition selector checks and complete state-union return menus.
- `research/unit-step/explorations/return-blocks-gap-check.mjs` — exact,
  resumable bounded-gap DFS.
- `research/unit-step/explorations/return-blocks-gap-verify.cpp` — independent
  exact, resumable validator with binary states and no memoization.

Ignored logs/checkpoints and the compiled checker are under
`.checkpoint-return-blocks/`; they are not final proof artifacts.
