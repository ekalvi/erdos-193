import {build,TYPES,triple,MERGERS,merge,image,sub} from './model.mjs';
const model=build(), $=id=>document.getElementById(id);
const tuple=p=>'('+p.join(', ')+')';
let n=69, playing=false, last=0, frame=null;
$('menu').innerHTML=TYPES.map((t,j)=>`<tr id="type${j}"><td><strong style="color:${t.color}">${t.name}</strong></td><td>${t.pairs.map(p=>p.join('→')).join(', ')}</td><td>${tuple(t.vector)}</td></tr>`).join('');
$('bars').innerHTML=TYPES.map((t,j)=>`<div class="barrow"><strong style="color:${t.color}">${t.name}</strong><div class="track"><div id="bar${j}" class="bar" style="background:${t.color}"></div></div><output id="count${j}"></output></div>`).join('');
$('merger').innerHTML=MERGERS.map(([i,j],k)=>`<option value="${k}" ${k===14?'selected':''}>${TYPES[i].name} + ${TYPES[j].name}</option>`).join('');
const projected=model.lift.map(([x,y,h])=>[x+.42*y,h/40+.22*y]);
function plot(id,points) {
  const canvas=$(id), ctx=canvas.getContext('2d'), rect=canvas.getBoundingClientRect();
  const w=rect.width,h=rect.height,dpr=window.devicePixelRatio||1;
  canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);
  let xmin=Infinity,xmax=-Infinity,ymin=Infinity,ymax=-Infinity;
  for(const [x,y] of points){xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);}
  const scale=Math.min((w-30)/Math.max(1,xmax-xmin),(h-30)/Math.max(1,ymax-ymin));
  const xy=([x,y])=>[w/2+(x-(xmin+xmax)/2)*scale,h/2-(y-(ymin+ymax)/2)*scale];
  function path(end,color,width){ctx.beginPath();for(let i=0;i<=end;i++){const [x,y]=xy(points[i]);i?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();}
  path(points.length-1,'#d8e0e6',1);path(n,'#496273',1.2);
  if(n>0){const [x,y]=xy(points[n-1]),[u,v]=xy(points[n]);ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(u,v);ctx.lineWidth=3;ctx.strokeStyle=TYPES[model.steps[n-1]].color;ctx.stroke();}
  const [x,y]=xy(points[n]);ctx.beginPath();ctx.arc(x,y,4.5,0,2*Math.PI);ctx.fillStyle='#172b3b';ctx.fill();
  const [sx,sy]=xy(points[0]);ctx.beginPath();ctx.arc(sx,sy,4,0,2*Math.PI);ctx.strokeStyle='#172b3b';ctx.lineWidth=1.5;ctx.stroke();
}
function render() {
  $('position').value=n;$('positionLabel').textContent=`${n} / 1023`;
  const p=model.basis[n],r=model.states[n],max=Math.max(1,...p);
  TYPES.forEach((t,j)=>{$('bar'+j).style.width=`${100*p[j]/max}%`;$('count'+j).textContent=p[j];$('type'+j).classList.toggle('selected',n>0&&model.steps[n-1]===j);});
  $('sourceReadout').textContent=`z${n} = ${tuple(model.source[n])}`;
  $('liftReadout').textContent=`Q${n} = ${tuple(model.lift[n])}`;
  $('basisReadout').textContent=`P${n} = ${tuple(p)}; sum = ${n}`;
  const terms=[...n.toString(2)].reverse().flatMap((b,j)=>b==='1'?[`${j%2?'−':'+'}1 (bit ${j})`]:[]);
  $('bits').textContent=`n=${n}, binary ${n.toString(2)}: ${terms.join(' ')||'0'} ≡ ${r} mod 4`;
  $('stepReadout').textContent=n?`Step ${n-1}→${n}: state ${model.states[n-1]}→${r}, type ${TYPES[model.steps[n-1]].name}. Add ${tuple(TYPES[model.steps[n-1]].vector)} in 3D, or increase coordinate ${TYPES[model.steps[n-1]].name} by 1 in 6D. T(P${n}) = ${tuple(image(p))}.`:'At the origin: all six counters are zero.';
  $('letters').innerHTML=model.steps.slice(0,48).map((j,k)=>`<span class="letter ${k===n-1?'active':''}" style="background:${TYPES[j].color}" title="Step ${k}">${TYPES[j].name}</span>`).join('');
  plot('source',model.source);plot('shadow',projected);
}
function select(value){n=Math.max(0,Math.min(1023,Number(value)));render();}
function stop(){playing=false;if(frame!==null)cancelAnimationFrame(frame);frame=null;$('play').textContent='Play';}
$('position').addEventListener('input',e=>{stop();select(e.target.value);});
$('back').onclick=()=>{stop();select(n-1);};$('next').onclick=()=>{stop();select(n+1);};$('reset').onclick=()=>{stop();select(0);};
$('play').onclick=()=>{if(playing){stop();return;}playing=true;$('play').textContent='Pause';if(n===1023)select(0);last=0;frame=requestAnimationFrame(tick);};
function tick(t){if(!playing)return;if(t-last>130){last=t;select(n+1);if(n===1023)stop();}if(playing)frame=requestAnimationFrame(tick);}
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
function check(){try{const a=Number($('a').value),b=Number($('b').value),c=Number($('c').value),v=triple(model,a,b,c),j=v.mismatch;
$('tripleResult').textContent=`[${a},${b}): ${tuple(v.left)} over ${v.p} steps. [${b},${c}): ${tuple(v.right)} over ${v.q} steps. ${j>=0?`Not collinear: coordinate ${TYPES[j].name} has proportions ${v.left[j]}/${v.p} ≠ ${v.right[j]}/${v.q}. Exact cross-products: ${v.q*v.left[j]} ≠ ${v.p*v.right[j]}.`:'Collinear.'}`;
}catch(e){$('tripleResult').textContent=e.message;}}
function showMerger(){const [i,j,a,b,c]=MERGERS[Number($('merger').value)],left=merge(sub(model.basis[b],model.basis[a]),i,j),right=merge(sub(model.basis[c],model.basis[b]),i,j);
$('mergeResult').textContent=`After merging ${TYPES[i].name} and ${TYPES[j].name}, intervals [${a},${b}) and [${b},${c}) have counts ${tuple(left)} and ${tuple(right)}. Both lengths are ${b-a}, so the projected vertices ${a}, ${b}, ${c} are collinear. The original six-coordinate vertices are not.`;
$('a').value=a;$('b').value=b;$('c').value=c;check();}
$('check').onclick=check;$('merger').onchange=showMerger;
let resizing;window.addEventListener('resize',()=>{clearTimeout(resizing);resizing=setTimeout(render,100);});
showMerger();render();
