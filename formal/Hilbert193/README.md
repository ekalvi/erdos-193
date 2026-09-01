# Lean formalization

This package formalizes the Gaussian-lattice construction in the joint Stijn Cambie–Erik Kalviainen version of the Erdős Problem 193 paper against pinned Lean 4 and Mathlib revisions.

`Hilbert193.erdos193_unconditional` in `Hilbert193/Continuity.lean` constructs a fixed finite step set in `ℤ³` and an infinite walk using that set, then proves that no ordered triple of distinct walk vertices is collinear. The historical package namespace is retained for repository compatibility; the theorem no longer imports the Hilbert decoder.

## Build and audit

```bash
lake build
lake env lean Hilbert193/AxiomAudit.lean
```

The load-bearing dependency chain is:

1. `GaussianValuation.lean` — the two-adic valuation of a Gaussian chord's squared norm.
2. `Gaussian.lean` — binary recursion for `u_n=i^{s₂(n)}` and `z_n=Σ_{r<n}u_r`, continuity, and the equal-state halving law.
3. `Construction.lean` — Gray-code planar tags, height tags, the all-pairs law, and the no-collinearity theorem.
4. `Continuity.lean` — the sixteen direction-pair steps, coordinate bounds, and the final theorem.
5. `AxiomAudit.lean` — reports the kernel dependencies of the public theorems.

The audit reports only Mathlib's standard `propext`, `Classical.choice`, and `Quot.sound`. There are no project-specific axioms, `sorry`s, or finite-computation assumptions in the theorem.
