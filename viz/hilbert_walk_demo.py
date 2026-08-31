"""Construct the Hilbert lift resolving Erdős Problem 193."""

Point2D = tuple[int, int]
Point = tuple[int, int, int]


# The Hilbert child corners c_q in cyclic Gray-code order. The alternative
# construction later reuses these same four corners as terminal-state tags.
c: tuple[Point2D, ...] = (
    (0, 0),
    (0, 1),
    (1, 1),
    (1, 0),
)


class K:
    """Base class for the four possible Hilbert decoder states."""

    symbol: str

    def __str__(self) -> str:
        return self.symbol


class Identity(K):
    symbol = "I"

    def __call__(self, x: int, y: int) -> Point2D:
        return x, y


class Swap(K):
    symbol = "S"

    def __call__(self, x: int, y: int) -> Point2D:
        return y, x


class Turn(K):
    symbol = "T"

    def __call__(self, x: int, y: int) -> Point2D:
        return 1 - y, 1 - x


class Complement(K):
    symbol = "C"

    def __call__(self, x: int, y: int) -> Point2D:
        return 1 - x, 1 - y


I = Identity()
S = Swap()
T = Turn()
C = Complement()

R: tuple[K, ...] = (S, I, I, T)


def compose(g: K, h: K) -> K:
    """Compose two decoder states as g ∘ h, with h acting first."""
    for transformation in (I, S, T, C):
        if all(transformation(*point) == g(*h(*point)) for point in c):
            return transformation

    raise ValueError("composition is not in K")


def decode(w: str) -> tuple[Point2D, K]:
    """Decode a base-4 word into its Hilbert point and terminal state."""
    if not w or any(digit not in "0123" for digit in w):
        raise ValueError(f"invalid base-4 word: {w!r}")

    g = I
    x, y = "", ""
    for digit in w:
        q = int(digit)
        x_bit, y_bit = g(*c[q])
        x, y = x + str(x_bit), y + str(y_bit)
        g = compose(g, R[q])

    return (int(x, 2), int(y, 2)), g


def to_base4(n: int) -> str:
    """Write the nonnegative index n as a base-4 word."""
    if n < 0:
        raise ValueError("n must be nonnegative")

    digits = ""
    while n:
        n, digit = divmod(n, 4)
        digits = str(digit) + digits

    return digits or "0"


def H(n: int) -> tuple[Point2D, K]:
    """Return the infinite Hilbert-path point H(n) and terminal state σ(n)."""
    w = to_base4(n)
    if len(w) % 2:
        w = "0" + w
    return decode(w)


def σ(n: int) -> K:
    """Return the terminal state σ(n)."""
    return H(n)[1]


def v_2(n: int) -> int | float:
    """Return the largest exponent e for which 2**e divides n."""
    if n == 0:
        return float("inf")

    n = abs(n)
    exponent = 0
    while n % 2 == 0:
        n //= 2
        exponent += 1
    return exponent


# Give the four terminal states cyclic labels used in both coordinate encodings.
def λ(state: K) -> int:
    """Give a terminal state its cyclic label I=0, S=1, C=2, T=3."""
    return {I: 0, S: 1, C: 2, T: 3}[state]


def state_corner(state: K) -> Point2D:
    """Return the Gray-code corner matching the state's cyclic label."""
    return c[λ(state)]


def G(n: int) -> Point2D:
    """Encode the terminal state in the low bits of H(n)."""
    (x, y), state = H(n)
    corner_x, corner_y = state_corner(state)
    return 2 * x + corner_x, 2 * y + corner_y


def z(n: int) -> int:
    """Encode the terminal state in the height modulo four."""
    return 4 * n + λ(σ(n))


def P(n: int) -> Point:
    """Return the Hilbert lift P_n=(G(n), z(n))."""
    x, y = G(n)
    return x, y, z(n)


def generate_walk(length: int) -> list[Point]:
    """Return the first length points; no indices are discarded."""
    if length < 0:
        raise ValueError("length cannot be negative")
    return [P(n) for n in range(length)]


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


def verify_all_pairs_identity(points: list[Point]) -> int:
    """Check ν₂(||G(n)-G(m)||²)=ν₂(z(n)-z(m)) for every pair."""
    checks = 0
    for m, n in index_pairs(len(points)):
        x_m, y_m, z_m = points[m]
        x_n, y_n, z_n = points[n]
        dx, dy = x_n - x_m, y_n - y_m
        assert v_2(dx * dx + dy * dy) == v_2(z_n - z_m)
        checks += 1
    return checks


def verify_step_bounds(points: list[Point]) -> int:
    """Check that every step lies in |x|,|y|≤3 and 1≤z≤7."""
    checks = 0
    for start, end in zip(points, points[1:]):
        dx, dy, dz = Δ(start, end)
        assert abs(dx) <= 3 and abs(dy) <= 3 and 1 <= dz <= 7
        checks += 1
    return checks


def verify_walk(points: list[Point]) -> int:
    """Verify every triple and return the number of collinearity checks."""
    checks = 0
    for i in range(len(points)):
        for j, k in index_pairs(len(points), i + 1):
            a, b, c_point = points[i], points[j], points[k]
            u = Δ(a, b)
            v = Δ(a, c_point)
            collinear = dot(u, v) ** 2 == dot(u, u) * dot(v, v)
            assert not collinear, f"collinear walk points: {a}, {b}, {c_point}"
            checks += 1
    return checks


def run_check(label: str, verify, points: list[Point], success: str) -> bool:
    """Run one assertion-based check and report its result without a traceback."""
    print(f"Checking {label}...")
    try:
        checks = verify(points)
    except AssertionError as error:
        detail = str(error).strip() or "assertion failed"
        print(f"FAIL {label}: {detail}")
        return False

    print(f"PASS {label}: {success.format(checks=checks)}")
    return True


def demonstrate(length: int) -> None:
    """Construct and finitely check a prefix, printing a compact report."""
    if length < 1:
        raise ValueError("length must be positive")

    print(f"Constructing the Hilbert lift with {length} points.")
    print("Every index is used; σ(n) is encoded in the planar coordinates and height.")
    walk = generate_walk(length)
    print(f"Constructed {len(walk)} candidate points from indices 0 through {length - 1}.")
    print(f"First point: {walk[0]}")
    print(f"Last point:  {walk[-1]}")
    print("First eight lifted points:")
    print("  n  σ(n)   H(n)    corner   P(n)")
    for n in range(min(8, length)):
        h_n, state = H(n)
        print(f"  {n:<2} {state!s:^4}  {h_n!s:<8} {state_corner(state)!s:<8} {walk[n]}")

    checks = (
        (
            "all-pairs identity",
            verify_all_pairs_identity,
            "{checks} pairs verified",
        ),
        ("finite step bounds", verify_step_bounds, "{checks} steps verified"),
        (
            "collinearity search",
            verify_walk,
            "no collinear triples among {checks} checked",
        ),
    )
    failures = sum(
        not run_check(label, verify, walk, success)
        for label, verify, success in checks
    )

    if failures:
        print(f"Finished with {failures} failed check{'s' if failures != 1 else ''}.")
    else:
        print("All finite checks passed.")
    print("Finite checks illustrate the construction; they do not prove infinity.")


if __name__ == "__main__":
    demonstrate(60)
