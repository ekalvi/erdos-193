# Attempted contradiction in five, then four, positive-basis dimensions

**September 6, 2026. Research work, not a completed lower-bound proof.**
The attempt did **not** prove impossibility in either dimension. The current
bounds and review status in [PROBLEM.md](../PROBLEM.md) are unchanged. These are
elementary reductions, exact finite diagnostics, and explicit gaps, not claims
of new literature results or independent manuscript approval.

This is the positive-standard-basis follow-up, not the original Erdős 193
finite-step theorem of Cambie and Kalviainen. The five-letter substitution
below is Shallit's candidate. No new joint authorship is assigned here.

## 1. Logical target and what an exhaustive proof would require

Write \(\mathcal B(d)\) for an infinite triple-free positive-basis walk in
\(\mathbb Z^d\). Appending a zero coordinate gives

\[
\mathcal B(4)\Longrightarrow\mathcal B(5),\qquad
\neg\mathcal B(5)\Longrightarrow\neg\mathcal B(4).
\]

Thus a successful 5D contradiction already disposes of 4D. If the former
stalls, a specifically four-letter obstruction is still worth seeking.
A 5D impossibility theorem would also rule out five-step 3D constructions by
basis encoding; see the [joint formulation](../JOINT-MINIMUM.md). Only together
with independent acceptance of the six-step upper bound would it give
\((d_*,s_*)=(6,6)\).

Let \(T_d\) be the tree of finite words over \(d\) letters that avoid adjacent
nonempty blocks of equal normalized Parikh vector, **including unequal
lengths**. Avoidance is inherited by prefixes, and every node has at most
\(d\) children. König's lemma gives the exact equivalence

\[
\neg\mathcal B(d)
\quad\Longleftrightarrow\quad
\exists L\ \text{such that }T_d\text{ has no word of length }L.
\tag{1}
\]

An exhaustive tree closure is therefore a legitimate unconditional proof.
A time limit, failure of one branch, or long surviving word is not a closure.
The [previous exact 5D prefix](../../../results/shallit-five-prefix.json) already
forces any such universal \(L\) in dimension five to exceed 38,416 steps.

## 2. A genuine counting obstruction, but not a dimension contradiction

Assume a triple-free walk \(P_0,\ldots,P_N\) in dimension \(d\ge2\). Fix **any**
rational probability vector \(p=a/q\), with \(a\in\mathbb Z_{\ge0}^d\),
\(q\ge1\), and \(\sum a_r=q\). Define the integer deviations

\[
E_n=qP_n-na,\qquad R_N=\max_{0\le n\le N}\|E_n\|_\infty.
\]

**Lemma.** Every value of \(E_n\) occurs at most twice, and

\[
N+1\le2(2R_N+1)^{d-1}.
\tag{2}
\]

**Proof.** If \(E_i=E_j=E_k\) for \(i<j<k\), then

\[
P_j-P_i=(j-i)a/q,\qquad P_k-P_j=(k-j)a/q,
\]

so these distinct vertices are collinear. Also \(\sum_r E_{n,r}=0\), hence
its first \(d-1\) integer coordinates determine the last. Each lies in
\([-R_N,R_N]\), giving at most \((2R_N+1)^{d-1}\) possible values. Each has
at most two preimages. \(\square\)

For the unscaled discrepancy \(D_p(N)=\max_{n\le N}\|P_n-np\|_\infty\),

\[
D_p(N)\ge
\frac{((N+1)/2)^{1/(d-1)}-1}{2q}.
\tag{3}
\]

Thus a hypothetical infinite walk has, relative to **each fixed rational**
\(p\), discrepancy \(\Omega(N^{1/4})\) in 5D or \(\Omega(N^{1/3})\) in 4D.
No existence of limiting frequencies is assumed in this statement.

This gives an actual contradiction for a walk with
\(D_p(N)=o(N^{1/(d-1)})\), in particular bounded discrepancy to a rational
line. **The missing premise is a universal upper bound of that strength.**
Finite alphabet, positive steps, recurrence, and convergence of frequencies
do not themselves supply it. Convergence only says \(D_p(N)=o(N)\), when
\(p\) is the limiting frequency vector.

### Bounded discrepancy to an irrational line also fails

Suppose \(\|P_n-np\|_\infty\le C\) for all \(n\), now with any real \(p\).
Choose an integer \(m>4C\) and color \(n\) by the first \(d-1\) coordinates
of \(P_n\) modulo \(m\). The three-term van der Waerden theorem supplies
\(i,i+t,i+2t\) of the same color, with \(t>0\). The first \(d-1\) coordinates
of

\[
P_i-2P_{i+t}+P_{i+2t}
\]

are multiples of \(m\), with absolute values at most \(4C<m\), so vanish.
The last vanishes because coordinate sums equal time. This is an ordinary
abelian square, a contradiction. This familiar bounded-discrepancy obstruction
works in **every** finite dimension; it does not single out four or five.

## 3. Why the 5D frequency argument stops: exact candidate algebra

Shallit's substitution is

\[
h(0)=01213101314310,\qquad h(r)=h(0)+r\pmod5.
\]

Its [incidence matrix and prior diagnostic](../../../design/UNIT-STEP-4D-5D-INVESTIGATION.md#exact-descent-available-so-far)
are

\[
M=\begin{pmatrix}
3&1&3&1&6\\6&3&1&3&1\\1&6&3&1&3\\3&1&6&3&1\\1&3&1&6&3
\end{pmatrix},\qquad P_{14n}=MP_n.
\]

For \(E_n=5P_n-n\mathbf1\), at aligned lengths
\(E_{14^k}=M^k(5e_0-\mathbf1)\). Put \(B=M^TM\) and
\(H=\{x:\sum x_r=0\}\). Direct integer multiplication shows that \(M\) is
normal and

\[
(B^2-42B+421I)|_H=0.
\]

In particular \(B\)'s eigenvalues on \(H\) are among
\(21\pm2\sqrt5\). The sequence \(S_k=\|E_{14^k}\|_2^2\) satisfies
\(S_{k+2}=42S_{k+1}-421S_k\), with \(S_0=20\), \(S_1=420\). Therefore

\[
\boxed{\|E_{14^k}\|_2^2
=10\big((21+2\sqrt5)^k+(21-2\sqrt5)^k\big).}
\tag{4}
\]

These deviations are unbounded, with growth exponent

\[
\alpha=\log_{14}\sqrt{21+2\sqrt5}=0.613398\ldots,
\]

not the sub-quarter-power growth needed for the 5D contradiction.

This fixed point nevertheless has limiting frequencies exactly \(1/5\).
Indeed, for \(0\le t<14\), its usual partial-block identity gives
\(E_{14n+t}=ME_n+C_{n,t}\), where \(C_{n,t}\in H\) ranges over a finite set.
On \(H\), \(\|M\|_2\le\sqrt{21+2\sqrt5}<14\). Iterating along the base-14
digits bounds \(\|E_n\|_2\) by a geometric sum \(O(n^\alpha)=o(n)\).
This proves frequency convergence without bounded discrepancy.

Equation (4) is an infinite algebraic statement about the substitution, **not**
an infinite avoidance proof. The candidate could still fail at a later triple.
It demonstrates why rational frequency alone is not the missing boundedness
premise, and the counting lemma does not eliminate this leading 5D candidate.

## 4. Four letters: useful restrictions and explicit failed shortcuts

### Full support in every eight-letter window

Every ternary eight-letter word contains an ordinary abelian square, as proved
by the [existing extension-tree certificate](../../../design/UNIT-STEP-4D-5D-INVESTIGATION.md#1-why-three-positive-coordinate-directions-cannot-work).
Consequently, in any hypothetical 4D triple-free walk, **every eight consecutive
steps use all four letters**. Each letter has gaps at most eight and appears
at least \(\lfloor L/8\rfloor\) times in every factor of length \(L\).

This supplies lower densities, not bounded count deviations. In dimension five
the same argument only forces at least four different letters in each such
window, not all five.

One can also assume uniform recurrence when seeking a contradiction: the
infinite avoiding words form a closed shift-invariant subset of a finite
alphabet shift. If nonempty, it has a minimal nonempty closed invariant subset.
Compactness and minimality make every occurring factor recur with bounded
gaps (finitely many inverse shifts of its cylinder cover that subset). This
reduction does not assert bounded discrepancy, rational frequencies, or even
frequency convergence for every uniformly recurrent word.

### An unequal-length square is a genuinely new obstruction

Write proportional Parikh vectors uniquely as
\(\psi(x)=a v\), \(\psi(y)=b v\), with \(v\) a primitive nonnegative integer
vector and positive integers \(a,b\). If lengths differ, \(a\ne b\), so
\(|xy|=(a+b)\|v\|_1\ge3\|v\|_1\).

In an ordinary-abelian-square-free word, such a pair cannot have support at
most three: support one forces an ordinary square immediately; support two
gives length at least six, exceeding the binary bound three; support three
gives length at least nine, exceeding the ternary bound seven.
Thus an unequal weak square avoiding ordinary squares must use at least four
letters and have total length at least twelve. That minimum is attained by

```
0123 | 01213230
```

The blocks have count vectors \((1,1,1,1)\) and \((2,2,2,2)\), while the
whole twelve-letter word has no ordinary abelian square. This is checked
independently by direct integer cross-products. In the 4D problem, any new
unequal-length obstruction inside an ordinary-square-free word must use all
four letters; in 5D its support can be four or five.

### Short-range consistency does not imply global consistency

The periodic word \((01020103)^\omega\) passes **all** collinearity tests
whose first-to-last index span is at most fifteen, at every cyclic starting
position. Nevertheless, it has a triple at \((0,8,16)\): the two periods
have the same counts \((4,2,1,1)\). Thus even a recurrent periodic model can
satisfy these short-range constraints. Finding a cycle in a bounded-memory
avoidance graph is not an infinite triple-free construction. Conversely,
periodicity of that local model says nothing about every global avoider.

## 5. Bounded universal-tree attempt: it did not close

The new [resumable extension-tree probe](contradiction_probe.mjs) tests **all**
possible next letters up to global renaming, rather than a construction family.
A new vertex is rejected exactly when two chords ending there have the same
primitive integer direction. Every new triple ends at that vertex, so pruning
is exact. Restricted-growth canonical words remove only label symmetry, not
possible walks. An empty complete tree would prove (1).

The initial run was budgeted for sixty seconds, one JS worker, and ten million
extension attempts, with a target of 128 steps. It reached a valid word after
**1,250 attempts**, in less than a second, rather than exhausting the tree.
The [saved result](checks/contradiction-4d-tree.json) contains the full word and
**partial DFS** counts, explicitly not complete level counts. An independent
check of all \(\binom{129}{3}=349,504\) triples confirms the witness.

Consequently any universal 4D obstruction length would have to be **greater
than 128**. This is a finite diagnostic, not a record claim, an infinite
construction, or evidence that every surviving branch extends indefinitely.
The run stops at this decision point rather than replacing the missing proof
with an ever-larger prefix search.

## 6. Reproduction and next proof obligation

From the repository root:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
node research/unit-step/tracks/check_contradiction_obstructions.mjs
node research/unit-step/tracks/contradiction_probe.mjs \
  --alphabet 4 --target 128 --seconds 60 --attempts 10000000 \
  --state-dir .checkpoint-unit-step-contradiction-4d \
  --output research/unit-step/tracks/checks/contradiction-4d-tree.json
node research/unit-step/check.mjs
node research/unit-step/joint_minimum_examples.mjs
```

The DFS checkpoints the word, next-child stack, counters, and best witness
atomically, validates code/config identity and a state checksum, and resumes
without revisiting checkpointed branches. SIGINT/SIGTERM yield a consistent
checkpoint. Per-invocation budgets may change; alphabet, target, and code may
not. A fresh state directory reproduces the run; a completed compatible run
rewrites the same deterministic result without searching again. Timestamped
JSONL logs and checkpoint state stay under ignored `.checkpoint-*` paths,
separate from the finite evidence. The CLI documents the bounds and states.

The bounded checker independently verifies all 6,561 ternary eight-letter
words, the complete small extension trees, every ternary DFS resume boundary,
the unequal-square witness, the periodic countermodel, the saved 4D result,
and the exact matrix identities. These tests are not certification of a new
infinite avoidance or dimension-impossibility theorem.

**Remaining proof obligation:** show every infinite four- or five-letter
ordinary-abelian-square-free word has an unequal weak abelian square, or supply
another universal obstruction. For the counting route specifically, derive a
strong enough discrepancy upper bound from full avoidance, not from an
unsupported boundedness assumption. For a tree proof, justify and finish a
complete finite obstruction, not merely a bounded-memory surrogate.

No exact minimum has changed. No manuscript attribution, central checkpoint,
or `viz/` claim is changed; this is an inconclusive research track, not a
production-site result.
