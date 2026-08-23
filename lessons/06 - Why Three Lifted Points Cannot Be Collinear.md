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

> [!info] What does “coprime” mean?
> Two positive integers are **coprime** when their greatest common divisor is 1:
> $$
> \gcd(r,s)=1.
> $$
> Equivalently, they share no positive integer factor larger than 1. For example, 8 and 15 are coprime because their only shared positive factor is 1. Neither number needs to be prime: 8 is not prime.
>
> Here $r$ and $s$ must be coprime because we already removed the entire greatest common factor $g$ from $A$ and $B$. If $r$ and $s$ still shared a factor, then $g$ would not have been the greatest common divisor.

Substitute into the collinearity equation:

$$
(gs)X=(gr)Y.
$$

Cancel the nonzero common factor $g$:

$$
sX=rY.
$$

Now we will construct the common vector $W$ rather than jump directly to it.

Write the two planar chords in coordinates:

$$
X=(X_x,X_y),\qquad Y=(Y_x,Y_y).
$$

The vector equation

$$
sX=rY
$$

means that both coordinate equations hold:

$$
sX_x=rY_x,
\qquad
sX_y=rY_y.
$$

The first equation says that $r$ divides $sX_x$. Because $\gcd(r,s)=1$, Euclid’s lemma says that $r$ must divide $X_x$. The same argument applied to the second equation says that $r$ must also divide $X_y$.

> [!info] The divisibility fact being used
> If $\gcd(r,s)=1$ and $r$ divides $sz$, then $r$ divides $z$. Any prime factor supplied by $r$ cannot be supplied by $s$, so it must already occur in $z$.

Therefore both fractions below are integers:

$$
W_x=\frac{X_x}{r},
\qquad
W_y=\frac{X_y}{r}.
$$

Define

$$
W=(W_x,W_y).
$$

This definition immediately gives

$$
X=rW.
$$

Now substitute that back into $sX=rY$:

$$
s(rW)=rY.
$$

Cancel the positive integer $r$:

$$
sW=Y.
$$

Thus we have proved, rather than assumed,

$$
\boxed{X=rW,\qquad Y=sW.}
$$

The vector $W$ is nonzero because $X$ is nonzero and $X=rW$. Geometrically, $W$ is the common integer direction singled out after the coprime scale factors $r$ and $s$ have been separated from the two chords. It need not be a primitive vector; its coordinates may still share a factor.

For example, if $r=3$, $s=5$, and

$$
5X=3Y,
$$

then 3 must divide both coordinates of $X$. If

$$
X=(6,-3),
$$

we define

$$
W=X/3=(2,-1),
$$

and the equation forces

$$
Y=5W=(10,-5).
$$

At this point collinearity has reduced the picture to one nonzero integer direction $W$ with two integer scale factors $r$ and $s$.

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

> [!info] Why does the endpoint pair law force oddness?
> It does not assume that $r+s$ is odd. It derives oddness from the unequal way scalar factors enter the two invariants.
>
> If $r+s$ contains $\delta$ factors of 2, multiplying the **integer index gap** by $r+s$ increases its valuation by $\delta$:
> $$
> \gamma\longmapsto\gamma+\delta.
> $$
> But multiplying the **planar vector** $W$ by $r+s$ inserts those $\delta$ factors into both coordinates, so its fingerprint increases by $2\delta$:
> $$
> \gamma\longmapsto\gamma+2\delta.
> $$
> The endpoint pair law demands that these two results be equal. Their difference is $\delta$, so equality is possible only when $\delta=0$. Since
> $$
> \delta=\nu_2(r+s),
> $$
> this means $r+s$ has no factor of 2—that is, $r+s$ is odd.
>
> For the smallest contrary case, suppose $r+s$ had exactly one factor of 2. The index side would become $\gamma+1$, while the vector side would become $\gamma+2$. They could not satisfy the pair law.

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

### Feedback on your checkpoint attempt

1. **Correct.** $A=b-a$ and $B=c-b$ are the two index gaps. Because index is used as height, they are also the two height changes. $X=H(b)-H(a)$ and $Y=H(c)-H(b)$ are the corresponding **planar** Hilbert chords. Keep “planar chord” distinct from the full three-dimensional displacements $(X,A)$ and $(Y,B)$.

2. **Correct idea.** Collinearity says that the two full displacements have the same planar change per unit height:
   $$
   \frac{X}{A}=\frac{Y}{B}.
   $$
   Multiplying by $AB$ gives
   $$
   BX=AY.
   $$

3. **Partly remembered.** Writing
   $$
   A=gr,\qquad B=gs,\qquad g=\gcd(A,B)
   $$
   reduces the ratio of the gaps to lowest terms. This has two uses:
   - immediately, $\gcd(r,s)=1$ lets Euclid’s lemma construct the integer vector $W$ with $X=rW$ and $Y=sW$;
   - later, if $\nu_2(r)=\nu_2(s)$, coprimality forces that common valuation to be zero.

4. **Conclusion remembered; derivation needs repair.** Define
   $$
   \gamma=\nu_2(g),\qquad
   \alpha=\nu_2(r),\qquad
   \beta=\nu_2(s),\qquad
   w=V(W).
   $$
   The pair law applied to $(a,b)$ compares the gap $gr$ with the chord $rW$:
   $$
   \gamma+\alpha=w+2\alpha,
   $$
   so
   $$
   w=\gamma-\alpha.
   $$
   Applied to $(b,c)$, it similarly gives
   $$
   w=\gamma-\beta.
   $$
   Hence $\alpha=\beta$. Because $r$ and $s$ are coprime, they cannot both have a factor of 2, so
   $$
   \alpha=\beta=0.
   $$
   That is exactly why $r$ and $s$ are odd.

5. **Conclusion partly remembered; here is the missing mechanism.** Let
   $$
   \delta=\nu_2(r+s).
   $$
   From the adjacent pairs we already know $\alpha=\beta=0$, which also gives $w=\gamma$. For the endpoint pair $(a,c)$:
   - its index gap is $g(r+s)$, with valuation $\gamma+\delta$;
   - its planar chord is $(r+s)W$, with fingerprint $w+2\delta=\gamma+2\delta$.

   The pair law equates those quantities:
   $$
   \gamma+\delta=\gamma+2\delta.
   $$
   Therefore $\delta=0$, which means $r+s$ is odd.

6. **Correct.** Under the collinearity assumption, the adjacent pairs force $r$ and $s$ to be odd. The endpoint pair forces $r+s$ to be odd. But two odd integers have an even sum, so the assumption is impossible.

> [!question] Retry before moving on
> Without looking above, restate answers 3, 4, and 5. In answer 4, include why $\alpha=\beta$ becomes $\alpha=\beta=0$. In answer 5, include the two expressions $\gamma+\delta$ and $\gamma+2\delta$.

### Whiteboard reconstruction assessment

> [!success] Checkpoint cleared
> Your whiteboard reconstruction recovered the complete proof architecture: collinearity, reduced gap ratio, the common integer vector, two adjacent pair laws, the endpoint pair law, and the odd-plus-odd contradiction. The earlier gaps in answers 3–5 are now repaired.

The board correctly reconstructed:

1. $A=b-a$, $B=c-b$, $X=H(b)-H(a)$, and $Y=H(c)-H(b)$;
2. collinearity gives $X/A=Y/B$, hence $BX=AY$;
3. $A=gr$ and $B=gs$ with coprime $r,s$;
4. $sX=rY$, followed by $X=rW$ and $Y=sW$;
5. the adjacent equations
   $$
   w=\gamma-\alpha,
   \qquad
   w=\gamma-\beta;
   $$
6. $\alpha=\beta=0$, hence $r,s$ are odd and $w=\gamma$;
7. the endpoint comparison forcing $\delta=\nu_2(r+s)=0$;
8. the contradiction that $r+s$ is both odd and even.

There is one local algebra correction. From

$$
\gamma+\delta=w+2\delta,
$$

the rearranged equation is

$$
\boxed{w=\gamma-\delta,}
$$

not $w=\gamma-2\delta$. Equivalently, subtract $\delta$ from both sides first:

$$
\gamma=w+\delta.
$$

Since the adjacent pairs already gave $w=\gamma$, either corrected form yields

$$
\delta=0.
$$

Two contextual premises should also appear when this is written as a standalone proof:

- $a,b,c$ are **selected indices with one common terminal state**, which is why the pair law applies to all three pairs $(a,b)$, $(b,c)$, and $(a,c)$;
- $V$ accepts planar vectors, so write its scaling rule as
  $$
  V(kU)=V(U)+2\nu_2(k)
  $$
  for a nonzero planar vector $U$, rather than using $A$, which already denotes an integer index gap.

> [!question] Final compression exercise
> Give the proof in five to seven sentences of ordinary language, using no displayed equations. Preserve these four links: collinearity produces one common vector; the adjacent pair laws make $r,s$ odd; the endpoint pair law makes $r+s$ odd; odd plus odd is even.
