#!/usr/bin/env node
// Exact symbolic-ratio attempt. A budget exit is NOT an interval certificate.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseArgs} from 'node:util';
import {IMAGE,M,PREFIX,multiply,prefixAt} from './shallit_ratio_automaton.mjs';

export const ROOT=Array(13).fill(0); // mask,u,v,A[5],B[5], with error A + theta B
export const stateKey=s=>s.join(',');
const hash=x=>createHash('sha256').update(x).digest('hex');
const source=fileURLToPath(import.meta.url);
export function compareFractions(n,d,p,q) {
  const x=n*q,y=p*d;
  if(Number.isSafeInteger(x)&&Number.isSafeInteger(y))return Math.sign(x-y);
  const a=BigInt(n)*BigInt(q),b=BigInt(p)*BigInt(d);return a<b?-1:a>b?1:0;
}

export function atParameter(s,n,d) {
  const numerator=s.slice(3,8).map((x,r)=>BigInt(x)*BigInt(d)+BigInt(s[8+r])*BigInt(n));
  return {clock:numerator.reduce((x,y)=>x+y,0n),norm:numerator.reduce((x,y)=>x+y*y,0n),denominator:BigInt(d)};
}

// Strict radius-two and clock guards. Quadratic minimization uses exact integers.
// A rational linear envelope is returned, not a claim that its whole interval passes the norm guard.
export function feasible(s,interval=[1,3,2,3]) {
  const A=s.slice(3,8),B=s.slice(8),N=B.reduce((x,y)=>x+y,0),p=-A.reduce((x,y)=>x+y,0);
  const [ln,ld,hn,hd]=interval;
  if(compareFractions(ln,ld,hn,hd)===0) {
    const q=atParameter(s,ln,ld);
    return q.norm<4n*q.denominator*q.denominator && q.clock>-q.denominator && q.clock<q.denominator
      ? {lo:[ln,ld],hi:[hn,hd]} : null;
  }
  let lo=[ln,ld],hi=[hn,hd];
  const restrict=(a,b,c,d)=>{
    if(compareFractions(a,b,...lo)>0)lo=[a,b];
    if(compareFractions(c,d,...hi)<0)hi=[c,d];
    return compareFractions(...lo,...hi)<0;
  };
  if(N && !restrict(p-1,N,p+1,N))return null;
  for(let r=0;r<5;r++)if(B[r] && !restrict(-2-A[r],B[r],2-A[r],B[r]))return null;
  if(!N)return {lo,hi}; // The only reachable zero-span state is the root.
  let aa=0n,ab=0n,bb=0n;
  for(let r=0;r<5;r++){const x=BigInt(A[r]),y=BigInt(B[r]);aa+=x*x;ab+=x*y;bb+=y*y;}
  const beforeLo=(-ab)*BigInt(lo[1])<BigInt(lo[0])*bb;
  const afterHi=(-ab)*BigInt(hi[1])>BigInt(hi[0])*bb;
  let passes;
  if(!beforeLo&&!afterHi)passes=aa*bb-ab*ab<4n*bb;
  else {
    const q=atParameter(s,...(beforeLo?lo:hi));passes=q.norm<4n*q.denominator*q.denominator;
  }
  return passes?{lo,hi}:null;
}

export function digitChild(s,digits) {
  const [mask,u,v]=s,[x,y,z]=digits;
  if((!(mask&1)&&x>y)||(!(mask&2)&&y>z))return null;
  const ma=multiply(M,s.slice(3,8)),mb=multiply(M,s.slice(8));
  return preparedChild(s,digits,ma,mb);
}
export function preparedChild(s,digits,ma,mb) {
  const [mask,u,v]=s,[x,y,z]=digits,t=IMAGE[x];
  if((!(mask&1)&&x>y)||(!(mask&2)&&y>z))return null;
  const A=ma.map((c,r)=>c+PREFIX[0][x][r]-PREFIX[u][y][r]);
  const B=mb.map((c,r)=>c+PREFIX[v][z][r]-PREFIX[0][x][r]);
  return [mask|(x<y?1:0)|(y<z?2:0),(u+IMAGE[y]-t+5)%5,(v+IMAGE[z]-t+5)%5,
    ...A.slice(t),...A.slice(0,t),...B.slice(t),...B.slice(0,t)];
}
export function accepting(s,interval=[1,3,2,3]) {
  if(s[0]!==3)return null;
  const A=s.slice(3,8),B=s.slice(8),p=-A.reduce((x,y)=>x+y,0),N=B.reduce((x,y)=>x+y,0);
  if(p<=0||p>=N||compareFractions(p,N,...interval.slice(0,2))<0||compareFractions(p,N,...interval.slice(2))>0)return null;
  return A.every((x,r)=>BigInt(N)*BigInt(x)+BigInt(p)*BigInt(B[r])===0n)?[p,N]:null;
}
export function reconstruct(nodes,last) {
  const path=[];while(last){path.push(nodes[last].digits);last=nodes[last].parent;}
  const indices=[0n,0n,0n];for(const digits of path.reverse())for(let r=0;r<3;r++)indices[r]=14n*indices[r]+BigInt(digits[r]);
  return indices;
}
function exactWitness(nodes,last) {
  const indices=reconstruct(nodes,last),[i,j,k]=indices;
  assert(i<j&&j<k);
  const p=indices.map(prefixAt),left=p[1].map((x,r)=>x-p[0][r]),right=p[2].map((x,r)=>x-p[1][r]);
  assert(left.every((x,r)=>(k-j)*x===(j-i)*right[r]));
  return {indices:indices.map(String),leftCounts:left.map(String),rightCounts:right.map(String)};
}
function durable(file,text,append=false) {
  fs.mkdirSync(path.dirname(file),{recursive:true});const target=append?file:`${file}.tmp-${process.pid}`;
  const fd=fs.openSync(target,append?'a':'w',0o600);try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  if(!append)fs.renameSync(target,file);
}
export function validateProgress(progress,interval) {
  assert(['running','closed','counterexample'].includes(progress.status));
  assert(Number.isInteger(progress.cursor)&&progress.cursor>=0&&progress.cursor<=progress.nodes.length);
  assert(Number.isInteger(progress.edge)&&progress.edge>=0&&progress.edge<=2744);
  assert(Number.isSafeInteger(progress.transitions)&&progress.transitions>=0);
  assert.equal(progress.transitions,progress.cursor*2744+progress.edge);
  assert.deepEqual(progress.nodes[0],{state:ROOT,parent:-1,digits:[]});
  const seen=new Set();
  progress.nodes.forEach((node,i)=>{
    const s=node.state;assert(s.length===13&&s.every(Number.isSafeInteger));
    assert(s[0]>=0&&s[0]<=3&&s[1]>=0&&s[1]<5&&s[2]>=0&&s[2]<5);
    assert(s.slice(3,8).every((x,r)=>x<=0&&x>=-s[8+r]));assert(feasible(s,interval));
    assert(!seen.has(stateKey(s)));seen.add(stateKey(s));
    if(i){assert(Number.isInteger(node.parent)&&node.parent>=0&&node.parent<i);
      assert(node.digits.length===3&&node.digits.every(x=>Number.isInteger(x)&&x>=0&&x<14));
      assert.deepEqual(s,digitChild(progress.nodes[node.parent].state,node.digits));}
    if(accepting(s,interval))assert(progress.status==='counterexample'&&i===progress.nodes.length-1);
  });
  if(progress.status==='closed')assert.equal(progress.cursor,progress.nodes.length);
  if(progress.status==='counterexample')assert(accepting(progress.nodes.at(-1).state,interval));
}

async function main() {
  const {values}=parseArgs({options:{seconds:{type:'string',default:'60'},'max-states':{type:'string',default:'20000'},
    'max-span':{type:'string',default:'1000000000'},'state-dir':{type:'string'},output:{type:'string'},help:{type:'boolean',short:'h'}}});
  if(values.help){console.log('Exact symbolic theta in [1/3,2/3], one JS worker.\n'
    +'--seconds 1..600 --max-states 1..100000 --max-span 1..1000000000 --state-dir DIR --output FILE\n'
    +'Resumes an identity/checksum-validated BFS queue and exact digit cursor; budgets may change.\n'
    +'Atomic checkpoints and timestamped logs every five seconds; SIGINT/SIGTERM flush at a yield.\n'
    +'Only a CLOSED graph is an interval certificate; budget exits are inconclusive.');return;}
  const seconds=Number(values.seconds),maxStates=Number(values['max-states']),maxSpan=Number(values['max-span']);
  for(const [x,lo,hi] of [[seconds,1,600],[maxStates,1,100000],[maxSpan,1,1e9]])assert(Number.isInteger(x)&&x>=lo&&x<=hi);
  assert(values['state-dir'],'--state-dir is required');
  const interval=[1,3,2,3],checkpoint=path.resolve(values['state-dir'],'state.json'),log=path.resolve(values['state-dir'],'run.jsonl');
  if(values.output)assert(![checkpoint,log].includes(path.resolve(values.output)));
  const identity={schema:1,codeSha256:hash(fs.readFileSync(source)),dependencySha256:hash(fs.readFileSync(new URL('shallit_ratio_automaton.mjs',import.meta.url))),interval};
  const event=(type,fields={})=>{const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';durable(log,line,true);process.stderr.write(line);};
  try {
    let progress={nodes:[{state:ROOT.slice(),parent:-1,digits:[]}],cursor:0,edge:0,transitions:0,status:'running'};
    const resumed=fs.existsSync(checkpoint);
    if(resumed){const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));assert.deepEqual(saved.identity,identity,'incompatible checkpoint');
      assert.equal(saved.checksum,hash(JSON.stringify(saved.progress)),'corrupt checkpoint');progress=saved.progress;validateProgress(progress,interval);}
    const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:hash(JSON.stringify(progress)),progress})+'\n');
    const seen=new Set(progress.nodes.map(n=>stateKey(n.state)));
    let stopped=false;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
    const start=performance.now(),initial=progress.transitions;let lastLog=start,budget=null;
    const report=()=>{const elapsed=(performance.now()-start)/1000;return {completedStates:progress.cursor,discoveredStates:progress.nodes.length,
      digitCursor:progress.edge,digitTransitions:progress.transitions,transitionsPerSecond:(progress.transitions-initial)/Math.max(elapsed,.001),
      totalReachableStates:'unknown; finiteness not established',closureEta:null,elapsedSeconds:elapsed,remainingSeconds:Math.max(0,seconds-elapsed),
      checkpoint,rssBytes:process.memoryUsage().rss};};
    event(resumed?'resume':'start',{...identity,...report(),seconds,maxStates,maxSpan,workers:1,rssLimitBytes:536870912});save();
    while(progress.status==='running'&&!stopped&&!budget&&performance.now()-start<seconds*1000) {
      if(progress.cursor===progress.nodes.length){progress.status='closed';break;}
      if(progress.nodes.length>=maxStates){budget='state_budget';break;}
      const parent=progress.cursor,s=progress.nodes[parent].state,ma=multiply(M,s.slice(3,8)),mb=multiply(M,s.slice(8));
      while(progress.edge<2744&&!stopped&&!budget&&progress.status==='running') {
        const code=progress.edge,digits=[Math.floor(code/196),Math.floor(code/14)%14,code%14];
        const next=preparedChild(s,digits,ma,mb);
        if(next&&feasible(next,interval)) {
          if(next.slice(8).reduce((x,y)=>x+y,0)>maxSpan){budget='span_budget';break;}
          const k=stateKey(next);
          if(!seen.has(k)){seen.add(k);progress.nodes.push({state:next,parent,digits});
            if(accepting(next,interval))progress.status='counterexample';}
        }
        progress.edge++;progress.transitions++;
        if(progress.transitions%1024===0)await new Promise(resolve=>setImmediate(resolve));
        if(performance.now()-lastLog>=5000){save();event('progress',report());lastLog=performance.now();
          if(process.memoryUsage().rss>536870912)budget='memory_budget';
          else if(performance.now()-start>=seconds*1000)budget='time_budget';}
      }
      if(progress.edge===2744){progress.cursor++;progress.edge=0;}
    }
    if(progress.status==='running'&&progress.cursor===progress.nodes.length)progress.status='closed';save();
    const outcome=progress.status==='running'?(stopped?'interrupted':budget??'time_budget'):progress.status;
    const result={...identity,outcome,states:progress.nodes.length,completedStates:progress.cursor,digitCursor:progress.edge,digitTransitions:progress.transitions,
      certifiesIntervalAvoidance:progress.status==='closed',scope:'Exact affine-state interval attempt; a budget exit proves no interval theorem.'};
    if(progress.status==='closed')result.closedStates=progress.nodes.map(n=>n.state);
    if(progress.status==='counterexample')result.witness=exactWitness(progress.nodes,progress.nodes.length-1);
    if(values.output)durable(values.output,JSON.stringify(result,null,2)+'\n');
    event(outcome,{...report(),output:values.output??null,certifiesIntervalAvoidance:result.certifiesIntervalAvoidance});if(stopped)process.exitCode=130;
  }catch(error){event('error',{message:error.message,checkpoint});throw error;}
}
if(process.argv[1]&&path.resolve(process.argv[1])===source)main().catch(error=>{console.error(error.message);process.exitCode=1;});
