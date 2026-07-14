# erdos-193 — no-three-in-line walks in ℤ³

**Can an infinite walk on the integer grid, with steps from a fixed finite menu, avoid
ever placing three of its points on a common straight line?**
That is [Erdős Problem #193](https://www.erdosproblems.com/193) (Gerver–Ramsey, open
since 1979). This repository is a computational attack on it: a construction that builds
record walks, and a certificate programme working toward a proof that they can run forever.

🌐 **Visual introduction:** [erdos-193.q5m.io](https://erdos-193.q5m.io) — the proof
strategy in six diagrams, and an interactive demo with real coordinates.

## Headline results

| Result | Status |
|---|---|
| **28,271-step walk, no 3 collinear** (124-move menu) | verified + SHA-256 certified, `amplified-193-28271.txt` |
| Exact maxima for small menus: **20** (±e₁,±e₂,±e₃), 14, 7; **3** in 2D | proven by exhaustive search |
| Universal availability: every one of 78,728 arithmetic states can steer in all 13 mod-3 directions | proven by exhaustion (1.22B transitions) |
| Fatal birth-mass **flat ≈ 32% across levels** → construction scales | measured, levels 3–6 |
| Symmetric Local-Lemma criterion closes at **H = 14** (corrected live-law constants) | certified constants; semantic repair of the chain in progress |
| Five earlier proof strategies refuted with quantitative tombstones | documented in `REPORT.md` |

## Verify our record walk yourself (30 seconds)

No trust required — the verifier is standalone (~80 lines, stdlib only):

```bash
python3 verify_walk.py amplified-193-28271.txt
# VERIFIED: 28271 steps, 28272 vertices, no repeated vertex, no 3 collinear
# sha256(steps): dec7e762386f1eac2eff6bccc3307a354ab79662f5770e55d88c074a57600f56
```

Works on any `amplified-*.txt` walk file in the repo.

## Reproduce things

Everything is deterministic (fixed seeds). [PyPy](https://pypy.org) is ~10–50× faster
than CPython here and strongly recommended for anything marked *(slow)*.

```bash
# sanity: the scientific controls must pass
python3 erdos193.py --controls

# rebuild the record walk from scratch (deterministic; hours under PyPy) (slow)
pypy3 amplify_rich.py 193 20 25000 3

# search random substitutions (the historical baseline the construction beat)
python3 erdos193.py --seed 1 --trials 100000 --output /tmp/demo.json

# exhaustive small-menu maxima (proves the "exactly 20" result)
pypy3 bnb193.py 2000000

# Stage-4 certificate computations (slow)
pypy3 step1_connectors4.py        # 7.1M legal connector words + closure
pypy3 np_hc_sidepass.py           # 1.22B transitions: availability + climb law
pypy3 np_hc_gpass.py              # successor-class tables (1.2 GB, local)
python3 step4_certify.py          # certified q̄ and LLL closure scan (needs numpy)
```

## What's in the repo

| File | What it is |
|---|---|
| `verify_walk.py` | **Start here** — standalone third-party verifier for any walk file |
| `amplified-*.txt` | Verified walk files (28,271 / 8,292 / …), plain step-index lists |
| `amplify_rich.py`, `amplify193.py` | The construction: enlarge by M, stitch anchor gaps, verify exactly |
| `search193.py`, `erdos193.py` | Exact-arithmetic core + the substitution-search baseline with controls |
| `bnb193.py`, `beam193.py`, `max2d_flat.py` | Exhaustive & randomized searches (exact maxima, 2D bounds) |
| `step1_connectors4.py`, `np_hc*.py`, `step4_certify*.py` | The certificate programme (Stage 4): word layer, state space, certified constants |
| `analyze_*.py`, `measure_dependency.py`, `provenance193.py` | Measurements: κ₃ spectra, divergence stratification, dependency structure |
| `design/` | Machine-generated design & hostile-review documents for the certificate |
| `results/`, `collar_multiplicity4.json`, `wsw_sameword.pkl` | Data artifacts (large binaries are local-only, rebuildable) |
| `viz/` | The website ([erdos-193.q5m.io](https://erdos-193.q5m.io)) |
| `REPORT.md` | **The full research log** — every result, refutation and correction, in order |

## State of the proof programme (honest version)

The construction works and scales (flat fatal-mass is the load-bearing measurement).
The certificate has certified constants and a closing criterion, **but is not a proof**:
the remaining gaps are the semantic containment theorem (in progress), the
coverage/completeness proof for birth events, the dependency bound as a theorem, and the
finite-to-infinite compactness lift. Details and status in `REPORT.md`. Independent
scrutiny is welcome — that's what the certificates are for.

## Background

- [Erdős Problem #193](https://www.erdosproblems.com/193) — problem statement and history
- Gerver & Ramsey, *On certain sequences of lattice points* (1979)
- Everything here is exact integer arithmetic — no floating point in any decision path.

---
Made in Canada 🇨🇦 by [ekalvi](https://github.com/ekalvi) · part of the [q5m](https://www.q5m.ai) family
