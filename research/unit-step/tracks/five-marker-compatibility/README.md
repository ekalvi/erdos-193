# Five marker pairs: a common-fraction invariant and exact synchronization failures

**September 10, 2026. AI-assisted bounded research, not human certification.**
This is a follow-up to [the two-marker reduction](../../explorations/universal-five.md),
not a manuscript or a numerical-threshold proof. No literature-priority claim is
made for the elementary interval, Helly, or graph arguments.

## 1. Verdict

**No universal five-letter impossibility theorem was obtained. No infinite
five-letter avoiding word was constructed or refuted.** The substantive results
are compatibility lemmas and an exact counterexample to a tempting forcing step:

1. **Common-fraction synchronization.** With the two outer cuts fixed, each
   marker pair has a finite set of attainable fractions of its total marker
   count. A weak square using those outer cuts exists **if and only if the
   intersection of all these sets is nonempty**. The split witnesses may differ
   between pairs: a common fraction makes their individual letter-count windows
   pairwise intersect, and interval Helly supplies a single physical split.
2. **A short defect bridge.** At one fixed fraction, nine successful pairs but
   not ten leave exactly a two-letter adjacent-swap obstruction. Eight successful
   pairs leave a ternary bridge of length at most seven. These statements use
   only the already necessary absence of ternary ordinary abelian squares.
3. **An exact failure of unsynchronized fractions:**

   ```text
   010213432340124
   ```

   is weak-square-free, including unequal adjacent lengths. All ten marker pairs
   have proper returns within its **same outer interval [0,15]**, but their
   fraction sets have empty intersection. Even agreement on both outer cuts and
   compatibility with a single actual word do not remove the fraction obligation.
4. **At one already fixed split**, a spanning five-cycle of vanishing marker
   minors suffices if the factor uses at least four letters. More generally the
   robust count-vector testing graphs are exactly the 2-vertex-connected graphs.
   This is a different graph from the occurrence-window graph in item 1.

The stronger proposed conclusion “all ten pairs have some witness, therefore
there is a common witness” is **false for finite avoiding words**. That does not
refute an infinite-only forcing theorem.

### Attribution and scope

The word/basis-walk equivalence and basis encoding are Shallit's, as recorded
in the [AI checkpoint](../../AI-CHECKPOINT.md). The prior two-marker note supplied
the 236-return alphabet, the ternary bound, and the explicit synchronization
obligation; those are not claimed as new here. The original Erdős 193 theorem
of Cambie–Kalviainen is separate. The proposed six-step follow-up retains its
recorded Kalviainen/Cambie/Shallit contributions and pending independent-review
status. No manuscript was edited and no collaborator approval is implied.

The proofs below and both implementations were produced in this AI-assisted
pass. “Independent checker” means a separately implemented arithmetic oracle,
not an independent human investigator or external mathematical certification.
No Gaussian, sign, offset, substitution, raw-iid, or local-lemma premise is used.

## 2. From the ten clocks to a common-fraction invariant

Let \(z=w[i:k]\) be an arbitrary finite factor of length \(N=k-i\). For now
assume every letter in \(A=\{0,1,2,3,4\}\) occurs. Set

\[
T=\psi(z),\qquad Q(t)=\psi(z[0:t])\quad(0\le t\le N).
\]

All split positions below are **physical word cuts**. At a split \(t\), write
\(U=Q(t)\), \(V=T-Q(t)\). For marker pair \(a,b\), the left and right marker
increments are \(m=U_a+U_b\), \(n=V_a+V_b\). If both are positive, the existing
marker equation is

\[
nU_b=mV_b
\quad\Longleftrightarrow\quad
T_aQ_b(t)=T_bQ_a(t).
\tag{1}
\]

Because \(T_a,T_b>0\), (1) with positive marker increments is equivalent to

\[
\frac{Q_a(t)}{T_a}=\frac{Q_b(t)}{T_b}
=\frac{m}{m+n}=\theta\in(0,1).
\tag{2}
\]

**This fraction is not initially \(t/N\).** It is the fraction of the whole
factor's marker counts already consumed. Confusing those quantities would
silently assume the desired conclusion.

For each pair define the finite, exact invariant

\[
E_{ab}(z)=\left\{\theta\in(0,1):\exists t\in\{1,\ldots,N-1\},\quad
 Q_a(t)=\theta T_a,\ Q_b(t)=\theta T_b\right\}.
\tag{3}
\]

It can be computed from the binary erasure of \(z\) onto \(a,b\) alone:
a projected prefix with these counts corresponds to an actual word cut.
All ten erasures must be those of **this same factor**, not independently
chosen binary words or unrelated factors.

### Theorem 1: common-fraction synchronization, with explicit quantifiers

For **every** finite word \(z\) in which every letter of a finite alphabet
\(A\), \(|A|\ge2\), occurs,

\[
\exists t\ (0<t<N):\quad \frac{Q(t)}t=\frac{T-Q(t)}{N-t}
\quad\Longleftrightarrow\quad
\bigcap_{\{a,b\}\subset A}E_{ab}(z)\ne\varnothing.
\tag{4}
\]

More precisely, for **every** \(\theta\) in that intersection, the one common
split is \(t=\theta N\), which is an integer. Thus the theorem permits different
middle witnesses only with the **same outer endpoints and the same fraction**.

**Proof.** For a fixed \(\theta\), let

\[
I_a(\theta)=\{t\in\{1,\ldots,N-1\}:Q_a(t)=\theta T_a\}.
\]

This is empty or an interval of integers, because \(Q_a(t)\) is nondecreasing.
If \(s_a=\theta T_a\) is an integer strictly between 0 and \(T_a\), and the
zero-indexed occurrence positions of \(a\) are \(p_{a,1},\ldots,p_{a,T_a}\),
then exactly

\[
I_a(\theta)=[p_{a,s_a}+1,\ p_{a,s_a+1}]\cap\mathbb Z.
\tag{5}
\]

Membership \(\theta\in E_{ab}\) means \(I_a(\theta)\cap I_b(\theta)\ne\varnothing\).
If it holds for every pair, all these integer intervals pairwise intersect.
Writing their endpoints \(L_a,R_a\), choose a largest left endpoint and a
smallest right endpoint. Their two intervals intersect, so
\(\max_aL_a\le\min_aR_a\). A common integer cut therefore exists. At that cut
\(Q(t)=\theta T\), and summing coordinates gives \(t=\theta N\). This proves
the forward construction of a physical weak square. Conversely a weak square
has \(Q(t)=(t/N)T\), so \(t/N\) belongs to every set (3). \(\square\)

If some letters are absent, apply the theorem to the actual support of \(T\).
For factors of length at least eight in a hypothetical avoiding five-letter
word, that support has size at least four by the prior ternary obstruction.
No four-letter impossibility assumption is needed.

**Denominator-locked corollary.** For every five-letter factor with positive
counts satisfying

\[
\gcd(T_a,T_b)=2\quad\text{for all }a\ne b,
\]

if every pair has any proper marker return using the factor's outer endpoints,
then the factor is a weak square at its midpoint. Indeed every nonempty
\(E_{ab}\) is exactly \(\{1/2\}\). More generally a pair's possible fractions
are among \(r/\gcd(T_a,T_b)\), with \(0<r<\gcd(T_a,T_b)\).

This corollary is a forcing statement **under stated arithmetic and return
hypotheses**, not a theorem that all infinite five-letter words satisfy them.

## 3. A bounded bridge for nearly synchronized clocks

Fix a factor with all five counts positive and a fraction \(\theta\in(0,1)\)
such that all \(\theta T_a\) are integers. Define the **occurrence-window graph**
\(K_\theta(z)\): its vertices are the five letters, and \(ab\) is an edge
exactly when \(\theta\in E_{ab}(z)\). It is an interval intersection graph by
(5), not an arbitrary ten-bit pattern.

Suppose it is not complete. Put

\[
r=\min_aR_a,\qquad \ell=\max_aL_a;\qquad r<\ell.
\]

The **defect bridge** is the actual factor \(B=z[r:\ell]\).
A vertex is universal (joined to all the other vertices) if and only if its
window contains \([r,\ell]\): intersection with the two extremal windows gives
\(L_a\le r\), \(R_a\ge\ell\), and conversely these inequalities imply all
intersections. Consequently **no universal letter occurs in \(B\)**. This is
a cross-pair compatibility restriction on one actual intervening factor.

### Theorem 2: eight pairs give a ternary bridge; nine give one swap

For every five-letter factor \(z\) with positive counts and with **no ordinary
abelian square supported on at most three letters**, and for every fraction
\(\theta\) as above:

- Ten edges in \(K_\theta\) give a weak square at \(\theta N\), by Theorem 1.
- Nine edges give exactly one missing pair \(ab\). In one of its orientations,
  \(B=ab\), \(r=\theta N-1\), \(\ell=\theta N+1\), and

  \[
  Q(\theta N)=\theta T+e_a-e_b.
  \tag{6}
  \]

  Swapping these adjacent letters to \(ba\) would make that split a weak square.
  No claim is made that such a swap preserves avoidance elsewhere.
- Eight edges give two missing pairs sharing a letter. The bridge is over their
  at most three incident letters and has length at most seven.

**Proof.** If precisely \(ab\) is missing, orient its disjoint windows so that
\(R_a<L_b\). Every other window intersects both, hence covers \([R_a,L_b]\).
Thus \(r=R_a\), \(\ell=L_b\), and the bridge contains only \(a,b\), starts
with \(a\), and ends with \(b\). The local hypothesis excludes repeated equal
letters and alternating length-four factors. An alternating binary word with
different endpoints has even length, so this bridge has length exactly two.
Before the bridge all coordinates have their target values except \(b\),
which is one short. In its middle the count vector is (6). Summing coordinates
gives the asserted cuts.

If the only two missing pairs were disjoint, say \(ab\) and \(cd\), orient
\(I_a\) before \(I_b\). Both \(I_c\) and \(I_d\) intersect \(I_a\) and \(I_b\),
so both span their gap and intersect each other, a contradiction. The two
missing pairs therefore share an endpoint. All other vertices are universal;
only three letters can occur in the bridge. The prior ternary length-eight
ordinary-square obstruction bounds its length by seven. \(\square\)

The hypotheses are weaker than full weak-square avoidance and are guaranteed
by the existing two-marker ternary-gap conditions. Importantly, the bounded
bridge does **not** bound \(T\), the denominator of \(\theta\), the outer cuts,
or which near-complete graphs occur in an infinite word.

### Nine is not ten: exact one-fraction witness

The word

```text
02340|12341
```

is weak-square-free. Its total vector is \((2,2,2,2,2)\). At fraction \(1/2\),
the five windows, in letter order, are

\[
[1,4],\ [6,9],\ [2,6],\ [3,7],\ [4,8].
\]

All pairs except \(01\) intersect. The bridge is \(z[4:6]=01\); at the nominal
midpoint the defect is \(e_0-e_1\). This realizes, rather than eliminates,
the adjacent-swap obstruction. It also shows that a five-cycle of pairwise
window intersections is **not** enough for Theorem 1.

## 4. All ten pairs, same outer cuts, incompatible fractions

Take the exactly checked word

```text
z = 010213432340124,       T = (3,3,3,3,3).
```

The complete fraction sets for its outer cuts \(0,15\) are:

| Pair | \(E_{ab}(z)\) | One physical split \(t\) |
|---|---|---:|
| 01 | \(\{1/3,2/3\}\) | 2 |
| 02 | \(\{2/3\}\) | 9 |
| 03 | \(\{2/3\}\) | 8 |
| 04 | \(\{2/3\}\) | 11 |
| 12 | \(\{1/3,2/3\}\) | 4 |
| 13 | \(\{2/3\}\) | 8 |
| 14 | \(\{2/3\}\) | 11 |
| 23 | \(\{1/3,2/3\}\) | 6 |
| 24 | \(\{1/3,2/3\}\) | 7 |
| 34 | \(\{1/3\}\) | 7 |

For multi-level rows the displayed split uses \(1/3\). Every row uses positive
marker increments on both sides, and both marker colors occur in both blocks.
For example pair 02 at cut 9 has left marker counts \((2,2)\) and right
\((1,1)\), whereas pair 34 at cut 7 has \((1,1)\) and \((2,2)\).

The intersection is empty: pair 02 requires \(2/3\), pair 34 requires \(1/3\).
At \(1/3\) there are five successful pairs; at \(2/3\) there are nine, missing
only 34. The latter bridge is \(z[9:11]=34\), and

\[
Q(10)=(2,2,2,3,1)=(2,2,2,2,2)+e_3-e_4.
\]

For each row the checker independently evaluates, on **those same physical
intervals**, the remaining three-coordinate residual

\[
(nU_c-mV_c)_{c\notin\{a,b\}}.
\tag{7}
\]

It is nonzero in every row. Equation (7) is the gap equation with the actual
endpoint offsets included in the physical counts, not an offset-free proxy.
For pair 02 at cut 9 it is \((0,0,-6)\) on letters \((1,3,4)\); for pair 34
at cut 7 it is \((6,6,0)\) on \((0,1,2)\). Thus these marker witnesses are
explicitly **not** being combined as a weak square.

The independent gcd-direction checker tests all \(\binom{16}{3}=560\) triples
of cuts in this word, not just the ten selected witnesses or equal lengths.
None is a weak square.

### Extension status: three different statements

1. The displayed word is a **finite** avoiding counterexample to the proposed
   finite synchronization lemma. Whether this prefix has an infinite avoiding
   extension is **not established or refuted** by this pass.
2. Its ten ternary-gap decompositions **do** extend compatibly and indefinitely
   as a local object: repeat \(z\) periodically. The 60 pair-gap occurrences
   in one period have maximum length six, and every gap is ternary weak-square-free,
   including those crossing the seam. Periodicity makes that finite seam audit
   a proof of the local statement at every position.
3. This periodic extension is **not** avoiding: \(z|z\) is an ordinary abelian
   square at cuts \(0,15,30\). Hence the indefinite local extension and the
   finite counterexample do not constitute a five-dimensional construction.

## 5. A separate same-split invariant: delete common zero letters

For one already fixed physical triple \(i<j<k\), set
\(U=\psi(w[i:j])\), \(V=\psi(w[j:k])\), and

\[
D_{ab}=U_aV_b-U_bV_a.
\]

The **same-split graph** \(R(i,j,k)\) has edge \(ab\) when \(D_{ab}=0\).
For genuine marker witnesses require positive marker increments as in (1).
The algebraic statement below remains valid even without that extra condition.

Let \(Z=\{a:U_a=V_a=0\}\). After deleting \(Z\), the vectors
\((U_a,V_a)\) are nonzero and nonnegative. Two are joined precisely when they
lie on the same ray. Thus the remaining graph is a disjoint union of cliques.
Vertices of \(Z\) were universal; retaining them can give completely spurious
connectivity. This is the only zero-coordinate trap in the ray argument.

### Theorem 3: sharp robust count-vector testing graphs

For every graph \(H\) on five labeled vertices, the following are equivalent:

- For **all** nonzero \(U,V\in\mathbb Z_{\ge0}^5\) with
  \(|\operatorname{supp}(U)\cup\operatorname{supp}(V)|\ge4\), vanishing of
  \(D_{ab}\) on every edge of \(H\) implies that \(U,V\) are proportional.
- \(H\) is connected and remains connected after deleting any one vertex.

**Proof.** There is at most one common zero letter. Under the second condition,
the surviving edges connect all active rays, so every ray is the same. Since
both total block counts are positive, this gives positive proportionality.
For necessity, if \(H\) is disconnected, assign \(U_a=1\) everywhere and
\(V_a=1\) or 2 constantly on its components, using both values. If \(H\) is
connected with a cut vertex \(z\), assign \(U_z=V_z=0\) and use those two
positive ratios on the components of \(H-z\). These give the required
nonproportional countervectors with union support five or four. \(\square\)

Consequently the five pairs \(01,12,23,34,40\) suffice **at the same split**.
Five edges are minimal for this robust count-vector test; a graph of that
size works exactly when it is a spanning cycle. With full positive support
and no common zero letter, a spanning tree already suffices. These are not
claims that any of the required simultaneous equalities are unavoidable.

The spectrum of possible numbers of zero minors on five letters, with no
common zero letter, is \(0,1,2,3,4,6,10\), from partitions into ray classes.
If both blocks use the same four-letter support, it is \(4,5,6,7,10\): the
absent letter contributes four tautological edges. Thus seven simultaneous
matches force proportionality with full union support, but in the four-letter
case one needs eight. These are count-vector conclusions, not a bound on word
length or on how often such matches occur.

Exact avoiding words in [examples.json](examples.json) show the traps are real:

| Word and split | \(U\) | \(V\) | What fails |
|---|---|---|---|
| `01234|041423` | (1,1,1,1,1) | (1,1,1,1,2) | Six simultaneous equations do not suffice. |
| `0123|03132` | (1,1,1,1,0) | (1,1,1,2,0) | Seven and a connected graph do not suffice; 4 is absent. |
| `0134|034314` | (1,1,0,1,1) | (1,1,0,2,2) | The path equations 01,12,23,34 all hold; their articulation letter 2 is absent. |

**Do not interchange the graphs:** \(K_\theta\) allows different split witnesses
and is an interval graph; \(R(i,j,k)\) fixes the split and is a ray-class graph
up to common zeros. The near-complete graph in §4 does not contradict Theorem 3,
because its edges do not hold at one physical triple.

## 6. Independent finite checks and reproduction

Files:

- [search.mjs](search.mjs): deterministic canonical DFS for a length-15 word
  with three of each letter; all-ratios suffix rejection by time-weighted counts.
- [verify.mjs](verify.mjs): separate raw-slice **BigInt primitive-direction**
  oracle, binary-erasure return sets, occurrence-position windows, exhaustive
  small classes, and a periodic seam audit; it imports nothing from the search.
- [examples.json](examples.json): exact small witnesses and expected count data.
- [test.mjs](test.mjs): serial CLI regression for budget resume, completed reuse,
  signal flush/resume, source/config mismatch, corrupt checksums, and invalid
  cursors. It compares regenerated results byte for byte.
- [checks.json](checks.json): deterministic independent finite-check output.

| Audit | Scope and result |
|---|---|
| Counterexample discovery | 41,825 DFS letter attempts; 2,065 complete canonical avoiding leaves visited before the first hit. Not an exhausted extension tree. |
| Five explicit avoiding words | 1,230 exact triples, including 1,074 unequal-length triples; no violations. |
| Nonuniform profiles and unequal ratios | 241 fixed-seed finite test words (120 with a planted common split), lengths at most 91; 10,590 split comparisons and 864 common-grid fractions. All three formulations agree, including 103 positive unequal-length splits. This is sampling/algebra validation, not exhaustive avoidance evidence. |
| Common-level and bridge audit | All 945 first-occurrence-canonical words with each of five letters twice (113,400 labeled equivalents); 155,925 triples. Of the 195 avoiding words, 54 have nine half-level edges and 64 have eight; all bridge assertions pass. |
| Same-split count graphs | 1,011,204 nonzero vector pairs in \(\{0,1,2,3\}^5\), union support at least four; all 1,024 testing graphs audited. Exactly 238 pass, precisely the 2-vertex-connected graphs. This is not word enumeration. |
| Periodic local extension | All 60 pair-gap occurrences per period checked, including seams; maximum gap six. Actual square at cuts 0,15,30. |

All integer arithmetic is exact. The count-grid products are at most nine;
word-square and projected-return oracles use BigInt. The grid originally
\(\{0,1,2\}\) had only three strictly positive ray slopes and could not realize
one theoretically possible spectrum entry. The checker caught that coverage
mistake; enlarging it to \(\{0,1,2,3\}\) realizes and verifies the full stated
spectrum. No theorem was inferred from the insufficient first grid.

From the isolated worktree root, no packages or Python are required:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
base=research/unit-step/tracks/five-marker-compatibility

taskset -c 0 node --single-threaded --v8-pool-size=1 "$base/search.mjs" \
  --state-dir .checkpoint-five-marker-search-v2 --budget-ms 60000
taskset -c 0 node --single-threaded --v8-pool-size=1 "$base/verify.mjs" \
  .checkpoint-five-marker-verify-final
taskset -c 0 node --single-threaded --v8-pool-size=1 "$base/test.mjs" \
  .checkpoint-five-marker-tests
cmp .checkpoint-five-marker-verify-final/result.json "$base/checks.json"
```

The repository's [research checkpoint workflow](../../../../.github/workflows/research-checkpoint.yml)
also runs `verify.mjs`, the serial `test.mjs` regressions (including witness
rediscovery), and a byte-for-byte comparison with `checks.json`. This validates
finite artifacts and resume behavior, not the missing infinite forcing theorem.

CPU affinity 0 applies to all descendant threads as well. The final search took
about 0.12 seconds, the independent checks 1.01 seconds, and the serial CLI
regression 3.2 seconds. None is a long prefix scan.

Code/data hashes and configuration are embedded in atomic checksum-protected
checkpoints; incompatible revisions require a fresh work directory. Search
checkpoints preserve the DFS cursor every 256 work-loop iterations; verifier
checkpoints preserve completed bounded stages. Both handle SIGINT/SIGTERM at
these boundaries. The regression observed SIGTERM saves after 218 search
attempts and one verifier stage, then resumed to identical results. Timestamped
logs and checkpoints remain under ignored `.checkpoint-five-marker-*` paths,
separate from proof artifacts. The tiny CLI regression reruns on restart.

## 7. Remaining universal step and consequences

Let \(\mathcal L\) be the set of infinite five-letter words avoiding every
ordinary abelian square supported on at most three letters. This is precisely
the local ternary obstruction relevant here; every ternary factor has length
at most seven and belongs to the prior gap alphabet. A sufficient universal
forcing theorem, **not proved**, is

\[
\forall w\in\mathcal L\quad
\exists i<k:\quad
|\operatorname{supp}\psi(w[i:k])|\ge4,
\qquad
\bigcap_{\{a,b\}\subset\operatorname{supp}\psi(w[i:k])}
E_{ab}(w[i:k])\ne\varnothing.
\tag{U}
\]

Theorem 1 would turn (U) into an actual weak square on the same intervals.
Words outside \(\mathcal L\) already have an ordinary, hence weak, square.
An infinite avoiding counterexample lies inside \(\mathcal L\), so (U) would
be decisive if established. It is stated as a sufficient target, not asserted
equivalent to every possible route to a universal impossibility theorem.

More explicitly, for a chosen factor total \(T\) put \(g=\gcd(T_a:a\in A)\).
The only possible common fractions are \(r/g\), \(1\le r<g\). At each such
fraction, a hypothetical avoiding word must retain a pair of **disjoint
occurrence windows**. The missing task is to force a factor and a fraction
with no such pair, not merely to find a return separately for every marker
pair. Dense graphs reduce the obstruction to the bounded bridges of §3, but
nothing here forces density or eliminates the adjacent-swap defect across all
outer factors and unbounded denominators. That is the precise stopping point.

One arithmetic step is available universally: for **every** infinite word and
**every** positive integers \(M,L\), some factor of length at least \(L\) has
all counts divisible by \(M\). Indeed one of the finitely many prefix-count
residues modulo \(M\) occurs infinitely often; choose two such occurrences
sufficiently far apart. In an avoiding word, taking \(L\ge8\) ensures support
at least four. Thus arbitrarily divisible outer factors themselves are not the
missing ingredient. Divisibility supplies candidate fractions, not intersecting
occurrence windows or the pairwise gcd-2 condition of the corollary.

No numerical bound changes:

\[
4\le d_*\le s_*.
\]

A proof of (U), or any other truly universal five-letter obstruction, would give
\(d_*\ge6\), hence \(s_*\ge6\). Only **together with independent validation of
the existing six-step upper bound** would it settle \((d_*,s_*)=(6,6)\).
This pass validates neither premise. It eliminates none of the six ordered
pairs under the proposed ceiling in [the joint formulation](../../JOINT-MINIMUM.md).
Shallit's infinite five-letter candidate is not refuted by this work; it was
not tested or used as a premise here. Concurrent investigations were not audited
and are not being assessed by this checkpoint.

## 8. Reproducible stopping checkpoint

- Bounded pass: started September 10 at 17:10 UTC; final fresh independent
  recheck completed at 18:01 UTC, with stopping documentation at about 52 minutes.
  The fresh output was byte-identical to `checks.json`. No calculation remains
  running. This is an early, reproducible stop within the approximately one-hour
  budget, not a claim that more finite scanning would finish the proof.
- Base: `cb55c0496952a5bc0151e75a496c1e8664b5098a` (`origin/main` at creation).
- Isolated worktree: `/home/q5m/.paseo/worktrees/3gh4xinf/five-marker-compatibility`.
- Branch: `research/five-marker-compatibility`.
- Read first on resume: §§1–4 and §7 of this note, then the compact examples and
  independent checks. Do not rerun a long survival scan or turn the swap lemma
  into a claim that swaps can be repaired without creating other violations.
- The research-only visualization records the common-fraction obligation and
  the finite failure; its numeric bounds and review caveats are unchanged.
  `site/build.mjs --check` and all three site template tests passed; the archive
  checker and joint-minimum finite examples also passed, without certifying any
  new infinite theorem. The prior two-marker checker was freshly rerun on CPU 0:
  its ternary tree and all 1,886,685 finite triple comparisons passed.
- Concurrent unrelated changes were detected in the original worktree and left
  untouched. In particular, later integration of the research-site page needs
  reconciliation with that work, not an overwrite of it.
- No manuscript, central minimum/checkpoint definition, original-worktree file,
  deployment, publication, commit, or merge is part of this pass.

### Integration checkpoint (September 10)

A subsequent integration pass on `research/checkpoint-2026-09-10` copied the
proof note, examples, search, verifier, CLI tests, and deterministic checks
from the isolated word worktree without changing the executable artifacts.
A fresh single-core verifier run matched `checks.json` byte for byte; the
search/resume/signal regressions, all 14 existing exploration stages, archive
and joint-minimum checks, and three site-build tests passed. The central
checkpoint and research-only page now index this work, and CI repeats the
new verification and regression checks. These are code-validation results,
not independent human proof certification.

The separate square-Koch attempt is deliberately **not** archived here. Its
detailed artifacts were discarded at the user's request; only the central
retirement note is retained. No claim from that discarded attempt is added
to this report's evidence ledger. Neither minimum bound nor manuscript
attribution changes.
