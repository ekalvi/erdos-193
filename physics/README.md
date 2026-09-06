# Exploratory physics applications

This directory investigates whether the Gaussian-lattice construction behind the
Erdős Problem 193 result has useful physics translations.

> None of these experiments is part of the unconditional proof. Numerical findings are
> finite evidence, and proposed applications are exploratory.

## Conclusions

1. Generic physics diagnostics find deterministic transverse diffusion-like scaling,
   ballistic lift height, strong temporal correlations, and poor global angular clearance.
2. A phase-modulated coined quantum walk is interesting but belongs to an established
   literature on Thue--Morse and morphic quantum drives. Only the exact four-phase instance
   was not located in the preliminary novelty audit.
3. The most direct use of no-three-collinear geometry is a Pauli-control corollary:
   aggregate generators of every two adjacent nonempty blocks do not commute and, if
   independently addressable, generate `su(2)`. Its normalized margin decays with scale.

Start with:

- [`QUANTUM-WALK-FINDINGS.md`](QUANTUM-WALK-FINDINGS.md) — synthesis of the quantum-walk experiments;
- [`QUANTUM-WALK-NOVELTY-AUDIT.md`](QUANTUM-WALK-NOVELTY-AUDIT.md) — prior-art review and claim limits;
- [`PAULI-NONCOMMUTATIVITY.md`](PAULI-NONCOMMUTATIVITY.md) — direct non-collinearity consequence;
- [`RESULTS.md`](RESULTS.md) — generic finite physics diagnostics.

## Reproduce

All scripts use only the Python standard library and one process. They write atomic
checkpoints and timestamped JSONL logs under `logs/`; rerunning an identical command resumes
validated work.

```bash
# Generic finite-prefix diagnostics
python3 physics/analyze_gaussian_walk.py

# Twelve coined-walk variants through 4,096 steps
python3 physics/coined_quantum_walk.py

# Independent direct validation through 8,192 steps
python3 physics/coined_quantum_walk.py \
  --steps 8192 \
  --models homogeneous gaussian_time_phase gaussian_space_phase \
  --checkpoint-interval 512 \
  --checkpoint logs/coined-quantum-walk-validation.ckpt.json \
  --wave-checkpoint logs/coined-quantum-walk-validation.wave.pkl \
  --log logs/coined-quantum-walk-validation.log \
  --output results/coined-quantum-walk-validation.json \
  --report physics/QUANTUM-WALK-VALIDATION.md

# Exact dyadic block recursion plus sampled momentum integration through 2^30
python3 physics/quantum_walk_rg.py \
  --max-level 30 --samples 131072 --checkpoint-interval 2048

# Independent momentum-quadrature replication
python3 physics/quantum_walk_rg.py \
  --max-level 30 --samples 65536 --seed 194 --checkpoint-interval 2048 \
  --checkpoint logs/quantum-walk-rg-replication.ckpt.json \
  --log logs/quantum-walk-rg-replication.log \
  --output results/quantum-walk-rg-replication.json \
  --report physics/QUANTUM-WALK-RG-REPLICATION.md

# Pauli block-commutator margins
python3 physics/analyze_pauli_noncommutativity.py
```

The completed JSON artifacts are in `results/`. Logs and checkpoints are separate from
those final exploratory artifacts, as required for reproducibility and interruption-safe
runs. Wavefunction pickle checkpoints are temporary and are deleted when a model finishes;
never load an untrusted pickle.
