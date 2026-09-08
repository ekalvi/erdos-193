# Track D: an arithmetic obstruction to substitution-scaling 3D projections

**Research note, September 6, 2026.** Deliverable for
[task D](../PARALLEL-TASKS.md#d-seek-economical-3d-realizations).
This is a proved obstruction to an explicitly restricted projection class,
with an exact arithmetic checker. It is not a five-step impossibility theorem,
an infinite avoidance proof for the candidate, or a determination of
$(d_*,s_*)$. The argument is not Lean-formalized; independent review is welcome.

The input is **Jeffrey Shallit's** cyclic five-letter candidate, as recorded in
[the investigation](../../../design/UNIT-STEP-4D-5D-INVESTIGATION.md#3-shallits-five-letter-candidate):

$$
h(0)=01213101314310,\qquad h(r)=h(0)+r\pmod5.
$$

The new argument below is an AI-assisted track result, not collaborator
approval or a change to any manuscript's attribution. No received manuscript,
central checkpoint, or other track's files are modified.

## 1. Exact class excluded

Let $w=h^\infty(0)$, and let $F(n)\in\mathbb Z^5$ count its first $n$ letters.
Fix a rational matrix $A\in\mathbb Q^{3\times5}$ and put $Q(n)=AF(n)$.
Integer matrices, with their at most five fixed integer step vectors, are
included. We do **not** require clock-height columns.

**Theorem.** Suppose there exist a fixed integer $t\ge1$, a fixed real matrix
$B\in\mathbb R^{3\times3}$, and a constant $C<\infty$ such that

$$
\|Q(14^t n)-BQ(n)\|_2\le C\qquad\text{for every }n\ge0. \tag{1}
$$

Then all five columns of $A$ are identical. Consequently $Q(n)=nv$ for a
fixed $v\in\mathbb Q^3$, and this projected walk is not triple-free.

Thus **no rational 3D projection with a fixed substitution scaling, even up
to a uniformly bounded error, can work for this word**. In particular it
excludes a triple-free projection satisfying $AM^t=BA$ for even one positive
$t$, or a recursion with a fixed $B$ and finitely many additive corrections
at aligned block boundaries. Blocking does not evade the obstruction.
There is no assumption that the basis candidate itself avoids triples.

**Not excluded:** a fixed integer projection with no law (1), unbounded
scaling errors, state-dependent linear maps instead of one $B$, another
five-letter word, or an unrelated four/five-step construction. In particular,
this does not refute $\operatorname{Proj}_3(w)$ from
[the joint formulation](../JOINT-MINIMUM.md#4-projection-the-existential-question-versus-the-universal-one).

## 2. Incidence algebra and a certificate valid for all powers

Columns of the incidence matrix count $h(0),\ldots,h(4)$:

$$
M=\begin{pmatrix}
3&1&3&1&6\\
6&3&1&3&1\\
1&6&3&1&3\\
3&1&6&3&1\\
1&3&1&6&3
\end{pmatrix},\qquad F(14n)=MF(n).
$$

Let $R e_r=e_{r+1\bmod5}$ and
$f(x)=3+6x+x^2+3x^3+x^4$. Then $M=f(R)$. The four-dimensional rational space

$$
H=\{u\in\mathbb Q^5:\textstyle\sum_r u_r=0\}
$$

is $M$-invariant. For a primitive fifth root $\zeta$, the map

$$
T:H\longrightarrow K=\mathbb Q(\zeta),\qquad
T(u)=\sum_{r=0}^4u_r\zeta^r
$$

is a rational vector-space isomorphism. Indeed,
$\Phi_5(x)=1+x+x^2+x^3+x^4$ is irreducible: $\Phi_5(x+1)$ is Eisenstein at 5.
The only rational relations among $1,\zeta,\ldots,\zeta^4$ have all five
coefficients equal; their intersection with $H$ is zero. Both spaces have
dimension four. Moreover,

$$
T(Mu)=\alpha T(u),\qquad
\alpha=f(\zeta)=2+5\zeta+2\zeta^3.
$$

For orientation, the characteristic polynomial on $H$ is

$$
p(X)=X^4-X^3+31X^2-51X+421,\qquad \det M=14\cdot421.
$$

Irreducibility of $p$ alone would not justify a claim about every $M^t$.
The following modular certificate supplies that missing quantifier.
The integer 421 is prime, and evaluation $\zeta\mapsto279$ defines a ring
homomorphism $\rho:\mathbb Z[\zeta]\to\mathbb F_{421}$. The exact table is

| $a$ | $279^a\pmod{421}$ | $f(279^a)\pmod{421}$ |
|---|---:|---:|
| 1 | 279 | 0 |
| 2 | 377 | 340 |
| 3 | 354 | 171 |
| 4 | 252 | 332 |

Here $279^5=1\pmod{421}$, $279\ne1$, and $\Phi_5(279)=0\pmod{421}$.
The four automorphisms of $K$ send $\zeta$ to $\zeta^a$, $1\le a\le4$.
For every $t\ge1$ and every $a\ne1$,

$$
\rho(\alpha^t)=0,
\qquad
\rho\bigl(f(\zeta^a)^t\bigr)=f(279^a)^t\ne0.
$$

Thus $\alpha^t$ differs from each of its other conjugates. Any equality
between two other conjugates can be carried to one involving $\alpha^t$
by a Galois automorphism, so all four are distinct. It follows that

$$
[\mathbb Q(\alpha^t):\mathbb Q]=4,
\qquad \mathbb Q[\alpha^t]=K
\qquad\text{for every }t\ge1. \tag{2}
$$

This is an all-powers argument using nonzero powers in a field, **not** a
finite scan of exponents.

**Invariant-subspace consequence.** For every $t\ge1$, the only rational
$M^t$-invariant subspaces of $H$ are $0$ and $H$. To see this, identify $H$
with $K$ using $T$. A nonzero invariant subspace containing $z\ne0$ contains
$q(\alpha^t)z$ for every rational polynomial $q$. By (2), these are all of
$K$, since multiplication by $z$ is invertible in the field.

## 3. Exact scaling forces all columns to coincide

First suppose $AM^t=BA$. Since $\operatorname{rank}_{\mathbb Q}A\le3$,
$\dim_{\mathbb Q}\ker A\ge2$, so

$$
\dim_{\mathbb Q}(\ker A\cap H)\ge2+4-5=1.
$$

The rational subspace $\ker A\cap H$ is $M^t$-invariant. This holds even
when $B$ is real: $Au=0$ implies $AM^t u=BAu=0$, and $M^t u$ is rational.
The consequence of (2) therefore gives $H\subset\ker A$. Each $e_r-e_s$
belongs to $H$, whence $Ae_r=Ae_s$ for every pair of letters. This proves
the exact-scaling case, without any restriction on step heights or signs.

## 4. Bounded errors cannot help

Here is a general rigidity lemma useful beyond this candidate.

**Lemma (expansive incidence).** Let an $L$-uniform substitution fixed point
contain every letter, with prefix counts $F(Ln)=MF(n)$ and an invertible
incidence matrix satisfying $\|M^{-k}\|_2\to0$. If a real matrix $D$ satisfies
$\sup_n\|DF(n)\|_2<\infty$, then $D=0$.

**Proof.** Let the uniform bound be $C$. For each letter $r$ choose an
occurrence $w_{m_r}=r$. For all $k\ge0$,

$$
DM^k e_r
 =D\bigl(F(L^k(m_r+1))-F(L^k m_r)\bigr),
\qquad \|DM^k e_r\|_2\le2C.
$$

With $s$ letters, the column bounds give $\|DM^k\|_2\le2C\sqrt{s}$.
Consequently
$\|D\|_2\le2C\sqrt{s}\,\|M^{-k}\|_2\to0$. $\square$

All five letters occur already in $h(0)$. Expansion for this particular $M$
has a simple integer sum-of-squares certificate, valid for every real $x$:

$$
\boxed{\|Mx\|_2^2
 =11\|x\|_2^2
  +4\sum_{r=0}^4(x_{r+1\bmod5}-x_r)^2
  +37\Bigl(\sum_{r=0}^4x_r\Bigr)^2.} \tag{3}
$$

Thus $\|M^{-k}\|_2\le11^{-k/2}\to0$. Apply the lemma to
$D=AM^t-BA$: equation (1) is exactly the boundedness of $DF(n)$.
It follows that $D=0$, reducing to Section 3. If the common column $v$ is
nonzero, $Q(0),Q(1),Q(2)=0,v,2v$ are distinct and collinear; if $v=0$, the
vertices coincide. Either case fails the required rank-two condition.
This completes the theorem. $\square$

## 5. Why the rational/integer requirement matters

There is an exact **real**, nonlattice 3D Fourier projection with columns

$$
v_r=(\operatorname{Re}\zeta^r,\operatorname{Im}\zeta^r,1),
\qquad 0\le r\le4.
$$

Its substitution scaling multiplies the horizontal complex coordinate by
$\alpha$ and height by 14. It preserves triple avoidance of **any valid
five-letter basis word**: for adjacent intervals of lengths $a,b>0$, write
$D=bU-aV$. Projected collinearity, using the clock height, says
$\sum D_r\zeta^r=0$; also $\sum D_r=0$. The same cyclotomic argument gives
$D=0$, which is exactly source collinearity. This is not an avoidance proof
for Shallit's unproved candidate.

These five real columns are rationally independent: a rational relation
must have all coefficients equal from the horizontal coordinate, and their
sum zero from height. Therefore no invertible real coordinate change can
put all five into $\mathbb Q^3$, let alone $\mathbb Z^3$, where any five
vectors are rationally dependent. Selecting one complex Fourier embedding
solves the real-coordinate compression, **not** the lattice problem.
Rounding these columns or succeeding on finite prefixes does not supply one
integer matrix that works at all lengths.

## 6. Reproduction and evidence level

From the repository root:

```bash
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p .checkpoint-track-d
node research/unit-step/tracks/check_d_shallit_projection.mjs \
  | tee .checkpoint-track-d/arithmetic.jsonl
node research/unit-step/joint_minimum_examples.mjs
node research/unit-step/check.mjs
```

[The checker](check_d_shallit_projection.mjs) independently reconstructs
$M$ from the substitution and uses only exact `BigInt` arithmetic. It checks
the characteristic polynomials, the cyclotomic action on $H$, the norm 421,
primality, the entire four-row separating table and six conjugate pairs,
and the sum-of-squares matrix identity (3). It also cross-checks the known
Gram polynomial $(X-196)(X^2-42X+421)^2$.

This fixed-size verifier takes less than a second, uses one worker and no
subprocesses, and writes no search/checkpoint state. It can be rerun in full
after interruption; there is no expensive accumulated computation to lose.
Its JSON output records timestamps, the source SHA-256, exact certificate
data, and scope. The optional durable log above stays in the ignored
checkpoint directory, separate from this proof artifact. No prefix or
bounded-exponent search is performed. Passing the checker validates the
finite arithmetic inputs; Sections 2–4 supply the infinite argument.

## 7. Stopping point, blocker, and proposed synthesis

**Result:** an unconditional, all-iterate obstruction to rational 3D
substitution scaling, strengthened to allow arbitrary bounded additive
errors, for this particular five-letter word. The expansive-incidence lemma
is a general auxiliary reduction. Neither result assumes a 2-adic law.

**Remaining blocker:** the theorem says nothing against a fixed rational
projection whose scaling discrepancy is unbounded. Hence a general integer
projection of this word, the word's own infinite basis-avoidance claim,
four-letter constructions, and the exact pair $(d_*,s_*)$ remain unresolved.

**Next bounded step:** if continuing with this word, do not search for a
closed three-coordinate linear substitution recursion, even after blocking
or adding bounded boundary errors. Instead keep the full four-dimensional
rational deviation state when analyzing a proposed integer observation.
For a clock-height matrix $A=(a;b;\mathbf1^T)$, the precise obligation is

$$
\{(k-j)(F(j)-F(i))-(j-i)(F(k)-F(j)):0\le i<j<k\}
\ \cap\ \{u\in H:a\cdot u=b\cdot u=0\}=\varnothing.
$$

This must exclude zero as well as nonzero kernel hits, and cover all interval
ratios. A boundary-state reduction must track components discarded by $A$;
one may not replace $AM$ by $BA$. A finite successful projection alone is
still insufficient, as explained by
[the uniformity distinction](../JOINT-MINIMUM.md#5-a-second-unification-the-order-of-the-quantifiers).

**Proposed checkpoint entry for later synthesis:** “Track D rules out rational
3D projections of Shallit's five-letter word admitting a fixed linear scaling
under any substitution iterate, even with bounded errors. General integer
projections remain open; no change to the minimum bounds.” Central files are
left untouched for parallel work. A [research-only visual summary](../../../viz/unit-step-track-d.html)
records the obstruction and changed route, with the independent-review caveat.
It is explicitly excluded from production by `.dockerignore`, preserving the
prior decision in PR #46 to keep unreviewed follow-up claims off the public site.
There is no public theorem-status or minimum-bound change.
