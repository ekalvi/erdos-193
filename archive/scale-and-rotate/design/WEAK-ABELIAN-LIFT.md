# Weak-abelian lift and the dimension-three obstruction

**Status: exact reduction and no-go audit, not a solution of Erdős #193.**
This note records a useful word-theoretic consequence of any successful walk
and, just as importantly, the dimension issue that prevents the converse from
being quoted as a solution of the stated problem in `Z^3`.

## 1. The exact lift

Let the distinct steps of an `S`-walk be labelled by an alphabet
`Sigma={1,...,q}`.  If its step word is `w`, write

```text
C_0 = 0,
C_n = sum_(t<n) e_(w_t) in Z^q
```

for the standard-basis prefix walk, and let `T(e_a)=s_a`, where `s_a` is
the step carrying label `a`.  Up to translation, the original walk is

```text
X_n = T(C_n).
```

For `i<j<k`, put `u=w[i:j)` and `v=w[j:k)`.  With `Psi` denoting the
Parikh map,

```text
C_j-C_i = Psi(u),
C_k-C_j = Psi(v).
```

All coordinates of these two vectors are nonnegative and their coordinate
sums are `|u|` and `|v|`.  They are linearly dependent exactly when

```text
|v| Psi(u) = |u| Psi(v),                              (1)
```

or, equivalently, the two adjacent factors have identical letter-frequency
vectors.  This is a weak abelian square in the terminology of
Avgustinovich--Puzynina.

Because a linear map sends collinear triples to collinear triples, (1) in the
step word would force `X_i,X_j,X_k` to be collinear.  Therefore:

> **Lift lemma.**  The step word of every triple-free finite-step walk is
> weak-abelian-square-free.

This implication is exact and needs no geometric regularity assumption.
The converse produces the standard-basis walk in `Z^q`: an infinite
weak-abelian-square-free `q`-letter word is an infinite triple-free finite-step
walk in dimension `q`.

## 2. Why this is not an equivalence for Erdős #193

Erdős #193 fixes the ambient lattice to `Z^3`.  For the original step map
`T:Z^q -> Z^3`, the exact bad event is

```text
T(Psi(u)) cross T(Psi(v)) = 0.                        (2)
```

Equation (1) implies (2), but for `q>3` the map can create additional
parallel pairs from nonproportional Parikh vectors.  A triple-free basis walk
in `Z^q` therefore does not automatically project to a triple-free walk in
`Z^3`.

There is a particularly clean special case.  If a linear functional `ell`
satisfies `ell(s)=1` for every step, then two nonzero adjacent displacements
can be parallel only with the positive ratio forced by their lengths.  In
that case (2) is equality of two weighted block averages.  But all such steps
lie in the affine plane `ell=1`; at most three of them can be affinely
independent.  With four or more labels there are rational frequency
differences that every such three-dimensional encoding identifies.

Using four affinely independent vertices of a tetrahedron does not repair the
problem: they cannot all lie in one plane `ell=1`, so a parallel pair can have
a scalar ratio different from the ratio of the two block lengths.  Ordinary
affine independence of the steps is not a collinearity-faithful projection
lemma.

The referee-grade statement is consequently one-way:

```text
Z^3 solution  =>  finite-alphabet weak-abelian-square-free word,
```

while the reverse direction needs a separate integer step assignment that
excludes every additional projective collision in (2).  No such general
projection theorem is proved here.

## 3. Integral normal form

Let `m=|u|`, `n=|v|`, `g=gcd(m,n)`, `m=ga`, and `n=gb`, with
`gcd(a,b)=1`.  Equation (1) holds exactly when there is a nonnegative integer
vector `z`, of coordinate sum `g`, such that

```text
Psi(u) = a z,
Psi(v) = b z.                                         (3)
```

This gives a useful exact indexing of unweighted poison events by primitive
Parikh rays.  For the actual `Z^3` problem, replace the Parikh ray in (3) by
the primitive signed direction of `T(Psi(u))`; equality up to sign is the
exact secant-poison relation.  This is another description of the global
line test, not a finite-state bound on it.

## 4. What the known word results say

- Gerver--Ramsey prove that a three-step menu cannot work: every sufficiently
  long three-letter word has the required adjacent frequency repetition.
  Their sharp finite statement is the obstruction behind the length-nine
  three-step walk theorem.
- Keranen's four-letter construction avoids ordinary abelian squares, where
  the two blocks have equal length and equal Parikh vectors.  That is weaker
  than (1).  The published 85-letter image of `0` already contains the exact
  unequal-length weak square

  ```text
  10212320210130 | 1020321,
  (4,4,4,2)      = 2 (2,2,2,1).
  ```

  These are positions `[33,47)` and `[47,54)` under zero-based indexing.
- The modern survey records binary unavoidability of weak abelian powers and
  the Gerver--Ramsey ternary construction avoiding only the very high power
  `5^11+1`.  It supplies no infinite weak-abelian-square-free word on a finite
  alphabet.

Primary references:

- J. L. Gerver and L. T. Ramsey, *On certain sequences of lattice points*,
  Pacific J. Math. 83 (1979), 357--363,
  <https://msp.org/pjm/1979/83-2/pjm-v83-n2-p08-s.pdf>.
- S. Avgustinovich and S. Puzynina, *Weak Abelian Periodicity of Infinite
  Words*, <https://arxiv.org/abs/1302.4359>.
- G. Fici and S. Puzynina, *Abelian combinatorics on words: a survey*,
  Section 8.2, <https://arxiv.org/abs/2207.09937>.

The absence of a square-avoidance theorem in those sources is literature
evidence, not a proof that no later construction exists.

## 5. Consequences for the two construction routes

### Scale and rotate

The verified 311,737-step `Z^3` walk has a 124-letter step word.  By the lift
lemma, that finite word is weak-abelian-square-free.  More strongly, it avoids
all weighted projective collisions (2) for its actual 124 step vectors.  Thus
the word view retains the construction as a valuable finite witness, but it
does not remove far secants: a far secant is precisely a primitive weighted
suffix direction born arbitrarily far back in the word.

The ordered-path safety game remains dimension-correct only if its poison
state uses the actual step map and retains every local and far projective
collision.  Replacing that state by unweighted Parikh rays would be a
relaxation, not a proof of #193.

### Affine decimation

The candidate

```text
P_n = (W_n, W_(2n), W_(5n))
```

lives in `Z^9`.  Proving it triple-free would be a genuine higher-dimensional
result, but not by itself an answer to the stated `Z^3` problem.  A valid use
of it for #193 needs one of the following additional results:

1. an explicit integer projection to `Z^3` proved to preserve all its
   noncollinear triples; or
2. a new three-dimensional candidate, for example

   ```text
   R_n = (n, F_n, G_n),
   ```

   whose two scalar automatic coordinates have no adjacent equal chord
   slopes.

For the second form, every step has first coordinate one, so collinearity is
exactly simultaneous equality of the two block-average increments.  This is
dimension-correct.  An exact screen of 16,908 small scalar choices killed all
of them by index 1,000; moreover the full `(V_(2n),V_(5n))` blocks already have
the common arithmetic-progression triple `(128,149,170)`, so that particular
pair fails under every scalar projection.

A stronger direct merge is

```text
R_n(C) = W_n + C W_(2n) + C^2 W_(5n) in Z^3.
```

It has at most 378 steps, all of common coordinate-sum height
`1+2C+5C^2`.  Coefficients 3 through 8 have exact finite counterexamples.  The
first surviving screen is `C=9`, with no collinear triple through index 30,000
after 450,014,999 exact chord checks.  This is a dimension-correct candidate,
not a theorem; finite prefixes forbid only finitely many coefficients and can
make projection search look artificially successful.  See
`affine/weighted-merge-screen.json`.

## 6. Smallest honest next gates

1. **Keep scale-and-rotate primary.**  The exact path-order replay has now
   been run.  Its literal radius-4 states are all unique across 131,097
   stitches, and augmenting the repeated radius-2 states with the exact
   `D=40` cloud makes all of them unique.  Exact backward-cone certificates now
   prove a 59-word floor for two variable L7 gaps and a six-word floor for all
   1.44 billion raw assignments in the corresponding three-gap cone.  The next
   gate adds the 47,467-word intermediate gap 3785 using poison-mask and
   compatibility-signature quotients; a far-tail rank remains necessary.
2. **Retain full chords and gaps in the direct `Z^3` defect.**  The `C=9`
   modular audit gives exact 12- and 360-state filters, but their natural
   26,244- and 787,320-state lifts are primitive, and modular zero is not
   prefix-closed.  A zero-SCC certificate is therefore impossible at those
   precisions.  Any remaining rational CEGAR must retain both adjacent chords
   and gaps.  Lidbetter's compact gap-ratio lemma does not automatically apply
   after projection, so all gap ratios need coverage unless a new ratio lemma
   is proved.
3. **Do not prioritize an unweighted four-letter DFS as a solution test.**
   It is useful combinatorics, and nonexistence would be an obstruction, but
   a survivor still needs a dimension-three weighted realization.

The strongest common obstruction is projective near-collision: normalized
direction closures may accumulate on a forbidden ray without any finite
integer equality.  Then a finite interval or polyhedral CEGAR can refine
forever unless an arithmetic ranking excludes exact zero.
