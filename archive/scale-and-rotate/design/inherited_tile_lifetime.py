#!/usr/bin/env python3
"""Exact finite owner-horizon audit for the inherited-tile guard pipeline.

This is an 18-probe experiment, not a census of all 131,097 L5--L8
stitches and not a proof of a finite-state invariant.  The probe set was fixed
before the result run.  Every probe is the middle step 122 of an inherited
tile with step signature (123,122,123):

    train L5:    523, 989
    train L6:    840, 1011, 1073, 1537, 1930, 3423, 7876, 8024, 8033
    validate L7: 1932, 13171, 21115, 3783
    holdout L8:  19872, 49039, 65694

The replay schedule bootstraps the most fragile *fragile* gap of tile zero
when one exists, then for each tile t places the fragile guard of tile t+1
before the still-unplaced gaps of tile t.  A guard exists only when its d24
size is below ``FRAGILE_CUT``; guard selection and local order use exactly
``(d24_size, gap_index)``.
Recorded connector choices are replayed; final-set triple-freeness makes every
such prefix legal.

At each probe the complete placed set is scanned.  There is no spatial or
endpoint cutoff.  For every candidate atom we record exact collision,
old--old-secant, and old--new--new-line witnesses.  The output includes exact
global/near masks, birth-age/type masks, monotone first activation and latest
redundant-witness times, and the minimum inherited-tile owner radius visible to
each killed word.  It deliberately does *not* call the latter two times
"first/last hit": a fixed-corridor poison atom is monotone, and this script
does not project one secant across a moving sequence of corridors.

Boundary anchors have both adjacent inherited tiles as possible owners.  A
multi-endpoint witness radius is minimized jointly over owner assignments;
the signed left/right Pareto frontier is retained in the witness-stream hash.

Low-priority single-core commands:

    env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/inherited_tile_lifetime.py estimate

    env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/inherited_tile_lifetime.py run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

from amplify_rich import M_BAL3  # noqa: E402
from gate_run import FRAGILE_CUT, MENU, load_domains, word_interiors  # noqa: E402
from imbricate193 import apply  # noqa: E402
from salvage_gate import (  # noqa: E402
    build_domain_model,
    cheb,
    compute_poison,
    line_key,
    mask_sha256,
    midpoint,
    primitive,
    sub,
)


PROBES = {
    "train": {5: (523, 989),
              6: (840, 1011, 1073, 1537, 1930, 3423, 7876, 8024, 8033)},
    "validate": {7: (1932, 13171, 21115, 3783)},
    "holdout": {8: (19872, 49039, 65694)},
}
ALL_PROBES = {
    level: tuple(gaps)
    for split in PROBES.values()
    for level, gaps in split.items()
}
SPLIT_OF_LEVEL = {level: split for split, levels in PROBES.items() for level in levels}
OWNER_RADII = (0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96,
               128, 192, 256, 384, 512, 768, 1024, 1536, 2048, 3072,
               4096, 6144, 8192, 12288, 16384, 24576, 32768)
# One independent reference scan is enough to check the shared atom geometry.
# Repeating the slower reference implementation on 200k+ point L8 prefixes
# adds no new code path and caused avoidable memory pressure in a pilot.
VERIFY_LEVELS = frozenset((5,))

EXPECTED_INPUT_SHA256 = {
    "viz/walk3d-data.json": "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883",
    "connector_domains4.pkl": "d3dbfd54b724b91b1391d2233931a865a5ff371789029556949c953419fa3e4f",
    "dstar5_fragile.pkl": "fe6ca45eda2874833d8257324bf7e29e2a4e855b0c4c27a9d2312702f28aefb3",
    "gate2-l7-construction-L5.pkl": "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d",
    "gate2-l7-construction-L6.pkl": "70fa3baac057492fb8ad325eba5417bdc1e98fbd474bec37dc5f5465230f9298",
    "gate2-l7-construction-L7.pkl": "304e71eb74939662c0d0251864193171e74f49fd2023a98df09dc45d99fa0660",
    "gate2-l7-construction-L8.pkl": "cc4002ebccde737ab46dc016937be4aa653620d809908d48d35bcf06fc884141",
    "gate_run.py": "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37",
    "design/salvage_gate.py": "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95",
    "amplify_rich.py": "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e",
    "imbricate193.py": "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb",
    "search193.py": "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc",
}

# Values are placed points, witness records, poisoned atoms, global survivors,
# far-only kills, maximum word/atom owner radius, maximum first-visible
# word/atom shell, and global-word/poisoned-atom/witness-stream hashes.
EXPECTED_PROBES = {
    (5, 523): (3694, 88, 82, 2516, 238, 101, 101, 3, 3,
               "17aab6053db94c6c08f938b5d63409d4777ba51f10f025072628a617d278e3e2",
               "5be577085d859732042a17d06eb3923b2937f4cba481c4dbe27fdde1b4972975",
               "46aeb06da31c215c5d9f99b0c209b8351b7ce7a6e4adf9c366f1694f7521d5fc"),
    (5, 989): (4796, 121, 104, 1367, 381, 12, 12, 2, 2,
               "3513d1309f217fa1bef3d89cfa35e9de3a39a08110d79f3148574eeabf4d1c65",
               "1d719b7fb53fc8db767c9770ad0d9c5d1296ab4620a94b277adb3477508ccf29",
               "ffc707486b816e349d14f5642f55d3a60fbbe995b849c201bf5da86801d75bd8"),
    (6, 840): (10180, 106, 96, 1412, 250, 18, 18, 2, 2,
               "b65d9d662a87cb3d71fdae4c8f708136178cb0e712aea8ead26c2cab4353e2d9",
               "59b0dd05ad747cf253109142e3faddc00018cc259f8028a7f6c958e6ba4aca23",
               "13666c480ab36ae105951180ae8d668976f34eaa89c3a07e9c1919eb334aec0e"),
    (6, 1011): (10596, 98, 90, 2301, 129, 269, 269, 4, 4,
                "bcc8b746609d3babacf75a96fca888a0b10482acb5cb2616af5b26780cd43f22",
                "dcdc8f39dc2929922e3a252bb3a7ad785194c0764ebf0cd40a909f0fb8151047",
                "4c66ae58d310b0a52d26e1bdd86ba7b1f8918dcedba3301622960b227ce1df6b"),
    (6, 1073): (10755, 122, 105, 1628, 291, 11, 11, 2, 2,
                "b4acb560bd001ec28c5e560c10de71d6b2c06ec9905b5ca0ef2e91c0da453f7b",
                "59938b084e303737e987dd6766d178a9dca985e57bbf26b9a10590eddbf81c15",
                "2ba85c42c27715faee8fe0c8e02dc506205047b363bc8ef297dd6fa7e8b1eec4"),
    (6, 1537): (11861, 112, 102, 1894, 183, 27, 27, 3, 3,
                "3c92247edc9a41078831311a4267f197701b060b86701cf0125afc167250cd32",
                "eda60a2fe148f3dd8fa5df25077b477b55404ef1c9b51935d2ab4ce68b919f48",
                "b0df5e960b622e7d43a35a498501f51af9bcc34e04b7f682531e90fa42327142"),
    (6, 1930): (12760, 122, 108, 1578, 317, 431, 431, 3, 3,
                "1b25258167ebb8626e02fc5c9d25df7a8a16ba8ec75f6a0cd87bb7f6cf832d2a",
                "a36ad8fea57a993344d47bfb3705c47c285ab4a0c021584810da4f2e7755f464",
                "6fa1bfd08a17c3f9a89e2d4ce086f8f65ba7fe34502f7b527a8b5e3e304e75af"),
    (6, 3423): (16308, 118, 107, 1238, 789, 74, 74, 3, 3,
                "87887a7f65813373855774672733a1ab8eda67623f0e02e273eaf171ac83e4bc",
                "add6ca40f62e1b49ae12d8f4b3aa588de63fb141ce252591b99187abb066b0c1",
                "fde97a0fa6fe4b75d8165e560a439066db74d9cb3284c7fe95e24fb1283adc66"),
    (6, 7876): (26876, 89, 80, 2311, 368, 625, 625, 4, 4,
                "86056420906c0ce79e178935603dea2a69180a0c8e8649c7b34bd84955316f88",
                "66943f6aec71f779b8f7a20e7c8159e3052aaa2c0aa3a211be2fd5bc2f4d376e",
                "f8cbfa3805749b73302f21238be3b5be0090c6172be17cdc997822890dfeab72"),
    (6, 8024): (27232, 123, 109, 1682, 314, 60, 61, 3, 3,
                "3a858d8b473d0f3224214dc157085d0abf085f1b4c039d0ba88f3ac6c1a21ba0",
                "51425e438b44634ae84f0babf84988ebc51bbb0ba9ed09b873d4d9bf99d23e31",
                "b0eac7bb26f0a09991e47a1a88f9cd984302cc0dfabd071a8468fb9fb66b6d13"),
    (6, 8033): (27253, 101, 91, 1423, 212, 90, 90, 4, 4,
                "f9e6946f759b8a5ada3cd8551a6076871c8ba5f8379aeb0abefa673be4beb8e3",
                "348ddec2eb7d8306e0fc669fb08374d062dac04734bcd8970a4bc4bf4763e6fc",
                "4eae9aaaaa4c9289df6236e3c65c10eba9c7bb9abc14cfa73d6cdf6073eae4cd"),
    (7, 1932): (32265, 114, 103, 1268, 144, 101, 101, 4, 4,
                "3d114409d01ea0efe9a963d78142f9df88348e3d5f53730c66cc2221d45cab91",
                "5b3aefae40a659f5ab8171d2deb6e02b9c7b78b4ba2a6a833c40b61c14cdc655",
                "3535e0dd038bf1fa0bf45e73657220bdcb52cad9125c46836f30c1e306ef6428"),
    (7, 3783): (36596, 169, 135, 403, 485, 20, 20, 2, 2,
                "b16faafedf67753a7194fa8678b44ea19c62eee0440edc246e84029c794aea06",
                "b46c62779d72cad193c3ed7b74bc042092c0f5717f8c010c24c0725089ac56a0",
                "413355ee86246de4dbb50c393dccfa7dddea140e94d5a20c27db31cf71798a7b"),
    (7, 13171): (58609, 105, 90, 1763, 679, 255, 255, 5, 5,
                 "bd2872120ca3e3c2b64a05a6189bf56a2b5f1a0ea6724817054d9a1c877dfa32",
                 "9bc6bda5b61e286dffb7091bd90cc3f1b58a8bfec94cef833018ba2e6883a354",
                 "b8c8d6d127b7cdde004efbd139a278e4220ce296df1c092e0f118999f9cedaeb"),
    (7, 21115): (77467, 143, 118, 1518, 539, 342, 342, 5, 5,
                 "e9b4ab7ae8bf64b4129a9e0dfe3951de5ab827b727a81f99a9621418e344e923",
                 "54f822dab951e37c985893ce7781cecbff6aa1b1f77f28b84aad1fec62de1824",
                 "e5e1c77bb2e83af6956af0c7c7efcb8fd5c315cdba94c8a0753673a816bd0107"),
    (8, 19872): (139725, 148, 122, 1508, 459, 18, 36, 2, 3,
                 "0b4b8ee1d081ab86f3ebb3ee02a2ba4cff672994ade8639d081e6caa2e8af31c",
                 "05e6517e67a787834b58756e3e78218b15daa83839d9f49bf9f420aea2139f04",
                 "36dea96f93acea3cffaf98ec8afd7c2bdc7a8980f5a78a34ac9f1e2169c1af12"),
    (8, 49039): (208507, 158, 134, 849, 308, 61, 61, 3, 3,
                 "24d27cb7aabe915315872640058ff3182fad06ec911ea64550bf111a4f728a3e",
                 "199251f5ed6a6cd0367202b7ff8e4f3c7c58aca1cafa06885473e2bd73521ed8",
                 "b848fde406af87c9479cee86486bc9afc73f4711c859a8a40fbf57bab2d4e329"),
    (8, 65694): (247564, 129, 111, 1513, 367, 7, 7, 1, 1,
                 "eb43d5705b286c513d49bded059c699cfd91f4e51172dc34a4ddf22ae355ce3b",
                 "5c1c6a07a303cf9c4b22189a5cbca9ef5d17f3b6b08935de36a3531aac1d6bfa",
                 "c62481b1860e2f717fbf24028fa1ee415b129eb2b96578203816d17d5fb66da8"),
}


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def bits_sha256(bits, size):
    return hashlib.sha256(bits.to_bytes((size + 7) // 8, "little")).hexdigest()


def bits_count_hash(bits, size):
    return {"words": bits.bit_count(), "mask_sha256": bits_sha256(bits, size)}


def finite_threshold_sha256(values):
    digest = hashlib.sha256()
    for value in values:
        encoded = 0xFFFFFFFF if math.isinf(value) else int(value)
        digest.update(struct.pack("<I", encoded))
    return digest.hexdigest()


def hist(values):
    return dict(sorted(Counter(str(v) for v in values).items()))


def distance_shell(distance):
    """0 for d<=40; j>=1 for 40*3^(j-1) < d <= 40*3^j."""
    if distance <= 40:
        return 0
    shell = 1
    ceiling = 120
    while distance > ceiling:
        shell += 1
        ceiling *= 3
    return shell


def load_viz():
    return json.loads((ROOT / "viz/walk3d-data.json").read_text())


def load_state(level):
    with (ROOT / f"gate2-l7-construction-L{level}.pkl").open("rb") as f:
        return pickle.load(f)


def exact_birth_levels(viz):
    """Recover exact point birth levels from the full L0--L8 ancestry."""
    births = {0: [0] * len(viz["levels"][0]["points"])}
    for level in range(1, 9):
        parents = viz["levels"][level]["parents"]
        points = [tuple(p) for p in viz["levels"][level]["points"]]
        old_points = [tuple(p) for p in viz["levels"][level - 1]["points"]]
        out = []
        for j, parent in enumerate(parents):
            first = j == 0 or parents[j - 1] != parent
            if first:
                assert points[j] == apply(M_BAL3, old_points[parent])
                out.append(births[level - 1][parent])
            else:
                out.append(level)
        births[level] = out
    return births


def tile_layout(level, state, viz):
    """Return gap tiles and exact adjacent-owner options for every anchor."""
    parents = viz["levels"][level - 1]["parents"]
    assert len(parents) == len(state["anchors"])
    assert len(state["parent_word"]) + 1 == len(parents)
    assert all(a <= b for a, b in zip(parents, parents[1:]))

    tile_gaps = defaultdict(list)
    for gap in range(len(state["parent_word"])):
        tile_gaps[parents[gap]].append(gap)
    tile_gaps = {tile: tuple(gaps) for tile, gaps in sorted(tile_gaps.items())}
    assert tuple(tile_gaps) == tuple(range(len(tile_gaps)))
    for gaps in tile_gaps.values():
        assert tuple(range(gaps[0], gaps[-1] + 1)) == gaps

    last_tile = len(tile_gaps) - 1
    owners = []
    for j, tile in enumerate(parents):
        boundary = j == 0 or parents[j - 1] != tile
        if boundary:
            choices = {tile}
            if tile > 0:
                choices.add(tile - 1)
            choices = {x for x in choices if 0 <= x <= last_tile}
        else:
            choices = {min(tile, last_tile)}
        owners.append(tuple(sorted(choices)))
    return tile_gaps, owners


def pipeline_schedule(state, tile_gaps, d24):
    guards = {}
    for tile, gaps in tile_gaps.items():
        fragile = [gap for gap in gaps
                   if d24[state["parent_word"][gap]] < FRAGILE_CUT]
        if fragile:
            guards[tile] = min(
                fragile,
                key=lambda gap: (d24[state["parent_word"][gap]], gap),
            )
    entries = []
    placed = set()

    def place(gap, sweep_tile, phase):
        if gap in placed:
            return
        entries.append({"gap": gap, "sweep_tile": sweep_tile, "phase": phase})
        placed.add(gap)

    if 0 in guards:
        place(guards[0], 0, "bootstrap-guard")
    for tile, gaps in tile_gaps.items():
        if tile + 1 in guards:
            place(guards[tile + 1], tile, "next-tile-guard")
        for gap in sorted(gaps, key=lambda i: (d24[state["parent_word"][i]], i)):
            place(gap, tile, "finish-current-tile")
    assert len(entries) == len(state["parent_word"])
    assert placed == set(range(len(state["parent_word"])))
    return entries, guards


def pareto_spans(owner_options, completion_tile):
    """Exact nondominated signed (left,right) spans over owner assignments."""
    spans = {(0, 0)}
    for options in owner_options:
        nxt = set()
        for left, right in spans:
            for owner in options:
                nxt.add((max(left, completion_tile - owner, 0),
                         max(right, owner - completion_tile, 0)))
        spans = {
            pair for pair in nxt
            if not any(other != pair and other[0] <= pair[0] and other[1] <= pair[1]
                       for other in nxt)
        }
    return tuple(sorted(spans))


def blank_info(n):
    return [
        {"threshold": math.inf, "owner_radius": math.inf,
         "first_visible_max_shell": math.inf,
         "first_activation": None, "latest_redundant": None,
         "categories": {}, "shell_categories": {}, "pareto": set()}
        for _ in range(n)
    ]


def update_range(record, activation, sweep_tile, radius, spans, distance):
    hit = (activation, -1 if sweep_tile is None else sweep_tile)
    if record.get("first_activation") is None or hit < record["first_activation"]:
        record["first_activation"] = hit
    if record.get("latest_redundant") is None or hit > record["latest_redundant"]:
        record["latest_redundant"] = hit
    record["owner_radius"] = min(record.get("owner_radius", math.inf), radius)
    record["threshold"] = min(record.get("threshold", math.inf), distance)
    combined = record.setdefault("pareto", set()) | set(spans)
    record["pareto"] = {
        pair for pair in combined
        if not any(other != pair and other[0] <= pair[0] and other[1] <= pair[1]
                   for other in combined)
    }


def record_witness(info, atom, witness_type, endpoint_profiles, activation,
                   sweep_tile, completion_tile, distance, stream):
    """Record one witness with birth/owner/placement correlated per endpoint.

    An endpoint profile is ``(level_age, owner_options, placement_action,
    placement_sweep_tile_or_None, corridor_distance)``.  Its exact distance
    shell is appended here.  The witness is geometrically unoriented, so its
    endpoint profiles are canonically sorted only after retaining every
    correlated field.
    """
    endpoint_profiles = tuple(sorted(
        (age, tuple(owners), action, -1 if sweep is None else sweep,
         endpoint_distance, distance_shell(endpoint_distance))
        for age, owners, action, sweep, endpoint_distance in endpoint_profiles
    ))
    ages = tuple(sorted(profile[0] for profile in endpoint_profiles))
    age_shells = tuple(sorted((profile[0], profile[5])
                              for profile in endpoint_profiles))
    owner_options = tuple(profile[1] for profile in endpoint_profiles)
    spans = pareto_spans(owner_options, completion_tile)
    radius = min(max(left, right) for left, right in spans)
    key = witness_type + ":" + ",".join(map(str, ages))
    shell_key = witness_type + ":" + ",".join(
        f"age{age}@shell{shell}" for age, shell in age_shells
    )
    update_range(info[atom], activation, sweep_tile, radius, spans, distance)
    info[atom]["first_visible_max_shell"] = min(
        info[atom]["first_visible_max_shell"],
        max(shell for _age, shell in age_shells),
    )
    category = info[atom]["categories"].setdefault(
        key, {"threshold": math.inf, "owner_radius": math.inf,
              "first_activation": None, "latest_redundant": None,
              "pareto": set()})
    update_range(category, activation, sweep_tile, radius, spans, distance)
    shell_category = info[atom]["shell_categories"].setdefault(
        shell_key, {"threshold": math.inf, "owner_radius": math.inf,
                    "first_activation": None, "latest_redundant": None,
                    "pareto": set()})
    update_range(shell_category, activation, sweep_tile, radius, spans, distance)
    stream.append((atom, witness_type, endpoint_profiles, activation,
                   -1 if sweep_tile is None else sweep_tile, spans, distance))


def exact_witness_scan(model, start, corridor_midpoint, points, births,
                       activation_actions, activation_sweeps, owner_options,
                       level, completion_tile):
    """Complete exact poison scan with correlated witness provenance."""
    info = blank_info(len(model["atom_desc"]))
    point_index = {p: j for j, p in enumerate(points)}
    assert len(point_index) == len(points)
    distances = [cheb(p, corridor_midpoint) for p in points]
    stream = []

    for offset, atom in model["site_id"].items():
        q = (start[0] + offset[0], start[1] + offset[1], start[2] + offset[2])
        collision = point_index.get(q)
        if collision is not None:
            j = collision
            record_witness(
                info, atom, "collision",
                ((level - births[j], owner_options[j], activation_actions[j],
                  activation_sweeps[j], distances[j]),),
                activation_actions[j], activation_sweeps[j], completion_tile,
                distances[j], stream,
            )

        seen = {}
        for j, p in enumerate(points):
            if p == q:
                continue
            direction = primitive(sub(p, q))
            old = seen.get(direction)
            if old is None:
                seen[direction] = j
                continue
            # Three points in one bucket would be three collinear placed points.
            assert not isinstance(old, tuple)
            seen[direction] = (old, j)
            activation = max(activation_actions[old], activation_actions[j])
            if activation < 0:
                sweep = None
            elif activation_actions[old] >= activation_actions[j]:
                sweep = activation_sweeps[old]
            else:
                sweep = activation_sweeps[j]
            record_witness(
                info, atom, "old-old-secant", (
                    (level - births[old], owner_options[old],
                     activation_actions[old], activation_sweeps[old],
                     distances[old]),
                    (level - births[j], owner_options[j],
                     activation_actions[j], activation_sweeps[j], distances[j]),
                ), activation, sweep, completion_tile,
                max(distances[old], distances[j]), stream,
            )
        seen.clear()

    for j, p in enumerate(points):
        rel = sub(p, start)
        for direction, by_moment in model["line_by_direction"].items():
            atom = by_moment.get((
                rel[1] * direction[2] - rel[2] * direction[1],
                rel[2] * direction[0] - rel[0] * direction[2],
                rel[0] * direction[1] - rel[1] * direction[0],
            ))
            if atom is not None:
                record_witness(
                    info, atom, "old-new-new-line", (
                        (level - births[j], owner_options[j],
                         activation_actions[j], activation_sweeps[j], distances[j]),
                    ), activation_actions[j], activation_sweeps[j],
                    completion_tile, distances[j], stream,
                )

    stream.sort()
    stream_hash = hashlib.sha256(
        json.dumps(stream, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return info, len(stream), stream_hash


def analyze_probe(level, gap, state, model, domain, points, births,
                  activation_actions, activation_sweeps, owner_options,
                  entry, action_rank, tile_gaps, guards, verify):
    tile = next(tile for tile, gaps in tile_gaps.items() if gap in gaps)
    gaps = tile_gaps[tile]
    assert len(gaps) == 3 and gaps[1] == gap
    assert tuple(state["parent_word"][i] for i in gaps) == (123, 122, 123)
    assert state["parent_word"][gap] == 122

    start = state["anchors"][gap]
    middle = midpoint(start, state["anchors"][gap + 1])
    info, witness_count, witness_hash = exact_witness_scan(
        model, start, middle, points, births, activation_actions,
        activation_sweeps, owner_options, level, tile,
    )
    poisoned = {a for a, rec in enumerate(info) if math.isfinite(rec["threshold"])}

    atom_word_bits = [0] * len(info)
    for wi, atoms in enumerate(model["word_atoms"]):
        bit = 1 << wi
        for atom in atoms:
            atom_word_bits[atom] |= bit
    full_bits = 0
    category_bits = defaultdict(int)
    shell_category_word_bits = defaultdict(int)
    shell_category_atom_bits = defaultdict(int)
    for atom in poisoned:
        full_bits |= atom_word_bits[atom]
        for category in info[atom]["categories"]:
            category_bits[category] |= atom_word_bits[atom]
        for descriptor in info[atom]["shell_categories"]:
            shell_category_word_bits[descriptor] |= atom_word_bits[atom]
            shell_category_atom_bits[descriptor] |= 1 << atom

    word_distance = []
    word_owner_radius = []
    word_first_visible_shell = []
    for atoms in model["word_atoms"]:
        word_distance.append(min((info[a]["threshold"] for a in atoms), default=math.inf))
        word_owner_radius.append(min((info[a]["owner_radius"] for a in atoms), default=math.inf))
        word_first_visible_shell.append(min(
            (info[a]["first_visible_max_shell"] for a in atoms),
            default=math.inf,
        ))

    near_bits = sum(1 << wi for wi, d in enumerate(word_distance) if d <= 40)
    owner_masks = {}
    for radius in OWNER_RADII:
        bits = sum(1 << wi for wi, r in enumerate(word_owner_radius) if r <= radius)
        owner_masks[str(radius)] = bits_count_hash(bits, len(domain))

    atom_owner_radii = [info[a]["owner_radius"] for a in range(len(info))]
    poisoned_atom_entries = [
        {
            "atom_id": atom,
            "atom_type": model["atom_desc"][atom][0],
            "minimum_owner_radius": int(info[atom]["owner_radius"]),
        }
        for atom in sorted(poisoned)
    ]
    atom_owner_masks = {}
    for radius in OWNER_RADII:
        bits = sum(1 << atom for atom in poisoned
                   if info[atom]["owner_radius"] <= radius)
        atom_owner_masks[str(radius)] = bits_count_hash(bits, len(info))
    poisoned_atom_radius_bits = sum(1 << atom for atom in poisoned)

    shell_descriptors = {
        descriptor: {
            "atom_membership": bits_count_hash(
                shell_category_atom_bits[descriptor], len(info)
            ),
            "word_membership": bits_count_hash(
                shell_category_word_bits[descriptor], len(domain)
            ),
        }
        for descriptor in sorted(shell_category_word_bits)
    }
    atom_first_shell = [info[a]["first_visible_max_shell"] for a in range(len(info))]
    max_atom_shell = max(int(atom_first_shell[a]) for a in poisoned)
    finite_word_shells = [int(shell) for shell in word_first_visible_shell
                          if math.isfinite(shell)]
    max_word_shell = max(finite_word_shells)
    atom_shell_disjoint = {}
    atom_shell_cumulative = {}
    word_shell_disjoint = {}
    word_shell_cumulative = {}
    for shell in range(max(max_atom_shell, max_word_shell) + 1):
        atom_exact = sum(1 << atom for atom in poisoned
                         if atom_first_shell[atom] == shell)
        atom_upto = sum(1 << atom for atom in poisoned
                        if atom_first_shell[atom] <= shell)
        word_exact = sum(1 << wi for wi, value in enumerate(word_first_visible_shell)
                         if value == shell)
        word_upto = sum(1 << wi for wi, value in enumerate(word_first_visible_shell)
                        if value <= shell)
        atom_shell_disjoint[str(shell)] = bits_count_hash(atom_exact, len(info))
        atom_shell_cumulative[str(shell)] = bits_count_hash(atom_upto, len(info))
        word_shell_disjoint[str(shell)] = bits_count_hash(word_exact, len(domain))
        word_shell_cumulative[str(shell)] = bits_count_hash(word_upto, len(domain))
    assert atom_upto == poisoned_atom_radius_bits
    assert word_upto == full_bits
    assert sum(item["words"] for item in atom_shell_disjoint.values()) == len(poisoned)
    assert sum(item["words"] for item in word_shell_disjoint.values()) == full_bits.bit_count()

    categories = {}
    for key, bits in sorted(category_bits.items()):
        records = [rec["categories"][key] for rec in info if key in rec["categories"]]
        first_action = [
            "initial" if rec["first_activation"][0] < 0
            else action_rank - rec["first_activation"][0]
            for rec in records
        ]
        latest_action = [
            "initial" if rec["latest_redundant"][0] < 0
            else action_rank - rec["latest_redundant"][0]
            for rec in records
        ]
        first_sweep = [
            "initial" if rec["first_activation"][0] < 0
            else entry["sweep_tile"] - rec["first_activation"][1]
            for rec in records
        ]
        latest_sweep = [
            "initial" if rec["latest_redundant"][0] < 0
            else entry["sweep_tile"] - rec["latest_redundant"][1]
            for rec in records
        ]
        categories[key] = {
            "atom_memberships": len(records),
            "killed_word_membership": bits_count_hash(bits, len(domain)),
            "first_activation_action_lag": hist(first_action),
            "latest_redundant_witness_action_lag": hist(latest_action),
            "first_activation_sweep_tile_lag": hist(first_sweep),
            "latest_redundant_witness_sweep_tile_lag": hist(latest_sweep),
            "minimum_owner_radius": hist(rec["owner_radius"] for rec in records),
        }

    if verify:
        reference = compute_poison(model, start, middle, points, births, level)
        reference_poisoned = {a for a, rec in enumerate(reference)
                              if math.isfinite(rec["threshold"])}
        assert poisoned == reference_poisoned

    chosen_index = domain.index(state["words"][gap])
    assert not (full_bits >> chosen_index) & 1
    finite_owner = [r for r in word_owner_radius if math.isfinite(r)]
    return {
        "split": SPLIT_OF_LEVEL[level],
        "level": level,
        "gap": gap,
        "step": state["parent_word"][gap],
        "completion_tile": tile,
        "completion_sweep_tile": entry["sweep_tile"],
        "completion_phase": entry["phase"],
        "action_rank": action_rank,
        "tile_gaps": list(gaps),
        "tile_signature": [state["parent_word"][i] for i in gaps],
        "tile_guard": guards.get(tile),
        "next_tile_guard": guards.get(tile + 1),
        "placed_points": len(points),
        "domain_size": len(domain),
        "candidate_atoms": {"sites": len(model["site_id"]),
                            "lines": len(model["line_id"])},
        "witness_records": witness_count,
        "witness_stream_sha256": witness_hash,
        "poisoned_atoms": len(poisoned),
        "poisoned_atom_minimum_owner_radius": {
            "bit_order": "atom id is bit (id mod 8) of byte floor(id/8)",
            "entries": poisoned_atom_entries,
            "all_poisoned_mask": bits_count_hash(
                poisoned_atom_radius_bits, len(info)
            ),
            "maximum": max(entry["minimum_owner_radius"]
                           for entry in poisoned_atom_entries),
            "vector_all_atoms_uint32_sha256": finite_threshold_sha256(
                atom_owner_radii
            ),
            "cumulative_atom_masks": atom_owner_masks,
        },
        "correlated_type_age_spatial_shell_contributions": {
            "overlap_semantics": (
                "any-witness memberships overlap across descriptors; endpoint "
                "age and shell stay correlated within each descriptor"
            ),
            "descriptors": shell_descriptors,
        },
        "first_visible_max_spatial_shell": {
            "semantics": (
                "minimum, over witnesses of an atom and then atoms of a word, "
                "of the maximum endpoint shell; disjoint masks partition the "
                "poisoned atoms or killed words"
            ),
            "atom": {
                "maximum": max_atom_shell,
                "histogram": hist("unpoisoned" if math.isinf(value) else int(value)
                                  for value in atom_first_shell),
                "vector_all_atoms_uint32_sha256": finite_threshold_sha256(
                    atom_first_shell
                ),
                "disjoint_masks": atom_shell_disjoint,
                "cumulative_masks": atom_shell_cumulative,
            },
            "word": {
                "maximum": max_word_shell,
                "histogram": hist("unpoisoned" if math.isinf(value) else int(value)
                                  for value in word_first_visible_shell),
                "vector_all_words_uint32_sha256": finite_threshold_sha256(
                    word_first_visible_shell
                ),
                "disjoint_masks": word_shell_disjoint,
                "cumulative_masks": word_shell_cumulative,
            },
        },
        "global_killed": bits_count_hash(full_bits, len(domain)),
        "global_survivors": len(domain) - full_bits.bit_count(),
        "near_D40_killed": bits_count_hash(near_bits, len(domain)),
        "far_unique_kills": (full_bits & ~near_bits).bit_count(),
        "chosen_domain_index": chosen_index,
        "chosen_global_legal": True,
        "word_minimum_owner_radius": {
            "histogram": hist("unpoisoned" if math.isinf(r) else int(r)
                              for r in word_owner_radius),
            "vector_uint32_sha256": finite_threshold_sha256(word_owner_radius),
            "maximum_finite": max(finite_owner, default=None),
            "cumulative_masks": owner_masks,
        },
        "word_first_spatial_witness_distance": {
            "histogram": hist("unpoisoned" if math.isinf(d) else int(d)
                              for d in word_distance),
            "vector_uint32_sha256": finite_threshold_sha256(word_distance),
        },
        "birth_age_and_type_contribution_masks_overlap": True,
        "birth_age_and_type_contribution_semantics": (
            "membership masks overlap: one word/atom may have witnesses in "
            "multiple type-and-age categories"
        ),
        "birth_age_and_type_contributions": categories,
        "reference_compute_poison_verified": verify,
    }


def build_context(level, viz, births_by_level, d24):
    state = load_state(level)
    expected = [apply(M_BAL3, tuple(p)) for p in viz["levels"][level - 1]["points"]]
    assert state["anchors"] == expected
    tile_gaps, anchor_owners = tile_layout(level, state, viz)
    schedule, guards = pipeline_schedule(state, tile_gaps, d24)
    return state, tile_gaps, anchor_owners, schedule, guards


def estimate(doms, d24, viz, births_by_level, model, selected):
    rows = []
    total_site = total_line = verify_extra = 0
    for level, probes in selected.items():
        state, tile_gaps, _owners, schedule, _guards = build_context(
            level, viz, births_by_level, d24)
        prefix_interiors = 0
        wanted = set(probes)
        for rank, entry in enumerate(schedule):
            gap = entry["gap"]
            if gap in wanted:
                placed = len(state["anchors"]) + prefix_interiors
                site_ops = placed * len(model["site_id"])
                line_ops = placed * len(model["line_by_direction"])
                rows.append({"level": level, "gap": gap, "action_rank": rank,
                             "placed_points": placed,
                             "site_direction_scans": site_ops,
                             "line_moment_lookups": line_ops,
                             "reference_verification": (
                                 level in VERIFY_LEVELS and gap == ALL_PROBES[level][0]
                             )})
                total_site += site_ops
                total_line += line_ops
                if level in VERIFY_LEVELS and gap == ALL_PROBES[level][0]:
                    verify_extra += site_ops + line_ops
            prefix_interiors += len(state["words"][gap]) - 1
    return {
        "status": "operation-count estimate; no poison geometry scanned",
        "probes": rows,
        "candidate_sites": len(model["site_id"]),
        "candidate_line_directions": len(model["line_by_direction"]),
        "site_direction_scans": total_site,
        "line_moment_lookups": total_line,
        "reference_verification_extra_scans": verify_extra,
        "total_geometric_inner_iterations": total_site + total_line + verify_extra,
    }


def run_experiment(doms, d24, viz, births_by_level, model, selected):
    domain = doms[122]
    results = []
    for level, probes in selected.items():
        state, tile_gaps, anchor_owners, schedule, guards = build_context(
            level, viz, births_by_level, d24)
        points = list(state["anchors"])
        births = list(births_by_level[level - 1])
        activation_actions = [-1] * len(points)
        activation_sweeps = [None] * len(points)
        owner_options = list(anchor_owners)
        gap_tile = {gap: tile for tile, gaps in tile_gaps.items() for gap in gaps}
        wanted = set(probes)
        for rank, entry in enumerate(schedule):
            gap = entry["gap"]
            if gap in wanted:
                print(f"exact L{level} gap {gap}: {len(points)} placed", flush=True)
                results.append(analyze_probe(
                    level, gap, state, model, domain, points, births,
                    activation_actions, activation_sweeps, owner_options,
                    entry, rank, tile_gaps, guards,
                    level in VERIFY_LEVELS and gap == ALL_PROBES[level][0],
                ))
            interiors = word_interiors(state["anchors"][gap], state["words"][gap])
            tile = gap_tile[gap]
            points.extend(interiors)
            births.extend([level] * len(interiors))
            activation_actions.extend([rank] * len(interiors))
            activation_sweeps.extend([entry["sweep_tile"]] * len(interiors))
            owner_options.extend([(tile,)] * len(interiors))
        assert len(points) == len(set(points))
        final = {tuple(p) for p in viz["levels"][level]["points"]}
        assert set(points) == final

    # Freeze the only learned horizon/codebook on L5--L6, then classify L7/L8.
    training = [r for r in results if r["split"] == "train"]
    complete_training = all(
        set(selected.get(level, ())) == set(gaps)
        for level, gaps in PROBES["train"].items()
    )
    horizon = (max(r["word_minimum_owner_radius"]["maximum_finite"]
                   for r in training) if complete_training else None)
    atom_horizon = (max(r["poisoned_atom_minimum_owner_radius"]["maximum"]
                        for r in training) if complete_training else None)
    atom_shell_horizon = (max(r["first_visible_max_spatial_shell"]["atom"]["maximum"]
                              for r in training) if complete_training else None)
    word_shell_horizon = (max(r["first_visible_max_spatial_shell"]["word"]["maximum"]
                              for r in training) if complete_training else None)
    codebook = sorted({key for r in training
                       for key in r["birth_age_and_type_contributions"]})
    for result in results:
        radius_hist = result["word_minimum_owner_radius"]["histogram"]
        beyond = (sum(count for key, count in radius_hist.items()
                      if key != "unpoisoned" and int(key) > horizon)
                  if horizon is not None else None)
        categories = set(result["birth_age_and_type_contributions"])
        beyond_atom_ids = [
            entry["atom_id"]
            for entry in result["poisoned_atom_minimum_owner_radius"]["entries"]
            if atom_horizon is not None
            and entry["minimum_owner_radius"] > atom_horizon
        ]
        beyond_atom_bits = sum(1 << atom for atom in beyond_atom_ids)
        atom_shell_hist = result["first_visible_max_spatial_shell"]["atom"]["histogram"]
        word_shell_hist = result["first_visible_max_spatial_shell"]["word"]["histogram"]
        result["frozen_training_comparison"] = {
            "training_owner_radius_horizon": horizon,
            "killed_words_beyond_training_horizon": beyond,
            "training_poisoned_atom_owner_radius_horizon": atom_horizon,
            "poisoned_atoms_beyond_training_atom_horizon": {
                "atom_ids": beyond_atom_ids if atom_horizon is not None else None,
                "count": len(beyond_atom_ids) if atom_horizon is not None else None,
                "mask_sha256": (bits_sha256(beyond_atom_bits,
                                             sum(result["candidate_atoms"].values()))
                                if atom_horizon is not None else None),
            },
            "training_first_visible_atom_shell_horizon": atom_shell_horizon,
            "poisoned_atoms_beyond_training_shell_horizon": (
                sum(count for key, count in atom_shell_hist.items()
                    if key != "unpoisoned" and int(key) > atom_shell_horizon)
                if atom_shell_horizon is not None else None
            ),
            "training_first_visible_word_shell_horizon": word_shell_horizon,
            "killed_words_beyond_training_shell_horizon": (
                sum(count for key, count in word_shell_hist.items()
                    if key != "unpoisoned" and int(key) > word_shell_horizon)
                if word_shell_horizon is not None else None
            ),
            "new_birth_age_type_categories": sorted(categories - set(codebook)),
        }
    return {
        "training_freeze": {
            "levels": [5, 6],
            "complete": complete_training,
            "owner_radius_horizon": horizon,
            "poisoned_atom_owner_radius_horizon": atom_horizon,
            "first_visible_atom_shell_horizon": atom_shell_horizon,
            "first_visible_word_shell_horizon": word_shell_horizon,
            "birth_age_type_codebook": codebook,
        },
        "probes": sorted(results, key=lambda r: (r["level"], r["gap"])),
    }


def assert_expected_result(experiment):
    """Pin the fixed-before-run canonical all-18 certificate."""
    freeze = experiment["training_freeze"]
    assert freeze["complete"] is True
    assert freeze["owner_radius_horizon"] == 625
    assert freeze["poisoned_atom_owner_radius_horizon"] == 625
    assert freeze["first_visible_word_shell_horizon"] == 4
    assert freeze["first_visible_atom_shell_horizon"] == 4

    observed = {}
    by_key = {}
    for result in experiment["probes"]:
        key = (result["level"], result["gap"])
        by_key[key] = result
        observed[key] = (
            result["placed_points"],
            result["witness_records"],
            result["poisoned_atoms"],
            result["global_survivors"],
            result["far_unique_kills"],
            result["word_minimum_owner_radius"]["maximum_finite"],
            result["poisoned_atom_minimum_owner_radius"]["maximum"],
            result["first_visible_max_spatial_shell"]["word"]["maximum"],
            result["first_visible_max_spatial_shell"]["atom"]["maximum"],
            result["global_killed"]["mask_sha256"],
            result["poisoned_atom_minimum_owner_radius"]["all_poisoned_mask"][
                "mask_sha256"
            ],
            result["witness_stream_sha256"],
        )
    assert observed == EXPECTED_PROBES

    for result in experiment["probes"]:
        comparison = result["frozen_training_comparison"]
        assert comparison["killed_words_beyond_training_horizon"] == 0
        assert comparison["poisoned_atoms_beyond_training_atom_horizon"]["count"] == 0

    first = by_key[(7, 13171)]
    first_shell = first["first_visible_max_spatial_shell"]
    assert first["frozen_training_comparison"][
        "killed_words_beyond_training_shell_horizon"
    ] == 56
    assert first["frozen_training_comparison"][
        "poisoned_atoms_beyond_training_shell_horizon"
    ] == 1
    assert first_shell["atom"]["disjoint_masks"]["5"] == {
        "words": 1,
        "mask_sha256": "0a5c572013b7ede759992c27e219f0dd6fb93895ce072187f0e64bea71b53359",
    }
    assert first_shell["word"]["disjoint_masks"]["5"] == {
        "words": 56,
        "mask_sha256": "51fae9aa4965bcb0e866eb1affcb454e5cc48b8f5a785f608fb2a6b853f6fbc9",
    }
    first_descriptor = first[
        "correlated_type_age_spatial_shell_contributions"
    ]["descriptors"]["old-old-secant:age0@shell4,age0@shell5"]
    assert first_descriptor["atom_membership"] == {
        "words": 1,
        "mask_sha256": "0a5c572013b7ede759992c27e219f0dd6fb93895ce072187f0e64bea71b53359",
    }
    assert first_descriptor["word_membership"] == {
        "words": 154,
        "mask_sha256": "d2abd53fcdf66a9f11b519a01b6a139090dc8d2b04eab14129e4dbe85d068594",
    }

    second = by_key[(7, 21115)]
    second_shell = second["first_visible_max_spatial_shell"]
    assert second["frozen_training_comparison"][
        "killed_words_beyond_training_shell_horizon"
    ] == 9
    assert second["frozen_training_comparison"][
        "poisoned_atoms_beyond_training_shell_horizon"
    ] == 1
    assert second_shell["atom"]["disjoint_masks"]["5"] == {
        "words": 1,
        "mask_sha256": "f0661d94412380d97d720cc403bbe87f25211529839f0e9cac4fc90b9dc9f91d",
    }
    assert second_shell["word"]["disjoint_masks"]["5"] == {
        "words": 9,
        "mask_sha256": "cbc8c345b46f680f9354bf3991d52c7798da7656d12d4b22f41b9ba6170d9e9a",
    }
    second_descriptor = second[
        "correlated_type_age_spatial_shell_contributions"
    ]["descriptors"]["old-new-new-line:age0@shell5"]
    assert second_descriptor["atom_membership"] == {
        "words": 1,
        "mask_sha256": "f0661d94412380d97d720cc403bbe87f25211529839f0e9cac4fc90b9dc9f91d",
    }
    assert second_descriptor["word_membership"] == {
        "words": 18,
        "mask_sha256": "1c212c13f571c08847ffb4dd937d543eecbd5235a4fcd97efb339cd532565237",
    }

    for key, result in by_key.items():
        if key not in ((7, 13171), (7, 21115)):
            assert result["frozen_training_comparison"][
                "killed_words_beyond_training_shell_horizon"
            ] == 0
            assert result["frozen_training_comparison"][
                "poisoned_atoms_beyond_training_shell_horizon"
            ] == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument("--output", type=Path,
                        default=ROOT / "design/inherited-tile-lifetime.json")
    parser.add_argument(
        "--only", action="append", default=[], metavar="LEVEL:GAP",
        help="smoke/phase mode: run only a fixed-manifest probe (repeatable)",
    )
    parser.add_argument(
        "--limit", type=int,
        help="smoke mode: retain only the first N fixed-manifest probes",
    )
    args = parser.parse_args()
    if sys.flags.optimize:
        raise RuntimeError("run without -O so certificate assertions remain active")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    observed_input_sha256 = {
        name: file_sha256(ROOT / name) for name in EXPECTED_INPUT_SHA256
    }
    assert observed_input_sha256 == EXPECTED_INPUT_SHA256

    selected = {level: list(gaps) for level, gaps in ALL_PROBES.items()}
    if args.only:
        requested = []
        for value in args.only:
            level, gap = map(int, value.split(":"))
            assert gap in ALL_PROBES.get(level, ()), (level, gap)
            requested.append((level, gap))
        selected = defaultdict(list)
        for level, gap in requested:
            selected[level].append(gap)
        selected = dict(selected)
    if args.limit is not None:
        assert args.limit > 0
        flat = [(level, gap) for level, gaps in selected.items() for gap in gaps]
        selected = defaultdict(list)
        for level, gap in flat[:args.limit]:
            selected[level].append(gap)
        selected = dict(selected)

    doms, d24 = load_domains()
    viz = load_viz()
    births_by_level = exact_birth_levels(viz)
    model = build_domain_model(doms[122])
    if args.mode == "estimate":
        out = estimate(doms, d24, viz, births_by_level, model, selected)
    else:
        experiment = run_experiment(
            doms, d24, viz, births_by_level, model, selected
        )
        canonical_selection = {
            level: tuple(gaps) for level, gaps in selected.items()
        } == ALL_PROBES
        if canonical_selection:
            assert_expected_result(experiment)
        out = {
            "status": ("exact finite 18-probe recorded-orbit audit; no endpoint cutoff; "
                       "not a full census or all-level proof"),
            "resource_policy": {"processes": 1, "thread_cap": 1, "nice": 15},
            "schedule": ("bootstrap guard(tile 0); for each t, guard(tile t+1), "
                         "then unplaced tile t gaps in (d24,gap) order"),
            "guard_rule": (
                "among gaps with d24_size < FRAGILE_CUT, argmin by "
                "(d24_size[parent_step], gap_index); no guard otherwise"
            ),
            "probe_preregistration": PROBES,
            "provenance_semantics": {
                "geometry": "complete global placed set; no endpoint or distance cutoff",
                "activation": ("first activation and latest redundant witness for a fixed "
                               "monotone poison atom; not moving-corridor first/last hit"),
                "owner_radius": ("joint minimum over adjacent boundary-anchor owners; signed "
                                 "left/right Pareto spans retained in witness-stream SHA-256"),
                "birth_shell": "exact level age (completion level minus point birth level)",
                "spatial_shell": ("correlated per witness endpoint: shell 0 is d<=40; "
                                  "shell j>=1 is 40*3^(j-1)<d<=40*3^j"),
                "category_masks": "overlapping memberships, never a partition",
            },
            "selected_probes": selected,
            "experiment": experiment,
        }
        out["input_sha256"] = observed_input_sha256
        out["checker_sha256"] = file_sha256(Path(__file__).resolve())

    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.mode == "run":
        args.output.write_text(text)
        print(f"wrote {args.output}", flush=True)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
