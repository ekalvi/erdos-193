# Hilbert–base-4 selector approach: current status

**Status:** exploratory construction programme, not a proof or candidate infinite walk.

## 1. Starting idea

Start with a planar Hilbert staircase

$$
H_n=(x_n,y_n)\in\mathbb Z^2
$$

and lift time into the third coordinate:

$$
P_n=(x_n,y_n,n)\in\mathbb Z^3.
$$

Each planar unit move becomes one of four three-dimensional moves:

$$
(\pm1,0,1),\qquad(0,\pm1,1).
$$

Thus the unthinned lifted staircase has a fixed finite step menu and never repeats a vertex.

The question is whether Hilbert recursion, combined with selecting only some points, can prevent three selected points from being collinear.

## 2. Exact meaning of collinearity

For $i<j<k$, the lifted points $P_i,P_j,P_k$ are collinear exactly when

$$
\frac{H_j-H_i}{j-i}
=
\frac{H_k-H_j}{k-j}.
$$

Equivalently, define the planar defect

$$
D(i,j,k)
=
(k-j)(H_j-H_i)
-
(j-i)(H_k-H_j).
$$

Then

$$
P_i,P_j,P_k\text{ collinear}
\iff
D(i,j,k)=(0,0).
$$

Interpretation:

> Two adjacent time intervals are fatal when they have exactly the same average planar displacement.

This is a useful and dimension-correct reformulation of Erdős Problem 193.

## 3. Why the complete Hilbert staircase fails

The standard order-2 Hilbert path already contains

$$
H_3=(0,1),\qquad H_4=(0,2),\qquad H_5=(0,3).
$$

After lifting,

$$
P_3=(0,1,3),\quad
P_4=(0,2,4),\quad
P_5=(0,3,5),
$$

and

$$
P_4-P_3=P_5-P_4=(0,1,1).
$$

Therefore the full lifted Hilbert path fails at order 2.

Every higher-order Hilbert grid contains rotated or reflected copies of this local pattern. Consequently:

$$
\boxed{\text{No complete Hilbert grid of order }m\ge2\text{ can be used unchanged.}}
$$

The time lift remains useful, but the standard Hilbert path itself is not a solution.

## 4. What thinning must preserve

Suppose we retain indices

$$
n_0<n_1<n_2<\cdots
$$

and use the selected points $P_{n_r}$.

The resulting step has vertical component

$$
n_{r+1}-n_r.
$$

Therefore a fixed finite step menu requires

$$
n_{r+1}-n_r\le B
$$

for some uniform constant $B$.

This is the central constraint on any selector:

$$
\boxed{\text{The selected index set must have bounded gaps.}}
$$

An arbitrarily sparse triple-free subsequence would not solve Erdős 193, because its $z$-increments could be unbounded.

Keeping the omitted Hilbert vertices as intermediate steps would not help: omitted vertices would then still be placed points and would still count in the collinearity condition.

## 5. Natural thinning rules tested so far

### 5.1 Keep only turning vertices

This removes the immediate straight-run triples and has gaps at most 3.

It still contains the lifted triple at indices

$$
8,\quad12,\quad16.
$$

At order 3, one orientation gives

$$
(2,2,8),\qquad(1,3,12),\qquad(0,4,16),
$$

whose adjacent differences are both

$$
(-1,1,4).
$$

So eliminating consecutive equal steps does not eliminate longer equal-average chords.

### 5.2 Keep one residue class modulo $q$

Selections

$$
n\equiv r\pmod q
$$

have constant gaps and therefore a finite menu.

Every residue class for every

$$
2\le q\le16
$$

was found to contain a triple by Hilbert order 6.

This is finite computational evidence against simple periodic decimation, not a theorem against all periodic selectors.

### 5.3 Repeat the order-2 deletion mask

The lifted $4\times4$ tile has exactly two internal triples:

$$
\{3,4,5\},\qquad\{10,11,12\}.
$$

Deleting one point from each produces a triple-free subset of 14 of the 16 points. For example, deleting 4 and 11 works and leaves gaps at most 2.

Repeating that rule according to the local residue modulo 16 fails at the next Hilbert level: it retains the triple

$$
8,\quad12,\quad16.
$$

In base 4,

$$
8=020_4,\qquad
12=030_4,\qquad
16=100_4.
$$

This shows that a selector cannot look only at a fixed suffix of the address. It must understand parent-cell boundaries and orientation.

## 6. Why simply chaining identical grids fails

Suppose identical tile copies are related by a constant lifted translation $T$. A fixed local point $U$ then appears as

$$
U,\qquad U+T,\qquad U+2T
$$

in three consecutive copies.

Those three points are automatically collinear.

A periodically repeating sequence of tile types has the same problem over one full period whenever the macro-placement repeats by a constant translation.

Therefore:

$$
\boxed{\text{The tile chain and selector must be genuinely aperiodic at the macro scale.}}
$$

Changing the tile size alone cannot defeat exact repetition.

## 7. Fixed-size supertiles

Choose an order-$m$ Hilbert grid as a fixed supertile. It has

$$
L=4^m
$$

positions and side length

$$
2^m.
$$

Partition the infinite index sequence into aligned blocks

$$
B_a=\{aL,\ldots,(a+1)L-1\}.
$$

If at least one point is selected from every block, consecutive selected indices differ by at most

$$
2L-1=2\cdot4^m-1.
$$

Provided the physical tiles use finitely many adjacent placements and orientations, the resulting three-dimensional displacement menu is finite.

Selecting exactly one representative per tile is particularly clean:

- no triple can lie entirely inside one tile;
- the problem becomes choosing one local address per tile;
- every remaining obstruction crosses tile boundaries.

However, “one point per tile” is only a coverage guarantee. It does not ensure that one of the tile's candidates survives all lines created by earlier selected pairs.

## 8. Why base 4 is the natural language

Hilbert recursion has four children at every level. An order-$m$ point has address

$$
(q_{m-1}\cdots q_1q_0)_4,
\qquad q_i\in\{0,1,2,3\}.
$$

Each digit chooses a child quadrant, with an associated rotation or reflection.

Base 4 therefore describes:

- common Hilbert-cell prefixes;
- the first level where points separate;
- orientation transitions;
- parent-cell boundaries;
- recursive selector states.

A hexadecimal formulation was considered and discarded. It grouped base-4 digits conveniently but introduced no useful theorem. The approach now uses base 4 directly.

## 9. Candidate grid size: $16\times16$

A $16\times16$ grid is Hilbert order 4. It has

$$
4^4=256
$$

local positions with addresses

$$
(q_3q_2q_1q_0)_4.
$$

If exactly one point is selected per order-4 tile, the selected-index gap is bounded by

$$
511.
$$

Why order 4 might help:

- 256 choices per tile;
- four complete recursive address levels;
- enough context to distinguish local, parent-boundary, and higher-boundary behavior;
- still finite enough for exact transition enumeration.

Why it might not help:

- more candidates do not by themselves control the unbounded number of old secants;
- the selector still has to avoid triples spanning arbitrarily distant tiles;
- a fixed-size tile cannot win by simple counting;
- increasing the grid size may only postpone the first counterexample.

There is currently no proof that $16\times16$ is sufficient or optimal. It is a plausible laboratory size, not a mathematically established threshold.

## 10. Proposed selector structure

The current conceptual selector is a finite-state process reading base-4 address digits.

A state might contain

$$
s=(o,c,b),
$$

where:

- $o$ is the current Hilbert rotation/reflection;
- $c$ records base-4 congruence or carry information;
- $b$ records entry, exit, interior, or parent-boundary status.

For an order-4 tile:

$$
s_0\xrightarrow{q_3}s_1
\xrightarrow{q_2}s_2
\xrightarrow{q_1}s_3
\xrightarrow{q_0}s_4.
$$

The final state decides whether the address is retained or belongs to the candidate set.

The selector could be either:

1. **Deterministic:** one representative address for each macro-state.
2. **Adaptive:** a finite candidate set for each state, with one surviving choice selected after accounting for relevant previous secants.

The adaptive version offers more availability but requires a stronger closure theorem.

## 11. Proposed proof mechanism

The promising base-4 idea is not a fixed digit mask. It is recursive descent by common prefixes.

Take three selected addresses and remove their longest common base-4 prefix.

### 11.1 Same-child case

If all three points lie in the same child, that child is an invertible rotated or reflected copy of a smaller Hilbert grid.

Collinearity is preserved by that affine map, so the triple reduces to a lower-level selector state.

This part is exact.

### 11.2 Cross-child case

If the addresses first differ at the current digit, their child labels form one of finitely many coarse patterns.

The hoped-for lemma is:

> For every reachable selector state and every cross-child pattern, one coordinate of the defect $D(i,j,k)$ has a nonzero first base-4 digit.

If that can be proved, then

$$
D(i,j,k)\neq0,
$$

and the triple is not collinear.

The induction would be:

$$
\text{remove common prefix}
\longrightarrow
\begin{cases}
\text{recurse inside one child},\\
\text{or expose a nonzero base-4 defect digit}.
\end{cases}
$$

## 12. What “linearity in the digits” means

A zero integer has every base-4 digit zero. Therefore, to prove

$$
D\neq0,
$$

it is enough to identify one scale $r$ where

$$
D_x/4^r\not\equiv0\pmod4
$$

or

$$
D_y/4^r\not\equiv0\pmod4.
$$

The selector would attempt to force that nonzero digit at the first Hilbert level where the three addresses separate.

This is the precise possible connection between positional digits and linearity:

- a line forces the weighted chord defect to vanish at every scale;
- the selector tries to force a nonvanishing digit at one recursively determined scale.

The difficulty is carries. A coarse nonzero-looking contribution can be cancelled by lower-level contributions and carries. A valid proof must track those exactly, not reason digitwise as though carries were absent.

## 13. Required certificate

A complete construction would need all of the following.

### 13.1 Coverage

Every order-4 supertile contains at least one selected point.

### 13.2 Uniform bounded gaps

The maximum gap remains bounded independently of recursion depth.

This can be tracked recursively using:

- first selected position;
- last selected position;
- largest internal gap;
- whether a child block is empty.

### 13.3 Reachable-state closure

Every reachable selector state has at least one legal successor. A long finite chain is insufficient.

### 13.4 Same-child induction

All selector states reachable inside oriented child cells satisfy the same triple-free theorem.

### 13.5 Cross-child nonvanishing

Every triple whose addresses first separate at the current level has

$$
D\neq0.
$$

### 13.6 No ambiguous carry cycle

There must not be a reachable recursive cycle in which the tested base-4 digit remains zero and the proof continually defers to another scale.

This last condition is likely decisive. If such cycles exist, the base-4 state is only a finite filter and does not control arbitrarily far secants.

## 14. Relationship to the existing project

This approach is consistent with the project's broader scale-and-tile programme:

- choose among finitely many local paths or representatives;
- retain a finite step menu;
- reject choices poisoned by old secants;
- seek a successor-closed state space;
- prove that far secants cannot return indefinitely.

The existing work shows that finite local availability is not enough. Far lines can remain silent for arbitrarily long periods and later return.

The Hilbert/base-4 approach is genuinely new only if its address recursion supplies a strict descent or nonzero-digit certificate for those far lines. Without that, it becomes another geometric encoding of the same unresolved far-secant problem.

## 15. Current status

### 15.1 Established exactly

- The time lift converts collinearity into equality of average planar displacement.
- The full Hilbert staircase fails at order 2.
- Every full higher-order Hilbert grid inherits local bad triples.
- A valid selector must have bounded gaps.
- The order-2 lifted tile has exactly two internal triples and a 14-point triple-free subset.
- Turning-point selection fails.
- Simple residue-class selections through modulus 16 fail at tested finite levels.
- Repeating the order-2 deletion mask fails at the next level.
- Periodically translated identical tiles create immediate macro-scale triples.
- One selection per fixed-size tile guarantees a finite step menu, but not triple-freeness.

### 15.2 Plausible but unproved

- A finite-state, orientation-aware base-4 selector may exploit Hilbert recursion.
- An order-4 $16\times16$ supertile may provide enough local choice and context.
- Cross-child collinearity might admit a first-nonzero-base-4-digit certificate.
- Dangerous far secants might compress into finitely many carry/address states.

### 15.3 Completely open

- Whether any bounded-gap triple-free Hilbert subset exists.
- Whether one representative per fixed supertile can be chosen forever.
- Whether the relevant carry state is finite.
- Whether cross-child ambiguity admits a strict descent.
- Whether increasing the tile size helps fundamentally rather than delaying failure.
- Whether the resulting construction can be made successor-closed and unconditional.

## 16. Bottom line

The approach has progressed from a geometric picture to a precise research programme:

$$
\boxed{
\begin{gathered}
\text{lifted Hilbert staircase}\\
+\ \text{bounded-gap selection}\\
+\ \text{one representative per fixed supertile}\\
+\ \text{orientation-aware base-4 automaton}\\
+\ \text{recursive nonzero-digit certificate}.
\end{gathered}
}
$$

It is **not currently a construction or proof**. Its strongest merit is that Hilbert addresses provide an exact recursive notion of the first scale where three points separate. Its central risk is that base-4 carries and far secants may require unbounded state, reproducing the obstruction already encountered in the main project.

The decisive question is:

> Can every cross-child collinearity candidate be forced either to reveal a nonzero base-4 defect digit or to descend to a strictly smaller state, with no infinite ambiguous cycle?

A positive answer would give the approach proof-level substance. A negative answer would show that Hilbert recursion organizes the obstruction but does not eliminate it.
