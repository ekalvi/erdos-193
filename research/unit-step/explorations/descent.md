# Focused follow-up: descent, infinite feasibility, and automatic selectors

**September 6, 2026. Three focused agents completed; parent review and fresh
checks completed. AI-assisted research, not human approval or a resolved minimum.**

## Verdict

The proposed unrestricted menu-preserving descent was **not proved**. Its
natural finite-path versions are false. However, the investigation produced a
stronger way to formulate the next attack:

> For any specified finite displacement menu, infinite subsampling feasibility
> is decidable by finite semigroup certificates. If a finite-menu subsequence
> exists, an automatic selector with the same menu exists.

The latter does **not** bound the selector's complexity in terms of menu size.
There is still no proof that every five-vector menu fails, no five-vector
infinite construction, and no changed bound on `d_*` or `s_*`.

The target throughout is the **particular** g85 walk in
[return-blocks.md](return-blocks.md). Even a complete no-five-subsequence theorem
would not establish the universal `s_*=6`. The original Erdős 193 theorem and
manuscript attribution remain separate and unchanged.

## 1. Three independently derived reports

| Report | Result | Important limitation |
|---|---|---|
| [Descent algebra](descent-algebra.md) | Exact all-scale endpoint laws; synchronized binary descent; a height-gcd necessary condition; one finite five-menu witness defeats every fixed base-4 rounding offset | Arbitrary infinite five-menu paths are not shown to synchronize. Two vectors can cover all seam types individually, so boundary-type coverage alone is insufficient. |
| [Automata](descent-automata.md) | Complete fixed-menu YES/NO decision theorem; prescribed-start variant; reduction to 4-automatic selectors | Matrix dimension, return-language size, and automatic-selector complexity depend on the menu heights. The bounded prototype is not a general large-input CLI or implemented selector-extraction tool. |
| [Adversarial audit](descent-adversary.md) | Counterexamples to floor descent, phase thinning, and first/last preprocessing; a valid fixed-phase edge lemma | Finite local counterexamples do not refute an existential implication for hypothetical infinite five-menu paths. No counterexample to full correction-state grouping was found or claimed. |

The parent read the arguments and reran all four agent checkers. An additional,
independently implemented direct-run verifier establishes the two fixed-menu
negative certificates in Section 4 below.

**Review correction:** the adversarial report's length-16, state-dependent
selector family is already a four-state affine-tag family covered by
[gaussian-tags.md](gaussian-tags.md). Its exact histogram (200 six-menu choices,
65,336 eight-menu choices) is useful finite data, not a newly excluded class.
That correction is recorded in the report itself.

## 2. What is wrong with naive coarsening, and what remains valid

For `D=diag(2,2,4)`, the correct identity is

\[
Q_{4m+a}=DQ_m+R(q_m,a),
\]

with 16 different corrections. Writing `p=H_n mod 16` identifies both the
child phase and the parent state; hence it identifies a correction `rho(p)`.
A fine vector `v=(x,y,h)` at that phase has parent vector

\[
T_v(p)=D^{-1}\bigl(v+\rho(p)-\rho(p+h\bmod16)\bigr).
\]

For an actual selected path, let `A_v` be the height residues where `v` occurs.
Its coalesced parent menu is exactly

\[
\bigcup_{v\in M}\{T_v(p):p\in A_v\}\setminus\{0\}.
\]

Thus `16|M|` is an unconditional upper bound, not `|M|`. Coalescence deletes
zero parent edges and adds no sums: a nonzero parent edge comes directly from
one fine edge crossing between occupied blocks. Gaps do shrink to at most
`ceil(B/4)`, but labels may split.

The source indices

```
0,17,34,51,78,100,127
```

use five displacement types and give six parent types for **each** rounding
`floor((n+b)/4)`, `b=0,1,2,3`. The exact tables are in the algebra report.
Other actual-Q examples refute fixed phase thinning and choosing first/last
selected representatives. Their translated copies occur arbitrarily late.

Two useful positive lemmas survive:

- **Fixed-phase edges:** if all selected indices already have one residue
  modulo four, equal fine labels have equal parent labels. The menu does not
  grow at that step. Producing this synchronized path, and re-establishing the
  property after each descent, remain separate obligations.
- **Height-gcd normalization:** with positive menu heights of common 2-adic
  gcd valuation `t>=2`, synchronized binary descent is an invertible linear
  transformation on the menu. The gap-16 obstruction consequently forces
  `max(menu heights)/2^t >=17`. For unsynchronized menus this does not supply
  a universal normalized gap bound.

A seven-vertex finite witness is enough to falsify a universal local lemma.
It is **not** enough to falsify a lemma restricted to infinitely extendable
menus. Section 4 makes that distinction concrete.

## 3. The infinite fixed-menu theorem

For a finite menu `M`, discard nonpositive-height vectors. Let
`B=floor((max height+3)/4)`. A vector of height `h` permits at most two source
index gaps, because `h=4g+s-r` with states in `{0,1,2,3}`.

1. Compute the exact finite language `L_M` of transition-word factors whose
   displacement sum lies in `M`. Only the candidate lengths are needed.
   Complete coverage comes from expanded adjacent pairs in the primitive
   eight-transition substitution, not a presumed stable prefix.
2. Build the NFA with states the empty word and proper prefixes of `L_M`.
   Completing a return resets to the empty word. Every infinite run resets
   infinitely often, since an unfinished return has length less than `B`.
3. For each transition letter `x`, let `P_(k,x)` be the Boolean matrix of
   its `k`-fold substituted word. The eight-matrix tuple updates by fixed
   Boolean products and lies in a finite semigroup.

**Negative certificate:** one component becomes zero. That actual substituted
factor recurs in every tail and blocks every NFA run, including runs entering
mid-return; no infinite selected path with `M` exists anywhere.

**Positive certificate:** the tuple repeats with every component nonzero.
Determinism gives nonvanishing at every scale, and finite branching gives an
infinite run. A separate finite row-state update handles an exactly prescribed
starting vertex; existence somewhere must not be advertised as existence at
every vertex.

**Automatic-selector theorem:** a positive tuple cycle can be decorated by
compatible NFA boundary states. Choosing finite product witnesses defines a
uniform decorated substitution. A cycle of its first-letter map supplies a
prolongable power; expand by the remaining substitution level and read reset
bits. This yields a **4-automatic selector** with infinitely many resets,
using only the original menu. The full extraction argument, including an
initial partial return, is in the automata report. No complexity bound
independent of menu heights follows.

The mathematical algorithm terminates for each finite integer input. The
current small prototype has an explicit regression cap; reaching that cap is
an error/unknown, never a mathematical NO. Only bounded examples were run.

## 4. Parent synthesis: the bad finite menus actually fail at infinity

The parent applied the prototype to two exact local counterexample menus,
then independently verified the negative certificates **without Boolean
matrix multiplication or importing the producer**.

### Menu A: the small floor witness

\[
M_A=\{(2,0,12),(1,1,30),(1,4,23),(-3,-1,14),(4,3,35)\}.
\]

There are exactly eight matching return words and 27 proper-prefix/NFA states.
The actual transition factor

```
tau^2(b) = bgabchbgafdabgab
```

kills all possible initial states. This menu cannot support an infinite
subsequence. Its maximum possible index gap is nine, so the prior gap-16
obstruction already implied this negative answer; this serves as a regression.

### Menu B: the witness defeating all four rounding offsets

\[
M_B=\{(7,3,70),(2,4,68),(1,-7,66),(4,6,108),(-3,2,89)\}.
\]

This has possible gaps up to **27**, beyond the old gap-16 class. There are
exactly 16 matching return words and 286 NFA prefix states. The factor

```
tau^2(c) = chbcdechbgabchbc
```

kills all of them. Starting from every possible partial-return state, the
numbers of states reachable after successive letters are

```
286,40,20,20,7,7,7,7,4,4,4,4,4,4,3,3,0.
```

**Proof of the infinite implication.** The independent verifier reconstructs
the complete return language from expanded actual adjacent pairs, forms all
proper-prefix states, and directly propagates their union through this
16-letter word. Ending with the empty set means there is no run through the
word from any boundary state. Primitivity places the word arbitrarily late
in the actual transition source. An infinite selected path would give a run
through every sufficiently late occurrence, even if its selected edges cross
the factor boundaries. This is impossible. Thus **no infinite subsequence
using `M_B` exists, at any initial vertex**.

This is an infinite impossibility theorem for **one specified five-vector
menu**, not a new general gap-27 obstruction. It demonstrates why the local
counterexample does not refute a future descent theorem restricted to infinite
extendability. Indeed, any at-most-five-menu infinite path containing all five
of these labels would have exactly this menu and is therefore excluded.

Reproduce the independent checks:

```sh
node research/unit-step/explorations/descent-five-menu-verify.mjs
```

The verifier takes well below one second. Its proof scope is the two displayed
menus only. For all first- and second-round bounded checks, run

```sh
bash research/unit-step/explorations/check-all.sh
```

## 5. Revised next attack—not a larger blind gap search

The desired construction-specific theorem is now precisely

\[
\forall M\subset\mathbb Z^3,\ |M|\le5:
\quad\exists k,x:\ P_{M,k,x}=0,
\]

where positive heights may be assumed and the return-language construction is
as above. Alternatively, a single five-menu nonzero cycle would supply the
infinite construction sought on the upper-bound side.

The best next proof-oriented target is an **infinite-extendability invariant
for the 16-height-residue correction system**, connected to these exact
certificates. A direct descent would follow if every hypothetical infinitely
extendable five-menu path admits a replacement whose parent-label union is
still at most five; finite arbitrary paths do not have that property. The
two certified negative menus show a concrete way that the infinite hypothesis
can eliminate local bad patterns. Proving that elimination uniformly is the
missing theorem, not a consequence of these examples.

Do not assert a bounded number of automatic-selector states merely because an
automatic witness exists. Do not replace the infinite parameter family by a
finite coefficient box. Do not infer a full correction-state return-sum bound
from the adversary's unsuccessful bounded search. The successful normalization
and fixed-menu decision theorems narrow the obligations but do not close them.

## 6. Run and review record

Three isolated contexts started from `aaf038f31f1433fc083360177efe8a67b67e5cb1`,
with read-only copies of the newer local return/tag reports. Agent runtimes
were approximately 15.6, 18.7, and 17.8 minutes. CPUs 0–2 were used one per
agent, CPU 3 by the parent; native computational threads were one. All agents
finished normally and no further round was launched.

Prompts, input hashes, sessions, logs, and completed statuses remain under
ignored `.checkpoint-s-star-descent/`. The parent repeated all four agent
checks and added the independent fixed-menu verifier. No packages, network
research, source-manuscript edits, commits, pushes, merges, publication, or
deployment were performed. The research-only visualization remains excluded
from production. All results remain AI-assisted and require human review.
