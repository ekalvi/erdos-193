// Complete periodic-rule menus, not finite-preview estimates.
// Mirrors the trailing-ones orbit in design/signed_gaussian_unit_step_audit.py.
(function (root) {
  'use strict';
  const directions = [[1, 0], [0, 1], [-1, 0], [0, -1]];
  const offsets = [[0, 0], [-1, 0], [-1, 1], [0, -1]];
  const mod4 = n => ((n % 4) + 4) % 4;
  function stepMenu(pattern) {
    if (!/^[+-]+$/.test(pattern)) throw new Error('Expected a nonempty +/- pattern');
    const signs = [...pattern].map(s => s === '+' ? 1 : -1);
    const changes = new Set();
    let prefix = 0;
    // delta(k+p)=delta(k)-sum(signs) mod 4: four periods exhaust the orbit.
    for (let k = 0; k < 4 * signs.length; k++) {
      const sign = signs[k % signs.length];
      changes.add(mod4(sign - prefix));
      prefix += sign;
    }
    const menu = new Map();
    for (const change of [...changes].sort()) {
      for (let r = 0; r < 4; r++) {
        // Every starting state is realizable using bits above the carry suffix.
        const s = mod4(r + change);
        const vector = [0, 1].map(j => 2 * directions[r][j] + offsets[s][j] - offsets[r][j]);
        vector.push(4 + s - r);
        const key = vector.join(',');
        if (!menu.has(key)) menu.set(key, {vector, state_pairs: []});
        menu.get(key).state_pairs.push([r, s]);
      }
    }
    return [...menu.values()].sort((a, b) => {
      for (let j = 0; j < 3; j++) if (a.vector[j] !== b.vector[j]) return a.vector[j] - b.vector[j];
      return 0;
    });
  }
  if (typeof module !== 'undefined') module.exports = {stepMenu};
  if (!root.document) return;

  const palette = ['#3987e5', '#1baf7a', '#e6a93a', '#b16bc3'];
  const stage = document.querySelector('#vectorMenuStage');
  const canvas = document.querySelector('#vectorMenuCanvas');
  const context = canvas?.getContext('2d');
  let drawnMenu = [];
  let yaw = -0.7;
  let pitch = -0.45;
  let dragging = false;
  let lastPointer = null;

  function project([x, y, z]) {
    // Match the Visualize page: integer height is the vertical scene axis.
    const px = x;
    const py = z;
    const pz = y;
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const qx = cy * px + sy * pz;
    const qz = -sy * px + cy * pz;
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    return [qx, cp * py - sp * qz];
  }

  function drawMenu() {
    if (!context || !stage || !drawnMenu.length) return;
    const ratio = Math.min(root.devicePixelRatio || 1, 2);
    const width = Math.max(1, stage.clientWidth);
    const height = Math.max(1, stage.clientHeight);
    if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
    }
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);
    const points = [[0, 0], ...drawnMenu.map(({vector}) => project(vector))];
    const xs = points.map(point => point[0]);
    const ys = points.map(point => point[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const spanX = Math.max(1, maxX - minX), spanY = Math.max(1, maxY - minY);
    const scale = Math.min(width * 0.68 / spanX, height * 0.68 / spanY);
    const centerX = width / 2 - (minX + maxX) * scale / 2;
    const centerY = height / 2 + (minY + maxY) * scale / 2;
    const screen = ([x, y]) => [centerX + x * scale, centerY - y * scale];
    const origin = screen([0, 0]);
    drawnMenu.forEach(({vector}, index) => {
      const endpoint = screen(project(vector));
      context.strokeStyle = palette[index % palette.length];
      context.globalAlpha = 0.78;
      context.lineWidth = 1.25;
      context.beginPath();
      context.moveTo(...origin);
      context.lineTo(...endpoint);
      context.stroke();
      context.globalAlpha = 1;
      context.fillStyle = palette[index % palette.length];
      context.beginPath();
      context.arc(...endpoint, 6, 0, Math.PI * 2);
      context.fill();
    });
    context.fillStyle = '#fff';
    context.beginPath();
    context.arc(...origin, 7, 0, Math.PI * 2);
    context.fill();
  }

  stage?.addEventListener('pointerdown', event => {
    dragging = true;
    lastPointer = [event.clientX, event.clientY];
    stage.classList.add('dragging');
    stage.setPointerCapture(event.pointerId);
  });
  stage?.addEventListener('pointermove', event => {
    if (!dragging) return;
    yaw += (event.clientX - lastPointer[0]) * 0.009;
    pitch = Math.max(-1.35, Math.min(1.35, pitch + (event.clientY - lastPointer[1]) * 0.009));
    lastPointer = [event.clientX, event.clientY];
    drawMenu();
  });
  const stopDragging = () => { dragging = false; lastPointer = null; stage?.classList.remove('dragging'); };
  stage?.addEventListener('pointerup', stopDragging);
  stage?.addEventListener('pointercancel', stopDragging);
  root.addEventListener('resize', drawMenu);
  if (typeof root.requestAnimationFrame === 'function') {
    let previous = performance.now();
    const animate = now => {
      if (!dragging && !document.hidden) {
        yaw += Math.min(50, now - previous) * 0.00008;
        drawMenu();
      }
      previous = now;
      root.requestAnimationFrame(animate);
    };
    root.requestAnimationFrame(animate);
  }

  function render({rule, pattern}) {
    const menu = stepMenu(pattern);
    drawnMenu = menu;
    document.querySelector('#vectorMenuTitle').textContent = `g${rule.length > 24 ? rule.slice(0, 16) + '…' : rule}: ${menu.length} distinct 3D step vectors`;
    const lengths = menu.map(({vector}) => Math.hypot(...vector));
    document.querySelector('#vectorMenuCount').textContent = menu.length;
    document.querySelector('#vectorMenuMin').textContent = Math.min(...lengths).toFixed(2);
    document.querySelector('#vectorMenuMax').textContent = Math.max(...lengths).toFixed(2);
    const body = document.querySelector('#vectorMenuRows');
    body.replaceChildren(...menu.map(({vector, state_pairs}, index) => {
      const item = document.createElement('div');
      item.className = 'vector-menu-item';
      const label = document.createElement('b');
      label.textContent = `${index + 1}. (${vector.join(', ')})`;
      const transitions = document.createElement('span');
      transitions.textContent = state_pairs.map(([r, s]) => `${r} → ${s}`).join('; ');
      item.append(label, transitions);
      return item;
    }));
    stage?.setAttribute('aria-label', `Rotating 3D diagram of all ${menu.length} exact step vectors for g${rule}`);
    drawMenu();
    const url = new URL(location.href);
    url.search = '';
    url.searchParams.set('rule', rule);
    url.hash = 'vector-menu';
    document.querySelector('#vectorPermalink').href = url.href;
    const alternating = rule === '85' || rule === '170';
    document.querySelector('#alternatingNotice').hidden = !alternating;
    document.title = `g${rule.length > 24 ? rule.slice(0, 16) + '…' : rule} · ${menu.length} step vectors — Signed Gaussian family`;
  }
  root.addEventListener('signed-gaussian-rule-change', event => render(event.detail));
  if (root.signedGaussianCurrentRule) render(root.signedGaussianCurrentRule);
})(typeof window === 'undefined' ? globalThis : window);
