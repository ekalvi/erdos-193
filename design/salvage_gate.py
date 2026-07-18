"""Exact salvage gate for the scale-and-rotate Erdős #193 construction.

This script does two independent jobs.

``poison`` replays selected L5--L8 stitches at their exact construction-time
placed sets.  For the pending connector domain it builds the finite monotone
legality atoms

    p_q   candidate site q is occupied or lies on an old--old secant;
    l_ab  an old point lies on the line through candidate sites a and b,

then computes exact local/global killed-word masks, distance/birth-shell
attribution, and the minimum number of additional arbitrary atoms needed to
hit every currently surviving connector word.

``states`` fingerprints the single realized ordered path (including actual
connector choices only after they have been placed) and tests state/transition
stabilization across every stitch in the L5--L8 construction pickles.

The script is intentionally single-process.  Run it at low priority, e.g.

    env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 nice -n 15 \
        python3 design/salvage_gate.py all

It does not touch the constructor, walk artifacts, or PM2 website.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import sys
import time
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amplify_rich import M_BAL3  # noqa: E402
from fast_legal import Store, word_legal_fast  # noqa: E402
from gate_run import MENU, load_domains, word_interiors  # noqa: E402
from imbricate193 import apply  # noqa: E402


LOCAL_RADIUS = 40
CELL = 40
DEFAULT_TARGETS = (
    (5, 1173, "L5 sampled-floor bottleneck"),
    (6, 8006, "L6 sampled-floor bottleneck"),
    (7, 3783, "L7 tractable low-availability bottleneck"),
    (8, 0, "L8 early control"),
    (6, 2892, "ordered-state alias A"),
    (7, 1103, "ordered-state alias B"),
)

# A sequentially legal point-set completion of the exact L7 bottleneck state.
# This is deliberately a negative control, not a claim that these points arise
# from earlier connector choices in the fixed stitch order.
L7_POINT_SET_JAM = (
    (118, -10043, -2878), (118, -10043, -2877),
    (114, -10042, -2880), (116, -10041, -2878),
    (119, -10043, -2879), (119, -10044, -2877),
    (823, -10043, -2173), (119, -10042, -2878),
    (119, -10042, -2877), (492, -10420, -2504),
    (668, -11145, -1777), (2339, -11155, -657),
    (2578, -12503, -1650), (115, -10042, -2881),
    (120, -10042, -2879), (118, -10041, -2879),
    (2410, -11190, -589), (118, -10041, -2880),
    (119, -10045, -2878), (415, -10341, -2579),
)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def primitive(v):
    g = math.gcd(math.gcd(abs(v[0]), abs(v[1])), abs(v[2]))
    if g == 0:
        return None
    u = (v[0] // g, v[1] // g, v[2] // g)
    for x in u:
        if x < 0:
            return (-u[0], -u[1], -u[2])
        if x > 0:
            return u
    raise AssertionError("nonzero primitive direction lost its sign")


def line_key(a, b):
    """Canonical integer line through a,b as (primitive direction, moment)."""
    u = primitive(sub(b, a))
    if u is None:
        raise ValueError("line through a repeated point")
    return u, cross(a, u)


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def midpoint(a, b):
    return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2, (a[2] + b[2]) // 2)


def state_path(level):
    return ROOT / f"gate2-l7-construction-L{level}.pkl"


@lru_cache(maxsize=None)
def load_state(level):
    with state_path(level).open("rb") as f:
        return pickle.load(f)


@lru_cache(maxsize=None)
def built_walk_with_birth(level):
    """Return the completed level walk and each point's absolute birth level."""
    if level == 4:
        data = json.loads((ROOT / "viz/walk3d-data.json").read_text())
        points = [tuple(p) for p in data["levels"][4]["points"]]
        return points, [4] * len(points)

    parent_points, parent_birth = built_walk_with_birth(level - 1)
    st = load_state(level)
    anchors = st["anchors"]
    expected = [apply(M_BAL3, p) for p in parent_points]
    assert anchors == expected, f"L{level} anchor/parent mismatch"

    chain = [anchors[0]]
    births = [parent_birth[0]]
    for i in range(len(st["parent_word"])):
        ints = word_interiors(anchors[i], st["words"][i])
        chain.extend(ints)
        births.extend([level] * len(ints))
        chain.append(anchors[i + 1])
        births.append(parent_birth[i + 1])
    assert len(chain) == len(births)
    assert len(chain) == len(set(chain))
    return chain, births


def replay_stitch(level, segment):
    st = load_state(level)
    order = st["order"]
    try:
        pos = order.index(segment)
    except ValueError as exc:
        raise ValueError(f"segment {segment} is not in L{level}") from exc

    parent_points, parent_birth = built_walk_with_birth(level - 1)
    expected = [apply(M_BAL3, p) for p in parent_points]
    assert st["anchors"] == expected
    points = list(st["anchors"])
    births = list(parent_birth)
    for old_segment in order[:pos]:
        ints = word_interiors(st["anchors"][old_segment], st["words"][old_segment])
        points.extend(ints)
        births.extend([level] * len(ints))
    assert len(points) == len(births)
    assert len(points) == len(set(points))
    return st, pos, points, births


def build_domain_model(domain):
    """Build canonical atom ids and the atom set of every connector word."""
    site_id = {}
    line_id = {}
    atom_desc = []
    word_atoms = []

    def get_site(q):
        if q not in site_id:
            site_id[q] = len(atom_desc)
            atom_desc.append(("site", q))
        return site_id[q]

    def get_line(key):
        if key not in line_id:
            line_id[key] = len(atom_desc)
            atom_desc.append(("line", key))
        return line_id[key]

    for word in domain:
        pts = word_interiors((0, 0, 0), word)
        atoms = {get_site(q) for q in pts}
        for j, a in enumerate(pts):
            for b in pts[j + 1 :]:
                atoms.add(get_line(line_key(a, b)))
        word_atoms.append(tuple(sorted(atoms)))

    by_direction = defaultdict(dict)
    for (u, moment), atom in line_id.items():
        by_direction[u][moment] = atom
    return {
        "site_id": site_id,
        "line_id": line_id,
        "atom_desc": atom_desc,
        "word_atoms": word_atoms,
        "line_by_direction": dict(by_direction),
    }


def blank_atom_info(n):
    return [
        {
            "threshold": math.inf,
            "witness_classes": set(),
            "birth_classes": set(),
            "birth_shells": set(),
            "first_witness_classes": set(),
            "first_birth_classes": set(),
            "first_birth_shells": set(),
        }
        for _ in range(n)
    ]


def endpoint_class(d1, d2):
    if d1 <= LOCAL_RADIUS and d2 <= LOCAL_RADIUS:
        return "near-near"
    if (d1 <= LOCAL_RADIUS) != (d2 <= LOCAL_RADIUS):
        return "cross"
    return "far-far"


def birth_class(level, b1, b2=None):
    if b2 is None:
        return "old-new-new:current" if b1 == level else "old-new-new:inherited"
    current = (b1 == level) + (b2 == level)
    return ("old-old:inherited-inherited", "old-old:current-inherited",
            "old-old:current-current")[current]


def record_witness(info, threshold, witness_class, births, birth_shell):
    if threshold < info["threshold"]:
        info["threshold"] = threshold
        info["first_witness_classes"] = {witness_class}
        info["first_birth_classes"] = {births}
        info["first_birth_shells"] = {birth_shell}
    elif threshold == info["threshold"]:
        info["first_witness_classes"].add(witness_class)
        info["first_birth_classes"].add(births)
        info["first_birth_shells"].add(birth_shell)
    # These three sets deliberately retain every genuine witness membership,
    # not only witnesses attaining the first spatial threshold.  The separate
    # first_* fields above keep the two meanings correlated and unambiguous.
    info["witness_classes"].add(witness_class)
    info["birth_classes"].add(births)
    info["birth_shells"].add(birth_shell)


def compute_poison(model, start, chord_midpoint, points, births, level):
    info = blank_atom_info(len(model["atom_desc"]))
    point_index = {p: j for j, p in enumerate(points)}
    distances = [cheb(p, chord_midpoint) for p in points]
    # A poisoned site needs two old endpoints in one primitive direction.
    # Iterating endpoints in distance order makes the first repeated direction
    # attain the true minimum possible max(endpoint distance), i.e. the second
    # nearest endpoint on that unoriented line.  The old insertion-order scan
    # was globally exact (poisoned or not) but its first-shell threshold was
    # not proof-grade in general.
    point_order = sorted(range(len(points)), key=lambda j: (distances[j], j))

    # Site atoms: collision or duplicate primitive old-point direction.
    for offset, atom in model["site_id"].items():
        q = add(start, offset)
        collision = point_index.get(q)
        if collision is not None:
            b = births[collision]
            d = distances[collision]
            record_witness(info[atom], d, "collision", f"collision:{'current' if b == level else 'inherited'}",
                           (level - b,))
            continue

        seen = {}
        for j in point_order:
            p = points[j]
            u = primitive(sub(p, q))
            old = seen.get(u)
            if old is None:
                seen[u] = j
                continue
            d1, d2 = distances[old], distances[j]
            b1, b2 = births[old], births[j]
            record_witness(
                info[atom], max(d1, d2), endpoint_class(d1, d2),
                birth_class(level, b1, b2), tuple(sorted((level - b1, level - b2))),
            )

    # Line atoms: for each old point and candidate primitive direction, its
    # moment identifies at most one candidate line.
    directions = list(model["line_by_direction"].items())
    for j, p in enumerate(points):
        rel = sub(p, start)
        d = distances[j]
        b = births[j]
        for u, by_moment in directions:
            atom = by_moment.get(cross(rel, u))
            if atom is not None:
                record_witness(
                    info[atom], d,
                    "old-new-new:near" if d <= LOCAL_RADIUS else "old-new-new:far",
                    birth_class(level, b), (level - b,),
                )
    return info


def shell_label(distance):
    assert distance > LOCAL_RADIUS
    lo = LOCAL_RADIUS
    while distance > 3 * lo:
        lo *= 3
    return f"{lo}-{3 * lo}"


def mask_sha256(indices, size):
    """Stable digest of a little-endian finite word mask."""
    data = bytearray((size + 7) // 8)
    for i in indices:
        data[i >> 3] |= 1 << (i & 7)
    return hashlib.sha256(data).hexdigest()


def greedy_cover(full, covers):
    uncovered = full
    solution = []
    while uncovered:
        best = max(range(len(covers)), key=lambda j: (covers[j] & uncovered).bit_count())
        gain = covers[best] & uncovered
        if not gain:
            return None
        solution.append(best)
        uncovered &= ~covers[best]
    return solution


def reduce_cover_patterns(coverage_by_atom):
    # Equal coverages are interchangeable.  A strict subset is dominated.
    representative = {}
    for atom, bits in coverage_by_atom.items():
        if bits:
            representative.setdefault(bits, atom)
    ordered = sorted(representative, key=int.bit_count, reverse=True)
    maximal = []
    for bits in ordered:
        if any((bits | kept) == kept for kept in maximal):
            continue
        maximal.append(bits)
    return maximal, [representative[bits] for bits in maximal]


def exact_cover_distance(survivor_word_atoms, poisoned, seconds):
    n = len(survivor_word_atoms)
    if n == 0:
        return {"status": "already-fatal", "minimum": 0}

    coverage = defaultdict(int)
    for bit, atoms in enumerate(survivor_word_atoms):
        for atom in atoms:
            if atom not in poisoned:
                coverage[atom] |= 1 << bit
    covers, representatives = reduce_cover_patterns(coverage)
    full = (1 << n) - 1
    greedy = greedy_cover(full, covers)
    if greedy is None:
        return {"status": "unhittable-word", "minimum": None}
    best = [len(greedy), list(greedy)]
    deadline = time.monotonic() + seconds
    nodes = 0
    timed_out = False
    memo = {}

    options = [[] for _ in range(n)]
    option_bits = [0] * n
    for j, bits in enumerate(covers):
        x = bits
        while x:
            one = x & -x
            e = one.bit_length() - 1
            options[e].append(j)
            option_bits[e] |= 1 << j
            x ^= one

    def lower_bound(uncovered):
        remaining = uncovered.bit_count()
        max_gain = max((bits & uncovered).bit_count() for bits in covers)
        cardinal = (remaining + max_gain - 1) // max_gain

        # Any selected uncovered words with pairwise-disjoint option sets need
        # distinct atoms.  This greedy packing is a valid, if nonoptimal, bound.
        elems = []
        x = uncovered
        while x:
            one = x & -x
            e = one.bit_length() - 1
            elems.append(e)
            x ^= one
        elems.sort(key=lambda e: len(options[e]))
        used = 0
        packing = 0
        for e in elems:
            if option_bits[e] & used:
                continue
            packing += 1
            used |= option_bits[e]
        return max(cardinal, packing)

    def dfs(uncovered, chosen):
        nonlocal nodes, timed_out
        nodes += 1
        if nodes % 1024 == 0 and time.monotonic() > deadline:
            timed_out = True
            return
        if not uncovered:
            if len(chosen) < best[0]:
                best[:] = [len(chosen), list(chosen)]
            return
        if len(chosen) + lower_bound(uncovered) >= best[0]:
            return
        old_depth = memo.get(uncovered)
        if old_depth is not None and old_depth <= len(chosen):
            return
        memo[uncovered] = len(chosen)

        # Branch on the uncovered word with the fewest still-useful atoms.
        x = uncovered
        branch = None
        while x:
            one = x & -x
            e = one.bit_length() - 1
            candidates = [j for j in options[e] if covers[j] & uncovered]
            if branch is None or len(candidates) < len(branch):
                branch = candidates
            x ^= one
        branch.sort(key=lambda j: (covers[j] & uncovered).bit_count(), reverse=True)
        for j in branch:
            dfs(uncovered & ~covers[j], chosen + [j])
            if timed_out:
                return

    root_lower = lower_bound(full)
    dfs(full, [])
    selected_atoms = [representatives[j] for j in best[1]]
    return {
        "status": "timeout" if timed_out else "exact",
        "minimum_or_upper": best[0],
        "root_lower_bound": root_lower,
        "nodes": nodes,
        "raw_candidate_atoms": len(coverage),
        "maximal_coverage_patterns": len(covers),
        "one_cover_atom_ids": selected_atoms,
    }


def analyze_stitch(level, segment, label, doms, d24, cover_seconds):
    t0 = time.time()
    st, pos, points, births = replay_stitch(level, segment)
    step = st["parent_word"][segment]
    domain = doms[step]
    start = st["anchors"][segment]
    mid = midpoint(start, st["anchors"][segment + 1])
    model = build_domain_model(domain)
    info = compute_poison(model, start, mid, points, births, level)
    poisoned = {j for j, x in enumerate(info) if math.isfinite(x["threshold"])}

    thresholds = []
    survivor_indices = set()
    local_survivors = 0
    shells = Counter()
    shell_word_indices = defaultdict(set)
    witness_word_classes = Counter()
    birth_word_classes = Counter()
    birth_shell_word_classes = Counter()
    birth_shell_word_indices = defaultdict(set)
    survivor_atoms = []
    for wi, atoms in enumerate(model["word_atoms"]):
        threshold = min((info[a]["threshold"] for a in atoms), default=math.inf)
        thresholds.append(threshold)
        if threshold > LOCAL_RADIUS:
            local_survivors += 1
        if math.isinf(threshold):
            survivor_indices.add(wi)
            survivor_atoms.append(atoms)
            continue
        if threshold <= LOCAL_RADIUS:
            continue
        shell = shell_label(threshold)
        shells[shell] += 1
        shell_word_indices[shell].add(wi)
        classes = set()
        birth_classes = set()
        birth_shells = set()
        for atom in atoms:
            if math.isfinite(info[atom]["threshold"]):
                classes.update(info[atom]["witness_classes"])
                birth_classes.update(info[atom]["birth_classes"])
                birth_shells.update(info[atom]["birth_shells"])
        for cls in classes:
            witness_word_classes[cls] += 1
        for cls in birth_classes:
            birth_word_classes[cls] += 1
        for cls in birth_shells:
            key = str(cls)
            birth_shell_word_classes[key] += 1
            birth_shell_word_indices[key].add(wi)

    global_survivors = len(survivor_indices)
    global_killed_indices = {
        wi for wi, threshold in enumerate(thresholds)
        if math.isfinite(threshold)
    }
    near_killed_indices = {
        wi for wi, threshold in enumerate(thresholds)
        if threshold <= LOCAL_RADIUS
    }
    atom_type_counts = Counter(model["atom_desc"][a][0] for a in poisoned)
    cover = exact_cover_distance(survivor_atoms, poisoned, cover_seconds)

    # Independent semantic cross-check against the production legality core.
    rng = Random(f"salvage-L{level}-i{segment}")
    sample_indices = (list(range(len(domain))) if len(domain) <= 200 else
                      rng.sample(range(len(domain)), 200))
    store = Store(points)
    memo = {}
    mismatches = []
    for wi in sample_indices:
        atom_legal = wi in survivor_indices
        production_legal = word_legal_fast(start, domain[wi], store, memo, MENU)
        if atom_legal != production_legal:
            mismatches.append(wi)
    assert not mismatches, f"atom/production legality mismatch: {mismatches[:5]}"

    chosen = st["words"][segment]
    try:
        chosen_index = domain.index(chosen)
    except ValueError:
        chosen_index = None

    result = {
        "level": level,
        "segment": segment,
        "position_in_stitch_order": pos,
        "label": label,
        "step": step,
        "d24": d24[step],
        "domain_size": len(domain),
        "placed_points": len(points),
        "candidate_sites": len(model["site_id"]),
        "candidate_lines": len(model["line_id"]),
        "poisoned_atoms": dict(sorted(atom_type_counts.items())),
        "provenance_semantics": (
            "threshold and first_* fields use nearest witnesses; unprefixed "
            "witness/birth sets are exact any-witness memberships"
        ),
        "local_radius": LOCAL_RADIUS,
        "local_survivors": local_survivors,
        "global_survivors": global_survivors,
        "tail_unique_kills": local_survivors - global_survivors,
        "tail_fraction_of_local_survivors": round(
            (local_survivors - global_survivors) / local_survivors, 6
        ) if local_survivors else None,
        "tail_unique_kills_by_first_shell": dict(sorted(shells.items())),
        "tail_word_witness_classes": dict(sorted(witness_word_classes.items())),
        "tail_word_birth_classes": dict(sorted(birth_word_classes.items())),
        "tail_word_birth_shell_memberships": dict(sorted(birth_shell_word_classes.items())),
        "exact_mask_sha256": {
            "bit_order": "word i is bit (i mod 8) of byte floor(i/8)",
            "global_killed": mask_sha256(global_killed_indices, len(domain)),
            "near_D40_killed": mask_sha256(near_killed_indices, len(domain)),
            "tail_first_shell_increments": {
                key: mask_sha256(indices, len(domain))
                for key, indices in sorted(shell_word_indices.items())
            },
            "tail_birth_shell_memberships": {
                key: mask_sha256(indices, len(domain))
                for key, indices in sorted(birth_shell_word_indices.items())
            },
        },
        "chosen_word_index": chosen_index,
        "chosen_word_global_legal": chosen_index in survivor_indices if chosen_index is not None else None,
        "production_crosscheck": {"sampled_words": len(sample_indices), "mismatches": 0},
        "additional_atom_cover": cover,
        "elapsed_s": round(time.time() - t0, 3),
    }
    return result, {
        "survivor_indices": survivor_indices,
        "poisoned": poisoned,
        "domain": domain,
        "chosen_index": chosen_index,
    }


def replay_fixed_domain_jam(doms, d24):
    """Reconstruct the committed 56-point length<=4 jam exactly."""
    certificate = json.loads((ROOT / "design/attack1-certify.json").read_text())
    jam = certificate["jam"]
    base_word = jam["base_word"]
    target = jam["seg_i"]

    parent = [(0, 0, 0)]
    for si in base_word:
        parent.append(add(parent[-1], MENU[si]))
    anchors = [apply(M_BAL3, p) for p in parent]
    points = list(anchors)
    births = [0] * len(anchors)
    store = Store(anchors)
    order = sorted(range(len(base_word)), key=lambda i: (d24[base_word[i]], i))

    for pos, segment in enumerate(order):
        if segment == target:
            serialized = ";".join(
                ",".join(map(str, p)) for p in sorted(points)
            )
            digest = hashlib.sha256(serialized.encode()).hexdigest()
            assert digest == "91f82e7374975e6a68e5ddeb15b75c7222c8ba6f7639b8f931d2f76c4d384d05"
            return certificate, pos, points, births, store

        start = anchors[segment]
        memo = {}
        chosen = next(
            (word for word in doms[base_word[segment]]
             if word_legal_fast(start, word, store, memo, MENU)),
            None,
        )
        assert chosen is not None
        interiors = word_interiors(start, chosen)
        store.add_many(interiors)
        points.extend(interiors)
        births.extend([1] * len(interiors))
    raise AssertionError("committed jam target was not reached")


def analyze_fixed_domain_jam(doms, d24):
    """Independent atom-model unit test against attack1-certify.json."""
    certificate, pos, points, births, store = replay_fixed_domain_jam(doms, d24)
    jam = certificate["jam"]
    step = jam["step_idx"]
    domain = doms[step]
    start = tuple(jam["A"])
    end = tuple(jam["B"])
    model = build_domain_model(domain)
    info = compute_poison(model, start, midpoint(start, end), points, births, 1)
    poisoned = {j for j, x in enumerate(info) if math.isfinite(x["threshold"])}
    survivors = {
        wi for wi, atoms in enumerate(model["word_atoms"])
        if not poisoned.intersection(atoms)
    }

    # Exhaustive, rather than sampled, comparison with the production checker.
    production_survivors = set()
    memo = {}
    for wi, word in enumerate(domain):
        if word_legal_fast(start, word, store, memo, MENU):
            production_survivors.add(wi)
    assert survivors == production_survivors == set()
    assert jam["survivors_reference"] == jam["survivors_fast"] == 0

    thresholds = [
        min((info[a]["threshold"] for a in atoms), default=math.inf)
        for atoms in model["word_atoms"]
    ]
    near_killed = {wi for wi, value in enumerate(thresholds) if value <= LOCAL_RADIUS}
    return {
        "source": "design/attack1-certify.json",
        "level": 1,
        "segment": jam["seg_i"],
        "position_in_stitch_order": pos,
        "step": step,
        "domain_size": len(domain),
        "placed_points": len(points),
        "atom_model_survivors": len(survivors),
        "production_survivors": len(production_survivors),
        "reference_survivors": jam["survivors_reference"],
        "near_D40_survivors": len(domain) - len(near_killed),
        "global_killed_mask_sha256": mask_sha256(range(len(domain)), len(domain)),
        "point_set_sha256": "91f82e7374975e6a68e5ddeb15b75c7222c8ba6f7639b8f931d2f76c4d384d05",
        "fixed_domain_max_word_length": 4,
        "certified_escape_length": len(jam["exhaustive"]["found"]),
        "certified_escape_word": jam["exhaustive"]["found"],
        "interpretation": (
            "exact fixed-domain jam; not an all-length jam and not claimed "
            "reachable in the L5-L8 realized orbit"
        ),
    }


def analyze_l7_point_set_jam(doms):
    """Verify the exact but not connector-reachable L7 completion jam."""
    st, pos, points, _births = replay_stitch(7, 3783)
    assert len(points) == 70_334
    store = Store(points)
    for point in L7_POINT_SET_JAM:
        assert store.legal(point), f"point-set jam witness is illegal: {point}"
        store.add_many([point])

    start = st["anchors"][3783]
    domain = doms[st["parent_word"][3783]]
    survivors = []
    memo = {}
    for wi, word in enumerate(domain):
        if word_legal_fast(start, word, store, memo, MENU):
            survivors.append(wi)
    assert not survivors

    mid = midpoint(start, st["anchors"][3784])
    local_witnesses = sum(
        cheb(point, mid) <= LOCAL_RADIUS for point in L7_POINT_SET_JAM
    )
    serialized = ";".join(
        ",".join(map(str, p)) for p in L7_POINT_SET_JAM
    )
    return {
        "level": 7,
        "segment": 3783,
        "position_in_stitch_order": pos,
        "step": st["parent_word"][3783],
        "initial_points": len(points),
        "sequentially_legal_added_points": len(L7_POINT_SET_JAM),
        "added_points_within_D40": local_witnesses,
        "final_points": len(store.pts),
        "domain_size": len(domain),
        "production_survivors_after_completion": 0,
        "ordered_witness_sha256": hashlib.sha256(serialized.encode()).hexdigest(),
        "interpretation": (
            "exact triple-free point-set completion jam; the 20 points have "
            "not been realized by legal earlier connector choices, so this "
            "is not a reachable ordered-path counterexample"
        ),
    }


def fingerprint(st, order, rank, pos, half_window):
    if pos >= len(order):
        return ("LEVEL-END",)
    i = order[pos]
    n = len(st["parent_word"])
    lo = max(0, i - half_window)
    hi = min(n, i + half_window + 1)
    origin = st["anchors"][i]
    anchors = tuple(sub(st["anchors"][j], origin) for j in range(lo, hi + 1))
    gaps = []
    for j in range(lo, hi):
        placed = rank[j] < pos
        gaps.append((st["parent_word"][j], st["words"][j] if placed else None))
    return (i - lo, st["parent_word"][i], anchors, tuple(gaps))


def cell_of(p):
    return (p[0] // CELL, p[1] // CELL, p[2] // CELL)


def gather_cloud(grid, centre, radius):
    c0 = cell_of((centre[0] - radius, centre[1] - radius, centre[2] - radius))
    c1 = cell_of((centre[0] + radius, centre[1] + radius, centre[2] + radius))
    out = []
    for x in range(c0[0], c1[0] + 1):
        for y in range(c0[1], c1[1] + 1):
            for z in range(c0[2], c1[2] + 1):
                for p in grid.get((x, y, z), ()):
                    if cheb(p, centre) <= radius:
                        out.append(sub(p, centre))
    return tuple(sorted(out))


def analyze_state_schedule(states, orders):
    result = {"half_windows": {}}
    fingerprints_by_h = {}

    for h in (2, 4, 8, 16):
        counts = Counter()
        transition_posts = defaultdict(set)
        for level, st in states.items():
            order = orders[level]
            rank = {gap: j for j, gap in enumerate(order)}
            fps = [
                fingerprint(st, order, rank, pos, h)
                for pos in range(len(order) + 1)
            ]
            for pos, fp in enumerate(fps[:-1]):
                counts[fp] += 1
                action = st["words"][order[pos]]
                transition_posts[(fp, action)].add(fps[pos + 1])
        fingerprints_by_h[h] = counts
        repeated_classes = sum(1 for n in counts.values() if n > 1)
        participating = sum(n for n in counts.values() if n > 1)
        ambiguous = [len(posts) for posts in transition_posts.values() if len(posts) > 1]
        result["half_windows"][str(h)] = {
            "unique_states": len(counts),
            "repeated_state_classes": repeated_classes,
            "states_in_repeated_classes": participating,
            "state_action_classes": len(transition_posts),
            "nondeterministic_state_action_classes": len(ambiguous),
            "max_successors_for_one_state_action": max(ambiguous, default=1),
        }

    repeated_h2 = {fp for fp, n in fingerprints_by_h[2].items() if n > 1}
    augmented = Counter()
    considered = 0
    for level, st in states.items():
        order = orders[level]
        rank = {gap: j for j, gap in enumerate(order)}
        grid = defaultdict(list)
        for p in st["anchors"]:
            grid[cell_of(p)].append(p)
        for pos, i in enumerate(order):
            fp = fingerprint(st, order, rank, pos, 2)
            if fp in repeated_h2:
                centre = midpoint(st["anchors"][i], st["anchors"][i + 1])
                cloud = gather_cloud(grid, centre, LOCAL_RADIUS)
                augmented[(fp, cloud)] += 1
                considered += 1
            for p in word_interiors(st["anchors"][i], st["words"][i]):
                grid[cell_of(p)].append(p)
    result["half_window_2_plus_exact_D40_cloud"] = {
        "states_considered": considered,
        "unique_augmented_states": len(augmented),
        "repeated_augmented_classes": sum(1 for n in augmented.values() if n > 1),
        "states_in_repeated_augmented_classes": sum(n for n in augmented.values() if n > 1),
    }
    return result


def analyze_states():
    levels = range(5, 9)
    states = {level: load_state(level) for level in levels}
    total = sum(len(st["order"]) for st in states.values())
    construction_orders = {
        level: tuple(st["order"]) for level, st in states.items()
    }
    path_orders = {
        level: tuple(range(len(st["parent_word"])))
        for level, st in states.items()
    }

    # Preserve the original top-level fields for existing result consumers.
    result = {"total_stitches": total}
    result.update(analyze_state_schedule(states, construction_orders))
    result["path_order"] = analyze_state_schedule(states, path_orders)
    result["path_order_interpretation"] = (
        "exact replay of the realized connector choices from left to right; "
        "each replay prefix is a subset of the verified final point set, so "
        "the recorded action remains legal"
    )
    return result


def poison_gate(cover_seconds):
    doms, d24 = load_domains()
    public = []
    private = {}
    for level, segment, label in DEFAULT_TARGETS:
        print(f"poison L{level} i={segment} ({label})", flush=True)
        result, internals = analyze_stitch(
            level, segment, label, doms, d24, cover_seconds
        )
        public.append(result)
        private[(level, segment)] = internals
        print(
            f"  local/global {result['local_survivors']}/"
            f"{result['global_survivors']}, tail {result['tail_unique_kills']}, "
            f"cover {result['additional_atom_cover']['status']} "
            f"{result['additional_atom_cover'].get('minimum_or_upper')}",
            flush=True,
        )

    a = private[(6, 2892)]
    b = private[(7, 1103)]
    assert len(a["domain"]) == len(b["domain"])
    common = a["survivor_indices"] & b["survivor_indices"]
    alias = {
        "states": [[6, 2892], [7, 1103]],
        "domain_size": len(a["domain"]),
        "global_killed_sizes": [
            len(a["domain"]) - len(a["survivor_indices"]),
            len(b["domain"]) - len(b["survivor_indices"]),
        ],
        "killed_mask_symmetric_difference": len(
            a["survivor_indices"] ^ b["survivor_indices"]
        ),
        "common_survivors": len(common),
        "chosen_A_legal_in_B": a["chosen_index"] in b["survivor_indices"],
        "chosen_B_legal_in_A": b["chosen_index"] in a["survivor_indices"],
        "common_action_exists": bool(common),
    }
    print("fixed-domain jam negative control", flush=True)
    negative_control = analyze_fixed_domain_jam(doms, d24)
    print("L7 triple-free point-set completion negative control", flush=True)
    point_set_jam = analyze_l7_point_set_jam(doms)
    return {
        "stitches": public,
        "ordered_alias": alias,
        "fixed_domain_jam_negative_control": negative_control,
        "L7_point_set_completion_negative_control": point_set_jam,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("poison", "states", "all"), nargs="?", default="all")
    parser.add_argument("--cover-seconds", type=float, default=60.0)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "design/salvage-gate-results.json",
    )
    args = parser.parse_args()
    t0 = time.time()
    out = {
        "status_classes": {
            "exact": "integer-exact finite computation",
            "timeout": "reported cover value is an upper bound",
            "interpretation": "finite construction-orbit evidence, not an all-level proof",
        },
        "resource_policy": {
            "processes": 1,
            "expected_thread_cap": 1,
            "recommended_nice": 15,
        },
    }
    if args.mode in ("poison", "all"):
        out["poison_gate"] = poison_gate(args.cover_seconds)
    if args.mode in ("states", "all"):
        print("ordered-state stabilization scan", flush=True)
        out["state_gate"] = analyze_states()
    out["elapsed_s"] = round(time.time() - t0, 3)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}", flush=True)


if __name__ == "__main__":
    main()
