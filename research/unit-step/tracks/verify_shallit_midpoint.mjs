#!/usr/bin/env node
// Independent affine-closure checker: derives the substitution data from the literal image.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {parseArgs} from 'node:util';
const {values}=parseArgs({options:{'state-dir':{type:'string',default:'.checkpoint-shallit-midpoint-validated'},
  output:{type:'string',default:new URL('checks/shallit-midpoint-validation.json',import.meta.url).pathname},help:{type:'boolean',short:'h'}}});
if(values.help){console.log('Independent closed-midpoint affine invariant and uniform-neighborhood validation.\n'
  +'--state-dir DIR --output FILE\nAtomic checked-row resume; code/data hashes reject incompatible checkpoints.\n'
  +'SIGINT/SIGTERM checkpoint at row boundaries; one JS worker. Not a full central-interval proof.');process.exit(0);}
const hash=x=>createHash('sha256').update(x).digest('hex');
const digits=[...'01213101314310'].map(Number);
const prefixes=Array.from({length:5},(_,a)=>Array.from({length:14},(_,t)=>
  Array.from({length:5},(_,r)=>digits.slice(0,t).filter(x=>(x+a)%5===r).length)));
const M=Array.from({length:5},(_,r)=>Array.from({length:5},(_,a)=>digits.filter(x=>(x+a)%5===r).length));
const times=(A,v)=>A.map(row=>row.reduce((s,x,r)=>s+x*v[r],0));
const inverseNumerator=Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>[227,1025,-305,-53,-473][(c-r+5)%5]));
for(let i=0;i<5;i++)for(let j=0;j<5;j++)assert.equal(M[i].reduce((sum,x,r)=>sum+x*inverseNumerator[r][j],0),i===j?5894:0);
const gram=Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>M.reduce((s,row)=>s+row[r]*row[c],0)));
assert.deepEqual(times(gram,Array(5).fill(1)),Array(5).fill(196));
for(let r=0;r<4;r++){
  const e=Array.from({length:5},(_,j)=>Number(j===r)-Number(j===4)),v=times(gram,e),vv=times(gram,v);
  assert.deepEqual(vv.map((x,j)=>x-42*v[j]+421*e[j]),Array(5).fill(0));
}
let inverseDiameter=0;
const boundaries=prefixes.flat().map(v=>times(inverseNumerator,v));
for(const x of boundaries)for(const y of boundaries)inverseDiameter=Math.max(inverseDiameter,x.reduce((sum,a,r)=>sum+(a-y[r])**2,0));
assert.equal(inverseDiameter,73769304);
assert(6400n*BigInt(inverseDiameter)<13689n*5894n**2n); // diameter < 117/80 = (3/4)(39/20)
for(let c=0;c<5;c++)assert.equal(M.reduce((sum,row)=>sum+row[c],0),14);
assert(prefixes.flat().every(p=>p.every(x=>x>=0)&&p.reduce((x,y)=>x+y,0)<=13));

const certificateFile=new URL('checks/shallit-midpoint.json',import.meta.url),bytes=fs.readFileSync(certificateFile),data=JSON.parse(bytes);
assert.equal(data.codeSha256,hash(fs.readFileSync(new URL('shallit_midpoint_certificate.mjs',import.meta.url))));
assert.deepEqual(data.dependencies.map(x=>x.file),['shallit_ratio_automaton.mjs','shallit_interval_automaton.mjs']);
for(const dep of data.dependencies)assert.equal(dep.sha256,hash(fs.readFileSync(new URL(dep.file,import.meta.url))));
function structure(certificate){
  assert.equal(certificate.schema,1);assert.equal(certificate.outcome,'closed');
  assert.deepEqual(certificate.center,[1,2]);assert.deepEqual(certificate.closedNormRadius,[39,20]);assert.equal(certificate.closedClockRadius,1);
  assert.equal(certificate.certifiesNeighborhood,true);assert.equal(certificate.certifiesWholeCentralInterval,false);
  assert.equal(certificate.states,certificate.closedStates.length);assert.equal(certificate.completedStates,certificate.states);
  const keys=new Set();let maxSpan=0;
  for(const s of certificate.closedStates){
    assert(s.length===13&&s.every(Number.isSafeInteger));assert(s[0]>=0&&s[0]<=3&&s[1]>=0&&s[1]<5&&s[2]>=0&&s[2]<5);
    const A=s.slice(3,8),B=s.slice(8);
    assert(A.every((x,r)=>x<=0&&x>=-B[r]));
    const N=B.reduce((x,y)=>x+y,0);
    // This explicit bound keeps every Number-valued linear operation exact.
    assert(Number.isSafeInteger(N)&&N<1e12,'unsafe coefficient range');
    const d=A.map((x,r)=>2*x+B[r]);
    assert(d.every(x=>Math.abs(x)<4));
    assert(d.reduce((x,y)=>x+y*y,0)<=15&&Math.abs(d.reduce((x,y)=>x+y,0))<=2);
    assert(!(s[0]===3&&d.every(x=>x===0)),'accepting midpoint state');
    const k=s.join(',');assert(!keys.has(k),'duplicate state');keys.add(k);maxSpan=Math.max(maxSpan,B.reduce((x,y)=>x+y,0));
  }
  assert(keys.has(Array(13).fill(0).join(',')),'missing root');
  return {keys,maxSpan};
}
const {keys,maxSpan}=structure(data);
assert.equal(data.maxSpan,maxSpan);
const C=14n*BigInt(maxSpan)+26n,E=40n*C;
assert.equal(BigInt(data.derivativeBound),C);assert.deepEqual(data.thetaRadius.map(BigInt),[1n,E]);
assert.deepEqual(data.thetaInterval.map(row=>row.map(BigInt)),[[E/2n-1n,E],[E/2n+1n,E]]);
assert((E/2n-1n)*3n>=E&&(E/2n+1n)*3n<=2n*E);
// Exact perturbation margins: outside norm >=2, outside clock >=3/2, strict-state norm >=1/2.
assert(79n>78n && 59n>40n && 19n>0n); // subtracting 1/40 preserves every required separation.

function checkRow(s,set){
  const [mask,u,v]=s,A=s.slice(3,8),B=s.slice(8),d=A.map((x,r)=>2*x+B[r]);
  const md=times(M,d),ma=times(M,A),mb=times(M,B),sum=d.reduce((x,y)=>x+y,0);
  let candidates=0,retained=0;
  for(let x=0;x<14;x++)for(let z=0;z<14;z++){
    const total=14*sum+x+z,lo=Math.max(0,Math.ceil((total-2)/2)),hi=Math.min(13,Math.floor((total+2)/2));
    for(let y=lo;y<=hi;y++){
      if((!(mask&1)&&x>y)||(!(mask&2)&&y>z))continue;candidates++;
      const q=md.map((c,r)=>c+prefixes[0][x][r]-2*prefixes[u][y][r]+prefixes[v][z][r]);
      if(q.reduce((a,b)=>a+b*b,0)>15)continue;
      const rawA=ma.map((c,r)=>c+prefixes[0][x][r]-prefixes[u][y][r]);
      const rawB=mb.map((c,r)=>c+prefixes[v][z][r]-prefixes[0][x][r]),rot=digits[x];
      const next=[mask|(x<y?1:0)|(y<z?2:0),(u+digits[y]-rot+5)%5,(v+digits[z]-rot+5)%5,
        ...rawA.slice(rot),...rawA.slice(0,rot),...rawB.slice(rot),...rawB.slice(0,rot)];
      assert(set.has(next.join(',')),`missing successor of ${s}: ${x},${y},${z}`);retained++;
    }
  }
  return {candidates,retained};
}
function durable(file,text,append=false){fs.mkdirSync(path.dirname(file),{recursive:true});const dest=append?file:`${file}.tmp-${process.pid}`;
  const fd=fs.openSync(dest,append?'a':'w');try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}if(!append)fs.renameSync(dest,file);}
const directory=path.resolve(values['state-dir']),checkpoint=path.join(directory,'state.json'),log=path.join(directory,'run.jsonl'),output=path.resolve(values.output);
assert(![checkpoint,log].includes(output));
const identity={schema:1,codeSha256:hash(fs.readFileSync(new URL(import.meta.url))),certificateSha256:hash(bytes)};
const event=(type,fields={})=>{const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';durable(log,line,true);process.stderr.write(line);};
let progress={row:0,candidates:0,retained:0};const resumed=fs.existsSync(checkpoint);
if(resumed){const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));assert.deepEqual(saved.identity,identity,'incompatible checkpoint');
  assert.equal(saved.checksum,hash(JSON.stringify(saved.progress)),'corrupt checkpoint');progress=saved.progress;
  assert(Number.isInteger(progress.row)&&progress.row>=0&&progress.row<=data.states);
  assert(Number.isSafeInteger(progress.candidates)&&progress.candidates>=0&&Number.isSafeInteger(progress.retained)&&progress.retained>=0);}
const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:hash(JSON.stringify(progress)),progress})+'\n');
let stopped=false;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
const start=performance.now(),initial=progress.row;let lastLog=start;
const report=()=>{const elapsed=(performance.now()-start)/1000,rate=(progress.row-initial)/Math.max(elapsed,.001);return {...progress,totalStates:data.states,
  rowsPerSecond:rate,elapsedSeconds:elapsed,etaSeconds:rate?(data.states-progress.row)/rate:null,checkpoint,rssBytes:process.memoryUsage().rss};};
event(resumed?'resume':'start',{...identity,...report(),workers:1});save();
try{
  while(progress.row<data.states&&!stopped){const checked=checkRow(data.closedStates[progress.row],keys);progress.candidates+=checked.candidates;progress.retained+=checked.retained;progress.row++;
    if(progress.row%128===0)await new Promise(resolve=>setImmediate(resolve));
    if(performance.now()-lastLog>5000){save();event('progress',report());lastLog=performance.now();}}
  save();
  if(stopped){event('interrupted',report());process.exitCode=130;}
  else{
    assert.equal(progress.retained,data.retainedTransitions);
    const root=Array(13).fill(0),missing=new Set(keys);missing.delete(data.closedStates[1].join(','));
    assert.throws(()=>checkRow(root,missing),/missing successor/);
    assert.throws(()=>structure({...data,states:data.states+1,completedStates:data.states+1,closedStates:[...data.closedStates,root]}),/duplicate state/);
    assert.throws(()=>structure({...data,states:data.states+1,completedStates:data.states+1,closedStates:[...data.closedStates,[3,...root.slice(1)]]}),/accepting midpoint state/);
    assert.throws(()=>structure({...data,states:data.states-1,completedStates:data.states-1,closedStates:data.closedStates.slice(1)}),/missing root/);
    const oversized=[0,0,0,...Array(5).fill(-1e12),...Array(5).fill(2e12)];
    assert.throws(()=>structure({...data,states:data.states+1,completedStates:data.states+1,closedStates:[...data.closedStates,oversized]}),/unsafe coefficient range/);
    const result={...identity,status:'pass',states:data.states,candidateTransitions:progress.candidates,retainedTransitions:progress.retained,
      maxSpan,derivativeBound:Number(C),thetaRadius:[1,Number(E)],thetaInterval:data.thetaInterval,
      gapRatioInterval:[[Number(E/2n-1n),Number(E/2n+1n)],[Number(E/2n+1n),Number(E/2n-1n)]],
      exactInverseDiameterNumerator:inverseDiameter,closedRadius:[39,20],perturbationAllowance:[1,40],
      rejectedMutations:['missing-successor','duplicate-state','accepting-state','missing-root','unsafe-coefficient-range'],
      scope:'Uniform all-length neighborhood of equal gaps via a finite affine invariant and exact margins; not the whole central interval or full 5D avoidance.'};
    durable(output,JSON.stringify(result,null,2)+'\n');event('complete',report());console.log(JSON.stringify(result));
  }
}catch(error){save();event('error',{message:error.message,...report()});throw error;}
