#!/usr/bin/env node
// Exact bounded 4D return-block audit. No dimension impossibility is claimed.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {directTriple} from './contradiction_probe.mjs';

if(process.argv.includes('--help')) {
  console.log('node research/unit-step/tracks/four_return_blocks.mjs [--write]\n'
    +'Enumerates 117 possible short return words and all ordered pairs, one JS worker.\n'
    +'Automatically resumes identity/checksum-validated rows from .checkpoint-four-return-blocks.\n'
    +'SIGINT/SIGTERM checkpoint at row boundaries; logs/checkpoints are separate from final evidence.\n'
    +'--write updates the deterministic research JSON; otherwise validates it.');
  process.exit(0);
}
assert(process.argv.slice(2).every(x=>x==='--write'),'unknown argument');
const hash=x=>createHash('sha256').update(x).digest('hex');
const identity={schema:1,codeSha256:hash(fs.readFileSync(new URL(import.meta.url))),
  checkerSha256:hash(fs.readFileSync(new URL('contradiction_probe.mjs',import.meta.url)))};
const words=[],byTailLength={};
for(let n=1;n<=7;n++)for(let code=0;code<3**n;code++) {
  let c=code;const word=Array.from({length:n},()=>{const a=c%3;c=Math.floor(c/3);return a;});
  if(directTriple(word,3,true)===null) {
    assert.equal(directTriple(word,3),null);
    words.push([3,...word]);byTailLength[n]=(byTailLength[n]??0)+1;
  }
}
assert.equal(words.length,117);
const types=new Map();for(const word of words) {
  const counts=Array(4).fill(0);for(const a of word)counts[a]++;
  types.set(counts.join(','),counts);
  assert.equal(directTriple([...word,3],4),null);
}
assert.equal(types.size,41);
const directory='.checkpoint-four-return-blocks',checkpoint=path.join(directory,'state.json'),log=path.join(directory,'run.jsonl');
function durable(file,text,append=false) {
  fs.mkdirSync(path.dirname(file),{recursive:true});const target=append?file:`${file}.tmp-${process.pid}`;
  const fd=fs.openSync(target,append?'a':'w');try{fs.writeFileSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  if(!append)fs.renameSync(target,file);
}
const event=(type,fields={})=>{const line=JSON.stringify({timestamp:new Date().toISOString(),event:type,...fields})+'\n';durable(log,line,true);process.stderr.write(line);};
let progress={row:0,pairsChecked:0,compatiblePairs:0};
const resumed=fs.existsSync(checkpoint);
if(resumed) {
  const saved=JSON.parse(fs.readFileSync(checkpoint,'utf8'));
  assert.deepEqual(saved.identity,identity,'incompatible checkpoint');
  assert.equal(saved.checksum,hash(JSON.stringify(saved.progress)),'corrupt checkpoint');
  progress=saved.progress;
  assert(Number.isInteger(progress.row)&&progress.row>=0&&progress.row<=117);
  assert.equal(progress.pairsChecked,progress.row*117);
  assert(Number.isInteger(progress.compatiblePairs)&&progress.compatiblePairs>=0&&progress.compatiblePairs<=progress.pairsChecked);
}
const save=()=>durable(checkpoint,JSON.stringify({identity,checksum:hash(JSON.stringify(progress)),progress})+'\n');
let stopped=false;process.on('SIGINT',()=>{stopped=true;});process.on('SIGTERM',()=>{stopped=true;});
const start=performance.now(),initial=progress.row;
const report=()=>{const elapsed=(performance.now()-start)/1000,rate=(progress.row-initial)/Math.max(elapsed,.001);
  return {...progress,totalRows:117,rowsPerSecond:rate,elapsedSeconds:elapsed,etaSeconds:rate?(117-progress.row)/rate:null,checkpoint};};
event(resumed?'resume':'start',{...identity,...report(),workers:1});save();
try {
  while(progress.row<words.length&&!stopped) {
    for(const second of words) {
      const joined=[...words[progress.row],...second];
      const ordinary=directTriple(joined,4,true),weak=directTriple(joined,4);
      assert.equal(ordinary===null,weak===null,'two-return compatibility distinguishes unequal lengths');
      progress.pairsChecked++;if(!weak)progress.compatiblePairs++;
    }
    progress.row++;
    if(progress.row%16===0){save();event('progress',report());}
    await new Promise(resolve=>setImmediate(resolve));
  }
  save();
  if(stopped){event('interrupted',report());process.exitCode=130;}
  else {
    // Three-return local compatibility is still insufficient, even with all eight-letter support constraints.
    const period='303132', blocks=['30','31','32'];
    for(let i=0;i<3;i++)assert.equal(directTriple([...(blocks[i]+blocks[(i+1)%3]+blocks[(i+2)%3])].map(Number),4),null);
    for(let i=0;i<6;i++) {
      const local=Array.from({length:11},(_,j)=>Number(period[(i+j)%6]));
      assert.equal(directTriple(local,4),null);
      assert.equal(new Set(local.slice(0,8)).size,4);
    }
    assert.deepEqual(directTriple([...(period+period)].map(Number),4),[0,6,12]);
    const result={...identity,returnWords:words.map(x=>x.join('')),byTailLength,
      parikhTypes:[...types.values()],returnWordCount:words.length,parikhTypeCount:types.size,
      pairsChecked:progress.pairsChecked,compatiblePairs:progress.compatiblePairs,
      allTwoReturnWeakTestsAgreeWithOrdinaryTests:true,
      threeReturnLocalCountermodel:{period,returnBlocks:blocks,firstTriple:[0,6,12]},
      scope:'Necessary 4D return-block description and failed local shortcuts; not a dimension lower bound.'};
    const output=new URL('checks/four-return-blocks.json',import.meta.url);
    if(process.argv.includes('--write'))durable(output.pathname,JSON.stringify(result,null,2)+'\n');
    else assert.deepEqual(JSON.parse(fs.readFileSync(output,'utf8')),result);
    event('complete',{...report(),returnWordCount:117,parikhTypeCount:41});
  }
} catch(error){save();event('error',{message:error.message,...report()});throw error;}
