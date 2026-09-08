#!/usr/bin/env node
/** Exact finite quotient of ALL infinite binary +/- sign streams.
 * Three low sign bits make an eight-letter block containing every state.
 * Its return words therefore depend only on those bits and the tail's exact
 * adjacent-change set. No enumeration of long periodic words is needed.
 * Single-core, bounded calculation; atomic result + identity-checked resume.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

export const directions = [[1,0],[0,1],[-1,0],[0,-1]];
export const cambie = [[0,0,0],[-1,0,1],[-1,1,2],[0,-1,3]];
const mod4 = x => ((x % 4) + 4) % 4;
export function block(signs, state = 0) {
  return Array.from({length: 2 ** signs.length}, (_, n) => {
    let s = state;
    for (let j = 0; j < signs.length; j++) if (n & (2 ** j)) s += signs[j];
    return mod4(s);
  });
}

// Find a lasso realizing exactly D. Vertex: prefix sign sum mod 4, seen D.
// Once all D has appeared, an allowed directed cycle completes an infinite
// stream. The returned prefix/cycle is independently replayable evidence.
export function changeWitness(mask) {
  function edges(p) {
    return [1,-1].filter(e => mask & (1 << mod4(e-p)))
      .map(e => ({e, p: mod4(p+e), bit: 1 << mod4(e-p)}));
  }
  function cycleFrom(start) {
    const queue = [{p:start, word:[]}], seen = new Set([start]);
    for (let at=0; at<queue.length; at++) {
      const {p,word} = queue[at];
      for (const edge of edges(p)) {
        const next = [...word, edge.e];
        if (edge.p === start) return next;
        if (!seen.has(edge.p)) { seen.add(edge.p); queue.push({p:edge.p, word:next}); }
      }
    }
    return null;
  }
  const queue = [{p:0, seen:0, word:[]}], visited = new Set(['0:0']);
  for (let at=0; at<queue.length; at++) {
    const item = queue[at];
    if (item.seen === mask) {
      const cycle = cycleFrom(item.p);
      if (cycle) return {prefix:item.word, cycle};
    }
    for (const edge of edges(item.p)) {
      const seen = item.seen | edge.bit, key = `${edge.p}:${seen}`;
      if (!visited.has(key)) {
        visited.add(key);
        queue.push({p:edge.p, seen, word:[...item.word,edge.e]});
      }
    }
  }
  return null;
}

export function returnTypes(signs, changeMask, selectMask) {
  const types = new Map();
  for (let r=0; r<4; r++) for (let d=0; d<4; d++) {
    if (!(changeMask & (1 << d))) continue;
    const word = [...block(signs,r), ...block(signs,mod4(r+d))];
    let last = -1;
    for (let k=0; k<word.length; k++) if (selectMask & (1 << word[k])) {
      if (last >= 0) {
        const letters = word.slice(last,k), a=letters[0], b=word[k];
        let x=0,y=0;
        for (const s of letters) { x+=directions[s][0]; y+=directions[s][1]; }
        const type = {a,b,x,y,length:letters.length};
        const key = [a,b,x,y,letters.length].join(',');
        if (!types.has(key)) types.set(key,{...type,word:letters});
      }
      last=k;
    }
  }
  return [...types.values()].sort((a,b) =>
    a.a-b.a || a.b-b.b || a.length-b.length || a.x-b.x || a.y-b.y);
}
export function menu(types, tags=cambie) {
  const result = new Map();
  for (const t of types) {
    const v=[2*t.x,2*t.y,4*t.length].map((v,j)=>v+tags[t.b][j]-tags[t.a][j]);
    const key=v.join(',');
    if (!result.has(key)) result.set(key,{vector:v,types:[]});
    result.get(key).types.push(t);
  }
  return [...result.values()];
}
function atomic(file, value) {
  fs.mkdirSync(path.dirname(file),{recursive:true});
  const tmp=`${file}.tmp`;
  const fd=fs.openSync(tmp,'w');
  try { fs.writeFileSync(fd,JSON.stringify(value)+'\n'); fs.fsyncSync(fd); }
  finally { fs.closeSync(fd); }
  fs.renameSync(tmp,file);
}
export function calculate() {
  const changes=[];
  for(let mask=1;mask<16;mask++) {
    const witness=changeWitness(mask);
    if (witness) changes.push({mask,changes:[0,1,2,3].filter(d=>mask&(1<<d)),witness});
  }
  const rows=[];
  for(let low=0;low<8;low++) {
    const signs=[0,1,2].map(j=>low&(1<<j)?-1:1);
    for (const change of changes) for(let select=1;select<16;select++) {
      const types=returnTypes(signs,change.mask,select);
      const vectors=menu(types);
      const byEndpoints={};
      for(const t of types) byEndpoints[`${t.a}${t.b}`]=(byEndpoints[`${t.a}${t.b}`]??0)+1;
      rows.push({lowSigns:signs,tailChangeMask:change.mask,selectMask:select,
        returnTypeCount:types.length,stepCount:vectors.length,
        endpointLowerBound:Math.max(...Object.values(byEndpoints)),
        maxGap:Math.max(...types.map(t=>t.length))});
    }
  }
  const minimum=Math.min(...rows.map(r=>r.stepCount));
  const minimizers=rows.filter(r=>r.stepCount===minimum).map(r=>({...r,
    menu:menu(returnTypes(r.lowSigns,r.tailChangeMask,r.selectMask))}));
  return {changes,caseCount:rows.length,minimum,minimizers,rows};
}

export function compact(result) {
  const bySelectorSize = [1,2,3,4].map(size => {
    const rows = result.rows.filter(r => [0,1,2,3].filter(j=>r.selectMask&(1<<j)).length===size);
    const histogram = {};
    for (const row of rows) histogram[row.stepCount]=(histogram[row.stepCount]??0)+1;
    return {size,cases:rows.length,minimum:Math.min(...rows.map(r=>r.stepCount)),histogram};
  });
  return {...result,bySelectorSize,
    rowFields:['lowSignMaskLSB','tailChangeMask','selectMask','returnTypeCount','stepCount','endpointLowerBound','maxGap'],
    rows:result.rows.map(r => [r.lowSigns.reduce((mask,e,j)=>mask|(e<0?1<<j:0),0),
      r.tailChangeMask,r.selectMask,r.returnTypeCount,r.stepCount,r.endpointLowerBound,r.maxGap])};
}

if (process.argv[1] && fileURLToPath(import.meta.url)===path.resolve(process.argv[1])) {
  if (process.argv.includes('--help')) {
    console.log('node research/unit-step/tracks/signed_return_topologies.mjs [--write]\n'
      +'Bounded one-core exact quotient, not a long-period/prefix scan. Atomically saves\n'
      +'an identity-checked result checkpoint; a compatible completed run is reused.\n'
      +'--write copies the result to research/unit-step/checks/signed-return-topologies.json.');
    process.exit(0);
  }
  const hash=crypto.createHash('sha256').update(fs.readFileSync(fileURLToPath(import.meta.url))).digest('hex');
  const dir='.checkpoint-signed-return-topologies', checkpoint=`${dir}/${hash}.json`;
  fs.mkdirSync(dir,{recursive:true});
  function log(event,fields={}) {
    const record={timestamp:new Date().toISOString(),event,...fields};
    fs.appendFileSync(`${dir}/run.jsonl`,JSON.stringify(record)+'\n');
    console.log(JSON.stringify(record));
  }
  const started=performance.now();
  log('start',{codeSha256:hash,cores:1,checkpoint,total:1080,estimatedSeconds:2});
  let saved;
  if(fs.existsSync(checkpoint)) {
    saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));
    if(saved.codeSha256!==hash || saved.schema!==1 || !saved.result) throw new Error('incompatible/corrupt checkpoint');
    const checksum=crypto.createHash('sha256').update(JSON.stringify(saved.result)).digest('hex');
    if(checksum!==saved.resultSha256) throw new Error('checkpoint checksum mismatch');
    log('resume',{completed:saved.result.caseCount});
  } else {
    const result=compact(calculate());
    saved={schema:1,codeSha256:hash,resultSha256:crypto.createHash('sha256').update(JSON.stringify(result)).digest('hex'),result};
    atomic(checkpoint,saved);
  }
  if(process.argv.includes('--write')) atomic('research/unit-step/checks/signed-return-topologies.json',saved);
  const elapsedSeconds=(performance.now()-started)/1000;
  log('complete',{completed:saved.result.caseCount,total:saved.result.caseCount,
    elapsedSeconds,perSecond:saved.result.caseCount/elapsedSeconds,remainingSeconds:0,
    minimum:saved.result.minimum,minimizerCount:saved.result.minimizers.length,
    realizableChangeSets:saved.result.changes.map(c=>c.changes),rssBytes:process.memoryUsage().rss});
}
