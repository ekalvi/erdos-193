#!/usr/bin/env python3
"""Exact L5 constructor with no new x-parallel secant lines.

For the frozen L4 -> L5 instance, all L5 anchors are present before any
connector is chosen.  The L4 walk has exactly 31 doubled ``(y,z)`` fibres;
these give 31 inherited x-parallel secant lines.  This checker follows the
recorded fragile-first L5 stitch order and chooses the first effective-domain
word satisfying both conditions below.

1. ``word_legal_fast`` accepts the word against the *alternate* prefix built
   by this checker (and the slower reference ``gate_run.word_legal`` agrees).
2. Every new interior has a previously unused ``(y,z)`` coordinate, including
   relative to the other interiors of the same word.

Condition 2 makes the set of doubled fibres at the end exactly the inherited
31-fibre set.  It is global, not a local-radius proxy.

The authoritative domains are too large to retain in ordinary Python objects
while constructing.  ``build_compact_cache`` therefore follows the audited
two-stage loader in ``x_axis_universal_bellman.py``: it consumes and releases
one D2--4 step at a time, retains only the 18 small fragile bases, then consumes
and releases one D5 step at a time.  Each word is written as one length byte
followed by one byte per menu index.  The resulting ~68 MB file is mmap'ed for
the construction.  It is a transparent encoding, not a quotient.

Finally, the selected words are reassembled in left-to-right path order and
``erdos193.first_disqualifier`` independently verifies the complete walk.
The output contains direct commitments to the alternate words and points.

This is a finite existence certificate for one pinned L5 state.  It does not
give an exhaustive survivor count, a uniform all-level availability theorem,
or any control of non-x-parallel secants beyond ordinary exact legality.

Run on one low-priority thread from the repository root:

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/no_new_x_line_constructor.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/no_new_x_line_constructor.py run \
        --cache /tmp/no-new-x-line-domains.bin \
        --output /tmp/no-new-x-line-L5-canonical.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
import pickle
import resource
import sys
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from erdos193 import first_disqualifier  # noqa: E402
from fast_legal import Store, word_legal_fast  # noqa: E402
from gate_run import MENU, word_interiors, word_legal  # noqa: E402
from design.x_axis_universal_bellman import (  # noqa: E402
    stream_effective_domains,
)


EXPECTED_INPUT_SHA256 = {
    "connector_domains4.pkl": (
        "d3dbfd54b724b91b1391d2233931a865a5ff371789029556949c953419fa3e4f"
    ),
    "dstar5_fragile.pkl": (
        "fe6ca45eda2874833d8257324bf7e29e2a4e855b0c4c27a9d2312702f28aefb3"
    ),
    "gate2-l7-construction-L5.pkl": (
        "bfe3efdd0ea2676122e06fcbe0ac79bf9bbefeb52c21bbe49bcf8f81cfb4232d"
    ),
    "gate_run.py": (
        "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37"
    ),
    "fast_legal.py": (
        "7e99bb3f7da040a74c57245e6e64f438ec8b925153b8ccd343ec27c829f694ed"
    ),
    "erdos193.py": (
        "d59e76abcacd19ba0389785ae077a75f957baef369b409b4e251cde6b82fed6b"
    ),
    "search193.py": (
        "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc"
    ),
    "amplify_rich.py": (
        "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e"
    ),
    "imbricate193.py": (
        "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb"
    ),
    "design/x_axis_universal_bellman.py": (
        "cd16f5600747b168a3deeb7c6d74164e9463fed6889054f5a39227a42b731bb7"
    ),
}
THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
EXPECTED_MENU_SIZE = 124
EXPECTED_FRAGILE_STEPS = 18
EXPECTED_D24_WORDS = 7_114_584
EXPECTED_D5_WORDS = 5_422_562
EXPECTED_EFFECTIVE_WORDS = 12_537_146
EXPECTED_WORD_SLOTS = 55_513_526
EXPECTED_CACHE_BYTES = 68_050_680
EXPECTED_L5_GAPS = 2_457
EXPECTED_L5_ANCHORS = 2_458
EXPECTED_INHERITED_DOUBLE_FIBRES = 31
CACHE_MAGIC = b"NOXLN001"


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def atomic_json_dump(payload, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=".no-new-x-line-", suffix=".json"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(payload, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def verify_inputs():
    observed = {}
    for name, expected in EXPECTED_INPUT_SHA256.items():
        digest = file_sha256(ROOT / name)
        if digest != expected:
            raise AssertionError("pinned input drift", name, digest, expected)
        observed[name] = digest
    return observed


def resource_policy(enforce):
    environment = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    compliant = all(value == "1" for value in environment.values()) and priority >= 15
    if enforce and not compliant:
        raise RuntimeError(
            "run requires all thread variables set to 1 and nice priority >= 15",
            environment,
            priority,
        )
    return {
        "thread_environment": environment,
        "process_nice": priority,
        "required_thread_value": "1",
        "required_minimum_nice": 15,
        "compliant": compliant,
    }


def encode_word(handle, word, step, word_index, digest):
    length = len(word)
    if not 1 <= length <= 255:
        raise AssertionError("invalid connector length", step, word_index, length)
    if any(not 0 <= child < len(MENU) for child in word):
        raise AssertionError("invalid menu index", step, word_index)
    encoded = bytes((length, *word))
    handle.write(encoded)
    digest.update(encoded)
    return length


def write_step_block(handle, step, words, layer):
    start = handle.tell()
    digest = hashlib.sha256()
    slots = 0
    maximum_length = 0
    for word_index, raw_word in enumerate(words):
        word = tuple(raw_word)
        length = encode_word(handle, word, step, word_index, digest)
        slots += length
        maximum_length = max(maximum_length, length)
    end = handle.tell()
    if end - start != len(words) + slots:
        raise AssertionError("compact block byte count mismatch", step)
    return {
        "step": step,
        "layer": layer,
        "start": start,
        "end": end,
        "words": len(words),
        "word_slots": slots,
        "maximum_word_length": maximum_length,
        "encoded_block_sha256": digest.hexdigest(),
    }


def build_compact_cache(cache_path):
    """Use the pinned universal loader to write a one-byte-per-symbol cache."""
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=cache_path.parent, prefix=".no-new-x-line-domains-", suffix=".bin"
    )
    blocks = {}
    census = None
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(CACHE_MAGIC)

            def process_step(step, words, layer):
                if step in blocks:
                    raise AssertionError("duplicate effective-domain block", step)
                blocks[step] = write_step_block(
                    output, step, words, layer
                )

            census = stream_effective_domains(process_step)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, cache_path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise

    if census["D2-4_words"] != EXPECTED_D24_WORDS:
        raise AssertionError("D2--4 word total drift", census["D2-4_words"])
    if census["D5_appended_words"] != EXPECTED_D5_WORDS:
        raise AssertionError("D5 word total drift", census["D5_appended_words"])
    if census["fragile_steps"] != EXPECTED_FRAGILE_STEPS:
        raise AssertionError("fragile-step count drift", census["fragile_steps"])
    if set(blocks) != set(range(len(MENU))):
        raise AssertionError("effective-domain block set drift")
    effective_total = sum(block["words"] for block in blocks.values())
    slot_total = sum(block["word_slots"] for block in blocks.values())
    if effective_total != EXPECTED_EFFECTIVE_WORDS:
        raise AssertionError("effective word total drift", effective_total)
    if slot_total != EXPECTED_WORD_SLOTS:
        raise AssertionError("word-slot total drift", slot_total)
    cache_bytes = cache_path.stat().st_size
    if cache_bytes != EXPECTED_CACHE_BYTES:
        raise AssertionError("cache byte total drift", cache_bytes)
    return {
        "format": "8-byte magic; repeated [uint8 length, uint8 menu-index...]",
        "magic_ascii": CACHE_MAGIC.decode("ascii"),
        "bytes": cache_bytes,
        "sha256": file_sha256(cache_path),
        "D2-4_words": census["D2-4_words"],
        "D5_appended_words": census["D5_appended_words"],
        "effective_words": effective_total,
        "word_slots": slot_total,
        "fragile_steps": census["fragile_steps"],
        "universal_loader_census": census,
        "blocks": [blocks[step] for step in sorted(blocks)],
        "block_metadata_sha256": stable_hash(
            [blocks[step] for step in sorted(blocks)]
        ),
    }


def iter_block_words(cache, block):
    cursor = block["start"]
    for ordinal in range(1, block["words"] + 1):
        if cursor >= block["end"]:
            raise AssertionError("truncated cache block", block["step"], ordinal)
        length = cache[cursor]
        cursor += 1
        end = cursor + length
        if end > block["end"]:
            raise AssertionError("truncated cache word", block["step"], ordinal)
        yield ordinal, tuple(cache[cursor:end])
        cursor = end
    if cursor != block["end"]:
        raise AssertionError("cache block has trailing bytes", block["step"])


def point_stream_sha256(points):
    digest = hashlib.sha256()
    for point in points:
        for coordinate in point:
            encoded = str(coordinate).encode("ascii")
            digest.update(len(encoded).to_bytes(2, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def word_map_sha256(words):
    digest = hashlib.sha256()
    for gap in sorted(words):
        word = words[gap]
        digest.update(gap.to_bytes(4, "little"))
        digest.update(bytes((len(word), *word)))
    return digest.hexdigest()


def construct(cache_path, cache_metadata):
    with (ROOT / "gate2-l7-construction-L5.pkl").open("rb") as handle:
        state = pickle.load(handle)
    parent_word = tuple(state["parent_word"])
    anchors = tuple(tuple(point) for point in state["anchors"])
    order = tuple(state["order"])
    if len(parent_word) != EXPECTED_L5_GAPS:
        raise AssertionError("L5 gap count drift", len(parent_word))
    if len(anchors) != EXPECTED_L5_ANCHORS:
        raise AssertionError("L5 anchor count drift", len(anchors))
    if sorted(order) != list(range(len(parent_word))):
        raise AssertionError("L5 stitch order is not a permutation")
    if len(MENU) != EXPECTED_MENU_SIZE:
        raise AssertionError("menu size drift", len(MENU))

    yz_counts = Counter((point[1], point[2]) for point in anchors)
    initial_histogram = Counter(yz_counts.values())
    if max(yz_counts.values(), default=0) != 2:
        raise AssertionError("anchor yz-fibre multiplicity drift")
    initial_double_fibres = {
        lateral for lateral, count in yz_counts.items() if count == 2
    }
    if len(initial_double_fibres) != EXPECTED_INHERITED_DOUBLE_FIBRES:
        raise AssertionError(
            "inherited doubled-fibre count drift", len(initial_double_fibres)
        )

    blocks = {record["step"]: record for record in cache_metadata["blocks"]}
    store = Store(anchors)
    selected = {}
    selection_records = []
    length_histogram = Counter()
    cache_path = Path(cache_path)
    with cache_path.open("rb") as handle:
        cache = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            if cache[:len(CACHE_MAGIC)] != CACHE_MAGIC:
                raise AssertionError("compact cache magic drift")
            for construction_rank, gap in enumerate(order):
                step = parent_word[gap]
                block = blocks[step]
                start = anchors[gap]
                target = anchors[gap + 1]
                memo = {}
                projection_rejected = 0
                exact_tested = 0
                chosen = None
                chosen_interiors = None
                chosen_ordinal = None
                for ordinal, word in iter_block_words(cache, block):
                    interiors = word_interiors(start, word)
                    local_lateral = set()
                    projection_clean = True
                    for point in interiors:
                        lateral = (point[1], point[2])
                        if lateral in yz_counts or lateral in local_lateral:
                            projection_clean = False
                            break
                        local_lateral.add(lateral)
                    if not projection_clean:
                        projection_rejected += 1
                        continue
                    exact_tested += 1
                    if not word_legal_fast(start, word, store, memo, MENU):
                        continue
                    if not word_legal(
                        start, word, store.pts, store.pset, {}
                    ):
                        raise AssertionError(
                            "fast/reference legality disagreement",
                            construction_rank,
                            gap,
                            step,
                            ordinal,
                        )
                    chosen = word
                    chosen_interiors = interiors
                    chosen_ordinal = ordinal
                    break
                if chosen is None:
                    raise AssertionError(
                        "no projection-clean exactly legal connector",
                        {
                            "construction_rank": construction_rank,
                            "gap": gap,
                            "step": step,
                            "domain_words": block["words"],
                            "projection_rejected": projection_rejected,
                            "projection_clean_exact_tested": exact_tested,
                        },
                    )

                endpoint = start
                for child in chosen:
                    vector = MENU[child]
                    endpoint = (
                        endpoint[0] + vector[0],
                        endpoint[1] + vector[1],
                        endpoint[2] + vector[2],
                    )
                if endpoint != target:
                    raise AssertionError("selected connector endpoint drift")
                for point in chosen_interiors:
                    lateral = (point[1], point[2])
                    if yz_counts[lateral] != 0:
                        raise AssertionError("new doubled yz fibre", lateral)
                    yz_counts[lateral] = 1
                store.add_many(chosen_interiors)
                selected[gap] = chosen
                length_histogram[len(chosen)] += 1
                selection_records.append({
                    "construction_rank": construction_rank,
                    "gap": gap,
                    "step": step,
                    "domain_words": block["words"],
                    "first_survivor_ordinal_1_based": chosen_ordinal,
                    "projection_rejected_before_survivor": projection_rejected,
                    "projection_clean_exact_tested_through_survivor": exact_tested,
                    "selected_word": list(chosen),
                })
        finally:
            cache.close()

    final_double_fibres = {
        lateral for lateral, count in yz_counts.items() if count == 2
    }
    if final_double_fibres != initial_double_fibres:
        raise AssertionError("doubled yz-fibre identity changed")
    if max(yz_counts.values(), default=0) != 2:
        raise AssertionError("final yz-fibre multiplicity exceeds two")

    chain = [anchors[0]]
    alternate_step_word = []
    for gap in range(len(parent_word)):
        word = selected[gap]
        chain.extend(word_interiors(anchors[gap], word))
        chain.append(anchors[gap + 1])
        alternate_step_word.extend(word)
    if len(chain) != len(store.pts) or set(chain) != store.pset:
        raise AssertionError("construction store/path mismatch")
    disqualifier = first_disqualifier(chain)
    if disqualifier is not None:
        raise AssertionError("independent ordered verifier failed", disqualifier)

    first_ordinals = [
        record["first_survivor_ordinal_1_based"]
        for record in selection_records
    ]
    exact_tests = [
        record["projection_clean_exact_tested_through_survivor"]
        for record in selection_records
    ]
    projection_rejections = [
        record["projection_rejected_before_survivor"]
        for record in selection_records
    ]
    maximum_record = max(
        selection_records,
        key=lambda record: (
            record["first_survivor_ordinal_1_based"],
            -record["construction_rank"],
        ),
    )
    return {
        "scope": {
            "level": 5,
            "schedule": "pinned fragile-first gate order",
            "selector": (
                "first effective-domain word that is globally projection-clean "
                "and exactly legal against this alternate prefix"
            ),
            "gaps": len(parent_word),
            "anchors": len(anchors),
            "all_anchors_present_before_first_stitch": True,
        },
        "projection_invariant": {
            "definition": (
                "each selected interior has a globally unused (y,z), including "
                "against anchors, earlier connectors, and its own word"
            ),
            "initial_fibre_histogram": {
                str(key): value for key, value in sorted(initial_histogram.items())
            },
            "final_fibre_histogram": {
                str(key): value
                for key, value in sorted(Counter(yz_counts.values()).items())
            },
            "initial_doubled_fibres": len(initial_double_fibres),
            "final_doubled_fibres": len(final_double_fibres),
            "new_doubled_fibres": 0,
            "doubled_fibre_set_preserved_exactly": True,
            "inherited_doubled_fibre_stream_sha256": stable_hash(
                sorted(initial_double_fibres)
            ),
        },
        "construction": {
            "completed": True,
            "points": len(chain),
            "steps": len(alternate_step_word),
            "selected_word_length_histogram": {
                str(key): value for key, value in sorted(length_histogram.items())
            },
            "minimum_effective_domain_words_over_stitches": min(
                blocks[step]["words"] for step in parent_word
            ),
            "minimum_joint_survivors_certified_per_stitch": 1,
            "survivor_counts_exhaustive": False,
            "first_domain_word_survived_stitches": sum(
                ordinal == 1 for ordinal in first_ordinals
            ),
            "maximum_first_survivor_ordinal_1_based": max(first_ordinals),
            "median_first_survivor_ordinal_1_based": sorted(first_ordinals)[
                len(first_ordinals) // 2
            ],
            "maximum_ordinal_witness": maximum_record,
            "total_projection_rejections_before_selected_words": sum(
                projection_rejections
            ),
            "maximum_projection_rejections_before_one_survivor": max(
                projection_rejections
            ),
            "total_projection_clean_exact_tests_through_survivors": sum(
                exact_tests
            ),
            "maximum_projection_clean_exact_tests_through_one_survivor": max(
                exact_tests
            ),
            "fast_and_reference_legality_agreed_on_every_selected_word": True,
        },
        "independent_verification": {
            "checker": "erdos193.first_disqualifier",
            "ordered_chain_result": None,
            "ordered_chain_triple_free_and_vertex_injective": True,
            "store_point_set_equals_ordered_chain_point_set": True,
        },
        "commitments": {
            "pinned_schedule_sha256": stable_hash(order),
            "selection_record_stream_sha256": stable_hash(selection_records),
            "alternate_words_by_gap_sha256": word_map_sha256(selected),
            "alternate_flat_step_word_sha256": hashlib.sha256(
                bytes(alternate_step_word)
            ).hexdigest(),
            "alternate_ordered_point_stream_sha256": point_stream_sha256(chain),
            "final_point_set_sha256": stable_hash(sorted(store.pset)),
        },
        "limitations": [
            "finite certificate for the pinned L4-to-L5 state only",
            "the 31 x-parallel lines inherited from L4 remain",
            "one survivor per stitch is witnessed; all survivors are not counted",
            "no uniform all-level transition or availability theorem",
            "no special elimination of non-x-parallel secants",
        ],
    }


def estimate_payload(policy):
    return {
        "mode": "estimate",
        "status": "no domain pickle loaded and no cache or output written",
        "resource_policy": policy,
        "expected_scope": {
            "effective_domain_words": EXPECTED_EFFECTIVE_WORDS,
            "word_slots": EXPECTED_WORD_SLOTS,
            "compact_cache_bytes": EXPECTED_CACHE_BYTES,
            "L5_gaps": EXPECTED_L5_GAPS,
            "independent_verifier_points": 8_214,
        },
        "estimated_resources": {
            "peak_resident_memory_MiB": "730--850",
            "hard_design_target_MiB": 900,
            "wall_seconds_per_run": "120--300",
            "processes": 1,
            "threads": 1,
            "nice": 15,
            "temporary_disk_MiB": 65,
        },
        "phases": [
            "pinned-hash validation",
            "two-stage D2--4 then D5 compact-cache construction",
            "fragile-first exact alternate L5 construction",
            "independent ordered-chain verification",
            "deterministic JSON commitments",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("estimate", "run"))
    parser.add_argument(
        "--cache", default="/tmp/no-new-x-line-domains.bin"
    )
    parser.add_argument(
        "--output", default="/tmp/no-new-x-line-L5-canonical.json"
    )
    args = parser.parse_args()

    policy = resource_policy(enforce=args.mode == "run")
    if args.mode == "estimate":
        print(json.dumps(estimate_payload(policy), sort_keys=True, indent=2))
        return

    observed_inputs = verify_inputs()
    cache_metadata = build_compact_cache(args.cache)
    result = construct(args.cache, cache_metadata)
    payload = {
        "schema_version": 1,
        "date": "2026-07-18",
        "status": "exact finite certificate",
        "checker": {
            "path": "design/no_new_x_line_constructor.py",
            "sha256": file_sha256(Path(__file__).resolve()),
        },
        "input_sha256": observed_inputs,
        "resource_policy": policy,
        "compact_domain_cache": cache_metadata,
        "result": result,
    }
    atomic_json_dump(payload, args.output)
    observation = {
        "output": str(Path(args.output).resolve()),
        "output_sha256": file_sha256(args.output),
        "maximum_resident_set_raw": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss,
    }
    print(json.dumps(observation, sort_keys=True))


if __name__ == "__main__":
    main()
