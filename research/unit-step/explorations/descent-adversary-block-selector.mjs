#!/usr/bin/env node
// Complete infinite menus for exactly one selected point per length-16 block,
// at offset a(q_m). Proof of completeness is in descent-adversary.md.
// This is not a prefix-stabilization test or arbitrary-selector exhaustion.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const started=Date.now(),L=16,scale=4;
const sha=crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex');
const emit=(type,x)=>console.log(JSON.stringify({time:new Date().toISOString(),type,...x}));
emit('start',{sha,L,scale,total:16**4,nativeThreads:1,scope:'infinite-complete state-dependent one-point-per-block selectors'});
const C=[[0,0],[-1,0],[-1,1],[0,-1]],U=[[1,0],[0,1],[-1,0],[0,-1]];
const q=n=>{let s=0,t=1;while(n){s+=t*(n%2);n=Math.floor(n/2);t=-t;}return(s%4+4)%4;};
const rot=(r,[x,y])=>[[x,y],[-y,x],[-x,-y],[y,-x]][r];
const Z=[[0,0]];for(let a=0;a<L;a++)Z.push(Z[a].map((x,j)=>x+U[q(a)][j]));
assert.deepEqual(Z[L],[scale,0]);
const F=Array.from({length:4},(_,r)=>Array.from({length:L},(_,a)=>{
 const s=(r+q(a))%4,p=rot(r,Z[a]);return[2*p[0]+C[s][0],2*p[1]+C[s][1],4*a+s];
}));
const edge=(r,s,a,b)=>F[s][b].map((x,j)=>x-F[r][a][j]+(j<2?2*scale*U[r][j]:4*L));
const ids=new Map(),vectors=[];
const id=v=>{const k=v.join(',');if(!ids.has(k)){ids.set(k,ids.size);vectors.push(v);}return ids.get(k);};
const pairs=Array.from({length:4},(_,r)=>[1,2].map(d=>[r,(r+d)%4])).flat();
// Independent direct-coordinate check for every endpoint-offset pair at an
// actual occurrence of each of the eight transitions. Infinite coverage is
// a substitution argument, not this bounded diagnostic.
const Q=[];let z=[0,0];
for(let n=0;n<=4096;n++){
 Q.push([2*z[0]+C[q(n)][0],2*z[1]+C[q(n)][1],4*n+q(n)]);
 z=z.map((x,j)=>x+U[q(n)][j]);
}
let coordinateChecks=0;
for(const [r,s] of pairs){
 let m=0;while(m<64&&(q(m)!==r||q(m+1)!==s))m++;
 assert(m<64);
 for(let a=0;a<L;a++)for(let b=0;b<L;b++){
  assert.deepEqual(edge(r,s,a,b),Q[L*(m+1)+b].map((x,j)=>x-Q[L*m+a][j]));
  coordinateChecks++;
 }
}
const lookup=pairs.map(([r,s])=>Array.from({length:L},(_,a)=>Array.from({length:L},(_,b)=>id(edge(r,s,a,b)))));
let best=Infinity,bestCount=0,witness=null,done=0;const histogram={};
for(let a=0;a<L;a++)for(let b=0;b<L;b++)for(let c=0;c<L;c++)for(let d=0;d<L;d++){
 const offsets=[a,b,c,d],labels=pairs.map(([r,s],j)=>lookup[j][offsets[r]][offsets[s]]),count=new Set(labels).size;
 histogram[count]=(histogram[count]??0)+1;
 if(count<best){best=count;bestCount=0;witness={offsets,menu:[...new Set(labels)].map(i=>vectors[i]),transitions:pairs.map(([r,s],j)=>({r,s,v:vectors[labels[j]]})),gaps:pairs.map(([r,s])=>L+offsets[s]-offsets[r])};}
 if(count===best)bestCount++;
 done++;
}
assert.equal(done,L**4);
assert.equal(best,6);assert.equal(bestCount,200);
assert.deepEqual(histogram,{'6':200,'8':65336});
emit('complete',{done,best,bestCount,histogram,witness,coordinateChecks,elapsedMs:Date.now()-started});
