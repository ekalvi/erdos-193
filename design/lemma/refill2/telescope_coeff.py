"""
TASK 8 CRUX ADJUDICATION — telescoped closing coefficient of the CHARGE route.

Crux:  b_k(rho) <= g * a_k(q, rho+4) = g * c_{k-1}(M^-1 q, (4/9)(rho+4)).

Birth-telescoping gives the crowding law c_k(.,r) <= E*S*r + 1 ASSUMING the refill
lemma b_j <= E*r, with S = sum_{j>=0} ||M^-j||_inf.  Feed that (induction hyp) back
into the charge to test self-consistency of b_k <= E*rho:

   b_k(rho) <= g*[ E*S*(4/9)(rho+4) + 1 ]   =>  slope = g*S*(4/9)*E.
   Self-consistent (slope <= E)  <=>  g*S*(4/9) <= 1.
"""
from fractions import Fraction as F
M=[[3,0,0],[0,0,-3],[0,3,-1]]
def matmul(A,B): return [[sum(A[i][t]*B[t][j] for t in range(3)) for j in range(3)] for i in range(3)]
def inv3(m):
    m=[[F(x) for x in r] for r in m]; a,b,c=m[0]; d,e,f=m[1]; g,h,i=m[2]
    det=a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
    adj=[[(e*i-f*h),-(b*i-c*h),(b*f-c*e)],[-(d*i-f*g),(a*i-c*g),-(a*f-c*d)],[(d*h-e*g),-(a*h-b*g),(a*e-b*d)]]
    return [[adj[r][col]/det for col in range(3)] for r in range(3)]
def infnorm(A): return max(sum(abs(x) for x in r) for r in A)
Minv=inv3(M); alpha=F(4,9)
P=[[F(r==c) for c in range(3)] for r in range(3)]; S=F(0)
for j in range(40): S+=infnorm(P); P=matmul(P,Minv)
print("S =",float(S),"  alpha=4/9=",float(alpha))
for g in (1,3,4):
    print(f"g={g}: telescoped charge coeff g*S*(4/9) = {float(g*S*alpha):.4f}  closes? {float(g*S*alpha)<1}")
print("closing threshold g <", float(1/(S*alpha)))
print("naive pre-telescope (4/9)(1+g), g=3:",float(alpha*4),"  g=4:",float(alpha*5))
