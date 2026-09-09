// Run: node design/test_family_vector_menu.cjs (bounded, single-process test).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {stepMenu} = require('../results/vector-menu.js');
const audit = require('../results/signed-gaussian-unit-step-audit.json');
const histogram = {};
const minimizers = [];
for (let rule = 0; rule < 256; rule++) {
  const pattern = rule.toString(2).padStart(8, '0').replaceAll('0', '+').replaceAll('1', '-');
  const menu = stepMenu(pattern);
  histogram[menu.length] = (histogram[menu.length] || 0) + 1;
  if (menu.length === 6) minimizers.push(rule);
  // Independent finite-walk cross-check, not the source of the complete-menu claim.
  const state = n => {
    let sum = 0;
    for (let j = 0; n; n >>>= 1, j++) if (n & 1) sum += pattern[j % 8] === '+' ? 1 : -1;
    return (sum % 4 + 4) % 4;
  };
  const directions = [[1, 0], [0, 1], [-1, 0], [0, -1]];
  const offsets = [[0, 0], [-1, 0], [-1, 1], [0, -1]];
  let x = 0, y = 0;
  const vertex = n => {
    const s = state(n);
    return [2 * x + offsets[s][0], 2 * y + offsets[s][1], 4 * n + s];
  };
  let previous = vertex(0);
  const seen = new Set();
  for (let n = 0; n < 4096; n++) {
    const [dx, dy] = directions[state(n)];
    x += dx; y += dy;
    const next = vertex(n + 1);
    seen.add(next.map((v, j) => v - previous[j]).join(','));
    previous = next;
  }
  assert.deepEqual([...seen].sort(), menu.map(m => m.vector.join(',')).sort(), `g${rule}`);
}
assert.deepEqual(histogram, audit.step_count_histogram);
assert.deepEqual(minimizers, [85, 170]);
for (const saved of audit.minimizers) assert.deepEqual(stepMenu(saved.pattern), saved.menu);
assert.throws(() => stepMenu(''));
assert.throws(() => stepMenu('+-x'));
assert.deepEqual(stepMenu('+-'), stepMenu('+-+-+-+-'));
assert.deepEqual(stepMenu('-+'), stepMenu('-+-+-+-+'));
assert.ok(stepMenu('++++++++-').length >= 6); // extended period-nine rule
assert.ok(stepMenu('+'.repeat(4096)).length >= 6); // browser maximum-period scale
// Guard against showing an old lift next to the improved menu.
for (const file of ['interactive-viewer.js', 'dynamic-lift3d.js']) {
  const source = fs.readFileSync(path.join(__dirname, '../results', file), 'utf8');
  assert.match(source, /const CORNERS = \[\[0, 0\], \[-1, 0\], \[-1, 1\], \[0, -1\]\]/);
}
console.log('PASS: all 256 exact menu counts, both saved menus, independent 4096-step prefixes, extended patterns, and preview offsets.');
