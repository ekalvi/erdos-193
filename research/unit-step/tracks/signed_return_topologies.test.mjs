import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {calculate,compact,changeWitness,block,returnTypes,cambie} from './signed_return_topologies.mjs';

const mod4 = n => ((n%4)+4)%4;
const state = (n,sign) => {
  let total=0,j=0;
  for (;n;n>>=1n,j++) if(n&1n) total+=sign(j);
  return mod4(total);
};
const signAt = witness => j => j < witness.prefix.length ? witness.prefix[j]
  : witness.cycle[(j-witness.prefix.length)%witness.cycle.length];
const typeKey = t => [t.a,t.b,t.x,t.y,t.length].join(',');

// Construct actual, possibly large, indices for every claimed tail pair.
// This independently validates reachability, rather than assuming that the
// four possible starting states occur at each carry depth.
function carryWitnesses(witness) {
  const sign=signAt(witness), result=new Map();
  let sum=0;
  for(let k=0;k<witness.prefix.length+witness.cycle.length;k++) {
    const delta=mod4(sign(k)-sum);
    for(let r=0;r<4;r++) {
      let n=(1n<<BigInt(k))-1n, needed=mod4(r-sum);
      // Three + signs or three - signs above bit k span all four residues.
      const positions=[[],[]];
      for(let j=k+1;Math.max(...positions.map(a=>a.length))<3;j++) {
        positions[sign(j)===1?0:1].push(j);
      }
      const index=positions.findIndex(a=>a.length>=3), e=index===0?1:-1;
      const count=mod4(e*needed);
      for(const j of positions[index].slice(0,count)) n |= 1n<<BigInt(j);
      assert.equal(state(n,sign),r);
      assert.equal(state(n+1n,sign),mod4(r+delta));
      result.set(`${r}:${delta}`,n);
    }
    sum+=sign(k);
  }
  return result;
}

test('nine exact carry classes, with independently replayed infinite witnesses',()=>{
  const masks=[];
  for(let mask=1;mask<16;mask++) {
    const witness=changeWitness(mask);
    if(!witness) continue;
    masks.push(mask);
    const sign=signAt(witness);
    let sum=0,seen=0;
    for(let k=0;k<witness.prefix.length+4*witness.cycle.length;k++) {
      seen |= 1<<mod4(sign(k)-sum);
      sum+=sign(k);
    }
    assert.equal(seen,mask);
    assert.equal(mod4(witness.cycle.reduce((a,b)=>a+b,0)),0);
    const actual=carryWitnesses(witness);
    for(let r=0;r<4;r++) for(let d=0;d<4;d++)
      assert.equal(actual.has(`${r}:${d}`),Boolean(mask&(1<<d)));
  }
  assert.deepEqual(masks,[3,6,7,9,11,12,13,14,15]);
});

test('every eight-letter low-bit block contains all four states',()=>{
  for(let low=0;low<8;low++) for(let r=0;r<4;r++) {
    const signs=[0,1,2].map(j=>low&(1<<j)?-1:1);
    assert.equal(new Set(block(signs,r)).size,4);
  }
});

test('all 1080 return catalogues agree with direct bit arithmetic at exact carry witnesses',()=>{
  for(let low=0;low<8;low++) {
    const signs=[0,1,2].map(j=>low&(1<<j)?-1:1);
    for(let mask=1;mask<16;mask++) {
      const witness=changeWitness(mask);
      if(!witness) continue;
      const tail=signAt(witness), sign=j=>j<3?signs[j]:tail(j-3);
      const words=[...carryWitnesses(witness).values()].map(n=>
        Array.from({length:16},(_,j)=>state(8n*n+BigInt(j),sign)));
      for(let select=1;select<16;select++) {
        const actual=new Set();
        for(const word of words) {
          let previous=-1;
          for(let n=0;n<word.length;n++) if(select&(1<<word[n])) {
            if(previous>=0) {
              const counts=[0,0,0,0];
              for(let j=previous;j<n;j++) counts[word[j]]++;
              actual.add([word[previous],word[n],counts[0]-counts[2],counts[1]-counts[3],n-previous].join(','));
            }
            previous=n;
          }
        }
        assert.deepEqual([...actual].sort(),returnTypes(signs,mask,select).map(typeKey).sort(),
          `low=${low}, tail=${mask}, selection=${select}`);
      }
    }
  }
});

test('tracked exact result, all selector-size minima, and six-vector positive controls',()=>{
  const result=compact(calculate());
  assert.equal(result.caseCount,1080);
  assert.deepEqual(result.bySelectorSize.map(r=>r.minimum),[7,6,7,6]);
  assert.equal(result.minimum,6);
  assert.equal(result.minimizers.length,10);
  const saved=JSON.parse(fs.readFileSync('research/unit-step/checks/signed-return-topologies.json','utf8'));
  assert.equal(saved.codeSha256,crypto.createHash('sha256').update(
    fs.readFileSync('research/unit-step/tracks/signed_return_topologies.mjs')).digest('hex'));
  assert.equal(saved.resultSha256,crypto.createHash('sha256').update(JSON.stringify(saved.result)).digest('hex'));
  assert.deepEqual(saved.result,result);
  for(const row of result.minimizers) for(const item of row.menu) {
    assert(item.vector[2]>0);
    for(const t of item.types) {
      assert.deepEqual(item.vector,[2*t.x,2*t.y,4*t.length].map((v,j)=>v+cambie[t.b][j]-cambie[t.a][j]));
    }
  }
});
