#!/usr/bin/env python3
"""Independent verifier for the 3-adic reachable-secant stop report."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


AUDITOR = "OpenAI Codex"


def signpost(message: str):
    print(
        f"[{AUDITOR}][3-adic secant audit verifier] {message}",
        file=sys.stderr,
        flush=True,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "design" / "padic-reachable-secant-depth-audit-summary.json"
DEFAULT_WITNESS = ROOT / "design" / "padic-reachable-secant-depth-witness.json"
EXPECTED_SCHEMA = "padic-reachable-secant-depth-audit/v1"
EXPECTED_WITNESS_SCHEMA = "padic-reachable-secant-depth-witness/v1"

M = (
    (3, 0, 0),
    (0, 0, -3),
    (0, 3, -1),
)
N = (
    (3, 0, 0),
    (0, -1, 3),
    (0, -3, 0),
)
H = (55, 34, 18)

EXPLICIT_Q_PATTERN = (
    r"3g_y\^2-g_y\*g_z\+3g_z\^2|"
    r"3y\^2-yz\+3z\^2|"
    r"3\*y\^2-y\*z\+3\*z\^2|"
    r"3 \* y \* y - y \* z \+ 3 \* z \* z|"
    r"3\*\(3\*y\^2-y\*z\+3\*z\^2\)|"
    r"lateral_q"
)
METRIC_Q_PATTERN = (
    r"M\^T ?Q ?M ?= ?9Q|M\^TQM=9Q|M\^T Q M = 9 Q|"
    r"MᵀQM.?=.?9Q|MᵀQ M.?=.?9Q|"
    r"\[\[1, ?0, ?0\], ?\[0, ?6, ?-1\], ?\[0, ?-1, ?6\]\]|"
    r"\(\(1, ?0, ?0\), ?\(0, ?6, ?-1\), ?\(0, ?-1, ?6\)\)"
)
DEPTH_PATTERN = r"padic_depth *= *min\(|latent_padic_depth"
RANK_EDIT_PATTERN = r"min[[:space:]]*\("


REQUIRED_PHRASES = {
    "design/UNCONDITIONAL-INDUCTION-PLAN.md": (
        "Status:** research plan, not a proof",
        "For a primitive direction `g`",
        "exact Plücker contact residual and",
    ),
    "design/FAR-SECANT-BIRTH-OPERATOR.md": (
        "canonical primitive direction",
        "There is no physical deep--deep rebirth",
    ),
    "design/LATENT-REENTRY-OBSTRUCTION.md": (
        "reachable-history or far-secant theorem",
        "An integer lattice line is not yet a secant of the realized path",
    ),
    "design/padic_macrocycle_lift.py": (
        "It does not prove reachable line birth",
        "padic_depth = min(x_valuation // 2, (q_valuation - 1) // 4)",
        "birth of a latent line from a reachable legal endpoint pair",
    ),
}


def stable_hash(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_hashed_json(path: Path, expected_schema: str):
    with Path(path).open() as handle:
        value = json.load(handle)
    if value.get("schema") != expected_schema:
        raise AssertionError(f"unexpected schema in {path}")
    claimed = value.get("payload_sha256")
    payload = dict(value)
    payload.pop("payload_sha256", None)
    if stable_hash(payload) != claimed:
        raise AssertionError(f"payload hash mismatch in {path}")
    return value, payload, claimed


def git(*arguments: str, allow_empty: bool = False) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode and not (allow_empty and result.returncode == 1):
        raise RuntimeError(
            f"git {' '.join(arguments)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def grep_files(revision: str, pattern: str):
    output = git("grep", "-l", "-I", "-E", pattern, revision, "--", allow_empty=True)
    prefix = revision + ":"
    paths = []
    for line in output.splitlines():
        paths.append(line[len(prefix):] if line.startswith(prefix) else line.split(":", 1)[-1])
    return sorted(set(paths))


def history_records(pattern: str):
    commits = git(
        "log", "--all", "--reverse", "--format=%H", "-G" + pattern
    ).splitlines()
    records = []
    for commit in commits:
        metadata = git("show", "-s", "--format=%aI%x1f%s", commit).rstrip("\n")
        authored_at, subject = metadata.split("\x1f", 1)
        files = sorted(set(
            line
            for line in git(
                "show", "--format=", "--name-only", "-G" + pattern, commit, "--"
            ).splitlines()
            if line
        ))
        records.append({
            "commit": commit,
            "authored_at": authored_at,
            "subject": subject,
            "files": files,
        })
    return records


def source_at(revision: str, path: str) -> str:
    return git("show", f"{revision}:{path}")


def is_rank_candidate_context(window: str) -> bool:
    compact = "".join(window.split())
    return (
        ("q_valuation" in window or "lateral_q" in window or "q(g)" in compact)
        and ("v3" in window or "valuation" in window or "nu_3" in window)
    )


def rank_candidate_occurrences(revision: str):
    records = []
    for path in grep_files(revision, RANK_EDIT_PATTERN):
        lines = source_at(revision, path).splitlines()
        for index, line in enumerate(lines):
            if "min(" not in "".join(line.split()):
                continue
            window = "\n".join(lines[max(0, index - 2):index + 3])
            if is_rank_candidate_context(window):
                records.append({
                    "path": path,
                    "line": index + 1,
                    "text": line.strip(),
                    "context": window,
                })
    return records


def historical_rank_candidate_occurrences():
    commits = git(
        "log", "--all", "--reverse", "--format=%H", "-G" + RANK_EDIT_PATTERN
    ).splitlines()
    records = []
    seen = set()
    for commit in commits:
        diff = git(
            "show",
            "--format=",
            "--unified=2",
            "-G" + RANK_EDIT_PATTERN,
            commit,
            "--",
        ).splitlines()
        path = None
        for index, line in enumerate(diff):
            if line.startswith("+++ b/"):
                path = line[6:]
                continue
            if path is None or "min(" not in "".join(line.split()):
                continue
            context_lines = []
            for candidate in diff[max(0, index - 2):index + 3]:
                if candidate.startswith(("+++", "---", "@@")):
                    continue
                context_lines.append(
                    candidate[1:] if candidate[:1] in {"+", "-", " "} else candidate
                )
            context = "\n".join(context_lines)
            if not is_rank_candidate_context(context):
                continue
            key = (commit, path, line.lstrip("+- ").strip())
            if key in seen:
                continue
            seen.add(key)
            metadata = git(
                "show", "-s", "--format=%aI%x1f%s", commit
            ).rstrip("\n")
            authored_at, subject = metadata.split("\x1f", 1)
            records.append({
                "commit": commit,
                "authored_at": authored_at,
                "subject": subject,
                "path": path,
                "change": line[:1] if line[:1] in {"+", "-"} else "context",
                "text": line.lstrip("+- ").strip(),
                "context": context,
            })
    return records


def exact_raw_rank_occurrences(records):
    matches = []
    for record in records:
        compact = "".join(record["context"].lower().split())
        compact = compact.replace("nu_3", "v3").replace("v_3", "v3")
        compact = compact.replace("g_x", "gx")
        if "min(v3(gx),v3(q(g)))" in compact:
            matches.append(record)
    return matches


def matrix_product(left, right):
    return tuple(
        tuple(
            sum(left[row][inner] * right[inner][column] for inner in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def matrix_vector(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def transpose(matrix):
    return tuple(tuple(matrix[column][row] for column in range(3)) for row in range(3))


def scale_matrix(factor, matrix):
    return tuple(tuple(factor * value for value in row) for row in matrix)


def q(vector):
    _x, y, z = vector
    return 3 * y * y - y * z + 3 * z * z


def v3(value):
    if value == 0:
        return None
    value = abs(value)
    valuation = 0
    while value % 3 == 0:
        value //= 3
        valuation += 1
    return valuation


def content(vector):
    divisor = 0
    for coordinate in vector:
        divisor = math.gcd(divisor, abs(coordinate))
    return divisor


def primitive(vector):
    divisor = content(vector)
    if not divisor:
        raise AssertionError("zero primitive witness")
    result = tuple(coordinate // divisor for coordinate in vector)
    if next(coordinate for coordinate in result if coordinate) < 0:
        result = tuple(-coordinate for coordinate in result)
    return result


def verify_algebra(summary):
    half = Fraction(1, 2)
    q_matrix = (
        (Fraction(0), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(3), -half),
        (Fraction(0), -half, Fraction(3)),
    )
    pulled_back = matrix_product(matrix_product(transpose(M), q_matrix), M)
    if pulled_back != scale_matrix(9, q_matrix):
        raise AssertionError("independent matrix proof of q(Mg)=9q(g) failed")
    transport = summary["algebra"]["transport"]
    if transport["q_after_M_coefficients"] != [0, 0, 0, 27, -9, 27]:
        raise AssertionError("summary polynomial coefficients disagree")


def verify_source_audit(summary):
    revision = summary["audited_head"]
    git("cat-file", "-e", revision + "^{commit}")
    audit = summary["source_audit"]
    observed = {
        "explicit_q_files": grep_files(revision, EXPLICIT_Q_PATTERN),
        "invariant_metric_ancestor_files": grep_files(revision, METRIC_Q_PATTERN),
        "latent_depth_files": grep_files(revision, DEPTH_PATTERN),
    }
    for key, value in observed.items():
        if audit[key] != value:
            raise AssertionError(f"source inventory mismatch: {key}")
    expected_history = {
        "invariant_metric": history_records(METRIC_Q_PATTERN),
        "explicit_q": history_records(EXPLICIT_Q_PATTERN),
        "latent_depth": history_records(DEPTH_PATTERN),
    }
    if audit["history"] != expected_history:
        raise AssertionError("history inventory mismatch")
    assigned = []
    for group in audit["semantic_groups"].values():
        assigned.extend(group["files"])
    if sorted(assigned) != audit["explicit_q_files"] or len(assigned) != len(set(assigned)):
        raise AssertionError("semantic source partition is not exact")
    for path, phrases in REQUIRED_PHRASES.items():
        text = git("show", f"{revision}:{path}")
        for phrase in phrases:
            if phrase not in text:
                raise AssertionError(f"proof-boundary phrase missing: {path}: {phrase}")
    occurrences = rank_candidate_occurrences(revision)
    if audit["rank_candidate_occurrences"] != occurrences:
        raise AssertionError("current scalar rank occurrence inventory mismatch")
    if {record["path"] for record in occurrences} != {
        "design/padic_macrocycle_lift.py",
        "design/verify_padic_macrocycle_lift.py",
    }:
        raise AssertionError("unexpected scalar rank occurrence set")
    for record in occurrences:
        if "min(x_valuation // 2, (q_valuation - 1) // 4)" not in record["text"]:
            raise AssertionError("rank occurrence is not the weighted latent formula")
    rank_history = historical_rank_candidate_occurrences()
    if audit["rank_candidate_history"] != rank_history:
        raise AssertionError("historical scalar rank occurrence inventory mismatch")
    raw_occurrences = exact_raw_rank_occurrences(rank_history)
    if audit["exact_raw_min_formula_occurrences"] != raw_occurrences:
        raise AssertionError("raw scalar rank occurrence inventory mismatch")
    if raw_occurrences:
        raise AssertionError("raw min(v3(gx),v3(q(g))) unexpectedly occurs in history")


def verify_representation_witness(witness):
    representatives = witness["raw_representation_dependence"][
        "same_geometric_line_representatives"
    ]
    for exponent, record in enumerate(representatives):
        vector = tuple(record["vector"])
        if vector != tuple((3**exponent) * coordinate for coordinate in (1, 1, 0)):
            raise AssertionError("scaling witness vector drift")
        if record["q"] != q(vector):
            raise AssertionError("scaling witness q drift")
        if (record["v3_x"], record["v3_q"]) != (exponent, 2 * exponent + 1):
            raise AssertionError("scaling witness valuation drift")
        if record["raw_min_depth"] != exponent:
            raise AssertionError("raw depth scaling witness drift")
        if tuple(record["primitive"]) != (1, 1, 0):
            raise AssertionError("primitive representation witness drift")

    vector = (1, 1, 0)
    for inherited_scales, record in enumerate(
        witness["birth_normalized_carriage"]["records"]
    ):
        if tuple(record["exact_chord"]) != vector:
            raise AssertionError("exact carriage chord drift")
        if record["inherited_scales"] != inherited_scales:
            raise AssertionError("inherited scale index drift")
        if record["residual_x"] != 0 or record["residual_q"] != 1:
            raise AssertionError("birth-normalized residual is not constant")
        vector = matrix_vector(M, vector)

    terminology = witness["x_parallel_terminology"]
    if q(tuple(terminology["x_parallel_direction"])) != 0:
        raise AssertionError("x-parallel q exceptional channel drift")
    if q(tuple(terminology["gx_zero_example"])) != 3:
        raise AssertionError("gx-zero lateral example drift")

    difference = witness["genealogical_vs_algebraic"]
    if difference["stipulated_genealogical_depth"] != 0:
        raise AssertionError("abstract genealogical witness drift")
    if difference["maximal_algebraic_depth"] != 1:
        raise AssertionError("abstract algebraic witness drift")
    if difference["M_inverse_chord"] != [[1, 1], [0, 1], [0, 1]]:
        raise AssertionError("first inverse chord drift")
    if difference["M_inverse_squared_chord"] != [[1, 3], [0, 1], [0, 1]]:
        raise AssertionError("second inverse chord drift")


def verify_latent_witness(witness):
    records = witness["latent_positive_control"]["records"]
    if witness["latent_positive_control"]["reachable_secant"] is not False:
        raise AssertionError("latent family scope was widened")
    n_squared = matrix_product(N, N)
    a = matrix_product(M, M)
    direction = H
    previous = None
    for n, record in enumerate(records):
        if tuple(record["direction"]) != direction:
            raise AssertionError("latent direction stream drift")
        if (record["v3_x"], record["v3_q"], record["latent_padic_depth"]) != (
            2 * n,
            4 * n + 1,
            n,
        ):
            raise AssertionError("latent depth formula drift")
        if n:
            image = matrix_vector(a, direction)
            if content(image) != 81 or primitive(image) != previous:
                raise AssertionError("latent primitive countdown drift")
            if record["forward_M_squared_content"] != 81:
                raise AssertionError("latent recorded content drift")
            if tuple(record["forward_primitive_direction"]) != previous:
                raise AssertionError("latent recorded successor drift")
        previous = direction
        direction = matrix_vector(n_squared, direction)


def verify_existing_macrocycle_claim(summary):
    path = ROOT / "design" / "padic-macrocycle-lift-summary.json"
    with path.open() as handle:
        certificate = json.load(handle)
    claimed = certificate["payload_sha256"]
    mathematical = dict(certificate)
    mathematical.pop("payload_sha256")
    if stable_hash(mathematical) != claimed:
        raise AssertionError("existing macrocycle payload hash mismatch")
    if certificate["estimate"]["total_state_edges"] != 66_429:
        raise AssertionError("existing macrocycle edge count drift")
    if certificate["latent_positive_control"]["depth"] != 16:
        raise AssertionError("existing latent regression depth drift")
    ledger = {record["id"]: record for record in summary["claim_ledger"]}
    if ledger["C8"]["classification"] != "EXACT FINITE":
        raise AssertionError("finite macrocycle claim mislabeled")


def verify(summary_path: Path, witness_path: Path):
    signpost("loading hashed summary and witness")
    _summary_file, summary, summary_hash = load_hashed_json(
        summary_path, EXPECTED_SCHEMA
    )
    _witness_file, witness, witness_hash = load_hashed_json(
        witness_path, EXPECTED_WITNESS_SCHEMA
    )
    if summary.get("auditor") != AUDITOR or witness.get("auditor") != AUDITOR:
        raise AssertionError("artifacts lack explicit OpenAI Codex signposting")
    if summary["witness"]["payload_sha256"] != witness_hash:
        raise AssertionError("summary does not commit to witness payload")
    if summary["stop_condition"]["number"] != 6:
        raise AssertionError("unexpected stop condition")
    if summary["stop_condition"]["classification"] != "PROVED":
        raise AssertionError("stop condition is not claim-ledger classified")
    signpost("checking exact quadratic identity")
    verify_algebra(summary)
    signpost("checking current tree and complete history inventory")
    verify_source_audit(summary)
    signpost("checking representation counterexamples")
    verify_representation_witness(witness)
    signpost("checking latent-family countdown")
    verify_latent_witness(witness)
    signpost("checking existing finite macrocycle commitment")
    verify_existing_macrocycle_claim(summary)
    signpost("verification complete")
    return {
        "auditor": AUDITOR,
        "status": "verified",
        "audited_head": summary["audited_head"],
        "stop_condition": 6,
        "summary_payload_sha256": summary_hash,
        "witness_payload_sha256": witness_hash,
        "explicit_q_files": len(summary["source_audit"]["explicit_q_files"]),
        "history_q_commits": len(summary["source_audit"]["history"]["explicit_q"]),
        "claims": len(summary["claim_ledger"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    args = parser.parse_args()
    print(json.dumps(verify(args.summary, args.witness), sort_keys=True))


if __name__ == "__main__":
    main()
