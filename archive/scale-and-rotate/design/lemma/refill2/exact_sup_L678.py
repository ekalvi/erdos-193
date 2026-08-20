import pickle
from collections import defaultdict
from search193 import candidate_step_vectors
MENU=candidate_step_vectors(2)
def wi(start,w):
    pts=[];x,y,z=start
    for si in w[:-1]:
        s=MENU[si];x,y,z=x+s[0],y+s[1],z+s[2];pts.append((x,y,z))
    return pts
def em(inter,rho):
    cnt=defaultdict(int)
    for (x,y,z) in inter:
        for cx in range(x-rho,x+rho+1):
         for cy in range(y-rho,y+rho+1):
          for cz in range(z-rho,z+rho+1):
            cnt[(cx,cy,cz)]+=1
    return max(cnt.values())
for L in (6,7,8):
    d=pickle.load(open(f"gate2-l7-construction-L{L}.pkl","rb"))
    a=d["anchors"];w=d["words"];inter=[]
    for i in range(len(a)-1): inter+=wi(a[i],w[i])
    print(f"L{L} exact-sup: rho1={em(inter,1)} rho2={em(inter,2)}",flush=True)
