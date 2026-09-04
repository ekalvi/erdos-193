(() => {
  const directions = [[1, 0], [0, 1], [-1, 0], [0, -1]];
  const colors = ['#56b4e9', '#c58cf4', '#38c99a', '#e6a93a'];

  document.querySelectorAll('[data-family-rule]').forEach((canvas, index) => {
    const rule = Number(canvas.dataset.familyRule);
    const signs = Array.from({ length: 8 }, (_, bit) => rule & (1 << (7 - bit)) ? -1 : 1);
    const points = [[0, 0]];
    let x = 0;
    let y = 0;

    for (let n = 0; n < 256; n++) {
      let direction = 0;
      let value = n;
      let bit = 0;
      while (value) {
        if (value & 1) direction += signs[bit & 7];
        bit++;
        value >>= 1;
      }
      direction = (direction % 4 + 4) % 4;
      x += directions[direction][0];
      y += directions[direction][1];
      points.push([x, y]);
    }

    const xs = points.map(point => point[0]);
    const ys = points.map(point => point[1]);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const span = Math.max(maxX - minX, maxY - minY, 1);
    const padding = 14;
    const scale = (canvas.width - padding * 2) / span;
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const context = canvas.getContext('2d');
    const project = point => [
      canvas.width / 2 + (point[0] - centerX) * scale,
      canvas.height / 2 - (point[1] - centerY) * scale,
    ];

    context.fillStyle = '#04060d';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.beginPath();
    points.forEach((point, pointIndex) => {
      const [projectedX, projectedY] = project(point);
      if (pointIndex) context.lineTo(projectedX, projectedY);
      else context.moveTo(projectedX, projectedY);
    });
    context.strokeStyle = colors[index];
    context.lineWidth = 2.5;
    context.lineCap = 'round';
    context.lineJoin = 'round';
    context.globalAlpha = .9;
    context.stroke();
    context.globalAlpha = 1;

    for (let n = 0; n < points.length; n += 32) {
      const [projectedX, projectedY] = project(points[n]);
      context.beginPath();
      context.arc(projectedX, projectedY, 2.2, 0, Math.PI * 2);
      context.fillStyle = '#edf5ff';
      context.fill();
    }
  });
})();
