#!/usr/bin/env node
// Bounded regression/algebra checks; these do not certify a 4D/5D impossibility.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync, spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { advance, initialState, points, endingTriple, directTriple, validateState } from './contradiction_probe.mjs';

// Independently compare the primitive-chord and direct cross-product tests.
for (let code = 0; code < 3 ** 8; code++) {
  let n = code;
  const word = Array.from({ length: 8 }, () => { const a = n % 3; n = Math.floor(n / 3); return a; });
  const p = points(word, 3);
  let viaChords = false;
  for (let end = 2; end <= 8; end++) if (endingTriple(p.slice(0, end + 1))) viaChords = true;
  const viaProducts = directTriple(word, 3) !== null;
  assert.equal(viaChords, viaProducts);
  assert(viaProducts);
  assert(directTriple(word, 3, true));
}

function finish(state, alphabet, target) {
  const p = points(state.word, alphabet);
  while (state.status === 'running') advance(state, p, alphabet, target);
  validateState(state, alphabet, target);
  return state;
}
const ternary = finish(initialState(), 3, 8);
assert.equal(ternary.status, 'exhausted');
assert.equal(ternary.bestWord.length, 7);
assert.deepEqual(ternary.acceptedByDepth, [1, 1, 1, 2, 3, 5, 5, 3]);
// Check every possible small checkpoint boundary, including backtracking states.
for (let pause = 0; pause <= ternary.attempted; pause++) {
  const state = initialState(), p = points([], 3);
  while (state.status === 'running' && state.attempted < pause) advance(state, p, 3, 8);
  const resumed = JSON.parse(JSON.stringify(state));
  validateState(resumed, 3, 8);
  assert.deepEqual(finish(resumed, 3, 8), ternary);
}
assert.equal(finish(initialState(), 2, 4).bestWord.length, 3);
assert.equal(finish(initialState(), 1, 2).bestWord.length, 1);
for (const alphabet of [4, 5]) {
  const state = finish(initialState(), alphabet, 12);
  assert.equal(state.status, 'witness');
  assert.equal(state.word.length, 12);
}

const unequal = [...'012301213230'].map(Number);
assert.equal(directTriple(unequal, 4, true), null);
assert.deepEqual(directTriple(unequal, 4), [0, 4, 12]);
assert.deepEqual(points(unequal, 4)[4], [1, 1, 1, 1]);
assert.deepEqual(points(unequal, 4)[12], [3, 3, 3, 3]);

// A periodic local countermodel, not a valid infinite walk.
const period = '01020103';
for (let start = 0; start < period.length; start++) {
  const word = Array.from({ length: 15 }, (_, n) => Number(period[(start + n) % period.length]));
  assert.equal(directTriple(word, 4), null);
}
assert.deepEqual(directTriple([...(period + period)].map(Number), 4), [0, 8, 16]);

// Exact deviation-space identity for Shallit's incidence matrix.
const M = [
  [3, 1, 3, 1, 6], [6, 3, 1, 3, 1], [1, 6, 3, 1, 3],
  [3, 1, 6, 3, 1], [1, 3, 1, 6, 3],
].map(row => row.map(BigInt));
const mul = (A, v) => A.map(row => row.reduce((sum, x, r) => sum + x * v[r], 0n));
const transpose = A => A[0].map((_, j) => A.map(row => row[j]));
const MT = transpose(M), B = M.map((_, j) => mul(MT, M.map(row => row[j])));
// B is symmetric, so the assembled columns can also be read as rows.
for (let j = 0; j < 5; j++) {
  assert.equal(M[j].reduce((a, b) => a + b, 0n), 14n);
  assert.equal(MT[j].reduce((a, b) => a + b, 0n), 14n);
  const basis = Array.from({ length: 5 }, (_, r) => BigInt((r === j ? 1 : 0) - (r === 4 ? 1 : 0)));
  const b = mul(B, basis), bb = mul(B, b);
  assert.deepEqual(bb.map((x, r) => x - 42n * b[r] + 421n * basis[r]), Array(5).fill(0n));
  assert.deepEqual(mul(M, mul(MT, basis)), mul(MT, mul(M, basis)));
}
let counts = [1n, 0n, 0n, 0n, 0n], length = 1n, t = 2n, tNext = 42n;
for (let k = 0; k <= 10; k++) {
  const deviation = counts.map(x => 5n * x - length);
  assert.equal(deviation.reduce((sum, x) => sum + x * x, 0n), 10n * t);
  counts = mul(M, counts); length *= 14n;
  [t, tNext] = [tNext, 42n * tNext - 421n * t];
}
// Verify the preserved partial search, then independently test every triple by rank.
const probePath = fileURLToPath(new URL('contradiction_probe.mjs', import.meta.url));
const evidence = JSON.parse(fs.readFileSync(new URL('checks/contradiction-4d-tree.json', import.meta.url), 'utf8'));
assert.equal(evidence.codeSha256, createHash('sha256').update(fs.readFileSync(probePath)).digest('hex'));
assert.equal(evidence.schema, 1);
assert.equal(evidence.alphabet, 4);
assert.equal(evidence.target, 128);
assert.equal(evidence.bestSteps, 128);
assert.equal(evidence.bestWord.length, 128);
assert.match(evidence.bestWord, /^[0-3]+$/);
assert.equal(evidence.outcome, 'witness');
assert.equal(evidence.countsScope, 'partial DFS traversal only');
assert.equal(evidence.provesImpossibility, false);
assert.equal(evidence.provesInfiniteExistence, false);
const replay = finish(initialState(), 4, 128);
assert.equal(replay.word.join(''), evidence.bestWord);
assert.equal(replay.attempted, evidence.attempted);
assert.equal(replay.attempted, 1250);
assert.deepEqual(replay.acceptedByDepth, evidence.acceptedByDepth);
assert.deepEqual(replay.rejectedByDepth, evidence.rejectedByDepth);
const vertices = [Array(4).fill(0n)];
for (const a of evidence.bestWord) {
  const p = [...vertices.at(-1)]; p[Number(a)]++; vertices.push(p);
}
let triples = 0;
for (let i = 0; i < vertices.length; i++) for (let j = i + 1; j < vertices.length; j++) {
  for (let k = j + 1; k < vertices.length; k++) {
    const u = vertices[j].map((x, r) => x - vertices[i][r]);
    const v = vertices[k].map((x, r) => x - vertices[j][r]);
    let rankTwo = false;
    for (let r = 0; r < 4; r++) for (let s = r + 1; s < 4; s++) {
      if (u[r] * v[s] !== u[s] * v[r]) rankTwo = true;
    }
    assert(rankTwo); triples++;
  }
}
assert.equal(triples, 349504);

// CLI interruption, on-disk resume, and corruption/config rejection, in owned temp storage.
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'unit-step-contradiction-test-'));
try {
  const args = [probePath, '--alphabet', '4', '--target', '512', '--seconds', '1',
    '--state-dir', temporary];
  const termination = await new Promise((resolve, reject) => {
    const child = spawn(process.execPath, args, { stdio: ['ignore', 'pipe', 'pipe'] });
    const timeout = setTimeout(() => { child.kill('SIGKILL'); reject(new Error('interrupt test timed out')); }, 10000);
    let log = '', signaled = false;
    child.stderr.on('data', data => {
      log += data;
      if (!signaled && log.includes('"event":"start"')) { signaled = true; child.kill('SIGTERM'); }
    });
    child.on('error', error => { clearTimeout(timeout); reject(error); });
    child.on('exit', (code, signal) => { clearTimeout(timeout); resolve({ code, signal, log }); });
  });
  assert.equal(termination.signal, null);
  assert.equal(termination.code, 130);
  assert(termination.log.includes('"event":"interrupted"'));
  const checkpoint = path.join(temporary, 'state.json');
  const interrupted = JSON.parse(fs.readFileSync(checkpoint, 'utf8'));
  assert.equal(interrupted.state.status, 'running');
  validateState(interrupted.state, 4, 512);
  execFileSync(process.execPath, [...args, '--attempts', '1'], { stdio: 'pipe' });
  const resumedText = fs.readFileSync(checkpoint, 'utf8');
  const resumed = JSON.parse(resumedText);
  assert.equal(resumed.state.attempted, interrupted.state.attempted + 1);
  validateState(resumed.state, 4, 512);
  const corrupt = { ...resumed, checksum: '0'.repeat(64) };
  fs.writeFileSync(checkpoint, JSON.stringify(corrupt));
  assert.throws(() => execFileSync(process.execPath, args, { stdio: 'pipe' }), /corrupt checkpoint checksum/);
  fs.writeFileSync(checkpoint, resumedText);
  assert.throws(() => execFileSync(process.execPath, [...args, '--alphabet', '5'], { stdio: 'pipe' }), /incompatible checkpoint/);
} finally {
  fs.rmSync(temporary, { recursive: true, force: true });
}
console.log('PASS: 6,561 ternary words; complete small trees; every ternary DFS resume boundary;\n'
  + 'unequal-length witness; periodic local countermodel; exact incidence/deviation identities;\n'
  + '4D search replay and 349,504 BigInt rank tests; SIGTERM/resume/corrupt/config CLI checks.\n'
  + 'No 4D/5D impossibility or infinite construction is certified by these checks.');
