#!/usr/bin/env node
// Exact finite automaton for one FIXED adjacent-length ratio in Shallit's word.
// The uniform normalized-error bound is proved in SHALLIT-RATIO-DESCENT.md.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

export const IMAGE = [...'01213101314310'].map(Number);
export const M = [[3,1,3,1,6],[6,3,1,3,1],[1,6,3,1,3],[3,1,6,3,1],[1,3,1,6,3]];
export const ADJ = Array.from({length: 5}, (_, r) =>
  Array.from({length: 5}, (_, c) => [227,1025,-305,-53,-473][(c-r+5)%5]));
export const DEN = 5894;
export const PREFIX = Array.from({length: 5}, (_, a) => {
  const rows = [Array(5).fill(0)];
  for (const letter of IMAGE) { const row = rows.at(-1).slice(); row[(a+letter)%5]++; rows.push(row); }
  return rows;
});
export const multiply = (A, v) => A.map(row => row.reduce((s, x, j) => s+x*v[j], 0));
export const ROOT = [0,0,0,0,0,0,0,0]; // strict-gap mask, relative letters j,k, five error coordinates
export const accepting = s => s[0] === 3 && s.slice(3).every(x => x === 0);
export const key = s => s.join(',');
const digest = x => createHash('sha256').update(x).digest('hex');
const sourcePath = fileURLToPath(import.meta.url);

export function inside(s, a, b) {
  const L = a+b, d = s.slice(3), sum = d.reduce((x,y) => x+y, 0);
  return d.reduce((x,y) => x+y*y, 0) < 4*L*L && Math.abs(sum) < L;
}

// One exact base-14 digit step. No coarse error bound is used in this function.
export function child(s, digits, a, b) {
  const [mask, u, v] = s, [i,j,k] = digits, L = a+b;
  if ((!(mask&1) && i>j) || (!(mask&2) && j>k)) return null;
  const md = multiply(M, s.slice(3));
  const raw = md.map((x,r) => x+b*PREFIX[0][i][r]-L*PREFIX[u][j][r]+a*PREFIX[v][k][r]);
  const rotation = IMAGE[i];
  return [mask | (i<j ? 1 : 0) | (j<k ? 2 : 0),
    (u+IMAGE[j]-rotation+5)%5, (v+IMAGE[k]-rotation+5)%5,
    ...raw.map((_,r) => raw[(r+rotation)%5])];
}

// Precompute only digit triples satisfying order and the necessary clock bound.
export function transitionFactory(a, b) {
  const cache = new Map(), L = a+b;
  return s => {
    const [mask,u,v] = s, sum = s.slice(3).reduce((x,y) => x+y, 0);
    const k = [mask,u,v,sum].join(',');
    if (cache.has(k)) return cache.get(k);
    const choices = [];
    for (let i=0;i<14;i++) for (let j=0;j<14;j++) for (let k=0;k<14;k++) {
      if ((!(mask&1) && i>j) || (!(mask&2) && j>k)) continue;
      if (Math.abs(14*sum+b*i-L*j+a*k) >= L) continue;
      const rotation = IMAGE[i];
      const raw = PREFIX[0][i].map((x,r) => b*x-L*PREFIX[u][j][r]+a*PREFIX[v][k][r]);
      choices.push({ digits:[i,j,k], rotation,
        header:[mask | (i<j ? 1 : 0) | (j<k ? 2 : 0),
          (u+IMAGE[j]-rotation+5)%5, (v+IMAGE[k]-rotation+5)%5],
        correction:raw.map((_,r) => raw[(r+rotation)%5]) });
    }
    cache.set(k, choices); return choices;
  };
}

export function fastChild(md, edge) {
  return [...edge.header, ...edge.correction.map((x,r) => x+md[(r+edge.rotation)%5])];
}

export function prefixAt(n) {
  n = BigInt(n);
  assert(n >= 0n);
  const digits = [];
  while (n) { digits.push(Number(n%14n)); n /= 14n; }
  let p = Array(5).fill(0n), letter = 0;
  for (const t of digits.reverse()) {
    p = M.map((row,r) => row.reduce((sum,x,j) => sum+BigInt(x)*p[j], BigInt(PREFIX[letter][t][r])));
    letter = (letter+IMAGE[t])%5;
  }
  return p;
}

export function witness(nodes, last, a, b) {
  const digits = [];
  while (last) { digits.push(nodes[last].digits); last = nodes[last].parent; }
  const indices = [0n,0n,0n];
  for (const row of digits.reverse()) for (let r=0;r<3;r++) indices[r]=14n*indices[r]+BigInt(row[r]);
  assert(indices[0]<indices[1] && indices[1]<indices[2]);
  const p = indices.map(prefixAt), left=p[1].map((x,r)=>x-p[0][r]), right=p[2].map((x,r)=>x-p[1][r]);
  assert(left.every((x,r)=>BigInt(b)*x===BigInt(a)*right[r]));
  return { indices:indices.map(String), leftCounts:left.map(String), rightCounts:right.map(String),
    leftLength:String(indices[1]-indices[0]), rightLength:String(indices[2]-indices[1]) };
}

function durable(filename, data, append=false) {
  fs.mkdirSync(path.dirname(filename), {recursive:true});
  const destination=append ? filename : `${filename}.tmp-${process.pid}`;
  const fd=fs.openSync(destination, append?'a':'w', 0o600);
  try { fs.writeFileSync(fd,data); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
  if (!append) fs.renameSync(destination,filename);
}

export function validateProgress(progress, a, b) {
  const {nodes,cursor,transitions,status} = progress;
  assert(['running','closed','counterexample'].includes(status));
  assert(Array.isArray(nodes) && nodes.length && Number.isInteger(cursor) && cursor>=0 && cursor<=nodes.length);
  assert(Number.isSafeInteger(transitions) && transitions>=0);
  assert.deepEqual(nodes[0], {state:ROOT,parent:-1,digits:[]});
  const keys=new Set();
  for (let i=0;i<nodes.length;i++) {
    const node=nodes[i], s=node.state;
    assert(s.length===8 && s.every(Number.isSafeInteger) && s[0]>=0 && s[0]<=3
      && s[1]>=0 && s[1]<5 && s[2]>=0 && s[2]<5 && inside(s,a,b));
    assert(!keys.has(key(s))); keys.add(key(s));
    if (i) {
      assert(Number.isInteger(node.parent) && node.parent>=0 && node.parent<i);
      assert(node.digits.length===3 && node.digits.every(x=>Number.isInteger(x)&&x>=0&&x<14));
      assert.deepEqual(s,child(nodes[node.parent].state,node.digits,a,b));
    }
    if (accepting(s)) assert(status==='counterexample' && i===nodes.length-1);
  }
  if (status==='closed') assert.equal(cursor,nodes.length);
  if (status==='counterexample') assert(accepting(nodes.at(-1).state));
}

async function main() {
  const {values}=parseArgs({options:{
    left:{type:'string',default:'1'}, right:{type:'string',default:'1'},
    seconds:{type:'string',default:'120'}, 'max-states':{type:'string',default:'100000'},
    'state-dir':{type:'string'}, output:{type:'string'}, help:{type:'boolean',short:'h'},
  }});
  if (values.help) {
    console.log('Exact fixed-ratio automaton for Shallit\'s five-letter word; one JS worker.\n'
      +'--left A --right B (coprime, each 1..8) --seconds 1..600 --max-states 1..300000\n'
      +'--state-dir DIR (required) --output FILE (optional, separate from checkpoints/logs)\n'
      +'Compatible commands resume at completed-state boundaries; completed states are not re-expanded.\n'
      +'Atomic checksummed checkpoints and timestamped logs every five seconds, plus start/stop.\n'
      +'SIGINT/SIGTERM checkpoint at an event-loop yield (every 64 completed states).\n'
      +'Time/state budgets may change; code and ratio may not. State limits are checked between states.\n'
      +'A closed graph certifies ONLY the specified ratio for all lengths; no global 5D claim.');
    return;
  }
  const a=Number(values.left), b=Number(values.right), seconds=Number(values.seconds), maxStates=Number(values['max-states']);
  const gcd=(a,b)=>b?gcd(b,a%b):a;
  for(const [x,lo,hi] of [[a,1,8],[b,1,8],[seconds,1,600],[maxStates,1,300000]])
    assert(Number.isInteger(x)&&x>=lo&&x<=hi,'invalid bounded parameter');
  assert.equal(gcd(a,b),1,'ratio must be in lowest terms');
  assert(values['state-dir'],'--state-dir is required');
  const checkpoint=path.resolve(values['state-dir'],'state.json'), log=path.resolve(values['state-dir'],'run.jsonl');
  if(values.output) assert(![checkpoint,log].includes(path.resolve(values.output)),'output must be separate');
  const identity={schema:1,codeSha256:digest(fs.readFileSync(sourcePath)),image0:IMAGE.join(''),left:a,right:b};
  const event=(type,fields={})=>{
    const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';
    durable(log,line,true);process.stderr.write(line);
  };
  try {
    let progress={nodes:[{state:ROOT.slice(),parent:-1,digits:[]}],cursor:0,transitions:0,status:'running'};
    const resumed=fs.existsSync(checkpoint);
    if(resumed) {
      const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));
      assert.deepEqual(saved.identity,identity,'incompatible checkpoint');
      assert.equal(saved.checksum,digest(JSON.stringify(saved.progress)),'corrupt checkpoint');
      progress=saved.progress;validateProgress(progress,a,b);
    }
    const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:digest(JSON.stringify(progress)),progress})+'\n');
    let stopped=false;
    process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
    const seen=new Map(progress.nodes.map((node,i)=>[key(node.state),i]));
    const choices=transitionFactory(a,b), start=performance.now(), initial=progress.cursor;
    let lastLog=start, resourceStop=false;
    const report=()=>{
      const elapsed=(performance.now()-start)/1000, rate=(progress.cursor-initial)/Math.max(elapsed,.001);
      return {completedStates:progress.cursor,discoveredStates:progress.nodes.length,transitions:progress.transitions,
        totalReachableStates:'unknown until closure',statesPerSecond:rate,elapsedSeconds:elapsed,
        currentQueueDrainSeconds:rate?(progress.nodes.length-progress.cursor)/rate:null,
        closureEta:null,remainingTimeBudgetSeconds:Math.max(0,seconds-elapsed),checkpoint,rssBytes:process.memoryUsage().rss};
    };
    event(resumed?'resume':'start',{...identity,...report(),seconds,maxStates,workers:1,rssLimitBytes:536870912});save();
    while(progress.status==='running' && !stopped && progress.nodes.length<maxStates
      && performance.now()-start<seconds*1000 && !resourceStop) {
      if(progress.cursor===progress.nodes.length) {progress.status='closed';break;}
      const index=progress.cursor, s=progress.nodes[index].state, md=multiply(M,s.slice(3));
      for(const edge of choices(s)) {
        progress.transitions++;
        const next=fastChild(md,edge);
        if(!inside(next,a,b)) continue;
        const k=key(next);
        if(seen.has(k)) continue;
        seen.set(k,progress.nodes.length);
        progress.nodes.push({state:next,parent:index,digits:edge.digits});
        if(accepting(next)) {progress.status='counterexample';break;}
      }
      if(progress.status==='running') progress.cursor++;
      if(progress.cursor%64===0) await new Promise(resolve=>setImmediate(resolve));
      if(performance.now()-lastLog>=5000) {
        save();event('progress',report());lastLog=performance.now();
        resourceStop=process.memoryUsage().rss>536870912;
      }
    }
    if(progress.status==='running' && progress.cursor===progress.nodes.length) progress.status='closed';
    save();
    const outcome=progress.status==='running'?(stopped?'interrupted':resourceStop?'memory_budget':'budget_reached'):progress.status;
    const result={...identity,outcome,states:progress.nodes.length,completedStates:progress.cursor,
      candidateTransitions:progress.transitions,normalizedErrorRadiusStrict:2,clockErrorBoundStrict:a+b,
      certifiesSpecifiedRatioAvoidance:progress.status==='closed',certifiesAllRatios:false,
      scope:'Only this fixed adjacent-length ratio in this substitution; not a universal dimension bound.'};
    if(progress.status==='closed') result.closedStates=progress.nodes.map(node=>node.state);
    if(progress.status==='counterexample') result.witness=witness(progress.nodes,progress.nodes.length-1,a,b);
    if(values.output) durable(values.output,JSON.stringify(result)+'\n');
    event(outcome,{...report(),output:values.output??null,certifiesSpecifiedRatioAvoidance:result.certifiesSpecifiedRatioAvoidance});
    if(stopped) process.exitCode=130;
  } catch(error) {event('error',{message:error.message,checkpoint});throw error;}
}

if(process.argv[1]&&path.resolve(process.argv[1])===sourcePath)
  main().catch(error=>{console.error(error.message);process.exitCode=1;});
