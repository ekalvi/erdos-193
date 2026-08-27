# Erdős Problem 193: proof skeleton

The construction gives an unconditional negative answer: there is an infinite finite-step walk in $\mathbb Z^3$ with no three collinear vertices.

1. **Build the nested Hilbert path and record its terminal state.** Decode an even-padded base-$4$ word $w=q_{\ell-1}\cdots q_0$. The symbol $g\in K$ is the mutable current decoder state, initialized as $g=I$; it is one of four maps on coordinate bits:
   $$
   \begin{aligned}
   I(x,y)&=(x,y),& S(x,y)&=(y,x),\\
   T(x,y)&=(1-y,1-x),& C(x,y)&=(1-x,1-y),
   \end{aligned}
   \qquad
   K=\{I,S,T,C\}.
   $$
   Digit $q\in\{0,1,2,3\}$ has a child corner $c_q$ and a transition map $r_q\in K$:
   $$
   \begin{array}{c|cccc}
   q&0&1&2&3\\ \hline
   c_q&(0,0)&(0,1)&(1,1)&(1,0)\\
   r_q&S&I&I&T
   \end{array}
   $$
   Here “update” means replacement of the current orientation map: when digit $q_j$ is read, emit
   $$
   (x_j,y_j)=g(c_{q_j})
   $$
   and then set $g\leftarrow g\circ r_{q_j}$. Thus $r_q$ is a digit-indexed map, unrelated to the integer $r$ used in Steps 5–7. Finally set
   $$
   H_\ell(w)=
   \left(
   \sum_{j=0}^{\ell-1}x_j2^j,
   \sum_{j=0}^{\ell-1}y_j2^j
   \right),
   $$
   After the last digit $q_0$, define $\sigma(w)$ to be the resulting value of $g$. Thus $g$ denotes the changing intermediate state, while $\sigma(w)$ denotes its terminal value. The four-copy induction shows that $H_\ell$ is bijective, consecutive inputs are lattice neighbors, and two leading zero digits change neither $H_\ell$ nor $\sigma$. Hence they define an injective infinite path
   $$
   H:\mathbb N\to\mathbb N^2,
   \qquad
   \|H(n+1)-H(n)\|_1=1,
   $$
   together with a terminal state $\sigma(n)\in K$.

2. **Define the planar two-adic invariant.** For $u=(u_x,u_y)\ne0$, put
   $$
   p(u)=\min\{\nu_2(u_x),\nu_2(u_y)\},
   $$
   $$
   \epsilon(u)=
   \begin{cases}
   1,&\nu_2(u_x)=\nu_2(u_y),\\
   0,&\nu_2(u_x)\ne\nu_2(u_y),
   \end{cases}
   \qquad
   V(u)=2p(u)+\epsilon(u).
   $$
   Multiplying both coordinates by a positive integer $k$ gives
   $$
   V(ku)=V(u)+2\nu_2(k).
   $$

3. **Prove the same-state pair law.** Let $m\ne n$ with $\sigma(m)=\sigma(n)$, and let $j$ be the least base-$4$ place where their even-padded words differ. Equal terminal states let us reverse their common lower-digit suffix to one common state immediately after place $j$. The corners $c_0,c_1,c_2,c_3$ form a cyclic Gray code, so at binary place $j$ exactly one coordinate differs when the two base-$4$ digits differ oddly, and both differ when their difference is $2\pmod4$. Therefore
   $$
   V(H(n)-H(m))=
   \begin{cases}
   2j,&\nu_2(|n-m|)=2j,\\
   2j+1,&\nu_2(|n-m|)=2j+1,
   \end{cases}
   $$
   and hence
   $$
   V(H(n)-H(m))=\nu_2(|n-m|).
   $$

4. **Select bounded-gap indices with one terminal state.** Use
   $$
   \rho(I)=5,\qquad \rho(S)=1,\qquad \rho(T)=13,\qquad \rho(C)=3,
   $$
   corresponding respectively to suffixes $11_4,01_4,31_4,03_4$, and define
   $$
   n_a=16a+\rho(\sigma(a)).
   $$
   Each suffix contributes a second copy of the prefix state, so every selected word ends in
   $$
   \sigma(n_a)=I.
   $$
   Since $\rho(K)=\{1,3,5,13\}$,
   $$
   4\le n_{a+1}-n_a\le28.
   $$

5. **Reduce a hypothetical collinear triple to one common planar vector.** On any set $E\subseteq\mathbb N$ where $\sigma$ is constant, lift by
   $$
   Q(n)=(H(n),n).
   $$
   Suppose $a<b<c$ in $E$ give three collinear lifts. Write
   $$
   A=b-a,\quad B=c-b,\quad
   X=H(b)-H(a),\quad Y=H(c)-H(b).
   $$
   Collinearity of $(X,A)$ and $(Y,B)$ gives $BX=AY$. If
   $$
   A=gr,\quad B=gs,\quad g=\gcd(A,B),\quad\gcd(r,s)=1,
   $$
   coordinatewise divisibility gives a nonzero $W\in\mathbb Z^2$ such that
   $$
   X=rW,\qquad Y=sW.
   $$

6. **The adjacent pairs force both reduced gaps to be odd.** Apply the pair law and scaling identity to $(a,b)$ and $(b,c)$:
   $$
   \nu_2(g)+\nu_2(r)=V(W)+2\nu_2(r),
   $$
   $$
   \nu_2(g)+\nu_2(s)=V(W)+2\nu_2(s).
   $$
   Thus $\nu_2(r)=\nu_2(s)$. Since $\gcd(r,s)=1$, both valuations are zero, so $r,s$ are odd and
   $$
   V(W)=\nu_2(g).
   $$

7. **The endpoint pair gives the contradiction.** Since
   $$
   c-a=g(r+s),
   \qquad
   H(c)-H(a)=(r+s)W,
   $$
   put $t=\nu_2(r+s)$. The pair law and scaling identity for $(a,c)$ give
   $$
   \nu_2(g)+t=V((r+s)W)=V(W)+2t=\nu_2(g)+2t.
   $$
   Hence $t=0$, so $r+s$ is odd. But Step 6 made both $r$ and $s$ odd, so their sum is even. Contradiction. Therefore every constant-$\sigma$ lift, in particular the selected lift, has no three collinear points.

8. **Form the required finite-step walk.** Define
   $$
   P_a=Q(n_a)=(H(n_a),n_a).
   $$
   It is infinite because its third coordinate strictly increases. For
   $$
   P_{a+1}-P_a=(d_x,d_y,d_z),
   $$
   the bounded selector gaps and unit Hilbert steps give
   $$
   4\le d_z\le28,
   \qquad
   |d_x|+|d_y|\le d_z.
   $$
   Thus every step lies in the fixed finite set
   $$
   S=\{(d_x,d_y,d_z)\in\mathbb Z^3:
   4\le d_z\le28,\ |d_x|+|d_y|\le d_z\}.
   $$
   Step 7 excludes collinear triples, so $(P_a)_{a\ge0}$ is the required counterexample.
