def gaussian_walk():
    z = 0j
    n = 0

    while True:
        s2 = n.bit_count()
        u = 1j ** s2
        c = 1j * (1 - u) / (1 - 1j)
        W = 2 * z + c
        H = 4 * n + s2 % 4
        P = round(W.real), round(W.imag), H
        yield P
        z += u
        n += 1
