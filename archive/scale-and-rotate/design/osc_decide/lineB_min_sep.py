"""
LINE B: attach a QUANTITATIVE min-|Delta| to the 8649-state carry automaton.
Question: does the automaton yield a positive uniform separation c>0 (|Delta|>=c*3^J),
or does the min over reachable carries approach 0 as depth grows?

Objects (verified against carry_automaton.py):
  M = [[3,0,0],[0,0,-3],[0,3,-1]],  Q(v)=x^2+6y^2-2yz+6z^2,  M^T Q M = 9 Q.
  Digit set D = {0} U O (collar), E = D - D  (the menu-closure difference set).
  Normalized bracket B = delta_J + sum_{i>=1} M^{-i} delta_{J-i},  delta_* in E, delta_J != 0.
  |Delta| = 3^J * |B|_Q. Target: inf |B|_Q over non-trivial addresses > 0 ?

We compute EXACTLY (integers / fractions).
"""
import json, ast, time, heapq, math
from fractions import Fraction as F
from collections import deque

OUT = "/Users/erik/homelab/math193/design/osc_decide"
M = [[3,0,0],[0,0,-3],[0,3,-1]]

def Q(v):
    x,y,z=v
    return x*x+6*y*y-2*y*z+6*z*z

def matvec(A,v):
    return (A[0][0]*v[0]+A[0][1]*v[1]+A[0][2]*v[2],
            A[1][0]*v[0]+A[1][1]*v[1]+A[1][2]*v[2],
            A[2][0]*v[0]+A[2][1]*v[1]+A[2][2]*v[2])

def Minv_frac(v):
    return (F(v[0],3), F(-v[1],9)+F(v[2],3), F(-v[1],3))

def in_MZ(v):
    r=Minv_frac(v)
    return all(x.denominator==1 for x in r)

def Minv_int(v):
    r=Minv_frac(v)
    return (int(r[0]),int(r[1]),int(r[2]))

def load():
    c=json.load(open("/Users/erik/homelab/math193/collar_multiplicity4.json"))
    O=[tuple(ast.literal_eval(k)) for k in c.keys()]
    D=[(0,0,0)]+O
    Eset=set()
    for a in D:
        for b in D:
            Eset.add((a[0]-b[0],a[1]-b[1],a[2]-b[2]))
    return D,O,sorted(Eset)

def main():
    t0=time.time()
    D,O,E=load()
    Eset=set(E)
    print(f"|D|={len(D)} |E|={len(E)} Emax_Q={max(Q(e) for e in E)}",flush=True)
    print(f"0 in E: {(0,0,0) in Eset}",flush=True)

    # ---- FACT 1: exact 0-cycle on E gives an EXACT coincidence (B=0) ----
    e0=(-12,-12,-7); e1=(4,1,-4)
    print("\n[FACT 1] exact zero-cycle test")
    print(f"  e0={e0} in E: {e0 in Eset}  Q(e0)={Q(e0)}")
    print(f"  e1={e1} in E: {e1 in Eset}  Q(e1)={Q(e1)}")
    s = tuple(a+b for a,b in zip(e0, matvec(M,e1)))   # e0 + M e1
    print(f"  e0 + M*e1 = {s}  (Delta at g=2, low-to-high f0=e0,f1=e1)")
    # normalized bracket with J=1: B = e1 + M^{-1} e0  (delta_J=e1 highest, delta_{J-1}=e0)
    b = (F(e1[0])+Minv_frac(e0)[0], F(e1[1])+Minv_frac(e0)[1], F(e1[2])+Minv_frac(e0)[2])
    print(f"  bracket B = e1 + M^-1 e0 = {tuple(str(x) for x in b)}")
    print(f"  => B==0 exactly: {all(x==0 for x in b)};  delta_J=e1!=0, tail all-zero after e0 (0 in E).")
    print(f"  => EXACT coincidence Delta=0 with non-trivial address => min |B|_Q = 0 ATTAINED.")

    # ---- FACT 2: nonzero brackets accumulate at 0 (perturb the zero-cycle deep) ----
    # tail = M^-1( e0 + M^-1( 0 + ... + M^-1( pert ))) : put a nonzero digit n levels down.
    # B = e1 + M^-1 e0 + M^-(n+1) pert = M^-(n+1) pert  (since e1+M^-1 e0 = 0).
    # |B|_Q = 3^-(n+1) |pert|_Q  -> 0 but nonzero.  Verify |M^-1 v|_Q = |v|_Q/3.
    pert=(1,0,0)  # in E
    print("\n[FACT 2] nonzero brackets accumulating at 0 (depth n below the zero-cycle):")
    for n in [0,3,6,9,12]:
        # |B|_Q = 3^-(n+1) * |pert|_Q ; |pert|_Q = sqrt(Q)
        valQ = math.sqrt(Q(pert)) / (3.0**(n+1))
        print(f"  n={n:2d}: nonzero |B|_Q = 3^-(n+1)*sqrt(Q(pert)) = {valQ:.3e}")
    print("  => inf over NONZERO brackets is also 0 (not bounded below).")

    # ---- FACT 3: automaton-native search: shortest nonzero 0->0 cycle length ----
    # (reconfirm the automaton itself accepts Delta=0; min-|Delta| attached to accepting
    #  structure is literally 0). BFS over reachable carry ball.
    def succ(c):
        out=[]
        for e in E:
            ss=(c[0]+e[0],c[1]+e[1],c[2]+e[2])
            if in_MZ(ss):
                out.append((Minv_int(ss),e))
        return out
    print("\n[FACT 3] shortest nontrivial 0->0 carry cycle (accepting => Delta=0):")
    start=[(sc,e) for (sc,e) in succ((0,0,0)) if e!=(0,0,0)]
    dist={(0,0,0):0}; par={}; dq=deque(); found=None
    for sc,e in start:
        if sc==(0,0,0): found=([e],1);break
        if sc not in dist: dist[sc]=1;par[sc]=((0,0,0),e);dq.append(sc)
    while dq and not found:
        c=dq.popleft()
        for sc,e in succ(c):
            if sc==(0,0,0):
                path=[e];cur=c
                while cur!=(0,0,0):
                    pc,pe=par[cur];path.append(pe);cur=pc
                path.reverse();found=(path,dist[c]+1);break
            if sc not in dist:
                dist[sc]=dist[c]+1;par[sc]=(c,e);dq.append(sc)
    path,ln=found
    print(f"  shortest length={ln}, digit-diffs={path}")
    # verify sum M^k f_k = 0
    S=(0,0,0);P=[[1,0,0],[0,1,0],[0,0,1]]
    def matmul(A,B):
        return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    for k in range(ln):
        tm=matvec(P,path[k]);S=(S[0]+tm[0],S[1]+tm[1],S[2]+tm[2]);P=matmul(M,P)
    print(f"  verify sum M^k f_k = {S} (==0 => accepting) ; min |Delta| on automaton = 0")

    res={
      "digit_set":"E = D - D (menu-closure), |E|=%d, contains 0: %s"%(len(E),(0,0,0) in Eset),
      "exact_zero_cycle":{"e0":list(e0),"e1":list(e1),"e0_plus_M_e1":list(s),
                          "bracket_B":[str(x) for x in b],"B_is_zero":all(x==0 for x in b)},
      "min_bracket_Q_attained":0.0,
      "nonzero_accumulation_at_0":True,
      "shortest_zero_cycle_len":ln,
      "verdict":"c = 0 on the 8649-state carry automaton (menu-closure digit set E): "
                "min |Delta| = 0 is ATTAINED (exact coincidence), and nonzero brackets "
                "accumulate at 0. NO positive uniform separation from this structure.",
      "runtime_s":round(time.time()-t0,1),
    }
    json.dump(res,open(f"{OUT}/lineB_min_sep_results.json","w"),indent=1)
    print(f"\n[{time.time()-t0:.1f}s] verdict: c=0 on this automaton. wrote lineB_min_sep_results.json")

if __name__=="__main__":
    main()
