# Erdős 193 — Why the Hilbert Pair Law Is True

**Previous:** [04 - Powers of Two as a Fingerprint](04%20-%20Powers%20of%20Two%20as%20a%20Fingerprint.md)  
**Proof roadmap:** [02 - Trace, Select, and Lift](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md)  
**Optional selector machinery:** [03A - Why I, S, T, and C Choose Those Offsets](03A%20-%20Why%20I%2C%20S%2C%20T%2C%20and%20C%20Choose%20Those%20Offsets.md)

## First: feedback on the previous checkpoint

Your ordinary integer valuations were all correct:

$$
\nu_2(40)=3,\qquad \nu_2(18)=1,\qquad \nu_2(7)=0.
$$

Your reasoning about the two vector examples was also pointed in the right direction, but the final arithmetic used the common power instead of its exponent.

For

$$
u=(6,12),
$$

the largest common power is $2^1=2$, so $p=1$. After dividing by 2, exactly one coordinate is odd. Therefore

$$
V(6,12)=2p=2\cdot1=2.
$$

For

$$
u=(6,10),
$$

we again have $p=1$, but after dividing by 2 both coordinates are odd. Therefore

$$
V(6,10)=2p+1=2\cdot1+1=3.
$$

The key distinction is:

- $2^p$ is the common power of two;
- $p$ is the number of factors of two;
- the fingerprint formula uses $p$, not $2^p$.

You correctly computed the scaling example:

$$
V(u)=3\quad\Longrightarrow\quad V(4u)=3+2\nu_2(4)=7.
$$

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

Each base-4 digit position produces one binary bit position in each Hilbert coordinate.

Because the lowest $j$ index digits agree, the planar coordinates agree in all binary positions below $j$. Consequently both coordinate differences are divisible by $2^j$.

At binary position $j$, use the child-corner table:

### Odd digit difference

Exactly one coordinate bit differs. After removing the common factor $2^j$:

- exactly one coordinate difference is odd;
- the other remains even.

Therefore

$$
V(H(n)-H(m))=2j.
$$

### Digit difference equal to 2 modulo 4

Both coordinate bits differ. After removing the common factor $2^j$, both coordinate differences are odd. Therefore

$$
V(H(n)-H(m))=2j+1.
$$

Higher binary positions contribute multiples of $2^{j+1}$, so they cannot change whether the bit at position $j$ is odd or even after division by $2^j$.

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

Once this connection feels non-magical, the next lesson can use it to exclude a collinear triple.
