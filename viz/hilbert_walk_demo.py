"""Construct the Hilbert-based walk from the Erdős 193 proof skeleton."""

import argparse

Point2D = tuple[int, int]
Point = tuple[int, int, int]


def to_base4(n: int) -> str:
    """Write the nonnegative index n as a base-4 word."""
    if n < 0:
        raise ValueError("n must be nonnegative")

    digits = ""
    while n:
        n, digit = divmod(n, 4)
        digits = str(digit) + digits

    return digits or "0"


class K:
    """Base class for the four possible Hilbert decoder states."""

    symbol: str

    def __call__(self, x: int, y: int) -> Point2D:
        """Apply this state to one pair of coordinate bits."""
        raise NotImplementedError

    def __str__(self) -> str:
        """Display the state using its proof symbol."""
        return self.symbol


class Identity(K):
    """Leave both coordinate bits unchanged: I(x, y) = (x, y)."""

    symbol = "I"

    def __call__(self, x: int, y: int) -> Point2D:
        return x, y


class Swap(K):
    """Swap the coordinate bits: S(x, y) = (y, x)."""

    symbol = "S"

    def __call__(self, x: int, y: int) -> Point2D:
        return y, x


class Turn(K):
    """Swap and complement the bits: T(x, y) = (1-y, 1-x)."""

    symbol = "T"

    def __call__(self, x: int, y: int) -> Point2D:
        return 1 - y, 1 - x


class Complement(K):
    """Complement both bits: C(x, y) = (1-x, 1-y)."""

    symbol = "C"

    def __call__(self, x: int, y: int) -> Point2D:
        return 1 - x, 1 - y


I = Identity()
S = Swap()
T = Turn()
C = Complement()


# The four child corners c_q in cyclic Gray-code order.
c: tuple[Point2D, ...] = (
    (0, 0),
    (0, 1),
    (1, 1),
    (1, 0),
)

# The digit-indexed transition maps r_0, r_1, r_2, r_3 from Step 1.
R: tuple[K, ...] = (S, I, I, T)


def compose(
    g: K,
    h: K,
) -> K:
    """Compose two decoder states as g ∘ h, with h acting first."""
    # The composition must be one of the same four maps in K. Compare its
    # action on every bit pair to recover that named terminal state.
    for transformation in (I, S, T, C):
        if all(transformation(*point) == g(*h(*point)) for point in c):
            return transformation

    raise ValueError("composition is not in K")


def decode(w: str) -> tuple[Point2D, K]:
    """Decode a base-4 word into its Hilbert point and terminal state."""
    if not w or any(digit not in "0123" for digit in w):
        raise ValueError(f"invalid base-4 word: {w!r}")

    # Step 1 starts in the identity state and reads the most significant
    # base-4 digit first. The strings collect the emitted binary digits.
    g = I
    x, y = "", ""

    for digit in w:
        q = int(digit)
        h = R[q]

        # Emit the corner bits using the current state, then update the state.
        # This order is essential to the decoder in the proof.
        _x, _y = g(*c[q])
        x, y = x + str(_x), y + str(_y)
        g = compose(g, h)

    # After the final digit, g is the terminal state σ(w).
    return (int(x, 2), int(y, 2)), g


def H(n: int) -> tuple[Point2D, K]:
    """Return the infinite Hilbert-path point H(n) and terminal state σ(n)."""
    w = to_base4(n)
    # Use the proof's even-length word. Adding another pair of leading zeros
    # would change neither the point nor its terminal state.
    if len(w) % 2:
        w = "0" + w
    return decode(w)


def σ(n: int) -> K:
    """Return the terminal state σ(n)."""
    return H(n)[1]


def v_2(n: int) -> int | float:
    """Count the factors of 2 in n, taking v_2(0) to be infinity."""
    if n == 0:
        return float("inf")

    n = abs(n)
    return (n & -n).bit_length() - 1


def V(u_x: int, u_y: int) -> int:
    """Return the planar two-adic invariant V(u)."""
    if u_x == 0 and u_y == 0:
        raise ValueError("V is undefined at (0, 0)")

    v_x, v_y = v_2(u_x), v_2(u_y)
    p = min(v_x, v_y)
    ε = int(v_x == v_y)
    return int(2 * p + ε)


def ρ(state: K) -> int:
    """Choose the Step 4 suffix offset that cancels terminal state σ."""
    # These are 11, 01, 31, and 03 in base 4 for I, S, T, and C.
    return {I: 5, S: 1, T: 13, C: 3}[state]


# Every selected index lies in a two-digit base-4 block of size 16.
block_size = 4**2


def n_a(a: int) -> int:
    """Select the bounded-gap index n_a in block a with terminal state I."""
    # Multiplication by 16 appends 00 in base 4, so σ(16a) = σ(a).
    return block_size * a + ρ(σ(block_size * a))


def generate_walk(length: int) -> list[Point]:
    """Return the lifted points P_a=(H(n_a), n_a) below walk length."""
    if length < 0:
        raise ValueError("length cannot be negative")

    walk = []
    a = 0
    while True:
        n = n_a(a)
        H_n, _ = H(n)
        # Step 8 lifts the planar point by using n as its third coordinate.
        walk.append((H_n[0], H_n[1], n))
        if len(walk) >= length:
            break
        a += 1
    return walk


def Δ(start: Point, end: Point) -> Point:
    """Return the vector from start to end."""
    return tuple(end_i - start_i for start_i, end_i in zip(start, end))


def dot(u: Point, v: Point) -> int:
    """Return the three-dimensional dot product of u and v."""
    return sum(u_i * v_i for u_i, v_i in zip(u, v))


def index_pairs(length: int, start: int = 0):
    """Yield every pair i < j of indices from start through length."""
    for i in range(start, length):
        for j in range(i + 1, length):
            yield i, j


def verify_pair_law(points: list[Point]) -> int:
    """Verify every pair and return the number of pair-law checks."""
    states = [σ(n) for _, _, n in points]
    checks = 0

    for i, j in index_pairs(len(points)):
        x_m, y_m, m = points[i]
        x_n, y_n, n = points[j]

        assert states[i] is states[j], "the pair law requires equal states"
        assert V(x_n - x_m, y_n - y_m) == v_2(n - m)
        checks += 1

    return checks


def verify_walk(points: list[Point]) -> int:
    """Verify every triple and return the number of collinearity checks."""
    checks = 0

    for i in range(len(points)):
        for j, k in index_pairs(len(points), i + 1):
            point_a, point_b, point_c = points[i], points[j], points[k]
            u = Δ(point_a, point_b)
            v = Δ(point_a, point_c)

            # Equality in Cauchy–Schwarz holds exactly when u and v
            # are collinear.
            collinear = dot(u, v) ** 2 == dot(u, u) * dot(v, v)
            assert (
                not collinear
            ), f"collinear walk points: {point_a}, {point_b}, {point_c}"
            checks += 1

    return checks


def demonstrate(length: int) -> None:
    """Construct and finitely check a prefix, printing a compact report."""
    if length < 1:
        raise ValueError("length must be positive")

    print(f"🧮 Attempting to construct a triple-free walk with {length} points.")
    # Construction is O(n log^2 n) with the current string-based decoder.
    walk = generate_walk(length)
    print(f"🛠️  Constructed a candidate walk of {len(walk)} points.")
    print(f"   First point: {walk[0]}")
    print(f"   Last point:  {walk[-1]}")

    print("⏱️  Verifying...")

    # This step is O(n^2): it checks every pair against the Hilbert Pair Law.
    pair_checks = verify_pair_law(walk)
    print(f"✅ Hilbert pair law verified for {pair_checks} pairs.")

    # This step is O(n^3), so it gets very slow for large walks.
    triple_checks = verify_walk(walk)
    print(f"✅ No collinear triples among {triple_checks} checked.")
    print("Finite checks illustrate the construction; they do not prove infinity.")


def parse_args() -> argparse.Namespace:
    """Parse the requested finite prefix length."""
    parser = argparse.ArgumentParser(
        description="Run the standalone handwritten Erdős 193 demonstration."
    )
    parser.add_argument(
        "--length",
        type=int,
        default=60,
        help="number of selected points to construct and check (default: 60)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # Proof and construction details: https://erdos-193.q5m.ai/proof.html
    demonstrate(parse_args().length)
