// Bounded CLI regressions: fresh and resumed counterexamples must fail closed.
// Each test owns a tiny temporary checkpoint directory; no repository checkpoint
// is changed. Runs are sequential and safely rerunnable after interruption.
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtempSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';

const checker=fileURLToPath(new URL('./return-blocks-gap-check.mjs',import.meta.url));
function run(cwd,gap,prefix,status){
  const result=spawnSync(process.execPath,
    ['--single-threaded','--v8-pool-size=1',checker,String(gap),String(prefix)],
    {cwd,encoding:'utf8',timeout:10000});
  assert.ifError(result.error);
  assert.equal(result.signal,null);
  assert.equal(result.status,status,result.stdout+result.stderr);
  return result.stdout.trim().split('\n').map(line=>JSON.parse(line));
}
function isolated(fn){
  const cwd=mkdtempSync(join(tmpdir(),'return-blocks-gap-exit-'));
  try{fn(cwd);}finally{rmSync(cwd,{recursive:true,force:true});}
}

for(const [gap,prefix] of [[1,2],[2,3]]){
  test(`counterexample exits 2 on fresh and resumed runs: gap=${gap}, prefix=${prefix}`,()=>isolated(cwd=>{
    const fresh=run(cwd,gap,prefix,2);
    assert.equal(fresh.at(-1).event,'result');
    const found=fresh.at(-1).found;
    assert.deepEqual(found.route,Array.from({length:prefix+1},(_,n)=>n));
    const checkpoint=JSON.parse(readFileSync(join(cwd,fresh[0].checkpoint),'utf8'));
    assert.deepEqual(checkpoint.found,found,'counterexample must be saved before failure');
    assert.equal(checkpoint.starts.length,1);
    const resumed=run(cwd,gap,prefix,2);
    assert.equal(resumed.at(-1).event,'resume-complete');
    assert.deepEqual(resumed.at(-1).found,found);
    assert.deepEqual(resumed.at(-1).starts,checkpoint.starts);
  }));
}

test('no-path result exits 0 on fresh and resumed runs',()=>isolated(cwd=>{
  const fresh=run(cwd,1,16,0),result=fresh.at(-1);
  assert.equal(result.event,'result');
  assert.equal(result.found,null);
  assert.equal(result.starts.length,1);
  assert(result.maxReach<16);
  const resumed=run(cwd,1,16,0);
  assert.equal(resumed.at(-1).event,'resume-complete');
  assert.equal(resumed.at(-1).found,null);
  assert.deepEqual(resumed.at(-1).starts,result.starts);
}));
