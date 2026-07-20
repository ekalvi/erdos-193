# X-projection coset addresses

## Scope

This note isolates the `yz`-projection part of the no-new-x-line policy.  It
proves an exact quotient/address lemma and an analytic radius-seven locality
bound for connector words of length at most five.  It does **not** prove that
a legal connector is always available, that a local state has a safe global
extension, or that non-x secants are controlled.

The state below always refers to the single realized ordered path and the one
connector actually selected at each gap.  Different words in a connector
domain are alternative actions.  Their union is not placed, and overlap
between two unchosen alternatives is irrelevant.

The companion checker is
`design/x_projection_coset_address.py`; its compact result is
`design/x-projection-coset-address-summary.json`.

## 1. Exact quotient coordinate

Let

\[
B=\begin{pmatrix}0&-3\\3&-1\end{pmatrix}.
\]

Its determinant is $9$, and the gcd of its entries is $1$, so its Smith
normal form is $\operatorname{diag}(1,9)$.  In particular,

\[
\mathbb Z^2/B\mathbb Z^2\cong\mathbb Z/9\mathbb Z.
\]

Define

\[
q(y,z)=y-3z\pmod 9.
\]

For $B(u,v)=(-3v,3u-v)$,

\[
q(B(u,v))=-3v-3(3u-v)=-9u.
\]

Thus $B\mathbb Z^2\subseteq\ker q$.  The map $q$ is surjective, while
both subgroups have index $9$, hence

\[
\boxed{\ker q=B\mathbb Z^2.}
\]

Use the representatives $d_r=(r,0)$, $0\le r<9$.  If $p=(y,z)$ and
$r=q(p)$, set

\[
c(p)=\left(\frac{r-y+3z}{9},\frac{r-y}{3}\right).
\]

Both coordinates are integers, and direct substitution gives

\[
\boxed{p=Bc(p)+d_r.}
\]

Consequently

\[
(a,r)\longmapsto Ba+d_r
\]

is a bijection from $\mathbb Z^2\times\{0,\ldots,8\}$ to $\mathbb Z^2$.
This is an exact address system, not a hash or a congruence approximation.

## 2. Connector role masks

Let $P=(p_0,\ldots,p_N)$ be the parent ordered path and let
$a_i=(p_{i,y},p_{i,z})$.  The child anchor above $p_i$ has lateral
coordinate $Ba_i$, hence address $(a_i,0)$.

At gap $i$, choose one word $w=(v_1,\ldots,v_m)$ from the domain of the
actual parent step.  For $1\le j<m$, let

\[
u_j=\pi_{yz}(v_1+\cdots+v_j)
\]

be its interior lateral prefix.  That child interior has lateral coordinate

\[
Ba_i+u_j=B(a_i+c(u_j))+d_{q(u_j)}.
\]

Its exact address is therefore

\[
\boxed{\alpha(i,j)=(a_i+c(u_j),q(u_j)).}
\]

Two child points have the same `yz` coordinate if and only if these addresses
are equal.

For one connector action define the finite multiset

\[
R_s(w)=\{\!\{(c(u_j),q(u_j)):1\le j<m\}\!\}.
\]

The complete x-projection effect of selecting $w$ at gap $i$ is the
translation of this one mask by $a_i$.  Connector words with the same mask
have the same x-projection effect even when their x-coordinates and non-x
secant behaviour differ.

Let $H=\{\!\{(a_i,0):0\le i\le N\}\!\}$ be the anchor-address multiset,
and let $T_iR_{s_i}(w_i)$ denote the translated realized mask at gap $i$.
The selected child connectors create no new doubled `yz` fibre exactly when:

1. every translated connector mask has no internal repeated address;
2. every translated connector mask is disjoint from the support of $H$;
3. translated masks belonging to distinct realized gaps are disjoint.

The multiplicity-two addresses already present in $H$ are precisely the
x-parallel lines inherited from the parent.  This statement neither places
nor compares two alternative words at the same gap.

## 3. Analytic radius-seven locality

Every connector has length at most five, so every interior prefix is the sum
of at most four MENU steps.  Its two lateral coordinates lie in
$[-8,8]^2$.

Suppose prefixes $p=(y,z)$ and $p'=(y',z')$ can collide after translation.
Their digits must agree.  Their carry difference is then

\[
c(p)-c(p')=
\left(
\frac{-(y-y')+3(z-z')}{9},
-\frac{y-y'}{3}
\right).
\]

Since $|y-y'|,|z-z'|\le16$, integrality gives

\[
|\Delta c_1|\le7,
\qquad
|\Delta c_2|\le5.
\]

Therefore

\[
\boxed{\|a_i-a_j\|_\infty>7
\quad\Longrightarrow\quad
\text{connectors at gaps }i,j\text{ cannot share a `yz` fibre}.}
\]

This bound is a theorem for every word over the radius-two MENU of length at
most five.  The pinned effective domains satisfy the sharper finite bound
$5$, as verified by the companion checker; radius $5$ is a pinned-cache
fact, while radius $7$ is the availability-independent analytic bound.

If every parent `yz` fibre contains at most two points, a radius-seven square
contains at most

\[
2(2\cdot7+1)^2=450

\]

parent gap occurrences.  Thus x-projection poisoning is a finite-range
constraint.  It has no far-secant tail.

This does not make the global online game finite automatically.  A
bounded-range constraint system can have long boundary dependencies or no
global extension, and the fragile-first schedule moves between distant
gaps.  A safety fixed point, extension theorem, SAT certificate, or comparable
global argument is still required.

## 4. Pinned finite role census

The companion checker streams the pinned 68,050,680-byte cache without
loading the domain pickles.  The checked census is:

- 12,537,146 effective words and 55,513,526 word slots;
- 42,976,380 interior-prefix occurrences;
- 217 distinct lateral prefix offsets and 39 distinct carries;
- all nine quotient digits occur;
- 291,414 step-specific ordered lateral-prefix signatures;
- 216,322 step-specific unordered projection masks;
- 201 to 8,059 projection masks per parent step;
- 9,687,350 words have no digit-zero interior prefix;
- 6,755,766 words have nonzero, pairwise-distinct interior digits;
- every one of the 124 parent steps has at least one such digit-simple word;
- the exact same-digit carry interaction radius in this cache is $5$.

These are domain counts, not survivor counts after exact secant poisoning.
A digit-simple word avoids child anchors and is internally projection-simple,
but two different realized gaps can still collide in a shared digit.

The current L6 policy was not restricted to digit-simple words.  For example,
the selected word `[0,5,0,55]` has prefix digits `(4,0,4)` and addresses

\[
(a+(0,2),4),\quad(a+(-1,1),0),\quad(a+(-1,3),4).
\]

It is projection-clean only because these actual coarse addresses are free.
This is a concrete obstruction to a residue-only or step-only state.

## 5. A 25-fibre local cage

Fibre multiplicity at most two does not imply positive connector
availability.

Fix a gap start with lateral coordinate $a$.  Occupy the 25 fibres

\[
a+[-2,2]^2.
\]

The central fibre already contains the start anchor.  The lateral projection
of every MENU step is one of exactly these 25 offsets.  Every domain word has
length at least two, so its first interior lies in an occupied fibre.
Therefore every connector word is projection-killed at its first interior.

This cage is compatible with an abstract finite triple-free point set: put
one point above each lateral fibre and choose its integer x-coordinate
successively.  At each choice, the finitely many earlier point-pairs forbid
only finitely many x-values, so an integer choice remains.

What is **not** proved is that this cage is reachable as a contiguous ordered
MENU walk, or reachable under the projection-fresh selector.  It is a
counterexample only to weak statements of the form

> triple-free plus `yz`-fibre multiplicity at most two implies a surviving
> connector.

A successful safety invariant must reserve capacity around unstitched gaps.

## 6. Exact scope and next test

The proved algebra and radius-seven theorem handle only x-parallel secant
births.  They do not control a secant whose direction has a nonzero `yz`
component.  Such a secant can still have both endpoints far from the stitch;
the far-secant lemma remains necessary.

The smallest decisive projection experiment is a mask-level SAT/CEGAR test
on the frozen L5-to-L6 state:

1. use one action variable for the selected role mask at each actual gap;
2. remove internally repeated and anchor-colliding masks;
3. add conflicts only between parent starts within analytic radius $7$;
4. ask for one simultaneous realized mask per gap;
5. if satisfiable, refine each mask to an exact 3D word and replay exact
   non-x legality, blocking failed refinements.

An UNSAT result would refute projection completion for that finite parent
state.  A SAT result would be a finite one-choice certificate, not an
all-level safety theorem.
