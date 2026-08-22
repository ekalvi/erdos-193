# Erdős 193 — Why Three Lifted Points Cannot Be Collinear

**Previous:** [05 - Why the Hilbert Pair Law Is True](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md)  
**Proof roadmap:** [02 - Trace, Select, and Lift](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md)

## What is already available

The construction retains Hilbert indices that all have the same terminal state. Therefore the pair law applies to every pair of retained indices:

$$
V\bigl(H(n)-H(m)\bigr)=\nu_2(n-m)
\qquad(m<n).
$$

We also know how the planar fingerprint behaves under positive integer scaling:

$$
V(ku)=V(u)+2\nu_2(k).
$$

This lesson combines those two facts. No further Hilbert decoding is needed.

---

## Assume three lifted points are collinear

Suppose three retained indices satisfy

$$
a<b<c.
$$

Their lifted points are

$$
P_a=(H(a),a),\qquad
P_b=(H(b),b),\qquad
P_c=(H(c),c).
$$

The planar part is the Hilbert point $H(n)$. The height is the index $n$ itself.

Name the two consecutive height gaps:

$$
A=b-a,\qquad B=c-b.
$$

Name the corresponding planar chords:

$$
X=H(b)-H(a),\qquad
Y=H(c)-H(b).
$$

So the two three-dimensional displacement vectors are

$$
P_b-P_a=(X,A),\qquad
P_c-P_b=(Y,B).
$$

Assume, for contradiction, that the three lifted points are collinear.

---

## What collinearity forces

For the two displacement vectors to point along one line, their planar parts must scale in the same ratio as their height parts:

$$
\frac{X}{A}=\frac{Y}{B}.
$$

Vector division is only a picture. The exact integer statement is the cross-multiplied equation

$$
BX=AY.
$$

This means both coordinate equations hold:

$$
B X_x=A Y_x,
\qquad
B X_y=A Y_y.
$$

> [!important]
> Collinearity is what connects the planar chords $X,Y$ to the index gaps $A,B$. The pair law by itself only describes one pair at a time.

---

## Remove the common part of the two gaps

Let

$$
g=\gcd(A,B).
$$

Write

$$
A=gr,\qquad B=gs,
$$

where $r$ and $s$ are coprime. In ordinary language, $g$ is everything the two gaps share, while $r$ and $s$ are what remains after that common part is removed.

Substitute into the collinearity equation:

$$
(gs)X=(gr)Y.
$$

Cancel the nonzero common factor $g$:

$$
sX=rY.
$$

Because $r$ and $s$ are coprime, this forces the two integer chords to be integer multiples of one common nonzero planar vector $W$:

$$
X=rW,\qquad Y=sW.
$$

Why is $W$ still an integer vector? Coordinate by coordinate,

$$
sX_i=rY_i.
$$

Since $r$ shares no factor with $s$, every factor of $r$ must divide $X_i$. Thus $r$ divides both coordinates of $X$, and $W=X/r$ has integer coordinates. The equation then gives $Y=sW$.

At this point collinearity has reduced the picture to one direction $W$ with two integer scale factors $r$ and $s$.

---

## Apply the pair law to the first two pairs

Introduce four valuations:

$$
\gamma=\nu_2(g),\qquad
\alpha=\nu_2(r),\qquad
\beta=\nu_2(s),\qquad
w=V(W).
$$

### Pair $(a,b)$

Its index gap is $A=gr$. Therefore

$$
\nu_2(A)=\gamma+\alpha.
$$

Its planar chord is $X=rW$. The scaling law gives

$$
V(X)=w+2\alpha.
$$

The pair law says these are equal:

$$
\gamma+\alpha=w+2\alpha.
$$

Hence

$$
w=\gamma-\alpha.
$$

### Pair $(b,c)$

The same calculation with $B=gs$ and $Y=sW$ gives

$$
\gamma+\beta=w+2\beta,
$$

so

$$
w=\gamma-\beta.
$$

The same $w$ cannot equal both expressions unless

$$
\alpha=\beta.
$$

Thus $r$ and $s$ contain the same number of factors of two.

But $r$ and $s$ are coprime. If their common valuation were positive, both would be even and would share a factor of 2. Therefore

$$
\alpha=\beta=0.
$$

So both reduced gap factors are odd:

$$
r\text{ is odd},\qquad s\text{ is odd}.
$$

Returning to either adjacent-pair equation also gives

$$
w=\gamma.
$$

---

## Now use the endpoint pair

The endpoint index gap is

$$
c-a=A+B=g(r+s).
$$

The endpoint planar chord is

$$
H(c)-H(a)=X+Y=(r+s)W.
$$

Let

$$
\delta=\nu_2(r+s).
$$

The index-gap valuation is

$$
\nu_2(c-a)=\gamma+\delta.
$$

The scaling law gives the chord fingerprint

$$
V\bigl((r+s)W\bigr)=w+2\delta.
$$

Since $w=\gamma$, the endpoint pair law would require

$$
\gamma+\delta=\gamma+2\delta.
$$

Subtracting $\gamma$ gives

$$
\delta=2\delta,
$$

hence

$$
\delta=0.
$$

That says $r+s$ is odd.

But the adjacent pairs already forced both $r$ and $s$ to be odd. The sum of two odd integers is even, so

$$
\nu_2(r+s)\ge 1.
$$

That says $\delta\ge1$.

We have reached the contradiction:

$$
\delta=0
\qquad\text{and}\qquad
\delta\ge1.
$$

Therefore the original assumption was impossible: three lifted same-terminal-state Hilbert points cannot be collinear.

---

## The whole contradiction in one table

| Pair | Index gap | Planar chord | Pair-law valuation | Scaling-law fingerprint |
|---|---:|---:|---:|---:|
| $(a,b)$ | $gr$ | $rW$ | $\gamma+\alpha$ | $w+2\alpha$ |
| $(b,c)$ | $gs$ | $sW$ | $\gamma+\beta$ | $w+2\beta$ |
| $(a,c)$ | $g(r+s)$ | $(r+s)W$ | $\gamma+\delta$ | $w+2\delta$ |

The first two rows force $r$ and $s$ to be odd and $w=\gamma$. The third row then forces $r+s$ to be odd. But odd plus odd is even.

> [!important]
> All three applications of the pair law are essential. The first two control $r$ and $s$ separately; the endpoint pair exposes the impossible parity of their sum.

---

## Why the coefficient 2 matters

The contradiction comes from a deliberate mismatch between two scaling rules:

- multiplying an integer gap by $k$ adds $\nu_2(k)$ to its valuation;
- multiplying a planar vector by $k$ adds $2\nu_2(k)$ to its fingerprint.

Collinearity tries to make the index gap and planar chord scale together. The pair law says their fingerprints must remain equal. The coefficients 1 and 2 make that impossible across all three pairs.

---

## From-memory summary

> Assume three lifted points are collinear. After removing the gcd of the two consecutive index gaps, collinearity writes their planar chords as $rW$ and $sW$ with coprime $r,s$. The pair law and scaling law on the two adjacent pairs force $r,s$ to be odd, while applying them to the endpoint pair forces $r+s$ to be odd. Since odd plus odd is even, no such triple exists.

---

## Checkpoint

1. What do $A,B,X,$ and $Y$ represent?
2. Why does collinearity give $BX=AY$?
3. Why do we write $A=gr$ and $B=gs$ with coprime $r,s$?
4. How do the first two pair-law equations force both $r$ and $s$ to be odd?
5. Why does the endpoint pair force $r+s$ to be odd?
6. Give the contradiction in three sentences without looking back.
