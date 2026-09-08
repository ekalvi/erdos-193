#!/usr/bin/env node
/** Exact overlap-directed search of dyadic phase selectors.
 * Branch on first/last vertices, force every known boundary displacement FIRST,
 * and then generate only internal paths using <= budget distinct vectors.
 * Never form the Cartesian product of all 2^L-1 selectors for four states.
 * One core; source/dependency/config-checked, atomic per-endpoint checkpoints.
 * SIGINT/TERM or --seconds retains completed units; the active unit may restart.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {setImmediate as yieldNow} from 'node:timers/promises';
import {tables} from './check_signed_phase_selector.mjs';

export const graphs=[[0,1],[1,2],[0,3],[2,3]];
const orders=[[0,1,2,3],[0,2,1,3],[0,3,2,1],[0,2,1,3]];
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const here=fileURLToPath(import.meta.url);
let stopped=false;
process.on('SIGINT',()=>{stopped=true;});
process.on('SIGTERM',()=>{stopped=true;});

export function searchUnit(t,q,graph,budget,first,last,{deadline=Infinity,memo=true}={}) {
  const L=2**q,changes=graphs[graph],order=orders[graph];
  const selected=Array(4).fill(null),positions=Array(4).fill(null),used=[];
  let visits=0,budgetPrunes=0,memoPrunes=0,endpointTests=0,witness=null;
  const pause=Symbol('deadline');
  function tick() {
    visits++;
    if(visits%4096===0 && (stopped || performance.now()>=deadline))throw pause;
  }
  function add(id) {
    if(used.includes(id))return true;
    if(used.length===budget){budgetPrunes++;return false;}
    used.push(id);return true;
  }
  function assign(depth) {
    tick();
    if(depth===4) {
      witness={positionsByTailState:positions.map(p=>p.slice()),
        menu:used.map(id=>t.vectors[id]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2])};
      return true;
    }
    const r=order[depth];
    for(let a=depth===0?first:0;a<(depth===0?first+1:L);a++)
      for(let b=depth===0?last:a;b<(depth===0?last+1:L);b++) {
        tick();endpointTests++;
        const before=used.length;
        selected[r]={first:a,last:b};
        let possible=true;
        // For any edge whose endpoints are now known, its exact displacement
        // is mandatory independently of the interior path in this block.
        for(const d of changes) {
          const s=(r+d)%4;
          if(selected[s]&&!add(t.boundary[r][s][b][selected[s].first])){possible=false;break;}
          const p=(r-d+4)%4;
          if(p!==r&&selected[p]&&!add(t.boundary[p][r][selected[p].last][a])){possible=false;break;}
        }
        if(possible) {
          const seen=new Set(),trace=[a];
          function extend(at) {
            tick();
            // For fixed endpoints/previous blocks, subsequent constraints
            // depend on this cursor and label SET, never path multiplicities.
            if(memo) {
              const key=`${at}:${used.slice().sort((a,b)=>a-b).join(',')}`;
              if(seen.has(key)){memoPrunes++;return false;}
              seen.add(key);
            }
            if(at===b) {
              positions[r]=trace.slice();
              return assign(depth+1);
            }
            for(let next=at+1;next<=b;next++) {
              const mark=used.length;
              if(add(t.intern[r][at][next])) {
                trace.push(next);
                if(extend(next))return true;
                trace.pop();
              }
              used.length=mark;
            }
            return false;
          }
          if(extend(a))return {status:'sat',witness,visits,budgetPrunes,memoPrunes,endpointTests};
        }
        selected[r]=null;positions[r]=null;used.length=before;
      }
    return false;
  }
  try {
    const found=assign(0);
    return {status:found?'sat':'unsat',witness,visits,budgetPrunes,memoPrunes,endpointTests};
  } catch(error) {
    if(error!==pause)throw error;
    return {status:'unknown',reason:stopped?'signal':'time-budget',visits,budgetPrunes,memoPrunes,endpointTests};
  }
}
function atomic(file,data) {
  fs.mkdirSync(path.dirname(file),{recursive:true});
  const tmp=`${file}.tmp`,fd=fs.openSync(tmp,'w');
  try {fs.writeFileSync(fd,JSON.stringify(data)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  fs.renameSync(tmp,file);
}
function parse(args) {
  const config={q:3,budget:5,seconds:120,output:null,checkpointDir:'.checkpoint-signed-phase-overlap',memo:true};
  for(let i=0;i<args.length;i++) {
    const a=args[i];
    if(a==='--help')return null;
    if(a==='--no-memo'){config.memo=false;continue;}
    const names={'--q':'q','--budget':'budget','--seconds':'seconds','--output':'output','--checkpoint-dir':'checkpointDir'};
    if(!(a in names)||i+1>=args.length)throw Error(`unknown/missing argument: ${a}`);
    const key=names[a],value=args[++i];
    config[key]=['q','budget','seconds'].includes(key)?Number(value):value;
  }
  if(!Number.isInteger(config.q)||config.q<1||config.q>5||!Number.isInteger(config.budget)
    ||config.budget<1||!Number.isFinite(config.seconds)||config.seconds<=0)throw Error('invalid q, budget, or seconds');
  return config;
}
async function main() {
  const config=parse(process.argv.slice(2));
  if(!config){console.log('node research/unit-step/tracks/signed_phase_overlap.mjs [--q 3|4] [--budget 5] [--seconds 120] [--output FILE] [--no-memo]\n'
    +'One-core exact boundary-first overlap search. Completed (topology, graph, first, last)\n'
    +'units resume atomically with source/dependency/config checksums. A timeout or signal\n'
    +'does not mark its active unit complete. Increase --seconds to continue a run.');return;}
  const identity={schema:1,sourceSha256:hash(fs.readFileSync(here)),
    tablesSha256:hash(fs.readFileSync(new URL('./check_signed_phase_selector.mjs',import.meta.url))),
    q:config.q,budget:config.budget,memo:config.memo};
  const root=`${config.checkpointDir}/${hash(JSON.stringify(identity))}`,checkpoint=`${root}/state.json`;
  fs.mkdirSync(root,{recursive:true});
  const log=(event,fields={})=>{
    const record={timestamp:new Date().toISOString(),event,...fields};
    fs.appendFileSync(`${root}/run.jsonl`,JSON.stringify(record)+'\n');console.log(JSON.stringify(record));
  };
  const start=performance.now(),deadline=start+1000*config.seconds,L=2**config.q;
  const total=L*4*L*(L+1)/2;
  let units={};
  if(fs.existsSync(checkpoint)) {
    const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));
    if(JSON.stringify(saved.identity)!==JSON.stringify(identity)||saved.unitsSha256!==hash(JSON.stringify(saved.units)))
      throw Error('incompatible/corrupt checkpoint');
    units=saved.units;
    for(const [key,u] of Object.entries(units)) {
      const [low,g,a,b]=key.split(':').map(Number);
      if(!Number.isInteger(low)||low<0||low>=L||!Number.isInteger(g)||g<0||g>=4||!Number.isInteger(a)
        ||a<0||b<a||b>=L||!['sat','unsat'].includes(u.status))throw Error('invalid completed unit');
    }
  }
  const initial=Object.keys(units).length;
  log('start',{identity,cores:1,checkpoint,completed:initial,total,timeBudgetSeconds:config.seconds,
    resume:'completed endpoint units reused; active interrupted unit restarts'});
  const save=()=>atomic(checkpoint,{identity,unitsSha256:hash(JSON.stringify(units)),units});
  let witness=null,unknown=null,lastLog=start,lastSave=start;
  try {
    search:for(let low=0;low<L;low++) {
      const t=tables(config.q,low);
      for(let g=0;g<4;g++)for(let a=0;a<L;a++)for(let b=a;b<L;b++) {
        const key=[low,g,a,b].join(':');
        if(units[key]) {
          if(units[key].status==='sat'){witness={low,graph:g,...units[key].witness};break search;}
          continue;
        }
        await yieldNow(); // Deliver SIGINT/TERM between bounded search units.
        if(stopped||performance.now()>=deadline){unknown={key,reason:stopped?'signal':'time-budget'};break search;}
        const result=searchUnit(t,config.q,g,config.budget,a,b,{deadline,memo:config.memo});
        if(result.status==='unknown'){unknown={key,...result};break search;}
        units[key]=result;
        const now=performance.now();
        if(now-lastSave>=1000){save();lastSave=now;}
        if(result.status==='sat'){witness={low,graph:g,...result.witness};break search;}
        if(now-lastLog>=2000) {
          const completed=Object.keys(units).length,elapsedSeconds=(now-start)/1000;
          const perSecond=(completed-initial)/elapsedSeconds;
          log('progress',{completed,total,current:key,elapsedSeconds,perSecond,
            remainingSeconds:perSecond>0?(total-completed)/perSecond:null,rssBytes:process.memoryUsage().rss});
          lastLog=now;
        }
      }
    }
    save();
    const completed=Object.keys(units).length;
    const totals=Object.values(units).reduce((s,u)=>{
      for(const k of ['visits','budgetPrunes','memoPrunes','endpointTests'])s[k]+=u[k];return s;
    },{visits:0,budgetPrunes:0,memoPrunes:0,endpointTests:0});
    const result={identity,scope:'fixed Cambie tags; one nonempty position set per dyadic block tail state',
      status:witness?'sat':completed===total?'unsat':'unknown',completed,total,totals,witness,unfinished:unknown};
    if(config.output)atomic(config.output,result);
    log('complete',{status:result.status,completed,total,totals,witness,unfinished:unknown,
      elapsedSeconds:(performance.now()-start)/1000,remainingSeconds:result.status==='unknown'?null:0,
      rssBytes:process.memoryUsage().rss});
  }catch(error){save();log('error',{message:String(error)});throw error;}
  if(stopped)process.exitCode=130;
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===path.resolve(process.argv[1]))await main();
