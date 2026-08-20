# Erdős Problem 193: a finite-step walk in ℤ³ with no three collinear vertices

This repository gives an explicit negative answer to [Erdős Problem 193](https://www.erdosproblems.com/193).

There are a finite set $S \subseteq \mathbb Z^3$ and an infinite sequence $P : \mathbb N \to \mathbb Z^3$ such that every difference $P_{n+1}-P_n$ lies in $S$, while no three distinct terms of $P$ are collinear.

The construction is unconditional and formalized in Lean 4. External mathematical review and community acceptance are still pending.

- **Visual explanation:** [erdos.q5m.io](https://erdos.q5m.io)
- **Proof manuscript:** [`paper/erdos193.pdf`](paper/erdos193.pdf)
- **Lean theorem:** `Hilbert193.erdos193_unconditional`
- **Formal proof guide:** [`formal/Hilbert193/README.md`](formal/Hilbert193/README.md)

## Result at a glance

The proof uses a nested discrete Hilbert path $H : \mathbb N \to \mathbb N^2$.

1. A finite-state rule selects one Hilbert index from every block of 16 indices.
2. The selected indices have gaps between 4 and 28.
3. Each selected planar point is lifted by its Hilbert index, giving points in $\mathbb Z^3$.
4. A two-adic invariant of every selected planar chord rules out three collinear lifted points.
5. Bounded index gaps and Hilbert adjacency imply that successive lifted points use a fixed finite step menu.

The Lean development checks this infinite argument. A separate 500,000-step computation is supporting evidence and an independently inspectable implementation check; it is not the proof of the infinite theorem.

## Verify the formal proof

The Lean package pins its Lean and Mathlib revisions.

```bash
cd formal/Hilbert193
lake build
lake env lean Hilbert193/AxiomAudit.lean
```

The axiom audit reports only Mathlib's standard `propext`, `Classical.choice`, and `Quot.sound`. No project-specific axioms or unfinished placeholders are used by the main theorem.

The load-bearing modules are:

1. [`Basic.lean`](formal/Hilbert193/Hilbert193/Basic.lean) — digits, orientations, and the Hilbert transducer.
2. [`Transducer.lean`](formal/Hilbert193/Hilbert193/Transducer.lean) — reversibility and coordinate evaluation.
3. [`Valuation.lean`](formal/Hilbert193/Hilbert193/Valuation.lean) — the two-adic planar chord invariant.
4. [`PairLaw.lean`](formal/Hilbert193/Hilbert193/PairLaw.lean) — the same-terminal-state pair law.
5. [`Construction.lean`](formal/Hilbert193/Hilbert193/Construction.lean) — bounded-gap selection and exclusion of collinear triples.
6. [`Continuity.lean`](formal/Hilbert193/Hilbert193/Continuity.lean) — the finite step menu and final theorem.
7. [`AxiomAudit.lean`](formal/Hilbert193/Hilbert193/AxiomAudit.lean) — kernel dependency report.

## Check the finite artifact

[`hilbert-193-500k.jsonl`](hilbert-193-500k.jsonl) contains 500,001 vertices from the explicit construction. The standalone Python verifier independently reconstructs every selected Hilbert index and coordinate, then checks every consecutive step against the 16-vector menu:

```bash
python3 verify_hilbert_construction.py
```

The recorded artifact has SHA-256
`6f8fdf59b7ecef5533b8a65265d80df961f67a955dabaf9d5bb973d7ae143d63`.

An independent C++ verifier checked all 125,000,250,000 earlier-point directions in the artifact and found no repeated vertex and no collinear triple. The signed-off result is in [`results/hilbert-193-500k-exhaustive.json`](results/hilbert-193-500k-exhaustive.json). Re-running the full quadratic scan takes roughly 105 minutes on the machine used for the recorded run and uses exactly four workers:

```bash
clang++ -O3 -std=c++17 -pthread verify_hilbert_exhaustive.cpp \
  -o verify_hilbert_exhaustive
./verify_hilbert_exhaustive hilbert-193-500k.jsonl
```

Both long-running programs checkpoint progress and resume only when checkpoint metadata matches the requested artifact and parameters.

## Reconstruct the finite artifact

The constructor is deterministic and safely resumable:

```bash
python3 construct_hilbert_walk.py
python3 verify_hilbert_construction.py
```

Construction logs and checkpoints live in `logs/`. The constructor and verifier use independent coordinate implementations.

## Repository map

| Path | Purpose |
|---|---|
| [`paper/erdos193.tex`](paper/erdos193.tex) | Mathematical proof manuscript |
| [`formal/Hilbert193/`](formal/Hilbert193/) | Lean 4 formalization and axiom audit |
| [`construct_hilbert_walk.py`](construct_hilbert_walk.py) | Deterministic finite-prefix constructor |
| [`verify_hilbert_construction.py`](verify_hilbert_construction.py) | Independent reconstruction and step-menu verifier |
| [`verify_hilbert_exhaustive.cpp`](verify_hilbert_exhaustive.cpp) | Exact quadratic no-three-collinear verifier |
| [`hilbert-193-500k.jsonl`](hilbert-193-500k.jsonl) | Recorded 500,000-step construction prefix |
| [`results/`](results/) | Final machine-readable verification result |
| [`design/`](design/) | Derivation notes and checks specific to the Hilbert proof |
| [`viz/`](viz/) | Public explanatory site and interactive walk |
| [`archive/`](archive/) | Superseded approaches, failed routes, and historical computations |

## Proof status and trust boundary

The repository distinguishes three forms of evidence:

- **Mathematical proof:** the argument in `paper/erdos193.tex`.
- **Kernel-checked formal proof:** the Lean theorem and its axiom audit in `formal/Hilbert193/`.
- **Finite computation:** independent reconstruction and exhaustive checking of a 500,000-step prefix.

The finite computation does not establish the infinite result. The paper and Lean development do. Remaining work is external review: checking that the formal definitions match the original problem exactly, reviewing the mathematical exposition, and obtaining community acceptance.

## Historical approaches

Earlier scale-and-rotate, affine, search, and certificate programmes are preserved under [`archive/`](archive/). They include useful finite records and exact negative results, but they are not dependencies of the current proof and should not be read as its proof path. The archive README explains the status and points to the chronological research record.

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). The manuscript source contains the mathematical bibliography and attribution details.
