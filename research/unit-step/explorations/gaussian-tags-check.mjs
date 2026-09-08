#!/usr/bin/env node
// Bounded exact linear-algebra diagnostic, not a prefix/recoding search.
// Every partition of the eight abstract transitions into <=5 displacement
// classes is tested for solvability with arbitrary Gaussian planar tags and
// four distinct rational height tags. Run time is seconds; no subprocesses.
import assert from 'node:assert/strict';
const edges = Array.from({length: 8}, (_, j) => [j % 4, (j % 4 + 1 + Math.floor(j / 4)) % 4]);
const units = [[1,0],[0,1],[-1,0],[0,-1]];
const inc = ([r,s]) => [1,2,3].map(j => Number(s===j)-Number(r===j));
const gcd = (a,b) => { a=a<0n?-a:a; b=b<0n?-b:b; while(b) [a,b]=[b,a%b]; return a; };
function primitive(row) {
  let g=0n; for(const x of row) g=gcd(g,x);
  if(!g) return row;
  if(row.find(x=>x)!==undefined && row.find(x=>x)<0n) g=-g;
  return row.map(x=>x/g);
}
function rank(rows, cols) {
  const a=rows.map(row=>row.slice(0,cols).map(BigInt)); let r=0;
  for(let c=0;c<cols && r<a.length;c++) {
    const p=a.findIndex((row,j)=>j>=r && row[c]!==0n); if(p<0) continue;
    [a[r],a[p]]=[a[p],a[r]]; a[r]=primitive(a[r]);
    for(let j=r+1;j<a.length;j++) if(a[j][c]!==0n) {
      const x=a[r][c],y=a[j][c]; a[j]=primitive(a[j].map((v,k)=>x*v-y*a[r][k]));
    }
    r++;
  }
  return r;
}
const out={status:'finite_exact_diagnostic', edges, partitions:0, consistent:0,
  distinctHeightFeasible:0, rankHistogram:{}, feasibleExamples:[], forcedPairHistogram:{}};
function test(labels) {
  out.partitions++;
  const first=new Map(), mat=[];
  for(let j=0;j<8;j++) {
    const l=labels[j]; if(!first.has(l)) {first.set(l,j); continue;}
    const k=first.get(l), ij=inc(edges[j]), ik=inc(edges[k]);
    mat.push([...ij.map((x,d)=>x-ik[d]), ...units[edges[k][0]].map((x,d)=>x-units[edges[j][0]][d])]);
  }
  const r=rank(mat,3); out.rankHistogram[r]=(out.rankHistogram[r]??0)+1;
  if(rank(mat.map(row=>[...row.slice(0,3),row[3]]),4)!==r ||
     rank(mat.map(row=>[...row.slice(0,3),row[4]]),4)!==r) return;
  out.consistent++;
  const forced=[];
  for(let a=0;a<4;a++) for(let b=a+1;b<4;b++) {
    if(rank([...mat.map(row=>row.slice(0,3)),inc([a,b])],3)===r) forced.push(`${a}${b}`);
  }
  if(!forced.length) {
    out.distinctHeightFeasible++;
    if(out.feasibleExamples.length<20) out.feasibleExamples.push({labels:[...labels],rank:r,mat});
  } else {
    const key=forced.join(','); out.forcedPairHistogram[key]=(out.forcedPairHistogram[key]??0)+1;
  }
}
function partitions(a,max) {
  if(a.length===8) { test(a); return; }
  for(let x=0;x<=Math.min(max+1,4);x++) { a.push(x); partitions(a,Math.max(max,x)); a.pop(); }
}
partitions([0],0);
assert.equal(out.partitions,3845);
assert.equal(out.consistent,992);
assert.equal(out.distinctHeightFeasible,12);

// New-source identity regression: f(n)=z(n)/u(n) is an isometry even when
// the endpoint states differ. Small bounded inputs; all norms use BigInt.
const v2 = x => { assert(x!==0n); x=x<0n?-x:x; let v=0; while(x%2n===0n) {x/=2n;v++;} return v; };
let sourcePairs=0;
for(let rule=0;rule<16;rule++) {
  let z=[0n,0n]; const f=[];
  for(let n=0;n<=32;n++) {
    let state=0;
    for(let b=0;(2**b)<=n;b++) if(Math.floor(n/2**b)%2)
      state+=(rule>>(b%4))&1 ? 1 : -1;
    state=(state%4+4)%4;
    const [ur,ui]=units[state].map(BigInt);
    f.push([z[0]*ur+z[1]*ui,z[1]*ur-z[0]*ui]);
    z=[z[0]+ur,z[1]+ui];
  }
  for(let m=0;m<32;m++) for(let n=m+1;n<=32;n++) {
    const x=f[n][0]-f[m][0],y=f[n][1]-f[m][1];
    assert.equal(v2(x*x+y*y),v2(BigInt(n-m))); sourcePairs++;
  }
}
out.sourceIsometryPairs=sourcePairs;
assert.equal(sourcePairs,8448);

// alpha=beta=2: all height permutations, all Gaussian residue assignments.
const perms=[];
function permute(a,left) { if(!left.length) {perms.push(a);return;}
  for(const x of left) permute([...a,x],left.filter(y=>y!==x)); }
permute([],[0,1,2,3]);
const residues=[[0n,0n],[1n,0n],[0n,1n],[1n,1n]];
let pairedResidues=0;
for(const t of perms) {
  let planarAssignments=0;
  for(const p of perms) {
    let ok=true;
    for(let r=0;r<4;r++) for(let s=r+1;s<4;s++) {
      const x=residues[p[s]][0]-residues[p[r]][0],y=residues[p[s]][1]-residues[p[r]][1];
      if(v2(x*x+y*y)!==v2(BigInt(t[s]-t[r]))) ok=false;
    }
    if(ok) planarAssignments++;
  }
  assert.equal(planarAssignments,8); pairedResidues+=planarAssignments;
}
assert.equal(pairedResidues,192);
out.minimalScalePairedResidues=pairedResidues;
console.log(JSON.stringify(out,null,2));
