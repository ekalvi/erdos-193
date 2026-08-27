#!/usr/bin/env python3
"""Run a short configurable prefix without modifying the handwritten demo."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from typing import Any


def demonstrate(api: Mapping[str, Any], length: int) -> None:
    """Construct and finitely check a prefix through the supplied demo API."""
    if length < 1:
        raise ValueError("length must be positive")

    print(f"🧮 Attempting to construct a triple-free walk with {length} points.")
    walk = api["generate_walk"](length)
    print(f"🛠️  Constructed a candidate walk of {len(walk)} points.")
    print(f"   First point: {walk[0]}")
    print(f"   Last point:  {walk[-1]}")

    print("⏱️  Verifying...")
    pair_checks = api["verify_pair_law"](walk)
    print(f"✅ Hilbert pair law verified for {pair_checks} pairs.")

    triple_checks = api["verify_walk"](walk)
    print(f"✅ No collinear triples among {triple_checks} checked.")
    print("Finite checks illustrate the construction; they do not prove infinity.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a short prefix of the handwritten Erdős 193 demo."
    )
    parser.add_argument(
        "--length",
        type=int,
        default=60,
        help="number of selected points to construct and check (default: 60)",
    )
    return parser.parse_args()


def main() -> None:
    import hilbert_walk_demo

    demonstrate(vars(hilbert_walk_demo), parse_args().length)


if __name__ == "__main__":
    main()
