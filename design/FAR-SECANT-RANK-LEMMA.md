# Far-secant rank lemma: exact obligations and conditional closure

**Status (2026-07-18): open design specification, not a proof of Erdős #193.**
This note separates elementary algebra that is already proved from
finite computations and from the missing uniform statements.  In particular,
it does **not** assert that the finite correlated quotient defined below
exists.

The intended use is as a referee checklist.  A future certificate closes the
far-secant gap only if it supplies every object and verifies every quantified
condition in Sections 4--8.  A finite replay, a sampled transition graph, or a
decreasing average shell profile is not a substitute.

## 1. Status ledger

| Item | Status | What may be used |
|---|---|---|
| Endpoint/line decomposition | **Theorem** | Exact classification of every new collision or collinear triple |
| Linear and affine Plücker transport | **Theorem** | Exact transport of points, secants, lines, and incidences under `M_BAL3` |
| Availability-grade correlated endpoint/secant quotient | **Open requirement** | A trivial all-poisoned TOP quotient exists; no quotient fine enough for the envelope and safety game is proved |
| Recurrent-type promotion and residual DAG | **Conditional graph lemma** | Valid only after a finite, universal, transition-sound quotient is supplied |
| Ranked cohort envelope | **Open requirement** | Must bound branching, reinjection, and near--deep and deep--deep pair creation |
| Combined nonfatality and safety greatest fixed point | **Open requirement** | Must retain a legal word after the exact near and sound far masks are unioned |
| Frozen-prefix `A -> B -> C -> D -> E` policy refinement | **Exact finite computation** | Ten fixed-`B`, fixed-`C` response leaves cover all 1,997 exact `A` actions; one fixed `D` works globally and each leaf has a fixed `E`; no successor congruence is proved |
| L5--L8 tagged-lineage and birth/shell trace audits | **Exact finite computation / finite evidence** | Exact one-orbit falsifiers and quotient-design data only; all nonzero enriched states remain unrepeated |
| L5--L8 x-parallel resonance audit | **Exact finite computation / obstruction** | Latent zero-effect lines reactivate, and exact effect-key cycles of periods 1--3 occur; even adjoining the recorded action leaves three physical period-three returns |
| Phase-free bounded-prefix x-line core | **Theorem** | Every effectful synchronized x-line lies among at most 1,681 integer lateral offsets per phase for the length-at-most-five domains; occupancy, births, and unrelated cursor jumps remain open |
| L9 selected-horizon age-two audit | **Exact finite computation / obstruction** | 58 of 488 actual tagged lineage states have nonzero L9-anchor poison, refuting literal age-two incidence-inertness; current connector interiors and universal closure remain untreated |

The current exact frozen-prefix result should not be conflated with the open
rows.  At the consecutive L8 cursors `A=67009`, `B=67011`, and `C=67008`, all
1,997 legal `A` actions have an immediate `B` response and every one of the
21,669 tested `A,B` histories has a `C` response.  The four coarse `A -> B`
response leaves are not closed: their sizes are 1,241, 206, 188, and 362, and
the 1,241- and 362-action leaves have no single fixed `B,C` pair.  Exact
`C`-poison predicates refine them into 10 response leaves covering all 1,997
actions with zero unresolved histories.  At the immediately following real
stitch, gap 67,013 of step type 19, every one of those 1,997 selected
`A,B,C` histories has a `D` response.  No further split is needed: the same
domain word `[0,3,4]` works in all ten leaves, each leaf has 283--796 common
`D` words, and the minimum per-history survivor count is 1,601.  The
immediately following stitch is `E=67012` of step type 17 at rank 67,014.
Every selected `A,B,C,D` history has an `E` response.  Again no predicate split
is needed: the existing ten leaves have 46--1,923 common `E` words, use five
distinct selected `E` words between them, and the minimum per-history survivor
count is 6,995.  The exact ten-channel union includes all four unary and all
six mixed-pair terms and agrees with two independent full-history poison
recomputations.  The
overlapping 1,977-action
`B=8765` probe similarly has no uniform `C` but refines into eight response
leaves.  These are proved finite facts for one frozen prefix, not bounded-state
observables, transition congruences, or a safety fixed point.

Writing the four source leaves as `L` and their selected C-response
subpartitions as `R_L`, the exact finite quantifier is

```text
there exists one fixed D_0 such that, for every L, there exists fixed B_L
and a finite partition R_L such that
    for every R in R_L, there exists fixed C_(L,R) such that
        for every exact A in R,
            P + A + B_L + C_(L,R) + D_0 + E_(L,R) is legal.
```

The `D` and `E` assertions are the exact canonical computations in
`l8_fourth_ply_transition.py` and `l8_fifth_ply_transition.py`; they remain
only two frozen-prefix transitions.

## 2. Exact endpoint/line decomposition

Let `H` be a finite set of distinct lattice points with no collinear triple.
Let `I` be the interior-point set of one candidate connector.  Its two anchors
already belong to `H`.  Assume the connector domain has certified, before this
test, that the complete word from anchor to anchor has no repeated point and no
internal collinear triple.

### Lemma 2.1 (exact extension criterion) -- **Theorem**

`H union I` is a distinct triple-free set if and only if all three conditions
hold:

1. `I` is disjoint from `H`;
2. no point of `I` lies on a line through two distinct points of `H`; and
3. no point of `H` lies on a line through two distinct points of `I`.

**Proof.**  A new defect contains one, two, or three points of `I`.  One new
point gives condition 1 or 2, two new points give condition 3, and three new
points are excluded by the connector-domain certification.  A defect with no
new point would already be a defect of `H`.  These cases are exhaustive.

This also settles the role of connector anchors.  They are old points in `H`,
not new interior points.  For example, a triple consisting of an anchor, an
old connector interior, and a new interior is an old--old--new site defect.  A
triple consisting of an anchor and two new interiors is an old--new--new line
defect.

### Corollary 2.2 (the `P+A+B` decomposition) -- **Theorem**

Suppose `P`, then connector interiors `A`, then connector interiors `B` have
been inserted legally and let `C` denote the pending connector interiors.  The
complete poison of a `C` word is

```text
BaseC(P) | TA(A) | TB(B) | XAB(A,B),
```

where the witness roles are exactly

```text
BaseC : collision P-C, P-P-C, P-C-C;
TA    : collision A-C, P-A-C, A-A-C, A-C-C;
TB    : collision B-C, P-B-C, B-B-C, B-C-C;
XAB   : A-B-C.
```

The remaining `C-C-C` and self-collision cases are connector-internal and are
excluded by the certified domain.  This is an equality of killed atoms or
killed words, not a disjoint decomposition of witnesses: several channels may
kill the same atom or word.

More generally, for a pending step type `s`, let `U_s` be the finite universe
of candidate site atoms and candidate-internal line atoms.  Let `Atoms_s(w)`
be the atoms used by word `w in D_s`.  Exact legality is equivalent to

```text
Atoms_s(w) intersection Poison_s(H) = empty.
```

Consequently a far-tail abstraction must cover both kinds of source:

- old endpoint pairs whose secant poisons a candidate site; and
- old singleton endpoints that lie on a line through two candidate sites.

Tracking only already visible poisoned atoms is unsound.  An endpoint whose
current atom mask is empty can form a new secant with a later active point or
can meet a different candidate-line family at the next corridor.

In the rest of this note, **endpoint** normally means an endpoint of an old
secant.  It is not restricted to a connector's two anchor points.

## 3. Exact affine and Plücker transport

Use the matrix in the realized scale-and-rotate construction,

```text
M = M_BAL3 = [ 3  0  0]
               [ 0  0 -3]
               [ 0  3 -1],       det(M) = 27.
```

Set

```text
C = cof(M) = det(M) M^(-T)
  = [ 9  0  0]
    [ 0 -3 -9]
    [ 0  9  0].
```

Here `cof` is the cross-product transport convention, not the adjugate acting
on column points.

### Lemma 3.1 (cross-product transport) -- **Theorem**

For all vectors `u,v`,

```text
(M u) cross (M v) = C (u cross v).
```

Moreover `det(C)=det(M)^2=729`, so `C` is injective over `Q^3` and over
`Z^3`.  Thus

```text
u cross v = 0  iff  (M u) cross (M v) = 0.
```

In particular, applying `M` to an old triple-free point set neither creates
nor removes collinearity among the affine images.

The Smith normal form of `C` is `diag(3,9,27)`.  Hence every component of
`C Omega` is divisible by three for integer `Omega`, while a nonzero `Omega`
never maps to zero.  This divisibility is exact algebra, but it is **not** by
itself a far-tail contraction theorem.  Primitive renormalization, translations,
new endpoint pairings, and connector corrections can reset the apparent
valuation.

### Lemma 3.2 (affine Plücker transport) -- **Theorem**

Represent an oriented affine line through `p` with nonzero, not necessarily
primitive direction `d` by the Plücker pair

```text
(d,m),                 m = p cross d,                 d dot m = 0.
```

A point `q` lies on this line exactly when `q cross d = m`.  Under the common
affine map

```text
F(x) = M x + t,
```

the same line has the exact unnormalised coordinates

```text
d' = M d,
m' = C m + t cross (M d).
```

Incidence is preserved in both directions:

```text
q cross d = m  iff  F(q) cross d' = m'.
```

One may divide `(d',m')` by the common direction gcd to recover the canonical
primitive line key.  Keeping the unnormalised pair avoids an illicit division
during symbolic transport.

### Warning 3.3 (unequal corrections destroy marginal closure) -- **Theorem**

The simple formula above applies when both endpoints receive the same affine
translation.  If two correlated endpoints instead evolve as

```text
p' = M p + alpha,       q' = M q + beta,
```

then, writing `d=q-p`,

```text
d' = M d + (beta-alpha),
m' = C(p cross d)
     + (M p) cross (beta-alpha)
     + alpha cross (M d)
     + alpha cross (beta-alpha).
```

The successor line therefore depends on the endpoint base point and on the
**joint** correction pair `(alpha,beta)`, not merely on separate marginal
types for the two address streams.  This is the algebraic reason that the
failed full-menu OSC and independent-address automata cannot be reused as a
far-secant quotient for the single realized ordered path.

The generation-two overlap in the full connector-menu closure is between
alternative connector choices.  It neither supplies this correlated quotient
nor refutes its possible existence: a concrete history selects one connector
at each gap and only jointly realizable address pairs belong in a valid
concretization.

### Lemma 3.4 (centred endpoint/line frontier) -- **Theorem**

Fix the anchor `a` of a pending corridor.  For each old point `p`, set

```text
u = p-a.
```

For each old secant through distinct old points `p,r`, set

```text
g  = canonprim(r-p),
mu = (p-a) cross g.
```

Let `E_a` be the set of centred endpoints `u` and `L_a` the set of primitive
line pairs `(g,mu)`.  If `x,y` are candidate offsets from `a`, then these two
frontiers decide every external legality atom exactly:

```text
collision at x                    iff  u = x for some u in E_a;
old point on candidate line x--y  iff  u cross (y-x) = x cross (y-x);
candidate site x on old secant    iff  x cross g = mu for some (g,mu) in L_a.
```

These are exactly the three cases in Lemma 2.1 in centred coordinates.
Recentring from `a` to `a+delta` gives

```text
u'  = u-delta,
g'  = g,
mu' = mu-delta cross g.
```

If the future centre is `a+c` before the next scale is applied, then

```text
u' = M(u-c).
```

Writing `t = gcd(Mg)`, choosing the sign `epsilon` that makes the direction
canonical, and using `C=cof(M)`, the primitive line transport is

```text
g'  = epsilon M g / t,
mu' = epsilon C(mu-c cross g) / t.
```

The Smith normal form of `M` is `diag(1,3,9)`.  Therefore a primitive `g`
has `t in {1,3,9}`.  Equivalently, without primitive normalisation,

```text
d' = M d,
m' = C(m-c cross d).
```

Inserting an actual connector updates `E` by its actual interior points and
updates `L` by every new--old and new--new line before recentering.  Thus this
frontier is an exact, correlation-preserving interface.  It does not assert
that the frontier has a uniformly finite useful quotient.

### Lemma 3.5 (exact line-offset expansion) -- **Theorem**

Let

```text
Q = [1    0      0  ]          R = Q^(-1)
    [0    1    -1/6]            = [1    0      0  ]
    [0  -1/6    1  ]              [0  36/35   6/35]
                                  [0   6/35  36/35].
```

Direct multiplication gives

```text
M^T Q M = 9Q,              C^T R C = 81R.
```

For a centred primitive line `(g,mu)`, define its anisotropic offset ratio

```text
h(g,mu) = sqrt(mu^T R mu) / sqrt(g^T Q g).
```

Primitive normalisation cancels from this ratio.  Under a common scale about
the same centre,

```text
h(epsilon M g/t, epsilon C mu/t) = 3 h(g,mu).
```

More generally, after recentering by `c` and then scaling,

```text
h' = 3 sqrt((mu-c cross g)^T R (mu-c cross g))
         / sqrt(g^T Q g).
```

Consequently, if the allowed recenter corrections in one synchronized
address transition obey

```text
sqrt((c cross g)^T R (c cross g)) / sqrt(g^T Q g) <= B,
```

then the triangle inequality gives `h' >= 3(h-B)`.  A candidate-site atom at
offset `x` can be hit only when `mu=x cross g`, hence only when

```text
h <= H_s := max over candidate offsets x and nonzero g of
             sqrt((x cross g)^T R (x cross g)) / sqrt(g^T Q g),
```

and `H_s` is a finite, exactly certifiable operator-norm bound for each finite
corridor type.  Thus a contracting shell operator is algebraically plausible
for the old-secant-to-candidate-site channel along a synchronized bounded-digit
lineage: beyond a checked threshold, offset rank moves strictly outward.

This is not a complete tail lemma.  It does not bound a jump to an unrelated
corridor centre, an old endpoint lying arbitrarily far along a
candidate-internal line, the birth of near--deep lines, deep--deep pair
creation, or the total Boolean union over all lineages.  Those omissions are
exactly the transport and envelope obligations in Requirements Q and E.

### Corollary 3.5.1 (phase-adjusted exterior escape rank) -- **Theorem under a finite synchronized phase graph**

Let `q` range over a finite directed graph of synchronized ancestral phases.
An edge `e:q -> q'` fixes a common-map descendant transition and has a sound
recentering bound `B_e` in the metric above.  Let `H_q` be the corresponding
maximum candidate-site effect threshold.  The Bellman operator

```text
(T D)_q = max over e:q->q' of (B_e + D_q'/3)
```

is a `1/3` contraction in the sup norm.  Hence it has a unique finite fixed
point `D`.  If `delta_q = h-D_q`, then every represented common-map line
transition satisfies

```text
delta_q' >= 3 delta_q.
```

Indeed, `h' >= 3(h-B_e)` and `D_q >= B_e+D_q'/3`, so
`h'-D_q' >= 3(h-D_q)`.  Primitive normalization does not change `h`.  Choose

```text
L > max_q max(0,H_q-D_q).
```

For `0 < delta_q < L`, define

```text
r_q = ceiling(log_3(L/delta_q)).
```

Either the successor is already outside every phase's effect threshold, or
`r_q' <= r_q-1`.  This gives a genuine strict escape rank for the
**exterior** `delta>0` block while retaining a line through any temporarily
zero-effect phase.

This theorem does not make the far state finite.  The Bellman core
`h <= D_q` may contain infinitely many integer lines, and exterior births can
have positive `delta` arbitrarily close to zero.  A uniform finite-rank
certificate still needs a separate gap statement: every newly born residual
line is either assigned to a uniformly finite promoted core or has
`delta >= epsilon > 0`.  No such Diophantine gap is proved.  If the sharp
calculation gives `D_q >= H_q` in all relevant phases, the entire effectful
region lies in the unresolved core and this exterior rank supplies no
availability-grade reduction.

### Lemma 3.6 (the only rational periodic direction) -- **Theorem**

The `x` axis is the only rational projective direction fixed by a positive
power of `M`.  Indeed, `M` has eigenvalue `3` on that axis.  Its `yz` block

```text
B = [0 -3]
    [3 -1]
```

has eigenvalues `3 exp(plus-or-minus i theta)` with `cos(theta)=-1/6`.
Niven's theorem implies `theta/pi` is irrational.  Hence no positive power of
`B` has a real eigendirection, and no mixed `x`--`yz` vector can be an
eigenvector of a power of `M`.  The same conclusion holds for canonical
primitive directions because projective periodicity would give a rational
eigenvector of that power.

Therefore, under pure common scaling with no recentering or new-point
injection, a rational direction other than the `x` axis can hit any one fixed
rational candidate direction at most once: two hits would make the target
direction projectively periodic.  This makes `x`-parallel lines the first
exact resonance class to test or promote.  It is not a complete endpoint rank,
because recentering changes an endpoint direction and new near--deep pairs
inject new lines.

### Lemma 3.7 (phase-free finite x-line core under bounded ancestral prefixes) -- **Theorem**

Fix the canonical x-parallel direction `g=e_1`.  Relative to a corridor anchor
`a`, an x-line is determined by the integer lateral offset

```text
zeta=(p_y-a_y,p_z-a_z) in Z^2,
mu=(0,zeta_z,-zeta_y).
```

For a child slot whose parent-word prefix is `c`, primitive normalization of
`M g=3g` gives the exact recurrence

```text
zeta' = B (zeta-c_perp),       B = [0 -3; 3 -1].
```

Let `h` be the lateral norm from the x-specialization of Lemma 3.5:

```text
h(y,z)^2 = (36y^2-12yz+36z^2)/35.
```

Then `h(Bv)=3h(v)` and

```text
h(y,z)^2 >= (6/7)(y^2+z^2).
```

If every connector word has length at most `m` and every menu step has lateral
coordinates in `[-2,2]^2`, every proper prefix and every candidate interior
site obeys

```text
h(c_perp) <= C_m := 2(m-1)sqrt(12/5).
```

Set `D_m=3C_m/2`.  The triangle inequality gives

```text
h(zeta') >= 3(h(zeta)-C_m).
```

Hence `h(zeta)>D_m` implies `h(zeta')>D_m`; the exterior is forward invariant
under **every** bounded-prefix ancestral transition.  Since every candidate
site has `h<=C_m<D_m`, an exterior x-line cannot poison the current corridor
or any synchronized descendant.  The promoted core

```text
X_m = {zeta in Z^2 : h(zeta)<=D_m}
```

is finite.  Indeed `y^2+z^2 <= (7/6)D_m^2`.  For the actual effective domains
`m<=5`, this places `X_m` inside `[-20,20]^2`, so there are at most 1,681
lateral offsets per retained corridor phase.  Even the optional length-eight
fallback would give the coarse bound `[-35,35]^2`, or 5,041 offsets.

This closes only fixed-direction **line geometry** under synchronized
parent-to-child prefix controls.  It does not close births.  A proof state must
also retain lateral endpoint occupancy `n(zeta) in {0,1,2}`: inserting a
distinct point into an occupancy-one fibre creates a new x-line, while an
occupancy-two fibre poisons the insertion.  Collision information must be
carried exactly or discharged separately.  The recurrence is injective, so
capped occupancy is sufficient for the x-only collinearity channel along a
legal synchronized history, but the present artifacts do not supply its
universal ordered update.

Nor does this lemma cover a same-level scheduler jump to an unrelated anchor.
Such a recentering need not be a bounded connector prefix and can bring an
unrepresented singleton or line into the new corridor frame.  The safety game
still needs a sound inherited-tile/address interface proving that every such
injection is represented.  Non-x directions also remain outside this lemma;
for arbitrary primitive `g`, bounded `h(g,mu)` does not imply finitely many
line keys (for example every `(g,0)` has `h=0`).

## 4. Concrete histories and the required correlated quotient

Everything from this section through Section 8 is an **open certificate
obligation** unless explicitly identified as a graph-theoretic implication.

A concrete ordered history `h` must retain at least:

- the single realized path factor and its actual connector word at every
  already filled gap;
- the placement/activation order, birth level, parent identity, and address of
  every active point;
- the pending corridor, its step type, inherited-tile phase, and anchor frame;
- every current and age-one endpoint needed by the exact retained frontier;
  and
- every age-at-least-two endpoint and correlated endpoint pair, unless a
  separately proved forward-invariant irrelevance test excludes it.

For a pending corridor `xi`, write `F(h,xi)` for this concrete deep endpoint
and secant frontier.  Membership may not be defined as "has nonzero effect at
`xi`": currently inert endpoints can reactivate.

### Requirement Q (correlated type quotient used by the certificate) -- **Open at availability grade**

Exhibit a finite set `T`, a type map `pi_xi(h,z)`, type concretizations
`Conc^T_xi(t)`, a
finite effect map `Eff_xi(t) subset U_s`, and, for every admissible retained
transition `(q,w)`, a finite universal relation
`Post^T_(q,w) subset T x T`.
They must satisfy all of the following.

1. **Total coverage.**  For every admissible concrete history represented by
   retained state `q`, every object of `F(h,xi)` has a type in `T`.
2. **Honest concretization.**  `Conc^T_xi(t)` is a set of triples
   `(h,xi,z)`, not a Cartesian product of independently possible endpoint
   addresses.  If `z` is a secant, its two endpoints occur together in the
   same realized history with their actual order and connector choices.
3. **Effect soundness.**  Every site or line atom poisoned by a concrete object
   in `Conc^T_xi(t)` belongs to `Eff_xi(t)`.  The effect map may overapproximate,
   but it may not omit an incidence.
4. **Universal transport.**  For every `(h,xi,z)` in `Conc^T_xi(t)`, every
   admissible exact action `w`, and every resulting concrete successor
   `(h',xi')`, every transported or newly relevant descendant `z'` is covered
   by some `t'` with `(t,t') in Post^T_(q,w)`.
5. **Pair closure.**  Universal transport includes collision,
   endpoint-on-candidate-line, old secants, every secant made from a deep
   endpoint and a retained/current point, and every required deep--deep pair.
   These are the `near--deep` and bilinear pair-creation channels.
6. **Noncircular policy closure.**  A quotient may be synthesized jointly with
   a policy and need only cover the transitions selected by that policy, but
   the certificate must independently prove seed inclusion, exact legality,
   and closure of every selected concrete successor.  Merely declaring that
   omitted histories or transitions are "unreachable under the desired
   policy" is circular.  If the quotient claims soundness for additional
   actions, their universal `Post^T` relations must also be checked.
7. **Transition congruence.**  Types identified by `pi` have the same certified
   successor overapproximation for every retained transition on which the
   quotient claims to be sound.  Agreement on one frozen prefix is not enough.

The seven soundness clauses alone do not make existence difficult.  A
one-element `TOP` type whose concretization contains every object, whose effect
is the whole atom universe, and whose successor is itself is a finite sound
overapproximation.  It is also useless because it kills every connector.  The
open assertion is the existence of an **availability-grade** finite quotient:
one simultaneously fine enough to support Requirement E and to leave a legal
connector in Requirement G.  Directions, moments, activation ranks, address
correlations, and partner identities can all grow with level, so finiteness of
the candidate atom universe gives no reason that such a useful quotient exists.

### Exact one-generation trace verdict -- **Finite computation, not Requirement Q**

`far_secant_future_trace.py` joins the pinned deep endpoint closure back to the
single realized ordered path without taking an address cross-product.  It
retains 42 actual L7 parent states, their actual selected connector words, and
all 146 consecutive L8 child slots with their actual L8 connector choices.
The exact full tagged-endpoint mask is strictly larger than the direct
endpoint/carried-line mask in 61 child states.  Those missing joins use 57
distinct partner points, including 24 connector points born in L8.  Even after
retaining mode, step, actual connector choice, and the direct mask, the tested
projection has two noncongruent classes with different full killed-word masks.
Thus that particular direct-frontier projection is unsound on the recorded
orbit.  The exact centred projection is not refuted only because all 146 child
states are singletons.

`far_secant_birth_shell_trace.py` then preserves the stored correlated
birth/spatial-shell commitments.  Across the same trace it has 94 exact
descriptor terms: 53 inherited-partner, 29 current-level-partner, and 12
direct.  The artifact supplies exact aggregate full, direct, partner-total,
and partner-priority-remainder masks.  It supplies inherited/current component
masks as exact monotone OR expressions, but not their separate aggregate raw
bitsets or union cardinalities.  Every repeated child class under the tested
exact-term, count, and presence keys is a zero-poison class; all nonzero states
are unrepeated.  All 42 enriched ordered parent transition states are
singletons, while a diagnostic parent key omitting child poison states and
child choices is noncongruent in two classes.

These computations prove the need for endpoint-to-other-point join data and
show that the present L7-to-L8 horizon supplies no nonzero stabilization
evidence.  They do not define a universal `Post^T`, cover alternate connector
histories, observe `sig_2`, or prove a contraction.  A second generation needs
selected L9 connectors and their exact prefix-aware partner closure; merely
scaling the L8 anchors is insufficient.

### Exact x-parallel resonance verdict -- **Finite computation and a concrete obstruction**

`x_axis_far_secant_resonance.py` exhaustively replays the pinned realized
L5--L8 paths in both the gate and pipeline stitch orders.  It scans all
131,097 corridors per order against the effective 12,537,146 connector words,
with no endpoint or distance cutoff, for the old--old--new channel in which a
candidate interior site lies on an active x-parallel secant.  It then closes
every actual selected descendant lineage from each strict-effect seed through
L8, including intermediate states with an empty current x-line mask.

The exact closed graph has 11,154 strict-effect seeds, 35,220 nodes, and
27,103 transitions.  Its transition census is

```text
effect -> effect   3,002       effect -> zero   8,109
zero   -> effect      35       zero   -> zero  15,957.
```

Thus current-mask forgetting is concretely unsound: 35 selected transitions
reactivate a retained line after a zero-effect state.  Among actual descendant
paths of lengths one, two, and three, the checker finds respectively 12, 2,
and 22 returns to the exact effect key consisting of parent step, relative
lateral coordinate, ordered strict site offsets, and the resulting exact
killed-word mask.  Six period-three records also return to the same recorded
selected connector action.  Gate and pipeline contain the same physical
returns, so after identifying the two schedules these are 18 physical
effect-key returns, including three physical effect-and-action returns.

These are exact finite projected cycles.  They refute a strict residual DAG
rank on that effect key; adjoining the recorded action is still insufficient.
They do **not** prove that source and target have congruent infinite futures,
an infinite policy cycle, or a connector jam.  Physical line identity also
does not separate the three action returns: each source and target carries the
same inherited line and endpoint identities in the recorded self-similar
descent.  Exact shell age separates this depth-three sample only by using an
unbounded field.  The smallest clean bounded discriminator found in this
finite audit is the two-generation ancestor step, but it has not been shown
transition-congruent and may recur later.  A universal proof must refine by
honest lineage/phase, promote this resonant block, or control it with a
non-strict contraction.  The tested selected-word/slot phase key is not a
congruence either: 4,396 of 12,781 phase classes have multiple observed effect
posts.

The audit is deliberately one-channel.  It omits non-x secants,
old-on-candidate-internal-line defects, alternate connector choices, L9 and
later levels, and the union with all other poison.  None of its recorded
selected words is killed by the complete x-line union, but that is not a
connector-availability result.  The compact certificate is
`x-axis-far-secant-resonance-summary.json`; the 121,520,326-byte raw artifact
was reproduced exactly after deleting its elapsed-time field.

### Exact Bellman-core verdict -- **Finite computation, not a universal rank**

`x_axis_bellman_barrier.py` evaluates the sharp phase-dependent Bellman
barrier on the finite observed x-line graph above.  Of 124 observed step
phases, 77 satisfy `H_q <= D_q`; their complete effect interval is therefore
inside the noncontracting core.  Forty-one nonterminal phases and six
observed-terminal phases satisfy `H_q > D_q`, but this classification alone
does not say that a realized line occupies the exterior interval.

`x_axis_barrier_node_join.py` then joins the barrier back to all 35,220 actual
lineage nodes.  Among the 11,154 strict-effect nodes, 11,107 are in the core
and only 47 are exterior.  Among the 24,066 currently latent nodes, 2,096 are
in the core and 21,970 are exterior.  All 13,826 recorded transitions out of
an exterior node stay exterior and satisfy the exact lower bound

```text
delta_target - 3 delta_source > 0.
```

There is no observed exterior-to-core re-entry.  Thus Corollary 3.5.1 behaves
exactly as intended on this finite orbit.  However, every one of the 36
effect-key return sources and all six effect-and-action return sources lie in
the core.  The computation therefore relocates, rather than closes, the
obstruction: the remaining x-axis task is a universal finite promotion or
other availability-grade control of the Bellman core.  More exterior shell
fitting cannot discharge the witnessed returns.  The compact certificates are
`x-axis-bellman-barrier-summary.json` and
`x-axis-barrier-node-join-summary.json`.

`x_axis_core_promotion_probe.py` tests the smallest geometric promotion on the
same pinned core.  Its 13,203 core occurrences collapse to 1,312 exact states
`(step,z)`: 748 have a strict effect and 564 are currently latent.  The complete
combined killed-word mask is congruent in every state.  After retaining the
actual connector word and ordered slot, 13,277 core-source transition
occurrences collapse to 5,542 action/slot-labelled edges and 1,645 whole-action
bundles, again with no observed successor conflict.  The 36 effect-key return
occurrences map to 15 geometric states and the six action returns map to three.

This is useful compression, not Requirement S.  The strict-secant versus
endpoint-collision decomposition is noncongruent in 92 geometric states; 575
states merge multiple concrete endpoint pairs; and the source artifact has no
singleton-occupancy or new-line-birth edges.  It also observes only 2,882
step/selected-word pairs out of 12,537,146 domain words.  A universal
x-parallel promotion must therefore scan every action/prefix control, compute
the full-domain barrier, enumerate its finite integer core, and add honest
ordered occupancy-`0/1/2` insertion transitions with exact collision data.
The compact certificate is `x-axis-core-promotion-probe-summary.json`.

## 5. Genuine recurrence, promotion, and the residual DAG

Form the directed graph of the universal type relation after Requirement Q is
proved.  A sampled edge graph, or an edge graph from only one recorded history,
is not this object.

A **genuine recurrent component** is a reachable cyclic SCC of the universal
graph containing a correlation-compatible cycle with a nonempty concrete
realization.  A cyclic SCC of a sound overapproximation may be spurious, but it
must be treated as potentially recurrent until a refinement proves that it is
not realizable.  An age-erased point-identity self-loop alone does not prove an
effectful projective incidence cycle.  Conversely, a potential cycle in a
sound overapproximation cannot simply be discarded because the sampled
history did not realize it.

### Requirement S (promotion) -- **Open**

For each reachable cyclic SCC, do one of the following with a checkable proof:

1. refine it away as concretely unrealizable;
2. promote the entire unresolved component, including enough endpoint and
   pair data to compute all of its future effects, into the exact retained
   noncontracting state.

For a conservative certificate, every cyclic SCC not discharged by item 1
must be promoted.  Calling a component "old", "far", or "usually inert" is
not a discharge.  A separately proved common Lyapunov contraction could
replace promotion, but then that component belongs to an additional
contraction-controlled block; it is not part of the residual DAG asserted
below.

The finite x-axis audit supplies an explicit warning for this requirement.
Its period-one through period-three effect-key returns are witnessed cycles in
that frozen graph, and three physical period-three returns survive after
adjoining the recorded action.  They are not automatically genuine cycles in
the universal quotient because future congruence is unproved, but no candidate
quotient may assign them a strict rank merely from the returned fields.  It
must refine, promote, or contractively retain them.

Promotion is not merely a relabelling operation.  The promoted endpoint and
pair population must itself have a uniformly finite exact representation and
closed successor rule.  If an SCC requires unbounded exact data, promotion
exposes an obstruction to this finite-state architecture rather than solving
it.

### Lemma 5.1 (residual rank after promotion) -- **Conditional theorem**

If `T` is finite and all remaining reachable cyclic SCCs have been removed by
Requirement S, the residual type graph is a finite DAG.  Define

```text
rho(t) = maximum length of a directed path beginning at t.
```

Then every residual edge `t -> t'` satisfies `rho(t') < rho(t)`.  Thus an
individual residual lineage has uniformly bounded length.

This is only a graph theorem.  It says nothing until the quotient and its
universal edges are sound.  It also does not bound the total tail by itself:
new cohorts enter, one object may branch into many descendants, and pair
formation can be nonlinear.

## 6. Ranked cohort envelope

Choose a macrotransition clock on which the common rank strictly decreases.
Objects that persist through many same-level stitches without such a decrease
belong in the retained state or require a finer clock/state.  Let `z_n(r,t)`
bound the multiplicity, weight, or Boolean presence of residual type `t` of
rank `r` immediately before macrotransition `n`.  The choice of arithmetic must
come with a proved map from the envelope to poisoned atoms or killed words.

### Requirement E (uniform switched envelope) -- **Open**

For every retained safe state `q` and admissible action `w`, certify a monotone
recurrence of the form

```text
z' <= b_(q,w) + A_(q,w) z,
```

or a stronger explicitly stated nonlinear recurrence, such that:

- `b_(q,w)` covers every age-one-to-age-two injection and every newly born
  residual object;
- `A_(q,w)` covers all transport, branching, atom changes, near--deep
  generation, and deep--deep generation;
- every nonzero entry sends rank strictly downward; and
- the bound holds jointly for every switching sequence allowed by the retained
  safety game.

With a common strict rank, all old-cohort products longer than the maximum rank
are zero.  For transitions indexed forward by
`z_(n+1) <= b_n + A_n z_n`, the exact forward expansion begins

```text
z_k <= b_(k-1) + A_(k-1) b_(k-2)
       + A_(k-1) A_(k-2) b_(k-3) + ...
       + A_(k-1) ... A_0 z_0.
```

If injections and branching are uniformly bounded, and products longer than
rank `R` vanish, a finite envelope can in principle be certified by taking the
supremum of the last `R` injection terms in this correctly ordered expansion
over every allowed switching string.

Equivalently, one may verify `b_(q,w)+A_(q,w) z_bar <= z_bar` for every allowed
transition.  Separate spectral radii for separate matrices do not suffice for
a switched system.

If a secant is reconstructed from independently bounded endpoint populations,
the recurrence generally contains a bilinear term.  It may be replaced by a
linear `A z` term only after joint endpoint-pair types or another sound
linearisation have been carried.  Ignoring that term is exactly the unsound
independent-address shortcut.

Finally convert `z_bar` to a sound finite tail mask

```text
Tail_xi(q,z_bar) subset U_s
```

that contains the effect of every concrete residual represented by the
envelope.  A scalar bound on the number of endpoints, shells, or incidences is
not useful unless this conversion proves which connector atoms or words may be
killed.

### Lemma 6.1 (Boolean nilpotent tail transfer) -- **Conditional theorem**

Suppose residual objects have a finite joint-address base type `tau` and a
rank in `{1,...,R}`.  Retain a Boolean presence variable `Z(tau,r)` even when
its current effect mask is empty.  If every selected transition has a sound
monotone transfer

```text
Z' <= b_e OR A_e Z
```

whose homogeneous edges strictly decrease `r`, then every product of `R`
homogeneous transfer operators is zero under arbitrary allowed switching.
Consequently the current residual poison is the exact Boolean OR of effects
from at most the last `R` sound birth cohorts after applying their permitted
transfers.  This handles overlap without converting witness counts into a
false damage bound.

The premise is strong.  `b_e` must include new connector points and all
old--new joins, and `A_e` must transport latent zero-effect tokens.  If old
secants are reconstructed from endpoint marginals rather than carried as
joint types, a bilinear correlated-pair term is required.  A BDD or monotone
antichain can compress these variables, but current-mask inclusion is not a
sound domination order; domination must also simulate every future latent
successor.

## 7. Combined nonfatality and greatest fixed point

Let a finite abstract state `q` contain the exact retained ordered-path state,
all promoted recurrent data, and the certified residual envelope.  Let
`Hist(q)` be its sound set of concrete histories.  It may be policy-specific
provided seed coverage and selected-action closure are independently proved.
For its
pending step `s(q)`, define the sound union

```text
Poison(q) = Near(q) | Promoted(q) | Tail(q).
```

`Near` must include the complete current and age-one endpoint/line closure;
`Promoted` must include all exact recurrent SCC effects; and `Tail` must be the
Requirement E overapproximation.  There is no distance or endpoint cutoff.

Define the uniformly legal actions

```text
Legal(q) = {w in D_(s(q)) :
            Atoms_(s(q))(w) intersection Poison(q) = empty}.
```

The existential action precedes the universal concrete history.  A single
selected word for `q` must be legal for every `h in Hist(q)`; otherwise the
state must be refined or the selector must be given the missing observable
data.

For a set `X` of abstract states, define

```text
Phi(X) = {q : there exists w in Legal(q) such that
                every nonempty sound abstract successor in Post^Q(q,w) lies in X
                and the ranked envelope inequality holds}.
```

### Requirement G (nonfatal safety fixed point) -- **Open**

Produce a finitely represented set `G` and a total selector `sigma` such that

```text
q_seed in G,
G subset Phi(G),
sigma(q) witnesses q in Phi(G) for every q in G.
```

Equivalently, certify that `q_seed` belongs to the greatest fixed point
`nu X.Phi(X)`.  Expanded into concrete quantifiers, the required statement is

```text
there exist finite certificate data
    (Q,T,pi,Conc^T,Hist,Post^T,Post^Q,Eff,rho,z_bar,G,sigma)
such that for every q in G and every h in Hist(q):
    sigma(q) is an exact legal connector for h; and
    every nonempty q' in Post^Q(q,sigma(q)) belongs to G; and
    for every concrete successor h' produced by that connector,
        some sound q' in Post^Q(q,sigma(q)) lies in G and contains h'.
```

The proof of legality uses Lemma 2.1 and effect soundness, not a sampled
survivor fraction.  Requiring `Post^Q(q,w) subset G` closes abstraction
nondeterminism.  `Hist`, the selected-action `Post^T`, `Post^Q`, and `sigma`
may be synthesized jointly, but seed inclusion and all selected concrete
successors must then be verified rather than assumed from the desired policy.

## 8. Conditional theorem chain

### Theorem 8.1 (what would make the construction unconditional) -- **Conditional**

Assume the connector domains are internally certified, the finite seed is
valid, every selected connector contains at least two menu steps, and
Requirements Q, S, E, and G are proved for every retained scale/tile phase and
every pending step type.  Then the scale-and-rotate scheme produces valid
finite triple-free walks of unbounded length.

**Proof chain.**

1. Lemma 3.1 preserves the triple-free inherited anchor skeleton under
   `M_BAL3`.
2. At each stitch, Requirement G selects a word outside the combined exact
   near, promoted, and sound residual poison.
3. Lemma 2.1 therefore proves that inserting its interiors preserves
   distinctness and triple-freeness.
4. Universal `Post^T` and `Post^Q` closure and the envelope inequality return the concrete
   successor to `G`; induction handles every later stitch and level.
5. Every old edge is replaced by a connector with at least two steps, so walk
   length at least doubles at each scale.  For the present radius-two menu this
   premise can also be checked directly: every nonzero menu step `s` satisfies
   `||M_BAL3 s||_infinity >= 3`, while one menu step has infinity norm at most
   two, so no scaled edge can be bridged by a one-step connector.  The
   resulting finite walks therefore have unbounded length over the fixed
   finite step menu.  Their point sets need not be nested.  The finitely
   branching tree of legal finite step words nevertheless has nodes at
   arbitrarily large depths, so König's lemma supplies an infinite legal
   branch.

This theorem is not presently applicable because Requirements Q, S, E, and G
are open.  Proving only one-prefix nonfatality, or producing another record
finite walk, does not establish any of them.

## 9. Exact selected-horizon L9 age-two audit

`l9_anchor_age2_precursor.py` applies `M_BAL3` to the completed selected L8
path, treats its 311,738 images as the initial L9 anchor skeleton, and promotes
the three tagged L7 connector points from age one to age two.  It follows the
actual correlated lineage `42 -> 146 -> 488`, checks 90 pending connector
domains containing 8,530,195 words in total, and uses every L9 anchor as a
possible partner without an endpoint or distance cutoff.  Its exact roles are:

```text
tagged endpoint collides with a candidate site;
tagged endpoint lies on a line through two candidate interiors;
candidate site lies on a secant through the tagged endpoint and another L9 anchor.
```

The result is nonempty: 58 of the 488 actual tagged lineage states poison at
least one word.  Thirty-nine effectful states descend from old--old source
roles and 19 from the previous old--new source role.  At the distinct-corridor
level, the direct tagged-endpoint channel kills 4,130 word occurrences and
joins with other L9 anchors kill 219,776; their exact union kills 223,786.
Partners born at L6, L7, and L8 all contribute.  A direct raw rescan of the
largest positive mask, over all 501,044 words in its domain, reproduces its
113,998-word union exactly.  Literal age-two incidence-inertness is therefore
false.

This is not a full L9 legality computation.  No L9 connector interior has yet
been selected or inserted, so the audit omits current-level connector points,
their new joins, alternate histories, untagged deep endpoints, later levels,
and the union with every other poison source.  The smallest tagged-component
residual is 2,413 of 2,570 words, but that is not a connector-availability
floor for the real L9 prefix.

`l9_age2_transition_stabilization.py` tests increasingly rich observed keys:
actual source mode and step, selected L8 parent word and slot; then the exact
direct mask; then the sparse exact partner-birth masks; then exact partner
identities.  The first two projections have respectively five and four
noncongruent classes.  The latter two have no noncongruent repeated effectful
class only because all 58 nonzero states are singletons; their repeated classes
are zero-poison states.  At the enriched L7-parent layer, the two repeated
classes are noncongruent under every tested refinement.  Hence the apparent
fine-key stabilization is vacuous and no transition quotient is established.

These are exact witnesses on one selected horizon, not the universal
`Post^T` graph of Requirement Q.  The compact certificates are
`l9-anchor-age2-precursor-summary.json` and
`l9-age2-transition-stabilization-summary.json`.

## 10. Failure modes a certificate must explicitly exclude

1. **Independent address streams.**  Combining endpoint types that never
   coexist on one realized ordered path manufactures false pairs and can also
   hide necessary correlations.
2. **Current-mask forgetting.**  An endpoint with zero present effect can
   reactivate after affine transport or pairing with a new active point.
3. **Mode preservation.**  A site witness can become a secant source or an
   endpoint-on-line witness; the original atom need not survive.
4. **Scalar shell decay.**  Shell number or owner distance is not monotone, and
   near--deep generation can return an outer endpoint to a near candidate
   effect.
5. **Valuation-only descent.**  `C Omega` gains a factor of three, but affine
   corrections, primitive normalisation, and new pairs can reset valuation.
6. **Sampled SCCs.**  Tarjan on one recorded history proves recurrence only in
   that finite witnessed graph, not in a universal transition quotient.
7. **Unpromoted resonance.**  A reachable effectful cycle gives no strict DAG
   rank and must be refined, contractively controlled, or retained exactly.
8. **Linearising pair creation without proof.**  Deep--deep and near--deep
   secants can introduce bilinear population terms.
9. **Separate-matrix contraction.**  Individual spectral radii below one do
   not imply contraction under arbitrary allowed switching.
10. **Damage counts without masks.**  Bounds on witnesses or endpoints do not
    imply a surviving word unless their union is soundly projected to the
    finite connector atom/word universe.
11. **Unproved policy reachability.**  A policy-specific abstraction is
    allowed, but declaring abstract states or omitted transitions unreachable
    is circular unless seed inclusion and every selected concrete successor
    are independently covered.
12. **Finite-depth closure.**  A positive two- or three-stitch computation at
    one frozen prefix is not successor closure and supplies no induction over
    levels.

## 11. Smallest honest next certificate

The next symbolic target is not another scalar shell fit.  It is:

1. treat the exact 10-leaf frozen-prefix response partition, including its
   common fourth action `[0,3,4]` and five selected fifth actions, as candidate
   predicates; replay it at additional prefixes/levels and test successor
   congruence and refinement stabilization without assuming either;
2. keep the complete current/age-one endpoint frontier and actual connector
   choices in the retained ordered state;
3. extend the selected L9 horizon by inserting its actual connector interiors,
   and close every tagged/current and current/current join before treating the
   observed age-two masks as complete poison;
4. refine or promote the x-axis Bellman core, which contains 11,107 of the
   11,154 observed strict effects and every observed return source: extend the
   observed 1,312-state geometric collapse to all 12,537,146 actions, then add
   singleton occupancy, collision, and line-birth transitions; prove that
   universal core representation or exhibit an unbounded compatible core
   orbit;
5. construct candidate finite point/Plücker/address types and their universal
   effect-labelled `Post^T` relation;
6. refine or promote every unresolved cyclic SCC, including the witnessed
   x-resonant returns;
7. certify a common residual DAG/escape rank and switched cohort envelope; and
8. run the exact connector-word nonfatality test inside the resulting greatest
   fixed point.

Failure to find a finite transition-congruent quotient is a legitimate
obstruction, not a missing implementation detail.  A reachable compatible
effectful SCC that cannot be absorbed into a finite retained state is the
strongest likely counterexample to this proof architecture.
Concretely, the dangerous object is a jointly realizable endpoint pair whose
secant follows a bounded affine-radix orbit inside the Bellman core, can remain
zero-effect for arbitrarily long intervals, and later reactivates with a future
depending on unbounded correlated address data.  An integral x-parallel cycle
is the simplest instance; a nonperiodic bounded orbit in the untreated full
difference closure would be more serious because it could require infinitely
many promoted states without presenting a short projective cycle.
