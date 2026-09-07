import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {searchUnit,graphs} from './signed_phase_overlap.mjs';
import {tables} from './check_signed_phase_selector.mjs';
import {changeWitness} from './signed_return_topologies.mjs';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');

function exactMenu(t,positions,graph) {
  const ids=new Set();
  for(let r=0;r<4;r++) {
    for(let j=1;j<positions[r].length;j++)ids.add(t.intern[r][positions[r][j-1]][positions[r][j]]);
    for(const d of graphs[graph])ids.add(t.boundary[r][(r+d)%4][positions[r].at(-1)][positions[(r+d)%4][0]]);
  }
  return [...ids].map(id=>t.vectors[id]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);
}
function flatMinimum(t,q,graph) {
  const L=2**q,options=Array.from({length:2**L-1},(_,i)=>Array.from({length:L},(_,j)=>j).filter(j=>(i+1)&(1<<j)));
  let minimum=Infinity;
  for(const a of options)for(const b of options)for(const c of options)for(const d of options)
    minimum=Math.min(minimum,exactMenu(t,[a,b,c,d],graph).length);
  return minimum;
}
function production(t,q,graph,budget,memo=true) {
  const L=2**q;
  for(let a=0;a<L;a++)for(let b=a;b<L;b++) {
    const result=searchUnit(t,q,graph,budget,a,b,{memo});
    assert.notEqual(result.status,'unknown');
    if(result.status==='sat') {
      assert.deepEqual(result.witness.menu,exactMenu(t,result.witness.positionsByTailState,graph));
      assert(result.witness.menu.length<=budget);
      return true;
    }
  }
  return false;
}

test('generic pruning agrees with flat enumeration, including non-Gaussian SAT cases',()=>{
  let seed=314159;
  const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
  for(let trial=0;trial<12;trial++) {
    const t=tables(1,0),labels=3+trial%5;
    t.vectors=Array.from({length:labels},(_,id)=>[id,0,1]);
    for(let r=0;r<4;r++) {
      t.intern[r][0][1]=random()%labels;
      for(let s=0;s<4;s++)for(let a=0;a<2;a++)for(let b=0;b<2;b++)
        t.boundary[r][s][a][b]=random()%labels;
    }
    for(let g=0;g<4;g++) {
      const minimum=flatMinimum(t,1,g);
      for(const memo of [false,true]) {
        assert.equal(production(t,1,g,minimum,memo),true);
        if(minimum>1)assert.equal(production(t,1,g,minimum-1,memo),false);
      }
    }
  }
});

test('Gaussian small cases agree with independent flat enumeration',()=>{
  for(const q of [1,2])for(let low=0;low<2**q;low++)for(let g=0;g<4;g++) {
    const t=tables(q,low);
    assert(flatMinimum(t,q,g)>=6);
    assert.equal(production(t,q,g,5),false);
  }
});

test('six-vector search witness agrees with a direct digit-sum subsequence',()=>{
  const q=1,low=0,g=1,t=tables(q,low);
  const result=searchUnit(t,q,g,6,0,0);
  assert.equal(result.status,'sat');
  const {positionsByTailState:selected,menu}=result.witness;
  assert.deepEqual(menu,exactMenu(t,selected,g));
  const tail=changeWitness(graphs[g].reduce((mask,d)=>mask|(1<<d),0));
  const sign=j=>j<tail.prefix.length?tail.prefix[j]:tail.cycle[(j-tail.prefix.length)%tail.cycle.length];
  function state(n,shift=0) {
    let total=0,j=0;
    for(;n;n=Math.floor(n/2),j++)if(n%2)total+=shift===1?sign(j):(j===0?1:sign(j-1));
    return (total%4+4)%4;
  }
  const c=[[0,0],[-1,0],[-1,1],[0,-1]],unit=[[1,0],[0,1],[-1,0],[0,-1]];
  let x=0,y=0,last=null;const seen=new Set();
  for(let n=0;n<4096;n++) {
    const s=state(n),r=state(Math.floor(n/2),1);
    const p=[2*x+c[s][0],2*y+c[s][1],4*n+s];
    if(selected[r].includes(n%2)) {
      if(last)seen.add(p.map((v,j)=>v-last[j]).join(','));last=p;
    }
    x+=unit[s][0];y+=unit[s][1];
  }
  assert.deepEqual([...seen].sort(),menu.map(v=>v.join(',')).sort());
});

test('public timeline matches selector evidence without promoting its scope',()=>{
  const html=fs.readFileSync('viz/progress.html','utf8');
  const section=html.match(/<aside\b[^>]*\bid="signed-selector-research"[^>]*>[\s\S]*?<\/aside>/)?.[0];
  assert(section,'missing signed-selector research status');
  assert.match(section,/data-status="computational"/);
  assert.match(section,/Cambie’s fixed tags/);
  assert.match(section,/nonempty position selections in every dyadic block, determined only by its tail state/);
  assert.match(section,/No four- or five-vector construction was found; the global minima remain open/);
  assert.match(section,/not a global lower bound or an all-block-size theorem/);
  assert.match(section,/The original Erdős 193 theorem is unchanged/);
  assert.match(section,/href="https:\/\/github\.com\/ekalvi\/erdos-193\/blob\/main\/research\/unit-step\/tracks\/HIGHER-SIGN-TOPOLOGIES\.md"/);
  for(const L of [8,16]) {
    const result=JSON.parse(fs.readFileSync(`research/unit-step/checks/signed-phase-overlap-${L}.json`,'utf8'));
    const row=section.match(new RegExp(`<li\\b[^>]*data-block-size="${L}"[^>]*>[\\s\\S]*?<\\/li>`))?.[0];
    assert(row,`missing ${L}-position result`);
    assert.equal(result.status,'unsat');assert.equal(result.completed,result.total);
    assert(row.includes(`data-completed-units="${result.completed}"`));
    assert(row.includes(`all ${result.completed.toLocaleString('en-US')} endpoint units complete`));
    assert(row.includes(`data-independent-reference="${L===8}"`));
    if(L===8)assert.match(row,/a second implementation independently confirms the exclusion/);
    else assert.match(row,/No second full-size implementation check or external review yet/);
  }
  const note=fs.readFileSync('research/unit-step/tracks/HIGHER-SIGN-TOPOLOGIES.md','utf8');
  assert(note.includes('../../../viz/progress.html#signed-selector-research'));
  assert(!note.includes('Public visualization is unchanged'));
});

test('saved 8/16 exclusions have complete endpoint coverage and matching code identity',()=>{
  const sourceSha256=hash(fs.readFileSync('research/unit-step/tracks/signed_phase_overlap.mjs'));
  const tablesSha256=hash(fs.readFileSync('research/unit-step/tracks/check_signed_phase_selector.mjs'));
  for(const [q,L] of [[3,8],[4,16]]) {
    const result=JSON.parse(fs.readFileSync(`research/unit-step/checks/signed-phase-overlap-${L}.json`,'utf8'));
    assert.equal(result.identity.sourceSha256,sourceSha256);assert.equal(result.identity.tablesSha256,tablesSha256);
    assert.equal(result.identity.q,q);assert.equal(result.identity.budget,5);
    assert.equal(result.status,'unsat');assert.equal(result.completed,L*4*L*(L+1)/2);
    assert.equal(result.total,result.completed);assert.equal(result.witness,null);assert.equal(result.unfinished,null);
  }
  const reference=JSON.parse(fs.readFileSync('research/unit-step/checks/signed-phase-reference-8.json','utf8'));
  assert.equal(reference.identity.sourceSha256,hash(fs.readFileSync('research/unit-step/tracks/check_signed_phase_overlap.mjs')));
  assert.equal(reference.identity.overlapSha256,sourceSha256);assert.equal(reference.identity.tablesSha256,tablesSha256);
  assert.equal(reference.status,'unsat');assert.equal(reference.rows.length,32);
  assert.equal(reference.assignmentsCovered,(32n*255n**4n).toString());
  assert.equal(new Set(reference.rows.map(r=>`${r.low}:${r.graph}`)).size,32);
  for(const row of reference.rows) {
    assert(row.low>=0&&row.low<8&&row.graph>=0&&row.graph<4);
    assert.equal(row.status,'unsat');assert.equal(row.assignmentsCovered,(255n**4n).toString());
  }
});
