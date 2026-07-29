# Fractional backward ghosts: boundedness and an infinite incidence obstruction

## Status

The bounded-integral-suffix lemma below is **PROVED**.  The subsequent
infinite-incidence theorem is also **PROVED**, but for arbitrary integer lattice
lines and the zero-control inverse branch.  It is an obstruction to a purely
spatial/phase quotient, not a proof that the distinguishing lines are reachable
secants in one legal chronological construction.

## 1. Exact backward bound and one-break integrality

For

\[
M=\begin{pmatrix}3&0&0\\0&0&-3\\0&3&-1\end{pmatrix},
\qquad
N=9M^{-1}=\begin{pmatrix}3&0&0\\0&-1&3\\0&-3&0\end{pmatrix},
\]

consider a backward ghost history

\[
y_j=c_j+M^{-1}y_{j+1},
\]

where each integral prefix control satisfies `||c_j||∞ <= 8` and the terminal
candidate satisfies `||y_n||∞ <= 8`.  Direct inversion gives

\[
M^{-1}=\begin{pmatrix}1/3&0&0\\0&-1/9&1/3\\0&-1/3&0\end{pmatrix},
\qquad \|M^{-1}\|_\infty=4/9.
\]

The cube of radius

\[
B=8+(4/9)B=72/5
\]

is backward invariant.  Induction therefore gives

\[
\|y_j\|_\infty\le 72/5
\]

at every depth.  If `y_j` is integral, then

\[
y_{j+1}=M(y_j-c_j)
\]

is integral.  Contrapositively, once a backward step is nonintegral, every
earlier backward step is nonintegral.  Thus an indefinitely extended history
is either integral throughout, or has one finite integral suffix, possibly
empty, followed backward by a permanently nonintegral rational tail.  Every
integral member of the suffix lies in

```text
{-14,-13,...,14}^3,
```

so there are exactly `29^3 = 24,389` possible integral spatial sites before
phase/history labels.

This proves the reported reduction.  It does **not** bound the length of the
integral suffix without a finite phase/control-state argument: a history may
revisit one of those sites.

## 2. Fractional ghosts are not harmless

A rational nonintegral point can lie on a line containing two integer points.
For example,

\[
M^{-1}(1,0,0)=(1/3,0,0)
\]

lies on the integer lattice line through `(0,0,0)` and `(1,0,0)`.  More
generally, if `y=a/D` with `a in Z^3`, then `y` lies on the line through `0`
and `a` (after separating an integer translate if desired).  Nonintegrality
therefore cannot be used as a no-incidence certificate.

## 3. Infinite exact incidence type inside the bounded tail

Let

\[
h=(0,1,0),\qquad v_n=N^n h,\qquad y_n=M^{-n}h=v_n/9^n
\]

for `n>=1`.  This is the backward branch with every control equal to zero.
Because `||M^{-1}||∞=4/9`, all `y_n` lie in the unit cube after the first step.
They are nonzero because `M` is invertible, and hence nonintegral because a
nonzero integer vector has infinity norm at least one.

Let `ell_n` be the lattice line through `0` and `v_n`.  It contains two integer
points and contains `y_n`.  We claim it contains no `y_m` for `m != n`.

It remains only to show that the projective directions `[v_n]` never repeat.
On the non-x `(y,z)` plane, `N` has matrix

\[
A=\begin{pmatrix}-1&3\\-3&0\end{pmatrix},
\qquad \operatorname{tr}A=-1,\quad\det A=9.
\]

Let its conjugate eigenvalues be `lambda` and `bar(lambda)`.  If a rational
nonzero vector were projectively periodic under a positive power `A^k`, then
`A^k` would have a rational eigenvalue.  Consequently
`lambda^k=bar(lambda)^k`, so `u=lambda/bar(lambda)` would be a root of unity.
But

\[
u+u^{-1}
=\frac{\lambda^2+\bar\lambda^2}{\lambda\bar\lambda}
=\frac{(\operatorname{tr}A)^2-2\det A}{\det A}
=-17/9.
\]

For a root of unity, `u+u^{-1}` is an algebraic integer.  A rational algebraic
integer is an integer, contradicting `-17/9`.  Hence all `[v_n]` are distinct.
Therefore

\[
y_m\in\ell_n \quad\Longleftrightarrow\quad m=n.
\]

The bounded fractional ghosts `y_n` consequently have pairwise distinct exact
incidence signatures against integer lattice lines.

## 4. Quotient consequence and boundary

Define two rational ghosts to be incidence-equivalent if exactly the same
integer lattice lines contain them.  Section 3 proves that this equivalence has
infinite index even inside a fixed bounded cube and along one inverse-control
branch.  Therefore no finite state consisting only of a phase label and one of
the 24,389 integral spatial sites, with all fractional tails collapsed into
finitely many generic classes, can preserve exact line incidence for arbitrary
integer secants.

This is a universal structural **no-go** for that proposed quotient.  It does
not prove infinite index on the *reachable chronological* token language.  A
valid finite proof could still show that only finitely many of the lines
`ell_n` can be born as reachable secants, or promote a finite reachable subset
using additional endpoint/birth data.  Thus the remaining positive obligation
is now sharper:

> prove a reachable-birth exclusion/promotion theorem for fractional-tail
> incidence, rather than trying to classify the tail from bounded Euclidean
> location and one-break integrality alone.

The exact regression checker is `fractional_ghost_tail_certificate.py`.  Its
finite depth test is only a check on the displayed all-depth algebraic proof.
