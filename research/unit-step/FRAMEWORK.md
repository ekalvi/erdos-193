# Working synthesis: the shared obstruction and the dimension bottleneck

**Research exposition, September 6, 2026.** This is a repository synthesis of
Cambie–Kalviainen's binary argument, Cambie's offset simplification, and the
ternary draft supplied by Shallit. It is not a new jointly approved paper or a
proof of the minimum dimension. Consult the [original manuscripts](../../paper/followups/README.md).

## 1. A common arithmetic lemma

Let $p$ be prime and $Q_n=(Z_n,H_n)$ be a sequence with integer, strictly
increasing heights. Let $F$ be a quadratic form on the spatial coordinates.
Suppose, for every distinct pair in an index set $S$,

$$
F(Z_n-Z_m)\ne0,\qquad
\nu_p(F(Z_n-Z_m))=\nu_p(H_n-H_m).
$$

Then no $p+1$ vertices indexed by $S$ are collinear.

**Argument.** If such vertices were on a line, their spatial slope relative to
height would be a fixed rational vector $v$. Homogeneity gives
$F(Z_n-Z_m)=F(v)(H_n-H_m)^2$. The nonzero assumption ensures $F(v)\ne0$.
Consequently all pairwise height differences have the same valuation
$e=-\nu_p(F(v))\ge0$. Subtract the first height and divide by $p^e$.
The resulting $p+1$ integers would have pairwise distinct residues modulo $p$,
which is impossible.

This elementary lemma extracts a shared proof step. Its hypotheses are the
hard construction-specific part; it supplies **no general construction for
arbitrary primes** and no dimension lower bound.

## 2. How the existing arguments fit

- **Cambie–Kalviainen / binary:** the source Gaussian walk establishes an
  equal-state identity with $F(X,Y)=X^2+Y^2$. State-dependent planar and height
  tags extend it to all pairs. Taking $p=2$ excludes three collinear vertices.
- **Cambie's 14D note / Kalviainen's 6D draft:** Cambie's changed offsets preserve
  the binary obstruction while identifying two pairs of steps. Kalviainen's
  alternating source restricts the occurring transitions from sixteen to
  eight, leaving six distinct displacements after those identifications.
- **Shallit-supplied ternary draft:** $F(X,Y)=X^2-3Y^2$ scales by $-3$ in the
  ternary descent. The identity is used only at a common state, then at the
  return vertices to state 0. Taking $p=3$ excludes four collinear returns.
  Five return-block types have only four different displacements.

Thus tagging all indices and selecting equal-state returns are two distinct
ways to use an arithmetic obstruction. Neither alone proves that a particular
number of basis directions is necessary.

## 3. Encoding and the sharp question

If a no-three-collinear walk uses finitely many displacement types
$v_1,\ldots,v_d$, count those types in a positive standard-basis walk $P_n$.
The linear map $T(e_j)=v_j$ maps $P_n$ back to the original vertices. A
collinear triple in $P_n$ would give one in its shadow, provided the shadow
vertices are distinct (in these constructions their heights increase).
This is Shallit's encoding principle in the present setting; $T$ need not be
injective on the whole space.

Conversely, the basis-walk counts show exactly why equal adjacent letter
proportions are forbidden. This gives the [geometric/combinatorial equivalence](PROBLEM.md),
not a third independent problem.

The number of types needed by **one such encoding** is only an upper bound on
$d_*$. It does not prove a global minimum. To reach the sharp threshold we
need either a new construction with fewer types or an obstruction to **all**
words on a smaller alphabet. The proved limitations of fixed g85 transition
coding do not exclude context-dependent or return-block constructions.

## 4. Focus

The useful synthesis question is: **which arithmetic structure is essential
for avoiding triples, and how economically can it be represented by positive
basis steps?** A separate general word-combinatorial lower bound may be needed.
The ternary result is a diagnostic comparison, not a substitute for resolving
4D/5D triple avoidance. No practical application or arbitrary-prime existence
theorem is asserted here.
