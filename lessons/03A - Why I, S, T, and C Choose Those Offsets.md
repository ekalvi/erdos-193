# Erdős 193 — Why $I$, $S$, $T$, and $C$ Choose Those Offsets

**Previous:** [03 - Why the Gaps Are 4 to 28](03%20-%20Why%20the%20Gaps%20Are%204%20to%2028.md)  
**Related:** [02 - Trace, Select, and Lift](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md)

## Short answer

The letters do not name the offsets. They name four possible **orientation states** of the Hilbert recursion.

The number assigned to each letter is a two-digit base-4 suffix whose orientation effect cancels that state and returns the selected index to state $I$.

> [!info] Why does the picture keep only blue?
> The picture contains **16 squares but only four terminal states**. The 16 squares are the 16 possible two-digit base-4 suffixes:
> $$
> 00_4,01_4,\ldots,33_4.
> $$
> Several different squares can have the same state, so the colors repeat. Blue is merely the visualization's color for state $I$.
>
> The pair law and the no-three-collinear theorem work for **any one fixed terminal state**. We could target $S$, $T$, or $C$ instead and obtain a different valid walk. State $I$ is chosen because it is the identity orientation, so “cancel the incoming state and return to the standard orientation” gives the cleanest correction table. The color blue itself has no mathematical significance.
>
> What we may not do without another argument is freely mix colors. The pair law applies when the two indices being compared have the same terminal state. Keeping one fixed color ensures that it applies to every pair of retained points.

## Why select only one square from each 16-index block?

The six blue squares visible in the order-2 picture are not six different states. They are six different indices that happen to finish in the same state.

The construction needs an explicit infinite sequence with bounded successive gaps. Its simple rule is:

> Divide the indices into blocks of 16 and choose one suffix in each block that cancels that block's incoming state.

For an incoming state $I$, the displayed correction table chooses offset 5. For incoming states $S$, $T$, and $C$, it chooses offsets 1, 13, and 3 respectively. Whichever position is activated, the complete selected index finishes in state $I$.

The other same-state squares are not defective; this particular selector simply does not need them. Keeping one representative per block makes the sequence and the bound

$$
4\le n_{a+1}-n_a\le28
$$

immediate. One could instead enumerate every index in one fixed terminal class: the pair and triple arguments would still apply, and adding extra same-state indices could only shorten the gaps. The repository's formal construction uses one representative per block because it is the cleanest explicit choice.

---

## What the letters mean

At each recursive scale, a Hilbert pattern may be rotated or reflected. Its state remembers that orientation.

The four terminal states that can arise are transformations of a coordinate pair $(x,y)$:

| State | Transformation | Mental picture |
|---|---|---|
| $I$ | $(x,y)$ | Identity: change nothing |
| $S$ | $(y,x)$ | Swap the coordinates |
| $T$ | $(1-y,1-x)$ | Swap and complement both coordinates |
| $C$ | $(1-x,1-y)$ | Complement both coordinates; a half-turn |

The letters are compact names for these transformations. $I$ is standard notation for “identity.” $S$ is naturally remembered as “swap,” and $C$ as “complement.” The letter $T$ is simply the manuscript’s label for the fourth transformation; the definition $(1-y,1-x)$ is what matters.

These four transformations form a tiny closed system:

$$
K=\{I,S,T,C\}.
$$

Each one is its own inverse:

$$
I^2=S^2=T^2=C^2=I.
$$

Also,

$$
ST=C.
$$

In plain language: applying any one of these transformations twice cancels it.

---

## Why only these four states appear

Each base-4 digit changes the Hilbert orientation as follows:

| Base-4 digit | Orientation contribution |
|---:|---:|
| $0$ | $S$ |
| $1$ | $I$ |
| $2$ | $I$ |
| $3$ | $T$ |

Starting from $I$, the recursion therefore builds terminal states only by combining $S$ and $T$. Because $S$ and $T$ commute and each cancels itself, the only possible results are

$$
I,\quad S,\quad T,\quad ST=C.
$$

The other square symmetries are useful in the full transducer table, but they are not reachable terminal states for an ordinary Hilbert index starting from $I$.

---

## Why an offset is a two-digit suffix

Recall that the selected index has the form

$$
n_a=16a+r_a.
$$

Because

$$
16=4^2,
$$

multiplying $a$ by 16 shifts its base-4 representation left by two digit positions. Adding $r_a$ fills those final two positions.

For example, if $a$ has base-4 representation

$$
a=(q_k\cdots q_1q_0)_4,
$$

then

$$
16a+5=(q_k\cdots q_1q_0\,11)_4,
$$

because $5=11_4$.

Thus choosing an offset is equivalent to appending a two-digit base-4 suffix.

---

## The cancellation table

Suppose the block index $a$ currently has terminal state $g$. We want the selected index $n_a$ to finish in state $I$.

Because every possible $g$ is its own inverse, we append a suffix whose orientation contribution is also $g$:

$$
g\cdot g=I.
$$

The proof uses this table:

| Incoming state $g$ | Appended base-4 suffix | Suffix contribution | Decimal offset | Final state |
|---:|---:|---:|---:|---:|
| $I$ | $11_4$ | $I$ | $5$ | $I\cdot I=I$ |
| $S$ | $01_4$ | $S$ | $1$ | $S\cdot S=I$ |
| $T$ | $31_4$ | $T$ | $13$ | $T\cdot T=I$ |
| $C$ | $03_4$ | $ST=C$ | $3$ | $C\cdot C=I$ |

Here is how to read two examples.

### Incoming state $S$

The suffix $01_4$ contains one digit $0$, which contributes $S$, followed by a digit $1$, which contributes $I$. Its total contribution is therefore $S$.

Appending it changes the state by

$$
S\cdot S=I.
$$

The suffix $01_4$ has decimal value $1$, so this means selecting offset $1$.

### Incoming state $C$

The suffix $03_4$ has a digit $0$ contributing $S$ and a digit $3$ contributing $T$. Its total contribution is

$$
ST=C.
$$

Appending it changes the state by

$$
C\cdot C=I.
$$

The suffix $03_4$ has decimal value $3$, so this means selecting offset $3$.

---

## Why not use a one-digit suffix?

One base-4 digit can contribute only

$$
S,\quad I,\quad\text{or}\quad T.
$$

No single digit contributes $C$. Therefore one digit cannot cancel all four possible incoming states.

Two digits are the shortest suffix length that can handle every state. Two base-4 digits also explain why the aligned blocks have size

$$
4^2=16.
$$

This is the real source of the 16-index block structure.

---

## Are these exact suffixes uniquely forced?

No. Other two-digit suffixes can have the same orientation contribution.

The proof needs a deterministic choice satisfying two properties:

1. its suffix contribution cancels the incoming state;
2. the resulting offsets remain uniformly bounded inside each 16-index block.

The displayed choices

$$
11_4,\quad01_4,\quad31_4,\quad03_4
$$

are explicit convenient representatives. Their decimal values are

$$
5,\quad1,\quad13,\quad3,
$$

which produce the safe gap bound from 4 to 28 derived in [Note 03](03%20-%20Why%20the%20Gaps%20Are%204%20to%2028.md). Different valid representatives could produce different numerical gap bounds; the proof only requires some fixed finite bound.

### All valid two-digit choices

The complete candidate table makes the convention visible:

| Required suffix contribution | Valid base-4 suffixes | Decimal offsets |
|---:|---:|---:|
| $I$ | $00_4,11_4,12_4,21_4,22_4,33_4$ | $0,5,6,9,10,15$ |
| $S$ | $01_4,02_4,10_4,20_4$ | $1,2,4,8$ |
| $T$ | $13_4,23_4,31_4,32_4$ | $7,11,13,14$ |
| $C$ | $03_4,30_4$ | $3,12$ |

Thus $I\mapsto5$, $S\mapsto1$, $T\mapsto13$, and $C\mapsto3$ is **not forced**.

The manuscript chooses an especially transparent spelling of each state:

- $11_4$: two neutral digits contribute $I$;
- $01_4$: digit 0 contributes $S$, then digit 1 contributes nothing;
- $31_4$: digit 3 contributes $T$, then digit 1 contributes nothing;
- $03_4$: digits 0 and 3 contribute $ST=C$.

These are easy representatives to derive directly from the generator rules. They are a convention, not an optimization claim. Replacing them by another fixed choice from each row would give the same final-state cancellation, with possibly different finite gap bounds.

### Why the first rings are at indices 5 and 17

For block $a=0$, the incoming state is $I$, so the table selects offset 5:

$$
n_0=16\cdot0+5=5.
$$

For block $a=1$, the incoming state is $S$, so the table selects offset 1:

$$
n_1=16\cdot1+1=17.
$$

Their difference is

$$
n_1-n_0=17-5=16+1-5=12.
$$

That 12 is the **index gap between two blocks**, not either square's offset within its own block. It lies inside the allowed range $4\le12\le28$. There are 11 indices strictly between 5 and 17, while the Hilbert path takes 12 unit steps from index 5 to index 17.

---

## One-sentence takeaway

> The block’s orientation state chooses one two-digit base-4 suffix with the same orientation effect; because every state is self-inverse, appending that suffix cancels the old state and makes every selected index end in state $I$.
