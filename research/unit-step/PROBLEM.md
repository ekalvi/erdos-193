# Minimum dimension for a no-three-collinear unit-step walk

**Open follow-up problem, not the original Erdős Problem 193.**

Let $\mathbb Z^d$ be the integer lattice in dimension $d$, and let
$e_1,\ldots,e_d$ be its standard basis vectors: $e_r$ has a $1$ in coordinate
$r$ and zeros elsewhere.

Determine the smallest positive integer $d_*$ for which there exists an infinite
sequence $(P_n)_{n\ge0}$ in $\mathbb Z^{d_*}$ satisfying:

1. **Start at the origin:** $P_0=0$.
2. **Take positive unit steps:**

   $$
   P_{n+1}-P_n\in\{e_1,\ldots,e_{d_*}\}\qquad(n\ge0).
   $$

3. **No three vertices are collinear:**

   $$
   (k-j)(P_j-P_i)\ne(j-i)(P_k-P_j)
   \qquad(0\le i<j<k).
   $$

The last condition is equivalent to noncollinearity because the coordinates
of $P_n$ sum to $n$.

## Current proof status

$$
\boxed{d_*\ge4\text{ is proved};\qquad d_*\le6\text{ is proposed, pending independent review}.}
$$

Thus the working target is $d_*\in\{4,5,6\}$, subject to vetting the six-dimensional
draft. This is a problem to solve, **not a conjecture that $d_*=6$**. Existence
of some finite upper bound is supplied by Shallit's 16D manuscript; the original
finite-step construction also admits a standard-basis encoding.

The goal is to determine $d_*$ exactly by proving existence in that dimension
and impossibility in every smaller dimension. Embedding a walk by appending
zero coordinates preserves the property, so impossibility in dimension $d_*-1$
suffices for all smaller dimensions.

## Exactly equivalent combinatorial problem

Determine the smallest alphabet size admitting an infinite word with no two
consecutive nonempty blocks $x,y$ such that

$$
\frac{\psi(x)}{|x|}=\frac{\psi(y)}{|y|},
$$

where $\psi$ counts each letter. The block lengths need not be equal. Such a
pair is a **weak abelian square**. The cumulative letter-count vectors are
exactly the unit-step vertices. This equivalence is Proposition 1 of Shallit's
[16D manuscript](../../paper/followups/2026-09-04-shallit-N16.pdf).

## Scope and completion criteria

- Seek an unconditional infinite theorem and a sharp lower bound, not merely
  long finite examples or optimality inside one construction family.
- Reconcile the geometric, arithmetic, and combinatorial explanations.
- Use the four-collinear/weak-abelian-cube draft only when it clarifies the
  common mechanism. It does not settle this triples problem.
- Treat practical applications as optional questions, not required or
  established consequences.
- Aim toward a joint synthesis by Stijn Cambie, Erik Kalviainen, and Jeffrey
  Shallit, subject to their agreement. This checkpoint does not assign a new
  paper's authorship or change the original paper's byline.

See the [AI resume checkpoint](AI-CHECKPOINT.md) for evidence and next actions.
