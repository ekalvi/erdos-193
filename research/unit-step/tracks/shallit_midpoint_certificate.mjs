#!/usr/bin/env node
// Compile a finite affine closure at theta=1/2 using CLOSED radius 39/20 and clock guards.
// If it closes without a strict zero, a quantitative neighborhood follows; see the note.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseArgs} from 'node:util';
import {IMAGE,M,PREFIX,multiply} from './shallit_ratio_automaton.mjs';
import {ROOT,stateKey,preparedChild,digitChild} from './shallit_interval_automaton.mjs';
const hash=x=>createHash('sha256').update(x).digest('hex');
const source=fileURLToPath(import.meta.url);
export const pointVector=s=>s.slice(3,8).map((x,r)=>2*x+s[8+r]);
export const span=s=>s.slice(8).reduce((x,y)=>x+y,0);
export const pointGuard=s=>{
  const d=pointVector(s);
  return d.every(x=>Math.abs(x)<4)&&d.reduce((x,y)=>x+y*y,0)<=15&&Math.abs(d.reduce((x,y)=>x+y,0))<=2;
};
export const pointAccept=s=>s[0]===3&&pointVector(s).every(x=>x===0);

export function makeEdges() {
  const cache=new Map();
  return s=>{
    const [mask,u,v]=s,d=pointVector(s),k=[mask,u,v,...d].join(',');
    if(cache.has(k))return cache.get(k);
    const md=multiply(M,d),sum=d.reduce((x,y)=>x+y,0),edges=[];
    for(let x=0;x<14;x++)for(let y=0;y<14;y++)for(let z=0;z<14;z++) {
      if((!(mask&1)&&x>y)||(!(mask&2)&&y>z))continue;
      if(Math.abs(14*sum+x-2*y+z)>2)continue;
      const raw=md.map((c,r)=>c+PREFIX[0][x][r]-2*PREFIX[u][y][r]+PREFIX[v][z][r]);
      if(raw.reduce((x,y)=>x+y*y,0)>15)continue;
      edges.push([x,y,z]);
    }
    cache.set(k,edges);return edges;
  };
}
function durable(file,text,append=false) {
  fs.mkdirSync(path.dirname(file),{recursive:true});const target=append?file:`${file}.tmp-${process.pid}`;
  const fd=fs.openSync(target,append?'a':'w',0o600);try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  if(!append)fs.renameSync(target,file);
}
export function validateProgress(p) {
  assert(['running','closed'].includes(p.status));
  assert(Number.isInteger(p.cursor)&&p.cursor>=0&&p.cursor<=p.nodes.length);
  assert(Number.isSafeInteger(p.edges)&&p.edges>=0);
  assert.deepEqual(p.nodes[0],{state:ROOT,parent:-1,digits:[]});
  const seen=new Set();p.nodes.forEach((node,i)=>{
    const s=node.state;assert(s.length===13&&s.every(Number.isSafeInteger));
    assert(s[0]>=0&&s[0]<=3&&s[1]>=0&&s[1]<5&&s[2]>=0&&s[2]<5);
    assert(s.slice(3,8).every((x,r)=>x<=0&&x>=-s[8+r]));assert(pointGuard(s));assert(!pointAccept(s));
    assert(!seen.has(stateKey(s)));seen.add(stateKey(s));
    if(i){assert(Number.isInteger(node.parent)&&node.parent>=0&&node.parent<i);
      assert(node.digits.length===3&&node.digits.every(x=>Number.isInteger(x)&&x>=0&&x<14));
      assert.deepEqual(s,digitChild(p.nodes[node.parent].state,node.digits));}
  });
  if(p.status==='closed')assert.equal(p.cursor,p.nodes.length);
}
async function main() {
  const {values}=parseArgs({options:{seconds:{type:'string',default:'120'},'max-states':{type:'string',default:'100000'},
    'state-dir':{type:'string'},output:{type:'string'},help:{type:'boolean',short:'h'}}});
  if(values.help){console.log('Closed midpoint affine-state compiler, one JS worker.\n'
    +'--seconds 1..600 --max-states 1..200000 --state-dir DIR --output FILE\n'
    +'Atomic identity/checksum-validated BFS resume at completed-state boundaries.\n'
    +'SIGINT/SIGTERM checkpoint; timestamped progress every five seconds.\n'
    +'Only closure certifies a neighborhood; budget exits are inconclusive.');return;}
  const seconds=Number(values.seconds),maxStates=Number(values['max-states']);
  assert(Number.isInteger(seconds)&&seconds>=1&&seconds<=600);assert(Number.isInteger(maxStates)&&maxStates>=1&&maxStates<=200000);
  assert(values['state-dir']);
  const checkpoint=path.resolve(values['state-dir'],'state.json'),log=path.resolve(values['state-dir'],'run.jsonl');
  if(values.output)assert(![checkpoint,log].includes(path.resolve(values.output)));
  const identity={schema:1,codeSha256:hash(fs.readFileSync(source)),
    dependencies:['shallit_ratio_automaton.mjs','shallit_interval_automaton.mjs'].map(file=>({file,sha256:hash(fs.readFileSync(new URL(file,import.meta.url)))})),
    center:[1,2],closedNormRadius:[39,20],closedClockRadius:1};
  const event=(type,fields={})=>{const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';durable(log,line,true);process.stderr.write(line);};
  try {
    let p={nodes:[{state:ROOT.slice(),parent:-1,digits:[]}],cursor:0,edges:0,status:'running'};
    const resumed=fs.existsSync(checkpoint);
    if(resumed){const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));assert.deepEqual(saved.identity,identity,'incompatible checkpoint');
      assert.equal(saved.checksum,hash(JSON.stringify(saved.progress)),'corrupt checkpoint');p=saved.progress;validateProgress(p);}
    const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:hash(JSON.stringify(p)),progress:p})+'\n');
    const seen=new Set(p.nodes.map(n=>stateKey(n.state))),edges=makeEdges();
    let stopped=false,budget=null;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
    const start=performance.now(),initial=p.cursor;let lastLog=start;
    const report=()=>{const elapsed=(performance.now()-start)/1000;return {completedStates:p.cursor,discoveredStates:p.nodes.length,
      retainedTransitions:p.edges,statesPerSecond:(p.cursor-initial)/Math.max(elapsed,.001),elapsedSeconds:elapsed,
      totalReachableStates:'unknown until closure',closureEta:null,remainingSeconds:Math.max(0,seconds-elapsed),checkpoint,rssBytes:process.memoryUsage().rss};};
    event(resumed?'resume':'start',{...identity,...report(),seconds,maxStates,workers:1,rssLimitBytes:536870912});save();
    while(p.status==='running'&&!stopped&&!budget&&performance.now()-start<seconds*1000) {
      if(p.cursor===p.nodes.length){p.status='closed';break;}
      if(p.nodes.length>=maxStates){budget='state_budget';break;}
      const parent=p.cursor,s=p.nodes[parent].state,ma=multiply(M,s.slice(3,8)),mb=multiply(M,s.slice(8));
      for(const digits of edges(s)) {
        const next=preparedChild(s,digits,ma,mb);assert(pointGuard(next));
        assert(!pointAccept(next),'unexpected midpoint counterexample');
        assert(span(next)<1e12,'span safety bound reached; no certificate');
        p.edges++;const k=stateKey(next);
        if(!seen.has(k)){seen.add(k);p.nodes.push({state:next,parent,digits});}
      }
      p.cursor++;
      if(p.cursor%64===0)await new Promise(resolve=>setImmediate(resolve));
      if(performance.now()-lastLog>=5000){save();event('progress',report());lastLog=performance.now();if(process.memoryUsage().rss>536870912)budget='memory_budget';}
    }
    if(p.status==='running'&&p.cursor===p.nodes.length)p.status='closed';save();
    const outcome=p.status==='closed'?'closed':stopped?'interrupted':budget??'time_budget';
    const result={...identity,outcome,states:p.nodes.length,completedStates:p.cursor,retainedTransitions:p.edges,
      certifiesNeighborhood:p.status==='closed',certifiesWholeCentralInterval:false,
      scope:'Exact affine closure and a uniform neighborhood of theta=1/2 only; not the whole [1/3,2/3].'};
    if(p.status==='closed') {
      const maxSpan=p.nodes.reduce((maximum,node)=>Math.max(maximum,span(node.state)),0),derivativeBound=14*maxSpan+26;
      const epsilonDenominator=40*derivativeBound;
      assert(Number.isSafeInteger(epsilonDenominator));
      result.maxSpan=maxSpan;result.derivativeBound=derivativeBound;result.thetaRadius=[1,epsilonDenominator];
      result.thetaInterval=[[epsilonDenominator/2-1,epsilonDenominator],[epsilonDenominator/2+1,epsilonDenominator]];
      result.closedStates=p.nodes.map(node=>node.state);
    }
    if(values.output)durable(values.output,JSON.stringify(result)+'\n');
    event(outcome,{...report(),output:values.output??null,certifiesNeighborhood:result.certifiesNeighborhood,
      maxSpan:result.maxSpan??null,thetaRadius:result.thetaRadius??null});if(stopped)process.exitCode=130;
  }catch(error){event('error',{message:error.message,checkpoint});throw error;}
}
if(process.argv[1]&&path.resolve(process.argv[1])===source)main().catch(error=>{console.error(error.message);process.exitCode=1;});
