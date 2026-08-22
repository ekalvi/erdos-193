# Erdős 193 — How Orientation Changes While Decoding

**Previous:** [05B — How to Read the Hilbert Digit Notation](05B%20-%20How%20to%20Read%20the%20Hilbert%20Digit%20Notation.md)

**Next:** [05D — What the Hilbert Terminal State Remembers](05D%20-%20What%20the%20Hilbert%20Terminal%20State%20Remembers.md)

**Return afterward to:** [05 — Why the Hilbert Pair Law Is True](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md)

## What this note must explain

The words “square,” “child,” “incoming orientation,” “outgoing orientation,” and “position $k-1$” are not useful until there is a picture underneath them.

This note builds that picture first.

The main idea is:

> A base-4 digit tells us which quarter of a grid region to enter. Inside that quarter is a smaller copy of the U-shaped Hilbert route. Sometimes that smaller U must be turned or reflected so all four quarters connect into one continuous path. Its arrangement is the orientation passed to the next digit.

---

## Start with one digit and four grid cells

With one base-4 digit, there are four possible indices:

$$
0,
1,
2,
3.
$$

Place four unit grid cells in a $2\times2$ block. The basic Hilbert route visits them in a U:

```text
1 ───> 2
↑       │
│       ↓
0       3
```

Give each cell a two-bit address:

- first bit: left half 0 or right half 1;
- second bit: lower half 0 or upper half 1.

That gives:

```text
                    x-bit
                  0         1
              ┌─────────┬─────────┐
y-bit 1       │ digit 1 │ digit 2 │
              │  (0,1)  │  (1,1)  │
              ├─────────┼─────────┤
y-bit 0       │ digit 0 │ digit 3 │
              │  (0,0)  │  (1,0)  │
              └─────────┴─────────┘
```

This is the basic digit table:

| Digit | Two-bit address |
|---:|---:|
| 0 | $(0,0)$ |
| 1 | $(0,1)$ |
| 2 | $(1,1)$ |
| 3 | $(1,0)$ |

At this one-digit scale, there is no smaller digit left to decode. Orientation has not yet created a complication.

---

## What “square” means here

In this discussion, a **square** is only a square block of grid cells.

Examples:

- a $2\times2$ block has four cells;
- a $4\times4$ block has sixteen cells;
- an $8\times8$ block has sixty-four cells.

We are not assuming any advanced geometry about squares. We are simply grouping grid cells into square-shaped regions.

Every time the Hilbert construction grows one level, it puts four copies of the previous grid into a larger square:

```text
four 1×1 cells make one 2×2 block
four 2×2 blocks make one 4×4 block
four 4×4 blocks make one 8×8 block
and so on
```

---

## What “child square” means

Take a $4\times4$ grid and divide it into four equal $2\times2$ quarters:

```text
┌───────────┬───────────┐
│           │           │
│ upper     │ upper     │
│ left      │ right     │
│           │           │
├───────────┼───────────┤
│           │           │
│ lower     │ lower     │
│ left      │ right     │
│           │           │
└───────────┴───────────┘
```

A mathematician may call each quarter a **child square** of the larger square.

There is no new kind of object hiding behind the word “child.” It means only:

> one of the four smaller equal quarters inside the region currently being examined.

This note will usually say **quarter** rather than child square.

---

## What two base-4 digits do

A two-digit base-4 number selects one cell in a $4\times4$ grid.

The digits are read from left to right:

1. the first digit selects one $2\times2$ quarter of the whole $4\times4$ grid;
2. the second digit selects one unit cell inside that chosen quarter.

For example:

$$
11_4
$$

means:

1. first digit 1: enter the upper-left quarter;
2. second digit 1: inside that quarter, enter its upper-left cell.

It is a nested address:

```text
whole 4×4 grid
└── upper-left 2×2 quarter       first digit 1
    └── upper-left unit cell     second digit 1
```

If every smaller U pointed the same way, decoding would end here. But those four U-shaped routes must join into one continuous route through all sixteen cells.

That need to connect them is where orientation enters.

---

## Build the real $4\times4$ Hilbert route

Here is the actual order-two Hilbert grid. Each cell contains the index that visits it:

|  | $x=0$ | $x=1$ | $x=2$ | $x=3$ |
|---:|---:|---:|---:|---:|
| $y=3$ | 5 | 6 | 9 | 10 |
| $y=2$ | 4 | 7 | 8 | 11 |
| $y=1$ | 3 | 2 | 13 | 12 |
| $y=0$ | 0 | 1 | 14 | 15 |

The complete route is

$$
0\to1\to2\to\cdots\to15.
$$

Now look at the four $2\times2$ quarters separately.

### Lower-left quarter: indices 0 through 3

```text
3 <─── 2
      ↑
0 ───> 1
```

The route goes right, then up, then left.

### Upper-left quarter: indices 4 through 7

```text
5 ───> 6
↑       │
│       ↓
4       7
```

This is the basic U: up, then right, then down.

### Upper-right quarter: indices 8 through 11

```text
9 ───> 10
↑        │
│        ↓
8        11
```

This also uses the basic U.

### Lower-right quarter: indices 12 through 15

```text
13 <─── 12
│
↓
14 ───> 15
```

The route goes left, then down, then right.

### Why the lower-right quarter has exactly that order

First clarify **order two**:

- order one uses one base-4 digit and a $2\times2$ grid;
- order two uses two base-4 digits and a $4\times4$ grid;
- “order” names the number of nested grid levels, not a special direction of travel.

Now derive the lower-right route rather than assuming it.

#### Base-4 bookkeeping fixes the index order

Every two-digit base-4 index whose first digit is 3 belongs to the lower-right quarter:

| Full base-4 index | Decimal index | Second digit |
|---:|---:|---:|
| $30_4$ | 12 | 0 |
| $31_4$ | 13 | 1 |
| $32_4$ | 14 | 2 |
| $33_4$ | 15 | 3 |

The first digit 3 chooses the large quarter. The second digit still runs through the local visit numbers 0, 1, 2, and 3.

Therefore the lower-right quarter must contain the indices in this order:

$$
12\to13\to14\to15.
$$

The recursion does not rearrange the index numbers. It changes **which local cell receives each suffix digit**.

#### Connectivity fixes where index 12 must begin

The preceding upper-right quarter ends at

$$
11:(3,2).
$$

Successive Hilbert points must share one grid edge. The only cell inside the lower-right quarter that touches $(3,2)$ is the cell directly below it:

$$
12:(3,1).
$$

Thus index 12 is forced to be the upper-right cell of its $2\times2$ quarter.

#### The endpoint fixes where index 15 must finish

The order-two route is being built as a larger version of the same basic U. To remain usable as one recursive copy at the next level, it must preserve the basic U’s outer endpoints: begin at the whole grid’s lower-left corner and finish at its lower-right corner. Therefore

$$
15:(3,0).
$$

Once 12 starts at the upper-right local cell and 15 must finish at the lower-right local cell, there is only one edge-connected way to visit the other two cells exactly once:

```text
13 <─── 12
│
↓
14 ───> 15
```

So the order is forced:

$$
(3,1)\to(2,1)\to(2,0)\to(3,0).
$$

It is not an arbitrary convention added after the rest of the path was drawn.

### How the recursion records this turn

Inside an unturned $2\times2$ U, the suffix digits have the local addresses

| Suffix digit | Basic local address |
|---:|---:|
| 0 | $(0,0)$ |
| 1 | $(0,1)$ |
| 2 | $(1,1)$ |
| 3 | $(1,0)$ |

For the lower-right quarter, the decoder carries a transformation called $T$:

$$
T(x,y)=(1-y,1-x).
$$

Apply $T$ to each basic local address:

| Full index | Suffix | Basic local address | Address after $T$ | Whole-grid coordinate |
|---:|---:|---:|---:|---:|
| $30_4=12$ | 0 | $(0,0)$ | $(1,1)$ | $(3,1)$ |
| $31_4=13$ | 1 | $(0,1)$ | $(0,1)$ | $(2,1)$ |
| $32_4=14$ | 2 | $(1,1)$ | $(0,0)$ | $(2,0)$ |
| $33_4=15$ | 3 | $(1,0)$ | $(1,0)$ | $(3,0)$ |

The “address after $T$” is measured inside the lower-right $2\times2$ quarter. That quarter begins at whole-grid coordinate $(2,0)$, so converting a local address to a whole-grid coordinate adds 2 to its x-coordinate.

This table is the bookkeeping behind the drawing:

```text
suffix digit:       0       1       2       3
full index:        12      13      14      15
local cell:       (1,1)   (0,1)   (0,0)   (1,0)
```

### How the same bookkeeping continues at deeper levels

Suppose the index has more digits after the initial 3.

1. The first digit 3 selects the lower-right quarter.
2. The decoder records that this quarter’s smaller route has orientation $T$.
3. The next digit is interpreted through $T$, just as suffix digit 0 became local cell $(1,1)$ above.
4. That next digit selects an even smaller quarter, which has its own turn relative to the already-turned region.
5. The decoder combines the old turn with the new local turn and carries the result to the following digit.

In compact notation, if the orientation already being carried is $g$ and digit $q$ has local turn $r_q$, then the orientation carried onward is

$$
g\circ r_q.
$$

This formula means:

> Arrange the small route as required inside the chosen quarter, then view that arrangement through every turn already inherited from earlier digits.

The state letter is therefore a bookkeeping shortcut. Instead of redrawing an increasingly tiny U after every digit, the decoder stores the combined turn and applies it to the next local address.

The four quarter routes point in different directions, but their endpoints touch:

- index 3 touches index 4;
- index 7 touches index 8;
- index 11 touches index 12.

That is how they form one continuous route.

---

## Orientation in ordinary language

**Orientation** means:

> Which way does the smaller U point inside the quarter we entered?

For the four quarters of the basic $4\times4$ route:

| First digit | Quarter entered | Arrangement of its smaller U |
|---:|---:|---:|
| 0 | lower left | turned so it goes right–up–left |
| 1 | upper left | basic U: up–right–down |
| 2 | upper right | basic U: up–right–down |
| 3 | lower right | turned so it goes left–down–right |

This is why the orientation carried forward differs according to the digit that was read.

It does **not** differ because the position happens to be called $k=3$, $k=2$, or $k=1$. It differs because digits 0, 1, 2, and 3 enter four different quarters whose internal routes point in different directions.

---

## What happens before and after reading one digit

Forget the words incoming and outgoing for a moment.

Before reading a digit, the decoder already knows which way the U points in the region currently being examined. That arrangement was determined by earlier digits to the left.

When it reads the current digit, it does two things:

1. it uses the current arrangement to locate the requested quarter and records one x-bit and one y-bit;
2. it remembers which way the smaller U points inside that quarter, because the next digit will be interpreted inside it.

In plain language:

```text
orientation carried from earlier digits
                 +
            current digit
                 │
                 ├──> record the current x-bit and y-bit
                 │
                 └──> carry the smaller U's orientation to the next digit
```

Only now attach the technical names:

- **incoming orientation** = the orientation available before reading the current digit;
- **outgoing orientation** = the orientation carried forward after entering the chosen quarter.

Thus:

> Incoming means “use this now.” Outgoing means “give this to the next digit.”

The outgoing orientation does not go backward and alter bits already recorded.

---

## Why the next position is called $k-1$

Positions are numbered from the right, starting at 0.

For

$$
1100_4,
$$

write the position above each digit:

| Position | 3 | 2 | 1 | 0 |
|---:|---:|---:|---:|---:|
| Digit | 1 | 1 | 0 | 0 |

The decoder reads from left to right:

$$
3\to2\to1\to0.
$$

Therefore:

- after position 3, the next digit is at position 2;
- after position 2, the next digit is at position 1;
- after position 1, the next digit is at position 0.

In general, the position immediately to the right of position $k$ is called $k-1$.

So the statement

> the orientation leaving position $k$ is used at position $k-1$

means only:

> carry the orientation to the next digit on the right.

It does not mean that we subtract 1 from the digit. It does not mean that the path moves backward. The expression $k-1$ is just the label of the next digit position.

This note will prefer “the next digit on the right” unless the position number matters.

---

## Example 1: why both 1s in $H(5)$ emit $(0,1)$

Write

$$
5=11_4.
$$

### First digit 1

We start with the basic U.

Digit 1 selects the upper-left quarter, whose address is

$$
(0,1).
$$

So the first recorded pair is

$$
(x_1,y_1)=(0,1).
$$

The $4\times4$ picture shows that the U inside the upper-left quarter is still the basic U. Therefore we carry the basic orientation to the next digit.

### Second digit 1

We are now inside the upper-left quarter, and its U still has the basic orientation.

Digit 1 again means “choose the upper-left part,” so the second recorded pair is also

$$
(x_0,y_0)=(0,1).
$$

The repeated output has a simple cause:

```text
first digit:   digit 1 interpreted through the basic U → (0,1)
second digit:  digit 1 interpreted through the basic U → (0,1)
```

The pairs have the same values but occupy different binary positions:

$$
x_1x_0=00_2=0,
\qquad
y_1y_0=11_2=3.
$$

Therefore

$$
H(5)=(0,3).
$$

---

## Example 2: orientation visibly changes a later digit

Use

$$
12=30_4.
$$

### First digit 3

We begin with the basic U. Digit 3 selects the lower-right quarter, so the first pair is its whole-grid address:

$$
(x_1,y_1)=(1,0).
$$

Now look again at the lower-right quarter of the real $4\times4$ route:

```text
13 <─── 12
│
↓
14 ───> 15
```

Its route does not begin at the lower-left local cell. It begins at the **upper-right** local cell, index 12.

That turned arrangement is what gets carried to the second digit.

### Second digit 0

Digit 0 means “take the first location in the local four-cell route.”

In the basic U, the first location is the lower-left cell, with local address $(0,0)$.

But inside this turned lower-right quarter, the first location is the upper-right local cell, with address

$$
(1,1).
$$

Therefore the second pair is

$$
(x_0,y_0)=(1,1),
$$

not $(0,0)$.

Now assemble the coordinate bits:

$$
x_1x_0=11_2=3,
\qquad
y_1y_0=01_2=1.
$$

Hence

$$
\boxed{H(12)=(3,1)}.
$$

This is orientation doing visible work:

> The first digit enters a quarter whose smaller U is turned. The second digit is interpreted through that turned U.

The formal name for this particular turned arrangement is $T$, but the name is less important than the picture.

---

## Example 3: why the orientation change in $H(80)$ is hard to see

Write

$$
80=1100_4.
$$

Read the digits from left to right:

| Position | Digit | Orientation used now | Pair recorded | Orientation carried to next digit |
|---:|---:|---:|---:|---:|
| 3 | 1 | basic | $(0,1)$ | basic |
| 2 | 1 | basic | $(0,1)$ | basic |
| 1 | 0 | basic | $(0,0)$ | swapped |
| 0 | 0 | swapped | $(0,0)$ | basic |

At position 1, digit 0 selects a quarter whose internal U is swapped. That swapped arrangement is carried to the final digit.

At position 0, the swap is genuinely active. But the basic pair for digit 0 is $(0,0)$, and swapping its two entries still gives

$$
(0,0).
$$

So the orientation changes internally without visibly changing that emitted pair.

This is why $H(80)$ is useful for the later pair law but poor as the first example of orientation. The $H(12)$ example makes the effect visible.

---

## Translation dictionary

| Technical phrase | Plain-language meaning |
|---|---|
| current square | the square grid region selected so far |
| child square | one of its four equal quarters |
| orientation | which way the smaller U points in that region |
| incoming orientation | the U arrangement used for the digit being read now |
| outgoing orientation | the U arrangement carried to the next digit on the right |
| position $k$ | the address of one digit, counted from the right starting at 0 |
| position $k-1$ | the next digit position on the right |
| terminal state | the orientation left over after the final digit |

---

## What you do not need yet

You do not yet need to memorize:

- all eight square symmetries;
- a full orientation multiplication table;
- formulas for composing transformations;
- the selector’s two-digit steering suffixes.

For the pair-law lesson, the conceptual requirements are only:

1. earlier digits determine how a later local U is arranged;
2. that arrangement can change which bit pair a later digit emits;
3. the orientation left after the final digit is retained as the terminal state.

The next note explains why matching terminal states let two decodings be aligned.

> [!next] Continue with terminal states
> Read [05D — What the Hilbert Terminal State Remembers](05D%20-%20What%20the%20Hilbert%20Terminal%20State%20Remembers.md) after the picture in this note feels stable.

---

## Tiny checkpoint

1. In this lesson, what does “child square” mean in ordinary language?
2. For $1100_4$, in what order are positions 3, 2, 1, and 0 read?
3. If an orientation is carried out of position 2, which digit position uses it next?
4. Why do both digits of $11_4$ emit $(0,1)$?
5. For $30_4$, why does the second digit 0 select local pair $(1,1)$ rather than $(0,0)$?
6. What is the difference between incoming and outgoing orientation without using either technical word?
