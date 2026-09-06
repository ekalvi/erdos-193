# Joint minimum problem: dimension, step count, and uniform realization

**Research formulation, September 6, 2026.** Determine the exact ordered pair
$(d_*,s_*)$ defined below. This sharpens the already resolved original
Erdős Problem 193; it is not another claim to solve that original problem.
The reductions here are elementary mathematical arguments, not a Lean
formalization or a resolution of either minimum. Independent review of the
six-step draft remains pending.

## 1. Two models and the logic matrix

For positive integers $r,s$, let $\mathcal E(r,s)$ mean that there exist a
**fixed** set $S\subset\mathbb Z^r\setminus\{0\}$ with $|S|\le s$ and an infinite
sequence $(Q_n)_{n\ge0}$ such that

- $Q_0=0$ and the vertices are pairwise distinct;
- $Q_{n+1}-Q_n\in S$ for every $n\ge0$;
- for every $0\le i<j<k$,

  $$
  \operatorname{rank}_{\mathbb Q}[\,Q_j-Q_i\quad Q_k-Q_j\,]=2.
  $$

The rank condition means no three vertices are collinear. The step vectors
are chosen once, before all indices; they may not change with the prefix
length. We count **at most** $s$ types and impose no uniform bound on their
integer coordinates across different candidate constructions.

Let $\mathcal B(d)$ mean the same avoidance property for a positive
standard-basis walk in $\mathbb Z^d$: $P_0=0$ and

$$
P_{n+1}-P_n\in\{e_1,\ldots,e_d\},\qquad
 e_1=(1,0,\ldots,0),\quad\ldots,\quad e_d=(0,\ldots,0,1).
$$

Each $e_j$ has exactly one $1$, in coordinate $j$, and zeros elsewhere.
The coordinates of $P_n$ sum to $n$. Thus, **for basis walks**, avoidance is
also equivalent to

$$
(k-j)(P_j-P_i)\ne(j-i)(P_k-P_j)\qquad(0\le i<j<k).
$$

Do not substitute this time-weighted test for the rank test on arbitrary
finite-step walks: their coordinate sums need not equal time.

For a fixed number $x$, the implication matrix is:

| Premise model | Existence proved | Impossibility proved |
|---|---|---|
| 3D, at most $x$ step types | $\mathcal E(3,x)\Rightarrow\mathcal B(x)$ | $\neg\mathcal E(3,x)$ alone gives no basis-walk conclusion |
| Positive basis, dimension $x$ | $\mathcal B(x)$ alone gives no 3D conclusion | $\neg\mathcal B(x)\Rightarrow\neg\mathcal E(3,x)$ |

The second valid implication is the **contrapositive** of the first.
"No conclusion" means not implied by this reduction; it does not assert that
a reverse theorem is false. "Impossible" means a theorem about **all** walks
in the indicated class, not a failed search or a family-specific obstruction.

Equivalently, the encoding excludes the combination "3D possible, basis
impossible". It does not exclude "basis possible, 3D impossible"; whether
that latter combination actually occurs is part of the joint problem.

**Vertex convention.** Allowing revisits while requiring an infinite set of
distinct vertices would not change these thresholds. In the directed step
graph on that set, arbitrarily long finite simple paths from the initial
vertex exist: finite outdegree makes every bounded-distance ball finite.
The finitely branching tree of such paths has an infinite branch by König's
lemma. That branch is a self-avoiding walk using the same step set and a
subset of the original vertices, so it inherits avoidance.

## 2. The common feasibility region

**Encoding lemma (Shallit's basis-encoding principle).** For every $r,s$,

$$
\mathcal E(r,s)\Longrightarrow\mathcal B(s).
$$

**Proof.** Label the used vectors $v_1,\ldots,v_t$, where $t\le s$. Replace
step $v_j$ by $e_j$ and let $P_n$ count the first $n$ labels. Define the linear
map $T(e_j)=v_j$, with arbitrary columns for unused labels. Then $T(P_n)=Q_n$.
A collinear triple of count vectors would have three distinct, collinear
images because the $Q_n$ are distinct. This contradicts the hypothesis.
Global injectivity of $T$ is not required. $\square$

Conversely, $\mathcal B(s)\Rightarrow\mathcal E(s,s)$, using the standard basis
as the step set. Appending zero coordinates or allowing more unused step
types preserves feasibility. In particular,

$$
 r\ge s\quad\Longrightarrow\quad
 \bigl(\mathcal E(r,s)\Longleftrightarrow\mathcal B(s)\bigr).
$$

Define the minimum step-count profile, with $\min\varnothing=\infty$,

$$
 m(r)=\min\{s\ge1:\mathcal E(r,s)\},\qquad
 d_*=\min\{d\ge1:\mathcal B(d)\},\qquad s_*=m(3).
$$

The original finite-step theorem and encoding make both minima finite. The
encoding lemma and the basis construction in dimension $d_*$ give

$$
\boxed{d_*=\min_{r\ge1}m(r)\le m(3)=s_*}.
$$

Thus $d_*$ is also the **minimum number of step types when ambient dimension
is unrestricted**, whereas $s_*$ is the minimum with ambient dimension fixed
at three. Moreover, $m(r)$ is nonincreasing, and

$$
 m(r)=d_*\qquad(r\ge d_*).
$$

**Aggregate task.** Determine $(d_*,s_*)$ exactly, with unconditional infinite
constructions and universal matching lower bounds. In particular, determine
whether the nonnegative compression gap

$$
\Delta=s_*-d_*
$$

is zero. Proving equality without finding the common value would establish a
useful reduction, but would not complete the exact-minimum task.

## 3. Current bounds and decisive outcomes

The ternary abelian-square obstruction proves $d_*\ge4$, and encoding then
proves $s_*\ge4$. The original [sixteen-step construction](../../paper/erdos193.tex)
gives a coarse unconditional ceiling of sixteen for both quantities.

The tagged $g_{85}$ construction already has the six spatial steps

$$
\{(1,0,5),(0,3,5),(-1,-2,5),(0,-1,1),(1,1,6),(-1,-1,2)\}.
$$

Its [written infinite argument](../../paper/unit_step_walk_N6_short.tex) and
basis encoding supply the proposed improvement for **both** models. The
construction is already found, not merely a proposed search. Independent
review of its proof remains pending. Subject to that review, the working
bounds and possible ordered pairs are

$$
4\le d_*\le s_*\le6,
$$

$$
(d_*,s_*)\in\{(4,4),(4,5),(4,6),(5,5),(5,6),(6,6)\}.
$$

No one of these pairs is asserted as the answer.

| New result | Consequence, using the proposed six-step upper bound |
|---|---|
| Four-step 3D construction | $(d_*,s_*)=(4,4)$ |
| Impossibility of 5D basis walks | $(d_*,s_*)=(6,6)$ |
| Five-step 3D construction | $(d_*,s_*)\in\{(4,4),(4,5),(5,5)\}$ |
| A 4D basis construction | $d_*=4$; $s_*\in\{4,5,6\}$ remains |
| A 5D basis construction | $d_*\le5$; it does not alone improve the 3D upper bound |
| Impossibility of five-step 3D walks | $s_*=6$; $d_*\in\{4,5,6\}$ remains |

The [six-vector optimality argument](../../design/SIGNED-GAUSSIAN-UNIT-STEP-OPTIMIZATION.md#optimality-inside-this-tag-scheme)
is restricted to the specified signed-Gaussian four-state tagging scheme.
It is not either of the universal impossibility results in this table.

## 4. Projection: the existential question versus the universal one

Let $\mathcal W_d$ be the infinite words over $\{1,\ldots,d\}$ whose consecutive
nonempty blocks never have equal normalized letter counts, even at unequal
lengths. Their cumulative Parikh vectors $P_n(w)$ are exactly the valid basis
walks; see the [equivalent word problem](PROBLEM.md).

For a particular $w\in\mathcal W_d$, define

$$
\operatorname{Proj}_3(w)\quad\Longleftrightarrow\quad
\exists A\in\mathbb Z^{3\times d}\ \forall i<j<k:\quad
\operatorname{rank}_{\mathbb Q}
 [\,A(P_j-P_i)\quad A(P_k-P_j)\,]=2.
$$

The five columns when $d=5$, or the $d$ columns in general, are the spatial
step vectors. The rank condition also prevents repeated projected vertices:
any repeated pair would give a rank-deficient triple with a later vertex.
Unused columns and coincidences among unused step labels are harmless; at
most $d$ spatial types are permitted.

Encoding and projection give the exact formulation

$$
\mathcal E(3,d)\Longleftrightarrow
\exists w\in\mathcal W_d:\operatorname{Proj}_3(w).
$$

Consequently,

$$
\boxed{s_*=d_*\Longleftrightarrow
\exists w\in\mathcal W_{d_*}:\operatorname{Proj}_3(w)}.
$$

Only **one optimal-alphabet witness** needs a 3D realization. The assertion
that **every** valid basis word has one is stronger and is not required.
Failure of one word to admit any projection would refute that universal
assertion, but would not itself prove $s_*>d_*$. Failure of one chosen matrix
refutes still less: only that matrix for that word.

For a fixed valid basis word, put $U=P_j-P_i$ and $V=P_k-P_j$. They are
linearly independent. The exact matrix condition can also be written

$$
\ker_{\mathbb Q}A\ \cap\ \operatorname{span}_{\mathbb Q}\{U,V\}
=\{0\}\qquad\text{for every }i<j<k.
$$

A convenient **restricted search family** takes columns $(a_j,b_j,1)$, so
projected height equals time. In this clock-height setting,

$$
A\bigl((k-j)U-(j-i)V\bigr)\ne0
$$

is an equivalent test. For general matrices it is only a necessary condition,
not a sufficient one. There is no assertion that all admissible 3D walks can
be normalized into this family. For example, $U=e_1,V=e_2$ with images
$(1,0,1)$ and $(2,0,2)$ gives distinct collinear vertices at times $0,1,2$,
even though $A(U-V)\ne0$.

## 5. A second unification: the order of the quantifiers

Let $\mathcal F_N(S)$ mean that there is a triple-free, distinct-vertex walk
starting at zero with **$N$ steps** from $S\subset\mathbb Z^3\setminus\{0\}$.
For every fixed alphabet size $s$,

$$
\boxed{\mathcal B(s)\Longleftrightarrow
\forall N\ge1\ \exists S_N,\ |S_N|\le s:\ \mathcal F_N(S_N)},
$$

whereas

$$
\boxed{\mathcal E(3,s)\Longleftrightarrow
\exists S,\ |S|\le s\ \forall N\ge1:\ \mathcal F_N(S)}.
$$

Here all sets consist of nonzero integer vectors. Hence:

- $d_*$ is the least step budget supporting **arbitrarily long finite 3D
  examples, with the step vectors allowed to depend on length**;
- $s_*$ is the least budget for which **one fixed step set works for all
  lengths**, equivalently for an infinite walk.

### Finite projection lemma

Every finite triple-free basis prefix $P_0,\ldots,P_N$ admits an integer
projection into 3D preserving avoidance, even into a plane. To see this, set
$B=N^2+2$ and give letter $r$ the vector

$$
 v_r=(B^{r-1},0,1)\qquad(1\le r\le s).
$$

For a triple let $a=j-i$, $b=k-j$, and $D=b(P_j-P_i)-a(P_k-P_j)$.
Then $D\ne0$, $\sum_rD_r=0$, and $|D_r|\le ab\le N^2$. Its highest nonzero
base-$B$ term dominates the sum of all lower terms, since $B-1>N^2$.
Thus $\sum_r B^{r-1}D_r\ne0$. The projected height equals time, so the
projected triple is not collinear. This constructs the required finite
projection; its coefficients grow with $N$.

### Compactness proofs and the missing uniformity

A basis word supplies every finite prefix, and the lemma supplies its
$S_N$. Conversely, encoding arbitrary finite 3D examples gives triple-free
basis words of every length over a fixed $s$-letter alphabet. Their
prefix-closed, finitely branching tree has an infinite branch by König's
lemma. This proves the first boxed equivalence.

For a **fixed finite $S$**, the tree of valid finite $S$-walks is also
finitely branching. Having paths of every length is equivalent to having
an infinite branch. This proves the second boxed equivalence.

The difference is precisely

$$
\forall N\ \exists S_N
\qquad\text{versus}\qquad
\exists S\ \forall N.
$$

A sufficient and, in this formulation, equivalent uniformity condition is

$$
\mathcal E(3,s)\Longleftrightarrow
\exists R\in\mathbb N\ \forall N\ge1\ \exists S_N\subset
([-R,R]^3\cap\mathbb Z^3)\setminus\{0\},\ |S_N|\le s:\ \mathcal F_N(S_N).
$$

Indeed there are only finitely many menus inside this box. One must work
for unbounded lengths, hence for every length by taking prefixes, and
compactness supplies an infinite walk. The other direction takes the
largest coordinate magnitude of a fixed successful menu.

Likewise, for a **fixed** basis word, integer matrices $A_N$ that preserve
prefixes and have coefficients uniformly bounded independently of $N$
yield one matrix preserving the whole word. Without that bound, finite
success does not imply an infinite realization. This is why larger prefix
scans alone cannot resolve the joint minimum.

## 6. Broader questions and explicit non-assumptions

**Collinearity trade-off (secondary).** Define

$$
 C_3(s)=\min_{S,Q}\ \sup_{\ell}\#\{n:Q_n\in\ell\},
$$

where $S$ has at most $s$ nonzero integer vectors, $Q$ ranges over infinite
self-avoiding $S$-walks from zero, and $\ell$ ranges over affine lines in
$\mathbb R^3$. Values may be infinite. Then

$$
 s_*=\min\{s:C_3(s)=2\}.
$$

This places [Adenwalla's step-count and forced-collinearity question](https://www.erdosproblems.com/forum/thread/193#post-8847)
in the same framework. The [four-collinear draft](../../design/WEAK-ABELIAN-CUBE-DRAFT-REVIEW.md)
has four spatial return displacements and would give $C_3(4)\le3$ if vetted.
It does not prove $C_3(4)=2$ or settle the triples threshold.

**No universal 2-adic hypothesis.** The [valuation framework](FRAMEWORK.md)
is a sufficient certificate, not a condition imposed on $\mathcal E$ or
$\mathcal B$. The literal equality
$\nu_2((\Delta X)^2+(\Delta Y)^2)=\nu_2(\Delta H)$ is not coordinate-invariant:
uniformly doubling a successful finite-step 3D walk preserves avoidance and
step count but shifts the two sides by two and one, respectively. Whether
an appropriate hidden certificate is necessary is a separate, stronger
structural question. Even such a certificate would not alone extend the
four-state six-vector lower bound to all constructions.

[Adenwalla's chaotic-orderings comparison](https://www.erdosproblems.com/forum/thread/proof-claim:5a48dd7b490340c598f617b09282d003#post-8846)
identifies related use of 2-adic valuation in Ardal, Brown, and Jungić,
[*Chaotic Orderings of the Rationals and Reals*](https://doi.org/10.4169/amer.math.monthly.118.10.921)
(2011). Its citation and abstract have been checked, but the full proof has
not yet been compared. It is not used as a premise here.

## 7. Completion criteria and checks

1. Independently vet the existing six-step/6D proof and maintain the distinction
   between the accepted original theorem and follow-up drafts.
2. Prove exact $d_*$ and $s_*$, or preserve an explicit unresolved pair list.
   Equality alone, finite success, or a lower bound inside one scheme is not
   completion.
3. Pursue a 4D/5D basis construction or universal obstruction; alternatively,
   seek a small 3D step menu with an infinite proof. A projected proof can
   establish the basis theorem at the same time.
4. Treat uniform integer realization or a minimal-word projection theorem as
   possible ways to bridge the models, not assumptions. Do not require a
   classification of every valid walk merely to establish the minima.

The bounded exact-integer checks in [joint_minimum_examples.mjs](joint_minimum_examples.mjs)
exercise the finite projection lemma and the distinction between general
rank and clock-height tests. Run:

```sh
node research/unit-step/joint_minimum_examples.mjs
node research/unit-step/check.mjs
```

These are finite algebra/consistency tests, not certification of the infinite
compactness arguments or a new construction. See the [AI checkpoint](AI-CHECKPOINT.md)
for the manuscripts, prior failed approaches, and proof-oriented next steps.
