# Erdős 193 — Powers of Two as a Fingerprint

**Main prerequisite:** [02 - Trace, Select, and Lift](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md)  
**Clarification:** [03 - Why the Gaps Are 4 to 28](03%20-%20Why%20the%20Gaps%20Are%204%20to%2028.md)  
**Optional machinery for later:** [03A - Why I, S, T, and C Choose Those Offsets](03A%20-%20Why%20I%2C%20S%2C%20T%2C%20and%20C%20Choose%20Those%20Offsets.md)

## We are reopening the intended black box

At the end of [Note 02](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md), the unexplained step was:

> An arithmetic fingerprint of every planar chord between selected Hilbert points prevents three lifted points from being collinear.

That fingerprint is built from powers of two. You do **not** need to understand the orientation transformations to understand this lesson.

We will build the idea in two layers:

1. the power-of-two fingerprint of an ordinary integer;
2. the custom fingerprint of a two-dimensional vector.

---

## Layer 1: how many factors of two does an integer contain?

Take a nonzero integer and repeatedly divide it by 2 until the result is odd.

The number of successful divisions is called its **2-adic valuation**, written

$$
\nu_2(n).
$$

Despite the technical name, it is just a count of factors of 2.

| Number | Factorization | Number of factors of 2 | $\nu_2$ |
|---:|---:|---:|---:|
| $7$ | $7$ | $0$ | $0$ |
| $18$ | $2\cdot9$ | $1$ | $1$ |
| $12$ | $4\cdot3$ | $2$ | $2$ |
| $40$ | $8\cdot5$ | $3$ | $3$ |
| $48$ | $16\cdot3$ | $4$ | $4$ |

So:

- odd numbers have valuation 0;
- numbers divisible by 2 but not 4 have valuation 1;
- numbers divisible by 4 but not 8 have valuation 2;
- and so on.

For a negative number, use its absolute value. The proof also adopts the convention

$$
\nu_2(0)=\infty,
$$

which simply means that zero is divisible by every power of two. We will rarely need to think about that special case directly.

---

## The binary viewpoint

In binary, $\nu_2(n)$ is the number of zeros at the right-hand end of the number.

For example,

$$
40=101000_2.
$$

It ends with three zeros, so

$$
\nu_2(40)=3.
$$

This binary viewpoint matters because the discrete Hilbert path converts base-4 index digits into pairs of binary coordinate digits.

---

## Two rules we will use later

### Multiplication adds valuations

If two nonzero integers are multiplied, their factors of two accumulate:

$$
\nu_2(ab)=\nu_2(a)+\nu_2(b).
$$

For example,

$$
12\cdot10=(4\cdot3)(2\cdot5)=8\cdot15,
$$

so

$$
\nu_2(12\cdot10)=2+1=3.
$$

### Two odd numbers have an even sum

If $r$ and $s$ are both odd, then $r+s$ is even. Therefore

$$
\nu_2(r+s)\ge1.
$$

This elementary fact will eventually provide the final contradiction in the no-collinear-triple proof.

---

## Layer 2: a fingerprint for a planar vector

A planar chord is a vector

$$
u=(u_x,u_y).
$$

We want one number that records the first binary scale at which this vector becomes visible.

Here is the procedure in plain language.

### Step A: remove the largest common power of two

Find the largest power of two dividing **both** coordinates. Suppose that common power is $2^p$.

Equivalently,

$$
p=\min\{\nu_2(u_x),\nu_2(u_y)\}.
$$

Divide both coordinates by $2^p$. At least one resulting coordinate must now be odd.

### Step B: record which parity pattern remains

After removing the common power:

- either exactly one coordinate is odd and the other is even;
- or both coordinates are odd.

The vector fingerprint $V(u)$ encodes both the scale $p$ and this final one-bit distinction:

$$
V(u)=
\begin{cases}
2p, & \text{if exactly one reduced coordinate is odd},\\
2p+1, & \text{if both reduced coordinates are odd}.
\end{cases}
$$

> [!warning] Do not confuse $p$ with $2^p$
> If the largest common power is $2^p=2$, then $p=1$. The expression $2p$ means $2\times p=2$, not $2\times2^p=4$.

So an even value of $V$ means “one coordinate first appears at this binary scale,” while an odd value means “both coordinates first appear at this scale.”

> [!important]
> $V(u)$ does not identify the vector. Many different vectors have the same fingerprint. It records only a power-of-two scale and a one-coordinate-versus-both-coordinates pattern.

---

## Examples of vector fingerprints

### Example 1: $u=(6,12)$

The coordinate valuations are

$$
\nu_2(6)=1,\qquad \nu_2(12)=2.
$$

The largest common power is $2^1$. Dividing by 2 gives

$$
(3,6).
$$

Exactly one coordinate is odd, so

$$
V(6,12)=2\cdot1=2.
$$

### Example 2: $u=(6,10)$

Both coordinates have valuation 1. Dividing by 2 gives

$$
(3,5).
$$

Both coordinates are odd, so

$$
V(6,10)=2\cdot1+1=3.
$$

### Example 3: $u=(12,20)$

Both coordinates have valuation 2. Dividing by 4 gives

$$
(3,5).
$$

Both reduced coordinates are odd, so

$$
V(12,20)=2\cdot2+1=5.
$$

### Example 4: $u=(8,12)$

The coordinate valuations are 3 and 2. Dividing both by 4 gives

$$
(2,3).
$$

Exactly one reduced coordinate is odd, so

$$
V(8,12)=2\cdot2=4.
$$

The alternating pattern is:

| $V(u)$ | Common power removed | Pattern afterward |
|---:|---:|---|
| $0$ | $1$ | exactly one coordinate odd |
| $1$ | $1$ | both coordinates odd |
| $2$ | $2$ | exactly one coordinate odd |
| $3$ | $2$ | both coordinates odd |
| $4$ | $4$ | exactly one coordinate odd |
| $5$ | $4$ | both coordinates odd |

---

## What scaling does to the fingerprint

Suppose a vector $u$ is multiplied by a positive integer $k$.

Every factor of two in $k$ is added to both coordinates. The common scale $p$ therefore increases by $\nu_2(k)$, while the one-odd-versus-both-odd pattern stays unchanged.

Consequently,

$$
V(ku)=V(u)+2\nu_2(k).
$$

Three useful special cases are:

- multiplying by an odd number leaves $V$ unchanged;
- multiplying by 2 increases $V$ by 2;
- multiplying by 4 increases $V$ by 4.

For example,

$$
u=(3,5)
$$

has fingerprint 1 because both coordinates are odd. Multiplying by 4 gives

$$
4u=(12,20),
$$

whose fingerprint is 5. The increase is

$$
2\nu_2(4)=2\cdot2=4.
$$

This scaling rule is the lever used against collinearity.

---

## The Hilbert pair law

Now we can state the crucial theorem without proving it yet.

Take two different Hilbert indices $m$ and $n$ with the same terminal state. Their planar chord is

$$
H(n)-H(m).
$$

The pair law says

$$
V\bigl(H(n)-H(m)\bigr)=\nu_2(|n-m|).
$$

In words:

> For same-state Hilbert indices, the power-of-two fingerprint of the planar displacement is exactly the number of factors of two in the index gap.

The index gap does not determine the entire planar chord. It determines this particular fingerprint exactly.

## What is standard—and what this proof introduces

The ingredients come from different layers.

### Established background

- The ordinary 2-adic valuation $\nu_2(n)$ is classical mathematics.
- Its rules, such as
  $$
  \nu_2(ab)=\nu_2(a)+\nu_2(b),
  $$
  are standard.
- The discrete Hilbert recursion and its four-child Gray-code order are also established constructions. The manuscript cites Hilbert and Sagan for that background.

### Purpose-built for this proof

The scalar vector fingerprint

$$
V(u)=2p(u)+\epsilon(u)
$$

is introduced in this manuscript. It packages two familiar pieces of 2-adic information:

1. the largest common power-of-two exponent $p(u)$ in the two coordinates;
2. one bit $\epsilon(u)$ recording whether the reduced coordinates are both odd or only one is odd.

So the raw ingredients are standard, while this exact packaging is a custom invariant designed for the proof. The coefficient 2 is chosen so that multiplying both vector coordinates by $k$ changes the fingerprint by

$$
2\nu_2(k),
$$

whereas multiplying one integer gap by $k$ changes its valuation by only $\nu_2(k)$. That deliberate mismatch is what later contradicts collinearity.

The same-terminal-state Hilbert pair law is the substantial proof-specific theorem:

$$
V\bigl(H(n)-H(m)\bigr)=\nu_2(|n-m|).
$$

It is not a generic law of arbitrary planar vectors, nor a standard fact about every Hilbert-curve convention. It is proved here for this nested discrete Hilbert indexing by combining the first base-4 mismatch, the Gray-code child corners, and the shared terminal-state rewind.

> [!warning] What “new” can safely mean
> The fingerprint definition and pair-law proof are new components of this repository and manuscript: they are introduced and proved here rather than cited from an earlier source. The Lean formalization checks that the theorem follows from the definitions; it does **not** establish historical priority or worldwide literature novelty. The manuscript has not completed external mathematical peer review, so the safe claim is **proof-specific work introduced here**, not yet **certified as never previously discovered in any equivalent form**.

---

## Three concrete interpretations

If the index gap has valuation 2, then the chord has fingerprint 2:

$$
\nu_2(|n-m|)=2
\quad\Longrightarrow\quad
V(H(n)-H(m))=2.
$$

That means both planar coordinate changes share one factor of 2, and after removing it exactly one is odd.

If the index gap has valuation 3, then the chord has fingerprint 3. Both coordinate changes share one factor of 2, and after removing it both are odd.

If the index gap has valuation 4, then the chord has fingerprint 4. Both coordinate changes share two factors of 2, and after removing them exactly one is odd.

The fingerprint alternates between “one coordinate appears” and “both coordinates appear” as the valuation of the index gap moves between even and odd values.

---

## Why the same-state condition appears

At an intuitive level, compare the base-4 representations of $m$ and $n$ from the low end.

- Their common low digits produce matching low binary coordinate bits.
- At the first base-4 digit where they differ, either one coordinate bit changes or both coordinate bits change.
- The terminal-state condition ensures the two indices interpret that first mismatch in the same orientation.

That is why the time-gap valuation and the chord fingerprint match.

This paragraph is enough for now. We do not need the full transformation table to use the pair law in the collinearity argument.

---

## Where this fits in the proof

From [Note 02](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md):

1. the selector puts every retained index into the same terminal state;
2. therefore the pair law applies to every pair of retained points;
3. the lift uses the index gap as the height gap;
4. collinearity would force planar chords to scale according to those height gaps;
5. the scaling rule for $V$ will make that impossible.

The next lesson will perform those five steps explicitly.

---

## Checkpoint

1. What are $\nu_2(40)$, $\nu_2(18)$, and $\nu_2(7)$?
2. Why do $(6,12)$ and $(6,10)$ have different vector fingerprints?
3. If $V(u)=3$, what is $V(4u)$?
4. State the Hilbert pair law in ordinary language.
5. What information does $V(u)$ deliberately throw away?
6. Which part feels least intuitive: integer valuation, vector fingerprint, scaling, or the pair-law connection?
