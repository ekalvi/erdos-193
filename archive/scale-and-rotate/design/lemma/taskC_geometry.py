"""
TASK C -- CONTRACTION FROM M-GEOMETRY.
Pure-python (no numpy). Computes:
 (1) Singular values of M_BAL3 (Jacobi eigensolver on M^T M).
 (2) M^{-1} image of a Chebyshev-R box: per-axis extent (L1 row sums of M^{-1})
     and the singular-direction ellipsoid semi-axes (= R/sigma_i(M)).
 (3) Derived alpha (dilated-old contribution as fraction of c10) under a
     local-1D density model, plus the worst-direction risk.
Outputs JSON to stdout.
"""
import json, math

M = [[3,0,0],[0,0,-3],[0,3,-1]]   # M_BAL3, det 27

def matmul(A,B):
    n=len(A); m=len(B[0]); k=len(B)
    return [[sum(A[i][t]*B[t][j] for t in range(k)) for j in range(m)] for i in range(n)]
def transpose(A):
    return [[A[j][i] for j in range(len(A))] for i in range(len(A[0]))]
def det3(A):
    return (A[0][0]*(A[1][1]*A[2][2]-A[1][2]*A[2][1])
           -A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0])
           +A[0][2]*(A[1][0]*A[2][1]-A[1][1]*A[2][0]))
def inv3(A):
    d=det3(A)
    c=[[ (A[1][1]*A[2][2]-A[1][2]*A[2][1]), -(A[0][1]*A[2][2]-A[0][2]*A[2][1]),  (A[0][1]*A[1][2]-A[0][2]*A[1][1])],
       [-(A[1][0]*A[2][2]-A[1][2]*A[2][0]),  (A[0][0]*A[2][2]-A[0][2]*A[2][0]), -(A[0][0]*A[1][2]-A[0][2]*A[1][0])],
       [ (A[1][0]*A[2][1]-A[1][1]*A[2][0]), -(A[0][0]*A[2][1]-A[0][1]*A[2][0]),  (A[0][0]*A[1][1]-A[0][1]*A[1][0])]]
    return [[c[i][j]/d for j in range(3)] for i in range(3)]

def jacobi_eig(S, iters=200):
    """Symmetric 3x3 eigen: returns (eigenvalues, eigenvectors-as-columns of V)."""
    n=len(S)
    A=[row[:] for row in S]
    V=[[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(iters):
        # find largest off-diagonal
        p,q,mx=0,1,0.0
        for i in range(n):
            for j in range(i+1,n):
                if abs(A[i][j])>mx: mx=abs(A[i][j]); p,q=i,j
        if mx<1e-18: break
        app=A[p][p]; aqq=A[q][q]; apq=A[p][q]
        phi=0.5*math.atan2(2*apq, aqq-app)
        c=math.cos(phi); s=math.sin(phi)
        for k in range(n):
            akp=A[k][p]; akq=A[k][q]
            A[k][p]=c*akp - s*akq
            A[k][q]=s*akp + c*akq
        for k in range(n):
            akp=A[p][k]; akq=A[q][k]
            A[p][k]=c*akp - s*akq
            A[q][k]=s*akp + c*akq
        for k in range(n):
            vkp=V[k][p]; vkq=V[k][q]
            V[k][p]=c*vkp - s*vkq
            V[k][q]=s*vkp + c*vkq
    eig=[A[i][i] for i in range(n)]
    return eig, V

# ---- (1) singular values ----
Mt=transpose(M)
MtM=matmul(Mt,M)
eig, V = jacobi_eig(MtM)
# sigma = sqrt(eigenvalue of M^T M)
sv=sorted((math.sqrt(max(e,0.0)) for e in eig), reverse=True)
sig_max, sig_mid, sig_min = sv

# eigenvalues of M (moduli) sanity: char poly. moduli all 3 per spec.
# right singular vectors (columns of V) sorted by sigma:
order=sorted(range(3), key=lambda i: -eig[i])
right_vecs=[[V[r][i] for r in range(3)] for i in order]  # each entry = a right singular vector

Minv=inv3(M)
# ---- (2) M^{-1} maps Cheb-R box ----
R=10.0
# per-axis Chebyshev extent of the pullback parallelepiped:
#   half-width along axis i = R * sum_j |Minv[i][j]|  (L1 norm of row i)
row_l1=[sum(abs(Minv[i][j]) for j in range(3)) for i in range(3)]
cheb_halfwidth=[R*r for r in row_l1]         # bounding Cheb box half-widths per axis
Minf=max(row_l1)                              # ||M^{-1}||_inf  (inf operator norm)
# singular-value view: image ellipsoid semi-axes of M^{-1} applied to L2-ball radius R
# = R * singular values of M^{-1} = R / sigma_i(M)
ell_semi=[R/s for s in sv]                     # [R/sig_max, R/sig_mid, R/sig_min]

# ---- (3) derived alpha ----
# Local-1D density model:
# Anchors at level k+1 are M*(level-k points). An anchor is within Cheb-R of point p
# iff the corresponding level-k point q lies in the pullback region B=M^{-1}(Cheb-R box
# centred at M^{-1}p). Along the (locally 1D) walk with linear density rho, the count of
# captured level-k points ~ rho * (arc-length of B along the walk tangent).
# The arc-length the pullback pulls in scales like the extent of B along that tangent.
#
# WORST DIRECTION: if the walk tangent aligns with the least-contracted direction of M^{-1}
# (= right singular vector of M for sigma_min), B stretches by 1/sigma_min. Then the pullback
# captures ~ (R/sigma_min) worth of arc length vs the (R) the direct Cheb-R ball would.
# => alpha_worst  = (1/sigma_min) / (dilation the *new* level lives at).
#
# But the level-(k+1) walk itself has been dilated by M (~x3) relative to level-k spacing.
# The natural comparison: a Cheb-R ball at level k+1 pulls back (via M^{-1}) to a region of
# Cheb-extent ~ R*||M^{-1}||_inf < R (since M^{-1} contracts). The dilated-old crowding is
# then c_k measured over that shrunken region. Under 1D scaling:
#     dilated_old(R) ~ c_k(R) * (effective pullback extent / R)
# giving the contraction factor:
alpha_iso   = Minf                 # isotropic / Chebyshev-operator estimate (avg-ish)
alpha_worst = 1.0/sig_min          # worst-direction: tangent || least-contracted axis
alpha_best  = 1.0/sig_max          # best-direction:  tangent || most-contracted axis
# A "typical 1D" alpha: geometric mean of the two axis contractions weighting is subtle;
# report the plane-average of 1/sigma over the two non-radial directions and the L1-row view.
alpha_geo   = (1.0/sig_max * 1.0/sig_min)**0.5

out={
 "M": M,
 "det": det3(M),
 "frobenius_sq": sum(M[i][j]**2 for i in range(3) for j in range(3)),
 "singular_values": {"sigma_max":sig_max,"sigma_mid":sig_mid,"sigma_min":sig_min},
 "sv_product": sv[0]*sv[1]*sv[2],
 "sv_sq_sum": sum(s*s for s in sv),
 "eig_moduli_note":"all eigenvalue moduli = 3 (det 27, rotation arccos(-1/6)); sigmas spread",
 "right_singular_vectors_of_M(cols by sigma desc)": right_vecs,
 "Minv": Minv,
 "Minv_inf_opnorm": Minf,
 "pullback_box_R": R,
 "pullback_cheb_halfwidth_per_axis": cheb_halfwidth,
 "pullback_ellipsoid_semiaxes_R_over_sigma": ell_semi,
 "alpha_isotropic(||Minv||_inf)": alpha_iso,
 "alpha_worst_direction(1/sigma_min)": alpha_worst,
 "alpha_best_direction(1/sigma_max)": alpha_best,
 "alpha_geo_mean": alpha_geo,
 "worst_direction_risk": (
    "sigma_min=%.4f < 3 => along its right-singular direction M dilates by only %.4f, "
    "so M^{-1} contracts by only 1/%.4f=%.4f there. A walk segment aligned with this "
    "direction contracts the dilated-old term by ~%.3f instead of the nominal 1/3=0.333. "
    "Since %.4f < 1 the term still contracts, so alpha stays below 1 in EVERY direction "
    "(max is 1/sigma_min=%.4f). No direction makes alpha>=1."
    % (sig_min, sig_min, sig_min, 1.0/sig_min, alpha_worst, alpha_worst, alpha_worst)),
}
print(json.dumps(out, indent=2))
