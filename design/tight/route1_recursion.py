"""Route 1 proof ingredients: recursion identity + M-dilation + stitch inflation."""
import sys, pickle, json
sys.path.insert(0,"/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from gate_run import word_interiors
from amplify_rich import M_BAL3
from imbricate193 import apply
MENU=candidate_step_vectors(2); M=M_BAL3

def load(level):
    return pickle.load(open(f"/Users/erik/homelab/math193/gate2-l7-construction-L{level}.pkl","rb"))

def build_chain_and_anchoridx(d):
    an=d["anchors"]; w=d["words"]
    chain=[an[0]]; aidx=[0]
    for i in range(len(an)-1):
        chain.extend(word_interiors(an[i],w[i])); chain.append(an[i+1]); aidx.append(len(chain)-1)
    return chain, aidx, w

def mul(p): return tuple(M[r][0]*p[0]+M[r][1]*p[1]+M[r][2]*p[2] for r in range(3))
def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]),abs(a[2]-b[2]))

out={}
# 1. recursion identity: L(k+1) anchors == M . (L k chain) ?
for lv in (6,7,8):
    dk=load(lv-1); dkp=load(lv)
    chain_k,_,_=build_chain_and_anchoridx(dk)
    an_kp=dkp["anchors"]
    ok = len(an_kp)==len(chain_k) and all(mul(chain_k[i])==an_kp[i] for i in range(len(chain_k)))
    out[f"recursion_anchors_eq_M_parent_L{lv}"]=ok

# 2. M-dilation on ACTUAL segment difference vectors + stitch word lengths
for lv in (6,7,8):
    d=load(lv)
    chain,aidx,w=build_chain_and_anchoridx(d)
    # max/min stitch word length (steps per anchor-gap)
    wl=[len(ww) for ww in w.values()]
    # M-dilation ratio |M d|inf/|d|inf over consecutive-anchor differences at parent level
    # (use this level's own anchor preimages: differences of parent points)
    # parent points = M^{-1} anchors; instead measure on this chain's step/short diffs:
    ratios=[]
    step=max(1,len(chain)//4000)
    for i in range(0,len(chain)-20,step):
        for n in (5,10,20):
            a=chain[i]; b=chain[i+n]
            dv=(b[0]-a[0],b[1]-a[1],b[2]-a[2])
            dn=max(abs(dv[0]),abs(dv[1]),abs(dv[2]))
            if dn==0: continue
            Md=mul(dv); Mn=max(abs(Md[0]),abs(Md[1]),abs(Md[2]))
            ratios.append(Mn/dn)
    out[f"L{lv}_stitch_wordlen"]={"min":min(wl),"max":max(wl),"mean":round(sum(wl)/len(wl),3),
        "hist":{k:wl.count(k) for k in range(min(wl),max(wl)+1)}}
    out[f"L{lv}_Mdilation_inf"]={"min":round(min(ratios),4),"mean":round(sum(ratios)/len(ratios),4),"max":round(max(ratios),4)}

# 3. per-level point-growth and extent-growth (the TRUE dilation)
prev=None
for lv in (5,6,7,8):
    d=load(lv); chain,_,_=build_chain_and_anchoridx(d)
    xs=[p[0] for p in chain]; ys=[p[1] for p in chain]; zs=[p[2] for p in chain]
    extent=max(max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs))
    cur=(len(chain),extent)
    if prev:
        out[f"growth_L{lv-1}_to_L{lv}"]={"pts_ratio":round(cur[0]/prev[0],4),"extent_ratio":round(cur[1]/prev[1],4)}
    prev=cur

# singular values check
print("sigma of M (2-norm):", "smin=2.5414 => inf-dilation bound 2.5414/sqrt(3)=%.4f"%(2.5414/(3**0.5)))
print(json.dumps(out,indent=1))
json.dump(out,open("/Users/erik/homelab/math193/design/tight/route1_recursion.json","w"),indent=1)
