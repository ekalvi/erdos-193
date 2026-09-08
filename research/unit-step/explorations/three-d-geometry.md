# Three-dimensional geometry: a sharp restricted obstruction and two reductions

**Independent AI research note, September 6, 2026; not human-reviewed.**
This concerns the follow-up step minimum, not the already settled original
Erdős 193 theorem of Cambie and Kalviainen. No manuscript attribution changes.

## 1. Verdict and exact scope

**No universal four-/five-step impossibility or infinite construction was found.**
The strongest concrete result obtained here is the following restricted,
coefficient-uniform theorem.

**Theorem A (two lines, one antipodal pair; sharp finite bound).** Let
$u,v\in\mathbb R^3$ be linearly independent and let $a_1,a_2,a_3$ be arbitrary
nonzero real numbers. For

$$
S\subseteq\{a_1u,a_2u,a_3u,v,-v\},
$$

every distinct-vertex, no-three-collinear $S$-walk has at most **15 steps**.
In particular, none of these at-most-five-step menus admits an infinite walk.
The bound is attained by an integer menu in this family.

For the target problem, require the displayed step vectors to be integers.
The theorem allows unbounded coefficients, either sign among the $a_i$, and
an antipodal, hence non-pointed, permitted menu. It does **not** cover general
rank-two menus, general non-pointed menus, or any full-rank three-dimensional
menu. The equal-and-opposite assumption on the two transverse steps matters.
Unused permitted steps are allowed, as in the definition of $s_*$.

Two additional proved reductions are recorded below:

* A rational-line quotient gives a necessary transverse lattice-packing bound.
  Consequently, any primitive constant-length substitution with all
  non-Perron eigenvalues smaller in modulus than the square root of its length
  fails under **every rational 3D projection**, whether or not the projection
  admits substitution scaling.
* A coefficient-uniform finite obstruction in even **one open oriented-matroid
  chamber** would already be a finite obstruction to the corresponding basis
  model. This identifies a quantifier barrier to a sign-pattern-only attack.

These are derivations in this investigation, not claims of literature novelty.
Neither changes the known minimum bounds.

## 2. Proofs and the failed unrestricted step

### A. Proof of the sharp restricted theorem

Write an $a_i u$ step as horizontal and a $\pm v$ step as transverse.
Consecutive steps on the same line give three collinear vertices (or a
revisit), so every valid walk alternates these two classes.

**No transverse sign reversal in a valid walk of length at least four.** Two
successive transverse steps with opposite signs have the three-step form

$$
\varepsilon v,\;a u,\;-\varepsilon v.
$$

If a horizontal step $b u$ follows, the four-step block has vertices at
$0$, $a u$, and $(a+b)u$ at its local indices $0,3,4$. These are collinear;
if two coincide, distinctness already fails. If instead a horizontal step
precedes, the block

$$b u,\;\varepsilon v,\;a u,\;-\varepsilon v$$

has the collinear vertices $0,b u,(a+b)u$ at indices $0,1,4$.
A three-step reversal block in a word of length at least four has an adjacent
step on at least one side, necessarily horizontal. Thus it cannot occur.
All transverse steps consequently have one common sign $\varepsilon$.

Now suppose a valid walk has 16 steps. Sample its vertices at times
$0,2,4,\ldots,16$. Alternation and the common transverse sign imply that its
eight sampled steps belong to

$$\{a_1u+\varepsilon v,\ a_2u+\varepsilon v,\ a_3u+\varepsilon v\}.$$

Every eight-letter ternary word contains an ordinary abelian square: two
adjacent nonempty blocks of equal length with identical letter counts.
Their displacement sums are equal under **any** assignment of vectors to the
three labels. The three sampled endpoints therefore form a midpoint triple,
or coincide, contradicting the hypotheses. This proves the 16-step
obstruction without a clock-height assumption or a temporal realization
assumption about an arbitrary rational relation.

The ternary lemma is prior knowledge, not a new result here. The repository's
[certificate](../../../design/UNIT-STEP-4D-5D-INVESTIGATION.md#1-why-three-positive-coordinate-directions-cannot-work)
records its complete canonical extension tree. Shallit's manuscript cites
T. C. Brown (1971) for this lower bound. For self-contained verification the
canonical surviving words, with letters named by first appearance, are:

| Length | Words avoiding ordinary abelian squares |
|---|---|
| 1 | `0` |
| 2 | `01` |
| 3 | `010`, `012` |
| 4 | `0102`, `0120`, `0121` |
| 5 | `01020`, `01021`, `01201`, `01202`, `01210` |
| 6 | `010201`, `010210`, `010212`, `012010`, `012101` |
| 7 | `0102010`, `0102101`, `0121012` |
| 8 | none |

Each row is obtained by appending each admissible canonical label and deleting
words containing an abelian square. The accompanying checker also checks all
$3^8=6561$ length-eight words independently of canonicalization.

**Sharpness.** Take $u=(1,0,0)$, $v=(0,1,0)$ and horizontal coefficients
$1,1000,1000000$, called $H_0,H_1,H_2$. The 15-step word

```text
H0, v, H1, v, H0, v, H2, v, H0, v, H1, v, H0, v, H2
```

has distinct vertices and no collinear triple. The checker verifies all 560
triples of its 16 vertices by exact `BigInt` determinants. It uses only four
of the permitted five types; this is sufficient for sharpness in the stated
at-most-five family. Thus a smaller coefficient-uniform cutoff is impossible.
The main upper-bound proof does not depend on this sharpness check.

### B. A lattice-packing obstruction, without clock height

**Proposition B.** Let $Q_0,\ldots,Q_N\in\mathbb Z^3$ be distinct and
triple-free. Let $B\in\mathbb Z^{2\times3}$ have rank two. Write

$$
R_i=\max_{0\le n\le N}(BQ_n)_i-\min_{0\le n\le N}(BQ_n)_i,
\qquad i=1,2.
$$

Then

$$\boxed{N+1\le 2(R_1+1)(R_2+1).} \tag{1}$$

Indeed, every fiber of $B$ is an affine line and contains at most two vertices.
There are at most $(R_1+1)(R_2+1)$ integer values in the containing rectangle.
No monotonicity, separating functional, sign restriction, or step budget is
used in this proof.

In particular, fix any rational vector $m\in\mathbb Q^3$. Choose an integer
rank-two $B$ with $Bm=0$; such a matrix exists also when $m=0$. If

$$D_N=\max_{0\le n\le N}\|Q_n-nm\|_\infty,$$

then $R_i\le 2\|B_i\|_1D_N$, where $B_i$ is row $i$. Equation (1) gives
$D_N\ge c\sqrt N-C$ for positive constants depending only on $B$.
In particular, **$Q_n=nm+o(\sqrt n)$ with rational $m$ is impossible** for an
infinite triple-free lattice walk. The pointwise little-oh bound also bounds
the prefix maximum by $o(\sqrt N)$: separate a fixed finite initial segment
from the tail. Rationality is used to produce a lattice-valued transverse
projection; no assertion for arbitrary irrational drift is made here.

**Corollary B.1 (subdiffusive substitution obstruction).** Let $h$ be a
primitive $L$-uniform substitution, $L\ge2$, on any finite number of letters,
with an infinite fixed point and incidence matrix $M$. Put
$H=\{x:\mathbf1^Tx=0\}$. If

$$\rho(M|_H)<\sqrt L,$$

then **every** rational matrix $A\in\mathbb Q^{3\times s}$ sends the fixed
point's prefix-count walk to a walk that fails distinctness or triple avoidance.
No relation $AM^t=CA$, even approximately, is assumed.

*Proof.* Primitivity gives a unique normalized Perron vector $f$, satisfying
$Mf=Lf$ and $\mathbf1^Tf=1$. It is rational, since this uniquely solvable
normalized linear system has rational coefficients. If $F(n)$ is the prefix
count, the fixed-point identity is

$$F(Ln+r)=MF(n)+C(w_n,r),\qquad 0\le r<L,$$

where $C(w_n,r)$ counts a prefix of a single substituted letter. Thus
$E(n)=F(n)-nf\in H$ obeys

$$E(Ln+r)=ME(n)+C(w_n,r)-rf.$$

The corrections form a finite bounded set in $H$. Choose
$\max(1,\rho(M|_H))<\theta<\sqrt L$. Finite-dimensional Jordan form gives
$\|(M|_H)^j\|\le K\theta^j$. Repeated division of $n$ by $L$ therefore yields

$$\|E(n)\|=O(n^{\log_L\theta})=o(\sqrt n).$$

Clear denominators of $A$. Its projected walk would have rational drift $Af$
and sub-square-root error, contradicting Proposition B. This proves the
corollary, including arbitrary non-clock projections. $\square$

This is **not** the prior Track D substitution-scaling theorem. That theorem
uses Shallit's particular incidence algebra to rule out a fixed projected
scaling law. Here there is no projected scaling premise, but there is instead
a restrictive spectral-growth premise. In particular, this corollary does
**not** exclude Shallit's five-letter candidate: its circulant incidence matrix
has deviation eigenvalue squared moduli $21\pm2\sqrt5$, both larger than
$L=14$. The source and these data are already recorded in the investigation
and the read-only prior `D-SHALLIT-PROJECTION.md`.

### C. Why a finite oriented-matroid classification does not remove coefficients

**Proposition C (open-chamber finite projection).** Fix $s\ge3$, and let
$\mathcal C\subset\mathbb R^{3\times s}$ be a nonempty open set of rank-three
matrices, closed under multiplication by positive scalars. Every finite
triple-free basis word over $s$ letters admits an integer projection
$A\in\mathcal C$ preserving distinctness and all its triples.

This applies to every nonempty chamber specifying strict signs of all
three-column determinants. It does not apply to lower-dimensional strata
where specified determinants vanish, such as Theorem A's two-line menus.

*Proof.* For a source triple, its two adjacent count differences $U,V$ are
linearly independent. The bad matrices satisfy
$\operatorname{rank}[AU\ AV]<2$, hence polynomial equations in the entries of
$A$. This is a proper algebraic subset: extend $U,V$ to a basis of the source
space and choose a linear map taking them to the first two standard vectors
of $\mathbb R^3$. Similarly, collapsing any distinct pair or making a used
column zero is a proper linear condition. A finite union of these bad sets
has empty interior. Its complement meets $\mathcal C$ in a nonempty open set,
which contains a rational matrix. Clear denominators; the cone property keeps
the resulting integer matrix in $\mathcal C$, and scaling preserves avoidance.
$\square$

Consequently, for **any one** such chamber and **each fixed** $N\ge1$,

$$
\begin{split}
&\text{no integer menu in }\mathcal C\text{ supports a valid }N\text{-step walk}\\
&\qquad\Longleftrightarrow\quad
\text{no }s\text{-letter basis word of length }N\text{ is valid}.
\end{split} \tag{2}
$$

The reverse direction is Shallit's prior basis-encoding principle. This shows
that a common finite horizon derived from the sign pattern alone, even in one
open chamber, would already obstruct the basis model. It cannot demonstrate
an arithmetic compression gap while leaving arbitrarily long basis prefixes.
An arithmetic proof with menu-dependent horizons is **not** ruled out.

There is also a real-coordinate infinite version: the bad sets for a fixed
infinite valid basis word are countably many proper algebraic sets, of measure
zero. Almost every real matrix in any open chamber preserves the entire word.
One cannot conclude that any rational or integer matrix does: all rational
matrices form a countable set and may lie in the bad union. This is precisely
where real oriented geometry and fixed integer realization separate.

**Explicit failed unrestricted step.** Five integer columns in rank three
have a two-dimensional rational kernel. A collinear triple requires a kernel
hit by $qU-pV$, where $U,V$ are counts of actual adjacent nonempty blocks and
$p,q$ are suitable integers, not necessarily of the same sign for a general
menu. The existence of a rational relation does not realize such blocks in
every word. Neither the matroid signs nor the packing inequality establishes
that missing temporal statement. Theorem A escapes this gap only because
alternation and the antipodal geometry force a ternary block encoding.

## 3. Finite checks and exact reproduction

From the repository root:

```sh
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p .checkpoint-three-d-geometry
node research/unit-step/explorations/check_three_d_geometry.mjs \
  | tee .checkpoint-three-d-geometry/check.jsonl
```

The fixed-size checker uses one worker, no subprocesses, and no packages. It
records timestamps and its SHA-256. The final run took **29 ms**. It checks:

1. all 6,561 ternary length-eight words and the displayed extension tree;
2. canonical alternating symbolic walks through 16 steps, allowing transverse
   sign changes, and rejecting coefficient-independent collinearities;
3. the 15-step integer witness, including distinctness and all 560 triples.

The symbolic horizontal position has three formal coefficient counts. For
three vertices whose heights are not all equal, collinearity is identically forced precisely
when every coefficient of the height-weighted horizontal defect vanishes;
three equal heights always force collinearity. This enumerates universal
algebraic failures, **not** all failures for any fixed numerical menu. The
symbolic survivor counts for lengths 0 through 16 were

```text
1, 2, 2, 4, 2, 3, 4, 6, 6, 8, 10, 13, 10, 8, 6, 5, 0
```

The analytic obstruction in Section 2A is independent of this symbolic scan.
The only positive claim based on numerical coordinates is the explicitly
finite sharpness witness. No large prefix searches, substitution recoding
searches, or uncheckpointed long computations were run. This subsecond verifier
can safely restart from scratch; there is no costly accumulated state.

## 4. Actual implications for the minima

* Theorem A removes the specified two-line/antipodal subfamily from possible
  four- and five-step witnesses, uniformly in all its coefficients.
* Corollary B.1 removes a class of substitution sources from **all** rational
  3D projections; it says nothing against a source outside its growth regime.
* Neither proves $\neg\mathcal E(3,4)$ or $\neg\mathcal E(3,5)$.
* There is no new bound on $d_*$ or $s_*$. The proved relation remains
  $4\le d_*\le s_*$. The proposed ceiling $s_*\le6$ retains the checkpoint's
  independent-review qualification. The prior AI audit is not human approval.
* Even a future universal five-step 3D obstruction would not determine $d_*$.
  No equality of the minima is assumed here.

## 5. Strongest next attack, stopping reason, and changed files

The next sharp extension of Theorem A is the two-line family

$$\{a_1u,a_2u,a_3u,pv,-qv\},\qquad p,q>0,$$

with unequal opposite lengths. It tests the exact failure of the geometric
compression: a transverse sign reversal no longer returns to the same
horizontal level, so the four-step forced triple disappears. One would need
an actual temporal argument, not merely the relation $q(pv)+p(-qv)=0$.
For example, the one-dimensional increment pattern $+2,+2,-1$ repeated has
pairwise distinct partial sums $0,2,4,3,5,7,6,\ldots$ despite infinitely many
sign reversals. Thus the equal-length sign-rigidity proof cannot simply be
reused. This example is **not** a triple-free 3D construction.

For full-rank menus, a useful next reduction must be arithmetic and allow
menu-dependent horizons, or else prove a genuine basis obstruction as in
(2). No general temporal kernel-hit theorem was established in this bounded
session. Stopping here preserves a proved restricted result instead of
claiming an unsupported universal lower bound. The packing reduction is
available for screening genuinely new substitution candidates, but does not
justify further scans of the already-tested Shallit candidate.

Files created:

* `research/unit-step/explorations/three-d-geometry.md` — this report.
* `research/unit-step/explorations/check_three_d_geometry.mjs` — small exact checker.
* `.checkpoint-three-d-geometry/check.jsonl` — ignored run log, not a proof artifact.

No manuscripts, central checkpoints/problem statements, visualization files,
or prior-track files were changed. No commit, publication, or deployment.
