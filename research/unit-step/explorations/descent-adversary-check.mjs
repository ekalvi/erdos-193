#!/usr/bin/env node
// Bounded exact adversarial tests, not an infinite-selector search.
// All computations finish well below 60s; no dependencies or child processes.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const started = Date.now();
const sha = crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex');
const log = (type, value) => console.log(JSON.stringify({time:new Date().toISOString(),type,...value}));
log('start',{sha, scope:'finite local descent identities/counterexamples', nativeThreads:1});
const C=[[0,0],[-1,0],[-1,1],[0,-1]];
const U=[[1,0],[0,1],[-1,0],[0,-1]];
const delta=[0,1,-1,0], d=[[0,0],[1,0],[1,1],[1,0]], D=[2,2,4];
const add=(a,b)=>a.map((x,j)=>x+b[j]);
const sub=(a,b)=>a.map((x,j)=>x-b[j]);
const rot=(r,[x,y])=>[[x,y],[-y,x],[-x,-y],[y,-x]][r];
const key=a=>a.join(',');
const unique=a=>[...new Map(a.map(x=>[key(x),x])).values()];
const q=n=>{let s=0,sign=1;while(n){s+=sign*(n%2);n=Math.floor(n/2);sign=-sign;}return (s%4+4)%4;};
const N=4096, Q=[], Z=[];
let z=[0,0];
for(let n=0;n<=N;n++){Z.push(z);Q.push([...add(z.map(x=>2*x),C[q(n)]),4*n+q(n)]);z=add(z,U[q(n)]);}
const R=(r,a)=>[...sub(add(rot(r,d[a]).map(x=>2*x),C[(r+delta[a]+4)%4]),C[r].map(x=>2*x)),4*a+(r+delta[a]+4)%4-4*r];
for(let n=0;n<=N;n++){
  const m=Math.floor(n/4),a=n%4,r=q(m);
  assert.equal(q(n),(r+delta[a]+4)%4);
  assert.deepEqual(Z[n],add(Z[m].map(x=>2*x),rot(r,d[a])));
  assert.deepEqual(Q[n],add(Q[m].map((x,j)=>x*D[j]),R(r,a)));
  const t=Q[n][2]%16;
  assert.equal(Math.floor(t/4),a);
  assert.equal(((t%4)-delta[a]+4)%4,r);
}
log('correction-table',{rows:Array.from({length:4},(_,r)=>({r,R:delta.map((_,a)=>R(r,a))})),verifiedEndpoints:N+1});
const disp=(a,b)=>sub(Q[b],Q[a]);
const menu=path=>unique(path.slice(1).map((n,j)=>disp(path[j],n)));
const floors=path=>path.map(n=>Math.floor(n/4)).filter((n,j,a)=>j===0||n!==a[j-1]);
const detail=path=>({path,states:path.map(q),fine:menu(path),fineEdges:path.slice(1).map((n,j)=>disp(path[j],n)),parents:floors(path),parent:menu(floors(path)),parentEdges:floors(path).slice(1).map((n,j,a)=>disp(floors(path)[j],n))});
// One-step edge fibers: necessary local information for a label-only descent.
const fibers=new Map();
for(let n=0;n<256;n++)for(let gap=1;gap<=16;gap++){
  const k=key(disp(n,n+gap)),w=disp(Math.floor(n/4),Math.floor((n+gap)/4));
  if(!fibers.has(k))fibers.set(k,new Map());
  if(!fibers.get(k).has(key(w)))fibers.get(k).set(key(w),{n,gap,w});
}
const worst=[...fibers].sort((a,b)=>b[1].size-a[1].size)[0];
log('edge-fiber',{fine:worst[0],distinctParent:worst[1].size,examples:[...worst[1].values()]});
const decoratedFibers=new Map();
for(let n=0;n<256;n++)for(let gap=1;gap<=16;gap++){
 const k=[key(disp(n,n+gap)),n%4,(n+gap)%4].join(';'),w=disp(Math.floor(n/4),Math.floor((n+gap)/4));
 if(!decoratedFibers.has(k))decoratedFibers.set(k,new Map());
 if(!decoratedFibers.get(k).has(key(w)))decoratedFibers.get(k).set(key(w),{n,gap,w,parentStates:[q(Math.floor(n/4)),q(Math.floor((n+gap)/4))]});
}
const decoratedWorst=[...decoratedFibers].sort((a,b)=>b[1].size-a[1].size)[0];
log('phase-decorated-edge-fiber',{fineAndPhases:decoratedWorst[0],distinctParent:decoratedWorst[1].size,examples:[...decoratedWorst[1].values()]});
// Search short finite paths only to falsify local menu preservation. This is
// not a rerun of the old exhaustive B=16 infinite obstruction.
let calls=0,witness=null;
function find(path,M,P,remaining,allowDuplicates=true){
  calls++;
  if(P.size>=6){witness=path.slice();return true;}
  if(remaining===0||P.size+remaining<6)return false;
  const n=path.at(-1);
  for(let gap=1;gap<=16;gap++){
    const m=n+gap;if(m>256)break;
    if(!allowDuplicates&&Math.floor(n/4)===Math.floor(m/4))continue;
    const vk=key(disp(n,m));if(M.size===5&&!M.has(vk))continue;
    const wk=key(disp(Math.floor(n/4),Math.floor(m/4)));
    const M2=new Set(M);M2.add(vk);
    const P2=new Set(P);if(wk!=='0,0,0')P2.add(wk);
    path.push(m);if(find(path,M2,P2,remaining-1,allowDuplicates))return true;path.pop();
  }
  return false;
}
for(let start=0;start<16&&!witness;start++)find([start],new Set(),new Set(),6,false);
assert(witness);assert.equal(menu(witness).length,5);assert.equal(menu(floors(witness)).length,6);
log('floor-counterexample',{calls,...detail(witness)});
// Fixed-phase local injectivity test at the correction-residue level. An
// edge within phase a has planar residue modulo 4 determined by r,s,a and
// height residue modulo 16 determined by q(child endpoints). If two pairs
// share these residues, test whether they have the same correction delta.
for(let a=0;a<4;a++){
 const bins=new Map(),collisions=[];
 for(let r=0;r<4;r++)for(let s=0;s<4;s++){
   const e=sub(R(s,a),R(r,a));
   const residue=[((e[0]%4)+4)%4,((e[1]%4)+4)%4,((e[2]+4*(s-r))%16+16)%16];
   // DQ_parent has planar 4*delta_z+2*delta_c, not planar zero mod4.
   residue[0]=((e[0]+2*(C[s][0]-C[r][0]))%4+4)%4;
   residue[1]=((e[1]+2*(C[s][1]-C[r][1]))%4+4)%4;
   const k=key(residue);if(!bins.has(k))bins.set(k,[]);bins.get(k).push({r,s,e});
 }
 for(const [residue,rows] of bins)if(unique(rows.map(x=>x.e)).length>1)collisions.push({residue,rows});
 assert.equal(collisions.length,0);
 log('fixed-phase-residue',{a,bins:bins.size,ambiguousCorrectionBins:collisions});
}
// Test whether naming the start/end phases in addition to the displacement
// suffices; no reachability assumption is used in this finite algebra table.
for(let a=0;a<4;a++)for(let b=0;b<4;b++){
 const bins=new Map();
 for(let r=0;r<4;r++)for(let s=0;s<4;s++){
   const e=sub(R(s,b),R(r,a));
   const residue=[((e[0]+2*(C[s][0]-C[r][0]))%4+4)%4,((e[1]+2*(C[s][1]-C[r][1]))%4+4)%4,((e[2]+4*(s-r))%16+16)%16];
   const k=key(residue);if(!bins.has(k))bins.set(k,[]);bins.get(k).push({r,s,e});
 }
 const bad=[...bins].filter(([,rows])=>unique(rows.map(x=>x.e)).length>1);
 if(bad.length)log('phase-pair-ambiguity',{a,b,bad});
}
// Bounded witness search for the named local repairs. No infinite positive
// inference is made, and no prior selector family is re-enumerated.
const firsts=path=>path.filter((n,j)=>j===0||Math.floor(n/4)!==Math.floor(path[j-1]/4));
const lasts=path=>path.filter((n,j)=>j===path.length-1||Math.floor(n/4)!==Math.floor(path[j+1]/4));
const found=new Map();
let repairCalls=0,repairCap=1000000;
const edges=Array.from({length:257},(_,n)=>Array.from({length:Math.min(16,256-n)},(_,j)=>({m:n+j+1,k:key(disp(n,n+j+1))})));
function repairs(path,M){
 if(++repairCalls>repairCap)return;
 if(path.length>=7){
  const targets=[];
  const first=firsts(path),last=lasts(path),fp=menu(first),lp=menu(last);
  if(first.length<path.length&&menu(floors(path)).length>=6)targets.push(['duplicate-parent',floors(path)]);
  if(fp.length>=6)targets.push(['first-in-block',first]);
  if(lp.length>=6)targets.push(['last-in-block',last]);
  if(fp.length>=6&&lp.length>=6)targets.push(['both-first-last',first]);
  const counts=[];
  for(let a=0;a<4;a++){
   const selected=path.filter(n=>n%4===a),count=menu(selected).length;counts.push(count);
   if(count>=6)targets.push([`phase-${a}`,selected]);
  }
  if(counts.every(c=>c>=6))targets.push(['all-four-phases',path]);
  for(const [target,selected] of targets)if(!found.has(target)){
   found.set(target,path.slice());
   log('repair-counterexample',{target,...detail(path),selected,selectedMenu:menu(selected),first,last,phaseCounts:counts});
  }
 }
 if(path.length>=48||path.at(-1)>=192||found.size===9)return;
 const candidates=edges[path.at(-1)].filter(e=>M.has(e.k)||M.size<5).sort((x,y)=>Number(M.has(y.k))-Number(M.has(x.k))||x.m-y.m);
 for(const e of candidates){
  if(repairCalls>=repairCap||found.size===9)break;
  const fresh=!M.has(e.k);M.add(e.k);path.push(e.m);repairs(path,M);path.pop();if(fresh)M.delete(e.k);
 }
}
for(let start=0;start<16&&repairCalls<repairCap&&found.size<9;start++)repairs([start],new Set());
log('repair-search-summary',{repairCalls,repairCap,targets:[...found.keys()],boundedSearchOnly:true});
// Deletion-minimize each certificate without increasing its fine menu.
const preserves=(name,path)=>{
 if(menu(path).length>5)return false;
 if(name==='duplicate-parent')return floors(path).length<path.length&&menu(floors(path)).length>=6;
 if(name==='first-in-block')return menu(firsts(path)).length>=6;
 if(name==='last-in-block')return menu(lasts(path)).length>=6;
 if(name==='both-first-last')return menu(firsts(path)).length>=6&&menu(lasts(path)).length>=6;
 if(name.startsWith('phase-'))return menu(path.filter(n=>n%4===Number(name.slice(6)))).length>=6;
 return false;
};
for(const [target,original] of found){
 let path=original.slice(),changed=true;
 while(changed){changed=false;for(let j=0;j<path.length;j++){
  const trial=path.filter((_,i)=>i!==j);if(preserves(target,trial)){path=trial;changed=true;break;}
 }}
 assert(preserves(target,path));
 log('minimized-repair',{target,...detail(path),first:firsts(path),firstMenu:menu(firsts(path)),last:lasts(path),lastMenu:menu(lasts(path)),phases:Array.from({length:4},(_,a)=>({a,path:path.filter(n=>n%4===a),menu:menu(path.filter(n=>n%4===a))}))});
}
// Grouping loops at an identical full correction state: a return can be a
// sum of several menu elements. Seek a finite actual split, not infinity.
let loopCalls=0,loopStartCalls=0,loopWitness=null,loopState=null;
function loopSearch(path,M){
 if(++loopCalls>500000||++loopStartCalls>5000)return false;
 if(path.length>=7){
  const bins=Array.from({length:16},()=>[]);
  for(const n of path)bins[4*q(Math.floor(n/4))+n%4].push(n);
  for(let t=0;t<16;t++)if(bins[t].length>=7&&menu(bins[t]).length>=6){loopWitness=path.slice();loopState=t;return true;}
 }
 if(path.length>=64||path.at(-1)>=256)return false;
 const candidates=edges[path.at(-1)].filter(e=>M.has(e.k)||M.size<5).sort((x,y)=>Number(M.has(y.k))-Number(M.has(x.k))||x.m-y.m);
 for(const e of candidates){
  if(loopCalls>=500000||loopStartCalls>=5000)break;
  const fresh=!M.has(e.k);M.add(e.k);path.push(e.m);if(loopSearch(path,M))return true;path.pop();if(fresh)M.delete(e.k);
 }
 return false;
}
for(let start=0;start<128&&!loopWitness&&loopCalls<500000;start++){
 loopStartCalls=0;loopSearch([start],new Set());
}
if(loopWitness){
 const selected=p=>p.filter(n=>4*q(Math.floor(n/4))+n%4===loopState);
 let path=loopWitness,changed=true;
 while(changed){changed=false;for(let j=0;j<path.length;j++){
  const trial=path.filter((_,i)=>i!==j);if(menu(trial).length<=5&&menu(selected(trial)).length>=6){path=trial;changed=true;break;}
 }}
 log('correction-state-loops-counterexample',{loopCalls,loopState,parentState:Math.floor(loopState/4),phase:loopState%4,...detail(path),selected:selected(path),selectedMenu:menu(selected(path)),selectedParentMenu:menu(floors(selected(path)))});
}else log('correction-state-loops-search',{loopCalls,witness:null,scope:'bounded inconclusive search, no preservation theorem'});
// Hard-coded report certificates, checked independently of search choices.
const reportFloor=[0,4,8,12,22,26,32];
assert.deepEqual(reportFloor.map(n=>Q[n]),[[0,0,0],[3,0,17],[4,3,35],[4,0,48],[5,2,89],[6,5,107],[8,7,131]]);
assert.equal(menu(reportFloor).length,5);assert.equal(menu(floors(reportFloor)).length,6);
const reportDuplicates=[4,13,14,15,16,26,35,36,37,38,39,40];
assert.equal(menu(reportDuplicates).length,5);assert.equal(menu(floors(reportDuplicates)).length,6);
assert(floors(reportDuplicates).length<reportDuplicates.length);
const reportPhase=[0,1,12,13,25,36,48,49,60,61,73,88,100,111,112,124,135,147,148];
assert.equal(menu(reportPhase).length,5);assert.equal(menu(reportPhase.filter(n=>n%4===0)).length,6);
assert(Math.max(...reportPhase.slice(1).map((n,j)=>n-reportPhase[j]))<=15);
const reportFirstLast=[2,3,4,11,12,27,28,35,36,37,38,39,40];
assert.equal(menu(reportFirstLast).length,5);assert.equal(menu(firsts(reportFirstLast)).length,6);assert.equal(menu(lasts(reportFirstLast)).length,6);
log('report-certificates',{floor:detail(reportFloor),duplicates:detail(reportDuplicates),phase:{...detail(reportPhase),selected:reportPhase.filter(n=>n%4===0),selectedMenu:menu(reportPhase.filter(n=>n%4===0))},firstLast:{...detail(reportFirstLast),first:firsts(reportFirstLast),firstMenu:menu(firsts(reportFirstLast)),last:lasts(reportFirstLast),lastMenu:menu(lasts(reportFirstLast))}});
log('finish',{elapsedMs:Date.now()-started});
