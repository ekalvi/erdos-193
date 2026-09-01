# Gaussian-lattice proof skeleton

## 1. Binary nearest-neighbor walk

Let

$$
u_n=i^{s_2(n)},\qquad z_n=\sum_{r<n}\nu_r\in\mathbb Z[i].$$

Then

$$
u_{2n+\varepsilon}=i^\varepsilon\nu_n,\qquad z_{2n+\varepsilon}=(1+i)z_n+\varepsilon\nu_n.$$

If $m<n$ and $\nu_m=\nu_n$, every common parity halving preserves the equality of states and factors the chord by $1+i$. After $\nu_2(n-m)$ halvings the index gap is odd; the remaining chord is a sum of an odd number of Gaussian units and has odd squared norm. Therefore

$$\nu_2(|z_n-z_m|^2)=\nu_2(n-m).$$

## 2. Encode the state twice

Write $\nu_n=i^{\alpha_n}$ with $\alpha_n\in\{0,1,2,3\}$ and use cyclic square corners

$$c_0=0,\quad c_1=i,\quad c_2=-1+i,\quad c_3=-1.$$

Define

$$w_n=2z_n+c_{\alpha_n},\qquad h_n=4n+\alpha_n,
\qquad P_n=(\Re w_n,\Im w_n,h_n).$$

For every $m<n$,

$$\nu_2(|w_n-w_m|^2)=\nu_2(h_n-h_m).$$

- Equal states: use the Gaussian same-state law; both tags cancel and both valuations gain two.
- Odd state difference: one planar coordinate and the height gap are odd.
- State difference $\pm2$: both planar coordinates are odd and both sides have valuation one.

## 3. Exclude a line

For a hypothetical collinear triple $a<b<c$, put

$$A=h_b-h_a,\quad B=h_c-h_b,
\qquad X=w_b-w_a,\quad Y=w_c-w_b.$$

Strict height growth gives $A,B>0$, and collinearity gives

$$\frac XA=\frac YB=\frac{X+Y}{A+B}.$$

The all-pairs law forces

$$\nu_2(A)=\nu_2(B)=\nu_2(A+B),$$

impossible because two integers with the same two-adic order have a sum with strictly larger order.

## 4. Bound the menu

A successive step is

$$w_{n+1}-w_n=2i^{\alpha_n}+c_{\alpha_{n+1}}-c_{\alpha_n},
\qquad h_{n+1}-h_n=4+\alpha_{n+1}-\alpha_n.$$

The planar coordinates have absolute value at most two and the height increment lies from one through seven. The ordered pair $(\alpha_n,\alpha_{n+1})$ determines the step, giving a fixed sixteen-vector menu.

## 5. Proof boundary

The argument above is unconditional and infinite. `Hilbert193.erdos193_unconditional` kernel-checks it in Lean. The historical Hilbert construction remains a geometric discovery model and alternative witness, not a premise of this proof. Finite Python checks are implementation evidence only.
