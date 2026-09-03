(() => {
  'use strict';

  const STEPS = 500000;
  const DIRECTIONS = [[1, 0], [0, 1], [-1, 0], [0, -1]];
  const CORNERS = [[0, 0], [0, 1], [-1, 1], [-1, 0]];
  const canvas = document.querySelector('#liftCanvas');
  const flatCanvas = document.querySelector('#curveCanvas');
  const button = document.querySelector('#lift3d');
  const status = document.querySelector('#liftStatus');
  const note = document.querySelector('#viewerNote');
  const inspector = document.querySelector('#inspector');

  if (!canvas || !button) return;

  const gl = canvas.getContext('webgl', {alpha: false, antialias: true, preserveDrawingBuffer: true});
  let active = false;
  let program = null;
  let positionBuffer = null;
  let colorBuffer = null;
  let vertexCount = 0;
  let builtRule = null;
  let buildToken = 0;
  let yaw = -0.72;
  let pitch = -0.48;
  let zoom = 2.35;
  let panX = 0;
  let panY = 0;
  let dragging = false;
  let lastX = 0;
  let lastY = 0;

  const vertexSource = `
    attribute vec3 aPosition;
    attribute vec3 aColor;
    uniform float uYaw;
    uniform float uPitch;
    uniform float uZoom;
    uniform float uAspect;
    uniform vec2 uPan;
    varying vec3 vColor;
    void main() {
      float cy = cos(uYaw), sy = sin(uYaw);
      float cp = cos(uPitch), sp = sin(uPitch);
      vec3 p = aPosition;
      vec3 q = vec3(cy*p.x + sy*p.z, p.y, -sy*p.x + cy*p.z);
      q = vec3(q.x, cp*q.y - sp*q.z, sp*q.y + cp*q.z);
      float w = 3.6 - q.z;
      gl_Position = vec4(q.x*uZoom/uAspect + uPan.x*w,
                         q.y*uZoom + uPan.y*w, q.z*0.08, w);
      vColor = aColor;
    }
  `;
  const fragmentSource = `
    precision mediump float;
    varying vec3 vColor;
    void main() { gl_FragColor = vec4(vColor, 0.82); }
  `;

  function shader(type, source) {
    const result = gl.createShader(type);
    gl.shaderSource(result, source);
    gl.compileShader(result);
    if (!gl.getShaderParameter(result, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(result));
    }
    return result;
  }

  function initializeGl() {
    if (!gl) throw new Error('WebGL is not available in this browser.');
    if (program) return;
    program = gl.createProgram();
    gl.attachShader(program, shader(gl.VERTEX_SHADER, vertexSource));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, fragmentSource));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(program));
    }
    positionBuffer = gl.createBuffer();
    colorBuffer = gl.createBuffer();
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  }

  function stateFor(n, signs) {
    let total = 0;
    let place = 0;
    while (n) {
      if (n & 1) total += signs[place & 7];
      place += 1;
      n = Math.floor(n / 2);
    }
    return ((total % 4) + 4) % 4;
  }

  function abbreviated(text, head = 20, tail = 8) {
    return text.length <= head + tail + 1 ? text : `${text.slice(0, head)}…${text.slice(-tail)}`;
  }

  function generate(pattern) {
    const signs = [...pattern].map(sign => sign === '-' ? -1 : 1);
    const count = STEPS + 1;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    let x = 0;
    let z = 0;
    let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;

    for (let n = 0; n < count; n += 1) {
      const state = stateFor(n, signs);
      const corner = CORNERS[state];
      const gx = 2 * x + corner[0];
      const gz = 2 * z + corner[1];
      const offset = n * 3;
      positions[offset] = gx;
      positions[offset + 1] = 4 * n + state;
      positions[offset + 2] = gz;
      minX = Math.min(minX, gx); maxX = Math.max(maxX, gx);
      minZ = Math.min(minZ, gz); maxZ = Math.max(maxZ, gz);

      const t = n / STEPS;
      colors[offset] = 0.96 - 0.55 * t;
      colors[offset + 1] = 0.48 + 0.32 * t;
      colors[offset + 2] = 0.28 + 0.68 * t;

      if (n < STEPS) {
        x += DIRECTIONS[state][0];
        z += DIRECTIONS[state][1];
      }
    }

    const planarSpan = Math.max(maxX - minX, maxZ - minZ, 1);
    const centerX = (minX + maxX) / 2;
    const centerZ = (minZ + maxZ) / 2;
    const minHeight = positions[1];
    const maxHeight = positions[(count - 1) * 3 + 1];
    const centerHeight = (minHeight + maxHeight) / 2;
    const heightSpan = Math.max(maxHeight - minHeight, 1);
    for (let n = 0; n < count; n += 1) {
      const offset = n * 3;
      positions[offset] = (positions[offset] - centerX) / planarSpan * 1.8;
      positions[offset + 1] = (positions[offset + 1] - centerHeight) / heightSpan * 1.8;
      positions[offset + 2] = (positions[offset + 2] - centerZ) / planarSpan * 1.8;
    }
    return {positions, colors, count};
  }

  function resize() {
    if (!active || !gl) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.round(canvas.clientWidth * ratio));
    const height = Math.max(1, Math.round(canvas.clientHeight * ratio));
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    gl.viewport(0, 0, width, height);
  }

  function draw() {
    if (!active || !program || !vertexCount) return;
    resize();
    gl.clearColor(0.027, 0.043, 0.078, 1);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(program);

    const positionLocation = gl.getAttribLocation(program, 'aPosition');
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.enableVertexAttribArray(positionLocation);
    gl.vertexAttribPointer(positionLocation, 3, gl.FLOAT, false, 0, 0);
    const colorLocation = gl.getAttribLocation(program, 'aColor');
    gl.bindBuffer(gl.ARRAY_BUFFER, colorBuffer);
    gl.enableVertexAttribArray(colorLocation);
    gl.vertexAttribPointer(colorLocation, 3, gl.FLOAT, false, 0, 0);

    gl.uniform1f(gl.getUniformLocation(program, 'uYaw'), yaw);
    gl.uniform1f(gl.getUniformLocation(program, 'uPitch'), pitch);
    gl.uniform1f(gl.getUniformLocation(program, 'uZoom'), zoom);
    gl.uniform1f(gl.getUniformLocation(program, 'uAspect'), canvas.width / canvas.height);
    gl.uniform2f(gl.getUniformLocation(program, 'uPan'), panX, panY);
    gl.drawArrays(gl.LINE_STRIP, 0, vertexCount);
  }

  function resetCamera() {
    yaw = -0.72;
    pitch = -0.48;
    zoom = 2.35;
    panX = panY = 0;
    draw();
  }

  function build(rule, pattern) {
    if (!active) return;
    const token = ++buildToken;
    const shortRule = abbreviated(rule);
    status.style.display = 'block';
    status.title = '';
    status.textContent = `BUILDING g${shortRule} · ${STEPS.toLocaleString()} STEPS · UNVERIFIED`;
    window.setTimeout(() => {
      if (!active || token !== buildToken) return;
      try {
        initializeGl();
        const data = generate(pattern);
        if (!active || token !== buildToken) return;
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, data.positions, gl.STATIC_DRAW);
        gl.bindBuffer(gl.ARRAY_BUFFER, colorBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, data.colors, gl.STATIC_DRAW);
        vertexCount = data.count;
        builtRule = rule;
        status.textContent = `DYNAMIC g${shortRule} · ${STEPS.toLocaleString()} STEPS · NOT VERIFIED`;
        draw();
      } catch (error) {
        status.textContent = '3D PREVIEW UNAVAILABLE';
        status.title = String(error.message || error);
      }
    }, 30);
  }

  function show() {
    active = true;
    inspector.hidden = true;
    flatCanvas.style.display = 'none';
    canvas.style.display = 'block';
    status.style.display = 'block';
    button.textContent = 'Return to 2D';
    button.classList.add('primary');
    note.textContent = 'drag to orbit · scroll to zoom · shift-drag to pan · double-click to reset';
    resetCamera();
    const current = window.signedGaussianCurrentRule;
    if (current) build(current.rule, current.pattern);
  }

  function hide() {
    active = false;
    inspector.hidden = false;
    buildToken += 1;
    canvas.style.display = 'none';
    flatCanvas.style.display = 'block';
    status.style.display = 'none';
    button.textContent = 'Lift to 3D';
    button.classList.remove('primary');
    note.textContent = 'scroll to zoom · drag to pan · select a vertex · double-click to reset';
    inspector.innerHTML = '<p>Hover or select a vertex to inspect its exact source and lifted coordinates.</p>';
  }

  button.addEventListener('click', () => active ? hide() : show());
  window.addEventListener('signed-gaussian-rule-change', event => {
    if (active && event.detail.rule !== builtRule) {
      build(event.detail.rule, event.detail.pattern);
    }
  });
  window.addEventListener('resize', draw);
  document.querySelector('#resetView').addEventListener('click', () => {
    if (active) resetCamera();
  });

  canvas.addEventListener('pointerdown', event => {
    dragging = true;
    lastX = event.clientX;
    lastY = event.clientY;
    canvas.classList.add('dragging');
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener('pointermove', event => {
    if (!dragging) return;
    const dx = event.clientX - lastX;
    const dy = event.clientY - lastY;
    lastX = event.clientX;
    lastY = event.clientY;
    if (event.shiftKey) {
      panX += dx / canvas.clientWidth * 2;
      panY -= dy / canvas.clientHeight * 2;
    } else {
      yaw += dx * 0.008;
      pitch = Math.max(-1.5, Math.min(1.5, pitch + dy * 0.008));
    }
    draw();
  });
  function endDrag(event) {
    dragging = false;
    canvas.classList.remove('dragging');
    if (event.pointerId !== undefined && canvas.hasPointerCapture(event.pointerId)) {
      canvas.releasePointerCapture(event.pointerId);
    }
  }
  canvas.addEventListener('pointerup', endDrag);
  canvas.addEventListener('pointercancel', endDrag);
  canvas.addEventListener('wheel', event => {
    event.preventDefault();
    zoom = Math.max(0.7, Math.min(18, zoom * Math.exp(-event.deltaY * 0.0012)));
    draw();
  }, {passive: false});
  canvas.addEventListener('dblclick', resetCamera);

  window.dynamicLift3d = {
    get active() { return active; },
    save() {
      draw();
      const link = document.createElement('a');
      link.download = `signed-gaussian-g${abbreviated(builtRule, 32, 8)}-dynamic-3d-unverified.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    }
  };
})();
