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

A rotated or reflected recursive square may change which pair is output. The foundational point is that one input digit always produces exactly two output bits: one destined for $x$ and one for $y$.

### Where does the basic table come from?

Start with a $2\times2$ square. Its four cells can be labeled by whether they lie in the low or high half of each coordinate:

```text
          x-bit
          0       1

y-bit 1  (0,1) → (1,1)
          ↑         ↓
y-bit 0  (0,0)   (1,0)
```

The arrows give the basic U-shaped Hilbert traversal:

$$
(0,0)\longrightarrow(0,1)\longrightarrow(1,1)\longrightarrow(1,0).
$$

Now number the visited cells in that order:

| Visit number | Cell bits |
|---:|---:|
| $0$ | $(0,0)$ |
| $1$ | $(0,1)$ |
| $2$ | $(1,1)$ |
| $3$ | $(1,0)$ |

That is exactly the basic digit-to-bit-pair table.

The order is chosen because every consecutive pair shares an edge:

- 0 to 1 changes only the y-bit;
- 1 to 2 changes only the x-bit;
- 2 to 3 changes only the y-bit.

This is the smallest Hilbert path.

### In what sense is this decoding rule “true”?

The table is part of the **definition** of the particular discrete Hilbert path used in the proof. It is not a numerical law that must be deduced from unrelated assumptions.

The geometric Hilbert construction says:

1. split the current square into four equal child squares;
2. visit those children in the U-shaped order above;
3. inside each child, repeat the same four-child construction at the next smaller scale;
4. rotate or reflect child copies when necessary so the exit of one copy touches the entrance of the next.

The decoder is the coordinate bookkeeping for that geometric recipe:

- the base-4 digit says which of the four children is visited;
- the emitted bit pair says which x-half and y-half contain that child;
- the orientation state says how the basic U has been rotated or reflected at the current scale.

After defining $H$ by these rules, one proves—by induction on the number of digits—that:

- every cell in the finite square appears exactly once;
- consecutive indices map to neighboring grid cells;
- adding the permitted leading-zero padding does not change the point.

Those facts are also checked by the Lean formalization. Thus the table defines the path, while the finite-order Hilbert lemmas prove that the recursively decoded object really has the required Hilbert-path behavior.

Different books may rotate, reflect, or reverse the entire starting convention. Those versions look different in coordinates but are equivalent for the geometry. This proof fixes the displayed convention and uses it consistently.

### Decode a real point from the final construction

The first index retained by the selector is

$$
n_0=5=11_4.
$$

This is a particularly clean example because digit 1 leaves the orientation unchanged.

Read the base-4 digits from left to right, most significant first:

| Step | Position | Input digit | Current orientation | Emitted pair |
|---:|---:|---:|---:|---:|
| 1 | $k=1$ | $q_1=1$ | basic | $(x_1,y_1)=(0,1)$ |
| 2 | $k=0$ | $q_0=1$ | basic | $(x_0,y_0)=(0,1)$ |

Now collect the x-bits by position:

$$
x_1x_0=00_2,
\qquad
x=0\cdot2^1+0\cdot2^0=0.
$$

Collect the y-bits:

$$
y_1y_0=11_2,
\qquad
y=1\cdot2^1+1\cdot2^0=3.
$$

Therefore

$$
H(5)=(0,3).
$$

The final three-dimensional construction then uses the index itself as height:

$$
P_0=(H(5),5)=(0,3,5).
$$

This is not a toy point; it is the first selected vertex of the actual walk.

### See the neighboring real indices

The four indices from $4$ through $7$ share the first base-4 digit 1:

| Decimal index | Base-4 index | Hilbert point |
|---:|---:|---:|
| $4$ | $10_4$ | $(0,2)$ |
| $5$ | $11_4$ | $(0,3)$ |
| $6$ | $12_4$ | $(1,3)$ |
| $7$ | $13_4$ | $(1,2)$ |

They trace a real U-shaped $2\times2$ piece:

```text
(0,3) → (1,3)       indices 5 → 6
  ↑         ↓
(0,2)   (1,2)       indices 4   7
```

For example, decode $6=12_4$:

- at $k=1$, digit 1 emits $(x_1,y_1)=(0,1)$;
- at $k=0$, digit 2 emits $(x_0,y_0)=(1,1)$;
- therefore $x_1x_0=01_2=1$ and $y_1y_0=11_2=3$;
- hence $H(6)=(1,3)$.

This small block shows the table doing exactly what the geometric Hilbert rule requires: four consecutive indices visit four neighboring cells in a U.

### Where orientation enters

The simple indices $10_4$ through $13_4$ remain in the basic orientation while their output bits are produced. Other prefixes place the same U-shaped pattern into a child square that must be rotated or reflected to connect with its neighbors.

In those cases, the decoder still reads one base-4 digit and emits one x-bit and one y-bit. The state merely transforms the basic pair before emitting it. The later same-terminal-state argument is designed so two compared indices apply one common transformation at their first mismatch.

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
