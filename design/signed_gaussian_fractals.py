#!/usr/bin/env python3
"""Explore signed binary-digit Gaussian walks and render an SVG gallery.

For a periodic word of signs eps_j in {+1,-1}, define

    state(n) = sum_j eps_j bit_j(n) (mod 4),
    u_n      = i**state(n),
    z_n      = sum_{k<n} u_k.

The original Gaussian walk is the period-one word '+'.  This script checks,
on a requested finite prefix, the same-state source law and the all-pairs law
for the tagged lift G_n = 2*z_n + corner(state(n)),
h_n = 4*n + state(n).  Finite checks are evidence, not an infinite proof.
"""

from __future__ import annotations

import argparse
from pathlib import Path

DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
CORNERS = ((0, 0), (0, 1), (-1, 1), (-1, 0))
# The complete period-eight family in binary order, with + before -:
# g0 = ++++++++ and g255 = --------.
PERIOD_EIGHT_PATTERNS = tuple(
    "".join("-" if mask & (1 << (7 - place)) else "+" for place in range(8))
    for mask in range(256)
)
DEFAULT_PATTERNS = PERIOD_EIGHT_PATTERNS
HILBERT_CORNERS = "c=(00,01,11,10)"
HILBERT_TURNS = "r=(S,I,I,T)"
TAG_COLORS = ("#56b4e9", "#e69f00", "#009e73", "#cc79a7")


def v2(n: int) -> int:
    """Return the ordinary 2-adic valuation of a nonzero integer."""
    if n == 0:
        raise ValueError("v2(0) is not used")
    n = abs(n)
    return (n & -n).bit_length() - 1


def parse_pattern(pattern: str) -> tuple[int, ...]:
    if not pattern or any(c not in "+-" for c in pattern):
        raise ValueError(f"pattern must be a nonempty +/- word: {pattern!r}")
    return tuple(1 if c == "+" else -1 for c in pattern)


def state(n: int, signs: tuple[int, ...]) -> int:
    total = 0
    place = 0
    while n:
        if n & 1:
            total += signs[place % len(signs)]
        place += 1
        n >>= 1
    return total % 4


def build(pattern: str, count: int):
    signs = parse_pattern(pattern)
    states: list[int] = []
    source = [(0, 0)]
    x = y = 0
    for n in range(count):
        q = state(n, signs)
        states.append(q)
        dx, dy = DIRECTIONS[q]
        x += dx
        y += dy
        source.append((x, y))
    tagged = [
        (2 * source[n][0] + CORNERS[q][0],
         2 * source[n][1] + CORNERS[q][1],
         4 * n + q)
        for n, q in enumerate(states)
    ]
    return states, source, tagged


def verify(pattern: str, count: int) -> dict[str, int]:
    states, source, tagged = build(pattern, count)
    groups = [[] for _ in range(4)]
    for n, q in enumerate(states):
        groups[q].append(n)

    same_state_checks = 0
    for indices in groups:
        for position, m in enumerate(indices):
            xm, ym = source[m]
            for n in indices[position + 1:]:
                dx = source[n][0] - xm
                dy = source[n][1] - ym
                norm = dx * dx + dy * dy
                if norm == 0 or v2(norm) != v2(n - m):
                    raise AssertionError(
                        f"same-state law failed for {pattern!r} at ({m}, {n})"
                    )
                same_state_checks += 1

    all_pair_checks = 0
    for m in range(count):
        xm, ym, hm = tagged[m]
        for n in range(m + 1, count):
            xn, yn, hn = tagged[n]
            norm = (xn - xm) ** 2 + (yn - ym) ** 2
            if norm == 0 or v2(norm) != v2(hn - hm):
                raise AssertionError(
                    f"tagged law failed for {pattern!r} at ({m}, {n})"
                )
            all_pair_checks += 1

    menu = {
        (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        for a, b in zip(tagged, tagged[1:])
    }
    return {
        "same_state_pairs": same_state_checks,
        "tagged_pairs": all_pair_checks,
        "step_vectors": len(menu),
    }


def hilbert_source(count: int) -> tuple[list[int], list[tuple[int, int]]]:
    """Return Hilbert terminal labels and a stage matching the nested-even decoder."""
    order = 0
    while 4 ** order < count:
        order += 1
    side = 1 << order
    points = []
    states = []
    # The Klein-four group codes I,S,T,C as 0,1,2,3 under xor.  Convert to
    # cyclic tag labels I,S,C,T = 0,1,2,3 after reading the base-4 digits.
    turn_codes = (1, 0, 0, 2)
    cyclic_label = (0, 1, 3, 2)
    for distance in range(count):
        x = y = 0
        remainder = distance
        scale = 1
        while scale < side:
            rx = 1 & (remainder // 2)
            ry = 1 & (remainder ^ rx)
            if ry == 0:
                if rx == 1:
                    x = scale - 1 - x
                    y = scale - 1 - y
                x, y = y, x
            x += scale * rx
            y += scale * ry
            remainder //= 4
            scale *= 2
        points.append((x, y))
        group_code = 0
        for place in range(order - 1, -1, -1):
            digit = (distance // (4 ** place)) % 4
            group_code ^= turn_codes[digit]
        states.append(cyclic_label[group_code])
    return states, points


def signed_rule(pattern: str) -> tuple[str, str]:
    return (
        f"ε={pattern} (period {len(pattern)}); σ=Σ ε[j mod {len(pattern)}]bⱼ mod 4",
        "z(n+1)=z(n)+i^σ(n)",
    )


def svg_gallery(
    patterns: list[str], depth: int, output: Path, *, index_offset: int = 0
) -> None:
    count = 1 << depth
    hilbert_states, hilbert_points = hilbert_source(count)
    panels = [
        (
            "Hilbert base-4 automaton",
            hilbert_states,
            hilbert_points,
            f"qⱼ∈{{0,1,2,3}}; {HILBERT_CORNERS}; {HILBERT_TURNS}",
            "emit (xⱼ,yⱼ)=gⱼ(c[qⱼ]); gⱼ₊₁=gⱼ∘r[qⱼ]",
        )
    ]
    for local_index, pattern in enumerate(patterns):
        family_index = index_offset + local_index
        states, source, _ = build(pattern, count)
        rule_1, rule_2 = signed_rule(pattern)
        panels.append(
            (f"g{family_index} · Signed Gaussian · ε={pattern}",
             states, source[:count], rule_1, rule_2)
        )

    width = 1600
    columns = 4
    grid_top = 500
    grid_panel_w = width / columns
    grid_panel_h = 420
    grid_rows = (len(patterns) + columns - 1) // columns
    height = grid_top + grid_rows * grid_panel_h
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#070b14"/>',
        f'<text x="30" y="35" fill="#eef4ff" font-family="system-ui,sans-serif" font-size="23" font-weight="700">{len(panels)} valuation-walk fractals and their automaton rules</text>',
        f'<text x="1570" y="34" text-anchor="end" fill="#8fa4c1" font-family="system-ui,sans-serif" font-size="13">{count:,} source vertices each</text>',
        '<text x="30" y="58" fill="#8fa4c1" font-family="system-ui,sans-serif" font-size="13">Monochrome traces preserve the geometry; every vertex is marked by its four-color state-tag subset.</text>',
        f'<text x="20" y="483" fill="#dce8f8" font-family="system-ui,sans-serif" font-size="15" font-weight="700">Period eight · family g{index_offset} through g{index_offset + len(patterns) - 1}</text>',
        '<line x1="335" y1="478" x2="1580" y2="478" stroke="#1c2b42"/>',
    ]
    legend_x = 950
    for label, (color, corner) in enumerate(zip(TAG_COLORS, ("00", "01", "11", "10"))):
        x = legend_x + 145 * label
        chunks.extend([
            f'<circle cx="{x}" cy="57" r="6" fill="{color}"/>',
            f'<text x="{x + 11}" y="61" fill="#c6d4e7" font-family="ui-monospace,monospace" font-size="12">state {label} · tag {corner}</text>',
        ])

    for index, (title, states, source, rule_1, rule_2) in enumerate(panels):
        xs = [p[0] for p in source]
        ys = [p[1] for p in source]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        span_x = max(1, xmax - xmin)
        span_y = max(1, ymax - ymin)
        if index == 0:
            panel_x, panel_y = 0, 88
            panel_w, panel_h = width, 360
            left, top = 35, 108
            draw_w, draw_h = 320, 320
            text_x, title_y = 390, 140
            rule_1_y, rule_2_y = 174, 198
            title_size, rule_size = 20, 14
        else:
            grid_index = index - 1
            col, row = grid_index % columns, grid_index // columns
            panel_x = col * grid_panel_w
            panel_y = grid_top + row * grid_panel_h
            panel_w, panel_h = grid_panel_w, grid_panel_h
            left, top = panel_x + 27, panel_y + 82
            draw_w, draw_h = panel_w - 54, panel_h - 104
            text_x, title_y = panel_x + 25, panel_y + 31
            rule_1_y, rule_2_y = panel_y + 52, panel_y + 68
            title_size, rule_size = 15, 10.5
        scale = min(draw_w / span_x, draw_h / span_y)
        ox = left + (draw_w - span_x * scale) / 2
        oy = top + (draw_h - span_y * scale) / 2
        screen = [
            (ox + (x - xmin) * scale, oy + (ymax - y) * scale)
            for x, y in source
        ]
        points = " ".join(f"{x:.2f},{y:.2f}" for x, y in screen)
        chunks.extend([
            f'<rect x="{panel_x + 10:.1f}" y="{panel_y + 7:.1f}" width="{panel_w - 20:.1f}" height="{panel_h - 14:.1f}" rx="10" fill="#0c1322" stroke="#1c2b42"/>',
            f'<text x="{text_x:.1f}" y="{title_y:.1f}" fill="#dce8f8" font-family="ui-monospace,monospace" font-size="{title_size}" font-weight="700">{title}</text>',
            f'<text x="{text_x:.1f}" y="{rule_1_y:.1f}" fill="#9eb1ca" font-family="ui-monospace,monospace" font-size="{rule_size}">{rule_1}</text>',
            f'<text x="{text_x:.1f}" y="{rule_2_y:.1f}" fill="#9eb1ca" font-family="ui-monospace,monospace" font-size="{rule_size}">{rule_2}</text>',
            f'<polyline points="{points}" fill="none" stroke="#aec2db" stroke-width="1.05" stroke-linecap="round" stroke-linejoin="round" opacity="0.82"/>',
        ])
        if index == 0:
            chunks.extend([
                '<text x="390" y="252" fill="#dce8f8" font-family="system-ui,sans-serif" font-size="16" font-weight="700">Shared state-tag lift</text>',
                '<text x="390" y="281" fill="#9eb1ca" font-family="ui-monospace,monospace" font-size="14">G(n)=2H(n)+c[σ(n)]</text>',
                '<text x="390" y="307" fill="#9eb1ca" font-family="ui-monospace,monospace" font-size="14">h(n)=4n+λ(σ(n))</text>',
                '<text x="390" y="344" fill="#56b4e9" font-family="ui-monospace,monospace" font-size="15">ν₂(||G(n)−G(m)||²)=ν₂(|h(n)−h(m)|)</text>',
            ])
        tag_dots = [[] for _ in range(4)]
        for n, (x, y) in enumerate(screen):
            tag_dots[states[n]].append(f"M{x:.2f},{y:.2f}h0.01")
        for label, color in enumerate(TAG_COLORS):
            chunks.append(
                f'<path d="{"".join(tag_dots[label])}" fill="none" stroke="{color}" '
                'stroke-width="1.35" stroke-linecap="round" opacity="0.92"/>'
            )
        chunks.extend([
            f'<circle cx="{screen[0][0]:.2f}" cy="{screen[0][1]:.2f}" r="3.6" fill="#ffffff" stroke="#07101d" stroke-width="1"/>',
            f'<circle cx="{screen[-1][0]:.2f}" cy="{screen[-1][1]:.2f}" r="3.6" fill="#ffffff" stroke="#07101d" stroke-width="1"/>',
        ])
    chunks.append('</svg>')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(chunks) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patterns", nargs="+", default=list(DEFAULT_PATTERNS))
    parser.add_argument("--check-count", type=int, default=1024)
    parser.add_argument("--depth", type=int, default=10)
    parser.add_argument("--start", type=int, default=0, help="first family index")
    parser.add_argument("--limit", type=int, default=64, help="number of rules to render")
    parser.add_argument(
        "--output", type=Path,
        default=Path("results/valuation-walk-fractals-g000-g063.svg"),
    )
    args = parser.parse_args()
    if args.check_count < 2 or args.depth < 1:
        parser.error("--check-count must be at least 2 and --depth must be positive")
    if args.start < 0 or args.limit < 1 or args.start + args.limit > len(args.patterns):
        parser.error("--start/--limit must select rules inside --patterns")
    selected = args.patterns[args.start:args.start + args.limit]

    for pattern in selected:
        result = verify(pattern, args.check_count)
        print(
            f"{pattern:>7}: {result['same_state_pairs']:,} same-state pairs, "
            f"{result['tagged_pairs']:,} tagged pairs, "
            f"{result['step_vectors']} step vectors"
        )
    svg_gallery(selected, args.depth, args.output, index_offset=args.start)
    print(
        f"wrote {args.output} ({1 << args.depth:,} steps per panel; "
        f"g{args.start}..g{args.start + len(selected) - 1})"
    )


if __name__ == "__main__":
    main()
