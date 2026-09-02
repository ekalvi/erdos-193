# Finite physics diagnostics for the Gaussian Erdős 193 walk

> **Status:** computational observations on a finite prefix, not a physical model and not
> part of the unconditional proof. “Spectrum” below means the temporal Fourier spectrum
> of planar unit steps, not a spatial material diffraction measurement.

Parameters: `{'points': 131072, 'max_correlation_lag': 256, 'edge_gap_limit': 16, 'triple_samples': 1000000, 'seed': 193}`

## Main observations

- Planar ensemble MSD log-log exponent: **1.063912**.
- Lifted 3D MSD exponent: **1.977478** (height is ballistic).
- Normalized temporal spectral entropy: **0.651986**
  (0 is one Fourier bin; 1 is flat power over all bins).
- Closest checked nonconsecutive vertices: distance **6.16441**
  at indices `[28, 30]`.
- Closest checked nonadjacent edges: distance **2.44949**
  for edges starting at `[6, 8]`.
- Smallest sampled triple angle: **8.91843903e-05°**
  at indices `[8986, 99423, 99466]` among 1,000,000 sampled triples.

## Selected step autocorrelations

`C(l)=mean(u[n+l] conjugate(u[n]))`.

| lag | Re C | Im C | |C| |
|---:|---:|---:|---:|
| 0 | 1 | 0 | 1 |
| 1 | 0.199998474 | 0.400004578 | 0.447217008 |
| 2 | 0.2 | 0.4 | 0.447213595 |
| 3 | 0 | -7.62956916e-06 | 7.62956916e-06 |
| 4 | 0.200018311 | 0.400006104 | 0.447227244 |
| 8 | 0.200024416 | 0.400048831 | 0.44726819 |
| 16 | 0.199975583 | 0.400073251 | 0.447268197 |
| 32 | 0.2 | 0.4 | 0.447213595 |
| 64 | 0.200293112 | 0.400097704 | 0.447432122 |
| 128 | 0.200391007 | 0.400782014 | 0.448087913 |
| 256 | 0.199608611 | 0.401174168 | 0.448089624 |

## Strongest temporal Fourier bins

| bin | cycles/step | power fraction |
|---:|---:|---:|
| 8721 | 0.0665359497 | 0.00287134998 |
| 8465 | 0.0645828247 | 0.00285433157 |
| 8737 | 0.06665802 | 0.00282170254 |
| 16913 | 0.12903595 | 0.00273961658 |
| 16929 | 0.12915802 | 0.0027151533 |
| 17441 | 0.13306427 | 0.0026868629 |
| 4369 | 0.0333328247 | 0.00256762557 |
| 16657 | 0.127082825 | 0.00238071819 |
| 17425 | 0.1329422 | 0.00237313601 |
| 17473 | 0.133308411 | 0.00231037399 |

## Angular and reciprocal-space diagnostics

- **17.111%** of sampled triples have angle below about `0.0573°`
  (`sin(theta)<1e-3`); **90.152%** are below about `0.573°`.
  Thus exact non-collinearity provides very little angular clearance.
- Finite-prefix scans use `S(q)=|sum_j exp(-i q·P_j)|^2/N` along x, y,
  height, and (1,1,1). The forward peak is separated from nonzero bins.
- Coordinate-sum parity counts are `[131072, 0]`: every tested point has
  `x+y+h` even. Consequently the (1,1,1) scan has a fully coherent
  `q=pi` peak. This is the exact parity sublattice selection rule, not
  evidence by itself for novel long-range order.

## Interpretation limits

Exact non-collinearity does not imply robust angular separation: sampled triples can
approach a line. Proximity minima apply to the reported finite prefix; the JSON flags
whether the monotone-height bound makes each minimum prefix-wide. Temporal Fourier
peaks characterize the symbolic time series, while the spatial scans are finite and
commensurate; neither establishes an infinite-volume diffraction measure or a physical
response without a specified coupling. See the JSON artifact for complete tables.
