# Erdős Problem 193 proof: notation and formula cheat sheet

Source of truth: `paper/erdos193.tex`, Sections 1–6. The proof ends before Section 7 (“Verification and evidence”).

## 1. Ambient conventions

| Notation | Meaning |
|---|---|
| $\mathbb N$ | Nonnegative integers $\{0,1,2,\ldots\}$ in this paper. |
| $\mathbb Z$, $\mathbb Z^2$, $\mathbb Z^3$ | Integers, planar integer lattice, and spatial integer lattice. |
| $\mathbb F_2$ | Field with two elements. Exponents reduced modulo $2$ encode parity. |
| $|x|$ | Absolute value. |
| $\|u\|_1$ | $\ell^1$ norm; for $u=(u_x,u_y)$, $\|u\|_1=|u_x|+|u_y|$. |
| $f\circ g$ | Function composition with the right-hand map acting first: $(f\circ g)(z)=f(g(z))$. |
| $\nu_2(k)$ | Two-adic valuation: the exponent of the largest power of $2$ dividing nonzero integer $k$. The convention is $\nu_2(0)=\infty$. |
| $q_j$ | Base-$4$ digit at place $j$; $j=0$ is the least significant digit. |
| $x_j,y_j$ | Coordinate bits emitted at binary place $j$. |
| $u_x,u_y$ | Coordinates of a planar vector $u$. |

An infinite $S$-walk is a sequence $(P_a)_{a\ge 0}\subseteq\mathbb Z^3$ satisfying

$$
P_{a+1}-P_a\in S \qquad (a\in\mathbb N),
$$

for one fixed finite step set $S\subseteq\mathbb Z^3$.

## 2. Hilbert decoder

### State transformations

The decoder acts on a bit pair $(x,y)\in\{0,1\}^2$ using

$$
\begin{aligned}
I(x,y)&=(x,y), & S(x,y)&=(y,x),\\
T(x,y)&=(1-y,1-x), & C(x,y)&=(1-x,1-y).
\end{aligned}
$$

Here $I$ is the identity, $S$ swaps the bits, $T$ swaps and complements them, and $C$ complements both. The state set is

$$
K=\{I,S,T,C\}\cong\mathbb F_2^2,
$$

with

$$
S^2=T^2=C^2=I,
\qquad S\circ T=T\circ S=C.
$$

Thus every $g\in K$ is an involution: $g^{-1}=g$.

During a decode, $g\in K$ is a **mutable local variable** for the current orientation state. It starts at

$$
g=I.
$$

After the last digit $q_0$ has been processed, define

$$
\sigma(w)=\text{the resulting value of }g.
$$

Thus $g$ denotes the changing intermediate state; $\sigma(w)$ denotes its final value. They are related, but they are not interchangeable during the scan.

### Digit data

The four child positions, in U-shaped traversal order, are

$$
c_0=(0,0),\qquad c_1=(0,1),\qquad c_2=(1,1),\qquad c_3=(1,0).
$$

The symbol $r_q$ denotes the transition map selected by digit $q$; it is not a numeric sequence. The lookup table is

$$
r_0=S,\qquad r_1=I,\qquad r_2=I,\qquad r_3=T.
$$

In

$$
g\longleftarrow g\circ r_q,
$$

“update” means **replace the current orientation map $g$ by the composed map $g\circ r_q$** after digit $q$ emits its coordinate bits. The subscripted map $r_q\in K$ is unrelated to the scalar integer $r$ used later in the collinearity proof.

For a length-$\ell$ base-$4$ word

$$
w=q_{\ell-1}\cdots q_1q_0,
$$

the decoder reads digits from most significant to least significant, begins in state $I$, and at digit $q_j$ performs

$$
(x_j,y_j)=g(c_{q_j}),
\qquad
g\longleftarrow g\circ r_{q_j}.
$$

Reading order and output place run oppositely: $q_{\ell-1}$ is read first, but the pair emitted by $q_j$ occupies binary place $j$.

The finite-order Hilbert point is

$$
H_\ell(w)=
\left(
\sum_{j=0}^{\ell-1}x_j2^j,
\sum_{j=0}^{\ell-1}y_j2^j
\right).
$$

The map $H_\ell$ is a bijection from length-$\ell$ base-$4$ words to
$\{0,\ldots,2^\ell-1\}^2$. Consecutive words represent planar lattice neighbors.

The finite-order induction also uses the convention that the order-$\ell$ route starts at $(0,0)$ and ends at $(2^\ell-1,0)$.

Writing $N=2^\ell$, bitwise action on an $N\times N$ child square is

$$
S(x,y)=(y,x),
\qquad
T(x,y)=(N-1-y,N-1-x).
$$

The four transformed order-$\ell$ copies have start–end pairs

$$
\begin{aligned}
(0,0)&\longrightarrow(0,N-1),\\
(0,N)&\longrightarrow(N-1,N),\\
(N,N)&\longrightarrow(2N-1,N),\\
(2N-1,N-1)&\longrightarrow(2N-1,0),
\end{aligned}
$$

and junction displacements $(0,1)$, $(1,0)$, and $(0,-1)$. A suffix decoded from state $g$ rather than $I$ has state $g\circ h$ whenever the $I$-started suffix has state $h$, and its emitted route is the bitwise $g$-transform of the $I$-started route.

### Padding, infinite path, and terminal state

Two leading zero digits do not change the point or terminal state:

$$
H_{\ell+2}(00w)=H_\ell(w),
\qquad
\sigma(00w)=\sigma(w).
$$

For $n\in\mathbb N$, use any sufficiently long, even-length, zero-padded base-$4$ representation of $n$:

- $H(n)\in\mathbb N^2$ is its finite-order Hilbert point;
- $\sigma(n)\in K$ is the state left after decoding it.

The same symbol $\sigma(w)$ denotes the terminal state of a finite word. Context distinguishes word input from integer input.

The infinite path $H:\mathbb N\to\mathbb N^2$ is injective and has unit steps:

$$
\|H(n+1)-H(n)\|_1=1.
$$

Only digits $0$ and $3$ change the state. If $N_0(w)$ and $N_3(w)$ count those digits, then

$$
\sigma(w)=S^{N_0(w)\bmod 2}T^{N_3(w)\bmod 2}.
$$

Thus $\sigma$ records exactly the parity pair $(N_0\bmod2,N_3\bmod2)$.

If digit $q$ leaves outgoing state $h$, its incoming state and emitted pair can be recovered backward:

$$
\text{incoming state}=h\circ r_q,
$$

$$
(h\circ r_q)(c_q)=h(r_q(c_q))=h(c_q),
$$

because $r_q(c_q)=c_q$.

## 3. Two-adic chord invariant

For a nonzero planar chord $u=(u_x,u_y)\in\mathbb Z^2\setminus\{0\}$, define

$$
p(u)=\min\{\nu_2(u_x),\nu_2(u_y)\},
$$

$$
\epsilon(u)=
\begin{cases}
1,&\nu_2(u_x)=\nu_2(u_y),\\
0,&\nu_2(u_x)\ne\nu_2(u_y),
\end{cases}
$$

and

$$
V(u)=2p(u)+\epsilon(u).
$$

Interpretation: $p(u)$ is the largest common binary scale of the two coordinates. The bit $\epsilon(u)$ says whether both normalized coordinates first become odd at that scale.

For every positive integer $k$,

$$
V(ku)=V(u)+2\nu_2(k).
$$

The factor $2$ appears because each binary scale has two possible $V$-values: one coordinate first appears ($2j$), or both do ($2j+1$).

### First-mismatch convention

For equal-length, even-padded words $q_{\ell-1}\cdots q_0$ and $q'_{\ell-1}\cdots q'_0$, define the first mismatch **from the low end** by

$$
j=\min\{k\ge0:q_k\ne q'_k\}.
$$

Digits $q_0,\ldots,q_{j-1}$ form the common low suffix. If the two words have equal terminal state, their Hilbert coordinates agree below binary place $j$, and at place $j$:

- exactly one coordinate bit differs if $q_j-q'_j$ is odd;
- both coordinate bits differ if $q_j-q'_j\equiv2\pmod4$.

In the pair-law proof, the local names are

$$
d=q_j,\qquad e=q'_j,
$$

and, for $m<n$,

$$
n-m=4^jM,
\qquad
M\equiv e-d\pmod4.
$$

A differing coordinate has the form

$$
\pm2^j+2^{j+1}L=2^j(\pm1+2L),
$$

where $L\in\mathbb Z$ and the parenthesized factor is odd.

### Pair law

For distinct indices with the same terminal state,

$$
\sigma(m)=\sigma(n)
\quad\Longrightarrow\quad
V(H(n)-H(m))=\nu_2(|n-m|).
$$

This is the proof’s central invariant.

## 4. Bounded-gap selector and lifted walk

For block index $a\ge0$, let $g=\sigma(a)$ and choose a two-digit base-$4$ suffix through the offset map $\rho:K\to\{1,3,5,13\}$:

| Prefix state $g$ | Chosen suffix | Decimal offset $\rho(g)$ | Full state chain |
|---|---:|---:|---|
| $I$ | $11_4$ | $5$ | $I\circ I\circ I=I$ |
| $S$ | $01_4$ | $1$ | $I\circ S\circ S=I$ |
| $T$ | $31_4$ | $13$ | $I\circ T\circ T=I$ |
| $C$ | $03_4$ | $3$ | $I\circ C\circ C=I$ |

Define the selected index

$$
n_a=16a+\rho(\sigma(a)).
$$

Multiplication by $16=4^2$ appends the chosen two base-$4$ digits. Since every $g\in K$ is its own inverse,

$$
\sigma(n_a)=I\circ g\circ g=I.
$$

The selected gaps satisfy

$$
n_{a+1}-n_a
=16+\rho(\sigma(a+1))-\rho(\sigma(a)),
$$

$$
4\le n_{a+1}-n_a\le28.
$$

Two lift notations are used:

$$
Q(n)=(H(n),n)
$$

for the generic lift of an index, and

$$
P_a=Q(n_a)=(H(n_a),n_a)\in\mathbb Z^3
$$

for the selected walk. Every $P_a$ has terminal state $I$ through its index $n_a$.

## 5. Collinearity contradiction

The same-state lift theorem says: if $E\subseteq\mathbb N$ and $\sigma$ is constant on $E$, then

$$
\{Q(n):n\in E\}
$$

contains no three collinear points.

For a hypothetical collinear triple with $a<b<c$ in $E$, define adjacent index gaps and planar chords by

$$
A=b-a,\qquad B=c-b,
$$

$$
X=H(b)-H(a),\qquad Y=H(c)-H(b).
$$

The corresponding spatial displacements are $(X,A)$ and $(Y,B)$. Because $A,B>0$, collinearity is equivalent to

$$
BX=AY.
$$

Factor the gaps as

$$
A=gr,\qquad B=gs,
$$

$$
g=\gcd(A,B),\qquad \gcd(r,s)=1.
$$

Cancelling $g$ gives $sX=rY$. Coordinatewise divisibility yields an integer vector $W\in\mathbb Z^2\setminus\{0\}$ with

$$
X=rW,\qquad Y=sW.
$$

Applying the pair law and scaling law to the adjacent pairs gives

$$
\nu_2(g)+\nu_2(r)
=V(X)=V(W)+2\nu_2(r),
$$

$$
\nu_2(g)+\nu_2(s)
=V(Y)=V(W)+2\nu_2(s).
$$

Hence

$$
\nu_2(r)=\nu_2(s)=0,
\qquad
V(W)=\nu_2(g),
$$

so coprime $r$ and $s$ are both odd.

For the endpoint pair,

$$
c-a=g(r+s),
\qquad
H(c)-H(a)=(r+s)W.
$$

Set

$$
t=\nu_2(r+s).
$$

The pair and scaling laws give

$$
\nu_2(g)+t
=V((r+s)W)
=V(W)+2t
=\nu_2(g)+2t.
$$

Therefore $t=0$, which says $r+s$ is odd. But $r$ and $s$ are both odd, so $r+s$ is even: contradiction.

## 6. Finite step menu

Write one successive spatial displacement as

$$
P_{a+1}-P_a=(d_x,d_y,d_z).
$$

Its height increment is

$$
d_z=n_{a+1}-n_a,
\qquad
4\le d_z\le28.
$$

Unit Hilbert steps and the triangle inequality give

$$
|d_x|+|d_y|
=\|H(n_{a+1})-H(n_a)\|_1
\le n_{a+1}-n_a=d_z.
$$

A fixed finite menu containing every realized step is therefore

$$
S=\{(d_x,d_y,d_z)\in\mathbb Z^3:
4\le d_z\le28,\ |d_x|+|d_y|\le d_z\}.
$$

This $S$ is a convenient finite superset, not the minimal realized menu.

## 7. Letter index

### Global or recurring symbols

| Symbol | Type | Role |
|---|---|---|
| $S$ | transformation, then set | Decoder swap $S(x,y)=(y,x)$ in Sections 2–4; finite spatial step set in the theorem and Section 5. See the collision warning below. |
| $P_a$ | $\mathbb Z^3$ | $a$th vertex of the selected infinite walk. |
| $H_\ell$ | finite words $\to\mathbb N^2$ | Finite-order Hilbert decoder. |
| $H$ | $\mathbb N\to\mathbb N^2$ | Nested infinite Hilbert path. |
| $\sigma$ | words or $\mathbb N\to K$ | Terminal value of the mutable decoder state $g$ after the last digit. |
| $K$ | four-element set/group | Decoder state space $\{I,S,T,C\}$. |
| $I,S,T,C$ | maps on $\{0,1\}^2$ | Four decoder transformations. |
| $c_q$ | $\{0,1\}^2$ | Child position associated with digit $q\in\{0,1,2,3\}$. |
| $r_q$ | $K$ | Digit-indexed transition map; after digit $q$, replace the current state $g$ by $g\circ r_q$. Not the scalar $r$ in the triple argument. |
| $w$ | base-$4$ word | Finite decoder input. |
| $\ell$ | nonnegative integer | Word length / finite Hilbert order. |
| $q_j,q'_j$ | base-$4$ digits | Digits of two compared words at place $j$. |
| $x_j,y_j$ | bits | Coordinate bits emitted at place $j$. |
| $N_0(w),N_3(w)$ | nonnegative integers | Counts of digits $0$ and $3$ in $w$. |
| $u=(u_x,u_y)$ | nonzero $\mathbb Z^2$ vector | Generic planar chord. |
| $p(u)$ | nonnegative integer | Common two-adic coordinate scale. |
| $\epsilon(u)$ | $\{0,1\}$ | Whether the coordinate valuations are equal. |
| $V(u)$ | nonnegative integer | Two-adic planar chord invariant. |
| $\rho$ | $K\to\{1,3,5,13\}$ | State-dependent selector offset. |
| $n_a$ | nonnegative integer | Selected Hilbert index in block $a$. |
| $Q(n)$ | $\mathbb Z^3$ | Generic lift $(H(n),n)$. |
| $E$ | subset of $\mathbb N$ | Arbitrary same-terminal-state index set. |
| $d_x,d_y,d_z$ | integers | Coordinates of one successive step of $P$. |

### Proof-local symbols

| Symbol | Scope | Meaning |
|---|---|---|
| $g,h$ | Decoder arguments | $g$ is the mutable current state, initialized at $I$, whose final value is $\sigma(w)$; $h$ is an outgoing or common state used in reverse decoding. |
| $d,e$ | First-mismatch lemma | Unequal digits $q_j,q'_j$. |
| $j$ | First-mismatch argument | Least digit place where two base-$4$ words differ. |
| $M$ | Pair-law proof | Integer remaining after $n-m=4^jM$. |
| $L$ | Pair-law proof | Integer collecting higher binary-place contributions. |
| $k$ | Scaling lemma | Positive integer scalar; in the mismatch definition, a dummy digit-place index. |
| $a$ | Selector sections | Block number indexing $n_a$ and $P_a$. |
| $a,b,c$ | Triple-free theorem | Three ordered indices in $E$; this reuses $a$ with a different local role. |
| $A,B$ | Triple-free theorem | Positive adjacent gaps $b-a$ and $c-b$. |
| $X,Y$ | Triple-free theorem | Adjacent planar chords. |
| $g$ | Triple-free theorem | $\gcd(A,B)$; this reuses $g$ with a different local role. |
| $r,s$ | Triple-free theorem | Coprime reduced gap factors: $A=gr$, $B=gs$. |
| $W$ | Triple-free theorem | Common nonzero primitive-direction multiple with $X=rW$, $Y=sW$. |
| $t$ | Triple-free theorem | $\nu_2(r+s)$. |

## 8. Collision and reading warnings

1. **$S$ is overloaded.** In the decoder, $S$ is the swap transformation. In the theorem and final section, $S\subseteq\mathbb Z^3$ is the finite step menu. Type and section determine the meaning.
2. **$g$ is local and overloaded.** In the decoder, $g\in K$ is the mutable current state: it starts at $I$, and its final value is $\sigma(w)$. In the collinearity proof, the unrelated integer $g$ means $\gcd(A,B)$.
3. **$r_q$ and $r$ are different objects.** The subscripted $r_q\in K$ is the transition map selected by base-$4$ digit $q$. The unsubscripted $r\in\mathbb N$ is the coprime reduced factor in $A=gr$.
4. **$a$ changes role.** It is the block/walk index in $n_a,P_a$, but one of three arbitrary ordered indices $a<b<c$ inside the same-state lift theorem.
5. **$\sigma$ is not a coordinate.** It is the accumulated terminal transformation left by decoding.
6. **Most-significant-first reading, least-significant place labels.** The decoder reads $q_{\ell-1},\ldots,q_0$, while $q_j$ emits at binary place $j$.
7. **“First mismatch” means from the low end.** It is the least $j$, not the first digit encountered by the forward decoder.
8. **$H(n)$ is planar; $Q(n)$ and $P_a$ are spatial.** The third coordinate is the Hilbert index itself.
9. **The menu is not the realized set.** The displayed finite $S$ contains all possible successive displacements allowed by the proved bounds; it need not be minimal.
