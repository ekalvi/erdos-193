# Track C: a finite return alphabet with an all-ratios boundary condition

**September 6, 2026. Research note with elementary proofs and exact finite
checks; not a resolution of the four-letter threshold.** This is the bounded
Task C deliverable from [the parallel handoff](../PARALLEL-TASKS.md#c-attack-the-four-letter-basis-threshold).
It concerns the [positive-basis follow-up](../PROBLEM.md), not another proof
of the already settled original Erdős 193 theorem.

## Outcome

1. **Proved reduction:** a four-letter solution exists if and only if an
   infinite sequence over an explicit **117-word ternary return alphabet**
   satisfies the cross-section condition in §3. The condition includes every
   partial endpoint and every unequal interval ratio; it is not merely a test
   at return times. There are 41 return-count vectors and 42 possible prefix-
   count vectors, but the actual prefix sets must stay attached to their words.
2. **Sharp local obstruction:** an ordinary abelian-square-free word containing
   a weak abelian square must use all four letters, and the shortest such
   factor has length **12**, with block lengths 4 and 8. The finite certificate
   lists **all 164 shortest factors up to renaming**, not just one example.
3. **Exact finite validation:** independent rank and cross-section tests agree
   on all **5,262,444 vertex triples** in the **13,689 pairs** of admissible
   internal gaps. These checks exercise the reduction; its infinite equivalence
   is proved below, not inferred from them.

Neither $d_* = 4$ nor $d_* > 4$ is established. The ordered-pair possibilities
in [the joint formulation](../JOINT-MINIMUM.md#3-current-bounds-and-decisive-outcomes)
are unchanged, as is the pending-review status of the proposed six-step upper
bound. In particular, even an eventual four-letter construction would establish
$d_*=4$, not automatically $s_*=4$.

## 1. The small-alphabet lemma and its sharp four-letter boundary

Write $\psi(v)$ for a word's Parikh vector. An **ordinary abelian square**
is a pair of consecutive nonempty blocks with equal lengths and equal counts.
A **weak abelian square** only requires
$\psi(x)/|x|=\psi(y)/|y|$.

### Lemma 1 (at most three letters)

An ordinary abelian-square-free word on at most three letters is also weak
abelian-square-free. The maximum ordinary-free lengths on one, two, and three
letters are respectively $1,3,7$.

**Proof.** The complete ternary extension tree, with letters renamed in order
of first appearance, is:

| Length | Canonical ordinary-free words |
|---|---|
| 0 | empty word |
| 1 | `0` |
| 2 | `01` |
| 3 | `010`, `012` |
| 4 | `0102`, `0120`, `0121` |
| 5 | `01020`, `01021`, `01201`, `01202`, `01210` |
| 6 | `010201`, `010210`, `010212`, `012010`, `012101` |
| 7 | `0102010`, `0102101`, `0121012` |
| 8 | none |

Each row is obtained by appending every already used letter or the next new
letter, allowing at most three, and rejecting an ordinary square ending at the
new position. Any newly introduced square must end there, so this generates
all words inductively. Restricting the same tree to at most one or two letters
gives the stated smaller maxima. This is the previously recorded
[ternary obstruction](../../../design/UNIT-STEP-4D-5D-INVESTIGATION.md#1-why-three-positive-coordinate-directions-cannot-work),
not a new lower bound. The accompanying checker independently enumerates all
9,841 labelled ternary words of lengths zero through eight and verifies the
whole tree using a different, rank-based test.

Suppose now that an ordinary-free word contains a weak square $xy$. Its count
vectors have the form

$$
\psi(x)=hR,\qquad \psi(y)=kR,
$$

where $R$ is a nonzero primitive nonnegative integral vector and $h,k$ are
positive integers. (Divide either count vector by the gcd of its coordinates;
integrality of the other vector makes its multiple of this primitive vector
an integer.) If $h=k$ this is already an ordinary square. Otherwise $h+k\ge3$.
If $t$ letters occur in $R$, then

$$
|xy|=(h+k)\|R\|_1\ge3t.
$$

For $t=1,2,3$ this exceeds the corresponding maximum ordinary-free length
$1,3,7$. The factor $xy$ uses only those $t$ letters, a contradiction. $\square$

### Corollary 2 (first genuinely unequal obstruction)

Every weak square in an ordinary-free four-letter word contains all four
letters in **each** block and has length at least 12. At length 12 its two
Parikh vectors are $(1,1,1,1)$ and $(2,2,2,2)$, in either order.

The bound is attained by

$$
\underbrace{01021323}_{(2,2,2,2)}\quad\big|\quad
\underbrace{0213}_{(1,1,1,1)}.
$$

This word has no ordinary abelian square. To verify that last assertion by
hand, for each half-length $m=1,\ldots,6$ compare all pairs of adjacent
$m$-letter blocks: none have equal counts. The exact checker performs those
comparisons and independently finds precisely the vertex triple $(0,8,12)$.
The lower bound follows from Lemma 1 and $3t$ with $t=4$; equality forces
$h+k=3$ and all four coordinates of $R$ to equal one. $\square$

The complete canonical ordinary-free tree on four letters has these row sizes:

| Length | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Words | 1 | 1 | 1 | 2 | 4 | 11 | 27 | 66 | 149 | 328 | 640 | 1216 | 2130 |

Of the 2,130 final words, exactly **164** have a weak square: 82 split after
four letters and 82 after eight. Their full list and splits are in
[`checks/four-letter-returns.json`](../checks/four-letter-returns.json).
Every proper factor of each is weak-square-free, by the lower bound and
ordinary avoidance. Thus the list is a complete local obstruction certificate
at the *first* unequal length, not an exhaustion of the four-letter extension
tree: **1,966 canonical words still survive at length 12**. Longer minimal
obstructions are not classified here.

## 2. Every four-letter solution has bounded ternary returns

In any weak-square-free four-letter word, **every length-eight factor uses all
four letters**: otherwise the ternary ordinary obstruction applies. Therefore
each letter occurs infinitely often with gaps at most eight, and consecutive
identical letters are forbidden.

Relabel the first letter as 0. There is a unique decomposition

$$
w=0u_1\,0u_2\,0u_3\cdots,
$$

where every $u_t$ is a nonempty ordinary-free word over $\{1,2,3\}$, of length
at most seven. Define the finite alphabet

$$
\mathcal U=\{u\in\{1,2,3\}^{*}:1\le |u|\le7,\ u\text{ has no ordinary abelian square}\}.
$$

Its numbers of words at lengths $1,\ldots,7$ are

$$
3,6,12,18,30,30,18,\qquad |\mathcal U|=117.
$$

These counts follow by labelling the tree in §1, and are independently checked
by full ternary enumeration. By Lemma 1 all these gaps are weak-free as well.
Here $u_t$ is the *marker-free gap*; $0u_t$ is the return block and has length
between two and eight. The received manuscripts are not being replaced by a
new four-letter construction: no successful infinite ordering of these return
blocks is supplied.

For $u\in\mathcal U$, let

$$
q(u)=\psi_{123}(u)\in\mathbb Z_{\ge0}^3,\qquad
B(u)=\{\psi_{123}(v):v\text{ is a prefix of }u\}.
$$

The empty and full prefixes are included. The 117 words give 41 distinct
$q(u)$ vectors and 696 word/prefix pairs. Moreover,

$$
\bigcup_{u\in\mathcal U}B(u)=\{0\}\cup\{q(u):u\in\mathcal U\}
$$

has 42 vectors: a nonempty prefix is itself in $\mathcal U$, and every word
is its own prefix. These are bounded **endpoint types**, not a proof that the
entire infinite avoidance condition has finitely many states.

## 3. Exact occurrence-count / cross-section reduction

For an arbitrary infinite sequence $(u_t)_{t\ge1}$ in $\mathcal U$, set

$$
X_0=X_1=0,\qquad X_t=\sum_{r=1}^{t-1}q(u_r)\quad(t\ge1),
$$

$$
C_0=\{0\},\qquad C_t=X_t+B(u_t)\quad(t\ge1).
$$

The vertices of the corresponding four-letter basis walk are **exactly**

$$
\{(0,0)\}\ \cup\ \bigcup_{t\ge1}\{(t,x):x\in C_t\}\ \subset\mathbb Z\times\mathbb Z^3.
$$

Indeed layer $t$ starts just after the $t$-th 0, runs through all prefixes of
$u_t$, and ends just before the next 0. Its original vertex indices are

$$
t+\sum_{r<t}|u_r|+|v|\qquad(v\text{ a prefix of }u_t).
$$

Distinct layers and the increasing prefix lengths account for every vertex
once. The exceptional layer 0 is necessary: dropping the origin would lose
some violations, including the example in §1.

### Theorem 3 (equivalent four-letter problem)

$\mathcal B(4)$ holds if and only if there is an infinite sequence in
$\mathcal U$ for which, for every $0\le a<b<c$ and every
$x\in C_a,y\in C_b,z\in C_c$,

$$
\boxed{(c-b)(y-x)\ne(b-a)(z-y).} \tag{R}
$$

**Proof.** Necessity follows from §2 and the vertex decomposition: the first
coordinate of these three vertices is the occurrence count of 0, so equality
in (R) is precisely their collinearity.

Conversely, construct $w=0u_1 0u_2\cdots$ from a sequence satisfying (R).
Suppose three chronologically ordered vertices are collinear, with successive
nonzero displacements $U,V$. All coordinates are nonnegative, and their sums
are positive block lengths, so $U$ and $V$ must be **positive** scalar
multiples. In particular, their marker coordinates are either both zero or
both positive; exactly one zero is impossible.

If both marker increments are zero, all three vertices lie in one layer, so
the offending pair is entirely inside one gap $u_t$. Lemma 1 rules this out.
If both are positive, their layers satisfy $a<b<c$, and proportionality is
exactly equality in (R), also impossible. Thus the whole word is weak-square-
free. This proves both directions without assuming equal original lengths or
aligned endpoints. $\square$

### Finite offsets, still unbounded scales and ratios

Put $m=b-a$, $n=c-b$, $A=X_b-X_a$ and $D=X_c-X_b$. Writing
$x=X_a+\alpha$, $y=X_b+\beta$, $z=X_c+\gamma$, a violation is equivalent to

$$
\boxed{nA-mD=n\alpha-(m+n)\beta+m\gamma,} \tag{B}
$$

where $\alpha\in B(u_a)$, $\beta\in B(u_b)$ and $\gamma\in B(u_c)$;
for $a=0$, interpret the first offset as zero. This is an all-ratios boundary
condition with finitely many possible individual offsets. It gives a precise
proof obligation for a proposed substitution or other mechanism on
$\mathcal U$: exclude (B) for every $a,m,n$ and every **compatible** offset
triple. Dividing the equation by $\gcd(m,n)$ can normalize its coefficients,
but does **not** remove the common spacing from the return sums or bound the
coprime ratio. There is no finite-state certification theorem here.

Do not replace the sets $B(u)$ by just $q(u)$. Nor may one choose arbitrary
members of the 42-vector union independently and call that an equivalent
condition: that relaxes the endpoint compatibility and can introduce spurious
violations. The 117 word labels retain exactly the information needed here.

### Why after-marker endpoints alone are insufficient

For the shortest example `010213230213`, the gaps are
`1`, `21323`, `213`. The origin and the vertices just after a 0 occur at
indices $0,1,3,9$, with points

$$
(0,0,0,0),\quad(1,0,0,0),\quad(2,1,0,0),\quad(3,2,2,2).
$$

They have no collinear triple, but the full prefix has

$$
P_0=0,\quad P_8=(2,2,2,2),\quad P_{12}=(3,3,3,3).
$$

In (B), take layers $(a,b,c)=(0,2,3)$ and offsets
$\alpha=0$, $\beta=(1,2,2)$, $\gamma=(1,1,1)$; then both sides equal
$(-1,-4,-4)$. Both endpoint offsets are full gap prefixes, which is why they
must be included. This finite counterexample shows exactly what a return-cut
prefix test can miss; it does not assert that a particular infinite return-cut
construction exists.

## 4. Reproduction and verification scope

Run from the repository root, using one computational core:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
node research/unit-step/tracks/check_four_letter_returns.mjs --help
# Fresh independent recomputation and comparison with the tracked certificate:
node research/unit-step/tracks/check_four_letter_returns.mjs \
  --work-dir .checkpoint-unit-step-four-returns-review
# A repeated command resumes validated completed stages without recomputation.
```

Use `--write` to intentionally regenerate
[`checks/four-letter-returns.json`](../checks/four-letter-returns.json).
The default work directory is `.checkpoint-unit-step-four-returns`. A source
hash and fixed bounds identify the calculation; incompatible or corrupt
checkpoints are rejected. Completed stages are written atomically. SIGINT and
SIGTERM stop after the current short stage and preserve its checkpoint.
Timestamped JSONL logs, elapsed time, stage throughput, estimated remaining
time, resource settings, and final status live in the work directory, not in
the certificate. A fresh run takes about one second on the development host.
No Python process, worker pool, long prefix scan, or fixed g85 relabelling
search is involved.

The checks cover:

- the entire labelled ternary tree through length eight, with ordinary
  suffix-count tests independently compared against all six rank minors;
- the entire canonical ordinary-free quaternary tree through length twelve,
  including the complete list of shortest genuinely unequal obstructions;
- reconstruction of the full basis vertices from the cross-sections, and
  equality of the **complete violating-triple sets**, not just yes/no answers,
  for every finite word $0u0v0$ with $u,v\in\mathcal U$;
- the unequal-length example and its failure to be detected at return cuts;
- an explicitly periodic non-candidate exercising marker-count ratios $1:3$
  and $3:1$, and the common spacing in $2:2$, against the independent rank test.

The finite-word harness permits a final empty gap to encode the last marker
of $0u0v0$. It is a terminal singleton layer, **not** a 118th internal gap.
All tested words have at most 17 letters; integer products are at most $17^2$,
so the JavaScript arithmetic is exact. The written proof, rather than finite
arithmetic, supplies the unbounded quantifiers of Theorem 3.

**Recorded validation:** fresh recomputation and full checkpoint reuse passed;
SIGINT and SIGTERM were each tested after the first completed stage, then
successfully resumed. Incorrect source identities, corrupt checkpoint digests,
non-prefix checkpoint stages, and missing, duplicate, or altered certificate
rows were rejected. The seven local links in this note, JavaScript syntax,
`node research/unit-step/check.mjs`, and
`node research/unit-step/joint_minimum_examples.mjs` also passed. These are
local validation results, not a report of independent collaborator review.

## 5. Blocker, next step, and synthesis proposal

**Remaining blocker:** (B) still involves arbitrarily long return sums and
arbitrary positive $m,n$. The finite return alphabet and the 164 local
obstructions do not imply that an infinite path exists or that every path
terminates. Pairwise admissibility of return words is not sufficient.

A next proof-oriented task is to seek a return substitution together with a
boundary-descent lemma for (B), keeping each actual prefix set in the state.
Any claim of a finite certificate must first prove a bound on the required
ancestor states **uniformly in both coprime ratios and common spacings**.
The 164 length-12 patterns can be used as sound local pruning rules, but a
larger prefix scan is not a substitute for that lemma.

For later integration, propose adding this track to the checkpoint as a
**proved reformulation plus finite local certificate, with no changed bound**.
The central checkpoint, problem statement, manuscripts, and production `viz/`
site are deliberately unchanged: the original unconditional proof and the
follow-up's best dimension bounds have not changed, and the six-dimensional
draft remains pending review. No publication, correspondence, merge, or
deployment is part of this work.

**Attribution.** The normalized-count / basis-walk formulation is Shallit's;
the small ternary obstruction is reused from the repository investigation
(which records Brown's reference). This track is an AI-assisted research
reduction and finite audit, not collaborator approval, a new manuscript byline,
or a claim to have established priority in the literature. Cambie–Kalviainen's
original theorem and the document-specific follow-up attributions remain as
recorded in [the archive](../../../paper/followups/README.md).
