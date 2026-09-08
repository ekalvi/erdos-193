# A uniform, narrow ratio interval for Shallit's five-letter candidate

**September 7, 2026. Computer-assisted research theorem; outside review pending.**
The requested whole interval from gap ratio 1:2 to 2:1 was **not** proved.
A smaller, genuine interval was certified instead. This is not a full 5D
construction, a 4D lower bound, Lean formalization, or a new minimum value.
Shallit retains credit for the candidate substitution. The original Erdős 193
finite-step theorem remains a separate result of Cambie and Kalviainen.

**Later same-day extension:** [gap ratios from 49:51 through 51:49](SHALLIT-INTERVAL-EXTENSION.md)
now have a larger, independently checked interval-wide invariant. The present
note preserves the first perturbation argument and its more conservative bound.

## 1. Result and its size

For \(w=h^\omega(0)\), where

\[
h(0)=01213101314310,\qquad h(r)=h(0)+r\pmod5,
\]

write \(F(n)\) for its prefix-count vector. The written argument and exact
finite certificate below exclude collinear triples \(F(i),F(j),F(k)\),
\(i<j<k\), whenever

\[
\boxed{\frac{j-i}{k-i}\in
\left[\frac12-\frac1{5\,114\,400},\frac12+\frac1{5\,114\,400}\right].}
\tag{1}
\]

Equivalently, their successive gap ratio is excluded throughout

\[
\boxed{\frac{j-i}{k-j}\in
\left[\frac{2\,557\,199}{2\,557\,201},
      \frac{2\,557\,201}{2\,557\,199}\right].}
\tag{2}
\]

The band extends only about \(7.82\times10^{-7}\) to either side of ratio
one. It is **very narrow**, but includes infinitely many unequal rational
ratios, for example \(2\,000\,001:2\,000\,000\). Every starting position
and every scale are covered. Ratios such as 2:3 remain unproved here.
The endpoints in (1) and (2) are included.

- [Finite affine invariant](checks/shallit-midpoint.json)
- [Independent validation summary](checks/shallit-midpoint-validation.json)
- [Earlier fixed-ratio descent argument](SHALLIT-RATIO-DESCENT.md)

## 2. Exact symbolic states, not sampled ratios

Use the notation \(M,B(r,t),s_t,R\) of the earlier descent note. For an
ordered triple \(i\le j\le k\), let \(m\) record the two strict-gap bits,
\(u=w_j-w_i\pmod5\), and \(v=w_k-w_i\pmod5\). Define integer vectors

\[
A=R^{-w_i}(F(i)-F(j)),\qquad
B=R^{-w_i}(F(k)-F(i)).
\]

Here the vector \(B\) is distinct from the boundary-prefix notation
\(B(r,t)\). Componentwise, \(-B\le A\le0\), \(B\ge0\), and
\(N=\sum B=k-i\). For the parameter \(\theta\), the canonical error is

\[
e(\theta)=A+\theta B.
\tag{3}
\]

A strict triple is collinear precisely when \(e(\theta)=0\) for
\(\theta=(j-i)/(k-i)\). A single symbolic state retains the full affine
function, not just its value at a chosen ratio.

Appending base-14 digits \((x,y,z)\) uses the same exact ordering and
relative-letter update as before. The affine coefficients change by

\[
\begin{aligned}
A'&=R^{-s_x}\bigl(MA+B(0,x)-B(u,y)\bigr),\\
B'&=R^{-s_x}\bigl(MB+B(v,z)-B(0,x)\bigr).
\end{aligned}
\tag{4}
\]

The [interval probe](shallit_interval_automaton.mjs) retains states for which
some \(\theta\in[1/3,2/3]\) satisfies \(\|e(\theta)\|_2<2\) and
\(|\sum e(\theta)|<1\). The clock and coordinate inequalities first give
rational interval bounds. Minimizing the convex quadratic
\(\|A+\theta B\|_2^2\) then decides feasibility using exact integer
products. Floating-point angles or rounded quadratic roots are not used.

No accumulated parameter history needs to be approximated: if a child
satisfies these guards at a particular parameter, the inverse recurrence
and the old contraction bound imply that its parent satisfies them at the
**same** parameter. Thus current-state feasibility is sufficient, and merging
identical affine states does not mix inconsistent ratio histories.

The initial whole-interval run reached its 20,000-state budget after 155
complete expansions: 21,357 discovered states and 425,320 digit transitions.
The limit is checked between complete state expansions, hence the overshoot.
The [saved bounded outcome](checks/shallit-interval-attempt.json) is explicitly
inconclusive. It neither proves closure nor proves that this symbolic graph
is infinite. We did not respond by claiming that a larger prefix would settle
infinity.

### Why one convex region per discrete state is unsafe

At \(\theta=1/2\), the actual triples \((0,3,6)\) and \((94,114,134)\)
have the same canonical header \((m,u,v)=(3,1,0)\), but errors

\[
\tfrac12(-1,1,-1,1,0),\qquad
\tfrac12(1,-1,1,-1,0).
\]

Both are reachable and nonzero. Any convex region containing both also
contains the forbidden zero. This rules out that particular convex merging
scheme, not arbitrary nonconvex or arithmetic certificates. The new
certificate keeps a finite family of exact affine functions instead.

## 3. Strengthen the guard slightly and include its boundary

The exact inverse-prefix diameter calculation from the earlier note gives

\[
\operatorname{diam}\{M^{-1}B(r,t)\}^2
=\frac{73\,769\,304}{5894^2}
<\left(\frac{117}{80}\right)^2.
\]

Together with \(\|M^{-1}\|_2<1/4\), a putative collinear triple's floor
ancestors satisfy

\[
\|e(\theta)\|_2<\rho:=\frac{39}{20},\qquad
|\sum e(\theta)|<1,
\tag{5}
\]

because \((117/80)/(1-1/4)=39/20\). These inequalities hold uniformly for
all \(0<\theta<1\). We may safely enlarge them to the **closed** guard
\(G(\theta)\) defined by \(\|e(\theta)\|_2\le\rho\) and
\(|\sum e(\theta)|\le1\).

Including the boundary at the central parameter is important: merely closing
a graph with strict guards would not provide a positive margin for discarded
boundary states when the ratio varies.

## 4. The finite affine closure at the midpoint

At \(\theta_0=1/2\), put \(d=2A+B\). The closed guard is exactly

\[
\|d\|_2^2\le15,\qquad |\sum d|\le2,
\]

because \(d\) is integral and \((2\rho)^2=15.21\).
The [midpoint compiler](shallit_midpoint_certificate.mjs) closes the reachable
graph of **full affine states** \((m,u,v,A,B)\) under (4), not merely the
smaller graph of midpoint values \(d\).

The resulting set \(S\):

- contains the root \((0,0,0,0,0)\);
- contains **10,786** affine states;
- is closed under all digit transitions whose child satisfies \(G(1/2)\);
- contains no strict state with \(e(1/2)=0\);
- has \(\max_{s\in S}\sum B_s=9,131\).

The separate [validator](verify_shallit_midpoint.mjs) derives substitution
counts directly from the literal image. It solves the clock inequality for
the middle digit, rather than calling the producer's transition generator,
and checks 2,200,277 clock/order-admissible transitions. Exactly 10,859 are
retained. Every retained successor belongs to \(S\). Missing successors,
missing roots, duplicates, and accepting states are rejected in mutation
tests. The precise bound on \(\sum B\) and all rational margins below are
also checked.

## 5. Lift that closure to an entire interval

Set

\[
C=14\cdot9,131+26=127,860,\qquad
\varepsilon=\frac1{40C}=\frac1{5,114,400}.
\]

For every state in \(S\), and every legal digit child of such a state,

\[
\|B\|_2\le C,\qquad |\sum B|\le C.
\tag{6}
\]

For a stored state this follows from \(B\ge0\) and \(\sum B\le9,131\).
For a child, use (4): the nonnegative matrix \(M\) has column sums 14, and
the two boundary-prefix vectors each have coordinate sum at most 13. Hence
\(\|B'\|_1\le14\sum B+26\le C\); rotation preserves this bound. This
argument does not require storing the discarded children.

For \(|\theta-1/2|\le\varepsilon\), changing the parameter therefore changes
the vector error, and its coordinate sum, by at most

\[
C\varepsilon=\frac1{40}.
\tag{7}
\]

**Closure persists.** If a digit child is not in \(S\), midpoint closure
implies that it fails the closed guard at \(1/2\). Its midpoint error has
half-integer coordinates. Thus either its norm is at least 2 (the next
possible squared numerator is 16), or its absolute coordinate sum is at
least \(3/2\). After perturbation, respectively,

\[
\|e(\theta)\|_2\ge2-\tfrac1{40}=\tfrac{79}{40}>\rho,
\qquad
|\sum e(\theta)|\ge\tfrac32-\tfrac1{40}=\tfrac{59}{40}>1.
\]

So it remains outside \(G(\theta)\). Every transition retained at the new
parameter therefore still has its child in \(S\).

**No accepting state appears.** Every strict state in \(S\) has a nonzero
half-integer midpoint error, of norm at least \(1/2\). Equation (7) leaves
norm at least \(1/2-1/40=19/40>0\), so it cannot become accepting anywhere
in the interval.

A true counterexample at such a parameter would give a digit path from the
root whose every ancestor satisfies (5), hence lies in the closed guard.
The two preceding paragraphs keep that path in \(S\) and exclude its
accepting endpoint. This proves (1), and the monotone transformation
\(\theta\mapsto\theta/(1-\theta)\) gives (2).

This is a quantitative parameter-dependent invariant argument, **not** an
interpolation between successful sample ratios.

## 6. Reproduction and honest next boundary

From the repository root:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
node research/unit-step/tracks/check_shallit_interval.mjs
node research/unit-step/tracks/shallit_interval_automaton.mjs \
  --seconds 60 --max-states 20000 --state-dir .checkpoint-shallit-interval \
  --output research/unit-step/tracks/checks/shallit-interval-attempt.json
node research/unit-step/tracks/shallit_midpoint_certificate.mjs \
  --seconds 120 --max-states 100000 --state-dir .checkpoint-shallit-midpoint \
  --output research/unit-step/tracks/checks/shallit-midpoint.json
node research/unit-step/tracks/verify_shallit_midpoint.mjs
node research/unit-step/tracks/test_shallit_interval_cli.mjs
```

The producers checkpoint their queues, parent/digit paths, counters, and
completed-state or digit cursors atomically. Source/dependency hashes and
checksums reject incompatible or corrupt restarts. The validator checkpoints
checked rows. SIGINT/SIGTERM yield consistent resumable state; completed
results are deterministic. Logs and checkpoints live under ignored
`.checkpoint-*` paths, not in the certificate files. CLI help documents limits
and resume behavior. The affine arithmetic tests include strict guard
boundaries, large-integer cancellation, 11,480 directly generated ordered
triples, and consistency with the earlier fixed-ratio certificates.

The displayed neighborhood is conservative, not asserted maximal. The next
step is a larger **uniform affine invariant** or a rigorously checked finite
cover by such neighborhoods—not a list of additional point ratios. No cover
of \([1/3,2/3]\) has been produced, and the more unbalanced ratios remain
outside this result. The minimum dimension and minimum 3D step count remain
unresolved. A scoped site-source update records this partial result; no site
was deployed and outside mathematical review remains pending.
