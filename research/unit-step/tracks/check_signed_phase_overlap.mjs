#!/usr/bin/env node
/** Independent subset-mask reference for the 8-position exclusion.
 * Enumerates each block's 255 nonempty subsets, then combines complete subsets
 * in natural state order. It does not use the production search's endpoint-first
 * path generation, opposite-state ordering, or memoization. A pruned subtree
 * represents exactly 255^(remaining states) assignments, counted with BigInt.
 * One core; atomic/checksummed per-topology checkpoints, SIGINT/TERM between cases.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {setImmediate as yieldNow} from 'node:timers/promises';
import {tables} from './check_signed_phase_selector.mjs';
import {graphs} from './signed_phase_overlap.mjs';
const here=fileURLToPath(import.meta.url),hash=x=>crypto.createHash('sha256').update(x).digest('hex');
let stopped=false;
process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
function atomic(file,data) {
  fs.mkdirSync(path.dirname(file),{recursive:true});const tmp=`${file}.tmp`,fd=fs.openSync(tmp,'w');
  try{fs.writeFileSync(fd,JSON.stringify(data)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  fs.renameSync(tmp,file);
}
export function reference(q,low,graph) {
  const L=2**q,N=2**L-1,t=tables(q,low),changes=graphs[graph];
  const options=Array.from({length:4},(_,r)=>Array.from({length:N},(_,index)=>{
    const selected=Array.from({length:L},(_,j)=>j).filter(j=>(index+1)&(1<<j));
    const internal=[...new Set(selected.slice(1).map((b,j)=>t.intern[r][selected[j]][b]))];
    return {first:selected[0],last:selected.at(-1),internal};
  }));
  const chosen=[],used=[];
  let visits=0,leaves=0,covered=0n;
  const subtree=[0,1,2,3].map(r=>BigInt(N)**BigInt(3-r));
  const add=id=>{if(used.includes(id))return true;if(used.length===5)return false;used.push(id);return true;};
  function assign(r) {
    for(const option of options[r]) {
      visits++;
      const mark=used.length;chosen[r]=option;
      let valid=option.internal.every(add);
      if(valid)for(const d of changes) {
        const s=(r+d)%4;
        if(s<=r&&!add(t.boundary[r][s][option.last][chosen[s].first])){valid=false;break;}
        const p=(r-d+4)%4;
        if(p<r&&!add(t.boundary[p][r][chosen[p].last][option.first])){valid=false;break;}
      }
      if(!valid)covered+=subtree[r];
      else if(r===3){covered++;leaves++;}
      else assign(r+1);
      used.length=mark;
    }
  }
  assign(0);
  assert.equal(covered,BigInt(N)**4n);
  assert.equal(leaves,0,`unexpected <=5-vector selector at q=${q}, low=${low}, graph=${graph}`);
  return {q,low,graph,assignmentsCovered:covered.toString(),visitedPartialAssignments:visits,
    fiveVectorSelectors:leaves,status:'unsat'};
}
async function main() {
  const q=Number(process.argv[process.argv.indexOf('--q')+1]||3);
  if(process.argv.includes('--help')){console.log('node research/unit-step/tracks/check_signed_phase_overlap.mjs --q 3 [--write]\n'
    +'Bounded independent q<=3 subset-mask reference. Completed sign/graph cases resume.');return;}
  const level=process.argv.includes('--q')?q:3;
  if(!Number.isInteger(level)||level<1||level>3)throw Error('--q must be 1..3');
  const identity={schema:1,sourceSha256:hash(fs.readFileSync(here)),q:level,
    tablesSha256:hash(fs.readFileSync(new URL('./check_signed_phase_selector.mjs',import.meta.url))),
    overlapSha256:hash(fs.readFileSync(new URL('./signed_phase_overlap.mjs',import.meta.url)))};
  const root=`.checkpoint-signed-phase-reference/${hash(JSON.stringify(identity))}`;
  fs.mkdirSync(root,{recursive:true});
  const log=(event,fields={})=>{const row={timestamp:new Date().toISOString(),event,...fields};
    fs.appendFileSync(`${root}/run.jsonl`,JSON.stringify(row)+'\n');console.log(JSON.stringify(row));};
  const started=performance.now(),total=2**level*4,rows=[];
  log('start',{identity,cores:1,total,checkpointDirectory:root,estimatedSeconds:60});
  for(let low=0;low<2**level;low++)for(let g=0;g<4;g++) {
    await yieldNow();if(stopped){log('interrupted',{completed:rows.length,total});process.exitCode=130;return;}
    const file=`${root}/${low}-${g}.json`;let result;
    if(fs.existsSync(file)) {
      const saved=JSON.parse(fs.readFileSync(file,'utf8'));
      assert.equal(saved.resultSha256,hash(JSON.stringify(saved.result)));
      assert.equal(JSON.stringify(saved.identity),JSON.stringify(identity));
      result=saved.result;assert.equal(result.low,low);assert.equal(result.graph,g);assert.equal(result.q,level);
    } else {
      result=reference(level,low,g);
      atomic(file,{identity,resultSha256:hash(JSON.stringify(result)),result});
    }
    rows.push(result);
    const elapsedSeconds=(performance.now()-started)/1000;
    log('progress',{completed:rows.length,total,low,graph:g,elapsedSeconds,perSecond:rows.length/elapsedSeconds,
      remainingSeconds:elapsedSeconds/rows.length*(total-rows.length),rssBytes:process.memoryUsage().rss});
  }
  const result={identity,status:'unsat',scope:'fixed tags; nonempty dyadic block selection by tail state',
    assignmentsCovered:rows.reduce((n,r)=>n+BigInt(r.assignmentsCovered),0n).toString(),
    visitedPartialAssignments:rows.reduce((n,r)=>n+r.visitedPartialAssignments,0),rows};
  if(process.argv.includes('--write'))atomic(`research/unit-step/checks/signed-phase-reference-${2**level}.json`,result);
  log('complete',{status:'unsat',completed:rows.length,total,assignmentsCovered:result.assignmentsCovered,
    visitedPartialAssignments:result.visitedPartialAssignments,elapsedSeconds:(performance.now()-started)/1000,remainingSeconds:0});
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===path.resolve(process.argv[1]))await main();
