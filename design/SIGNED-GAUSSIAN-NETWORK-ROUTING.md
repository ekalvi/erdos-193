# Signed Gaussian walks as network-routing and traffic-scheduling primitives

**Status:** exploratory adjacent-application note. The algebraic statements below are exact and include proofs or derivations. The routing interpretations are hypotheses, not performance claims. No transport or packet-routing benchmark has yet been run, and this note does not change the proof status of the Erdős 193 result.

## Executive verdict

The signed Gaussian **family**, rather than one displayed walk, has three structures that can matter to networks:

1. every member uses the same finite menu of 16 tagged transitions;
2. finite sign prefixes form a nested binary route-code tree; and
3. on a synchronous dyadic frame, the family is exactly a column-phased Walsh--Hadamard codebook.

The best immediate application is therefore **orthogonal probing, telemetry, or deterministic multiscale scheduling**, not ordinary origin-to-destination pathfinding. A concrete severe-fault telemetry design and decoder prototype are developed in [`WALSH-CODED-ALTERNATE-MARKING.md`](WALSH-CODED-ALTERNATE-MARKING.md).

The phrase “no three collinear” does have an exact network interpretation, but only after network edges are given additive labels. It then means:

> two adjacent route or service intervals never have exactly the same average labeled resource signature.

That is an anti-repetition or anti-resonance property. It is not, by itself, a congestion, latency, fairness, reachability, or edge-disjointness guarantee.

There are also decisive negative findings for direct routing:

- two distinct synchronized sign rules choose the same one of four ports in exactly half the slots, compared with one quarter in an independent uniform four-way model;
- all rules are confined to the same opposite pair of ports at each synchronized slot;
- after `N = 2^p` raw planar steps, every rule is only Euclidean distance `sqrt(N)` from its start and can reach only four possible endpoints; and
- the planar source walks can revisit nodes. The monotone tagged lift prevents repeated *lifted* vertices, not repeated physical planar locations.

So the family should not be marketed as a new routing algorithm. It is a promising deterministic code/schedule from which a routing mechanism might be built.

---

## 1. The full family, not only the original rule

Let

$$
\varepsilon=(\varepsilon_0,\varepsilon_1,\ldots),
\qquad \varepsilon_j\in\{+1,-1\},
$$

be any infinite sign stream. If $b_j(n)$ is bit $j$ of $n$, define

$$
\alpha_\varepsilon(n)
 = \sum_{j\geq 0}\varepsilon_j b_j(n)\pmod 4,
\qquad
u_\varepsilon(n)=i^{\alpha_\varepsilon(n)},
\qquad
z_\varepsilon(n)=\sum_{r<n}u_\varepsilon(r).
$$

Only finitely many terms enter $\alpha_\varepsilon(n)$ for each $n$. The paper's walk is the constant rule $\varepsilon_j=+1$.

### 1.1 Shifted binary recursion

Write $T\varepsilon=(\varepsilon_1,\varepsilon_2,\ldots)$. Directly from binary expansion,

$$
\begin{aligned}
u_\varepsilon(2n)&=u_{T\varepsilon}(n),\\
u_\varepsilon(2n+1)&=i^{\varepsilon_0}u_{T\varepsilon}(n),\\
z_\varepsilon(2n)&=(1+i^{\varepsilon_0})z_{T\varepsilon}(n),\\
z_\varepsilon(2n+1)&=(1+i^{\varepsilon_0})z_{T\varepsilon}(n)+u_{T\varepsilon}(n).
\end{aligned}
$$

Both possible factors, $1+i$ and $1-i$, have squared norm 2.

If $m<n$, $u_\varepsilon(m)=u_\varepsilon(n)$, and $n-m$ is even, then $m,n$ have the same parity. The endpoint unit terms cancel in the odd--odd case, so

$$
z_\varepsilon(n)-z_\varepsilon(m)
  =(1+i^{\varepsilon_0})
    \bigl(z_{T\varepsilon}(n')-z_{T\varepsilon}(m')\bigr),
$$

where $m',n'$ are obtained by halving. Repeating this for $\nu_2(n-m)$ levels gives

$$
\boxed{
\nu_2\!\left(\left|z_\varepsilon(n)-z_\varepsilon(m)\right|^2\right)
 =\nu_2(n-m).
}
$$

At the final odd gap, the chord is a sum of an odd number of Gaussian units. Its real and imaginary coordinates have odd sum, so its squared norm is odd. This is the same proof as in the paper, except that the sign stream shifts after each halving.

The existing state tags therefore extend the identity to every pair. With

$$
w_\varepsilon(n)=2z_\varepsilon(n)+c_{\alpha_\varepsilon(n)},
\qquad
h_\varepsilon(n)=4n+\alpha_\varepsilon(n),
$$

one obtains

$$
\boxed{
\nu_2\!\left(\left|w_\varepsilon(n)-w_\varepsilon(m)\right|^2\right)
 =\nu_2\!\left(h_\varepsilon(n)-h_\varepsilon(m)\right)
}
\qquad(m<n).
$$

The paper's collinearity contradiction then applies verbatim.

**Consequence.** The extension gives a solution for every sign stream, not merely every finite periodic sign word. At $n=2^j$, the state is $1$ when $\varepsilon_j=+1$ and $3$ when $\varepsilon_j=-1$, so the sign stream can be recovered from its walk. Hence there are continuum-many distinct walks.

This family extension is an elementary derivation in this note and has finite support in `signed_gaussian_fractals.py`; unlike the original constant-sign theorem, it has not yet been added to the repository's Lean proof.

### 1.2 One universal transition network

For current state $j$ and next state $k$, a tagged step is

$$
s_{jk}
 =\left(2i^j+c_k-c_j,\;4+k-j\right),
\qquad j,k\in\{0,1,2,3\}.
$$

Thus all family members are directed paths from the origin in the same Cayley supergraph

$$
\operatorname{Cay}(\mathbb Z^3,S),
\qquad S=\{s_{jk}:0\leq j,k<4\}.
$$

A more faithful transition network keeps only an edge $x\to x+s_{jk}$ when the height of $x$ is congruent to $j$ modulo 4. The edge then lands in state $k$. Every edge increases height, and the network has 16 link types (four available from each state). This is already a legitimate time-expanded network of nodes. It is not yet a routing scheme for an arbitrary physical graph.

### 1.3 Causal, nested choices

The actions before time $2^p$ depend only on
$\varepsilon_0,\ldots,\varepsilon_{p-1}$. Two rules sharing those signs have identical first $2^p$ actions. If they first differ at $p$, they choose opposite actions at time $2^p$.

Consequently the family is the boundary of a binary tree of compatible finite schedules. A controller may choose $\varepsilon_p$ when time $2^p$ is reached, using all observations so far, without invalidating the all-pairs theorem for the eventual realized sign stream. The price is a very slow control rate: one new binary choice per doubling of the horizon.

---

## 2. What “collinear” can mean for a network

### 2.1 It is not preserved by a plain graph isomorphism

A graph isomorphism preserves adjacency, degree, paths, and cycles. It does **not** preserve Euclidean lines because an abstract graph has no affine combinations or scalar multiplication.

There are three different notions that should not be conflated.

1. **Affine embedding.** An injective affine map of lattice coordinates preserves literal collinearity. This applies to geometric lattice or Cayley networks, but not to arbitrary routers and roads.
2. **Graph-geodesic collinearity.** Graph theory calls vertices $a,b,c$ collinear when one lies on a shortest path between the other two; sets avoiding this are called general-position sets. This is a natural graph-metric analogue, but a poor routing target. In an unweighted triangle-free network, every non-backtracking two-edge walk $a-b-c$ already has $d(a,c)=d(a,b)+d(b,c)=2$.
3. **Additive resource collinearity.** Label edges by additive resource vectors and append a positive clock or cost. This is the useful interpretation here.

The third notion gives an isomorphism of **labeled additive path structures**, not an isomorphism of bare graphs.

### 2.2 Prefix sums turn collinearity into equal average traffic signatures

Let a network action $e$ have

- an additive signature $\ell(e)\in\mathbb Z^d$, such as signed link use, queue service, or a linear sketch of an edge-incidence vector; and
- a positive cost $\tau(e)\in\mathbb Z_{>0}$, such as slots, latency units, or service quanta.

For a path $e_0,e_1,\ldots$, form prefix nodes

$$
R_n=\sum_{r<n}\ell(e_r),
\qquad
T_n=\sum_{r<n}\tau(e_r),
\qquad
Q_n=(R_n,T_n).
$$

For $a<b<c$, put

$$
X=R_b-R_a,\quad A=T_b-T_a,
\qquad
Y=R_c-R_b,\quad B=T_c-T_b.
$$

Because $A,B>0$,

$$
\boxed{
Q_a,Q_b,Q_c\text{ are collinear}
\iff
\frac{X}{A}=\frac{Y}{B}.
}
$$

The right side says that the adjacent intervals have exactly the same average resource signature per unit cost. Equivalently, all $2\times2$ minors of the two augmented interval vectors vanish.

For the signed Gaussian lift, take $R_n=w_\varepsilon(n)$ and $T_n=h_\varepsilon(n)$. The no-three theorem is exactly a guarantee that no two adjacent intervals repeat this normalized signature.

The signed coordinates are not an algebraic obstacle to nonnegative accounting. For a tagged transition $(\Delta w,\Delta h)$, choose an integer $K$ large enough that

$$
\rho=(K\Delta h+\Re\Delta w,\;K\Delta h+\Im\Delta w)
$$

is coordinatewise nonnegative for all 16 transitions. An interval then uses

$$
\frac{\sum\rho}{\sum\Delta h}
  =K(1,1)+\frac{\Delta w}{\Delta h}.
$$

Two intervals have the same average $\rho$ exactly when their Gaussian rates agree. This realizes the ternary relation with nonnegative counters, although the counters are engineered signatures rather than a congestion model.

This equivalence explains the transferable mechanism:

- path concatenation becomes vector addition;
- proportional traffic profiles become collinearity; and
- the 2-adic fingerprint makes proportionality impossible across the two adjacent intervals and their union.

It also marks the boundary. Congestion is an inequality such as “load exceeds capacity,” not an exact proportionality relation. The collinearity proof is naturally good at excluding exact algebraic degeneracies, not at optimizing inequalities.

### 2.3 Why the 2-adic argument works

Suppose adjacent intervals had the same rate. Then their planar signatures and durations would scale together. Squared norm is homogeneous of degree two:

$$
|qX|^2=q^2|X|^2,
$$

whereas the pair fingerprint makes its valuation track duration with degree one:

$$
\nu_2(|X|^2)=\nu_2(A).
$$

That degree mismatch forces

$$
\nu_2(A)=\nu_2(B)=\nu_2(A+B),
$$

which is impossible when the first two valuations agree: after removing their common power of two, odd plus odd is even.

This suggests a general design principle for networks:

> encode a forbidden proportional-resource event by a homogeneous polynomial, then arrange for a non-Archimedean fingerprint whose scaling degree disagrees with the polynomial's degree.

No such encoding is presently known for ordinary capacity overload, shortest-path routing, or queue stability.

### 2.4 Exact anti-repetition is not robust separation

The result excludes equality, but normalized interval signatures can still be very close. Since

$$
BX-AY\in\mathbb Z^2\setminus\{0\},
$$

one obtains only a scale-dependent separation of order at least $1/(AB)$ between the two rates. That tends to zero for long intervals. This can matter for exact digital slot resonance, but it is much less compelling for noisy road traffic unless a quantitative separation theorem is added.

---

## 3. The hidden Walsh--Hadamard codebook

For a length-$p$ sign word, write

$$
r_j=\frac{1-\varepsilon_j}{2}\in\{0,1\}.
$$

Then

$$
\begin{aligned}
\alpha_\varepsilon(n)
&=s_2(n)-2\sum_{j<p}r_jb_j(n)\pmod4,\\
u_\varepsilon(n)
&=i^{s_2(n)}(-1)^{r\cdot b(n)}.
\end{aligned}
$$

On the frame $0\leq n<2^p$, the factor $(-1)^{r\cdot b(n)}$ is a Walsh character. Therefore

$$
\boxed{
\sum_{n=0}^{2^p-1}
 u_r(n)\overline{u_s(n)}
 =2^p\,\mathbf 1_{r=s}.
}
$$

The matrix of all family symbols is a Walsh--Hadamard matrix with each column multiplied by the same Gaussian phase $i^{s_2(n)}$. Column phasing does not change row orthogonality.

For distinct rules $r\ne s$, the ratio is the nontrivial character

$$
\frac{u_r(n)}{u_s(n)}=(-1)^{(r\oplus s)\cdot b(n)}.
$$

It follows that, over a complete synchronous frame:

- the rules choose the **same** direction in exactly half the slots;
- they choose **opposite** directions in exactly half the slots; and
- they are never perpendicular.

This is excellent signed orthogonality and mediocre physical four-port diversity. Signed cancellation in a linear measurement is not the same thing as nonnegative capacity sharing.

### 3.1 Dyadic balance of each rule

The displacement over one complete frame factors as

$$
D_p=z_\varepsilon(2^p)
   =\prod_{j=0}^{p-1}(1+i^{\varepsilon_j}),
\qquad
|D_p|=2^{p/2}.
$$

If $C_q$ is the number of slots using direction $i^q$, then

$$
\begin{aligned}
C_0&=2^{p-2}+\tfrac12\Re D_p,&
C_2&=2^{p-2}-\tfrac12\Re D_p,\\
C_1&=2^{p-2}+\tfrac12\Im D_p,&
C_3&=2^{p-2}-\tfrac12\Im D_p.
\end{aligned}
$$

Thus each port differs from one quarter of the frame by at most
$2^{p/2-1}$. The relative imbalance decays like $2^{-p/2}$.

The same self-similarity gives an $O(\sqrt L)$ port discrepancy on arbitrary intervals of length $L$: every aligned dyadic block of length $2^k$ has net displacement of magnitude $2^{k/2}$, and an arbitrary interval decomposes into at most two blocks of each dyadic size. In addition, state parity is the ordinary Thue--Morse bit parity, whose sum over any interval is bounded by two; this controls the total assigned to each opposite port pair. Together these facts bound each individual port count by $L/4+O(\sqrt L)$. This is deterministic random-walk-scale balance, not the constant discrepancy obtainable from round-robin service.

### 3.2 The synchronized-family bottleneck

For every rule,

$$
\alpha_\varepsilon(n)\equiv s_2(n)\pmod2.
$$

So at a fixed synchronized slot all rules use one common opposite pair:

- east/west when $s_2(n)$ is even;
- north/south when $s_2(n)$ is odd.

This global synchronization is inherited from the exact 2-adic mechanism. A four-way router using the raw rules would leave half its next hops idle at almost every slot.

A trivial symmetry extension helps aggregate balance: the four rotations
$u,iu,-u,-iu$ place one flow on each port in every slot. But round robin can already do that. A network application must show some additional value from multiscale structure, adaptation, or code orthogonality.

### 3.3 Dyadic endpoint obstruction

Changing a sign changes the argument of $D_p$ by a multiple of $\pi/2$. At a fixed depth $p$, all $2^p$ rules therefore end at only four planar points, each at distance $2^{p/2}$ from the origin.

A raw route takes $N=2^p$ unit hops to achieve Euclidean displacement $\sqrt N$, so its stretch is exactly $\sqrt N$. The many visually different curves do **not** provide many destinations. This rules out using the source family directly as a shortest-path codebook.

---

## 4. Exact period-eight audit

Run:

```bash
python3 design/signed_gaussian_network_audit.py --period 8
```

The script is intentionally bounded to periods at most eight and uses one short process. It checks all 256 rule schedules and all 255 nontrivial Walsh characters with integer arithmetic; the character calculation establishes the stated relation for all 32,640 distinct rule pairs without enumerating them separately.

| Quantity | Exact period-eight result |
|---|---:|
| rules / frame slots | 256 / 256 |
| same-port slots for every distinct pair | 128 |
| opposite-port slots for every distinct pair | 128 |
| perpendicular-port slots for every distinct pair | 0 |
| possible per-rule port counts | permutations by quarter-turn of `(72,64,56,64)` |
| load at slot 0 when all rules are synchronized | `(256,0,0,0)` |
| load in the other even-parity slots | `(128,0,128,0)` |
| load in odd-parity slots | `(0,128,0,128)` |
| source endpoint distance after 256 hops | 16 |
| source-route Euclidean stretch | 16 |
| distinct source planar vertices among 257 visits | 81 through 214 |

The final row is computational rather than needed by the formulas. It shows that every period-eight source route revisits a planar node. The tagged three-dimensional lift remains vertex-distinct because its height is strictly increasing.

---

## 5. Candidate applications

### 5.1 Synchronous network probing and telemetry — strongest candidate

Suppose $2^p$ probe streams contribute linearly to a synchronized measurement:

$$
y(n)=\sum_r a_r u_r(n)+\eta(n).
$$

Orthogonality gives

$$
a_r=2^{-p}\sum_n y(n)\overline{u_r(n)}
$$

in the noiseless case. After removing the common column phase $i^{s_2(n)}$, all streams can be decoded by a fast Walsh--Hadamard transform.

Possible uses include:

- concurrent path-health probes;
- link or queue tomography with coded probe amplitudes;
- identifying which route introduced a periodic disturbance; and
- nested code allocation where doubling the frame exposes one more rule bit.

This connection is real but not new coding theory: Walsh functions have long been used for synchronous spread-spectrum communication. The potentially distinctive part is the compatibility with the cumulative Gaussian geometry and the all-interval anti-rate-repetition lift.

**Requirements:** synchronized frames, a sufficiently linear observable, and a way to encode signs or phases. Ordinary packet counts are nonnegative and queueing is nonlinear; one may need differential probes, packet markings, or paired measurements. Walsh orthogonality also generally degrades under timing offsets, so asynchronous cross-correlation is a required next test.

### 5.2 Deterministic multipath scheduling — plausible only with modifications

Map the four symbols to four equal-cost next hops. One flow then has $O(\sqrt L)$ discrepancy over intervals and a compact deterministic rule. Sign bits can be chosen causally at dyadic boundaries, and different rules supply a large schedule codebook.

Useful variants to test are:

- four-rotation bundles for exact aggregate balance;
- assigning opposite symbols to genuinely edge-disjoint complementary paths;
- random or optimized start phases to break the common parity synchronization;
- restarting the construction in bounded epochs so new sign choices arrive faster; and
- choosing future signs from observed queue imbalance.

The unmodified family is not competitive with round robin for equal capacities and is not comparable to topology-aware oblivious routing. It has no theorem for queue stability, packet ordering, failures, or worst-case edge congestion.

### 5.3 Hierarchical multicast or route-template aggregation

A common sign prefix gives an exactly common action prefix, with the next sign causing a controlled opposite branch. This can encode a binary hierarchy:

- related destinations share a route template;
- multicast traffic shares a trunk before branching; or
- route policies inherit a common coarse schedule and differ at finer scales.

This is an isomorphism between the **sign-prefix tree and the action-prefix tree**. It is not automatically an embedding as a physical tree, because distinct geometric traces may meet again and the source walk may revisit nodes.

### 5.4 Traffic-signal phase perturbation — speculative

The four states can represent four movement phases, and the 16 state-pair transitions can represent phase changes with transition-dependent virtual durations $4+k-j\in\{1,\ldots,7\}$. The no-collinearity theorem would then say that adjacent epochs never have exactly equal normalized signed service profiles.

This might be useful as deterministic multiscale dither to prevent exact locking between periodic arrival platoons and fixed signal cycles. It is not yet a traffic-control result:

- vehicles and service rates are nonnegative;
- minimum greens, amber/all-red clearances, and incompatible movements constrain transitions;
- green waves deliberately create synchronization;
- demand-adaptive and max-pressure controllers use live queues; and
- exact non-repetition without a robust separation margin may have no macroscopic effect.

A road application should therefore use the family only as an offset or perturbation layer on top of a safe controller, never as the controller itself.

### 5.5 Streaming coding vectors — algebraically adjacent

No three tagged points are affinely dependent. Equivalently, their homogeneous vectors $(1,P_n)$ are linearly independent in triples over $\mathbb Q$. This is closer in algebraic shape to network coding than congestion routing and could supply a bounded-update stream of 3-wise innovative coefficient vectors.

Reduction modulo a finite field can create collisions, and “any three independent” is weaker than the rank requirements of a general network code. This deserves a separate finite-field investigation before any claim.

### 5.6 Mobile-anchor sensor localization — a literal collinearity use

Mobile-anchor-assisted wireless sensor localization is a real path-planning domain in which collinear beacon positions are explicitly treated as a failure mode. A GPS-equipped robot or UAV follows a route and broadcasts its position; an unknown sensor waits until it has heard enough geometrically independent beacon positions. Existing work uses Hilbert, triangle, Z-, H-, M-, and nested-hexagon routes specifically to supply three non-collinear broadcasts.

A finite prefix of the lifted family gives a robot a 16-motion-primitive trajectory for which every three physical 3D beacon positions are non-collinear. For a localization or calibration method whose relevant rank condition is exactly non-collinearity in physical 3-space, this separates that condition from coverage: once a receiver hears any three positions, exact collinearity cannot be the failure.

It is not plug-and-play:

- common 2D trilateration expects three non-collinear beacon positions in the sensor's plane, while projecting the 3D lift can create collinear triples;
- a generic projection can preserve non-collinearity for any fixed finite prefix, but arbitrarily small tilt merely turns exact degeneracies into numerically useless, nearly collinear triples;
- unconstrained 3D range localization generally needs four non-coplanar anchors, which the theorem does not supply (short family prefixes contain many coplanar quadruples);
- the height coordinate is monotone, so a physical 3D mission needs finite-prefix scaling and an altitude budget; and
- exact non-collinearity does not by itself ensure good geometric dilution of precision.

There is nevertheless a measurable family-selection effect. Run

```bash
python3 design/mobile_anchor_geometry_audit.py
```

For all 256 period-eight rules and their 256-point native isotropic 3D prefixes, the audit examines every beacon triangle with pairwise diameter at most 20 lattice units. Rule 42 (`++-+-+-+`) maximizes the worst local interior angle at about $5.184^\circ$; the constant-positive rule and the family median are about $0.706^\circ$, and the worst rule is about $0.490^\circ$. Collinearity and ranking are checked with exact integer arithmetic; only degree rendering uses floating point. These are finite native-lattice data, not receiver coverage or localization-error results, and anisotropic physical scaling changes them.

The credible experiment is a finite UAV/mobile-anchor mission: search family rules and invertible anisotropic scalings for coverage, path length, minimum visible-triangle angle, and localization error, then compare with the established Hilbert and nested-hexagon baselines. This is the clearest application of the actual no-collinearity conclusion, but it needs more geometric engineering than the coded-telemetry application.

A representative application source is D. Yildiz and S. Karagol, *Path Planning for Mobile-Anchor Based Wireless Sensor Networks Localization: Obstacle-Presence Schemes*, Sensors 21 (2021), [doi:10.3390/s21113697](https://doi.org/10.3390/s21113697).

---

## 6. Proposed falsifiable experiments

### 6.1 Packet network

Use a four-spine Clos or a graph with four equal-cost paths. Compare:

1. per-flow ECMP hashing;
2. packet round robin or deficit round robin;
3. random per-packet routing;
4. rotor-router/quasirandom diffusion;
5. raw signed Gaussian rules;
6. four-rotation bundles;
7. phased or adaptively extended signed rules; and
8. signed rules used only as probe codes, not forwarding decisions.

Test synchronized and asynchronous flow starts, periodic and bursty arrivals, unequal capacities, and one-link failures. Record maximum edge congestion, queue discrepancy, packet reordering, mean and tail latency, path stretch, control-state size, and recovery time.

**Kill criterion:** if the family does not beat the simple baselines on either a proved discrepancy measure or a reproducible latency/congestion regime, retain only the Walsh probing interpretation.

### 6.2 Road traffic

In a microscopic simulator such as SUMO, use a small grid with four-phase junctions. Compare fixed-time coordination, a green wave, an actuated baseline, a queue-based controller, and the same controllers with signed-family phase dithering. Test demand periods deliberately commensurate and incommensurate with the base cycle.

Record delay, stops, throughput, spillback, queue variance, pedestrian clearance violations, and sensitivity to clock offset.

**Kill criterion:** an effect that disappears under small timing noise or loses to ordinary randomized cycle jitter is not a useful consequence of the exact collinearity theorem.

---

## 7. Mathematical next steps

1. **Formalize the arbitrary-sign theorem.** Generalize the Lean Gaussian recursion from a fixed quarter-turn to a shifted sign stream, then reuse the tag and no-collinearity layers.
2. **Formalize the Walsh corollary.** It is a one-line character identity but is the clearest data-network bridge.
3. **Bound asynchronous correlations.** Synchronous orthogonality is insufficient for independently starting flows.
4. **Prove sharp arbitrary-interval discrepancy.** The dyadic decomposition gives $O(\sqrt L)$; constants and transition-tag effects remain to be optimized.
5. **Seek a topology-aware homomorphism.** Specify when the 16 transition types can be mapped to feasible paths while preserving an injective additive resource signature.
6. **Add destination steering.** At dyadic horizons the source family has only four endpoints. A useful route family needs target reachability without destroying the valuation law.
7. **Investigate weighted or higher-arity analogues.** Unequal capacities and non-four-way switches may require other cyclotomic lattices and valuations; this is currently only a direction, not a theorem.

---

## 8. Relation to established areas

These are comparison points, not claims of equivalence or novelty:

- graph general position formalizes the geodesic “no three on a shortest path” notion: P. Manuel and S. Klavžar, *A general position problem in graph theory*, Bull. Aust. Math. Soc. 98 (2018), [doi:10.1017/S0004972718000473](https://doi.org/10.1017/S0004972718000473);
- Walsh functions are classical synchronous communication codes: H. F. Harmuth, *Applications of Walsh functions in communications*, IEEE Spectrum 6 (1969), [doi:10.1109/MSPEC.1969.5214175](https://doi.org/10.1109/MSPEC.1969.5214175);
- quasirandom load balancing studies deterministic analogues of randomized diffusion, with topology and discrepancy guarantees absent here: T. Friedrich, M. Gairing, and T. Sauerwald, *Quasirandom Load Balancing*, SIAM J. Comput. 41 (2012), [doi:10.1137/100799216](https://doi.org/10.1137/100799216);
- classical oblivious routing is explicitly topology-aware and is designed around worst-case communication or congestion guarantees under unknown demands: L. G. Valiant and G. J. Brebner, *Universal schemes for parallel communication* (1981), [doi:10.1145/800076.802479](https://doi.org/10.1145/800076.802479), and M. Bienkowski, M. Korzeniowski, and H. Räcke, *A practical algorithm for constructing oblivious routing schemes* (2003), [doi:10.1145/777417.777418](https://doi.org/10.1145/777417.777418).

## Bottom line

The family supplies a reusable **finite-action, multiscale, valuation-certified schedule code**. Collinearity becomes “identical average additive resource behavior on adjacent intervals” once a network is equipped with the right labels. That is a valid and potentially useful isomorphism of path signatures.

It does not turn the fractal traces into efficient physical routes. The strongest near-term path is to investigate the family as a nested Walsh probe/telemetry code and as a controlled anti-resonance perturbation, while requiring ordinary routing algorithms to continue handling destinations, capacities, congestion, and failures.
