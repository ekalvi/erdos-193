# Track B: bounded boundary states for Shallit's five-letter word

**September 6, 2026. Research result, not a complete five-letter proof.**
Based on `origin/main` at `aaf038f`, on branch `research/shallit-five-proof`.
Shallit supplied the candidate; these are AI-assisted track notes and exact
checks, not collaborator approval or a new manuscript byline.

## Outcome and precise scope

For the fixed point of

\[
h(0)=01213101314310,\qquad h(r)=h(0)+r\pmod5,
\]

this track supplies:

1. An **all-ratios ancestor bound**, independent of the size of the indices:
   \(\|D_t\|_\infty/(p+q)<6735/3811\), with the defect defined below.
2. An exact, terminating **finite-state decision reduction for each fixed
   coprime ratio** \(p:q\), including arbitrary partial boundaries and
   coalescing parent indices.
3. Independently checked closed-state certificates proving infinite avoidance
   at reduced adjacent-length ratios **\(1:1,1:2,2:1\)**.
4. An explicit obstruction to taking the union of these *unnormalized* state
   spaces: it is already unbounded after one ancestor step, even for ratios
   tending to \(1:1\).

**Still open:** avoidance for every positive rational ratio. There is no
counterexample here and no infinite 5D construction theorem. In particular,
no bound on \(d_*\) or \(s_*\) improves. This does not affect the already
settled original Erdős 193 theorem. The infinite implications below are
written mathematical arguments plus finite integer certificates, not Lean
formalization; human review remains appropriate.

The three certificates are not longer prefix scans. Their closure condition
covers every scale at the specified ratio. Conversely, checking finitely many
ratios does **not** cover their infinite union.

## 1. Exact states and descent (all positive coprime p, q)

Write \(w=h^\omega(0)\), and let \(F(n)\in\mathbb Z^5\) count the first \(n\)
letters. Fix positive coprime integers \(p,q\), and set \(s=p+q\). Keep these
coefficients fixed throughout descent; **do not replace them by the parent
interval lengths**. For indices \(a\le b\le c\), define

\[
D=qF(a)-sF(b)+pF(c).
\]

For \(a<b<c\), the condition \(D=0\) is exactly a weak abelian square with
left:right length ratio \(p:q\). Indeed \(\sum F(n)=n\) gives
\(q(b-a)=p(c-b)\), and the vector equation gives equal normalized counts.
Coprimality means the lengths are \(gp,gq\) for some positive integer \(g\).

A state records

\[
(w_a,w_b,w_c;\ \epsilon_{ab},\epsilon_{bc};\ D),
\]

where an \(\epsilon\) is 1 for a strict inequality and 0 for equality.
The equality flags are necessary: floor division can merge two or three
indices. Ignoring such mergers would make an avoidance certificate unsound.

Let \(B(r,t)=\psi(h(r)[0:t])\), for \(0\le t<14\). The incidence matrix and
its adjugate are

\[
M=\begin{pmatrix}
3&1&3&1&6\\6&3&1&3&1\\1&6&3&1&3\\3&1&6&3&1\\1&3&1&6&3
\end{pmatrix},\quad \det M=5894,
\]

\[
A=\operatorname{adj}M=
\begin{pmatrix}
227&1025&-305&-53&-473\\
-473&227&1025&-305&-53\\
-53&-473&227&1025&-305\\
-305&-53&-473&227&1025\\
1025&-305&-53&-473&227
\end{pmatrix}.
\]

Both \(MA=5894I\) and the entries can be checked with integer arithmetic.
Writing \(a=14a'+t_a\), and similarly for \(b,c\), gives

\[
F(14n+t)=MF(n)+B(w_n,t),
\]

\[
\boxed{D'=M^{-1}\bigl(D-qB_a+sB_b-pB_c\bigr).} \tag{1}
\]

For each choice of the three offsets, the parent letters are forced:
\(r_i=w_i-h(0)_{t_i}\pmod5\). Thus there are only \(14^3\) boundary choices
per state before considering equality flags.

The exact order rule for either neighboring pair is:

- A strict parent pair always gives a strict child pair, regardless of offsets.
- An equal parent pair requires equal parent letters. Its offsets must be
  nondecreasing, and the child is strict exactly when the offsets are strict.

Discard nonintegral \(D'\). If all three parent indices are equal, also discard
\(D'\ne0\), which is impossible for actual prefix counts. A state with all
three indices equal, all three letters equal, and \(D'=0\) is **accepting**.
No assumption about occurrence of other states is made; their inclusion is
an overapproximation until a whole accepting path is realized.

## 2. Complete one-step lattice sieve for every ratio

Define

\[
\Phi(v)=\left(\sum_jv_j\bmod14,\quad\sum_{j=0}^4 279^jv_j\bmod421\right).
\]

Then

\[
\boxed{v\in M\mathbb Z^5\ \Longleftrightarrow\ \Phi(v)=(0,0).} \tag{2}
\]

**Proof.** The columns of \(M\) sum to 14. Also \(279^5=1\pmod{421}\) and
\(3+6(279)+(279)^2+3(279)^3+(279)^4=0\pmod{421}\), so \(\Phi M=0\).
The map \(\Phi\) is onto: multiples of \(e_0\) set its first component, and
multiples of \(e_1-e_0\) adjust the second without changing the first, since
\(\gcd(279-1,421)=1\). Thus its kernel has index \(14\cdot421=5894\), equal
to the index of \(M\mathbb Z^5\), proving equality. □

Apply (2) to the right side of (1). This handles **all** \(p,q\), including
coefficients divisible by 2, 7, or 421; no coefficient is inverted modulo
these numbers. The producer uses this sieve as an acceleration. The validator
does not: it reconstructs \(A\) by integer cofactors and tests divisibility of
all five coordinates directly for every offset triple.

The earlier **170 nonzero integral corrections** remain algebraic cases, not
170 occurring triples. They cannot simply be discarded. The new method keeps
nonzero defects, iterates their possible parents, and checks closure instead
of assuming that a parent defect vanishes.

## 3. Uniform normalized bound

**Lemma.** Start with any state with \(D_0=0\). Every state reachable by a
finite number of the ancestor transitions (1) satisfies

\[
\boxed{\frac{\|D_t\|_\infty}{s}<\frac{6735}{3811},\qquad
       \left|\sum_j(D_t)_j\right|<s.} \tag{3}
\]

These constants hold for **every** positive \(p,q\), not just the three
ratios whose closures were computed.

**Proof of the vector bound.** Every row of \(A\) has absolute sum 2083, so
\(\|M^{-1}\|_\infty=2083/5894=:\kappa<1\). In each coordinate, the minimum
and maximum of \(AB(r,t)\) over the 70 prefixes are respectively \(-1068\)
and \(5667\). In coordinate zero these occur at \((r,t)=(2,8),(0,13)\);
cyclic symmetry gives the other coordinates. Direct enumeration of just these
70 vectors independently verifies the extrema.

Put \(C=M^{-1}B\). After dividing (1) by \(s\), its forcing term is

\[
C_b-\frac qs C_a-\frac ps C_c.
\]

Because \(p/s,q/s>0\) and sum to one, each coordinate lies in an interval
of absolute radius at most \((5667+1068)/5894=6735/5894\). Consequently

\[
\frac{\|D_t\|_\infty}{s}
 \le \frac{6735}{5894}\sum_{j=0}^{t-1}\kappa^j
 =\frac{6735}{3811}(1-\kappa^t)<\frac{6735}{3811}.
\]

The initial case \(t=0\) also satisfies the strict bound.

**Proof of the sum bound.** Let \(d=\sum D\). Column sums give
\(d'=(d-qt_a+st_b-pt_c)/14\). The last three terms have absolute value at
most \(13s\). Thus \(|d|<s\) implies \(|d'|<(s+13s)/14=s\); start at zero.
This also proves the bound for algebraically reachable states that are not
known to occur. □

## 4. A finite decision certificate for each fixed ratio

For fixed \(p,q\), the integer defects in (3) form a finite set. A crude
upper bound on the number of states is

\[
500\left(2\left\lfloor\frac{6735(p+q)}{3811}\right\rfloor+1\right)^5,
\]

before exploiting the sum bound, equality constraints, or actual reachability.
The bound is not a practical runtime estimate.

Start from the 125 states with arbitrary three letters, both inequalities
strict, and \(D=0\). Repeatedly add every allowed parent described in §1.
This procedure terminates by (3), unless a user resource limit stops it first.

**Theorem (fixed-ratio decision).** The fixed point has a weak abelian square
of reduced length ratio \(p:q\) if and only if this ancestor closure reaches
an accepting state.

**Only-if.** Take an actual witness. Its letters, defect, and order flags
satisfy (1) at every stage. Repeated floor division of its nonnegative indices
by 14 eventually makes all three zero. Every intermediate state is retained
by the transition rules, and the final state is accepting.

**If.** Take a finite path from a root to an accepting state. All three letters
at the latter are some \(r\). Every letter occurs in \(h(0)\), so choose an
index \(n\) with \(w_n=r\), and realize that terminal state by \((n,n,n)\).
Reverse the path, replacing every parent index \(u\) by \(14u+t\) using the
recorded offsets. The letter identities, (1), and the exact order rules show
inductively that each child state is realized with its claimed defect. The
root then gives actual \(a<b<c\) and \(D=0\). □

In particular, **any finite set** containing all roots, containing no accepting
state, and closed under every allowed parent is an avoidance certificate.
The verifier does not have to trust the producer's traversal, reachability
claims, stopping rule, or sieve. It checks this closure directly.

## 5. Validated fixed-ratio infinite results

| Reduced left:right ratio | States | Allowed transitions | Exact certificate |
|---|---:|---:|---|
| 1:1 | 245 | 860 | [ratio-1-1.json](checks/ratio-1-1.json) |
| 1:2 | 145 | 210 | [ratio-1-2.json](checks/ratio-1-2.json) |
| 2:1 | 140 | 205 | [ratio-2-1.json](checks/ratio-2-1.json) |

All three contain every root, are ancestor-closed, and have no accepting state.
By §4 they exclude these ratios **at all positions and all lengths**. The
first gives ordinary abelian-square avoidance. The other two address genuine
unequal-length cases; neither their union nor ordinary square avoidance
settles weak abelian-square avoidance for arbitrary lengths.

[check.mjs](check.mjs) independently constructs the matrix and its cofactors,
checks the bounds' finite arithmetic, and enumerates every \(14^3\) offset
choice for every saved state. It rejects missing, duplicate, altered, missing-root,
accepting-state, and wrong-transition-count mutations. The small 196-position
prefix-identity regression check is labelled finite and is not the reason the
avoidance statements are infinite.

## 6. Why this is not one finite certificate for all ratios

The bound in (3) is on \(D/(p+q)\), not on the integer vector \(D\) itself.
Nor does it bound the reduced denominator \(p+q\).

This distinction is essential even if the interval ratio is bounded close to
one. Put \(N=5894\), \(p=Nk+1\), \(q=p+N\), for \(k\ge0\). These are
coprime because \(\gcd(p,q)=\gcd(Nk+1,N)=1\). Choose parent boundary letters
\((0,0,0)\) with offsets \((1,0,13)\), and strict parent inequalities.
The child letters are \((1,0,0)\), a root state. Since

\[
B(0,1)=e_0,\quad B(0,0)=0,\quad B(0,13)=Me_0-e_0,
\]

its allowed parent defect is

\[
D'=-p e_0-Ae_0=(-p-227,\ 473,\ 53,\ 305,\ -1025).
\]

This is integral and unbounded as \(k\to\infty\), while \(q/p\to1\).
Thus even the first parent layer over all primitive ratios is infinite in
this raw state representation. **These are allowed algebraic states, not
counterexamples or proof of their occurrence.** This is only an obstruction
to using a single finite union of these integer states, not to all possible
proof methods or to the candidate itself.

A next all-ratios approach needs a new ingredient: for example, an exact
parameterized invariant in \((p/s,D/s)\) with congruence information, or a
proved bound on the primitive coefficient sum for a minimal counterexample.
A bound on the real ratio alone is insufficient. Running this fixed-ratio
decider on more and more ratios is not an infinite proof and is not the
recommended replacement for that missing argument.

## 7. Reproduction and operational checks

From the repository root (Node 22; no package install):

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
track=research/unit-step/tracks/shallit-five
id=$(sha256sum "$track/boundary.mjs" | cut -c1-12)
for pair in '1 1' '1 2' '2 1'; do
  read -r p q <<< "$pair"
  node "$track/boundary.mjs" --p "$p" --q "$q" \
    --state-dir ".checkpoint-shallit-boundary-$id-$p-$q" || exit
 done
node "$track/check.mjs"
node "$track/test.mjs"
```

Generation of these three closures takes less than a second; independent
validation plus mutation tests takes about five seconds on one core here.
The checker rebuilds complete parent sets rather than trusting certificate
counts. Both producer and validator must pass before claiming a fixed-ratio
result. This code does not rerun the 737-million-chord prefix test.

`boundary.mjs --help` documents ratio parameters, a default 60-second / 100,000
state resource boundary, and resume behavior. A bounded stop exits 2, saves
progress, and writes **no new final certificate**. SIGINT/SIGTERM checkpoint
between completed states and exit 130. Compatible restarts resume or reuse
completed work. An interrupted first state is correctly logged as a resume
even when zero states were completed. Code/parameter mismatches and corrupted
checkpoints are rejected; after a code change use a new state directory.
The exact implementation caps \(p+q\) at one million so its intermediate
integer arithmetic is safely below \(2^{53}\); the mathematical lemmas have
no such cap. Witness reconstruction, if reached, uses BigInt indices/counts.

Final certificates are separate from ignored `.checkpoint-*` state and durable
timestamped logs. `test.mjs` checks bounded interruption/resume, byte-identical
completed reuse, SIGTERM/resume, incompatible and corrupt checkpoints, and
invalid arguments. Check and test tasks themselves checkpoint completed work.
No received manuscripts, central checkpoint files, other tracks, or production
deployments are modified.

## Proposed synthesis update (not an edit to shared checkpoint files)

Replace “finite evidence only for this candidate” by the more precise ledger:
**finite all-ratios prefix evidence; infinite fixed-ratio certificates at
1:1, 1:2, 2:1; all-ratios ancestor bound and per-ratio finite decision reduction;
full weak-abelian-square avoidance unresolved**. Preserve the previous prefix
result and the 170-correction diagnostic. A small `viz/` source notice carries
this same scope; no deployment is performed.

### Starting sources and attribution

- [Task B](../../PARALLEL-TASKS.md#b-settle-shallits-five-letter-candidate).
- [Original investigation](../../../../design/UNIT-STEP-4D-5D-INVESTIGATION.md#3-shallits-five-letter-candidate).
- [Original algebra diagnostic](../../../../design/shallit_substitution_algebra.py)
  and [independent correction validator](../../../../design/check_unit_step_dimension_results.py).
- [Shallit manuscript archive](../../../../paper/followups/README.md), preserved unchanged.
