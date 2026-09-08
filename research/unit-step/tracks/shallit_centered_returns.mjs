#!/usr/bin/env node
// Finite exact quotient for three equal centered prefix vectors, not full 5D avoidance.
import assert from 'node:assert/strict';import fs from 'node:fs';import path from 'node:path';
import {createHash} from 'node:crypto';import {fileURLToPath} from 'node:url';import {parseArgs} from 'node:util';
import {IMAGE,M,PREFIX,multiply,prefixAt} from './shallit_ratio_automaton.mjs';
const source=fileURLToPath(import.meta.url),hash=x=>createHash('sha256').update(x).digest('hex');
export const norm=v=>v.reduce((a,b)=>a+b*b,0);
export const VECTORS=[];
for(let r=0;r<5;r++){
  const values=[];for(let x=-9;x<=9;x++)if((x%5+5)%5===r)values.push(x);
  for(const a of values)for(const b of values)for(const c of values)for(const d of values){const e=-a-b-c-d;
    if(values.includes(e)&&norm([a,b,c,d,e])<=95)VECTORS.push([a,b,c,d,e]);}
}
const vectorIndex=new Map(VECTORS.map((v,i)=>[v.join(','),i]));
export const ZERO=vectorIndex.get('0,0,0,0,0'),ROOT=[0,0,0,ZERO,ZERO],key=s=>s.join(',');
export const accepting=s=>s[0]===3&&s[3]===ZERO&&s[4]===ZERO;
export function directChild(s,[x,y,z]){
  const [mask,u,v,ix,iy]=s;if((!(mask&1)&&x>y)||(!(mask&2)&&y>z))return null;
  const raw=(id,r,t)=>multiply(M,VECTORS[id]).map((a,j)=>a+5*(PREFIX[r][t][j]-PREFIX[0][x][j])-(t-x));
  const X=raw(ix,u,y),Y=raw(iy,v,z),rotation=IMAGE[x];
  if(norm(X)>95||norm(Y)>95||norm(Y.map((a,j)=>a-X[j]))>95)return null;
  const a=vectorIndex.get([...X.slice(rotation),...X.slice(0,rotation)].join(',')),b=vectorIndex.get([...Y.slice(rotation),...Y.slice(0,rotation)].join(','));
  assert(a!==undefined&&b!==undefined);
  return [mask|(x<y?1:0)|(y<z?2:0),(u+IMAGE[y]-rotation+5)%5,(v+IMAGE[z]-rotation+5)%5,a,b];
}
export function transitionFactory(){
  const pairs=new Map();
  const choices=(u,id)=>{
    const k=`${u},${id}`;if(pairs.has(k))return pairs.get(k);
    const rows=Array.from({length:14},()=>[]),mv=multiply(M,VECTORS[id]);
    for(let x=0;x<14;x++)for(let y=0;y<14;y++){
      const raw=mv.map((a,r)=>a+5*(PREFIX[u][y][r]-PREFIX[0][x][r])-(y-x)),s=IMAGE[x];
      const index=vectorIndex.get([...raw.slice(s),...raw.slice(0,s)].join(','));
      if(index!==undefined)rows[x].push({digit:y,letter:(u+IMAGE[y]-s+5)%5,index});
    }
    pairs.set(k,rows);return rows;
  };
  return s=>{
    const [mask,u,v,a,b]=s,left=choices(u,a),right=choices(v,b),edges=[];let candidates=0;
    for(let x=0;x<14;x++)for(const y of left[x])for(const z of right[x]){
      if((!(mask&1)&&x>y.digit)||(!(mask&2)&&y.digit>z.digit))continue;candidates++;
      if(norm(VECTORS[z.index].map((q,r)=>q-VECTORS[y.index][r]))>95)continue;
      edges.push({digits:[x,y.digit,z.digit],state:[mask|(x<y.digit?1:0)|(y.digit<z.digit?2:0),y.letter,z.letter,y.index,z.index]});
    }
    return {edges,candidates};
  };
}
export function validateProgress(p){
  assert(['running','closed','counterexample'].includes(p.status));
  assert(Number.isInteger(p.cursor)&&p.cursor>=0&&p.cursor<=p.nodes.length);
  assert(Number.isSafeInteger(p.candidates)&&p.candidates>=0&&Number.isSafeInteger(p.retained)&&p.retained>=0);
  assert.deepEqual(p.nodes[0],{state:ROOT,parent:-1,digits:[]});const seen=new Set();
  for(let i=0;i<p.nodes.length;i++){
    const n=p.nodes[i],s=n.state;assert(s.length===5&&s.every(Number.isInteger));assert(s[0]>=0&&s[0]<=3&&s[1]>=0&&s[1]<5&&s[2]>=0&&s[2]<5);
    assert(s[3]>=0&&s[3]<VECTORS.length&&s[4]>=0&&s[4]<VECTORS.length);assert(norm(VECTORS[s[4]].map((x,r)=>x-VECTORS[s[3]][r]))<=95);
    assert(!seen.has(key(s)));seen.add(key(s));
    if(i){assert(n.parent>=0&&n.parent<i&&Number.isInteger(n.parent));assert(n.digits.length===3&&n.digits.every(x=>Number.isInteger(x)&&x>=0&&x<14));assert.deepEqual(s,directChild(p.nodes[n.parent].state,n.digits));}
  }
  if(p.status==='closed'){assert.equal(p.cursor,p.nodes.length);assert(p.nodes.every(n=>!accepting(n.state)));}
}
function witness(nodes,id){
  const digits=[];for(let i=id;i;i=nodes[i].parent)digits.push(nodes[i].digits);digits.reverse();
  const indices=[0n,0n,0n];for(const row of digits)for(let r=0;r<3;r++)indices[r]=14n*indices[r]+BigInt(row[r]);
  const F=indices.map(prefixAt),C=F.map((v,j)=>v.map(x=>5n*x-indices[j]));
  assert(indices[0]<indices[1]&&indices[1]<indices[2]);assert.deepEqual(C[0],C[1]);assert.deepEqual(C[1],C[2]);
  return {digits,indices:indices.map(String),counts:F.map(v=>v.map(String)),centeredCounts:C[0].map(String)};
}
function durable(file,text,append=false){fs.mkdirSync(path.dirname(file),{recursive:true});const dest=append?file:`${file}.tmp-${process.pid}`;
  const fd=fs.openSync(dest,append?'a':'w',0o600);try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}if(!append)fs.renameSync(dest,file);}
async function main(){
  const {values}=parseArgs({options:{'state-dir':{type:'string',default:'.checkpoint-shallit-centered-returns'},seconds:{type:'string',default:'120'},
    'max-states':{type:'string',default:'300000'},output:{type:'string',default:new URL('checks/shallit-centered-returns.json',import.meta.url).pathname},help:{type:'boolean',short:'h'}}});
  if(values.help){console.log('Exact finite centered-prefix triple-return automaton. Does not certify all directions.\n'
    +'--state-dir DIR --seconds 1..600 --max-states 1..1100000 --output FILE\nAtomic queue checkpoints bind source/dependency hashes and checksum.\n'
    +'Resume at completed-parent boundaries; budgets may change. SIGINT/SIGTERM checkpoint. One JS worker, 512 MiB RSS guard.');return;}
  const seconds=Number(values.seconds),maxStates=Number(values['max-states']);assert(Number.isInteger(seconds)&&seconds>=1&&seconds<=600);
  assert(Number.isInteger(maxStates)&&maxStates>=1&&maxStates<=1100000);
  const directory=path.resolve(values['state-dir']),checkpoint=path.join(directory,'state.json'),log=path.join(directory,'run.jsonl'),output=path.resolve(values.output);
  assert(![checkpoint,log].includes(output));
  const identity={schema:1,model:'three-equal-centered-prefixes',codeSha256:hash(fs.readFileSync(source)),dependencySha256:hash(fs.readFileSync(new URL('shallit_ratio_automaton.mjs',import.meta.url))),scaledPairNormSquaredLimit:95};
  const event=(type,fields={})=>{const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';durable(log,line,true);process.stderr.write(line);};
  try{
    let p={nodes:[{state:ROOT.slice(),parent:-1,digits:[]}],cursor:0,candidates:0,retained:0,status:'running'};const resumed=fs.existsSync(checkpoint);
    if(resumed){const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));assert.deepEqual(saved.identity,identity,'incompatible checkpoint');assert.equal(saved.checksum,hash(JSON.stringify(saved.progress)),'corrupt checkpoint');p=saved.progress;validateProgress(p);}
    const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:hash(JSON.stringify(p)),progress:p})+'\n');
    let stopped=false,budget=null;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
    const seen=new Set(p.nodes.map(n=>key(n.state))),edgesFor=transitionFactory(),start=performance.now(),initial=p.cursor;let lastLog=start;
    const report=()=>{const elapsed=(performance.now()-start)/1000,rate=(p.cursor-initial)/Math.max(.001,elapsed);return {completedStates:p.cursor,discoveredStates:p.nodes.length,finiteUniverseUpperBound:4*25*10171,
      candidates:p.candidates,retainedTransitions:p.retained,statesPerSecond:rate,elapsedSeconds:elapsed,queueEtaSeconds:rate?(p.nodes.length-p.cursor)/rate:null,checkpoint,rssBytes:process.memoryUsage().rss};};
    event(resumed?'resume':'start',{...identity,...report(),seconds,maxStates,workers:1});save();
    while(p.status==='running'&&p.cursor<p.nodes.length&&!stopped&&performance.now()-start<seconds*1000){
      if(p.nodes.length>=maxStates){budget='state_budget';break;}const parent=p.cursor,{edges,candidates}=edgesFor(p.nodes[parent].state);p.candidates+=candidates;
      for(const edge of edges){p.retained++;const k=key(edge.state);if(seen.has(k))continue;
        seen.add(k);const id=p.nodes.length;p.nodes.push({...edge,parent});
        if(accepting(edge.state)){p.witness=witness(p.nodes,id);p.status='counterexample';break;}}
      p.cursor++;
      if(p.cursor%64===0)await new Promise(resolve=>setImmediate(resolve));
      if(performance.now()-lastLog>=5000){save();event('progress',report());lastLog=performance.now();if(process.memoryUsage().rss>536870912){budget='memory_budget';break;}}
    }
    if(p.status==='running'&&p.cursor===p.nodes.length)p.status='closed';save();
    const outcome=p.status==='running'?(stopped?'interrupted':budget??'time_budget'):p.status;
    const result={...identity,outcome,states:p.nodes.length,completedStates:p.cursor,candidateTransitions:p.candidates,retainedTransitions:p.retained,
      vectorCount:VECTORS.length,certifiesUniformDirectionAvoidance:p.status==='closed',certifiesAllDirections:false,
      scope:'Only a closed invariant excludes three equal centered prefixes, equivalently collinearity parallel to (1,1,1,1,1), at all lengths and ratios. Not full 5D avoidance.'};
    if(p.status==='closed'){result.vectors=VECTORS;result.closedStates=p.nodes.map(n=>n.state);}if(p.witness)result.witness=p.witness;
    durable(output,JSON.stringify(result)+'\n');event(outcome,{...report(),output});if(stopped)process.exitCode=130;
  }catch(error){event('error',{message:error.message,checkpoint});throw error;}
}
if(process.argv[1]&&path.resolve(process.argv[1])===source)main().catch(error=>{console.error(error.message);process.exitCode=1;});
