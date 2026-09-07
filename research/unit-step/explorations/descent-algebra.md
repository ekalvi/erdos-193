# Tagged descent for the g85 subsequence problem

**descent-algebra track, September 6, 2026. Research partial result, not a
complete no-five-subsequence theorem.** The supplied `return-blocks.md` is the
latest input checkpoint, not an output of this track. Its computer-assisted
statements are used with their existing AI-review / non-human-approval status.

## 1. Verdict and scope

**The requested unrestricted descent is not proved.** Nor is the existence of
an infinite five-displacement subsequence proved or disproved here.

The useful results are:

1. Exact base-4 affine laws, at one and every scale, including all endpoint
   tags. There are 16 distinct one-scale corrections, not one common linear
   renormalization.
2. An exact formula for the parent displacement menu. Floor division followed
   by removing repeated parents does not introduce sums of edges; nevertheless
   it can split labels and increase five to six. A seven-vertex witness below
   defeats **all four fixed rounding offsets**, with no coalescing parents.
3. A proved **phase-synchronized descent**, including a binary refinement that
   stays in the same g85 walk. Consequently, using the supplied gap-16
   obstruction, any hypothetical five-menu subsequence with height gcd of
   2-adic valuation `t >= 2` must have
   `max(menu heights) / 2^t >= 17`. This is an all-scale restricted obstruction,
   not a normalization of every possible menu to gap 16.
4. A second tempting shortcut fails: merely requiring a menu to cross each of
   the eight arbitrarily large substitution-boundary types does not force six.
   Two explicit vectors suffice for that necessary condition. This is **not**
   a two-vector path, since compatibility between crossings is missing.

These conclusions concern the specified walk only. They give **no new bound
on `s_*` or `d_*`**, and say nothing new about the separately settled original
Erdős 193 theorem. Even the full target theorem would not prove `s_* = 6`.

The construction's attribution remains Kalviainen's six-step draft, using
Cambie's offsets and Shallit's encoding, based on Cambie–Kalviainen. None of
the manuscript or construction-review statuses is changed by this report.

## 2. Definitions and the exact endpoint law

Use representatives `q_n in {0,1,2,3}` throughout, and distinguish a state
reduced modulo four from its integer representative in a height:

\[
q_n=\left[\sum_j(-1)^j b_j(n)\right]_4,\quad
z_n=\sum_{u<n}i^{q_u},\quad
c=(0,-1,-1+i,-i),
\]
\[
W_n=2z_n+c_{q_n},\qquad H_n=4n+q_n,\qquad
Q_n=(\Re W_n,\Im W_n,H_n).
\]

Let `t=(0,1,-1,0)`, `d=(0,1,1+i,1)`, and
`D=diag(2,2,4)`. Splitting the binary digits after the last two gives

\[
q_{4m+a}=[q_m+t_a]_4.
\]

The sum of the four Gaussian units in the block at `4m` is
`i^{q_m}(1+i-i+1)=2i^{q_m}`; their partial sums are `i^{q_m}d_a`.
Summing complete blocks and then a partial block therefore proves

\[
z_{4m+a}=2z_m+i^{q_m}d_a.
\]

For `r=q_m` and `s=[r+t_a]_4`, substitution into the definition of `Q` gives

\[
\boxed{Q_{4m+a}=DQ_m+R(r,a)},\qquad
R(r,a)=\bigl(2i^r d_a+c_s-2c_r,\ 4a+s-4r\bigr). \tag{1}
\]

Here a complex entry denotes the first two real coordinates. The full table,
with each entry an ordinary integer triple, is

| `r` | `a=0` | `a=1` | `a=2` | `a=3` |
|---|---|---|---|---|
| 0 | (0,0,0) | (1,0,5) | (2,1,11) | (2,0,12) |
| 1 | (1,0,-3) | (1,3,2) | (0,2,4) | (1,2,9) |
| 2 | (1,-1,-6) | (0,-3,-1) | (-1,-4,1) | (-1,-1,6) |
| 3 | (0,1,-9) | (0,0,-8) | (1,1,-2) | (0,-1,3) |

In particular, `R(r,0)=(-c_r,-3r)`, so even aligned endpoints do not satisfy
`Q_(4m)=DQ_m` without their state correction.

### All base-4 scales

For `0 <= a < 4^k`, the same digit split and block sum give

\[
q_{4^k m+a}=[q_m+q_a]_4,\qquad
z_{4^k m+a}=2^k z_m+i^{q_m}z_a.
\]

Thus, with `s=[r+q_a]_4`,

\[
\boxed{Q_{4^k m+a}=D^kQ_m+R_k(r,a)},\qquad
R_k(r,a)=\bigl(2i^r z_a+c_s-2^kc_r,\ 4a+s-4^kr\bigr). \tag{2}
\]

This is an algebraic identity for every index and scale, not an inference
from a checked prefix.

## 3. What happens to a completely arbitrary selected path

Let `n_j` be strictly increasing, `m_j=floor(n_j/4)`, `a_j=n_j mod 4`, and
`r_j=q_(m_j)`. For `v_j=Q_(n_(j+1))-Q_(n_j)`, equation (1) gives

\[
Q_{m_{j+1}}-Q_{m_j}
=D^{-1}\bigl(v_j+R(r_j,a_j)-R(r_{j+1},a_{j+1})\bigr). \tag{3}
\]

There is a useful reduction from pairs of arbitrary phases to just 16 possible
starting phases per label. Set `p=H_n mod 16`, represented in `0,...,15`.
Then

\[
a=\lfloor p/4\rfloor,\quad s=p\bmod4,\quad r=[s-t_a]_4.
\]

Define `rho(p)=R(r,a)` by this formula. An edge `v=(x,y,h)` advances the height
phase by exactly `h mod 16`, so its parent label is

\[
\boxed{T_v(p)=D^{-1}\bigl(v+\rho(p)-\rho([p+h]_{16})\bigr).} \tag{4}
\]

For an actual edge this is integral. Some formal phase/label combinations
need not be actual edges and must not be assumed realizable.

If `A_v` is the set of starting phases where label `v` actually occurs in the
selected path, its coalesced parent menu is **exactly**

\[
\left(\bigcup_{v\in S}\{T_v(p):p\in A_v\}\right)\setminus\{0\}. \tag{5}
\]

Consequently the always-valid bound is `16|S|`, not `|S|`. A sufficient
menu-preservation hypothesis is that the endpoint correction difference is
constant on all occurrences of each label. More generally, preservation is
exactly the assertion that the set in (5) has size at most `|S|`; different
child labels are allowed to have the same image.

**Zero parent gaps and coalescence.** The sequence `m_j` is nondecreasing.
Its equal values occur in consecutive finite runs. Removing repetitions leaves
an infinite strictly increasing sequence, because `n_j` tends to infinity.
The transition between two consecutive distinct parent values is the image
of the original edge between the last member of one run and the first member
of the next. Edges within runs have parent label zero. Thus coalescence deletes
zeros and introduces **no sums or additional labels**. If child gaps are at
most `B`, the resulting parent gaps are at most `ceil(B/4)`.

For example, selected indices `0,1,2,4` have parents `0,0,0,1`; the sole
nonzero parent edge comes directly from the original edge `2 -> 4`.

This differs from thinning to one phase **before** division: a return to that
phase can concatenate several nonzero child edges. Its label is then a sum of
menu vectors, with no five-label bound established by pigeonhole alone.

## 4. Exact finite failures of unqualified menu preservation

Already a single label has two positive-gap parent images:

| Child edge | Child vector | Parent edge | Parent vector |
|---|---|---|---|
| `0 -> 6` | (2,2,24) | `0 -> 1` | (1,0,5) |
| `2 -> 8` | (2,2,24) | `0 -> 2` | (2,1,11) |

More decisively, take the selected indices

\[
0,17,34,51,78,100,127.
\]

Their consecutive labels, in order, are

\[
(7,3,70),\ (2,4,68),\ (1,-7,66),\ (4,6,108),\
(-3,2,89),\ (4,6,108).
\]

There are five labels. For each possible fixed rounding offset `b=0,1,2,3`,
the parent indices `floor((n_j+b)/4)` and the **six pairwise distinct** parent
labels are as follows:

| `b` | Parent indices | Parent labels, in order |
|---|---|---|
| 0 | 0,4,8,12,19,25,31 | (3,0,17); (1,3,18); (0,-3,13); (3,2,29); (-2,2,24); (2,2,24) |
| 1 | 0,4,8,13,19,25,32 | (3,0,17); (1,3,18); (1,-3,18); (2,2,24); (-2,2,24); (3,3,30) |
| 2 | 0,4,9,13,20,25,32 | (3,0,17); (1,2,19); (1,-2,17); (2,5,29); (-2,-1,19); (3,3,30) |
| 3 | 0,5,9,13,20,25,32 | (3,3,22); (1,-1,14); (1,-2,17); (2,5,29); (-2,-1,19); (3,3,30) |

All original gaps are between 17 and 27. No parent points coalesce. This
refutes the finite-path lemma even if it is allowed to choose the best global
rounding offset. It does **not** refute an infinite-only theorem, or one that
chooses a different subsequence by some stronger rule.

The checker also preserves the first-found witness
`0,17,34,51,70,90,109`, whose ordinary floor parents have six labels; the
repeated child label is `(3,2,77)`, with parent images `(3,3,22)` and
`(1,2,19)`. Both binary rounding offsets inflate this first witness to six.
Its base-4 offset 2 does preserve five, which is why the stronger second
witness above was checked rather than assuming one witness covered all offsets.

## 5. The valid synchronized descent and a height-gcd corollary

### Base-4 version

**Lemma.** Suppose all consecutive menu heights are divisible by `4^(k+1)`.
Then the selected points have a common state and a common index residue modulo
`4^k`. Their parent indices `floor(n_j/4^k)` are strictly increasing, and their
menu is exactly `D^(-k)S`. In particular its cardinality is unchanged and each
index gap is divided by `4^k`.

**Proof.** All selected heights are congruent modulo `4^(k+1)`. Since
`H_n=4n+q_n` with `0<=q_n<4`, this fixes `a=n mod 4^k` and `q_n`.
The digit identity fixes `r=q_(floor(n/4^k))` as well. Hence the correction
`R_k(r,a)` in (2) is the same at every selected endpoint. It cancels in every
chord. Distinct indices in one residue class have distinct parents, and
`D^k` is invertible. This proves all claims. QED.

This condition is not inferred for an arbitrary menu. Merely keeping infinitely
many points in one of these classes does not preserve the original menu.

### Binary refinement in the same walk

The alternating binary rule closes under one-bit deletion by conjugation:

\[
q_{2m+a}=[a-q_m]_4,\qquad
z_{2m+a}=(1+i)\overline{z_m}+a i^{-q_m}\quad(a=0,1).
\]

Define the invertible real-linear integer map

\[
L(x,y,h)=(x+y,x-y,2h),\qquad L^2=D.
\]

Writing `s=[a-r]_4`, the exact identity is

\[
Q_{2m+a}=LQ_m+E(r,a),\qquad
E(r,a)=\bigl(2a i^{-r}+c_s-(1+i)\overline{c_r},\ 4a+s-2r\bigr). \tag{6}
\]

If all menu heights are divisible by eight, `H_n mod 8` fixes both `a` and
`q_n`, hence `r`; the correction in (6) is constant. The parent menu is exactly
`L^(-1)S`, and gaps are divided by two. The resulting points are again points
of **this same** `Q`, not of an unspecified sign-stream companion.

Iterating proves: divisibility of every menu height by `2^(k+2)` permits `k`
menu-preserving binary descents. All intermediate phases are synchronized:
the initial condition fixes `q_n` and `n mod 2^k`, and each digit deletion
fixes the next common state and the remaining residue.

**Corollary using the supplied gap-16 obstruction.** Let `G` be the gcd of the
positive heights in a hypothetical infinite menu of at most five vectors,
and let `t=nu_2(G)`. If `t>=2`, then

\[
\boxed{\max_{v\in S}h(v)/2^t\ \ge\ 17.} \tag{7}
\]

Indeed, perform `k=t-2` binary descents (zero descents when `t=2`). The original
selected state is constant, so its gaps are exactly `h(v)/4`. The parent gaps
are therefore exactly `h(v)/2^t`. If all were at most 16, the supplied infinite
gap-16 theorem would be contradicted. This proof does not rerun its finite
certificate or confer independent human approval on it.

For `t=0` or `t=1`, only the original restriction `max h >=65` is obtained
here (`>=66` when all heights are even). The synchronized normalization stops
at height gcd valuation two. Menus whose normalized largest height is at least
17 are not eliminated by (7), regardless of how large that number is.

## 6. Why a boundary-type covering shortcut also fails

This section records an exact failed candidate, not another gap-cutoff search.
Let `T=4^k m`, `r=q_(m-1)`, `s=q_m`, and consider a chord from `T-x` to `T+y`,
where `1<=x<=4^k` and `0<=y<4^k`. Every adjacent state type is `r -> r+1` or
`r -> r+2` modulo four, giving eight seam types.

Digit complementation in `2k` binary digits gives
`q_(4^k-1-j)=-q_j mod 4`. Consequently the start and end states are

\[
p=[r-q_{x-1}]_4,\qquad e=[s+q_y]_4,
\]

and the seam-crossing vector is exactly

\[
\boxed{V_{r,s}(x,y)=
\bigl(2(i^r\overline{z_x}+i^s z_y)+c_e-c_p,\
4(x+y)+e-p\bigr).} \tag{8}
\]

For a fixed finite gap bound and sufficiently large `k`, an infinite selected
path must cross every sufficiently late such seam by some edge of this form.
The substitution has arbitrarily late occurrences of every adjacent state
pair, so all eight types are necessary. The candidate argument was that
covering these eight types alone might require six vectors. It does not:

| Vector | Seam `r -> s` | `(x,y)` |
|---|---|---|
| (1,9,198) | 0 -> 1 | (3,46) |
| (1,9,198) | 1 -> 2 | (43,6) |
| (1,9,198) | 1 -> 3 | (49,0) |
| (1,9,198) | 2 -> 0 | (17,32) |
| (-1,-9,194) | 0 -> 2 | (17,32) |
| (-1,-9,194) | 2 -> 3 | (3,46) |
| (-1,-9,194) | 3 -> 0 | (43,6) |
| (-1,-9,194) | 3 -> 1 | (49,0) |

Equation (8) proves these witnesses at every scale with `4^k>=49` and at every
actual seam of the indicated type. Each gap is 49. The checker independently
realizes every row in the actual walk at a seam of scale `4^4=256`.

Thus even two vectors pass this necessary seam-cover test. There is no claim
that these crossings can be connected using those vectors, or using five
vectors. In fact the missing compatibility is indispensable. The checker
found the cover by examining seam chords with `x+y<=128`; the displayed
witnesses themselves, not completeness beyond that range, refute the proposed
six-vector covering argument.

## 7. Exact checks and reproduction

New bounded checker:
`research/unit-step/explorations/descent-algebra-check.mjs`.
It uses integer arithmetic, the alternating binary definition for `q`, and
Gaussian-unit summation for `Q`, independently cross-checked against the
supplied eight-transition / six-vector table. It verifies (1) and (6) through
index 6144, and (2) at scales `k=1,...,4` through that index; the proofs above
establish their unrestricted versions. Formula (4), including zero parent
gaps, is also checked for starts below 512 and gaps 1 through 32. The modest
prefix endpoint allows every seam witness to be checked as an actual chord,
rather than just a formal seam.

The two small witness searches examine child gaps 17 through 32, solely to
test the named finite descent claims, not to extend the known no-five gap
cutoff. They stop at the first witnesses after 55 and 257 recursive calls.
The seam experiment is another bounded algebra diagnostic, not an exhaustive
selector search. No prior exhaustive selectors or fixed recodings were rerun.

Run sequentially from this worktree:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
mkdir -p .checkpoint-descent-algebra
taskset -c 0 node --single-threaded --v8-pool-size=1 \
  research/unit-step/explorations/descent-algebra-check.mjs \
  > .checkpoint-descent-algebra/check.json
```

The checker prints exact corrections, menus, witnesses, parameters, source
SHA-256, start/end timestamps, and elapsed time. The final validation completed
at `2026-09-06T23:03:25Z` in 483 ms; its source SHA-256 was
`b152e1c46c36ef6550407e9569d823553907f9fb3d8a6b2e2b959f10b174ac94`.
No computation exceeds
60 seconds, no substantive Python is used, and no resumable long run is needed.
Only CPU 0 is used; output is far below the 300 MB limit. Logs/output remain
under the ignored checkpoint directory, separate from this report.

An intermediate validation correctly failed when actual-seam checking was
strengthened from optional to mandatory: the initial 4096-point array did not
include the first occurrence of every scale-256 seam. Extending the bounded
array to 6144 fixed this coverage issue. It did not change any witness or
assert an additional gap obstruction.

## 8. Precise missing step and stopping point

An infinite finite menu automatically has bounded index gaps, since every
edge height satisfies `h >= 4d-3`. Thus a hypothetical counterexample has a
least possible maximum gap `B`, and the supplied obstruction makes `B>16`.
Ordinary floor division has maximum gap at most `ceil(B/4)<B`. Minimality would
therefore force the actual image set (5) to have at least six elements.
The local obstruction to proving otherwise is genuine, as Section 4 shows.

**Strongest next action:** analyze infinite realizability of the phase-labelled
edge set `A_v` in (5), including the constraints between successive large-block
crossings. One needs a new infinite argument that either prevents the observed
label-splitting patterns from persisting in a five-menu path, or supplies a
replacement path with a proved five-label return menu. A mere pigeonhole
selection of one phase, a height-gcd normalization without sufficient common
valuation, or a cover of seam types is insufficient. No such infinite
compatibility theorem has been proved here.

This is the honest stopping point: exact algebra and restricted descent, plus
short falsifications of two natural unrestricted shortcuts. There is no
justification to raise a numerical gap cutoff or to claim that all
construction-specific subsequences have been excluded.

### Files changed

Only two new output files:

- `research/unit-step/explorations/descent-algebra.md` — this report.
- `research/unit-step/explorations/descent-algebra-check.mjs` — bounded exact
  law checks and finite witnesses.

Ignored check output is under `.checkpoint-descent-algebra/`. Supplied
exploration inputs, manuscripts, central checkpoint/problem files, and `viz`
were not edited. No rival new outputs were read; no commits, network activity,
package installations, or publication actions were performed.
