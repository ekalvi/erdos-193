"""Construct the Gaussian-lattice lift in the joint Cambie–Kalviainen paper."""

from functools import cache
from math import gcd

Point2D = tuple[int, int]
Point = tuple[int, int, int]

# u_n = i^s₂(n), represented as an integer vector.
UNITS: tuple[Point2D, ...] = ((1, 0), (0, 1), (-1, 0), (0, -1))
# The same four states, encoded as cyclic Gray-code corners.
CORNERS: tuple[Point2D, ...] = ((0, 0), (0, 1), (-1, 1), (-1, 0))
STATE_NAMES = ("1", "i", "−1", "−i")


def state(n: int) -> int:
    """Return α_n=s₂(n) mod 4."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    return n.bit_count() % 4


def add(a: Point2D, b: Point2D) -> Point2D:
    return a[0] + b[0], a[1] + b[1]


def multiply_one_plus_i(z: Point2D) -> Point2D:
    """Return (1+i)z in integer coordinates."""
    return z[0] - z[1], z[0] + z[1]


@cache
def Z(n: int) -> Point2D:
    """Return z_n=Σ_{r<n} i^s₂(r), using its binary recurrence."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    if n == 0:
        return 0, 0
    parent, bit = divmod(n, 2)
    z = multiply_one_plus_i(Z(parent))
    return add(z, UNITS[state(parent)]) if bit else z


def W(n: int) -> Point2D:
    """Append the direction state as a Gray-code planar tag."""
    z_x, z_y = Z(n)
    c_x, c_y = CORNERS[state(n)]
    return 2 * z_x + c_x, 2 * z_y + c_y


def height(n: int) -> int:
    """Append the same state as the low base-4 height digit."""
    return 4 * n + state(n)


def P(n: int) -> Point:
    """Return P_n=(Re w_n, Im w_n, h_n)."""
    x, y = W(n)
    return x, y, height(n)


def generate_walk(length: int) -> list[Point]:
    """Generate a prefix in one pass along the Gaussian unit-step walk."""
    if length < 0:
        raise ValueError("length cannot be negative")
    points: list[Point] = []
    z_x = z_y = 0
    for n in range(length):
        alpha = state(n)
        c_x, c_y = CORNERS[alpha]
        points.append((2 * z_x + c_x, 2 * z_y + c_y, 4 * n + alpha))
        u_x, u_y = UNITS[alpha]
        z_x, z_y = z_x + u_x, z_y + u_y
    return points


def v_2(n: int) -> int | float:
    """Return the exponent of 2 in a nonzero integer."""
    if n == 0:
        return float("inf")
    n = abs(n)
    return (n & -n).bit_length() - 1


def delta(start: Point, end: Point) -> Point:
    return tuple(b - a for a, b in zip(start, end))


def index_pairs(length: int, start: int = 0):
    for i in range(start, length):
        for j in range(i + 1, length):
            yield i, j


def verify_all_pairs_identity(points: list[Point]) -> int:
    """Check ν₂(|Δw|²)=ν₂(Δh) for every pair."""
    checks = 0
    for m, n in index_pairs(len(points)):
        dx, dy, dh = delta(points[m], points[n])
        assert v_2(dx * dx + dy * dy) == v_2(dh)
        checks += 1
    return checks


def verify_step_menu(points: list[Point]) -> int:
    """Check the small-step bounds and the fixed sixteen-vector menu."""
    menu = {delta(a, b) for a, b in zip(points, points[1:])}
    for dx, dy, dh in menu:
        assert abs(dx) <= 2 and abs(dy) <= 2 and 1 <= dh <= 7
    assert len(menu) <= 16
    return len(points) - 1


def verify_walk(points: list[Point]) -> int:
    """Check exact primitive directions from each anchor are unique."""
    checks = 0
    for i, anchor in enumerate(points):
        seen: set[Point] = set()
        for point in points[i + 1 :]:
            direction = delta(anchor, point)
            divisor = gcd(gcd(abs(direction[0]), abs(direction[1])), direction[2])
            primitive = tuple(coordinate // divisor for coordinate in direction)
            assert primitive not in seen, f"collinear chord from {anchor}: {primitive}"
            seen.add(primitive)
            checks += 1
    return checks


def run_check(label: str, verify, points: list[Point], success: str) -> bool:
    print(f"Checking {label}...")
    try:
        checks = verify(points)
    except AssertionError as error:
        print(f"FAIL {label}: {str(error).strip() or 'assertion failed'}")
        return False
    print(f"PASS {label}: {success.format(checks=checks)}")
    return True


def demonstrate(length: int) -> None:
    """Construct and finitely check a prefix, printing a compact report."""
    if length < 1:
        raise ValueError("length must be positive")
    print(f"Constructing the Gaussian lift with {length} points.")
    print("The direction state is encoded in both the planar tag and the height.")
    walk = generate_walk(length)
    print(f"Constructed indices 0 through {length - 1}.")
    print("First eight lifted points:")
    print("  n  u_n   z_n       corner    P_n")
    for n in range(min(8, length)):
        print(f"  {n:<2} {STATE_NAMES[state(n)]:^4}  {Z(n)!s:<9} {CORNERS[state(n)]!s:<9} {walk[n]}")
    checks = (
        ("all-pairs identity", verify_all_pairs_identity, "{checks} pairs verified"),
        ("sixteen-step menu", verify_step_menu, "{checks} steps verified"),
        ("collinearity search", verify_walk, "{checks} anchored directions unique"),
    )
    failures = sum(not run_check(label, verify, walk, success) for label, verify, success in checks)
    print("All finite checks passed." if not failures else f"Finished with {failures} failed checks.")
    print("Finite checks illustrate the construction; they do not prove infinity.")


if __name__ == "__main__":
    demonstrate(60)
