#!/usr/bin/env node
// Independent literal-image derivation and closed-interval invariant checker.
import assert from 'node:assert/strict';import fs from 'node:fs';import path from 'node:path';
import {createHash} from 'node:crypto';import {parseArgs} from 'node:util';import {fileURLToPath} from 'node:url';
const source=fileURLToPath(import.meta.url),hash=x=>createHash('sha256').update(x).digest('hex');
const image=[...'01213101314310'].map(Number);
const prefix=Array.from({length:5},(_,a)=>Array.from({length:14},(_,t)=>Array.from({length:5},(_,r)=>image.slice(0,t).filter(x=>(x+a)%5===r).length)));
const matrix=Array.from({length:5},(_,r)=>Array.from({length:5},(_,a)=>image.filter(x=>(x+a)%5===r).length));
const times=v=>matrix.map(row=>row.reduce((sum,x,r)=>sum+x*v[r],0));
const compare=(a,b,c,d)=>{const x=a*d,y=c*b;if(Number.isSafeInteger(x)&&Number.isSafeInteger(y))return x<y?-1:x>y?1:0;
  const X=BigInt(a)*BigInt(d),Y=BigInt(c)*BigInt(b);return X<Y?-1:X>Y?1:0;};
export function feasible(A,B,I){
  const N=B.reduce((a,b)=>a+b,0),p=-A.reduce((a,b)=>a+b,0);if(!N)return A.every(x=>x===0);
  const lower=[[I[0],I[1]],[p-1,N]],upper=[[I[2],I[3]],[p+1,N]];
  for(let r=0;r<5;r++)if(B[r]){lower.push([-39-20*A[r],20*B[r]]);upper.push([39-20*A[r],20*B[r]]);}
  const lo=lower.reduce((x,y)=>compare(...x,...y)<0?y:x),hi=upper.reduce((x,y)=>compare(...x,...y)>0?y:x);
  if(compare(...lo,...hi)>0)return false;
  const a=A.map(BigInt),b=B.map(BigInt),dot=(x,y)=>x.reduce((sum,c,r)=>sum+c*y[r],0n);
  const aa=dot(a,a),ab=dot(a,b),bb=dot(b,b),L=lo.map(BigInt),H=hi.map(BigInt);
  if(-ab*L[1]>=L[0]*bb&&-ab*H[1]<=H[0]*bb)return 400n*(aa*bb-ab*ab)<=1521n*bb;
  const [n,d]=-ab*L[1]<L[0]*bb?L:H;
  return 400n*(aa*d*d+2n*ab*n*d+bb*n*n)<=1521n*d*d;
}
export function structure(data){
  assert.equal(data.schema,1);assert.equal(data.outcome,'closed');assert.equal(data.certifiesIntervalAvoidance,true);
  assert.deepEqual(data.closedNormRadius,[39,20]);assert.equal(data.closedClockRadius,1);
  const I=data.interval;assert(I.length===4&&I.every(x=>Number.isSafeInteger(x)&&x>0&&x<=2e9));
  assert(I[0]<I[1]&&I[2]<I[3]&&compare(...I.slice(0,2),...I.slice(2))<=0);
  assert.equal(data.states,data.closedStates.length);assert.equal(data.completedStates,data.states);
  const keys=new Set();let maxSpan=0;
  for(const s of data.closedStates){assert(s.length===13&&s.every(Number.isSafeInteger));const [mask,u,v]=s;
    assert(mask>=0&&mask<=3&&u>=0&&u<5&&v>=0&&v<5);
    const A=s.slice(3,8),B=s.slice(8);assert(A.every((x,r)=>x<=0&&x>=-B[r]));
    const N=B.reduce((a,b)=>a+b,0),p=-A.reduce((a,b)=>a+b,0);
    assert(Number.isSafeInteger(N)&&N<=1e12,'unsafe coefficient range');maxSpan=Math.max(maxSpan,N);
    assert((mask&1)?p>0:p===0);assert((mask&2)?p<N:p===N);
    if(!(mask&1))assert.equal(u,0);if(!(mask&2))assert.equal(u,v);
    if(mask===3&&compare(p,N,...I.slice(0,2))>=0&&compare(p,N,...I.slice(2))<=0)
      assert(A.some((x,r)=>BigInt(x)*BigInt(N)+BigInt(p)*BigInt(B[r])!==0n),'accepting state');
    const key=s.join(',');assert(!keys.has(key),'duplicate state');keys.add(key);
  }
  assert(keys.has(Array(13).fill(0).join(',')),'missing root');return {keys,maxSpan};
}
export function checkRow(s,I,keys){
  const [mask,u,v]=s,A=s.slice(3,8),B=s.slice(8),ma=times(A),mb=times(B);
  const N=B.reduce((a,b)=>a+b,0),p=-A.reduce((a,b)=>a+b,0);let candidates=0,retained=0;
  // Enumerate all digits, rather than importing the producer's clock-strip iterator.
  for(let x=0;x<14;x++)for(let y=0;y<14;y++)for(let z=0;z<14;z++){
    if((!(mask&1)&&x>y)||(!(mask&2)&&y>z))continue;
    const nextN=14*N+z-x,nextP=14*p+y-x;
    if(nextN&&(compare(nextP-1,nextN,...I.slice(2))>0||compare(nextP+1,nextN,...I.slice(0,2))<0))continue;
    candidates++;
    const a=ma.map((c,r)=>c+prefix[0][x][r]-prefix[u][y][r]),b=mb.map((c,r)=>c+prefix[v][z][r]-prefix[0][x][r]);
    if(!feasible(a,b,I))continue;
    const r=image[x],next=[mask|(x<y?1:0)|(y<z?2:0),(u+image[y]-r+5)%5,(v+image[z]-r+5)%5,
      ...a.slice(r),...a.slice(0,r),...b.slice(r),...b.slice(0,r)];
    assert(keys.has(next.join(',')),`missing successor: ${s}; digits ${x},${y},${z}`);retained++;
  }
  return {candidates,retained};
}
function durable(file,text,append=false){fs.mkdirSync(path.dirname(file),{recursive:true});const dest=append?file:`${file}.tmp-${process.pid}`;
  const fd=fs.openSync(dest,append?'a':'w',0o600);try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}if(!append)fs.renameSync(dest,file);}
async function main(){
  const {values}=parseArgs({options:{input:{type:'string',default:new URL('checks/shallit-extension-100.json',import.meta.url).pathname},
    'state-dir':{type:'string'},output:{type:'string'},seconds:{type:'string',default:'300'},'max-rows':{type:'string'},help:{type:'boolean',short:'h'}}});
  if(values.help){console.log('Independent exact closed-interval invariant validation.\n--input FILE --state-dir DIR --output FILE --seconds 1..600 --max-rows N\n'
    +'Defaults derive checkpoint/output names from the input. Atomic row resume binds code and certificate hashes.\n'
    +'SIGINT/SIGTERM and time/row budgets checkpoint; only a complete check writes a passing summary. One worker.');return;}
  const seconds=Number(values.seconds),maxRows=values['max-rows']?Number(values['max-rows']):Infinity;
  assert(Number.isInteger(seconds)&&seconds>=1&&seconds<=600);assert(maxRows===Infinity||(Number.isInteger(maxRows)&&maxRows>=0));
  const input=path.resolve(values.input),base=path.basename(input,'.json'),directory=path.resolve(values['state-dir']??`.checkpoint-${base}-validation`);
  const checkpoint=path.join(directory,'state.json'),log=path.join(directory,'run.jsonl'),output=path.resolve(values.output??path.join(path.dirname(input),`${base}-validation.json`));
  assert(![input,checkpoint,log].includes(output));
  const bytes=fs.readFileSync(input),data=JSON.parse(bytes),{keys,maxSpan}=structure(data),I=data.interval;
  assert.equal(data.codeSha256,hash(fs.readFileSync(new URL('shallit_interval_extension.mjs',import.meta.url))));
  assert.deepEqual(data.dependencies.map(x=>x.file),['shallit_ratio_automaton.mjs','shallit_interval_automaton.mjs']);
  for(const dep of data.dependencies)assert.equal(dep.sha256,hash(fs.readFileSync(new URL(dep.file,import.meta.url))));
  // Exact sharpened descent constants, independently checked in the midpoint validator.
  const inv=Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>[227,1025,-305,-53,-473][(c-r+5)%5]));
  for(let r=0;r<5;r++)for(let c=0;c<5;c++)assert.equal(matrix[r].reduce((sum,x,j)=>sum+x*inv[j][c],0),r===c?5894:0);
  const G=Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>matrix.reduce((sum,row)=>sum+row[r]*row[c],0)));
  const mv=(m,v)=>m.map(row=>row.reduce((sum,x,j)=>sum+x*v[j],0));assert.deepEqual(mv(G,Array(5).fill(1)),Array(5).fill(196));
  for(let r=0;r<4;r++){const e=Array.from({length:5},(_,j)=>Number(j===r)-Number(j===4)),v=mv(G,e);assert.deepEqual(mv(G,v).map((x,j)=>x-42*v[j]+421*e[j]),Array(5).fill(0));}
  const Q=prefix.flat().map(v=>mv(inv,v));let diameter=0;for(const x of Q)for(const y of Q)diameter=Math.max(diameter,x.reduce((sum,a,r)=>sum+(a-y[r])**2,0));
  assert.equal(diameter,73769304);assert(6400n*BigInt(diameter)<13689n*5894n**2n);
  const identity={schema:1,codeSha256:hash(fs.readFileSync(source)),certificateSha256:hash(bytes)};
  const event=(type,fields={})=>{const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';durable(log,line,true);process.stderr.write(line);};
  let p={row:0,candidates:0,retained:0};const resumed=fs.existsSync(checkpoint);
  if(resumed){const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));assert.deepEqual(saved.identity,identity,'incompatible checkpoint');
    assert.equal(saved.checksum,hash(JSON.stringify(saved.progress)),'corrupt checkpoint');p=saved.progress;
    assert(Number.isInteger(p.row)&&p.row>=0&&p.row<=data.states&&Number.isSafeInteger(p.candidates)&&p.candidates>=0&&Number.isSafeInteger(p.retained)&&p.retained>=0);}
  const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:hash(JSON.stringify(p)),progress:p})+'\n');
  let stopped=false;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
  const start=performance.now(),initial=p.row;let lastLog=start;
  const report=()=>{const elapsed=(performance.now()-start)/1000,rate=(p.row-initial)/Math.max(elapsed,.001);return {...p,totalStates:data.states,rowsPerSecond:rate,
    elapsedSeconds:elapsed,etaSeconds:rate?(data.states-p.row)/rate:null,checkpoint,rssBytes:process.memoryUsage().rss};};
  event(resumed?'resume':'start',{...identity,...report(),seconds,maxRows:Number.isFinite(maxRows)?maxRows:null,workers:1});save();
  try{
    while(p.row<data.states&&p.row-initial<maxRows&&!stopped&&performance.now()-start<seconds*1000){
      const checked=checkRow(data.closedStates[p.row],I,keys);p.candidates+=checked.candidates;p.retained+=checked.retained;p.row++;
      if(p.row%16===0)await new Promise(resolve=>setImmediate(resolve));
      if(performance.now()-lastLog>=5000){save();event('progress',report());lastLog=performance.now();}
    }
    save();if(p.row<data.states){event(stopped?'interrupted':'budget',report());if(stopped)process.exitCode=130;return;}
    assert.equal(p.candidates,data.testedTransitions);
    const root=Array(13).fill(0),missing=new Set(keys);missing.delete(data.closedStates[1].join(','));
    assert.throws(()=>checkRow(root,I,missing),/missing successor/);
    assert.throws(()=>structure({...data,states:data.states+1,completedStates:data.states+1,closedStates:[...data.closedStates,root]}),/duplicate state/);
    assert.throws(()=>structure({...data,states:data.states-1,completedStates:data.states-1,closedStates:data.closedStates.slice(1)}),/missing root/);
    const zero=[3,0,0,-1,0,0,0,0,2,0,0,0,0];
    assert.throws(()=>structure({...data,states:data.states+1,completedStates:data.states+1,closedStates:[...data.closedStates,zero]}),/accepting state/);
    const result={...identity,status:'pass',interval:I,states:data.states,candidateTransitions:p.candidates,retainedTransitions:p.retained,maxSpan,
      gapRatioInterval:[[I[0],I[1]-I[0]],[I[2],I[3]-I[2]]],
      rejectedMutations:['missing-successor','duplicate-state','missing-root','accepting-state'],
      scope:'Exact finite affine invariant for the entire displayed parameter interval, at all positions and lengths; not an all-ratios 5D proof.'};
    durable(output,JSON.stringify(result,null,2)+'\n');event('complete',report());console.log(JSON.stringify(result));
  }catch(error){save();event('error',{message:error.message,...report()});throw error;}
}
if(process.argv[1]&&path.resolve(process.argv[1])===source)main().catch(error=>{console.error(error.message);process.exitCode=1;});
