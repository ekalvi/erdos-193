#!/usr/bin/env node
// Bounded exact extension tree, not an infinite existence test. One JS worker.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const sha = text => createHash('sha256').update(text).digest('hex');
const sourcePath = fileURLToPath(import.meta.url);
const gcd = (a, b) => { while (b) [a, b] = [b, a % b]; return a; };

export function points(word, alphabet) {
  const p = [Array(alphabet).fill(0)];
  for (const a of word) { const q = p.at(-1).slice(); q[a]++; p.push(q); }
  return p;
}

// For a previously valid prefix, every new triple ends at its new endpoint.
// Two chords ending there are parallel iff their primitive integer vectors agree.
export function endingTriple(p) {
  const k = p.length - 1, seen = new Map();
  for (let i = k - 1; i >= 0; i--) {
    const v = p[k].map((x, r) => x - p[i][r]);
    const g = v.reduce(gcd, 0), key = v.map(x => x / g).join(',');
    if (seen.has(key)) return [i, seen.get(key), k];
    seen.set(key, i);
  }
  return null;
}

// Independent direct cross-product check, including unequal adjacent lengths.
export function directTriple(word, alphabet, ordinaryOnly = false) {
  const p = points(word, alphabet);
  for (let k = 2; k < p.length; k++) for (let j = 1; j < k; j++) {
    for (let i = 0; i < j; i++) {
      if (ordinaryOnly && j - i !== k - j) continue;
      if (p[0].every((_, r) => (k - j) * (p[j][r] - p[i][r])
        === (j - i) * (p[k][r] - p[j][r]))) return [i, j, k];
    }
  }
  return null;
}

export function initialState() {
  return { word: [], next: [0], attempted: 0, acceptedByDepth: [1],
    rejectedByDepth: [0], bestWord: [], status: 'running' };
}

export function advance(state, p, alphabet, target) {
  while (state.status === 'running') {
    const depth = state.word.length;
    // Canonical restricted-growth words quotient only by global letter renaming.
    const choices = Math.min(alphabet, 2 + Math.max(-1, ...state.word));
    if (state.next[depth] === choices) {
      if (!depth) { state.status = 'exhausted'; return; }
      state.word.pop(); state.next.pop(); p.pop(); continue;
    }
    const a = state.next[depth]++;
    state.attempted++;
    while (state.rejectedByDepth.length <= depth + 1) state.rejectedByDepth.push(0);
    const q = p.at(-1).slice(); q[a]++; p.push(q);
    if (endingTriple(p)) {
      p.pop();
      state.rejectedByDepth[depth + 1] = (state.rejectedByDepth[depth + 1] ?? 0) + 1;
    } else {
      state.word.push(a); state.next.push(0);
      state.acceptedByDepth[depth + 1] = (state.acceptedByDepth[depth + 1] ?? 0) + 1;
      if (state.word.length > state.bestWord.length) state.bestWord = state.word.slice();
      if (state.word.length === target) state.status = 'witness';
    }
    return;
  }
}

export function validateState(state, alphabet, target) {
  assert(['running', 'witness', 'exhausted'].includes(state.status));
  for (const word of [state.word, state.bestWord]) {
    assert(Array.isArray(word) && word.length <= target);
    let maximum = -1;
    for (const a of word) {
      assert(Number.isInteger(a) && a >= 0 && a < alphabet && a <= maximum + 1);
      maximum = Math.max(maximum, a);
    }
    assert.equal(directTriple(word, alphabet), null);
  }
  assert.equal(state.next.length, state.word.length + 1);
  for (let depth = 0; depth < state.next.length; depth++) {
    const choices = Math.min(alphabet, 2 + Math.max(-1, ...state.word.slice(0, depth)));
    assert(Number.isInteger(state.next[depth]) && state.next[depth] >= 0 && state.next[depth] <= choices);
    if (depth < state.word.length) assert.equal(state.next[depth], state.word[depth] + 1);
  }
  assert(Number.isSafeInteger(state.attempted) && state.attempted >= 0);
  for (const counts of [state.acceptedByDepth, state.rejectedByDepth]) {
    assert(Array.isArray(counts) && counts.every(x => Number.isSafeInteger(x) && x >= 0));
  }
  assert.equal(state.acceptedByDepth[0], 1);
  assert.equal(state.rejectedByDepth[0], 0);
  assert.equal(state.attempted, state.acceptedByDepth.reduce((a, b) => a + b, 0) - 1
    + state.rejectedByDepth.reduce((a, b) => a + b, 0));
  assert.equal(state.bestWord.length, state.acceptedByDepth.length - 1);
  assert(state.word.length <= state.bestWord.length);
  if (state.status === 'witness') assert.equal(state.word.length, target);
  else assert(state.bestWord.length < target);
  if (state.status === 'exhausted') {
    assert.equal(state.word.length, 0); assert.deepEqual(state.next, [1]);
  }
}

function durableWrite(filename, value, append = false) {
  fs.mkdirSync(path.dirname(filename), { recursive: true });
  const destination = append ? filename : `${filename}.tmp-${process.pid}`;
  const fd = fs.openSync(destination, append ? 'a' : 'w', 0o600);
  try { fs.writeFileSync(fd, value); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
  if (!append) fs.renameSync(destination, filename);
}

async function main() {
  const { values } = parseArgs({ options: {
    alphabet: { type: 'string', default: '4' }, target: { type: 'string', default: '128' },
    seconds: { type: 'string', default: '60' }, attempts: { type: 'string', default: '1000000' },
    'state-dir': { type: 'string', default: '.checkpoint-unit-step-contradiction-4d' },
    output: { type: 'string' }, help: { type: 'boolean', short: 'h' },
  } });
  if (values.help) {
    console.log('Bounded exact canonical extension-tree search (one JS worker).\n'
      + '--alphabet 1..8 --target 2..512 --seconds 1..600 --attempts 1..1000000000\n'
      + '--state-dir DIR --output FILE (optional finite result, separate from checkpoints)\n'
      + 'Repeating compatible commands resumes the DFS stack without revisiting completed branches.\n'
      + 'Per-invocation time/attempt budgets may change; code/alphabet/target may not.\n'
      + 'Atomic identity/checksum-validated checkpoints and timestamped JSONL logs every five seconds.\n'
      + 'SIGINT/SIGTERM checkpoint at the next event-loop yield (every 1024 attempts).\n'
      + 'Only EXHAUSTED proves impossibility; a target witness or budget limit does not.');
    return;
  }
  const alphabet = Number(values.alphabet), target = Number(values.target);
  const seconds = Number(values.seconds), attempts = Number(values.attempts);
  for (const [x, lo, hi] of [[alphabet, 1, 8], [target, 2, 512], [seconds, 1, 600], [attempts, 1, 1e9]])
    assert(Number.isInteger(x) && x >= lo && x <= hi, 'invalid bounded parameter');
  const codeSha256 = sha(fs.readFileSync(sourcePath));
  const identity = { schema: 1, codeSha256, alphabet, target };
  const checkpoint = path.resolve(values['state-dir'], 'state.json');
  const log = path.resolve(values['state-dir'], 'run.jsonl');
  if (values.output) assert(![checkpoint, log].includes(path.resolve(values.output)), 'output must be separate');
  const event = (type, fields = {}) => {
    const line = JSON.stringify({ timestamp: new Date().toISOString(), event: type, ...fields }) + '\n';
    durableWrite(log, line, true); process.stderr.write(line);
  };
  let state = initialState();
  try {
    const resumed = fs.existsSync(checkpoint);
    if (resumed) {
      const saved = JSON.parse(fs.readFileSync(checkpoint, 'utf8'));
      assert.deepEqual(saved.identity, identity, 'incompatible checkpoint; use another state directory');
      assert.equal(saved.checksum, sha(JSON.stringify(saved.state)), 'corrupt checkpoint checksum');
      state = saved.state; validateState(state, alphabet, target);
    }
    const save = () => durableWrite(checkpoint, JSON.stringify({ identity,
      checksum: sha(JSON.stringify(state)), state }) + '\n');
    let stopped = false;
    process.on('SIGINT', () => { stopped = true; });
    process.on('SIGTERM', () => { stopped = true; });
    const start = performance.now(), initialAttempts = state.attempted;
    let lastLog = start;
    const p = points(state.word, alphabet);
    const progress = () => {
      const elapsedSeconds = (performance.now() - start) / 1000;
      return { completedAttempts: state.attempted, invocationAttempts: state.attempted - initialAttempts,
        attemptBudget: attempts, elapsedSeconds, attemptsPerSecond: (state.attempted - initialAttempts) / Math.max(.001, elapsedSeconds),
        remainingTimeBudgetSeconds: Math.max(0, seconds - elapsedSeconds), exhaustionEta: null,
        totalTreeSize: 'unknown', deepest: state.bestWord.length, target, checkpoint,
        rssBytes: process.memoryUsage().rss };
    };
    event(resumed ? 'resume' : 'start', { ...identity, ...progress(), seconds, workers: 1,
      resume: 'validated stack; completed branches are not repeated' });
    save();
    while (state.status === 'running' && !stopped && state.attempted - initialAttempts < attempts
      && performance.now() - start < seconds * 1000) {
      advance(state, p, alphabet, target);
      if ((state.attempted - initialAttempts) % 1024 === 0) await new Promise(resolve => setImmediate(resolve));
      if (performance.now() - lastLog >= 5000) {
        save(); event('progress', progress()); lastLog = performance.now();
      }
    }
    save();
    const outcome = state.status === 'running' ? (stopped ? 'interrupted' : 'budget_reached') : state.status;
    assert.equal(directTriple(state.bestWord, alphabet), null);
    const result = { ...identity, outcome, attempted: state.attempted,
      acceptedByDepth: state.acceptedByDepth, rejectedByDepth: state.rejectedByDepth,
      countsScope: state.status === 'exhausted' ? 'complete canonical tree' : 'partial DFS traversal only',
      bestWord: state.bestWord.join(''), bestSteps: state.bestWord.length,
      bestWordVerifiedBy: 'independent exact cross-products, all i<j<k',
      provesImpossibility: state.status === 'exhausted',
      provesInfiniteExistence: false };
    if (values.output) durableWrite(values.output, JSON.stringify(result, null, 2) + '\n');
    event(outcome, { ...progress(), result: values.output ?? null, provesImpossibility: result.provesImpossibility });
    if (stopped) process.exitCode = 130;
  } catch (error) {
    event('error', { message: error.message, checkpoint }); throw error;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === sourcePath) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
