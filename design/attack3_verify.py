"""Independent verification of the 26-point Model-B hitting set using the
PROJECT'S OWN legality predicate (gate_run.word_legal / amplify193.legal_against).
Places only A0, A1 and the 26 obstacle points; checks every word of
D_2-4 + D_5 for step (2,2,-2) is illegal. Also re-checks the whole obstacle
configuration is triple-free (erdos193.first_disqualifier)."""
import pickle, sys, time, os
sys.path.insert(0, "/Users/erik/homelab/math193")
os.chdir("/Users/erik/homelab/math193")
from search193 import candidate_step_vectors
from gate_run import word_legal, MENU, IDX
from erdos193 import first_disqualifier

PICKS = [(2,2,4),(4,4,4),(2,4,4),(4,2,4),(-6,-6,-3),(8,8,9),(-2,0,-2),
         (0,-1,-1),(7,6,9),(6,7,9),(-1,-2,-1),(-6,-3,-3),(-1,0,-2),(0,-1,-2),
         (10,13,14),(-2,0,-1),(11,13,14),(13,10,14),(9,12,11),(12,9,11),
         (7,6,10),(-10,-14,-12),(14,10,8),(0,-2,-1),(5,9,8),(-2,-5,-2)]
A0, A1 = (0,0,0), (6,6,8)
points = [A0, A1] + PICKS
print("config triple-free check (first_disqualifier):", first_disqualifier(points))
pset = set(points)

d4 = pickle.load(open("connector_domains4.pkl","rb"))
dom24 = sorted(d4["domains"][IDX[(2,2,-2)]], key=len)
d5 = pickle.load(open("dstar5_fragile.pkl","rb"))
wordsB = [tuple(w) for w in dom24] + [tuple(IDX[v] for v in w) for w in d5[(2,2,-2)]]
print("words:", len(wordsB))
t0=time.time(); memo={}; alive=0; alive_ex=[]
for wi,w in enumerate(wordsB):
    if word_legal(A0, w, points, pset, memo):
        alive += 1
        if len(alive_ex)<5: alive_ex.append(w)
    if wi%10000==0:
        print("  %d/%d alive=%d (%.1fs)"%(wi,len(wordsB),alive,time.time()-t0)); sys.stdout.flush()
print("FINAL: surviving legal words = %d / %d  (%.1fs)"%(alive,len(wordsB),time.time()-t0))
print("examples:", alive_ex)
