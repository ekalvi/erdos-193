# Arbitrary Gaussian state tags: an all-pairs classification and six-step obstruction

**September 6, 2026 — gaussian-tags research subagent. New analytic argument,
not human review or Lean certification.** Base: `aaf038f31f1433fc083360177efe8a67b67e5cb1`.

## 1. Verdict and exact scope

**New restricted theorem:** arbitrary integer height tags, arbitrary Gaussian
planar tags and scale, and arbitrary infinite sign streams do not reduce the
step count below six **if the lift satisfies the standard all-pairs valuation
identity, allowing any constant valuation offset**. The tags admitting that
identity are classified below. No coefficient bound, sign period, monotonicity
of height, or fixed state ordering is assumed.

Here is the precise family. Fix any infinite stream
`epsilon_j in {+1,-1}` and define

\[
 r(n)=\left[\sum_{j\ge0}\epsilon_j b_j(n)\right]_4,\qquad
 u_n=i^{r(n)},\qquad z_n=\sum_{m<n}u_m.
\]

Let `a` be a nonzero Gaussian integer, `L` a nonzero integer,
`c_0,...,c_3` Gaussian integers, and `t_0,...,t_3` integers. Set

\[
 W_n=a z_n+c_{r(n)},\qquad H_n=Ln+t_{r(n)}.
\]

All indices are retained. Subtracting the initial vertex is harmless. Write
`pi=1+i`, `v_pi(x)=nu_2(|x|^2)` for a nonzero Gaussian integer, and

\[
 \alpha=v_\pi(a),\qquad \beta=\nu_2(L).
\]

The **exact admissibility assumption** is that some fixed integer `kappa`
satisfies, for every pair of distinct indices,

\[
 W_n-W_m\ne0,\quad H_n-H_m\ne0,\qquad
 v_\pi(W_n-W_m)=\nu_2(H_n-H_m)+\kappa. \tag{V}
\]

The literal identity in the manuscripts is `kappa=0`. Allowing a constant
also covers independent integral rescalings of planar and height coordinates.

### Classification theorem

Condition (V) holds **if and only if** `kappa=alpha-beta` and, for every
pair of different states `r,s`,

\[
 \boxed{\quad
 \mu_{rs}:=\nu_2(t_s-t_r)<\beta,\qquad
 v_\pi(c_s-c_r)=\mu_{rs}+\kappa.
 \quad} \tag{T}
\]

In particular the four height tags are distinct modulo `2^beta`, and the
four planar tags are distinct modulo `pi^alpha`; necessarily
`alpha,beta >= 2`. These statements are necessary, not merely a convenient
sufficient tagging convention.

### Step-count theorem

Every lift satisfying (V), equivalently (T), uses **at least six distinct
spatial displacement vectors** in `Z^3`. The usual alternating six-step lift
attains six, so six is the exact minimum within this entire admissible family.

**Not claimed:** a universal lower bound `s_* >= 6` or `d_* >= 6`;
classification of every conceivable all-pairs certificate; impossibility of
an affine-tag lift certified by a different argument; or a new resolution of
the original Erdős 193 theorem.

### Prior versus new

The original Gaussian construction is due to Cambie–Kalviainen; Cambie's
offsets and Shallit's encoding underlie Kalviainen's six-step draft. The prior
read-only `A-SIX-STEP-AUDIT.md`, especially Section 6, establishes the narrower
obstruction with `a=2`, `H_n=4n+r(n)`, and a prescribed cyclic parity pattern
(up to the symmetries specified there). Its arbitrary-stream argument is a
useful lead, not an assumed proof of the present extension.

The new content here is necessity of the tag classification (including
ruling out overlapping height residue classes), removal of fixed height
ordering/representatives and scale, and the coefficient-free collision proof.
All needed source facts are proved below.

## 2. Full proof

### 2.1 An isometric version of the signed source

Put

\[
 f_\epsilon(n)=z_\epsilon(n)/u_\epsilon(n)\in\mathbb Z[i].
\]

Let `S epsilon` be the shifted stream and write `e=epsilon_0`. Grouping even
and odd summands gives

\[
\begin{aligned}
 u_\epsilon(2n)&=u_{S\epsilon}(n),&
 u_\epsilon(2n+1)&=i^e u_{S\epsilon}(n),\\
 z_\epsilon(2n)&=(1+i^e)z_{S\epsilon}(n),&
 z_\epsilon(2n+1)&=(1+i^e)z_{S\epsilon}(n)+u_{S\epsilon}(n).
\end{aligned}
\]

Consequently

\[
\begin{aligned}
 f_\epsilon(2n)&=(1+i^e)f_{S\epsilon}(n),\\
 f_\epsilon(2n+1)&=(1+i^{-e})f_{S\epsilon}(n)+i^{-e}. \tag{1}
\end{aligned}
\]

The two coefficients have `v_pi=1`. For endpoints of the same parity, their
constant terms cancel, and deleting the common low bit adds exactly one to
the valuation. For opposite parity, the even image is zero modulo `pi` and
the odd image is one modulo `pi`, so their difference has valuation zero.
Iterating exactly `nu_2(n-m)` times proves, **without a state-equality
hypothesis**,

\[
 v_\pi(f_\epsilon(n)-f_\epsilon(m))=\nu_2(n-m). \tag{2}
\]

Thus `f_epsilon` extends uniquely to an isometric map

\[
 f:\mathbb Z_2\longrightarrow R,
\]

where `R` is the completion of `Z[i]` at `pi`. In particular it is injective
and nonconstant. This follows directly by completing Cauchy sequences in
(2); no real/complex convergence is being asserted. It is also onto: for
each `k`, (2) gives an injection between the `2^k` source residues and the
`2^k` target residues, hence a bijection, and the compatible inverse residues
converge. Surjectivity is not needed below.

The familiar equal-state source identity is immediate from (2): if
`r(n)=r(m)=r`, then `z_n-z_m=i^r(f(n)-f(m))`.

### 2.2 All four states occur over every 2-adic neighborhood

Fix `k`, a low-bit residue `b mod 2^k`, and a desired state `r`. Among
positions at least `k`, one sign occurs at least three times. Choose three
such positions, all with sign `eta`. Keeping the low bits equal to `b`,
turn on zero, one, two, or three chosen high bits. Their states are

\[
 r(b)+q\eta\pmod4\qquad(q=0,1,2,3),
\]

which exhaust all states. Therefore, for every `x in Z_2` and state `r`,
there are natural indices `n_k -> x` 2-adically with `r(n_k)=r`.

Along these indices the source identity is exactly

\[
 z_{n_k}=i^r f(n_k)\longrightarrow i^r f(x).
\]

This density statement applies to every infinite sign stream; periodicity
or a bound on the locations of the chosen high bits is irrelevant.

### 2.3 Necessity: height residue classes cannot overlap

First choose any two distinct indices in one state. The equal-state identity
just proved forces `kappa=alpha-beta` in (V).

Suppose, seeking a contradiction, that two different states `r,s` have

\[
 t_r-t_s\in 2^\beta\mathbb Z_2.
\]

This includes equal integer tags. Since `L/2^beta` is a 2-adic unit,

\[
 \tau=(t_r-t_s)/L\in\mathbb Z_2.
\]

Fix any `x in Z_2`. By Section 2.2 choose state-`r` indices tending to `x`
and state-`s` indices tending to `x+tau`. Their height differences tend to
zero 2-adically. By (V) the corresponding planar differences tend to zero
`pi`-adically. Continuity therefore gives, for every `x`,

\[
 a i^r f(x)+c_r=a i^s f(x+\tau)+c_s,
\]

or, in the fraction field of `R`,

\[
 f(x+\tau)=\zeta f(x)+b,
 \qquad \zeta=i^{r-s}\ne1,\quad b=(c_r-c_s)/(a i^s). \tag{3}
\]

Let `q=2` or `4` be the order of `zeta`. Iterating (3), using
`1+zeta+...+zeta^(q-1)=0`, gives

\[
 f(x+q\tau)=f(x).
\]

Injectivity gives `q tau=0`. The additive group `Z_2` is torsion-free, so
`tau=0`. But (3) would then make `(1-zeta)f(x)` constant, contradicting that
`f` is nonconstant in a characteristic-zero field. This rules out the
supposed overlap.

Thus `mu_rs=nu_2(t_s-t_r)<beta` for every different pair of states. To obtain
the planar condition, choose indices in those two states tending to zero
2-adically. Their height differences tend to `t_s-t_r`, with eventual
valuation `mu_rs`, while their planar differences tend to `c_s-c_r` because
`f(0)=0`. Equation (V), or reduction modulo sufficiently high powers, gives

\[
 v_\pi(c_s-c_r)=\mu_{rs}+\kappa<\alpha.
\]

This proves (T). It also proves distinctness of the planar residues. Counting
residues proves `alpha,beta >= 2`.

### 2.4 Sufficiency and the complete residue description

Suppose (T) holds. For equal endpoint states, the source identity gives

\[
 v_\pi(W_n-W_m)=\alpha+\nu_2(n-m),\qquad
 \nu_2(H_n-H_m)=\beta+\nu_2(n-m).
\]

For different endpoint states, the planar source term is divisible by
`pi^alpha` and the height clock term by `2^beta`. The tag differences have
strictly smaller valuations, so they determine the two valuations without
cancellation. This proves (V), including nonvanishing of all chords.

This is also a classification of **all integer representatives**: only
`t_r mod 2^beta` and `c_r mod pi^alpha` matter. Once (T) holds, any independent
replacement

\[
 t_r\mapsto t_r+2^\beta k_r,\qquad
 c_r\mapsto c_r+\pi^\alpha d_r
\]

with integers `k_r` and Gaussian integers `d_r` preserves admissibility.
The scale's unit part, signs of the heights, and ordering of the four
representatives are unrestricted.

For `kappa=0`, choose any four distinct residues modulo `2^alpha` and an
isometric copy of their rooted binary residue tree among Gaussian residues
modulo `pi^alpha`. This describes exactly all solutions: pairwise depths of
common prefixes must agree. Every height choice has such a copy, for example
by sending binary digits `b_j` to `sum b_j pi^j`. More generally (T) is the
same finite-tree condition with depth shift `kappa`, including the requirement
that the shifted valuations be nonnegative.

In the minimal-scale case `alpha=beta=2`, the height residues can be **any
of the 24 state permutations of `0,1,2,3`**, not merely cyclic ordering.
For each such assignment, exactly eight assignments of the four Gaussian
residues modulo `pi^2` preserve the distances: exchange the two parity
branches, and independently exchange the two leaves in each branch.
Thus there are 192 paired residue assignments, before choosing unrestricted
representatives. The prior fixed-height proof concerned one height assignment
and its permitted planar parity assignments.

Finally (V) still certifies no three collinear vertices without monotone
heights. Heights of all vertices are distinct. On a hypothetical line,
all three complex slopes are equal and nonzero; their squared-norm
valuations are `kappa-nu_2(Delta H)`. The three height differences would
therefore have equal valuation, impossible for nonzero `A,B,A+B` because two
integers of the same valuation have a sum of larger valuation. Negative
height differences cause no change to this argument.

### 2.5 The key new collision lemma

For an ordered state pair let

\[
 V_{rs}=(a i^r+c_s-c_r,\ L+t_s-t_r).
\]

We identify a complex coordinate with its two integer coordinates.
For **different, non-loop transitions**, an equality `V_rs=V_uv` can occur
only if the four endpoint states are all different.

Indeed equal sources or equal targets immediately force equal integer height
tags, hence equal transitions. Reversed transitions would force equal height
tags too. It remains to rule out a two-edge directed path on distinct states,
which, after exchanging the two edges if necessary, has the form
`V_rs=V_sv`.

Put `d=t_s-t_r=t_v-t_s`, `mu=nu_2(d)`. By (T), applied to `r,v`,

\[
 \mu+1=\nu_2(t_v-t_r)<\beta.
\]

Write `C=c_s-c_r`; then `v_pi(C)=mu+kappa`. Equality of planar steps gives

\[
 c_v-c_r=2C+a(i^r-i^s).
\]

Since `v_pi(2)=2`, the right side has valuation at least

\[
 \min\{\mu+\kappa+2,\alpha\}>\mu+\kappa+1.
\]

But (T) applied to `r,v` requires valuation exactly `mu+kappa+1`, a
contradiction. This proves the lemma. It uses the strict scale separation
whose necessity was proved above, not a presumed cyclic parity coloring.

### 2.6 Every sign stream supplies the required transitions

An increment with `k` trailing ones has state change

\[
 \delta_k=\epsilon_k-\sum_{j<k}\epsilon_j\pmod4.
\]

Keeping those trailing bits and the next zero fixed, the high-bit choice in
Section 2.2 realizes this change from **every** starting state. Thus each
`delta_k` supplies all four corresponding transitions.

Put `D={delta_k:k>=0}`. It contains an odd change
`delta_0=epsilon_0`. Also `delta_1` is either `0` or `2`.

If `0 in D`, the four loops have distinct vectors `(a i^r,L)`. The odd
change supplies a directed four-cycle. Its tag-height increments `t_s-t_r`
are nonzero and sum to zero, so the actual step heights `L+t_s-t_r` have at
least two different values, neither equal to `L`.
Together these give at least six steps. (The collision lemma improves this
case to at least seven, but six suffices.)

If `0 notin D`, then `2 in D` and an odd change is present. Complex
conjugation together with the relabeling `r -> -r` exchanges changes `1`
and `3`, preserves admissibility and step count, and replaces `a,c_r` by
their corresponding conjugates. It therefore suffices to count the eight
transitions of changes `1` and `2`.

### 2.7 Solving the remaining collisions without coefficient enumeration

Subtract the common height `L` from each step for this count. Define

\[
 A_r=(a i^r+c_{r+1}-c_r,\ t_{r+1}-t_r),\qquad
 B_r=(a i^r+c_{r+2}-c_r,\ t_{r+2}-t_r),
\]

with subscripts modulo four. The collision lemma implies:

* No `A` equals a `B`: such two transitions share an endpoint.
* Among `A`'s only `A_0=A_2` or `A_1=A_3` is possible.
* `B_2=-B_0` and `B_3=-B_1`, with every `B` nonzero. The `B` menu therefore
  has either four values or two values. Two values mean either
  `B_0=B_1` or `B_0=B_3`, with the opposite pair merging automatically.

For `x=c` or `x=t`, abbreviate

\[
 K_x=x_0+x_3-x_1-x_2,\qquad
 J_x=-x_0-x_1+x_2+x_3.
\]

The complete relevant collision equations are

| Collision | Planar equation | Height equation |
|---|---|---|
| `A_0=A_2` | `K_c=2a` | `K_t=0` |
| `A_1=A_3` | `J_c=-2ai` | `J_t=0` |
| `B_0=B_1` | `K_c=a(1-i)` | `K_t=0` |
| `B_0=B_3` | `J_c=-a(1+i)` | `J_t=0` |

Simultaneous `K_t=J_t=0` forces `t_0=t_2` and `t_1=t_3`, forbidden by (T).
In particular at most one `A` pair can merge, so there are at least three
`A` values.

If there are four `B` values, the total is at least seven. If there are two:

* `B_0=B_1` precludes `A_0=A_2` because `a(1-i) != 2a`, and precludes
  `A_1=A_3` by the two height equations.
* `B_0=B_3` precludes `A_1=A_3` because `-a(1+i) != -2ai`, and precludes
  `A_0=A_2` by the two height equations.

Thus in the two-value case all four `A`'s are distinct, giving exactly the
lower bound `4+2=6`. Additional transitions can only increase the menu.
This completes the theorem for every infinite sign stream and every set of
coefficients satisfying (V).

## 3. Finite evidence, failed stronger step, and reproduction

**The proof above does not depend on finite enumeration.** A preliminary,
stronger idea was false: distinct integer height tags alone do not force six.
The companion checker solves the exact rational linear equations for all
partitions of the eight abstract change-1/change-2 transitions into at most
five displacement classes. It enumerates partitions of affine equations,
**not coefficient boxes or finite walk prefixes**. It neither generates nor
retests any recoded word or prior fixed-recoding counterexample. It uses
fraction-free `BigInt` rank computations with no numerical tolerance.

There are 3,845 such partitions; 992 admit planar solutions; 12 also permit
four distinct rational height tags. For example, with `a=2`, `L=4`,

\[
 (t_0,t_1,t_2,t_3)=(0,1,2,3),\qquad
 (c_0,c_1,c_2,c_3)=(0,1,4-2i,7-4i),
\]

the eight abstract transitions have five distinct vectors. This is **not an
admissible lift**: the tag difference `c_2-c_0=4-2i` has valuation two, whereas
`t_2-t_0=2` has valuation one. No triple-free claim is made for it. This failed
stronger step motivated the collision lemma, rather than an unsupported
assumption that distinct heights suffice.

Reproduce the bounded diagnostic from the worktree root:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
node research/unit-step/explorations/gaussian-tags-check.mjs
```

The checker additionally verifies the new source-isometry identity on 8,448
pairs (all 16 period-four sign streams, indices 0 through 32) and checks all
192 minimal-scale paired residue assignments. These bounded regressions do
not replace the arbitrary-stream or arbitrary-coefficient proofs.

This takes approximately one second on the single pinned CPU, with no
workers, subprocesses, packages, or Python. Output includes all 12 surviving
unconstrained patterns; it is finite algebraic evidence only. A local output
was saved under ignored `.checkpoint-gaussian-tags/algebra.json`. No long
computation or large prefix test was run.

## 4. What really follows for the minima

This closes the direct all-pairs valuation route to a four- or five-step
construction throughout the stated arbitrary four-state affine-tag family.
The obstruction is strictly broader than fixed `4n+r` coding and does not
assume that hypothetical successful walks possess a hidden valuation law.

It does **not** improve the universal bounds on `d_*` or `s_*`, prove equality
of those minima, or select one of the current possible ordered pairs.
The existing six-step construction supplies the matching family example;
its attribution and outstanding human-review status are unchanged. The
original Erdős 193 result remains distinct and unchanged.

## 5. Strongest next attack, stopping reason, and changed files

The strongest next attack outside this obstruction is a lift that deliberately
violates (V), or uses more than four states, index/context-dependent tags, or
a different source. Merely permuting height residues, changing representatives,
or enlarging scalar coefficients cannot defeat this theorem. Within this
family, a proposed alternative all-pairs certificate must explain exactly why
it avoids the finite-order-rotation versus torsion-free-translation argument
in Section 2.3, rather than silently dropping a pair case.

**Stopping reason:** the requested broadening has a complete analytic proof
and classification within an explicit certificate class. Broader universal
optimality would require an additional structural theorem not justified by
this work. A larger finite scan would not supply it. Independent review should
focus on the 2-adic limit/density argument and the shared-endpoint collision
lemma.

Files added/changed:

* `research/unit-step/explorations/gaussian-tags.md` — this report.
* `research/unit-step/explorations/gaussian-tags-check.mjs` — bounded exact
  diagnostic for the failed distinct-height-only strengthening.

Ignored local diagnostic output: `.checkpoint-gaussian-tags/algebra.json`.
No manuscript, central checkpoint/problem file, visualization, or prior report
was edited; no commit or external action was performed.
