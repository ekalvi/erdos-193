# Shallit's five-letter candidate: bounded descent and fixed-ratio certificates

**September 6, 2026. Research result with exact finite-state certificates.**
A written reduction and a separately implemented closure checker establish
avoidance for adjacent-length ratios **1:1, 1:2, and 2:1 at every length and
position** in Shallit's candidate. This is stronger than a prefix check, but
**does not prove avoidance at arbitrary ratios or an infinite 5D construction**.
The reduction and certificates have not been independently peer-reviewed or
Lean-formalized. No new manuscript authorship or novelty claim is assigned.

**September 7 follow-up:** the [uniform interval from gap ratio 49:51 through 51:49](SHALLIT-INTERVAL-EXTENSION.md)
now has an exact finite affine invariant and separate validation, extending the
[first tiny neighborhood of equal gaps](SHALLIT-UNIFORM-NEIGHBORHOOD.md).
It does not cover the entire central interval or prove the full 5D claim;
outside review remains pending.

The positive-basis minimum remains open; the original Erdős 193 theorem of
Cambie and Kalviainen is a different, already settled finite-step problem.
See [PROBLEM.md](../PROBLEM.md) and [JOINT-MINIMUM.md](../JOINT-MINIMUM.md).
The earlier [contradiction attempt](CONTRADICTION-5D-4D.md) did not rule out 4D
or 5D. The separate [4D return-block audit](FOUR-RETURN-BLOCKS.md) also does not
supply a dimension lower bound.

## 1. Exact recurrence and the target relation

Retain Shallit's substitution and attribution:

\[
h(0)=01213101314310,\qquad h(r)=h(0)+r\pmod5.
\]

Let \(s_t\) be digit \(t\) of this fourteen-letter image, for \(0\le t<14\),
and let \(w=h^\omega(0)\). Let \(F(n)\) count the letters before position
\(n\), including \(F(0)=0\). Write \(B(r,t)\) for the Parikh vector of the
first \(t\) letters of \(h(r)\). Then

\[
w_{14n+t}=w_n+s_t\pmod5,\qquad
F(14n+t)=MF(n)+B(w_n,t),
\tag{1}
\]

where

\[
M=\begin{pmatrix}
3&1&3&1&6\\6&3&1&3&1\\1&6&3&1&3\\3&1&6&3&1\\1&3&1&6&3
\end{pmatrix}.
\]

In particular the letter at an index is the sum of its base-14 digit scores
\(s_t\), modulo five. Equations (1) compute arbitrarily large indexed counts
exactly, without generating the intervening word.

Fix positive coprime integers \(a,b\), and put \(L=a+b\). For ordered
indices \(i\le j\le k\), define

\[
D(i,j,k)=bF(i)-LF(j)+aF(k).
\tag{2}
\]

For **strict** indices, \(D=0\) means
\(b(F(j)-F(i))=a(F(k)-F(j))\). Summing coordinates gives
\(b(j-i)=a(k-j)\), so this is exactly collinearity with adjacent-length ratio
\(a:b\). All positive multiples of that ratio are included.

## 2. A uniform normalized-error bound for every ratio

The matrix is invertible. Its squared singular values are
\(196\) and \(21\pm2\sqrt5\), each of the latter occurring twice. Since
\(21-2\sqrt5>16\),

\[
\|M^{-1}\|_2<\tfrac14.
\tag{3}
\]

For an exact integer check, \(5894M^{-1}\) is the circulant matrix whose first
row is

\[
(227,1025,-305,-53,-473),
\]

with each successive row shifted right by one. Call this integer matrix
\(A\). Direct multiplication gives \(AM=MA=5894I\). Also
\(( (M^TM)^2-42M^TM+421I )|_H=0\) on \(H=\{x:\sum x_r=0\}\), while the
constant vector has squared singular value 196. This verifies (3) without
floating-point eigenvalue calculations.

There are only seventy boundary vectors \(B(r,t)\), for five letters and
fourteen offsets. Exhausting their 4,900 ordered pairs gives

\[
\max_{r,t,u,v}\|AB(r,t)-AB(u,v)\|_2^2=73\,769\,304
<\frac94\,5894^2.
\tag{4}
\]

The maximum is attained by \((r,t)=(0,13)\), \((u,v)=(1,13)\).
Thus the diameter of \(\{M^{-1}B(r,t)\}\) is strictly less than \(3/2\).
Both the inverse identity and the complete diameter calculation are checked
by [the exact validator](check_shallit_ratio_automaton.mjs).

**Uniform descent lemma.** Suppose \(i<j<k\) satisfies (2) with \(D=0\).
For every \(r\ge0\), let

\[
i_r=\lfloor i/14^r\rfloor,\quad
j_r=\lfloor j/14^r\rfloor,\quad
k_r=\lfloor k/14^r\rfloor,\quad D_r=D(i_r,j_r,k_r).
\]

Then

\[
\boxed{\|D_r\|_2<2L,\qquad |\textstyle\sum D_r|<L.}
\tag{5}
\]

In particular \(\|D_r/L\|_2<2\), **uniformly over all positive ratios**.

**Proof.** At a single descent, (1) gives

\[
D_{r-1}=MD_r+C_r,\qquad
C_r=bB_i-LB_j+aB_k.
\]

By convexity and (4),

\[
\|M^{-1}C_r\|_2
=L\left\|\frac bL(M^{-1}B_i-M^{-1}B_j)
 +\frac aL(M^{-1}B_k-M^{-1}B_j)\right\|_2<\tfrac32L.
\]

Consequently \(\|D_r\|_2<\frac14\|D_{r-1}\|_2+\frac32L\).
Starting with \(D_0=0\) proves the first bound by induction.
For the second, (2) and the coordinate-sum clock give \(bi-Lj+ak=0\).
Dividing by \(14^r\) and taking floors gives

\[
\sum D_r=-b\{i/14^r\}+L\{j/14^r\}-a\{k/14^r\}\in(-L,L).
\]

Here braces denote fractional parts. \(\square\)

This is a boundedness lemma, **not yet an all-ratios finiteness lemma**.
The normalized states lie on grids with unbounded denominators as \(a+b\)
varies. For each fixed \(a,b\), however, the unnormalized \(D_r\) is an
integer vector in a finite ball. That distinction is essential.

## 3. A finite automaton for a fixed ratio

Let \(R e_t=e_{t+1\bmod5}\). The matrix \(M\) commutes with \(R\), and
\(B(u,t)=R^uB(0,t)\). Encode an ordered index triple by

\[
(m,u,v,d),\quad
m=\mathbf1_{i<j}+2\mathbf1_{j<k},\quad
u=w_j-w_i\pmod5,\quad v=w_k-w_i\pmod5,\quad
 d=R^{-w_i}D(i,j,k).
\tag{6}
\]

The letter called \(u\) in the state is the relative letter \(w_j-w_i\).
Only a common cyclic relabeling has been removed. Rotation preserves norms
and coordinate sums, so (5) holds for \(d\).

The initial state, at \((i,j,k)=(0,0,0)\), is \((0,0,0,0)\).
For a digit triple \((x,y,z)\in\{0,\ldots,13\}^3\), form indices
\((14i+x,14j+y,14k+z)\). If \(i=j\), require \(x\le y\); if \(j=k\),
require \(y\le z\). Strict old inequalities permit arbitrary corresponding
digits. The new strict-gap mask is the old mask with the bits for \(x<y\)
and \(y<z\) added. With \(s=s_x\), the remaining update is exactly

\[
\begin{aligned}
u'&=u+s_y-s\pmod5,\\
v'&=v+s_z-s\pmod5,\\
d'&=R^{-s}\bigl(Md+bB(0,x)-LB(u,y)+aB(v,z)\bigr).
\end{aligned}
\tag{7}
\]

Keep only states with \(\|d\|_2^2<4L^2\) and \(|\sum d|<L\).
There are finitely many: at most \(100(4L-1)^5\), before applying the sharper
norm and clock constraints. A state is **accepting** precisely when \(m=3\)
and \(d=0\).

### Why this finite check proves an infinite statement

1. Every accepting path from the initial state reconstructs three strict
   base-14 indices, and (1), (6), and (7) verify their actual counts. It is a
   genuine counterexample, not merely an algebraically allowed boundary case.
2. Conversely, every actual counterexample has finitely many base-14 digits.
   Reading those digits from the most significant end gives a path from the
   initial state to an accepting state. Its intermediate states are exactly
   canonical rotations of the floor ancestors in (5), so none is pruned.
3. Therefore a finite set containing the initial state, closed under every
   retained digit transition, and containing no accepting state is an
   inductive certificate excluding the ratio at **every** length and position.

Paths that leave the bound cannot leave and later return to an accepting
state: that would contradict the ancestor bound applied to the endpoint.
This is the justification for pruning, not an assumption based on a prefix.
No assertion that every bounded state is realizable is needed for checking a
closed invariant set. The generator explores only states reachable from the
root; the independent validator checks closure directly.

## 4. Completed certificates

| Adjacent-length ratio | States | Clock/order-admissible digit transitions checked | Retained transitions |
|---|---:|---:|---:|
| 1:1 | 3,794 | 731,038 | 4,548 |
| 1:2 | 11,186 | 2,224,352 | 11,478 |
| 2:1 | 12,617 | 2,507,982 | 12,994 |

All three reachable graphs close without an accepting state. The first
certifies ordinary abelian-square avoidance. The other two exclude the
specified unequal-length weak abelian squares at arbitrary scales.

- [1:1 invariant set](checks/shallit-ratio-1-1.json)
- [1:2 invariant set](checks/shallit-ratio-1-2.json)
- [2:1 invariant set](checks/shallit-ratio-2-1.json)
- [Independent validation summary and source hashes](checks/shallit-ratio-validation.json)

The generator enumerates digit triples, then applies the clock bound. The
validator instead solves that inequality for the middle digit and checks
every retained successor using a separately written update. It verifies the
root, bounds, uniqueness, absence of accepting states, and full closure.
Removing a root or successor, duplicating a state, and adding an accepting
state are rejected in mutation tests. Exact recurrence tests compare 17,952
small ordered index triples with directly generated counts, including cases
where floor ancestors coincide. All 2,745 counts in \(h^3(0)\), including its
endpoint, match the independent big-integer indexed-count routine.

These are computationally checked finite invariant certificates supporting
the written infinite fixed-ratio statements. They are not collaborator
approval, peer review, Lean certification, or proof of the full 5D claim.

## 5. A tempting finite-ratio shortcut is false

One might hope all factor Parikh vectors have bounded coordinate gcd, thereby
bounding the multipliers in a proportional pair. They do not. The factor at
positions \([52,57)\) is

```
04213
```

with Parikh vector \(\mathbf1\). Since \(M\mathbf1=14\mathbf1\), its images
are actual factors at \([52\cdot14^r,57\cdot14^r)\), with vectors
\(14^r\mathbf1\). Thus factor gcds are unbounded.
This supplies pairs on lines parallel to \(\mathbf1\), not collinear triples;
it does not refute the candidate. Any finite-ratio reduction must exploit
**adjacency in a minimal counterexample**, not a false bound on all factors.

## 6. Reproduction, resume, and the next proof obligation

From the repository root, use one JS worker and constrain native libraries:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
for ratio in '1 1' '1 2' '2 1'; do
  set -- $ratio
  node research/unit-step/tracks/shallit_ratio_automaton.mjs \
    --left "$1" --right "$2" --seconds 120 --max-states 100000 \
    --state-dir ".checkpoint-shallit-ratio-$1-$2" \
    --output "research/unit-step/tracks/checks/shallit-ratio-$1-$2.json"
done
node research/unit-step/tracks/check_shallit_ratio_automaton.mjs \
  --state-dir .checkpoint-shallit-ratio-checked
node research/unit-step/tracks/test_shallit_ratio_cli.mjs
node research/unit-step/tracks/four_return_blocks.mjs
node research/unit-step/check.mjs
node research/unit-step/joint_minimum_examples.mjs
```

The automaton checkpoints its BFS queue, completed-state cursor, parent/digit
witness paths, and counters atomically. Identity and checksum checks reject
incompatible or corrupt restarts. Per-run time/state budgets can change;
ratio and source cannot. SIGINT/SIGTERM stop at consistent state boundaries.
The mathematical graph is finite for every fixed positive ratio; the bounded
CLI deliberately accepts coefficients only up to eight and enforces a
state/memory limit. A budget exit is inconclusive, not a certificate.
The independent validator also checkpoints completed rows and certificate
hashes. Repeating a completed command reuses validated progress and produces
the same final artifact. Use fresh state directories for an independent
regeneration; do not silently discard incompatible progress. The CLI regression
tests exercise producer and validator interruption/resume, byte-identical
completed results, and corrupt/config checkpoint rejection in temporary
storage. Timestamped logs and checkpoints remain separate under ignored
`.checkpoint-*` paths.

**Next main obligation:** turn the ratio-dependent finite invariants into a
uniform argument for every coprime \(a,b>0\), or prove a finite bound on the
ratios of a minimal counterexample. Neither has been done. Checking additional
individual ratios, however many, cannot substitute for that step.

The 4D return-block work is a separate lower-bound attempt. Even a successful
5D basis construction would not by itself settle the minimum 3D step count.
No exact minimum or status of the six-step manuscript has changed. A narrowly
scoped, review-pending entry in `viz/progress.html` records the fixed-ratio
certificates separately from the original theorem; no site was deployed.
