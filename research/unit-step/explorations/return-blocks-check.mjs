#!/usr/bin/env node
// Exact finite-selector exploration. No dependencies, one JS thread.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
const start = Date.now();
const log = (event, data = {}) => console.log(JSON.stringify({time:new Date().toISOString(), event, ...data}));
const sha256 = createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex');
const N = 4096;
log('start', {sha256, N, selectors:65535, threads:1});
const delta = [0,1,3,0];
const c = [[0,0],[-1,0],[-1,1],[0,-1]];
const u = [[1,0],[0,1],[-1,0],[0,-1]];
const q = new Uint8Array(N+2);
for(let n=1;n<q.length;n++) q[n]=(q[Math.floor(n/4)]+delta[n%4])%4;
const X = new Int32Array(N+1), Y = new Int32Array(N+1), H = new Int32Array(N+1);
let x=0,y=0;
for(let n=0;n<=N;n++) {X[n]=2*x+c[q[n]][0];Y[n]=2*y+c[q[n]][1];H[n]=4*n+q[n];x+=u[q[n]][0];y+=u[q[n]][1];}
let unresolved=[], worst=0, worstMask=0;
for(let mask=1;mask<65536;mask++) {
  let prev=-1;
  const seen=new Set();
  for(let n=0;n<=N;n++) if(mask & (1<<(4*q[n]+n%4))) {
    if(prev>=0) seen.add(`${X[n]-X[prev]},${Y[n]-Y[prev]},${H[n]-H[prev]}`);
    prev=n;
    if(seen.size>=6) {if(n>worst) {worst=n;worstMask=mask;} break;}
  }
  if(seen.size<6) unresolved.push({mask,menu:[...seen]});
  if(mask%8192===0)log('progress',{completed:mask,total:65535,elapsed_s:(Date.now()-start)/1000});
}
log('phase-state-result',{unresolved,worst,worstMask,elapsed_s:(Date.now()-start)/1000});
assert.equal(unresolved.length,0,'selectors with fewer than six observed need more work');
// Broader family: retain n iff (q[n], q[n+1], n mod 4) is accepted.
// At phases 0,1,2 only one outgoing transition per state is possible;
// phase 3 has both transitions, giving exactly 20 symbols.
const types=[];
for(let p=0;p<4;p++)for(let r=0;r<4;r++) {
 const ds=p===0||p===2?[1]:p===1?[2]:[1,2];
 for(const d of ds)types.push([r,(r+d)%4,p]);
}
const typeIds=new Map(types.map((v,i)=>[v.join(','),i]));
const symbols=Array.from({length:N+1},(_,n)=>typeIds.get([q[n],q[n+1],n%4].join(',')));
assert.ok(symbols.every(x=>x!==undefined));
let edgeWorst=0,edgeWorstMask=0,edgeUnresolved=[];
for(let mask=1;mask<(1<<20);mask++){
 let prev=-1;const seen=new Set();
 for(let n=0;n<=N;n++)if(mask&(1<<symbols[n])){
  if(prev>=0)seen.add(`${X[n]-X[prev]},${Y[n]-Y[prev]},${H[n]-H[prev]}`);
  prev=n;
  if(seen.size>=6){if(n>edgeWorst){edgeWorst=n;edgeWorstMask=mask;}break;}
 }
 if(seen.size<6)edgeUnresolved.push(mask);
 if(mask%131072===0)log('edge-phase-progress',{completed:mask,total:(1<<20)-1,elapsed_s:(Date.now()-start)/1000});
}
log('edge-phase-result',{types,unresolved:edgeUnresolved,worst:edgeWorst,worstMask:edgeWorstMask});
assert.equal(edgeUnresolved.length,0);
// Prove primitivity for the actual decorated substitution (not a prefix test).
const child=(type)=>{
 const [r,s]=type;
 return [[r,(r+1)%4,0],[(r+1)%4,(r+3)%4,1],[(r+3)%4,r,2],[r,s,3]].map(t=>typeIds.get(t.join(',')));
};
let images=types.map((_,i)=>[i]);let primitiveDepth=0;
while(!images.every(w=>new Set(w).size===20)){
 assert.ok(primitiveDepth<6);
 images=images.map(w=>w.flatMap(i=>child(types[i])));primitiveDepth++;
}
log('edge-phase-primitivity',{depth:primitiveDepth,blockLength:4**primitiveDepth,gapBound:2*4**primitiveDepth-1});
// Exact state-only return menus, not merely prefix-observed menus.
// mu^2(r) contains all four states, so any nonempty state selector has
// gap <=31. Every factor of length <=32 lies in mu^3(ab) for a legal pair ab.
const muWord=w=>w.flatMap(r=>delta.map(d=>(r+d)%4));
const stateImages=Array.from({length:4},(_,r)=>muWord(muWord([r])));
assert.ok(stateImages.every(w=>new Set(w).size===4));
const blocks=[];
for(let r=0;r<4;r++)for(const d of [1,2]){
 let w=[r,(r+d)%4];for(let k=0;k<3;k++)w=muWord(w);blocks.push(w);
}
const stateReturns=[];
for(let mask=1;mask<16;mask++){
 const menu=new Set();let maxGap=0;
 for(const w of blocks){
  let x=0,y=0,prev=null;
  for(let n=0;n<w.length;n++){
   const r=w[n],p=[2*x+c[r][0],2*y+c[r][1],4*n+r];
   if(mask&(1<<r)){
    if(prev){menu.add(p.map((v,k)=>v-prev.p[k]).join(','));maxGap=Math.max(maxGap,n-prev.n);}
    prev={n,p};
   }
   x+=u[r][0];y+=u[r][1];
  }
 }
 stateReturns.push({mask,states:[0,1,2,3].filter(r=>mask&(1<<r)),count:menu.size,maxGap,menu:[...menu].map(v=>v.split(',').map(Number)).sort((a,b)=>a[2]-b[2]||a[0]-b[0]||a[1]-b[1])});
}
log('state-only-exact-returns',{stateReturns});
log('done',{elapsed_s:(Date.now()-start)/1000});
