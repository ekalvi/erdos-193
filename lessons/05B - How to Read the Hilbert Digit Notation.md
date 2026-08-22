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

Before calculating, separate two questions that the compact table can blur together.

#### Why does digit 1 emit $(0,1)$?

The pair $(0,1)$ is not yet the final coordinate $(0,1)$. At one scale, it is the **address of one child square**:

- the first bit 0 says “use the left half in x”;
- the second bit 1 says “use the upper half in y.”

Draw the four child squares in the basic orientation:

|  | Left half: x-bit 0 | Right half: x-bit 1 |
|---:|---:|---:|
| Upper half: y-bit 1 | digit 1: $(0,1)$ | digit 2: $(1,1)$ |
| Lower half: y-bit 0 | digit 0: $(0,0)$ | digit 3: $(1,0)$ |

The Hilbert path visits those children in the U-shaped order

$$
0\longrightarrow1\longrightarrow2\longrightarrow3.
$$

Therefore digit 1 means “the upper-left child,” whose low/high address is $(0,1)$. That geometric address—not ordinary binary counting—is the source of the table entry.

#### Why do both digits in $11_4$ emit $(0,1)$?

The two 1s make the same local choice at **different scales**:

1. the first 1 chooses the upper-left $2\times2$ child of the whole $4\times4$ square;
2. the second 1 chooses the upper-left cell inside that chosen child.

This is a nested address:

```text
whole 4×4 square
└── upper-left 2×2 child        first digit 1 → (x₁,y₁) = (0,1)
    └── upper-left unit cell    second digit 1 → (x₀,y₀) = (0,1)
```

The orientation remains basic after digit 1. Therefore the second lookup uses exactly the same table as the first:

$$
\text{same digit 1}+\text{same basic orientation}
\quad\Longrightarrow\quad
\text{same emitted pair }(0,1).
$$

The pairs have equal values but different place values:

- $(x_1,y_1)=(0,1)$ supplies the $2^1$ bits;
- $(x_0,y_0)=(0,1)$ supplies the $2^0$ bits.

This is like the repeated digit in decimal 11: both written digits are 1, but the left one contributes 10 while the right one contributes 1.

The order-two Hilbert grid makes the nested choice visible. Each cell below contains its decimal Hilbert index:

|  | $x=0$ | $x=1$ | $x=2$ | $x=3$ |
|---:|---:|---:|---:|---:|
| $y=3$ | **5** | 6 | 9 | 10 |
| $y=2$ | 4 | 7 | 8 | 11 |
| $y=1$ | 3 | 2 | 13 | 12 |
| $y=0$ | 0 | 1 | 14 | 15 |

The first digit 1 selects the upper-left block containing indices 4, 5, 6, and 7. The second digit 1 selects index 5’s upper-left cell within that block. Thus the nested address lands at $(x,y)=(0,3)$.

#### What does “orientation remains basic” mean here?

Orientation describes how the little U-shaped path inside the chosen child is rotated or reflected relative to the parent square. It is not an extra coordinate and not merely the direction in which a walker is facing.

Look at the upper-left block in the grid:

$$
4:(0,2)
\longrightarrow
5:(0,3)
\longrightarrow
6:(1,3)
\longrightarrow
7:(1,2).
$$

That is the same basic U as the original digit table:

$$
(0,0)\longrightarrow(0,1)\longrightarrow(1,1)\longrightarrow(1,0),
$$

only translated upward by 2. No rotation or reflection is needed. This is why choosing child 1 leaves the orientation basic.

That unchanged orientation is also what makes the connections work:

- index 3 at $(0,1)$ is adjacent to the block’s entrance, index 4 at $(0,2)$;
- the block’s exit, index 7 at $(1,2)$, is adjacent to index 8 at $(2,2)$.

Other children sometimes need a rotated or reflected internal U so these entrance and exit cells remain adjacent. The orientation state records that transformation. No such transformation occurs during either digit of $11_4$.

Now read the base-4 digits from left to right, most significant first:

| Step | Position | Input digit | Incoming orientation | Emitted pair | Outgoing orientation |
|---:|---:|---:|---:|---:|---:|
| 1 | $k=1$ | $q_1=1$ | basic | $(x_1,y_1)=(0,1)$ | basic |
| 2 | $k=0$ | $q_0=1$ | basic | $(x_0,y_0)=(0,1)$ | basic |

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

### Decode $H(80)$ from start to finish

This is the larger example used in Lesson 05’s pair-law discussion.

First convert the decimal index 80 to base 4:

$$
80=1\cdot4^3+1\cdot4^2+0\cdot4^1+0\cdot4^0
=64+16.
$$

Therefore

$$
80=1100_4.
$$

Label the digits by position:

| Position | $k=3$ | $k=2$ | $k=1$ | $k=0$ |
|---:|---:|---:|---:|---:|
| Digit $q_k$ | $1$ | $1$ | $0$ | $0$ |

The decoder reads from the most significant position $k=3$ toward the least significant position $k=0$.

For this trace, only two orientation names appear:

- $I$: the basic orientation; do not transform the child bits;
- $S$: swap the x-bit and y-bit.

The complete decoding trace is:

| Position | Input digit | Incoming orientation | Basic child pair | Emitted pair $(x_k,y_k)$ | Outgoing orientation |
|---:|---:|---:|---:|---:|---:|
| $k=3$ | $1$ | $I$ | $(0,1)$ | $(0,1)$ | $I$ |
| $k=2$ | $1$ | $I$ | $(0,1)$ | $(0,1)$ | $I$ |
| $k=1$ | $0$ | $I$ | $(0,0)$ | $(0,0)$ | $S$ |
| $k=0$ | $0$ | $S$ | $(0,0)$ | $(0,0)$ | $I$ |

Read the table one row at a time:

1. At $k=3$, digit 1 emits $(x_3,y_3)=(0,1)$ and leaves the orientation at $I$.
2. At $k=2$, digit 1 again emits $(x_2,y_2)=(0,1)$ and leaves the orientation at $I$.
3. At $k=1$, digit 0 emits $(x_1,y_1)=(0,0)$ and changes the orientation from $I$ to the swap state $S$.
4. At $k=0$, digit 0 is read in state $S$. Swapping $(0,0)$ still gives $(0,0)$, so $(x_0,y_0)=(0,0)$. A second digit 0 cancels the first swap and returns the final orientation to $I$.

Now collect the emitted x-bits in position order:

$$
x_3x_2x_1x_0=0000_2.
$$

Hence

$$
x=0\cdot2^3+0\cdot2^2+0\cdot2^1+0\cdot2^0=0.
$$

Collect the y-bits:

$$
y_3y_2y_1y_0=1100_2.
$$

Hence

$$
y=1\cdot2^3+1\cdot2^2+0\cdot2^1+0\cdot2^0
=8+4
=12.
$$

Therefore

$$
\boxed{H(80)=(0,12)}.
$$

The final orientation is $I$. Index $0=0000_4$ also finishes in state $I$ and gives

$$
H(0)=(0,0).
$$

Thus this concrete pair has:

$$
H(80)-H(0)=(0,12)
$$

and index gap 80. The later pair-law calculation checks that both fingerprints equal 4:

$$
V(0,12)=4,
\qquad
\nu_2(80)=4.
$$

#### Companion example: $H(96)$

The second concrete pair in Lesson 05 uses

$$
96=1200_4.
$$

Its trace differs from $1100_4$ only at position $k=2$: digit 2 emits $(1,1)$ instead of digit 1 emitting $(0,1)$. The resulting coordinate bits are

$$
x_3x_2x_1x_0=0100_2=4,
\qquad
y_3y_2y_1y_0=1100_2=12.
$$

Therefore

$$
H(96)=(4,12).
$$

This one changed digit switches the reduced planar chord from $(0,3)$ to $(1,3)$ after division by 4—the one-odd-versus-both-odd distinction used by the vector fingerprint.

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

### Checkpoint feedback

#### 1. Reading the subscripts

Correct:

$$
q_0=3,\qquad q_1=2,\qquad q_2=1.
$$

The subscript counts positions from the right, starting at 0.

#### 2. Listing $\{0,1\}^2$

One typo: the final pair must be $(1,1)$, not $(1,2)$:

$$
\{0,1\}^2
=
\{(0,0),(0,1),(1,0),(1,1)\}.
$$

Each slot is chosen from $\{0,1\}$, so neither slot can contain 2.

#### 3. Reassembling the x-coordinate

Correct:

$$
x
=
1\cdot2^2+0\cdot2^1+1\cdot2^0
=
1\cdot4+0\cdot2+1\cdot1
=5.
$$

Equivalently, the bits form $101_2$, whose decimal value is 5.

#### 4. What “emit” means

The central explanation is correct. Two precision fixes:

- $n$ is the ordinary nonnegative integer serving as the Hilbert index; $q_k$ is its base-4 digit at position $k$.
- The basic U-shaped table gives the emitted pair only in the basic orientation. In general, the current orientation may rotate or reflect that child-square address before producing $(x_k,y_k)$.

Thus the precise statement is:

> At position $k$, the Hilbert decoder reads the base-4 digit $q_k$, interprets its child-square address using the current orientation, and emits one bit $x_k$ for binary position $k$ of x and one bit $y_k$ for binary position $k$ of y.

The Gray-code-like order

$$
(0,0),(0,1),(1,1),(1,0)
$$

is what makes consecutive child choices follow the U rather than ordinary binary counting order.

#### 5. Why powers of 2 appear

The information-packing idea is right, but the direct place-value answer is:

> Once the decoder has separated the output into $x_k$ and $y_k$, each coordinate consists of bits. Bits use binary place values $2^k$, not base-4 place values $4^k$.

One base-4 digit has four possibilities. One pair of bits also has four possibilities:

$$
4=2\cdot2.
$$

Therefore one base-4 digit carries exactly enough information to supply one x-bit and one y-bit. It does not contain twice as much information as the pair; it contains the same information, redistributed between the two coordinates.

### Short version to remember

> Write the Hilbert index $n$ in base 4. At every position $k$, its digit $q_k$ chooses one of four child squares. The current orientation turns that choice into two bits, $(x_k,y_k)$—one for x and one for y. Assemble all the x-bits and y-bits using binary place values $2^k$. In the basic orientation, the child addresses follow the U-shaped order $(0,0),(0,1),(1,1),(1,0)$.

After these symbols feel routine, return to [the paused section of Lesson 05](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md#one-base-4-digit-emits-two-coordinate-bits).
