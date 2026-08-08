# Cardinality-matched spherical menu comparison

**Status:** exact finite experiment through Level 3; not an infinite construction or an availability theorem.

## Question and controlled design

The canonical menu is the 124-vector Chebyshev ball

```text
S_cube = [-2,2]^3 ∩ Z^3 minus {0}.
```

A literal Euclidean radius-two sphere has only the six axial lattice points, so
it is not a useful cardinality-matched analogue.  The comparison instead uses

```text
S_sphere = {v in Z^3 : v_x^2 + v_y^2 + v_z^2 = 74}.
```

This shell has 120 primitive vectors: the signed permutations of `(8,3,1)`,
`(7,5,0)`, and `(7,4,3)`.  Every move has exactly the same Euclidean length,
and all 120 moves have distinct oriented projective directions.  This is close
to the cube menu's 124 moves, of which only 98 are distinct oriented
projective directions because 26 are radial duplicates.

To isolate the menu choice, both variants use exactly the same:

- expansion matrix

  ```text
  M = ((3,0,0),(0,0,-3),(0,3,-2));
  ```
- invariant quadratic metric

  ```text
  Q = ((1,0,0),(0,6,-2),(0,-2,6)),   M^T Q M = 9Q;
  ```
- greedy triple-free Level-0 length `4` and random seed `193`;
- natural anchor order and future-anchor obstacle semantics;
- randomized shortest-first DFS, maximum connector length `12`, six tries per
  gap, four level restarts, and `30,000` nodes per depth attempt;
- exact integer no-three-collinear verification.

The common matrix differs from the canonical record orbit's matrix.  That is
intentional: the even-norm spherical shell generates an even-coordinate-sum
sublattice, and this matrix preserves it.  The experiment is a controlled menu
comparison, not a replay of the record orbit.

## Reproduction and artifacts

```bash
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    python3 -B design/spherical_menu_comparison.py run --variant cube

env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    python3 -B design/spherical_menu_comparison.py run --variant sphere

python3 -B design/spherical_menu_comparison.py compare \
    --cube-result design/spherical-menu-cube-result.json \
    --sphere-result design/spherical-menu-sphere-result.json \
    --output design/spherical-menu-comparison-summary.json
```

The run command checkpoints after every completed anchor gap and resumes only
when its code/config/menu identity matches.  `SIGINT` and `SIGTERM` lose at
most the current gap.  Durable progress logs and working checkpoints default
to `/tmp/spherical-menu-comparison/`.

Repository artifacts:

- `design/spherical_menu_comparison.py` — constructor, verifier, metrics, resume logic;
- `design/spherical-menu-cube-result.json` — complete cube words and diagnostics;
- `design/spherical-menu-sphere-result.json` — complete sphere words and diagnostics;
- `design/spherical-menu-comparison-summary.json` — compact comparison and hashes.

An independent call to the repository's pre-existing `first_disqualifier`
verifier also accepted every saved level of both variants.

## Results

Both menus completed all three requested amplification levels with no repeated
point and no collinear triple.

| level | cube steps | sphere steps | cube DFS nodes | sphere DFS nodes |
|---:|---:|---:|---:|---:|
| 0 | 4 | 4 | — | — |
| 1 | 12 | 17 | 410 | 67,310 |
| 2 | 41 | 64 | 1,760 | 239,235 |
| 3 | 145 | 240 | 10,139 | 1,170,189 |
| **L1–L3 total** | — | — | **12,309** | **1,476,734** |

The sphere needed **119.97 times** as many deterministic DFS nodes in total.
This is not merely because its preceding level had more gaps: at Level 3 the
cost was `18,284` nodes per parent gap versus `247`, still a **73.9-fold**
penalty.  Runtime is machine-dependent and is not the primary metric, but the
corresponding Level-3 times were about `1.13 s` and `164.95 s`.

### Dilution and normalized crowding

For scale ratio three, define the cumulative effective dimension at Level `k`
by

```text
d_k = log(|W_k|/|W_0|) / (k log 3).
```

Lower is preferable for the amplification proof programme: it means fewer new
points per unit volume growth and a more thread-like walk.

| Level-3 diagnostic | cube | sphere | preferable |
|---|---:|---:|---|
| cumulative effective dimension | **1.0894** | 1.2423 | lower |
| maximum normalized `Q`-neighbors at radius multiplier 4 | **16** | 23 | lower |
| maximum connector length used | **5** | 7 | lower |

The normalized crowding threshold is

```text
Q(p-q) <= 16 * mean_{s in menu} Q(s),
```

so it compensates for the very different raw coordinate sizes of the two
menus.  At Level 2 the sphere was slightly less crowded (`18` versus `19`),
but this reversed at Level 3 (`23` versus `16`).

### Where the sphere was better

The sphere did produce substantially more generic directional freedom.

| Level-3 diagnostic | cube | sphere | preferable |
|---|---:|---:|---|
| minimum immediately legal menu moves | 91/124 = 73.4% | **111/120 = 92.5%** | higher |
| unique secant-direction fraction | 87.9% | **96.3%** | higher |
| maximum parallel secant multiplicity | 14 | **11** | lower |
| parallel-secant collision probability | `3.96e-5` | **`3.90e-6`** | lower |

Here a secant collision means that two unordered point pairs have the same
primitive unoriented direction.  Despite having 2.73 times as many point pairs
at Level 3, the spherical walk had fewer such collisions in absolute terms
(`1,630` versus `2,221`) and about a tenfold lower normalized probability.
This is genuine evidence that equal-radius directions reduce exact parallel
stacking.

That improvement did **not** translate into easy anchor-to-anchor routing.
Immediate free steps need not sum to the prescribed transformed parent step.
The pure sphere has no short radial moves, so satisfying the displacement while
avoiding all existing secants was much harder.

### Angular coverage of the menus

Both menus have isotropic second moment, but the particular lattice shell is
not more uniformly distributed at finer angular scales.

| menu diagnostic | cube | sphere | preferable |
|---|---:|---:|---|
| distinct oriented directions | 98 | **120** | higher |
| minimum separation | **15.79°** | 9.43° | higher |
| sampled covering radius (20,000 deterministic probes) | **17.59°** | 21.46° | lower |

Thus the radius-74 shell has both closer clusters and larger uncovered holes.
Merely putting all vectors on one sphere does not create a uniformly spaced
spherical code.

## Spherical-coordinate conclusion

Ordinary `(radius, theta, phi)` coordinates are not an integer arithmetic
system: trigonometric coordinates are generally irrational, and vector
addition becomes nonlinear.  The useful exact representations are primitive
integer projective directions, rational dot/cross products, and the invariant
quadratic metric `Q` above.

A menu on a strict invariant `Q`-sphere has an additional structural cost.  If
all steps have `Q`-norm `R`, then `Mv` has `Q`-norm `3R`.  If three shell steps
sum to `Mv`, equality holds in the triangle inequality, forcing all three to
be positively parallel.  The resulting connector is collinear and illegal.
Therefore every legal connector on an exact `Q`-sphere has length at least
four, imposing the lower growth dimension

```text
log(4) / log(3) = 1.26186...
```

before any global obstacles are considered.  A `Q`-sphere aligns elegantly
with the expansion but is consequently not a promising pure replacement at
scale three.

## Verdict

For this constructor, seed, and three-level controlled test, the **cube menu is
better overall** on the proof-relevant primary diagnostics:

- about `120x` less routing search;
- lower growth dimension;
- lower matched-scale Level-3 crowding;
- shorter connectors;
- better fine angular covering despite having fewer unique directions.

The sphere is better on a real secondary effect: it strongly suppresses
parallel-secant concentration and leaves more arbitrary next moves legal.  That
suggests a **hybrid menu** as the useful follow-up—retain a small set of radial
short moves for displacement closure while adding a carefully optimized
spherical code for secant deconcentration.  The present data do not justify
replacing the cube by a pure equal-radius shell.

## Claim boundary

This is one deterministic seed through three finite levels.  It does not prove
that the cube dominates every spherical shell, every seed, or every routing
policy.  It proves neither successor closure nor an infinite walk.  In
particular, the tenfold secant-deconcentration signal is worth preserving in a
future hybrid test, but it is not itself a far-secant availability theorem.
