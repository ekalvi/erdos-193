#!/usr/bin/env node
// Bounded exact algebra checks, not a no-five-subsequence certificate.
// No dependencies; intended runtime < 60s. One CPU via taskset -c 0.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const started = Date.now();
const sourceSha256 = createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex');
const N = 6144, germGap = 128;
const mod4 = x => ((x % 4) + 4) % 4;
const add = (a,b) => a.map((x,j) => x+b[j]);
const sub = (a,b) => a.map((x,j) => x-b[j]);
const scale = (a,s) => a.map(x => x*s);
const rot = (v,r) => [v,[-v[1],v[0]],[-v[0],-v[1]],[v[1],-v[0]]][mod4(r)];
const key = v => v.join(',');
const c = [[0,0],[-1,0],[-1,1],[0,-1]], t = [0,1,-1,0];
const da = [[0,0],[1,0],[1,1],[1,0]];
function state(n) {
  let r=0, s=1;
  while(n) {r += s*(n%2); n=Math.floor(n/2); s=-s;}
  return mod4(r);
}
const q = Array.from({length:N+1},(_,n)=>state(n));
const z = [[0,0]], Q=[];
for(let n=0;n<=N;n++) {
  if(n) z.push(add(z[n-1],rot([1,0],q[n-1])));
  Q.push([...add(scale(z[n],2),c[q[n]]),4*n+q[n]]);
}
// Independent coordinate cross-check against the supplied eight-transition table.
const transitions = {'01':[1,0,5],'12':[0,3,5],'23':[-1,-2,5],'30':[0,-1,1],
  '02':[1,1,6],'13':[1,1,6],'20':[-1,-1,2],'31':[-1,-1,2]};
for(let n=0;n<N;n++) assert.deepEqual(sub(Q[n+1],Q[n]),transitions[`${q[n]}${q[n+1]}`]);
const R = Array.from({length:4},(_,r)=>Array.from({length:4},(_,a)=>[
  ...sub(add(scale(rot(da[a],r),2),c[mod4(r+t[a])]),scale(c[r],2)),
  4*a+mod4(r+t[a])-4*r
]));
assert.equal(new Set(R.flat().map(key)).size,16);
const D = v => [2*v[0],2*v[1],4*v[2]];
for(let n=0;n<=N;n++) {
  const m=Math.floor(n/4), a=n%4;
  assert.equal(q[n],mod4(q[m]+t[a]));
  assert.deepEqual(z[n],add(scale(z[m],2),rot(da[a],q[m])));
  assert.deepEqual(Q[n],add(D(Q[m]),R[q[m]][a]));
}
// Height phase alone recovers the correction; include zero parent gaps.
const rho = p => {const a=Math.floor(p/4); return R[mod4(p%4-t[a])][a];};
for(let n=0;n<512;n++) for(let gap=1;gap<=32;gap++) {
  const m=n+gap, v=sub(Q[m],Q[n]);
  const numerator=sub(add(v,rho(Q[n][2]%16)),rho((Q[n][2]+v[2])%16));
  assert.deepEqual(numerator,D(sub(Q[Math.floor(m/4)],Q[Math.floor(n/4)])));
}
assert.deepEqual([...new Set([0,1,2,4].map(n=>Math.floor(n/4)))],[0,1]);
// General all-scale base-4 and binary identities (proof is in the report).
const L = v => [v[0]+v[1],v[0]-v[1],2*v[2]];
const E = Array.from({length:4},(_,r)=>Array.from({length:2},(_,a)=>[
  ...sub(add(scale(rot([a,0],-r),2),c[mod4(a-r)]),L([...c[r],0]).slice(0,2)),
  4*a+mod4(a-r)-2*r
]));
for(let n=0;n<=N;n++) {
  const m=Math.floor(n/2), a=n%2;
  assert.deepEqual(Q[n],add(L(Q[m]),E[q[m]][a]));
}
for(let k=1;k<=4;k++) {
  const b=4**k, planar=2**k;
  for(let n=0;n<=N;n++) {
    const m=Math.floor(n/b), a=n%b, r=q[m], s=mod4(r+q[a]);
    const correction=[...sub(add(scale(rot(z[a],r),2),c[s]),scale(c[r],planar)),4*a+s-b*r];
    assert.deepEqual(Q[n],add([planar*Q[m][0],planar*Q[m][1],b*Q[m][2]],correction));
  }
}
// A named all-scale-boundary candidate: must the eight seam types
// require six labels merely to cross each seam once? x>=1,y>=0.
// Enumeration refutes/diagnoses that candidate only; it proves no cutoff theorem.
const masks=new Map(), reps=new Map();
for(let r=0;r<4;r++) for(let inc=1;inc<=2;inc++) {
  const s=mod4(r+inc), bit=1<<(2*r+inc-1);
  const seamParent=q.findIndex((rr,j)=>j>0 && q[j-1]===r && rr===s);
  assert.ok(seamParent>0);
  for(let gap=1;gap<=germGap;gap++) for(let x=1;x<=gap;x++) {
    const y=gap-x, p=mod4(r-q[x-1]), e=mod4(s+q[y]);
    const left=rot([z[x][0],-z[x][1]],r), right=rot(z[y],s);
    const v=[...add(scale(add(left,right),2),sub(c[e],c[p])),4*gap+e-p];
    const k=key(v); masks.set(k,(masks.get(k)||0)|bit);
    if(!reps.has(k)) reps.set(k,[]);
    const rows=reps.get(k);
    if(!rows.some(a=>a.bit===bit)) rows.push({bit,r,s,x,y});
    // Independently realize this seam at 4^4*m, beyond the gap bound.
    const center=256*seamParent;
    assert.ok(center+y<=N,'every seam must be independently realized');
    assert.deepEqual(v,sub(Q[center+y],Q[center-x]));
  }
}
const maskRepresentative=new Map();
for(const [v,mask] of masks) if(!maskRepresentative.has(mask)) maskRepresentative.set(mask,v);
const cover=Array(256).fill(null); cover[0]=[];
for(let mask=0;mask<256;mask++) if(cover[mask]) for(const [bits,v] of maskRepresentative) {
  const next=mask|bits, candidate=[...cover[mask],v];
  if(!cover[next] || candidate.length<cover[next].length) cover[next]=candidate;
}
const coverWitness=cover[255].map(v=>({v:v.split(',').map(Number),mask:masks.get(v),seams:reps.get(v)}));
// Endpoint-label ambiguity, with both parent gaps strictly positive.
const fibers=new Map();
for(let n=0;n<512;n++) for(let gap=4;gap<=32;gap++) {
  const m=n+gap, v=sub(Q[m],Q[n]), p=sub(Q[Math.floor(m/4)],Q[Math.floor(n/4)]);
  const k=key(v); if(!fibers.has(k)) fibers.set(k,new Map());
  const row=fibers.get(k); if(!row.has(key(p))) row.set(key(p),{n,m,v,parent:p,startPhase:[q[Math.floor(n/4)],n%4],endPhase:[q[Math.floor(m/4)],m%4]});
}
const split=[...fibers.values()].find(rows=>rows.size>=2);
// Direct counterexample to the naive finite-path menu monotonicity lemma.
// All child gaps are >=17, so there are no coalescing parents.
let dfsNodes=0, inflationWitness=null;
function inflate(path,childMenu,parentMenu) {
  if(++dfsNodes>500000) return false;
  if(parentMenu.size>=6) {
    inflationWitness={path,parents:path.map(n=>Math.floor(n/4)),
      childMenu:[...childMenu].map(k=>k.split(',').map(Number)),
      parentMenu:[...parentMenu].map(k=>k.split(',').map(Number))}; return true;
  }
  if(path.length>=9) return false;
  const n=path.at(-1);
  for(let gap=17;gap<=32;gap++) {
    const m=n+gap, ck=key(sub(Q[m],Q[n])), pk=key(sub(Q[Math.floor(m/4)],Q[Math.floor(n/4)]));
    if(!childMenu.has(ck)&&childMenu.size===5) continue;
    if(inflate([...path,m],new Set([...childMenu,ck]),new Set([...parentMenu,pk]))) return true;
  }
  return false;
}
inflate([0],new Set(),new Set());
assert.ok(inflationWitness,'bounded diagnostic did not find an inflation witness');
inflationWitness.edges=inflationWitness.path.slice(1).map((m,j)=>{
  const n=inflationWitness.path[j];
  return {n,m,child:sub(Q[m],Q[n]),parent:sub(Q[Math.floor(m/4)],Q[Math.floor(n/4)])};
});
// Freeze the witnesses asserted in the report, separately from discovering them.
assert.deepEqual(inflationWitness.path,[0,17,34,51,70,90,109]);
assert.equal(inflationWitness.childMenu.length,5);
assert.equal(inflationWitness.parentMenu.length,6);
inflationWitness.offsetDecimations=[];
for(const base of [2,4]) for(let offset=0;offset<base;offset++) {
  const parents=[...new Set(inflationWitness.path.map(n=>Math.floor((n+offset)/base)))];
  const menu=[...new Set(parents.slice(1).map((m,j)=>key(sub(Q[m],Q[parents[j]]))))];
  inflationWitness.offsetDecimations.push({base,offset,parents,menu:menu.map(k=>k.split(',').map(Number)),count:menu.length});
}
// Does choosing one global base-4 rounding offset repair finite menu monotonicity?
let allOffsetNodes=0, allOffsetWitness=null;
function inflateAllOffsets(path,childMenu,menus) {
  if(++allOffsetNodes>500000) return false;
  if(menus.every(menu=>menu.size>=6)) {
    allOffsetWitness={path,childMenu:[...childMenu].map(k=>k.split(',').map(Number)),
      offsets:menus.map((menu,offset)=>({offset,parents:path.map(n=>Math.floor((n+offset)/4)),
        menu:[...menu].map(k=>k.split(',').map(Number))}))}; return true;
  }
  if(path.length>=11) return false;
  const n=path.at(-1);
  for(let gap=17;gap<=32;gap++) {
    const m=n+gap, ck=key(sub(Q[m],Q[n]));
    if(!childMenu.has(ck)&&childMenu.size===5) continue;
    const nextMenus=menus.map((menu,b)=>new Set([...menu,key(sub(Q[Math.floor((m+b)/4)],Q[Math.floor((n+b)/4)]))]));
    if(inflateAllOffsets([...path,m],new Set([...childMenu,ck]),nextMenus)) return true;
  }
  return false;
}
inflateAllOffsets([0],new Set(),Array.from({length:4},()=>new Set()));
assert.ok(allOffsetWitness,'bounded diagnostic did not find an all-offset witness');
assert.deepEqual(allOffsetWitness.path,[0,17,34,51,78,100,127]);
assert.equal(allOffsetWitness.childMenu.length,5);
for(const {menu} of allOffsetWitness.offsets) assert.equal(menu.length,6);
assert.deepEqual(inflationWitness.offsetDecimations.filter(x=>x.base===2).map(x=>x.count),[6,6]);
assert.equal(cover[255].length,2);
assert.deepEqual(coverWitness.map(x=>x.v),[[1,9,198],[-1,-9,194]]);
console.log(JSON.stringify({schema:1,startedAt:new Date(started).toISOString(),timestamp:new Date().toISOString(),
  sourceSha256,kind:'bounded-exact-check',N,germGap,R,E,
  seamMasks:[...maskRepresentative.keys()].sort((a,b)=>a-b),minimumSeamCover:cover[255].length,coverWitness,
  splitWitness:[...split.values()].slice(0,2),dfsNodes,inflationWitness,allOffsetNodes,allOffsetWitness,elapsedMs:Date.now()-started},null,2));
