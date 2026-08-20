# Plan for an unconditional inductive proof

**Status:** research plan, not a proof and not a new finite certificate.

**Implementation checkpoint 1 (2026-07-29): complete on this branch.**
`padic_macrocycle_lift.py` now isolates the exact `8 -> 16 -> 8` affine
Pluecker transport, proves the `t in {1,3,9}` normalization split, and emits a
budgeted/resumable finite residue census.  Its independent verifier checks the
committed `padic-macrocycle-lift-summary.json`: 66,429 projective state edges
through modulus `3^5` and the latent family through depth 16.

The useful outcome is algebraic, not the finite depth.  In the y-unit chart
`[g]=[x:1:z]`, inverse macrotransport is

```text
(x,z) -> (9x/u,(3-9z)/u),       u=-8-3z,
```

and

```text
q(g)=3g_y^2-g_y*g_z+3g_z^2,     q(N^2 g)=81q(g).
```

The chart has one 3-adic attracting projective direction; `x` contracts by
`3^2` and `z` by `3^4`.  For the known latent family,
`nu_3((g_n)_x)=2n` and `nu_3(q(g_n))=4n+1`.  Thus a larger bounded-modulus
state cannot encode the exact reveal countdown.  The next positive target is
a policy-reachable birth theorem giving a uniform bound on simultaneous
3-adic proximity to `g_x=0` and `q(g)=0`.

**Implementation checkpoint 2 (2026-07-30): complete for the fixed latent
orbit under the existing guard.**
`latent_family_reachable_entry_audit.py` and its independent verifier prove
that no member of the projective `N`-orbit of `H=(55,34,18)` can become a
secant in any finite continuation of the canonical guarded-L5 parent that
preserves the same two-cone birth guard.  The parent has exactly four
`348/275` cone lineages and all are orbit-disjoint; every new orbit member
would be rejected by that cone guard.  This removes one singular family from
Gate D.  It does not prove successor availability, unguarded exclusion, or a
uniform bound for other residual families, so the general reachable-birth
target remains open.

**Implementation checkpoint 3 (2026-07-31): bounded returning-line no-go.**
The exact observed L5--L8 `x`-line trace contains 1,021 physical returning
lines, 2,988 return episodes, and 2,980 minimized local-control types.  The
66,429-edge latent family covers none of them; the exact type count grows
`77, 205, 639, 2,059` by terminal level; and no implemented line rank
decreases on every observed return.  The fixed abstract orbit is already
excluded by the two-cone/provenance theorem under the guard.  Therefore stop
expanding that latent family as a model for reachable returns.  The next
state-design target is honest cursor-import birth/address provenance plus the
remaining directions outside the frozen guarded cones.

This plan is based on `main` at `ba42159`, including the merge of PR #6 at
`f9f6f1a`.  It targets the one universal statement that PR #6 leaves open:
connector availability on every reachable successor history, not just on the
certified guarded L5 -> L6 chronology.

## 1. Evidence ledger

The following distinction is load-bearing.

| Source | Status used here | Consequence |
|---|---|---|
| PR #6: invariant-cone inheritance | **PROVED** | A finite family of invariant direction classes can be grandfathered and frozen, conditional on availability under the birth guard. |
| PR #6: bounded fractional-tail formula and infinite incidence types | **PROVED** | Phase plus bounded spatial position cannot be the inductive state.  Reachable births, joint endpoint ancestry, and exact-zero recurrence must be represented. |
| PR #6: guarded L5 -> L6 transition and all-choice census | **CERTIFIED FINITE** | One chronology has 71--198,431 surviving choices per prefix.  This supplies a base case, a bottleneck, and falsification data; it supplies no universal transition. |
| PR #6: coefficient-nine affine family | **PROVED REFUTATION** | The photographed `C=9` candidate is dead for an infinite family of indices, not just at one finite prefix. |
| Guarded cone-core audit | **PROVED, POLICY-RELATIVE** | Every guarded `11/3` or `348/275` secant is one of 246 inherited pair lineages; both known positive-depth latent families are excluded under the guard.  Effects outside the cones and availability remain open. |
| Observed returning-line audit, L5--L8 | **CERTIFIED FINITE / NO-GO** | The fixed 66,429-edge family covers none of 1,021 observed returning lines; 2,980 exact trace types continue growing and no implemented rank decreases universally. |
| Photographs: four-increment dependence bounds, height-three/height-four classifications, the 118-word slab language, and the morphic census | **REPORTED / UNAUDITED** | No source, certificate, or checker for these claims is present in this checkout.  They are not premises of the plan. |

The photographs contain an intermediate claim that four height-at-most-three
dependences survive and a later claim that every such dependence is excluded.
The later statement may supersede the former, but neither is usable until the
other machine's artifacts are imported and independently checked.  PR #6 also
explicitly labels the reported q-uniform classifications and latent U/V
families unaudited.

Even if every photographed four-increment claim is correct, it is a negative
result for a small step alphabet.  The current target uses the fixed
124-vector radius-two alphabet.  Eliminating four-increment constructions does
not imply Erdős #193; it only argues against pivoting the main proof effort back
to that restricted construction class.

## 2. Decision

Continue the scale-and-rotate construction, but stop treating additional
levels as the main deliverable.  The proof should be a hybrid induction:

1. **Promote or forbid every genuinely recurrent exact-zero contact class.**
2. **Give every remaining reachable endpoint/secant cohort a strict arithmetic
   rank.**
3. **Prove that the exact union of near, promoted, and ranked effects leaves a
   connector and returns every successor to the same invariant.**

This is the concrete form of Requirements Q, S, E, and G in
`FAR-SECANT-RANK-LEMMA.md`.  A guarded L6 -> L7 run is useful only as a
counterexample generator for a proposed invariant.  Another successful single
chronology would not advance the universal quantifier.

The bounded returning-line audit retires the fixed latent macrocycle as a
model for observed recurrence.  Apply the proved cone/provenance exclusion
first; do not derive a universal residual basis from arbitrary 3-adic
functions.  Any next finite controller proposal must expose how unrelated
cursor imports acquire and retain their remote birth/address history.

## 3. The inductive lemma to prove

Use exact centered endpoint tokens and primitive Plücker line tokens as in
`FAR-SECANT-BIRTH-OPERATOR.md`.  The target certificate must provide:

- a finite controller state set `Q` with sound correlated concrete-history
  sets `Hist(q)`;
- a finite exact promoted block `P(q)` for noncontracting endpoint and secant
  classes;
- a bounded residual-rank envelope `Z(q)` for every unpromoted cohort;
- the complete killed-word mask
  `Near(q) | Promoted(q) | Tail(q)`; and
- one connector `sigma(q)` for each retained state.

The required lemma is:

> **Reachable 3-adic birth/rank safety lemma.**  The seed has a retained state.
> At every insertion, all new endpoints, all old--new and new--new secants, all
> already-born deep--deep secants, and every unrelated-cursor import are covered
> by `P` or `Z`.  Every exact-zero recurrent class is either proved unreachable
> or has a uniformly finite promoted representation.  Every other transported
> class strictly decreases a common finite rank.  For every concrete history
> in `Hist(q)`, `sigma(q)` is outside the exact global killed-word mask, and
> every sound concrete successor is represented by another retained state.

This lemma is intentionally stronger than agreement on finite traces and
weaker than classifying every bounded fractional ghost.  It classifies only the
policy-reachable joint endpoint/secant language.  Once proved, the existing
inheritance algebra, level growth, induction, and König argument give the
unconditional theorem.

## 4. Candidate rank: 3-adic first-return depth

The matrix arithmetic points to a specific induction rather than a generic
finite-state search.  For a primitive direction `g`, write

```text
g' = M g / t,             t = gcd(M g).
```

Because `det(M)=27` and `g` is primitive, `t` is one of `1,3,9`; `t=27` would
force every coordinate of `g` to be divisible by three.  Thus primitive
normalization has three exact 3-adic branches.  The direction and moment
transport is already known:

```text
g'  = epsilon M g / t,
mu' = epsilon cof(M)(mu - c cross g) / t.
```

For each finite phase/action/candidate contact template `tau`, seek an integer
Plücker residual polynomial `F_tau(g,mu)` with a transport identity of the form

```text
F_tau'(g',mu') = 3^e F_tau(g,mu) / t^d,
```

where `e,d` are explicit and the correlated prefix control is part of `tau`.
The intended all-depth implication is

```text
contact after n macrosteps
    => nu_3(F_tau(g,mu)) >= a*n-b                         (4.1)
```

for fixed positive `a`, except on explicitly solved singular components
`F_tau=0`.  Off those components, the valuation in (4.1) gives a finite
first-return rank.  On them, the class must be promoted, broken by the selected
policy, or forbidden at line birth.

This is where the photographed 3-adic suggestion is useful as a method, not as
a lemma.  The object to descend on is the exact Plücker contact residual and
joint address, not the coefficient height of a four-increment dependence.

A finite congruence census may discover the residuals and singular components,
but finite stabilization is not a proof.  The proof obligation is a lifting
lemma over `Z_3`: nonsingular residue classes lift uniquely and acquire the
strict valuation rank; every singular lift is solved symbolically and placed
in a finite promoted/guarded family.

## 5. Work program and gates

### A. Import and audit the photographed work

Obtain the scripts, raw certificates, input hashes, and test suite from the
other machine.  Reconcile the intermediate four-survivor statement with the
later full height-three exclusion.  Independently verify:

- canonicalization under permutation and sign;
- exhaustiveness of each symbolic case partition;
- the distinction between arbitrary finite prefixes and an all-length theorem;
- parameter-uniform claims for the two displayed dependence families and the
  `(-a,-b,0,a)` slab family; and
- the morphic search's exact scope and primitive-image assumptions.

**Gate A:** publish a claim ledger with each item marked proved, certified
finite, reported, or refuted.  None of these artifacts is a dependency of the
main induction unless its theorem is explicitly connected to the 124-step
construction.

### B. Build the correlated 3-adic contact transducer

Freeze one scale-equivariant scheduler and a policy channel before examining
its return graph.  Start from the guarded whole-word domains of PR #6; do not
add all 47,942 abstract holonomy polynomials as guards.  Most are not known to
be physical reachable secants, and the finite survivor floor is too small for
blind guard accumulation.

For increasing moduli `3^k`, enumerate exact correlated transitions carrying:

- pending step, corridor phase, selected whole word, slot, and prefix control;
- the joint least-common-ancestor/address state of both line endpoints;
- canonical primitive `(g,mu)` residue data;
- current site, candidate-line, and near--deep effect masks; and
- the insertion/cursor-import channel that created or exposed the token.

No Cartesian product of endpoint marginals is allowed.  Partition refinement
uses future masks and successor behavior, not current masks alone.

**Gate B:** every repeated residue/SCC has an exact witness family or a proof
that the overapproximation is spurious.  If new SCC structure grows with `k`
without a finite algebraic lifting description, the finite promotion route has
not earned a long search.

### C. Prove the 3-adic lifting and recurrence theorem

Turn the stable candidate structure from Gate B into an all-depth proof:

1. derive (4.1) by stripping one correlated address/control digit;
2. solve every singular lift as an exact algebraic component;
3. prove each cyclic component unrealizable, policy-broken, or finitely
   promotable with a closed successor rule; and
4. put the remaining components in a finite DAG, whose maximum path length is
   the residual rank.

The two guarded invariant cones are initial promoted examples, not an
exhaustive list.  Affine moments must be included: direction-only cone
membership cannot distinguish translated parallel lines or future candidate
incidence.

**Gate C:** an independent symbolic checker verifies the displayed transport
identities and the complete singular/nonsingular partition.  No conclusion is
allowed from checking only `k <= K`.

### D. Prove the reachable-birth bound by joint ancestry induction

Every physical secant is attributed once, to insertion of its later endpoint.
Induct on the joint endpoint address tree, not on Euclidean distance.  Prove
that a birth with first-return rank above a uniform constant `R` forces one of:

- a long common ancestral suffix that reduces to a finite local birth check;
- membership in a promoted singular component; or
- violation of the selected birth guard.

The induction must cover global old--new partners, same-word new--new pairs,
already-carried deep--deep pairs, and coefficient-one same-level cursor
imports.  The local 23-edge exclusion in `FAR-SECANT-BIRTH-OPERATOR.md` is a
base case, not a global ancestry theorem.

**Gate D:** one level-independent `R` covers every selected concrete successor.
All discarded endpoint identities have a proved reconstruction or irrelevance
rule.  A bound observed on L5/L6/L7 is not Gate D.

### E. Solve the exact availability game

With promoted classes and residual rank frozen, build

```text
Poison(q) = Near(q) | Promoted(q) | Tail(q)
Legal(q)  = {w in D_s : Atoms(w) is disjoint from Poison(q)}.
```

Represent correlated alternatives by exact mask antichains or ROBDDs.  Use the
PR #6 all-choice census to order actions and to attack the unique 71-survivor
bottleneck first, but never use its survivor counts as a lower bound on other
histories.  Compute the greatest fixed point

```text
Phi(X) = {q : exists w in Legal(q), every sound successor after w is in X}
```

and export `G`, `sigma`, and every sound successor edge.

**Gate E:** `q_seed in G`, `G subset Phi(G)`, each selected word is common to
all concrete histories represented by its state, and an independent verifier
recomputes exact masks and universal successor closure.  An empty fixed point
is a useful refutation of the frozen policy, not permission to weaken the
quantifiers.

### F. Assemble the unconditional proof

State the finite seed and connector domains, prove inheritance, cite the
reachable birth/rank safety lemma, and induct over every stitch and level.
Every connector has at least two steps, so finite walk lengths are unbounded.
Apply König's lemma to the finitely branching tree of valid words over the same
124-step alphabet.  Do not claim that the nonnested amplified levels converge
to the infinite walk.

**Gate F:** a short independent verifier checks only immutable logical data and
exact certificate relations.  The prose proof names every computational lemma
and its scope.

## 6. Fast falsifiers before any large run

Run these only after a candidate state/rank is defined.

1. At the guarded L6 rank-4,473 bottleneck, branch over all 71 survivors and
   search for two histories merged by the candidate state but having different
   next exact masks or successors.
2. Replay the known latent `8 -> 16 -> 8` family and the finite x-line returns;
   the candidate must promote, break, or strictly rank them rather than forget
   their zero current masks.
3. Inject all old--new and new--new births and unrelated-cursor imports into the
   proposed state.  Compare against full exact recomputation on the sealed
   L5 -> L6 chronology.
4. Only then use a guarded L6 -> L7 construction as an adversarial test.  Force
   choices toward maximal future poison rather than merely selecting the first
   survivor.

Any disagreement refines or rejects the invariant.  Agreement is finite
non-falsification only.

## 7. Long-run and certificate protocol

Every search expected to outlive an interactive run must have these commands
before its first full execution:

```text
estimate    count deterministic work units without doing the expensive scan
run         accept --checkpoint, --max-seconds, and deterministic shard/range
verify      independently replay a completed immutable certificate
```

A checkpoint must atomically record at least:

```text
schema/version, logical input names and SHA-256 hashes, code commitment,
phase, shard/range, exact frontier cursor, completed/total work units,
elapsed seconds, recent and lifetime throughput, ETA seconds,
state/SCC counts, rejection counters, and payload SHA-256.
```

Additional rules:

- print a heartbeat at a fixed wall-clock interval with `done/total`, rate, ETA,
  current phase, and checkpoint path;
- derive the resume cursor from the sealed checkpoint, never by scanning for a
  plausible partial output;
- partition work by immutable integer ranges and merge every range, including
  empty or unfavorable ranges;
- use atomic temporary-file replacement and fail closed on hash/schema/input
  mismatches;
- keep timestamps, RSS, inode data, resolved absolute paths, and host-specific
  `/tmp` spellings outside hashed mathematical payloads;
- make the verifier independent of constructor caches and heuristics; and
- report finite depth as regression coverage, never as an all-depth theorem.

This incorporates the portability defect identified in the PR #6 review:
certificate identity must depend on logical content, not `/tmp` versus
`/private/tmp` path resolution.

## 8. Decision points

| Observation | Decision |
|---|---|
| Photographed certificates fail independent reproduction | Quarantine those claims; continue the main induction without them. |
| A finite set of singular 3-adic components closes under correlated transport | Promote/guard them and proceed to the birth induction. |
| Singular components or future right languages have provably infinite reachable index | Stop the finite-quotient route; either prove a policy-weighted RCZI envelope or redesign the scheduler/menu/matrix. |
| Reachable births have no uniform valuation/first-return bound | The current guarded policy is not inductive; do not answer by computing another level. |
| The exact greatest fixed point is empty | Extract the concrete losing channel; refine the state once if it was an abstraction artifact, otherwise change the policy. |
| Gates C--E pass | Assemble the theorem immediately; further record walks are unnecessary. |

## 9. First implementation slice

The first code slice should be deliberately small:

1. write the exact contact residuals for one complete correlated macrocycle;
2. prove and regression-check the `t in {1,3,9}` primitive normalization split;
3. enumerate residue lifts only far enough to propose singular components;
4. replay the known latent family as a mandatory positive control; and
5. emit a compact lift graph whose every edge can be checked without the
   constructor.

Its output is a conjecture generator for Gate C, not a proof certificate.  No
full L7 construction or broad state census should begin until this slice has
produced a precise all-depth lifting conjecture.
