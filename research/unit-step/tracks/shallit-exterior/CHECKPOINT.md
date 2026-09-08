# Exterior-descent attempt: stopped, candidate still open

**September 7, 2026. Branch: `research/shallit-exterior-descent`.**
Based on `09c68d0`. Earlier geometry/midpoint work is preserved separately at
`e39f264` on `try-shallit-5d-basis-pattern-3d-geometry`; it was not merged here.
Maintenance finished before this attempt resumed. No owned calculations remain
running. No deployment, correspondence, central-bound changes, or site changes.

## Target and decision

The authorized target is the exact pair in [JOINT-MINIMUM.md](../../JOINT-MINIMUM.md).
A complete proof for Jeffrey Shallit's five-letter word would give an infinite
5D basis construction, hence `d_* <= 5`, but would not alone give a fixed integer
five-step 3D construction or determine either exact minimum.

This attempt replaced explicit length-ratio carries by **exact exterior rank
data**, retaining the nonlinear rank condition rather than a convex relaxation.
The proposed finite enumeration still fails: even primitive integer exterior
states have an unbounded algebraic inverse-state family. No sufficient
fixed-point-language filter was obtained. **Stop here; no construction, universal
lower bound, or elimination of a possible minimum pair resulted.**

This is an AI-assisted stopping analysis, not human mathematical review. The
candidate is not refuted, and more expressive arithmetic or language-dependent
invariants are not excluded.

## The attempted descent

Use Shallit's substitution `h(0)=01213101314310`, with other images obtained by
cyclic letter shifts. Let `M` be its incidence matrix. For adjacent child count
vectors `U,V`, all ten coordinates of `W=U∧V` vanish exactly when the corresponding
three basis vertices are collinear, with no length ratio specified.

Writing the parent counts as `X,Y` and boundary corrections as `A,B` gives

\[
 U=MX+A,\quad V=MY+B,
\]
\[
 W=(\mathop{\bigwedge}\nolimits^2M)(X\wedge Y)
       +(MX)\wedge B+A\wedge(MY)+A\wedge B.
\]

The exterior matrix is invertible: its determinant is `5894^4`. Its least
singular value is greater than 16, whereas the largest singular value of `M`
is 14. The checker verifies positive leading principal minors of
`E^T E-256 I` for `E=∧²M`; the nonnegative row/column sums of `M` are all 14.
Thus there really is a favorable expansion gap, not merely numerical evidence.

However, the boundary terms still contain `X,Y`. The gap supplies estimates
proportional to interval length, not an absolute integer-state bound. Merely
normalizing an area vector by its gcd does not remove this problem.

## Exact obstruction to primitive raw-state finiteness

Put `N=5894`, let `1` be the all-ones vector, and set

\[
 v=(227,-473,-53,-305,1025),\qquad Mv=Ne_0.
\]

For **every integer `k>=1`**, take

\[
 a=Nk+1,\quad b=N(k+1)+1,\quad C=14k\mathbf1-e_0,
\]
\[
 X=ak\mathbf1-kv,\qquad
 Y=bk\mathbf1-(k+1)v-e_0.
\]

Both parent count vectors are positive and nonuniform. Also `gcd(a,b)=1` and
`a != b`. Choose parent endpoint letters `(0,0,0)` and boundary digits `(1,0,13)`.
Since `h(0)` begins and ends with 0, the boundary corrections are
`A=-e_0`, `B=Me_0-e_0`. Exact substitution gives

\[
 MX-e_0=aC,\qquad MY+Me_0-e_0=bC.
\]

The child area is therefore zero. In lexicographic pair order
`01,02,03,04,12,13,14,23,24,34`, the parent area divided by `2k` is

\[
 P(k)=(2947k+587,\ 2947k+167,\ 2947k+419,\ 2947k-911,
       -210,-84,-749,126,-539,-665).
\]

This vector is primitive: the last six coordinates have gcd 7, and the first
is 6 modulo 7. It has infinitely many distinct projective directions: its
`12` coordinate stays `-210`, forcing any proportionality factor to be one,
while its `01` coordinate strictly increases. Thus even the primitive parent
area vectors cannot form one finite raw-state set containing these inverse
transitions. Unlike the earlier uniform-parent example, the same-letter
uniform-return exclusion does not apply to these two parent count vectors.

**Scope is crucial:** no occurrence of these ordered parent blocks in the
fixed point has been established. Neither positivity, nonuniformity, endpoint
labels, nor exact lattice compatibility proves that occurrence. This is not a
family of counterexamples to Shallit's word, nor a proof that every possible
exterior-based invariant must fail. A full-language restriction might remove
these algebraic states; that missing step was not supplied.

## Reproduction

`check.mjs` independently builds `M` from the five images and verifies the
matrix identities, the positive-definiteness certificates, and the entire
family by **polynomial identities**, not a finite sample of ratios. It saves
`check.json`. Logs and identity/checksum-bound atomic checkpoints are separate,
under ignored `.checkpoint-shallit-exterior/` directories.

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
taskset -c 0 node research/unit-step/tracks/shallit-exterior/check.mjs
```

`--help` documents budget interruption, resume, and output options. The exact
audit, one-phase interruption/resume, idempotence, checksum rejection, and
incompatible-identity rejection passed. This is a small stopping-obstruction
audit, **not an all-ratios avoidance certificate**.
No larger scan, isolated-ratio closure, or next research subtask was started.
