# Erdős Problem 193: a finite-step walk in ℤ³ with no three collinear vertices

This repository gives an explicit negative answer to [Erdős Problem 193](https://www.erdosproblems.com/193).

There are a finite set $S \subseteq \mathbb Z^3$ and an infinite sequence $P : \mathbb N \to \mathbb Z^3$ such that every difference $P_{n+1}-P_n$ lies in $S$, while no three distinct terms of $P$ are collinear.

The construction is unconditional and formalized in Lean 4. External mathematical review and community acceptance are still pending.

- **Visual explanation:** [erdos-193.q5m.ai](https://erdos-193.q5m.ai)
- **Guided explanation:** [`viz/learn.html`](viz/learn.html)
- **Production deployment:** [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- **Proof manuscript:** [`paper/erdos193.pdf`](paper/erdos193.pdf)
- **Lean theorem:** `Hilbert193.erdos193_unconditional`
- **Formal proof guide:** [`formal/Hilbert193/README.md`](formal/Hilbert193/README.md)

## Result at a glance

The proof uses a nested discrete Hilbert path $H : \mathbb N \to \mathbb N^2$.

1. Every Hilbert index carries one of four terminal orientation states.
2. Matching Gray-code and height tags encode that state without discarding points.
3. The same-state two-adic pair law thereby extends to every pair of tagged vertices.
4. Applying the all-pairs law to two adjacent chords and their sum rules out a collinear triple.
5. Hilbert adjacency bounds tagged planar steps by 3 and height steps between 1 and 7.

The Lean development checks this complete infinite argument. The standalone Python demo independently checks finite prefixes; finite computation is not a premise of the theorem.

## Verify the formal proof

The Lean package pins its Lean and Mathlib revisions.

```bash
cd formal/Hilbert193
lake build
lake env lean Hilbert193/AxiomAudit.lean
```

The axiom audit reports only Mathlib's standard `propext`, `Classical.choice`, and `Quot.sound`. No project-specific axioms or unfinished placeholders are used by the main theorem.

The load-bearing modules are:

1. [`Basic.lean`](formal/Hilbert193/Hilbert193/Basic.lean) — shared elementary definitions.
2. [`Transducer.lean`](formal/Hilbert193/Hilbert193/Transducer.lean) — digits, orientations, and the Hilbert transducer.
3. [`Valuation.lean`](formal/Hilbert193/Hilbert193/Valuation.lean) — the two-adic planar chord invariant.
4. [`PairLaw.lean`](formal/Hilbert193/Hilbert193/PairLaw.lean) — the same-terminal-state pair law and lifting obstruction.
5. [`Construction.lean`](formal/Hilbert193/Hilbert193/Construction.lean) — state tags, all-pairs law, and exclusion of collinear triples.
6. [`Continuity.lean`](formal/Hilbert193/Hilbert193/Continuity.lean) — Hilbert adjacency, tagged finite step menu, and final theorem.
7. [`AxiomAudit.lean`](formal/Hilbert193/Hilbert193/AxiomAudit.lean) — kernel dependency report.

## Archived finite artifact from the earlier selector construction

[`hilbert-193-500k.jsonl`](hilbert-193-500k.jsonl) contains 500,001 vertices from the earlier bounded-gap selector construction. It remains independently inspectable evidence for that valid alternative witness, but it is not an implementation of the tagged walk now used in the manuscript and Lean theorem. The standalone verifier reconstructs every selected index and checks its 16-vector step menu:

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
