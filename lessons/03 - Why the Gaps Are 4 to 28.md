# Erdős 193 — Why the Gaps Are 4 to 28

**Previous:** [02 - Trace, Select, and Lift](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md)  
**Related:** [01 - The Problem in Plain English](01%20-%20The%20Problem%20in%20Plain%20English.md)

## Where your understanding is now

You have the main architecture. In your own words:

- follow the Hilbert path through “time”;
- choose one special point from each block;
- use time as height;
- exploit bounded gaps for the finite step menu;
- use the still-unexplained 2-adic pair law to prevent collinearity.

That is the correct proof outline.

Before opening the 2-adic black box, four details need sharpening.

---

## Adjustment 1: the order is trace, select, lift

The construction proceeds in this order:

1. **Trace** the complete planar Hilbert path $H(0),H(1),H(2),\ldots$.
2. **Select** special indices $n_0,n_1,n_2,\ldots$.
3. **Lift** only the selected planar points into three dimensions.

The final walk does not visit the unselected points.

---

## Adjustment 2: the lift is literal, not only a visualization

Writing

$$
P_a=(H(n_a),n_a)
$$

literally defines the third coordinate of $P_a$ to be $n_a$.

If we lifted every Hilbert point, time $n$ would rise by one unit whenever the Hilbert path advanced by one step. But the final walk retains only selected times. Therefore two consecutive vertices of the final walk rise by

$$
n_{a+1}-n_a,
$$

which can be anywhere from 4 to 28.

“Time as altitude” is a helpful picture, but it is also the exact mathematical construction.

---

## Adjustment 3: these are blocks of indices

The blocks are

$$
\{0,1,\ldots,15\},\quad
\{16,17,\ldots,31\},\quad
\{32,33,\ldots,47\},\quad\ldots
$$

Each block contains 16 consecutive **times** or **indices** along the Hilbert path.

Because of the Hilbert recursion, one may also picture those 16 points as a rotated or reflected $4\times4$ patch. It is not a $16\times16$ grid. More importantly, the finite-step proof does not need the patch picture. It needs only:

- each single Hilbert-time step moves to a neighboring planar grid point;
- consecutive selected times differ by at most 28.

---

## Your 1-to-31 intuition is correct—for arbitrary choices

Suppose we were free to select any offset from each 16-index block.

- The closest possible choices would be the last index of one block and the first index of the next: a gap of 1.
- The farthest possible choices would be the first index of one block and the last index of the next: a gap of 31.

So arbitrary one-per-block selection would indeed give

$$
1\le n_{a+1}-n_a\le31.
$$

The proof gets 4-to-28 because its selector does **not** use arbitrary offsets.

---

## The four allowed offsets

Every block begins at $16a$. The selector chooses

$$
n_a=16a+r_a,
$$

where the correction, or offset, is restricted to

$$
r_a\in\{1,3,5,13\}.
$$

Which of those four offsets is used depends on the Hilbert terminal state of the block index $a$. The mechanism choosing the correct offset will come later. For the gap calculation, only the four possible values matter.

### One selection, not four

The set $\{1,3,5,13\}$ lists four **candidate offsets**. It does not mean that all four points are retained from every block.

Each block has one terminal state, and that state determines one offset:

| Terminal state | Chosen offset |
|---|---:|
| $I$ | $5$ |
| $S$ | $1$ |
| $T$ | $13$ |
| $C$ | $3$ |

Thus each block contributes exactly one selected index $n_a$.

For example, block $a=7$ contains indices $112$ through $127$. If its state calls for offset $13$, the construction selects

$$
n_7=112+13=125
$$

and does **not** also select the points at offsets $1$, $3$, or $5$.

The four offsets describe the different positions that may be selected across different blocks. A useful picture is:

> Four candidate slots per block; the block's state activates exactly one slot.

The next selected index is

$$
n_{a+1}=16(a+1)+r_{a+1}.
$$

Subtracting gives

$$
\begin{aligned}
n_{a+1}-n_a
&=16(a+1)+r_{a+1}-(16a+r_a)\\
&=16+r_{a+1}-r_a.
\end{aligned}
$$

This says:

> Start with the 16-unit distance between the beginnings of consecutive blocks, then adjust for where each selected point sits inside its block.

---

## The smallest possible guaranteed gap

To make the gap as small as possible:

- select as late as allowed in the first block: $r_a=13$;
- select as early as allowed in the next block: $r_{a+1}=1$.

Then

$$
n_{a+1}-n_a=16+1-13=4.
$$

On a number line, these selected indices are

$$
16a+13
\qquad\text{and}\qquad
16a+17.
$$

Their difference is 4.

---

## The largest possible guaranteed gap

To make the gap as large as possible:

- select as early as allowed in the first block: $r_a=1$;
- select as late as allowed in the next block: $r_{a+1}=13$.

Then

$$
n_{a+1}-n_a=16+13-1=28.
$$

The selected indices are

$$
16a+1
\qquad\text{and}\qquad
16a+29.
$$

Their difference is 28.

Therefore

$$
4\le n_{a+1}-n_a\le28.
$$

These are safe bounds obtained from the allowed offsets. The proof does not need every integer gap from 4 through 28 to occur.

---

## Why a bounded index gap gives finitely many 3D steps

Suppose the index gap is $d$, where $4\le d\le28$.

The full Hilbert path takes exactly $d$ neighboring grid steps between those times. After $d$ unit moves, its net planar displacement $(\Delta x,\Delta y)$ must satisfy

$$
|\Delta x|+|\Delta y|\le d\le28.
$$

The lifted step is

$$
(\Delta x,\Delta y,d).
$$

All three entries are integers and all are bounded. Consequently, only finitely many such triples exist.

Notice what is *not* needed: we do not need to enumerate vectors connecting two “16×16 grids.” The unit-step property plus the bound $d\le28$ already does the job.

---

## Adjustment 4: why not use every Hilbert point?

It may be true that the lift of every Hilbert point contains collinear triples, but that is not the logical reason used by this proof.

The reason is narrower and more important:

> The pair law is proved only for pairs of indices with the same terminal state.

If we used every index, different pairs could have different states, so the theorem would not apply uniformly. The selector forces every retained index into one common terminal state. Then the pair law applies to every pair of retained points.

The selector therefore has two jobs:

1. keep the selected indices close enough to produce a finite step menu;
2. put every selected index into the same state so the anti-collinearity theorem applies globally.

---

## One refinement about collinearity

It is better not to think of “planar vectors proportional” and “heights proportional” as two unrelated conditions.

Take selected indices $a<b<c$. Let

$$
A=b-a,\qquad B=c-b
$$

be the two height gaps, and let

$$
X=H(b)-H(a),\qquad Y=H(c)-H(b)
$$

be the corresponding planar chord vectors.

The two three-dimensional chord vectors are

$$
(X,A)\qquad\text{and}\qquad(Y,B).
$$

If the three lifted points were collinear, those 3D chord vectors would share one proportionality factor. Their height coordinates force what that factor must be. After cross-multiplying, the planar consequence is

$$
BX=AY.
$$

In words:

> The height gaps dictate exactly how the two planar chords would have to scale.

The 2-adic pair law will show that this scaling equation is impossible.

---

## Updated from-memory summary

> Trace a discrete Hilbert path, select one same-state index per 16-index block using one of four offsets, then lift each selected point by using its index as height. The offsets give gaps from 4 to 28, so the resulting 3D steps come from a finite menu. A same-state 2-adic pair law then prevents three lifted points from being collinear.

---

## Checkpoint

1. If arbitrary offsets $0$ through $15$ were allowed, why would the gap range be 1-to-31?
2. With allowed offsets $r_a=13$ and $r_{a+1}=3$, what is the next gap?
3. Is a block here fundamentally a block of spatial squares or a block of Hilbert indices?
4. What are the selector’s two separate jobs?
5. In your own words, what does the equation $BX=AY$ say geometrically?
