# Exact far-secant birth operator and the zero-ghost obstruction

**Status (2026-07-18): theorem-level operator specification and obstruction;
not a reachable-birth bound, availability certificate, or proof of Erdős
#193.**  This note starts from `LATENT-REENTRY-OBSTRUCTION.md`.  It explains
exactly what a shell transfer would have to carry, proves that geometric shell
decay cannot control the latent `L_n` family, and states a quantitative
reachable-birth envelope which would suffice.

The old fatal-mass profiles are evidence only.  In particular, the observed
shares

```text
19%, 35%, 26%, 12%, 6%, 2%, 0.5%, 0%
```

across successive spatial shells are not coefficients of a sound transfer
operator.  The masks overlap, their sources change with the cursor, and an
exact incidence has full Boolean strength regardless of endpoint distance.

## 1. Exact objects and the killed-word functional

Fix one concrete ordered history `h` and its pending corridor `q`, translated
so that the corridor anchor is zero.  Let `s(q)` be the step type.  The finite
atom universe is the disjoint union

```text
U_s = V_s disjoint-union A_s,
```

where `V_s` contains candidate site offsets and `A_s` contains the affine
lines determined by pairs of candidate interiors.  For every connector word
`w in D_s`, let `Atoms_s(w)` contain its site atoms and its candidate-internal
line atoms.  For an atom `a`, put

```text
Words_s(a) = {w in D_s : a in Atoms_s(w)}.
```

The exact far frontier has two kinds of persistent token.

* An endpoint token is `(id,birth,address,u)`, where `u` is its exact centred
  integer position.  The identity, birth data, and correlated address are
  logically needed even when only `u` is displayed.
* A secant token is `(id_1,id_2,birth,address,g,mu)`, where `g` is the
  canonical primitive direction and `mu=u_1 cross g`.  Its address is the
  joint minimal address tree of the two endpoints, not a product of two
  marginal address languages.

Write these exact sets as `E_q(h)` and `L_q(h)`.  Their current atom effect is

```text
Eff_q(E,L) =
    {x in V_s : u=x for some u in E}                         # collision
  union {x in V_s : x cross g=mu for some (g,mu) in L}       # old-old-new
  union {lambda(x,y) in A_s :
             u cross (y-x)=x cross (y-x) for some u in E}.   # old-new-new
```

Consequently their exact killed-word mask is the monotone union

```text
Kill_q(E,L) = OR_(a in Eff_q(E,L)) Words_s(a).               (1.1)
```

Equation (1.1), rather than a witness count or a sum of shell masses, is the
object which availability must avoid.  A BDD or antichain may represent this
union, but it may merge two token sets only under a future-simulation order;
current-mask inclusion is not such an order.

## 2. Exact insertion, birth, transport, and cursor import

Suppose the selected word inserts the finite interior set `I_w`.  Before any
change of corridor frame, the exact frontier update is

```text
E+ = E union I_w,

L+ = L
     union {line(i,e) : i in I_w, e in E}
     union {line(i,j) : i,j in I_w, i<j}.                   (2.1)
```

Thus every old--new line, including every near--deep line, is injected at the
moment its new endpoint is inserted.  Every new--new line is injected too.
There is no physical deep--deep rebirth: the line through two old endpoints
was born when the later endpoint was inserted and must have been carried ever
since.  If an abstraction has discarded that joint line frontier, then its
import operator must reconstruct

```text
{line(e,f) : e,f in E_deep, e<f},                           (2.2)
```

which is a correlated quadratic injection.  Omitting (2.2), or replacing it
by independent endpoint marginals, is unsound.

There are two elementary frame changes.

1. Along a common ancestral child slot with prefix control `c`,

   ```text
   u'  = M(u-c),
   g'  = epsilon M g/t,
   mu' = epsilon C(mu-c cross g)/t,
   t   = gcd(Mg),                         C=cof(M).          (2.3)
   ```

2. Along a same-level cursor change by the exact anchor displacement `delta`,

   ```text
   u'  = u-delta,
   g'  = g,
   mu' = mu-delta cross g.                                  (2.4)
   ```

Neither formula permits a distance cutoff.  In particular (2.4) has no
expansion or contraction at all and can import a previously invisible object
into the next finite corridor.  A state which retains only a neighbourhood of
the old cursor therefore needs an explicit import term containing every
endpoint and pair token omitted from that neighbourhood.

The concrete one-stitch operator is the following composition:

```text
T_(q,w)(E,L)
  = Import_(q,w)
      OR Reframe_(q,w)( E union I_w,
                        L union Pair(I_w,E) union Pair(I_w,I_w) ).  (2.5)
```

Here `Import` is empty only when the state has carried the complete global
frontier.  For a local state it must include unrelated-cursor endpoints,
their already born secants, and the deep--deep closure (2.2) if those secants
were not retained.  Formula (2.5) includes all direct, old--new,
deep--deep, and same-level channels before the word mask (1.1) is taken.

## 3. Exact-zero tokens are a separate, noncontracting block

For a line `ell=(g,mu)` and an actual correlated future edge string
`alpha`, let `Phi_alpha(x)` be the exact pulled-back ghost site.  Define the
zero language

```text
Zero_q(h,ell) = {(alpha,x) : mu=Phi_alpha(x) cross g}.       (3.1)
```

A line with empty current mask can have a nonempty (3.1).  The transition of
this language is exact left quotient: after choosing edge `e`,

```text
Zero_q(h,ell) restricted to words beginning with e
       = e concatenated with Zero_q'(h',T_e ell).           (3.2)
```

Hence the smallest literal zero-token state is the correlated cursor plus the
exact Pluecker pair and joint endpoint provenance.  A Boolean flag saying only
"some future zero exists" is not transition-sufficient; different zeros can
have different reveal suffixes and killed-word masks.

A sound triangular shell operator must therefore have the form

```text
Z' = LeftQuotient_e(Z) OR Zero(Birth_e) OR Zero(Import_e),
R' <= b_e^+ OR A_e R,

K' = Near' OR Kill(Z') OR Kill(R').                         (3.3)
```

`Z` contains exact-zero/right-language tokens.  `R` contains only residual
tokens for which a positive-gap rank has actually been proved.  Births in
(2.1), deep--deep reconstruction in (2.2), and unrelated-cursor imports in
(2.5) must be split between `Z` and `R` by exact predicates.  The first line
of (3.3) is Boolean transport with coefficient one; no metric contraction of
address tails changes an exact zero.  Any recurrent zero-language class must
be promoted, proved unreachable, or controlled by a separate quantitative
birth moment.

This is the sound use of a shell decomposition.  A scalar recurrence on the
observed shell word counts is not (3.3), because it has no exact-zero state,
no pair birth operator, no cursor import, and no monotone mask union.

## 4. The latent family has spacing `9^n` and constant reveal weight

Use the exact cycle and notation from `LATENT-REENTRY-OBSTRUCTION.md`:

```text
g_n=N^(2n)h,       h=(55,34,18),       N=9M^(-1),
L_n={x : x cross g_n=p cross g_n}.
```

Every `g_n` is primitive, every `L_n` is an integer lattice line, and one
complete `8 -> 16 -> 8` phase cycle sends `L_n` to `L_(n-1)`.  The following
strengthening is immediate but important.

### Proposition 4.1 (exact spacing and nondecaying reveal) -- theorem

Let `||v||_Q=sqrt(v^T Qv)`, with `M^T Q M=9Q`.  Then:

1. `N^T Q N=9Q`, and therefore

   ```text
   ||g_n||_Q = 9^n ||h||_Q.                                (4.1)
   ```

2. If `a_n,b_n` are distinct integer points of `L_n`, then
   `b_n-a_n=k g_n` for a nonzero integer `k`.  Hence

   ```text
   ||b_n-a_n||_Q >= 9^n ||h||_Q.                            (4.2)
   ```

3. After exactly `n` phase cycles, `L_n` becomes `L_0` and hits the selected
   step-8 interior `a=(-2,-2,-2)`.  Thus its revealed killed-word fraction is
   at least

   ```text
   omega := |Words_8(a)|/|D_8| >= 1/15920,                  (4.3)
   ```

   independent of `n`.  The lower bound uses only the certified selected word
   `[0,1,16]`, which contains `a`; the true atom frequency may be larger.

**Proof.**  From `N=9M^(-1)` and `M^TQM=9Q` one gets
`N^TQN=9Q`; applying this `2n` times proves (4.1).  A primitive integer
direction generates the lattice of integer differences parallel to it, so
two integer points on `L_n` differ by a nonzero integral multiple of `g_n`,
proving (4.2).  The exact all-`n` re-entry theorem proves the first sentence of
item 3.  Every word containing the hit site is killed, and the pinned step-8
domain has 15,920 words, proving (4.3).  QED.

The Euclidean and Chebyshev spacings also grow at least exponentially by norm
equivalence; more directly `(g_n)_x=55*9^n`.  Consequently a spatial shell
index grows like `2n`, while the eventual per-token word damage stays bounded
below by the fixed positive number `omega`.

### Corollary 4.2 (no decaying per-token shell weight) -- theorem

No estimate of the form

```text
eventual killed-word mass of every integer line in shell j <= C theta^j,
                                                               theta<1,
```

can hold.  Nor can a transfer potential `V` simultaneously satisfy all three
properties below on all integer secants:

```text
current killed-word mass <= V,
V(T ell) <= rho V(ell) for a phase macrotransition, rho<1,
V(newborn ell) <= B for one uniform finite B.
```

Indeed `T^n L_n=L_0`, so (4.3) gives

```text
V(L_n) >= omega rho^(-n).                                  (4.4)
```

Combining (4.1) and (4.4), a contracting potential must charge a newborn line
at least a positive power of its primitive lattice spacing:

```text
V(L_n) >= omega
  (||g_n||_Q/||h||_Q)^(log_9(1/rho)).                       (4.5)
```

Thus contraction is not impossible as formal bookkeeping.  It reverses the
naive intuition: a farther latent resonance must receive a *larger* birth
charge.  A uniform birth bound then becomes a theorem excluding all
sufficiently deep `L_n`-type births.

This corollary is geometric.  It does not prove that any `L_n` is a secant in
a reachable globally legal walk history.  That reachability distinction is
exactly where a useful theorem could still enter.

## 5. The canonical contracting operator is a future-contact moment

There is a precise contracting functional for zero ghosts, but its finiteness
is the missing theorem.  Fix `0<rho<1`.  For an exact token set `S` at a
correlated state `q`, define

```text
V_q(S) = sup over allowed correlated future strings alpha of
           rho^(-|alpha|)
           * mu_(s_alpha)( Kill_(q_alpha)(Post_alpha S) ),  (5.1)

mu_s(K)=|K|/|D_s|.
```

The supremum includes endpoint effects, carried-line effects, and the exact
union of their word masks.  It does not invent future old--new lines: those
are placed in the birth cohort of the later insertion by (2.1).  If a local
state does not carry global objects, its `Post` includes the exact imports of
(2.5).

For every allowed edge `e:q->q'`, (5.1) gives the Bellman inequality

```text
V_q'(Post_e S) <= rho V_q(S).                               (5.2)
```

It is also monotone and subadditive under union.  Moreover it is the **least**
scalar functional with these properties which dominates current killed-word
mass.  Indeed, if another functional `W` dominates current mass and obeys the
analogue of (5.2), then iteration along any length-`n` string gives

```text
mu(Kill(Post_alpha S)) <= W(Post_alpha S) <= rho^n W(S).
```

Taking `rho^(-n)` times the left side and then the supremum proves
`V_q(S)<=W_q(S)`.  Thus changing scalar norms cannot evade the birth cost
below; it can only overestimate it.

Therefore, if the aggregate
new birth/import cohort `B_e(h,w)` obeyed the reachable-history bound

```text
V_q'(B_e(h,w)) <= b                                        (5.3)
```

for every safe concrete history and selected action, the far budget would
satisfy

```text
v' <= rho v+b,             hence v <= b/(1-rho).            (5.4)
```

The `L_n` calculation shows exactly what (5.3) costs:

```text
V(L_n) >= omega rho^(-n).
```

Thus (5.3) is an exponential first-return moment bound on reachable births,
not a consequence of geometric IFS contraction.  A zero token with fixed
positive effects at arbitrarily late times has `V=infinity` and must be
promoted or excluded.  Same-level cursor edges must either satisfy (5.2) as
part of the chosen macrotransition or be included in `B_e`; silently omitting
them invalidates (5.4).

The scalar functional (5.1) is deliberately stronger than a mask-valued BDD
certificate only in its final union bound.  One may replace `mu` by a monotone
antichain of exact masks and prove that the fixed-point union misses a word.
That can exploit overlap.  It does not remove the exponentially growing
birth charge forced by a delayed exact zero.

## 6. Weakest direct quantitative envelope sufficient for availability

A geometric rate is convenient but not necessary.  The weaker condition is a
summable exact birth-cohort profile.

Choose a macroclock and attribute each endpoint to its insertion, each secant
to the insertion of its later endpoint, and every otherwise omitted object to
the cursor import at which it first enters the retained state.  Let
`F_(t,n)` be the exact killed-word mask, at macrotime `t+n`, of the cohort born
or imported at time `t`, after the actual correlated transports.  All
old--new and new--new pairs are in that cohort's injection; already carried
deep--deep pairs are not recreated.

A sufficient envelope is a nonnegative summable sequence `beta_n` such that,
for every state in the claimed invariant, every selected action, every allowed
correlated successor string of length `n`, and every ending step type,

```text
mu_(s_(t+n))(F_(t,n)) <= beta_n,             sum_n beta_n < infinity.  (6.1)
```

If current/age-one and promoted poison has normalized word mass at most
`nu_s`, then the exact union bound gives

```text
mu_s(Kill_far) <= sum_(n>=2) beta_n,

nu_s + sum_(n>=2) beta_n < 1                              (6.2)
```

as a direct connector-survivor theorem.  Absolute word counts, or an exact
BDD union which leaves a word, may replace the normalized inequality.  The
profile must be checked at intermediate stitches, not only at completed
levels.  If a macrotransition groups a whole level, its retained near state
must separately certify every stitch inside the block.

Condition (6.1) is weaker than the geometric choice `beta_n<=b rho^n`, and it
states the actual missing quantitative content with no claim that the state
space is finite.  A finite safety proof additionally needs a finite
representation and closed transition rule for the near/promoted state and for
the envelope.  Conversely, if reachable births contain an `L_n`-type cohort
for every `n` with the common reveal atom from (4.3), then `beta_n>=omega` on
an infinite subsequence and (6.1) is impossible.

## 7. Why level-uniform crowding does not imply the envelope

The existing crowding theorem counts points in bounded balls.  It does not
bound orientations of pairs whose endpoints are arbitrarily far apart.

For every sufficiently large `n`, choose one integer point `x_n` on `L_n` and
the second point `x_n+g_n`.  This two-point set is triple-free.  Its endpoints
have Chebyshev separation at least `55*9^n`, so every Chebyshev ball of radius
at most ten contains at most one of them.  It satisfies the strongest possible
fixed-radius crowding bound.  Replacing `x_n` by `x_n+k g_n` puts both
endpoints arbitrarily far from the current corridor without changing the
secant.  Nevertheless their secant is `L_n`, and after `n` phase cycles it has
the fixed positive reveal weight (4.3).

Therefore neither the old Lemma R nor the repository's stronger
level-uniform cubic crowding estimate implies (5.3), (6.1), a finite zero
right-congruence, or positive connector availability.  To obtain one of those
statements from geometry requires a genuinely two-point, direction-sensitive
reachable-history theorem--for example an exponential bound on the future
contact moment of all secants actually born by the policy.  One-point ball
counts cannot supply it.

### 7.1 Generic descendant branching is expansive -- theorem and exact census

There is also no generic contraction hidden in the connector substitution.
For either frozen lattice-`T` action channel, let `A_s` be its accepted whole
words at source step `s`, and define the nonnegative first-moment kernel

```text
B_(s,t)=|A_s|^(-1) sum_(w in A_s) multiplicity_t(w).
```

Every accepted connector has between two and five child roles.  Consequently

```text
B 1 >= 2 1,                 B 1 <= 5 1,
2 <= spectral_radius(B) <= 5.                              (7.1)
```

The lower bound follows by iteration, `B^n 1>=2^n 1`; the upper bound follows
from the infinity operator norm.  Thus no positive weighted norm makes the
**all-descendant** role transfer contract below one.  A small probability
along one prescribed address cannot be multiplied into a tail bound after all
descendant branches are restored.  If two required roles share a parent, the
exact factor is the count of whole words containing both roles, not a product
of their marginals.

The complete pinned census verifies the stronger finite contact fact on the
780-state lattice `T`: the zero-envelope avoid-source kernel has no edges,
while the ordered-envelope kernel has 67,786 edges, longest directed path 217,
and is nilpotent with exponent at most 218.  This is genuine contraction for
continuously effectful `T` contacts.  It does not cover silent Pluecker ghosts,
old--new or new--new births, same-level cursor imports, or chronological
conditioning.  Conditioning the frozen uniform action set on exact legality
can raise a rare role probability to one.  Therefore (7.1) is an obstruction
to a generic branching proof, and the nilpotent `T` result is not (5.3) or
(6.1).  The sealed computation is
`design/generic-ghost-transfer-census-summary.json`.

## 8. A local ancestry exclusion and its exact boundary

The latent spacing does yield one useful policy-independent exclusion once
the endpoint addresses are kept correlated.  Use

```text
Q(x,y,z)=x^2+y^2+z^2-yz/3,       Q(Mv)=9Q(v).
```

For the radius-two menu,

```text
S^2=max Q(menu step)=40/3,
Q(h)=4301,                        h=(55,34,18).
```

Give every level point its actual parent: an anchor `Mp` has error zero and a
proper connector interior has the form `Mp+e`, where `e` is a prefix of at
most four menu steps.  After `r` actual parent lifts,

```text
||e_total||_Q <= 2S(3^r-1),       |(e_total)_x| <= 4(3^r-1).
```

Therefore two endpoints with `r`-level ancestors `p,q` satisfy

```text
|x_x-y_x| <= 3^r |p_x-q_x| + 8(3^r-1).                 (8.1)
```

Take `r=2n`, assuming the current level is at least `2n`.  If the endpoint
pair supports `L_n`, its primitive spacing has x component `55*9^n`.
Equation (8.1) forces

```text
|p_x-q_x| >= 47+8/9^n,
```

and hence the exact integer bound

```text
|p_x-q_x| >= 48.                                      (8.2)
```

Every ordered parent edge changes x by at most two, so the two ancestors are
at least 24 ordered path edges apart.  In particular, no one connector tile,
no new--new pair in one word, no new--local-anchor pair, and no common
ancestor interval of at most 23 edges can birth an `L_n` secant.  Equivalently,
a correlated ancestor block of x-diameter at most 47 excludes the family.
The Q-norm calculation gives the slightly weaker threshold
`||p-q||_Q >= sqrt(4301)-4sqrt(40/3)(1-9^-n)`.

This is a theorem about the local birth channel, not a uniform cutoff.  The
constructor initially contains every current-level anchor, and (2.1) pairs a
new interior with every such global endpoint.  Zero-envelope acyclicity does
not restrict that partner, fresh-yz excludes only x-parallel births, and a
same-level cursor translation has coefficient one.  Thus a dangerous pair may
have ancestors more than 23 edges apart or may be imported from another
cursor.  For levels below `2n`, only a finite seed/whole-walk diameter check is
available.

The exact additional hypothesis which would close this family is:

> **RCA-23.** Every reachable secant whose zero language contains an `n`-fold
> latent `8 -> 16 -> 8` suffix has correlated endpoint parents `2n` levels
> back in one ordered interval of at most 23 edges (or x-diameter at most 47),
> while every cross-tile birth and cursor import is either covered by the same
> assertion or separately retained and excluded.

No current invariant proves RCA-23.  The calculation localizes the missing
proof to joint global endpoint addresses; it does not remove it.

### 8.1 Grandfathered invariant-cone freeze -- conditional policy theorem

There is a stronger inductive guard for the **two named** latent spectra.  For
a direction `d=(r,y,z)`, put

```text
q(d)=3y^2-yz+3z^2,
F_11(d)=3q(d)-11r^2,
F_348(d)=275q(d)-348r^2.
```

Direct substitution gives

```text
F_j(Md)=9F_j(d).                                      (8.3)
```

Homogeneity shows that primitive normalization preserves the zero predicate,
and same-level cursor translation does not change direction.  Fix a valid
finite base walk `W_0`.  At every later insertion impose the global guard

```text
F_j(i-p) != 0     for each new interior i and every old point p,
F_j(i-i') != 0    for every two new interiors in the same word,       (8.4)
```

for `j in {11,348}`.  Then every future `F_j=0` physical secant is exactly the
scaled descendant of a base secant.  Indeed anchor--anchor differences are
`M(p-q)` and inherit cone membership by (8.3); every other pair has a later
connector endpoint and is tested at its birth by (8.4).  Cursor imports can
reveal an old physical line but cannot create one.

This **grandfathered cone-freeze lemma is a theorem conditional only on using
the guard**.  It does not prove that a legal word satisfying (8.4) always
exists.  The audited L5 path cannot be used as evidence for that survivor
claim: among its 34,175,778 pairs there are 758 cone secants, of which 512 are
connector-born.  It may instead be declared the finite base and the guard
started at L6, with all 758 base lines promoted and still included in exact
legality.

The finite list of 13 named rays from the L5 diagnostic is not an inductive
replacement for (8.4).  If `g_(n+1)=N^2 g_n`, then

```text
M^2 g_(n+1)=81 g_n;
```

the first ray omitted by a finite-diameter list may enter the list one
macrocycle later.  The invariant cone avoids that error.  For a base direction
already in one named bi-infinite orbit, non-x projective aperiodicity gives a
unique exponent and hence a finite remaining countdown; a base cone direction
outside that orbit never enters it.  Exact affine moments can remove putative
matches but must still be carried.

This closes only the two named families, conditional on connector
availability under (8.4) and exact handling of the finite promoted base lines.
No theorem says these cones exhaust recurrent zero languages.  The 768-state
non-x control SCC and the untreated affine carry make such an exhaustiveness
claim unjustified.  An unconditional proof still needs a classification of
all recurrent zero classes or a summable birth bound for everything outside
the promoted cones.

The first finite guard test is now complete and independently audited.  From
the exact 2,458-anchor L4 skeleton, the guarded L5 selector completes all 2,457
stitches.  Its independent checker reproduces all 4,211 cone rejections and
scans all 34,407,660 terminal pairs of the 8,296-point output.  Exactly 246
target-cone pairs remain, every one inherited anchor--anchor; there is no
connector-born target-cone secant and no collinear triple.  This is an exact
finite validation of (8.4), not a uniform availability theorem.

A separate guarded L6 continuation from the ordinary audited 8,268-point L5
base is paused at 6,348 / 8,267 stitches without obstruction.  It does not
descend from the guarded-L5 path, so the two computations are not an inductive
two-level orbit.  Its independent auditor remains locked until terminal source
pins exist.

The exact short-return holonomy census also makes the exhaustiveness warning
quantitative.  Keeping actual accepted whole words, slots, prefix controls,
and correlated `8 -> 16 -> 8` pairs yields 3,136 affine return maps and 2,094
fixed points.  Full-candidate reveals produce 47,946 primitive guard
polynomials: four known classes and 47,942 others.  A two-loop composition
gives infinitely many exact affine fixed points.  These are action-channel
objects only--no physical secant birth, chronological compatibility,
repeatable legality, or availability conclusion follows.  The prepared
role-first checker filters them through one actual L5-to-L6 lineage and exact
Pluecker incidence before reporting any reachable poison.

## 9. Referee-grade remaining lemma

The weakest clean analytic replacement for the informal shell claim is:

> **Reachable far-birth envelope.**  Exhibit a policy-specific, inductively
> closed set of concrete histories and either (a) a summable profile (6.1), or
> (b) a number `rho<1`, the exact future-contact functional (5.1) or a sound
> finite upper representation of it, and a uniform birth/import bound (5.3).
> The birth operator must include every old--new and new--new secant; every
> deep--deep secant must be carried from birth or injected by the exact joint
> pair closure; every unrelated same-level cursor import must be covered; and
> current poison must be the exact monotone word-mask union (1.1).  Recurrent
> or infinite-moment zero classes must be promoted with a uniformly finite
> exact representation or proved unreachable.  Finally, the resulting near,
> promoted, and far masks must have a common surviving connector and every
> selected successor must remain in the invariant.

No present computation proves this lemma.  The fatal-mass experiment reports
a declining *spatial-shell* profile on one finite orbit; it does not measure
the birth-cohort quantities in (6.1), identify them under universal correlated
continuation, or control the exact-zero block.  The latent family proves that
this is a mathematical gap, not merely missing error bars on the observed
decay.
