#!/usr/bin/env node
// Bounded exact checks for descent-automata.md. No packages or parallel workers.
// This checker is deliberately small; it is not a gap-cutoff/menu search.
import assert from 'node:assert/strict';

const pair = [[0,1],[1,2],[2,3],[3,0],[0,2],[1,3],[2,0],[3,1]];
const names = 'abcdefgh';
const key = v => v.join(',');
const add = (a,b) => a.map((x,j) => x+b[j]);
const sub = (a,b) => a.map((x,j) => x-b[j]);
const c = [[0,0],[-1,0],[-1,1],[0,-1]];
const u = [[1,0],[0,1],[-1,0],[0,-1]];
const e = [0,1,-1,0], d = [[0,0],[1,0],[1,1],[1,0]];
const mod4 = x => (x%4+4)%4;
const rot = ([x,y],r) => [[x,y],[-y,x],[-x,-y],[y,-x]][r];
const tau = pair.map(([r,s]) => [[r,mod4(r+1)],[mod4(r+1),mod4(r-1)],
  [mod4(r-1),r],[r,s]].map(p => pair.findIndex(q => key(q)===key(p))));
const expand = w => w.flatMap(a => tau[a]);
const vec = pair.map(([r,s]) => [2*u[r][0]+c[s][0]-c[r][0],
  2*u[r][1]+c[s][1]-c[r][1],4+s-r]);
const R = Array.from({length:4},(_,r) => Array.from({length:4},(_,a) => {
  const s=mod4(r+e[a]), z=rot(d[a],r);
  return [2*z[0]+c[s][0]-2*c[r][0],2*z[1]+c[s][1]-2*c[r][1],4*a+s-4*r];
}));
const sigma = n => { let r=0,sgn=1; while(n) {r+=sgn*(n%2);n=Math.floor(n/2);sgn=-sgn;}return mod4(r); };
const q=Array.from({length:1025},(_,n)=>sigma(n)), Q=[], z=[];
let zz=[0,0];
for(let n=0;n<q.length;n++) {z.push(zz);Q.push([2*zz[0]+c[q[n]][0],2*zz[1]+c[q[n]][1],4*n+q[n]]);zz=add(zz,u[q[n]]);}
for(let n=0;n<q.length;n++) {
  const m=Math.floor(n/4),a=n%4;
  assert.equal(q[n],mod4(q[m]+e[a]));
  assert.deepEqual(z[n],add(z[m].map(x=>2*x),rot(d[a],q[m])));
  assert.deepEqual(Q[n],add(Q[m].map((x,j)=>x*(j===2?4:2)),R[q[m]][a]));
  if(n+1<q.length) assert.deepEqual(sub(Q[n+1],Q[n]),vec[pair.findIndex(p=>key(p)===key([q[n],q[n+1]]))]);
}
let primitivePower=0;
for(let k=1;k<=4;k++) {
  const coverage=tau.map((_,a)=>{let w=[a];for(let j=0;j<k;j++)w=expand(w);return new Set(w).size;});
  if(coverage.every(n=>n===8)) {primitivePower=k;break;}
}
assert(primitivePower);
// Named descent claim: flooring each selected index by four never increases
// the menu. Search only three-edge witnesses in a tiny bounded box.
let witness=null;
outer: for(let n=0;n<128;n++) for(let a=1;a<=8;a++) for(let b=1;b<=8;b++) for(let cc=1;cc<=8;cc++) {
  const ns=[n,n+a,n+a+b,n+a+b+cc], ps=ns.map(t=>Math.floor(t/4)).filter((t,j,ar)=>j===0||t!==ar[j-1]);
  const fine=ns.slice(1).map((t,j)=>sub(Q[t],Q[ns[j]]));
  const coarse=ps.slice(1).map((t,j)=>sub(Q[t],Q[ps[j]]));
  if(new Set(fine.map(key)).size<new Set(coarse.map(key)).size) {
    witness={indices:ns,parents:ps,fine,coarse};break outer;
  }
}
assert(witness,'expected a floor-descent cardinality counterexample');
const fiveIndices=[1,4,11,14,20,24,32], fiveParents=fiveIndices.map(n=>Math.floor(n/4));
const fiveFine=fiveIndices.slice(1).map((n,j)=>sub(Q[n],Q[fiveIndices[j]]));
const fiveCoarse=fiveParents.slice(1).map((n,j)=>sub(Q[n],Q[fiveParents[j]]));
assert.equal(new Set(fiveFine.map(key)).size,5);
assert.equal(new Set(fiveCoarse.map(key)).size,6);
const fiveWitness={indices:fiveIndices,parents:fiveParents,
  vertices:fiveIndices.map(n=>Q[n]),parentVertices:fiveParents.map(n=>Q[n]),
  fine:fiveFine,coarse:fiveCoarse};

// All actual adjacent pairs of the eight-transition fixed point, proved by
// internal-pair + boundary-pair closure. tau is primitive as checked above.
const adj=new Set();
for(const w of tau)for(let j=0;j<3;j++)adj.add(`${w[j]},${w[j+1]}`);
let changed=true;
while(changed) {changed=false;for(const k of [...adj]){const [a,b]=k.split(',').map(Number),p=`${tau[a][3]},${tau[b][0]}`;if(!adj.has(p)){adj.add(p);changed=true;}}}
function menuWords(menu) {
  const H=Math.max(0,...menu.map(v=>v[2])), B=Math.floor((H+3)/4);
  if(!B)return [];
  let k=0,L=1;while(L<B){L*=4;k++;}
  const words=new Map(),wanted=new Set(menu.map(key));
  const gaps=[...new Set(menu.flatMap(v=>{
    const ans=[];for(let g=Math.max(1,Math.ceil((v[2]-3)/4));g<=Math.floor((v[2]+3)/4);g++)ans.push(g);return ans;
  }))];
  for(const ab of adj) {
    let w=ab.split(',').map(Number);for(let j=0;j<k;j++)w=expand(w);
    for(const g of gaps)for(let i=0;i+g<=w.length;i++) {
      const v=[0,0,0];for(let j=0;j<g;j++)for(let t=0;t<3;t++)v[t]+=vec[w[i+j]][t];
      if(wanted.has(key(v))) {const f=w.slice(i,i+g);words.set(key(f),f);}
    }
  }
  return [...words.values()].sort((a,b)=>a.length-b.length||key(a).localeCompare(key(b)));
}
function automaton(menu) {
  // States are the empty word and all proper prefixes of matching words.
  const words=menuWords(menu), ps=new Map([['',[]]]);
  for(const w of words)for(let j=1;j<w.length;j++)ps.set(key(w.slice(0,j)),w.slice(0,j));
  const prefixes=[...ps.values()], index=new Map(prefixes.map((p,j)=>[key(p),j]));
  const whole=new Set(words.map(key));
  const matrices=tau.map((_,a)=>prefixes.map(p=>{
    const k=key([...p,a]);let mask=0n;
    if(whole.has(k))mask|=1n;
    if(index.has(k))mask|=1n<<BigInt(index.get(k));
    return mask;
  }));
  return {words,prefixes,matrices};
}
const rowProduct=(row,M)=>{let out=0n;for(let j=0;j<M.length;j++)if(row&(1n<<BigInt(j)))out|=M[j];return out;};
const multiply=(A,B)=>A.map(row=>rowProduct(row,B));
const identity=n=>Array.from({length:n},(_,j)=>1n<<BigInt(j));
const matrixWord=(w,P,n)=>w.reduce((A,a)=>multiply(A,P[a]),identity(n));
const nextTuple=P=>tau.map(w=>matrixWord(w,P,P[0].length));
const tupleKey=P=>P.map(M=>M.map(x=>x.toString(16)).join(',')).join(';');
function decide(menu,start=null) {
  menu=menu.filter(v=>v[2]>0);
  const {words,prefixes,matrices}=automaton(menu),n=prefixes.length;
  let P=matrices,k=0,row=null;
  if(start!==null) {
    let W=[0];while(W.length<=start){W=expand(W);P=nextTuple(P);k++;}
    row=matrixWord(W.slice(start),matrices,n)[0];
  }
  const seen=new Map(), limit=10000;
  while(k<limit) {
    const dead=start===null?P.findIndex(M=>M.every(x=>x===0n)):(row===0n?0:-1);
    if(dead>=0)return {verdict:'NO',start,k,zeroLetter:start===null?names[dead]:null,states:n,words:words.map(w=>w.map(a=>names[a]).join(''))};
    const t=tupleKey(P)+(row===null?'':`|${row.toString(16)}`);
    if(seen.has(t))return {verdict:'YES',start,k,cycleStart:seen.get(t),states:n,words:words.map(w=>w.map(a=>names[a]).join(''))};
    seen.set(t,k);
    if(row!==null)for(const a of tau[0].slice(1))row=rowProduct(row,P[a]);
    P=nextTuple(P);k++;
  }
  throw Error('bounded regression cap exceeded; no mathematical negative conclusion');
}
const full=[...new Map(vec.map(v=>[key(v),v])).values()];
const even=[[-1,-1,2],[-1,-3,6],[1,1,6],[1,3,10],[-2,0,12],[2,0,12]];
const tests={
  fullAny:decide(full),
  fullAt13:decide(full,13),
  omitD:decide(full.filter(v=>key(v)!=='0,-1,1')),
  evenAny:decide(even),
  evenAt0:decide(even,0),
  evenAt1:decide(even,1),
  evenAt3:decide(even,3),
  evenAt4:decide(even,4),
  nonpositiveOnly:decide([[0,0,0],[0,0,-1]])
};
assert.equal(tests.fullAny.verdict,'YES');assert.equal(tests.fullAt13.verdict,'YES');
assert.equal(tests.omitD.verdict,'NO');assert.equal(tests.evenAny.verdict,'YES');
assert.equal(tests.evenAt0.verdict,'YES');assert.equal(tests.nonpositiveOnly.verdict,'NO');
assert.equal(tests.evenAt1.verdict,'NO');assert.equal(tests.evenAt3.verdict,'YES');assert.equal(tests.evenAt4.verdict,'NO');
const evenNFA=automaton(even), P1=nextTuple(evenNFA.matrices), P2=nextTuple(P1), P3=nextTuple(P2);
assert.deepEqual(P2,P3);
const evenCycleCertificate={states:evenNFA.prefixes.map(w=>w.map(a=>names[a]).join('')||'epsilon'),
  equality:'P_2 = P_3; all 8 component matrices are nonzero',
  rowsHex:Object.fromEntries(P2.map((M,a)=>[names[a],M.map(r=>r.toString(16))]))};
console.log(JSON.stringify({timestamp:new Date().toISOString(),scope:'bounded algebra and fixed-menu semigroup regressions, not a universal five-menu exclusion',primitivePower,adjacentTransitionPairs:[...adj].map(k=>k.split(',').map(Number).map(a=>names[a]).join('')).sort(),R,witness,fiveWitness,tests,evenCycleCertificate},null,2));
