# Track A: audit of the six-step / six-coordinate argument

**September 6, 2026. AI-assisted research review, not collaborator approval or
Lean certification.** Reviewed against repository commit
`aaf038f31f1433fc083360177efe8a67b67e5cb1`.

## 1. Verdict and source-by-source audit

**No mathematical gap was found in the six-step construction or its basis
encoding.** Sections 2–5 below supply the omitted intermediate identities and
an infinite argument independent of the finite checks. With the state always
represented in `{0,1,2,3}`, the written construction establishes a fixed
six-vector, triple-free walk in `Z³` and its positive-basis lift in `N⁶`.
The separate six-vector lower bound also checks out **under the precise
fixed-tag hypotheses in Section 6**. It is not a global lower bound for either
minimum.

Two presentation changes are recommended, without changing received sources:

1. Explicitly choose the representative $\sigma(n)\in\{0,1,2,3\}$ before using
   it as an integer height tag; a residue class alone cannot define $h_n$.
2. The page-two reference to “the six vectors in (3)” must apply to $g_{85}$,
   not to both alternating rules. With the same offsets, $g_{170}$ has six
   vectors but a **different menu**, listed in Section 5. This does not affect
   the theorem's $g_{85}$ proof.

### Audit map

Line references are to the unchanged
[short LaTeX source](../../../paper/unit_step_walk_N6_short.tex).

| Source location | Claim / audit finding | Expanded justification |
|---|---|---|
| Lines 23–27 | The theorem is the six-coordinate follow-up, not the original Erdős 193 statement. Attribution remains Kalviainen's draft, using Cambie's offsets and Shallit's encoding. | Sections 4–5 |
| Lines 30–34 | Signed binary source is well-defined: each binary expansion has finite support. State representatives need to be explicit. | Section 2 |
| Lines 35–41, equation (1) | Same-state valuation identity is correct. The shortened halving argument needs a **shifted** sign stream; the odd-endpoint boundary term cancels by state equality. | Section 2 |
| Lines 43–52, equation (2) | All-state extension is correct for the displayed offsets, including nonzero planar chords. Equal states add two to both valuations, not zero. | Section 3 |
| Line 52 | Heights strictly increase, so all spatial vertices are distinct; $Q_0=0$ as required for a linear, rather than affine, encoding map. | Section 3 |
| Lines 52–57 | The three-slope contradiction is valid for arbitrary unequal intervals. Squared slopes are nonzero rational numbers, so their valuations are defined. | Section 4 |
| Lines 59–63 | Binary carries give changes $1$ or $2$ modulo four for every index. | Section 5 |
| Lines 64–72, equation (3) | All eight permitted pairs occur; the step arithmetic and the two collisions are correct. There are exactly six spatial vectors. | Section 5 |
| Line 73 | The basis lift preserves triple avoidance. Global injectivity of the projection is neither true nor needed; distinct images of the walk vertices suffice. | Section 5 |
| Lines 77–78 | Preserve the source's attribution and AI disclosure. This review is not an external human review or a formalization. | Status above |
| Line 82 | All-positive signs do admit all sixteen transitions. Both alternating rules admit eight transitions and six vectors, but the menu in (3) is only $g_{85}$'s. | Sections 5–6 |
| Lines 84–94 | Pictures and the explanatory linear shadow are not proof premises. The geometry is certified by the preceding argument, not by a rendered prefix. | Sections 4–5 |
| [Family notes, lines 100–114](../../../design/SIGNED-GAUSSIAN-UNIT-STEP-OPTIMIZATION.md#optimality-inside-this-tag-scheme) | The restricted optimality argument is correct. “Symmetric” can be replaced by the explicit second collision calculation below. | Section 6 |

The comparison source is the original
[Cambie–Kalviainen Gaussian proof](../../../paper/erdos193.tex). No assertion
about its accepted theorem or its Lean package is changed here. The six-step
PDF and LaTeX, original source, and signed-family notes are SHA-256 identified
in the [finite-check result](../checks/six-step-audit.json). No manuscript,
PDF, byline, or central checkpoint was edited.

## 2. Signed source: the full halving identity

It is useful to prove the source lemma for an **arbitrary infinite** sign
stream $\epsilon=(\epsilon_0,\epsilon_1,\ldots)$ with $\epsilon_j\in\{-1,1\}$.
Let $S\epsilon$ denote its shift, and define

$$
\sigma_\epsilon(n)=\Bigl[\sum_{j\ge0}\epsilon_jb_j(n)\Bigr]_4,
\qquad u_\epsilon(n)=i^{\sigma_\epsilon(n)},\qquad
z_\epsilon(n)=\sum_{t<n}u_\epsilon(t),
$$

where $[\cdot]_4$ is the representative in $\{0,1,2,3\}$. Directly grouping
even and odd summands gives, for $e\in\{0,1\}$,

$$
\begin{aligned}
u_\epsilon(2t+e)&=i^{e\epsilon_0}u_{S\epsilon}(t),\\
z_\epsilon(2t+e)&=(1+i^{\epsilon_0})z_{S\epsilon}(t)
                         +e\,u_{S\epsilon}(t).
\end{aligned} \tag{A1}
$$

Suppose $m=2a+e<n=2b+e$ and $u_\epsilon(m)=u_\epsilon(n)$. The first identity
implies $u_{S\epsilon}(a)=u_{S\epsilon}(b)$. The extra terms in the second
identity therefore cancel, **including when $e=1$**, yielding

$$
z_\epsilon(n)-z_\epsilon(m)
 =(1+i^{\epsilon_0})\bigl(z_{S\epsilon}(b)-z_{S\epsilon}(a)\bigr). \tag{A2}
$$

Write $t=\nu_2(n-m)$. As long as the difference is even, its endpoints share
the final bit and (A2) applies; state equality descends at every stage. Hence

$$
z_\epsilon(n)-z_\epsilon(m)
 =\prod_{j=0}^{t-1}(1+i^{\epsilon_j})\,
   \bigl(z_{S^t\epsilon}(n')-z_{S^t\epsilon}(m')\bigr), \tag{A3}
$$

with $n'-m'$ odd. The empty product covers $t=0$. The remaining chord is a sum
of an odd number of units from $\{1,i,-1,-i\}$. For a unit its real and
imaginary coordinates sum to an odd integer, so for this chord $x+iy$,
$x+y$ is odd and $x^2+y^2$ is odd. In particular the chord is nonzero. Each
factor in (A3) has squared norm two. Thus

$$
u_\epsilon(m)=u_\epsilon(n),\quad m<n
\quad\Longrightarrow\quad
\nu_2\bigl(|z_\epsilon(n)-z_\epsilon(m)|^2\bigr)=\nu_2(n-m). \tag{A4}
$$

For the manuscript, $\epsilon_j=(-1)^j$; its shifted stream is the negative
stream, not the original stream. Equivalently,
$u_{S\epsilon}=\overline{u_\epsilon}$ and
$z_{S\epsilon}=\overline{z_\epsilon}$. Tracking the shift in (A1)–(A3) avoids
silently reusing the all-positive recurrence. No periodicity assumption was
used to prove (A4).

## 3. Tags, all pairs, and distinct heights

Take the manuscript's exact offsets

$$
(c_0,c_1,c_2,c_3)=(0,-1,-1+i,-i),\quad
w_n=2z_n+c_{\sigma(n)},\quad h_n=4n+\sigma(n).
$$

Their coordinate parities, in state order, are
$(0,0),(1,0),(1,1),(0,1)$. For $m<n$, put $a=\sigma(m)$,
$b=\sigma(n)$, $d=n-m>0$, $Z=z_n-z_m$, and

$$
W=2Z+c_b-c_a,\qquad H=4d+b-a.
$$

All cases are exhausted by the following table:

| Endpoint states | Squared planar norm | Height difference | Valuation |
|---|---|---|---|
| $a=b$ | $\lvert W\rvert^2=4\lvert Z\rvert^2$; (A4) makes $Z\ne0$ | $H=4d$ | Both $2+\nu_2(d)$ |
| $a,b$ of opposite parity | Exactly one coordinate of $W$ is odd | $H$ odd | Both zero |
| $a\ne b$, same parity | Both coordinates of $W$ odd; $\lvert W\rvert^2\equiv2\pmod4$ | $b-a=\pm2$, so $H\equiv2\pmod4$ | Both one |

Thus every planar chord is nonzero and

$$
\nu_2(|w_n-w_m|^2)=\nu_2(h_n-h_m)\qquad(m<n). \tag{A5}
$$

The representatives give $h_{n+1}-h_n=4+\sigma(n+1)-\sigma(n)\in\{1,\ldots,7\}$,
so the heights are strictly increasing. Also $\sigma(0)=0$, $z_0=c_0=0$,
and therefore $Q_0=(\Re w_0,\Im w_0,h_0)=0$. These observations justify both
distinctness and the origin normalization used by the encoding.

## 4. Infinite noncollinearity, with all denominators accounted for

If $Q_a,Q_b,Q_c$ were collinear for $a<b<c$, set

$$
A=h_b-h_a>0,\quad B=h_c-h_b>0,\quad
X=w_b-w_a,\quad Y=w_c-w_b.
$$

Because heights are distinct, projection to the height coordinate on this
line is injective, and collinearity gives

$$
\frac XA=\frac YB=\frac{X+Y}{A+B}.
$$

None of these slopes is zero, by Section 3. Their squared moduli are equal
positive rationals. For example, (A5) gives

$$
\nu_2\!\left(\left|\frac XA\right|^2\right)
 =\nu_2(|X|^2)-2\nu_2(A)=-\nu_2(A).
$$

The other two pairs give $-\nu_2(B)$ and $-\nu_2(A+B)$. Consequently all
three height valuations would be equal, say to $t$. But $A/2^t$ and $B/2^t$
are odd integers, whereas $(A+B)/2^t$ is even, a contradiction.

This is an infinite argument for **every** $a<b<c$. It uses neither equal
adjacent index lengths nor any finite prefix computation.

## 5. Exact menu and the six-coordinate encoding

If $n$ has $k$ trailing ones, incrementing it resets bits $0,\ldots,k-1$
and sets bit $k$. For alternating signs the state change is

$$
\sigma(n+1)-\sigma(n)\equiv
(-1)^k-\sum_{j<k}(-1)^j
\equiv\begin{cases}1&k\text{ even},\\2&k\text{ odd}\end{cases}\pmod4.
$$

For actual representatives $r,s\in\{0,1,2,3\}$ the step is

$$
v_{r,s}=(\Re(2i^r+c_s-c_r),\Im(2i^r+c_s-c_r),4+s-r).
$$

In particular the height uses the **integer difference** $s-r$, not its
residue modulo four. Substituting the eight permitted pairs gives:

| Pair | Spatial vector | Least index $n$ with $(\sigma(n),\sigma(n+1))$ this pair |
|---|---|---|
| 01 | $(1,0,5)$ | 0 |
| 12 | $(0,3,5)$ | 4 |
| 23 | $(-1,-2,5)$ | 10 |
| 30 | $(0,-1,1)$ | 2 |
| 02 | $(1,1,6)$ | 9 |
| 13 | $(1,1,6)$ | 1 |
| 20 | $(-1,-1,2)$ | 5 |
| 31 | $(-1,-1,2)$ | 21 |

The carry calculation excludes other pairs for **all indices**. The displayed
finite witnesses prove that each permitted pair actually occurs; their
minimality is only a finite diagnostic and is not needed for the theorem.
The six vectors are distinct and have positive heights.

Label the distinct vectors $v_1,\ldots,v_6$ and let $P_n$ count the first $n$
step labels. Then $P_0=0$, $P_{n+1}-P_n$ is a positive standard basis vector,
and the coordinates of $P_n$ sum to $n$. The linear map $T(e_j)=v_j$ satisfies
$T(P_n)=Q_n$, since both sides start at zero and have the same increments.
A collinear triple of $P_n$ would map into a line or a point; its images are
three distinct $Q_n$, so they would form a forbidden collinear triple.
This proves the stated six-coordinate conclusion and the fixed six-step 3D
conclusion simultaneously. It does not prove that either minimum equals six.

**Companion-rule correction.** For $g_{170}$, $\sigma$ is negated modulo four,
so the permitted changes are $3$ and $2$, not $1$ and $2$. Its menu with the
same offsets is

$$
\{(2,-1,7),(1,2,3),(-2,-1,3),(-1,0,3),(1,1,6),(-1,-1,2)\}.
$$

The first four entries come from $03,10,21,32$, respectively; the last two
still come from $02,13$ and $20,31$. The same source/tag proof applies.
A precise replacement for the last clause of source line 82 would be:
“leaving six vectors for each rule; (3) lists those for $g_{85}$.”

## 6. Separate audit: what “six is optimal in the scheme” proves

### Exact hypotheses

Fix any infinite sign stream $\epsilon_j\in\{-1,1\}$, with source and state
representatives as in Section 2. Use **all indices**, fixed planar scale two,
and the fixed height formula $4n+\sigma_\epsilon(n)$. Let the time-independent
integer offsets have the same cyclic parity pattern as Cambie's: after a
common parity translation,

$$
(c_0,c_1,c_2,c_3)\equiv((0,0),(1,0),(1,1),(0,1))\pmod2.
$$

The proof also allows interchanging the two parity coordinates. Offsets may
otherwise be arbitrarily large; they need not be literal corners of a square.
Count distinct **spatial displacement vectors** before any new coding.
Under these hypotheses at least six vectors occur. Subtracting $Q_0$ if
$c_0\ne0$ does not affect the count or the argument.

### All starting states really occur

For a carry of length $k$, define

$$
\delta_k=\epsilon_k-\sum_{j<k}\epsilon_j\pmod4,\qquad
D=\{\delta_k:k\ge0\}.
$$

Fix $k$. Set the trailing $k$ bits to one and bit $k$ to zero. Among the
infinitely many positions above $k$, some sign $\eta\in\{-1,1\}$ occurs at
least three times. Choose three such positions. Setting zero, one, two, or
three of their bits to one, and all other high bits to zero, produces starting
states

$$
\sum_{j<k}\epsilon_j+q\eta\pmod4\qquad(q=0,1,2,3).
$$

These exhaust all four residues without changing the carry length. Therefore
**each** $\delta\in D$ occurs from **every** starting state. This proves the
complete transition set without extrapolating from a prefix or assuming a
periodic stream.

Furthermore $\delta_0=\epsilon_0\in\{1,3\}$ and

$$
\delta_{k+1}-\delta_k
 =\epsilon_{k+1}-2\epsilon_k
 \equiv-\epsilon_{k+1}\in\{1,-1\}\pmod4.
$$

Thus $|D|\ge2$, and if it equals two its values form one of the four adjacent
pairs on the residue cycle: $\{0,1\},\{1,2\},\{2,3\},\{0,3\}$.
For comparison, all-positive signs have $\delta_k=1-k\pmod4$, so all four
changes and all sixteen transitions occur, as claimed on page two.

### Height classes and the only delicate collisions

Different height classes cannot collide. Their complete inventory is:

| Change $\delta$ | Heights as starting state runs through $0,1,2,3$ |
|---|---|
| 0 | $4,4,4,4$ |
| 1 | $5,5,5,1$ |
| 2 | $6,6,2,2$ |
| 3 | $7,3,3,3$ |

If $0\in D$, its four vectors $(2i^r,4)$ are distinct, while any other
change adds two disjoint height classes. This already gives at least six.
If $0\notin D$ and $|D|\ge3$, then $D=\{1,2,3\}$, whose six disjoint height
classes also suffice. Only $D=\{1,2\}$ and $D=\{2,3\}$ remain.

Write $p_{r,s}=2i^r+c_s-c_r$ for the planar part and put
$K=c_0+c_3-c_1-c_2$. Exact affine identities give

$$
\begin{aligned}
p_{0,2}-p_{1,3}&=2-2i-K,\\
p_{2,0}-p_{3,1}&=-(2-2i-K),\\
p_{0,1}-p_{2,3}&=4-K,\\
p_{1,0}-p_{3,2}&=4i+K.
\end{aligned} \tag{A6}
$$

Consequently the height-six pair collides exactly when the height-two pair
collides, and this is exactly $K=2-2i$.

- **$D=\{1,2\}$.** The height-five candidates are $p_{0,1},p_{1,2},p_{2,3}$.
  Consecutive candidates have different coordinate parities, so only the first
  and third could coincide. By (A6) that would require $K=4$. If the size-two
  pairs merge, $K=2-2i\ne4$, and the count is at least
  $3+1+1+1=6$ (heights $5,1,6,2$). If they do not merge, the count is at least
  $2+1+2+2=7$.
- **$D=\{2,3\}$.** The height-three candidates are $p_{1,0},p_{2,1},p_{3,2}$.
  Again only the first and third could coincide by parity, now requiring
  $K=-4i$. This is incompatible with $K=2-2i$, so exactly the same lower
  bounds follow (heights $3,7,6,2$). No unspoken symmetry of the integer height
  representatives is needed.

Cambie's offsets have $K=2-2i$, and either alternating stream attains six.
Thus six is **exactly optimal within this fixed signed four-state tag scheme**,
for arbitrary sign streams and all allowed integer offset representatives.
Neither bounded enumeration of representatives nor a maximum sign period is
a premise.

The result does **not** cover changing the height tags or planar scale,
index-dependent tags, deleting/grouping steps, context-dependent recoding,
other sources, or arbitrary 3D menus. In particular it proves neither
$d_*\ge6$ nor $s_*\ge6$.

## 7. Reproducible finite diagnostics

The independent [checker](check_six_step_audit.mjs) constructs states directly
from binary digits and sums Gaussian units; it imports no construction or
previous audit code. Gaussian arithmetic, norms, cross products, and the
encoding checks use exact `BigInt`. The
[tracked result](../checks/six-step-audit.json) has status `finite_checks_pass`.

Completed checks:

- All 16 period-four sign patterns, at indices $0\le n\le128$: 2,064 recurrence
  instances, 32,768 same-state pairs, 16,128 even same-state halving instances,
  and 132,096 all-state tagged pairs.
- The eight $g_{85}$ transition rows and their least witnesses, the distinct
  $g_{170}$ menu, and 128 steps of the basis projection identity.
- All 5,456 triples among vertices $0,\ldots,32$ in each of the spatial and
  basis models, as finite regression checks only.
- Four affine coefficient identities in (A6), the four height-class rows, and
  all eight cyclic parity taggings. These check algebraic bookkeeping, not an
  enumeration of all possible integer offsets.

These are **finite checks**, not the proof of infinity or a global obstruction.
The proof is Sections 2–6. No large prefix scan or exhausted fixed-coding
search was rerun.

From the repository root:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
node research/unit-step/tracks/check_six_step_audit.mjs --recompute
node research/unit-step/check.mjs
node research/unit-step/joint_minimum_examples.mjs
```

The first command recomputes and compares against the tracked result; `--write`
explicitly regenerates it after inspection. There are 18 bounded cases, one
worker, and no subprocesses. Every completed case is atomically checkpointed
under ignored `.checkpoint-six-step-audit/`; UTC JSONL logs record source/code/
config identity, start/resume, progress, throughput, ETA, and outcome. Running
without `--recompute` resumes checksum- and identity-validated progress.
`SIGINT`/`SIGTERM` stop between cases after saving. See `--help` for separate
checkpoint/log paths and `--stop-after` for a deterministic resume test. Logs
and checkpoints are not proof artifacts. The whole finite check takes seconds,
not a long-running search.

## 8. Handoff and remaining obligations

**Task A outcome:** the infinite construction and the narrowly scoped
optimality argument have complete expanded derivations; no unresolved core
proof obligation was identified in this audit. The two presentation issues
in Section 1 should be resolved in an author-approved, separately versioned
revision, not by silently replacing the archived manuscript.

**Still outstanding:** human collaborator/external review, any desired Lean
formalization of the signed construction, and the exact minima. This review
supports the proposed $4\le d_*\le s_*\le6$ region but selects none of its six
candidate ordered pairs. It does not imply equality of the minima. The
original Erdős 193 theorem remains distinct and unchanged.

**Proposed later synthesis update (not applied to shared checkpoint files):**
link this audit in the six-step and scheme-optimality ledger rows, record
“AI-assisted Track A audit completed; no core gap found; collaborator review
and Lean certification still pending,” and retain the 4D/5D open status.
No external acceptance should be inferred from this task's completion.

**Next useful step:** ask the manuscript's authors/reviewers to inspect (A1)–(A5)
and the explicit hypotheses/(A6) independently, then approve the two wording
corrections. A further prefix scan is not the missing review step. No
correspondence, merge, publication, or deployment was performed.
