# All-ratio direction reduction for Shallit's candidate

**September 7, 2026. Computer-assisted research lemmas; outside review pending.**
These results concern Shallit's five-letter candidate. They do **not** prove
full 5D avoidance, rule out 4D, or change the minimum-dimension bounds. The
original Cambie–Kalviainen Erdős 193 theorem is a separate, proved result.

## 1. A sharper remaining counterexample

Let \(w=h^\omega(0)\), \(h(0)=01213101314310\), and
\(h(r)=h(0)+r\pmod5\). Write \(F(n)\) for prefix counts.

The new exact certificates exclude, at **every position, length, and ratio**:

1. Collinear triples whose common direction is \(\mathbf1=(1,1,1,1,1)\).
2. Collinear triples whose common nonnegative direction has a zero coordinate.

Consequently, any remaining adjacent proportional blocks must have

\[
\psi(U)=rK,\qquad\psi(V)=sK,
\]

where \(r,s\) are positive integers and \(K\in\mathbb Z_{>0}^5\) is primitive
and **nonconstant**. The multipliers \(r,s\) need not be coprime when \(K\)
is chosen primitive. In particular \(\sum K\ge6\), so both block lengths
would be at least six.

This is a direction reduction across **all ratios**, not another enlargement
of the [near-equal-gap interval](SHALLIT-INTERVAL-EXTENSION.md). Positive
nonuniform directions remain unresolved.

- [Centered-return invariant](checks/shallit-centered-returns.json)
- [Independent validation and missing-letter audit](checks/shallit-centered-validation.json)
- [Producer](shallit_centered_returns.mjs), [separate checker](verify_shallit_centered_returns.mjs)

## 2. Exact quotient for the uniform direction

Set

\[
C(n)=5F(n)-n\mathbf1.
\]

Then \(C(i)=C(j)=C(k)\), with \(i<j<k\), is exactly a collinear triple
parallel to \(\mathbf1\) in the original walk. We prove that no centered
point is visited three times. Two visits are possible and are not rejected.

For a triple of ordered indices, store its strict-gap mask, the relative
letters \(u=w_j-w_i\), \(v=w_k-w_i\), and the canonical centered differences

\[
X=R^{-w_i}(C(j)-C(i)),\qquad
Y=R^{-w_i}(C(k)-C(i)).
\]

Unlike the earlier affine model, this quotient discards common uniform count
increments. It is sound because \(M\mathbf1=14\mathbf1\), so centering
commutes with the substitution matrix.

With \(B(a,t)\) the boundary-prefix counts and \(s_x=h(0)_x\), a digit
transition \((x,y,z)\) updates

\[
\begin{aligned}
X'&=R^{-s_x}\bigl(MX+5B(u,y)-5B(0,x)-(y-x)\mathbf1\bigr),\\
Y'&=R^{-s_x}\bigl(MY+5B(v,z)-5B(0,x)-(z-x)\mathbf1\bigr).
\end{aligned}
\]

The ordinary order/letter update is unchanged. There is no ratio parameter.

### Uniform ancestor bound

The [exact descent constants](SHALLIT-UNIFORM-NEIGHBORHOOD.md) give
\(\|M^{-1}\|_2<1/4\) and inverse-prefix diameter below \(117/80\).
Orthogonal projection to the zero-sum subspace cannot increase that diameter;
it commutes with \(M^{-1}\). Starting from a triple return, each floor
ancestor therefore satisfies

\[
\|X\|_2,\ \|Y\|_2,\ \|Y-X\|_2<
\frac{5(117/80)}{1-1/4}=\frac{39}{4}.
\]

Each vector is integral, has coordinate sum zero, and has all coordinates
congruent modulo five. Thus each squared norm is at most 95. Exactly **161**
lattice vectors meet these conditions, and **10,171** ordered pairs also
satisfy the third norm bound. This establishes a finite state universe
*before* the search; the largest possible universe including all headers is
at most \(4\cdot25\cdot10,171=1,017,100\).

The reachable invariant closes with **3,691 states**, 5,009 pair-compatible
candidate transitions, and 4,061 retained transitions. It contains the root,
contains every retained successor, and contains no strict state with
\(X=Y=0\). A genuine uniform-direction triple would give a guarded root-to-
accepting path, contradicting this checked closure.

The separate checker derives the substitution directly from its literal
image, exhausts the lattice by a different enumeration, checks the matrix
identities and diameter, and checks closure without importing the producer's
transition table. Missing-root, missing-successor, duplicate, and accepting
state mutations are rejected. The artifact stores vector indices into the
161-vector table, not growing uncentered counts.

### An actual infinite family is compressed

The factor at \([52,57)\) is `04213`, with counts \(\mathbf1\). Its iterated
images have counts \(14^r\mathbf1\). For every \(r\ge0\), the triples

\[
(i,j,k)=(52\cdot14^r,\ 57\cdot14^r,\ 57\cdot14^r+1)
\]

have exactly the same quotient state:

\[
(m,u,v)=(3,4,0),\quad X=0,\quad Y=(-1,-1,-1,-1,4).
\]

The endpoint letters follow from the digit recurrence; the \(r=0\) case is
checked directly. This state is nonaccepting. The original count vectors
are unbounded, but a single exact state represents this entire family.
This does not yet describe the saved large-state branch in the central-ratio
search, whose centered differences are themselves large.

## 3. Exclude missing-letter directions at all ratios

Every image \(h(a)\) contains every letter. Any factor of length 27 contains
a complete length-14 image: if it begins inside an image, at most 13 letters
precede the next complete image. Hence a factor missing a letter has length
at most 26.

If adjacent blocks are proportional and one lacks a letter, both lack that
letter, so their **whole concatenation** has length at most 26.

All adjacent letters of \(w\) are distinct: this holds inside every image,
and image boundaries preserve the parent pair because \(h(a)\) starts and
ends in \(a\). All 20 distinct-letter pairs already occur in \(h^2(0)\).
Every factor of length at most 26 is contained in \(h^2(ab)\) for one of
those pairs, since each level-two image has length 196.

The checker exhausts these 20 length-392 templates. It considers 2,437,500
ordered triples with total span at most 26 and checks the **463,550** of them
whose concatenation omits a letter. None satisfies the exact proportionality
equations. This finite language cover proves the claim at all positions,
not merely in a tested prefix.

## 4. Two shortcuts that still cannot finish the proof

### A finite literal affine list cannot cover all ratios

For every \(N\ge2\), take the actual triple \((0,1,N)\) and
\(\theta=1/N\). Its earlier affine error is

\[
e(\theta)=-e_0+F(N)/N.
\]

Since \(F(N)/N\) is a probability vector, \(\|e(\theta)\|_2\le\sqrt2<39/20\)
and its coordinate sum is zero. The error is nonzero because the word begins
`01`. Its floor ancestors have the first two indices equal to zero, and
errors of norm and coordinate sum at most \(14^{-r}\) at depth \(r\ge1\).
They also satisfy the guard at the same parameter.

Thus the literal affine graph over \(0<\theta<1\) contains infinitely many
nonaccepting reachable states: \(\sum B=N\) distinguishes them. No finite
closed list of individual affine functions can cover that whole domain.
This is a limitation of that representation, **not** of finite certificates
with symbolic families, nor a proof that the central interval
\([1/3,2/3]\) has an infinite graph.

### Centering does not preserve the full no-three-collinear property

Already at indices \((0,67,78)\),

\[
F(67)=(9,15,17,13,13),\quad F(78)=(9,18,21,15,15),
\]

while \(C(67)=2v\), \(C(78)=3v\), with
\(v=(-11,4,9,-1,-1)\). These three centered points are collinear, but the
original points are not. The quotient theorem excludes three **equal**
centered points, not three arbitrary collinear centered points.

## 5. Even nonuniform, full-support factor gcds are unbounded

The uniform-direction theorem does not rescue the tempting shortcut
“nonuniform factor counts have bounded gcd.” The following exact family
rules that out as well.

For any integer \(q\ge2\) coprime to \(\det M=5894\), reading digit 1 induces
the permutation

\[
(P,\ell)\longmapsto(MP+e_\ell,\ell+1)
\]

on \((\mathbb Z/q\mathbb Z)^5\times\mathbb Z/5\mathbb Z\). Invertibility of
\(M\) modulo \(q\) makes this map bijective. Its orbit from \((0,0)\) returns
after some positive \(t\le5q^5\), with \(5\mid t\). Therefore the actual
prefix at

\[
n_t=(14^t-1)/13
\]

has every count divisible by \(q\). It uses all five letters since \(t\ge5\).

It is never uniform. To see this, put \(T=R^{-1}M\),
\(z=5e_4-\mathbf1\), and \(G_t=R^{-t}C(n_t)\). The recurrence gives
\(G_t=\sum_{j=0}^{t-1}T^jz\). If \(G_t=0\), then
\((T^t-I)z=(T-I)G_t=0\). But \(z\ne0\) and
\(\|T^t z\|_2>4^t\|z\|_2\), contradicting \(T^t z=z\).

Taking \(q=3^k\) proves unbounded gcds even among **nonuniform, full-support**
factors. The small modular example \(q=3\) has period 40 and actual coordinate
gcd 615; the infinite lemma relies on the permutation and expansion argument,
not that sample. These are single factors, not adjacent proportional pairs.
Any successful global argument must use adjacency or other joint constraints.

## 6. Reproduction and next obligation

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
node research/unit-step/tracks/shallit_centered_returns.mjs
node research/unit-step/tracks/verify_shallit_centered_returns.mjs
node research/unit-step/tracks/test_shallit_centered.mjs
```

The producer checkpoints completed-parent queue progress; the validator
checkpoints rows and language templates. Both bind source/data identities and
checksums, handle SIGINT/SIGTERM, and write deterministic completed artifacts.
Budget exits are not proofs. The regression suite checks interruption/resume,
corruption/config rejection, direct versus cached transitions, and exact
large-index examples without generating large prefixes.

The remaining target is proportional adjacent blocks with a positive,
nonuniform primitive count vector. The joint shared-boundary arithmetic must
be controlled; neither counting more affine states nor a factor-gcd bound
settles it. The earlier central interval remains incomplete, and extremely
unbalanced ratios are not globally resolved either. A complete 5D construction
would still need a separate 4D impossibility theorem to establish minimum
five. All new lemmas await outside mathematical review and are not
Lean-formalized. Site source is updated; nothing is deployed.
