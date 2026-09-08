# New-words track: an all-ratios probability estimate and a local-lemma obstruction

**September 6, 2026. Independent AI research note; not human-reviewed.**
No infinite four/five-letter construction was obtained. No claim of priority is
made for the elementary probabilistic arguments below.

## 1. Verdict and exact scope

**Useful partial result, not a determination of either minimum.** This note
proves two statements about iid random letters and a standard class of
probabilistic approaches:

1. Write \(P_d(a,b)\) for the probability that independent uniform blocks of
   lengths \(a,b\) over \(d\) letters have the same normalized Parikh vector.
   For every \(d\ge2\) and real \(\gamma\ge0\),
   \[
   \boxed{\sum_{a,b\ge1}(a+b)^\gamma P_d(a,b)<\infty
   \quad\Longleftrightarrow\quad d>2\gamma+3.} \tag{A}
   \]
   This includes **every positive rational ratio**, with a uniform gcd-sensitive
   upper bound. Thus the unweighted all-ratios sum is finite on four/five
   letters, but the interval-length-weighted sum is infinite. The latter
   divergence persists using just lengths \((d,dt)\), with ratios \(1:t\).
2. For every finite alphabet, **no dependency-graph-only local-lemma guarantee
   based on the raw interval-overlap graph and the event marginals** can
   establish avoidance for arbitrarily long iid words. This includes the
   ordinary asymmetric LLL and, more generally, any universally valid guarantee
   using only those data. An induced-star countermodel proves the obstruction.
   It persists after discarding all events below any fixed size cutoff and
   for iid concatenations of bounded-length nonempty random macroblocks.

Statement 2 does **not** rule out lopsided dependencies, conditioning,
multiscale random constructions, resampling analyses exploiting more than
marginals, or all entropy-compression methods. Statement 1's divergence does
not itself imply impossibility of an avoiding word.

**Prior work, not a premise for the new proofs.** Shallit supplied the
14-uniform five-letter candidate and the basis/word equivalence. The read-only
prior `SHALLIT-FIVE.md` records fixed-ratio certificates and an all-ratios
boundary-state obstruction, not full five-letter avoidance. None of its
certificates or computations is used below. Cambie–Kalviainen's original
Erdős 193 theorem is distinct and already settled; the proposed six-step
follow-up and its review status are unchanged. No manuscripts were edited.

## 2. Proofs and the explicit failed constructive step

### 2.1 Exact all-ratios formula

Let \(\psi\) be the letter-count vector. Put
\[
 g=\gcd(a,b),\qquad a=gp,\quad b=gq,\quad \gcd(p,q)=1.
\]
The equality \(b\psi(x)=a\psi(y)\) is equivalent to
\[
 \psi(x)=p r,\qquad\psi(y)=q r,
 \qquad r\in\mathbb Z_{\ge0}^d,\quad\sum_i r_i=g.
\]
Indeed, coordinatewise coprimality first forces these divisibilities; summing
then gives \(\sum r_i=g\). Consequently
\[
 P_d(a,b)=d^{-(a+b)}
 \sum_{\substack{r\ge0\\\sum r_i=g}}
 \frac{a!}{\prod_i(pr_i)!}\frac{b!}{\prod_i(qr_i)!}. \tag{1}
\]
This is an identity, including arbitrarily unequal lengths, not an asymptotic
formula or a restriction to equal-length abelian squares.

### 2.2 A uniform multinomial estimate

Write \(u=(1/d,\ldots,1/d)\), \(\sigma=(d-1)/2\), and
\[
 f_n(v)=d^{-n}\frac{n!}{\prod_i v_i!}\quad(\sum_i v_i=n).
\]
There are constants \(C_d,c_d>0\), independent of \(n,v\), such that
\[
 f_n(v)\le C_d n^{-\sigma}
 \exp\!\left(-c_d\frac{\|v-nu\|_2^2}{n}\right). \tag{2}
\]
Here is a proof to specify the uniformity even at the boundary of the simplex.
For \(x=v/n\), let \(D(x\Vert u)=\sum_i x_i\log(dx_i)\), with \(0\log0=0\).
Taylor's formula along the segment from \(u\) to \(x\), using the Hessian
\(\operatorname{diag}(1/x_i)\ge I\), gives
\(D(x\Vert u)\ge\frac12\|x-u\|_2^2\), by continuity at zero coordinates.
The multinomial theorem also gives the entropy bound
\(f_n(v)\le e^{-nD(x\Vert u)}\).

If every \(v_i\ge n/(2d)\), the elementary two-sided Stirling inequalities give
\[
 f_n(v)\le C_d\frac{\sqrt n}{\prod_i\sqrt{v_i}}
 e^{-nD(x\Vert u)}
 \le C'_d n^{-\sigma}e^{-nD(x\Vert u)}.
\]
Otherwise \(\|x-u\|_2^2\ge1/(4d^2)\), so \(D\ge1/(8d^2)\). Split the entropy
exponent in half. The factor \(e^{-nD/2}\le e^{-n/(16d^2)}\) absorbs
\(n^\sigma\), with a finite constant depending only on \(d\); the other half
is at most \(e^{-\|v-nu\|_2^2/(4n)}\). This proves (2), for instance with
\(c_d=1/4\) after enlarging \(C_d\).

Apply (2) twice in (1). The exponent contains
\[
 \frac{\|pr-gpu\|^2}{gp}+\frac{\|qr-gqu\|^2}{gq}
 =\frac{p+q}{g}\|r-gu\|^2.
\]
Sum over the first \(d-1\) integer coordinates of \(r\), extending the domain
to all of \(\mathbb Z^{d-1}\). For \(\alpha>0\), uniformly in the shift \(t\),
\[
 \sum_{m\in\mathbb Z}e^{-\alpha(m-t)^2}
 \le 2+\sqrt{\pi/\alpha}.
\]
For example, bound each of the two tails of the unimodal Gaussian by its
integral, retaining at most two central terms. Taking the product of these
bounds proves
\[
 \boxed{P_d(a,b)\le C_d\left[
 (ab)^{-\sigma}
 +\left(\frac{g^2}{ab(a+b)}\right)^\sigma\right].} \tag{3}
\]
Constants are enlarged harmlessly between displays. In reduced-ratio variables,
the two terms are respectively
\((g^2pq)^{-\sigma}\) and \((gpq(p+q))^{-\sigma}\).

**The first term must not be omitted.** It is the discrete lattice-atom term;
replacing the lattice sum only by a Gaussian integral loses it. Section 2.4
shows that precisely this term controls extremely unequal balanced blocks.

### 2.3 Sharp summability: proof of (A)

Suppose first that \(\sigma>\gamma+1\). With
\(K_\gamma=\max(1,2^{\gamma-1})\), we have
\((a+b)^\gamma\le K_\gamma(a^\gamma+b^\gamma)\). Therefore the first term of
(3) sums to at most
\[
 2K_\gamma\zeta(\sigma)\zeta(\sigma-\gamma).
\]
For the second term, pass to \(g,p,q\) and then discard coprimality to obtain
\[
 \begin{aligned}
 &\sum_{g\ge1}g^{\gamma-\sigma}
   \sum_{\substack{p,q\ge1\\(p,q)=1}}
   (pq)^{-\sigma}(p+q)^{\gamma-\sigma}\\
 &\hspace{1cm}\le
 \zeta(\sigma-\gamma)\zeta(\sigma)^2<\infty.
 \end{aligned} \tag{4}
\]
Here \(\gamma-\sigma<0\), so the discarded factor \((p+q)^{\gamma-\sigma}\)
is at most one. Equations (3)–(4) are a genuine summable bound over all ratios.

For the converse, let \(Y\) be the Parikh vector of a uniform length-\(n\)
block. Since \(\mathbb E\|Y-nu\|_2^2=n(1-1/d)\le n\), at least half its mass
lies within radius \(\sqrt{2n}\) of \(nu\). This region has at most
\((4\sqrt n)^{d-1}\) possible count vectors: the first \(d-1\) coordinates
determine the last. Cauchy–Schwarz on that region yields
\[
 P_d(n,n)=\sum_v f_n(v)^2\ge 4^{-d}n^{-\sigma}. \tag{5}
\]
The diagonal subseries in (A) thus diverges whenever
\(\gamma-\sigma\ge-1\). This proves both directions of (A).

Interpretations, with their exact limitations:

- On a two-sided iid word, the expected number of weak squares at one specified
  **split** is finite exactly when \(d\ge4\). For these dimensions the number
  at each split is almost surely finite, simultaneously at all splits, by
  countability. It need not be zero, and there need not be a globally good tail.
- For one specified **letter position**, exactly \(a+b\) translates of an
  event with lengths \(a,b\) contain that position. Its expected total event
  incidence is consequently finite exactly when \(d\ge6\). Infinite expectation
  is not a statement of almost-sure infinite incidence or unavoidable squares.
- More quantitatively, for
  \(W_d(N)=\sum_{1\le a,b\le N}(a+b)P_d(a,b)\), the same estimates give
  \(W_4(N)=\Theta(\sqrt N)\) and \(W_5(N)=\Theta(\log N)\).
  The upper bounds follow from (3), summing \(g\le N\) and allowing every
  \(p,q\); the matching lower bounds follow from (5).

### 2.4 The unequal-length obstruction is real, not hidden in the diagonal

Take \(a=d\), \(b=dt\), with \(t\ge1\). Ask that the first block contain each
letter once and the second each letter exactly \(t\) times. This event has
probability
\[
 B_d(t)=\frac{d!}{d^d}\frac{(dt)!}{(t!)^d d^{dt}}
 \sim \frac{d!}{d^d}\sqrt d\,(2\pi t)^{-\sigma}. \tag{6}
\]
It is a weak square with reduced ratio \(1:t\) and fixed gcd \(d\). Thus
\(P_d(d,dt)\ge B_d(t)\). In fact they are asymptotic: (1) here sums over
finitely many compositions of \(d\); the unique uniform one is \((1,\ldots,1)\),
and every other composition has positive relative entropy, making its long
block probability exponentially small in \(t\).

Consequently even the **arbitrarily unequal subfamily** satisfies
\[
 \sum_t (d+dt)^\gamma P_d(d,dt)=\infty
 \quad\text{if }\sigma\le\gamma+1.
\]
For four/five letters this rules out interval-length summability without
appealing to equal squares. Keeping only the second term in (3) would instead
predict an invalid \(O(t^{-2\sigma})\) estimate in this family.

### 2.5 Why even the convergent regime does not make the raw LLL work

The following is stronger than failure to find good LLL parameters.
Fix any \(d\ge2\) and cutoff \(L\ge1\). Consider equal-length square events
with both lengths at least \(L\), sampled in an iid word, and use the graph
joining events exactly when their variable intervals overlap.

Let \(H_n\) be the event with lengths \((n,n)\) starting at position zero.
Inside its \(2n\)-letter support, place
\(m=\lfloor n/L\rfloor\) consecutive disjoint events \(B_1,\ldots,B_m\), each
with lengths \((L,L)\). For \(n>L\), their induced overlap graph is a star,
with hub \(H_n\) and pairwise nonadjacent leaves. Put
\(\delta=P_d(L,L)>0\). The hub marginal satisfies the elementary collision
bound
\[
 p_n=P_d(n,n)\ge\binom{n+d-1}{d-1}^{-1}, \tag{7}
\]
because its two independent count vectors have at most that many possible
values. For all sufficiently large \(n\), polynomial decay versus exponential
decay gives
\[
 p_n\ge(1-\delta)^m. \tag{8}
\]

**Asymmetric LLL obstruction.** If its parameters obeyed
\(\mathbb P(E)\le x_E\prod_{F\sim E}(1-x_F)\), then every leaf would have
\(x_{B_i}\ge\delta\), while the hub would require
\(p_n\le x_{H_n}(1-\delta)^m<(1-\delta)^m\), contradicting (8).
Extra neighbors only make this inequality harder.

**Obstruction to every graph-and-marginals-only guarantee.** On an auxiliary
probability space take mutually independent events \(B_i\) of probability
\(\delta\), and put \(C=\bigcap_i B_i^c\), of probability
\(r=(1-\delta)^m\). By (8), one can define an event \(H\) of probability
exactly \(p_n\) containing \(C\): add to \(C\) an independently thinned part
of \(C^c\), with thinning probability \((p_n-r)/(1-r)\). These events have a
valid star dependency graph and precisely the desired marginals, but
\[
 H^c\cap\bigcap_i B_i^c=\varnothing.
\]
Additional events in any larger finite overlap graph can be assigned their
prescribed marginals independently of everything constructed so far; the
larger graph is still a valid dependency graph, and avoidance is still
impossible. Therefore no universally valid theorem based **only** on that
graph and those marginals can guarantee avoidance of the original family.
This includes optimal graph-only local-lemma criteria, not just one choice of
asymmetric parameters. It does not say the auxiliary events are actual word
squares; that difference is exactly the additional structure the method must
exploit.

Discarding events below any fixed size cutoff does not help: choose a fixed
\(L\) above it and repeat the proof. **Discarding is not conditioning** on the
absence of those events. The proof makes no claim about the conditional
probabilities after such conditioning.

The argument also covers iid bounded-length nonempty macroblocks, of any
distribution. If every macroblock has length at most \(\ell\), then \(n\)
macroblocks have at most \((\ell n+1)^d\) possible Parikh vectors. Independent
adjacent collections have matching counts with at least the reciprocal
probability. Matching counts also forces matching total letter lengths, so
this is an actual weak square at macroblock boundaries, even when individual
macroblock lengths vary. A fixed number of macroblocks supplies a
positive-probability leaf event, and the same star proof applies in macroblock
coordinates. If that probability is one, avoidance already fails trivially.
For constant macroblock length the sharper support bound is
\(\binom{\ell n+d-1}{d-1}\). Thus independently sampling large locally vetted
blocks does not repair a graph-only overlap LLL. This does not cover arbitrary
Markov or scale-dependent block ensembles.

### 2.6 The failed constructive step

No inference from (A) to positive probability of total avoidance is valid.
In particular, summable hazards at one split cannot simply be combined over
all splits: changing/deleting a block changes many other adjacent-block tests,
and deletion creates new adjacencies. A reconstruction argument, a suitable
conditioned law, or a deterministic boundary-alignment lemma is missing.
The induced-star proof shows that optimizing constants in the raw-overlap LLL
cannot supply that missing step, even on alphabets larger than five.

## 3. Finite evidence and exact reproduction

The bounded checker `new-words-check.mjs` independently:

- enumerates every word of total length 2–7 over four and five letters and
  every split, comparing observed counts with (1): **119,490 words, 42
  alphabet/length-pair cases**, all exact integer comparisons passed;
- checks the balanced-anchor counts underlying (6) for \(d=4,5,6\),
  \(t=1,2,3,4\);
- finds exact finite horizons already certifying the graph-only obstruction
  with \(L=1\). Using just (7), the first half-lengths \(n\ge2\) satisfying
  \(d^n\ge\binom{n+d-1}{d-1}(d-1)^n\) are:

  | Alphabet | Half-length | Total horizon |
  |---|---:|---:|
  | 4 | 30 | 60 |
  | 5 | 60 | 120 |
  | 6 | 102 | 204 |

These horizons obstruct a proof method; they are **not** maximum lengths of
avoiding words. No Shallit prefix or fixed recoding was tested. The asymptotic
and infinite statements rest on the proofs above, not this checker.

From the repository root, no packages required:

```sh
mkdir -p .checkpoint-new-words
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_THREADPOOL_SIZE=1
taskset -c 1 node --v8-pool-size=1 \
  research/unit-step/explorations/new-words-check.mjs \
  > .checkpoint-new-words/check.jsonl 2>&1
```

Observed checker time was 58 ms, with no workers and CPU affinity 1. It logs
UTC timestamps, parameters, source hash, progress, and final assertions.
It is a fixed tiny regression, not a long computation; restart reruns it.
No substantive Python, package installation, subagents, or parallel compute
was used. Ignored logs remain separate from the report and checker.

## 4. Implications for the actual minima and integer 3D realization

**No numerical bound improves.** In particular, nothing here proves
\(d_*\ge5\), \(d_*\le5\), or \(s_*=6\). The proved relation
\(4\le d_*\le s_*\), and the separately proposed six-step ceiling subject to
its own review, are unaffected. The coincidence of six with the iid
length-weighted summability threshold is not evidence of a universal
six-letter obstruction: the raw graph-only method fails even above six.

No basis witness was constructed, so there is no candidate fixed integer
3D realization to certify. Were a future non-iid argument to construct a
four/five-letter weak-square-free word, it would initially prove only the
corresponding basis upper bound. For \(s_*\), one must additionally exhibit
one fixed integer matrix \(A\in\mathbb Z^{3\times d}\) satisfying
\[
 \operatorname{rank}_{\mathbb Q}
 [A\psi(x)\quad A\psi(y)]=2
\]
for **all** adjacent nonempty factors of that same infinite word. A generic
real projection or integer projections varying with the prefix length do not
supply this quantifier. Alternatively the probabilistic construction could
work directly with rank-deficiency events for one specified fixed integer
step menu. Equal-Parikh squares remain forbidden events for every such menu,
so the raw iid graph-only obstruction is still relevant to that route.

## 5. Strongest next attack, stopping reason, and files

**Next attack:** replace independent letters/independent bounded macroblocks by
a genuinely scale-dependent construction. A useful target is a deterministic
boundary-alignment rule or conditional probability estimate that eliminates
the linear number of independent bounded-scale neighbors of a long event.
The gcd decomposition (1) specifies what must be controlled: both the Gaussian
bulk and the discrete balanced atom in (6), for unbounded \(p,q\), not just
ordinary abelian squares. In a hypothetical accounting scheme costing
\((a+b)^\gamma\) per event, (A) clears the summability hurdle precisely when
\(\gamma<1/2\) on four letters or \(\gamma<1\) on five; producing such an
accounting scheme, its valid dependency/conditional bounds, and its constants
is still a separate task, not an existence theorem here.

**Stopping reason:** the bounded session produced a complete all-ratios
estimate and a rigorous broad obstruction, but no vetted morphism,
scale-dependent ensemble, or 3D matrix. Extending iid simulations or tuning
raw LLL weights would not address the proved obstruction. Record this partial
result rather than present an unsupported construction.

**Files changed (new only):**

- `research/unit-step/explorations/new-words.md` — this report.
- `research/unit-step/explorations/new-words-check.mjs` — bounded exact checker.
- Ignored operational files: `.checkpoint-new-words/run.log` and
  `.checkpoint-new-words/check.jsonl`.

No central checkpoint/problem files, manuscripts, prior/rival outputs, or
`viz/` files were changed; nothing was committed or published.
