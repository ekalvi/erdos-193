#!/usr/bin/env node
// Bounded exact algebra and recurrence tests. Fixed-ratio certificates are checked below.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import {parseArgs} from 'node:util';
import { IMAGE, M, ADJ, DEN, PREFIX, ROOT, multiply, child, prefixAt, inside, accepting,
  transitionFactory, fastChild, key, validateProgress } from './shallit_ratio_automaton.mjs';

const {values}=parseArgs({options:{'state-dir':{type:'string',default:'.checkpoint-shallit-ratio-validation'},
  output:{type:'string',default:new URL('checks/shallit-ratio-validation.json',import.meta.url).pathname},
  help:{type:'boolean',short:'h'}}});
if(values.help) {
  console.log('Independent exact fixed-ratio certificate validation, one JS worker.\n'
    +'--state-dir DIR --output FILE\n'
    +'Automatically resumes checked rows after identity/checksum validation; SIGINT/SIGTERM checkpoint.\n'
    +'Use a fresh state directory after code or certificate changes. No all-ratios claim is checked.');
  process.exit(0);
}
assert.equal(IMAGE.join(''),'01213101314310');
for(let a=0;a<5;a++) {
  const image=IMAGE.map(x=>(a+x)%5);
  for(let t=0;t<=14;t++) assert.deepEqual(PREFIX[a][t],Array.from({length:5},(_,r)=>image.slice(0,t).filter(x=>x===r).length));
  assert.deepEqual(M.map(row=>row[a]),PREFIX[a][14]);
}
for(let i=0;i<5;i++) for(let j=0;j<5;j++) {
  assert.equal(M[i].reduce((s,x,r)=>s+x*ADJ[r][j],0),i===j?DEN:0);
  assert.equal(ADJ[i].reduce((s,x,r)=>s+x*M[r][j],0),i===j?DEN:0);
}
const B=Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>M.reduce((s,row)=>s+row[r]*row[c],0)));
assert.deepEqual(multiply(B,Array(5).fill(1)),Array(5).fill(196));
for(let r=0;r<4;r++) {
  const v=Array.from({length:5},(_,j)=>Number(j===r)-Number(j===4)), bv=multiply(B,v), bbv=multiply(B,bv);
  assert.deepEqual(bbv.map((x,j)=>x-42*bv[j]+421*v[j]),Array(5).fill(0));
}
// On the sum-zero space the squared singular values are 21 +/- 2 sqrt(5) > 16.
assert(25>4*5); // 5 > 2 sqrt(5), so 21 - 2 sqrt(5) > 16.
let maximum=0, maximizingPair=null;
const inversePrefixes=[];
for(let a=0;a<5;a++)for(let t=0;t<14;t++)inversePrefixes.push({a,t,v:multiply(ADJ,PREFIX[a][t])});
for(const x of inversePrefixes)for(const y of inversePrefixes) {
  const squared=x.v.reduce((s,v,r)=>s+(v-y.v[r])**2,0);
  if(squared>maximum) {maximum=squared;maximizingPair=[[x.a,x.t],[y.a,y.t]];}
}
assert.equal(maximum,73769304);
assert(4*maximum<9*DEN*DEN); // diameter of M^-1(prefix set) is strictly below 3/2.

let word=[0];
for(let k=0;k<3;k++)word=word.flatMap(a=>IMAGE.map(x=>(a+x)%5));
const counts=[Array(5).fill(0)];
for(const a of word) {const p=counts.at(-1).slice();p[a]++;counts.push(p);}
for(let n=0;n<=word.length;n++)assert.deepEqual(prefixAt(n),counts[n].map(BigInt));
assert.equal(word.slice(52,57).join(''),'04213');
assert.deepEqual(counts[57].map((x,r)=>x-counts[52][r]),Array(5).fill(1));
assert.deepEqual(multiply(M,Array(5).fill(1)),Array(5).fill(14));
const normalized=(indices,a,b)=>{
  const [i,j,k]=indices, rotation=word[i];
  const d=counts[i].map((x,r)=>b*x-(a+b)*counts[j][r]+a*counts[k][r]);
  return [Number(i<j)+2*Number(j<k),(word[j]-rotation+5)%5,(word[k]-rotation+5)%5,
    ...d.map((_,r)=>d[(r+rotation)%5])];
};
let recurrences=0;
for(const [a,b] of [[1,1],[1,2],[2,1]]) {
  const choices=transitionFactory(a,b);
  for(let i=0;i<32;i++)for(let j=i;j<32;j++)for(let k=j;k<32;k++) {
    const indices=[i,j,k], parent=normalized(indices.map(x=>Math.floor(x/14)),a,b);
    assert.deepEqual(child(parent,indices.map(x=>x%14),a,b),normalized(indices,a,b));recurrences++;
  }
  for(const s of [ROOT,normalized([0,1,2],a,b),normalized([0,0,1],a,b),normalized([0,1,1],a,b)]) {
    if(!inside(s,a,b))continue;
    const edges=choices(s), direct=[];
    for(let i=0;i<14;i++)for(let j=0;j<14;j++)for(let k=0;k<14;k++) {
      const next=child(s,[i,j,k],a,b);
      if(next && Math.abs(next.slice(3).reduce((x,y)=>x+y,0))<a+b)direct.push([i,j,k].join(','));
    }
    assert.deepEqual(edges.map(edge=>edge.digits.join(',')),direct);
    for(const edge of edges)assert.deepEqual(fastChild(multiply(M,s.slice(3)),edge),child(s,edge.digits,a,b));
  }
}
validateProgress({nodes:[{state:ROOT,parent:-1,digits:[]}],cursor:0,transitions:0,status:'running'},1,1);
const algebra={inversePrefixDiameterSquaredNumerator:maximum,inversePrefixDenominator:DEN,
  maximizingPair,prefixesChecked:word.length+1,recurrencesChecked:recurrences};

// Independent closure check: solve the clock inequality for the middle digit,
// rather than using the producer's transition factory or its child function.
function structure(data) {
  assert.equal(data.schema,1);assert.equal(data.image0,'01213101314310');
  assert.equal(data.outcome,'closed');assert.equal(data.certifiesSpecifiedRatioAvoidance,true);
  assert.equal(data.certifiesAllRatios,false);assert.equal(data.normalizedErrorRadiusStrict,2);
  assert.equal(data.clockErrorBoundStrict,data.left+data.right);
  assert(Number.isInteger(data.left)&&data.left>0&&Number.isInteger(data.right)&&data.right>0);
  assert.equal(data.states,data.closedStates.length);assert.equal(data.completedStates,data.states);
  const states=new Set(), L=data.left+data.right;
  for(const s of data.closedStates) {
    assert(s.length===8&&s.every(Number.isSafeInteger));
    assert(s[0]>=0&&s[0]<=3&&s[1]>=0&&s[1]<5&&s[2]>=0&&s[2]<5);
    const d=s.slice(3);
    assert(d.reduce((x,y)=>x+y*y,0)<4*L*L&&Math.abs(d.reduce((x,y)=>x+y,0))<L);
    assert(!(s[0]===3&&d.every(x=>x===0)),'accepting state in certificate');
    const k=s.join(',');assert(!states.has(k),'duplicate state');states.add(k);
  }
  assert(states.has('0,0,0,0,0,0,0,0'),'missing root');
  return states;
}
function checkRow(data,s,states) {
  const [mask,u,v]=s, d=s.slice(3), a=data.left,b=data.right,L=a+b;
  const sum=d.reduce((x,y)=>x+y,0), md=M.map(row=>row.reduce((x,c,r)=>x+c*d[r],0));
  let candidates=0, retained=0;
  for(let i=0;i<14;i++)for(let k=0;k<14;k++) {
    const z=14*sum+b*i+a*k;
    const lo=Math.max(0,Math.ceil((z-L+1)/L)),hi=Math.min(13,Math.floor((z+L-1)/L));
    for(let j=lo;j<=hi;j++) {
      if((!(mask&1)&&i>j)||(!(mask&2)&&j>k))continue;
      candidates++;
      const raw=md.map((x,r)=>x+b*PREFIX[0][i][r]-L*PREFIX[u][j][r]+a*PREFIX[v][k][r]);
      if(raw.reduce((x,y)=>x+y*y,0)>=4*L*L)continue;
      const rotated=raw.slice(IMAGE[i]).concat(raw.slice(0,IMAGE[i]));
      const next=[mask|(i<j?1:0)|(j<k?2:0),(u+IMAGE[j]-IMAGE[i]+5)%5,(v+IMAGE[k]-IMAGE[i]+5)%5,...rotated];
      assert(states.has(next.join(',')),`missing child of ${s}: digits ${i},${j},${k}`);retained++;
    }
  }
  return {candidates,retained};
}

const hash=x=>createHash('sha256').update(x).digest('hex');
const files=['1-1','1-2','2-1'].map(r=>new URL(`checks/shallit-ratio-${r}.json`,import.meta.url));
const certificates=files.map(file=>{const bytes=fs.readFileSync(file);return {data:JSON.parse(bytes),sha256:hash(bytes)};});
const producerSha=hash(fs.readFileSync(new URL('shallit_ratio_automaton.mjs',import.meta.url)));
for(const {data} of certificates)assert.equal(data.codeSha256,producerSha);
const identity={schema:1,codeSha256:hash(fs.readFileSync(new URL(import.meta.url))),
  certificates:certificates.map(({data,sha256})=>({left:data.left,right:data.right,sha256}))};
const directory=path.resolve(values['state-dir']),checkpoint=path.join(directory,'state.json'),log=path.join(directory,'run.jsonl');
const output=path.resolve(values.output);
assert(![checkpoint,log].includes(output),'output must be separate from checkpoint/log');
fs.mkdirSync(directory,{recursive:true});
function durable(file,text,append=false) {
  fs.mkdirSync(path.dirname(file),{recursive:true});const target=append?file:`${file}.tmp-${process.pid}`;
  const fd=fs.openSync(target,append?'a':'w');try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  if(!append)fs.renameSync(target,file);
}
const event=(type,fields={})=>{const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';durable(log,line,true);process.stderr.write(line);};
let progress={file:0,row:0,candidates:0,retained:0,completed:[]};
const resumed=fs.existsSync(checkpoint);
if(resumed) {
  const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));
  assert.deepEqual(saved.identity,identity,'incompatible validator checkpoint');
  assert.equal(saved.checksum,hash(JSON.stringify(saved.progress)),'corrupt validator checkpoint');
  progress=saved.progress;
  assert(Number.isInteger(progress.file)&&progress.file>=0&&progress.file<=certificates.length);
  assert.equal(progress.completed.length,progress.file);
  assert(Number.isInteger(progress.row)&&progress.row>=0&&progress.row<=(certificates[progress.file]?.data.states??0));
  assert(Number.isSafeInteger(progress.candidates)&&progress.candidates>=0);
  assert(Number.isSafeInteger(progress.retained)&&progress.retained>=0);
}
const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:hash(JSON.stringify(progress)),progress})+'\n');
let stopped=false;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
const start=performance.now();let lastLog=start, rowsThisRun=0;
const report=()=>{const elapsed=(performance.now()-start)/1000,rate=rowsThisRun/Math.max(elapsed,.001);
  const remaining=certificates.slice(progress.file).reduce((s,x)=>s+x.data.states,0)-progress.row;
  return {completedCertificates:progress.file,totalCertificates:certificates.length,currentRow:progress.row,
    remainingRows:remaining,rowsPerSecond:rate,elapsedSeconds:elapsed,etaSeconds:rate?remaining/rate:null,
    checkpoint,rssBytes:process.memoryUsage().rss};};
event(resumed?'resume':'start',{...identity,...report(),workers:1});save();
try {
  while(progress.file<certificates.length&&!stopped) {
    const data=certificates[progress.file].data, states=structure(data);
    while(progress.row<data.states&&!stopped) {
      const result=checkRow(data,data.closedStates[progress.row],states);
      progress.candidates+=result.candidates;progress.retained+=result.retained;progress.row++;rowsThisRun++;
      if(progress.row%128===0)await new Promise(resolve=>setImmediate(resolve));
      if(performance.now()-lastLog>5000){save();event('progress',report());lastLog=performance.now();}
    }
    if(stopped)break;
    assert.equal(progress.candidates,data.candidateTransitions);
    progress.completed.push({left:data.left,right:data.right,states:data.states,
      candidateTransitions:progress.candidates,retainedTransitions:progress.retained});
    progress.file++;progress.row=0;progress.candidates=0;progress.retained=0;
    save();event('certificate_verified',report());
  }
  save();
  if(stopped){event('interrupted',report());process.exitCode=130;}
  else {
    // Mutation checks are small: removal of the first root successor must break closure.
    const data=certificates[0].data;
    assert.throws(()=>structure({...data,states:data.states-1,completedStates:data.states-1,closedStates:data.closedStates.slice(1)}),/missing root/);
    assert.throws(()=>structure({...data,states:data.states+1,completedStates:data.states+1,closedStates:[...data.closedStates,ROOT]}),/duplicate state/);
    assert.throws(()=>structure({...data,states:data.states+1,completedStates:data.states+1,closedStates:[...data.closedStates,[3,0,0,0,0,0,0,0]]}),/accepting state/);
    const missing=structure(data);missing.delete(data.closedStates[1].join(','));
    assert.throws(()=>checkRow(data,ROOT,missing),/missing child/);
    const result={...identity,status:'pass',algebra,certificatesVerified:progress.completed,
      rejectedMutations:['missing-root','duplicate-state','accepting-state','missing-successor'],
      scope:'Independent fixed-ratio invariant certificates plus exact descent identities; not all-ratios avoidance.'};
    durable(output,JSON.stringify(result,null,2)+'\n');
    event('complete',report());console.log(JSON.stringify(result));
  }
} catch(error){save();event('error',{message:error.message,...report()});throw error;}
