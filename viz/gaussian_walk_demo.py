"""Construct and finitely verify the joint Cambie–Kalviainen Gaussian walk."""



def gaussian_walk(n):
    z = 0j
    points = []

    for k in range(n):
        s2 = k.bit_count()
        u = 1j ** s2
        c = 1j * (1 - u) / (1 - 1j)
        W = 2 * z + c
        H = 4 * k + s2 % 4
        P = int(W.real), int(W.imag), H
        points.append(P)
        z += u

    return points


def v2(n):
    if n == 0:
        return float("inf")
    n = abs(n)
    return (n & -n).bit_length() - 1

def gcd(a, b):
    while b:
        a, b = b, a % b
    return abs(a)


def delta(a, b):
    return tuple(y - x for x, y in zip(a, b))


def index_pairs(n):
    for i in range(n):
        for j in range(i + 1, n):
            yield i, j


def verify_all_pairs(points):
    checks = 0
    for m, n in index_pairs(len(points)):
        dx, dy, dh = delta(points[m], points[n])
        assert v2(dx * dx + dy * dy) == v2(dh)
        checks += 1
    return checks


def verify_step_menu(points):
    menu = {delta(a, b) for a, b in zip(points, points[1:])}
    for dx, dy, dh in menu:
        assert abs(dx) <= 2 and abs(dy) <= 2 and 1 <= dh <= 7
    assert len(menu) <= 16
    return len(points) - 1


def verify_no_collinear_triple(points):
    checks = 0
    for i, anchor in enumerate(points):
        directions = set()
        for point in points[i + 1:]:
            direction = delta(anchor, point)
            divisor = gcd(gcd(abs(direction[0]), abs(direction[1])), direction[2])
            primitive = tuple(coordinate // divisor for coordinate in direction)
            assert primitive not in directions
            directions.add(primitive)
            checks += 1
    return checks


def run_check(name, verify, points, message):
    print(f"Checking {name}...")
    checks = verify(points)
    print(f"PASS {name}: {message.format(checks=checks)}")


def demonstrate(n):
    points = gaussian_walk(n)
    print(f"Generated the first {n:,} points of the infinite walk.")
    print("First eight points:")
    for k, point in enumerate(points[:8]):
        print(f"  P_{k} = {point}")
    print(f"Last point: P_{n - 1} = {points[-1]}")

    run_check("all-pairs identity", verify_all_pairs, points, "{checks} pairs verified")
    run_check("small step menu", verify_step_menu, points, "{checks} steps verified")
    run_check(
        "collinearity search",
        verify_no_collinear_triple,
        points,
        "{checks} anchored directions unique",
    )
    print("All finite checks passed.")
    print("These checks inspect a prefix; the proof establishes the infinite walk.")


if __name__ == "__main__":
    demonstrate(60)
