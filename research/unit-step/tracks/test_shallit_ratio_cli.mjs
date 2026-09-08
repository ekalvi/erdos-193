#!/usr/bin/env node
// Bounded interruption/resume regression tests in owned temporary directories.
import assert from 'node:assert/strict';
import {execFileSync,spawn} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateProgress} from './shallit_ratio_automaton.mjs';

const probe=fileURLToPath(new URL('shallit_ratio_automaton.mjs',import.meta.url));
const validator=fileURLToPath(new URL('check_shallit_ratio_automaton.mjs',import.meta.url));
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'shallit-ratio-cli-'));
const run=args=>execFileSync(process.execPath,args,{stdio:'pipe',timeout:20000});
async function interrupt(args) {
  return new Promise((resolve,reject)=>{
    const child=spawn(process.execPath,args,{stdio:['ignore','pipe','pipe']});
    let output='',signaled=false;
    const timeout=setTimeout(()=>{child.kill('SIGKILL');reject(new Error('interrupt test timeout'));},10000);
    child.stdout.resume();
    child.stderr.on('data',data=>{
      output+=data;
      if(!signaled&&output.includes('"event":"start"')){signaled=true;child.kill('SIGTERM');}
    });
    child.on('error',error=>{clearTimeout(timeout);reject(error);});
    child.on('close',(code,signal)=>{clearTimeout(timeout);resolve({code,signal,output});});
  });
}
try {
  // Pause after a completed root expansion, then resume to the exact saved invariant.
  const state=path.join(temporary,'budget'), output=path.join(temporary,'budget-result.json');
  const args=[probe,'--left','1','--right','1','--seconds','10','--state-dir',state,'--output',output];
  run([...args,'--max-states','2']);
  const paused=JSON.parse(fs.readFileSync(path.join(state,'state.json'),'utf8'));
  assert.equal(paused.progress.cursor,1);assert.equal(paused.progress.status,'running');
  validateProgress(paused.progress,1,1);
  run([...args,'--max-states','100000']);
  const expected=fs.readFileSync(new URL('checks/shallit-ratio-1-1.json',import.meta.url),'utf8');
  assert.equal(fs.readFileSync(output,'utf8'),expected);
  run(args);assert.equal(fs.readFileSync(output,'utf8'),expected);

  const signalState=path.join(temporary,'signal'),signalOutput=path.join(temporary,'signal-result.json');
  const signalArgs=[probe,'--left','1','--right','2','--seconds','10','--state-dir',signalState,'--output',signalOutput];
  const stopped=await interrupt(signalArgs);
  assert.equal(stopped.code,130);assert.equal(stopped.signal,null);assert(stopped.output.includes('"event":"interrupted"'));
  const checkpoint=path.join(signalState,'state.json'),saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));
  assert.equal(saved.progress.status,'running');validateProgress(saved.progress,1,2);
  run(signalArgs);
  assert.equal(fs.readFileSync(signalOutput,'utf8'),fs.readFileSync(new URL('checks/shallit-ratio-1-2.json',import.meta.url),'utf8'));
  const good=fs.readFileSync(checkpoint,'utf8'),corrupt=JSON.parse(good);corrupt.checksum='0'.repeat(64);
  fs.writeFileSync(checkpoint,JSON.stringify(corrupt));
  assert.throws(()=>run(signalArgs),/corrupt checkpoint/);
  fs.writeFileSync(checkpoint,good);
  assert.throws(()=>run([...signalArgs,'--right','3']),/incompatible checkpoint/);

  const checkState=path.join(temporary,'validation'),checkOutput=path.join(temporary,'validation-result.json');
  const checkArgs=[validator,'--state-dir',checkState,'--output',checkOutput];
  const checkStopped=await interrupt(checkArgs);
  assert.equal(checkStopped.code,130);assert.equal(checkStopped.signal,null);
  assert(checkStopped.output.includes('"event":"interrupted"'));
  run(checkArgs);
  const checked=fs.readFileSync(checkOutput,'utf8');
  assert.equal(checked,fs.readFileSync(new URL('checks/shallit-ratio-validation.json',import.meta.url),'utf8'));
  run(checkArgs);assert.equal(fs.readFileSync(checkOutput,'utf8'),checked);
  const checkCheckpoint=path.join(checkState,'state.json');
  const bad=JSON.parse(fs.readFileSync(checkCheckpoint,'utf8'));bad.checksum='0'.repeat(64);
  fs.writeFileSync(checkCheckpoint,JSON.stringify(bad));
  assert.throws(()=>run(checkArgs),/corrupt validator checkpoint/);
  const site=fs.readFileSync(new URL('../../../viz/progress.html',import.meta.url),'utf8');
  const entry=site.match(/<article[^>]*id="basis-ratio-certificates"[^>]*>[\s\S]*?<\/article>/g);
  assert.equal(entry?.length,1);
  for(const phrase of ['1:1, 1:2, and 2:1','Arbitrary ratios remain unresolved',
    'awaits outside mathematical review','not Lean-formalized','SHALLIT-RATIO-DESCENT.md'])assert(entry[0].includes(phrase));
  assert(fs.statSync(new URL('SHALLIT-RATIO-DESCENT.md',import.meta.url)).isFile());
  console.log('PASS: bounded-state pause/resume; producer and validator SIGTERM recovery;\n'
    +'byte-identical completed resumes; corrupt/config checkpoint rejection; static site scope/link.');
} finally {
  fs.rmSync(temporary,{recursive:true,force:true});
}
