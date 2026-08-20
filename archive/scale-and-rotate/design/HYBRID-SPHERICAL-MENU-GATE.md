# Pre-registered hybrid spherical-menu gate

**Status:** exact finite Level-0--Level-3 experiment; the selected hybrid fails the gate.  This is not an infinite-construction theorem.

## Goal

The pure 120-vector sphere reduced Level-3 parallel-secant collision probability
by about a factor of ten, but made prescribed anchor routing roughly 74 times
harder per gap than the cube.  The proposed salvage was to retain every short
cube move and add a small spherical direction layer.

The hybrid was required to preserve short displacement closure while achieving:

1. Level-3 routing nodes per gap at most `2x` the cube;
2. cumulative growth dimension at most `1.12`;
3. normalized Level-3 `Q`-crowding at most the cube value `16`;
4. parallel-secant collision probability at most one third of the cube value.

No scalar score or post-run candidate selection is used.

## Static layer selection

Before constructing any hybrid walk, four 24-move layers were compared using
20,000 deterministic Fibonacci-sphere probes:

| candidate layer | hybrid menu size | sampled covering radius | mean nearest-probe angle |
|---|---:|---:|---:|
| cube control | 124 | 17.594 degrees | 8.199 degrees |
| full shell `x^2+y^2+z^2=10` | 148 | 14.704 degrees | 7.447 degrees |
| **full shell `x^2+y^2+z^2=11`** | **148** | **13.938 degrees** | **7.344 degrees** |
| full shell `x^2+y^2+z^2=13` | 148 | 17.594 degrees | 7.869 degrees |
| angularly greedy half of shell 14 | 148 | 17.594 degrees | 7.716 degrees |

The fixed selection rule chose the smallest sampled covering radius, with mean
angle and then name as tie breakers.  It selected all 24 signed permutations
of `(3,1,1)`, giving 122 distinct oriented projective directions in the
148-move hybrid menu.

## Short-connector gate correction

The first draft required exact connector closure by length four.  Its control
failed: four of the eight unresolved hybrid-menu directions were original cube
steps, and the matched cube construction itself uses length-five connectors.
Therefore length four was not a baseline-preserving gate and could not fairly
reject the hybrid.

This was detected **before constructing any hybrid level**.  The closure bound
was repaired to the cube-calibrated length five; all numerical Level-3 gates
were left unchanged.  Under that fair bound every one of the 148 hybrid steps
has an exact intrinsically triple-free connector:

```text
minimum connector lengths: 38 at length 2,
                           70 at length 3,
                           32 at length 4,
                            8 at length 5,
                            0 missing.
```

## Controlled construction

The hybrid and cube control use the same:

- `M=((3,0,0),(0,0,-3),(0,3,-2))` and its invariant `Q` metric;
- Level-0 length four and random seed 193;
- future-anchor semantics, natural gap order, DFS budgets, and exact verifier;
- normalized metrics from `spherical_menu_comparison.py`.

The hybrid completed all requested levels and was independently accepted by the
repository's pre-existing `first_disqualifier` verifier:

| level | cube steps | hybrid steps | cube DFS nodes | hybrid DFS nodes |
|---:|---:|---:|---:|---:|
| 0 | 4 | 4 | — | — |
| 1 | 12 | 13 | 410 | 25,514 |
| 2 | 41 | 55 | 1,760 | 335,631 |
| 3 | 145 | 186 | 10,139 | 569,221 |

## Gate result

| Level-3 gate | required | cube | hybrid | result |
|---|---:|---:|---:|---|
| exact short closure | every step by length 5 | yes | yes | **pass** |
| routing nodes per gap | at most `2x` cube | 247.3 | 10,349.5 (`41.85x`) | **fail** |
| cumulative growth dimension | at most 1.12 | 1.0894 | 1.1649 | **fail** |
| normalized `Q` radius-4 crowding | at most 16 | 16 | 17 | **fail** |
| parallel-secant probability | at most one third cube | `3.965e-5` | `1.793e-5` (`0.452x`) | **fail** |

The hybrid does retain part of the spherical signal: it reduces parallel-secant
collision probability by a factor of `2.21`.  But that misses the required
factor three and costs a factor `41.85` in Level-3 routing work per gap.  Its
minimum immediately legal menu fraction also falls to `65.5%`, below the cube's
`73.4%`, and one realized Level-3 connector has length ten.

## Decision

**Retire this statically selected hybrid candidate and do not pivot the main
proof route to spherical menus.**

The negative decision is stronger than the pure-sphere result: even after
retaining every cube move, adding the angularly best of four small spherical
layers does not convert secant deconcentration into proof-friendly routing.
The direction-diversity benefit is real but too expensive under the tested
constructor.

This does not prove that every hybrid menu fails.  It does satisfy the promised
bounded follow-up, and the pre-registered result gives no justification for a
larger spherical parameter search.  Further work should return to the main
reachable far-secant/birth-address obstruction unless a new theorem—not another
menu sweep—changes the tradeoff.

## Reproduction and artifacts

```bash
python3 -B design/hybrid_spherical_menu_experiment.py screen
python3 -B design/hybrid_spherical_menu_experiment.py run
python3 -B design/hybrid_spherical_menu_experiment.py compare
```

The closure phase checkpoints after every source step; amplification checkpoints
after every parent gap.  `SIGINT`/`SIGTERM` resume safely.

Repository artifacts:

- `design/hybrid_spherical_menu_experiment.py`
- `design/hybrid-spherical-menu-screen.json`
- `design/hybrid-spherical-menu-result.json`
- `design/hybrid-spherical-menu-summary.json`

## Claim boundary

This is one preselected 24-move layer, one deterministic seed, and three finite
levels.  It proves neither universal hybrid failure, successor closure, nor an
infinite walk.
