# Erdős 193 — What the Hilbert Terminal State Remembers

**Previous:** [05C — When Hilbert Orientation Applies](05C%20-%20When%20Hilbert%20Orientation%20Applies.md)

**Return afterward to:** [05 — Why the Hilbert Pair Law Is True](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md)

**Selector machinery for later:** [03A — Why I, S, T, and C Choose Those Offsets](03A%20-%20Why%20I%2C%20S%2C%20T%2C%20and%20C%20Choose%20Those%20Offsets.md)

## Why this lesson belongs here

Lesson 05C followed the orientation state while the decoder moved from one digit to the next. One question remains before the pair law can feel natural:

> What does the state left over after the final digit remember, and why does the proof deliberately compare indices with matching final states?

That leftover state is the **terminal state**.

It is not a terminal point, not an endpoint coordinate, and not a new fourth coordinate. It is simply the decoder’s orientation memory after every base-4 digit has been processed.

---

## State during decoding versus terminal state

While digits remain, the current state tells the decoder how to interpret the next child-square address.

After the last digit $q_0$:

- the coordinate bits have all been emitted;
- no smaller child remains to be selected;
- the final outgoing orientation has no next digit on which to act.

We retain that final outgoing orientation and call it

$$
\sigma(n),
$$

read as “the terminal state of index $n$.”

Thus:

```text
start in basic state I
        ↓
read every digit from left to right
        ↓
emit all x-bits and y-bits
        ↓
state remaining after q₀ = terminal state σ(n)
```

The terminal state does not modify the completed coordinate $H(n)$. It records the net orientation accumulated during the descent through all the nested child squares.

---

## Only digits 0 and 3 change the state

From Lesson 05C, the four relative refinements are

$$
r_0=S,
\qquad r_1=I,
\qquad r_2=I,
\qquad r_3=T.
$$

Therefore:

- digit 0 contributes one swap $S$;
- digits 1 and 2 contribute no orientation change;
- digit 3 contributes one other diagonal reflection $T$.

Both $S$ and $T$ undo themselves when applied twice:

$$
S\circ S=I,
\qquad
T\circ T=I.
$$

They also commute, and applying both gives the state $C$:

$$
S\circ T=T\circ S=C.
$$

Consequently, the final state remembers only two parity questions:

1. Did digit 0 occur an even or odd number of times?
2. Did digit 3 occur an even or odd number of times?

It does not need to remember the exact counts or their order.

---

## The four possible terminal states

| Number of 0 digits | Number of 3 digits | Terminal state | Transformation remembered |
|---:|---:|---:|---:|
| even | even | $I$ | $(x,y)$ |
| odd | even | $S$ | $(y,x)$ |
| even | odd | $T$ | $(1-y,1-x)$ |
| odd | odd | $C$ | $(1-x,1-y)$ |

So the terminal state is a two-bit fingerprint of the base-4 word:

```text
parity of number of 0s
            +
parity of number of 3s
            ↓
one of I, S, T, C
```

The full square-symmetry system contains eight transformations, but a word that starts in $I$ and uses only the Hilbert refinements $S$, $I$, $I$, and $T$ finishes in one of these four.

---

## Concrete terminal-state examples

| Index | Even-padded base-4 word | Number of 0s | Number of 3s | Terminal state | Hilbert point |
|---:|---:|---:|---:|---:|---:|
| $0$ | $00_4$ | 2 | 0 | $I$ | $(0,0)$ |
| $5$ | $11_4$ | 0 | 0 | $I$ | $(0,3)$ |
| $12$ | $30_4$ | 1 | 1 | $C$ | $(3,1)$ |
| $80$ | $1100_4$ | 2 | 0 | $I$ | $(0,12)$ |
| $96$ | $1200_4$ | 2 | 0 | $I$ | $(4,12)$ |

For index 12, one zero contributes $S$ and one three contributes $T$:

$$
\sigma(12)=S\circ T=C.
$$

For index 80, its two zeros contribute two swaps, which cancel:

$$
\sigma(80)=S\circ S=I.
$$

Digits 1 and 2 do not alter either result.

---

## Why leading-zero padding does not change the state

The construction may prepend two zero digits so all words have a suitable common even length.

Each zero contributes $S$. Two new zeros contribute

$$
S\circ S=I.
$$

Therefore padding $00_4$ onto the left changes neither the point nor the terminal state.

For example, index 0 may be represented as either

$$
00_4
$$

or, when compared with a four-digit index, as

$$
0000_4.
$$

Both versions finish in state $I$.

---

## Why the pair law looks from the right

Suppose two indices $m$ and $n$ are written with a common even length. Compare their base-4 digits from the right until reaching the first mismatch.

Call that mismatch position $j$.

Then:

- positions $0,1,\ldots,j-1$ form one identical low suffix;
- position $j$ contains two different digits;
- positions above $j$ may also differ.

The index-gap valuation is controlled by this first mismatch from the right. The pair law must prove that the planar-coordinate fingerprint is controlled by the same mismatch.

The difficulty is orientation: reading forward from the left, the higher digits may place the two decoders in different incoming orientations at position $j$.

Matching terminal states lets the proof solve that difficulty by running the shared low suffix **backward**.

---

## The rewind idea

For one fixed digit, the orientation transition can be undone. If you know:

- the outgoing state;
- the digit that was read;

then you can recover the incoming state.

Now suppose $m$ and $n$ have:

1. the same terminal state;
2. the same digits below position $j$.

Start at their equal terminal states and undo the shared low digits one at a time:

```text
same terminal state
        ↑ undo the same q₀ in both words
same preceding state
        ↑ undo the same q₁ in both words
same preceding state
        ↑ continue through the shared suffix
same state immediately after position j
```

Because every undo operation starts with equal states and uses the same digit, equality is preserved at every step.

Therefore the two decoders have one common orientation immediately **after** their mismatching digits at position $j$. Call that common orientation $h$.

This is exactly the alignment the proof needs.

---

## Why “immediately after” is enough

At first, one might expect the two **incoming** states at the mismatch to be equal. They need not be, because the two mismatching digits can impose different refinements.

The Hilbert transitions have a special property: each digit’s refinement fixes that digit’s own child corner. As a result, if $h$ is the outgoing state after a digit $q$, the pair emitted at that digit can be recovered as

$$
h(c_q).
$$

Thus, at the mismatch, the two emitted pairs are

$$
h(c_d)
\qquad\text{and}\qquad
h(c_e),
$$

where $d$ and $e$ are the two different digits.

The important point is that **one common symmetry $h$ acts on both child corners**.

A square symmetry may swap or reflect the coordinates, but it preserves whether two corners differ in:

- exactly one coordinate; or
- both coordinates.

That is the one-bit-versus-two-bit distinction needed by the pair law.

---

## Worked rewind: indices 0 and 80

Use a common four-digit length:

$$
0=0000_4,
\qquad
80=1100_4.
$$

Their terminal states are both $I$. From the right, their digits are:

| Position | $k=3$ | $k=2$ | $k=1$ | $k=0$ |
|---:|---:|---:|---:|---:|
| $0$ | 0 | 0 | 0 | 0 |
| $80$ | 1 | 1 | 0 | 0 |
| Comparison from right | may differ | first mismatch | same | same |

Their shared low suffix is $00_4$, and the first mismatch from the right is at $j=2$.

Start from their common terminal state $I$:

1. Undo the common digit 0 at $k=0$. Both states rewind from $I$ to $S$.
2. Undo the common digit 0 at $k=1$. Both states rewind from $S$ to $I$.

Therefore the common state immediately after the mismatch at $k=2$ is

$$
h=I.
$$

At the mismatch:

- index 0 has digit 0, with child corner $c_0=(0,0)$;
- index 80 has digit 1, with child corner $c_1=(0,1)$.

Apply the same recovered symmetry $h=I$:

$$
h(c_0)=(0,0),
\qquad
h(c_1)=(0,1).
$$

These pairs differ in exactly one coordinate. That is the odd-digit-difference case of the pair law.

The complete points are

$$
H(0)=(0,0),
\qquad
H(80)=(0,12).
$$

Their planar chord is $(0,12)$, whose reduced parity pattern likewise has exactly one odd coordinate.

---

## Companion comparison: indices 0 and 96

Now compare

$$
0=0000_4,
\qquad
96=1200_4.
$$

Again:

- both terminal states are $I$;
- the shared low suffix is $00_4$;
- the first mismatch from the right is at $j=2$;
- rewinding the suffix recovers the same $h=I$.

At the mismatch, the digits are 0 and 2:

$$
h(c_0)=(0,0),
\qquad
h(c_2)=(1,1).
$$

Now both coordinate bits differ. This is the digit-difference-2 case of the pair law.

The complete points are

$$
H(0)=(0,0),
\qquad
H(96)=(4,12).
$$

After removing their common factor 4, the planar chord becomes $(1,3)$, whose two coordinates are both odd.

---

## What could fail without matching terminal states?

The two words could still share the same low suffix, but the backward process would begin from two different final orientations.

Undoing identical digits from different states does not make those states equal. At the mismatch, the two corners might then be viewed through different symmetries:

$$
h_m(c_d)
\qquad\text{and}\qquad
h_n(c_e).
$$

With $h_m\neq h_n$, the proof no longer has one common transformation preserving the Gray-code comparison between $c_d$ and $c_e$.

So equal terminal state does not say that the points are equal, nearby, or similarly oriented everywhere. It gives one precise capability:

> The common low suffix can be rewound in lockstep until both mismatching child corners are viewed through one common square symmetry.

---

## Why the selector cares about terminal states

There are only four reachable terminal states:

$$
I,S,T,C.
$$

The selector examines each block of sixteen consecutive Hilbert indices. Appending two base-4 digits gives enough steering freedom to make the selected index finish in one chosen terminal state.

Thus the selector arranges that every retained index belongs to one common terminal class. The bounded offsets keep successive selected indices close enough to give a finite step menu; the shared terminal state makes the pair law available for every pair of selected points.

The exact suffix choices and offsets are optional machinery developed in [Lesson 03A](03A%20-%20Why%20I%2C%20S%2C%20T%2C%20and%20C%20Choose%20Those%20Offsets.md).

---

## What to remember

1. The terminal state is the outgoing orientation left after the final base-4 digit.
2. It records the parity of the number of 0 digits and the number of 3 digits.
3. Its four possible values are $I,S,T,C$.
4. Equal terminal states let us rewind a shared low suffix in lockstep.
5. After rewinding, the first mismatching corners are compared through one common square symmetry.
6. That common symmetry preserves “one coordinate differs” versus “both coordinates differ,” which is the geometric half of the pair law.

A short version suitable for recall is:

> A terminal state is the Hilbert decoder’s leftover orientation memory. If two indices finish in the same state, their identical final base-4 digits can be undone together, aligning the orientation at their first mismatch. The mismatch then controls whether one or both coordinate bits differ.

---

## Tiny checkpoint

1. Is a terminal state a coordinate, an endpoint, or leftover decoder memory?
2. Which digits can change the terminal state?
3. What terminal state results when a base-4 word contains an odd number of 0s and an odd number of 3s?
4. Why do equal terminal states plus a common low suffix let us recover one common state after the first mismatch?
5. For $0000_4$ versus $1100_4$, do the mismatching digits 0 and 1 produce a difference in one coordinate bit or both?
6. What exact part of the comparison can fail when the terminal states are different?
