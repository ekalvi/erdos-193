# Erdős 193 — When Hilbert Orientation Applies

**Previous:** [05B — How to Read the Hilbert Digit Notation](05B%20-%20How%20to%20Read%20the%20Hilbert%20Digit%20Notation.md)

**Return afterward to:** [the real-point decoding in Lesson 05B](05B%20-%20How%20to%20Read%20the%20Hilbert%20Digit%20Notation.md#decode-a-real-point-from-the-final-construction)

**Later use:** [05 — Why the Hilbert Pair Law Is True](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md)

## The short answer

At every base-4 digit, the decoder performs **two separate jobs**:

1. **Incoming orientation acts now.** It tells the decoder how to transform the selected child-square address into the emitted pair $(x_k,y_k)$.
2. **Outgoing orientation acts on the next row.** It becomes the incoming orientation when the decoder reads the next digit to the right.

Thus an outgoing orientation does **not** alter the pair emitted on its own row. It controls how the decoder interprets the smaller square entered on that row.

If a row processes position $k$, its outgoing orientation is passed to position $k-1$:

```text
position k                              position k−1

incoming orientation ─┐
                      ├─ emit (xₖ,yₖ)
input digit qₖ ───────┘
                      └─ outgoing orientation ──────> incoming orientation
```

At the leftmost digit, the incoming orientation is always the basic orientation $I$. After the rightmost digit, the outgoing orientation is the **terminal state**.

---

## First separate $k$ from $q_k$

These symbols perform different jobs:

- $k$ is a **position number**;
- $q_k$ is the **base-4 digit stored at that position**.

For example, if

$$
n=1100_4,
$$

then

$$
q_3=1,
\qquad q_2=1,
\qquad q_1=0,
\qquad q_0=0.
$$

The orientation rule does not change merely because the position is $k=3$ rather than $k=1$. The relevant input is the digit value $q_k$.

A digit 0 triggers the same relative orientation change wherever it appears. Likewise for digits 1, 2, and 3.

There is one qualification: the **name of the resulting outgoing state** depends on both the incoming state and the digit. The digit determines which relative rotation or reflection is added to the orientation already present.

---

## The two pieces of information attached to a digit

In the basic orientation, digit $q$ first identifies a child square:

| Digit $q$ | Basic child address $c_q$ | Location |
|---:|---:|---:|
| 0 | $(0,0)$ | lower left |
| 1 | $(0,1)$ | upper left |
| 2 | $(1,1)$ | upper right |
| 3 | $(1,0)$ | lower right |

That address answers:

> Which child square did we enter?

But the decoder also needs to know:

> How is the smaller U-shaped path oriented inside that child?

For this Hilbert convention, the child’s internal refinement is:

| Digit $q$ | Child address | Orientation of the U inside that child |
|---:|---:|---:|
| 0 | $(0,0)$ | $S$: swap x and y |
| 1 | $(0,1)$ | $I$: leave it unchanged |
| 2 | $(1,1)$ | $I$: leave it unchanged |
| 3 | $(1,0)$ | $T$: reflect across the other diagonal |

The transformations used here are

$$
I(x,y)=(x,y),
$$

$$
S(x,y)=(y,x),
$$

and

$$
T(x,y)=(1-y,1-x).
$$

The child address controls the bit pair emitted **at the current scale**. The child’s internal orientation controls how later digits are decoded **inside that child**.

That separation is the key idea.

---

## Why the internal orientation differs by digit

The four large child squares must connect into one continuous path. Their internal copies of the U cannot all point the same way.

At order two, examine each $2\times2$ child using coordinates relative to that child’s lower-left corner.

| First digit | Relative path inside its child | Internal orientation |
|---:|---:|---:|
| 0 | $(0,0)\to(1,0)\to(1,1)\to(0,1)$ | $S$ |
| 1 | $(0,0)\to(0,1)\to(1,1)\to(1,0)$ | $I$ |
| 2 | $(0,0)\to(0,1)\to(1,1)\to(1,0)$ | $I$ |
| 3 | $(1,1)\to(0,1)\to(0,0)\to(1,0)$ | $T$ |

Children 1 and 2 use the basic U unchanged. The first and last children are reoriented so that:

- the entire path starts at the required outer corner;
- the exit from each child touches the entrance to the next child;
- the entire path ends at the required outer corner.

Therefore the digit value $q_k$ determines the relative refinement:

$$
r_0=S,
\qquad r_1=I,
\qquad r_2=I,
\qquad r_3=T.
$$

This is not a numerical property of the digits 0, 1, 2, and 3. It is geometric bookkeeping for the four differently placed recursive copies of the Hilbert path.

---

## The exact rule for one row

Suppose the row reads digit $q_k$ with incoming orientation $g$.

### Job 1: emit the current coordinate bits

Take the basic child address $c_{q_k}$ and apply the **incoming** orientation:

$$
(x_k,y_k)=g(c_{q_k}).
$$

### Job 2: prepare to decode inside that child

Take the child’s relative refinement $r_{q_k}$ and combine it with the incoming orientation:

$$
\text{outgoing orientation}=g\circ r_{q_k}.
$$

Read $g\circ r_{q_k}$ as:

> First orient the little path as required inside this child, then view that little path through the orientation already applied to its parent.

The outgoing orientation is passed unchanged into the next row. It becomes that row’s incoming orientation.

In pseudocode:

```text
state = basic orientation I

for each base-4 digit qₖ, from left to right:
    child_address = basic address of qₖ
    (xₖ,yₖ) = state applied to child_address
    state = state combined with the internal orientation for qₖ
```

---

## Example 1: why both rows of $H(5)$ use the basic orientation

Write

$$
5=11_4.
$$

Start in state $I$.

| Position | Digit | Incoming | Emitted now | Relative refinement | Outgoing |
|---:|---:|---:|---:|---:|---:|
| $k=1$ | 1 | $I$ | $I(c_1)=I(0,1)=(0,1)$ | $r_1=I$ | $I$ |
| $k=0$ | 1 | $I$ | $I(c_1)=I(0,1)=(0,1)$ | $r_1=I$ | $I$ |

On the first row, digit 1 chooses the upper-left child and says that its inner U remains basic. Therefore the outgoing orientation is $I$.

That outgoing $I$ becomes the incoming orientation on the second row. The second digit is also 1, so the same lookup occurs again.

This is why both rows emit $(0,1)$:

$$
\text{same digit}+
\text{same incoming orientation}
=
\text{same emitted pair}.
$$

The two pairs occupy different binary positions, producing

$$
x_1x_0=00_2,
\qquad
y_1y_0=11_2,
$$

and hence

$$
H(5)=(0,3).
$$

---

## Example 2: exactly when the swap in $H(80)$ applies

Write

$$
80=1100_4.
$$

The orientation handoff is:

| Position | Digit | Incoming | Emitted now | Outgoing |
|---:|---:|---:|---:|---:|
| $k=3$ | 1 | $I$ | $(0,1)$ | $I$ |
| $k=2$ | 1 | $I$ | $(0,1)$ | $I$ |
| $k=1$ | 0 | $I$ | $(0,0)$ | $S$ |
| $k=0$ | 0 | $S$ | $S(0,0)=(0,0)$ | $I$ |

Focus on the last two rows.

At $k=1$, the incoming state is $I$, so digit 0 emits

$$
I(c_0)=I(0,0)=(0,0).
$$

Digit 0 also says that the U inside that selected child must be swapped. Therefore the row’s outgoing state becomes $S$.

That $S$ does not modify $(x_1,y_1)$ retroactively. It becomes the incoming state at $k=0$.

At $k=0$, the next digit 0 has basic child address $(0,0)$. Apply the incoming swap:

$$
S(0,0)=(0,0).
$$

The swap is active, but swapping two zeros produces the same visible pair. This is why $H(80)$ is not the best example for **seeing** the output change.

The second digit 0 adds another swap. Two swaps cancel:

$$
S\circ S=I.
$$

Therefore the terminal state is $I$.

---

## Example 3: an orientation that visibly changes an emitted pair

Use

$$
12=30_4.
$$

Start in state $I$.

### First row: digit 3 at position 1

The basic address of digit 3 is

$$
c_3=(1,0).
$$

The incoming orientation is $I$, so

$$
(x_1,y_1)=I(1,0)=(1,0).
$$

Digit 3 places the internal U in orientation $T$. Therefore the outgoing orientation is $T$.

### Second row: digit 0 at position 0

The outgoing $T$ from the previous row is now the incoming orientation.

Digit 0’s basic child address is

$$
c_0=(0,0).
$$

This time the decoder must apply $T$ before emitting:

$$
(x_0,y_0)
=T(0,0)
=(1-0,1-0)
=(1,1).
$$

Without the orientation, digit 0 would have emitted $(0,0)$. The incoming $T$ visibly changes it to $(1,1)$.

The coordinate bits are therefore

$$
x_1x_0=11_2=3,
\qquad
y_1y_0=01_2=1.
$$

Hence

$$
\boxed{H(12)=(3,1)}.
$$

This is the cleanest illustration of when incoming orientation applies: the transformation inherited from an earlier digit changes the interpretation of a later digit.

---

## What happens after the final digit?

The outgoing orientation after position $k=0$ has no more coordinate digit to transform. It is retained as the **terminal state** of the index.

Thus the terminal state does not change the coordinate already constructed. It records the net orientation left after the complete recursive descent.

The selector later chooses indices with a common terminal state. That common state is what lets the pair-law comparison align the two decoders at their first mismatching digit.

For now, remember only:

> Incoming orientation affects this row’s output. Outgoing orientation becomes next row’s input. The output after the last row is the terminal state.

> [!next] Continue with terminal states
> [05D — What the Hilbert Terminal State Remembers](05D%20-%20What%20the%20Hilbert%20Terminal%20State%20Remembers.md) explains the four possible final states, how to read them from a base-4 word, and why matching final states let the pair-law proof rewind a common low suffix.

---

## Tiny checkpoint

1. Which orientation transforms the emitted pair on the current row: incoming or outgoing?
2. If the outgoing orientation at position $k=2$ is $S$, what is the incoming orientation at position $k=1$?
3. Is the relative refinement chosen by the position number $k$, or by the digit value $q_k$?
4. In the $H(80)$ trace, why does the incoming $S$ at $k=0$ still emit $(0,0)$?
5. In the $H(12)$ trace, why does digit 0 emit $(1,1)$ rather than its basic pair $(0,0)$?
