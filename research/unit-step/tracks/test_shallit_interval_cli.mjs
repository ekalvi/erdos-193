#!/usr/bin/env node
// Bounded restart regressions in owned temporary storage. No network or server.
import assert from 'node:assert/strict';
import {execFileSync,spawn} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateProgress as validateInterval} from './shallit_interval_automaton.mjs';
import {validateProgress as validateMidpoint} from './shallit_midpoint_certificate.mjs';
const file=name=>fileURLToPath(new URL(name,import.meta.url));
const run=args=>execFileSync(process.execPath,args,{stdio:'pipe',timeout:20000});
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'shallit-interval-cli-'));
async function interrupt(args){return new Promise((resolve,reject)=>{
  const child=spawn(process.execPath,args,{stdio:['ignore','pipe','pipe']});child.stdout.resume();let log='',signaled=false;
  const timeout=setTimeout(()=>{child.kill('SIGKILL');reject(new Error('interrupt timeout'));},10000);
  child.stderr.on('data',data=>{log+=data;if(!signaled&&log.includes('"event":"start"')){signaled=true;child.kill('SIGTERM');}});
  child.on('error',error=>{clearTimeout(timeout);reject(error);});
  child.on('close',(code,signal)=>{clearTimeout(timeout);resolve({code,signal,log});});
});}
try{
  const probe=file('shallit_interval_automaton.mjs'),midpoint=file('shallit_midpoint_certificate.mjs'),validator=file('verify_shallit_midpoint.mjs');
  const expectedInterval=fs.readFileSync(file('checks/shallit-interval-attempt.json'),'utf8');
  const expectedMidpoint=fs.readFileSync(file('checks/shallit-midpoint.json'),'utf8');
  const expectedValidation=fs.readFileSync(file('checks/shallit-midpoint-validation.json'),'utf8');
  const aDir=path.join(temporary,'affine'),aOut=path.join(temporary,'affine.json');
  const aArgs=[probe,'--seconds','10','--max-states','20000','--state-dir',aDir,'--output',aOut];
  run([...aArgs,'--max-span','1']);
  const early=JSON.parse(fs.readFileSync(path.join(aDir,'state.json'),'utf8'));
  assert.equal(early.progress.status,'running');assert(early.progress.edge>0);validateInterval(early.progress,[1,3,2,3]);
  run(aArgs);assert.equal(fs.readFileSync(aOut,'utf8'),expectedInterval);
  const signalDir=path.join(temporary,'affine-signal'),signalOut=path.join(temporary,'affine-signal.json');
  const signalArgs=[probe,'--seconds','10','--max-states','20000','--state-dir',signalDir,'--output',signalOut];
  const interrupted=await interrupt(signalArgs);assert.equal(interrupted.code,130);assert.equal(interrupted.signal,null);
  assert(interrupted.log.includes('"event":"interrupted"'));
  const signalState=JSON.parse(fs.readFileSync(path.join(signalDir,'state.json'),'utf8'));
  validateInterval(signalState.progress,[1,3,2,3]);run(signalArgs);assert.equal(fs.readFileSync(signalOut,'utf8'),expectedInterval);

  const mDir=path.join(temporary,'midpoint'),mOut=path.join(temporary,'midpoint.json');
  const mArgs=[midpoint,'--seconds','10','--max-states','100000','--state-dir',mDir,'--output',mOut];
  run([...mArgs,'--max-states','2']);
  const partial=JSON.parse(fs.readFileSync(path.join(mDir,'state.json'),'utf8'));
  assert.equal(partial.progress.cursor,1);validateMidpoint(partial.progress);
  run(mArgs);assert.equal(fs.readFileSync(mOut,'utf8'),expectedMidpoint);
  run(mArgs);assert.equal(fs.readFileSync(mOut,'utf8'),expectedMidpoint);
  const mSignal=path.join(temporary,'midpoint-signal'),mSignalOut=path.join(temporary,'midpoint-signal.json');
  const mSignalArgs=[midpoint,'--seconds','10','--state-dir',mSignal,'--output',mSignalOut];
  const mStopped=await interrupt(mSignalArgs);assert.equal(mStopped.code,130);assert.equal(mStopped.signal,null);
  assert(mStopped.log.includes('"event":"interrupted"'));
  validateMidpoint(JSON.parse(fs.readFileSync(path.join(mSignal,'state.json'),'utf8')).progress);
  run(mSignalArgs);assert.equal(fs.readFileSync(mSignalOut,'utf8'),expectedMidpoint);

  const vDir=path.join(temporary,'validator'),vOut=path.join(temporary,'validator.json');
  const vArgs=[validator,'--state-dir',vDir,'--output',vOut];
  const vStopped=await interrupt(vArgs);assert.equal(vStopped.code,130);assert.equal(vStopped.signal,null);
  assert(vStopped.log.includes('"event":"interrupted"'));
  run(vArgs);assert.equal(fs.readFileSync(vOut,'utf8'),expectedValidation);
  run(vArgs);assert.equal(fs.readFileSync(vOut,'utf8'),expectedValidation);

  for(const [directory,args] of [[aDir,aArgs],[mDir,mArgs],[vDir,vArgs]]){
    const checkpoint=path.join(directory,'state.json'),good=fs.readFileSync(checkpoint,'utf8'),bad=JSON.parse(good);
    bad.checksum='0'.repeat(64);fs.writeFileSync(checkpoint,JSON.stringify(bad));assert.throws(()=>run(args),/corrupt checkpoint/);
    const incompatible=JSON.parse(good);incompatible.identity.schema=999;
    fs.writeFileSync(checkpoint,JSON.stringify(incompatible));assert.throws(()=>run(args),/incompatible checkpoint/);
    fs.writeFileSync(checkpoint,good);
  }
  const site=fs.readFileSync(new URL('../../../viz/progress.html',import.meta.url),'utf8');
  const entries=site.match(/<article[^>]*id="basis-uniform-neighborhood"[^>]*>[\s\S]*?<\/article>/g);
  assert.equal(entries?.length,1);
  for(const phrase of ['2557199/2557201','2557201/2557199','very narrow','not the full','outside mathematical review','SHALLIT-UNIFORM-NEIGHBORHOOD.md'])assert(entries[0].includes(phrase));
  console.log('PASS: symbolic digit-cursor/span-budget resume; midpoint state-budget resume;\n'
    +'all three SIGTERM recoveries; identical completed artifacts; corrupt/config rejection; scoped site link.');
}finally{fs.rmSync(temporary,{recursive:true,force:true});}
