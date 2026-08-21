# Erdős 193 — How to Read the Hilbert Digit Notation

**Return afterward to:** [Lesson 05 — One base-4 digit emits two coordinate bits](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md#one-base-4-digit-emits-two-coordinate-bits)  
**Place-value background:** [Lesson 05A](05A%20-%20Why%20Matching%20Final%20Digits%20Forces%20Divisibility.md)

## Purpose of this note

The compact notation in Lesson 05 assumes several conventions at once. None of them is conceptually deep, but reading them simultaneously can make the Hilbert rule look more mysterious than it is.

This note decodes each symbol before returning to the mathematics.

---

## First: what is $H(n)$?

Think of $H$ as a machine:

- input: one nonnegative integer $n$, the time or index along the Hilbert path;
- output: one point on the two-dimensional integer grid.

Writing

$$
H(n)=(x(n),y(n))
$$

means:

- $x(n)$ is the horizontal coordinate produced from index $n$;
- $y(n)$ is the vertical coordinate produced from index $n$.

For example, the construction has

$$
H(80)=(0,12).
$$

This says that index 80 maps to the planar point whose $x$-coordinate is 0 and whose $y$-coordinate is 12.

The parentheses in $x(n)$ mean “the value of $x$ produced from input $n$.” They do not mean multiplication.

---

## What is a position $k$?

A numeral has digit positions. Count them from the right, starting at zero.

For the base-4 numeral

$$
123_4,
$$

the positions are:

| Position | $2$ | $1$ | $0$ |
|---:|---:|---:|---:|
| Digit | $1$ | $2$ | $3$ |
| Place value | $4^2=16$ | $4^1=4$ | $4^0=1$ |

The letter $k$ is a variable standing for whichever position we are discussing:

- $k=0$: the rightmost position;
- $k=1$: the next position to the left;
- $k=2$: the next one;
- and so on.

It is like saying “player number $k$” when we want one statement that applies to every player. The letter is a reusable label, not one fixed position.

---

## What is $q_k$?

The letter $q$ is used for a base-4 digit. The subscript tells us its position.

Thus

$$
q_k
$$

means:

> the base-4 digit occupying position $k$.

For

$$
n=123_4,
$$

we have

$$
q_0=3,
\qquad
q_1=2,
\qquad
q_2=1.
$$

The subscript is not multiplication and not an exponent. It is an address saying where the digit lives.

Because this is base 4, every $q_k$ must be one of the four allowed digits:

$$
q_k\in\{0,1,2,3\}.
$$

The symbol $\in$ means “is an element of” or, more plainly, “is one of.” Therefore the displayed statement says:

> The digit at position $k$ is one of 0, 1, 2, or 3.

---

## What is a bit?

A **bit** is one binary digit. It can have only two values:

$$
0\quad\text{or}\quad1.
$$

The set of possible bit values is written

$$
\{0,1\}.
$$

Curly braces mean “the set containing these possibilities.”

---

## What does $\{0,1\}^2$ mean?

Here the superscript 2 does **not** mean that 0 and 1 are being squared.

It means:

> Make an ordered pair with two slots, choosing each slot from $\{0,1\}$.

There are four possible pairs:

$$
\{0,1\}^2
=
\{(0,0),(0,1),(1,0),(1,1)\}.
$$

Therefore

$$
(x_k,y_k)\in\{0,1\}^2
$$

means:

- $x_k$ is one bit, either 0 or 1;
- $y_k$ is another bit, either 0 or 1;
- together they form one of the four listed ordered pairs.

The order matters: $(0,1)$ and $(1,0)$ are different because the first slot belongs to $x$ and the second belongs to $y$.

---

## What does “emits” mean?

“Emits” is computer-science language for **outputs**.

At base-4 position $k$, the Hilbert decoding rule:

1. reads the index digit $q_k$;
2. keeps track of the current orientation of the recursive square;
3. outputs one pair of bits $(x_k,y_k)$.

In the basic orientation, the output table is:

| Input digit $q_k$ | Output pair $(x_k,y_k)$ |
|---:|---:|
| $0$ | $(0,0)$ |
| $1$ | $(0,1)$ |
| $2$ | $(1,1)$ |
| $3$ | $(1,0)$ |

So, for example, in the basic orientation:

- reading digit 0 outputs x-bit 0 and y-bit 0;
- reading digit 2 outputs x-bit 1 and y-bit 1;
- reading digit 3 outputs x-bit 1 and y-bit 0.

A rotated or reflected recursive square may change which pair is output. That orientation machinery comes later. The foundational point is that one input digit always produces exactly two output bits: one destined for $x$ and one for $y$.

---

## Why can one base-4 digit correspond to two bits?

A base-4 digit has four possible values:

$$
0,1,2,3.
$$

A pair of bits also has four possible values:

$$
(0,0),(0,1),(1,0),(1,1).
$$

So there is exactly enough information in one base-4 digit to choose one two-bit pair:

$$
4\text{ possibilities}=2\times2\text{ possibilities}.
$$

Geometrically, one recursive square has four child squares. The bit pair says whether the chosen child lies in the low or high half of each coordinate:

- first bit: low or high half in $x$;
- second bit: low or high half in $y$.

The Hilbert order uses

$$
(0,0),(0,1),(1,1),(1,0)
$$

rather than ordinary binary counting order. This makes consecutive child choices share an edge: each consecutive pair changes only one coordinate bit.

---

## What is $x_k$?

The symbol $x_k$ means:

> the bit that the Hilbert decoder places at binary position $k$ of the final $x$-coordinate.

Similarly, $y_k$ is the bit placed at binary position $k$ of the final $y$-coordinate.

For example, suppose a decoder has produced these three x-bits:

| Binary position $k$ | $2$ | $1$ | $0$ |
|---:|---:|---:|---:|
| Bit $x_k$ | $0$ | $1$ | $1$ |
| Place value | $2^2=4$ | $2^1=2$ | $2^0=1$ |

Then the x-coordinate has binary representation

$$
011_2
$$

and decimal value

$$
0\cdot4+1\cdot2+1\cdot1=3.
$$

If the corresponding y-bits are

| Binary position $k$ | $2$ | $1$ | $0$ |
|---:|---:|---:|---:|
| Bit $y_k$ | $1$ | $1$ | $0$ |
| Place value | $2^2=4$ | $2^1=2$ | $2^0=1$ |

then

$$
y=110_2=1\cdot4+1\cdot2+0\cdot1=6.
$$

The resulting point is

$$
(x,y)=(3,6).
$$

This example only illustrates how emitted bits are assembled into coordinates; it is not claiming that a particular Hilbert index maps to $(3,6)$.

---

## Why are there summation signs?

The symbol

$$
\sum_k
$$

means “add the following expression for every relevant position $k$.”

Thus

$$
x(n)=\sum_k x_k2^k
$$

is shorthand for

$$
x(n)=x_0\cdot2^0+x_1\cdot2^1+x_2\cdot2^2+x_3\cdot2^3+\cdots.
$$

This is not a new Hilbert-specific operation. It is simply the ordinary place-value rule for reading a binary numeral.

Likewise,

$$
y(n)=\sum_k y_k2^k
$$

means

$$
y(n)=y_0\cdot2^0+y_1\cdot2^1+y_2\cdot2^2+y_3\cdot2^3+\cdots.
$$

Only finitely many bits are nonzero for any particular finite index, so these sums are ordinary finite place-value calculations in practice.

---

## Translating the original paragraph into ordinary language

The compact version says:

> At every base-4 position $k$, the Hilbert rule reads digit $q_k$ and emits $(x_k,y_k)\in\{0,1\}^2$. Then $x(n)=\sum_kx_k2^k$ and $y(n)=\sum_ky_k2^k$.

The same statement without compressed notation is:

> Examine each base-4 digit position of the Hilbert index. At that position, the decoding rule reads one digit from 0 through 3 and outputs two binary digits. Put the first output into the matching binary position of the x-coordinate and the second output into the matching binary position of the y-coordinate. After every position has been processed, evaluate the two binary numerals to obtain the coordinates of the Hilbert point.

---

## Symbol glossary

| Symbol | Read it as |
|---|---|
| $H(n)$ | the Hilbert point at index $n$ |
| $x(n),y(n)$ | its two coordinate values |
| $k$ | a zero-based digit position |
| $q_k$ | the base-4 index digit at position $k$ |
| $\in$ | belongs to; is one of |
| $\{0,1\}$ | the two possible bit values |
| $\{0,1\}^2$ | all ordered pairs of two bits |
| $(x_k,y_k)$ | the two bits output at position $k$ |
| $\sum_k$ | add over all relevant positions $k$ |
| $2^k$ | the binary place value at position $k$ |

---

## Tiny checkpoint

1. For $n=123_4$, what are $q_0$, $q_1$, and $q_2$?
2. List every member of $\{0,1\}^2$.
3. If $x_2=1$, $x_1=0$, and $x_0=1$, what is the decimal value of $x$?
4. In ordinary language, what does it mean for the Hilbert rule to “emit $(x_k,y_k)$ at position $k$”?
5. Why does the formula for $x(n)$ contain powers of 2 rather than powers of 4?

After these symbols feel routine, return to [the paused section of Lesson 05](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md#one-base-4-digit-emits-two-coordinate-bits).
