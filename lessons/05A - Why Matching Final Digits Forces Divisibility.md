# Erdős 193 — Why Matching Final Digits Forces Divisibility

**Return afterward to:** [Note 05 — What this says about the index gap](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md#what-this-says-about-the-index-gap)  
**Background:** [04 - Powers of Two as a Fingerprint](04%20-%20Powers%20of%20Two%20as%20a%20Fingerprint.md)

## The source of the confusion

This part uses three phrases that are easy to blur together:

1. **the digits agree** — some rightmost written digits are identical;
2. **the index gap** — the result of subtracting the two complete index numbers;
3. **the mismatching-digit difference** — the subtraction of just the first two digits that do not agree.

They are related, but they are not the same object.

“Lowest” or “least significant” digits means the **rightmost** digits. The rightmost position has the smallest place value, namely 1.

The key fact comes from ordinary place value, not from the Hilbert path.

---

## Start with a decimal example

Consider

$$
82{,}347
\qquad\text{and}\qquad
15{,}347.
$$

Their final three decimal digits agree: both end in $347$.

Rewrite them by separating the common suffix:

$$
82{,}347=82\cdot1000+347,
$$

$$
15{,}347=15\cdot1000+347.
$$

Now subtract the complete numbers:

$$
\begin{aligned}
82{,}347-15{,}347
&=(82\cdot1000+347)-(15\cdot1000+347)\\
&=(82-15)\cdot1000\\
&=67\cdot1000.
\end{aligned}
$$

The matching suffix $347$ cancels. Therefore the difference is divisible by $1000=10^3$.

General decimal rule:

> If two decimal numbers have the same final $j$ digits, their difference is divisible by $10^j$.

---

## Base 4 uses the same place-value rule

Decimal place values are

$$
1,10,100,1000,\ldots
$$

Base-4 place values are

$$
1,4,16,64,\ldots
$$

More explicitly:

| Position from the right | Base-4 place value |
|---:|---:|
| $0$ | $4^0=1$ |
| $1$ | $4^1=4$ |
| $2$ | $4^2=16$ |
| $3$ | $4^3=64$ |

> [!warning] Digit positions start at zero
> A three-digit base-4 number has positions $2,1,0$, so its leftmost digit multiplies $4^2=16$. The value $4^3=64$ belongs to position 3, which first appears in a four-digit number such as $1000_4$.

For example,

$$
103_4=1\cdot16+0\cdot4+3\cdot1=19.
$$

Likewise,

$$
203_4=2\cdot16+0\cdot4+3\cdot1=35.
$$

The subscript 4 says to interpret the digits using powers of 4 rather than powers of 10.

---

## A concrete base-4 subtraction

Compare

$$
103_4
\qquad\text{and}\qquad
203_4.
$$

Their two rightmost base-4 digits agree: both end in $03_4$.

Their first mismatch from the right is at position $j=2$:

| Position | $2$ | $1$ | $0$ |
|---:|---:|---:|---:|
| First index | $1$ | $0$ | $3$ |
| Second index | $2$ | $0$ | $3$ |
| Comparison | different | same | same |

Subtracting in base 4 gives

$$
203_4-103_4=100_4.
$$

And

$$
100_4=4^2=16.
$$

So matching two rightmost base-4 digits forced the complete index gap to be divisible by

$$
4^2.
$$

---

## The general cancellation

Suppose two indices share their final $j$ base-4 digits. Let $R$ be the numerical value of that common suffix.

Then the indices can be written as

$$
m=4^jA+R,
$$

$$
n=4^jB+R,
$$

where $A$ and $B$ contain everything to the left of the shared suffix.

Subtract the complete indices:

$$
\begin{aligned}
n-m
&=(4^jB+R)-(4^jA+R)\\
&=4^j(B-A).
\end{aligned}
$$

The common suffix $R$ disappears. Therefore

$$
4^j\mid(n-m),
$$

which means that $n-m$ is divisible by $4^j$.

That is the entire reason matching final digits force divisibility.

---

## Why this creates $2j$ factors of two

Because

$$
4=2^2,
$$

we have

$$
4^j=(2^2)^j=2^{2j}.
$$

Therefore divisibility by $4^j$ guarantees at least $2j$ factors of two in the index gap:

$$
\nu_2(|n-m|)\ge2j.
$$

For the previous example, $j=2$, so

$$
4^j=4^2=16=2^4.
$$

The gap contains at least four factors of two.

---

## Why the note says “at least”

After factoring out $4^j$, the remaining multiplier $B-A$ might itself contain another factor of two.

Compare three examples.

### Mismatching digits differ by 1—an odd difference

$$
203_4-103_4=100_4=16.
$$

Here

$$
\nu_2(16)=4=2j.
$$

There is no extra factor of two after the guaranteed $4^2$.

### Mismatching digits differ by 3—also an odd difference

$$
303_4-003_4=300_4=48.
$$

The leading zero in $003_4$ does not change its value; it keeps the place values visually aligned. Here

$$
48=3\cdot16,
$$

so

$$
\nu_2(48)=4=2j.
$$

The multiplier 3 is odd, so again there is no extra factor of two beyond the guaranteed $4^2$.

### Mismatching digits differ by 2—the even difference

$$
303_4-103_4=200_4=32.
$$

Now

$$
32=2\cdot16,
$$

so

$$
\nu_2(32)=5=2j+1.
$$

The first mismatching digits differ by 2, providing one additional factor of two.

These cases are exhaustive. A base-4 digit can only be $0$, $1$, $2$, or $3$, so two unequal digits can have absolute difference only $1$, $2$, or $3$:

| Absolute digit difference | Parity | Extra factors of 2 after $4^j$ |
|---:|---:|---:|
| $1$ | odd | $0$ |
| $2$ | even but not divisible by $4$ | $1$ |
| $3$ | odd | $0$ |

The complete index gap may be much larger, because digits farther left may also differ. After factoring out $4^j$, however, those higher-place contributions are multiples of 4. They cannot change whether the remaining multiplier is odd or is 2 modulo 4.

That is why Note 05 splits into two cases:

- odd mismatching-digit difference gives $2j$ factors of two;
- mismatching digits differing by 2 gives $2j+1$ factors of two.

---

## One base-4 digit represents two binary places

This is the conversion worth remembering:

$$
\text{one base-4 place}=\text{two binary places},
$$

because

$$
4=2^2.
$$

Thus:

- $j$ matching low base-4 index digits force $2j$ binary factors into the **index gap**;
- the corresponding $j$ matching low coordinate bits force $j$ binary factors into each **coordinate gap**.

This apparent mismatch is exactly why the vector fingerprint uses $2p$ or $2p+1$.

For the Hilbert chord, the common coordinate exponent is $p=j$:

- if one coordinate bit changes at the mismatch, $V=2j$;
- if both coordinate bits change, $V=2j+1$.

Those are the same two values obtained from the index gap.

---

## A compact mental model

Picture cutting two base-4 indices into a left prefix and a shared right suffix:

$$
\boxed{A}\,\boxed{R}
\qquad\text{and}\qquad
\boxed{B}\,\boxed{R}.
$$

If the suffix has $j$ base-4 digits, its place-value width is $4^j$. Subtracting cancels the two copies of $R$, leaving

$$
4^j(B-A).
$$

So:

> Matching rightmost digits create trailing zeros in the difference.

In base 4, each trailing zero contributes two factors of two.

---

## Tiny checkpoint

1. Why is $72{,}125-41{,}125$ divisible by $1000$?
2. What are the decimal values of $103_4$ and $203_4$?
3. Why is their difference divisible by $4^2$?
4. Why does divisibility by $4^2$ guarantee four factors of two?
5. In this discussion, what is the difference between “the digits differ” and “the indices differ”?

After these feel routine, return to [the paused section of Note 05](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md#what-this-says-about-the-index-gap).
