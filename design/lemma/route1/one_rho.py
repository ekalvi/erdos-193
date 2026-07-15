import pickle, sys
from collections import defaultdict
from gate_run import word_interiors
def build_chain(L):
    d=pickle.load(open(f'gate2-l7-construction-L{L}.pkl','rb'))
    a=d['anchors']; w=d['words']; ch=[a[0]]
    for i in range(len(w)): ch+=word_interiors(a[i],w[i]); ch+=[a[i+1]]
    return ch
L=int(sys.argv[1]); rho=int(sys.argv[2])
pts=build_chain(L)
cnt=defaultdict(int); R=range(-rho,rho+1)
for (x,y,z) in pts:
    for dx in R:
        xx=x+dx
        for dy in R:
            yy=y+dy
            for dz in R: cnt[(xx,yy,z+dz)]+=1
b=max(cnt.values())
print(f'L{L} rho={rho} EXACTmax={b} C=(b-1)/rho={(b-1)/rho:.3f}',flush=True)
