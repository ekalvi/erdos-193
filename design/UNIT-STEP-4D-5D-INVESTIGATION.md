# Unit-step dimensions four and five: first investigation

Date: September 5, 2026. Status: research notes for vetting, not a publication.

## Outcome and scope

**No infinite four- or five-dimensional construction has been proved here.**
The current six-dimensional draft remains the upper-bound construction. The
standard-basis variant has bounds `4 <= k_min <= 6`, subject to vetting that
six-dimensional draft. Nothing below improves the upper bound.

This question restricts every step to a **positive standard basis vector**.
It must not be confused with the original small-step problem in dimension
three, for which the repository contains a construction using other vectors.
The three-dimensional impossibility below applies only to the unit-step variant.

Results of this investigation:

1. A short, exhaustive certificate reconfirms that eight steps in three positive
   coordinate directions always produce a collinear triple.
2. **Every fixed coding of the eight alternating-rule transitions into five
   letters fails.** All 1,050 codings have explicit equal-block counterexamples
   within 85 steps. All 1,701 four-letter codings fail within 44 steps.
3. Shallit's five-letter substitution passes an exact all-triples check of
   38,417 vertices. This is finite evidence, not an infinite proof.
4. Exact substitution algebra proves descent for block-aligned triples and
   identifies the partial-block correction terms obstructing naive descent.

No family-page or other public-site claim is added. These files and results
remain local research until the user chooses to publish them.

## 1. Why three positive coordinate directions cannot work

Represent a walk by a word over its coordinate directions. Let `F(n)` be the
vector counting letters in its first `n` positions, so the walk is `P_n=F(n)`.
For `a<b<c`, put `p=b-a`, `q=c-b`. Collinearity is exactly

\[
q(F(b)-F(a))=p(F(c)-F(b)).
\]

In particular, two consecutive equal-length blocks with identical letter counts
produce a midpoint triple. Such a pair is usually called an abelian square.

The following is the complete extension tree of ternary words avoiding these
squares, after renaming letters in order of first appearance:

| Length | Surviving canonical words |
|---|---|
| 1 | `0` |
| 2 | `01` |
| 3 | `010`, `012` |
| 4 | `0102`, `0120`, `0121` |
| 5 | `01020`, `01021`, `01201`, `01202`, `01210` |
| 6 | `010201`, `010210`, `010212`, `012010`, `012101` |
| 7 | `0102010`, `0102101`, `0121012` |
| 8 | none |

For example, extending `0102010` by `0`, `1`, or `2` creates respectively
`0|0`, `01|01`, or `0102|0102`. The other two seven-letter rows are equally
checkable. Every discarded extension contains two adjacent blocks with the
same counts, so the table proves the eight-step upper bound. The seven-letter
examples show sharpness.

Two independent implementations also checked all `3^8=6,561` words. The first
uses primitive chord directions, while the second directly compares letter
counts of adjacent equal-length blocks. This is a **finite exhaustive proof of
impossibility**, not an extrapolation about a sampled infinite word.

Shallit's manuscript cites T. C. Brown, *Is there a sequence on four symbols in
which no two adjacent segments are permutations of one another?*, American
Mathematical Monthly 78 (1971), 886–888, for this lower bound. The certificate
above is independently verifiable and does not depend on that citation.

## 2. A stronger obstruction for modifying rules 85 and 170

For rule 85, let

\[
\sigma(n)=\sum_{j\ge0}(-1)^j b_j(n)\pmod4.
\]

Use this fixed ordering of its eight transition types:

\[
(01,12,23,30,02,13,20,31).
\]

A fixed coding assigns one coordinate direction to each transition. It may
identify any transitions, not only ones whose vectors coincide under Cambie's
offsets. Thus it is a strictly broader experiment than merging the six vectors
in the existing proof.

Up to permutation of the new coordinate names, all onto codings are the set
partitions of eight objects into `k` nonempty classes. Restricted-growth strings
enumerate these without omission or duplication. Independently, the Stirling
recurrence `S(n,k)=k*S(n-1,k)+S(n-1,k-1)` verifies the totals.

| Target dimensions | Codings exhausted | Counterexamples | Latest endpoint needed |
|---|---:|---:|---:|
| 4 | 1,701 | 1,701 | 44 |
| 5 | 1,050 | 1,050 | 85 |

The run generated 256 steps but every saved counterexample uses only the first
85. The independent checker regenerates only those 85 steps using a different
bit-state implementation, checks every witness by integer cross multiplication,
and checks all coding identities and counts. Every witness in fact has equal
adjacent block lengths.

**Conclusion:** no fixed assignment of four or five positive coordinate steps
to these eight transitions produces a good infinite word. This is a
computer-assisted finite obstruction with explicit certificates, not merely a
failure to find a coding.

Rule 170 negates every state modulo four. Its transition word is therefore the
same abstract eight-letter word after a bijective renaming, so the obstruction
applies to it too.

This does **not** rule out context-dependent encodings, changing the underlying
word, or unrelated four- or five-dimensional constructions. Nor does it prove
that every other signed rule has the same fixed-coding obstruction.

### Smaller certificate: all fifteen mergers of the existing six directions

Write

\[
A=01,\ B=12,\ C=23,\ D=30,\ E=\{02,13\},\ F=\{20,31\}.
\]

Identifying any two of these six letters gives the following midpoint triple
of prefix indices in the resulting five-dimensional walk:

| Merged letters | Indices `(a,b,c)` |
|---|---|
| A,B | (3,4,5) |
| A,C | (6,9,12) |
| A,D | (2,3,4) |
| A,E | (0,1,2) |
| A,F | (5,6,7) |
| B,C | (19,20,21) |
| B,D | (28,35,42) |
| B,E | (11,14,17) |
| B,F | (4,5,6) |
| C,D | (10,11,12) |
| C,E | (9,10,11) |
| C,F | (20,21,22) |
| D,E | (1,2,3) |
| D,F | (14,17,20) |
| E,F | (41,55,69) |

For example, after merging E and F, the intervals `[41,55)` and `[55,69)`
both have counts `(3,2,2,3,4)` in the five remaining coordinates.

## 3. Shallit's five-letter candidate

Let `h` be the 14-uniform substitution on letters modulo five determined by

```
h(0) = 01213101314310
h(r) = h(0) + r (letterwise modulo 5).
```

Because `h(0)` starts with zero, its iterates converge to an infinite fixed
point beginning in zero. Counting its five letters gives a standard-basis walk
in `N^5`. To prove that it works one must exclude adjacent blocks with the same
**normalized** counts, including blocks of different lengths. Proving only
ordinary abelian-square avoidance would not suffice.

### Finite evidence

`design/verify_unit_step_prefix.cpp` checked the complete prefix `h^4(0)`:

- 38,416 steps, hence **38,417 vertices**;
- **737,913,736 chords**, exactly `38417*38416/2`;
- no two chords from a common starting vertex have the same primitive integer
  direction;
- therefore no collinear triple anywhere in that prefix, for equal or unequal
  adjacent lengths.

The calculation uses integer gcds and exact vector equality, not floating-point
angles or a sampled subset of triples. One core completed it in about 137 seconds
on this run. Hash-table collisions cannot affect the result because full vector
keys are compared for equality.

This does not establish the infinite claim. There is no proved finite-check
threshold that promotes this prefix result to an infinite theorem.

### Exact descent available so far

The incidence matrix, with column `r` counting the letters of `h(r)`, is

\[
M=\begin{pmatrix}
3&1&3&1&6\\
6&3&1&3&1\\
1&6&3&1&3\\
3&1&6&3&1\\
1&3&1&6&3
\end{pmatrix},\qquad \det M=5894=14\cdot421.
\]

For the prefix-count vector `F(n)`,

\[
F(14n)=MF(n).
\]

Since `M` is invertible over the rationals, a collinear triple at indices
`14a,14b,14c` implies one at `a,b,c`. Thus a minimal counterexample cannot have
all three indices divisible by 14.

More generally, with `w_n` the fixed-point letter and `B(r,t)` the count vector
of the first `t` letters of `h(r)`,

\[
F(14n+t)=MF(n)+B(w_n,t),\qquad 0\le t<14.
\]

If a proposed triple has interval lengths `p,q`, dividing its collinearity
identity by `M` introduces

\[
-M^{-1}\big(qB_a-(p+q)B_b+pB_c\big).
\]

These terms need not vanish. They must be controlled before descent can prove
anything about arbitrary triples.

As an exact diagnostic, put

\[
f(x)=3+6x+x^2+3x^3+x^4.
\]

For a primitive fifth root `zeta`, multiplication by `f(zeta)` on the
four-dimensional frequency-deviation space has characteristic polynomial

\[
t^4-t^3+31t^2-51t+421.
\]

Its norm is 421. The squared singular values of `M` are
`196`, `21-2*sqrt(5)` twice, and `21+2*sqrt(5)` twice. In particular its inverse
contracts, which makes a bounded-correction/desubstitution strategy plausible,
but contraction alone does not give a finite certificate for arbitrary `p:q`.

There is a fifth root `279 mod 421` at which `f` vanishes. The algebra probe
exhausts the 70 possibilities `(letter, offset)` at each boundary and tests

\[
t_a-2t_b+t_c\equiv0\pmod{14},\qquad
B_a(279)-2B_b(279)+B_c(279)\equiv0\pmod{421}.
\]

It verifies the resulting parent corrections exactly using `M^{-1}`. There
are **170 boundary triples with a nonzero integral correction**, even with the
equal-length coefficients `1,-2,1`. These are algebraically allowed boundary
cases, **not 170 actual collinear triples** in the fixed point.

For a simple example, `h(0)` starts and ends in zero, so

\[
B(0,1)-2B(0,0)+B(0,13)=Me_0.
\]

The residues therefore do not force the endpoints to block boundaries. A proof
must handle such partial-block cases and all unequal-length ratios rather than
assuming them away.

## 4. Reproduction and validation

Run from the repository root, with at most one worker per command:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
python3 design/unit_step_dimension_probe.py

src=design/verify_unit_step_prefix.cpp
g++ -O2 -std=c++17 -Wall -Wextra -pedantic \
  -DSOURCE_SHA=\"$(sha256sum "$src" | cut -d' ' -f1)\" \
  "$src" -o /tmp/verify_unit_step_prefix
/tmp/verify_unit_step_prefix --steps 38416

uv run --with sympy python design/shallit_substitution_algebra.py
python3 design/check_unit_step_dimension_results.py --binary /tmp/verify_unit_step_prefix
```

Final evidence artifacts:

- `results/unit-step-dimension-probe.json`: full coding/witness certificates,
  ternary lower-bound summary, and code/config identity;
- `results/shallit-five-prefix.json`: the exact finite-prefix result;
- `results/shallit-substitution-algebra.json`: exact matrix and correction data.

Checkpoints and timestamped logs are under ignored `.checkpoint-*` directories,
not in the final artifacts. Identical invocations resume validated progress;
incompatible checkpoints are rejected. C++ interruption repeats only the
unfinished anchor. The Python finite-coding audit checkpoints completed codings.
The symbolic diagnostic and each independent validation task are small atomic
units which are reused after completion.

Validation passed: independent ternary exhaustion, all 2,751 coding certificates,
primitive-direction vs direct triple checks on all ternary six-letter words,
C++ known-positive/known-negative finite cases, C++ SIGTERM/resume and incompatible
checkpoint rejection, and every saved algebraic correction.

## Next proof-oriented step

Keep Shallit's five-letter word as the leading candidate. Seek a certified
reduction of **all** normalized-count coincidences to a finite set of boundary
states, or find an exact counterexample. The missing theorem is such a reduction,
not a larger finite-prefix test. For our alternating word, any further reduction
must change more than its fixed eight-transition labeling.
