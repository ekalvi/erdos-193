# Erdős Problem 193: a finite-step walk in ℤ³ with no three collinear vertices

This repository gives an explicit negative answer to [Erdős Problem 193](https://www.erdosproblems.com/193): it constructs an infinite sequence in $\mathbb Z^3$ whose consecutive differences come from a fixed finite set, while no three vertices are collinear.

The construction is unconditional and formalized in Lean 4. External mathematical review and community acceptance remain pending.

## Read and run it

- **Production site:** [erdos-193.q5m.ai](https://erdos-193.q5m.ai)
- **Current paper:** [PDF](https://erdos-193.q5m.ai/erdos-193-gaussian-proof.pdf) · [LaTeX source](paper/erdos193.tex)
- **Lean theorem:** [`Hilbert193.erdos193_unconditional`](formal/Hilbert193/Hilbert193/Continuity.lean) · [formal proof guide](formal/Hilbert193/README.md)
- **Minimal constructor:** [`viz/gaussian_walk.py`](viz/gaussian_walk.py)
- **Executable finite checks:** [`viz/gaussian_walk_demo.py`](viz/gaussian_walk_demo.py) · [run in the browser](https://erdos-193.q5m.ai/demo.html)

## Construction at a glance

Let $u_n=i^{s_2(n)}$, where $s_2(n)$ is the binary digit sum, and let $z_n=\sum_{r<n}u_r$. Matching planar and height tags lift this Gaussian-lattice walk to points $P_n\in\mathbb Z^3$.

The proof establishes the all-pairs identity

$$
\nu_2\!\left(|w_n-w_m|^2\right)=\nu_2(h_n-h_m).
$$

A planar chord scaled by an integer gains twice that integer's two-adic valuation in squared norm, while its height gains it only once. This mismatch rules out a collinear triple. Consecutive points use a fixed menu of 16 small three-dimensional steps.

## Verify the formal proof

The Lean package pins its Lean and Mathlib revisions.

```bash
cd formal/Hilbert193
lake build
lake env lean Hilbert193/AxiomAudit.lean
```

The axiom audit reports only Mathlib's standard `propext`, `Classical.choice`, and `Quot.sound`; the main theorem uses no project-specific axioms or unfinished placeholders.

To replay the independent finite checks:

```bash
python3 viz/gaussian_walk_demo.py
```

Finite computation is supporting evidence, not a premise of the infinite theorem.

## Authors and provenance

The current paper is jointly authored by [Stijn Cambie](https://arxiv.org/search/?query=Stijn+Cambie&searchtype=author) and [Erik Kalviainen](https://github.com/ekalvi). Cambie proposed the all-index and Gaussian-lattice simplifications; Kalviainen developed the original Hilbert construction and migrated the final proof into Lean, executable checks, and this site. Both authors have checked the proof and state the result as an unconditional theorem. Both development streams were AI-assisted; S.C. is supported by FWO grant 1225224N.

The earlier Hilbert construction and finite artifacts are retained as provenance but are not premises of the current Gaussian proof. Citation metadata is in [`CITATION.cff`](CITATION.cff), and the chronological development record is on the [timeline](https://erdos-193.q5m.ai/progress.html).
