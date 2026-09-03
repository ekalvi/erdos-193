(() => {
  'use strict';

  const DEFAULT_DEPTH = 10;
  const MAX_RULE_BITS = 4096;
  const MAX_RULE_DIGITS = 1234;
  const DIRECTIONS = [[1, 0], [0, 1], [-1, 0], [0, -1]];
  const CORNERS = [[0, 0], [0, 1], [-1, 1], [-1, 0]];
  const COLORS = ['#56b4e9', '#e69f00', '#009e73', '#cc79a7'];
  const TAGS = ['00', '01', '11', '10'];
  const canvas = document.querySelector('#curveCanvas');
  const ctx = canvas.getContext('2d', {alpha: false});
  const stage = document.querySelector('#curveStage');
  const explorer = document.querySelector('.explorer');
  const fullscreenView = document.querySelector('#fullscreenView');
  const secondaryControlsToggle = document.querySelector('#secondaryControlsToggle');
  const ruleNumber = document.querySelector('#ruleNumber');
  const ruleSlider = document.querySelector('#ruleSlider');
  const ruleName = document.querySelector('#ruleName');
  const formula = document.querySelector('#formula');
  const ruleHelp = document.querySelector('#ruleHelp');
  const signLabel = document.querySelector('#signLabel');
  const depthSlider = document.querySelector('#depthSlider');
  const depthValue = document.querySelector('#depthValue');
  const decreaseDepth = document.querySelector('#decreaseDepth');
  const increaseDepth = document.querySelector('#increaseDepth');
  const inspector = document.querySelector('#inspector');
  const signButtons = [...document.querySelectorAll('[data-sign-place]')];
  const tagButtons = [...document.querySelectorAll('[data-tag]')];

  let rule = 0n;
  let depth = DEFAULT_DEPTH;
  let points = [];
  let states = [];
  let bounds = null;
  let zoom = 1;
  let panX = 0;
  let panY = 0;
  let selected = null;
  let hovered = null;
  let dragging = false;
  let didDrag = false;
  let dragX = 0;
  let dragY = 0;
  let pinchGesture = null;
  let gestureWasPinch = false;
  const activePointers = new Map();
  let showTrace = true;
  const shownTags = [false, false, false, false];

  function parseRule(value) {
    const text = String(value).trim();
    if (!/^\d+$/.test(text)) throw new Error('Enter a nonnegative decimal integer.');
    if (text.length > MAX_RULE_DIGITS) {
      throw new Error(`Rule is too large for this browser preview (maximum ${MAX_RULE_BITS.toLocaleString()} bits).`);
    }
    const parsed = BigInt(text);
    const bitLength = parsed === 0n ? 1 : parsed.toString(2).length;
    if (bitLength > MAX_RULE_BITS) {
      throw new Error(`Rule is too large for this browser preview (maximum ${MAX_RULE_BITS.toLocaleString()} bits).`);
    }
    return parsed;
  }

  function decodeRule(value) {
    const period = Math.max(8, (value + 256n).toString(2).length - 1);
    const offset = (1n << BigInt(period)) - 256n;
    const code = value - offset;
    const binary = code.toString(2).padStart(period, '0');
    return {
      period,
      offset,
      code,
      pattern: [...binary].map(bit => bit === '1' ? '-' : '+')
    };
  }

  function patternFor(value) {
    return decodeRule(value).pattern;
  }

  function abbreviated(text, head = 20, tail = 10) {
    return text.length <= head + tail + 1 ? text : `${text.slice(0, head)}…${text.slice(-tail)}`;
  }

  function stateFor(n, signs) {
    let total = 0;
    let place = 0;
    while (n) {
      if (n & 1) total += signs[place % signs.length];
      place += 1;
      n = Math.floor(n / 2);
    }
    return ((total % 4) + 4) % 4;
  }

  function build(value) {
    const pattern = patternFor(value);
    const signs = pattern.map(sign => sign === '+' ? 1 : -1);
    const count = 2 ** depth;
    const nextPoints = [[0, 0]];
    const nextStates = [];
    let x = 0;
    let y = 0;
    for (let n = 0; n < count; n += 1) {
      const state = stateFor(n, signs);
      nextStates.push(state);
      const [dx, dy] = DIRECTIONS[state];
      x += dx;
      y += dy;
      nextPoints.push([x, y]);
    }
    points = nextPoints.slice(0, count);
    states = nextStates;
    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    points.forEach(([px, py]) => {
      minX = Math.min(minX, px); maxX = Math.max(maxX, px);
      minY = Math.min(minY, py); maxY = Math.max(maxY, py);
    });
    bounds = {minX, maxX, minY, maxY};
    const ruleText = value.toString();
    const patternText = pattern.join('');
    ruleName.textContent = `g${abbreviated(ruleText)} · ε=${abbreviated(patternText, 32, 16)}`;
    ruleName.title = `g${ruleText} · ε=${patternText}`;
    formula.textContent = `σ(n)=Σ ε[j mod ${pattern.length}]bⱼ(n) mod 4 · z(n+1)=z(n)+i^σ(n) · 2^${depth} vertices`;
    depthValue.textContent = `${depth} · ${count.toLocaleString()} vertices`;
    decreaseDepth.disabled = depth <= 4;
    increaseDepth.disabled = depth >= 16;
    signLabel.textContent = pattern.length === 8
      ? 'Signs ε₀ through ε₇ · period 8'
      : `First 8 signs · period ${pattern.length.toLocaleString()}`;
    signButtons.forEach((button, place) => {
      button.textContent = pattern[place];
      button.classList.toggle('minus', pattern[place] === '-');
      button.setAttribute('aria-label', `ε${place}: ${pattern[place] === '+' ? 'plus' : 'minus'}`);
    });
    canvas.setAttribute('aria-label', `Interactive signed Gaussian curve g${abbreviated(ruleText)}, period ${pattern.length}`);
    return pattern;
  }

  function metrics() {
    const width = stage.clientWidth;
    const height = stage.clientHeight;
    const spanX = Math.max(1, bounds.maxX - bounds.minX);
    const spanY = Math.max(1, bounds.maxY - bounds.minY);
    const padding = Math.min(width, height) * 0.075;
    const fit = Math.min((width - 2 * padding) / spanX, (height - 2 * padding) / spanY);
    return {
      width, height, fit,
      worldX: (bounds.minX + bounds.maxX) / 2,
      worldY: (bounds.minY + bounds.maxY) / 2
    };
  }

  function screenPoint(point, m = metrics()) {
    const scale = m.fit * zoom;
    return [
      m.width / 2 + panX + (point[0] - m.worldX) * scale,
      m.height / 2 + panY - (point[1] - m.worldY) * scale
    ];
  }

  function resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.round(stage.clientWidth * dpr));
    const height = Math.max(1, Math.round(stage.clientHeight * dpr));
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }

  function drawGrid(m) {
    const scale = m.fit * zoom;
    if (scale < 5) return;
    const stepOptions = [1, 2, 5, 10, 20, 50, 100, 200];
    const step = stepOptions.find(value => value * scale >= 28) || 500;
    const topLeft = worldAt(0, 0, m);
    const bottomRight = worldAt(m.width, m.height, m);
    ctx.beginPath();
    ctx.strokeStyle = '#17243a';
    ctx.lineWidth = 1;
    for (let x = Math.ceil(Math.min(topLeft[0], bottomRight[0]) / step) * step; x <= Math.max(topLeft[0], bottomRight[0]); x += step) {
      const sx = screenPoint([x, 0], m)[0];
      ctx.moveTo(sx, 0); ctx.lineTo(sx, m.height);
    }
    for (let y = Math.ceil(Math.min(topLeft[1], bottomRight[1]) / step) * step; y <= Math.max(topLeft[1], bottomRight[1]); y += step) {
      const sy = screenPoint([0, y], m)[1];
      ctx.moveTo(0, sy); ctx.lineTo(m.width, sy);
    }
    ctx.stroke();
  }

  function draw() {
    if (!bounds) return;
    const m = metrics();
    ctx.fillStyle = '#080e1a';
    ctx.fillRect(0, 0, m.width, m.height);
    drawGrid(m);

    if (showTrace) {
      ctx.beginPath();
      points.forEach((point, index) => {
        const [x, y] = screenPoint(point, m);
        if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = '#b9cbe0';
      ctx.globalAlpha = 0.72;
      ctx.lineWidth = Math.min(3, 1.25 + Math.log2(zoom + 1) * 0.4);
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    const radius = Math.min(4.2, 1.65 + Math.log2(zoom + 1) * 0.7);
    for (let tag = 0; tag < 4; tag += 1) {
      if (!shownTags[tag]) continue;
      ctx.beginPath();
      for (let n = 0; n < points.length; n += 1) {
        if (states[n] !== tag) continue;
        const [x, y] = screenPoint(points[n], m);
        if (x < -radius || y < -radius || x > m.width + radius || y > m.height + radius) continue;
        ctx.moveTo(x + radius, y);
        ctx.arc(x, y, radius, 0, Math.PI * 2);
      }
      ctx.fillStyle = COLORS[tag];
      ctx.globalAlpha = 0.92;
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    const focus = hovered ?? selected;
    if (focus !== null) {
      const [x, y] = screenPoint(points[focus], m);
      ctx.beginPath();
      ctx.arc(x, y, radius + 5, 0, Math.PI * 2);
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }

  function worldAt(screenX, screenY, m = metrics()) {
    const scale = m.fit * zoom;
    return [
      m.worldX + (screenX - m.width / 2 - panX) / scale,
      m.worldY - (screenY - m.height / 2 - panY) / scale
    ];
  }

  function nearestVertex(x, y) {
    const m = metrics();
    let nearest = null;
    let best = 14 * 14;
    points.forEach((point, n) => {
      const [sx, sy] = screenPoint(point, m);
      const distance = (sx - x) ** 2 + (sy - y) ** 2;
      if (distance < best) { best = distance; nearest = n; }
    });
    return nearest;
  }

  function inspect(n) {
    if (n === null) {
      inspector.innerHTML = '<p>Hover or select a vertex to inspect its exact source and lifted coordinates.</p>';
      return;
    }
    const [x, y] = points[n];
    const state = states[n];
    const [cx, cy] = CORNERS[state];
    const [dx, dy] = DIRECTIONS[state];
    inspector.innerHTML = `<dl><dt>vertex</dt><dd>n=${n}</dd><dt>source</dt><dd>zₙ=(${x}, ${y})</dd><dt>state</dt><dd><span class="dot" style="background:${COLORS[state]}"></span>σ(n)=${state}, tag ${TAGS[state]}</dd><dt>direction</dt><dd>i^σ=(${dx}, ${dy})</dd><dt>lift</dt><dd>Gₙ=(${2 * x + cx}, ${2 * y + cy})</dd><dt>height</dt><dd>hₙ=${4 * n + state}</dd></dl>`;
  }

  function updateUrl() {
    const url = new URL(location.href);
    url.searchParams.set('rule', String(rule));
    url.searchParams.set('depth', String(depth));
    history.replaceState(null, '', url);
  }

  function setRule(value, updateHistory = true) {
    let nextRule;
    try {
      nextRule = parseRule(value);
    } catch (error) {
      ruleNumber.classList.add('invalid');
      ruleNumber.setCustomValidity(error.message);
      ruleHelp.textContent = error.message;
      return false;
    }
    rule = nextRule;
    const ruleText = rule.toString();
    ruleNumber.value = ruleText;
    ruleNumber.classList.remove('invalid');
    ruleNumber.setCustomValidity('');
    ruleHelp.textContent = rule <= 255n
      ? 'Period 8 · included in the static atlas.'
      : `Extended rule · period ${patternFor(rule).length.toLocaleString()} · generated on demand.`;
    ruleSlider.value = rule <= 255n ? ruleText : '255';
    ruleSlider.title = rule <= 255n ? `g${ruleText}` : 'Atlas slider covers g0–g255; use the exact field for this rule.';
    selected = null;
    hovered = null;
    zoom = 1;
    panX = panY = 0;
    const pattern = build(rule);
    inspect(null);
    draw();
    window.signedGaussianCurrentRule = {rule: ruleText, pattern: pattern.join('')};
    window.dispatchEvent(new CustomEvent('signed-gaussian-rule-change', {
      detail: window.signedGaussianCurrentRule
    }));
    if (updateHistory) updateUrl();
    return true;
  }

  function setDepth(value, updateHistory = true) {
    depth = Math.max(4, Math.min(16, Math.round(Number(value) || DEFAULT_DEPTH)));
    depthSlider.value = depth;
    selected = null;
    hovered = null;
    zoom = 1;
    panX = panY = 0;
    build(rule);
    inspect(null);
    draw();
    if (updateHistory) updateUrl();
  }

  ruleNumber.addEventListener('change', event => setRule(event.target.value));
  ruleSlider.addEventListener('input', event => setRule(event.target.value));
  depthSlider.addEventListener('input', event => setDepth(event.target.value));
  decreaseDepth.addEventListener('click', () => setDepth(depth - 1));
  increaseDepth.addEventListener('click', () => setDepth(depth + 1));
  document.querySelector('#previousRule').addEventListener('click', () => setRule(rule > 0n ? rule - 1n : 0n));
  document.querySelector('#nextRule').addEventListener('click', () => setRule(rule + 1n));
  document.querySelector('#resetView').addEventListener('click', () => {
    zoom = 1; panX = panY = 0; draw();
  });
  function setSecondaryControls(open) {
    explorer.classList.toggle('mobile-controls-open', open);
    secondaryControlsToggle.setAttribute('aria-expanded', String(open));
    const label = open ? 'Hide display settings' : 'Show display settings';
    secondaryControlsToggle.setAttribute('aria-label', label);
    secondaryControlsToggle.title = label;
  }
  secondaryControlsToggle.addEventListener('click', () => {
    setSecondaryControls(!explorer.classList.contains('mobile-controls-open'));
  });
  if (explorer.requestFullscreen) {
    fullscreenView.addEventListener('click', async () => {
      try {
        if (document.fullscreenElement === explorer) await document.exitFullscreen();
        else await explorer.requestFullscreen();
      } catch (error) {
        inspector.innerHTML = `<p>Full screen could not start: ${String(error.message || error)}</p>`;
      }
    });
    document.addEventListener('fullscreenchange', () => {
      const isFullscreen = document.fullscreenElement === explorer;
      const label = isFullscreen ? 'Exit full screen' : 'Enter full screen';
      fullscreenView.setAttribute('aria-label', label);
      fullscreenView.title = label;
      fullscreenView.setAttribute('aria-pressed', String(isFullscreen));
      if (!isFullscreen) setSecondaryControls(false);
      window.setTimeout(() => {
        resize();
        window.dispatchEvent(new Event('resize'));
      }, 50);
    });
  } else {
    fullscreenView.disabled = true;
    fullscreenView.title = 'Full-screen mode is not supported by this browser.';
  }
  document.querySelector('#traceToggle').addEventListener('change', event => {
    showTrace = event.target.checked; draw();
  });
  document.querySelector('#saveView').addEventListener('click', () => {
    if (window.dynamicLift3d?.active) {
      window.dynamicLift3d.save();
      return;
    }
    draw();
    const link = document.createElement('a');
    link.download = `signed-gaussian-g${abbreviated(rule.toString(), 32, 8)}-d${depth}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  });
  signButtons.forEach((button, place) => button.addEventListener('click', () => {
    const decoded = decodeRule(rule);
    const mask = 1n << BigInt(decoded.period - 1 - place);
    setRule(decoded.offset + (decoded.code ^ mask));
  }));
  tagButtons.forEach(button => button.addEventListener('click', () => {
    const tag = Number(button.dataset.tag);
    shownTags[tag] = !shownTags[tag];
    button.setAttribute('aria-pressed', String(shownTags[tag]));
    draw();
  }));

  canvas.addEventListener('wheel', event => {
    event.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const oldZoom = zoom;
    zoom = Math.max(0.5, Math.min(80, zoom * Math.exp(-event.deltaY * 0.0015)));
    const ratio = zoom / oldZoom;
    panX = x - rect.width / 2 - ratio * (x - rect.width / 2 - panX);
    panY = y - rect.height / 2 - ratio * (y - rect.height / 2 - panY);
    draw();
  }, {passive: false});
  function twoPointerGesture() {
    const [first, second] = [...activePointers.values()];
    return {
      distance: Math.max(1, Math.hypot(second.x - first.x, second.y - first.y)),
      x: (first.x + second.x) / 2,
      y: (first.y + second.y) / 2
    };
  }

  canvas.addEventListener('pointerdown', event => {
    activePointers.set(event.pointerId, {x: event.clientX, y: event.clientY});
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add('dragging');
    if (activePointers.size === 1) {
      dragging = true;
      didDrag = false;
      gestureWasPinch = false;
      dragX = event.clientX;
      dragY = event.clientY;
    } else {
      dragging = false;
      didDrag = true;
      gestureWasPinch = true;
      pinchGesture = twoPointerGesture();
    }
  });
  canvas.addEventListener('pointermove', event => {
    if (activePointers.has(event.pointerId)) {
      activePointers.set(event.pointerId, {x: event.clientX, y: event.clientY});
      if (activePointers.size >= 2) {
        const next = twoPointerGesture();
        if (pinchGesture) {
          const rect = canvas.getBoundingClientRect();
          const oldZoom = zoom;
          zoom = Math.max(0.5, Math.min(80, zoom * next.distance / pinchGesture.distance));
          const ratio = zoom / oldZoom;
          const previousX = pinchGesture.x - rect.left;
          const previousY = pinchGesture.y - rect.top;
          const nextX = next.x - rect.left;
          const nextY = next.y - rect.top;
          panX = nextX - rect.width / 2 - ratio * (previousX - rect.width / 2 - panX);
          panY = nextY - rect.height / 2 - ratio * (previousY - rect.height / 2 - panY);
        }
        pinchGesture = next;
        hovered = null;
        draw();
        return;
      }
      if (dragging) {
        const dx = event.clientX - dragX;
        const dy = event.clientY - dragY;
        if (Math.hypot(dx, dy) >= 2) didDrag = true;
        panX += dx;
        panY += dy;
        dragX = event.clientX;
        dragY = event.clientY;
        hovered = null;
        draw();
      }
      return;
    }
    const rect = canvas.getBoundingClientRect();
    hovered = nearestVertex(event.clientX - rect.left, event.clientY - rect.top);
    inspect(hovered ?? selected);
    draw();
  });
  function endPointer(event, cancelled = false) {
    activePointers.delete(event.pointerId);
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    pinchGesture = null;
    if (activePointers.size === 1) {
      const remaining = [...activePointers.values()][0];
      dragging = true;
      dragX = remaining.x;
      dragY = remaining.y;
      return;
    }
    dragging = false;
    canvas.classList.remove('dragging');
    if (!cancelled && !didDrag && !gestureWasPinch) {
      const rect = canvas.getBoundingClientRect();
      selected = nearestVertex(event.clientX - rect.left, event.clientY - rect.top);
      inspect(selected);
      draw();
    }
    gestureWasPinch = false;
  }
  canvas.addEventListener('pointerup', event => endPointer(event));
  canvas.addEventListener('pointercancel', event => endPointer(event, true));
  canvas.addEventListener('pointerleave', () => {
    hovered = null;
    inspect(selected);
    if (!dragging) draw();
  });
  canvas.addEventListener('dblclick', () => {
    zoom = 1; panX = panY = 0; draw();
  });

  const params = new URLSearchParams(location.search);
  const initialRule = params.get('rule') ?? '0';
  const initialDepth = Number(params.get('depth'));
  depth = Number.isFinite(initialDepth) && initialDepth >= 4 && initialDepth <= 16
    ? Math.round(initialDepth) : DEFAULT_DEPTH;
  depthSlider.value = depth;
  if (!setRule(initialRule, false)) setRule('0', false);
  new ResizeObserver(resize).observe(stage);
  resize();
})();
