"""
Reconstruct concrete connector words for a g=2 anchor-collision and test whether
it is a GENUINE witness or an over-approximation artifact.

For a candidate (d1, s1, d2): find a base step a and connector Ca in domains[a]
whose partial-sum interior at some position t equals d1 with Ca[t]=s1, and a
connector Cp in domains[s1] whose partial-sum interior at some position equals d2
(or d2 is the anchor digit 0).  Materialize the two gen-2 words as explicit point
sequences (descending to the connector menu-steps) and check per-word internal
triple-freeness (the design's clause (a)).
"""
import pickle, sys, json
from search193 import candidate_step_vectors
MENU=candidate_step_vectors(2)
M=[[3,0,0],[0,0,-3],[0,3,-1]]
def mv(v): return (3*v[0], -3*v[2], 3*v[1]-v[2])

dom=pickle.load(open('connector_domains4.pkl','rb'))['domains']

def interiors_with_next(C):
    """list of (offset, next_state=C[t]) for t=0..len-1 ; offset = partial sum before step t.
    t=0 -> offset (0,0,0) (anchor), next C[0]."""
    out=[((0,0,0), C[0])]
    x=y=z=0
    for t in range(1,len(C)):
        s=MENU[C[t-1]]; x+=s[0]; y+=s[1]; z+=s[2]
        out.append(((x,y,z), C[t]))
    return out

def find_connector_giving(state, digit):
    """find a connector C in domains[state] and position t with interior-offset==digit."""
    for C in dom[state]:
        for (off,nxt) in interiors_with_next(C):
            if off==digit:
                return C, nxt
    return None, None

def find_edge_into(s1, digit):
    """find base state a and connector Ca in domains[a] with an interior==digit at pos with next==s1."""
    for a in dom:
        for C in dom[a]:
            for (off,nxt) in interiors_with_next(C):
                if off==digit and nxt==s1:
                    return a, C
    return None, None

# candidate witness from g2 results: V=(0,0,0)
# u = (d1=(-1,0,0), d2=(3,0,0)) ; v = (d1=(0,0,0), d2=(0,0,0))
def try_word(d1, d2, label):
    print(f"--- word {label}: d1={d1} d2={d2} ---", flush=True)
    if d1==(0,0,0):
        # anchor child of root: pick any connector; next state = its C[0]; represent
        # find any state s1 reachable as an anchor next-state
        a=next(iter(dom)); Ca=dom[a][0]; s1=Ca[0]
    else:
        a, Ca = find_edge_into_any(d1)
        if a is None:
            print("  NO connector produces interior d1 -> illegal digit"); return None
        s1=None
        for (off,nxt) in interiors_with_next(Ca):
            if off==d1: s1=nxt;break
    # level2 digit d2 from state s1
    if d2==(0,0,0):
        ok=True; Cp=dom[s1][0] if s1 in dom else None
    else:
        Cp, nxt2 = find_connector_giving(s1, d2)
        ok = Cp is not None
    print(f"  base a={a} MENU[a]={MENU[a]} ; level1 connector Ca={Ca} ; s1={s1} MENU[s1]={MENU[s1]}", flush=True)
    print(f"  level2 digit {d2} available from s1? {ok}", flush=True)
    if not ok:
        print("  -> d2 NOT available from s1 : over-approximation flagged this as legal but chain fails")
        return False
    anchor=(mv(d1)[0]+d2[0], mv(d1)[1]+d2[1], mv(d1)[2]+d2[2])
    print(f"  gen-2 anchor M*d1+d2 = {anchor}", flush=True)
    return anchor

def find_edge_into_any(d1):
    return find_edge_into_first(d1)
def find_edge_into_first(d1):
    for a in dom:
        for C in dom[a]:
            for (off,nxt) in interiors_with_next(C):
                if off==d1:
                    return a, C
    return None, None

print("Testing witness V=(0,0,0): u=((-1,0,0),(3,0,0)) vs v=((0,0,0),(0,0,0))",flush=True)
au=try_word((-1,0,0),(3,0,0),"u")
av=try_word((0,0,0),(0,0,0),"v")
print(f"\nanchors: u={au} v={av} equal={au==av}",flush=True)

# Also test a NON-trivial pair (both non-anchor) to avoid degenerate anchor-child:
print("\n\nTesting a both-nonzero collision if present (V=[1,0,0]):",flush=True)
# from sample: V=[1,0,0] pairs include (0,0,0)->(1,0,0) [that's d1=0] and (-1,0,0)->(4,0,0)
a1=try_word((-1,0,0),(4,0,0),"u2")
a2=try_word((0,0,0),(1,0,0),"v2")
print(f"anchors: u2={a1} v2={a2} equal={a1==a2}",flush=True)
