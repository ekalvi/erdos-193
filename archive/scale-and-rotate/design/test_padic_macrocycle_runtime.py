#!/usr/bin/env python3
"""Regression test for macrocycle checkpoint, log, and rate contracts."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "design" / "padic_macrocycle_lift.py"
THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}


def load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def run_producer(checkpoint, output, log, *, resume, max_seconds):
    command = [
        sys.executable,
        "-B",
        str(PRODUCER),
        "run",
        "--max-k",
        "2",
        "--latent-depth",
        "2",
        "--max-seconds",
        str(max_seconds),
        "--progress-seconds",
        "0.000000001",
        "--checkpoint-seconds",
        "0",
        "--checkpoint",
        str(checkpoint),
        "--output",
        str(output),
        "--log",
        str(log),
    ]
    if resume:
        command.append("--resume")
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRONMENT)
    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def read_log(path):
    records = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
            records.append(record)
    return records


def main():
    with tempfile.TemporaryDirectory(prefix="padic-macrocycle-runtime-") as directory:
        temporary = Path(directory)
        checkpoint = temporary / "resumed-checkpoint.json"
        output = temporary / "resumed-output.json"
        log = temporary / "resumed-run.jsonl"

        run_producer(
            checkpoint,
            output,
            log,
            resume=False,
            max_seconds=0.000000001,
        )
        first = load_json(checkpoint)
        first_active = first["active_precision"]
        if (
            first["status"] != "paused"
            or first_active["k"] != 1
            or first_active["next_x"] != 1
            or first["completed_state_edges"] != 3
        ):
            raise AssertionError("first bounded run did not retain row one")

        run_producer(
            checkpoint,
            output,
            log,
            resume=True,
            max_seconds=0.000000001,
        )
        second = load_json(checkpoint)
        second_active = second["active_precision"]
        if (
            second["status"] != "paused"
            or second_active["k"] != 1
            or second_active["next_x"] <= first_active["next_x"]
            or second["completed_state_edges"] <= first["completed_state_edges"]
        ):
            raise AssertionError("repeated bounded resume did not advance")

        run_producer(
            checkpoint,
            output,
            log,
            resume=True,
            max_seconds=0,
        )
        completed = load_json(checkpoint)
        if (
            completed["status"] != "complete"
            or completed["active_precision"] is not None
            or completed["completed_state_edges"] != 90
        ):
            raise AssertionError("resumed run did not complete exactly")

        fresh_checkpoint = temporary / "fresh-checkpoint.json"
        fresh_output = temporary / "fresh-output.json"
        fresh_log = temporary / "fresh-run.jsonl"
        run_producer(
            fresh_checkpoint,
            fresh_output,
            fresh_log,
            resume=False,
            max_seconds=0,
        )
        if load_json(output) != load_json(fresh_output):
            raise AssertionError("resumed output differs from uninterrupted output")

        records = read_log(log)
        events = {record["event"] for record in records}
        required = {"start", "resume_state", "progress", "paused", "complete"}
        if not required <= events:
            raise AssertionError("durable log event coverage is incomplete")
        starts = [record for record in records if record["event"] == "start"]
        if len(starts) != 3 or any(
            record["resource_settings"] != THREAD_ENVIRONMENT for record in starts
        ):
            raise AssertionError("start records omit resource identity")
        if not any(
            record["event"] == "resume_state"
            and record["mode"] == "resume"
            and record["active_next_x"] == 1
            for record in records
        ):
            raise AssertionError("resume state did not record the active frontier")

        progress_records = [
            record for record in records if record["event"] == "progress"
        ]
        if not progress_records:
            raise AssertionError("no progress records were persisted")
        for record in progress_records:
            expected_rate = (
                record["invocation_work"]
                / record["invocation_elapsed_seconds"]
            )
            observed_rate = record["rate_states_per_second"]
            tolerance = max(2.0, expected_rate * 0.02)
            if abs(observed_rate - expected_rate) > tolerance:
                raise AssertionError("rate mixes incompatible work/time intervals")
            if record["done"] > record["total"]:
                raise AssertionError("reported progress exceeds total work")

        print(json.dumps({
            "status": "verified",
            "first_active_next_x": first_active["next_x"],
            "second_active_next_x": second_active["next_x"],
            "completed_state_edges": completed["completed_state_edges"],
            "durable_log_records": len(records),
            "progress_records": len(progress_records),
            "resumed_matches_fresh": True,
        }, sort_keys=True))


if __name__ == "__main__":
    main()
