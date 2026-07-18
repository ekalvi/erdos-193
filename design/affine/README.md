# Affine-decimation route

**Status: the original `Z^9` walk is a higher-dimensional laboratory; a direct
weighted merge in `Z^3` is now the dimension-correct candidate, with
triple-freeness open.**  This route is independent of the scale-and-rotate
connector induction.  A proof about the nine-dimensional product alone would
not settle Erdos #193, whose ambient lattice is fixed to `Z^3`.

## Candidate and proved finite menu

Let `lambda` be the fixed point beginning in symbol 0 of Lidbetter's
seven-uniform morphism (the table is embedded in both source files here).  Map
symbol `a` to the coordinate step `e_(a mod 3)` and define

```text
W_0 = 0,
W_(n+1) = W_n + e_(lambda_n).
```

The candidate is

```text
P_n = (W_n, W_(2n), W_(5n)) in Z^9.
```

Its step from `n` to `n+1` has three blocks with coordinate sums 1, 2, and 5.
Consequently it uses at most

```text
C(3,2) C(4,2) C(7,2) = 3 * 6 * 21 = 378
```

integer step vectors.  This is a proof, not a prefix observation.  The first
block has coordinate sum `n`, so all vertices are distinct.  Proving that no
three `P_n` are collinear would prove the corresponding finite-step theorem in
dimension nine.

## Dimension-three barrier

There is no proved collinearity-faithful integer projection of this walk from
`Z^9` to `Z^3`.  A generic real projection is irrelevant: it need not be
integer-valued, and avoiding every one of countably many bad triples is not a
finite verification.  Likewise, a fixed integer linear projection can turn
two independent chord vectors into parallel vectors.

Consequently this route can contribute to #193 only after an additional
theorem supplies either:

1. an explicit integer projection that preserves noncollinearity for every
   triple of this particular walk; or
2. a direct three-dimensional variant, such as
   `R_n=(n,F_n,G_n)`, with two scalar automatic coordinates whose adjacent
   chord slopes are never simultaneously equal.

See `../WEAK-ABELIAN-LIFT.md` for the exact projection obstruction.

## Direct weighted merge in `Z^3`

A dimension-correct compression is

```text
R_n(C) = W_n + C W_(2n) + C^2 W_(5n) in Z^3.            (A)
```

Its increments use at most the same `3 * 6 * 21 = 378` combinations.  Every
increment has coordinate sum

```text
H_C = 1 + 2C + 5C^2 > 0,
```

so the vertices are distinct and any two parallel ordered chords have the
ratio forced by their index lengths.  With

```text
Z_n(C) = V_n + C V_(2n) + C^2 V_(5n),
```

triple-freeness is exactly nonvanishing of the projected defect

```text
D_C(i;m,n) = D_1(i;m,n) + C D_2(i;m,n) + C^2 D_5(i;m,n). (B)
```

It retains the exact descent identity

```text
D_C(7i;7m,7n) = 28 D_C(i;m,n).                          (C)
```

Thus `D_C=0 => 7 divides i,m,n` would prove (A) triple-free by infinite
descent.  This divisibility lemma is not proved.

`check_weighted_merge.cpp` hashes every primitive chord direction and is an
exact all-triples prefix checker.  The first coefficient screen found:

| `C` | Exact result |
|---:|---|
| 3 | counterexample `(604,610,616)`; prefix through 615 clean |
| 4 | counterexample `(1725,1823,2803)` |
| 5 | counterexample `(825,833,841)` |
| 6 | counterexample `(1382,1424,1466)` |
| 7 | counterexample `(16244,18696,21148)` |
| 8 | counterexample `(6458,7424,8873)` |
| 9 | no counterexample through index 30,000; 450,014,999 chords checked |

The full coordinates, hashes, and controls are in
`weighted-merge-screen.json`.  The `C=9` result is finite evidence only.  For
any finite prefix, only finitely many projection coefficients are forbidden,
so coefficient search can manufacture long survivors without producing a
uniform invariant.  `C=9` should be promoted only if its projected normalized
defect graph has a finite zero-exclusion or divisibility-descent certificate.

The recurrence generator now constructs the exact `C=9` projected correction
table.  It still has 17,280 minimal Mealy states and 8,074 distinct correction
vectors--exactly the counts of the full product table.  Ordinary output/state
minimization therefore gives no simplification; a proof quotient would have to
use defect geometry, divisibility, or another semantic invariant.

### Coefficient-nine staged modular audit

The coefficient itself gives a cheaper *filter*, although not a proof.  Writing

```text
E = D_1 + 9 D_2 + 81 D_5,
```

an exact zero forces `9 | D_1` and `9 | (D_1/9+D_2)`.  Partition refinement of
the projected correction recurrence gives the following exact hierarchy:

| Required defect precision | Modulus on the centered `Z` recurrence | Minimal correction states |
|---|---:|---:|
| `E mod 9` | 27 | 12 |
| `E mod 81` | 243 | 360 |
| `E mod 729` | 2,187 | 17,280 |

For all 1,774,630 triples ending by index 220, the survivor counts are 74,342,
1,245, 14 and 0 modulo `9,81,729,6561`, respectively.  This is a strong staged
finite filter.  It is not bounded-valuation descent: primitive nonzero defects
survive through `7^7`, and `(i,m,n)=(78,1675,385)` has
`E=9^5(150,135)` with `3` not dividing `m`.

The smallest SCC interpretation also fails exactly.  The single-index lift

```text
(t mod 27, lambda_t, Z_t mod 27)
```

has 26,244 states and is primitive.  Even after retaining the complete
360-class correction information needed at the next base-9 digit while keeping
values modulo 27, the 787,320-state lift remains primitive.  Therefore an
independent three-endpoint product has one SCC and a zero-containing SCC cannot
be separated at this precision.  Zero is not prefix-closed either: endpoints
`(4,10,22)` have centered defect zero modulo 243, while their base-7 parents
`(0,1,3)` do not.  A solver may use the modular layers only as filters inside a
sound chord/gap or polyhedral state; it may not retain only zero prefixes.
`c9_modular_gate.py` reconstructs these quotients independently, checks 7,007
direct recurrence transitions, certifies both primitive graphs and binds the
state/edge relations by SHA-256.  Its compact checked output is
`c9-modular-gate-summary.json`.

## Exact collinearity defect

Write three indices as `i, i+m, i+m+n`, with `m,n >= 1`.  The coordinate sum of
the first `W` chord is `m`, and that of the second is `n`.  Hence collinearity is
equivalent to

```text
n (P_(i+m)-P_i) = m (P_(i+m+n)-P_(i+m)).                 (1)
```

Let `c=(1,1,1)`,

```text
V_t = 3 W_t - t c,
Q_t = (V_t, V_(2t), V_(5t)).
```

The affine coordinate-sum term cancels from (1), so define the exact integer
defect

```text
D(i;m,n) = n (Q_(i+m)-Q_i)
           - m (Q_(i+m+n)-Q_(i+m)).                     (2)
```

The theorem needed is simply `D(i;m,n) != 0` for all `i>=0,m,n>=1`.

## Exact base-7 recurrence

Every morphism image has projected Parikh vector `4 e_(a mod 3)+c`.  Therefore

```text
W_(7t) = 4 W_t + t c,
V_(7t) = 4 V_t.
```

More generally,

```text
V_(7t+r) = 4 V_t + g(lambda_t,r),  0 <= r < 7,
```

where `g` is a finite integer table.  The multipliers 2 and 5 introduce only
base-7 carries.  The exact joint symbol state

```text
(lambda_t, lambda_(2t), lambda_(2t+1),
 lambda_(5t), ..., lambda_(5t+4))
```

obeys a finite digit transition and determines `h` in

```text
Q_(7t+r) = 4 Q_t + h(state(t),r).                        (3)
```

`affine_recurrence.py` constructs this transducer from the morphism rather than
assuming it.  The current exact table has:

- 17,280 reachable joint states;
- 8,074 distinct correction vectors;
- maximum correction coordinate 21 in absolute value;
- no reduction under ordinary correction-transducer partition refinement.

It also verifies 70,007 instances of (3) over parent indices 0 through 10,000.
The finite table construction proves (3) symbolically; the prefix check guards
the implementation.

Scaling all three indices and both gaps gives

```text
D(7i;7m,7n) = 28 D(i;m,n).                               (4)
```

Thus a proof that every zero forces `7 | i,m,n` would yield infinite descent.
No such divisibility theorem is currently known.

## Exact finite computation

`check_affine_125.cpp` first hashes every triple collinear in the `W_n` block,
then checks the `2n` and `5n` blocks using (1).  It uses exact integer arithmetic
and examines all triples, not a sample.

The reproducible low-priority run through index 30,000 found no counterexample:

```text
vertices                         30,001
base-projection triples checked 175,158
minimum nonzero raw defect             1  at (5,6,7)
minimum normalized defect       0.0180851 at (24716,25656,26596)
minimum raw/28^floor(log_7 gap)  0.0755056 at (14012,14222,16742)
```

The checker reports the `W`-block raw defect; the corresponding `Q` defect is
three times that value.

This is finite evidence only.  The result and build hashes are in
`affine-125-prefix-30000.json`.

Build and run with one low-priority core:

```sh
clang++ -O3 -std=c++17 -Wall -Wextra -pedantic \
  design/affine/check_affine_125.cpp -o /tmp/check_affine_125

clang++ -O3 -std=c++17 -Wall -Wextra -pedantic \
  design/affine/check_weighted_merge.cpp -o /tmp/check_weighted_merge

env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    nice -n 15 /tmp/check_affine_125 30000

env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    nice -n 15 /tmp/check_weighted_merge 30000 9

env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    nice -n 15 python3 -B design/affine/affine_recurrence.py

env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    nice -n 15 python3 -B design/affine/c9_modular_gate.py \
      --staged --mod243-depth 7
```

## Compact gap-ratio reduction for the `Z^9` product

Lidbetter's primary proof shows that two collinear `W` chords at seven-adic gap
scales `7^a` and `7^b` have `|a-b|<=3` when the smaller gap is at least seven;
the special smaller-gap case gives a scale difference at most five.  Applied to
the two adjacent chords of a hypothetical collinear triple, this yields the safe
compact range

```text
7^(-6) < m/n < 7^6.                                      (5)
```

This is derived from the distance-ratio argument in Section 4 of Finn
Lidbetter, *An infinite walk in Z^3 with no 189 collinear points*,
<https://arxiv.org/abs/2303.14579>.  It bounds relative gap scale, not absolute
gap size.

This reduction does **not** follow for the weighted merge.  A zero of
`D_1+C D_2+C^2 D_5` need not make the `W_n` block collinear, so Lidbetter's
full-chord premise is absent.  A `C=9` certificate must cover arbitrary gap
ratios or first prove a new projected gap-ratio lemma.

## Referee-grade missing lemma for the `Z^9` candidate

A clean sufficient statement is a uniform chord-transversality estimate.  Let
`alpha=log_7(4)`.  Prove that some `eta>0` satisfies, whenever (5) holds,

```text
|| (Q_(i+m)-Q_i)/m
   - (Q_(i+m+n)-Q_(i+m))/n ||_infinity
    >= eta * max(m,n)^(alpha-1).                          (6)
```

Equivalently, at scale `7^k <= max(m,n) < 7^(k+1)`, prove

```text
||D(i;m,n)||_infinity >= eta' * 28^k.                     (7)
```

Either statement implies that the exact `Z^9` defect never vanishes.  Neither
is currently proved, and the 30,001-vertex check does not imply a uniform
margin.  This lemma would still leave the dimension-three barrier above.

## Proposed certificate for the `Z^9` product

The shortest credible next attempt is a rational polyhedral CEGAR proof:

1. Use the exact correction transducer generated here.
2. Build a synchronous base-7 transducer for `i,m,n`, additions, carries,
   positivity/order, and gap-ratio range (5).
3. Propagate normalized chord/defect enclosures, dividing the next scale by 28.
4. Close a node when one exact rational defect interval excludes zero.
5. Send the all-zero digit branch to the exact descent identity (4).
6. Refine every remaining zero-containing node by another digit or a separating
   rational hyperplane.
7. Independently check the resulting finite graph, transition inclusions, and
   exclusion/descent labels.

If every branch closes, this proves the `Z^9` candidate triple-free.  If a
zero-containing branch becomes periodic, evaluate it exactly: it may expose a
counterexample, a zero limit that refutes the positive-margin lemma, or a
weaker arithmetic rank that still excludes finite exact zero.  A separate
projection or direct-`Z^3` lemma would still be required for #193.

## Strongest obstruction

Ordinary automaticity is not enough.  The exact correction transducer is already
large and minimal, while the defect is bilinear in two unbounded gaps.  No fixed
modulus can certify descent: finite colorings necessarily have long arithmetic
progressions producing modular second-difference false positives at nonzero
residues modulo seven.

More seriously, the normalized graph-directed defect closure may contain zero
without any finite integer triple attaining zero.  In that case the positive
margin (6) is false and interval CEGAR will refine forever.  Long repeated
morphic factors make this a real possibility.  The current data support the
candidate but do not resolve this obstruction.

## Dimension-correct certificate target

For #193 itself, the live automatic target is `C=9` in (A), not the full `Z^9`
defect.  Generate the projected correction table

```text
h_9 = h_1 + 9 h_2 + 81 h_5
```

from the existing 17,280 joint states.  A sound finite proof graph must accept
all positive `i,m,n` and retain both adjacent chords and both gaps.  If
`u=y-x`, `v=z-y`, `A=Z_y-Z_x`, `B=Z_z-Z_y` and the appended endpoint digits
give `p=beta-alpha`, `q=gamma-beta`, then the exact defect update contains

```text
F' = 28 F + 4(q A-p B) + 7(v deltaA-u deltaB)
     + (q deltaA-p deltaB).
```

Thus `F` plus the symbol state is not closed.  Every zero-containing cell must
instead be certified by one of two labels:

1. exact common divisibility, sending `(i,m,n)` to `(i/7,m/7,n/7)` via (C);
2. an exact rational separator proving the projected defect cannot be zero.

Unlike the product certificate, this graph cannot assume the compact gap range
(5).  The 12- and 360-state modular quotients can cheaply prune cells, but their
primitive lifts cannot themselves supply the invariant.  A non-descent
recurrent component whose nested rational sets keep zero would refute a
uniform-margin proof and force a different arithmetic ranking.  The clean
30,001-vertex prefix does not rule out that obstruction; the failures for
`C=3,...,8` show that projection cancellation is real.
