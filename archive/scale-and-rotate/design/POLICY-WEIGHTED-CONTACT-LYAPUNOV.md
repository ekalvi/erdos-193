# Policy-weighted contact Lyapunov certificate

**Status (2026-07-19): theorem-level deterministic extraction lemma and
certificate design; not a reachable-birth bound, cursor-import lemma,
availability certificate, or proof of Erdős #193.**

This note asks whether a fixed distribution on connector words can be used as
an analytic device even though the construction ultimately needs one
deterministic connector at every stitch.  The answer is yes, but only after
the quantifiers are placed in the correct order.  The reference distribution
must be frozen before the safety calculation.  The bad-word set must be the
union over all concrete histories represented by one abstract state, and the
successor potential of a word must be the supremum over all those histories
and every sound abstract successor.  Under those conventions an average
strict inequality produces one word which is simultaneously legal for every
represented history and returns every successor to the safe region.

The resulting mechanism can make a rare exact latent return contract even
though the generic all-descendant role kernel has spectral radius between two
and five.  It does not make births or unrelated-cursor imports small.  The
missing theorem is a policy-specific, correlation-preserving contact zeta
which is summable over all primitive birth directions and is closed under the
complete birth and import operator.

The exact endpoint/secant objects, killed-word masks, and birth equations used
below are those of `design/FAR-SECANT-BIRTH-OPERATOR.md`.  The zero-language
and correlated-address warnings are those of
`design/GHOST-LANGUAGE-AUTOMATON.md`.  Nothing here permits independently
chosen endpoint address streams, a distance cutoff, or deletion of a token
whose present mask is zero.

## 1. Concrete and abstract objects

Let `Q` be a finite proposed retained state set.  For `q in Q`, let

```text
Hist(q)
```

be its sound set of concrete ordered histories.  A history contains the
single realized path, all actual connector choices, the exact pending
corridor, and the endpoint and joint endpoint-pair frontier required by the
birth operator.  `Hist(q)` is not a product of independently possible point
addresses.

Let `D_q=D_(s(q))` be the finite connector domain and fix, in advance, a
rational reference distribution

```text
p_q : D_q -> [0,1],       sum_(w in D_q) p_q(w)=1.          (1.1)
```

Zero-probability words are outside this proposed policy channel.  The support,
all probabilities, and every later refinement claimed by the certificate
must be preregistered or independently derived from earlier frozen data.
Reweighting after inspecting which words survive is not allowed.

For a concrete history `h in Hist(q)`, write `Legal(h,w)` for exact legality
of inserting `w`.  It includes collisions, old--old--new secants,
old--new--new incidences, and internal legality.  Let

```text
Succ(q,h,w)
```

be the set of all sound `(q',h')` pairs asserted by the abstraction after a
legal insertion.  It must contain every concrete successor.  Abstraction
nondeterminism is universal, not existential.

Finally let `X_q(h)>=0` be a proposed far-contact potential.  It may be a
scalar projection of a vector, BDD, or antichain, but its proof must give a
sound map from the exact endpoint/secant frontier to `X`.  In particular,
currently silent Plücker tokens remain represented.

## 2. Deterministic extraction from a frozen word distribution

For one state `q`, define the **uniform bad set**

```text
Bad(q) = {w in supp(p_q) :
             there exists h in Hist(q) with not Legal(h,w)}.       (2.1)
```

The existential quantifier over histories is inside the definition of
`Bad(q)`.  Thus a word outside `Bad(q)` is legal for every represented
history.  A per-history probability bound is insufficient.

For `w not in Bad(q)`, define its worst sound successor potential

```text
Y_q(w) = sup { X_q'(h') :
               h in Hist(q), (q',h') in Succ(q,h,w) }.             (2.2)
```

Use `Y_q(w)=0` if the displayed set is empty.  The supremum over histories and
sound successors is taken before averaging over words.

### Theorem 2.1 (fractional Bellman extraction) -- theorem

Fix numbers

```text
0 <= n < 1,       0 <= rho < 1,       b >= 0,       R > 0.
```

Suppose that, for every retained state `q` under consideration,

```text
sup_(h in Hist(q)) X_q(h) <= R,                              (2.3)

p_q(Bad(q)) <= n+R,                                         (2.4)

sum_(w not in Bad(q)) p_q(w) Y_q(w) <= rho R+b,             (2.5)
```

and

```text
rho+n+R+b/R < 1.                                            (2.6)
```

Then there is a word `w_q in supp(p_q)\Bad(q)` such that

```text
Y_q(w_q) <= R.                                              (2.7)
```

Consequently `w_q` is legal for every `h in Hist(q)`, and every sound
successor after that word again satisfies the potential barrier.

**Proof.**  By (2.4),

```text
p_q(supp(p_q)\Bad(q)) >= 1-n-R.                             (2.8)
```

If every uniformly legal word had `Y_q(w)>R`, then

```text
sum_(w not in Bad(q)) p_q(w)Y_q(w)
    > R(1-n-R).                                             (2.9)
```

Condition (2.6) is exactly

```text
rho R+b < R(1-n-R),                                        (2.10)
```

contradicting (2.5).  Hence one uniformly legal word satisfies (2.7).
QED.

The use of the unnormalised sum in (2.5) is deliberate.  No conditional
distribution on the surviving words is introduced after the history is
known.  Equivalently, the conditional mean over uniformly legal words is at
most `(rho R+b)/(1-n-R)`, but (2.5) is the certificate-bearing inequality.

For fixed `b>0`, the algebraic expression `R+b/R` is minimised at
`R=sqrt(b)`.  Therefore, **only if** (2.3)--(2.5) have been proved with that
same value `R=sqrt(b)` (and with the displayed `rho,n,b` valid at that value),
the convenient sufficient numerical condition is

```text
rho+n+2 sqrt(b) < 1.                                       (2.11)
```

Equation (2.11) is not a licence to rescale an arbitrary potential after the
fact.  Such a rescaling generally changes the birth constant `b` and can
invalidate both the potential barrier (2.3) and the far bad-mass domination
in (2.4).  Without a same-`R` certificate, one must check (2.6) at the actual
certified value of `R`.

Exact mask overlap can improve (2.4) and should be used when available;
`n+R` is only a safe additive form.

### Corollary 2.2 (safety-game closure) -- conditional theorem

Suppose a finite set `G subset Q` contains the seed, (2.3)--(2.6) hold for
every `q in G`, and `Succ(q,h,w_q)` is contained in states of `G` for every
`q`, `h`, and the extracted word `w_q`.  Then the selector

```text
sigma(q)=w_q
```

is a deterministic safety strategy common to all histories represented by
each state.  The proof is direct induction using Theorem 2.1.  This is the
quantifier order needed by Requirement G of
`design/FAR-SECANT-RANK-LEMMA.md`.

## 3. Exact reference contact moment

Fix `0<rho<1`.  Start with one concrete history `h in Hist(q)` and one exact
endpoint or secant token `z`.  A future word string

```text
alpha=(w_0,...,w_(m-1))                                    (3.1)
```

is followed through the exact concrete ordered history.  Its cylinder weight
is

```text
P_q(alpha)=product_(j=0)^(m-1) p_(q_j)(w_j).               (3.2)
```

The states, cursor frames, endpoint pair, selected connector words, slots,
and prefix controls in this continuation are correlated.  Equation (3.2)
does not authorize a Cartesian product of two endpoint address languages or
independent sibling events inside one whole word.

No future-legality conditioning is hidden here.  Before the calculation, the
certificate must choose either (a) every formal domain continuation under the
exact affine, cursor, and birth equations, including branches whose inserted
point set would later be rejected, or (b) a smaller continuation relation
whose closure has already been proved independently.  Formal illegal branches
are geometric overapproximations, not asserted legal histories.  Deleting a
branch merely because the eventual safety policy would not choose it is
circular.  In the notation below, `h_alpha` may therefore denote a formal
geometric continuation; all endpoint and joint-pair correlations are still
retained exactly.

Let `z_alpha` be the exact transported token.  Define

```text
d_(q_alpha,h_alpha)(z_alpha)
  = p_(q_alpha)({w : z_alpha contributes an atom killing w}).       (3.3)
```

For a secant this contains its direct candidate-site mask.  For an endpoint
it contains collision and endpoint-on-candidate-internal-line masks.  Lines
formed by pairing an endpoint with a later connector interior enter the birth
cohort of that later insertion; they are not silently attributed to the old
endpoint.

The exact reference future-contact moment is

```text
V_(rho,q)(h,z)
  = sum_(m>=0) rho^(-m)
      sum_(exact correlated alpha of length m)
        P_q(alpha) d_(q_alpha,h_alpha)(z_alpha).            (3.4)
```

If there is abstraction nondeterminism, a sound upper version takes the
supremum over its concrete resolutions before the outer sum.  A certificate
may instead give a finite positive supersolution of the Bellman equations;
literal evaluation of (3.4) is not required.

Formula (3.4) includes a token with zero current mask.  Its `m=0` term can be
zero while a later term is positive.  In particular it does not identify two
tokens merely because both current masks are empty.

Where the exact formal post is defined for every reference word, index
shifting gives

```text
sum_w p_q(w) V_(rho,q_w)(h_w,Post_w z)
    = rho (V_(rho,q)(h,z)-d_(q,h)(z))
    <= rho V_(rho,q)(h,z).                                 (3.5)
```

For a safety certificate it is enough to prove the weaker uniformly-legal
version used in (2.5).  Birth and import cohorts add the `b` term.  Equation
(3.5) explains why an averaged contact potential can decrease even though a
specific rare latent suffix survives.  Corollary 4.2 of
`design/FAR-SECANT-BIRTH-OPERATOR.md` rules out contraction on every allowed
edge; it does not rule out the frozen-distribution average (3.5).

## 4. Correlated primitive-direction contact zeta

Fix `q`, a word `w not in Bad(q)`, and a labelled connector-interior slot
`a` of `w`.  For `h in Hist(q)`, write `Old(h)` for the pre-insertion point
set and `i_a=i_a(h,w)` for the actual point placed in slot `a`.  In every
sound concrete successor `(q',h') in Succ(q,h,w)`, each old--new line born at
that slot has the form

```text
ell(i_a,u),       u in Old(h),
g=canonprim(u-i_a),       mu=i_a cross g.                   (4.1)
```

Define its robust **post-insertion** direction weight by

```text
v^+_(rho,q,w,a)(g)
  = sup { V_(rho,q')(h',ell(i_a,u)) :
            h in Hist(q),
            (q',h') in Succ(q,h,w),
            u in Old(h), canonprim(u-i_a)=g }.              (4.2)
```

The value in (4.2) is defined to be `0` when the displayed class is empty.
Thus it ranges only over correlated concrete histories, actual old endpoints,
and **every** sound successor state/history in which the line has just been
born.  In particular the new token is charged at `q',h'`, where it enters the
Bellman potential, rather than at the source `q,h`.  The exact token continues
to retain its endpoint identities, joint address tree, birth data, and
Plücker moment.  The scalar upper weight in (4.2) does not replace that
provenance by independent marginals.

Define the primitive-direction contact zeta

```text
Z^+_(rho,q,w,a) = sum_(primitive canonical g in Z^3)
                    v^+_(rho,q,w,a)(g).                    (4.3)
```

### Lemma 4.1 (direction injection at an old--new birth) -- theorem

Fix an exact **legal** transition `h --w--> h'` whose post-insertion point set
is triple-free, one of its sound successor labels `q'`, and a newly inserted
point `i_a`.  Only after this legal insertion is known, at most one old
endpoint has a given canonical primitive direction from `i_a`.  Consequently

```text
sum_(u in Old(h)) V_(rho,q')(h',ell(i_a,u))
    <= Z^+_(rho,q,w,a).                                    (4.4)
```

**Proof.**  If distinct old points `u_1,u_2` have the same canonical primitive
direction from `i_a`, then `i_a,u_1,u_2` lie on one affine line, contradicting
triple-freeness of the legally formed successor.  Apply (4.2) in this
particular successor and sum over directions.  QED.

No direction-injection claim is made for a merely proposed site, an illegal
formal insertion, or a post state not proved triple-free.

To connect the zeta to the additive Bellman term, let `Birth(h,w)` be the
exact set of new endpoint tokens, new--new line tokens, and old--new line
tokens first created by the insertion.  For every sound successor define

```text
beta_rho(q,h,w;q',h')
  = sum_(z in Birth(h,w)) V_(rho,q')(h',z),                 (4.5)

B_q(w)
  = sup { beta_rho(q,h,w;q',h') :
            h in Hist(q), (q',h') in Succ(q,h,w) }.         (4.6)
```

Use `B_q(w)=0` if the successor class is empty.  Every contact weight in
(4.5) is therefore evaluated after insertion and the supremum in (4.6)
quantifies over every sound successor, just as `Y_q(w)` does.  Lemma 4.1 gives
an upper bound for the old--new part of (4.6) by summing
`Z^+_(rho,q,w,a)` over the labelled new slots.  The finitely many new--new
lines and new endpoint tokens must be added separately and uniformly over the
same successor class.

If `I_q(w)` is the analogous nonnegative, all-successor upper charge for new
cursor-import cohorts, the required birth/import hypothesis is the
unnormalised bound

```text
sum_(w not in Bad(q)) p_q(w) (B_q(w)+I_q(w)) <= b           (4.7)
```

in every retained state.  Together with the `rho R` drift of the carried
tokens, (4.7) yields the right-hand side `rho R+b` in (2.5).  A zeta evaluated
only in the source history, or only for one selected abstract successor,
does not establish that Bellman inequality.

Thus a uniform finite upper bound on (4.3) controls every old--new line made
by one new point in every covered successor, regardless of the number or
distance of old endpoints.  With at most four connector interiors, the
old--new direct-line birth charge is at most the sum of four such zeta bounds.
The at most six new--new lines and at most four new endpoint tokens are the
separate finite terms in (4.5).  Every old pair line must be carried from its
original birth.  Reconstructing discarded deep--deep lines from endpoint
marginals reintroduces the unsound quadratic term and is not covered by
(4.4).

Endpoint effects and later near--deep joins still require their own endpoint
contact moment.  Lemma 4.1 controls the direct line born from an old endpoint;
it is not permission to discard that endpoint's identity or its correlated
role in later pair creation.

## 5. The dimension-three threshold

The number of primitive integer directions in any fixed norm ball of radius
`R` is `O(R^3)`.  Therefore the power bound

```text
v^+_(rho,q,w,a)(g) <= C (1+||g||_Q)^(-3-epsilon)            (5.1)
```

would make (4.3) finite, uniformly over the finite insertion-site and phase
sets.

For the known two-level inverse families, primitive direction height grows
by a factor of nine per macrocycle.  A direction shell at macrodepth `m`
therefore has the coarse lattice capacity

```text
O(9^(3m)) = O(729^m).                                      (5.2)
```

Suppose a sound contact-language theorem gives, for every unpromoted member
of shell `m`, terminal reference contact at most `A theta^m`.  In the
exponentially weighted moment (3.4), its charge is at most

```text
A (theta/rho)^m.                                           (5.3)
```

Summing (5.3) over the coarse shell count (5.2) gives

```text
sum_(m>=0) C A (729 theta/rho)^m
  = C A/(1-729 theta/rho),                                 (5.4)
```

provided

```text
729 theta < rho < 1.                                      (5.5)
```

The summability statement is strictly stronger than a cubic exponent.  Under
(5.5) there is some `epsilon>0` such that

```text
9^(3+epsilon) theta/rho < 1.                               (5.5a)
```

Equivalently the resulting direction weight has power exponent
`3+epsilon`, not merely three.  Without the extra exponential moment,
ordinary zeta convergence requires the strict inequality `729 theta<1`,
equivalently `9^(3+epsilon)theta<1` for some positive `epsilon`.  Equality at
`729 theta=1` is not summable.  These inequalities explain the
availability-relevant threshold; they do not prove that arbitrary reachable
line directions have the assumed height/contact relation.  Affine moments,
multiple exact contact addresses, same-level cursor queries, and recurrent
small-direction classes must all be included in the theorem supplying
`theta`.

More generally, if a birth shell has multiplicity at most `B_0 Lambda^m`
and terminal contact at most `A theta_c^m`, then its contribution to the
birth term in Theorem 2.1 is bounded by

```text
b <= B_0 A/(1-Lambda theta_c/rho),
Lambda theta_c < rho < 1.                                 (5.6)
```

The final safety test is still (2.6), or (2.11) only when (2.3)--(2.5) are
proved at the same `R=sqrt(b)` as specified after Theorem 2.1.  Convergence of
(5.6) by itself is not availability-grade; its constant may be too large,
and exact word-mask overlap may be essential.

## 6. Exact known-template coefficients and provenance

The following numbers are exact statistics of the frozen uniform accepted
word model, not probabilities of a chronological legal policy.  Their compact
source is

```text
design/known-template-weighted-birth-probe-summary.json
```

with reported raw artifact SHA-256

```text
af466dccabbc56d720effb0d0a811c69cc3d727cfedc92f04ccff44a2a9583d1
```

and checker commitment

```text
design/known_template_weighted_birth_probe.py
cba506adefbc75f0fceab04a707d84e9538602133da4516fa0006348642748ee
```

The probe pins the accepted-action certificate
`9ce2de5f7936349b4cc7e830dcf962f26164693dbf66da1ba3fcc9a1d73e2112`
and its bitsets
`f75568afab8b17df620d3fed4cd174862db33c20f482a07ef38741db0c9e88cb`.

For the ordered envelope,

```text
a_8  = 287/14418,
a_16 = 319/14005,
theta_ord = a_8 a_16
          = 91553/201924090
          approximately 0.0004534,                         (6.1)

729 theta_ord
  = 66742137/201924090
  approximately 0.33053,

terminal reveal fraction r_8 = 1493/14418.                (6.2)
```

For the zero envelope,

```text
a_8=a_16=193/9954,
theta_zero = 37249/99082116
           approximately 0.0003759,                        (6.3)

729 theta_zero
  = 27154521/99082116
  approximately 0.27406,

terminal reveal fraction r_8 = 503/4977.                  (6.4)
```

For the tested `J=11/3` macrocycle, one required phase has zero qualifying
accepted words in each frozen filter, so the reported macro coefficient is
exactly zero.  Its incremental terminal reveal fractions are `7/4519` in the
ordered envelope and `3/1712` in the zero envelope.  Terminal factors affect
the constant `A` in (5.4), not the convergence threshold.  This breaks that
one action-channel cycle; it does not classify all recurrent zero languages.

Theorem 2.1 does **not** condition its reference distribution on the legal
words: a future sound drift certificate would use the unnormalised sum (2.5),
without dividing by legal mass.  But (6.1) and (6.3) are only exact
accepted-word marginal factors for the two named artificial reference-policy
channels.  They are candidate factors for a future sound contact operator if
an independent construction proves that those channels cover every required
correlated contact path, birth/import cohort, and sound successor.  The
current artifacts do not prove that and do not make (6.1) or (6.3)
safety-game transition probabilities or coefficients of an already sound
Bellman operator.

For comparison only, suppose one instead tried to describe a random choice
conditioned on the common legal set.  If a separately proved common legal
reference mass at the two phases were at least `eta_8,eta_16`, then the role
coefficient of that different, conditioned process would only be bounded by

```text
theta_cond <= theta/(eta_8 eta_16).                         (6.5)
```

Thus that conservative conditioned-role comparison would require

```text
eta_8 eta_16 > 729 theta.                                  (6.6)
```

For equal phase masses, (6.6) requires approximately

```text
eta > 0.5749     ordered envelope,
eta > 0.5235     zero envelope.                            (6.7)
```

Equivalently the common poisoned reference mass must be below approximately
`0.4251` or `0.4765`, respectively.  No sampled availability floor establishes
these uniform bounds.  Equations (6.5)--(6.7) are not assumptions of Theorem
2.1 or Lemma RCZI and must not be used to renormalise the Bellman drift
post-hoc.

The generic role source is

```text
design/generic-ghost-transfer-census-summary.json
```

with reported artifact SHA-256
`72833076715d8d868b9c0dc0fd228d2b9e50af2b7bba07185213c0683cb3a6a4`
and checker commitment
`225c597214ceffdd74ad5fa7fb08a81e0473ed6da2f0377759dfbed2d707d772`.
It proves that the all-descendant first-moment kernel has spectral radius in
`[2,5]`.  That kernel is not (3.4): it counts every connector role and has no
exact incidence predicate.  Conversely, one prescribed low-probability role
path is not a proof about the union of all exact contact paths.  A successful
operator must sit between these two extremes: every exact latent contact path
is included, but noncontacting roles are not charged merely because they are
children.

## 7. Remaining reachable-birth and cursor-import lemma

The analytic route closes only after proving the following statement.

> **Lemma RCZI (reachable correlated contact zeta and imports).**  Exhibit a
> finite retained ordered state set `Q`, sound correlated concretizations
> `Hist(q)`, frozen rational word distributions `p_q`, a finite exact promoted
> block, constants `rho,n,b,R`, and sound endpoint and secant contact weights
> such that:
>
> 1. the seed belongs to a retained state and every selected concrete
>    successor is covered;
> 2. the current exact killed-word union for all histories in one state has
>    common reference mass at most `n+R`, with `n` the certified
>    near/promoted common-mask contribution and `R` the certified far-contact
>    contribution (the same scalar radius used in (2.3));
> 3. every endpoint and joint endpoint-pair token, including every token with
>    zero current mask, is covered by the contact weights or the exact promoted
>    block;
> 4. the uniformly legal, all-successor transport satisfies the unnormalised
>    Bellman drift (2.5); no independent endpoint address streams are used;
> 5. for every represented history, uniformly legal word, and sound successor
>    state/history, each insertion injects every old--new and new--new line
>    and every new endpoint; their post-insertion contact charge and every
>    new import charge obey the unnormalised all-successor bound (4.7), so
>    they are genuinely included in `b`;
> 6. already born deep--deep lines are carried from birth; if a local state
>    discards them, their exact joint reconstruction is charged explicitly;
> 7. every same-level cursor import is either already present in the global
>    frontier, belongs to a finite promoted class, traverses a uniformly
>    bounded acyclic/ranked import block, or is included in `b`; an import-only
>    recurrent class is not assigned a fictitious contraction;
> 8. the primitive-direction zeta (4.3), the analogous endpoint contact sum,
>    and every promoted mask are uniformly finite and sound for the actual
>    correlated ordered continuation language; and
> 9. the strict numerical inequality (2.6) holds in every retained state.

Theorem 2.1 and seed/successor closure then give the far part of a deterministic
safety certificate.  Combining it with exact near legality and the usual
scale-and-rotate growth argument would make the construction unconditional.

No current repository result proves Lemma RCZI.  In particular:

* the known-template coefficients cover only two named inverse families;
* the finite lattice-`T` nilpotence result omits silent ghosts, births, and
  cursor imports;
* the x-axis Bellman barrier controls synchronized exterior transport but not
  occupancy, births, or unrelated-cursor injection; and
* level-uniform one-point crowding does not imply the direction/contact zeta.

## 8. Smallest preregistered finite screen

The smallest honest experiment on the existing sealed role/domain data is a
**negative-capable prescribed-role cycle screen**.  A positive result is only
a gate for Lemma RCZI, not a proof of it.

Freeze before running:

1. the zero-envelope accepted-word set;
2. the uniform distribution on that set at each of the 124 source steps;
3. every exact role label `(s,c,t)`, using its already sealed whole-word count;
4. the complete edge set, with no removal after seeing cycle weights; and
5. a target common legal reference mass `eta_0=3/5` for a separately labelled
   conditioned-role diagnostic.  This number is a design target, not a
   currently proved floor and not an input to the unconditioned Bellman
   theorem.

For each role put

```text
P_(s,c,t)
  = #{accepted whole words at s containing role (c,t)}
      / #{accepted whole words at s}.                       (8.1)
```

Compute the exact maximum geometric cycle mean `kappa_*` of these edge
probabilities.  The associated PF feasibility inequalities are

```text
P_(s,c,t) v_t <= kappa_cert v_s
for every exact role edge,       v_s>0.                     (8.2)
```

The infimum feasible coefficient is the maximum cycle mean on the cyclic
part.  It need not be represented by an attained rational vector on an
arbitrary reducible graph.  Therefore report both kinds of certificate:

* a failure is witnessed by an explicit directed cycle whose exact product is
  at least the proposed threshold to the cycle length; and
* a success is witnessed by a positive rational vector and a rational
  `kappa_cert` strictly below the threshold, with exact nonnegative slack on
  every edge.

The multiplicative Karp calculation may additionally bracket `kappa_*`
algebraically.  Do not replace sibling joint events by products of marginals.

Preregister these verdicts:

```text
kappa_* >= 1/27
  -> hard failure of the simplest one-role-per-level,
     dimension-three power-law route for this frozen distribution;

kappa_cert < 1/27
  -> unconditioned prescribed-address screen pass only;

kappa_* >= eta_0/27 = 1/45
  -> failure of the preregistered 40%-poison conditioned screen;

kappa_cert < 1/45
  -> conditioned prescribed-address screen pass only.       (8.3)
```

The strict screen inequalities are exactly what leave a positive exponent
margin: for example `kappa_cert<1/27` implies
`3^(3+epsilon)kappa_cert<1` for some `epsilon>0`.  The `eta_0` rows concern a
hypothetical conditioned role process only.  They are reported to expose how
quickly naive conditioning can consume the margin; they are not required by
the unconditioned extraction theorem and may not replace (2.5).

Passing (8.3) does not control multiplicity of exact contact addresses,
affine moments, births, zero-mask re-entry, or coefficient-one cursor imports.
The weights and distribution must then be frozen and lifted to an exact
contact/carry operator.  That second operator must include every
future-contact-compatible role and must pass its own PF/Bellman inequality
with the final constants satisfying (2.6).  Failure of that refinement is a
failure, not permission to delete the offending states or to retune `p_q` on
the same data.

The ordered envelope may be run later as an independently preregistered
replication.  Choosing whichever filter gives the better result after both
are inspected would be post-hoc model selection and is not a certificate.

## 9. Two exact obstructions the certificate must exclude

### Proposition 9.1 (angularly saturated birth fan) -- broad-state theorem

Fix a future corridor with finite candidate-site set `V`, every connector word
having at least one proper interior in `V`, and choose an integer point
`i not in V`.  There is a finite triple-free set `H union {i}` such that for
every distinct ray from `i` through a point
`x in V`, `H` contains one remote point `u_x` on that ray.  The points can be
chosen arbitrarily remote and with uniformly bounded fixed-radius crowding.
Then the old--new secants `line(i,u_x)` kill every connector word at the future
corridor, for every reference distribution.

**Proof.**  Group `V` by rays from `i`.  On each distinct ray choose one
integer point `u_x=i+k_x(x-i)`.  Choose the integers `k_x` successively and
large.  At each choice only finitely many values create a collinearity with a
pair of previously chosen points; the whole ray cannot already be such a
forbidden line because that would put `i` and two earlier points on one line.
Thus the final set is triple-free, and large separations give the stated local
crowding.  Every candidate site lies on its corresponding old--new secant, so
every word, which contains some candidate interior, is killed.  QED.

This proposition does not assert reachability from the canonical seed.  It
does prove that triple-freeness, finite domains, word probabilities, and
fixed-radius or cubic one-point crowding alone cannot bound `b` or the common
bad mass.  Lemma RCZI must use a genuine reachable ordered-history
restriction which excludes this fan or charges it before it becomes fatal.

### Proposition 9.2 (coefficient-one recurrent zero class) -- theorem

Suppose an unpromoted future-contact class has a sound exact cycle whose
transfer coefficient is one on every edge.  Suppose also that, after
arbitrarily many turns around that cycle, it has an allowed exit with positive
killed-word mass and with total reference coefficient at least one fixed
`a>0`, independent of the number of turns.  Then no positive exponentially
weighted contact moment with `rho<1` is finite on that class, and no positive
PF weight can make its homogeneous transfer contract below one.

**Proof.**  Repeating the cycle `m` times costs reference coefficient one.
Taking the positive exit afterward contributes at least `a rho^(-m)` to
(3.4).  This is unbounded as `m` grows.  Equivalently, the
homogeneous transfer contains a permutation-cycle submatrix of spectral
radius one.  QED.

Such a class must be proved unreachable, broken by the selected policy,
placed in a uniformly finite exact promoted block, or controlled by a
separate finite rank.  Calling its current mask zero does none of these.  The
fixed non-x geometric two-cycle and the finite x-axis returns are warnings,
not yet instances of Proposition 9.2 for the reachable infinite ordered
policy: physical birth and repeatable global legality remain unproved.

## 10. Referee verdict

A frozen word distribution can be more than evidence.  Theorem 2.1 converts
the correct unnormalised average inequality into one deterministic connector
common to every history in an abstract state, with universal successor
closure.  It also explains why the small exact coefficients of the two known
latent templates are relevant despite generic role branching.

The distribution does not itself supply the inequality.  The load-bearing
new mathematics is Lemma RCZI: a summable, exact, correlated contact zeta for
all reachable endpoint and secant births, together with sound treatment of
same-level cursor imports and every recurrent zero class.  Until that lemma
and the final strict constants are certified, the weighted calculation is a
promising proof design and a sharp falsifier, not an unconditional far-secant
tail theorem.
