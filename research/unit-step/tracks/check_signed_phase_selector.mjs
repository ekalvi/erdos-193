#!/usr/bin/env node
/** Independent, one-core, bounded exhaustive validator of q=1,2 SAT exclusions.
 * Uses direct two-block state words and displacement IDs, not a SAT solver.
 * Atomic per-q checkpoints resume validated completed work. Each q takes seconds.
 * Also checks a six-vector positive control and the saved SAT source identity.
 */
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const corners=[[0,0],[-1,0],[-1,1],[0,-1]];
const graphs=[[0,1],[1,2],[0,3],[2,3]];
const hash=text=>crypto.createHash('sha256').update(text).digest('hex');
function atomic(file,data) {
  fs.mkdirSync(path.dirname(file),{recursive:true});
  const tmp=`${file}.tmp`, fd=fs.openSync(tmp,'w');
  try {fs.writeFileSync(fd,JSON.stringify(data,null,2)+'\n');fs.fsyncSync(fd);} finally {fs.closeSync(fd);}
  fs.renameSync(tmp,file);
}
// Build actual finite state words, sum their unit directions, and tag vertices.
// No use of the Python model's rotated block-point formula.
export function tables(q,low) {
  const L=2**q,ids=new Map();
  const intern=Array.from({length:4},()=>Array.from({length:L},()=>[]));
  const boundary=Array.from({length:4},()=>Array.from({length:4},()=>Array.from({length:L},()=>[])));
  const label=v=>{const key=v.join(',');if(!ids.has(key))ids.set(key,ids.size);return ids.get(key);};
  const word=r=>Array.from({length:L},(_,j)=>{
    let s=r;
    for(let bit=0;bit<q;bit++)if(j&(1<<bit))s+=(low&(1<<bit))?-1:1;
    return (s%4+4)%4;
  });
  for(let r=0;r<4;r++)for(let s=0;s<4;s++) {
    let x=0,y=0;
    const points=[...word(r),...word(s)].map((a,n)=>{
      const p=[2*x+corners[a][0],2*y+corners[a][1],4*n+a];
      if(a===0)x++;else if(a===1)y++;else if(a===2)x--;else y--;
      return p;
    });
    for(let a=0;a<L;a++) {
      for(let b=a+1;b<L;b++)intern[r][a][b]=label(points[b].map((v,j)=>v-points[a][j]));
      for(let b=0;b<L;b++)boundary[r][s][a][b]=label(points[L+b].map((v,j)=>v-points[a][j]));
    }
  }
  return {intern,boundary,vectors:[...ids.keys()].map(key=>key.split(',').map(Number))};
}
export function audit(q) {
  const L=2**q;
  let checked=0, feasible=0;
  for(let low=0;low<L;low++) {
    const t=tables(q,low);
    const options=Array.from({length:4},(_,r)=>Array.from({length:2**L-1},(_,index)=>{
      const positions=Array.from({length:L},(_,j)=>j).filter(j=>(index+1)&(1<<j));
      return {first:positions[0],last:positions.at(-1),
        internal:positions.slice(1).map((b,j)=>t.intern[r][positions[j]][b])};
    }));
    for(const changes of graphs)for(const a of options[0])for(const b of options[1])
      for(const c of options[2])for(const d of options[3]) {
        checked++;
        const choices=[a,b,c,d],used=[];
        const add=id=>{if(!used.includes(id))used.push(id);return used.length<=5;};
        let ok=true;
        outer:for(let r=0;r<4;r++) {
          for(const id of choices[r].internal)if(!add(id)){ok=false;break outer;}
          for(const delta of changes) {
            const s=(r+delta)%4;
            if(!add(t.boundary[r][s][choices[r].last][choices[s].first])){ok=false;break outer;}
          }
        }
        if(ok)feasible++;
      }
  }
  assert.equal(checked,L*4*(2**L-1)**4);
  assert.equal(feasible,0);
  return {q,blockSize:L,lowSignCases:L,minimalTailGraphs:4,selectorAssignments:checked,
    atMostFiveVectorAssignments:feasible,status:'exhaustively-excluded-in-stated-class'};
}

function main() {
  if(process.argv.includes('--help')) {
    console.log('node research/unit-step/tracks/check_signed_phase_selector.mjs [--write]\n'
      +'Independent bounded q=1,2 enumeration; completed per-q checkpoints resume.\n'
      +'--write saves the independently checked exclusion counts and six-vector control.');return;
  }
  const codeSha256=hash(fs.readFileSync(fileURLToPath(import.meta.url)));
  const dir=`.checkpoint-signed-phase-check/${codeSha256}`;
  fs.mkdirSync(dir,{recursive:true});
  const log=(event,fields={})=>{
    const record={timestamp:new Date().toISOString(),event,...fields};
    fs.appendFileSync(`${dir}/run.jsonl`,JSON.stringify(record)+'\n');
    console.log(JSON.stringify(record));
  };
  log('start',{codeSha256,cores:1,total:2,checkpointDirectory:dir,estimatedSeconds:5});
  const results=[];
  for(const q of [1,2]) {
    const started=performance.now(),file=`${dir}/level-${q}.json`;
    let result;
    if(fs.existsSync(file)) {
      const saved=JSON.parse(fs.readFileSync(file,'utf8'));
      assert.equal(saved.codeSha256,codeSha256);
      assert.equal(saved.resultSha256,hash(JSON.stringify(saved.result)));
      assert.equal(saved.result.q,q);
      result=saved.result;log('resume',{q,completed:result.selectorAssignments});
    } else {
      result=audit(q);
      atomic(file,{codeSha256,resultSha256:hash(JSON.stringify(result)),result});
    }
    results.push(result);
    const elapsedSeconds=(performance.now()-started)/1000;
    log('level-complete',{...result,completed:q,total:2,elapsedSeconds,
      perSecond:result.selectorAssignments/elapsedSeconds,remainingSeconds:q===2?0:5,
      rssBytes:process.memoryUsage().rss});
  }
  const sat=JSON.parse(fs.readFileSync('research/unit-step/checks/signed-phase-selector.json','utf8'));
  assert.equal(sat.identity.sourceSha256,hash(fs.readFileSync('research/unit-step/tracks/signed_phase_selector.py')));
  assert.deepEqual(sat.results.map(r=>r.status),['unsat','unsat','unknown','unknown']);
  // Exact positive control: epsilon_0=+, alternating tail starting -.
  // Select both points in each length-two block; all eight tail edges occur.
  const t=tables(1,0),ids=new Set();
  for(let r=0;r<4;r++) {
    ids.add(t.intern[r][0][1]);
    for(const d of [2,3])ids.add(t.boundary[r][(r+d)%4][1][0]);
  }
  const six=[...ids].map(id=>t.vectors[id]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);
  assert.deepEqual(six,[[-1,-2,5],[-1,-1,2],[0,-1,1],[0,3,5],[1,0,5],[1,1,6]]);
  const output={schema:1,codeSha256,solverSourceSha256:sat.identity.sourceSha256,results,
    sixVectorControl:{lowSigns:[1],tailChanges:[2,3],positionsByTailState:[[0,1],[0,1],[0,1],[0,1]],menu:six}};
  if(process.argv.includes('--write'))atomic('research/unit-step/checks/signed-phase-independent.json',output);
  else assert.deepEqual(JSON.parse(fs.readFileSync('research/unit-step/checks/signed-phase-independent.json','utf8')),output);
  log('complete',{completed:2,total:2,remainingSeconds:0,sixVectorControlPassed:true});
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))main();
