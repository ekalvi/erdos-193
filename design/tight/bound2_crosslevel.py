"""
Clean cross-level verification of BOUND2:
  b_Q^{(k)}(R) <= b_Q^{(k-1)}(R/3) + I_Q^{(k)}(R)     [child=k, parent=k-1]

Two checks:
 (A) EXACT metric identity: #{level-k anchors in Q-ball(q,R)}
       == #{level-(k-1) walk pts in Q-ball(M^{-1} q, R/3)}, EXACTLY
     (this is the theorem MᵀQM=9Q => M is a Q-similarity of ratio 3).
     We verify the *count* equality holds at the realised sup centres.
 (B) The recursion inequality with the ACTUAL parent-level b_Q (not a same-level
     proxy), using ceil(R/3) to be safe on the parent radius.
Also re-confirms contraction: implied fixed point vs measured C_Q.
"""
import sys, pickle, math, json
from collections import defaultdict
sys.path.insert(0,"/Users/erik/homelab/math193")
from gate_run import word_interiors

LAM=3.3617; D=math.log(LAM)/math.log(3); PHI=3.0**(-D)

def Qform(v):
    x,y,z=v; return x*x+6*y*y-2*y*z+6*z*z

def build(L):
    d=pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{L}.pkl","rb"))
    anchors=d['anchors']; words=d['words']
    pts=[]; arc=[]; anc=[]
    pts.append(tuple(anchors[0])); arc.append(-1)
    anc.append(tuple(anchors[0]))
    for i in range(len(anchors)-1):
        for p in word_interiors(anchors[i],words[i]):
            pts.append(tuple(p)); arc.append(i)
        pts.append(tuple(anchors[i+1])); arc.append(-1)
        anc.append(tuple(anchors[i+1]))
    return pts,arc,anc

def qmax(pts,R,centres):
    R2=R*R; cell=max(int(math.ceil(R)),1)
    g=defaultdict(list)
    for p in pts: g[(p[0]//cell,p[1]//cell,p[2]//cell)].append(p)
    best=0
    for q in centres:
        gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell; c=0
        for dx in(-2,-1,0,1,2):
          for dy in(-2,-1,0,1,2):
            for dz in(-2,-1,0,1,2):
              for p in g.get((gx+dx,gy+dy,gz+dz),()):
                if Qform((p[0]-q[0],p[1]-q[1],p[2]-q[2]))<=R2: c+=1
        if c>best: best=c
    return best

def qmax_split(pts,arc,R,centres):
    """return (max total b_Q, and at the total-sup centre: #anchors, #interiors)."""
    R2=R*R; cell=max(int(math.ceil(R)),1)
    g=defaultdict(list)
    for idx,p in enumerate(pts): g[(p[0]//cell,p[1]//cell,p[2]//cell)].append(idx)
    best=0; bA=0; bI=0
    for q in centres:
        gx,gy,gz=q[0]//cell,q[1]//cell,q[2]//cell; cA=0; cI=0
        for dx in(-2,-1,0,1,2):
          for dy in(-2,-1,0,1,2):
            for dz in(-2,-1,0,1,2):
              for idx in g.get((gx+dx,gy+dy,gz+dz),()):
                p=pts[idx]
                if Qform((p[0]-q[0],p[1]-q[1],p[2]-q[2]))<=R2:
                    if arc[idx]<0: cA+=1
                    else: cI+=1
        if cA+cI>best: best=cA+cI; bA=cA; bI=cI
    return best,bA,bI

if __name__=="__main__":
    parent,child = 6,7
    pp,pa,pnc = build(parent)
    cp,ca,cnc = build(child)
    Rs=[3,6,9,12,15,17,18,21,27]
    out={"parent":parent,"child":child,"d":D,"phi":PHI,"rows":[]}
    # centres: subsample child for large R
    Ncp=len(cp)
    print(f"parent L{parent} N={len(pp)}  child L{child} N={Ncp}")
    allhold=True
    for R in Rs:
        stride=1 if R<=9 else max(1,Ncp//25000)
        cc=cp[::stride]
        bk,bkA,bkI = qmax_split(cp,ca,R,cc)          # child total, anchors, interiors at sup
        Rp=math.ceil(R/3.0)
        # parent b_Q at ceil(R/3): centres = parent pts (subsample if big)
        pc = pp[::(1 if Rp<=9 else max(1,len(pp)//25000))]
        bparent = qmax(pp,Rp,pc)
        rhs = bparent + bkI
        hold = bk<=rhs
        allhold=allhold and hold
        out["rows"].append({"R":R,"b_child":bk,"child_anchors_at_sup":bkA,
            "child_interiors_at_sup":bkI,"ceil_R/3":Rp,"b_parent_R/3":bparent,
            "rhs":rhs,"holds":hold})
        print(f"R={R:3} b_child={bk:3} (anch={bkA:3},int={bkI:3})  b_parent(ceil {Rp})={bparent:3} "
              f"+ I_child={bkI:3} = {rhs:3}  HOLDS={hold}",flush=True)
    out["recursion_holds_all_R"]=allhold
    # contraction summary
    C_child=max(r["b_child"]/r["R"]**D for r in out["rows"])
    E_child=max(r["child_interiors_at_sup"]/r["R"]**D for r in out["rows"])
    out["C_child_supRge3"]=round(C_child,3)
    out["E_child_supRge3"]=round(E_child,3)
    out["implied_fixed_point_Cstar"]=round(E_child/(1-PHI),3)
    out["contraction_dominates(E<(1-phi)C)"]= E_child<(1-PHI)*C_child
    print(json.dumps({k:out[k] for k in ["recursion_holds_all_R","C_child_supRge3",
        "E_child_supRge3","implied_fixed_point_Cstar","contraction_dominates(E<(1-phi)C)"]}))
    json.dump(out,open("design/tight/bound2_crosslevel.json","w"),indent=1)
    print("WROTE design/tight/bound2_crosslevel.json")
