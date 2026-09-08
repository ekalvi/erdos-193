#!/usr/bin/env node
// Independent literal-image checker for centered triple returns and missing-letter factors.
import assert from 'node:assert/strict';import fs from 'node:fs';import path from 'node:path';
import {createHash} from 'node:crypto';import {fileURLToPath} from 'node:url';import {parseArgs} from 'node:util';
const source=fileURLToPath(import.meta.url),hash=x=>createHash('sha256').update(x).digest('hex');
const image=[...'01213101314310'].map(Number),expand=w=>w.flatMap(a=>image.map(x=>(x+a)%5));
const matrix=Array.from({length:5},(_,r)=>Array.from({length:5},(_,a)=>image.filter(x=>(x+a)%5===r).length));
const prefix=Array.from({length:5},(_,a)=>Array.from({length:14},(_,t)=>Array.from({length:5},(_,r)=>image.slice(0,t).filter(x=>(x+a)%5===r).length)));
const multiply=(m,v)=>m.map(row=>row.reduce((sum,x,j)=>sum+x*v[j],0)),norm=v=>v.reduce((sum,x)=>sum+x*x,0);
export function structure(data){
  assert.equal(data.schema,1);assert.equal(data.model,'three-equal-centered-prefixes');assert.equal(data.outcome,'closed');
  assert.equal(data.scaledPairNormSquaredLimit,95);assert.equal(data.certifiesUniformDirectionAvoidance,true);assert.equal(data.certifiesAllDirections,false);
  assert.equal(data.states,data.closedStates.length);assert.equal(data.completedStates,data.states);assert.equal(data.vectorCount,data.vectors.length);
  const vectorKeys=new Set();for(const v of data.vectors){assert(v.length===5&&v.every(x=>Number.isInteger(x)&&Math.abs(x)<=9));
    assert.equal(v.reduce((a,b)=>a+b,0),0);assert(norm(v)<=95);assert(v.every(x=>(x-v[0])%5===0));assert(!vectorKeys.has(v.join(',')));vectorKeys.add(v.join(','));}
  // Different exhaustive lattice enumeration from the producer's residue-class loops.
  let latticeCount=0;for(let a=-9;a<=9;a++)for(let b=-9;b<=9;b++)for(let c=-9;c<=9;c++)for(let d=-9;d<=9;d++){
    const e=-a-b-c-d,v=[a,b,c,d,e];if(Math.abs(e)>9||v.some(x=>(x-a)%5!==0)||norm(v)>95)continue;
    latticeCount++;assert(vectorKeys.has(v.join(',')));
  }
  assert.equal(latticeCount,data.vectors.length);assert.equal(latticeCount,161);
  const zero=data.vectors.findIndex(v=>v.every(x=>x===0)),root=[0,0,0,zero,zero],keys=new Set();
  for(const s of data.closedStates){assert(s.length===5&&s.every(Number.isInteger));const [m,u,v,a,b]=s;
    assert(m>=0&&m<=3&&u>=0&&u<5&&v>=0&&v<5&&a>=0&&a<data.vectorCount&&b>=0&&b<data.vectorCount);
    assert(norm(data.vectors[b].map((x,r)=>x-data.vectors[a][r]))<=95);
    if(!(m&1)){assert.equal(a,zero);assert.equal(u,0);}if(!(m&2)){assert.equal(a,b);assert.equal(u,v);}
    assert(!(m===3&&a===zero&&b===zero),'accepting state');assert(!keys.has(s.join(',')),'duplicate state');keys.add(s.join(','));
  }
  assert(keys.has(root.join(',')),'missing root');return {zero,root,keys};
}
export function checkRow(s,data,keys){
  const [mask,u,v,a,b]=s,X=data.vectors[a],Y=data.vectors[b],mx=multiply(matrix,X),my=multiply(matrix,Y);
  const index=new Map(data.vectors.map((v,i)=>[v.join(','),i]));let candidates=0,retained=0;
  for(let x=0;x<14;x++)for(let y=0;y<14;y++){
    if(!(mask&1)&&x>y)continue;
    const A=mx.map((q,r)=>q+5*prefix[u][y][r]-5*prefix[0][x][r]-y+x);if(norm(A)>95)continue;
    for(let z=0;z<14;z++){
      if(!(mask&2)&&y>z)continue;
      const B=my.map((q,r)=>q+5*prefix[v][z][r]-5*prefix[0][x][r]-z+x);if(norm(B)>95)continue;candidates++;
      if(norm(B.map((q,r)=>q-A[r]))>95)continue;
      const rotation=image[x],a=index.get(A.map((_,r)=>A[(r+rotation)%5]).join(',')),b=index.get(B.map((_,r)=>B[(r+rotation)%5]).join(','));
      assert(a!==undefined&&b!==undefined);
      const child=[mask|(x<y?1:0)|(y<z?2:0),(u+image[y]-rotation+5)%5,(v+image[z]-rotation+5)%5,a,b];
      assert(keys.has(child.join(',')),`missing successor: ${s}; digits ${x},${y},${z}`);retained++;
    }
  }
  return {candidates,retained};
}
export function missingLetterTemplates(){
  assert(image[0]===0&&image.at(-1)===0&&image.every((x,i)=>!i||x!==image[i-1]));assert.equal(new Set(image).size,5);
  const w=expand(expand([0])),pairs=new Set(w.slice(1).map((a,i)=>5*w[i]+a));assert.equal(pairs.size,20);
  assert([...pairs].every(x=>Math.floor(x/5)!==x%5));
  return [...pairs].sort((a,b)=>a-b).map(p=>({letters:[Math.floor(p/5),p%5],word:expand(expand([Math.floor(p/5),p%5]))}));
}
export function auditTemplate({letters,word}){
  const counts=[Array(5).fill(0)];for(const a of word){const next=counts.at(-1).slice();next[a]++;counts.push(next);}
  let triples=0,properSupportTriples=0;
  for(let i=0;i<word.length-1;i++)for(let k=i+2;k<=Math.min(i+26,word.length);k++){
    const total=counts[k].map((x,r)=>x-counts[i][r]),N=k-i;triples+=N-1;if(total.every(x=>x>0))continue;
    for(let j=i+1;j<k;j++){properSupportTriples++;const m=j-i;
      assert(total.some((x,r)=>N*(counts[j][r]-counts[i][r])!==m*x),`proper-support counterexample in ${letters}: ${i},${j},${k}`);}
  }
  return {triples,properSupportTriples};
}
function algebra(){
  const inv=Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>[227,1025,-305,-53,-473][(c-r+5)%5]));
  for(let r=0;r<5;r++)for(let c=0;c<5;c++)assert.equal(matrix[r].reduce((sum,x,j)=>sum+x*inv[j][c],0),r===c?5894:0);
  assert.deepEqual(multiply(matrix,Array(5).fill(1)),Array(5).fill(14));
  const G=Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>matrix.reduce((sum,row)=>sum+row[r]*row[c],0)));
  assert.deepEqual(multiply(G,Array(5).fill(1)),Array(5).fill(196));
  for(let r=0;r<4;r++){const e=Array.from({length:5},(_,j)=>Number(j===r)-Number(j===4)),v=multiply(G,e);
    assert.deepEqual(multiply(G,v).map((x,j)=>x-42*v[j]+421*e[j]),Array(5).fill(0));}
  const boundaries=prefix.flat().map(v=>multiply(inv,v));let diameter=0;
  for(const x of boundaries)for(const y of boundaries)diameter=Math.max(diameter,norm(x.map((a,r)=>a-y[r])));
  assert.equal(diameter,73769304);assert(6400n*BigInt(diameter)<13689n*5894n**2n);assert(95n*16n<1521n&&96n*16n>1521n);
}
function durable(file,text,append=false){fs.mkdirSync(path.dirname(file),{recursive:true});const dest=append?file:`${file}.tmp-${process.pid}`;
  const fd=fs.openSync(dest,append?'a':'w',0o600);try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}if(!append)fs.renameSync(dest,file);}
async function main(){
  const {values}=parseArgs({options:{'state-dir':{type:'string',default:'.checkpoint-shallit-centered-validated'},
    output:{type:'string',default:new URL('checks/shallit-centered-validation.json',import.meta.url).pathname},'max-units':{type:'string'},help:{type:'boolean',short:'h'}}});
  if(values.help){console.log('Independent centered-return certificate and missing-letter finite-language audit.\n--state-dir DIR --output FILE --max-units N\n'
    +'Atomic row/template resume binds code/data hashes and checksum. SIGINT/SIGTERM checkpoint; only completion writes a passing result. One worker.');return;}
  const maxUnits=values['max-units']?Number(values['max-units']):Infinity;assert(maxUnits===Infinity||(Number.isInteger(maxUnits)&&maxUnits>=0));
  const bytes=fs.readFileSync(new URL('checks/shallit-centered-returns.json',import.meta.url)),data=JSON.parse(bytes),{zero,root,keys}=structure(data);algebra();
  assert.equal(data.codeSha256,hash(fs.readFileSync(new URL('shallit_centered_returns.mjs',import.meta.url))));
  assert.equal(data.dependencySha256,hash(fs.readFileSync(new URL('shallit_ratio_automaton.mjs',import.meta.url))));
  const templates=missingLetterTemplates(),directory=path.resolve(values['state-dir']),checkpoint=path.join(directory,'state.json'),log=path.join(directory,'run.jsonl'),output=path.resolve(values.output);
  assert(![checkpoint,log,new URL('checks/shallit-centered-returns.json',import.meta.url).pathname].includes(output));
  const identity={schema:1,codeSha256:hash(fs.readFileSync(source)),certificateSha256:hash(bytes)};
  let p={row:0,template:0,candidates:0,retained:0,triples:0,properSupportTriples:0};const resumed=fs.existsSync(checkpoint);
  if(resumed){const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));assert.deepEqual(saved.identity,identity,'incompatible checkpoint');assert.equal(saved.checksum,hash(JSON.stringify(saved.progress)),'corrupt checkpoint');p=saved.progress;
    assert(Object.values(p).every(x=>Number.isSafeInteger(x)&&x>=0));assert(p.row<=data.states&&p.template<=templates.length);}
  const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:hash(JSON.stringify(p)),progress:p})+'\n');
  const event=(type,fields={})=>{const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';durable(log,line,true);process.stderr.write(line);};
  let stopped=false;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
  const start=performance.now(),initial=p.row+p.template;let lastLog=start;
  const report=()=>{const elapsed=(performance.now()-start)/1000,rate=(p.row+p.template-initial)/Math.max(.001,elapsed);return {...p,totalRows:data.states,totalTemplates:templates.length,
    unitsPerSecond:rate,elapsedSeconds:elapsed,etaSeconds:rate?(data.states+templates.length-p.row-p.template)/rate:null,checkpoint,rssBytes:process.memoryUsage().rss};};
  event(resumed?'resume':'start',{...identity,...report(),workers:1});save();
  try{
    while(p.row<data.states&&!stopped&&p.row+p.template-initial<maxUnits){
      const q=checkRow(data.closedStates[p.row],data,keys);p.candidates+=q.candidates;p.retained+=q.retained;p.row++;
      if(p.row%32===0)await new Promise(resolve=>setImmediate(resolve));
      if(performance.now()-lastLog>=5000){save();event('progress',report());lastLog=performance.now();}
    }
    while(p.row===data.states&&p.template<templates.length&&!stopped&&p.row+p.template-initial<maxUnits){
      const q=auditTemplate(templates[p.template]);p.triples+=q.triples;p.properSupportTriples+=q.properSupportTriples;p.template++;
      save();await new Promise(resolve=>setImmediate(resolve));
    }
    save();if(p.row<data.states||p.template<templates.length){event(stopped?'interrupted':'budget',report());if(stopped)process.exitCode=130;return;}
    assert.equal(p.candidates,data.candidateTransitions);assert.equal(p.retained,data.retainedTransitions);
    const missing=new Set(keys);missing.delete(data.closedStates[1].join(','));assert.throws(()=>checkRow(root,data,missing),/missing successor/);
    assert.throws(()=>structure({...data,states:data.states+1,completedStates:data.states+1,closedStates:[...data.closedStates,root]}),/duplicate state/);
    assert.throws(()=>structure({...data,states:data.states-1,completedStates:data.states-1,closedStates:data.closedStates.slice(1)}),/missing root/);
    assert.throws(()=>structure({...data,states:data.states+1,completedStates:data.states+1,closedStates:[...data.closedStates,[3,0,0,zero,zero]]}),/accepting state/);
    const word=expand(expand([0])),F=[Array(5).fill(0)];for(const a of word){const v=F.at(-1).slice();v[a]++;F.push(v);}
    const C=n=>F[n].map(x=>5*x-n);assert.deepEqual(C(67).map(x=>3*x),C(78).map(x=>2*x));assert(F[67].some((x,r)=>78*x!==67*F[78][r]));
    const result={...identity,status:'pass',uniformDirection:{states:data.states,latticeVectors:data.vectorCount,candidateTransitions:p.candidates,retainedTransitions:p.retained},
      properSupport:{templates:templates.length,maximumMissingLetterFactorLength:26,triplesConsidered:p.triples,properSupportTriplesChecked:p.properSupportTriples},
      strongerProjectionCounterexample:{indices:[0,67,78],counts:[F[0],F[67],F[78]],centeredNumerators:[2,3],collinearInOriginalWalk:false},
      rejectedMutations:['missing-successor','duplicate-state','missing-root','accepting-state'],
      scope:'At all ratios and positions, excludes uniform directions and directions missing a letter. Positive nonuniform directions remain open; not full 5D avoidance.'};
    durable(output,JSON.stringify(result,null,2)+'\n');event('complete',report());console.log(JSON.stringify(result));
  }catch(error){save();event('error',{message:error.message,...report()});throw error;}
}
if(process.argv[1]&&path.resolve(process.argv[1])===source)main().catch(error=>{console.error(error.message);process.exitCode=1;});
