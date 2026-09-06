#!/usr/bin/env node
/** Independent exact certificate validator: no producer import or residue sieve.
 * Enumerates all 14^3 offsets and uses integer cofactors. Each small certificate
 * is an atomic resumable task. SIGINT/SIGTERM finish that task before stopping.
 */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { setImmediate as yieldNow } from 'node:timers/promises';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const IMAGE = [...'01213101314310'].map(Number);
const mod = (a, b) => ((a % b) + b) % b;
const dot = (a, b) => a.reduce((s, x, j) => s + x * b[j], 0);
const sum = v => v.reduce((a, b) => a + b, 0);
const digest = value => crypto.createHash('sha256').update(value).digest('hex');
const checksum = value => digest(JSON.stringify(value));
const stateKey = v => JSON.stringify([v.letters, v.strict, v.defect]);
const gcd = (a, b) => b ? gcd(b, a % b) : a;
const determinant = a => a.length === 1 ? a[0][0] : a[0].reduce((s, x, j) =>
  s + (-1) ** j * x * determinant(a.slice(1).map(row => row.filter((_, k) => k !== j))), 0);
const matrix = Array.from({ length: 5 }, (_, i) => Array.from({ length: 5 }, (_, j) =>
  IMAGE.filter(x => (x + j) % 5 === i).length));
const det = determinant(matrix);
const adj = matrix.map((row, i) => row.map((_, j) => (-1) ** (i + j)
  * determinant(matrix.filter((_, r) => r !== j).map(row => row.filter((_, c) => c !== i)))));
const prefixes = Array.from({ length: 5 }, (_, r) => Array.from({ length: 14 }, (_, t) =>
  Array.from({ length: 5 }, (_, j) => IMAGE.slice(0, t).filter(x => (r + x) % 5 === j).length)));
const atomic = (name, data) => {
  fs.mkdirSync(path.dirname(name), { recursive: true });
  const temp = `${name}.tmp-${process.pid}`;
  fs.writeFileSync(temp, `${JSON.stringify(data, null, 2)}\n`);
  fs.renameSync(temp, name);
};

export function checkAlgebra() {
  assert.equal(det, 5894);
  assert.deepEqual(adj[0], [227, 1025, -305, -53, -473]);
  for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) {
    assert.equal(dot(matrix[i], adj.map(row => row[j])), i === j ? det : 0);
  }
  const powers = Array.from({ length: 5 }, (_, i) => Number(279n ** BigInt(i) % 421n));
  assert.equal(Number(279n ** 5n % 421n), 1);
  for (let j = 0; j < 5; j++) {
    assert.equal(mod(dot(powers, matrix.map(row => row[j])), 421), 0);
    assert.equal(sum(matrix.map(row => row[j])), 14);
  }
  assert.equal(gcd(421, powers[1] - powers[0]), 1); // Quotient map is onto.
  for (const row of adj) {
    assert.equal(sum(row.map(Math.abs)), 2083);
    const values = prefixes.flat().map(b => dot(row, b));
    assert.equal(Math.min(...values), -1068);
    assert.equal(Math.max(...values), 5667);
    assert.equal(Math.max(...values) - Math.min(...values), 6735);
  }
  assert.equal(det - 2083, 3811);
  assert.equal(dot(adj[0], prefixes[2][8]), -1068);
  assert.equal(dot(adj[0], prefixes[0][13]), 5667);
  // Polynomial identity for the unbounded one-step family in README §6:
  // B(0,1)+B(0,13)=M e_0, so q=p+det gives D'=-p e_0-adj(M)e_0.
  assert.deepEqual(prefixes[0][1], [1, 0, 0, 0, 0]);
  assert.deepEqual(prefixes[0][0], [0, 0, 0, 0, 0]);
  assert.deepEqual(prefixes[0][1].map((x, j) => x + prefixes[0][13][j]), matrix.map(row => row[0]));
  assert.deepEqual(adj.map(row => row[0]), [227, -473, -53, -305, 1025]);
  // Check the prefix recurrence independently on a SMALL exact word, not as
  // evidence of infinite avoidance. Include boundary equality and all residues.
  const word = IMAGE.flatMap(r => IMAGE.map(x => (x + r) % 5));
  const F = [[0, 0, 0, 0, 0]];
  for (const r of word) { const v = [...F.at(-1)]; v[r]++; F.push(v); }
  for (let n = 0; n < 14; n++) for (let t = 0; t < 14; t++) {
    assert.deepEqual(F[14 * n + t], matrix.map((row, j) => dot(row, F[n]) + prefixes[word[n]][t][j]));
  }
  return { determinant: det, inverse_row_norm: '2083/5894', forcing_width: '6735/5894',
    normalized_defect_radius: '6735/3811', prefix_identity_cases: 196 };
}

function permitted(childStrict, parentStrict, x, y, rx, ry) {
  if (parentStrict) return childStrict === 1;
  return rx === ry && x <= y && childStrict === Number(x < y);
}

export async function verifyCertificate(data, onProgress = () => {}) {
  const { p, q } = data.identity ?? {}, s = p + q;
  assert(Number.isSafeInteger(p) && Number.isSafeInteger(q) && p > 0 && q > 0
    && s <= 1000000 && gcd(p, q) === 1, 'invalid ratio');
  assert.equal(data.identity.schema, 1);
  assert.equal(data.identity.image0, IMAGE.join(''));
  assert.equal(data.status, 'fixed_ratio_avoidance_certificate');
  assert(Array.isArray(data.states) && data.states.length >= 125);
  const states = new Map();
  for (const v of data.states) {
    assert(Array.isArray(v.letters) && v.letters.length === 3
      && v.letters.every(x => Number.isInteger(x) && x >= 0 && x < 5));
    assert(Array.isArray(v.strict) && v.strict.length === 2 && v.strict.every(x => x === 0 || x === 1));
    assert(Array.isArray(v.defect) && v.defect.length === 5 && v.defect.every(x => Number.isSafeInteger(x)
      && Math.abs(x) * 3811 <= 6735 * s));
    assert(Math.abs(sum(v.defect)) < s);
    for (let i = 0; i < 2; i++) if (!v.strict[i]) assert.equal(v.letters[i], v.letters[i + 1]);
    assert(v.strict.some(Boolean), 'accepting or impossible equal-index state in avoidance certificate');
    const k = stateKey(v);
    assert(!states.has(k), 'duplicate state');
    states.set(k, v);
  }
  for (let a = 0; a < 5; a++) for (let b = 0; b < 5; b++) for (let c = 0; c < 5; c++) {
    assert(states.has(stateKey({ letters: [a, b, c], strict: [1, 1], defect: [0, 0, 0, 0, 0] })), 'missing root');
  }
  let transitions = 0, completed = 0;
  for (const child of states.values()) {
    // Unlike the producer: direct full offset enumeration, no 14/421 filtering.
    for (let x = 0; x < 14; x++) for (let y = 0; y < 14; y++) for (let z = 0; z < 14; z++) {
      const letters = [x, y, z].map((t, j) => mod(child.letters[j] - IMAGE[t], 5));
      const bs = [x, y, z].map((t, j) => prefixes[letters[j]][t]);
      const rhs = child.defect.map((d, j) => d - q * bs[0][j] + s * bs[1][j] - p * bs[2][j]);
      const numerators = adj.map(row => dot(row, rhs));
      assert(numerators.every(Number.isSafeInteger));
      if (numerators.some(n => n % det)) continue;
      const defect = numerators.map(n => n / det || 0);
      for (const ab of [0, 1]) for (const bc of [0, 1]) {
        if (!permitted(child.strict[0], ab, x, y, letters[0], letters[1])
          || !permitted(child.strict[1], bc, y, z, letters[1], letters[2])) continue;
        if (!ab && !bc && defect.some(Boolean)) continue; // Impossible actual parent.
        assert(ab || bc, 'reachable accepting state');
        const parent = { letters, strict: [ab, bc], defect };
        assert(states.has(stateKey(parent)), `not ancestor-closed: ${stateKey(child)} -> ${stateKey(parent)}`);
        transitions++;
      }
    }
    completed++;
    if (completed % 32 === 0) { onProgress(completed, states.size); await yieldNow(); }
  }
  assert.equal(data.transitions, transitions, 'incorrect transition count');
  return { ratio: [p, q], states: states.size, transitions };
}

export async function mutationTests(data) {
  const clone = () => structuredClone(data);
  const missing = clone(); missing.states.pop();
  const duplicate = clone(); duplicate.states.push(structuredClone(duplicate.states[0]));
  const altered = clone(); altered.states.at(-1).defect[0] += 100;
  const root = clone(); root.states.shift();
  const terminal = clone(); terminal.states.push({ letters: [0, 0, 0], strict: [0, 0], defect: [0, 0, 0, 0, 0] });
  const count = clone(); count.transitions++;
  for (const [name, bad] of Object.entries({ missing, duplicate, altered, root, terminal, count })) {
    await assert.rejects(() => verifyCertificate(bad), { name: 'AssertionError' }, `accepted ${name} mutation`);
  }
  return ['missing', 'duplicate', 'altered', 'root', 'terminal', 'count'];
}

async function main() {
  if (process.argv.includes('--help')) {
    console.log('Usage: node check.mjs [certificate.json ...]\nDefaults: all checks/ratio-*.json next to this script.\nOne core; atomic per-certificate checkpoints under .checkpoint-shallit-boundary-check-<identity>.\nCompleted validated work is reused; corrupt state is rejected. SIGINT/SIGTERM stop after the current small task.');
    return 0;
  }
  const files = process.argv.length > 2 ? process.argv.slice(2).map(x => path.resolve(x))
    : fs.readdirSync(path.join(HERE, 'checks')).filter(x => /^ratio-\d+-\d+\.json$/.test(x)).sort().map(x => path.join(HERE, 'checks', x));
  assert(files.length > 0);
  const sourceHash = digest(fs.readFileSync(path.join(HERE, 'boundary.mjs')));
  const identity = { schema: 1, code_sha256: digest(fs.readFileSync(fileURLToPath(import.meta.url))),
    producer_sha256: sourceHash, files: files.map(file => [path.relative(HERE, file), digest(fs.readFileSync(file))]) };
  const dir = `.checkpoint-shallit-boundary-check-${checksum(identity).slice(0, 16)}`;
  const checkpoint = path.join(dir, 'state.json'), logFile = path.join(dir, 'run.jsonl');
  fs.mkdirSync(dir, { recursive: true });
  const log = (event, extra = {}) => {
    const row = { time: new Date().toISOString(), event, ...extra };
    fs.appendFileSync(logFile, `${JSON.stringify(row)}\n`);
    console.log(JSON.stringify(row));
  };
  const started = performance.now();
  let state = { identity, completed: [] }, stopped = false;
  for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => { stopped = true; });
  try {
    if (fs.existsSync(checkpoint)) {
      const saved = JSON.parse(fs.readFileSync(checkpoint, 'utf8'));
      assert.equal(saved.sha256, checksum(saved.payload), 'corrupt checkpoint');
      state = saved.payload;
      assert.deepEqual(state.identity, identity, 'incompatible checkpoint');
    }
    const persist = () => atomic(checkpoint, { payload: state, sha256: checksum(state) });
    log(state.completed.length ? 'resume' : 'start', { identity, threads: 1,
      completed: state.completed.length, total: files.length + 1, checkpoint });
    if (!state.completed.includes('algebra')) {
      const result = checkAlgebra();
      state.completed.push('algebra'); persist(); log('algebra', result);
    }
    for (const file of files) {
      if (state.completed.includes(file)) continue;
      if (stopped) { log('interrupted', { checkpoint }); return 130; }
      const data = JSON.parse(fs.readFileSync(file, 'utf8'));
      assert.equal(data.identity.code_sha256, sourceHash, 'certificate producer identity differs');
      const namedRatio = /^ratio-(\d+)-(\d+)\.json$/.exec(path.basename(file));
      if (namedRatio) assert.deepEqual([data.identity.p, data.identity.q], namedRatio.slice(1).map(Number));
      const taskStarted = performance.now();
      let last = taskStarted;
      const result = await verifyCertificate(data, (completed, total) => {
        if (performance.now() - last > 2000) {
          const elapsed = (performance.now() - taskStarted) / 1000;
          log('progress', { file, completed, total, elapsed_seconds: elapsed,
            states_per_second: completed / elapsed, eta_seconds: (total - completed) * elapsed / completed, checkpoint });
          last = performance.now();
        }
      });
      // Mutations exercise closure, not just hashes or the producer's row count.
      const rejected_mutations = await mutationTests(data);
      state.completed.push(file); persist();
      log('certificate_valid', { file, ...result, rejected_mutations,
        elapsed_seconds: (performance.now() - started) / 1000,
        states_per_second: result.states * 1000 / (performance.now() - taskStarted), eta_seconds: 0, checkpoint });
      await yieldNow();
    }
    log('complete', { certificates: files.length, elapsed_seconds: (performance.now() - started) / 1000,
      scope: 'Exact finite closed-state certificates, implying only the specified fixed-ratio infinite theorems.' });
    return 0;
  } catch (error) {
    log('error', { message: error.message, checkpoint });
    throw error;
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exitCode = await main();
