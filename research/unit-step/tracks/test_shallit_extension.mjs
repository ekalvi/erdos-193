#!/usr/bin/env node
import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {execFileSync,spawn} from 'node:child_process';import {fileURLToPath} from 'node:url';
import {closedFeasible,choices,findCycle,validateProgress} from './shallit_interval_extension.mjs';
import {feasible} from './verify_shallit_interval_extension.mjs';
import {digitChild,atParameter,ROOT} from './shallit_interval_automaton.mjs';
import {prefixAt} from './shallit_ratio_automaton.mjs';
const file=name=>fileURLToPath(new URL(name,import.meta.url));
const sourceData=JSON.parse(fs.readFileSync(file('checks/shallit-extension-100.json'),'utf8'));
const intervals=[[1,2,1,2],[999998,2000000,1000002,2000000],[98,200,102,200],[1,3,2,3]];
let comparisons=0;
for(let id=0;id<sourceData.states;id+=73){const s=sourceData.closedStates[id];
  for(let k=0;k<12;k++){const next=digitChild(s,[(3*k)%14,(7*k+1)%14,(11*k+2)%14]);if(!next)continue;
    for(const I of intervals){assert.equal(Boolean(closedFeasible(next,I)),feasible(next.slice(3,8),next.slice(8),I));comparisons++;}}
}
for(const s of sourceData.closedStates.slice(0,12))for(const I of intervals){
  const expected=[];for(let x=0;x<14;x++)for(let y=0;y<14;y++)for(let z=0;z<14;z++){
    const t=digitChild(s,[x,y,z]);if(!t)continue;
    const N=BigInt(t.slice(8).reduce((a,b)=>a+b,0)),p=-BigInt(t.slice(3,8).reduce((a,b)=>a+b,0));
    if(BigInt(I[0])*N-p*BigInt(I[1])<=BigInt(I[1])&&BigInt(I[2])*N-p*BigInt(I[3])>=-BigInt(I[3]))expected.push([x,y,z].join(','));
  }
  assert.deepEqual(choices(s,I).map(String).sort(),expected.sort());
}
const boundary=[3,0,0,-2,0,0,0,0,83,156,0,0,0];
for(const [n,expected] of [[9999,true],[10000,true],[10001,false]]){
  const I=[n,1000000,n,1000000];assert.equal(Boolean(closedFeasible(boundary,I)),expected);assert.equal(feasible(boundary.slice(3,8),boundary.slice(8),I),expected);
}
const big=10000000000,large=[3,0,0,-big,-big,0,0,0,2*big,2*big,0,0,0];
assert(closedFeasible(large,[1,2,1,2])&&feasible(large.slice(3,8),large.slice(8),[1,2,1,2]));
// A synthetic, deliberately non-root-reachable cycle tests the detector only.
// It is NOT a cycle claimed to occur in Shallit's word.
const fake=[3,0,0,-1,0,0,0,0,4,0,0,0,0],digits=[0,13,0],next=digitChild(fake,digits);
const cycle=findCycle([{state:fake,parent:-1,digits:[]}],0,next,digits,[98,200,102,200]);
assert.deepEqual(cycle.theta,['1','2']);assert.equal(cycle.spanBefore,4);assert.equal(cycle.spanAfter,56);
assert.deepEqual(atParameter(fake,1,2),atParameter(next,1,2));
const perturbed=next.slice();perturbed[3]++;assert.equal(findCycle([{state:fake,parent:-1,digits:[]}],0,perturbed,digits,[98,200,102,200]),null);

const frontier=JSON.parse(fs.readFileSync(file('checks/shallit-central-frontier.json'),'utf8'));
assert.equal(frontier.producerIdentity.codeSha256,sourceData.codeSha256);
let frontierState=ROOT.slice();const indices=[0n,0n,0n];
for(const row of frontier.digits){frontierState=digitChild(frontierState,row);for(let r=0;r<3;r++)indices[r]=14n*indices[r]+BigInt(row[r]);}
assert.deepEqual(frontierState,frontier.state);assert.deepEqual(indices.map(String),frontier.indices);
const F=indices.map(prefixAt),[i,j,k]=indices;assert(i<j&&j<k);assert.equal(k-i,BigInt(frontier.span));
function letter(n){let s=0;while(n){s+=Number('01213101314310'[Number(n%14n)]);n/=14n;}return s%5;}
const rotation=letter(i),rawA=F[0].map((x,r)=>x-F[1][r]),rawB=F[2].map((x,r)=>x-F[0][r]);
assert.deepEqual(frontierState.slice(3).map(BigInt),[...rawA.slice(rotation),...rawA.slice(0,rotation),...rawB.slice(rotation),...rawB.slice(0,rotation)]);
assert.deepEqual(frontierState.slice(0,3),[3,(letter(j)-rotation+5)%5,(letter(k)-rotation+5)%5]);
const [tn,td]=frontier.theta.map(BigInt),errors=frontierState.slice(3,8).map((x,r)=>BigInt(x)*td+BigInt(frontierState[8+r])*tn);
const norm=errors.reduce((a,b)=>a+b*b,0n),clock=errors.reduce((a,b)=>a+b,0n);
assert.equal(String(norm),frontier.squaredErrorNumerator);assert.equal(String(td),frontier.errorDenominator);
assert(norm>0n&&400n*norm<=1521n*td*td&&clock>=-td&&clock<=td);
assert(tn*3n>=td&&tn*3n<=2n*td&&tn*100n>51n*td);
assert(F[0].some((_,r)=>(k-j)*(F[1][r]-F[0][r])!==(j-i)*(F[2][r]-F[1][r])));

const run=args=>execFileSync(process.execPath,args,{stdio:'pipe',timeout:45000});
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'shallit-extension-test-'));
async function interrupt(args){return new Promise((resolve,reject)=>{const child=spawn(process.execPath,args,{stdio:['ignore','pipe','pipe']});child.stdout.resume();let log='',sent=false;
  const timer=setTimeout(()=>{child.kill('SIGKILL');reject(new Error('signal timeout'));},10000);
  child.stderr.on('data',bytes=>{log+=bytes;if(!sent&&/"event":"(?:start|resume)"/.test(log)){sent=true;child.kill('SIGTERM');}});
  child.on('error',error=>{clearTimeout(timer);reject(error);});child.on('close',(code,signal)=>{clearTimeout(timer);resolve({code,signal,log});});});}
try{
  const dir=path.join(temp,'producer'),out=path.join(temp,'producer.json'),producer=file('shallit_interval_extension.mjs');
  const args=[producer,'--radius-denominator','1000000','--seconds','20','--max-states','100000','--state-dir',dir,'--output',out];
  run([...args,'--max-states','2']);
  const partial=JSON.parse(fs.readFileSync(path.join(dir,'state.json'),'utf8'));assert.equal(partial.progress.nodes.length,2);validateProgress(partial.progress,[999998,2000000,1000002,2000000]);
  run(args);const golden=fs.readFileSync(file('checks/shallit-extension-1000000.json'),'utf8');assert.equal(fs.readFileSync(out,'utf8'),golden);
  run(args);assert.equal(fs.readFileSync(out,'utf8'),golden);
  assert.throws(()=>run([...args,'--radius-denominator','100']),/incompatible checkpoint/);
  const signalDir=path.join(temp,'signal'),signalOut=path.join(temp,'signal.json');
  const signalArgs=[producer,'--radius-denominator','1000000','--seconds','20','--state-dir',signalDir,'--output',signalOut];
  const stopped=await interrupt(signalArgs);assert.equal(stopped.code,130);assert.equal(stopped.signal,null);assert(stopped.log.includes('"event":"interrupted"'));
  validateProgress(JSON.parse(fs.readFileSync(path.join(signalDir,'state.json'),'utf8')).progress,[999998,2000000,1000002,2000000]);
  run(signalArgs);assert.equal(fs.readFileSync(signalOut,'utf8'),golden);
  const vDir=path.join(temp,'validator'),vOut=path.join(temp,'validator.json');
  const vArgs=[file('verify_shallit_interval_extension.mjs'),'--input',file('checks/shallit-extension-1000000.json'),'--state-dir',vDir,'--output',vOut];
  run([...vArgs,'--max-rows','1']);assert.equal(JSON.parse(fs.readFileSync(path.join(vDir,'state.json'),'utf8')).progress.row,1);
  const vStopped=await interrupt(vArgs);assert.equal(vStopped.code,130);assert.equal(vStopped.signal,null);assert(vStopped.log.includes('"event":"interrupted"'));
  run(vArgs);const vGolden=fs.readFileSync(vOut,'utf8');run(vArgs);assert.equal(fs.readFileSync(vOut,'utf8'),vGolden);
  for(const [d,a] of [[dir,args],[vDir,vArgs]]){
    const checkpoint=path.join(d,'state.json'),good=fs.readFileSync(checkpoint,'utf8'),bad=JSON.parse(good);
    bad.checksum='0'.repeat(64);fs.writeFileSync(checkpoint,JSON.stringify(bad));assert.throws(()=>run(a),/corrupt checkpoint/);
    const incompatible=JSON.parse(good);incompatible.identity.schema=99;fs.writeFileSync(checkpoint,JSON.stringify(incompatible));assert.throws(()=>run(a),/incompatible checkpoint/);
  }
  const site=fs.readFileSync(new URL('../../../viz/progress.html',import.meta.url),'utf8');
  const entries=site.match(/<article[^>]*id="basis-wider-interval"[^>]*>[\s\S]*?<\/article>/g);assert.equal(entries?.length,1);
  for(const text of ['49:51','51:49',sourceData.states.toLocaleString('en-US'),sourceData.testedTransitions.toLocaleString('en-US'),
    'does not cover the full','outside mathematical review','SHALLIT-INTERVAL-EXTENSION.md'])assert(entries[0].includes(text));
  console.log(JSON.stringify({status:'pass',independentFeasibilityComparisons:comparisons,clockIteratorComparisons:48,
    closedBoundaryAndLargeIntegerTests:true,syntheticCycleDetectorTest:true,cycleObservedInCandidate:false,
    producerAndValidatorResume:true,corruptAndConfigRejection:true,largeFrontierTripleReconstructedExactly:true}));
}finally{fs.rmSync(temp,{recursive:true,force:true});}
