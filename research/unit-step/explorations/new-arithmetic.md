# New-arithmetic: obstructions to alternate norm mechanisms

**September 6, 2026. Independent AI research report; not human approval.**

## 1. Verdict and exact scope

No four- or five-step construction was obtained. No global lower bound on
`d_*` or `s_*` is improved. The strongest finding is an unconditional
**restricted no-go theorem**:

> For any odd prime, a ramified binary quadratic norm cannot certify an
> infinite bounded-step, strictly increasing-height walk by requiring both
> the all-pairs valuation identity and a fixed sum-free set of leading-unit
> ratios. Such a certificate forces the height set to have density zero.

This rules out a natural repair of the invalid argument that an odd-prime
valuation identity alone excludes triples. Two further obstructions are proved:

* A quadratic form anisotropic modulo the chosen prime cannot satisfy the
  valuation identity on any infinite bounded-increment distinct-height walk.
  This includes using the Eisenstein norm at 2 or the Gaussian norm at 3.
* A specified stationary, reversible binary source for `X²+2Y²` requires at
  least six **states**. States are not spatial step types; this is not `s_*≥6`.

An explicit four-state `X²−2Y²` attempt turns out to be exactly an integer
coordinate change of the existing alternating Gaussian source. It supplies no
new mechanism or smaller menu.

**Prior work used:** Cambie–Kalviainen's Gaussian source/valuation method;
Cambie's offsets; Kalviainen's alternating signed source and proposed six-step
construction; Shallit's basis encoding. Definitions and prior proof status are
as in `AI-CHECKPOINT.md`, `PROBLEM.md`, `JOINT-MINIMUM.md`, and `FRAMEWORK.md`.
The observations below were derived in this session; no literature novelty is
claimed. The original Erdős 193 theorem is distinct and already settled.

## 2. Proofs and explicit failed construction step

### 2.1 Why the proposed odd-prime repair would exclude triples

Write `v_p` for the valuation and `F` for a homogeneous quadratic form.
Consider integer vertices `Q_n=(Z_n,H_n)` with strictly increasing heights.
For **every** `m<n`, require

\[
 F(Z_n-Z_m)\ne0,\qquad
 v_p(F(Z_n-Z_m))=v_p(H_n-H_m),                         \tag{V}
\]

and, for a fixed `C ⊂ F_p^*`,

\[
 \overline{F(Z_n-Z_m)/(H_n-H_m)}\in C.                 \tag{U}
\]

The bar denotes reduction of a rational p-adic unit modulo p, which (V)
makes well-defined. Call `C` sum-free if `(C+C)∩C=∅`.

If three vertices were collinear, their spatial slope relative to height
would be a fixed rational vector `v`. Writing their successive positive
height differences as `A,B`, their three quotients in (U) would be

\[
 F(v)A,\quad F(v)B,\quad F(v)(A+B).
\]

They are p-adic units by (V); the third is the sum of the first two. Thus
sum-freeness excludes the triple. This is a valid sufficient certificate,
not a claim that it is realizable. For example `C={±c}` is sum-free when
`p≥5`. For odd p, (V) alone does not suffice: the three collinear points
`(X,Y,H)=(0,0,0),(1,0,1),(2,0,2)` satisfy (V) for `F=X²+pY²`.

### 2.2 Main no-go: ramified odd-prime norm plus any sum-free unit set

**Theorem.** Let p be odd, `a∈Z` with `p∤a`, and

\[
 F(X,Y)=X^2+p aY^2.
\]

There is no infinite integer sequence with `0<H_{n+1}−H_n≤D` for a fixed
finite D satisfying (V) and (U) for a fixed sum-free `C⊂F_p^*`.
There is no restriction on the number or size of planar steps. In particular,
no fixed finite 3D step menu with strictly increasing height can do this.

**Finite-field lemma.** The graph of a permutation `f:F_p→F_p` has three
collinear points when p is odd.

*Proof.* Suppose not. From any one graph point, the other `p−1` points have
nonzero finite slopes, because both coordinates are distinct. All these
slopes must differ. Therefore every nonzero slope occurs exactly once from
each point. Fix slope 1. Every point then has exactly one partner on its
slope-1 line; these lines partition the p points into pairs. This contradicts
odd p. ∎

*Proof of theorem.* The two summands of F have valuations of opposite parity,
so cancellation at the minimum is impossible:

\[
 v_p(F(x,y))=\min\{2v_p(x),1+2v_p(y)\}.               \tag{1}
\]

Use the usual value `v_p(0)=∞` in this formula. Consider any occupied height
residue class modulo `p^e`. We claim that it cannot have all p children
occupied modulo `p^{e+1}`. Suppose otherwise, and choose one vertex from each
child. Write their distinct next height digits as `t∈F_p`.

If `e=2r`, (V) and (1) say that all planar differences have both coordinates
divisible by `p^r`, and their X-coordinates divided by `p^r` have distinct
residues modulo p. After subtracting one planar reference point, denote those
residues by `f(t)`. Thus f is a permutation. For each chosen ordered pair,

\[
 \overline{F(\Delta Z)/\Delta H}
   =\frac{(\Delta f)^2}{\Delta t}.                    \tag{2}
\]

If `e=2r+1`, all X differences are divisible by `p^{r+1}`, all Y differences
by `p^r`, and the normalized Y residues instead give a permutation f. Now

\[
 \overline{F(\Delta Z)/\Delta H}
   =a\frac{(\Delta f)^2}{\Delta t}.                   \tag{3}
\]

The finite-field lemma supplies three collinear graph points. Order their
actual vertices by index. Their common finite-field slope `λ` is nonzero.
Equations (2) or (3) make their three unit ratios

\[
 \kappa\lambda^2(t_2-t_1),\quad
 \kappa\lambda^2(t_3-t_2),\quad
 \kappa\lambda^2(t_3-t_1),
\]

where `κ=1` or `a`. All three belong to C; the third is the sum of the first
two, a contradiction. This argument does **not** assume numerical ordering
of the digits and does **not** assume `C=−C`.

Thus every occupied node of the p-adic height residue tree has at most `p−1`
children. At most `(p−1)^k` residue classes modulo `p^k` are occupied, so for
any interval of integer length M,

\[
 \#(\{H_n\}\cap I)\le (p-1)^k(\lfloor M/p^k\rfloor+1).
\]

First letting M grow for fixed k and then letting k grow gives upper density
zero. But bounded positive increments give lower density at least `1/D` in
the positive height ray. Contradiction. ∎

**Scope.** This excludes the complete all-pairs certificate (V)+(U) for this
norm family, not all odd-prime constructions. State-dependent ratio sets,
additional information not expressible by one fixed C, split forms, other
recursions, or nonmonotone-height constructions are not ruled out. A rational
change of planar coordinates can transfer this obstruction when denominators
are uniformly cleared and the transformed certificate is explicitly checked;
no general classification is being assumed here.

### 2.3 Unramified / anisotropic-mod-p obstruction

**Theorem.** Suppose an integral quadratic form F in any finite number of
variables is anisotropic modulo p: `F(x)≡0 mod p` implies `x≡0 mod p`.
Then (V) cannot hold for infinitely many distinct integer heights with bounded
successive absolute increments.

*Proof.* For every nonzero integral x, factor out the greatest common p-power
from its coordinates. The remaining vector is nonzero modulo p, hence

\[
 v_p(F(x))=2\min_i v_p(x_i).
\]

Consequently every pairwise height difference has even valuation. In the
height residue tree, branching is possible at depths `0,2,4,…`, but each
occupied node at depth `1,3,5,…` has at most one child. Thus at most `p^k`
classes modulo `p^{2k}` are occupied. An interval of length M contains at most

\[
 p^k(\lfloor M/p^{2k}\rfloor+1)=O_p(\sqrt{M+1})
\]

occupied integers, choosing k near half `log_p(M+1)`. N distinct heights
with successive absolute increments at most D lie in an interval of length
at most DN, contradicting `N=O_p(√(DN+1))` as N grows. ∎

Concrete excluded alternatives are `X²+XY+Y²` at p=2 (the Eisenstein norm),
and `X²+Y²` at any prime `p≡3 mod 4`. This is about the valuation equality;
it does not exclude using these rings with another invariant.

### 2.4 A small-state obstruction for the other ramified binary norm

The following is a precise restricted model, **not** a step-count model.
Let a finite nonempty state set have N states, two permutations `f_0,f_1`,
and planar vectors `u_s=(x_s,y_s)∈Z²`, with every `x_s` odd. Require

\[
 u_{f_0(s)}+u_{f_1(s)}=L u_s,\qquad
 L=\begin{pmatrix}0&-2\\1&0\end{pmatrix}.              \tag{4}
\]

For `F=X²+2Y²`, this gives `F(Lz)=2F(z)`. The odd x condition is the easy
odd-interval base case: a sum of an odd number of source vectors has odd F.
Bijective digit columns give the usual equal-state descent. These conditions
are sufficient source ingredients, not necessary ingredients of every walk.

**Claim:** (4) forces `N≥6`.

*Proof.* Sum (4) over states. Since the digit maps are permutations,
`2Σu=LΣu`; hence `Σu=0`. Since all x's are odd, N is even.
Let A be the nonnegative integer matrix with `(Av)_s=v_{f_0(s)}+v_{f_1(s)}`.
Writing coordinate columns as X,Y gives `AX=−2Y`, `AY=X`. They span a real
invariant plane with eigenvalues `±i√2`; also `A1=2·1`.

Modulo 2, `AY=X` says the two children of each state have opposite y parities.
The permutation `f_1∘f_0^{-1}` therefore switches the two y-parity classes,
so all its cycles are even. Its permutation matrix has eigenvalue −1, and
factoring A as one permutation matrix times `I+R` shows `det A=0`.
Thus A has eigenvalues `2,0,i√2,−i√2`, so N is at least four. If N=4 these
are all the eigenvalues, giving `tr(A²)=4−2−2=0`, but `tr A=2`.
Nonnegativity makes this impossible: `tr(A²)=Σ_i A_ii²+Σ_{i≠j}A_ijA_ji`,
so zero forces all diagonal entries to vanish. Hence N cannot be four;
evenness now gives N≥6. ∎

This does not establish existence at six. For orientation, an eight-state
algebraic system satisfying (4) is

\[
 f_0(s)=s+1,\quad f_1(s)=s+3\pmod8,
\]

\[
 (u_0,\ldots,u_7)=
 ((1,-1),(1,0),(1,0),(1,1),(-1,1),(-1,0),(-1,0),(-1,-1)).
\]

The digit-0 map has no fixed initial state here; these equations alone are
not a newly certified infinite walk or a menu with eight (or fewer) types.
One would still need a compatible infinite source, all-pairs tags or returns,
and the resulting spatial menu count.

### 2.5 Explicit failed novelty test: the real quadratic four-state source

A promising-looking `F=X²−2Y²` source has

\[
 (u_0,u_1,u_2,u_3)=((1,0),(1,1),(-1,0),(-1,-1)),
\]

\[
 0\mapsto21,\quad1\mapsto10,\quad2\mapsto03,\quad3\mapsto32,
\]

with the fixed point beginning at 1. Its block-sum map is
`L(X,Y)=(2Y,X)`, and `F(Lz)=−2F(z)`. Both digit maps are permutations;
all source x-coordinates are odd, so the equal-state valuation descent works.

However, relabel states by `ℓ(0)=1, ℓ(1)=0, ℓ(2)=3, ℓ(3)=2`. The digit maps
become `r↦−r` and `r↦1−r mod 4`, exactly the alternating signed Gaussian
recursion. Moreover

\[
 u_s=B i^{\ell(s)},\qquad
 B=\begin{pmatrix}1&1\\1&0\end{pmatrix},\quad\det B=-1.
\]

Even the norm valuation is unchanged for **all** nonzero integer (x,y):

\[
 v_2(F(B(x,y)))=v_2(-x^2+2xy+y^2)=v_2(x^2+y^2).
\]

To prove this, remove their common power of 2. Opposite parities give valuation
zero for both forms; two odd coordinates give valuation one for both forms
by reduction modulo 4.

Transporting Cambie's offsets and the existing height tags gives exactly

\[
 \{(1,1,5),(3,0,5),(-3,-1,5),(-1,0,1),(2,1,6),(-2,-1,2)\},
\]

the B-images of the existing six vectors. These remain six distinct vectors.
This is a coordinate-conjugate existing construction, not a new upper bound.
No claim is made that every possible tagging of this source has been excluded.

**All-pairs obligation for any successor candidate:** give one fixed finite
integer menu, an infinite source, pairwise distinct vertices, and for every
`i<j<k` prove rank two for the two adjacent chords. A valid sufficient route
is the all-pairs p=2 identity (V), with nonzero form values and increasing
height. An equal-state identity alone needs a proved tagging or return-block
bridge. Neither small state count nor a finite prefix meets this obligation.

## 3. Finite evidence and reproduction

The accompanying small checker verifies exact algebra only:

* 257,280 sign-pair scalar cases for primes 5 through 43;
* 746 normalized permutation graphs for p=3,5,7, all containing a triple;
* the exact source conjugacy, block-sum identities, and six-vector image menu;
* 4,224 integer tests of the transformed norm valuation identity;
* all 617 ordered pairs of permutations on one through four states: none
  has `√−2` as an eigenvalue, checked by exact BigInt elimination;
* the eight-state algebraic equations above.

The proofs above do not extrapolate from these checks. No prefix search,
previous large chord test, or fixed six-label recoding enumeration was run.

From repository root:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
mkdir -p .checkpoint-new-arithmetic
set -o pipefail
node research/unit-step/explorations/new-arithmetic-check.mjs \
  | tee .checkpoint-new-arithmetic/check.log
```

The bounded checker runs in well under one second here; it is idempotent,
writes no proof artifact, and records timestamps and its source hash. Its
output log is ignored. No Python, parallel computation, packages, or subagents
were used. The infinite mathematical arguments still need independent review.

## 4. Actual implications for the two minima

None of these obstructions is universal over four- or five-step 3D walks.
Thus the established relation `4≤d_*≤s_*` is unchanged, as is the proposed
six-step ceiling subject to review. In particular, “six source states needed
in (4)” does not mean “six spatial displacements needed,” and does not imply
any new basis dimension lower bound. No equality of the two minima follows.

## 5. Strongest next attack and stopping reason

The useful reduction is to **stop trying a fixed sum-free leading-unit repair
of an odd-prime ramified norm certificate**: the full-branch finite-field
obstruction rules it out regardless of step budget. The unramified norm
variant is ruled out even before the unit refinement.

A next arithmetic attempt should therefore use a genuinely different binary
state recursion (not the displayed real-quadratic conjugate), or an odd-prime
invariant with state-dependent extra data not reducible to (V)+(U). For the
`X²+2Y²` route, the first concrete unresolved source sizes in the specified
reversible model are six and eight; even a source there needs a return/tag
compression proof before it says anything about five spatial types. This is
a sharply delimited research direction, not a candidate upper bound.

Stopping reason: the bounded investigation produced proved restricted
obstructions and exposed the one economical explicit source as prior work in
different coordinates. There is no justified ≤5-step candidate to test, and
larger prefix searches would not repair that gap.

**Files changed:**

* `research/unit-step/explorations/new-arithmetic.md` (this report, new).
* `research/unit-step/explorations/new-arithmetic-check.mjs` (new).
* Ignored run output: `.checkpoint-new-arithmetic/check.log`.

No manuscript, central checkpoint/problem file, visualization, or prior-agent
artifact was edited. No commit, publication, or deployment was made.
