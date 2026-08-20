#!/usr/bin/env python3
"""Lightweight algebraic CEGAR analysis of the exact 3998-versus-0 witness.

This consumer performs no connector-domain or placed-point-pair scan.  It
loads the pinned future-compatibility result, its L7->L8 centered geometry,
and the L9 initial-anchor precursor.  Every mask used in a partition key is
decoded to its raw integer bitset; hashes are checked only as payload
commitments.

The analysis compares several translation-normalized refinements of the
current physical-partner key:

* exact centered endpoint offsets;
* exact primitive Plucker direction and centered moment of the source token;
* exact primitive Plucker data from each tagged endpoint to the actually
  selected connector's terminal endpoint;
* the one-bit zero/nonzero ghost residual for the decisive prefix/site query;
* the terminal-line moment modulo 3; and
* a deliberately empirical one-residue mod-9 CEGAR split.

It reports congruence twice.  ``mask_transition`` compares only the ordered
next direct/endpoint/near-deep killed masks.  ``full_state_transition`` also
compares the next birth/owner-shell and physical-partner state.  A finite
non-falsification result is not a universal right-congruence proof.

Run on one low-priority thread::

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/far_secant_translation_cegar.py \
        --output /tmp/far-secant-translation-cegar.json
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import resource
import sys
import tempfile
import time
import zlib
from collections import defaultdict
from fractions import Fraction
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPATIBILITY = Path(
    "/tmp/far-secant-future-compatibility-probe-canonical.json"
)
DEFAULT_FUTURE = Path("/tmp/far-secant-future-trace-canonical.json")
DEFAULT_L9 = Path("/tmp/l9-anchor-age2-precursor-canonical.json")

EXPECTED_SHA256 = {
    "compatibility": (
        "72af973f12179f1b25b24a23d77d8420888964bce219b0106a32c79be698dda6"
    ),
    "future": (
        "611bf74be1d42bd15d311964603daa573f8ff39a0f3bcb9542f4063341919b87"
    ),
    "l9": (
        "961f9e5f0772d9df508ab0aefaa7405e3cc21637d59560cdda95c4edf61d809f"
    ),
}
EXPECTED_CHECKER_SHA256 = {
    "compatibility": (
        "4f95c0afd084306e7ecb202c49567a376e52d101cb3f9274fefd01d6d62fbf46"
    ),
    "future": (
        "6f286cb118166c1375eb777ec6e24bcdc58766b98538099c604eb97b5c3dd430"
    ),
    "l9": (
        "66f776e7ae4eff4c35d004d870d82458582a4c2b6516f20257149a08e5535b90"
    ),
}

THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

M_BAL3 = ((3, 0, 0), (0, 0, -3), (0, 3, -1))
MENU = tuple(
    vector
    for vector in product(range(-2, 3), repeat=3)
    if vector != (0, 0, 0)
)
WITNESS = {
    "source_gap": 13171,
    "l8_A": 41282,
    "l8_B": 41297,
    "slot": 1,
    "child_site": (2, 3, 5),
    "tagged_endpoint": "connector:L7:G12324:I2",
    "latent_partner": "connector:L7:G12329:I2",
}


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def as_json(value):
    if isinstance(value, Fraction):
        return {
            "numerator": value.numerator,
            "denominator": value.denominator,
        }
    if isinstance(value, tuple):
        return [as_json(item) for item in value]
    if isinstance(value, list):
        return [as_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): as_json(item) for key, item in value.items()}
    return value


def stable_bytes(value):
    return json.dumps(
        as_json(value), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def load_json(path):
    with path.open() as handle:
        return json.load(handle)


def add(left, right):
    return tuple(left[axis] + right[axis] for axis in range(3))


def sub(left, right):
    return tuple(left[axis] - right[axis] for axis in range(3))


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def primitive(vector):
    divisor = math.gcd(
        math.gcd(abs(vector[0]), abs(vector[1])), abs(vector[2])
    )
    if divisor == 0:
        return None
    result = tuple(value // divisor for value in vector)
    for value in result:
        if value < 0:
            return tuple(-item for item in result)
        if value > 0:
            return result
    raise AssertionError("nonzero primitive direction lost sign")


def inverse_M(vector):
    """Exact inverse of M_BAL3 on a possibly non-lattice query vector."""
    x, y, z = vector
    return (
        Fraction(x, 3),
        Fraction(z, 3) - Fraction(y, 9),
        -Fraction(y, 3),
    )


def apply_M(vector):
    return tuple(
        sum(M_BAL3[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def selected_prefix(word, slot):
    prefix = (0, 0, 0)
    for menu_index in word[:slot]:
        prefix = add(prefix, MENU[menu_index])
    return prefix


def selected_terminal(word):
    return selected_prefix(word, len(word))


def centered_line(first, second):
    direction = primitive(sub(second, first))
    if direction is None:
        return {"coincident": True}
    return {
        "coincident": False,
        "primitive_direction": direction,
        "relative_moment": cross(first, direction),
    }


def ghost_residual(line, prefix, child_site):
    if line["coincident"]:
        return None
    ghost_site = add(prefix, inverse_M(child_site))
    return sub(
        line["relative_moment"],
        cross(ghost_site, line["primitive_direction"]),
    )


def enforce_resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "all thread-cap variables must equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    if nice < 15:
        raise RuntimeError(f"run under nice -n 15; observed {nice}")
    return {"processes": 1, "thread_cap": 1, "nice": nice}


class MaskDecoder:
    def __init__(self, artifact):
        self.payloads = artifact["exact_mask_store"]["payloads"]
        self.cache = {}

    def bits(self, record):
        reference = record["exact_payload_ref"]
        if reference not in self.cache:
            payload = self.payloads[reference]
            raw = zlib.decompress(
                base64.b64decode(payload["payload_base64"])
            )
            assert len(raw) == payload["uncompressed_bytes"]
            assert hashlib.sha256(raw).hexdigest() == record["mask_sha256"]
            bits = int.from_bytes(raw, "little")
            assert bits.bit_count() == record["killed_words"]
            assert bits >> record["domain_words"] == 0
            self.cache[reference] = bits
        return self.cache[reference]


def keyed_masks(records, decoder):
    return tuple(
        (
            tuple(record["key"])
            if isinstance(record["key"], list)
            else record["key"],
            decoder.bits(record["mask"]),
        )
        for record in records
    )


def current_key(state, decoder, level):
    address = state["literal_joint_address"]
    components = state["local_exact_components"]
    if level == 8:
        step = address["l8_stitch"]["step"]
        actual_word = tuple(
            address["l8_stitch"]["actual_selected_connector_word"]
        )
        near_name = "near_deep_tagged_partner_site_poison"
    else:
        step = address["l9_precursor_stitch"]["step"]
        actual_word = ()
        near_name = "near_deep_tagged_initial_anchor_site_poison"
    return (
        tuple(address["source_token"]["ordered_tagged_endpoint_stable_ids"]),
        address["source_token"]["witness_type"],
        step,
        state["domain_words"],
        actual_word,
        decoder.bits(components["direct_carried_tagged_pair_site_poison"]),
        decoder.bits(components["endpoint_collision"]),
        decoder.bits(components["endpoint_on_candidate_internal_line"]),
        decoder.bits(components[near_name]),
        state["source_token_owner_profile"][
            "minimum_joint_owner_base3_shell"
        ],
        keyed_masks(state["endpoint_birth_owner_shell_masks"], decoder),
        keyed_masks(state["near_deep_birth_owner_shell_masks"], decoder),
        keyed_masks(state["physical_partner_masks"], decoder),
    )


def mask_outcome(state, l9_by_gap, decoder):
    result = []
    source_gap = state["identity"]["source_gap"]
    for successor in state["ordered_l9_successors"]:
        child = l9_by_gap[(source_gap, successor["l9_gap"])]
        components = child["local_exact_components"]
        result.append((
            successor["step"],
            decoder.bits(
                components["direct_carried_tagged_pair_site_poison"]
            ),
            decoder.bits(components["endpoint_collision"]),
            decoder.bits(
                components["endpoint_on_candidate_internal_line"]
            ),
            decoder.bits(
                components["near_deep_tagged_initial_anchor_site_poison"]
            ),
        ))
    return tuple(result)


def full_outcome(state, l9_by_gap, decoder):
    source_gap = state["identity"]["source_gap"]
    return tuple(
        current_key(
            l9_by_gap[(source_gap, successor["l9_gap"])], decoder, 9
        )
        for successor in state["ordered_l9_successors"]
    )


def identity(state):
    return (
        state["identity"]["source_gap"],
        state["identity"]["l7_parent_gap"],
        state["identity"]["l8_gap"],
    )


def audit_refinement(states, base_keys, feature, mask_outcomes, full_outcomes):
    groups = defaultdict(list)
    for state in states:
        item = identity(state)
        groups[(base_keys[item], feature(state))].append(item)
    repeated = [members for members in groups.values() if len(members) > 1]
    repeated.sort()
    mask_bad = [
        members for members in repeated
        if len({mask_outcomes[item] for item in members}) > 1
    ]
    full_bad = [
        members for members in repeated
        if len({full_outcomes[item] for item in members}) > 1
    ]
    return {
        "nodes": len(states),
        "classes": len(groups),
        "repeated_classes": len(repeated),
        "largest_class": max((len(members) for members in repeated), default=1),
        "mask_transition_noncongruent_classes": len(mask_bad),
        "full_state_transition_noncongruent_classes": len(full_bad),
        "repeated_class_members": as_json(repeated),
        "mask_noncongruent_members": as_json(mask_bad),
        "full_state_noncongruent_members": as_json(full_bad),
    }


def future_geometry(state, future_by_gap):
    return future_by_gap[
        (state["identity"]["source_gap"], state["identity"]["l8_gap"])
    ]["centered_geometry"]


def centered_endpoints_feature(state, future_by_gap):
    return tuple(
        (endpoint["stable_id"], tuple(endpoint["vector"]))
        for endpoint in future_geometry(state, future_by_gap)["endpoints"]
    )


def first_centered_endpoint_feature(state, future_by_gap):
    endpoint = future_geometry(state, future_by_gap)["endpoints"][0]
    return endpoint["stable_id"], tuple(endpoint["vector"])


def source_plucker_feature(state, future_by_gap):
    geometry = future_geometry(state, future_by_gap)
    if geometry["carried_two_endpoint_secants"]:
        return tuple(
            (
                tuple(line["primitive_direction"]),
                tuple(line["relative_moment"]),
            )
            for line in geometry["carried_two_endpoint_secants"]
        )
    image = geometry["transported_source_atom_image"]
    assert image["kind"] == "line"
    return ((
        tuple(image["primitive_direction"]),
        tuple(image["relative_moment"]),
    ),)


def source_direction_feature(state, future_by_gap):
    return tuple(
        direction for direction, _moment in source_plucker_feature(
            state, future_by_gap
        )
    )


def source_primary_line(state, future_by_gap):
    direction, moment = source_plucker_feature(state, future_by_gap)[0]
    return {
        "coincident": False,
        "primitive_direction": direction,
        "relative_moment": moment,
    }


def terminal_relation_feature(state, future_by_gap, include_terminal_id=False):
    geometry = future_geometry(state, future_by_gap)
    word = state["literal_joint_address"]["l8_stitch"][
        "actual_selected_connector_word"
    ]
    terminal = selected_terminal(word)
    relation = []
    for endpoint in geometry["endpoints"]:
        line = centered_line(tuple(endpoint["vector"]), terminal)
        relation.append((endpoint["stable_id"], tuple(sorted(line.items()))))
    if include_terminal_id:
        terminal_id = state["ordered_l9_successors"][-1][
            "ordered_corridor_endpoint_stable_ids"
        ][1]
        return terminal_id, tuple(relation)
    return tuple(relation)


def terminal_last_line(state, future_by_gap):
    geometry = future_geometry(state, future_by_gap)
    endpoint = tuple(geometry["endpoints"][-1]["vector"])
    word = state["literal_joint_address"]["l8_stitch"][
        "actual_selected_connector_word"
    ]
    return centered_line(endpoint, selected_terminal(word))


def terminal_direction_feature(state, future_by_gap):
    relation = terminal_relation_feature(state, future_by_gap)
    result = []
    for stable_id, encoded_line in relation:
        line = dict(encoded_line)
        result.append((
            stable_id,
            "coincident" if line["coincident"] else line[
                "primitive_direction"
            ],
        ))
    return tuple(result)


def selected_terminal_stable_id(state):
    return state["ordered_l9_successors"][-1][
        "ordered_corridor_endpoint_stable_ids"
    ][1]


def ghost_query_residual(state, future_by_gap):
    word = state["literal_joint_address"]["l8_stitch"][
        "actual_selected_connector_word"
    ]
    line = terminal_last_line(state, future_by_gap)
    return ghost_residual(
        line, selected_prefix(word, WITNESS["slot"]), WITNESS["child_site"]
    )


def source_moment_y(state, future_by_gap):
    return source_primary_line(state, future_by_gap)["relative_moment"][1]


def terminal_moment_y(state, future_by_gap):
    line = terminal_last_line(state, future_by_gap)
    return None if line["coincident"] else line["relative_moment"][1]


def mod3_terminal_feature(state, future_by_gap):
    line = terminal_last_line(state, future_by_gap)
    if line["coincident"]:
        return ("coincident",)
    return tuple(value % 3 for value in line["relative_moment"])


def empirical_rho_mod9(state, future_by_gap):
    terminal_y = terminal_moment_y(state, future_by_gap)
    if terminal_y is None:
        return ("coincident", source_moment_y(state, future_by_gap) % 9)
    return (source_moment_y(state, future_by_gap) + terminal_y) % 9


def absolute_partner_at_l8(l9, stable_id):
    profile = next(
        profile for profile in l9["partner_profiles"]["profiles"]
        if profile["stable_id"] == stable_id
    )
    l9_coordinate = tuple(profile["l9_coordinate"])
    coordinate = inverse_M(l9_coordinate)
    assert all(value.denominator == 1 for value in coordinate)
    coordinate = tuple(value.numerator for value in coordinate)
    assert apply_M(coordinate) == l9_coordinate
    return coordinate, profile


def witness_algebra(state, future_by_gap, partner_coordinate):
    geometry_record = future_by_gap[
        (state["identity"]["source_gap"], state["identity"]["l8_gap"])
    ]
    geometry = geometry_record["centered_geometry"]
    start = tuple(geometry_record["actual_corridor_start_coordinate"])
    endpoint_record = next(
        endpoint for endpoint in geometry["endpoints"]
        if endpoint["stable_id"] == WITNESS["tagged_endpoint"]
    )
    endpoint = tuple(endpoint_record["vector"])
    partner = sub(partner_coordinate, start)
    word = state["literal_joint_address"]["l8_stitch"][
        "actual_selected_connector_word"
    ]
    prefix = selected_prefix(word, WITNESS["slot"])
    terminal = selected_terminal(word)
    fixed_partner_line = centered_line(endpoint, partner)
    terminal_line = centered_line(endpoint, terminal)
    source_line = source_primary_line(state, future_by_gap)
    return {
        "identity": state["identity"],
        "corridor_start": start,
        "tagged_endpoint_centered_offset": endpoint,
        "fixed_partner_centered_offset": partner,
        "selected_terminal_centered_offset": terminal,
        "selected_terminal_is_fixed_partner": terminal == partner,
        "actual_selected_word": word,
        "selected_slot": WITNESS["slot"],
        "selected_prefix": prefix,
        "child_site": WITNESS["child_site"],
        "ghost_site_in_parent_frame": add(
            prefix, inverse_M(WITNESS["child_site"])
        ),
        "source_token_line": source_line,
        "fixed_tagged_partner_line": fixed_partner_line,
        "fixed_partner_ghost_residual": ghost_residual(
            fixed_partner_line, prefix, WITNESS["child_site"]
        ),
        "selected_terminal_relation_line": terminal_line,
        "selected_terminal_ghost_residual": ghost_residual(
            terminal_line, prefix, WITNESS["child_site"]
        ),
        "terminal_moment_mod3": (
            None if terminal_line["coincident"] else tuple(
                value % 3 for value in terminal_line["relative_moment"]
            )
        ),
        "empirical_rho_mod9": empirical_rho_mod9(state, future_by_gap),
    }


def atomic_write_json(path, result):
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(as_json(result), handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def build_result(compatibility, future, l9, input_hashes, resource_policy):
    started = time.monotonic()
    decoder = MaskDecoder(compatibility)
    states = compatibility["states"]["L8"]
    l9_by_gap = {
        (state["identity"]["source_gap"], state["identity"]["l9_gap"]): state
        for state in compatibility["states"]["L9"]
    }
    future_by_gap = {
        (state["source_gap"], state["l8_gap"]): state
        for state in future["child_states"]
    }
    base_keys = {
        identity(state): current_key(state, decoder, 8) for state in states
    }
    mask_outcomes = {
        identity(state): mask_outcome(state, l9_by_gap, decoder)
        for state in states
    }
    full_outcomes = {
        identity(state): full_outcome(state, l9_by_gap, decoder)
        for state in states
    }

    features = {
        "current_key_only": lambda _state: (),
        "exact_centered_tagged_endpoint_offsets": (
            lambda state: centered_endpoints_feature(state, future_by_gap)
        ),
        "one_exact_centered_tagged_endpoint_offset": (
            lambda state: first_centered_endpoint_feature(
                state, future_by_gap
            )
        ),
        "source_token_primitive_direction_only": (
            lambda state: source_direction_feature(state, future_by_gap)
        ),
        "exact_source_token_primitive_Plucker_line": (
            lambda state: source_plucker_feature(state, future_by_gap)
        ),
        "selected_terminal_partner_primitive_directions": (
            lambda state: terminal_direction_feature(state, future_by_gap)
        ),
        "exact_selected_terminal_partner_relations": (
            lambda state: terminal_relation_feature(state, future_by_gap)
        ),
        "one_bit_discovered_partner_is_selected_terminal": (
            lambda state: selected_terminal_stable_id(state)
            == WITNESS["latent_partner"]
        ),
        "one_bit_decisive_ghost_residual_is_zero": (
            lambda state: ghost_query_residual(state, future_by_gap)
            == (Fraction(0), Fraction(0), Fraction(0))
        ),
        "selected_terminal_relative_moment_mod_3": (
            lambda state: mod3_terminal_feature(state, future_by_gap)
        ),
        "empirical_rho_mod_9": (
            lambda state: empirical_rho_mod9(state, future_by_gap)
        ),
    }
    audits = {
        name: audit_refinement(
            states, base_keys, feature, mask_outcomes, full_outcomes
        )
        for name, feature in features.items()
    }
    expected = {
        "current_key_only": (142, 4, 1, 3),
        "exact_centered_tagged_endpoint_offsets": (146, 0, 0, 0),
        "one_exact_centered_tagged_endpoint_offset": (146, 0, 0, 0),
        "source_token_primitive_direction_only": (142, 4, 1, 3),
        "exact_source_token_primitive_Plucker_line": (146, 0, 0, 0),
        "selected_terminal_partner_primitive_directions": (146, 0, 0, 0),
        "exact_selected_terminal_partner_relations": (146, 0, 0, 0),
        "one_bit_discovered_partner_is_selected_terminal": (143, 3, 0, 2),
        "one_bit_decisive_ghost_residual_is_zero": (143, 3, 0, 2),
        "selected_terminal_relative_moment_mod_3": (143, 3, 0, 2),
        "empirical_rho_mod_9": (145, 1, 0, 0),
    }
    for name, values in expected.items():
        record = audits[name]
        assert (
            record["classes"],
            record["repeated_classes"],
            record["mask_transition_noncongruent_classes"],
            record["full_state_transition_noncongruent_classes"],
        ) == values

    partner_coordinate, partner_profile = absolute_partner_at_l8(
        l9, WITNESS["latent_partner"]
    )
    states_by_gap = {
        state["identity"]["l8_gap"]: state for state in states
    }
    algebra_A = witness_algebra(
        states_by_gap[WITNESS["l8_A"]], future_by_gap, partner_coordinate
    )
    algebra_B = witness_algebra(
        states_by_gap[WITNESS["l8_B"]], future_by_gap, partner_coordinate
    )
    assert algebra_A["fixed_partner_ghost_residual"] == (
        Fraction(0), Fraction(0), Fraction(0)
    )
    assert algebra_A["selected_terminal_is_fixed_partner"]
    assert algebra_B["fixed_partner_ghost_residual"] == (
        Fraction(404), Fraction(98), Fraction(438)
    )
    assert algebra_B["selected_terminal_ghost_residual"] == (
        Fraction(202, 3), Fraction(49, 3), Fraction(73)
    )
    assert algebra_A["terminal_moment_mod3"] == (1, 1, 0)
    assert algebra_B["terminal_moment_mod3"] == (0, 0, 0)
    assert algebra_A["empirical_rho_mod9"] == 4
    assert algebra_B["empirical_rho_mod9"] == 6

    elapsed = round(time.monotonic() - started, 3)
    maximum_resident = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "status": (
            "exact lightweight algebraic analysis of the finite 3998-vs-0 "
            "witness; not a universal refinement or proof"
        ),
        "checker_sha256": file_sha256(Path(__file__)),
        "input_sha256": input_hashes,
        "resource_policy": {
            **resource_policy,
            "elapsed_seconds": elapsed,
            "maximum_resident_platform_units": maximum_resident,
            "resident_unit_note": "bytes on macOS; KiB on Linux",
        },
        "translation_normalization": {
            "origin": "the concrete pending corridor start",
            "global_translation_invariance": (
                "endpoint and partner coordinates are first centered at the "
                "corridor start; Plucker moments and ghost residuals are "
                "computed only from these centered vectors"
            ),
            "ghost_formula": "r = mu - (c + M^{-1} x') cross g",
            "matrix": M_BAL3,
        },
        "witness": {
            "definition": WITNESS,
            "latent_partner_L8_coordinate": partner_coordinate,
            "latent_partner_birth_profile": partner_profile,
            "state_A": algebra_A,
            "state_B": algebra_B,
            "exact_difference": {
                "A_fixed_partner_residual": algebra_A[
                    "fixed_partner_ghost_residual"
                ],
                "B_fixed_partner_residual": algebra_B[
                    "fixed_partner_ghost_residual"
                ],
                "A_selected_terminal_residual": algebra_A[
                    "selected_terminal_ghost_residual"
                ],
                "B_selected_terminal_residual": algebra_B[
                    "selected_terminal_ghost_residual"
                ],
                "A_terminal_moment_mod3": algebra_A[
                    "terminal_moment_mod3"
                ],
                "B_terminal_moment_mod3": algebra_B[
                    "terminal_moment_mod3"
                ],
            },
        },
        "finite_partition_audits": audits,
        "smallest_observed_refinements": {
            "one_bit_physical_partner_role_refinement": {
                "field": (
                    "whether the discovered latent partner "
                    "connector:L7:G12329:I2 is the selected connector's "
                    "terminal endpoint"
                ),
                "witness_values": {"A": True, "B": False},
                "distinguishes_witness": True,
                "classes": 143,
                "repeated_classes": 3,
                "all_repeated_classes_mask_transition_congruent": True,
                "all_repeated_classes_full_state_transition_congruent": False,
                "warning": (
                    "this bit is specific to the discovered partner and "
                    "does not retain its line after it ceases to be the "
                    "terminal endpoint"
                ),
            },
            "one_bit_mask_refinement": {
                "field": (
                    "whether the last tagged endpoint-to-selected-terminal "
                    "line has zero ghost residual at slot 1 and child site "
                    "(2,3,5)"
                ),
                "distinguishes_witness": True,
                "classes": 143,
                "repeated_classes": 3,
                "all_repeated_classes_mask_transition_congruent": True,
                "all_repeated_classes_full_state_transition_congruent": False,
                "warning": (
                    "one query bit is exact only for this prefix/site; it is "
                    "not sound for unlisted sites or later continuations"
                ),
            },
            "uniform_local_mod3_refinement": {
                "field": (
                    "the three coordinates modulo 3 of the centered Plucker "
                    "moment from the last tagged endpoint to the selected "
                    "terminal endpoint"
                ),
                "witness_values": {"A": [1, 1, 0], "B": [0, 0, 0]},
                "classes": 143,
                "repeated_classes": 3,
                "all_repeated_classes_mask_transition_congruent": True,
                "all_repeated_classes_full_state_transition_congruent": False,
                "warning": (
                    "a modular nonzero residue proves nonzero, but a zero "
                    "residue does not prove exact incidence or supply an "
                    "exact successor transfer"
                ),
            },
            "smallest_tested_nonvacuous_full_state_split": {
                "field": (
                    "rho = (source-token centered moment coordinate 1 + "
                    "selected-terminal relation centered moment coordinate "
                    "1) mod 9"
                ),
                "witness_values": {"A": 4, "B": 6},
                "classes": 145,
                "repeated_classes": 1,
                "all_repeated_classes_mask_transition_congruent": True,
                "all_repeated_classes_full_state_transition_congruent": True,
                "warning": (
                    "rho was selected after inspecting this finite trace; "
                    "it has no proved transfer law and is evidence only"
                ),
            },
        },
        "proposed_CEGAR_refinement": {
            "state_token": (
                "retain the discovered latent joint token (tagged endpoint "
                "stable/birth address, partner stable/birth/owner address, "
                "primitive direction g, exact centered moment mu), even "
                "while its current killed mask is empty"
            ),
            "selected_action_transfer": (
                "for every actual prefix c, transport the joint line exactly "
                "and evaluate candidate sites with r=mu-(c+M^{-1}x')cross g; "
                "do not reconstruct the line from independent endpoint "
                "marginals"
            ),
            "first_refinement_for_the_counterexample": {
                "tagged_endpoint": WITNESS["tagged_endpoint"],
                "partner": WITNESS["latent_partner"],
                "partner_role_in_A": "selected connector terminal endpoint",
                "exact_A_line": algebra_A["fixed_tagged_partner_line"],
                "exact_B_line": algebra_B["fixed_tagged_partner_line"],
            },
            "why_exact_Plucker_is_the_sound_choice": (
                "it decides every candidate-site incidence of this latent "
                "line and has an exact affine/cofactor successor update; the "
                "one-bit and modular splits decide only the observed query"
            ),
            "finite_trace_result": (
                "one exact centered tagged endpoint offset, exact source "
                "Plucker data, and exact selected-terminal primitive "
                "directions or full relations each make all 146 L8 states "
                "singleton; they distinguish the witness but provide no "
                "nonvacuous finite-index evidence"
            ),
        },
        "soundness_limits": [
            "the CEGAR token closes only the discovered tagged-partner line; other remote partners can require further refinements",
            "the selected-terminal relation does not cover a partner that is neither selected endpoint nor otherwise retained",
            "the L9 horizon omits current-L9 connector interiors and has no selected L9 word",
            "the experiment contains one realized action per stitch and no alternate-action Post closure",
            "finite repeated-class congruence does not prove a universal finite right congruence",
            "exact Plucker states are singleton here, so a separate contraction, ranking, promotion, or proved finite quotient remains necessary",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compatibility", type=Path, default=DEFAULT_COMPATIBILITY
    )
    parser.add_argument("--future", type=Path, default=DEFAULT_FUTURE)
    parser.add_argument("--l9", type=Path, default=DEFAULT_L9)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    resource_policy = enforce_resource_policy()
    paths = {
        "compatibility": args.compatibility,
        "future": args.future,
        "l9": args.l9,
    }
    input_hashes = {name: file_sha256(path) for name, path in paths.items()}
    assert input_hashes == EXPECTED_SHA256
    compatibility = load_json(args.compatibility)
    future = load_json(args.future)
    l9 = load_json(args.l9)
    assert compatibility["checker_sha256"] == EXPECTED_CHECKER_SHA256[
        "compatibility"
    ]
    assert future["checker_sha256"] == EXPECTED_CHECKER_SHA256["future"]
    assert l9["checker_sha256"] == EXPECTED_CHECKER_SHA256["l9"]
    result = build_result(
        compatibility, future, l9, input_hashes, resource_policy
    )
    if args.output is None:
        json.dump(as_json(result), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        atomic_write_json(args.output, result)


if __name__ == "__main__":
    main()
