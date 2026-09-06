#!/usr/bin/env python3
"""Independently validate the dimension-obstruction certificates and prefix checker.

Completed validation tasks are atomically checkpointed under an ignored state
directory named by code/config identity. Restart resumes completed tasks. All
work and subprocesses use one core. SIGINT/SIGTERM stop after the current small
validation task. The C++ interruption test also checks its own resume behavior.
"""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import signal
import subprocess
import time

from unit_step_dimension_probe import atomic_json, log_event, first_collision

ROOT = Path(__file__).resolve().parents[1]
STOP = False


def no_abelian_square(word):
    for length in range(1, len(word) // 2 + 1):
        for start in range(len(word) - 2 * length + 1):
            if Counter(word[start:start+length]) == Counter(word[start+length:start+2*length]):
                return False
    return True


def lower_bound():
    assert all(not no_abelian_square(w) for w in itertools.product(range(3), repeat=8))
    for word in ("0102010", "0102101", "0121012"):
        assert no_abelian_square(word)


def codings():
    data = json.loads((ROOT / "results/unit-step-dimension-probe.json").read_text())
    expected_hash = hashlib.sha256((ROOT / "design/unit_step_dimension_probe.py").read_bytes()).hexdigest()
    assert data["identity"]["code_sha256"] == expected_hash
    # Independent state implementation via even/odd bit masks, only 86 vertices.
    states = [((n & 0x55555555).bit_count() - (n & 0xAAAAAAAA).bit_count()) % 4 for n in range(86)]
    pairs = [tuple(p) for p in data["identity"]["pairs"]]
    source = [pairs.index((a, b)) for a, b in zip(states, states[1:])]
    seen = {4: set(), 5: set()}
    for row in data["codings"]:
        k, coding, hit = row["alphabet"], row["coding"], row["collision"]
        assert len(coding) == 8 and coding[0] == 0
        for i in range(1, 8):
            assert 0 <= coding[i] <= 1 + max(coding[:i])
        assert set(coding) == set(range(k))
        assert tuple(coding) not in seen[k]
        seen[k].add(tuple(coding))
        a, b, c = hit["indices"]
        assert 0 <= a < b < c <= 85
        left = Counter(coding[x] for x in source[a:b])
        right = Counter(coding[x] for x in source[b:c])
        assert all((c-b) * left[j] == (b-a) * right[j] for j in range(k))
        assert [left[j] for j in range(k)] == hit["left_counts"]
        assert [right[j] for j in range(k)] == hit["right_counts"]
        # Stronger than needed: every stored witness is an ordinary abelian square.
        assert b-a == c-b
    # Independent Stirling recurrence counts all unlabeled partitions.
    stirling = {(0, 0): 1}
    for n in range(1, 9):
        for k in range(1, n+1):
            stirling[n, k] = k * stirling.get((n-1, k), 0) + stirling.get((n-1, k-1), 0)
    assert len(seen[4]) == stirling[8, 4] == 1701
    assert len(seen[5]) == stirling[8, 5] == 1050


def collision_algorithm():
    # Check the geometric algorithm against direct all-triples cross multiplication.
    for word in itertools.product(range(3), repeat=6):
        points = [[word[:n].count(j) for j in range(3)] for n in range(7)]
        bad = any(all((c-b) * (points[b][j]-points[a][j]) == (b-a) * (points[c][j]-points[b][j])
                      for j in range(3)) for a, b, c in itertools.combinations(range(7), 3))
        assert (first_collision(word, 3) is not None) == bad


def cpp_test(binary, state):
    def run(name, image, k, steps):
        target = state / name
        output = target / "output.json"
        command = [str(binary), "--image0", image, "--alphabet", str(k), "--steps", str(steps),
                   "--state-dir", str(target), "--output", str(output)]
        completed = subprocess.run(command, capture_output=True, text=True)
        assert completed.returncode in (0, 1), completed.stderr
        return json.loads(output.read_text())
    bad = run("bad", "012", 3, 8)
    assert bad["status"] == "counterexample"
    # Independently generate the cyclic substitution word and recheck the witness.
    image = (0, 1, 2)
    word = (0,)
    while len(word) < 8:
        word = tuple((letter + offset) % 3 for letter in word for offset in image)
    a, b, c = bad["indices"]
    left, right = Counter(word[a:b]), Counter(word[b:c])
    assert all((c-b) * left[j] == (b-a) * right[j] for j in range(3))
    good = run("small-good", "01213101314310", 5, 196)
    assert good["status"] == "finite_prefix_pass" and good["chords_checked"] == 196*197//2
    assert run("small-good", "01213101314310", 5, 196) == good


def cpp_resume(binary, state):
    target = state / "interrupt"
    output = target / "output.json"
    command = [str(binary), "--steps", "2744", "--state-dir", str(target), "--output", str(output)]
    # Do not disturb a completed interruption test when resuming this validator.
    if not output.exists():
        with (state / "cpp-interrupt.stderr").open("a") as errors:
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=errors)
            time.sleep(0.1)
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
            assert process.wait(timeout=30) in (0, 130)
            assert (target / "checkpoint.txt").exists()
            completed = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=errors, timeout=30)
            assert completed.returncode == 0
    result = json.loads(output.read_text())
    assert result["status"] == "finite_prefix_pass" and result["chords_checked"] == 2744*2745//2
    events = [json.loads(line)["event"] for line in (target / "run.jsonl").read_text().splitlines()]
    assert "interrupted" in events and "resume" in events and events[-1] == "complete"
    # An incompatible parameter must be rejected, not silently reused.
    wrong = command.copy()
    wrong[2] = "2745"
    completed = subprocess.run(wrong, capture_output=True, text=True, timeout=10)
    assert completed.returncode == 2 and "incompatible" in completed.stderr


def expected_algebra_corrections():
    """Reconstruct all integral nonzero corrections, without the producer's sieve.

    Use exact Gaussian elimination rather than SymPy or the 421-root filter.
    The bounded 70^3 enumeration is one atomic, resumable validation task.
    """
    image = tuple(map(int, "01213101314310"))
    counts = [image.count(j) for j in range(5)]
    matrix = [[counts[(i-j) % 5] for j in range(5)] for i in range(5)]
    augmented = [[Fraction(x) for x in row] + [Fraction(i == j) for j in range(5)]
                 for i, row in enumerate(matrix)]
    determinant = Fraction(1)
    for column in range(5):
        pivot = next(i for i in range(column, 5) if augmented[i][column])
        if pivot != column:
            augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
            determinant *= -1
        scale = augmented[column][column]
        determinant *= scale
        augmented[column] = [x / scale for x in augmented[column]]
        for i in range(5):
            if i != column:
                scale = augmented[i][column]
                augmented[i] = [x - scale*y for x, y in zip(augmented[i], augmented[column])]
    assert determinant == 5894
    adjugate = [[x * determinant for x in row[5:]] for row in augmented]
    assert all(x.denominator == 1 for row in adjugate for x in row)
    adjugate = [[int(x) for x in row] for row in adjugate]
    determinant = int(determinant)
    prefixes = []
    for letter in range(5):
        for offset in range(14):
            prefix = [(letter + c) % 5 for c in image[:offset]]
            prefixes.append(((letter, offset), tuple(prefix.count(j) for j in range(5))))
    expected = set()
    for a, b, c in itertools.product(prefixes, repeat=3):
        vector = tuple(x - 2*y + z for x, y, z in zip(a[1], b[1], c[1]))
        # Every incidence column sums to 14, so this is a necessary condition.
        if not any(vector) or sum(vector) % 14:
            continue
        numerators = [sum(x*y for x, y in zip(row, vector)) for row in adjugate]
        if all(x % determinant == 0 for x in numerators):
            expected.add(((a[0], b[0], c[0]), tuple(x // determinant for x in numerators)))
    assert len(expected) == 170
    return matrix, determinant, expected


def validate_algebra(data, expected):
    matrix, determinant, rows = expected
    assert data["image0"] == "01213101314310"
    assert data["matrix"] == matrix
    assert data["determinant"] == determinant
    saved = data["nonzero_boundary_corrections"]
    assert len(saved) == len(rows), "incomplete boundary-correction list"
    seen = set()
    for item in saved:
        boundaries = tuple(tuple(pair) for pair in item["boundaries"])
        correction = tuple(item["correction"])
        assert len(boundaries) == 3 and all(len(pair) == 2 for pair in boundaries)
        assert all(type(letter) is int and 0 <= letter < 5 and
                   type(offset) is int and 0 <= offset < 14 for letter, offset in boundaries)
        assert len(correction) == 5 and all(type(x) is int for x in correction)
        key = (boundaries, correction)
        assert key not in seen, "duplicate boundary correction"
        seen.add(key)
    assert seen == rows, "boundary-correction set differs from independent reconstruction"


def algebra():
    data = json.loads((ROOT / "results/shallit-substitution-algebra.json").read_text())
    expected = expected_algebra_corrections()
    validate_algebra(data, expected)
    saved = data["nonzero_boundary_corrections"]
    altered = dict(saved[0], correction=[saved[0]["correction"][0] + 1,
                                       *saved[0]["correction"][1:]])
    mutations = {"empty": [], "truncated": saved[:-1],
                 "duplicate": [*saved[:-1], saved[0]], "altered": [altered, *saved[1:]]}
    for name, rows in mutations.items():
        try:
            validate_algebra(dict(data, nonzero_boundary_corrections=rows), expected)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"accepted {name} boundary-correction certificate")
    return dict(nonzero_boundary_corrections=len(expected[2]), rejected_mutations=list(mutations))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    binary = args.binary.resolve()
    sources = [Path(__file__), ROOT / "design/unit_step_dimension_probe.py", ROOT / "design/shallit_substitution_algebra.py",
               ROOT / "design/verify_unit_step_prefix.cpp", ROOT / "results/unit-step-dimension-probe.json",
               ROOT / "results/shallit-substitution-algebra.json", binary]
    identity = {str(path.name): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:16]
    state = ROOT / (".checkpoint-unit-step-tests-" + key)
    state.mkdir(exist_ok=True)
    checkpoint, log = state / "state.json", state / "run.jsonl"
    saved = json.loads(checkpoint.read_text()) if checkpoint.exists() else dict(identity=identity, completed=[])
    assert saved["identity"] == identity
    tasks = {"ternary_lower_bound": lower_bound, "all_coding_witnesses": codings,
             "collision_algorithm": collision_algorithm, "cpp_known_cases": lambda: cpp_test(binary, state),
             "cpp_interrupt_resume_reject": lambda: cpp_resume(binary, state), "algebra_corrections": algebra}
    assert set(saved["completed"]) <= tasks.keys()
    def stop(_signum, _frame):
        global STOP
        STOP = True
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, stop)
    log_event(log, "resume" if saved["completed"] else "start", identity=identity, threads=1,
              completed=len(saved["completed"]), total=len(tasks), checkpoint=str(checkpoint))
    started = time.monotonic()
    for name, task in tasks.items():
        if name in saved["completed"]:
            continue
        if STOP:
            log_event(log, "interrupted", completed=len(saved["completed"]))
            return 130
        try:
            details = task()
        except Exception as exc:
            log_event(log, "error", task=name, error=repr(exc))
            raise
        saved["completed"].append(name)
        atomic_json(checkpoint, saved)
        log_event(log, "progress", task=name, completed=len(saved["completed"]), total=len(tasks),
                  elapsed_seconds=time.monotonic()-started, checkpoint=str(checkpoint), details=details)
    log_event(log, "complete", tests=len(tasks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
