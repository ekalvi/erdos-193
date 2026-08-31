const DIGIT_COLORS = ['#0072B2', '#E69F00', '#009E73', '#CC79A7'];
const STATE_COLORS = {I: '#56B4E9', S: '#E69F00', C: '#CC79A7', T: '#009E73'};
const STATE_DESC = {
  I: 'label 0 · corner (0,0)',
  S: 'label 1 · corner (0,1)',
  C: 'label 2 · corner (1,1)',
  T: 'label 3 · corner (1,0)',
};
const STATE_ARROW = {I: '0', S: '1', C: '2', T: '3'};
const STATE_COLOR_NAME = {I: 'blue', S: 'orange', C: 'purple', T: 'green'};
const STATE_LABEL = {I: 0, S: 1, C: 2, T: 3};
const STATE_TAG = {I: [0, 0], S: [0, 1], C: [1, 1], T: [1, 0]};
const CHILD = [[0, 0], [0, 1], [1, 1], [1, 0]];
const STATES = {
  I: [0, 0, 0], X: [0, 1, 0], Y: [0, 0, 1], C: [0, 1, 1],
  S: [1, 0, 0], R: [1, 1, 0], L: [1, 0, 1], T: [1, 1, 1],
};
const NAMES = Object.keys(STATES);
const REFINEMENT = ['S', 'I', 'I', 'T'];
let order = 4;
let focus = null;
let points = [];
let byCell = new Map();
let picked = [];
let hover = null;
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');
const panel = document.getElementById('panel');

function act(name, [x, y]) {
  const [swap, bx, by] = STATES[name];
  return [(swap ? y : x) ^ bx, (swap ? x : y) ^ by];
}

function compose(g, h) {
  for (const candidate of NAMES) {
    if (CHILD.every(point => {
      const a = act(candidate, point);
      const b = act(g, act(h, point));
      return a[0] === b[0] && a[1] === b[1];
    })) return candidate;
  }
  throw new Error('state closure failed');
}

function transduce(n, length = order) {
  let state = 'I';
  let x = 0;
  let y = 0;
  const address = [];
  for (let position = length - 1; position >= 0; position -= 1) {
    const q = Math.floor(n / 4 ** position) % 4;
    address.push(q);
    const [xBit, yBit] = act(state, CHILD[q]);
    x = 2 * x + xBit;
    y = 2 * y + yBit;
    state = compose(state, REFINEMENT[q]);
  }
  const label = STATE_LABEL[state];
  const tag = STATE_TAG[state];
  return {
    n, x, y, state, label, tag, address,
    gx: 2 * x + tag[0],
    gy: 2 * y + tag[1],
    z: 4 * n + label,
  };
}

function v2(n) {
  if (n === 0) return Infinity;
  n = Math.abs(n);
  let value = 0;
  while (n % 2 === 0) {
    n /= 2;
    value += 1;
  }
  return value;
}

function pairValue(dx, dy) {
  const vx = v2(dx);
  const vy = v2(dy);
  return 2 * Math.min(vx, vy) + (vx === vy ? 1 : 0);
}

function base4(address) {
  return `${address.join('')}₄`;
}

function digitStrip(address) {
  return `<div class="digits">${address.map(q =>
    `<span class="digit" style="background:${DIGIT_COLORS[q]}">${q}</span>`
  ).join('')}</div>`;
}

function buildPalette() {
  const holder = document.getElementById('statePalette');
  holder.innerHTML = Object.keys(STATE_COLORS).map(state =>
    `<button class="key" data-state="${state}" style="color:${STATE_COLORS[state]}">` +
      `<span class="swatch route" style="background:${STATE_COLORS[state]}">${STATE_ARROW[state]}</span>` +
      `<div><b>${STATE_COLOR_NAME[state]} · state ${state}</b>` +
      `<small>${STATE_DESC[state]}</small></div></button>`
  ).join('');
  holder.querySelectorAll('button').forEach(button => {
    button.onclick = () => {
      focus = focus === button.dataset.state ? null : button.dataset.state;
      render();
    };
  });
}

function rebuild() {
  points = [];
  byCell.clear();
  const total = 4 ** order;
  for (let n = 0; n < total; n += 1) {
    const point = transduce(n);
    points.push(point);
    byCell.set(`${point.gx},${point.gy}`, point);
  }
  picked = [];
  hover = null;
  render();
}

function render() {
  const side = 2 ** (order + 1);
  const size = canvas.width;
  const cell = size / side;
  context.clearRect(0, 0, size, size);
  context.fillStyle = '#10141d';
  context.fillRect(0, 0, size, size);

  if (document.getElementById('pathToggle').checked) {
    context.beginPath();
    points.forEach((point, index) => {
      const x = (point.gx + 0.5) * cell;
      const y = size - (point.gy + 0.5) * cell;
      if (index) context.lineTo(x, y);
      else context.moveTo(x, y);
    });
    context.strokeStyle = order === 6 ? '#ffffff20' : '#ffffff45';
    context.lineWidth = Math.max(1, cell * 0.16);
    context.stroke();
  }

  for (const point of points) {
    context.globalAlpha = focus && point.state !== focus ? 0.14 : 1;
    context.fillStyle = STATE_COLORS[point.state];
    const radius = Math.max(1.4, cell * 0.34);
    context.beginPath();
    context.arc(
      (point.gx + 0.5) * cell,
      size - (point.gy + 0.5) * cell,
      radius,
      0,
      Math.PI * 2,
    );
    context.fill();
  }
  context.globalAlpha = 1;

  for (const [index, point] of picked.entries()) {
    context.strokeStyle = index ? '#ffdf6e' : '#fff';
    context.lineWidth = Math.max(2, cell * 0.22);
    context.strokeRect(
      point.gx * cell,
      size - (point.gy + 1) * cell,
      Math.max(3, cell),
      Math.max(3, cell),
    );
  }
  if (picked.length === 2) {
    context.beginPath();
    context.moveTo(
      (picked[0].gx + 0.5) * cell,
      size - (picked[0].gy + 0.5) * cell,
    );
    context.lineTo(
      (picked[1].gx + 0.5) * cell,
      size - (picked[1].gy + 0.5) * cell,
    );
    context.strokeStyle = '#fff';
    context.lineWidth = 2;
    context.stroke();
  }

  document.querySelectorAll('#statePalette button').forEach(button => {
    button.classList.toggle('active', button.dataset.state === focus);
  });
  updatePanel();
}

function pointDetails(point, title = 'Point') {
  return `<h2>${title}</h2><dl>` +
    `<dt>index</dt><dd>${point.n}</dd>` +
    `<dt>address</dt><dd>${base4(point.address)}</dd>` +
    `<dt>Hilbert H(n)</dt><dd>(${point.x}, ${point.y})</dd>` +
    `<dt>state</dt><dd><span style="color:${STATE_COLORS[point.state]};font-weight:700">` +
      `${point.state} · λ=${point.label} · u=(${point.tag.join(', ')})</span></dd>` +
    `<dt>planar G(n)</dt><dd>(${point.gx}, ${point.gy})</dd>` +
    `<dt>height z(n)</dt><dd>${point.z}</dd>` +
    `<dt>lift P(n)</dt><dd>(${point.gx}, ${point.gy}, ${point.z})</dd>` +
    `</dl>${digitStrip(point.address)}`;
}

function updatePanel() {
  if (picked.length === 2) {
    const [a, b] = picked[0].n < picked[1].n ? picked : [picked[1], picked[0]];
    const dx = b.gx - a.gx;
    const dy = b.gy - a.gy;
    const dz = b.z - a.z;
    const planarValue = pairValue(dx, dy);
    const heightValue = v2(dz);
    panel.innerHTML = `<h2>Pair inspector</h2><dl>` +
      `<dt>indices</dt><dd>${a.n} → ${b.n}</dd>` +
      `<dt>states</dt><dd><span style="color:${STATE_COLORS[a.state]}">${a.state}</span>` +
        ` → <span style="color:${STATE_COLORS[b.state]}">${b.state}</span></dd>` +
      `<dt>planar chord</dt><dd>(${dx}, ${dy})</dd>` +
      `<dt>height gap</dt><dd>${dz}</dd>` +
      `<dt>V(planar chord)</dt><dd>${planarValue}</dd>` +
      `<dt>ν₂(height gap)</dt><dd>${heightValue}</dd></dl>` +
      `<div class="equation">${planarValue === heightValue
        ? '<span class="ok">Exact all-pairs match.</span> The identity applies to every pair of terminal states.'
        : '<strong>Mismatch — implementation error.</strong>'}</div>`;
    return;
  }
  const point = picked[0] || hover;
  if (point) {
    panel.innerHTML = pointDetails(point, picked.length ? 'Selected point' : 'Hovered point');
    return;
  }
  panel.innerHTML = '<h2>Point inspector</h2><p class="muted">' +
    'Hover a colored coordinate. Click two points to verify the all-pairs identity.</p>';
}

function eventPoint(event) {
  const rect = canvas.getBoundingClientRect();
  const side = 2 ** (order + 1);
  const gx = Math.max(0, Math.min(side - 1,
    Math.floor((event.clientX - rect.left) / rect.width * side)));
  const gy = Math.max(0, Math.min(side - 1,
    side - 1 - Math.floor((event.clientY - rect.top) / rect.height * side)));
  return byCell.get(`${gx},${gy}`);
}

canvas.onmousemove = event => {
  hover = eventPoint(event);
  updatePanel();
};
canvas.onmouseleave = () => {
  hover = null;
  updatePanel();
};
canvas.onclick = event => {
  const point = eventPoint(event);
  if (!point) return;
  if (picked.length === 2) picked = [];
  picked.push(point);
  render();
};
document.querySelectorAll('[data-order]').forEach(button => {
  button.onclick = () => {
    order = Number(button.dataset.order);
    document.querySelectorAll('[data-order]').forEach(candidate => {
      candidate.classList.toggle('active', candidate === button);
    });
    rebuild();
  };
});
document.getElementById('pathToggle').onchange = render;
document.getElementById('clearPair').onclick = () => {
  picked = [];
  render();
};

buildPalette();
rebuild();
