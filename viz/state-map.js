const STATE_COLORS = ['#56B4E9', '#E69F00', '#CC79A7', '#009E73'];
const STATE_NAMES = ['1 · east', 'i · north', '−1 · west', '−i · south'];
const UNITS = [[1, 0], [0, 1], [-1, 0], [0, -1]];
const TAGS = [[0, 0], [0, 1], [-1, 1], [-1, 0]];
let order = 4;
let focus = null;
let points = [];
let picked = [];
let hover = null;
let transform = null;
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');
const panel = document.getElementById('panel');

function state(n) {
  let count = 0;
  while (n) {
    count += n & 1;
    n = Math.floor(n / 2);
  }
  return count % 4;
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

function binary(n) {
  return `${n.toString(2)}₂`;
}

function buildPalette() {
  const holder = document.getElementById('statePalette');
  holder.innerHTML = STATE_NAMES.map((name, alpha) =>
    `<button class="key" data-state="${alpha}" style="color:${STATE_COLORS[alpha]}">` +
      `<span class="swatch route" style="background:${STATE_COLORS[alpha]}">${alpha}</span>` +
      `<div><b>${name}</b><small>α=${alpha} · corner (${TAGS[alpha].join(', ')})</small></div></button>`
  ).join('');
  holder.querySelectorAll('button').forEach(button => {
    button.onclick = () => {
      const alpha = Number(button.dataset.state);
      focus = focus === alpha ? null : alpha;
      render();
    };
  });
}

function rebuild() {
  points = [];
  const total = 4 ** order;
  let zx = 0;
  let zy = 0;
  for (let n = 0; n < total; n += 1) {
    const alpha = state(n);
    const [tx, ty] = TAGS[alpha];
    points.push({
      n, alpha, zx, zy, tag: TAGS[alpha],
      gx: 2 * zx + tx,
      gy: 2 * zy + ty,
      h: 4 * n + alpha,
    });
    zx += UNITS[alpha][0];
    zy += UNITS[alpha][1];
  }
  picked = [];
  hover = null;
  fitTransform();
  render();
}

function fitTransform() {
  const xs = points.map(point => point.gx);
  const ys = points.map(point => point.gy);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const padding = 34;
  const spanX = Math.max(1, maxX - minX);
  const spanY = Math.max(1, maxY - minY);
  const scale = Math.min((canvas.width - 2 * padding) / spanX, (canvas.height - 2 * padding) / spanY);
  transform = {
    minX, minY, maxY, scale,
    x: value => padding + (value - minX) * scale,
    y: value => canvas.height - padding - (value - minY) * scale,
  };
}

function render() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = '#10141d';
  context.fillRect(0, 0, canvas.width, canvas.height);

  if (document.getElementById('pathToggle').checked) {
    context.beginPath();
    points.forEach((point, index) => {
      const x = transform.x(point.gx);
      const y = transform.y(point.gy);
      if (index) context.lineTo(x, y);
      else context.moveTo(x, y);
    });
    context.strokeStyle = order === 6 ? '#ffffff24' : '#ffffff55';
    context.lineWidth = order === 6 ? 1 : 1.5;
    context.stroke();
  }

  const radius = order === 6 ? 1.2 : order === 4 ? 2.2 : 4;
  for (const point of points) {
    context.globalAlpha = focus !== null && point.alpha !== focus ? 0.12 : 1;
    context.fillStyle = STATE_COLORS[point.alpha];
    context.beginPath();
    context.arc(transform.x(point.gx), transform.y(point.gy), radius, 0, Math.PI * 2);
    context.fill();
  }
  context.globalAlpha = 1;

  picked.forEach((point, index) => {
    context.strokeStyle = index ? '#ffdf6e' : '#fff';
    context.lineWidth = 2;
    context.beginPath();
    context.arc(transform.x(point.gx), transform.y(point.gy), Math.max(5, radius + 3), 0, Math.PI * 2);
    context.stroke();
  });
  if (picked.length === 2) {
    context.beginPath();
    context.moveTo(transform.x(picked[0].gx), transform.y(picked[0].gy));
    context.lineTo(transform.x(picked[1].gx), transform.y(picked[1].gy));
    context.strokeStyle = '#fff';
    context.lineWidth = 2;
    context.stroke();
  }

  document.querySelectorAll('#statePalette button').forEach(button => {
    button.classList.toggle('active', Number(button.dataset.state) === focus);
  });
  updatePanel();
}

function pointDetails(point, title = 'Point') {
  return `<h2>${title}</h2><dl>` +
    `<dt>index</dt><dd>${point.n} · ${binary(point.n)}</dd>` +
    `<dt>digit sum state</dt><dd><span style="color:${STATE_COLORS[point.alpha]};font-weight:700">` +
      `${STATE_NAMES[point.alpha]} · α=${point.alpha}</span></dd>` +
    `<dt>Gaussian zₙ</dt><dd>${point.zx} ${point.zy < 0 ? '−' : '+'} ${Math.abs(point.zy)}i</dd>` +
    `<dt>corner tag</dt><dd>(${point.tag.join(', ')})</dd>` +
    `<dt>tagged wₙ</dt><dd>(${point.gx}, ${point.gy})</dd>` +
    `<dt>height hₙ</dt><dd>${point.h}</dd>` +
    `<dt>lift Pₙ</dt><dd>(${point.gx}, ${point.gy}, ${point.h})</dd></dl>`;
}

function updatePanel() {
  if (picked.length === 2) {
    const [a, b] = picked[0].n < picked[1].n ? picked : [picked[1], picked[0]];
    const dx = b.gx - a.gx;
    const dy = b.gy - a.gy;
    const dh = b.h - a.h;
    const planarValue = v2(dx * dx + dy * dy);
    const heightValue = v2(dh);
    panel.innerHTML = `<h2>Pair inspector</h2><dl>` +
      `<dt>indices</dt><dd>${a.n} → ${b.n}</dd>` +
      `<dt>directions</dt><dd><span style="color:${STATE_COLORS[a.alpha]}">${STATE_NAMES[a.alpha]}</span>` +
        ` → <span style="color:${STATE_COLORS[b.alpha]}">${STATE_NAMES[b.alpha]}</span></dd>` +
      `<dt>planar chord</dt><dd>(${dx}, ${dy})</dd>` +
      `<dt>squared norm</dt><dd>${dx * dx + dy * dy}</dd>` +
      `<dt>height gap</dt><dd>${dh}</dd>` +
      `<dt>ν₂(|Δw|²)</dt><dd>${planarValue}</dd>` +
      `<dt>ν₂(Δh)</dt><dd>${heightValue}</dd></dl>` +
      `<div class="equation">${planarValue === heightValue
        ? '<span class="ok">Exact all-pairs match.</span> The Gaussian chord and height have the same binary fingerprint.'
        : '<strong>Mismatch — implementation error.</strong>'}</div>`;
    return;
  }
  const point = picked[0] || hover;
  panel.innerHTML = point
    ? pointDetails(point, picked.length ? 'Selected point' : 'Hovered point')
    : '<h2>Point inspector</h2><p class="muted">Hover a colored point. Click two points to verify the all-pairs identity.</p>';
}

function eventPoint(event) {
  const rect = canvas.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width * canvas.width;
  const y = (event.clientY - rect.top) / rect.height * canvas.height;
  let best = null;
  let bestDistance = order === 6 ? 35 : 80;
  for (const point of points) {
    const dx = transform.x(point.gx) - x;
    const dy = transform.y(point.gy) - y;
    const distance = dx * dx + dy * dy;
    if (distance < bestDistance) {
      best = point;
      bestDistance = distance;
    }
  }
  return best;
}

canvas.onmousemove = event => { hover = eventPoint(event); updatePanel(); };
canvas.onmouseleave = () => { hover = null; updatePanel(); };
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
    document.querySelectorAll('[data-order]').forEach(item => item.classList.toggle('active', item === button));
    rebuild();
  };
});
document.getElementById('pathToggle').onchange = render;
document.getElementById('clearPair').onclick = () => { picked = []; render(); };
window.addEventListener('resize', () => { fitTransform(); render(); });

buildPalette();
rebuild();
