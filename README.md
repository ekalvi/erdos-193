# erdos-193 — collinear-triple-free walks in Z³

Computational programme around Problem #193: **does there exist an infinite walk
in Z³, with steps from a finite set, no three of whose vertices are collinear?**
(Gerver–Ramsey showed collinear counts can be bounded in Z³, and proved the
analogous 2D statement is false; full avoidance of 3 collinear points is open.)

All arithmetic is exact-integer (cross products; no floats in any decision).
See **[REPORT.md](REPORT.md)** for the consolidated findings and next steps.

## Headline results (2026-07-11)

- **Exhaustively proven maxima** (finite theorems, modulo code correctness):
  the longest triple-free walk with steps ±e₁,±e₂,±e₃ is **exactly 20**;
  with {e₁,e₂,e₃,(1,1,1)} exactly 14; tetrahedral steps exactly 7.
  In 2D with ±e₁,±e₂ the maximum is exactly **3**.
- **Random primitive substitutions cap out early**: best safe prefixes 27 / 24 /
  39 / 46 (4-letter r2 / 4-letter r3 / 5-letter / 6-letter) over ~12.8M
  candidates — while a *freely chosen* walk on the same 4 steps reaches **226**.
  The obstruction is combinatorial repetitiveness, not geometry.
- **Pattern B is universal and forced**: for any primitive substitution,
  Perron–Frobenius alignment makes all long return-word displacements
  asymptotically parallel (normalized determinants δ_m → 0 at rate governed by
  |λ₂|/λ₁; verified numerically). Hence no primitive substitution fixed point
  can maintain a uniformly full-rank return structure — that search class is
  closed off.
- **Imbricated (self-similar under an expanding integer matrix M) walks**:
  the displacement dynamics is M itself, so equal-modulus spectra with an
  irrational rotation evade the Perron collapse. With
  M = diag(2, companion(λ²+λ+4)) (complex pair of modulus 2, cos θ = −1/4),
  ~276 random menus already beat all 5.15M abelian 4-letter candidates
  (30 vs 27). Structural fact discovered en route: **no letter can ever repeat
  adjacently** in a valid imbricated word (anchors 0, D, 2D are collinear), so
  the construction is forced into square-free words.

## Files

| File | Purpose |
|---|---|
| `search193.py` | Original exact search: substitution fixed points, first collinear triple, return words, ranks |
| `erdos193.py` | Staged/sharded/checkpointed searcher + scientific controls + verification |
| `bnb193.py` | Exhaustive / budgeted DFS for the longest triple-free walk on a fixed step menu |
| `beam193.py` | Randomized probes (beam + randomized-restart DFS) to test ceiling-vs-artifact |
| `imbricate193.py` | Imbricated construction: tile fabrication (abelian solver + triple-free ordering), expansion matrices |
| `imbricate_seam.py` | Seam-aware tile assignment: pools, clearance ranking, occurring-pair closure |
| `results/*.json` | Shard checkpoints: top-100 candidates with substitutions, steps, disqualifiers, return profiles, SHA-256 word hashes |
| `REPORT.md` | Consolidated findings, proofs-vs-evidence accounting, next steps |

## Reproduce

```bash
python3 erdos193.py --controls            # scientific controls (must pass)
python3 erdos193.py --seed 193000000 --trials 100000 --output results/demo.json
python3 bnb193.py 2000000                 # exhaustive maxima for small menus
python3 beam193.py 5 20                   # randomized ceiling probes
python3 imbricate_seam.py 100             # seam-aware imbricated search
```

Python 3.9+, stdlib only.
