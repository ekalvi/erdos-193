# Erdős 193 — Why the Hilbert Pair Law Is True

**Previous:** [04 - Powers of Two as a Fingerprint](04%20-%20Powers%20of%20Two%20as%20a%20Fingerprint.md)  
**Proof roadmap:** [02 - Trace, Select, and Lift](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md)  
**Optional selector machinery:** [03A - Why I, S, T, and C Choose Those Offsets](03A%20-%20Why%20I%2C%20S%2C%20T%2C%20and%20C%20Choose%20Those%20Offsets.md)

## First: feedback on the previous checkpoint

Your ordinary integer valuations were all correct:

$$
\nu_2(40)=3,\qquad \nu_2(18)=1,\qquad \nu_2(7)=0.
$$

Your retry uses the right distinction. There is one arithmetic transcription error:

$$
\frac{(6,12)}{2}=(3,6),
$$

not $(3,4)$. Exactly one coordinate of $(3,6)$ is odd, so

$$
V(6,12)=2.
$$

For the second vector,

$$
\frac{(6,10)}{2}=(3,5).
$$

Both reduced coordinates are odd, so

$$
V(6,10)=3.
$$

Your conclusion was therefore correct: the two vectors have the same common exponent $p=1$, but different reduced parity patterns.

You correctly computed the scaling example:

$$
V(u)=3\quad\Longrightarrow\quad V(4u)=3+2\nu_2(4)=7.
$$

Your ordinary-language pair-law statement is also correct. More precisely, for two same-terminal-state Hilbert indices, the fingerprint of their **planar displacement** equals the 2-adic valuation of their **index gap**.

---

## What the vector fingerprint remembers—and forgets

The fingerprint $V(u)$ remembers exactly two things:

1. the exponent $p$ of the largest power of two dividing both coordinates;
2. whether, after removing that power, exactly one coordinate is odd or both are odd.

It deliberately forgets:

- the exact coordinate values;
- their signs;
- the vector’s length;
- its slope or direction;
- all odd factors;
- when the coordinate valuations differ, which coordinate has the smaller one.

For example,

$$
(6,12),\qquad(10,28),\qquad(-14,20)
$$

all have fingerprint 2. In each case the coordinate valuations are 1 and 2 in some order, even though the vectors point in different directions and have different lengths.

That information loss is intentional. The proof needs one feature that behaves predictably under scaling, not a complete description of each chord.

---

## The statement we need to understand

> [!tip] Terminal-state prerequisite
> If “same terminal state” is still only a phrase, read [05D — What the Hilbert Terminal State Remembers](05D%20-%20What%20the%20Hilbert%20Terminal%20State%20Remembers.md) before continuing. It explains the final orientation memory and the backward-rewind argument used below.

For two different Hilbert indices $m$ and $n$ with the same terminal state, the pair law says

$$
V\bigl(H(n)-H(m)\bigr)=\nu_2(|n-m|).
$$

The left side examines the planar displacement. The right side examines the time gap.

Why should those completely different-looking quantities agree?

The bridge is that:

> One base-4 digit of the index controls one binary digit in each planar coordinate.

We will now build the law from that fact.

---

## Four Hilbert children and their coordinate bits

At one recursive level, the Hilbert path visits four child squares in this order:

| Base-4 digit | Child-corner bits |
|---:|---:|
| $0$ | $(0,0)$ |
| $1$ | $(0,1)$ |
| $2$ | $(1,1)$ |
| $3$ | $(1,0)$ |

Notice the order:

$$
(0,0),\quad(0,1),\quad(1,1),\quad(1,0).
$$

Consecutive corners differ in exactly one coordinate. This is sometimes called a Gray-code order.

There are two ways two different digits can compare:

### Their difference is odd

The possible odd absolute differences are $1$ and $3$. Difference 1 occurs for $0$ versus $1$, $1$ versus $2$, or $2$ versus $3$; difference 3 occurs for $0$ versus $3$.

Their corner-bit pairs differ in exactly **one** coordinate.

### Their difference is 2 modulo 4—that is, the digits differ by 2

The pairs are $0$ versus $2$, or $1$ versus $3$.

“Modulo 4” classifies integers by the remainder left after division by 4. Saying

$$
k\equiv2\pmod4
$$

means that $k$ leaves remainder 2 after division by 4. Examples are

$$
2,6,10,14,\ldots
$$

For our base-4 digits, the phrase is simpler than it sounds: the relevant pairs differ by exactly 2. A signed difference may be $2$ or $-2$, but these are equivalent modulo 4 because they differ from each other by 4.

Their corner-bit pairs differ in **both** coordinates.

This one-coordinate-versus-both-coordinates distinction is exactly what the odd/even part of $V$ records.

---

## Find the first differing base-4 digit from the right

Write $m$ and $n$ in base 4, padding with leading zeros if necessary. Compare their digits from the right-hand, least-significant end.

Suppose the first place where they differ is position $j$.

That means:

- the lowest $j$ base-4 digits are identical;
- the digits at position $j$ are different.

For example, the schematic numbers

$$
(\cdots 2\,103)_4
\qquad\text{and}\qquad
(\cdots 3\,103)_4
$$

have the same three low digits $103$, so their first possible mismatch is at position $j=3$.

---

## What this says about the index gap

> [!tip] Place-value bridge
> If the next paragraph feels too compressed, read [05A - Why Matching Final Digits Forces Divisibility](05A%20-%20Why%20Matching%20Final%20Digits%20Forces%20Divisibility.md). It derives this step using decimal and base-4 subtraction before returning to the pair law.

Because the lowest $j$ base-4 digits agree, their difference is divisible by

$$
4^j=2^{2j}.
$$

So the index gap already contains at least $2j$ factors of two.

What happens next depends on the two mismatching digits.

### Odd digit difference

After removing $4^j$, the remaining difference is odd. Therefore

$$
\nu_2(|n-m|)=2j.
$$

### Digit difference equal to 2 modulo 4

After removing $4^j$, the remaining difference is divisible by 2 but not 4. Therefore

$$
\nu_2(|n-m|)=2j+1.
$$

Thus the parity of the mismatching base-4 digits determines whether the valuation is $2j$ or $2j+1$.

---

## What the same mismatch says about the planar chord

> [!note] Need notation background?
> If $k$, $q_k$, $\in$, $\{0,1\}^2$, “emits,” or the summation signs are unfamiliar, read [Lesson 05B — How to Read the Hilbert Digit Notation](05B%20-%20How%20to%20Read%20the%20Hilbert%20Digit%20Notation.md) before continuing.

This is the less obvious half of the pair law. We need to connect digits of the **index** to divisibility of the two **coordinate differences**.

### One base-4 digit emits two coordinate bits

Write the Hilbert point as

$$
H(n)=(x(n),y(n)).
$$

At every base-4 position $k$, the Hilbert rule reads one index digit $q_k\in\{0,1,2,3\}$ and emits a pair of bits

$$
(x_k,y_k)\in\{0,1\}^2.
$$

The first emitted bit becomes binary position $k$ of the $x$-coordinate, and the second becomes binary position $k$ of the $y$-coordinate:

$$
x(n)=\sum_k x_k2^k,
\qquad
y(n)=\sum_k y_k2^k.
$$

So one base-4 index position does **not** become two binary positions in one coordinate. It becomes:

> one binary bit of $x$ and one binary bit of $y$, both at the same position.

In the basic orientation, the digit-to-bit-pair table is

| Base-4 digit | Emitted coordinate bits |
|---:|---:|
| $0$ | $(0,0)$ |
| $1$ | $(0,1)$ |
| $2$ | $(1,1)$ |
| $3$ | $(1,0)$ |

Rotated or reflected Hilbert copies may swap or complement these bits, but they preserve whether two emitted pairs differ in one coordinate or both.

### Why matching index digits give matching coordinate bits here

This implication uses both hypotheses:

1. the lowest $j$ base-4 digits of $m$ and $n$ agree;
2. $m$ and $n$ have the same terminal state.

The terminal state is the orientation memory of the Hilbert decoder. Starting from one common terminal state, mentally rewind the two identical low-digit suffixes in parallel. At every position below $j$, both indices encounter:

- the same orientation;
- the same base-4 digit;
- therefore the same emitted pair of coordinate bits.

Thus the lowest $j$ binary bits of $x(m)$ and $x(n)$ agree, and the lowest $j$ binary bits of $y(m)$ and $y(n)$ agree.

> [!important]
> Matching low index digits by themselves are not the whole reason. The same-terminal-state condition aligns the decoder orientations so those matching digits emit matching coordinate bits.

### Matching low binary bits force coordinate divisibility

This is the binary version of the place-value cancellation in Lesson 05A.

If two $x$-coordinates share their lowest $j$ binary bits, call the common low-bit value $L_x$. We can write

$$
x(m)=2^jA_x+L_x,
\qquad
x(n)=2^jB_x+L_x.
$$

Subtracting cancels the shared low bits:

$$
x(n)-x(m)=2^j(B_x-A_x).
$$

Therefore $x(n)-x(m)$ is divisible by $2^j$. The identical argument for $y$ gives

$$
y(n)-y(m)=2^j(B_y-A_y).
$$

Consequently the planar chord

$$
H(n)-H(m)
$$

has both coordinates divisible by $2^j$.

This establishes only a **common minimum** of $j$ factors. The first mismatch tells us whether exactly one coordinate stops being divisible there or both do.

### What happens at binary position $j$

At position $j$, the two base-4 digits are different. Because the indices have aligned orientation, compare their two child-corner bit pairs through one common square symmetry.

#### Odd digit difference: one coordinate bit changes

If the base-4 digits differ by 1 or 3, their emitted pairs differ in exactly one coordinate.

For the coordinate whose bit changes at position $j$:

- all lower bits agree, giving a factor $2^j$;
- the bit at position $j$ differs, so no further factor of 2 is possible.

That coordinate difference has valuation exactly $j$.

The other coordinate’s bit at position $j$ still agrees, so its difference remains divisible by $2^{j+1}$. Its valuation is greater than $j$ (or infinite if that coordinate difference is zero).

Therefore the two coordinate valuations have:

$$
\min\{\nu_2(\Delta x),\nu_2(\Delta y)\}=j
$$

but are unequal. By the definition of the vector fingerprint,

$$
V(H(n)-H(m))=2j.
$$

#### Digit difference 2: both coordinate bits change

If the base-4 digits differ by 2, their emitted pairs differ in both coordinates.

For both coordinates:

- all lower bits agree, giving a factor $2^j$;
- the bit at position $j$ differs, preventing another factor of 2.

Thus

$$
\nu_2(\Delta x)=\nu_2(\Delta y)=j.
$$

The minimum is again $j$, but now the coordinate valuations are equal. Therefore

$$
V(H(n)-H(m))=2j+1.
$$

Higher binary positions contribute multiples of $2^{j+1}$. They cannot change whether the difference at position $j$, after division by $2^j$, is odd or even.

### Two concrete same-state examples

These examples use actual points of the Hilbert path. All three displayed indices have the same terminal state.

#### Odd mismatch at $j=2$

Take

$$
m=0=0000_4,
\qquad
n=80=1100_4.
$$

The two low base-4 digits $00$ agree. The first mismatch is at position $2$, where the digits are $0$ and $1$, an odd difference.

The Hilbert points are

$$
H(0)=(0,0),
\qquad
H(80)=(0,12).
$$

Hence the planar chord is

$$
H(80)-H(0)=(0,12)=4(0,3).
$$

After removing $2^j=2^2=4$, exactly one coordinate is odd. Therefore

$$
V(0,12)=2j=4.
$$

The index gap agrees:

$$
80=16\cdot5=2^4\cdot5,
\qquad
\nu_2(80)=4.
$$

#### Difference-2 mismatch at $j=2$

Now take

$$
m=0=0000_4,
\qquad
n=96=1200_4.
$$

Again the two low digits $00$ agree, but the first mismatching digits are now $0$ and $2$.

The Hilbert points are

$$
H(0)=(0,0),
\qquad
H(96)=(4,12).
$$

The planar chord is

$$
H(96)-H(0)=(4,12)=4(1,3).
$$

After removing $2^j=4$, both coordinates are odd. Therefore

$$
V(4,12)=2j+1=5.
$$

The index gap again agrees:

$$
96=32\cdot3=2^5\cdot3,
\qquad
\nu_2(96)=5.
$$

The two examples isolate the entire mechanism:

| Mismatch at position $j=2$ | Reduced chord after dividing by $2^j$ | Fingerprint | Index-gap valuation |
|---|---:|---:|---:|
| digits $0$ and $1$ | $(0,3)$: exactly one odd | $4$ | $4$ |
| digits $0$ and $2$ | $(1,3)$: both odd | $5$ | $5$ |

---

## The two sides now match

Both the index gap and the planar chord are controlled by the same first mismatching base-4 digit:

| First mismatch | Index-gap valuation | Reduced planar-coordinate pattern | Vector fingerprint |
|---|---:|---|---:|
| digit difference odd | $2j$ | exactly one coordinate odd | $2j$ |
| digit difference $2$ modulo $4$ | $2j+1$ | both coordinates odd | $2j+1$ |

Therefore

$$
V\bigl(H(n)-H(m)\bigr)=\nu_2(|n-m|).
$$

That is the Hilbert pair law.

---

## So what does “same terminal state” do?

The child-corner table is repeatedly rotated or reflected as the Hilbert pattern recurses. Without controlling orientation, two indices could interpret their mismatching digits through different rotated or reflected copies of the pattern.

A terminal state is just a small piece of memory recording this cumulative orientation. It is **not** the point’s location and it is not another coordinate.

When $m$ and $n$ have the same terminal state, we can mentally rewind their identical low-digit suffix in lockstep. At the first mismatch, both child corners are being viewed through the same square symmetry.

That common symmetry might swap or flip coordinates, but it preserves the only distinction we care about:

- two corners differing in one coordinate still differ in one coordinate;
- two corners differing in both coordinates still differ in both.

So “same terminal state” means:

> The two indices have aligned orientation context, allowing the first digit mismatch to produce the same one-coordinate-versus-both-coordinate rule in both points.

This is all you need from the state machinery for the main proof.

---

## Two small examples

### Mismatch at position $j=0$

There are no matching lower digits.

- Digits $0$ and $1$ differ by an odd number. Their corners $(0,0)$ and $(0,1)$ differ in one coordinate. Both sides of the pair law equal 0.
- Digits $0$ and $2$ differ by 2. Their corners $(0,0)$ and $(1,1)$ differ in both coordinates. Both sides equal 1.

### Mismatch at position $j=1$

The lowest base-4 digit agrees, so the index gap is divisible by $4=2^2$, and both planar-coordinate differences are divisible by $2$.

- If the mismatching digits differ by an odd number, the index valuation and vector fingerprint are both $2$.
- If they differ by 2 modulo 4, the index valuation and vector fingerprint are both $3$.

Each additional matching low base-4 digit adds 2 to both sides of the law.

---

## The pair law in ordinary language

> For two same-state Hilbert times, find the first base-4 digit where the times differ when reading from the right. Its position gives the common power-of-two scale, and the type of digit mismatch says whether one or both planar coordinate bits change. Those two pieces of information are encoded identically by the time-gap valuation and the planar-vector fingerprint.

This is a theorem about **all** same-state pairs, not a pattern inferred from finite examples.

---

## Checkpoint

1. Correct the fingerprints: what are $V(6,12)$ and $V(6,10)$?
2. If two coordinate valuations are equal, does that force one particular fingerprint, or only force the fingerprint to be odd? Explain.
3. If the first base-4 mismatch is at position $j=2$ and the digit difference is odd, what are the index-gap valuation and chord fingerprint?
4. What changes if that digit difference is 2 modulo 4?
5. Explain “same terminal state” without naming any of the states or transformations.
6. In one or two sentences, why do the two sides of the pair law agree?


## Checkpoint feedback

Answers 1, 3, and 4 are correct:

$$
V(6,12)=2,\qquad V(6,10)=3,
$$

and a mismatch at $j=2$ gives either

$$
2j=4
$$

for an odd digit difference, or

$$
2j+1=5
$$

for a digit difference of 2 modulo 4. In each case the index-gap valuation and chord fingerprint have the same value.

### Repair to answer 2

Equal coordinate valuations do **not** allow either reduced parity pattern. If

$$
\nu_2(u_x)=\nu_2(u_y)=p,
$$

then dividing both coordinates by $2^p$ makes **both** coordinates odd. Thus equality of the two valuations forces the fingerprint to be odd:

$$
V(u)=2p+1.
$$

It does not force one particular numerical fingerprint because $p$ could be 0, 1, 2, and so on.

### Repair to answer 5

Your answer describes how the final state is calculated. The requested ordinary-language meaning is:

> Two indices have the same terminal state when, after all their base-4 digits have been decoded, the decoder is carrying the same leftover orientation memory.

That common leftover memory is useful because a shared final string of digits can then be undone in lockstep. Immediately after that shared suffix has been removed, both mismatching digits are viewed through one common orientation.

Commutativity helps calculate the terminal state from the whole digit word. **Invertibility** is the property used by the backward-rewind argument.

### Refinement to answer 6

Your central idea is correct. The complete bridge has three parts:

1. the first mismatch from the right is at the same position $j$ on both sides;
2. the same digit difference selects the same $2j$-versus-$2j+1$ branch;
3. equal terminal states plus the common low suffix ensure that the two mismatching digits are interpreted through one common orientation.

Rewind undoes digit-dependent state changes; it does not literally remove coordinate bits.

## Repair cleared

Your restatement of answer 2 is correct with two notation refinements:

- call the common coordinate valuation $p$, reserving $j$ for a base-4 mismatch position;
- $p$ may be zero, not only positive.

Thus equal coordinate valuations force

$$
V(u)=2p+1,
$$

which is odd, but they do not determine one particular odd value.

Your restatement of answer 5 is correct: the terminal state is the leftover orientation memory after the decoder has processed the complete base-4 index. Two different points can finish with the same memory.

The pair-law prerequisite is now clear enough to continue.

**Next:** [06 - Why Three Lifted Points Cannot Be Collinear](06%20-%20Why%20Three%20Lifted%20Points%20Cannot%20Be%20Collinear.md)
