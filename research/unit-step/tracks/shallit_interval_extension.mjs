#!/usr/bin/env node
// Exact closed-guard interval extension with a detector for infinite affine-state families.
import assert from 'node:assert/strict';
import fs from 'node:fs';import path from 'node:path';import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';import {parseArgs} from 'node:util';
import {M,multiply,prefixAt} from './shallit_ratio_automaton.mjs';
import {ROOT,stateKey,preparedChild,digitChild,compareFractions,atParameter,reconstruct,accepting} from './shallit_interval_automaton.mjs';
const source=fileURLToPath(import.meta.url),hash=x=>createHash('sha256').update(x).digest('hex');
const gcd=(a,b)=>b?gcd(b,a%b):a;
export const span=s=>s.slice(8).reduce((x,y)=>x+y,0);
export function closedAt(s,n,d){const q=atParameter(s,n,d);return 400n*q.norm<=1521n*q.denominator*q.denominator&&q.clock>=-q.denominator&&q.clock<=q.denominator;}
export function closedFeasible(s,I){
  const A=s.slice(3,8),B=s.slice(8),N=span(s),p=-A.reduce((x,y)=>x+y,0);
  let lo=I.slice(0,2),hi=I.slice(2);
  const cut=(a,b,c,d)=>{if(compareFractions(a,b,...lo)>0)lo=[a,b];if(compareFractions(c,d,...hi)<0)hi=[c,d];return compareFractions(...lo,...hi)<=0;};
  if(N&&!cut(p-1,N,p+1,N))return null;
  for(let r=0;r<5;r++)if(B[r]&&!cut(-39-20*A[r],20*B[r],39-20*A[r],20*B[r]))return null;
  if(!N)return lo.map(BigInt);
  let ab=0n,bb=0n;for(let r=0;r<5;r++){ab+=BigInt(A[r])*BigInt(B[r]);bb+=BigInt(B[r])**2n;}
  let t=[-ab,bb];
  if(t[0]*BigInt(lo[1])<BigInt(lo[0])*t[1])t=lo.map(BigInt);
  if(t[0]*BigInt(hi[1])>BigInt(hi[0])*t[1])t=hi.map(BigInt);
  return closedAt(s,...t)?t:null;
}
const floorDiv=(n,d)=>n>=0n?n/d:-((-n+d-1n)/d);
export function choices(s,I){
  const [mask]=s,N=span(s),p=-s.slice(3,8).reduce((x,y)=>x+y,0),out=[];
  for(let x=0;x<14;x++)for(let z=0;z<14;z++){
    const nextN=14*N+z-x;if(nextN<0)continue;
    const low=BigInt(I[0])*BigInt(nextN)+BigInt(I[1])*BigInt(x-14*p-1);
    const high=BigInt(I[2])*BigInt(nextN)+BigInt(I[3])*BigInt(x-14*p+1);
    const lo=Math.max(0,Number(-floorDiv(-low,BigInt(I[1])))),hi=Math.min(13,Number(floorDiv(high,BigInt(I[3]))));
    for(let y=lo;y<=hi;y++)if(!((!(mask&1)&&x>y)||(!(mask&2)&&y>z)))out.push([x,y,z]);
  }
  return out;
}
function pathTo(nodes,id){const rows=[];while(id){rows.push(nodes[id].digits);id=nodes[id].parent;}return rows.reverse();}
export function findCycle(nodes,parent,next,digits,I){
  if(next[0]!==3)return null;
  for(let id=parent;id>=0;id=nodes[id].parent){
    const s=nodes[id].state;if(s[0]!==3||s[1]!==next[1]||s[2]!==next[2])continue;
    const da=next.slice(3,8).map((x,r)=>BigInt(x)-BigInt(s[3+r]));
    const db=next.slice(8).map((x,r)=>BigInt(x)-BigInt(s[8+r]));
    const r=db.findIndex(x=>x!==0n);if(r<0)continue;
    let n=-da[r],d=db[r];if(d<0n){n=-n;d=-d;}if(n<=0n||n>=d)continue;
    if(n*BigInt(I[1])<BigInt(I[0])*d||n*BigInt(I[3])>BigInt(I[2])*d)continue;
    if(da.some((x,r)=>x*d+n*db[r]!==0n)||!closedAt(s,n,d))continue;
    const divisor=gcd(n,d);n/=divisor;d/=divisor;
    const point=atParameter(s,n,d);assert(point.norm>0n,'accepting state must be handled first');
    assert(span(next)>span(s)&&span(s)>=2);
    const prefix=pathTo(nodes,id),full=[...pathTo(nodes,parent),digits];
    return {theta:[String(n),String(d)],prefixDigits:prefix,cycleDigits:full.slice(prefix.length),
      ancestorState:s,descendantState:next,spanBefore:span(s),spanAfter:span(next),
      scope:'Nonzero periodic point-state with strictly growing affine coefficients; obstruction to a finite literal affine-state invariant, not a collinear triple.'};
  }
  return null;
}
function durable(file,text,append=false){fs.mkdirSync(path.dirname(file),{recursive:true});const dest=append?file:`${file}.tmp-${process.pid}`;
  const fd=fs.openSync(dest,append?'a':'w',0o600);try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}if(!append)fs.renameSync(dest,file);}
export function validateProgress(p,I){
  assert(['running','closed','cycle','counterexample'].includes(p.status));assert(Number.isSafeInteger(p.transitions)&&p.transitions>=0);
  assert.deepEqual(p.nodes[0],{state:ROOT,parent:-1,digits:[]});const keys=new Set();
  p.nodes.forEach((node,i)=>{const s=node.state;assert(s.length===13&&s.every(Number.isSafeInteger));
    assert(s[0]>=0&&s[0]<=3&&s[1]>=0&&s[1]<5&&s[2]>=0&&s[2]<5);
    assert(s.slice(3,8).every((x,r)=>x<=0&&x>=-s[8+r])&&span(s)<=1e12);assert(closedFeasible(s,I));
    assert(!keys.has(stateKey(s)));keys.add(stateKey(s));
    if(i){assert(Number.isInteger(node.parent)&&node.parent>=0&&node.parent<i);assert(node.digits.length===3&&node.digits.every(x=>Number.isInteger(x)&&x>=0&&x<14));
      assert.deepEqual(s,digitChild(p.nodes[node.parent].state,node.digits));}
  });
  p.stack.forEach(([id,cursor],i)=>{assert(Number.isInteger(id)&&id>=0&&id<p.nodes.length);assert(Number.isInteger(cursor)&&cursor>=0&&cursor<=choices(p.nodes[id].state,I).length);
    if(i)assert.equal(p.nodes[id].parent,p.stack[i-1][0]);});
  if(p.status==='closed')assert.equal(p.stack.length,0);
}
async function main(){
  const {values}=parseArgs({options:{'radius-denominator':{type:'string',default:'1000000'},seconds:{type:'string',default:'120'},
    'max-states':{type:'string',default:'100000'},'max-span':{type:'string',default:'1000000000000'},'state-dir':{type:'string'},output:{type:'string'},help:{type:'boolean',short:'h'}}});
  if(values.help){console.log('Exact DFS extension for theta in [1/2-1/D,1/2+1/D], radius 39/20 and clock guards closed.\n'
    +'--radius-denominator D (6..1e9; D=6 is the full requested central interval)\n'
    +'--seconds 1..600 --max-states 1..200000 --max-span 1..1e12 --state-dir DIR --output FILE\n'
    +'Identity/checksum-validated atomic DFS resume; budgets may change, parameter interval may not.\n'
    +'SIGINT/SIGTERM checkpoint. Closed=interval certificate; cycle=literal-affine-method obstruction; budgets=inconclusive.');return;}
  const D=Number(values['radius-denominator']),seconds=Number(values.seconds),maxStates=Number(values['max-states']),maxSpan=Number(values['max-span']);
  for(const [x,lo,hi] of [[D,6,1e9],[seconds,1,600],[maxStates,1,200000],[maxSpan,1,1e12]])assert(Number.isInteger(x)&&x>=lo&&x<=hi);
  assert(values['state-dir']);const I=[D-2,2*D,D+2,2*D],checkpoint=path.resolve(values['state-dir'],'state.json'),log=path.resolve(values['state-dir'],'run.jsonl');
  if(values.output)assert(![checkpoint,log].includes(path.resolve(values.output)));
  const identity={schema:1,codeSha256:hash(fs.readFileSync(source)),dependencies:['shallit_ratio_automaton.mjs','shallit_interval_automaton.mjs'].map(file=>({file,sha256:hash(fs.readFileSync(new URL(file,import.meta.url)))})),interval:I,closedNormRadius:[39,20],closedClockRadius:1};
  const event=(type,fields={})=>{const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';durable(log,line,true);process.stderr.write(line);};
  try{
    let p={nodes:[{state:ROOT.slice(),parent:-1,digits:[]}],stack:[[0,0]],transitions:0,completed:0,status:'running'};
    const resumed=fs.existsSync(checkpoint);
    if(resumed){const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));assert.deepEqual(saved.identity,identity,'incompatible checkpoint');
      assert.equal(saved.checksum,hash(JSON.stringify(saved.progress)),'corrupt checkpoint');p=saved.progress;validateProgress(p,I);}
    const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:hash(JSON.stringify(p)),progress:p})+'\n');
    const seen=new Set(p.nodes.map(n=>stateKey(n.state))),cache=new Map();
    const edgesFor=id=>{if(!cache.has(id)){const s=p.nodes[id].state;cache.set(id,{edges:choices(s,I),ma:multiply(M,s.slice(3,8)),mb:multiply(M,s.slice(8))});}return cache.get(id);};
    let stopped=false,budget=null;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
    const start=performance.now(),initial=p.transitions;let lastLog=start;
    const report=()=>{const elapsed=(performance.now()-start)/1000;return {discoveredStates:p.nodes.length,completedStates:p.completed,stackDepth:p.stack.length,
      testedTransitions:p.transitions,transitionsPerSecond:(p.transitions-initial)/Math.max(elapsed,.001),elapsedSeconds:elapsed,remainingSeconds:Math.max(0,seconds-elapsed),
      totalStates:'unknown; finiteness not assumed',closureEta:null,checkpoint,rssBytes:process.memoryUsage().rss};};
    event(resumed?'resume':'start',{...identity,...report(),seconds,maxStates,maxSpan,workers:1,rssLimitBytes:536870912});save();
    while(p.status==='running'&&!stopped&&!budget&&performance.now()-start<seconds*1000){
      if(!p.stack.length){p.status='closed';break;}if(p.nodes.length>=maxStates){budget='state_budget';break;}
      const frame=p.stack.at(-1),[parent,cursor]=frame,{edges,ma,mb}=edgesFor(parent);
      if(cursor===edges.length){p.stack.pop();cache.delete(parent);p.completed++;continue;}
      const digits=edges[cursor],next=preparedChild(p.nodes[parent].state,digits,ma,mb);
      assert(next);const parameter=closedFeasible(next,I);
      if(parameter&&span(next)>maxSpan){budget='span_budget';break;}
      frame[1]++;p.transitions++;
      if(parameter){
        const zero=accepting(next,I);
        if(zero){const id=p.nodes.length;p.nodes.push({state:next,parent,digits});
          const indices=reconstruct(p.nodes,id),F=indices.map(prefixAt),[i,j,k]=indices;
          assert(i<j&&j<k&&F[0].every((_,r)=>(k-j)*(F[1][r]-F[0][r])===(j-i)*(F[2][r]-F[1][r])));
          p.witness={indices:indices.map(String),counts:F.map(v=>v.map(String))};p.status='counterexample';break;}
        const cycle=findCycle(p.nodes,parent,next,digits,I);
        if(cycle){p.cycle=cycle;p.status='cycle';break;}
        const key=stateKey(next);if(!seen.has(key)){seen.add(key);const id=p.nodes.length;p.nodes.push({state:next,parent,digits});p.stack.push([id,0]);}
      }
      if(p.transitions%256===0)await new Promise(resolve=>setImmediate(resolve));
      if(performance.now()-lastLog>=5000){save();event('progress',report());lastLog=performance.now();if(process.memoryUsage().rss>536870912)budget='memory_budget';}
    }
    if(p.status==='running'&&!p.stack.length)p.status='closed';save();
    const outcome=p.status==='running'?(stopped?'interrupted':budget??'time_budget'):p.status;
    const result={...identity,outcome,states:p.nodes.length,completedStates:p.completed,testedTransitions:p.transitions,
      certifiesIntervalAvoidance:p.status==='closed',scope:'Only a closed invariant certifies avoidance. A nonzero cycle obstructs this finite affine-list method, not the candidate itself.'};
    if(p.status==='closed')result.closedStates=p.nodes.map(n=>n.state);if(p.cycle)result.cycle=p.cycle;if(p.witness)result.witness=p.witness;
    if(values.output)durable(values.output,JSON.stringify(result)+'\n');
    event(outcome,{...report(),output:values.output??null,certifiesIntervalAvoidance:result.certifiesIntervalAvoidance,cycleTheta:p.cycle?.theta??null});if(stopped)process.exitCode=130;
  }catch(error){event('error',{message:error.message,checkpoint});throw error;}
}
if(process.argv[1]&&path.resolve(process.argv[1])===source)main().catch(error=>{console.error(error.message);process.exitCode=1;});
