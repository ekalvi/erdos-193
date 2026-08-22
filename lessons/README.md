# Guided lessons for Erdős Problem 193

This sequence develops the proof’s main ideas for a reader who is comfortable with basic arithmetic and coordinates but may be new to Hilbert paths, base-4 notation, and two-adic valuation.

The lessons favor mental models, worked examples, and active-recall checkpoints before formal notation. Read them in order and answer each checkpoint from memory before continuing.

## Scope and status

These notes are a pedagogical companion to the [proof manuscript](../paper/erdos193.pdf), not a replacement for it. The current sequence develops the problem statement, the trace-select-lift construction, bounded-gap selection, two-adic vector fingerprints, and the same-terminal-state Hilbert pair law. The manuscript contains the complete no-three-collinear argument and the remaining formal details.

The repository’s construction is unconditional and formalized in Lean 4. External mathematical review and community acceptance are still pending.

## Recommended order

1. [The problem in plain English](01%20-%20The%20Problem%20in%20Plain%20English.md) — the lattice, finite step menu, infinite walk, collinearity, and what a negative answer must construct.
2. [Trace, select, and lift](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md) — the complete high-level architecture and the separate jobs performed by each component.
3. [Why the gaps are 4 to 28](03%20-%20Why%20the%20Gaps%20Are%204%20to%2028.md) — one selected index per block, the four candidate offsets, and the finite-step argument.
4. [Why the orientation states choose those offsets](03A%20-%20Why%20I%2C%20S%2C%20T%2C%20and%20C%20Choose%20Those%20Offsets.md) — an optional deeper explanation of the two-digit base-4 steering suffixes.
5. [Powers of two as a fingerprint](04%20-%20Powers%20of%20Two%20as%20a%20Fingerprint.md) — ordinary two-adic valuation, the custom planar-vector invariant, and its scaling law.
6. [Why the Hilbert pair law is true](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md) — how the first base-4 mismatch controls both the index-gap valuation and planar-chord fingerprint.

If the place-value step in Lesson 05 feels compressed, pause for [Why matching final digits forces divisibility](05A%20-%20Why%20Matching%20Final%20Digits%20Forces%20Divisibility.md), then return to Lesson 05.

If the digit-to-coordinate notation in Lesson 05 is unfamiliar, pause for [How to read the Hilbert digit notation](05B%20-%20How%20to%20Read%20the%20Hilbert%20Digit%20Notation.md). It defines $k$, $q_k$, $\in$, $\{0,1\}^2$, emitted bits, and the coordinate sums from first principles.

If incoming and outgoing orientation states are unclear, continue with [When Hilbert orientation applies](05C%20-%20When%20Hilbert%20Orientation%20Applies.md). It separates the state that transforms the current digit from the state passed to the next digit and gives a worked example where orientation visibly changes an emitted pair.

## Authoritative proof sources

- [Proof manuscript](../paper/erdos193.pdf)
- [Lean formal proof guide](../formal/Hilbert193/README.md)
- Main Lean theorem: `Hilbert193.erdos193_unconditional`

Finite computations in this repository are supporting evidence and implementation checks; they are not premises of the infinite theorem.
