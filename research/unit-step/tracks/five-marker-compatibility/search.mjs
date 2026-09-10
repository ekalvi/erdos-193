#!/usr/bin/env node
// Bounded, resumable discovery only. verify.mjs independently checks the witness.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { setImmediate as yieldNow } from 'node:timers/promises';

const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log(`Usage: node --single-threaded search.mjs [--state-dir DIR] [--budget-ms N]
Search canonical five-letter words with three occurrences per letter, rejecting
ALL weak abelian squares (arbitrary adjacent lengths). Stop at the first word
whose ten marker pairs each return at fraction 1/3 or 2/3 within the SAME outer
interval. This is a finite counterexample search, not an infinite construction.
Atomic checkpoints validate source/config identity and a SHA-256 checksum.
Resume preserves the DFS cursor; SIGINT/SIGTERM flush at a 256-iteration boundary.
Budget is per invocation, not part of the compatible search configuration.`);
  process.exit(0);
}
let stateDir = '.checkpoint-five-marker-search', budgetMs = 60_000;
for (let i = 0; i < args.length; i += 2) {
  assert(i + 1 < args.length, 'missing argument');
  if (args[i] === '--state-dir') stateDir = args[i + 1];
  else if (args[i] === '--budget-ms') budgetMs = Number(args[i + 1]);
  else throw Error(`unknown argument ${args[i]}`);
}
assert(Number.isSafeInteger(budgetMs) && budgetMs >= 0);
fs.mkdirSync(stateDir, { recursive: true });
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
const identity = { schema: 1, sourceSha256: sha(fs.readFileSync(fileURLToPath(import.meta.url))),
  alphabet: 5, counts: [3, 3, 3, 3, 3], canonical: true, predicate: 'all-pair-interior-returns' };
const checkpoint = path.join(stateDir, 'state.json'), logPath = path.join(stateDir, 'run.jsonl');
function atomic(file, value) {
  const tmp = `${file}.tmp`; fs.writeFileSync(tmp, JSON.stringify(value, null, 2) + '\n'); fs.renameSync(tmp, file);
}
function log(event, extra = {}) {
  const row = { utc: new Date().toISOString(), event, ...extra };
  fs.appendFileSync(logPath, JSON.stringify(row) + '\n'); console.log(JSON.stringify(row));
}
let state = { identity, word: [], next: [0], attempts: 0, leaves: 0, elapsedMs: 0, status: 'running', witness: null };
const resumed = fs.existsSync(checkpoint);
if (resumed) {
  const saved = JSON.parse(fs.readFileSync(checkpoint));
  assert.equal(saved.sha256, sha(JSON.stringify(saved.payload)), 'corrupt checkpoint checksum');
  assert.deepEqual(saved.payload.identity, identity, 'incompatible checkpoint; use a fresh directory');
  state = saved.payload;
  assert(['running', 'found', 'exhausted'].includes(state.status));
  assert(Array.isArray(state.word) && state.word.length <= 15);
  assert.equal(state.next.length, state.word.length + 1);
  assert(state.word.every(a => Number.isInteger(a) && a >= 0 && a < 5));
  assert(state.next.every(a => Number.isInteger(a) && a >= 0 && a <= 5));
  assert(Number.isSafeInteger(state.attempts) && state.attempts >= 0);
  assert(Number.isSafeInteger(state.leaves) && state.leaves >= 0);
  assert(Number.isFinite(state.elapsedMs) && state.elapsedMs >= 0);
}
const pairs = []; for (let a = 0; a < 5; a++) for (let b = a + 1; b < 5; b++) pairs.push([a, b]);
function prefixes(word) {
  const p = [Array(5).fill(0)];
  for (const a of word) { const next = [...p.at(-1)]; next[a]++; p.push(next); }
  return p;
}
function newSquare(word) {
  const p = prefixes(word), k = word.length;
  for (let j = 1; j < k; j++) for (let i = 0; i < j; i++) {
    if (p[k].every((v, r) => (k - j) * (p[j][r] - p[i][r]) === (j - i) * (v - p[j][r]))) return [i, j, k];
  }
  return null;
}
function pairLevels(word) {
  const p = prefixes(word);
  return pairs.map(([a, b]) => ({ pair: [a, b], levels: [1, 2].filter(r => p.some(row => row[a] === r && row[b] === r)) }));
}
// Validate the saved valid path; at most 15 tiny finite prefixes.
for (let n = 1; n <= state.word.length; n++) {
  assert.equal(newSquare(state.word.slice(0, n)), null, 'invalid saved avoiding prefix');
  assert(state.word[n - 1] <= 1 + Math.max(-1, ...state.word.slice(0, n - 1)), 'noncanonical saved prefix');
}
assert(prefixes(state.word).at(-1).every(n => n <= 3));
if (state.status === 'found') {
  assert.equal(state.word.length, 15);
  assert.deepEqual(state.witness, { word: state.word.join(''), counts: [3, 3, 3, 3, 3], pairs: pairLevels(state.word) });
  assert(state.witness.pairs.every(row => row.levels.length > 0));
}
let signal = null;
process.on('SIGINT', () => { signal = 'SIGINT'; });
process.on('SIGTERM', () => { signal = 'SIGTERM'; });
const started = Date.now(), initialAttempts = state.attempts, initialElapsed = state.elapsedMs;
function save() {
  state.elapsedMs = initialElapsed + Date.now() - started;
  atomic(checkpoint, { payload: state, sha256: sha(JSON.stringify(state)) });
}
function summary() {
  const ms = Date.now() - started, rate = ms ? (state.attempts - initialAttempts) * 1000 / ms : 0;
  return { status: state.status, attempts: state.attempts, leaves: state.leaves, depth: state.word.length,
    completedTargets: state.status === 'running' ? 0 : 1, totalTargets: 1,
    attemptsPerSecond: rate, elapsedMs: initialElapsed + ms,
    eta: state.status === 'running' ? 'unknown search-to-first-witness; bounded by invocation budget' : 'complete',
    budgetRemainingMs: Math.max(0, budgetMs - ms), checkpoint };
}
log(resumed ? 'resume' : 'start', { identity, budgetMs, state: summary(),
  resources: { workerThreads: 0, affinity: fs.readFileSync('/proc/self/status', 'utf8').match(/^Cpus_allowed_list:\s*(.*)$/m)?.[1],
    OMP_NUM_THREADS: process.env.OMP_NUM_THREADS, OPENBLAS_NUM_THREADS: process.env.OPENBLAS_NUM_THREADS,
    MKL_NUM_THREADS: process.env.MKL_NUM_THREADS, NUMEXPR_NUM_THREADS: process.env.NUMEXPR_NUM_THREADS,
    UV_THREADPOOL_SIZE: process.env.UV_THREADPOOL_SIZE } });
let lastLog = started;
try {
  while (state.status === 'running' && !signal && Date.now() - started < budgetMs) {
    for (let batch = 0; batch < 256 && state.status === 'running'; batch++) {
      const depth = state.word.length;
      if (depth === 15) {
        state.leaves++;
        const rows = pairLevels(state.word);
        if (rows.every(row => row.levels.length > 0)) {
          state.status = 'found'; state.witness = { word: state.word.join(''), counts: [3, 3, 3, 3, 3], pairs: rows }; break;
        }
        state.word.pop(); state.next.pop(); continue;
      }
      if (state.next[depth] === 5) {
        if (depth === 0) { state.status = 'exhausted'; break; }
        state.word.pop(); state.next.pop(); continue;
      }
      const a = state.next[depth]++; state.attempts++;
      if (a > 1 + Math.max(-1, ...state.word)) continue;
      if (state.word.filter(b => b === a).length === 3) continue;
      const candidate = [...state.word, a];
      if (newSquare(candidate)) continue;
      state.word.push(a); state.next.push(0);
    }
    save();
    if (Date.now() - lastLog >= 5000) { log('progress', summary()); lastLog = Date.now(); }
    await yieldNow();
  }
  save();
  if (state.status === 'found') atomic(path.join(stateDir, 'result.json'), { identity, ...state.witness });
  log(signal ? 'interrupted' : state.status === 'running' ? 'budget-stop' : 'complete', { ...summary(), signal, witness: state.witness });
  if (signal) process.exitCode = signal === 'SIGINT' ? 130 : 143;
} catch (error) {
  save(); log('error', { ...summary(), message: error.stack }); process.exitCode = 1;
}
