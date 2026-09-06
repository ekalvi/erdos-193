#!/usr/bin/env python3
"""Prototype a signed-Gaussian/Walsh coded path-loss measurement frame.

The proposed controlled-domain scheme assigns one rule ID to each monitored
path.  During slot n, packets for rule r receive the two-bit signed-Gaussian
mark

    alpha(r, n) = popcount(n) - 2*parity(r & n)  (mod 4).

A measurement point keeps four aggregate color counters per slot.  Their
signed complex difference is demodulated by the common Gaussian phase and a
fast Walsh-Hadamard transform recovers every path's constant per-slot volume.

This is a bounded algebra/engineering model, not a packet-level simulator or
an RFC-compatible implementation.  It reports exact constant-rate recovery,
counter/readout tradeoffs, clock-slip sensitivity, and the analytic sampling
noise expected from active Bernoulli-loss probes.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
import math


def power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def parse_probability(text: str) -> Fraction:
    value = Fraction(text)
    if not 0 <= value <= 1:
        raise argparse.ArgumentTypeError("probabilities must lie in [0, 1]")
    return value


def gaussian_state(rule: int, slot: int) -> int:
    """Column-phased Walsh symbol encoded as one of 1, i, -1, -i."""
    return (slot.bit_count() - 2 * ((rule & slot).bit_count() & 1)) % 4


def fwht(values: list[Fraction]) -> list[Fraction]:
    """Unnormalized in-place-order Walsh-Hadamard transform."""
    result = values.copy()
    width = 1
    while width < len(result):
        for start in range(0, len(result), 2 * width):
            for offset in range(width):
                left = result[start + offset]
                right = result[start + offset + width]
                result[start + offset] = left + right
                result[start + offset + width] = left - right
        width *= 2
    return result


def aggregate_colors(volumes: list[list[Fraction]]) -> list[tuple[Fraction, ...]]:
    """Return four aggregate color counters for every true slot."""
    rules = len(volumes)
    slots = len(volumes[0])
    counters: list[tuple[Fraction, ...]] = []
    for slot in range(slots):
        colors = [Fraction(0) for _ in range(4)]
        for rule in range(rules):
            colors[gaussian_state(rule, slot)] += volumes[rule][slot]
        counters.append(tuple(colors))
    return counters


def rotate_back(x: Fraction, y: Fraction, phase: int) -> tuple[Fraction, Fraction]:
    """Multiply x+i*y by i**(-phase)."""
    phase %= 4
    if phase == 0:
        return x, y
    if phase == 1:
        return y, -x
    if phase == 2:
        return -x, -y
    return -y, x


def decode_colors(
    counters: list[tuple[Fraction, ...]], *, cyclic_clock_slip: int = 0
) -> list[tuple[Fraction, Fraction]]:
    """Decode complex rule coefficients under an optional slot-label error."""
    slots = len(counters)
    real_samples: list[Fraction] = []
    imag_samples: list[Fraction] = []
    for assumed_slot in range(slots):
        true_slot = (assumed_slot + cyclic_clock_slip) % slots
        c0, c1, c2, c3 = counters[true_slot]
        real, imag = rotate_back(c0 - c2, c1 - c3, assumed_slot.bit_count())
        real_samples.append(real)
        imag_samples.append(imag)
    real_coefficients = fwht(real_samples)
    imag_coefficients = fwht(imag_samples)
    return [
        (real_coefficients[rule] / slots, imag_coefficients[rule] / slots)
        for rule in range(slots)
    ]


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else str(value)


def float_summary(value: float) -> float:
    return round(value, 9)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paths",
        type=int,
        default=64,
        help="number of paths and slots; must be a power of two <= 256 (default: 64)",
    )
    parser.add_argument(
        "--probes-per-path-slot",
        type=int,
        default=1,
        help="controlled active probes sent by each path in each slot (default: 1)",
    )
    parser.add_argument(
        "--normal-delivery",
        type=parse_probability,
        default=Fraction(999, 1000),
        help="normal per-probe delivery probability (default: 0.999)",
    )
    parser.add_argument(
        "--impaired-delivery",
        type=parse_probability,
        default=Fraction(9, 10),
        help="delivery probability on one impaired path (default: 0.9)",
    )
    parser.add_argument(
        "--impaired-path",
        type=int,
        default=7,
        help="zero-based impaired path ID (default: 7)",
    )
    parser.add_argument(
        "--slot-ms",
        type=Fraction,
        default=Fraction(10),
        help="measurement slot duration in milliseconds (default: 10)",
    )
    args = parser.parse_args()

    if not power_of_two(args.paths) or args.paths > 256:
        parser.error("--paths must be a power of two no greater than 256")
    if args.probes_per_path_slot < 1:
        parser.error("--probes-per-path-slot must be positive")
    if not 0 <= args.impaired_path < args.paths:
        parser.error("--impaired-path must select an existing path")
    if args.slot_ms <= 0:
        parser.error("--slot-ms must be positive")

    paths = slots = args.paths

    # Exercise every coefficient with a distinct exact value before running the
    # operationally shaped equal-probe scenario below.
    calibration = [
        [Fraction(3 * rule + 1, 7) for _ in range(slots)]
        for rule in range(paths)
    ]
    decoded_calibration = decode_colors(aggregate_colors(calibration))
    for rule, coefficient in enumerate(decoded_calibration):
        expected = Fraction(3 * rule + 1, 7)
        if coefficient != (expected, Fraction(0)):
            raise AssertionError(("calibration decode", rule, coefficient, expected))

    sent_rate = Fraction(args.probes_per_path_slot)
    delivery = [args.normal_delivery for _ in range(paths)]
    delivery[args.impaired_path] = args.impaired_delivery

    sent = [[sent_rate for _ in range(slots)] for _ in range(paths)]
    expected_received = [
        [sent_rate * delivery[rule] for _ in range(slots)]
        for rule in range(paths)
    ]

    sent_counters = aggregate_colors(sent)
    received_counters = aggregate_colors(expected_received)
    decoded_sent = decode_colors(sent_counters)
    decoded_received = decode_colors(received_counters)

    for rule in range(paths):
        if decoded_sent[rule] != (sent_rate, Fraction(0)):
            raise AssertionError(("sent decode", rule, decoded_sent[rule]))
        expected = sent_rate * delivery[rule]
        if decoded_received[rule] != (expected, Fraction(0)):
            raise AssertionError(("received decode", rule, decoded_received[rule], expected))

    slipped = decode_colors(received_counters, cyclic_clock_slip=1)
    slip_squared_error = sum(
        (float(real - sent_rate * delivery[rule])) ** 2 + float(imag) ** 2
        for rule, (real, imag) in enumerate(slipped)
    ) / paths
    slip_max_error = max(
        math.hypot(float(real - sent_rate * delivery[rule]), float(imag))
        for rule, (real, imag) in enumerate(slipped)
    )

    # With K probes per path and slot, independent Bernoulli delivery makes
    # every coded estimate collect shot noise from every path.  Dedicated
    # per-path counters collect only the selected path's shot noise.
    k = args.probes_per_path_slot
    coded_variance = sum(float(q * (1 - q)) for q in delivery) / (slots * k)
    coded_standard_error = math.sqrt(coded_variance)
    impaired_dedicated_error = math.sqrt(
        float(args.impaired_delivery * (1 - args.impaired_delivery)) / (slots * k)
    )
    normal_dedicated_error = math.sqrt(
        float(args.normal_delivery * (1 - args.normal_delivery)) / (slots * k)
    )
    delivery_gap = abs(float(args.normal_delivery - args.impaired_delivery))
    frames_for_five_sigma = (
        math.ceil((5 * coded_standard_error / delivery_gap) ** 2)
        if delivery_gap > 0
        else None
    )

    conventional_counters = 2 * paths
    four_color_counters = 4
    two_counter_demodulated = 2
    output = {
        "status": (
            "bounded expected-value prototype; not an RFC profile, packet-level "
            "benchmark, or production-readiness claim"
        ),
        "configuration": {
            "paths": paths,
            "slots_per_frame": slots,
            "slot_ms": fraction_text(args.slot_ms),
            "frame_ms": fraction_text(args.slot_ms * slots),
            "probes_per_path_slot": k,
            "probe_packets_per_frame": paths * slots * k,
            "normal_delivery": fraction_text(args.normal_delivery),
            "impaired_path": args.impaired_path,
            "impaired_delivery": fraction_text(args.impaired_delivery),
        },
        "exact_constant_rate_model": {
            "decoded_all_paths_exactly": True,
            "maximum_absolute_decode_error": "0",
            "interpretation": (
                "the four aggregate color counters recover every constant per-slot "
                "sent and expected-delivered path volume"
            ),
        },
        "hardware_tradeoff_per_measurement_point": {
            "conventional_two_color_per_path_counters": conventional_counters,
            "coded_four_color_aggregate_counters": four_color_counters,
            "coded_counters_if_common_phase_is_derived": two_counter_demodulated,
            "state_reduction_vs_four_color": conventional_counters / four_color_counters,
            "four_color_counter_deltas_exported_per_frame": four_color_counters * slots,
            "demodulated_signed_samples_exported_per_frame": slots,
            "trade": "counter state is exchanged for synchronized samples and frame latency",
        },
        "independent_packet_loss_noise": {
            "coded_delivery_standard_error_one_frame": float_summary(coded_standard_error),
            "dedicated_impaired_path_standard_error_one_frame": float_summary(
                impaired_dedicated_error
            ),
            "dedicated_normal_path_standard_error_one_frame": float_summary(
                normal_dedicated_error
            ),
            "independent_frames_for_five_sigma_gap": frames_for_five_sigma,
            "warning": (
                "coded estimates include shot noise from every path; this is suitable "
                "for persistent severe faults before precision loss measurement"
            ),
        },
        "one_slot_cyclic_clock_slip": {
            "root_mean_square_coefficient_error": float_summary(
                math.sqrt(slip_squared_error)
            ),
            "maximum_coefficient_error": float_summary(slip_max_error),
            "warning": "orthogonality requires shared slot boundaries",
        },
        "marking_rule": (
            "alpha=(popcount(slot)-2*parity(rule_id & slot)) mod 4; "
            "bit ordering only permutes rule IDs"
        ),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
