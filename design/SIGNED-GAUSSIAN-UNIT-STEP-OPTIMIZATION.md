# Six-coordinate unit-step walk from the signed Gaussian family

## Result

There is an infinite standard-basis walk in \(\mathbb N^6\) with no three collinear vertices. Consequently, for Shallit's minimum alphabet/dimension,

\[
4\le k_{\min}\le 6.
\]

This is a derived theorem about the unit-step variant, not a stronger solution of Erdős Problem 193 in dimension three.

## Geometric context

The planar rules and one tagged lift are rendered in `results/unit-step-g85-g170-context.svg`. Regenerate the SVG, PNG, and paper-ready PDF with:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run --with matplotlib python design/render_unit_step_context.py
```

The planar images explain which transitions survive, while the compressed-height lift shows the three-dimensional linear image used in the proof. They are finite illustrations, not premises of the infinite theorem.

## Alternating signed Gaussian rule

Write \(b_j(n)\) for bit \(j\) of \(n\), and define

\[
\sigma(n)=\sum_{j\ge0}(-1)^j b_j(n)\pmod4,
\qquad
u_n=i^{\sigma(n)},
\qquad
z_n=\sum_{r<n}u_r.
\]

Use Cambie's offsets

\[
(c_0,c_1,c_2,c_3)=(0,-1,-1+i,-i)
\]

and the tagged lift

\[
w_n=2z_n+c_{\sigma(n)},\qquad h_n=4n+\sigma(n),
\qquad Q_n=(\Re w_n,\Im w_n,h_n).
\]

The signed Gaussian halving argument gives, whenever two endpoint states agree,

\[
\nu_2(|z_n-z_m|^2)=\nu_2(n-m).
\]

Indeed, after removing one common terminal bit, the chord is multiplied by either \(1+i\) or \(1-i\); both have squared norm 2. Repeating until the index difference is odd proves the identity exactly as in the constant-sign construction. The parity pattern of the four offsets then gives for every \(m<n\)

\[
\nu_2(|w_n-w_m|^2)=\nu_2(h_n-h_m).
\]

The usual equal-slope valuation contradiction proves that the points \(Q_n\) contain no collinear triple.

## Why only six distinct steps occur

If \(n\) has \(k\) trailing 1 bits, incrementing \(n\) changes the state by

\[
\delta_k=(-1)^k-\sum_{j<k}(-1)^j\pmod4.
\]

Thus

\[
\delta_k=1\quad(k\text{ even}),
\qquad
\delta_k=2\quad(k\text{ odd}).
\]

Only transitions \(s=r+1\) and \(s=r+2\pmod4\) can occur. Their lifted steps

\[
v_{r,s}=(2i^r+c_s-c_r,\;4+s-r)
\]

are the following six distinct vectors:

| vector | state pair(s) |
|---|---|
| \((1,0,5)\) | \((0,1)\) |
| \((0,3,5)\) | \((1,2)\) |
| \((-1,-2,5)\) | \((2,3)\) |
| \((0,-1,1)\) | \((3,0)\) |
| \((1,1,6)\) | \((0,2),(1,3)\) |
| \((-1,-1,2)\) | \((2,0),(3,1)\) |

All eight state pairs occur (the least witness indices are respectively \(0,4,10,2,9,1,5,21\) when ordered as above before merging), although only the upper bound of six is needed.

List the six vectors as \(v_1,\ldots,v_6\). Replace each step \(v_j\) by the standard basis vector \(e_j\in\mathbb N^6\). The linear map \(T(e_j)=v_j\) sends the resulting walk back to \((Q_n)\). A collinear triple in the basis walk would therefore produce a collinear triple in \((Q_n)\), which is impossible. Coordinate sums equal the index, so the basis-walk vertices are distinct.

## Optimality inside this tag scheme

This six-vector count is minimal among all signed rules with this four-state valuation tag mechanism, even if the integer representatives of the four offset parity classes are changed.

Let \(D\) be the set of possible changes \(\delta_k\). Since \(\delta_0=\pm1\) and each successive \(\delta_k\) moves by \(\pm1\) modulo 4, \(|D|\ge2\). For each change that occurs, all four starting states occur: above the trailing-ones suffix, select zero through three positions carrying the same sign to realize every residue modulo 4. The two-value possibilities are the adjacent pairs \(\{0,1\}\), \(\{1,2\}\), \(\{2,3\}\), and \(\{0,3\}\).

For \(D=\{1,2\}\), separate vectors by their height coordinates. There is one unavoidable height-1 vector, three height-5 vectors, two height-6 vectors, and two height-2 vectors. The two height-6 vectors coincide exactly when the two height-2 vectors coincide. Under that equality, the three height-5 vectors are pairwise distinct: adjacent candidates have different parity vectors, while equality of the first and third contradicts the common size-two collision equation. Hence at least

\[
1+3+1+1=6
\]

vectors remain. Without the size-two collision there are already at least six. The \(D=\{2,3\}\) case is symmetric. For \(D=\{0,1\}\) or \(\{0,3\}\), zero-change alone contributes the four distinct vectors \((2i^r,4)\), and the nonzero change contributes vectors in two further height classes, again giving at least six.

If \(|D|\ge3\), the distinct integer height classes already force six vectors when \(0\notin D\). When \(0\in D\), its four distinct height-4 vectors and the other changes force still more. Therefore no signed rule in this scheme can produce a four- or five-coordinate construction.

## Exact audit

Run:

```bash
python3 design/signed_gaussian_unit_step_audit.py
```

The calculation determines the complete transition-change orbit algebraically over four sign periods; it does not extrapolate from a finite walk prefix. For all 256 displayed period-eight rules it finds:

- 226 rules with 14 distinct steps;
- 28 rules with 10 distinct steps;
- 2 rules with 6 distinct steps;
- minimizers \(g_{85}=+-+-+-+-\) and \(g_{170}=-+-+-+-+\).

Machine-readable output is written atomically to `results/signed-gaussian-unit-step-audit.json`. Larger runs stream their two passes, append timestamped progress and ETA records under `logs/`, checkpoint at configurable intervals, and automatically resume only when the period, offsets, schema, and code identity match.

An exact run over all 65,536 period-16 words also has minimum six. Its only minimizers are `+-+-+-+-+-+-+-+-` and `-+-+-+-+-+-+-+-+`, the same two primitive period-two rules written with a longer period. Thus period 16 introduces no improvement; periods beyond 16 have not been exhaustively enumerated, while the structural lower bound above rules out five dimensions throughout this particular signed four-state tag scheme.
