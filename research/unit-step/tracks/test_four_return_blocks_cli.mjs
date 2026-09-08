#!/usr/bin/env node
// Bounded regression: custom state isolation, concurrent runs, and safe resumes.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFile, spawnSync} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';

const audit=fileURLToPath(new URL('four_return_blocks.mjs',import.meta.url));
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'four-return-cli-'));
const options={cwd:temporary,encoding:'utf8',timeout:20000,
  env:{...process.env,OMP_NUM_THREADS:'1',OPENBLAS_NUM_THREADS:'1',
    MKL_NUM_THREADS:'1',NUMEXPR_NUM_THREADS:'1',UV_THREADPOOL_SIZE:'1'}};
const run=(...args)=>spawnSync(process.execPath,[audit,...args],options);
const success=(...args)=>{
  const result=run(...args);
  assert.ifError(result.error);
  assert.equal(result.status,0,result.stderr);
  return result;
};
const read=file=>fs.readFileSync(file,'utf8');
try {
  const defaultDirectory=path.join(temporary,'.checkpoint-four-return-blocks');
  fs.mkdirSync(defaultDirectory);
  const stale=JSON.stringify({identity:{schema:'deliberately incompatible'},progress:{}});
  const defaultState=path.join(defaultDirectory,'state.json');
  const defaultLog=path.join(defaultDirectory,'run.jsonl');
  fs.writeFileSync(defaultState,stale);
  fs.writeFileSync(defaultLog,'untouched default log\n');
  assert.match(run().stderr,/incompatible checkpoint/);

  // Separate custom directories must work despite stale default state, including
  // concurrent invocations. All children inherit the harness's single-CPU pin.
  const execute=promisify(execFile);
  const results=await Promise.allSettled(['state a','state b'].map(directory=>
    execute(process.execPath,[audit,'--state-dir',directory],options)));
  for(const result of results)assert.equal(result.status,'fulfilled',String(result.reason));
  const a=path.join(temporary,'state a'),b=path.join(temporary,'state b');
  for(const directory of [a,b]) {
    const saved=JSON.parse(read(path.join(directory,'state.json')));
    assert.deepEqual(saved.progress,{row:117,pairsChecked:13689,compatiblePairs:7164});
    const events=read(path.join(directory,'run.jsonl')).trim().split('\n').map(JSON.parse);
    assert.equal(events[0].event,'start');
    assert.equal(events.at(-1).event,'complete');
    assert(events.every(event=>event.checkpoint===path.join(directory,'state.json')));
  }
  const completed=read(path.join(a,'state.json'));
  assert.equal(read(path.join(b,'state.json')),completed);
  const bLog=read(path.join(b,'run.jsonl'));
  assert.match(success('--state-dir',a).stderr,/"event":"resume"/);
  assert.equal(read(path.join(a,'state.json')),completed);
  assert.equal(read(path.join(b,'run.jsonl')),bLog);

  const corrupt=JSON.parse(completed);
  corrupt.checksum='invalid checksum';
  fs.writeFileSync(path.join(a,'state.json'),JSON.stringify(corrupt));
  const failed=run('--state-dir',a);
  assert.notEqual(failed.status,0);
  assert.match(failed.stderr,/corrupt checkpoint/);
  success('--state-dir',b);
  success('--state-dir','fresh replacement');
  assert.equal(read(path.join(a,'state.json')),JSON.stringify(corrupt));
  assert.equal(read(defaultState),stale);
  assert.equal(read(defaultLog),'untouched default log\n');

  assert.match(success('--help').stdout,/--state-dir DIR/);
  for(const args of [['--state-dir'],['--state-dir',''],['--unknown'],['unexpected']])
    assert.notEqual(run(...args).status,0);
  const harness=read(new URL('check_uniform_checkpoint.sh',import.meta.url));
  assert(harness.includes('run node "$track/four_return_blocks.mjs" --state-dir "$state/four-return"'));
  console.log('PASS: stale default untouched; concurrent custom states isolated; completed resume; corruption isolation; fresh replacement; CLI and harness forwarding.');
} finally {
  fs.rmSync(temporary,{recursive:true,force:true});
}
