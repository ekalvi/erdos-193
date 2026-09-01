def gaussian_walk(n):
    z = 0j
    points = []

    for k in range(n):
        s2 = k.bit_count()
        u = 1j**s2
        c = 1j * (1 - u) / (1 - 1j)
        W = 2 * z + c
        H = 4 * k + s2 % 4
        P = int(W.real), int(W.imag), H
        points.append(P)
        z += u

    return points
