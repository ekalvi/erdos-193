# Decisive cheap test: is the load-bearing c(q,4) "drift" 10->12 a DISTRIBUTION SHIFT
# (dangerous) or an EXTREME-VALUE artifact of sampling 3.36x more points per level
# (benign)? Measure the FULL c(q,4) distribution per level; check per-capita tail
# fractions for stability. Uses existing L5-L8 walks — no L9 build needed.
import pickle
from collections import defaultdict, Counter
from gate_run import word_interiors

def build_chain(pkl):
    st = pickle.load(open(pkl,'rb'))
    anchors, words, pw = st['anchors'], st['words'], st['parent_word']
    chain = [anchors[0]]
    for i in range(len(pw)):
        chain.extend(word_interiors(anchors[i], words[i]))
        chain.append(anchors[i+1])
    return chain

def c4_distribution(chain, R=4):
    C = 5
    grid = defaultdict(list)
    for p in chain: grid[(p[0]//C,p[1]//C,p[2]//C)].append(p)
    hist = Counter()
    for p in chain:
        cx,cy,cz = p; cnt=0
        gx,gy,gz = cx//C,cy//C,cz//C
        for bx in range(gx-1,gx+2):
            for by in range(gy-1,gy+2):
                for bz in range(gz-1,gz+2):
                    for (x,y,z) in grid.get((bx,by,bz),()):
                        if 0 < max(abs(x-cx),abs(y-cy),abs(z-cz)) <= R: cnt+=1
        hist[cnt]+=1
    return hist

print("level  N       max  mean   | per-capita fraction with c(4) >= k")
print("                           |    >=8      >=10     >=11     >=12")
for L,pkl in [(5,'gate2-l7-construction-L5.pkl'),(6,'gate2-l7-construction-L6.pkl'),
              (7,'gate2-l7-construction-L7.pkl'),(8,'gate2-l7-construction-L8.pkl')]:
    ch = build_chain(pkl); N=len(ch)
    h = c4_distribution(ch)
    mx = max(h); mean = sum(k*v for k,v in h.items())/N
    def frac(k): return sum(v for kk,v in h.items() if kk>=k)/N
    print(f"L{L:<2}   {N:<7} {mx:<4} {mean:.3f}  |  {frac(8):.5f}  {frac(10):.6f}  {frac(11):.6f}  {frac(12):.6f}", flush=True)
print("\nIf tail fractions are LEVEL-STABLE -> extreme-value (benign, true sup fixed ~12-13).")
print("If tail fractions GROW per level -> distribution shift (availability constant at real risk).")
