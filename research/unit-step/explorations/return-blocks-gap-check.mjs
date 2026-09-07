#!/usr/bin/env node
// Finite obstruction search, arbitrary selectors with bounded gaps.
// Completed starting positions are atomic and resumable. An interrupted
// starting position restarts, never discarding completed starting positions.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,renameSync,existsSync,mkdirSync} from 'node:fs';
if(process.argv.includes('--help')) {console.log('Usage: node return-blocks-gap-check.mjs GAP [PREFIX=128]\nExact DFS of all five-displacement paths with gaps <= GAP through a source prefix.\nCheckpoints under .checkpoint-return-blocks validate code/config and resume completed starting positions.\nAn interrupted starting position restarts. Use one process and native thread limits 1.\nExit status: 0=no path, 2=counterexample, 1=error; resumed results use the same status.');process.exit(0);}
const B=Number(process.argv[2]??2), N=Number(process.argv[3]??128);
if(!Number.isSafeInteger(B)||!Number.isSafeInteger(N)||B<1||N<=B)throw Error('usage: node return-blocks-gap-check.mjs GAP [PREFIX=128]');
const start=Date.now();
const sha256=createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex');
const dir='.checkpoint-return-blocks';mkdirSync(dir,{recursive:true});
const path=`${dir}/gap-${B}-${N}-${sha256.slice(0,12)}.json`;
const log=(event,data={})=>console.log(JSON.stringify({time:new Date().toISOString(),event,B,N,...data}));
let state={sha256,B,N,starts:[],found:null};
if(existsSync(path)){state=JSON.parse(readFileSync(path));assert.equal(state.sha256,sha256);assert.equal(state.B,B);assert.equal(state.N,N);assert.ok(Array.isArray(state.starts));assert.ok(state.starts.length<=B);for(let j=0;j<state.starts.length;j++){assert.equal(state.starts[j].first,j);assert.ok(Number.isSafeInteger(state.starts[j].nodes));}}
const save=()=>{writeFileSync(path+'.tmp',JSON.stringify(state)+'\n');renameSync(path+'.tmp',path);};
log('start',{sha256,threads:1,checkpoint:path,resume:'validated completed starting positions',completed:state.starts.length,total:B});
if(state.starts.length===B||state.found){log('resume-complete',state);process.exit(state.found?2:0);}
const delta=[0,1,3,0],c=[[0,0],[-1,0],[-1,1],[0,-1]],u=[[1,0],[0,1],[-1,0],[0,-1]];
const q=new Uint8Array(N+B+1),P=[];
for(let n=1;n<q.length;n++)q[n]=(q[Math.floor(n/4)]+delta[n%4])%4;
let x=0,y=0;
for(let n=0;n<q.length;n++){P.push([2*x+c[q[n]][0],2*y+c[q[n]][1],4*n+q[n]]);x+=u[q[n]][0];y+=u[q[n]][1];}
const vectors=[],ids=new Map(),edge=[];
for(let n=0;n<N;n++){
 const row=[];
 for(let d=1;d<=B;d++){
  const v=P[n+d].map((a,k)=>a-P[n][k]), key=v.join(',');
  if(!ids.has(key)){ids.set(key,vectors.length);vectors.push(v);}
  row.push(ids.get(key));
 }
 edge.push(row);
}
let nodes=0, found=null, maxReach=0, activeFirst=0, unitStart=Date.now();const memo=new Set(),route=[];
function dfs(n,menu){
 nodes++;maxReach=Math.max(maxReach,n);
 if(nodes%1000000===0)log('progress',{first:activeFirst,nodes,elapsed_s:(Date.now()-start)/1000,throughput_nodes_s:Math.round(nodes/((Date.now()-unitStart)/1000)),rss:process.memoryUsage().rss,checkpoint:path});
 if(n>=N){found={route:[...route,n],menu:menu.map(i=>vectors[i])};return true;}
 // Five-label states mostly die immediately; omitting their global cache
 // greatly reduces memory without pruning any branch.
 const key=menu.length<5?n+':'+menu.join(','):null;if(key!==null&&memo.has(key))return false;
 route.push(n);
 for(let d=1;d<=B;d++){
  const id=edge[n][d-1];
  if(menu.includes(id)){if(dfs(n+d,menu))return true;}
  else if(menu.length<5){const next=[...menu,id].sort((a,b)=>a-b);if(dfs(n+d,next))return true;}
 }
 route.pop();if(key!==null)memo.add(key);
 return false;
}
for(let first=state.starts.length;first<B;first++){
 activeFirst=first;nodes=0;maxReach=0;memo.clear();route.length=0;
 unitStart=Date.now();
 dfs(first,[]);
 const record={first,nodes,memo:memo.size,maxReach,elapsed_s:(Date.now()-unitStart)/1000};
 state.starts.push(record);state.found=found;state.universe=vectors.length;save();
 log('start-position-complete',{...record,completed:first+1,total:B,eta_s:record.elapsed_s*(B-first-1),checkpoint:path});
 if(found)break;
}
log('result',{...state,nodes:state.starts.reduce((a,r)=>a+r.nodes,0),maxReach:Math.max(...state.starts.map(r=>r.maxReach)),elapsed_s:(Date.now()-start)/1000});
process.exitCode=state.found?2:0;
