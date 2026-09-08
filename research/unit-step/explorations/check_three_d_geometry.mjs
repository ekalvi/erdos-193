#!/usr/bin/env node
// Fixed-size exact checker, one worker, no subprocesses or accumulated search state.
// All integers below have absolute value < 2^53; the geometry witness uses BigInt.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
const started = Date.now();
const sourceSha256 = createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex');
const log = (data) => console.log(JSON.stringify({ time: new Date().toISOString(), ...data }));
log({ phase: 'start', sourceSha256, workers: 1, maxSteps: 16,
  resume: 'Fixed-size verifier: rerun in full; no expensive accumulated state.' });

function abelianSquare(w) {
  for (let i = 0; i < w.length; ++i) {
    for (let len = 1; i + 2 * len <= w.length; ++len) {
      const d = [0, 0, 0];
      for (let j = 0; j < len; ++j) { ++d[w[i + j]]; --d[w[i + len + j]]; }
      if (d.every(x => x === 0)) return true;
    }
  }
  return false;
}
for (let n = 0; n < 3 ** 8; ++n) {
  let t = n;
  const w = Array.from({ length: 8 }, () => { const r = t % 3; t = Math.floor(t / 3); return r; });
  assert(abelianSquare(w));
}
// Canonical ternary extension tree, with letters named by first appearance.
const ternaryTree = [['']];
for (let len = 1; len <= 8; ++len) {
  const next = [];
  for (const w of ternaryTree.at(-1)) {
    const max = w.length ? Math.max(...[...w].map(Number)) : -1;
    for (let a = 0; a <= Math.min(2, max + 1); ++a) {
      const v = w + a;
      if (!abelianSquare([...v].map(Number))) next.push(v);
    }
  }
  ternaryTree.push(next);
}
assert.equal(ternaryTree[8].length, 0);

// Horizontal steps are a_0 u, a_1 u, a_2 u; vertical steps are +/-v.
// Formal horizontal counts X are in Z^3, while height is in Z.
// Three equal heights are always geometrically collinear. Otherwise, the
// height-weighted horizontal defect vanishes identically iff all its three
// integer coefficients vanish. This explores forced, coefficient-independent
// failures only; particular coefficients can cause additional failures.
const counts = Array(17).fill(0);
let longest = [];
const p = [[0, 0, 0, 0]];
function forcedFailure(q) {
  for (const r of p) if (r.every((x, j) => x === q[j])) return true;
  for (let i = 0; i < p.length; ++i) for (let j = i + 1; j < p.length; ++j) {
    const x = p[i], y = p[j];
    const a = y[3] - x[3], b = q[3] - y[3];
    if (a === 0 && b === 0) return true;
    if ([0, 1, 2].every(r => b * (y[r] - x[r]) === a * (q[r] - y[r]))) return true;
  }
  return false;
}
function dfs(w, maxH, seenV) {
  ++counts[w.length];
  if (w.length > longest.length) longest = [...w];
  if (w.length === 16) return;
  const last = w.at(-1);
  const options = [];
  if (last === undefined || typeof last === 'string')
    for (let r = 0; r <= Math.min(2, maxH + 1); ++r) options.push(r);
  if (last === undefined || typeof last === 'number')
    options.push(...(seenV ? ['+', '-'] : ['+']));
  for (const step of options) {
    const q = [...p.at(-1)];
    if (typeof step === 'number') ++q[step]; else q[3] += step === '+' ? 1 : -1;
    if (forcedFailure(q)) continue;
    p.push(q);
    dfs([...w, step], typeof step === 'number' ? Math.max(maxH, step) : maxH,
      seenV || typeof step === 'string');
    p.pop();
  }
}
dfs([], -1, false);
assert.equal(counts[16], 0);
assert.equal(longest.length, 15);

// A concrete integer realization of the longest formal survivor.
// If this assertion fails, only the proposed sharpness witness fails, not the
// analytic 16-step theorem. The final output records the actual coefficients.
const coefficients = [1n, 1000n, 1000000n];
const vertices = [[0n, 0n]];
for (const step of longest) {
  const q = [...vertices.at(-1)];
  if (typeof step === 'number') q[0] += coefficients[step]; else q[1] += step === '+' ? 1n : -1n;
  for (const r of vertices) assert(q[0] !== r[0] || q[1] !== r[1]);
  for (let i = 0; i < vertices.length; ++i) for (let j = i + 1; j < vertices.length; ++j) {
    const a = vertices[i], b = vertices[j];
    assert((b[0] - a[0]) * (q[1] - b[1]) !== (b[1] - a[1]) * (q[0] - b[0]));
  }
  vertices.push(q);
}
log({ phase: 'complete', sourceSha256, elapsedMs: Date.now() - started,
  ternaryWordsChecked: 3 ** 8, ternaryTree, canonicalSurvivorsByStepCount: counts,
  longestFormalWord: longest, integerWitnessCoefficients: coefficients.map(String),
  witnessSteps: longest.length, witnessVertices: vertices.map(q => q.map(String)),
  scope: 'Exact bounded checks; analytic report proves the all-coefficient 16-step obstruction. No unrestricted five-step theorem.' });
