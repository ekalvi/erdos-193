# Ordered ghost language and the non-x carry obstruction

This note isolates what the ghost-site calculation proves about a carried
far secant for `M_BAL3`, and what it does **not** prove.  It uses only the
single realized ordered control language.  Taking an independent Cartesian
product of connector choices at successive levels would change the language
and is not sound for this purpose.

## 1. Exact ordered ghost language -- theorem

Let

```text
M = [3  0  0; 0  0 -3; 0  3 -1],
C = cof(M),
N = 9 M^(-1) = [3  0  0; 0 -1  3; 0 -3  0].
```

Fix a concrete ordered history and a pending corridor phase `q`.  A legal
successor edge `e` is an actual connector slot in an actual selected word.  It
has a parent-frame prefix control `c_e in Z^3` and a successor phase.  Let
`L_q(h)` denote the tree of edge strings that are compatible with the same
ordered history `h` and with its subsequent actual choices.  It is not the
free monoid on the union of all menu edges.

For an edge string `alpha=e_0...e_(n-1)` in this tree, put

```text
Phi_alpha(x) = c_0 + M^(-1)c_1 + ...
                   + M^(-(n-1))c_(n-1) + M^(-n)x.       (1.1)
```

If the current centred primitive line is `ell=(g,mu)`, where a point `y`
lies on `ell` exactly when `y cross g=mu`, then its exact future direct-hit
language is

```text
Z_q(h,ell) = {(alpha,x):
    alpha in L_q(h), x is a candidate site at the end of alpha,
    mu = Phi_alpha(x) cross g}.                          (1.2)
```

Indeed one child transition sends a parent point `y` to `M(y-c_e)`, so the
child query `x` pulls back to `c_e+M^(-1)x`.  Iterating gives (1.1).  Thus
(1.2) is equivalent to incidence of `x` with the line transported through
the same correlated edge string.

There is an entirely integral form.  Since `M^(-i)=N^i/9^i`, define

```text
Y_alpha(x) = sum_(i=0)^(n-1) 9^(n-i) N^i c_i + N^n x in Z^3.
```

Then

```text
(alpha,x) in Z_q(h,ell)
    iff Y_alpha(x) cross g = 9^n mu.                    (1.3)
```

Equation (1.3), not a floating-point distance test, is the exact Diophantine
word predicate that a carry certificate must recognize.

## 2. Zero and positive residuals -- theorem

For one query in (1.1), let

```text
r = mu - Phi_alpha(x) cross g,
kappa = ||r||_R / ||g||_Q,
```

where `M^T Q M=9Q` and `C^T R C=81R`, as in
`FAR-SECANT-RANK-LEMMA.md`.  If the primitive transported direction is

```text
g_alpha = epsilon M^n g / tau_alpha,
```

then the transported residual is

```text
r_alpha = epsilon C^n r / tau_alpha.
```

Consequently

```text
kappa_alpha = 3^n kappa,       r_alpha=0 iff r=0.       (2.1)
```

This gives a mandatory split.

* A zero residual is noncontracting Boolean information.  Along that exact
  correlated branch it remains an incidence.  It must be retained exactly,
  proved unreachable, or represented by a sound finite future-compatibility
  class.
* A positive residual has a strict metric expansion along the fixed branch.
  This becomes a uniform finite rank only after a uniform lower gap for every
  residual injected by the exact birth operator.  Finiteness of the digit
  alphabet does not supply that gap.

The second bullet must not be read as a count of killed words: a different
continuation gives a different ghost query.  A sound rank has to quantify over
the whole correlated continuation tree of the token.

## 3. What a finite carry automaton would mean

The literal exact forward carry is the canonical transported Pluecker state

```text
(q,g_i,mu_i) --e--> (q', canonprim(Mg_i),
                           canonically scaled C(mu_i-c_e cross g_i)).
```

A candidate site is accepted by the exact equation `x cross g_i=mu_i`.
For every rational non-x direction `g`, the projective directions
`[M^i g]` are pairwise distinct.  Equality at two different times would give
a rational non-x eigenline of a positive power of `M`, which does not exist.
Therefore the literal Pluecker carry machine has infinitely many direction
states for every non-x token.

This observation does **not** prove that (1.2) is nonregular.  A smaller
automaton could merge different directions if they have the same right
language over the actual ordered continuations.  The needed equivalence is

```text
(h,ell) ~ (h',ell')
```

exactly when the two tokens have identical direct, endpoint, near--deep, and
killed-word effects after every correlated continuation on which the proposed
certificate relies.  A finite automaton exists only if this right congruence
has finite index on reachable concrete tokens.  Neither finite connector
domains nor contraction of `M^(-1)` proves finite index.

For comparison, the x direction has a fixed projective direction and reduces
to the already proved finite lateral-offset core.  The obstruction here is
specifically the nonperiodic non-x projective coordinate together with line
births and cursor imports.

## 4. What the `N^n`, `t=9` family proves -- theorem

Let `h=(0,1,0)` and `g_n=N^n h`.  More generally the same conclusions hold
for the family in Lemma 3.6.1 when the stated primitivity condition is met.
Then

```text
[T(g_n)]=[g_(n-1)],   t(g_n)=9,       ||g_n||_Q=3^n||h||_Q.
```

Thus there are primitive integer directions with arbitrarily long runs on
which canonical direction height contracts by `1/3`.  This proves all of the
following.

1. No bounded modulus, bounded 3-adic valuation counter, or monotone
   direction-height rank handles all primitive integer directions.
2. The literal exact carry set is not uniformly bounded by the connector
   digit radius.
3. Bare integrality gives no uniform positive-residual gap.  At a current
   integer candidate `x`, a nonzero integer residual satisfies only

   ```text
   kappa >= 6/(7 ||g||_2),
   ```

   using the extremal eigenvalues of `Q` and `R`.  This tends to zero on
   `g_n`.  More explicitly, because `g_n=(0,y_n,z_n)` is primitive, choose
   Bezout integers `a_n,b_n` with `a_n z_n-b_n y_n=1`.  The integer line of
   direction `g_n` through `x+(0,a_n,b_n)` has residual `(1,0,0)` up to sign,
   and hence normalized residual of order `3^(-n)`.
4. At ghost depth `m`, (1.3) gives only

   ```text
   kappa > 0  ==>  kappa >= 6/(7 * 9^m * ||g||_2).
   ```

   After applying the factor `3^m` from (2.1), this lower bound is still only
   `6/(7 * 3^m * ||g||_2)`.  The denominator arithmetic loses faster than
   the metric residual expands.

These are unconditional arithmetic obstructions over integer lines.  They do
**not** show that every `g_n` is born as a secant of the realized ordered
walk, or that the realized continuation language can distinguish the
directions.  Therefore the `N^n` family alone is not an infinite-index proof
for the ordered-path certificate.

## 5. A precise conditional infinite-index criterion

The following criterion says what would turn the arithmetic warning into a
counterexample to a finite future-compatibility quotient.

Suppose an ordered-compatible macro word `beta` of length `d` has all of the
following properties.

1. It is a repeatable cycle at one candidate-hit node `(q,x)` in the
   correlated continuation language, not merely a cycle obtained by combining
   edges from different connector histories.
2. Every edge of `beta` is degenerate in the exact sense

   ```text
   x' = M(x-c_e),
   ```

   so a line through the current site is carried through the next site for
   every direction.
3. There is an ordered-compatible selector exit `e` with nonzero

   ```text
   Delta = x' - M(x-c_e),
   ```

   and a non-x primitive direction `h` such that
   `canonprim(Mh)=canonprim(Delta)`.
4. For every `n`, one reachable concrete history at this same interface
   contains a carried secant through `x` of direction
   `g_n=canonprim(M^(-dn)h)`.  The common connector skeleton `beta^k e` is an
   ordered-compatible continuation from every one of these histories for
   every `k>=0`; all legality other than the tested incidence bit is retained
   in this compatibility statement.

Then these tokens have pairwise different right languages.  The suffix
`beta^k e` accepts the token of direction `g_n` exactly when `k=n`: it is
accepted at `k=n` by construction, while acceptance at a second value would
make the non-x line `[h]` periodic under a positive power of `M`.  Hence the
ordered future-compatibility congruence has infinite index.

The `N^n` family supplies integral primitive preimages for suitable `h`; it
does not supply hypotheses 1 or 4.  In particular:

* a cycle in the full-menu degenerate-site graph proves only an
  arbitrary-switching obstruction;
* an x-avoiding word witness still does not prove compatibility with the rest
  of the placed path; and
* the decisive counterexample needs reachable secant births and repeatability
  along one correlated ordered control language.

### Exact fixed-cycle refinement -- finite computation plus theorem

The pinned full-domain non-x scan now supplies a much stronger geometric
witness than its original 256-cycle countdown.  Its x-avoiding graph has one
768-vertex cyclic SCC and the exact two-edge cycle

```text
x_0=(-3,0,-3), c_0=(-2,1,-2), word [15,1,20,71], slot 1,
x_1=(-3,3,-2), c_1=(-2,4,-2), word [20,71,1,15], slot 2.
```

Both controls satisfy `x_(i+1)=M(x_i-c_i)`, and both listed words are exact
cache occurrences whose interiors omit the carried site.  Let the reveal
direction be `d=(3,-1,3)`, from `x_0` to the candidate site `(-6,1,-6)`.
For `r!=0`, the projective quantity

```text
J(r,y,z) = (3y^2-yz+3z^2)/r^2
```

is invariant under `M`.  This follows from the universal integer identity

```text
B^T [6 -1; -1 6] B = 9 [6 -1; -1 6]
```

and the simultaneous map `r -> 3r`.  Here `J(d)=11/3`.  The three interior
displacements from `x_0` have `J` values `17/9,3,5`, and the three from `x_1`
have values `5,3,3`.  Hence no forward or inverse projective iterate of `d`
can meet an interior of either fixed word.  The fixed-label countdown is
therefore carried-line-clean for **every** cycle count; the finite 256-cycle
check is superseded for this pair.

Moreover `g_n=canonprim(N^(2n)d)` is an integer primitive inverse family.
After `k` cycles the line through `x_0` of direction `g_n` hits the reveal
site exactly when `k=n`.  A second hit would make `d` projectively periodic;
that is impossible because `A=B/3` has determinant one and trace `-1/3`, so a
periodic eigenvalue `u` would make the rational number `u+u^(-1)=-1/3` an
algebraic integer.

Thus the fixed geometric cycle has infinitely many exact carried-line right
languages.  This is **not yet** an infinite-index theorem for the correlated
realized-path language: the repository has not proved that all lines of
direction `g_n` are reachable secants at this interface, or that these two
words are globally legal and repeatable in one compatible ordered control
tree.  Those are precisely the remaining birth and correlation hypotheses in
the criterion above.  The executable certificate and compact output are
`nonx_cycle_invariant_certificate.py` and
`nonx-cycle-invariant-certificate-summary.json`.

## 6. Availability-grade rank/promotion lemma still needed

For a retained ordered state `q`, let `Gamma_q` be the closure of all ghost
points `Phi_alpha(x)` from its **correlated** allowed continuation tree.  The
digit bound and `||M^(-1)v||_Q=||v||_Q/3` make `Gamma_q` compact.  For a line
`ell=(g,mu)`, define

```text
d_q(ell) = inf_(y in Gamma_q) ||mu-y cross g||_R / ||g||_Q.   (6.1)
```

Along an allowed edge, the distance to that edge's child ghost set scales by
exactly three.  A line with `d_q(ell)>0` has no direct hit at any finite future
stitch.  A line with `d_q(ell)=0` meets the compact ghost closure and cannot be
discarded by a positive-residual argument, even if the contact is only an
infinite-address limit.

For the load-bearing old--new birth, this has a concrete form.  If the
selected connector inserts `i`, an old endpoint is `u`, and
`g=canonprim(u-i)`, then the newborn line has `mu=i cross g` and

```text
d_q(line(i,u)) = inf_((alpha,x) in the correlated ghost tree)
    ||(i-Phi_alpha(x)) cross g||_R / ||g||_Q.           (6.2)
```

The missing Diophantine assertion therefore concerns the actual correlated
triples `(h,i,u)`, not the finite connector alphabet alone.  The old endpoint
`u` and hence `g` are unbounded; current-scale integrality gives only an
`O(1/||g||)` lower bound for a nonzero value in (6.2).

A sufficient theorem-grade replacement for an informal contracting shell
claim in the **direct carried-line channel** is the following uniform
birth-gap/promotion assertion.  The full legality theorem must assert the
analogous alternative for the two endpoint channels and for near--deep joins;
(6.1) alone says nothing about an endpoint lying on a candidate-internal line
or about a new line made from that endpoint and a future connector point.

There exist a constant `eta>0`, a finite exact promoted state `P`, and a
uniform finite birth-signature bound `B` such that, for every concrete history
represented by a safe state and every exact connector insertion:

1. every old--new and new--new secant, and every imported carried secant, is
   created as a joint endpoint-pair token;
2. each created line, for its direct-hit component, either belongs to `P` or
   satisfies `d_q(ell)>=eta`;
3. each endpoint component and each possible near--deep join separately has
   either a finite promoted future signature or a uniform positive gap for
   its exact collision/collinearity polynomial over the same correlated
   continuation tree;
4. `P` is closed under every selected correlated transition and records all
   direct, endpoint, near--deep, and word-mask effects exactly;
5. the union of unpromoted births from the finite connector interior joined
   to the entire old endpoint frontier has at most `B` exact future-effect
   signatures (or an explicitly certified monotone BDD/antichain with the
   same universal meaning); and
6. same-level cursor changes import no endpoint or line outside these two
   classes.

Under these clauses, zero/limit-contact components are promoted, every
unpromoted component has a uniform expanding separation in its own exact
incidence equation, and the residual cohort transfer can be given a finite
rank.  Combined with a finite bound on injections per rank, the Boolean
nilpotent-tail lemma yields a finite poison mask for the safety game.

An equivalent, sometimes easier, assertion replaces `eta` by a uniform
finite-depth statement: there is `R` such that every unpromoted newborn line
has empty exact ghost language beyond depth `R`, and the exact union of its
effects during those `R` levels has one of finitely many birth signatures.
The last `R` cohorts can then be retained.  This formulation makes clear that
a bound only on current killed words is insufficient: currently empty line
tokens can reactivate.

No current repository computation proves either formulation.  The main
Diophantine obstacle is that old--new directions are unbounded, and integrality
allows normalized misses of size `O(1/||g||)`.  A successful proof must obtain
the gap from the **reachable ordered birth language**, or prove that every
small-gap/zero-contact family has a finite closed promotion.  It cannot obtain
it from the finite connector alphabet alone.

## 7. Practical verdict

The ghost identity is useful, but only as a splitter:

```text
zero residual  -> exact correlated promotion/right congruence;
positive residual -> rank only after a uniform reachable-birth gap.
```

The most decisive analytic/computational next test is therefore not another
distance-shell fit.  It is to search the actual realized ancestry for the
four hypotheses in Section 5 while separately measuring whether newborn
near--deep lines violate any proposed version of (6.1).  A positive result
would be an ordered-path infinite-index obstruction; a negative finite-level
result would remain evidence only until repeatability and all-birth closure
are proved.
