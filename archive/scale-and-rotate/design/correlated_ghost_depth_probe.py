#!/usr/bin/env python3
"""Exact resumable L8 -> L9 carried-ghost depth probe.

This is a theorem diagnostic for the concrete ``42 -> 146 -> 488`` ordered
trace.  Its token universe is deliberately larger than the effectful-partner
menus emitted by the earlier compatibility probe.  At each of the 146 L8
source corridors it retains, for every tagged source endpoint, every physical
L8 point that existed before that stitch.  In particular, a physical
endpoint-pair token is retained even when its current killed-word mask is
zero.  The endpoints remain correlated; their address streams are never
split.

For each oriented token ``(tagged endpoint, physical partner)`` the checker
retains

* both stable endpoint identities and exact birth addresses;
* the partner's pipeline activation rank (``-1`` for inherited anchors);
* exact endpoint and partner coordinates in the current corridor frame;
* the canonical primitive Pluecker pair ``(g,m)``, where
  ``g=primitive(partner-endpoint)`` and ``m=endpoint_relative cross g``;
* the exact source killed-word bitset; and
* the ordered tuple of exact L9 child killed-word bitsets, together with the
  transported child Pluecker states.

There is no endpoint, path-index, spatial, or distance cutoff.  Candidate
site masks are made from every word in the pinned connector domains.  A
complete direction index is used only as an exact join: the pinned L8 set has
no three collinear points, so a direction from a tagged endpoint identifies
at most one physical partner.

The full token stream can exceed seventy million occurrences.  It is not
expanded into JSON.  Exact nonzero masks and their reconstructible compressed
payloads are stored in a resumable SQLite certificate.  Every token,
including every all-zero token, is nevertheless streamed through the depth
shell census, exact transition-congruence tests, and a deterministic block
commitment.  Congruence keys all contain the two stable endpoint identities,
so classes cannot cross physical pairs; this permits exact pair-local
reduction without an enormous global sort.  Literal/singleton and repeated
class counts are reported separately so a zero-disagreement result cannot be
mistaken for nonvacuous stabilization.

The depth shells are finite observations, not a tail theorem:

``depth_0``
    the carried physical line kills a current L8 connector word;
``depth_1``
    the current mask is zero but at least one ordered L9 child mask is
    nonzero; and
``silent_through_depth_1``
    both tested generations are zero (nothing beyond L9 is inferred).

The exact 3,998-versus-zero witness is a mandatory regression.  The positive
state is ``(13171,12329,41282)``, its slot-1 L9 child is gap 138866, the
tagged endpoint is ``connector:L7:G12324:I2``, and the latent partner is
``connector:L7:G12329:I2``.  It must reproduce 3,998 killed words and mask
SHA-256 ``ea2336...48be``; state ``(13171,12333,41297)`` must reproduce zero.

Scope boundary: this carries every token already physical before each tested
L8 stitch.  It does not add tokens born at that stitch or later in the rest
of L8, does not include a selected L9 word or L9 prefix interiors, and does
not test alternate connector histories.  Consequently it can falsify a
projected right congruence on the recorded tree, but cannot certify all-action
Post closure, a contracting tail, positive availability, or an unconditional
theorem.

Estimate and self-check do not open any construction pickle, connector-domain
pickle, or pinned result JSON.  A full/resumed run is one process and one
thread and fails closed unless it is run at nice value at least 15::

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/correlated_ghost_depth_probe.py estimate

    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
        VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
        nice -n 15 python3 -B design/correlated_ghost_depth_probe.py run \
        --database /tmp/correlated-ghost-depth-probe.sqlite \
        --output /tmp/correlated-ghost-depth-probe.json

The default safety caps are six elapsed hours, 2,200 MiB resident memory, and
200 million checked work units per invocation.  Work/RSS/time are checked at
least every 50,000 units and before every durable step or token-block commit.
Stopping on a cap is graceful and leaves only completed transactions to
resume.  Changing the checker, inputs, or block size invalidates a database
rather than silently resuming it.
"""

from __future__ import annotations

import argparse
import base64
import bisect
import gc
import hashlib
import json
import math
import os
import pickle
import platform
import resource
import sqlite3
import sys
import tempfile
import time
import zlib
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "design"))

# These imports contain no top-level construction-data reads.  Their exact
# source hashes are pinned below and verified before ``run`` calls a helper.
from amplify_rich import M_BAL3  # noqa: E402
from deep_incidence_lineage import (  # noqa: E402
    build_l8_catalog,
    build_path_origins,
)
from gate_run import FRAGILE_CUT, IDX, MENU, word_interiors  # noqa: E402
from imbricate193 import apply  # noqa: E402
from inherited_tile_lifetime import exact_birth_levels, load_viz  # noqa: E402
from salvage_gate import cross, primitive, sub  # noqa: E402


SCHEMA_VERSION = 3
TARGET_LEVEL = 8
EXPECTED_L8_STATES = 146
EXPECTED_L9_CHILDREN = 488
EXPECTED_L8_POINTS = 311_738
# The 146 source stitches use 58 steps and their selected child words use 90;
# their exact union contains 99 connector-domain steps.
EXPECTED_EFFECTIVE_STEPS = 99
EXPECTED_ENDPOINT_STATE_PAIRS = 235
TOKEN_OCCURRENCE_UPPER_BOUND = 73_258_195
DEFAULT_BLOCK_SIZE = 512
DEFAULT_MAX_RSS_MIB = 2200.0
DEFAULT_DATABASE = Path("/tmp/correlated-ghost-depth-probe.sqlite")
DEFAULT_OUTPUT = Path("/tmp/correlated-ghost-depth-probe.json")
DEFAULT_TRACE = Path("/tmp/far-secant-birth-shell-trace-canonical.json")
DEFAULT_L9 = Path("/tmp/l9-anchor-age2-precursor-canonical.json")
DEFAULT_COMPATIBILITY = Path(
    "/tmp/far-secant-future-compatibility-probe-canonical.json"
)

THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

SOURCE_DEFINITIONS = {
    13171: {
        "witness_type": "old-old-secant",
        "tagged_endpoint_stable_ids": (
            "connector:L7:G12291:I1",
            "connector:L7:G12324:I2",
        ),
        "expected_states": 89,
        "expected_children": 305,
    },
    21115: {
        "witness_type": "old-new-new-line",
        "tagged_endpoint_stable_ids": (
            "connector:L7:G19950:I2",
        ),
        "expected_states": 57,
        "expected_children": 183,
    },
}

EXPECTED_INPUT_SHA256 = {
    "trace": "5c525ef4cc0c77ed96a2f67238e785d0382ead806f96479854a691498de99488",
    "l9": "961f9e5f0772d9df508ab0aefaa7405e3cc21637d59560cdda95c4edf61d809f",
    "compatibility": "72af973f12179f1b25b24a23d77d8420888964bce219b0106a32c79be698dda6",
    "viz/walk3d-data.json": "d4392af018ee7d7c40c224622e9a606d3b1fb3da0c8c25613c93cb2dc901c883",
    "gate2-l7-construction-L8.pkl": "cc4002ebccde737ab46dc016937be4aa653620d809908d48d35bcf06fc884141",
    "connector_domains4.pkl": "d3dbfd54b724b91b1391d2233931a865a5ff371789029556949c953419fa3e4f",
    "dstar5_fragile.pkl": "fe6ca45eda2874833d8257324bf7e29e2a4e855b0c4c27a9d2312702f28aefb3",
    "design/deep_incidence_lineage.py": "cde329fafc79ec95ea0f3d8d8a060219af45633f6414f7f3fb8426fad4888be7",
    "design/l9_anchor_age2_precursor.py": "66f776e7ae4eff4c35d004d870d82458582a4c2b6516f20257149a08e5535b90",
    "design/far_secant_future_compatibility_probe.py": "4f95c0afd084306e7ecb202c49567a376e52d101cb3f9274fefd01d6d62fbf46",
    "design/far_secant_birth_shell_trace.py": "dd35f8ac5459d6df05d8b960f82b709f69380268ed144ac5c0e6789d178c35b9",
    "design/far_secant_future_trace.py": "6f286cb118166c1375eb777ec6e24bcdc58766b98538099c604eb97b5c3dd430",
    "design/inherited_tile_lifetime.py": "b1421cb6681a63b641ecc82ff6681b0b78b0a78af29d90332ebe17dadfc222b4",
    "gate_run.py": "16da12c29406dfb10d4eacbadd4c9cee1f595f6f23bcab8fd07827acc3b7cc37",
    "amplify_rich.py": "4ca067a352db370c3c7c254a89655dd00b01f629eb1f2f5faebe97a64222a02e",
    "imbricate193.py": "0f6c97255a5f01f0ec1d0d9fc9219d67ac8f115f558f82745fdc4be7c7a5e3cb",
    "design/salvage_gate.py": "ef1838b6561d68547fa3423353483bece656198458973a984188d441a0767d95",
    "search193.py": "0588060ebc443cc85521af1a34a6a3f94b4c4462365c7e03282bf1afb7cdcffc",
}

EXPECTED_CHECKERS = {
    "trace": "dd35f8ac5459d6df05d8b960f82b709f69380268ed144ac5c0e6789d178c35b9",
    "l9": "66f776e7ae4eff4c35d004d870d82458582a4c2b6516f20257149a08e5535b90",
    "compatibility": "4f95c0afd084306e7ecb202c49567a376e52d101cb3f9274fefd01d6d62fbf46",
}

WITNESS = {
    "state_A": (13171, 12329, 41282),
    "state_B": (13171, 12333, 41297),
    "endpoint": "connector:L7:G12324:I2",
    "partner": "connector:L7:G12329:I2",
    "slot": 1,
    "child_A": 138866,
    "child_B": 138914,
    "step": 114,
    "domain_words": 453_015,
    "positive_words": 3_998,
    "positive_sha256": (
        "ea2336c635af801427f98932c26c03dcafccf652967781f753d45e87f61948be"
    ),
    "zero_sha256": (
        "1848a4118123c129928c08aa9f080173a93997eb465534299e0675f5fd99b71c"
    ),
}

PROJECTIONS = (
    "legacy_current_effect",
    "physical_pluecker",
    "full_correlated",
    "literal_address",
)
OUTCOME_KINDS = ("ordered_child_mask_tree", "ordered_child_correlated_tree")


class BudgetExceeded(RuntimeError):
    """A graceful resource-cap stop; completed transactions remain valid."""


def as_json(value):
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


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def add(left, right):
    return tuple(left[axis] + right[axis] for axis in range(3))


def line_state(endpoint_relative, partner_relative):
    direction = primitive(sub(partner_relative, endpoint_relative))
    if direction is None:
        raise ValueError("physical token has repeated endpoints")
    moment = cross(endpoint_relative, direction)
    assert cross(partner_relative, direction) == moment
    return tuple(direction), tuple(moment)


def base3_shell(value):
    if value <= 0:
        raise ValueError("base-three shell requires a positive integer")
    shell = 0
    ceiling = 1
    while value > ceiling:
        ceiling *= 3
        shell += 1
    return shell


def mask_raw(bits, domain_words):
    if bits < 0 or bits >> domain_words:
        raise ValueError("bitset outside its declared connector domain")
    return bits.to_bytes((domain_words + 7) // 8, "little")


def mask_sha256(bits, domain_words):
    return hashlib.sha256(mask_raw(bits, domain_words)).hexdigest()


def current_rss_mib():
    maximum = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes; Linux and most BSD-derived Python builds report KiB.
    if platform.system() == "Darwin":
        return maximum / (1024 * 1024)
    return maximum / 1024


def enforce_resource_policy():
    observed = {name: os.environ.get(name) for name in THREAD_ENV_VARS}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "all thread-cap variables must equal 1: "
            + json.dumps(observed, sort_keys=True)
        )
    if not hasattr(os, "getpriority"):
        raise RuntimeError("this platform cannot verify the process nice value")
    nice_value = os.getpriority(os.PRIO_PROCESS, 0)
    if nice_value < 15:
        raise RuntimeError(
            f"run under `nice -n 15`; observed nice value {nice_value}"
        )
    return {
        "processes": 1,
        "thread_cap": 1,
        "nice": nice_value,
        "thread_environment": observed,
    }


class WorkBudget:
    def __init__(self, max_seconds, max_rss_mib, max_work_units, interval):
        self.started = time.monotonic()
        self.max_seconds = max_seconds
        self.max_rss_mib = max_rss_mib
        self.max_work_units = max_work_units
        self.interval = interval
        self.work_units = 0
        self.next_check = 0
        self.peak_rss_mib = current_rss_mib()
        self.check("initialization")

    def consume(self, units=1, label="work"):
        if units < 0:
            raise ValueError("negative work increment")
        self.work_units += units
        if self.work_units >= self.next_check:
            self.check(label)
            self.next_check = self.work_units + self.interval

    def check(self, label):
        elapsed = time.monotonic() - self.started
        rss = current_rss_mib()
        self.peak_rss_mib = max(self.peak_rss_mib, rss)
        if elapsed > self.max_seconds:
            raise BudgetExceeded(
                f"elapsed-time cap at {label}: {elapsed:.1f}s > "
                f"{self.max_seconds:.1f}s"
            )
        if rss > self.max_rss_mib:
            raise BudgetExceeded(
                f"RSS cap at {label}: {rss:.1f} MiB > "
                f"{self.max_rss_mib:.1f} MiB"
            )
        if self.work_units > self.max_work_units:
            raise BudgetExceeded(
                f"work cap at {label}: {self.work_units} > "
                f"{self.max_work_units}"
            )

    def record(self):
        return {
            "elapsed_seconds": round(time.monotonic() - self.started, 3),
            "work_units_this_invocation": self.work_units,
            "peak_rss_mib": round(self.peak_rss_mib, 3),
            "caps": {
                "max_seconds": self.max_seconds,
                "max_rss_mib": self.max_rss_mib,
                "max_work_units": self.max_work_units,
                "check_interval_work_units": self.interval,
            },
        }


def input_paths(arguments):
    return {
        "trace": arguments.trace,
        "l9": arguments.l9,
        "compatibility": arguments.compatibility,
        **{
            relative: ROOT / relative
            for relative in EXPECTED_INPUT_SHA256
            if relative not in ("trace", "l9", "compatibility")
        },
    }


def validate_run_inputs(arguments):
    paths = input_paths(arguments)
    observed = {name: file_sha256(path) for name, path in paths.items()}
    if observed != EXPECTED_INPUT_SHA256:
        differences = {
            name: {
                "expected": EXPECTED_INPUT_SHA256[name],
                "observed": observed.get(name),
            }
            for name in EXPECTED_INPUT_SHA256
            if observed.get(name) != EXPECTED_INPUT_SHA256[name]
        }
        raise RuntimeError(
            "pinned input hash mismatch: "
            + json.dumps(differences, sort_keys=True)
        )

    trace = json.loads(arguments.trace.read_text())
    l9 = json.loads(arguments.l9.read_text())
    compatibility = json.loads(arguments.compatibility.read_text())
    assert trace["checker_sha256"] == EXPECTED_CHECKERS["trace"]
    assert l9["checker_sha256"] == EXPECTED_CHECKERS["l9"]
    assert compatibility["checker_sha256"] == EXPECTED_CHECKERS[
        "compatibility"
    ]
    assert l9["upstream_trace"]["sha256"] == observed["trace"]
    assert compatibility["input_sha256"]["birth"] == observed["trace"]
    assert compatibility["input_sha256"]["l9"] == observed["l9"]
    assert len(trace["child_states"]) == EXPECTED_L8_STATES
    assert len(l9["exact_corridor_masks"]["records"]) == EXPECTED_L9_CHILDREN
    assert len(compatibility["states"]["L8"]) == EXPECTED_L8_STATES
    assert len(compatibility["states"]["L9"]) == EXPECTED_L9_CHILDREN
    assert compatibility["scope"]["endpoint_or_distance_cutoff"] is None
    return trace, l9, compatibility, observed


def relevant_connector_steps(trace):
    """Derive the exact source/child step support before opening domains."""
    steps = set()
    for item in trace["child_states"]:
        source_step = item["step"]
        actual_word = tuple(item["actual_selected_connector_word"])
        assert source_step in range(len(MENU))
        assert actual_word
        assert all(step in range(len(MENU)) for step in actual_word)
        steps.add(source_step)
        steps.update(actual_word)
    assert len(steps) == EXPECTED_EFFECTIVE_STEPS
    return frozenset(steps)


def load_relevant_domains(relevant_steps):
    """Load exactly the 99 used domains with ``gate_run`` ordering.

    The complete D2--4 size map is retained because the chronological catalog
    needs it to reconstruct the frozen fragile-first schedule.  Domain words
    for unused steps are discarded before any sorted copy is made.  For every
    retained step, the ordering is byte-for-byte semantic-equivalent to
    ``gate_run.load_domains``: stable ``sorted(..., key=len)`` followed by the
    original D*5 fragile-word stream in pickle order.
    """
    relevant_steps = frozenset(relevant_steps)
    assert len(relevant_steps) == EXPECTED_EFFECTIVE_STEPS
    d4_path = ROOT / "connector_domains4.pkl"
    with d4_path.open("rb") as handle:
        d4 = pickle.load(handle)
    assert tuple(map(tuple, d4["menu"])) == tuple(MENU)
    raw_domains = d4["domains"]
    d24_size = {step: len(words) for step, words in raw_domains.items()}
    assert relevant_steps <= set(raw_domains)
    for step in tuple(raw_domains):
        if step not in relevant_steps:
            del raw_domains[step]
    del d4
    gc.collect()

    domains = {}
    for step in sorted(relevant_steps):
        raw_words = raw_domains.pop(step)
        domains[step] = sorted(raw_words, key=len)
        del raw_words
    assert not raw_domains
    del raw_domains
    gc.collect()

    d5_path = ROOT / "dstar5_fragile.pkl"
    with d5_path.open("rb") as handle:
        d5 = pickle.load(handle)
    for step_vector, words in d5.items():
        step = IDX[tuple(step_vector)]
        assert d24_size[step] < FRAGILE_CUT
        if step in relevant_steps:
            domains[step].extend(
                tuple(IDX[tuple(vector)] for vector in word)
                for word in words
            )
    del d5
    gc.collect()
    assert set(domains) == set(relevant_steps)
    return domains, d24_size


def initialize_database(path, run_signature, metadata):
    path = Path(path).resolve()
    if not path.parent.is_dir():
        raise FileNotFoundError(f"database parent does not exist: {path.parent}")
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=FULL")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS masks (
            mask_id INTEGER PRIMARY KEY,
            domain_words INTEGER NOT NULL,
            killed_words INTEGER NOT NULL,
            mask_sha256 TEXT NOT NULL,
            raw_bytes INTEGER NOT NULL,
            zlib_payload BLOB NOT NULL,
            UNIQUE(domain_words, mask_sha256)
        );
        CREATE TABLE IF NOT EXISTS effects (
            state_ordinal INTEGER NOT NULL,
            endpoint_ordinal INTEGER NOT NULL,
            phase INTEGER NOT NULL,
            slot INTEGER NOT NULL,
            partner_index INTEGER NOT NULL,
            step INTEGER NOT NULL,
            domain_words INTEGER NOT NULL,
            mask_id INTEGER NOT NULL REFERENCES masks(mask_id),
            PRIMARY KEY (
                state_ordinal, endpoint_ordinal, phase, slot, partner_index
            )
        );
        CREATE INDEX IF NOT EXISTS effects_partner_index
            ON effects(partner_index, state_ordinal, endpoint_ordinal);
        CREATE TABLE IF NOT EXISTS completed_steps (
            step INTEGER PRIMARY KEY,
            domain_words INTEGER NOT NULL,
            site_offsets INTEGER NOT NULL,
            requested_offsets INTEGER NOT NULL,
            nonzero_effects INTEGER NOT NULL,
            summary_json TEXT NOT NULL,
            summary_sha256 TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS token_chunks (
            role_ordinal INTEGER NOT NULL,
            partner_start INTEGER NOT NULL,
            partner_stop INTEGER NOT NULL,
            token_occurrences INTEGER NOT NULL,
            block_sha256 TEXT NOT NULL,
            summary_json TEXT NOT NULL,
            summary_sha256 TEXT NOT NULL,
            PRIMARY KEY(role_ordinal, partner_start)
        );
        """
    )
    expected_columns = {
        "meta": ("key", "value"),
        "masks": (
            "mask_id", "domain_words", "killed_words", "mask_sha256",
            "raw_bytes", "zlib_payload",
        ),
        "effects": (
            "state_ordinal", "endpoint_ordinal", "phase", "slot",
            "partner_index", "step", "domain_words", "mask_id",
        ),
        "completed_steps": (
            "step", "domain_words", "site_offsets", "requested_offsets",
            "nonzero_effects", "summary_json", "summary_sha256",
        ),
        "token_chunks": (
            "role_ordinal", "partner_start", "partner_stop",
            "token_occurrences", "block_sha256", "summary_json",
            "summary_sha256",
        ),
    }
    for table, expected in expected_columns.items():
        observed = tuple(
            row[1] for row in connection.execute(f"PRAGMA table_info({table})")
        )
        if observed != expected:
            raise RuntimeError(
                f"SQLite table layout mismatch for {table}: {observed!r}"
            )
    existing = dict(connection.execute("SELECT key,value FROM meta"))
    if existing:
        if set(existing) != {"schema_version", "run_signature", "metadata"}:
            raise RuntimeError("existing database metadata key mismatch")
        if existing.get("run_signature") != run_signature:
            raise RuntimeError(
                "existing database has a different checker/input/config "
                "signature; choose a new --database path"
            )
        if int(existing.get("schema_version", -1)) != SCHEMA_VERSION:
            raise RuntimeError("existing database schema version mismatch")
        if json.loads(existing["metadata"]) != metadata:
            raise RuntimeError("existing database metadata payload mismatch")
    else:
        with connection:
            connection.executemany(
                "INSERT INTO meta(key,value) VALUES (?,?)",
                [
                    ("schema_version", str(SCHEMA_VERSION)),
                    ("run_signature", run_signature),
                    ("metadata", json.dumps(metadata, sort_keys=True)),
                ],
            )
    integrity = connection.execute("PRAGMA quick_check").fetchall()
    if integrity != [("ok",)]:
        raise RuntimeError(f"SQLite quick_check failed: {integrity!r}")
    return connection, path


class MaskStore:
    def __init__(self, connection):
        self.connection = connection
        self.metadata_cache = {}
        self.bits_cache = OrderedDict()
        self.zero_cache = {}

    def cache_bits(self, mask_id, bits):
        self.bits_cache[mask_id] = bits
        self.bits_cache.move_to_end(mask_id)
        while len(self.bits_cache) > 256:
            self.bits_cache.popitem(last=False)

    def add(self, bits, domain_words):
        raw = mask_raw(bits, domain_words)
        digest = hashlib.sha256(raw).hexdigest()
        row = self.connection.execute(
            "SELECT mask_id,killed_words,raw_bytes,zlib_payload "
            "FROM masks WHERE domain_words=? AND mask_sha256=?",
            (domain_words, digest),
        ).fetchone()
        if row is not None:
            mask_id, killed_words, raw_bytes, payload = row
            decoded = zlib.decompress(payload)
            if decoded != raw:
                raise RuntimeError("SHA-256 mask collision or corrupt database")
            assert killed_words == bits.bit_count()
            assert raw_bytes == len(raw)
            self.metadata_cache[mask_id] = (
                domain_words, killed_words, digest
            )
            self.cache_bits(mask_id, bits)
            return mask_id
        cursor = self.connection.execute(
            "INSERT INTO masks(domain_words,killed_words,mask_sha256,"
            "raw_bytes,zlib_payload) VALUES (?,?,?,?,?)",
            (
                domain_words,
                bits.bit_count(),
                digest,
                len(raw),
                zlib.compress(raw, level=9),
            ),
        )
        mask_id = cursor.lastrowid
        self.metadata_cache[mask_id] = (
            domain_words, bits.bit_count(), digest
        )
        self.cache_bits(mask_id, bits)
        return mask_id

    def zero(self, domain_words):
        if domain_words not in self.zero_cache:
            self.zero_cache[domain_words] = self.add(0, domain_words)
        return self.zero_cache[domain_words]

    def metadata(self, mask_id):
        if mask_id not in self.metadata_cache:
            row = self.connection.execute(
                "SELECT domain_words,killed_words,mask_sha256 FROM masks "
                "WHERE mask_id=?",
                (mask_id,),
            ).fetchone()
            if row is None:
                raise KeyError(mask_id)
            self.metadata_cache[mask_id] = tuple(row)
        return self.metadata_cache[mask_id]

    def bits(self, mask_id):
        if mask_id in self.bits_cache:
            self.bits_cache.move_to_end(mask_id)
        else:
            row = self.connection.execute(
                "SELECT domain_words,killed_words,mask_sha256,zlib_payload "
                "FROM masks WHERE mask_id=?",
                (mask_id,),
            ).fetchone()
            if row is None:
                raise KeyError(mask_id)
            domain_words, killed_words, digest, payload = row
            raw = zlib.decompress(payload)
            assert len(raw) == (domain_words + 7) // 8
            assert hashlib.sha256(raw).hexdigest() == digest
            bits = int.from_bytes(raw, "little")
            assert bits.bit_count() == killed_words
            assert bits >> domain_words == 0
            self.cache_bits(mask_id, bits)
            self.metadata_cache[mask_id] = (
                domain_words, killed_words, digest
            )
        return self.bits_cache[mask_id]

    def record(self, mask_id):
        domain_words, killed_words, digest = self.metadata(mask_id)
        return {
            "mask_id": mask_id,
            "domain_words": domain_words,
            "killed_words": killed_words,
            "mask_sha256": digest,
            "payload_location": "SQLite masks.zlib_payload",
        }


def block_starts(parents):
    starts = {}
    previous = None
    for index, parent in enumerate(parents):
        if index == 0 or parent != previous:
            assert parent not in starts
            starts[parent] = index
        previous = parent
    return starts


def build_structural_context(trace, domains, d24):
    viz = load_viz()
    with (ROOT / "gate2-l7-construction-L8.pkl").open("rb") as handle:
        state8 = pickle.load(handle)
    births_by_level = exact_birth_levels(viz)
    points_by_level, origins = build_path_origins(viz)
    catalog = build_l8_catalog(
        state8, viz, births_by_level, origins, d24
    )
    assert len(catalog["points"]) == EXPECTED_L8_POINTS
    points8 = [tuple(point) for point in points_by_level[TARGET_LEVEL]]
    assert len(points8) == EXPECTED_L8_POINTS
    parents8 = viz["levels"][TARGET_LEVEL]["parents"]
    starts8 = block_starts(parents8)

    path_index_by_stable_id = {
        origin["stable_id"]: index
        for index, origin in enumerate(origins[TARGET_LEVEL])
    }
    assert len(path_index_by_stable_id) == EXPECTED_L8_POINTS
    catalog_index_by_stable_id = {
        record["stable_id"]: index
        for index, record in enumerate(catalog["points"])
    }
    assert len(catalog_index_by_stable_id) == EXPECTED_L8_POINTS
    for record in catalog["points"]:
        path_index = path_index_by_stable_id[record["stable_id"]]
        assert tuple(points8[path_index]) == tuple(record["coordinate"])
        record["l8_path_index"] = path_index

    child_states = sorted(
        trace["child_states"],
        key=lambda item: (
            item["source_gap"], item["l7_parent_gap"], item["l8_gap"]
        ),
    )
    states = []
    source_counts = Counter()
    child_counts = Counter()
    for state_ordinal, item in enumerate(child_states):
        source_gap = item["source_gap"]
        definition = SOURCE_DEFINITIONS[source_gap]
        assert item["witness_type"] == definition["witness_type"]
        gap = item["l8_gap"]
        word = tuple(state8["words"][gap])
        assert list(word) == item["actual_selected_connector_word"]
        rank, schedule_entry = catalog["schedule_by_gap"][gap]
        start = tuple(state8["anchors"][gap])
        assert item["step"] == state8["parent_word"][gap]
        assert add(start, apply(M_BAL3, MENU[item["step"]])) == tuple(
            state8["anchors"][gap + 1]
        )
        if word not in domains[item["step"]]:
            raise AssertionError(
                ("selected L8 word is absent from its exact domain", gap)
            )
        child_start = starts8[gap]
        child_stop = child_start
        while child_stop < len(parents8) and parents8[child_stop] == gap:
            child_stop += 1
        assert child_stop - child_start == len(word)
        children = []
        for slot, step in enumerate(word):
            l9_gap = child_start + slot
            assert child_start <= l9_gap < child_stop
            assert parents8[l9_gap] == gap
            assert sub(points8[l9_gap + 1], points8[l9_gap]) == MENU[step]
            children.append({
                "slot": slot,
                "l9_gap": l9_gap,
                "step": step,
                "start": apply(M_BAL3, points8[l9_gap]),
            })
            child_counts[source_gap] += 1
        state = {
            "state_ordinal": state_ordinal,
            "identity": (
                source_gap, item["l7_parent_gap"], item["l8_gap"]
            ),
            "source_gap": source_gap,
            "witness_type": definition["witness_type"],
            "l7_parent_gap": item["l7_parent_gap"],
            "l8_gap": gap,
            "step": item["step"],
            "actual_word": word,
            "pipeline_rank": rank,
            "pipeline_sweep_tile": schedule_entry["sweep_tile"],
            "start": start,
            "children": tuple(children),
            "endpoint_ids": definition["tagged_endpoint_stable_ids"],
        }
        states.append(state)
        source_counts[source_gap] += 1

    assert len(states) == EXPECTED_L8_STATES
    assert sum(child_counts.values()) == EXPECTED_L9_CHILDREN
    assert sum(
        len(state["endpoint_ids"]) for state in states
    ) == EXPECTED_ENDPOINT_STATE_PAIRS
    for source_gap, definition in SOURCE_DEFINITIONS.items():
        assert source_counts[source_gap] == definition["expected_states"]
        assert child_counts[source_gap] == definition["expected_children"]

    endpoint_catalog_indexes = {
        stable_id: catalog_index_by_stable_id[stable_id]
        for definition in SOURCE_DEFINITIONS.values()
        for stable_id in definition["tagged_endpoint_stable_ids"]
    }
    for state in states:
        for stable_id in state["endpoint_ids"]:
            endpoint = catalog["points"][
                endpoint_catalog_indexes[stable_id]
            ]
            assert endpoint["activation_action"] < state["pipeline_rank"]
    return {
        "catalog": catalog,
        "states": states,
        "endpoint_catalog_indexes": endpoint_catalog_indexes,
        "catalog_index_by_stable_id": catalog_index_by_stable_id,
    }


def build_direction_indexes(context, budget):
    points = context["catalog"]["points"]
    indexes8 = {}
    indexes9 = {}
    summaries = []
    for stable_id, endpoint_index in sorted(
        context["endpoint_catalog_indexes"].items()
    ):
        endpoint = tuple(points[endpoint_index]["coordinate"])
        index8 = {}
        index9 = {}
        digest = hashlib.sha256()
        for partner_index, partner in enumerate(points):
            budget.consume(label="direction-index")
            if partner_index == endpoint_index:
                continue
            direction8 = primitive(sub(tuple(partner["coordinate"]), endpoint))
            assert direction8 is not None
            assert direction8 not in index8, (
                "three collinear completed-L8 points", stable_id, direction8
            )
            direction9 = primitive(apply(M_BAL3, direction8))
            assert direction9 is not None
            assert direction9 not in index9
            index8[tuple(direction8)] = partner_index
            index9[tuple(direction9)] = partner_index
        assert len(index8) == len(index9) == EXPECTED_L8_POINTS - 1
        for direction, partner_index in sorted(index8.items()):
            partner = points[partner_index]
            digest.update(stable_bytes((
                direction,
                partner_index,
                partner["stable_id"],
                partner["activation_action"],
                partner["coordinate"],
            )))
            digest.update(b"\n")
        indexes8[stable_id] = index8
        indexes9[stable_id] = index9
        summaries.append({
            "tagged_endpoint_stable_id": stable_id,
            "directions": len(index8),
            "l8_direction_index_sha256": digest.hexdigest(),
            "affine_child_direction_index_is_bijective": True,
        })
    return indexes8, indexes9, summaries


def build_observations(context, indexes8, indexes9, domains):
    points = context["catalog"]["points"]
    observations = []
    domain_sizes = {step: len(domain) for step, domain in domains.items()}
    for state in context["states"]:
        for endpoint_ordinal, stable_id in enumerate(state["endpoint_ids"]):
            endpoint_index = context["endpoint_catalog_indexes"][stable_id]
            endpoint8 = tuple(points[endpoint_index]["coordinate"])
            observations.append({
                "state_ordinal": state["state_ordinal"],
                "endpoint_ordinal": endpoint_ordinal,
                "endpoint_stable_id": stable_id,
                "endpoint_index": endpoint_index,
                "phase": 0,
                "slot": -1,
                "step": state["step"],
                "domain_words": domain_sizes[state["step"]],
                "start": state["start"],
                "endpoint_coordinate": endpoint8,
                "direction_index": indexes8[stable_id],
                "pipeline_rank": state["pipeline_rank"],
                "selected_word": state["actual_word"],
            })
            endpoint9 = apply(M_BAL3, endpoint8)
            for child in state["children"]:
                observations.append({
                    "state_ordinal": state["state_ordinal"],
                    "endpoint_ordinal": endpoint_ordinal,
                    "endpoint_stable_id": stable_id,
                    "endpoint_index": endpoint_index,
                    "phase": 1,
                    "slot": child["slot"],
                    "step": child["step"],
                    "domain_words": domain_sizes[child["step"]],
                    "start": child["start"],
                    "endpoint_coordinate": endpoint9,
                    "direction_index": indexes9[stable_id],
                    "pipeline_rank": state["pipeline_rank"],
                    "selected_word": None,
                })
    assert sum(item["phase"] == 0 for item in observations) == (
        EXPECTED_ENDPOINT_STATE_PAIRS
    )
    assert len({item["step"] for item in observations}) == (
        EXPECTED_EFFECTIVE_STEPS
    )
    return observations


def site_offsets_for_domain(domain, step, budget):
    expected_endpoint = apply(M_BAL3, MENU[step])
    offsets = set()
    for word in domain:
        budget.consume(label="domain-site-model")
        position = (0, 0, 0)
        for menu_index in word:
            position = add(position, MENU[menu_index])
        assert position == expected_endpoint
        offsets.update(word_interiors((0, 0, 0), word))
    return offsets


def requested_offset_associations(
    observations, site_offsets, context, budget,
):
    points = context["catalog"]["points"]
    associations = defaultdict(list)
    for observation in observations:
        endpoint = observation["endpoint_coordinate"]
        for offset in site_offsets:
            budget.consume(label="offset-partner-join")
            query = add(observation["start"], offset)
            if query == endpoint:
                continue
            direction = primitive(sub(query, endpoint))
            assert direction is not None
            partner_index = observation["direction_index"].get(
                tuple(direction)
            )
            if partner_index is None:
                continue
            partner = points[partner_index]
            if partner["activation_action"] >= observation["pipeline_rank"]:
                continue
            partner_coordinate = tuple(partner["coordinate"])
            if observation["phase"] == 1:
                partner_coordinate = apply(M_BAL3, partner_coordinate)
            if query == partner_coordinate:
                # A candidate equal to the old partner is a collision channel,
                # not an interior point strictly on this two-endpoint secant.
                continue
            assert len({endpoint, partner_coordinate, query}) == 3
            assert primitive(sub(partner_coordinate, endpoint)) == direction
            effect_key = (
                observation["state_ordinal"],
                observation["endpoint_ordinal"],
                observation["phase"],
                observation["slot"],
                partner_index,
            )
            associations[offset].append(effect_key)
    return associations


def exact_requested_site_masks(domain, requested_offsets, budget):
    bits_by_offset = {offset: 0 for offset in requested_offsets}
    for word_index, word in enumerate(domain):
        budget.consume(label="domain-word-mask-scan")
        present = set(word_interiors((0, 0, 0), word)) & requested_offsets
        flag = 1 << word_index
        for offset in present:
            bits_by_offset[offset] |= flag
    assert all(bits for bits in bits_by_offset.values())
    return bits_by_offset


def expected_effect_lattice(observations):
    grouped = defaultdict(list)
    for observation in observations:
        grouped[observation["step"]].append(observation)
    lattice = {}
    for step, records in grouped.items():
        domain_sizes = {record["domain_words"] for record in records}
        assert len(domain_sizes) == 1
        lattice[step] = {
            "domain_words": domain_sizes.pop(),
            "observations": len(records),
            "observation_keys": frozenset(
                (
                    record["state_ordinal"], record["endpoint_ordinal"],
                    record["phase"], record["slot"],
                )
                for record in records
            ),
            "phase_0_observations": sum(
                record["phase"] == 0 for record in records
            ),
            "unique_phase_0_selected_words": len({
                tuple(record["selected_word"])
                for record in records if record["phase"] == 0
            }),
        }
        assert len(lattice[step]["observation_keys"]) == len(records)
    assert len(lattice) == EXPECTED_EFFECTIVE_STEPS
    return lattice


def validate_effect_checkpoints(connection, expected_lattice):
    completed = {}
    rows = connection.execute(
        "SELECT step,domain_words,site_offsets,requested_offsets,"
        "nonzero_effects,summary_json,summary_sha256 "
        "FROM completed_steps ORDER BY step"
    )
    for row in rows:
        step, domain_words, sites, requested, nonzero, payload, digest = row
        if step in completed:
            raise RuntimeError(f"duplicate completed effect step {step}")
        if step not in expected_lattice:
            raise RuntimeError(f"unexpected completed effect step {step}")
        expected = expected_lattice[step]
        if domain_words != expected["domain_words"]:
            raise RuntimeError(
                f"completed step {step} has the wrong domain size"
            )
        if hashlib.sha256(payload.encode()).hexdigest() != digest:
            raise RuntimeError(
                f"completed step {step} summary commitment mismatch"
            )
        summary = json.loads(payload)
        duplicated = {
            "step": step,
            "domain_words": domain_words,
            "site_offsets": sites,
            "requested_offsets": requested,
            "nonzero_effects": nonzero,
        }
        for key, value in duplicated.items():
            if summary.get(key) != value:
                raise RuntimeError(
                    f"completed step {step} summary field mismatch: {key}"
                )
        for key in (
            "observations", "phase_0_observations",
            "unique_phase_0_selected_words",
        ):
            if summary.get(key) != expected[key]:
                raise RuntimeError(
                    f"completed step {step} eligibility mismatch: {key}"
                )
        if not (0 <= requested <= sites and nonzero >= 0):
            raise RuntimeError(f"invalid completed-step counts for {step}")
        effect_rows = connection.execute(
            "SELECT e.state_ordinal,e.endpoint_ordinal,e.phase,e.slot,"
            "e.partner_index,e.domain_words,m.domain_words,m.killed_words,"
            "m.mask_sha256 FROM effects e JOIN masks m ON e.mask_id=m.mask_id "
            "WHERE e.step=? ORDER BY e.state_ordinal,e.endpoint_ordinal,"
            "e.phase,e.slot,e.partner_index",
            (step,),
        ).fetchall()
        if len(effect_rows) != nonzero:
            raise RuntimeError(
                f"completed step {step} has the wrong effect-row count"
            )
        effect_commitment_records = []
        for effect_row in effect_rows:
            effect_key = tuple(effect_row[:5])
            if effect_key[:4] not in expected["observation_keys"]:
                raise RuntimeError(
                    f"completed step {step} has an alien observation key"
                )
            if effect_row[5] != domain_words or effect_row[6] != domain_words:
                raise RuntimeError(
                    f"completed step {step} has a cross-domain effect row"
                )
            if not (0 <= effect_key[4] < EXPECTED_L8_POINTS):
                raise RuntimeError(
                    f"completed step {step} has an invalid partner index"
                )
            if effect_row[7] <= 0:
                raise RuntimeError(
                    f"completed step {step} materializes a zero effect"
                )
            effect_commitment_records.append([
                list(effect_key), effect_row[8], effect_row[7]
            ])
        if stable_hash(effect_commitment_records) != summary.get(
            "effect_key_mask_stream_sha256"
        ):
            raise RuntimeError(
                f"completed step {step} effect commitment mismatch"
            )
        completed[step] = domain_words
    effect_steps = {
        row[0] for row in connection.execute("SELECT DISTINCT step FROM effects")
    }
    if not effect_steps <= set(completed):
        raise RuntimeError(
            "effect rows exist outside whole completed-step transactions"
        )
    return completed


def scan_effect_steps(
    connection, mask_store, domains, observations, context, budget,
    stop_after_steps, effect_lattice,
):
    completed = validate_effect_checkpoints(connection, effect_lattice)
    observations_by_step = defaultdict(list)
    for observation in observations:
        observations_by_step[observation["step"]].append(observation)
    assert set(observations_by_step) <= set(domains)
    processed_this_invocation = 0
    for ordinal, step in enumerate(sorted(observations_by_step), 1):
        domain = domains.pop(step)
        selected_word_indexes = {}
        unique_selected_indexes = {}
        for observation in observations_by_step[step]:
            if observation["phase"] != 0:
                continue
            word = tuple(observation["selected_word"])
            if word not in unique_selected_indexes:
                try:
                    unique_selected_indexes[word] = domain.index(word)
                except ValueError as error:
                    raise AssertionError(
                        ("selected word absent from exact domain", step, word)
                    ) from error
            observation_key = (
                observation["state_ordinal"],
                observation["endpoint_ordinal"],
                observation["phase"], observation["slot"],
            )
            selected_word_indexes[observation_key] = (
                unique_selected_indexes[word]
            )
        assert len(selected_word_indexes) == effect_lattice[step][
            "phase_0_observations"
        ]
        assert len(unique_selected_indexes) == effect_lattice[step][
            "unique_phase_0_selected_words"
        ]
        if step in completed:
            assert completed[step] == len(domain)
            del domain
            continue
        if (
            stop_after_steps is not None
            and processed_this_invocation >= stop_after_steps
        ):
            domains[step] = domain
            break
        budget.check(f"before effect step {step}")
        print(
            f"effect step {ordinal}/{len(observations_by_step)}: "
            f"step={step}, words={len(domain)}, "
            f"observations={len(observations_by_step[step])}",
            flush=True,
        )
        site_offsets = site_offsets_for_domain(domain, step, budget)
        associations = requested_offset_associations(
            observations_by_step[step], site_offsets, context, budget
        )
        requested_offsets = set(associations)
        bits_by_offset = exact_requested_site_masks(
            domain, requested_offsets, budget
        )
        effect_bits = defaultdict(int)
        for offset, effect_keys in associations.items():
            bits = bits_by_offset[offset]
            for effect_key in effect_keys:
                effect_bits[effect_key] |= bits

        observation_by_key = {
            (
                item["state_ordinal"], item["endpoint_ordinal"],
                item["phase"], item["slot"],
            ): item
            for item in observations_by_step[step]
        }
        with connection:
            connection.execute("DELETE FROM effects WHERE step=?", (step,))
            mask_store.zero(len(domain))
            for effect_key, bits in sorted(effect_bits.items()):
                state_ordinal, endpoint_ordinal, phase, slot, partner_index = (
                    effect_key
                )
                assert (
                    state_ordinal, endpoint_ordinal, phase, slot
                ) in observation_by_key
                assert bits.bit_count() > 0
                if phase == 0:
                    selected_index = selected_word_indexes[
                        (state_ordinal, endpoint_ordinal, phase, slot)
                    ]
                    assert not ((bits >> selected_index) & 1)
                mask_id = mask_store.add(bits, len(domain))
                connection.execute(
                    "INSERT INTO effects(state_ordinal,endpoint_ordinal,phase,"
                    "slot,partner_index,step,domain_words,mask_id) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (
                        state_ordinal, endpoint_ordinal, phase, slot,
                        partner_index, step, len(domain), mask_id,
                    ),
                )
            summary = {
                "step": step,
                "domain_words": len(domain),
                "site_offsets": len(site_offsets),
                "observations": len(observations_by_step[step]),
                "phase_0_observations": len(selected_word_indexes),
                "unique_phase_0_selected_words": len(
                    unique_selected_indexes
                ),
                "requested_offsets": len(requested_offsets),
                "nonzero_effects": len(effect_bits),
                "site_offset_stream_sha256": stable_hash(sorted(site_offsets)),
                "effect_key_mask_stream_sha256": stable_hash([
                    [list(key), mask_sha256(bits, len(domain)), bits.bit_count()]
                    for key, bits in sorted(effect_bits.items())
                ]),
            }
            payload = json.dumps(
                summary, sort_keys=True, separators=(",", ":")
            )
            connection.execute(
                "INSERT INTO completed_steps(step,domain_words,site_offsets,"
                "requested_offsets,nonzero_effects,summary_json,"
                "summary_sha256) VALUES (?,?,?,?,?,?,?)",
                (
                    step, len(domain), len(site_offsets),
                    len(requested_offsets), len(effect_bits),
                    payload, hashlib.sha256(payload.encode()).hexdigest(),
                ),
            )
        budget.check(f"after effect step {step} commit")
        processed_this_invocation += 1
        del domain, site_offsets, associations, requested_offsets
        del bits_by_offset, effect_bits
        gc.collect()
    return processed_this_invocation


def decode_upstream_mask(record, payloads):
    payload = payloads[record["exact_payload_ref"]]
    assert payload["domain_words"] == record["domain_words"]
    raw = zlib.decompress(base64.b64decode(payload["payload_base64"]))
    assert len(raw) == payload["uncompressed_bytes"]
    assert hashlib.sha256(raw).hexdigest() == record["mask_sha256"]
    bits = int.from_bytes(raw, "little")
    assert bits.bit_count() == record["killed_words"]
    assert bits >> record["domain_words"] == 0
    return bits


def effect_index(connection):
    result = {}
    for row in connection.execute(
        "SELECT state_ordinal,endpoint_ordinal,phase,slot,partner_index,"
        "mask_id FROM effects ORDER BY state_ordinal,endpoint_ordinal,phase,"
        "slot,partner_index"
    ):
        key = tuple(row[:5])
        assert key not in result
        result[key] = row[5]
    return result


def upstream_state_indexes(compatibility):
    l8 = {}
    for record in compatibility["states"]["L8"]:
        key = (
            record["identity"]["source_gap"],
            record["identity"]["l7_parent_gap"],
            record["identity"]["l8_gap"],
        )
        if key in l8:
            raise AssertionError(("duplicate upstream L8 identity", key))
        l8[key] = record
    l9 = {}
    for record in compatibility["states"]["L9"]:
        key = (
            record["identity"]["source_gap"],
            record["identity"]["l7_parent_gap"],
            record["identity"]["l8_gap"],
            record["identity"]["l9_gap"],
        )
        if key in l9:
            raise AssertionError(("duplicate upstream L9 identity", key))
        l9[key] = record
    assert len(l8) == EXPECTED_L8_STATES
    assert len(l9) == EXPECTED_L9_CHILDREN
    return l8, l9


def decoded_partner_mask_index(records, payloads, label):
    result = {}
    for item in records:
        partner_id = item["key"]
        assert isinstance(partner_id, str)
        if partner_id in result:
            raise AssertionError(("duplicate upstream partner mask", label,
                                  partner_id))
        result[partner_id] = decode_upstream_mask(item["mask"], payloads)
    return result


def audit_against_upstream(
    connection, mask_store, context, compatibility, budget,
):
    effects = effect_index(connection)
    payloads = compatibility["exact_mask_store"]["payloads"]
    upstream_l8, upstream_l9 = upstream_state_indexes(compatibility)
    points = context["catalog"]["points"]
    catalog_index_by_stable_id = context["catalog_index_by_stable_id"]
    all_tagged_ids = {
        stable_id
        for definition in SOURCE_DEFINITIONS.values()
        for stable_id in definition["tagged_endpoint_stable_ids"]
    }
    effects_by_observation = defaultdict(list)
    for key, mask_id in effects.items():
        effects_by_observation[key[:4]].append((key[4], mask_id))
    compared_partner_masks = 0
    compared_direct_masks = 0
    for state in context["states"]:
        budget.consume(label="upstream-crosscheck")
        l8_record = upstream_l8[state["identity"]]
        l8_address = l8_record["literal_joint_address"]["l8_stitch"]
        l8_source = l8_record["literal_joint_address"]["source_token"]
        assert l8_record["schema"] == (
            "physical-tagged-token-L8-compatibility-state-v1"
        )
        assert l8_record["domain_words"] == state["domain_words"]
        assert l8_record["selected_word_avoids_tagged_component"] is True
        assert l8_address["l8_gap"] == state["l8_gap"]
        assert l8_address["step"] == state["step"]
        assert tuple(l8_address["actual_selected_connector_word"]) == (
            state["actual_word"]
        )
        assert tuple(
            l8_source["ordered_tagged_endpoint_stable_ids"]
        ) == tuple(state["endpoint_ids"])
        assert l8_source["source_gap"] == state["source_gap"]
        assert l8_source["witness_type"] == state["witness_type"]
        upstream_successors = tuple(
            (item["slot"], item["l9_gap"], item["step"])
            for item in l8_record["ordered_l9_successors"]
        )
        local_successors = tuple(
            (child["slot"], child["l9_gap"], child["step"])
            for child in state["children"]
        )
        assert upstream_successors == local_successors
        def partner_is_preexisting(partner_id):
            partner_index = catalog_index_by_stable_id[partner_id]
            return (
                points[partner_index]["activation_action"]
                < state["pipeline_rank"]
            )
        expected_partner = decoded_partner_mask_index(
            l8_record["physical_partner_masks"], payloads,
            ("L8", state["identity"]),
        )
        actual_by_partner = defaultdict(int)
        direct_actual = 0
        for endpoint_ordinal in range(len(state["endpoint_ids"])):
            observation_key = (
                state["state_ordinal"], endpoint_ordinal, 0, -1
            )
            for partner_index, mask_id in effects_by_observation.get(
                observation_key, ()
            ):
                partner_id = points[partner_index]["stable_id"]
                if partner_id in all_tagged_ids:
                    direct_actual |= mask_store.bits(mask_id)
                else:
                    actual_by_partner[partner_id] |= mask_store.bits(mask_id)
        for partner_id, expected in expected_partner.items():
            assert partner_is_preexisting(partner_id)
            assert actual_by_partner[partner_id] == expected
            compared_partner_masks += 1
        assert set(actual_by_partner) == set(expected_partner)

        direct_expected = decode_upstream_mask(
            l8_record["local_exact_components"][
                "direct_carried_tagged_pair_site_poison"
            ],
            payloads,
        )
        assert direct_actual == direct_expected
        compared_direct_masks += 1

        for child in state["children"]:
            l9_key = state["identity"] + (child["l9_gap"],)
            l9_record = upstream_l9[l9_key]
            l9_l8_address = l9_record["literal_joint_address"]["l8_stitch"]
            precursor = l9_record["literal_joint_address"][
                "l9_precursor_stitch"
            ]
            l9_source = l9_record["literal_joint_address"]["source_token"]
            assert l9_record["schema"] == (
                "physical-tagged-token-L9-precursor-compatibility-state-v1"
            )
            assert l9_record["domain_words"] == child["domain_words"]
            assert l9_l8_address["l8_gap"] == state["l8_gap"]
            assert l9_l8_address["step"] == state["step"]
            assert tuple(
                l9_l8_address["actual_selected_connector_word"]
            ) == state["actual_word"]
            assert precursor["l9_gap"] == child["l9_gap"]
            assert precursor["actual_child_slot_zero_based"] == child["slot"]
            assert precursor["step"] == child["step"]
            assert tuple(precursor["actual_parent_l8_word"]) == (
                state["actual_word"]
            )
            assert precursor["selected_l9_connector_word"] is None
            assert l9_record["selected_l9_connector_word"] is None
            assert tuple(
                l9_source["ordered_tagged_endpoint_stable_ids"]
            ) == tuple(state["endpoint_ids"])
            assert l9_source["source_gap"] == state["source_gap"]
            assert l9_source["witness_type"] == state["witness_type"]
            all_expected_partner = decoded_partner_mask_index(
                l9_record["physical_partner_masks"], payloads,
                ("L9", l9_key),
            )
            assert all(
                partner_id in catalog_index_by_stable_id
                for partner_id in all_expected_partner
            )
            expected_partner = {
                partner_id: bits
                for partner_id, bits in all_expected_partner.items()
                if partner_is_preexisting(partner_id)
            }
            actual_by_partner = defaultdict(int)
            direct_actual = 0
            for endpoint_ordinal in range(len(state["endpoint_ids"])):
                observation_key = (
                    state["state_ordinal"], endpoint_ordinal, 1,
                    child["slot"],
                )
                for partner_index, mask_id in effects_by_observation.get(
                    observation_key, ()
                ):
                    partner_id = points[partner_index]["stable_id"]
                    if partner_id in all_tagged_ids:
                        direct_actual |= mask_store.bits(mask_id)
                    else:
                        actual_by_partner[partner_id] |= mask_store.bits(mask_id)
            for partner_id, expected in expected_partner.items():
                assert actual_by_partner[partner_id] == expected
                compared_partner_masks += 1
            assert set(actual_by_partner) == set(expected_partner)

            direct_expected = decode_upstream_mask(
                l9_record["local_exact_components"][
                    "direct_carried_tagged_pair_site_poison"
                ],
                payloads,
            )
            assert direct_actual == direct_expected
            compared_direct_masks += 1
    return effects, {
        "L8_states_checked": EXPECTED_L8_STATES,
        "L9_children_checked": EXPECTED_L9_CHILDREN,
        "nonzero_physical_partner_masks_reproduced": compared_partner_masks,
        "direct_carried_pair_masks_reproduced": compared_direct_masks,
        "cutoff": None,
        "important_scope": (
            "L9 upstream partner masks born after the parent L8 rank are "
            "excluded because this checker carries preexisting tokens only"
        ),
    }


def profile_tuple(point):
    return (
        point["stable_id"],
        point["birth_level"],
        point["birth_gap"],
        point["interior_ordinal"],
        point["activation_action"],
        point["l8_path_index"],
    )


def profile_tuple_record(profile):
    return {
        "stable_id": profile[0],
        "birth_level": profile[1],
        "birth_gap": profile[2],
        "interior_ordinal": profile[3],
        "pipeline_activation_rank": profile[4],
        "l8_path_index": profile[5],
    }


def mask_key(mask_store, mask_id):
    domain_words, killed_words, digest = mask_store.metadata(mask_id)
    return domain_words, killed_words, digest


def token_record(
    state, endpoint_ordinal, endpoint, partner, partner_index,
    effects, mask_store,
):
    endpoint_coordinate = tuple(endpoint["coordinate"])
    partner_coordinate = tuple(partner["coordinate"])
    endpoint_relative = sub(endpoint_coordinate, state["start"])
    partner_relative = sub(partner_coordinate, state["start"])
    direction, moment = line_state(endpoint_relative, partner_relative)
    source_mask_id = effects.get((
        state["state_ordinal"], endpoint_ordinal, 0, -1, partner_index,
    ))
    if source_mask_id is None:
        source_mask_id = mask_store.zero(state["domain_words"])
    source_key = mask_key(mask_store, source_mask_id)

    children = []
    endpoint9 = apply(M_BAL3, endpoint_coordinate)
    partner9 = apply(M_BAL3, partner_coordinate)
    for child in state["children"]:
        endpoint_child_relative = sub(endpoint9, child["start"])
        partner_child_relative = sub(partner9, child["start"])
        child_direction, child_moment = line_state(
            endpoint_child_relative, partner_child_relative
        )
        child_mask_id = effects.get((
            state["state_ordinal"], endpoint_ordinal, 1, child["slot"],
            partner_index,
        ))
        if child_mask_id is None:
            child_mask_id = mask_store.zero(child["domain_words"])
        children.append({
            "slot": child["slot"],
            "l9_gap": child["l9_gap"],
            "step": child["step"],
            "domain_words": child["domain_words"],
            "endpoint_relative": tuple(endpoint_child_relative),
            "partner_relative": tuple(partner_child_relative),
            "primitive_direction": child_direction,
            "relative_moment": child_moment,
            "mask_id": child_mask_id,
            "mask_key": mask_key(mask_store, child_mask_id),
        })
    source_nonzero = source_key[1] > 0
    child_nonzero = any(child["mask_key"][1] > 0 for child in children)
    depth_shell = (
        "depth_0" if source_nonzero
        else "depth_1" if child_nonzero
        else "silent_through_depth_1"
    )
    return {
        "state_identity": state["identity"],
        "state_ordinal": state["state_ordinal"],
        "source_gap": state["source_gap"],
        "witness_type": state["witness_type"],
        "step": state["step"],
        "domain_words": state["domain_words"],
        "actual_word": state["actual_word"],
        "pipeline_rank": state["pipeline_rank"],
        "endpoint_ordinal": endpoint_ordinal,
        "endpoint_profile": profile_tuple(endpoint),
        "partner_profile": profile_tuple(partner),
        "endpoint_relative": tuple(endpoint_relative),
        "partner_relative": tuple(partner_relative),
        "primitive_direction": direction,
        "relative_moment": moment,
        "source_mask_id": source_mask_id,
        "source_mask_key": source_key,
        "children": tuple(children),
        "depth_shell": depth_shell,
    }


def projection_key(record, projection):
    pair = (
        record["endpoint_profile"][0], record["partner_profile"][0]
    )
    birth = (
        record["endpoint_profile"][1:], record["partner_profile"][1:]
    )
    common = (
        pair,
        record["witness_type"],
        record["step"],
        record["domain_words"],
        (record["source_mask_id"], record["source_mask_key"]),
        record["actual_word"],
    )
    if projection == "legacy_current_effect":
        return common + (birth,)
    pluecker = common + (
        birth, record["primitive_direction"], record["relative_moment"]
    )
    if projection == "physical_pluecker":
        return pluecker
    full = pluecker + (
        record["endpoint_relative"], record["partner_relative"]
    )
    if projection == "full_correlated":
        return full
    if projection == "literal_address":
        return full + (record["state_identity"],)
    raise KeyError(projection)


def outcome_key(record, outcome_kind):
    if outcome_kind == "ordered_child_mask_tree":
        return tuple(
            (
                child["slot"], child["step"], child["domain_words"],
                (child["mask_id"], child["mask_key"]),
            )
            for child in record["children"]
        )
    if outcome_kind == "ordered_child_correlated_tree":
        return tuple(
            (
                child["slot"], child["step"], child["domain_words"],
                child["endpoint_relative"], child["partner_relative"],
                child["primitive_direction"], child["relative_moment"],
                (child["mask_id"], child["mask_key"]),
            )
            for child in record["children"]
        )
    raise KeyError(outcome_kind)


def compact_token_record(record, mask_store):
    return {
        "state_identity": list(record["state_identity"]),
        "state_ordinal": record["state_ordinal"],
        "source_gap": record["source_gap"],
        "witness_type": record["witness_type"],
        "step": record["step"],
        "actual_word": list(record["actual_word"]),
        "pipeline_rank": record["pipeline_rank"],
        "endpoint": {
            "profile": profile_tuple_record(record["endpoint_profile"]),
            "current_frame_coordinate": list(record["endpoint_relative"]),
        },
        "partner": {
            "profile": profile_tuple_record(record["partner_profile"]),
            "current_frame_coordinate": list(record["partner_relative"]),
        },
        "primitive_Pluecker": {
            "g": list(record["primitive_direction"]),
            "m": list(record["relative_moment"]),
        },
        "source_mask": mask_store.record(record["source_mask_id"]),
        "ordered_children": [
            {
                "slot": child["slot"],
                "l9_gap": child["l9_gap"],
                "step": child["step"],
                "endpoint_current_frame_coordinate": list(
                    child["endpoint_relative"]
                ),
                "partner_current_frame_coordinate": list(
                    child["partner_relative"]
                ),
                "primitive_Pluecker": {
                    "g": list(child["primitive_direction"]),
                    "m": list(child["relative_moment"]),
                },
                "mask": mask_store.record(child["mask_id"]),
            }
            for child in record["children"]
        ],
        "depth_shell": record["depth_shell"],
    }


def token_stream_tuple(record):
    """Canonical all-field token commitment without verbose JSON labels."""
    return (
        record["state_identity"],
        record["state_ordinal"],
        record["source_gap"],
        record["witness_type"],
        record["step"],
        record["domain_words"],
        record["actual_word"],
        record["pipeline_rank"],
        record["endpoint_ordinal"],
        record["endpoint_profile"],
        record["partner_profile"],
        record["endpoint_relative"],
        record["partner_relative"],
        record["primitive_direction"],
        record["relative_moment"],
        (record["source_mask_id"], record["source_mask_key"]),
        tuple(
            (
                child["slot"], child["l9_gap"], child["step"],
                child["domain_words"], child["endpoint_relative"],
                child["partner_relative"], child["primitive_direction"],
                child["relative_moment"],
                (child["mask_id"], child["mask_key"]),
            )
            for child in record["children"]
        ),
        record["depth_shell"],
    )


def empty_projection_stats():
    return {
        projection: {
            outcome: {
                "occurrences": 0,
                "classes": 0,
                "singleton_classes": 0,
                "repeated_classes": 0,
                "noncongruent_classes": 0,
                "maximum_class_size": 0,
                "maximum_distinct_outcomes": 0,
                "class_size_histogram": {},
                "examples": [],
            }
            for outcome in OUTCOME_KINDS
        }
        for projection in PROJECTIONS
    }


def add_histogram(target, key, amount=1):
    text = str(key)
    target[text] = target.get(text, 0) + amount


def audit_pair_records(records, mask_store):
    result = empty_projection_stats()
    for projection in PROJECTIONS:
        groups = defaultdict(list)
        for record in records:
            groups[projection_key(record, projection)].append(record)
        for outcome_kind in OUTCOME_KINDS:
            stats = result[projection][outcome_kind]
            stats["occurrences"] = len(records)
            stats["classes"] = len(groups)
            for key, members in groups.items():
                size = len(members)
                add_histogram(stats["class_size_histogram"], size)
                stats["maximum_class_size"] = max(
                    stats["maximum_class_size"], size
                )
                if size == 1:
                    stats["singleton_classes"] += 1
                else:
                    stats["repeated_classes"] += 1
                outcomes = defaultdict(list)
                for member in members:
                    outcomes[outcome_key(member, outcome_kind)].append(member)
                stats["maximum_distinct_outcomes"] = max(
                    stats["maximum_distinct_outcomes"], len(outcomes)
                )
                if len(outcomes) > 1:
                    stats["noncongruent_classes"] += 1
                    if len(stats["examples"]) < 3:
                        stats["examples"].append({
                            "projection_key_sha256": stable_hash(key),
                            "class_size": size,
                            "distinct_outcomes": len(outcomes),
                            "members": [
                                compact_token_record(member, mask_store)
                                for member in members[:4]
                            ],
                        })
    return result


def merge_projection_stats(target, source, example_limit=8):
    for projection in PROJECTIONS:
        for outcome_kind in OUTCOME_KINDS:
            left = target[projection][outcome_kind]
            right = source[projection][outcome_kind]
            for key in (
                "occurrences", "classes", "singleton_classes",
                "repeated_classes", "noncongruent_classes",
            ):
                left[key] += right[key]
            left["maximum_class_size"] = max(
                left["maximum_class_size"], right["maximum_class_size"]
            )
            left["maximum_distinct_outcomes"] = max(
                left["maximum_distinct_outcomes"],
                right["maximum_distinct_outcomes"],
            )
            for size, count in right["class_size_histogram"].items():
                left["class_size_histogram"][size] = (
                    left["class_size_histogram"].get(size, 0) + count
                )
            available = example_limit - len(left["examples"])
            if available > 0:
                left["examples"].extend(right["examples"][:available])


def empty_chunk_summary():
    return {
        "token_occurrences": 0,
        "depth_shells": {},
        "birth_depth_shells": {},
        "projection_stats": empty_projection_stats(),
        "depth_examples": {
            "depth_0": [],
            "depth_1": [],
            "silent_through_depth_1": [],
        },
    }


def role_definitions(context):
    roles = []
    for source_gap in sorted(SOURCE_DEFINITIONS):
        states = [
            state for state in context["states"]
            if state["source_gap"] == source_gap
        ]
        for endpoint_ordinal, stable_id in enumerate(
            SOURCE_DEFINITIONS[source_gap]["tagged_endpoint_stable_ids"]
        ):
            roles.append({
                "role_ordinal": len(roles),
                "source_gap": source_gap,
                "endpoint_ordinal": endpoint_ordinal,
                "endpoint_stable_id": stable_id,
                "endpoint_catalog_index": context[
                    "endpoint_catalog_indexes"
                ][stable_id],
                "states": states,
            })
    assert len(roles) == 3
    return roles


def expected_token_occurrences(context):
    """Count eligibility independently of the block/token emission loop."""
    points = context["catalog"]["points"]
    activation_actions = sorted(
        point["activation_action"] for point in points
    )
    total = 0
    by_role = []
    for role in role_definitions(context):
        endpoint = points[role["endpoint_catalog_index"]]
        role_total = 0
        for state in role["states"]:
            assert endpoint["activation_action"] < state["pipeline_rank"]
            eligible_points = bisect.bisect_left(
                activation_actions, state["pipeline_rank"]
            )
            assert eligible_points >= 1
            role_total += eligible_points - 1
        total += role_total
        by_role.append({
            "role_ordinal": role["role_ordinal"],
            "source_gap": role["source_gap"],
            "endpoint_stable_id": role["endpoint_stable_id"],
            "expected_token_occurrences": role_total,
        })
    assert 0 < total <= TOKEN_OCCURRENCE_UPPER_BOUND
    return total, by_role


def activation_shell(partner, state):
    activation = partner["activation_action"]
    if activation == -1:
        return "inherited"
    lag = state["pipeline_rank"] - activation
    assert lag > 0
    return f"lag_base3_shell_{base3_shell(lag)}"


def process_token_block(
    role, partner_start, partner_stop, context, effects, mask_store, budget,
):
    points = context["catalog"]["points"]
    endpoint = points[role["endpoint_catalog_index"]]
    summary = empty_chunk_summary()
    digest = hashlib.sha256()
    for partner_index in range(partner_start, partner_stop):
        partner = points[partner_index]
        if partner_index == role["endpoint_catalog_index"]:
            continue
        pair_records = []
        for state in role["states"]:
            budget.consume(label="token-stream")
            if partner["activation_action"] >= state["pipeline_rank"]:
                continue
            record = token_record(
                state, role["endpoint_ordinal"], endpoint, partner,
                partner_index, effects, mask_store,
            )
            pair_records.append(record)
            summary["token_occurrences"] += 1
            add_histogram(summary["depth_shells"], record["depth_shell"])
            birth_shell = (
                endpoint["birth_level"], partner["birth_level"],
                activation_shell(partner, state), record["depth_shell"],
            )
            add_histogram(
                summary["birth_depth_shells"],
                json.dumps(as_json(birth_shell), separators=(",", ":")),
            )
            example_bucket = summary["depth_examples"][record["depth_shell"]]
            if len(example_bucket) < 3:
                example_bucket.append(compact_token_record(record, mask_store))
            digest.update(stable_bytes(token_stream_tuple(record)))
            digest.update(b"\n")
        if pair_records:
            pair_stats = audit_pair_records(pair_records, mask_store)
            merge_projection_stats(
                summary["projection_stats"], pair_stats, example_limit=3
            )
    summary["block_token_stream_sha256"] = digest.hexdigest()
    summary["partner_start"] = partner_start
    summary["partner_stop"] = partner_stop
    summary["role_ordinal"] = role["role_ordinal"]
    summary["source_gap"] = role["source_gap"]
    summary["endpoint_stable_id"] = role["endpoint_stable_id"]
    return summary


def scan_token_chunks(
    connection, context, effects, mask_store, budget, block_size,
    stop_after_blocks, chunk_lattice, expected_occurrences,
):
    completed = validate_token_checkpoints(
        connection, chunk_lattice, expected_occurrences
    )
    blocks_this_invocation = 0
    points = context["catalog"]["points"]
    for role in role_definitions(context):
        for partner_start in range(0, len(points), block_size):
            partner_stop = min(partner_start + block_size, len(points))
            key = (role["role_ordinal"], partner_start)
            assert key in chunk_lattice
            assert chunk_lattice[key]["partner_stop"] == partner_stop
            if key in completed:
                continue
            if (
                stop_after_blocks is not None
                and blocks_this_invocation >= stop_after_blocks
            ):
                return blocks_this_invocation
            budget.check(
                f"before token block role={key[0]} start={key[1]}"
            )
            summary = process_token_block(
                role, partner_start, partner_stop, context, effects,
                mask_store, budget,
            )
            assert summary["token_occurrences"] == chunk_lattice[key][
                "expected_token_occurrences"
            ]
            payload = json.dumps(summary, sort_keys=True, separators=(",", ":"))
            summary_digest = hashlib.sha256(payload.encode()).hexdigest()
            with connection:
                connection.execute(
                    "INSERT INTO token_chunks(role_ordinal,partner_start,"
                    "partner_stop,token_occurrences,block_sha256,summary_json,"
                    "summary_sha256) VALUES (?,?,?,?,?,?,?)",
                    (
                        role["role_ordinal"], partner_start, partner_stop,
                        summary["token_occurrences"],
                        summary["block_token_stream_sha256"], payload,
                        summary_digest,
                    ),
                )
            blocks_this_invocation += 1
            if blocks_this_invocation % 16 == 0:
                print(
                    f"token blocks committed this invocation: "
                    f"{blocks_this_invocation}",
                    flush=True,
                )
            budget.check(
                f"after token block role={key[0]} start={key[1]}"
            )
    return blocks_this_invocation


def expected_token_chunk_lattice(context, block_size):
    points = context["catalog"]["points"]
    lattice = {}
    for role in role_definitions(context):
        for start in range(0, len(points), block_size):
            stop = min(start + block_size, len(points))
            chunk_activations = sorted(
                points[index]["activation_action"]
                for index in range(start, stop)
            )
            occurrences = 0
            endpoint_in_chunk = (
                start <= role["endpoint_catalog_index"] < stop
            )
            for state in role["states"]:
                occurrences += bisect.bisect_left(
                    chunk_activations, state["pipeline_rank"]
                )
                if endpoint_in_chunk:
                    occurrences -= 1
            key = (role["role_ordinal"], start)
            assert key not in lattice
            lattice[key] = {
                "partner_stop": stop,
                "source_gap": role["source_gap"],
                "endpoint_stable_id": role["endpoint_stable_id"],
                "expected_token_occurrences": occurrences,
            }
    return lattice


def validate_token_checkpoints(
    connection, expected_lattice, expected_occurrences,
):
    completed = {}
    rows = connection.execute(
        "SELECT role_ordinal,partner_start,partner_stop,token_occurrences,"
        "block_sha256,summary_json,summary_sha256 FROM token_chunks "
        "ORDER BY role_ordinal,partner_start"
    )
    for row in rows:
        role, start, stop, occurrences, block_digest, payload, digest = row
        key = (role, start)
        if key in completed:
            raise RuntimeError(f"duplicate token chunk {key}")
        if key not in expected_lattice:
            raise RuntimeError(f"unexpected token chunk {key}")
        expected = expected_lattice[key]
        if stop != expected["partner_stop"]:
            raise RuntimeError(f"wrong partner range for token chunk {key}")
        if hashlib.sha256(payload.encode()).hexdigest() != digest:
            raise RuntimeError(f"token chunk summary mismatch for {key}")
        summary = json.loads(payload)
        duplicated = {
            "role_ordinal": role,
            "partner_start": start,
            "partner_stop": stop,
            "token_occurrences": occurrences,
            "block_token_stream_sha256": block_digest,
            "source_gap": expected["source_gap"],
            "endpoint_stable_id": expected["endpoint_stable_id"],
        }
        for field, value in duplicated.items():
            if summary.get(field) != value:
                raise RuntimeError(
                    f"token chunk {key} summary field mismatch: {field}"
                )
        if occurrences < 0:
            raise RuntimeError(f"negative token count for chunk {key}")
        if occurrences != expected["expected_token_occurrences"]:
            raise RuntimeError(
                f"wrong independently expected token count for chunk {key}"
            )
        completed[key] = occurrences
    if set(completed) == set(expected_lattice):
        total = sum(completed.values())
        if total != expected_occurrences:
            raise RuntimeError(
                "terminal token count differs from independent eligibility "
                f"count: stored={total}, expected={expected_occurrences}"
            )
    return completed


def aggregate_token_chunks(
    connection, expected_lattice, expected_occurrences,
):
    validate_token_checkpoints(
        connection, expected_lattice, expected_occurrences
    )
    aggregate = empty_chunk_summary()
    block_commitments = []
    rows = connection.execute(
        "SELECT role_ordinal,partner_start,partner_stop,token_occurrences,"
        "block_sha256,summary_json FROM token_chunks "
        "ORDER BY role_ordinal,partner_start"
    )
    for row in rows:
        role_ordinal, start, stop, occurrences, digest, payload = row
        summary = json.loads(payload)
        assert summary["token_occurrences"] == occurrences
        assert summary["block_token_stream_sha256"] == digest
        aggregate["token_occurrences"] += occurrences
        for key, count in summary["depth_shells"].items():
            aggregate["depth_shells"][key] = (
                aggregate["depth_shells"].get(key, 0) + count
            )
        for key, count in summary["birth_depth_shells"].items():
            aggregate["birth_depth_shells"][key] = (
                aggregate["birth_depth_shells"].get(key, 0) + count
            )
        merge_projection_stats(
            aggregate["projection_stats"], summary["projection_stats"]
        )
        for shell, examples in summary["depth_examples"].items():
            available = 8 - len(aggregate["depth_examples"][shell])
            if available > 0:
                aggregate["depth_examples"][shell].extend(examples[:available])
        block_commitments.append((
            role_ordinal, start, stop, occurrences, digest
        ))
    aggregate["hierarchical_token_stream_sha256"] = stable_hash(
        block_commitments
    )
    aggregate["committed_blocks"] = len(block_commitments)
    for projection in PROJECTIONS:
        for outcome_kind in OUTCOME_KINDS:
            stats = aggregate["projection_stats"][projection][outcome_kind]
            assert stats["occurrences"] == aggregate["token_occurrences"]
            assert (
                stats["singleton_classes"] + stats["repeated_classes"]
                == stats["classes"]
            )
            stats["all_classes_singleton"] = (
                stats["classes"] == stats["singleton_classes"]
            )
            stats["zero_disagreement_would_be_vacuous"] = (
                stats["repeated_classes"] == 0
            )
            stats["interpretation"] = (
                "noncongruent_classes > 0 is a finite exact falsifier; zero "
                "is nonvacuous only when repeated_classes > 0, and is never "
                "a universal all-action closure proof"
            )
    return aggregate


def mask_manifest(connection):
    digest = hashlib.sha256()
    masks = 0
    killed_total = 0
    raw_total = 0
    compressed_total = 0
    for row in connection.execute(
        "SELECT mask_id,domain_words,killed_words,mask_sha256,raw_bytes,"
        "zlib_payload FROM masks ORDER BY mask_id"
    ):
        mask_id, domain_words, killed, sha, raw_bytes, payload = row
        decoded = zlib.decompress(payload)
        assert len(decoded) == raw_bytes
        assert hashlib.sha256(decoded).hexdigest() == sha
        digest.update(stable_bytes((
            mask_id, domain_words, killed, sha, raw_bytes,
            hashlib.sha256(payload).hexdigest(),
        )))
        digest.update(b"\n")
        masks += 1
        killed_total += killed
        raw_total += raw_bytes
        compressed_total += len(payload)
    return {
        "unique_exact_masks": masks,
        "sum_killed_words_over_unique_masks": killed_total,
        "uncompressed_bytes": raw_total,
        "zlib_bytes": compressed_total,
        "mask_manifest_sha256": digest.hexdigest(),
        "payload_table": "masks",
        "encoding": (
            "zlib-compressed fixed-length little-endian bitset; bit i is "
            "connector-domain word i"
        ),
    }


def effect_manifest(connection):
    digest = hashlib.sha256()
    count = 0
    for row in connection.execute(
        "SELECT e.state_ordinal,e.endpoint_ordinal,e.phase,e.slot,"
        "e.partner_index,e.step,e.domain_words,m.killed_words,m.mask_sha256 "
        "FROM effects e JOIN masks m ON e.mask_id=m.mask_id "
        "ORDER BY e.state_ordinal,e.endpoint_ordinal,e.phase,e.slot,"
        "e.partner_index"
    ):
        digest.update(stable_bytes(tuple(row)))
        digest.update(b"\n")
        count += 1
    return {
        "nonzero_effect_rows": count,
        "effect_stream_sha256": digest.hexdigest(),
        "zero_effect_rows_materialized": 0,
        "zero_effect_semantics": (
            "absence of a row after the complete no-cutoff direction join "
            "means the exact fixed-length zero mask for that domain"
        ),
    }


def witness_token(
    state_identity, endpoint_id, partner_id, context, effects, mask_store,
):
    state = next(
        state for state in context["states"]
        if state["identity"] == state_identity
    )
    endpoint_ordinal = state["endpoint_ids"].index(endpoint_id)
    endpoint = context["catalog"]["points"][
        context["endpoint_catalog_indexes"][endpoint_id]
    ]
    partner_index = context["catalog_index_by_stable_id"][partner_id]
    partner = context["catalog"]["points"][partner_index]
    assert partner["activation_action"] < state["pipeline_rank"]
    return token_record(
        state, endpoint_ordinal, endpoint, partner, partner_index,
        effects, mask_store,
    )


def regression_3998_vs_zero(context, effects, mask_store):
    first = witness_token(
        WITNESS["state_A"], WITNESS["endpoint"], WITNESS["partner"],
        context, effects, mask_store,
    )
    second = witness_token(
        WITNESS["state_B"], WITNESS["endpoint"], WITNESS["partner"],
        context, effects, mask_store,
    )
    assert first["source_mask_key"][1] == 0
    assert second["source_mask_key"][1] == 0
    first_child = first["children"][WITNESS["slot"]]
    second_child = second["children"][WITNESS["slot"]]
    assert first_child["l9_gap"] == WITNESS["child_A"]
    assert second_child["l9_gap"] == WITNESS["child_B"]
    assert first_child["step"] == second_child["step"] == WITNESS["step"]
    assert first_child["mask_key"] == (
        WITNESS["domain_words"], WITNESS["positive_words"],
        WITNESS["positive_sha256"],
    )
    assert second_child["mask_key"] == (
        WITNESS["domain_words"], 0, WITNESS["zero_sha256"],
    )
    assert projection_key(first, "legacy_current_effect") == projection_key(
        second, "legacy_current_effect"
    )
    assert outcome_key(first, "ordered_child_mask_tree") != outcome_key(
        second, "ordered_child_mask_tree"
    )
    assert projection_key(first, "physical_pluecker") != projection_key(
        second, "physical_pluecker"
    )
    return {
        "passed": True,
        "common_legacy_current_effect_key_sha256": stable_hash(
            projection_key(first, "legacy_current_effect")
        ),
        "legacy_key_has_distinct_ordered_child_mask_trees": True,
        "exact_physical_Pluecker_key_separates_witness": True,
        "state_A": compact_token_record(first, mask_store),
        "state_B": compact_token_record(second, mask_store),
    }


def completed_step_summaries(connection):
    return [
        json.loads(row[0])
        for row in connection.execute(
            "SELECT summary_json FROM completed_steps ORDER BY step"
        )
    ]


def progress_record(
    connection, effect_lattice=None, chunk_lattice=None,
    expected_occurrences=None, expected_blocks_fallback=None,
):
    if effect_lattice is None:
        completed_steps = {
            row[0] for row in connection.execute(
                "SELECT step FROM completed_steps"
            )
        }
        effect_complete = False
        expected_steps = EXPECTED_EFFECTIVE_STEPS
    else:
        completed_steps = validate_effect_checkpoints(
            connection, effect_lattice
        )
        effect_complete = set(completed_steps) == set(effect_lattice)
        expected_steps = len(effect_lattice)
    if chunk_lattice is None:
        completed_chunks = {
            (row[0], row[1]): row[2]
            for row in connection.execute(
                "SELECT role_ordinal,partner_start,token_occurrences "
                "FROM token_chunks"
            )
        }
        token_complete = False
        expected_blocks = expected_blocks_fallback
    else:
        completed_chunks = validate_token_checkpoints(
            connection, chunk_lattice, expected_occurrences
        )
        token_complete = set(completed_chunks) == set(chunk_lattice)
        expected_blocks = len(chunk_lattice)
    tokens = sum(completed_chunks.values())
    return {
        "completed_effect_steps": len(completed_steps),
        "expected_effect_steps": expected_steps,
        "completed_token_blocks": len(completed_chunks),
        "expected_token_blocks": expected_blocks,
        "committed_token_occurrences": tokens,
        "expected_terminal_token_occurrences": expected_occurrences,
        "effect_key_lattice_exact": effect_complete,
        "token_key_range_lattice_exact": token_complete,
        "effect_phase_complete": effect_complete,
        "token_phase_complete": token_complete,
    }


def atomic_write_json(path, result):
    path = Path(path).resolve()
    if not path.parent.is_dir():
        raise FileNotFoundError(f"output parent does not exist: {path.parent}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return file_sha256(path), path.stat().st_size


def estimate_result(resource_policy, arguments):
    paths = {
        "trace": arguments.trace,
        "l9": arguments.l9,
        "compatibility": arguments.compatibility,
        "viz/walk3d-data.json": ROOT / "viz/walk3d-data.json",
        "gate2-l7-construction-L8.pkl": (
            ROOT / "gate2-l7-construction-L8.pkl"
        ),
        "connector_domains4.pkl": ROOT / "connector_domains4.pkl",
        "dstar5_fragile.pkl": ROOT / "dstar5_fragile.pkl",
    }
    # ``stat`` is intentional: estimate does not open or hash these artifacts.
    stat_only = {
        name: {
            "path": str(path),
            "exists": path.is_file(),
            "bytes_if_present": path.stat().st_size if path.is_file() else None,
        }
        for name, path in paths.items()
    }
    return {
        "status": (
            "static estimate only; no construction pickle, domain pickle, "
            "or pinned result JSON was opened"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "resource_policy": resource_policy,
        "stat_only_inputs": stat_only,
        "planned_exact_scope": {
            "L8_states": EXPECTED_L8_STATES,
            "ordered_L9_children": EXPECTED_L9_CHILDREN,
            "completed_L8_physical_points": EXPECTED_L8_POINTS,
            "tagged_endpoint_state_pairs": EXPECTED_ENDPOINT_STATE_PAIRS,
            "token_occurrence_upper_bound": TOKEN_OCCURRENCE_UPPER_BOUND,
            "effective_connector_steps": EXPECTED_EFFECTIVE_STEPS,
            "endpoint_or_distance_cutoff": None,
        },
        "storage_plan": (
            "SQLite stores deduplicated exact nonzero masks and block-level "
            "commitments; every zero token is streamed through the exact "
            "census/congruence reductions without a materialized row"
        ),
        "domain_loading": (
            "the full D2--4 size map is read for schedule reconstruction, "
            "but only the 99 source/child step domains are retained and "
            "sorted; unused word lists are discarded first"
        ),
        "rough_runtime": "tens of minutes to several hours at nice 15",
        "rough_peak_RSS": (
            "expected below the enforced 2200 MiB default cap; the former "
            "all-domain loader was observed to peak at 1880 MiB before work"
        ),
        "not_a_proof": True,
    }


def self_check_result(resource_policy):
    # No construction artifact is touched.  Exercise exact line transport,
    # mask storage/deduplication, depth classification, and congruence logic.
    endpoint_relative = (1, 2, 3)
    partner_relative = (4, 2, 3)
    direction, moment = line_state(endpoint_relative, partner_relative)
    assert direction == (1, 0, 0)
    assert moment == (0, 3, -2)
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE masks(mask_id INTEGER PRIMARY KEY,domain_words INTEGER,"
        "killed_words INTEGER,mask_sha256 TEXT,raw_bytes INTEGER,"
        "zlib_payload BLOB,UNIQUE(domain_words,mask_sha256))"
    )
    store = MaskStore(connection)
    with connection:
        zero = store.zero(7)
        positive = store.add((1 << 1) | (1 << 5), 7)
        duplicate = store.add((1 << 1) | (1 << 5), 7)
    assert positive == duplicate
    assert store.bits(zero) == 0
    assert store.bits(positive).bit_count() == 2
    synthetic_common = {
        "endpoint_profile": ("endpoint", 7, 10, 1, -1, 20),
        "partner_profile": ("partner", 7, 11, 2, -1, 21),
        "witness_type": "old-old-secant",
        "step": 3,
        "domain_words": 7,
        "source_mask_id": zero,
        "source_mask_key": (7, 0, mask_sha256(0, 7)),
        "actual_word": (1, 2),
        "primitive_direction": (1, 0, 0),
        "endpoint_relative": (1, 2, 3),
        "partner_relative": (4, 2, 3),
        "state_identity": (1, 2, 3),
    }
    first = {
        **synthetic_common,
        "relative_moment": (0, 3, -2),
        "children": ({
            "slot": 0,
            "step": 1,
            "domain_words": 7,
            "endpoint_relative": (3, 4, 5),
            "partner_relative": (6, 4, 5),
            "primitive_direction": (1, 0, 0),
            "relative_moment": (0, 5, -4),
            "mask_id": positive,
            "mask_key": (7, 2, mask_sha256((1 << 1) | (1 << 5), 7)),
        },),
    }
    second = {
        **synthetic_common,
        "relative_moment": (0, 4, -2),
        "children": ({
            **first["children"][0],
            "mask_id": zero,
            "mask_key": (7, 0, mask_sha256(0, 7)),
        },),
    }
    assert projection_key(first, "legacy_current_effect") == projection_key(
        second, "legacy_current_effect"
    )
    assert outcome_key(first, "ordered_child_mask_tree") != outcome_key(
        second, "ordered_child_mask_tree"
    )
    assert projection_key(first, "physical_pluecker") != projection_key(
        second, "physical_pluecker"
    )
    connection.close()
    return {
        "status": (
            "synthetic self-check passed; no construction pickle, domain "
            "pickle, or pinned result JSON was opened"
        ),
        "checker_sha256": file_sha256(Path(__file__).resolve()),
        "resource_policy": resource_policy,
        "checks": {
            "canonical_Pluecker_line": True,
            "fixed_length_zero_mask": True,
            "exact_mask_roundtrip": True,
            "exact_mask_deduplication": True,
            "weak_projection_noncongruence_detected": True,
            "Pluecker_refinement_separates_synthetic_witness": True,
            "large_artifacts_opened": False,
        },
    }


def run_result(arguments, resource_policy):
    checker_sha = file_sha256(Path(__file__).resolve())
    trace, l9, compatibility, observed = validate_run_inputs(arguments)
    run_metadata = {
        "schema_version": SCHEMA_VERSION,
        "checker_sha256": checker_sha,
        "input_sha256": observed,
        "partner_block_size": arguments.partner_block_size,
        "token_semantics": "preexisting-at-source oriented physical pair",
    }
    run_signature = stable_hash(run_metadata)
    connection, database_path = initialize_database(
        arguments.database, run_signature, run_metadata
    )
    mask_store = MaskStore(connection)
    budget = WorkBudget(
        arguments.max_seconds,
        arguments.max_rss_mib,
        arguments.max_work_units,
        arguments.check_interval,
    )
    context = None
    effect_lattice = None
    chunk_lattice = None
    expected_occurrences = None
    expected_occurrences_by_role = None
    expected_blocks = 3 * math.ceil(
        EXPECTED_L8_POINTS / arguments.partner_block_size
    )
    stop_reason = None
    try:
        relevant_steps = relevant_connector_steps(trace)
        domains, d24 = load_relevant_domains(relevant_steps)
        budget.check("after connector-domain load")
        context = build_structural_context(trace, domains, d24)
        del d24
        gc.collect()
        budget.check("after structural context and D2--4 release")
        for state in context["states"]:
            state["domain_words"] = len(domains[state["step"]])
            for child in state["children"]:
                child["domain_words"] = len(domains[child["step"]])
        indexes8, indexes9, direction_summaries = build_direction_indexes(
            context, budget
        )
        observations = build_observations(
            context, indexes8, indexes9, domains
        )
        effect_lattice = expected_effect_lattice(observations)
        chunk_lattice = expected_token_chunk_lattice(
            context, arguments.partner_block_size
        )
        expected_blocks = len(chunk_lattice)
        (
            expected_occurrences,
            expected_occurrences_by_role,
        ) = expected_token_occurrences(context)
        assert sum(
            item["expected_token_occurrences"]
            for item in chunk_lattice.values()
        ) == expected_occurrences
        relevant_steps = {item["step"] for item in observations}
        assert relevant_steps == set(domains)
        for step in list(domains):
            if step not in relevant_steps:
                del domains[step]
        assert len(domains) == EXPECTED_EFFECTIVE_STEPS
        gc.collect()
        scan_effect_steps(
            connection, mask_store, domains, observations, context, budget,
            arguments.stop_after_steps, effect_lattice,
        )
        del domains, observations, indexes8, indexes9
        gc.collect()

        progress = progress_record(
            connection, effect_lattice, chunk_lattice,
            expected_occurrences, expected_blocks,
        )
        upstream_audit = None
        witness = None
        if progress["effect_phase_complete"]:
            effects, upstream_audit = audit_against_upstream(
                connection, mask_store, context, compatibility, budget
            )
            witness = regression_3998_vs_zero(
                context, effects, mask_store
            )
            scan_token_chunks(
                connection, context, effects, mask_store, budget,
                arguments.partner_block_size, arguments.stop_after_blocks,
                chunk_lattice, expected_occurrences,
            )
        else:
            effects = None
        progress = progress_record(
            connection, effect_lattice, chunk_lattice,
            expected_occurrences, expected_blocks,
        )
        complete = (
            progress["effect_phase_complete"]
            and progress["token_phase_complete"]
        )
        token_summary = aggregate_token_chunks(
            connection, chunk_lattice, expected_occurrences
        )
        token_summary["independent_expected_token_occurrences"] = (
            expected_occurrences
        )
        token_summary["independent_expected_occurrences_by_role"] = (
            expected_occurrences_by_role
        )
        result = {
            "status": (
                "complete exact finite carried-ghost depth-0/1 probe; not a "
                "tail lemma, all-action safety certificate, or theorem"
                if complete else
                "resumable partial exact carried-ghost depth probe"
            ),
            "complete": complete,
            "checker_sha256": checker_sha,
            "run_signature": run_signature,
            "input_sha256": observed,
            "database": {
                "path": str(database_path),
                "schema_version": SCHEMA_VERSION,
                "resume_fail_closed": True,
                "mask_manifest": mask_manifest(connection),
                "effect_manifest": effect_manifest(connection),
            },
            "resource_policy": {**resource_policy, **budget.record()},
            "progress": progress,
            "direction_indexes": direction_summaries,
            "effect_step_summaries": completed_step_summaries(connection),
            "upstream_exact_mask_crosscheck": upstream_audit,
            "regression_3998_vs_zero": witness,
            "token_stream": token_summary,
            "projection_semantics": {
                "all_keys_include": (
                    "both stable endpoint identities, exact birth profiles, "
                    "the current step/domain/mask, and actual selected word"
                ),
                "legacy_current_effect": (
                    "omits current coordinates and Pluecker data; retained "
                    "to reproduce the known latent-partner failure"
                ),
                "physical_pluecker": (
                    "adds exact primitive (g,m), but not the two individual "
                    "current-frame endpoint coordinates"
                ),
                "full_correlated": (
                    "adds both individual current-frame coordinates"
                ),
                "literal_address": (
                    "also adds the concrete source state identity"
                ),
                "ordered_child_mask_tree": (
                    "ordered slot/step/domain/exact-mask tuple"
                ),
                "ordered_child_correlated_tree": (
                    "the mask tree plus transported child endpoint "
                    "coordinates and primitive (g,m)"
                ),
                "pair_local_reduction_is_exact": (
                    "every projection starts with the same two stable IDs, "
                    "so no class can cross a physical endpoint pair"
                ),
                "mask_equality": (
                    "computed with SQLite mask IDs assigned only after an "
                    "exact fixed-length raw-byte comparison; SHA-256 values "
                    "are output commitments, not semantic equality oracles"
                ),
            },
            "state_definition": {
                "token": (
                    "ordered tagged endpoint plus one physical partner that "
                    "has pipeline activation rank below the L8 stitch rank"
                ),
                "stable_endpoint_identities": True,
                "birth_level_gap_ordinal_and_activation_rank": True,
                "current_frame_coordinates": True,
                "primitive_Pluecker_g_m": True,
                "source_and_ordered_child_exact_masks": True,
                "actual_selected_L8_word": True,
                "independent_endpoint_address_streams": False,
                "endpoint_or_distance_cutoff": None,
            },
            "soundness_boundary": {
                "included": [
                    "all three pinned tagged endpoints",
                    "every physical point preexisting at each of 146 L8 source stitches",
                    "all exact source-domain candidate-site masks",
                    "all exact ordered L9 child candidate-site masks for carried tokens",
                    "zero-current-mask tokens and depth-1 latent reveals",
                    "pair-local exact congruence tests with literal vacuity counts",
                ],
                "omitted": [
                    "secants with neither endpoint among the three tagged endpoints",
                    "tokens born at the source stitch or later during completion of L8",
                    "selected L9 connector words and current-L9 prefix interiors",
                    "endpoint collision and candidate-internal-line unary channels",
                    "alternate connector histories and universal all-action Post closure",
                    "depth two or any infinite tail/ranking/contraction statement",
                    "complete availability and an unconditional Erdos #193 theorem",
                ],
                "finite_zero_disagreement_warning": (
                    "zero noncongruence is only finite non-falsification; it "
                    "is explicitly labeled vacuous when every class is a singleton"
                ),
            },
        }
        return result, 0
    except BudgetExceeded as error:
        stop_reason = str(error)
        progress = progress_record(
            connection, effect_lattice, chunk_lattice,
            expected_occurrences, expected_blocks,
        )
        result = {
            "status": "resource cap reached; safe resumable checkpoint",
            "complete": False,
            "stop_reason": stop_reason,
            "checker_sha256": checker_sha,
            "run_signature": run_signature,
            "input_sha256": observed,
            "database": {
                "path": str(database_path),
                "schema_version": SCHEMA_VERSION,
                "resume_fail_closed": True,
            },
            "resource_policy": {**resource_policy, **budget.record()},
            "progress": progress,
            "durability": (
                "only whole completed effect-step and token-block SQLite "
                "transactions are retained"
            ),
        }
        return result, 75
    finally:
        connection.close()


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("estimate", "self-check", "run"))
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--l9", type=Path, default=DEFAULT_L9)
    parser.add_argument(
        "--compatibility", type=Path, default=DEFAULT_COMPATIBILITY
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--partner-block-size", type=int, default=DEFAULT_BLOCK_SIZE
    )
    parser.add_argument("--max-seconds", type=float, default=6 * 60 * 60)
    parser.add_argument(
        "--max-rss-mib", type=float, default=DEFAULT_MAX_RSS_MIB
    )
    parser.add_argument("--max-work-units", type=int, default=200_000_000)
    parser.add_argument("--check-interval", type=int, default=50_000)
    parser.add_argument("--stop-after-steps", type=int)
    parser.add_argument("--stop-after-blocks", type=int)
    arguments = parser.parse_args()
    if arguments.partner_block_size <= 0:
        parser.error("--partner-block-size must be positive")
    if arguments.max_seconds <= 0 or arguments.max_rss_mib <= 0:
        parser.error("time and RSS caps must be positive")
    if arguments.max_work_units <= 0 or arguments.check_interval <= 0:
        parser.error("work cap and check interval must be positive")
    for name in ("stop_after_steps", "stop_after_blocks"):
        value = getattr(arguments, name)
        if value is not None and value < 0:
            parser.error(f"--{name.replace('_', '-')} cannot be negative")
    if arguments.mode == "run":
        database = arguments.database.resolve()
        output = arguments.output.resolve()
        protected = {
            Path(path).resolve() for path in input_paths(arguments).values()
        }
        protected.add(Path(__file__).resolve())
        if database == output:
            parser.error("--database and --output must be different paths")
        if database in protected or output in protected:
            parser.error(
                "database/output paths cannot overwrite pinned inputs or "
                "the checker source"
            )
    return arguments


def main():
    arguments = parse_arguments()
    if sys.flags.optimize:
        raise RuntimeError("run without -O; certificate assertions are required")
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"run from repository root: cd {ROOT}")
    resource_policy = enforce_resource_policy()
    if arguments.mode == "estimate":
        result = estimate_result(resource_policy, arguments)
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    if arguments.mode == "self-check":
        result = self_check_result(resource_policy)
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    result, exit_code = run_result(arguments, resource_policy)
    output_sha, output_bytes = atomic_write_json(arguments.output, result)
    print(json.dumps({
        "output": str(arguments.output.resolve()),
        "bytes": output_bytes,
        "sha256": output_sha,
        "complete": result["complete"],
        "exit_code": exit_code,
        "progress": result["progress"],
    }, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
