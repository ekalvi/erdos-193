# Erdős 193 — What the Hilbert Terminal State Remembers

**Previous:** [05C — How Orientation Changes While Decoding](05C%20-%20When%20Hilbert%20Orientation%20Applies.md)

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

### Your “one more recursion” interpretation

Yes: for a finite base-4 word $w$, the state after its final digit is terminal only because the word has ended.

If we extend that recursive address by appending one finer-scale digit $d$ on the **right**,

$$
w\longrightarrow wd,
$$

then the old terminal state $\sigma(w)$ becomes the incoming orientation used to decode $d$:

```text
decode every digit of w
        ↓
state σ(w): terminal because w stops here
        ↓ append a new finer digit d
the same state σ(w): incoming orientation for d
```

Appending $d$ creates a longer recursive address and therefore a different finite Hilbert index. It is not merely another spelling of the old index.

Do not confuse this with the construction’s permitted even padding. Prepending $00_4$ on the **left** processes those zeros before $w$; their two swaps cancel, so the represented point and terminal state remain unchanged. Left padding does not place a new digit after the old terminal state.

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

## Why the permitted leading-zero padding does not change the state

The parity restriction matters:

> One extra leading zero generally changes the orientation. Two extra leading zeros cancel.

Each zero contributes $S$. Therefore

$$
0\quad\text{contributes}\quad S,
$$

while

$$
00\quad\text{contributes}\quad S\circ S=I.
$$

The construction defines $H(n)$ using a base-4 word of **even length**. If a longer representation is needed, it adds zeros while keeping the total length even. Any two allowed even lengths differ by an even number, so one allowed representation is obtained from another by prepending pairs $00_4$.

For example, compare three finite decodings of the integer 5:

| Written word | Length | Allowed by the even-length definition of $H(5)$? | Decoder point | Terminal state |
|---:|---:|---:|---:|---:|
| $11_4$ | 2 | yes | $(0,3)$ | $I$ |
| $011_4$ | 3 | no | $(3,0)$ | $S$ |
| $0011_4$ | 4 | yes | $(0,3)$ | $I$ |

The single added zero in $011_4$ changes both the finite decoder point and the terminal state. The second added zero in $0011_4$ cancels that swap and restores the original decoding.

Thus the allowed representations

$$
11_4,\qquad0011_4,\qquad000011_4,\qquad\ldots
$$

all give the same point and terminal state. They differ by pairs of leading zeros.

For a base-4 word whose ordinary length is odd, the smallest allowed representation does begin with one zero so that its total length becomes even. Every other allowed representation then adds two more zeros at a time. The terminal state $\sigma(n)$ is defined from these even-padded words, not from an arbitrary number of leading zeros.

When two indices are compared, both are padded to one common even length. This makes their coordinates and terminal states compatible.

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

> [!important] How important is rewind?
> Rewind is **load-bearing but local**. You do not need it to define the Hilbert path, decode $H(n)$, or understand the trace-select-lift construction at a high level. It is essential to this proof of the Hilbert pair law: it converts “same terminal state” plus “same low suffix” into “same orientation immediately after the first mismatch.”
>
> You do not need to memorize the state tables. Retain one implication:
>
> $$\text{same terminal state}+\text{same final digits}\Longrightarrow\text{same state after undoing those digits}.$$
>
> A different proof could hide this in a complete transition-table calculation, but it would still need the same invertibility fact in another form.

## Rewind means undoing known state toggles

The word **rewind** sounds more sophisticated than the operation.

The terminal state remembers two on/off orientation switches:

- reading digit 0 toggles $S$;
- reading digit 3 toggles $T$;
- digits 1 and 2 toggle nothing.

Both toggles undo themselves:

$$
S\circ S=I,
\qquad
T\circ T=I.
$$

Therefore, if we know the digit that was just read, we undo its state change by applying the same toggle again:

| Digit being undone | Forward effect | Backward undo |
|---:|---:|---:|
| 0 | add $S$ | add $S$ again |
| 1 | no change | no change |
| 2 | no change | no change |
| 3 | add $T$ | add $T$ again |

For example, suppose digit 0 changed an earlier state $S$ into the outgoing state $I$:

$$
S\circ S=I.
$$

If we know the outgoing state is $I$ and the digit was 0, apply $S$ once more:

$$
I\circ S=S.
$$

That recovers the earlier state.

The only logical rule needed for rewinding two words is:

> Equal outgoing states, undone through the same known digit, produce equal preceding states.

---

## Put every state of $0000_4$ and $1100_4$ on one line

Compare

$$
0=0000_4
\qquad\text{and}\qquad
80=1100_4.
$$

Their digits and forward state histories are:

| Word | Start | After position 3 | After position 2 | After position 1 | After position 0 |
|---:|---:|---:|---:|---:|---:|
| $0000_4$ | $I$ | $S$ | $I$ | $S$ | $I$ |
| $1100_4$ | $I$ | $I$ | $I$ | $S$ | $I$ |

The last column is the terminal state. Both words finish in $I$.

Reading from the right, positions 0 and 1 contain the same suffix digits:

```text
0000
  └─┴─ common suffix 00

1100
  └─┴─ common suffix 00
```

Their first mismatch from the right is at position 2:

| Position | 3 | 2 | 1 | 0 |
|---:|---:|---:|---:|---:|
| $0000_4$ | 0 | **0** | 0 | 0 |
| $1100_4$ | 1 | **1** | 0 | 0 |
| Comparison from right | may differ | first mismatch | same | same |

The forward table already reveals an important fact: although the states differ after position 3, they have become equal immediately after the mismatching digits at position 2. Both are $I$ there.

The rewind argument is how the proof discovers that equality from information at the right-hand end.

---

## Rewind the common suffix one digit at a time

Begin at the right-hand end:

```text
terminal state of 0000 = I
terminal state of 1100 = I
```

### Undo the common digit 0 at position 0

Both words end in $I$, and both read digit 0 at position 0. Undo a 0 by toggling $S$:

$$
I\circ S=S.
$$

Therefore both states immediately before position 0—equivalently, immediately after position 1—were $S$.

### Undo the common digit 0 at position 1

Both recovered states are $S$, and both words again read digit 0. Toggle $S$ again:

$$
S\circ S=I.
$$

Therefore both states immediately before position 1—equivalently, immediately after position 2—were $I$.

We have now removed the entire common suffix $00_4$. We arrive at one common state immediately after the first mismatch:

$$
h=I.
$$

Nothing mysterious occurred:

```text
same terminal I
    ↑ undo the same final 0
same state S
    ↑ undo the same preceding 0
same state I immediately after the mismatch
```

---

## What happens at the mismatch

At position 2:

- $0000_4$ has digit 0;
- $1100_4$ has digit 1.

Their incoming states at that position are not equal:

- the first word enters digit 0 in state $S$;
- the second word enters digit 1 in state $I$.

Process each digit:

| Word | Incoming state | Mismatch digit | Pair emitted | Outgoing state |
|---:|---:|---:|---:|---:|
| $0000_4$ | $S$ | 0 | $S(0,0)=(0,0)$ | $I$ |
| $1100_4$ | $I$ | 1 | $I(0,1)=(0,1)$ | $I$ |

The two emitted pairs are

$$
(0,0)
\qquad\text{and}\qquad
(0,1).
$$

They differ in exactly one coordinate bit: the y-bit.

This answers checkpoint question 5.

The complete points are

$$
H(0)=(0,0),
\qquad
H(80)=(0,12).
$$

Their planar chord is $(0,12)$, whose reduced parity pattern likewise has exactly one odd coordinate.

---

## Why one common outgoing state is enough in general

The example used common outgoing state $h=I$. In another pair, the recovered state $h$ could be $S$, $T$, or $C$.

The Hilbert transition has one specially designed property: each digit’s local turn leaves that digit’s chosen corner fixed. Consequently, once we know the outgoing state $h$ after a digit $q$, that digit’s emitted pair can be recovered as

$$
h(c_q).
$$

So if the mismatching digits are $d$ and $e$, their two emitted pairs are

$$
h(c_d)
\qquad\text{and}\qquad
h(c_e).
$$

The same transformation $h$ acts on both basic child corners.

Every square transformation $I,S,T,$ or $C$ preserves whether two corners differ in:

- exactly one coordinate; or
- both coordinates.

That is why equal terminal states plus a shared low suffix recover the Gray-code one-bit-versus-two-bit comparison at the mismatch.

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

## What actually fails when terminal states differ?

Use an example that still has a common low suffix:

$$
0=0000_4,
\qquad
56=0320_4.
$$

Their final digit at position 0 is the same:

```text
0000
   └─ common suffix 0

0320
   └─ common suffix 0
```

Their first mismatch from the right is at position 1:

- $0000_4$ has digit 0;
- $0320_4$ has digit 2.

Those digits differ by 2. In one common orientation, their basic corners $(0,0)$ and $(1,1)$ would differ in both coordinate bits.

But the terminal states are different:

$$
\sigma(0000_4)=I,
\qquad
\sigma(0320_4)=T.
$$

Try to rewind the common final digit 0:

- undoing 0 from terminal state $I$ recovers $S$;
- undoing 0 from terminal state $T$ recovers $C$.

The recovered states remain different:

$$
S\neq C.
$$

Therefore there is no one common orientation after the mismatch.

At the mismatch itself, the actual decoding is:

| Word | Incoming state | Mismatch digit | Pair emitted | Outgoing state |
|---:|---:|---:|---:|---:|
| $0000_4$ | $I$ | 0 | $I(0,0)=(0,0)$ | $S$ |
| $0320_4$ | $C$ | 2 | $C(1,1)=(0,0)$ | $C$ |

The mismatching digits 0 and 2 would normally indicate that both coordinate bits differ. Here the two different orientations make the emitted pairs identical:

$$
(0,0)
\qquad\text{versus}\qquad
(0,0).
$$

That is the exact failure: without a common orientation, the Gray-code relationship between the two digit values no longer predicts the relationship between the two emitted pairs.

The failure propagates to the complete pair-law quantities:

$$
H(0)=(0,0),
\qquad
H(56)=(1,5).
$$

For their planar chord $(1,5)$,

$$
V(1,5)=1,
$$

while

$$
\nu_2(56)=3.
$$

They are unequal, as expected because the same-terminal-state hypothesis is absent.

In general, different terminal states make the backward process begin from different final orientations. Undoing identical suffix digits preserves that difference instead of creating equality. At the mismatch, the two corners are then viewed through two potentially different transformations:

$$
h_m(c_d)
\qquad\text{and}\qquad
h_n(c_e).
$$

With $h_m\neq h_n$, there is no common transformation preserving the one-coordinate-versus-both-coordinate comparison.

So equal terminal state gives one precise capability:

> The common low suffix can be rewound in lockstep until both mismatching child corners are viewed through one common square transformation.

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

### Checkpoint feedback

#### 1. What terminal state is

Correct: it is leftover decoder memory. If another finer digit were appended on the right, this state would become that digit’s incoming orientation.

One refinement: commutativity is not what makes the state terminal. The state is terminal simply because the word ends. The fact that $S$ and $T$ commute explains why the leftover state can be summarized using only the parity of the number of 0s and 3s.

#### 2. Which digits change it

Correct:

- digit 0 contributes $S$;
- digit 3 contributes $T$;
- digits 1 and 2 contribute $I$ and leave the state unchanged.

#### 3. Odd number of 0s and odd number of 3s

Correct:

$$
S\circ T=C.
$$

One uncancelled $S$ and one uncancelled $T$ combine into $C$.

#### 4. Why the rewind recovers one common state

Each known digit transition is reversible:

- undo 0 by applying $S$ again;
- undo 1 or 2 by doing nothing;
- undo 3 by applying $T$ again.

Start from equal terminal states. The two words have the same low suffix, so at each backward step they undo the same digit. Equal states subjected to the same undo operation remain equal. Repeating through the entire suffix yields one common state immediately after the first mismatch.

#### 5. $0000_4$ versus $1100_4$

The mismatching digits are 0 and 1. Their emitted pairs are

$$
(0,0)
\qquad\text{and}\qquad
(0,1).
$$

Exactly one coordinate bit differs: the y-bit.

#### 6. What fails with different terminal states

The rewind starts from different states. Undoing the same suffix digits does not make them equal, so the two mismatching corners can be interpreted through different orientations.

The concrete example $0000_4$ versus $0320_4$ shows the failure:

- mismatch digits 0 and 2 should differ in both bits under one common orientation;
- different orientations make both actual emitted pairs equal to $(0,0)$.

Therefore the raw digit difference no longer predicts whether one or both coordinate bits differ.
