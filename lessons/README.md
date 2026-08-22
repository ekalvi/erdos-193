# Guided lessons for Erdős Problem 193

This sequence develops the proof’s main ideas for a reader who is comfortable with basic arithmetic and coordinates but may be new to Hilbert paths, base-4 notation, and two-adic valuation.

The lessons favor mental models, worked examples, and active-recall checkpoints before formal notation. Read them in order and answer each checkpoint from memory before continuing.

## Scope and status

These notes are a pedagogical companion to the [proof manuscript](../paper/erdos193.pdf), not a replacement for it. The current sequence develops the problem statement, the trace-select-lift construction, bounded-gap selection, two-adic vector fingerprints, the same-terminal-state Hilbert pair law, and the contradiction excluding collinear triples. The manuscript contains the remaining formal details.

The repository’s construction is unconditional and formalized in Lean 4. External mathematical review and community acceptance are still pending.

## Recommended order

1. [The problem in plain English](01%20-%20The%20Problem%20in%20Plain%20English.md) — the lattice, finite step menu, infinite walk, collinearity, and what a negative answer must construct.
2. [Trace, select, and lift](02%20-%20Trace%2C%20Select%2C%20and%20Lift.md) — the complete high-level architecture and the separate jobs performed by each component.
3. [Why the gaps are 4 to 28](03%20-%20Why%20the%20Gaps%20Are%204%20to%2028.md) — one selected index per block, the four candidate offsets, and the finite-step argument.
4. [Why the orientation states choose those offsets](03A%20-%20Why%20I%2C%20S%2C%20T%2C%20and%20C%20Choose%20Those%20Offsets.md) — an optional deeper explanation of the two-digit base-4 steering suffixes.
5. [Powers of two as a fingerprint](04%20-%20Powers%20of%20Two%20as%20a%20Fingerprint.md) — ordinary two-adic valuation, the custom planar-vector invariant, and its scaling law.
6. [Why the Hilbert pair law is true](05%20-%20Why%20the%20Hilbert%20Pair%20Law%20Is%20True.md) — how the first base-4 mismatch controls both the index-gap valuation and planar-chord fingerprint.
7. [Why three lifted points cannot be collinear](06%20-%20Why%20Three%20Lifted%20Points%20Cannot%20Be%20Collinear.md) — how collinearity, the pair law, and the fingerprint scaling law force an impossible odd-plus-odd parity conclusion.

If the place-value step in Lesson 05 feels compressed, pause for [Why matching final digits forces divisibility](05A%20-%20Why%20Matching%20Final%20Digits%20Forces%20Divisibility.md), then return to Lesson 05.

If the digit-to-coordinate notation in Lesson 05 is unfamiliar, pause for [How to read the Hilbert digit notation](05B%20-%20How%20to%20Read%20the%20Hilbert%20Digit%20Notation.md). It defines $k$, $q_k$, $\in$, $\{0,1\}^2$, emitted bits, and the coordinate sums from first principles.

If the square-within-a-square picture or orientation handoff is unclear, continue with [How orientation changes while decoding](05C%20-%20When%20Hilbert%20Orientation%20Applies.md). It constructs the actual $4\times4$ route, defines a “child square” as one ordinary quarter of the grid, and explains why an orientation carried from position $k$ is used by the next digit at position $k-1$.

Before using the same-terminal-state hypothesis in Lesson 05, read [What the Hilbert terminal state remembers](05D%20-%20What%20the%20Hilbert%20Terminal%20State%20Remembers.md). It explains the four reachable states, their digit-parity meaning, and why equal terminal states permit the backward-rewind comparison at the first mismatch.

## Authoritative proof sources

- [Proof manuscript](../paper/erdos193.pdf)
- [Lean formal proof guide](../formal/Hilbert193/README.md)
- Main Lean theorem: `Hilbert193.erdos193_unconditional`

Finite computations in this repository are supporting evidence and implementation checks; they are not premises of the infinite theorem.
