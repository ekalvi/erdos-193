# Universal-five: two-marker returns and return-vector irreducibility

**Independent AI research note, September 6, 2026. Not a manuscript, collaborator approval, or a threshold proof.**

## 1. Verdict and exact scope

**The universal five-letter lower bound is not proved.** No infinite construction is claimed either. The strongest deliverable is an unconditional, all-ratios **two-marker return reduction for every five-letter word**, together with a general compression obstruction for an alphabet-minimal counterexample.

New work in this note:

1. Five-letter weak-abelian-square avoidance is equivalent to an explicit cross-section avoidance condition on **236 colored ternary-gap return words**. There are **84 return-count vectors** and **42 ternary prefix-count vectors**. Unlike a single-marker reduction, the two-marker return lengths are universally bounded, without recurrence assumptions or a four-letter impossibility premise.
2. **Return-vector compression theorem:** if an avoiding word has any tail tiled by nonempty blocks with at most \(r\) distinct Parikh vectors, then an infinite avoiding word exists over at most \(r\) letters. Consequently, if a five-letter solution exists but no four-letter solution exists, **every such tiling has at least five distinct Parikh vectors**. In particular, every recurrent factor has at least five distinct Parikh return vectors.
3. The reductions to uniform recurrence and to bounded single-letter gaps are proved with their quantifiers. Uniform recurrence can be imposed on an existential witness; it is not assumed of all words.
4. A small quantitative obstruction excludes bounded discrepancy about any rational frequency vector: for five letters, integer-scaled discrepancy radius \(B\) through time \(N\) requires \(N+1\le 2(2B+1)^4\).

These are elementary reductions/necessary conditions, not a claim of literature priority. They do not change any numerical bound on \(d_*\) or \(s_*\).

### Prior results, not new findings

- The normalized-Parikh/basis-walk equivalence and basis encoding are Shallit's, as attributed in the repository checkpoint.
- The ternary ordinary-abelian-square obstruction (maximum length seven) is prior work, independently rechecked here.
- The read-only lead was `FOUR-LETTER-RETURN-REDUCTION.md`, the earlier Track C note supplied under the tournament's `prior/` directory. Its 117 nonempty ternary gaps, partial-endpoint warning, and four-letter cross-section method motivated this extension. Its conclusions were not used as an unverified five-letter premise.
- The original Erdős 193 theorem of Cambie–Kalviainen is distinct and already settled. The proposed six-step construction and manuscript attributions retain their recorded review status; this note does not audit that construction.

## 2. Proofs and the failed universal step

Write \(\psi(v)\) for a word's count vector. An avoiding word has no consecutive nonempty blocks \(x,y\) with \(\psi(x)/|x|=\psi(y)/|y|\). All cuts below are actual word boundaries.

### 2.1 The precise obstruction to using one marker

Every length-eight factor of an avoiding five-letter word uses at least four letters. Otherwise the ternary ordinary-square obstruction applies.

This only says that **every pair of letters meets every length-eight factor**. It does not say that every individual letter does. Removing one letter leaves four, whose avoidance threshold is precisely unresolved. Thus the four-letter argument cannot simply replace ternary gaps by an asserted finite list of quaternary gaps.

For reference, the ternary ordinary-free extension tree has canonical row sizes

\[
1,1,1,2,3,5,5,3,0\qquad(\text{lengths }0,\ldots,8).
\]

The full labeled row sizes are \(1,3,6,12,18,30,30,18,0\). Appending each letter and rejecting any new ordinary square enumerates the entire tree: every new violation ends at the appended position. The attached checker independently regenerates this finite certificate.

An ordinary-free ternary word is also weak-square-free. Indeed, proportional integral counts have the form \(hR,kR\), with \(R\) primitive and \(h,k\) positive integers. Unless \(h=k\), which is already an ordinary square, the total length is at least \(3t\), where \(t\) is the support size of \(R\). For \(t=1,2,3\), this exceeds the ordinary-free maximum \(1,3,7\), respectively. Integrality of the multiplier follows from primitivity, for example by Bézout's identity on the coordinates of \(R\).

### 2.2 Universal five-letter two-marker theorem

Fix any pair of letters and rename it \(\{0,1\}\); the other letters are \(\{2,3,4\}\). Define

\[
\mathcal G=\{u\in\{2,3,4\}^*: |u|\le7,\ u\text{ has no ordinary abelian square}\}.
\]

The empty gap is included. Its labeled length counts are

\[
1,3,6,12,18,30,30,18;\qquad |\mathcal G|=118.
\]

Every avoiding word has the unique decomposition

\[
w=u_0c_1u_1c_2u_2\cdots,
\qquad u_t\in\mathcal G,\quad c_t\in\{0,1\}.
\tag{1}
\]

This follows because a marker-free gap cannot have length eight. In particular, marker occurrences are infinite and successive marker positions differ by at most eight. Empty internal gaps are necessary: unlike a single-marker decomposition, consecutive distinct markers are allowed.

For \(u\in\mathcal G\), put

\[
q(u)=\psi_{234}(u),\qquad
B(u)=\{\psi_{234}(v):v\text{ is a prefix of }u\}.
\]

Define

\[
H_0=X_0=0,\qquad
H_t=\sum_{r=1}^t c_r,\quad
X_t=\sum_{r=0}^{t-1}q(u_r)\quad(t\ge1),
\]

where \(H_t\) is scalar and \(X_t\) is a three-vector. Let

\[
C_t=\{(H_t,X_t+\alpha):\alpha\in B(u_t)\}\subset\mathbb Z^4
\qquad(t\ge0).
\]

In the invertible integer coordinates

\[
(P_0,P_1,P_2,P_3,P_4)\longmapsto
(P_0+P_1,P_1,P_2,P_3,P_4),
\]

the walk's vertices are exactly

\[
\bigcup_{t\ge0}\{(t,z):z\in C_t\}.
\tag{2}
\]

Here subscripts on \(P\) in this displayed coordinate map denote coordinate labels, not times. Layer zero contains **all** initial-gap prefixes, not merely the origin unless \(u_0\) is empty. For \(t\ge1\), a prefix \(v\) of \(u_t\) corresponds to original time

\[
|u_0|+t+\sum_{r=1}^{t-1}|u_r|+|v|.
\]

**Theorem A.** A sequence (1) is avoiding if and only if, for every \(0\le a<b<c\) and every \(x\in C_a,y\in C_b,z\in C_c\),

\[
(c-b)(y-x)\ne(b-a)(z-y).
\tag{R5}
\]

**Proof.** For vertices in three different layers, their first coordinate is the marker count, so equality in (R5) is exactly collinearity in (2). Necessity follows.

Conversely, take a purported chronologically ordered collinear triple. Its two displacement vectors in the original count coordinates are nonzero and nonnegative; hence they are positive scalar multiples. Their marker increments are therefore either both zero or both positive. They cannot have exactly one zero. If both are zero, the entire offending factor is in one ternary gap, excluded by §2.1. If both are positive, its layers are strictly increasing and (R5) excludes it. This covers every endpoint and every ratio. ∎

The return alphabet is

\[
\mathcal R=\{(c,u):c\in\{0,1\},\ u\in\mathcal G\},\qquad |\mathcal R|=236.
\]

The return block is \(cu\), of length one through eight. There are 42 different \(q(u)\), hence 84 full return-count vectors \((1-c,c,q(u))\). The union of the \(B(u)\) has 42 elements: a prefix is itself a gap. There are 1,394 colored word/prefix incidences. These counts are exact finite audits, not the reason the infinite equivalence holds.

For an existence formulation, one may take \(u_0\) empty by choosing a marker pair containing the first letter. For a fixed arbitrary pair and an arbitrary word, retain \(u_0\) as above. Thus no initial vertices are silently discarded.

### 2.3 The remaining global equation

Set \(m=b-a\), \(n=c-b\), and choose compatible offsets \(\alpha\in B(u_a)\), \(\beta\in B(u_b)\), \(\gamma\in B(u_c)\). A violation is exactly the simultaneous pair of equations

\[
n(H_b-H_a)=m(H_c-H_b),
\tag{M}
\]

\[
n(X_b-X_a)-m(X_c-X_b)
=n\alpha-(m+n)\beta+m\gamma.
\tag{G}
\]

Equation (M) requires equal normalized **marker-color** counts, while (G) handles the remaining three coordinates and all partial endpoints.

**Explicit failed step:** binary recurrence can give instances of (M), but no argument here forces the same intervals and compatible offsets to satisfy (G). The three-dimensional ternary count sums in (G) are unbounded. Finite choices for each individual offset do not bound \(m,n\), their coprime ratio, their common spacing, or the accumulated return sums. Nor can the prefix sets be detached from their actual gap words.

The required universal quantifier remains

\[
\forall(c_t,u_t)_{t\ge1}\quad
\exists a<b<c,\alpha,\beta,\gamma\quad
\text{such that (M) and (G) both hold},
\]

with \(u_0\) and all offset compatibilities included. It is **not proved**. Checking a finite list of local return combinations cannot replace it.

### 2.4 Return-vector compression: a global necessary condition

**Theorem B.** Let \(w\) be an infinite avoiding word on any finite alphabet. Suppose some tail admits a partition

\[
w[p_0:\infty)=R_0R_1R_2\cdots
\]

into nonempty finite words, and the set \(\{\psi(R_i):i\ge0\}\) has cardinality \(r<\infty\). Then an infinite avoiding word exists over \(r\) letters.

**Proof.** List the distinct vectors as \(V_1,\ldots,V_r\) and code \(R_i\) by the index of its vector. If two consecutive nonempty code blocks have normalized count vectors equal, their code Parikh vectors are positive proportional. Applying the linear map \(e_j\mapsto V_j\) makes their vector sums positive proportional. Those sums are the Parikh vectors of two consecutive nonempty factors of the original word, contradicting avoidance. No equality of the lengths of the \(R_i\) is required. ∎

This is Shallit's encoding principle applied to **return chords**, not a claimed new encoding principle.

Consequences with precise scopes:

- Unconditionally, no avoiding word admits such a tiling with at most three vectors, by the prior ternary obstruction.
- **If \(\neg\mathcal B(4)\)**, no avoiding word on any alphabet admits such a tiling with at most four vectors.
- In particular, a five-letter witness for an alphabet minimum of five must have **at least five distinct Parikh return vectors for every recurrent nonempty factor**. Take consecutive starting positions of occurrences as the cuts; overlapping occurrences still give positive-length return blocks, so the proof is unchanged.
- Every two-marker return-count code from §2.2 is itself avoiding on its actually used subset of the 84-vector alphabet. If only four vectors are used, it yields \(\mathcal B(4)\). Its avoidance alone is not sufficient for (R5), since it forgets partial endpoints.

There is also a uniform finite-window form. If \(\neg\mathcal B(4)\), König's lemma gives a finite maximum \(L_4\) for lengths of four-letter avoiding words. For **any** avoiding word and **any** partition into nonempty blocks, every \(L_4+1\) consecutive blocks have at least five distinct Parikh vectors. Otherwise their vector code is a forbidden four-letter finite word. This quantifies over arbitrary induced return scales, not just the original letter-scale local obstructions. No value for \(L_4\) is established here, and its existence must not be assumed unconditionally.

### 2.5 What compactness really permits

**Proposition C.** If an infinite avoiding word exists on at most five letters, there is a uniformly recurrent such word. If no four-letter avoiding word exists, this witness uses all five letters.

**Proof.** Let \(X\) be the set of avoiding one-sided words on the fixed five-letter alphabet. It is a closed shift-invariant subset of the compact product space: every violation has a finite witness. A descending chain of nonempty closed shift-invariant subsets has nonempty intersection, so the usual minimal-set argument gives a minimal nonempty such subset \(Y\subseteq X\).

The forward orbit closure of any \(y\in Y\) is all of \(Y\). For any factor \(v\) occurring in \(Y\), its prefix cylinder \(U\) is nonempty and relatively open. The sets \(\sigma^{-n}U\), \(n\ge0\), cover \(Y\). A finite subcover supplies a bound \(K\) such that every \(\sigma^t y\) sees an occurrence of \(v\) within the next \(K\) positions. Thus \(y\) is uniformly recurrent. If it omitted a letter, it would itself give a four-letter witness. ∎

A separate elementary compactness observation is useful: if one letter has arbitrarily long missing intervals in an avoiding word, there are avoiding words of arbitrary finite length on the other four letters. Their finitely branching prefix tree has an infinite branch, proving \(\mathcal B(4)\).

Consequently, **under \(\neg\mathcal B(4)\)** every length-\(L_4+1\) factor of **every** avoiding five-letter word uses all five letters. This is a universal single-letter gap bound, but conditional on the unresolved four-letter impossibility. Without that premise only the two-marker bound of eight is unconditional.

Theorem B plus Proposition C gives a justified target class: an alphabet-minimal five-letter witness may be chosen uniformly recurrent, with finite sets of return words to each factor, but every such set has at least five different count vectors. It need not be morphic, balanced, uniquely ergodic, or valuation-governed.

### 2.6 An additional quantitative necessary condition

**Proposition D (rational-drift packing).** For an avoiding basis walk \(P_0,\ldots,P_N\) in \(q\) dimensions, fix a rational frequency vector \(p=a/D\), with \(a\in\mathbb Z_{\ge0}^q\), \(D>0\), and \(\sum a_i=D\). If

\[
|DP_{n,i}-na_i|\le B\quad(0\le n\le N,\ 1\le i<q),
\]

where \(B\) is a nonnegative integer, then

\[
N+1\le 2(2B+1)^{q-1}.
\]

**Proof.** The first \(q-1\) integer error coordinates determine the last, since their sum over all \(q\) coordinates is zero. Three identical error vectors at different times would put three vertices on one line of direction \(a\ne0\). Each error vector therefore occurs at most twice. There are at most \((2B+1)^{q-1}\) possibilities. ∎

For \(q=5\) this forces discrepancy of order at least \(N^{1/4}\) from every fixed rational drift, with the denominator factor understood. The same argument applies on every translated finite interval. This excludes bounded rational-drift descriptions, not arbitrary finite-state descent certificates or arbitrary five-letter words. It is an elementary packing corollary, not a threshold argument.

## 3. Finite evidence and exact reproduction

Checker: [`universal-five-check.mjs`](universal-five-check.mjs). No packages, Python, worker pools, Shallit-specific prefix tests, or fixed recoding searches were used.

From the worktree root:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
node --check research/unit-step/explorations/universal-five-check.mjs
node --single-threaded --v8-pool-size=1 \
  research/unit-step/explorations/universal-five-check.mjs \
  .checkpoint-universal-five
```

Use a new ignored work directory for a fresh independent run. Repeating a completed command validates its source/config identity and checkpoint digest and reuses completed stages. Atomic stage checkpoints and timestamped JSONL logs stay in the work directory. The actual bounded run took about one second on CPU 2; there is no long search or uncheckpointed substantive Python process.

Recorded source SHA-256:

`0cd71e2d9db0124eaa7300483682a578a1a10e0a243ca96f6528265e464ae2bb`

Results:

| Audit | Scope | Result |
|---|---|---|
| Ternary tree and return alphabet | Entire ordinary-free extension tree through length eight | 118 gaps including empty; 236 colored returns; 84 return vectors; 42 prefix vectors |
| Short return pairs | All 6,400 words \(0u c v d\), \(|u|,|v|\le4\), \(c,d\in\{0,1\}\) | Direct and cross-section tests agree on all 870,304 triples |
| Full gaps / initial gaps / examples | 236 one-gap cases, 1,000 fixed-seed samples, two explicit unequal examples | Agreement on all 1,016,381 triples |

Total: **7,638 test cases and 1,886,685 exact vertex-triple comparisons**, including 17 unequal-length violations. Tests include initial gaps, empty internal and terminal gaps, both marker colors, and the prior length-12 partial-endpoint example. The largest tested word length is at most 24, so all integer products are exact in JavaScript numbers. A repeated run successfully reused all three validated checkpoints, and its result was byte-identical to the fresh result.

These are algebra/indexing checks. Most tested words are **not** claimed to avoid squares. Sampling is labeled sampling; the entire five-letter extension tree has not been exhausted. The infinite equivalence and compression statements rest on the proofs above.

## 4. Implications that really follow for the two minima

No numerical improvement follows. The established lower bound remains

\[
4\le d_*\le s_*.
\]

The proposed six-step upper bound retains its independent-review qualification. Neither \(d_*\ge5\), \(d_*\ge6\), nor \(s_*\ge6\) is established here.

If an eventual proof made (R5) impossible for every sequence, it would give \(\neg\mathcal B(5)\), hence \(d_*\ge6\) and \(s_*\ge6\) by encoding. That implication is valid; its premise is missing. A successful four-vector return compression would instead give a four-letter basis construction, not automatically a fixed four-step 3D construction.

## 5. Strongest next attack and stopping reason

The useful next global attack is to exploit the **simultaneous ten marker-pair clocks** of one five-letter word. Each pair has the same bounded ternary-gap alphabet, but the different decompositions must arise from one underlying word. A contradiction must force a compatible instance of (M)+(G), not merely separate equalities in different pairs or at different intervals.

The return-vector theorem supplies a separate sound target when investigating an alphabet-minimal five-letter counterexample: a factor with only four Parikh return vectors collapses the problem to a four-letter construction. It does not by itself contradict the known lower bound of four. A putative recurrence theorem forcing at most three vectors would be decisive, but no such theorem is supplied.

**Stopping reason:** after the bounded proof-oriented pass, the simultaneous unbounded return-sum/ratio quantifier remains untouched by a forcing argument. Increasing local enumeration would not justify closing it. The finite checks validate the new reduction rather than pretend to advance the numerical threshold. Work stopped within the requested time budget, with no publication, commit, merge, or central-status edits.

### Files changed

- `research/unit-step/explorations/universal-five.md` — this report.
- `research/unit-step/explorations/universal-five-check.mjs` — small exact checker.
- Ignored runtime files only: `.checkpoint-universal-five/{state.json,run.jsonl,result.json,resumed-result.json}`.

No manuscripts, central checkpoint/problem files, or `viz/` files were changed.
