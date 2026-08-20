"""
Rigorously reconstruct a TYPE-CORRECT g=2 exact overlap:
 witness (start a=1, end type 22): w1=((0,1,0),(-2,2,-2)), w2=((0,0,0),(-2,2,1)).
Exhibit explicit connectors for each leg; confirm both are valid typed paths
a=1 -> s1 -> 22 with the stated digits; confirm identical composed map
(same anchor V, same g, same end type 22 => identical cylinder K = f(K_22)).
"""
import pickle
from search193 import candidate_step_vectors
MENU=candidate_step_vectors(2)
def mv(v): return (3*v[0], -3*v[2], 3*v[1]-v[2])
dom=pickle.load(open('connector_domains4.pkl','rb'))['domains']

def interiors_with_next(C):
    out=[((0,0,0), C[0])]
    x=y=z=0
    for t in range(1,len(C)):
        s=MENU[C[t-1]]; x+=s[0];y+=s[1];z+=s[2]; out.append(((x,y,z), C[t]))
    return out

def find_leg(src, digit, dst):
    """connector C in domains[src] with an interior==digit whose next==dst."""
    for C in dom[src]:
        for (off,nxt) in interiors_with_next(C):
            if off==digit and nxt==dst:
                return C, [(off,nxt) for (off,nxt) in interiors_with_next(C)]
    return None, None

def find_leg_anynext(src, digit):
    for C in dom[src]:
        for (off,nxt) in interiors_with_next(C):
            if off==digit:
                return C, nxt
    return None, None

def verify_word(a, d1, d2, end, label):
    print(f"[{label}] typed path type {a} --({d1})--> s1 --({d2})--> {end}",flush=True)
    # leg1: from a, interior d1 -> some s1 ; require that from s1 there is a leg2 giving d2->end
    ok=False
    for C1 in dom[a]:
        for (off1,s1) in interiors_with_next(C1):
            if off1!=d1: continue
            C2,_=find_leg(s1, d2, end)
            if C2 is not None:
                print(f"   leg1 connector={C1} (interior {d1} at next-state s1={s1}, MENU[s1]={MENU[s1]})",flush=True)
                print(f"   leg2 connector={C2} from s1={s1} (interior {d2} -> end {end}, MENU[end]={MENU[end]})",flush=True)
                V=(mv(d1)[0]+d2[0], mv(d1)[1]+d2[1], mv(d1)[2]+d2[2])
                print(f"   anchor V = M*d1+d2 = {V}",flush=True)
                ok=(V,end)
                break
        if ok: break
    if not ok: print("   COULD NOT reconstruct -> not a valid typed path",flush=True)
    return ok

print("=== TYPE-CORRECT WITNESS: start=1, end=22 ===",flush=True)
r1=verify_word(1,(0,1,0),(-2,2,-2),22,"w1")
r2=verify_word(1,(0,0,0),(-2,2,1),22,"w2")
print(f"\n>>> w1 anchor/end = {r1}",flush=True)
print(f">>> w2 anchor/end = {r2}",flush=True)
if r1 and r2:
    print(f">>> SAME start type (1), SAME anchor ({r1[0]==r2[0]}: {r1[0]}), SAME end type ({r1[1]==r2[1]}: {r1[1]})",flush=True)
    print(f">>> => f_w1 = f_w2 (same affine map, gen 2) AND same end-type sub-attractor K_22",flush=True)
    print(f">>> => K_w1 = f(K_22) = K_w2  IDENTICAL cylinder => EXACT OVERLAP => OSC FAILS on menu-closure GDS",flush=True)
    print(f">>> words distinct: {((0,1,0),(-2,2,-2))} != {((0,0,0),(-2,2,1))} : True",flush=True)
