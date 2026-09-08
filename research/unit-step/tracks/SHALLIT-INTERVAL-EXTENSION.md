# Uniform extension: gap ratios from 49:51 through 51:49

**September 7, 2026. Exact computer-assisted research theorem; outside review
pending.** This improves the earlier tiny neighborhood but does **not** cover
the requested whole range from 1:2 through 2:1. It does not establish a 5D
construction or change the minimum-dimension bounds. Shallit's substitution
and the original Cambie–Kalviainen Erdős 193 theorem retain their attribution.

**Later structural follow-up:** the [all-ratio direction reduction](SHALLIT-DIRECTION-REDUCTION.md)
now excludes uniform directions and directions missing a letter, without
restricting the ratio. Positive nonuniform directions and the remaining
central interval are still unresolved.

## Result

In Shallit's fixed point, with prefix counts \(F(n)\), there are no collinear
triples \(F(i),F(j),F(k)\), \(i<j<k\), whose successive gap ratio satisfies

\[
\boxed{\frac{49}{51}\le\frac{j-i}{k-j}\le\frac{51}{49}.}
\]

Equivalently, the parameter \(\theta=(j-i)/(k-i)\) lies in the **entire closed
interval** \([49/100,51/100]\). All starting positions and all scales are
covered. This is approximately a four-percent band on either side of equal
gaps, rather than a checklist of individual ratios. For example, it includes
25:26 and 26:25 at every scale and position.

The exact affine-state certificate contains **21,694 states**. A separate
checker verified all **37,528,109** clock/order-admissible digit transitions;
21,768 transitions are retained, and every retained successor belongs to the
certificate. No state is accepting at any parameter in the interval.

- [Certificate](checks/shallit-extension-100.json)
- [Independent validation](checks/shallit-extension-100-validation.json)
- [Earlier midpoint-neighborhood proof and descent constants](SHALLIT-UNIFORM-NEIGHBORHOOD.md)

## Why this is an interval theorem

Keep the full state \((m,u,v,A,B)\) and affine error \(e(\theta)=A+\theta B\)
from the earlier note. Here

\[
A=R^{-w_i}(F(i)-F(j)),\quad B=R^{-w_i}(F(k)-F(i)),\quad
p=-\sum A=j-i,\quad N=\sum B=k-i.
\]

The exact digit recurrence is unchanged. Retain a child precisely when there
exists a parameter in the chosen interval satisfying the **closed** guards

\[
\|A+\theta B\|_2\le39/20,\qquad |\theta N-p|\le1.
\tag{1}
\]

The inverse-matrix and boundary-prefix inequalities in the earlier note imply
that every floor ancestor of a genuine counterexample satisfies these guards
at the **same** parameter. The sharpened inverse diameter is independently
rechecked here, not inferred from the successful runs.

Feasibility is exact: intersect the parameter interval with the rational clock
strip and each necessary coordinate strip, then minimize

\[
Q(\theta)=\langle A,A\rangle+2\theta\langle A,B\rangle
          +\theta^2\langle B,B\rangle.
\]

Its minimum occurs at a rational endpoint or at
\(-\langle A,B\rangle/\langle B,B\rangle\). Integer arithmetic decides whether
that minimum is at most \(1521/400\). Boundaries are included; rounded roots
and floating-point near-zero judgments are not used. The validator uses a
separate quadratic determinant calculation, derives the substitution counts
from the literal image, and enumerates all three digits rather than importing
the producer's clock-strip iterator. Explicit coefficient bounds keep linear
Number operations exact; potentially large products use BigInt.

A finite set containing the root and closed under every transition feasible
at **any** parameter in the interval is an invariant for every parameter in
that interval. A true counterexample would have a guarded digit path inside
this set. For each strict stored state, the only possible accepting parameter
is \(p/N\); the checker excludes the simultaneous coordinate equations
\(NA+pB=0\) whenever \(p/N\) lies in the interval. Hence no such endpoint
exists. This is the entire infinite reduction; no maximum walk length is
assumed.

Unlike the first neighborhood proof, this extension does not use a common
Lipschitz margin. It checks interval-wide closure directly and adds genuinely
new affine states when necessary. The maximum stored span is 9,190, but that
is a property of the closed invariant, **not** an assumed bound on walks.

## What happened to the full central interval

The DFS implementation avoids the first breadth-first run's immediate queue
explosion, but it has **not** closed \([1/3,2/3]\). After three bounded segments
it recorded 80,878 states, 80,868 complete expansions, and 220,418,298 tested
transitions. The [saved outcome](checks/shallit-extension-6.json) is a time
budget exit, not a certificate of avoidance or of infinitude.

One independently checked [frontier state](checks/shallit-central-frontier.json)
comes from the actual indices

\[
(3,291,449,862,\ 15,565,971,114,\ 22,013,009,446),
\]

with span 18,721,559,584. It has a nonzero error inside (1) at a parameter
approximately 0.6556356161. The exact rational parameter and root digit path
are saved. This is finite evidence of very large affine coefficients, **not**
a collinear triple or a proof that the graph is infinite. No huge word prefix
was generated: its counts are computed directly from the base-14 digits.

A new detector looks for equal nonzero parameter-specialized states along an
ancestor path. Such a genuine cycle, if found and independently checked,
would produce infinitely many distinct affine states: repeating its digits
preserves the point-state, while the span grows by
\(N'=14^rN+z-x>N\) for a strict triple. That would obstruct a finite literal
list of affine states under this guard, not necessarily the candidate itself.
**No such cycle was found in these runs.** The detector's positive regression
case is explicitly synthetic and not claimed reachable in Shallit's word.

The remaining task is still a uniform argument for the rest of the central
interval, then the more unbalanced ratios. Further finite closure work is
resumable, but simply raising a budget is not a mathematical finiteness
argument. A sound representation of unbounded affine families may be needed;
that necessity has not been proved either.

## Reproduction and validation

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
node research/unit-step/tracks/shallit_interval_extension.mjs \
  --radius-denominator 100 --seconds 120 --max-states 100000 \
  --state-dir .checkpoint-shallit-extension-100 \
  --output research/unit-step/tracks/checks/shallit-extension-100.json
node research/unit-step/tracks/verify_shallit_interval_extension.mjs
node research/unit-step/tracks/test_shallit_extension.mjs
```

Use radius denominator 6 and `.checkpoint-shallit-extension-6` to resume the
unfinished full-central run. Its output must remain explicitly inconclusive
unless a complete invariant or independently checked counterexample results.
Budgets may change across compatible restarts; parameter intervals may not.
Source/dependency hashes and checksums bind atomic checkpoints. DFS frames,
parent/digit paths, counters, and validator rows are persisted. SIGINT/SIGTERM
checkpoint consistently. Each worker is single-threaded JavaScript; bounded
runs log progress and memory use durably. No workers were left running.

Regression coverage includes 14,224 comparisons of independently implemented
feasibility decisions, 48 complete clock-iterator comparisons, exact closed
boundaries, large-integer cancellation, mutation rejection, producer/validator
interruptions, budget resumes, byte-identical completed resumes, corrupt and
incompatible checkpoint rejection, and exact reconstruction of the large
frontier triple. These checks support the written research theorem; they do
not replace outside mathematical review or Lean formalization. Site source
was updated, but nothing was deployed.
