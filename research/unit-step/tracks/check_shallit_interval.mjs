#!/usr/bin/env node
// Bounded independent arithmetic checks of the symbolic interval engine.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {IMAGE} from './shallit_ratio_automaton.mjs';
import {compareFractions,atParameter,feasible,accepting,digitChild,ROOT} from './shallit_interval_automaton.mjs';

const cmp=(a,b)=>{const x=a[0]*b[1]-b[0]*a[1];return x<0n?-1:x>0n?1:0;};
function reference(s) {
  const A=s.slice(3,8).map(BigInt),B=s.slice(8).map(BigInt),N=B.reduce((x,y)=>x+y,0n),p=-A.reduce((x,y)=>x+y,0n);
  if(!N)return A.every(x=>x===0n);
  let lo=[1n,3n],hi=[2n,3n];
  if(cmp([p-1n,N],lo)>0)lo=[p-1n,N];
  if(cmp([p+1n,N],hi)<0)hi=[p+1n,N];
  if(cmp(lo,hi)>=0)return false;
  const ab=A.reduce((sum,x,r)=>sum+x*B[r],0n),bb=B.reduce((sum,x)=>sum+x*x,0n);
  let t=[-ab,bb];if(cmp(t,lo)<0)t=lo;if(cmp(t,hi)>0)t=hi;
  const distance=A.reduce((sum,x,r)=>{const v=x*t[1]+B[r]*t[0];return sum+v*v;},0n);
  return distance<4n*t[1]*t[1];
}
assert.equal(compareFractions(999999999,1000000000,1000000000,1000000001),-1);
assert.equal(compareFractions(1000000000,1000000001,999999999,1000000000),1);
const tangent=[3,0,0,-2,-2,0,0,0,2,2,2,2,0];
assert.equal(feasible(tangent),null);assert.equal(reference(tangent),false);
const n=1000000000;
const largeTangent=[3,0,0,-n-1,-n-1,-n+1,-n+1,-n,2*n,2*n,2*n,2*n,2*n];
assert.equal(feasible(largeTangent),null);assert.equal(reference(largeTangent),false);
assert.equal(feasible([1,0,0,-3,0,0,0,0,3,0,0,0,0]),null); // strict clock touches theta=2/3
assert(feasible(ROOT));
const synthetic=[3,0,0,-1,0,0,0,0,3,0,0,0,0];
assert(feasible(synthetic));assert.deepEqual(accepting(synthetic),[1,3]);

let word=[0];for(let k=0;k<3;k++)word=word.flatMap(a=>IMAGE.map(t=>(a+t)%5));
const F=[Array(5).fill(0)];for(const a of word){const p=F.at(-1).slice();p[a]++;F.push(p);}
function state(i,j,k) {
  const rotation=word[i],A=F[i].map((x,r)=>x-F[j][r]),B=F[k].map((x,r)=>x-F[i][r]);
  return [Number(i<j)+2*Number(j<k),(word[j]-rotation+5)%5,(word[k]-rotation+5)%5,
    ...A.slice(rotation),...A.slice(0,rotation),...B.slice(rotation),...B.slice(0,rotation)];
}
const fixed=[['1-1',1,2],['1-2',1,3],['2-1',2,3]].map(([name,num,den])=>({num,den,
  states:new Set(JSON.parse(fs.readFileSync(new URL(`checks/shallit-ratio-${name}.json`,import.meta.url),'utf8')).closedStates.map(s=>s.join(',')))}));
let tested=0,pointMemberships=0;
for(let i=0;i<40;i++)for(let j=i;j<40;j++)for(let k=j;k<40;k++) {
  const s=state(i,j,k);
  assert.equal(feasible(s)!==null,reference(s));
  assert.deepEqual(digitChild(state(Math.floor(i/14),Math.floor(j/14),Math.floor(k/14)),[i%14,j%14,k%14]),s);
  for(const {num,den,states} of fixed) {
    const q=atParameter(s,num,den),passes=q.norm<4n*BigInt(den*den)&&q.clock>-BigInt(den)&&q.clock<BigInt(den);
    assert.equal(feasible(s,[num,den,num,den])!==null,passes);
    if(passes){const d=s.slice(3,8).map((x,r)=>den*x+num*s[8+r]);assert(states.has([...s.slice(0,3),...d].join(',')));pointMemberships++;}
  }
  assert.equal(accepting(s),null);tested++;
}
const first=state(0,3,6),second=state(94,114,134);
assert.deepEqual(first.slice(0,3),[3,1,0]);assert.deepEqual(second.slice(0,3),[3,1,0]);
const firstError=first.slice(3,8).map((x,r)=>2*x+first[8+r]),secondError=second.slice(3,8).map((x,r)=>2*x+second[8+r]);
assert(firstError.some(x=>x!==0));assert.deepEqual(secondError,firstError.map(x=>-x||0));
const midpoint=JSON.parse(fs.readFileSync(new URL('checks/shallit-midpoint.json',import.meta.url),'utf8'));
const midpointKeys=new Set(midpoint.closedStates.map(s=>s.join(',')));
assert(midpointKeys.has(first.join(','))&&midpointKeys.has(second.join(',')));
console.log(JSON.stringify({status:'pass',smallOrderedTriples:tested,fixedCertificateMemberships:pointMemberships,
  strictBoundaryAndLargeIntegerTests:true,convexMergingCountermodel:true,
  scope:'Exact affine recurrence, interval feasibility, and convex-merging diagnostics; the uniform theorem has a separate certificate checker.'}));
