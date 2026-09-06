import assert from 'node:assert/strict';
import {build,TYPES,state,image,sub,triple,MERGERS,merge} from './model.mjs';
const m=build();
assert.deepEqual(m.states.slice(0,8),[0,1,3,0,1,2,0,1]);
const gcd=(a,b)=>{while(b)[a,b]=[b,a%b];return Math.abs(a);};
const v2=x=>{assert.ok(x>0);let k=0;while(x%2===0){x/=2;k++;}return k;};
for(let n=0;n<m.vertices;n++) {
  assert.equal(m.basis[n].reduce((a,b)=>a+b),n);
  assert.deepEqual(image(m.basis[n]),m.lift[n]);
  if(n) {
    assert.deepEqual(sub(m.lift[n],m.lift[n-1]),TYPES[m.steps[n-1]].vector);
    assert.equal(sub(m.basis[n],m.basis[n-1]).filter(x=>x===1).length,1);
    assert.ok(m.lift[n][2]>m.lift[n-1][2]);
  }
  if(n<1023) {
    let k=0,t=n;while(t%2){k++;t=Math.floor(t/2);}
    assert.equal((state(n+1)-state(n)+4)%4,k%2?2:1);
  }
}
// Independent four-uniform transition-word generator, proved in the notes.
const rules=['afda','bgab','chbc','decd','afde','bgaf','chbg','dech'];
let word='a';while(word.length<1023)word=[...word].map(c=>rules[c.charCodeAt(0)-97]).join('');
assert.deepEqual([...word.slice(0,1023)].map(c=>[0,1,2,3,4,4,5,5][c.charCodeAt(0)-97]),m.steps);
let pairs=0;
for(let a=0;a<m.vertices-1;a++) {
  const seen=new Set();
  for(let b=a+1;b<m.vertices;b++) {
    const diff=sub(m.basis[b],m.basis[a]),divisor=diff.reduce(gcd),key=diff.map(x=>x/divisor).join(',');
    assert.ok(!seen.has(key),'collinear triple in finite prefix');seen.add(key);
    const [x,y,h]=sub(m.lift[b],m.lift[a]);assert.equal(v2(x*x+y*y),v2(h));pairs++;
  }
}
for(const [i,j,a,b,c] of MERGERS) {
  assert.ok(triple(m,a,b,c).mismatch>=0);
  assert.deepEqual(merge(sub(m.basis[b],m.basis[a]),i,j),merge(sub(m.basis[c],m.basis[b]),i,j));
}
assert.throws(()=>triple(m,10,5,20));assert.throws(()=>build(1));
console.log(JSON.stringify({status:'pass',vertices:m.vertices,exact_pairs:pairs,mergers:MERGERS.length,scope:'Finite model validation, not an infinite proof'}));
