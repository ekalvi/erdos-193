#!/usr/bin/env node
// Independent direct-run verifier for two fixed-menu extinction certificates.
// No Boolean matrices or code imported from the semigroup producer. Tiny,
// deterministic, one process; safely rerun from scratch after interruption.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const started=Date.now();
const pairs=[[0,1],[1,2],[2,3],[3,0],[0,2],[1,3],[2,0],[3,1]];
const names='abcdefgh',units=[[1,0],[0,1],[-1,0],[0,-1]];
const offsets=[[0,0],[-1,0],[-1,1],[0,-1]];
const id=(r,s)=>{const n=pairs.findIndex(p=>p[0]===r&&p[1]===s);assert(n>=0);return names[n];};
// Derive the transition substitution from the four-state base-4 recurrence.
const substitution=new Map(pairs.map(([r,s],j)=>{
  const states=[r,(r+1)%4,(r+3)%4,r,s];
  return [names[j],states.slice(1).map((v,k)=>id(states[k],v)).join('')];
}));
const expand=w=>[...w].map(x=>substitution.get(x)).join('');
const displacements=new Map(pairs.map(([r,s],j)=>[names[j],[
  2*units[r][0]+offsets[s][0]-offsets[r][0],
  2*units[r][1]+offsets[s][1]-offsets[r][1],4+s-r
]]));
const adjacent=new Set();
for(const w of substitution.values())for(let k=1;k<w.length;k++)adjacent.add(w.slice(k-1,k+1));
for(let changed=true;changed;){changed=false;for(const w of [...adjacent]){
  const next=substitution.get(w[0]).at(-1)+substitution.get(w[1])[0];
  if(!adjacent.has(next)){adjacent.add(next);changed=true;}
}}
assert.equal(adjacent.size,12);
// Verify primitivity, justifying that the certified zero factors recur.
for(const letter of names){let w=letter;for(let k=0;k<3;k++)w=expand(w);assert.equal(new Set(w).size,8);}
const tasks=[
 {id:'small-floor-witness',menu:[[2,0,12],[1,1,30],[1,4,23],[-3,-1,14],[4,3,35]],letter:'b',power:2,expectedWords:8,expectedStates:27},
 {id:'all-four-roundings-witness',menu:[[7,3,70],[2,4,68],[1,-7,66],[4,6,108],[-3,2,89]],letter:'c',power:2,expectedWords:16,expectedStates:286}
];
const results=[];
for(const task of tasks){
  assert.equal(task.menu.length,5);assert(task.menu.flat().every(Number.isSafeInteger));
  const H=Math.max(...task.menu.map(v=>v[2])),B=Math.floor((H+3)/4);
  assert(B<=32); // This is a fixed-size certificate verifier, not a general CLI.
  const gaps=new Set();
  for(const v of task.menu)for(let g=Math.max(1,Math.ceil((v[2]-3)/4));g<=Math.floor((v[2]+3)/4);g++)gaps.add(g);
  let length=1,power=0;while(length<B){length*=4;power++;}
  const wanted=new Set(task.menu.map(v=>v.join(','))),words=new Set();
  // Every factor of length <= B lies in an expanded actual adjacent pair;
  // every word expanded here is an actual factor. Thus this language is exact.
  for(const ab of adjacent){let w=ab;for(let k=0;k<power;k++)w=expand(w);
    for(const g of gaps)for(let i=0;i+g<=w.length;i++){
      const v=[0,0,0];for(const ch of w.slice(i,i+g)){const step=displacements.get(ch);for(let c=0;c<3;c++)v[c]+=step[c];}
      if(wanted.has(v.join(',')))words.add(w.slice(i,i+g));
    }
  }
  const prefixes=new Set(['']);for(const w of words)for(let k=1;k<w.length;k++)prefixes.add(w.slice(0,k));
  assert.equal(words.size,task.expectedWords);assert.equal(prefixes.size,task.expectedStates);
  let barrier=task.letter;for(let k=0;k<task.power;k++)barrier=expand(barrier);
  // Start from EVERY possible partial-return state, not just an aligned cut.
  let reachable=new Set(prefixes);const frontierSizes=[reachable.size];
  for(const letter of barrier){const next=new Set();for(const p of reachable){
    const child=p+letter;if(prefixes.has(child))next.add(child);if(words.has(child))next.add('');
  }reachable=next;frontierSizes.push(reachable.size);}
  assert.equal(reachable.size,0,'extinction certificate failed');
  results.push({id:task.id,menu:task.menu,maxPossibleGap:B,returnWords:words.size,
    prefixStates:prefixes.size,barrierLetter:task.letter,barrierPower:task.power,
    barrier,frontierSizes,verdict:'NO infinite subsequence with this fixed menu'});
}
console.log(JSON.stringify({schema:1,status:'pass',timestamp:new Date().toISOString(),
  sourceSha256:createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex'),
  workers:1,elapsedMs:Date.now()-started,results,
  scope:'Direct extinction checks plus the complete-language and recurring-factor arguments in descent.md. Two specified menus only; not a universal five-menu theorem.'},null,2));
