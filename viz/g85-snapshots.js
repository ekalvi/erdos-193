(() => {
  'use strict';
  const count = 1024;
  const directions = [[1, 0], [0, 1], [-1, 0], [0, -1]];
  const offsets = [[0, 0], [-1, 0], [-1, 1], [0, -1]];
  const state = n => {
    let sum = 0;
    for (let place = 0; n; n >>>= 1, place++) if (n & 1) sum += place % 2 ? -1 : 1;
    return (sum % 4 + 4) % 4;
  };
  const source = [];
  const lift = [];
  let x = 0, y = 0;
  for (let n = 0; n < count; n++) {
    const sigma = state(n);
    source.push([x, y]);
    lift.push([2 * x + offsets[sigma][0], 2 * y + offsets[sigma][1], 4 * n + sigma]);
    if (n + 1 < count) {
      x += directions[sigma][0];
      y += directions[sigma][1];
    }
  }

  function render(canvas, points, project, hueStart, hueEnd) {
    const context = canvas.getContext('2d');
    if (!context) return;
    const draw = () => {
      const box = canvas.parentElement.getBoundingClientRect();
      const width = Math.max(1, box.width), height = Math.max(1, box.height);
      const ratio = Math.min(devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      context.fillStyle = '#04060d';
      context.fillRect(0, 0, width, height);
      const projected = points.map(project);
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (const [px, py] of projected) {
        minX = Math.min(minX, px); maxX = Math.max(maxX, px);
        minY = Math.min(minY, py); maxY = Math.max(maxY, py);
      }
      const padding = 28;
      const scale = Math.min((width - 2 * padding) / (maxX - minX || 1),
                             (height - 2 * padding) / (maxY - minY || 1));
      const drawnWidth = (maxX - minX) * scale, drawnHeight = (maxY - minY) * scale;
      const left = (width - drawnWidth) / 2, top = (height - drawnHeight) / 2;
      const screen = ([px, py]) => [left + (px - minX) * scale,
                                    top + drawnHeight - (py - minY) * scale];
      context.lineWidth = 1;
      for (let i = 1; i < projected.length; i++) {
        const t = i / (projected.length - 1);
        const hue = hueStart + (hueEnd - hueStart) * t;
        context.strokeStyle = `hsl(${hue} 72% ${55 + 10 * t}%)`;
        context.globalAlpha = 0.82;
        context.beginPath();
        context.moveTo(...screen(projected[i - 1]));
        context.lineTo(...screen(projected[i]));
        context.stroke();
      }
      context.globalAlpha = 1;
      const start = screen(projected[0]), end = screen(projected.at(-1));
      context.fillStyle = '#fff'; context.beginPath(); context.arc(...start, 4, 0, Math.PI * 2); context.fill();
      context.fillStyle = '#f2bf63'; context.beginPath(); context.arc(...end, 4, 0, Math.PI * 2); context.fill();
    };
    draw();
    if ('ResizeObserver' in window) new ResizeObserver(draw).observe(canvas.parentElement);
    else addEventListener('resize', draw);
  }

  const planar = document.querySelector('#g85PlanarSnapshot');
  const lifted = document.querySelector('#g85LiftSnapshot');
  if (planar) render(planar, source, ([px, py]) => [px, py], 188, 202);
  if (lifted) render(lifted, lift, ([px, py, h]) => [px - py, (px + py) * .42 - h * .012], 145, 215);
})();
