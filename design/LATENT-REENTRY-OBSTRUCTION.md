# Latent re-entry under a common degenerate potential

**Status (2026-07-18): exact geometric carried-line obstruction, not a
reachable-history or far-secant theorem.**  The certificate is
`nonx_latent_reentry_certificate.py`; its compact commitments and conclusions
are in `nonx-latent-reentry-certificate-summary.json`.

## 1. What the height-two potential does prove

For a parent step `s`, candidate site `x`, selected whole word `w`, and one
ordered slot with prefix control `c` and child step `t`, put

```text
y = M(x-c).
```

This is a **degenerate candidate-to-candidate edge** when `y` is in the child
candidate set.  Given a common integer potential `rho(s,x)`, a whole word is
compatible with that potential exactly when every source `x` having some
non-descending induced edge is one of the word's own interiors.  Equivalently,

```text
x not in I_s(w) and y in C_t  ==>  rho(t,y) < rho(s,x).       (1.1)
```

The equivalence matters: if `x` is in the selected word, a carried old secant
through `x` kills that word, so the non-descending edge cannot occur along a
legal direct-line continuation.  Thus (1.1) gives a strict rank for every
**continuously effectful, degenerate, legal** carried-site chain.  The pinned
124-word pilot has such a potential of height two.

It does not rank a line whose current candidate mask is empty.  No vertex
`(s,x)` exists for such a step, so (1.1) imposes no inequality.

## 2. The smallest exact carried-line transition

In a corridor-centred frame represent one primitive affine line by its
Pluecker pair

```text
ell=(g,m),       m=p cross g,       x lies on ell iff x cross g=m.
```

For an ancestral slot with prefix `c`, points move by

```text
x' = M(x-c).
```

Let `C=cof(M)`, let `tau=gcd(Mg)`, and let `epsilon` choose the canonical sign
of the primitive successor direction.  The exact line transition is

```text
g' = epsilon Mg/tau,
m' = epsilon C(m-c cross g)/tau.                            (2.1)
```

The direct candidate mask is derived exactly as

```text
Mask_q(g,m) = {x in C_q : x cross g=m}.                     (2.2)
```

Consequently the smallest transition-sufficient state for one already-born
line in the direct old--old--new channel is the correlated cursor `q` plus
the exact pair `(g,m)`.  The current mask and a potential value are derived
data; they cannot replace `(g,m)`.

An integer hit `x` may be retained as a convenient marker.  Its virtual image
obeys `x'=M(x-c)` even when `x'` is not a candidate.  This separates four
mechanisms which must not be conflated.

1. **Continuous degenerate effect.**  If both `x` and `x'` are candidate
   sites, (1.1) ranks the legal transition.
2. **Continuous nondegenerate effect/reset.**  If the next hit is another
   candidate `y`, then

   ```text
   y-M(x-c) = k g'
   ```

   for an integer `k`.  A nonzero left side selects the direction.  The
   finite selector argument applies only while hits are consecutive.
3. **Latent transport and re-entry.**  During an empty-mask interval the
   virtual marker continues by the affine recurrence but is outside the
   candidate graph.  After a macro word `alpha`, a new hit `y` occurs exactly
   when the rational pullback ghost `Phi_alpha(y)` lies on the old line.  Its
   denominator and the reset coefficient `k` are unbounded.  This bypasses
   (1.1).
4. **Births and unrelated cursor moves.**  A line through a newly inserted
   point and an old endpoint, a new--new secant, or a line imported at another
   same-level corridor has no predecessor under (2.1).  These are injection
   operators, not carried-line transitions.  Full legality also needs the
   endpoint identities/positions for endpoint-on-candidate-line and
   near--deep joins.

Thus an exact full frontier would at least retain a correlated cursor, exact
endpoint tokens, and exact joint endpoint-pair/line tokens.  That concrete
state is not finite.

## 3. Exact infinite latent countdown inside the fixed policy

The selected fixed words contain the repeatable phase cycle

```text
step 8, word [0,1,16], slot 2, c=(-4,-4,-3)  -> step 16
step 16, word [8,23,24], slot 0, c=(0,0,0)    -> step 8.
```

Across the two slots the affine macro map is

```text
F(x)=M^2(x-c),
p=(-9/2,-39/11,-31/11),       F(p)=p.
```

Let

```text
a=(-2,-2,-2),                 h=22(a-p)=(55,34,18),
N=9M^(-1),                    g_n=N^(2n)h,
L_n={x : x cross g_n = p cross g_n}.
```

These are genuine integer lattice lines for every `n`:

- every `g_n` is primitive;
- `g_n mod 22` has exact period five;
- `P cross g_n=0 mod 22` for `P=22p=(-99,-78,-62)`, so the moment
  `p cross g_n` is integral; and
- for primitive `g`, the image of `x -> x cross g` is the saturated integer
  plane perpendicular to `g`, so an integral moment is attained by an integer
  point.

Since `M^2N^2=81I`,

```text
F(L_n)=L_(n-1).                                           (3.1)
```

The all-`n` silence assertion is exact, not extrapolated from the 64-step
direct replay.  The checker extracts the full candidate sets for steps 8 and
16: each has 214 sites.  Step-16 sites are pulled back to the step-8 frame by
`c+M^(-1)x`.  For every resulting direction `d=z-p`, use

```text
J(r,y,z)=(3y^2-yz+3z^2)/r^2.
```

This is projectively invariant under `M`, and `J(g_n)=348/275`.  Among all
428 phase-adjusted candidates, exactly two have that value:

```text
phase 8:  x=(-2,-2,-2), primitive d=(55,34,18)=g_0;
phase 16: x=(-4,1,2),   primitive d=(165,-20,102).
```

But `(g_n)_x=55*9^n`.  Hence neither direction equals `g_n` for any `n>=1`.
It follows that `L_n` has an empty **full candidate-site mask** at both phases,
returns as `L_(n-1)` after a complete cycle, and after exactly `n` cycles
returns as `L_0`.  Then it hits `a`, which is an interior of the selected
step-8 word.

For `n<m`, the continuation consisting of `n` complete phase cycles followed
by the selected step-8 word is killed by `L_n` and not by `L_m`.  Therefore
the direct carried-line future congruence over all integer lattice lines has
infinite index even under these fixed common-potential-compatible actions.
An integer lattice line is not yet a secant of the realized path: that further
requires two placed endpoints on it.  The height-two candidate potential is
never consulted during the silent countdown.

## 4. Exact consequence and reachability boundary

This result rules out the proposed implication

```text
common candidate-site potential
    => finite exact zero-mask/carried-line core.
```

It also shows why a contracting positive-residual shell transfer is
insufficient.  Each `L_n` has exact zero residual against a depth-`n` ghost,
despite having zero current mask.  Such a token belongs to the promoted
zero/contact class, and this class already has infinitely many geometric
right languages.

It does **not** prove that the reachable safety game has infinite index.  The
certificate does not show that any `L_n` is born from two points in one legal
ordered-path history, or that all other poison channels permit the displayed
phase cycle to repeat from such a history.  A finite proof remains possible
only if it adds at least one genuinely new ingredient:

1. a reachable-birth theorem excluding all but finitely many of these latent
   line languages;
2. a stronger action policy which breaks every reachable latent macro cycle,
   not merely every degenerate candidate-site cycle; or
3. an additional well-founded first-return/contraction rank which handles
   exact zero ghosts and is closed under births and cursor imports.

Newly born secants and unrelated same-level jumps remain separate obligations
under every option.  The fixed computation proves an obstruction to the
geometric core argument, not an obstruction to every possible ordered-path
safety certificate and not an unconditional result for Erdős #193.
