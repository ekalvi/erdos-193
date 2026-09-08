#!/usr/bin/env node
/** Exact fixed-ratio ancestor closure, NOT an all-ratios avoidance proof.
 * One JS computational thread. Atomic identity/hash-checked checkpoints resume
 * after interruption; only the unfinished batch is repeated. See README.md.
 */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { setImmediate as yieldNow } from 'node:timers/promises';

const IMAGE = [...'01213101314310'].map(Number);
const COUNTS = [3, 6, 1, 3, 1];
const M = Array.from({ length: 5 }, (_, i) => COUNTS.map((_, j) => COUNTS[(i - j + 5) % 5]));
const FIRST = [227, 1025, -305, -53, -473];
const ADJ = FIRST.map((_, i) => FIRST.map((_, j) => FIRST[(j - i + 5) % 5]));
const DET = 5894;
const POWERS = [1, 279, 377, 354, 252]; // Independently checked below.
const mod = (x, n) => ((x % n) + n) % n;
const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
const sum = a => a.reduce((s, x) => s + x, 0);
const hash = x => crypto.createHash('sha256').update(x).digest('hex');
const digest = x => hash(JSON.stringify(x));
const key = s => [...s.letters, ...s.strict, ...s.defect].join(',');
const gcd = (a, b) => b ? gcd(b, a % b) : a;
const atomic = (name, data) => {
  fs.mkdirSync(path.dirname(name), { recursive: true });
  const temp = `${name}.tmp-${process.pid}`;
  fs.writeFileSync(temp, `${JSON.stringify(data, null, 2)}\n`);
  fs.renameSync(temp, name);
};

function options() {
  const args = process.argv.slice(2);
  if (args.includes('--help')) {
    console.log(`Usage: node boundary.mjs --p P --q Q [--state-dir DIR] [--output FILE]
  [--max-seconds 60] [--max-states 100000]
P:Q is the reduced LEFT:RIGHT length ratio (positive coprime integers,
P+Q <= 1000000 for safe exact Number arithmetic). Defaults to 1:1.
The finite closure decides this ONE ratio at ALL scales, not all ratios.
Limits stop safely with exit 2 and no new final artifact; raise them to resume.
SIGINT/SIGTERM checkpoint between states and exit 130. Completed compatible
work is reused. Incompatible/corrupt checkpoints are rejected. Logs and state
are separate from final certificates. Use one computational core.`);
    process.exit(0);
  }
  const result = { p: 1, q: 1, maxSeconds: 60, maxStates: 100000 };
  const names = { '--p': 'p', '--q': 'q', '--state-dir': 'stateDir', '--output': 'output',
    '--max-seconds': 'maxSeconds', '--max-states': 'maxStates' };
  for (let i = 0; i < args.length; i += 2) {
    assert(names[args[i]] && args[i + 1] && !args[i + 1].startsWith('--'), 'unknown/missing option');
    const name = names[args[i]];
    result[name] = ['stateDir', 'output'].includes(name) ? args[i + 1] : Number(args[i + 1]);
  }
  for (const name of ['p', 'q', 'maxStates']) assert(Number.isSafeInteger(result[name]) && result[name] > 0);
  assert(Number.isFinite(result.maxSeconds) && result.maxSeconds > 0);
  assert(gcd(result.p, result.q) === 1 && result.p + result.q <= 1000000, 'invalid/too large reduced ratio');
  result.stateDir ??= `.checkpoint-shallit-boundary-${result.p}-${result.q}`;
  result.output ??= `research/unit-step/tracks/shallit-five/checks/ratio-${result.p}-${result.q}.json`;
  return result;
}

function prefixTables() {
  const byChild = Array.from({ length: 5 }, () => []);
  for (let r = 0; r < 5; r++) {
    const counts = [0, 0, 0, 0, 0];
    for (let t = 0; t < 14; t++) {
      const child = (r + IMAGE[t]) % 5;
      byChild[child].push({ r, t, counts: [...counts], residue: mod(dot(POWERS, counts), 421) });
      counts[child]++;
    }
  }
  return byChild;
}

function orderChoices(strict, a, b) {
  if (!strict) return a.t === b.t && a.r === b.r ? [0] : [];
  return a.t < b.t && a.r === b.r ? [1, 0] : [1];
}

function prefix(n) {
  let counts = [0n, 0n, 0n, 0n, 0n], letter = 0;
  const digits = [];
  while (n) { digits.push(Number(n % 14n)); n /= 14n; }
  for (const t of digits.reverse()) {
    counts = M.map(row => row.reduce((s, x, i) => s + BigInt(x) * counts[i], 0n));
    for (let j = 0; j < t; j++) counts[(letter + IMAGE[j]) % 5]++;
    letter = (letter + IMAGE[t]) % 5;
  }
  return counts;
}

function witness(nodes, id, p, q) {
  // All five letters occur in h(0); realize the equal-index terminal there.
  const n = BigInt(IMAGE.indexOf(nodes[id].letters[0]));
  let indices = [n, n, n];
  while (nodes[id].from !== null) {
    indices = indices.map((x, i) => 14n * x + BigInt(nodes[id].offsets[i]));
    id = nodes[id].from;
  }
  const [a, b, c] = indices;
  assert(a < b && b < c);
  const points = indices.map(prefix);
  const left = points[1].map((x, i) => x - points[0][i]);
  const right = points[2].map((x, i) => x - points[1][i]);
  assert(left.every((x, i) => BigInt(q) * x === BigInt(p) * right[i]));
  return { indices: indices.map(String), left_counts: left.map(String), right_counts: right.map(String) };
}

async function main() {
  const o = options(), { p, q } = o, s = p + q;
  assert.deepEqual(POWERS, Array.from({ length: 5 }, (_, i) => Number(279n ** BigInt(i) % 421n)));
  assert.deepEqual(M.map(row => ADJ[0].map((_, j) => dot(row, ADJ.map(r => r[j])))),
    M.map((row, i) => row.map((_, j) => i === j ? DET : 0)));
  const identity = { schema: 1, image0: IMAGE.join(''), p, q,
    code_sha256: hash(fs.readFileSync(fileURLToPath(import.meta.url))) };
  fs.mkdirSync(o.stateDir, { recursive: true });
  const checkpoint = path.join(o.stateDir, 'state.json'), logFile = path.join(o.stateDir, 'run.jsonl');
  const started = performance.now();
  const log = (event, extra = {}) => {
    const row = { time: new Date().toISOString(), event, ...extra };
    fs.appendFileSync(logFile, `${JSON.stringify(row)}\n`);
    console.error(JSON.stringify(row));
  };
  let saved;
  const resuming = fs.existsSync(checkpoint);
  try {
    if (resuming) {
      const envelope = JSON.parse(fs.readFileSync(checkpoint, 'utf8'));
      assert.equal(envelope.sha256, digest(envelope.payload), 'corrupt checkpoint');
      saved = envelope.payload;
      assert.deepEqual(saved.identity, identity, 'incompatible checkpoint');
    } else {
      const nodes = [];
      for (let a = 0; a < 5; a++) for (let b = 0; b < 5; b++) for (let c = 0; c < 5; c++) {
        nodes.push({ letters: [a, b, c], strict: [1, 1], defect: [0, 0, 0, 0, 0], from: null });
      }
      saved = { identity, nodes, completed: 0, transitions: 0, terminal: null };
    }
    assert(Number.isInteger(saved.completed) && saved.completed >= 0 && saved.completed <= saved.nodes.length);
    const nodes = saved.nodes, seen = new Map(nodes.map((node, i) => [key(node), i]));
    assert.equal(seen.size, nodes.length, 'duplicate checkpoint states');
    const persist = () => atomic(checkpoint, { payload: saved, sha256: digest(saved) });
    let stopped = false, lastProgress = performance.now(), lastCompleted = saved.completed;
    for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => { stopped = true; });
    log(resuming ? 'resume' : 'start', { identity, threads: 1, completed: saved.completed,
      discovered: nodes.length, total: 'unknown until closure', checkpoint, limits: o,
      eta_seconds: null, reason: 'unknown reachable closure size' });
    const table = prefixTables();
    const last = table.map(rows => {
      const index = new Map();
      for (const row of rows) {
        const k = mod(p * row.t, 14) + 14 * mod(p * row.residue, 421);
        if (!index.has(k)) index.set(k, []);
        index.get(k).push(row);
      }
      return index;
    });
    while (saved.completed < nodes.length && saved.terminal === null) {
      await yieldNow(); // Deliver signals without abandoning a partially processed state.
      if (stopped || (performance.now() - started) / 1000 >= o.maxSeconds || nodes.length > o.maxStates) {
        persist();
        log(stopped ? 'interrupted' : 'bounded_stop', { completed: saved.completed, discovered: nodes.length,
          elapsed_seconds: (performance.now() - started) / 1000, checkpoint });
        return stopped ? 130 : 2;
      }
      const id = saved.completed, child = nodes[id];
      const d14 = mod(sum(child.defect), 14), d421 = mod(dot(POWERS, child.defect), 421);
      for (const a of table[child.letters[0]]) for (const b of table[child.letters[1]]) {
        const ab = orderChoices(child.strict[0], a, b);
        if (!ab.length) continue;
        const k = mod(d14 - q * a.t + s * b.t, 14)
          + 14 * mod(d421 - q * a.residue + s * b.residue, 421);
        for (const c of last[child.letters[2]].get(k) ?? []) {
          const bc = orderChoices(child.strict[1], b, c);
          if (!bc.length) continue;
          const v = child.defect.map((x, i) => x - q * a.counts[i] + s * b.counts[i] - p * c.counts[i]);
          const numerators = ADJ.map(row => dot(row, v));
          assert(numerators.every(x => Number.isSafeInteger(x) && x % DET === 0), 'incomplete lattice sieve');
          const defect = numerators.map(x => x / DET || 0);
          assert(defect.every(x => Math.abs(x) * 3811 <= 6735 * s), 'defect radius violated');
          assert(Math.abs(sum(defect)) < s, 'length defect violated');
          for (const x of ab) for (const y of bc) {
            // Equality of all three parent indices forces zero defect.
            if (!x && !y && defect.some(z => z !== 0)) continue;
            const parent = { letters: [a.r, b.r, c.r], strict: [x, y], defect,
              from: id, offsets: [a.t, b.t, c.t] };
            const stateKey = key(parent);
            let parentId = seen.get(stateKey);
            if (parentId === undefined) {
              parentId = nodes.length;
              seen.set(stateKey, parentId);
              nodes.push(parent);
            }
            saved.transitions++;
            if (!x && !y) saved.terminal = parentId;
          }
        }
      }
      saved.completed++;
      if (performance.now() - lastProgress >= 2000) {
        persist();
        const now = performance.now();
        log('progress', { completed: saved.completed, discovered: nodes.length, total: 'unknown until closure',
          states_per_second: (saved.completed - lastCompleted) * 1000 / (now - lastProgress),
          elapsed_seconds: (now - started) / 1000, eta_seconds: null, checkpoint,
          rss_bytes: process.memoryUsage().rss });
        lastProgress = now; lastCompleted = saved.completed;
      }
    }
    persist();
    const output = saved.terminal === null
      ? { identity, status: 'fixed_ratio_avoidance_certificate',
        scope: `Infinite avoidance at the single reduced length ratio ${p}:${q}; NOT all ratios.`,
        transitions: saved.transitions,
        states: nodes.map(({ letters, strict, defect }) => ({ letters, strict, defect })) }
      : { identity, status: 'counterexample', ...witness(nodes, saved.terminal, p, q) };
    atomic(o.output, output);
    log('complete', { status: output.status, states: nodes.length, transitions: saved.transitions,
      elapsed_seconds: (performance.now() - started) / 1000, output: o.output, checkpoint });
    return saved.terminal === null ? 0 : 1;
  } catch (error) {
    log('error', { message: error.message, checkpoint, elapsed_seconds: (performance.now() - started) / 1000 });
    throw error;
  }
}
process.exitCode = await main();
