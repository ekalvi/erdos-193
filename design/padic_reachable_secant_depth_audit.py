#!/usr/bin/env python3
"""Hostile source/algebra audit of the proposed 3-adic secant depth.

The audit deliberately stops before a guarded L5 -> L6 birth census.  It proves
that the repository's only scalar q-depth is a positive control for one
abstract carried-line family, not a reachable-newborn rank or a transition
lemma.  All arithmetic is exact and all repository-history queries are pinned
to the audited Git object.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import sys
import time


AUDITOR = "OpenAI Codex"
SCHEMA = "padic-reachable-secant-depth-audit/v1"
WITNESS_SCHEMA = "padic-reachable-secant-depth-witness/v1"
CHECKPOINT_SCHEMA = "padic-reachable-secant-depth-checkpoint/v1"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "design" / "padic-reachable-secant-depth-audit-summary.json"
DEFAULT_WITNESS = ROOT / "design" / "padic-reachable-secant-depth-witness.json"
DEFAULT_CHECKPOINT = Path("/tmp/padic-reachable-secant-depth-audit-checkpoint.json")

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


SEMANTIC_GROUPS = {
    "guarded_finite_endpoint_chords": {
        "representation": (
            "q is evaluated on the exact endpoint difference because the cone "
            "equation is homogeneous; canonical primitive direction and moment "
            "are stored when a line key is needed"
        ),
        "domain": (
            "fixed finite guarded L5/L6 point-pair, old-new, and same-word "
            "new-new scans; not an all-history birth theorem"
        ),
        "files": [
            "design/GUARDED-L5-L6-TRANSITION.md",
            "design/guarded_l5_l6_common.py",
            "design/guarded_l5_to_l6.py",
            "design/lattice-T-projective-spectrum-census-summary.json",
            "design/lattice_t_l5_cone_guard_audit.py",
            "design/lattice_t_l6_cone_birth_guard.py",
            "design/lattice_t_l6_cone_guard_audit.py",
            "design/lattice_t_l6_cone_guard_pin_report.py",
            "design/lattice_t_projective_spectrum_census.py",
            "design/lattice_t_projective_spectrum_diagnostic.py",
        ],
    },
    "abstract_holonomy_or_reveal_descriptors": {
        "representation": (
            "canonical primitive rational reveal/contact direction derived from "
            "a fixed point or pulled-back candidate; not generally an endpoint chord"
        ),
        "domain": (
            "finite affine holonomy and role-first diagnostics; physical secant "
            "birth, global legality, or repeatability is explicitly not proved"
        ),
        "files": [
            "design/lattice_t_role_first_holonomy_reachability.py",
            "design/lattice_t_role_first_l5_range_merge.py",
            "design/lattice_t_short_return_holonomy.py",
        ],
    },
    "abstract_carried_line_obstructions": {
        "representation": (
            "canonical primitive affine-line direction g together with the "
            "Pluecker moment; g_n is not an exact endpoint difference"
        ),
        "domain": (
            "integer lattice lines and fixed-policy carried/silent-returning "
            "families; reachability as a secant of two placed points is not proved"
        ),
        "files": [
            "design/LATENT-REENTRY-OBSTRUCTION.md",
            "design/nonx-cycle-invariant-certificate-summary.json",
            "design/nonx-latent-reentry-certificate-summary.json",
            "design/nonx_cycle_invariant_certificate.py",
            "design/nonx_latent_reentry_certificate.py",
        ],
    },
    "primitive_pluecker_operator_and_plan": {
        "representation": (
            "canonical primitive direction g and exact Pluecker moment mu; "
            "unnormalized pairs are retained only during symbolic transport"
        ),
        "domain": (
            "exact general line-token operators plus an explicitly open proposal "
            "for policy-reachable newborns, carried lines, and cursor imports"
        ),
        "files": [
            "design/FAR-SECANT-BIRTH-OPERATOR.md",
            "design/FAR-SECANT-RANK-LEMMA.md",
            "design/GHOST-LANGUAGE-AUTOMATON.md",
            "design/ORDERED-PATH-SAFETY-GATE.md",
            "design/UNCONDITIONAL-INDUCTION-PLAN.md",
        ],
    },
    "latent_depth_positive_control": {
        "representation": (
            "canonical primitive g_n=N^(2n)H in the y-unit projective chart; "
            "the scalar depth is min(v3(g_x)//2,(v3(q(g))-1)//4)"
        ),
        "domain": (
            "one fixed abstract latent line family; exact algebra for all n and "
            "finite regression through n=16, but no reachable secant birth"
        ),
        "files": [
            "design/padic-macrocycle-lift-summary.json",
            "design/padic_macrocycle_lift.py",
            "design/verify_padic_macrocycle_lift.py",
        ],
    },
    "mixed_expository_summaries": {
        "representation": "inherits the distinct representations of the cited sources",
        "domain": "expository summary only; no additional theorem",
        "files": [
            "REPORT.md",
            "viz/proof-steps.html",
        ],
    },
}


REQUIRED_SOURCE_PHRASES = {
    "design/UNCONDITIONAL-INDUCTION-PLAN.md": [
        "Status:** research plan, not a proof",
        "For a primitive direction `g`",
        "The object to descend on is the exact Plücker contact residual and",
    ],
    "design/FAR-SECANT-BIRTH-OPERATOR.md": [
        "where `g` is the",
        "canonical primitive direction",
        "There is no physical deep--deep rebirth",
    ],
    "design/LATENT-REENTRY-OBSTRUCTION.md": [
        "exact geometric carried-line obstruction, not a",
        "An integer lattice line is not yet a secant of the realized path",
    ],
    "design/padic_macrocycle_lift.py": [
        "It does not prove reachable line birth",
        "padic_depth = min(x_valuation // 2, (q_valuation - 1) // 4)",
        "birth of a latent line from a reachable legal endpoint pair",
    ],
}


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


def git_grep_files(revision: str, pattern: str) -> list[str]:
    output = git("grep", "-l", "-I", "-E", pattern, revision, "--", allow_empty=True)
    files = []
    prefix = revision + ":"
    for line in output.splitlines():
        if line.startswith(prefix):
            files.append(line[len(prefix):])
        else:
            files.append(line.split(":", 1)[-1])
    return sorted(set(files))


def history_records(pattern: str) -> list[dict[str, object]]:
    hashes = git(
        "log", "--all", "--reverse", "--format=%H", "-G" + pattern
    ).splitlines()
    records = []
    for commit in hashes:
        metadata = git("show", "-s", "--format=%aI%x1f%s", commit).rstrip("\n")
        authored_at, subject = metadata.split("\x1f", 1)
        files = [
            line
            for line in git(
                "show", "--format=", "--name-only", "-G" + pattern, commit, "--"
            ).splitlines()
            if line
        ]
        records.append({
            "commit": commit,
            "authored_at": authored_at,
            "subject": subject,
            "files": sorted(set(files)),
        })
    return records


def source_at(revision: str, path: str) -> str:
    return git("show", f"{revision}:{path}")


def matrix_vector(matrix, vector):
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def matrix_product(left, right):
    return tuple(
        tuple(
            sum(left[row][inner] * right[inner][column] for inner in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def scale(factor: int, vector):
    return tuple(factor * coordinate for coordinate in vector)


def content(vector) -> int:
    divisor = 0
    for coordinate in vector:
        divisor = math.gcd(divisor, abs(coordinate))
    return divisor


def canonical_primitive(vector):
    divisor = content(vector)
    if not divisor:
        raise ValueError("zero vector has no primitive direction")
    primitive = tuple(coordinate // divisor for coordinate in vector)
    first = next(coordinate for coordinate in primitive if coordinate)
    return scale(-1, primitive) if first < 0 else primitive


def lateral_q(vector) -> int:
    _x, y, z = vector
    return 3 * y * y - y * z + 3 * z * z


def exact_v3(value: int):
    if value == 0:
        return None
    value = abs(value)
    valuation = 0
    while value % 3 == 0:
        value //= 3
        valuation += 1
    return valuation


def valuation_record(value: int):
    valuation = exact_v3(value)
    return "infinity" if valuation is None else valuation


def finite_min(left, right):
    if left is None:
        return right
    if right is None:
        return left
    return min(left, right)


def raw_depth(vector):
    return finite_min(exact_v3(vector[0]), exact_v3(lateral_q(vector)))


def weighted_depth(vector):
    x_valuation = exact_v3(vector[0])
    q_valuation = exact_v3(lateral_q(vector))
    x_term = None if x_valuation is None else x_valuation
    q_term = None if q_valuation is None else q_valuation // 2
    return finite_min(x_term, q_term)


def polynomial_identity_record():
    # M(x,y,z)=(3x,-3z,3y-z).  Store coefficients in the order
    # x^2, xy, xz, y^2, yz, z^2.
    pulled_back = [0, 0, 0, 27, -9, 27]
    expected = [0, 0, 0, 27, -9, 27]
    if pulled_back != expected:
        raise AssertionError("q(Mg)=9q(g) coefficient drift")
    return {
        "input_q_coefficients": [0, 0, 0, 3, -1, 3],
        "q_after_M_coefficients": pulled_back,
        "nine_q_coefficients": expected,
        "identity": "q(Mg)=9*q(g)",
        "status": "PROVED",
    }


def scaling_records():
    records = []
    for exponent in range(3):
        vector = scale(3**exponent, (1, 1, 0))
        records.append({
            "scale_exponent": exponent,
            "vector": list(vector),
            "q": lateral_q(vector),
            "v3_x": valuation_record(vector[0]),
            "v3_q": valuation_record(lateral_q(vector)),
            "raw_min_depth": raw_depth(vector),
            "weighted_projective_candidate": weighted_depth(vector),
            "primitive": list(canonical_primitive(vector)),
        })
    if [record["raw_min_depth"] for record in records] != [0, 1, 2]:
        raise AssertionError("raw representation witness drift")
    if [record["weighted_projective_candidate"] for record in records] != [0, 1, 2]:
        raise AssertionError("weighted representation witness drift")
    return records


def exact_carriage_records():
    vector = (1, 1, 0)
    records = []
    for inherited_scales in range(4):
        x_valuation = exact_v3(vector[0])
        q_valuation = exact_v3(lateral_q(vector))
        if x_valuation is None or q_valuation is None:
            raise AssertionError("finite carriage witness became exceptional")
        records.append({
            "inherited_scales": inherited_scales,
            "exact_chord": list(vector),
            "primitive_direction": list(canonical_primitive(vector)),
            "v3_x": x_valuation,
            "v3_q": q_valuation,
            "residual_x": x_valuation - inherited_scales,
            "residual_q": q_valuation - 2 * inherited_scales,
        })
        vector = matrix_vector(M, vector)
    if {record["residual_x"] for record in records} != {0}:
        raise AssertionError("normalized x carriage is not constant")
    if {record["residual_q"] for record in records} != {1}:
        raise AssertionError("normalized q carriage is not constant")
    return records


def latent_records(depth: int = 6):
    n_squared = matrix_product(N, N)
    a = matrix_product(M, M)
    direction = H
    records = []
    for n in range(depth + 1):
        x_valuation = exact_v3(direction[0])
        q_valuation = exact_v3(lateral_q(direction))
        if x_valuation is None or q_valuation is None:
            raise AssertionError("latent direction hit an exceptional valuation")
        padic_depth = min(x_valuation // 2, (q_valuation - 1) // 4)
        forward_primitive = None
        forward_content = None
        if n:
            image = matrix_vector(a, direction)
            forward_content = content(image)
            forward_primitive = canonical_primitive(image)
            if forward_primitive != tuple(records[-1]["direction"]):
                raise AssertionError("latent primitive countdown drift")
        records.append({
            "n": n,
            "direction": list(direction),
            "v3_x": x_valuation,
            "v3_q": q_valuation,
            "latent_padic_depth": padic_depth,
            "forward_M_squared_content": forward_content,
            "forward_primitive_direction": (
                None if forward_primitive is None else list(forward_primitive)
            ),
        })
        if (x_valuation, q_valuation, padic_depth) != (2 * n, 4 * n + 1, n):
            raise AssertionError("latent valuation formula drift")
        direction = matrix_vector(n_squared, direction)
    return records


def normalization_difference_witness():
    chord = (3, 0, 0)
    inverse_once = (Fraction(1), Fraction(0), Fraction(0))
    inverse_twice = (Fraction(1, 3), Fraction(0), Fraction(0))
    return {
        "scope": (
            "abstract integer endpoints with stipulated unrelated provenance; "
            "not claimed reachable in the guarded construction"
        ),
        "endpoints": [[0, 0, 0], [3, 0, 0]],
        "exact_chord": list(chord),
        "stipulated_genealogical_depth": 0,
        "maximal_algebraic_depth": 1,
        "M_inverse_chord": [[value.numerator, value.denominator] for value in inverse_once],
        "M_inverse_squared_chord": [
            [value.numerator, value.denominator] for value in inverse_twice
        ],
    }


def is_rank_candidate_context(window: str) -> bool:
    compact = "".join(window.split())
    return (
        ("q_valuation" in window or "lateral_q" in window or "q(g)" in compact)
        and ("v3" in window or "valuation" in window or "nu_3" in window)
    )


def rank_candidate_occurrences(revision: str):
    paths = git_grep_files(revision, RANK_EDIT_PATTERN)
    records = []
    for path in paths:
        text = source_at(revision, path)
        lines = text.splitlines()
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


def validate_semantic_partition(q_files: list[str]):
    assigned = set()
    for group in SEMANTIC_GROUPS.values():
        assigned.update(group["files"])
    missing = sorted(set(q_files) - assigned)
    extra = sorted(assigned - set(q_files))
    if missing or extra:
        raise AssertionError(
            f"semantic q-source partition drift: missing={missing}, extra={extra}"
        )


def current_source_audit(head: str):
    explicit_files = git_grep_files(head, EXPLICIT_Q_PATTERN)
    metric_files = git_grep_files(head, METRIC_Q_PATTERN)
    depth_files = git_grep_files(head, DEPTH_PATTERN)
    validate_semantic_partition(explicit_files)
    for path, phrases in REQUIRED_SOURCE_PHRASES.items():
        text = source_at(head, path)
        for phrase in phrases:
            if phrase not in text:
                raise AssertionError(
                    f"required proof-boundary phrase missing: {path}: {phrase}"
                )
    return {
        "explicit_q_files": explicit_files,
        "invariant_metric_ancestor_files": metric_files,
        "latent_depth_files": depth_files,
        "rank_candidate_occurrences": rank_candidate_occurrences(head),
        "semantic_groups": SEMANTIC_GROUPS,
    }


def assemble_source_audit(current, histories, rank_history):
    result = dict(current)
    result["history"] = histories
    result["rank_candidate_history"] = rank_history
    result["exact_raw_min_formula_occurrences"] = exact_raw_rank_occurrences(
        rank_history
    )
    result["origin_conclusion"] = (
        "The full invariant form x^2+2q(y,z) predates the secant use.  "
        "Projective J=q/r^2 and cone guards were introduced later; the only "
        "scalar min-depth was introduced with the fixed latent-family "
        "positive control.  No raw min(v3(gx),v3(q(g))) theorem occurs."
    )
    return result


def source_audit(head: str):
    current = current_source_audit(head)
    histories = {
        "invariant_metric": history_records(METRIC_Q_PATTERN),
        "explicit_q": history_records(EXPLICIT_Q_PATTERN),
        "latent_depth": history_records(DEPTH_PATTERN),
    }
    return assemble_source_audit(
        current,
        histories,
        historical_rank_candidate_occurrences(),
    )


def build_witness(head: str):
    scaling = scaling_records()
    carriage = exact_carriage_records()
    latent = latent_records()
    return {
        "schema": WITNESS_SCHEMA,
        "auditor": AUDITOR,
        "audited_head": head,
        "raw_representation_dependence": {
            "status": "REFUTED",
            "same_geometric_line_representatives": scaling,
            "conclusion": (
                "Both raw min(v3(gx),v3(q(g))) and "
                "min(v3(gx),floor(v3(q(g))/2)) change under g -> 3g."
            ),
        },
        "birth_normalized_carriage": {
            "status": "PROVED",
            "records": carriage,
            "conclusion": (
                "For g_k=M^k g_0, subtracting (k,2k) recovers the birth "
                "valuations exactly and is constant, not a strict countdown."
            ),
        },
        "genealogical_vs_algebraic": normalization_difference_witness(),
        "x_parallel_terminology": {
            "status": "PROVED",
            "x_parallel_direction": [1, 0, 0],
            "x_parallel_gx": 1,
            "x_parallel_q": 0,
            "gx_zero_example": [0, 1, 0],
            "gx_zero_example_q": 3,
            "conclusion": (
                "Over integer directions q=0 is the x-parallel channel; gx=0 "
                "is the lateral plane, not the x-parallel channel."
            ),
        },
        "latent_positive_control": {
            "status": "PROVED",
            "reachable_secant": False,
            "records": latent,
            "conclusion": (
                "The repository scalar depth equals n and the canonical primitive "
                "line counts down under the fixed M^2 macrocycle.  The sources "
                "explicitly do not prove birth from two reachable endpoints."
            ),
        },
    }


def build_payload(head=None, witness=None, source=None):
    head = git("rev-parse", "HEAD").strip() if head is None else head
    witness = build_witness(head) if witness is None else witness
    witness_hash = stable_hash(witness)
    payload = {
        "schema": SCHEMA,
        "auditor": AUDITOR,
        "execution_protocol": {
            "signpost_prefix": f"[{AUDITOR}][3-adic secant audit]",
            "checkpoint_schema": CHECKPOINT_SCHEMA,
            "supports_estimate": True,
            "supports_resume": True,
            "supports_time_bounded_pause": True,
        },
        "audited_head": head,
        "status": (
            "STOP CONDITION 6: the universal reachable-secant scalar rank is not "
            "repository-backed and has no incidence-lifetime transition lemma"
        ),
        "stop_condition": {
            "number": 6,
            "classification": "PROVED",
            "trigger": (
                "q is repository-backed, but min(v3(gx),v3(q(g))) is not the "
                "repository rank.  The only equivalent scalar is a fixed-family "
                "positive control, explicitly outside reachable-secant scope."
            ),
        },
        "source_audit": source_audit(head) if source is None else source,
        "algebra": {
            "matrix": [list(row) for row in M],
            "q": "3*gy^2-gy*gz+3*gz^2",
            "transport": polynomial_identity_record(),
            "homogeneity": "q(3^s*g)=3^(2s)*q(g)",
        },
        "representation_verdict": {
            "raw_rank": "REFUTED",
            "canonical_repository_direction": "canonical primitive direction",
            "projective_repair": (
                "Subtract c=min_i v3(g_i) from v3(gx) and 2c from v3(q), "
                "equivalently use the 3-primitive direction.  This repairs only "
                "arbitrary scalar representation, not the lifetime theorem."
            ),
            "genealogical_pullback": (
                "For pure exact carriage M^k g_birth, M^(-k)g_current=g_birth; "
                "therefore any scalar of that pullback is constant."
            ),
            "incidence_state": (
                "Exact future incidence requires at least primitive direction g, "
                "Pluecker moment mu, correlated cursor/phase, and joint endpoint "
                "provenance; direction valuations alone are insufficient."
            ),
        },
        "claim_ledger": [
            {
                "id": "C1",
                "classification": "PROVED",
                "claim": "q(Mg)=9q(g) as an integer polynomial identity.",
            },
            {
                "id": "C2",
                "classification": "REFUTED",
                "claim": "Raw min depth is independent of the chord representative.",
            },
            {
                "id": "C3",
                "classification": "PROVED",
                "claim": (
                    "Primitive 3-content normalization repairs projective "
                    "representation dependence, but proves no return bound."
                ),
            },
            {
                "id": "C4",
                "classification": "PROVED",
                "claim": (
                    "The repository's rank-facing g is a canonical primitive "
                    "line direction, not an exact endpoint chord."
                ),
            },
            {
                "id": "C5",
                "classification": "PROVED",
                "claim": (
                    "For the abstract latent family, weighted q-depth equals the "
                    "exact fixed-macrocycle return countdown."
                ),
            },
            {
                "id": "C6",
                "classification": "CONJECTURED",
                "claim": (
                    "Policy-reachable newborn secants have a uniform corrected "
                    "first-return rank after singular promotion."
                ),
            },
            {
                "id": "C7",
                "classification": "REFUTED",
                "claim": (
                    "Birth-normalized residual valuations alone strictly decrease "
                    "under pure carriage; they are exactly constant."
                ),
            },
            {
                "id": "C8",
                "classification": "EXACT FINITE",
                "claim": (
                    "The committed macrocycle certificate covers 66,429 residue "
                    "edges through 3^5 and latent depth 16."
                ),
            },
            {
                "id": "C9",
                "classification": "EXACT FINITE",
                "claim": (
                    "The guarded L5 -> L6 cone result is one fixed chronology, "
                    "not a universal reachable-history transition."
                ),
            },
            {
                "id": "C10",
                "classification": "REFUTED",
                "claim": (
                    "A bounded scalar rank by itself implies bounded simultaneous "
                    "multiplicity or a finite safety state."
                ),
            },
            {
                "id": "C11",
                "classification": "MEASURED",
                "claim": (
                    "No measurement is used as proof in this stop report; deeper "
                    "L5/L6 rank-lifetime correlations were intentionally not run."
                ),
            },
        ],
        "corrected_theorem": {
            "classification": "PROVED",
            "statement": (
                "Let g_n=N^(2n)(55,34,18), represented canonically primitive. "
                "Then v3((g_n)_x)=2n, v3(q(g_n))=4n+1, and the fixed primitive "
                "M^2 line transition sends g_n to g_(n-1).  Hence the repository "
                "latent scalar depth equals n on this family.  This theorem is "
                "about abstract integer lattice lines, not reachable secants."
            ),
        },
        "four_required_answers": {
            "what_is_g": (
                "In the repository proposal, g is the canonical primitive affine-line "
                "direction in a Pluecker token (g,mu).  Cone guards may evaluate the "
                "homogeneous polynomial on a raw endpoint difference.  The proposed "
                "birth-normalized exact chord is a different, new object."
            ),
            "when_is_secant_born": (
                "Repository-backed canonical birth is insertion of the later endpoint; "
                "all old-new and same-word new-new lines are injected then.  A cursor "
                "import is exposure, not birth; deep-deep lines are not reborn."
            ),
            "what_scale_can_be_factored": (
                "Arbitrary scalar representation may be removed canonically by primitive "
                "normalization.  Genealogical M-scale may be removed only from exact joint "
                "endpoint provenance proving common carriage.  Maximal algebraic pullback "
                "is not a substitute for that provenance."
            ),
            "why_rank_decreases_or_promotes": (
                "No general proof exists.  The fixed latent family counts down only after "
                "canonical primitive normalization of one macrocycle.  Birth-normalized "
                "exact-chord valuations are constant, and no finite promoted closure for "
                "all reachable silent SCCs has been proved."
            ),
        },
        "remaining_lemmas": [
            "Canonical joint-endpoint provenance and inherited-scale lemma.",
            "Exact correlated contact-residual transition for every legal stitch and cursor move.",
            "Uniform reachable-newborn residual bound for every birth channel.",
            "Strict decrease, bounded-block decrease, or finite promotion for every reachable silent SCC.",
            "Finite promoted occupancy and multiplicity closure under births and imports.",
            "Whole-word correlated poison-mask safety fixed point with positive availability.",
        ],
        "witness": {
            "path": "design/padic-reachable-secant-depth-witness.json",
            "payload_sha256": witness_hash,
        },
    }
    return payload, witness


def stable_hash(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def atomic_json_dump(value, path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


PHASES = (
    "exact_witnesses",
    "current_source_inventory",
    "invariant_metric_history",
    "explicit_q_history",
    "latent_depth_history",
    "rank_candidate_history",
)


def signpost(message: str):
    print(f"[{AUDITOR}][3-adic secant audit] {message}", file=sys.stderr, flush=True)


def source_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def checkpoint_fingerprint(head: str) -> str:
    return stable_hash({
        "schema": CHECKPOINT_SCHEMA,
        "auditor": AUDITOR,
        "audited_head": head,
        "source_sha256": source_sha256(Path(__file__).resolve()),
        "patterns": {
            "explicit_q": EXPLICIT_Q_PATTERN,
            "invariant_metric": METRIC_Q_PATTERN,
            "latent_depth": DEPTH_PATTERN,
            "rank_candidate": RANK_EDIT_PATTERN,
        },
    })


def fresh_checkpoint(
    head: str,
    fingerprint: str,
    summary_path: Path,
    witness_path: Path,
):
    return {
        "schema": CHECKPOINT_SCHEMA,
        "auditor": AUDITOR,
        "audited_head": head,
        "fingerprint": fingerprint,
        "outputs": {
            "summary": str(summary_path),
            "witness": str(witness_path),
        },
        "completed_phases": [],
        "data": {},
        "status": "running",
    }


def load_checkpoint(path: Path, head: str, fingerprint: str):
    with Path(path).open() as handle:
        checkpoint = json.load(handle)
    if checkpoint.get("schema") != CHECKPOINT_SCHEMA:
        raise RuntimeError("checkpoint schema mismatch")
    if checkpoint.get("audited_head") != head:
        raise RuntimeError("checkpoint audited-head mismatch")
    if checkpoint.get("fingerprint") != fingerprint:
        raise RuntimeError("checkpoint fingerprint mismatch; code or inputs changed")
    completed = checkpoint.get("completed_phases")
    if (
        not isinstance(completed, list)
        or len(completed) != len(set(completed))
        or any(phase not in PHASES for phase in completed)
    ):
        raise RuntimeError("checkpoint phase ledger is invalid")
    outputs = checkpoint.get("outputs")
    if (
        not isinstance(outputs, dict)
        or set(outputs) != {"summary", "witness"}
        or not all(isinstance(path, str) and path for path in outputs.values())
    ):
        raise RuntimeError("checkpoint output paths are invalid")
    return checkpoint


def paused_result(checkpoint, checkpoint_path: Path):
    return {
        "auditor": AUDITOR,
        "status": "paused",
        "audited_head": checkpoint["audited_head"],
        "checkpoint": str(checkpoint_path),
        "completed_phases": checkpoint["completed_phases"],
        "remaining_phases": [
            phase for phase in PHASES
            if phase not in checkpoint["completed_phases"]
        ],
        "resume_argv": [
            "python3",
            "-B",
            "design/padic_reachable_secant_depth_audit.py",
            "run",
            "--resume",
            "--checkpoint",
            str(checkpoint_path),
        ],
    }


def execute_phase(phase: str, head: str, data):
    if phase == "exact_witnesses":
        data["witness"] = build_witness(head)
    elif phase == "current_source_inventory":
        data["current_source"] = current_source_audit(head)
    elif phase == "invariant_metric_history":
        data["invariant_metric_history"] = history_records(METRIC_Q_PATTERN)
    elif phase == "explicit_q_history":
        data["explicit_q_history"] = history_records(EXPLICIT_Q_PATTERN)
    elif phase == "latent_depth_history":
        data["latent_depth_history"] = history_records(DEPTH_PATTERN)
    elif phase == "rank_candidate_history":
        data["rank_candidate_history"] = historical_rank_candidate_occurrences()
    else:
        raise AssertionError(f"unknown phase {phase}")


def finalize_outputs(checkpoint, summary_path: Path, witness_path: Path):
    data = checkpoint["data"]
    histories = {
        "invariant_metric": data["invariant_metric_history"],
        "explicit_q": data["explicit_q_history"],
        "latent_depth": data["latent_depth_history"],
    }
    source = assemble_source_audit(
        data["current_source"],
        histories,
        data["rank_candidate_history"],
    )
    payload, witness = build_payload(
        head=checkpoint["audited_head"],
        witness=data["witness"],
        source=source,
    )
    witness_with_hash = dict(witness)
    witness_with_hash["payload_sha256"] = stable_hash(witness)
    payload_with_hash = dict(payload)
    payload_with_hash["payload_sha256"] = stable_hash(payload)
    atomic_json_dump(witness_with_hash, witness_path)
    atomic_json_dump(payload_with_hash, summary_path)
    return {
        "auditor": AUDITOR,
        "status": "complete",
        "verdict": "stopped_at_condition_6",
        "stop_condition": 6,
        "audited_head": payload["audited_head"],
        "summary": str(summary_path),
        "summary_payload_sha256": payload_with_hash["payload_sha256"],
        "witness": str(witness_path),
        "witness_payload_sha256": witness_with_hash["payload_sha256"],
    }


def run_checkpointed(args):
    head = git("rev-parse", "HEAD").strip()
    fingerprint = checkpoint_fingerprint(head)
    if args.resume:
        if not args.checkpoint.exists():
            raise RuntimeError(f"resume checkpoint does not exist: {args.checkpoint}")
        checkpoint = load_checkpoint(args.checkpoint, head, fingerprint)
        args.summary = Path(checkpoint["outputs"]["summary"])
        args.witness = Path(checkpoint["outputs"]["witness"])
        signpost(
            f"resuming {len(checkpoint['completed_phases'])}/{len(PHASES)} "
            f"phases from {args.checkpoint}"
        )
    else:
        if args.checkpoint.exists():
            raise RuntimeError(
                f"checkpoint exists: {args.checkpoint}; pass --resume or choose another path"
            )
        checkpoint = fresh_checkpoint(
            head,
            fingerprint,
            args.summary,
            args.witness,
        )
        atomic_json_dump(checkpoint, args.checkpoint)
        signpost(f"started audit at {head}; checkpoint {args.checkpoint}")

    started = time.monotonic()
    phases_this_run = 0
    for phase in PHASES:
        if phase in checkpoint["completed_phases"]:
            continue
        elapsed = time.monotonic() - started
        if (
            (args.max_seconds > 0 and elapsed >= args.max_seconds)
            or (args.max_phases > 0 and phases_this_run >= args.max_phases)
        ):
            checkpoint["status"] = "paused"
            atomic_json_dump(checkpoint, args.checkpoint)
            signpost(f"paused safely before {phase}")
            result = paused_result(checkpoint, args.checkpoint)
            print(json.dumps(result, sort_keys=True))
            return result
        signpost(f"phase {len(checkpoint['completed_phases']) + 1}/{len(PHASES)}: {phase}")
        execute_phase(phase, head, checkpoint["data"])
        checkpoint["completed_phases"].append(phase)
        checkpoint["status"] = "running"
        atomic_json_dump(checkpoint, args.checkpoint)
        phases_this_run += 1

    result = finalize_outputs(checkpoint, args.summary, args.witness)
    checkpoint["status"] = "complete"
    checkpoint["result"] = result
    atomic_json_dump(checkpoint, args.checkpoint)
    signpost("complete; STOP CONDITION 6 certified")
    print(json.dumps(result, sort_keys=True))
    return result


def estimate():
    result = {
        "auditor": AUDITOR,
        "status": "estimate",
        "audited_head": git("rev-parse", "HEAD").strip(),
        "deterministic_work_units": len(PHASES),
        "phases": list(PHASES),
        "pause_boundary": "between exact phases; interrupted phases replay on resume",
    }
    signpost(f"estimate: {len(PHASES)} deterministic phases")
    print(json.dumps(result, sort_keys=True))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("estimate", "run"), nargs="?", default="run")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--max-seconds",
        type=float,
        default=0.0,
        help="pause at the next phase boundary after this many seconds; zero is unlimited",
    )
    parser.add_argument(
        "--max-phases",
        type=int,
        default=0,
        help="deterministic phase budget for pause/resume testing; zero is unlimited",
    )
    args = parser.parse_args()
    if args.max_seconds < 0 or args.max_phases < 0:
        parser.error("pause budgets must be nonnegative")
    if args.command == "estimate":
        if args.resume:
            parser.error("--resume applies only to run")
        estimate()
    else:
        run_checkpointed(args)


if __name__ == "__main__":
    main()
