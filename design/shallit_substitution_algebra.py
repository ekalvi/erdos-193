#!/usr/bin/env python3
"""Small exact algebra probes for Shallit's cyclic five-letter substitution.

Results are an algebraic diagnostic, NOT an infinite no-collinearity proof.
One single-core task checkpoints atomically on completion; compatible completed
results are reused on restart. The bounded 70^3 residue test takes seconds.
Run with: uv run --with sympy python design/shallit_substitution_algebra.py
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import signal
import time

import sympy as s
from unit_step_dimension_probe import atomic_json, log_event

IMAGE = tuple(map(int, "01213101314310"))


def compute():
    x, t = s.symbols("x t")
    counts = [IMAGE.count(j) for j in range(5)]
    matrix = s.Matrix(5, 5, lambda i, j: counts[(i - j) % 5])
    f = sum(counts[j] * x**j for j in range(5))
    phi = s.cyclotomic_poly(5, x)
    roots = [r for r in range(2, 421) if pow(r, 5, 421) == 1
             and sum(counts[j] * pow(r, j, 421) for j in range(5)) % 421 == 0]
    assert len(roots) == 1
    root = roots[0]
    prefixes = []
    for letter in range(5):
        prefix = [0] * 5
        for offset in range(14):
            residue = sum(prefix[j] * pow(root, j, 421) for j in range(5)) % 421
            prefixes.append(dict(letter=letter, offset=offset, counts=prefix.copy(), residue=residue))
            prefix[(IMAGE[offset] + letter) % 5] += 1
    relations = []
    for a in prefixes:
        for b in prefixes:
            for c in prefixes:
                if (a["offset"] - 2 * b["offset"] + c["offset"]) % 14 != 0:
                    continue
                if (a["residue"] - 2 * b["residue"] + c["residue"]) % 421 != 0:
                    continue
                diff = s.Matrix([u - 2 * v + w for u, v, w in zip(a["counts"], b["counts"], c["counts"])])
                parent = matrix.inv() * diff
                assert all(v.q == 1 for v in parent)
                if diff != s.zeros(5, 1):
                    relations.append(dict(boundaries=[[v["letter"], v["offset"]] for v in (a, b, c)],
                                          correction=list(map(int, parent))))
    return dict(image0="".join(map(str, IMAGE)), incidence_columns="Parikh vectors of images of 0 through 4",
        counts=counts, matrix=[list(map(int, matrix.row(j))) for j in range(5)], determinant=int(matrix.det()),
        cyclotomic_eigenvalue_polynomial=str(s.resultant(phi, t - f, x)),
        cyclotomic_norm=int(s.resultant(phi, f, x)), residue_prime=421, root_mod_prime=root,
        singular_values_squared=[14**2, "21-2*sqrt(5)", "21-2*sqrt(5)", "21+2*sqrt(5)", "21+2*sqrt(5)"],
        nonzero_boundary_corrections=relations,
        scope="Exact substitution algebra and boundary diagnostic only; not a proof of avoidance.")


def main():
    state = Path(".checkpoint-shallit-algebra")
    state.mkdir(exist_ok=True)
    identity = dict(code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), schema=1)
    checkpoint, output, log = state / "state.json", Path("results/shallit-substitution-algebra.json"), state / "run.jsonl"
    if checkpoint.exists():
        saved = json.loads(checkpoint.read_text())
        if saved.get("identity") != identity:
            raise SystemExit("incompatible checkpoint, use a new state directory")
        result = saved["result"]
        digest = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
        if saved.get("sha256") != digest:
            raise SystemExit("corrupt checkpoint")
        log_event(log, "resume_complete", identity=identity, threads=1, checkpoint=str(checkpoint))
    else:
        interrupted = []
        def stop(signum, _frame):
            interrupted.append(signum)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, stop)
        log_event(log, "start", identity=identity, threads=1, completed=0, total=1, eta_seconds=5,
                  checkpoint=str(checkpoint))
        started = time.monotonic()
        try:
            result = compute()
            digest = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
            atomic_json(checkpoint, dict(identity=identity, result=result, sha256=digest))
            log_event(log, "checkpoint", completed=1, total=1, elapsed_seconds=time.monotonic() - started,
                      checkpoint=str(checkpoint), interrupted=bool(interrupted))
        except Exception as exc:
            log_event(log, "error", error=repr(exc))
            raise
    atomic_json(output, dict(identity=identity, **result))
    log_event(log, "complete", output=str(output), determinant=result["determinant"],
              nonzero_corrections=len(result["nonzero_boundary_corrections"]))


if __name__ == "__main__":
    main()
