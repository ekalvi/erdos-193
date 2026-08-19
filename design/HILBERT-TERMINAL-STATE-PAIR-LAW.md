# A terminal-state pair law for the nested discrete Hilbert path

**Status:** unconditional affirmative construction, kernel-checked in Lean, with independent finite checks. The formal theorem constructs an infinite walk in $\mathbb Z^3$, proves every consecutive displacement belongs to one fixed finite set, and proves that no ordered triple is collinear. External mathematical review is pending.

## Executive verdict

The proposed same-terminal-state pair law exists.

For the exact infinite Hilbert indexing defined below, let $\sigma(n)$ be the terminal orientation state of the even-padded base-4 word for $n$. For a nonzero planar vector $u=(u_x,u_y)$, define

$$
p(u)=\min\{\nu_2(u_x),\nu_2(u_y)\},
$$

where $\nu_2(0)=\infty$, and

$$
\epsilon(u)=
\begin{cases}
1,&\nu_2(u_x)=\nu_2(u_y),\\
0,&\nu_2(u_x)\ne\nu_2(u_y).
\end{cases}
$$

Set

$$
V(u)=2p(u)+\epsilon(u).
$$

Then, for every $m<n$ with $\sigma(m)=\sigma(n)$,

$$
\boxed{V(H(n)-H(m))=\nu_2(n-m).}
$$

Moreover, for every positive integer $k$,

$$
\boxed{V(ku)=V(u)+2\nu_2(k).}
$$

These two identities imply that no three lifted points

$$
(H(n),n)
$$

whose indices share one terminal state can be collinear.

Two base-4 suffix digits suffice, and one digit does not suffice, to steer every possible terminal state to one fixed state. Consequently every interval of 16 aligned indices contains an index of terminal state $I$. An explicit representative choice has successive index gaps between 4 and 28. `Hilbert193/Continuity.lean` proves the missing all-index bridge: fixed-length Hilbert words are lattice-adjacent, the most-significant-first coordinate model equals the existing low-to-high transducer model, and successive selected planar points have Manhattan distance at most 28. Hence every lifted step lies in the fixed finite box $[-28,28]^2\times[4,28]$. The theorem `erdos193_unconditional` packages this with the no-three result, while the first 500,000 steps independently realize exactly 16 vectors.

The proof and the finite evidence are separated below.

---

## 1. Exact finite-state Hilbert transducer

### 1.1 Square-symmetry states

A state acts on a coordinate-bit pair $(x,y)\in\{0,1\}^2$. Use the following eight states:

| State | Action on $(x,y)$ |
|---|---|
| $I$ | $(x,y)$ |
| $X$ | $(1-x,y)$ |
| $Y$ | $(x,1-y)$ |
| $C$ | $(1-x,1-y)$ |
| $S$ | $(y,x)$ |
| $R$ | $(1-y,x)$ |
| $L$ | $(y,1-x)$ |
| $T$ | $(1-y,1-x)$ |

Composition is ordinary function composition. The four canonical Hilbert child positions, in traversal order, are

$$
c_0=(0,0),\qquad c_1=(0,1),\qquad c_2=(1,1),\qquad c_3=(1,0).
$$

The internal orientation maps of those children are

$$
r_0=S,\qquad r_1=I,\qquad r_2=I,\qquad r_3=T.
$$

If the incoming state is $g$ and the next base-4 digit is $q$, the transducer

1. emits the planar coordinate-bit pair $g(c_q)$; and
2. enters state $g\circ r_q$.

### 1.2 Complete transition/output table

Each entry is `emitted bits / next state`.

| Incoming state | digit 0 | digit 1 | digit 2 | digit 3 |
|---|---|---|---|---|
| $I$ | $00/S$ | $01/I$ | $11/I$ | $10/T$ |
| $X$ | $10/R$ | $11/X$ | $01/X$ | $00/L$ |
| $Y$ | $01/L$ | $00/Y$ | $10/Y$ | $11/R$ |
| $C$ | $11/T$ | $10/C$ | $00/C$ | $01/S$ |
| $S$ | $00/I$ | $10/S$ | $11/S$ | $01/C$ |
| $R$ | $10/X$ | $00/R$ | $01/R$ | $11/Y$ |
| $L$ | $01/Y$ | $11/L$ | $10/L$ | $00/X$ |
| $T$ | $11/C$ | $01/T$ | $00/T$ | $10/I$ |

### 1.3 Finite words and coordinates

For a length-$\ell$ base-4 word

$$
w=q_{\ell-1}\cdots q_1q_0,
$$

read digits from most significant to least significant, starting in state $I$. If the emitted pairs are

$$
(x_{\ell-1},y_{\ell-1}),\ldots,(x_0,y_0),
$$

define

$$
H_\ell(w)
=
\left(
\sum_{j=0}^{\ell-1}x_j2^j,
\sum_{j=0}^{\ell-1}y_j2^j
\right).
$$

This agrees exactly with the standard discrete Hilbert `d2xy` convention. At order 1 it traverses

$$
(0,0),(0,1),(1,1),(1,0),
$$

and the recursion is the standard four-child Hilbert recursion with the first and last child reflected as specified by $S$ and $T$.

### 1.4 Reversibility

The following properties are exact.

1. For a fixed digit $q$, the state transition
   
   $$
   g\mapsto g\circ r_q
   $$
   
   is a permutation of the eight states.
2. Knowing the outgoing state $h$ and digit $q$ uniquely recovers the incoming state:
   
   $$
   g=h\circ r_q,
   $$
   
   because every $r_q$ is an involution.
3. The 32 pairs `(emitted bits, outgoing state)` obtained from the 32 inputs `(incoming state, digit)` are all distinct. Thus the complete labeled transducer is reversible.
4. Each refinement map fixes its own child corner:
   
   $$
   r_q(c_q)=c_q.
   $$
   
   Therefore, if $h=g\circ r_q$ is the outgoing state, the emitted pair can be reconstructed backward as
   
   $$
   g(c_q)=h\circ r_q(c_q)=h(c_q).
   $$

The fourth identity is the key low-end property.

---

## 2. One genuinely infinite discrete Hilbert indexing

Finite Hilbert grids of successive orders alternate their orientation near the origin. To remove that ambiguity, retain the nested even orders.

For $n\ge0$, write $n$ in base 4 and pad it on the left with zeros to any even length $2r$ satisfying

$$
n<4^{2r}.
$$

Run the transducer from state $I$ and call the resulting point $H(n)$.

This is independent of the chosen sufficiently large even length. Indeed, prepending two zero digits gives

$$
I\xrightarrow{0,\ 00}S\xrightarrow{0,\ 00}I.
$$

The two added coordinate bits are both zero and the state returns to $I$. Hence

$$
H_{2r+2}(00w)=H_{2r}(w).
$$

Consequently:

- the order-$2r$ path is the initial segment of the order-$(2r+2)$ path;
- $H:\mathbb N\to\mathbb N^2$ is well defined;
- every consecutive pair $H(n),H(n+1)$ is a unit grid edge, since it lies in some common finite Hilbert order;
- $H$ is injective, since every finite-order Hilbert map is a bijection onto its square;
- the nested squares exhaust $\mathbb N^2$.

This is the frozen infinite convention used throughout the memo.

---

## 3. Terminal state and transition semigroup

Only digits 0 and 3 change the orientation state:

$$
r_0=S,\qquad r_3=T,
$$

while digits 1 and 2 act as $I$.

The two nontrivial generators are commuting involutions:

$$
S^2=T^2=I,
\qquad
ST=TS=C.
$$

Thus the reachable transition semigroup from $I$ is the Klein four-group

$$
K=\{I,S,T,C\}\cong(\mathbb Z/2\mathbb Z)^2.
$$

Its multiplication table is

| $\circ$ | $I$ | $S$ | $T$ | $C$ |
|---|---:|---:|---:|---:|
| $I$ | $I$ | $S$ | $T$ | $C$ |
| $S$ | $S$ | $I$ | $C$ | $T$ |
| $T$ | $T$ | $C$ | $I$ | $S$ |
| $C$ | $C$ | $T$ | $S$ | $I$ |

For a complete even-padded word $w$, let $N_0(w)$ and $N_3(w)$ denote its counts of digits 0 and 3. Its terminal state is

$$
\boxed{
\sigma(w)=S^{N_0(w)\bmod2}T^{N_3(w)\bmod2}.
}
$$

Adding two leading zeros does not change this statistic. It is therefore well defined for the infinite indexing.

The smallest quotient of the digit word determining the terminal state is the homomorphism

$$
\phi:\{0,1,2,3\}^*\longrightarrow(\mathbb Z/2\mathbb Z)^2
$$

with

$$
\phi(0)=(1,0),\quad
\phi(3)=(0,1),\quad
\phi(1)=\phi(2)=(0,0).
$$

It is minimal: the words $\varnothing,0,3,03$ realize the four distinct terminal states $I,S,T,C$.

---

## 4. Comparing a same-state pair from the low end

Let $m<n$. Pad their base-4 words to one common even length:

$$
m=(a_{\ell-1}\cdots a_0)_4,
\qquad
n=(b_{\ell-1}\cdots b_0)_4.
$$

Assume

$$
\sigma(m)=\sigma(n).
$$

Let $j$ be the first low-end position where the words differ:

$$
a_i=b_i\quad(0\le i<j),
\qquad
a_j\ne b_j.
$$

### 4.1 Backward cancellation through the common suffix

The suffix digits below position $j$ are equal. Their combined state transition is right composition by one group element $R$. If $h_m,h_n$ are the states immediately after processing position $j$, equality of terminal states gives

$$
h_m\circ R=h_n\circ R.
$$

Right cancellation in the symmetry group gives

$$
h_m=h_n=:h.
$$

Thus equality of terminal states really does permit exact reversal through the entire common low suffix.

The incoming states immediately before the mismatching digits need not agree. If

$$
d=a_j,\qquad e=b_j,
$$

then they are respectively

$$
h\circ r_d,
\qquad h\circ r_e.
$$

However, the backward-emission identity gives their emitted coordinate bits as

$$
h(c_d),\qquad h(c_e).
$$

So both mismatching digits are interpreted in one common outgoing orientation row $h$.

All lower emitted coordinate bits are identical because both computations begin the common suffix in the same state $h$.

### 4.2 Complete first-mismatch table

For each common outgoing state $h$, the first four columns list

$$
h(c_0),h(c_1),h(c_2),h(c_3).
$$

The remaining columns give the signed difference

$$
h(c_e)-h(c_d)
$$

for the six unordered pairs $d<e$. Reversing an ordered pair negates the listed vector, so the table covers all 12 unequal ordered digit pairs in every state.

| $h$ | $c_0$ | $c_1$ | $c_2$ | $c_3$ | 01 | 02 | 03 | 12 | 13 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|
| $I$ | 00 | 01 | 11 | 10 | $(0,1)$ | $(1,1)$ | $(1,0)$ | $(1,0)$ | $(1,-1)$ | $(0,-1)$ |
| $X$ | 10 | 11 | 01 | 00 | $(0,1)$ | $(-1,1)$ | $(-1,0)$ | $(-1,0)$ | $(-1,-1)$ | $(0,-1)$ |
| $Y$ | 01 | 00 | 10 | 11 | $(0,-1)$ | $(1,-1)$ | $(1,0)$ | $(1,0)$ | $(1,1)$ | $(0,1)$ |
| $C$ | 11 | 10 | 00 | 01 | $(0,-1)$ | $(-1,-1)$ | $(-1,0)$ | $(-1,0)$ | $(-1,1)$ | $(0,1)$ |
| $S$ | 00 | 10 | 11 | 01 | $(1,0)$ | $(1,1)$ | $(0,1)$ | $(0,1)$ | $(-1,1)$ | $(-1,0)$ |
| $R$ | 10 | 00 | 01 | 11 | $(-1,0)$ | $(-1,1)$ | $(0,1)$ | $(0,1)$ | $(1,1)$ | $(1,0)$ |
| $L$ | 01 | 11 | 10 | 00 | $(1,0)$ | $(1,-1)$ | $(0,-1)$ | $(0,-1)$ | $(-1,-1)$ | $(-1,0)$ |
| $T$ | 11 | 01 | 00 | 10 | $(-1,0)$ | $(-1,-1)$ | $(0,-1)$ | $(0,-1)$ | $(1,-1)$ | $(1,0)$ |

Two state-independent facts follow.

1. If $d-e$ is odd, then $c_d$ and $c_e$ differ in exactly one coordinate bit. Every square symmetry preserves that fact.
2. If $d-e\equiv2\pmod4$, then $c_d$ and $c_e$ differ in both coordinate bits.

These are the only possibilities for unequal base-4 digits.

---

## 5. The pairwise valuation law

### 5.1 Candidate forced by the mismatch table

For a nonzero planar integer vector $u=(u_x,u_y)$, put

$$
p(u)=\min\{\nu_2(u_x),\nu_2(u_y)\},
$$

with $\nu_2(0)=\infty$, and define the direction bit

$$
\epsilon(u)=
\begin{cases}
1,&\nu_2(u_x)=\nu_2(u_y),\\
0,&\nu_2(u_x)\ne\nu_2(u_y).
\end{cases}
$$

The minimal candidate indicated by the table is

$$
\boxed{V(u)=2p(u)+\epsilon(u).}
$$

The extra bit is necessary: $p(u)$ alone cannot distinguish a first differing base-4 digit difference of 1 or 3 from a difference of 2.

### 5.2 Scaling law

For every positive integer $k$,

$$
\nu_2(ku_x)=\nu_2(k)+\nu_2(u_x)
$$

and similarly for $u_y$. Hence

$$
p(ku)=p(u)+\nu_2(k),
$$

while equality or inequality of the two coordinate valuations is unchanged. Therefore

$$
\boxed{V(ku)=V(u)+2\nu_2(k).}
$$

### 5.3 All-length theorem

**Theorem 1 — same-terminal-state pair law.** If $m<n$ and

$$
\sigma(m)=\sigma(n),
$$

then

$$
\boxed{V(H(n)-H(m))=\nu_2(n-m).}
$$

**Proof.** Use the common even padding and let $j$ be the first differing base-4 position from the low end.

Because positions below $j$ agree,

$$
n-m=4^jK
$$

for an integer $K$ satisfying

$$
K\equiv b_j-a_j\pmod4.
$$

There are two cases.

#### Case 1: $b_j-a_j$ is odd

Then

$$
\nu_2(n-m)=2j.
$$

The mismatch table shows that exactly one emitted coordinate bit differs at position $j$. All lower coordinate bits agree exactly. Higher bits contribute multiples of $2^{j+1}$ and cannot change the parity after division by $2^j$.

Thus exactly one coordinate of

$$
H(n)-H(m)
$$

has valuation $j$, while the other has valuation strictly greater than $j$. Hence

$$
p=j,
\qquad
\epsilon=0,
$$

and

$$
V=2j=\nu_2(n-m).
$$

#### Case 2: $b_j-a_j\equiv2\pmod4$

Then

$$
\nu_2(n-m)=2j+1.
$$

The mismatch table shows that both emitted coordinate bits differ at position $j$. Again the lower bits agree and higher bits cannot alter the first differing bit. Therefore both coordinate differences have valuation exactly $j$:

$$
p=j,
\qquad
\epsilon=1.
$$

Consequently

$$
V=2j+1=\nu_2(n-m).
$$

These exhaust all unequal digit pairs. The treatment of lower digits and higher carries is exact: lower digits cancel because their transducer states and outputs agree, while higher digits are multiples of the next binary place. ∎

---

## 6. Exhaustive attempts to falsify the pair law

The companion verifier is

`design/hilbert_terminal_pair_law.py`.

It independently implements both the transducer and the standard finite-order `d2xy` algorithm.

The completed checks were:

1. The literal 8-state transition/output table above was regenerated exactly.
2. For every digit, the state transition was verified to be a permutation.
3. All 32 `(incoming state, digit)` combinations had distinct `(output, outgoing state)` pairs.
4. Transducer coordinates agreed with independent standard `d2xy` coordinates at every index through order 6.
5. Prefix nesting under two leading zeros was checked at every index through order 6.
6. The terminal parity formula was checked at every index below $4^6$.
7. Every same-terminal pair with
   
   $$
   0\le m<n<4096
   $$
   
   was tested: 2,096,128 pairs, no counterexample.
8. With deterministic seed 193, 100,000 same-terminal random pairs of 160-bit indices were tested. They required 401,982 candidate pairs; no counterexample was found.
9. The first 100,000 explicitly steered representatives all had terminal state $I$ and successive gaps from 4 through 28.
10. As a separate direct geometric check, the first 5,000 steered lifted vertices were compared by primitive three-dimensional chord direction. All 12,497,500 chords from an earlier to a later vertex had no repeated primitive direction from a common starting vertex; hence no triple was found.

The finite checks are evidence and implementation validation. The all-length result rests on Theorem 1, not extrapolation from those checks.

---

## 7. Collinearity consequence

**Theorem 2 — every terminal-state class is triple-free after the time lift.** Fix a terminal state $s\in\{I,S,T,C\}$. Then the points

$$
\{(H(n),n):\sigma(n)=s\}
$$

contain no three collinear points.

**Proof.** Suppose, for contradiction, that

$$
a<b<c,
\qquad
\sigma(a)=\sigma(b)=\sigma(c)=s,
$$

and that the three lifted points are collinear.

Set

$$
A=b-a,
\qquad
B=c-b,
$$

and define the planar chords

$$
X=H(b)-H(a),
\qquad
Y=H(c)-H(b).
$$

Equality of lifted chord slopes gives

$$
B X=A Y. \tag{1}
$$

Let

$$
g=\gcd(A,B),
\qquad
A=gr,
\qquad
B=gs,
\qquad
\gcd(r,s)=1.
$$

Equation (1) becomes

$$
sX=rY.
$$

Since $r$ and $s$ are coprime, $r$ divides both coordinates of $X$ and $s$ divides both coordinates of $Y$. Thus there is an integer planar vector $W$ such that

$$
X=rW,
\qquad
Y=sW. \tag{2}
$$

The vector $W$ is nonzero because $H$ is injective.

Put

$$
\gamma=\nu_2(g),
\qquad
\alpha=\nu_2(r),
\qquad
\beta=\nu_2(s).
$$

Apply Theorem 1 to the pair $(a,b)$ and use the scaling law:

$$
\begin{aligned}
\nu_2(A)
&=V(X)\\
\gamma+\alpha
&=V(rW)\\
&=V(W)+2\alpha.
\end{aligned}
$$

Therefore

$$
V(W)=\gamma-\alpha. \tag{3}
$$

Apply the same argument to $(b,c)$:

$$
\begin{aligned}
\nu_2(B)
&=V(Y)\\
\gamma+\beta
&=V(sW)\\
&=V(W)+2\beta,
\end{aligned}
$$

so

$$
V(W)=\gamma-\beta. \tag{4}
$$

Equations (3) and (4) imply

$$
\alpha=\beta.
$$

Because $r$ and $s$ are coprime, they cannot both be even. Equal $2$-adic valuations therefore force

$$
\alpha=\beta=0.
$$

Hence $r$ and $s$ are both odd, and (3) gives

$$
V(W)=\gamma. \tag{5}
$$

Now consider the endpoint pair $(a,c)$. Its index gap and planar chord are

$$
A+B=g(r+s)
$$

and, by (2),

$$
H(c)-H(a)=X+Y=(r+s)W.
$$

Let

$$
\delta=\nu_2(r+s).
$$

Theorem 1 and the scaling law give

$$
\begin{aligned}
\nu_2(A+B)
&=V((r+s)W),\\
\gamma+\delta
&=V(W)+2\delta,\\
\gamma+\delta
&=\gamma+2\delta
\end{aligned}
$$

using (5). Therefore

$$
\delta=0. \tag{6}
$$

But $r$ and $s$ are both odd, so $r+s$ is even and

$$
\delta\ge1,
$$

contradicting (6). No such triple exists. ∎

The contradiction uses all three pair laws: gaps $A$, $B$, and $A+B$.

---

## 8. Bounded gaps by a two-digit steering suffix

The terminal-state group is

$$
K=\{I,S,T,C\}.
$$

To steer an incoming state $g$ to $I$, append a suffix whose transition product equals $g^{-1}=g$.

### 8.1 Minimum suffix length

A one-digit suffix has possible transition products

$$
\{S,I,T\},
$$

coming from digits 0, 1 or 2, and 3. It cannot produce $C$. Therefore one digit cannot steer every incoming state to $I$.

Two digits suffice:

| Incoming state | Base-4 suffix | Suffix product | Final state |
|---|---:|---:|---:|
| $I$ | $11_4$ | $I$ | $I$ |
| $S$ | $01_4$ | $S$ | $I$ |
| $T$ | $31_4$ | $T$ | $I$ |
| $C$ | $03_4$ | $ST=C$ | $I$ |

Thus the minimum uniform steering-suffix length is exactly 2.

### 8.2 Explicit syndetic representatives

For each block index $a\ge0$, compute its even-padded terminal state $\sigma(a)$ and define

$$
\rho(I)=11_4=5,
\qquad
\rho(S)=01_4=1,
\qquad
\rho(T)=31_4=13,
\qquad
\rho(C)=03_4=3.
$$

Set

$$
s_a=16a+\rho(\sigma(a)).
$$

Appending the corresponding two-digit suffix gives

$$
\sigma(s_a)=I.
$$

There is one such representative in every aligned block

$$
[16a,16a+15].
$$

Because

$$
\rho(\sigma(a))\in\{1,3,5,13\},
$$

successive representative gaps satisfy

$$
\begin{aligned}
s_{a+1}-s_a
&=16+\rho(\sigma(a+1))-\rho(\sigma(a)),\\
4&\le s_{a+1}-s_a\le28.
\end{aligned}
$$

Therefore the full terminal class

$$
A_I=\{n:\sigma(n)=I\}
$$

is syndetic, with gaps no larger than 28, because it contains every representative $s_a$.

The same conclusion holds for every target terminal state after multiplying the correction table by that target state.

---

## 9. Consequence for the finite-step walk

Enumerate the state-$I$ indices increasingly:

$$
a_0<a_1<a_2<\cdots,
\qquad
\sigma(a_j)=I.
$$

Define lifted vertices

$$
Q_j=(H(a_j),a_j)\in\mathbb Z^3.
$$

By Theorem 2, no three $Q_j$ are collinear.

The index gaps satisfy

$$
1\le a_{j+1}-a_j\le28.
$$

The original Hilbert path takes planar unit steps, so

$$
\|H(a_{j+1})-H(a_j)\|_1
\le a_{j+1}-a_j
\le28.
$$

Consequently every walk step

$$
Q_{j+1}-Q_j
$$

belongs to the finite set

$$
\left\{
(dx,dy,dz)\in\mathbb Z^3:
1\le dz\le28,
\ |dx|+|dy|\le dz
\right\}.
$$

The $z$-coordinate is strictly increasing, so vertices do not repeat. Translating $Q_0$ to the origin gives an infinite lattice walk with a fixed finite step menu and no three collinear vertices.

Within the definitions used by Erdős Problem 193, this is an unconditional affirmative construction.

---

## 10. Final status: proof versus experiment

### Proved in this memo

1. The stated 8-state table realizes the standard discrete Hilbert recursion.
2. Even leading-zero padding produces a genuinely infinite nested Hilbert indexing.
3. The terminal state is exactly the pair of parities of the counts of digits 0 and 3.
4. Equal terminal states permit exact backward cancellation through a common low suffix.
5. The complete mismatch table forces the valuation
   
   $$
   V(u)=2\min(\nu_2(u_x),\nu_2(u_y))
   +\mathbf 1_{\nu_2(u_x)=\nu_2(u_y)}.
   $$
6. For same-terminal pairs,
   
   $$
   V(H(n)-H(m))=\nu_2(n-m).
   $$
7. The scaling law is
   
   $$
   V(ku)=V(u)+2\nu_2(k).
   $$
8. Every terminal-state class is triple-free after the time lift.
9. Two suffix digits are necessary and sufficient to steer every incoming terminal state to one fixed state.
10. A terminal-state class has uniformly bounded gaps, explicitly at most 28.
11. The corresponding lifted subsequence is an infinite finite-step walk in $\mathbb Z^3$ with no three collinear vertices.

### Experimental evidence

1. Exact agreement with standard finite Hilbert indexing through order 6.
2. 2,096,128 exhaustive same-terminal small pairs, with no failure.
3. 100,000 same-terminal random 160-bit pairs, with no failure.
4. 100,000 steered representatives satisfying the predicted state and gap bounds.
5. A direct no-three-collinear check on the first 5,000 steered vertices.

These computations validate the implementation and attempted falsification. They are not premises of the all-length proofs.

### Remaining review risk

The complete construction is kernel-checked, but has not yet undergone external mathematical peer review. The load-bearing points for human review are narrow and explicit:

1. the backward-emission identity $r_q(c_q)=c_q$;
2. cancellation through the common low suffix;
3. the distinction between one-bit and two-bit mismatch cases;
4. the factor 2 in the scaling law for $V$;
5. the use of all three gaps $A,B,A+B$ in Theorem 2;
6. compatibility of the two-digit steering suffix with even leading-zero padding;
7. the fixed-length Hilbert adjacency induction and the MSB/LSB coordinate equivalence in `Continuity.lean`.

No unbounded old-secant state, adaptive selector, supertile closure, or cross-child defect induction is used.
