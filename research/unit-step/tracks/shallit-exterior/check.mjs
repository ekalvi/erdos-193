#!/usr/bin/env node
// Exact audit of a stopped all-ratios exterior-descent attempt, not a construction.
// One worker. Completed bounded phases resume from identity/checksum-checked state.
import assert from 'node:assert/strict';
import {parseArgs} from 'node:util';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,renameSync,mkdirSync,appendFileSync,existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const {values}=parseArgs({options:{checkpoint:{type:'string'},output:{type:'string'},'stop-after-phases':{type:'string',default:'0'},help:{type:'boolean'}}});
if(values.help){console.log(`Usage: node check.mjs [--checkpoint PATH] [--output PATH] [--stop-after-phases N]
One worker; exact matrix and polynomial identities, not ratio or prefix scans.
Atomic checksummed checkpoints bind code/config identity. Restart reuses completed
phases; incompatible/corrupt state is rejected. Budget/SIGINT/SIGTERM stops save
between bounded phases and exit 75 if work remains. Final output is idempotent.
No full avoidance certificate or changed minimum bound is claimed.`);process.exit(0);}
const here=fileURLToPath(new URL('./',import.meta.url)),root=path.resolve(here,'../../../..');
const hash=x=>createHash('sha256').update(x).digest('hex'),json=x=>JSON.stringify(x,(_,v)=>typeof v==='bigint'?v.toString():v);
const identity={schema:1,task:'exterior-descent-stopping-check',code_sha256:hash(readFileSync(new URL('check.mjs',import.meta.url))),word:'01213101314310'};
const scratch=path.join(root,'.checkpoint-shallit-exterior',hash(json(identity)).slice(0,16));mkdirSync(scratch,{recursive:true});
const checkpoint=values.checkpoint||path.join(scratch,'state.json'),output=values.output||path.join(here,'check.json');
const atomic=(file,value)=>{mkdirSync(path.dirname(file),{recursive:true});const temp=file+'.tmp';writeFileSync(temp,JSON.stringify(value,(_,v)=>typeof v==='bigint'?v.toString():v,2)+'\n');renameSync(temp,file);};
const log=row=>{const line=json({time:new Date().toISOString(),...row});appendFileSync(path.join(scratch,'run.jsonl'),line+'\n');console.log(line);};
let state={identity,completed:{}},stop=false;for(const sig of ['SIGINT','SIGTERM'])process.on(sig,()=>stop=true);
const save=()=>atomic(checkpoint,{state,sha256:hash(json(state))});
const started=performance.now();
try{
 const budget=Number(values['stop-after-phases']);assert(Number.isSafeInteger(budget)&&budget>=0);
 const resumed=existsSync(checkpoint);if(resumed){const e=JSON.parse(readFileSync(checkpoint));assert.equal(hash(json(e.state)),e.sha256,'Checkpoint checksum mismatch');assert.deepEqual(e.state.identity,identity,'Incompatible code/config checkpoint');assert(e.state.completed&&typeof e.state.completed==='object');const names=Object.keys(e.state.completed);assert.deepEqual(names,['matrix','family'].slice(0,names.length),'Invalid checkpoint phases');assert(names.length<=2);state=e.state;}
 const h=[...identity.word].map(Number),M=Array.from({length:5},(_,r)=>Array.from({length:5},(_,a)=>BigInt(h.filter(t=>(t+a)%5===r).length)));
 const pairs=[];for(let r=0;r<5;r++)for(let s=r+1;s<5;s++)pairs.push([r,s]);
 const mv=(A,v)=>A.map(row=>row.reduce((z,x,r)=>z+x*v[r],0n));
 const wedge=(u,v)=>pairs.map(([r,s])=>u[r]*v[s]-u[s]*v[r]);
 const det=matrix=>{const A=matrix.map(row=>row.slice());let sign=1n,prev=1n;for(let k=0;k<A.length-1;k++){let p=k;while(p<A.length&&A[p][k]===0n)p++;if(p===A.length)return 0n;if(p!==k){[A[p],A[k]]=[A[k],A[p]];sign=-sign;}const pivot=A[k][k];for(let i=k+1;i<A.length;i++)for(let j=k+1;j<A.length;j++){const n=A[i][j]*pivot-A[i][k]*A[k][j];assert.equal(n%prev,0n);A[i][j]=n/prev;}for(let i=k+1;i<A.length;i++)A[i][k]=0n;prev=pivot;}return sign*A.at(-1).at(-1);};
 const gram=(A,c)=>A[0].map((_,i)=>A[0].map((__,j)=>A.reduce((s,row)=>s+row[i]*row[j],0n)-(i===j?c:0n)));
 const tasks={
  matrix:()=>{
   const exterior=pairs.map(([i,j])=>pairs.map(([r,s])=>M[i][r]*M[j][s]-M[i][s]*M[j][r]));
   assert.equal(det(M),5894n);assert.equal(det(exterior),5894n**4n);
   for(const row of M)assert.equal(row.reduce((s,x)=>s+x,0n),14n);for(let c=0;c<5;c++)assert.equal(M.reduce((s,row)=>s+row[c],0n),14n);
   const minors=A=>A.map((_,i)=>det(A.slice(0,i+1).map(row=>row.slice(0,i+1))));
   const mMinors=minors(gram(M,16n)),wMinors=minors(gram(exterior,256n));assert(mMinors.every(x=>x>0n));assert(wMinors.every(x=>x>0n));
   for(let i=0;i<5;i++)for(let j=0;j<5;j++){const u=Array.from({length:5},(_,r)=>r===i?1n:0n),v=Array.from({length:5},(_,r)=>r===j?1n:0n);assert.deepEqual(wedge(mv(M,u),mv(M,v)),mv(exterior,wedge(u,v)));}
   return {M,exterior_matrix:exterior,determinant:det(exterior),matrix_gram_minors:mMinors,exterior_gram_minors:wMinors,bilinear_basis_checks:25,spectral_gap:'min singular value of exterior matrix >16; max singular value of M =14'};
  },
  family:()=>{
   // Polynomials in k, coefficients low degree first. All assertions are symbolic.
   const trim=P=>{const Q=P.slice();while(Q.length>1&&Q.at(-1)===0n)Q.pop();return Q;};
   const add=(P,Q,c=1n)=>trim(Array.from({length:Math.max(P.length,Q.length)},(_,i)=>(P[i]||0n)+c*(Q[i]||0n)));
   const scale=(P,c)=>trim(P.map(x=>x*c));
   const mul=(P,Q)=>{let R=[0n];for(let i=0;i<P.length;i++)for(let j=0;j<Q.length;j++){const T=Array(i+j+1).fill(0n);T[i+j]=P[i]*Q[j];R=add(R,T);}return R;};
   const pmv=(A,v)=>A.map(row=>row.reduce((s,x,r)=>add(s,scale(v[r],x)),[0n]));
   const pwedge=(u,v)=>pairs.map(([r,s])=>add(mul(u[r],v[s]),mul(u[s],v[r]),-1n));
   const N=5894n,v=[227n,-473n,-53n,-305n,1025n],e=[1n,0n,0n,0n,0n];assert.deepEqual(mv(M,v),e.map(x=>N*x));
   const a=[1n,N],b=[N+1n,N],C=e.map(x=>[-x,14n]);
   const X=v.map(x=>[0n,1n-x,N]),Y=v.map((x,r)=>[-x-e[r],N+1n-x,N]);
   const MX=pmv(M,X),MY=pmv(M,Y),Me=mv(M,e);
   const U=MX.map((P,r)=>add(P,[-e[r]])),V=MY.map((P,r)=>add(P,[Me[r]-e[r]]));
   assert.deepEqual(U,C.map(P=>mul(a,P)));assert.deepEqual(V,C.map(P=>mul(b,P)));assert(pwedge(U,V).every(P=>P.length===1&&P[0]===0n));
   const primitive=[[587n,2947n],[167n,2947n],[419n,2947n],[-911n,2947n],[-210n],[-84n],[-749n],[126n],[-539n],[-665n]];
   const W=pwedge(X,Y);assert.deepEqual(W,primitive.map(P=>mul([0n,2n],P)));
   const gcd=(a,b)=>b?gcd(b,a%b):a<0n?-a:a;
   assert.equal(primitive.slice(4).reduce((g,P)=>gcd(g,P[0]),0n),7n);assert.equal(2947n%7n,0n);assert.equal(587n%7n,6n);
   for(let r=0;r<5;r++){assert(N+1n-v[r]>0n);assert(Y[r].reduce((s,x)=>s+x,0n)>0n);}
   // Coprime child coefficients: b-a=N and a=1 mod N. Both parent vectors
   // are nonuniform, so the earlier uniform-return endpoint lemma does not apply.
   assert.deepEqual(add(b,a,-1n),[N]);assert.equal(a[0],1n);assert.notEqual(v[0],v[1]);
   return {parameter:'every integer k >=1',adjugate_column:v,child_coefficients:{a,b},common_counts:C,parent_counts:{X,Y},primitive_parent_wedge:primitive,parent_wedge_content:'2k',primitivity_certificate:{constant_coordinate_gcd:7,first_coordinate_mod_7:6},distinct_projective_states:'coordinate (1,2) stays -210, while (0,1)=2947k+587',parent_endpoint_letters:[0,0,0],offsets:[1,0,13],scope:'Algebraically admissible positive parent counts; fixed-point occurrence is NOT established. Not counterexamples to Shallit candidate.'};
  },
 };
 log({event:resumed?'resume':'start',identity,workers:1,completed:Object.keys(state.completed),total_phases:2,checkpoint});save();let completed=0;
 for(const [name,run]of Object.entries(tasks)){if(state.completed[name])continue;if(stop){save();log({event:'interrupted'});process.exitCode=75;break;}const then=performance.now();state.completed[name]=run();save();log({event:'phase_complete',phase:name,completed:Object.keys(state.completed).length,total_phases:2,elapsed_seconds:(performance.now()-then)/1000});completed++;await new Promise(r=>setImmediate(r));if(budget&&completed>=budget)stop=true;}
 if(Object.keys(state.completed).length===2){const result={identity,status:'checked_stopping_obstruction',checks:state.completed,proof_status:'No finite all-ratios exterior certificate obtained. Primitive wedge normalization does not make the raw inverse states finite. No change to d_* or s_*; Shallit candidate remains open.'};atomic(output,result);log({event:'complete',elapsed_seconds:(performance.now()-started)/1000,output,proof_status:result.proof_status});}
}catch(error){log({event:'error',message:error.stack});process.exitCode=1;}
