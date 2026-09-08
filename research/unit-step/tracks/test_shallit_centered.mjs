#!/usr/bin/env node
// Bounded exact regressions and executable examples for the direction reduction.
import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {execFileSync,spawn} from 'node:child_process';import {fileURLToPath} from 'node:url';
import {VECTORS,ROOT,norm,directChild,transitionFactory,key,validateProgress} from './shallit_centered_returns.mjs';
import {M,prefixAt,IMAGE} from './shallit_ratio_automaton.mjs';
const file=name=>fileURLToPath(new URL(name,import.meta.url));
assert.equal(VECTORS.length,161);let pairs=0;for(const X of VECTORS)for(const Y of VECTORS)if(norm(X.map((x,r)=>x-Y[r]))<=95)pairs++;assert.equal(pairs,10171);
const rows=[ROOT];for(let i=0;i<30;i++)rows.push([3,i%5,(3*i)%5,(7*i)%161,(11*i)%161]);
const edgesFor=transitionFactory();
for(const s of rows){const brute=[];for(let x=0;x<14;x++)for(let y=0;y<14;y++)for(let z=0;z<14;z++){const t=directChild(s,[x,y,z]);if(t)brute.push(`${x},${y},${z}:${key(t)}`);}
  assert.deepEqual(edgesFor(s).edges.map(e=>`${e.digits}:${key(e.state)}`).sort(),brute.sort());}
const certificate=JSON.parse(fs.readFileSync(file('checks/shallit-centered-returns.json'),'utf8')),stateKeys=new Set(certificate.closedStates.map(key));
const vectorIndex=new Map(VECTORS.map((v,i)=>[v.join(','),i]));
function letter(n){let s=0;while(n){s+=IMAGE[Number(n%14n)];n/=14n;}return s%5;}
// One exact state represents infinitely many substituted balanced-pair families.
for(const r of [0,1,2,3,4,5,6,7,8,20,100]){
  const q=14n**BigInt(r),indices=[52n*q,57n*q,57n*q+1n],F=indices.map(prefixAt);
  const X=F[1].map((x,j)=>5n*(x-F[0][j])-(indices[1]-indices[0]));
  const Y=F[2].map((x,j)=>5n*(x-F[0][j])-(indices[2]-indices[0]));
  assert.deepEqual(X,Array(5).fill(0n));assert.deepEqual(Y,[-1n,-1n,-1n,-1n,4n]);
  assert.deepEqual(indices.map(letter),[0,4,0]);
  const s=[3,4,0,vectorIndex.get(X.join(',')),vectorIndex.get(Y.join(','))];assert(stateKeys.has(key(s)));
}
// The literal affine guard necessarily retains infinitely many unit-gap states.
for(const n of [2n,3n,14n,196n,38416n,10n**20n]){
  const F=prefixAt(n),E=F.map((x,r)=>x-(r===0?n:0n)),square=E.reduce((a,b)=>a+b*b,0n);
  assert.equal(F.reduce((a,b)=>a+b,0n),n);assert(square>0n&&square<2n*n*n);
  for(let d=14n;d<=n;d*=14n){const G=prefixAt(n/d);assert(G.reduce((a,b)=>a+b*b,0n)<=n*n/(d*d));}
}
// A modular permutation example for the unbounded nonuniform-gcd lemma.
const modulus=3;let residue=[0,0,0,0,0],symbol=0,period=0;
do{residue=M.map((row,r)=>(row.reduce((sum,x,j)=>sum+x*residue[j],0)+Number(r===symbol))%modulus);symbol=(symbol+1)%5;period++;
  assert(period<=5*modulus**5);}while(symbol||residue.some(x=>x));
assert.equal(period,40);const n=(14n**BigInt(period)-1n)/13n,F=prefixAt(n),gcd=(a,b)=>b?gcd(b,a%b):a;
assert(F.every(x=>x>0n&&x%3n===0n)&&F.some(x=>x!==F[0]));assert.equal(F.reduce(gcd),615n);

const temp=fs.mkdtempSync(path.join(os.tmpdir(),'shallit-centered-test-')),run=args=>execFileSync(process.execPath,args,{stdio:'pipe',timeout:20000});
async function interrupt(args){return new Promise((resolve,reject)=>{const child=spawn(process.execPath,args,{stdio:['ignore','pipe','pipe']});child.stdout.resume();let log='',sent=false;
  const timer=setTimeout(()=>{child.kill('SIGKILL');reject(new Error('signal timeout'));},10000);
  child.stderr.on('data',bytes=>{log+=bytes;if(!sent&&/"event":"(?:start|resume)"/.test(log)){sent=true;child.kill('SIGTERM');}});
  child.on('error',error=>{clearTimeout(timer);reject(error);});child.on('close',(code,signal)=>{clearTimeout(timer);resolve({code,signal,log});});});}
try{
  const dir=path.join(temp,'producer'),out=path.join(temp,'producer.json'),args=[file('shallit_centered_returns.mjs'),'--state-dir',dir,'--output',out];
  run([...args,'--max-states','2']);const p=JSON.parse(fs.readFileSync(path.join(dir,'state.json'),'utf8')).progress;assert.equal(p.cursor,1);validateProgress(p);
  run(args);const golden=fs.readFileSync(file('checks/shallit-centered-returns.json'),'utf8');assert.equal(fs.readFileSync(out,'utf8'),golden);
  run(args);assert.equal(fs.readFileSync(out,'utf8'),golden);
  const sDir=path.join(temp,'signal'),sOut=path.join(temp,'signal.json'),sArgs=[file('shallit_centered_returns.mjs'),'--state-dir',sDir,'--output',sOut];
  const stopped=await interrupt(sArgs);assert.equal(stopped.code,130);assert.equal(stopped.signal,null);assert(stopped.log.includes('"event":"interrupted"'));
  validateProgress(JSON.parse(fs.readFileSync(path.join(sDir,'state.json'),'utf8')).progress);run(sArgs);assert.equal(fs.readFileSync(sOut,'utf8'),golden);
  const vDir=path.join(temp,'validator'),vOut=path.join(temp,'validator.json'),vArgs=[file('verify_shallit_centered_returns.mjs'),'--state-dir',vDir,'--output',vOut];
  run([...vArgs,'--max-units','1']);assert.equal(JSON.parse(fs.readFileSync(path.join(vDir,'state.json'),'utf8')).progress.row,1);
  const vStopped=await interrupt(vArgs);assert.equal(vStopped.code,130);assert.equal(vStopped.signal,null);assert(vStopped.log.includes('"event":"interrupted"'));
  run(vArgs);const expected=fs.readFileSync(file('checks/shallit-centered-validation.json'),'utf8');assert.equal(fs.readFileSync(vOut,'utf8'),expected);
  run(vArgs);assert.equal(fs.readFileSync(vOut,'utf8'),expected);
  for(const [directory,a] of [[dir,args],[vDir,vArgs]]){
    const checkpoint=path.join(directory,'state.json'),good=fs.readFileSync(checkpoint,'utf8'),bad=JSON.parse(good);
    bad.checksum='0'.repeat(64);fs.writeFileSync(checkpoint,JSON.stringify(bad));assert.throws(()=>run(a),/corrupt checkpoint/);
    const incompatible=JSON.parse(good);incompatible.identity.schema=99;fs.writeFileSync(checkpoint,JSON.stringify(incompatible));assert.throws(()=>run(a),/incompatible checkpoint/);
  }
  const site=fs.readFileSync(new URL('../../../viz/progress.html',import.meta.url),'utf8');
  const entries=site.match(/<article[^>]*id="basis-direction-reduction"[^>]*>[\s\S]*?<\/article>/g);assert.equal(entries?.length,1);
  for(const text of ['3,691','every position, length, and gap ratio','missing a letter','nonuniform','does not establish full 5D',
    'Outside mathematical review','SHALLIT-DIRECTION-REDUCTION.md'])assert(entries[0].includes(text));
  console.log(JSON.stringify({status:'pass',latticeVectors:161,compatiblePairs:10171,transitionRows:rows.length,
    balancedFamilySampleExponents:[0,1,2,3,4,5,6,7,8,20,100],unitGapGuardSamples:6,nonuniformGcdExample:{modulus,period,gcd:615},
    producerAndValidatorResume:true,corruptAndConfigRejection:true,scope:'Regression checks accompany written infinite lemmas; samples alone do not prove them.'}));
}finally{fs.rmSync(temp,{recursive:true,force:true});}
