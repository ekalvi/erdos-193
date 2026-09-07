#!/usr/bin/env node
// Bounded exact algebra checks only; no prefix search or infinite certification.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
const started = new Date().toISOString();
const mod = (a, p) => ((a % p) + p) % p;
const v2 = n => { n = Math.abs(n); assert(n > 0); let e = 0; while (n % 2 === 0) { n /= 2; e++; } return e; };
const primes = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43];
let signPairCases = 0;
for (const p of primes) for (let c = 1; c < p; c++) {
  const allowed = x => mod(x, p) === c || mod(x, p) === p - c;
  for (let a = 1; a < p; a++) for (let b = 1; b < p; b++) {
    signPairCases++;
    if (mod(a + b, p) === 0) continue;
    assert(!(allowed(a * a) && allowed(b * b)
      && allowed((a + b) ** 2 * ((p + 1) / 2))));
  }
}
// The exception p=3 is genuine: squared increments 1,1,4 over heights 1,1,2.
assert.equal(mod(4 * 2, 3), 2);

// Exact conjugacy of the apparent Q=X^2-2Y^2 alternative to g85.
const U = [[1, 0], [1, 1], [-1, 0], [-1, -1]];
const first = [2, 1, 0, 3], second = [1, 0, 3, 2];
const label = [1, 0, 3, 2]; // alternative state -> Gaussian exponent
const gaussianU = [[1, 0], [0, 1], [-1, 0], [0, -1]];
const B = ([x, y]) => [x + y, x];
const L = ([x, y]) => [2 * y, x];
const plus = (a, b) => a.map((x, i) => x + b[i]);
for (let s = 0; s < 4; s++) {
  assert.deepEqual(U[s], B(gaussianU[label[s]]));
  assert.deepEqual(plus(U[first[s]], U[second[s]]), L(U[s]));
  assert.equal(label[first[s]], mod(-label[s], 4));
  assert.equal(label[second[s]], mod(1 - label[s], 4));
}
let normCases = 0;
for (let x = -32; x <= 32; x++) for (let y = -32; y <= 32; y++) {
  if (x === 0 && y === 0) continue;
  assert.equal(v2(-x * x + 2 * x * y + y * y), v2(x * x + y * y));
  normCases++;
}
const gaussianTags = [[0, 0], [-1, 0], [-1, 1], [0, -1]];
const menu = new Set();
for (let a = 0; a < 4; a++) for (const jump of [1, 2]) {
  const b = (a + jump) % 4;
  const xy = gaussianU[a].map((x, j) => 2 * x + gaussianTags[b][j] - gaussianTags[a][j]);
  menu.add(JSON.stringify([...B(xy), 4 + b - a]));
}
const expectedMenu = [[1, 1, 5], [3, 0, 5], [-3, -1, 5], [-1, 0, 1], [2, 1, 6], [-2, -1, 2]];
assert.deepEqual([...menu].sort(), expectedMenu.map(JSON.stringify).sort());

// An eight-state algebraic system for sqrt(-2): equations, not a new walk.
const X = [1, 1, 1, 1, -1, -1, -1, -1];
const U8 = X.map((x, s) => [x, -(X[(s + 1) % 8] + X[(s + 3) % 8]) / 2]);
for (let s = 0; s < 8; s++) {
  assert.deepEqual(plus(U8[(s + 1) % 8], U8[(s + 3) % 8]), [-2 * U8[s][1], U8[s][0]]);
  assert.equal(mod(U8[s][0], 2), 1);
}

// Supplemental exhaustive algebra: no sum of two permutations on <=4 states
// has the eigenvalue sqrt(-2). BigInt elimination makes this exact.
function permutations(a) {
  if (!a.length) return [[]];
  return a.flatMap((x, i) => permutations(a.filter((_, j) => i !== j)).map(t => [x, ...t]));
}
function rank(matrix) {
  const a = matrix.map(row => row.map(BigInt));
  let r = 0;
  for (let c = 0; c < a[0].length && r < a.length; c++) {
    let pivot = r;
    while (pivot < a.length && a[pivot][c] === 0n) pivot++;
    if (pivot === a.length) continue;
    [a[r], a[pivot]] = [a[pivot], a[r]];
    for (let j = r + 1; j < a.length; j++) {
      if (a[j][c] === 0n) continue;
      const u = a[r][c], v = a[j][c];
      for (let k = c; k < a[0].length; k++) a[j][k] = u * a[j][k] - v * a[r][k];
    }
    r++;
  }
  return r;
}
let permutationPairs = 0;
for (let n = 1; n <= 4; n++) {
  const ps = permutations(Array.from({ length: n }, (_, i) => i));
  for (const p of ps) for (const q of ps) {
    const a = p.map((_, i) => p.map((_, j) => +(p[i] === j) + +(q[i] === j)));
    const a2plus2 = a.map((row, i) => row.map((_, j) => row.reduce((s, x, k) => s + x * a[k][j], 0) + 2 * +(i === j)));
    assert.equal(rank(a2plus2), n);
    permutationPairs++;
  }
}
// Every odd-order permutation graph contains a collinear triple.
let permutationGraphs = 0;
for (const p of [3, 5, 7]) for (const tail of permutations(Array.from({ length: p - 1 }, (_, i) => i + 1))) {
  const f = [0, ...tail];
  let collinear = false;
  for (let a = 0; a < p; a++) for (let b = a + 1; b < p; b++) for (let c = b + 1; c < p; c++) {
    if (mod((b - a) * (f[c] - f[a]) - (c - a) * (f[b] - f[a]), p) === 0) collinear = true;
  }
  assert(collinear);
  permutationGraphs++;
}
console.log(JSON.stringify({
  status: 'pass', started, finished: new Date().toISOString(),
  source_sha256: createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex'),
  scope: 'bounded exact algebra; infinite claims are proved in new-arithmetic.md',
  threads: 1, primes, signPairCases, normCases, permutationPairs, permutationGraphs,
  transformedExistingSixStepMenu: expectedMenu,
  sqrtMinusTwoEightStateVectors: U8,
}, null, 2));
