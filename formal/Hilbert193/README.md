# Hilbert193

Lean 4 formalization of the all-index state-tagged Hilbert construction for
Erdős Problem 193.

## Main result

`Hilbert193.erdos193_unconditional` in `Hilbert193/Continuity.lean` constructs
a fixed finite step set in `ℤ³` and an infinite walk using that set, then proves
that no ordered triple of distinct walk vertices is collinear.

## Verification

```sh
lake build
lake env lean Hilbert193/AxiomAudit.lean
```

The package pins Lean 4.33.0 and its Mathlib revision in
`lake-manifest.json`. The axiom audit prints only Mathlib's standard
`propext`, `Classical.choice`, and `Quot.sound`.

## Module order

1. `Basic.lean` — shared elementary definitions.
2. `Transducer.lean` — digits, square orientations, and the Hilbert transducer.
3. `Valuation.lean` — the two-adic planar chord invariant.
4. `PairLaw.lean` — the same-terminal-state pair law and lifting obstruction.
5. `Construction.lean` — state tags, the all-pairs law, and no-three-in-line lift.
6. `Continuity.lean` — Hilbert adjacency, the tagged finite step menu, and final theorem.
7. `AxiomAudit.lean` — kernel dependency report for the load-bearing theorems.
