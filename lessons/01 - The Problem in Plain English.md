# Erdős Problem 193 — The Problem in Plain English

## The one-sentence version

Imagine a walker moving forever among the integer-coordinate points of three-dimensional space. The walker may reuse only a **finite menu of step types**. Must the visited points eventually include three points lying on one straight line?

That is the whole question.

---

## First, picture the world

A point of $\mathbb{Z}^3$ is simply a location with three integer coordinates, such as

$$
(4,-2,7).
$$

Think of infinitely large three-dimensional graph paper. The walker may stand only where the grid lines meet.

The notation $\mathbb{Z}^3$ means:

- $\mathbb{Z}$: the integers $\ldots,-2,-1,0,1,2,\ldots$
- the exponent $3$: each point has three coordinates

No advanced idea is hiding here.

---

## What is the finite set $S$?

$S$ is a fixed, finite menu of allowed **step vectors**.

For example, suppose

$$
S=\{(1,0,0),(0,1,0),(0,0,1)\}.
$$

Then every move must go one unit in one of the three positive coordinate directions. The walker may use each allowed step as often as desired, but may never invent a fourth kind of step.

This distinction matters:

> **The menu of step types is finite. The walk itself is infinite.**

A finite menu does not trap the walker in a finite region. Repeatedly taking $(1,0,0)$ already travels arbitrarily far.

---

## Decoding the step formula

If the visited points are

$$
a_1,a_2,a_3,\ldots,
$$

then

$$
a_{i+1}-a_i\in S
$$

just says:

> Subtract the current location from the next location. The resulting move must be one of the allowed moves in $S$.

For example, if

$$
a_i=(4,-2,7)
$$

and

$$
a_{i+1}=(5,-2,7),
$$

then the step was

$$
a_{i+1}-a_i=(1,0,0).
$$

---

## What counts as three collinear points?

Three distinct points are **collinear** when one straight line passes through all three.

They do **not** have to be:

- consecutive points in the walk;
- equally spaced;
- visited in their order along the line.

For example,

$$
(0,0,0),\qquad (2,2,2),\qquad (5,5,5)
$$

are collinear. All three lie on the diagonal line whose coordinates grow together. The gaps are different, but that does not matter.

This is a global condition: a point visited today could complete a line with any two points visited much earlier.

---

## What does “must” mean?

The original question asks whether **every** infinite walk with a finite step menu must contain a collinear triple.

There are two possible kinds of answer:

### A “yes” proof

Show that no matter how someone chooses the finite menu and no matter how cleverly they walk, three collinear visited points are unavoidable.

### A “no” proof

Produce one counterexample:

1. one particular finite step menu $S$;
2. one particular infinite walk using only steps from $S$;
3. a proof that this walk never contains three distinct collinear points.

The construction in this project claims the second outcome: **no**. It constructs such a counterexample. The construction and its no-three-collinear property have been formalized in Lean; independent mathematical review is still pending.

---

## Why this is not easy

Avoiding a collinear triple for the first 100 or one million points is a finite computation.

The problem asks for an **infinite guarantee**. Every new point must avoid completing a line determined by every earlier pair of points, while the walker remains restricted to the same finite step menu forever.

Those demands pull in opposite directions:

- avoiding old lines seems to require ever more freedom;
- the finite step menu permanently limits the available moves.

The proof needs a repeating structure that supplies both freedom and a permanent reason collinearity cannot occur.

---

## Your from-memory summary skeleton

Without looking back, try to complete this sentence:

> Erdős Problem 193 asks whether every __________ walk through __________ using only __________ possible step vectors must eventually visit __________ points on one __________.

Do not worry about polished wording yet.

---

## Calibration questions

Answer these in your own words, without trying to sound mathematical:

1. What is finite in the problem, and what is infinite?
2. What does $a_{i+1}-a_i$ represent?
3. Do the three collinear points need to be consecutive or equally spaced?
4. Because the claimed answer is “no,” what three things must the construction provide or prove?
5. Which phrase or idea in this note still feels least clear?

Your answers will determine how much geometry and proof language the next note should introduce.
