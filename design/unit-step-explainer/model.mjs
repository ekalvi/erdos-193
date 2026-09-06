// Exact integer model. No rendering assumptions enter the mathematics.
export const TYPES = [
  {name:'A', pairs:[[0,1]], vector:[1,0,5], color:'#0072b2'},
  {name:'B', pairs:[[1,2]], vector:[0,3,5], color:'#b36b00'},
  {name:'C', pairs:[[2,3]], vector:[-1,-2,5], color:'#008568'},
  {name:'D', pairs:[[3,0]], vector:[0,-1,1], color:'#b44982'},
  {name:'E', pairs:[[0,2],[1,3]], vector:[1,1,6], color:'#7746ad'},
  {name:'F', pairs:[[2,0],[3,1]], vector:[-1,-1,2], color:'#bd491b'},
];
export const OFFSETS = [[0,0],[-1,0],[-1,1],[0,-1]];
const DIR = [[1,0],[0,1],[-1,0],[0,-1]];
export function state(n) {
  let sum=0, sign=1;
  while(n) {sum+=sign*(n%2); sign=-sign; n=Math.floor(n/2);}
  return ((sum%4)+4)%4;
}
export function build(vertices=1024) {
  if(!Number.isInteger(vertices)||vertices<2||vertices>65536) throw Error('Invalid vertex count');
  const source=[[0,0]], basis=[Array(6).fill(0)], lift=[], steps=[], states=[];
  for(let n=0;n<vertices;n++) {
    const r=state(n); states.push(r);
    const [x,y]=source[n];
    lift.push([2*x+OFFSETS[r][0],2*y+OFFSETS[r][1],4*n+r]);
    if(n+1<vertices) {
      const s=state(n+1), type=TYPES.findIndex(t=>t.pairs.some(([a,b])=>a===r&&b===s));
      if(type<0) throw Error('Unexpected transition');
      const p=basis[n].slice(); p[type]++;
      steps.push(type); basis.push(p); source.push([x+DIR[r][0],y+DIR[r][1]]);
    }
  }
  return {source,basis,lift,steps,states,vertices};
}
export const sub=(a,b)=>a.map((v,j)=>v-b[j]);
export const image=p=>[0,1,2].map(j=>p.reduce((s,v,i)=>s+v*TYPES[i].vector[j],0));
export function triple(model,a,b,c) {
  if(![a,b,c].every(Number.isInteger)||a<0||a>=b||b>=c||c>=model.vertices) throw Error('Choose 0 ≤ a < b < c ≤ 1023');
  const left=sub(model.basis[b],model.basis[a]), right=sub(model.basis[c],model.basis[b]);
  return {left,right,p:b-a,q:c-b,mismatch:left.findIndex((x,j)=>(c-b)*x!==(b-a)*right[j])};
}
export const MERGERS = [
  [0,1,3,4,5],[0,2,6,9,12],[0,3,2,3,4],[0,4,0,1,2],[0,5,5,6,7],
  [1,2,19,20,21],[1,3,28,35,42],[1,4,11,14,17],[1,5,4,5,6],
  [2,3,10,11,12],[2,4,9,10,11],[2,5,20,21,22],
  [3,4,1,2,3],[3,5,14,17,20],[4,5,41,55,69],
];
export function merge(p,i,j) {return p.map((x,k)=>k===i?x+p[j]:x).filter((_,k)=>k!==j);}
