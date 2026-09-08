#!/usr/bin/env node
/** Independent bounded integer/algebra checks for Track A, not an infinite proof.
 * No imports from the construction, previous audits, or saved mathematical results.
 * Single worker. Each bounded case is atomically checkpointed; see --help.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync, mkdirSync, readFileSync, renameSync, writeFileSync, appendFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const digest = data => createHash('sha256').update(data).digest('hex');
const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log(`Usage: node research/unit-step/tracks/check_six_step_audit.mjs [options]
  --write              Atomically write the tracked finite-check result (default: compare).
  --recompute          Explicitly replace prior progress, recomputing every case.
  --checkpoint PATH    Default: .checkpoint-six-step-audit/state.json (relative to repo).
  --log PATH           Default: .checkpoint-six-step-audit/run.jsonl (relative to repo).
  --stop-after N        Pause after N newly completed cases, for bounded runs/resume tests.
Resume validates code/source/config identity and a checkpoint checksum; incompatible or
corrupt progress is rejected. SIGINT/SIGTERM stop between bounded cases after saving.
One computational worker; no subprocesses, numerical libraries, or network. Logs include
UTC progress/ETA. All checks are finite diagnostics, not certification of infinity.`);
  process.exit(0);
}
const options = {write: false, recompute: false, checkpoint: '.checkpoint-six-step-audit/state.json',
  log: '.checkpoint-six-step-audit/run.jsonl', stopAfter: Infinity};
for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === '--write') options.write = true;
  else if (arg === '--recompute') options.recompute = true;
  else if (arg === '--checkpoint' || arg === '--log') {
    assert(args[i + 1] && !args[i + 1].startsWith('--'), `${arg} requires a path`);
    options[arg.slice(2)] = args[++i];
  } else if (arg === '--stop-after') {
    options.stopAfter = Number(args[++i]);
    assert(Number.isSafeInteger(options.stopAfter) && options.stopAfter > 0, 'positive case count required');
  } else assert.fail(`unknown option: ${arg}`);
}
const checkpoint = path.resolve(root, options.checkpoint);
const logPath = path.resolve(root, options.log);
const output = path.join(root, 'research/unit-step/checks/six-step-audit.json');
assert.equal(new Set([checkpoint, logPath, output]).size, 3, 'output, log, and checkpoint must differ');
const atomic = (file, value) => {
  mkdirSync(path.dirname(file), {recursive: true});
  const temporary = `${file}.tmp-${process.pid}`;
  writeFileSync(temporary, JSON.stringify(value, null, 2) + '\n');
  renameSync(temporary, file);
};
mkdirSync(path.dirname(logPath), {recursive: true});
const log = (event, fields = {}) => appendFileSync(logPath,
  JSON.stringify({timestamp: new Date().toISOString(), event, ...fields}) + '\n');
const reviewed = ['paper/unit_step_walk_N6_short.tex', 'paper/unit_step_walk_N6_short.pdf',
  'paper/erdos193.tex', 'design/SIGNED-GAUSSIAN-UNIT-STEP-OPTIMIZATION.md'];
const identity = {schema: 1, code_sha256: digest(readFileSync(fileURLToPath(import.meta.url))),
  source_sha256: Object.fromEntries(reviewed.map(file => [file, digest(readFileSync(path.join(root, file)))])),
  config: {sign_period: 4, sign_patterns: 16, last_index: 128, triple_last_index: 32}};

// Gaussian integers, norms, valuations, and cross products use BigInt throughout.
const units = [[1n, 0n], [0n, 1n], [-1n, 0n], [0n, -1n]];
const offsets = [[0n, 0n], [-1n, 0n], [-1n, 1n], [0n, -1n]];
const add = (a, b) => a.map((x, j) => x + b[j]);
const sub = (a, b) => a.map((x, j) => x - b[j]);
const scale = (k, a) => a.map(x => k * x);
const mul = ([a, b], [c, d]) => [a * c - b * d, a * d + b * c];
const norm = ([x, y]) => x * x + y * y;
const mod4 = n => ((n % 4) + 4) % 4;
const v2 = n => {
  assert(n > 0n, 'valuation needs a positive nonzero integer');
  let result = 0;
  while (n % 2n === 0n) { n /= 2n; result++; }
  return result;
};
const state = (signs, n, shift = 0) => {
  let sum = 0, bit = 0;
  while (n > 0) { sum += (n % 2) * signs[(bit++ + shift) % signs.length]; n = Math.floor(n / 2); }
  return mod4(sum);
};
const walk = (signs, last, shift = 0) => {
  const states = [], z = [[0n, 0n]], w = [], q = [];
  for (let n = 0; n <= last; n++) {
    const s = state(signs, n, shift);
    states.push(s);
    w.push(add(scale(2n, z[n]), offsets[s]));
    q.push([...w[n], 4n * BigInt(n) + BigInt(s)]);
    if (n < last) z.push(add(z[n], units[s]));
  }
  return {states, z, w, q};
};
const step = (r, s) => [...add(scale(2n, units[r]), sub(offsets[s], offsets[r])), BigInt(4 + s - r)];
const key = a => a.join(',');
const numbers = a => a.map(x => { const n = Number(x); assert(Number.isSafeInteger(n)); return n; });
const cases = [];
for (let mask = 0; mask < 16; mask++) cases.push({name: `sign-pattern-${mask}`, run: () => {
  const signs = Array.from({length: 4}, (_, j) => mask & (1 << j) ? 1 : -1);
  const a = walk(signs, identity.config.last_index), shifted = walk(signs, identity.config.last_index, 1);
  const factor = add(units[0], units[mod4(signs[0])]);
  let same = 0, halvings = 0, pairs = 0;
  for (let n = 0; n <= identity.config.last_index; n++) {
    const t = Math.floor(n / 2), bit = n % 2;
    assert.equal(a.states[n], mod4(shifted.states[t] + bit * signs[0]));
    assert.deepEqual(a.z[n], add(mul(factor, shifted.z[t]), scale(BigInt(bit), units[shifted.states[t]])));
    for (let m = 0; m < n; m++) {
      if (a.states[m] === a.states[n]) {
        assert.equal(v2(norm(sub(a.z[n], a.z[m]))), v2(BigInt(n - m)));
        same++;
        if ((n - m) % 2 === 0) {
          const b = Math.floor(m / 2);
          assert.equal(shifted.states[b], shifted.states[t]);
          assert.deepEqual(sub(a.z[n], a.z[m]), mul(factor, sub(shifted.z[t], shifted.z[b])));
          halvings++;
        }
      }
      assert.equal(v2(norm(sub(a.w[n], a.w[m]))), v2(a.q[n][2] - a.q[m][2]));
      pairs++;
    }
  }
  return {signs, recurrence_indices: a.states.length, same_state_pairs: same,
    even_same_state_halvings: halvings, all_state_pairs: pairs};
}});

cases.push({name: 'alternating-menus-and-encoding', run: () => {
  const expected = [
    ['01', 0, [1, 0, 5]], ['12', 4, [0, 3, 5]], ['23', 10, [-1, -2, 5]], ['30', 2, [0, -1, 1]],
    ['02', 9, [1, 1, 6]], ['13', 1, [1, 1, 6]], ['20', 5, [-1, -1, 2]], ['31', 21, [-1, -1, 2]],
  ];
  const a = walk([1, -1], identity.config.last_index), reverse = walk([-1, 1], identity.config.last_index);
  const first = new Map(), reversePairs = new Set(), reverseMenu = new Map();
  const vectors = expected.filter((_, j) => ![5, 7].includes(j)).map(row => row[2].map(BigInt));
  const p = [Array(6).fill(0n)];
  assert.deepEqual(a.q[0], [0n, 0n, 0n]);
  for (let n = 0; n < identity.config.last_index; n++) {
    const r = a.states[n], s = a.states[n + 1], pair = `${r}${s}`;
    let k = 0, t = n;
    while (t % 2 === 1) { k++; t = Math.floor(t / 2); }
    assert.equal(mod4(s - r), k % 2 === 0 ? 1 : 2);
    assert.deepEqual(sub(a.q[n + 1], a.q[n]), step(r, s));
    if (!first.has(pair)) first.set(pair, n);
    const label = vectors.findIndex(v => key(v) === key(step(r, s)));
    assert(label >= 0);
    const next = [...p[n]];
    next[label]++;
    p.push(next);
    const projected = next.reduce((v, count, j) => add(v, scale(count, vectors[j])), [0n, 0n, 0n]);
    assert.deepEqual(projected, a.q[n + 1]);
    assert.equal(next.reduce((x, y) => x + y, 0n), BigInt(n + 1));
    const rr = reverse.states[n], ss = reverse.states[n + 1];
    assert.equal(mod4(ss - rr), k % 2 === 0 ? 3 : 2);
    reversePairs.add(`${rr}${ss}`);
    assert.deepEqual(sub(reverse.q[n + 1], reverse.q[n]), step(rr, ss));
    reverseMenu.set(key(step(rr, ss)), numbers(step(rr, ss)));
  }
  assert.equal(first.size, 8);
  for (const [pair, witness, vector] of expected) {
    assert.equal(first.get(pair), witness);
    assert.deepEqual(numbers(step(+pair[0], +pair[1])), vector);
  }
  assert.deepEqual([...reversePairs].sort(), ['02', '03', '10', '13', '20', '21', '31', '32']);
  const expectedReverse = [[2, -1, 7], [1, 2, 3], [-2, -1, 3], [-1, 0, 3], [1, 1, 6], [-1, -1, 2]];
  assert.deepEqual([...reverseMenu.keys()].sort(), expectedReverse.map(key).sort());
  let triples = 0;
  for (let i = 0; i <= identity.config.triple_last_index; i++)
    for (let j = i + 1; j <= identity.config.triple_last_index; j++)
      for (let k = j + 1; k <= identity.config.triple_last_index; k++) {
        const u = sub(a.q[j], a.q[i]), v = sub(a.q[k], a.q[j]);
        assert([u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
          .some(x => x !== 0n));
        assert(sub(scale(BigInt(k - j), sub(p[j], p[i])), scale(BigInt(j - i), sub(p[k], p[j])))
          .some(x => x !== 0n));
        triples++;
      }
  return {g85_transition_witnesses: expected.map(([pair, least_index, vector]) => ({pair, least_index, vector})),
    g170_vectors: expectedReverse, encoded_steps: p.length - 1, triples_in_each_model: triples};
}});

cases.push({name: 'offset-collision-coefficients', run: () => {
  // Affine forms [constant real, constant imaginary, coefficient of c0, ..., c3].
  // The offset coefficients are real integers multiplying arbitrary complex offsets.
  const f = (r, s) => [...scale(2n, units[r]), ...Array.from({length: 4}, (_, j) => BigInt((j === s) - (j === r)))];
  const deltaTwo = sub(f(0, 2), f(1, 3));
  assert.deepEqual(deltaTwo, [2n, -2n, -1n, 1n, 1n, -1n]); // 2-2i-K
  assert.deepEqual(sub(f(2, 0), f(3, 1)), scale(-1n, deltaTwo));
  assert.deepEqual(sub(f(0, 1), f(2, 3)), [4n, 0n, -1n, 1n, 1n, -1n]); // 4-K
  assert.deepEqual(sub(f(1, 0), f(3, 2)), [0n, 4n, 1n, -1n, -1n, 1n]); // 4i+K
  const heightClasses = Array.from({length: 4}, (_, delta) => Array.from({length: 4}, (_, r) => 4 + mod4(r + delta) - r));
  assert.deepEqual(heightClasses, [[4, 4, 4, 4], [5, 5, 5, 1], [6, 6, 2, 2], [7, 3, 3, 3]]);
  // Every cyclic parity tagging: four common translations and either orientation.
  for (let origin = 0; origin < 4; origin++) for (const edge of [1, 2]) {
    const c = [origin, origin ^ edge, origin ^ 3, origin ^ edge ^ 3];
    assert.notEqual(c[1] ^ c[0], c[2] ^ c[1]);
    assert.notEqual(c[2] ^ c[1], c[3] ^ c[2]);
    assert.equal(c[1] ^ c[0], c[3] ^ c[2]);
  }
  return {affine_coefficient_identities: 4, cyclic_parity_taggings: 8, height_classes_by_delta: heightClasses};
}});

let signal;
for (const name of ['SIGINT', 'SIGTERM']) process.on(name, () => { signal = name; });
try {
  const started = performance.now();
  let completed = [];
  if (!options.recompute && existsSync(checkpoint)) {
    const saved = JSON.parse(readFileSync(checkpoint, 'utf8'));
    assert.equal(saved.sha256, digest(JSON.stringify(saved.payload)), 'corrupt checkpoint checksum');
    assert.deepEqual(saved.payload.identity, identity, 'incompatible checkpoint; use a new path or --recompute');
    completed = saved.payload.completed;
    assert(Array.isArray(completed) && completed.length <= cases.length);
    completed.forEach((row, i) => assert.equal(row.name, cases[i].name, 'invalid completed-case order'));
  }
  const initial = completed.length;
  log(initial ? 'resume' : 'start', {identity, completed: initial, total: cases.length,
    checkpoint, workers: 1, elapsed_seconds: 0});
  for (let i = initial; i < cases.length; i++) {
    if (signal || i - initial >= options.stopAfter) break;
    const result = cases[i].run();
    completed.push({name: cases[i].name, result});
    const payload = {identity, completed};
    atomic(checkpoint, {payload, sha256: digest(JSON.stringify(payload))});
    const elapsed = (performance.now() - started) / 1000, rate = (completed.length - initial) / elapsed;
    log('progress', {case: cases[i].name, completed: completed.length, total: cases.length,
      cases_per_second: rate, elapsed_seconds: elapsed, eta_seconds: (cases.length - completed.length) / rate});
    await new Promise(resolve => setImmediate(resolve));
  }
  if (completed.length < cases.length || signal) {
    log('paused', {signal: signal ?? null, completed: completed.length, total: cases.length, checkpoint});
    console.log(JSON.stringify({status: 'paused', completed: completed.length, total: cases.length}));
    if (signal) process.exitCode = signal === 'SIGINT' ? 130 : 143;
  } else {
    const result = {identity, status: 'finite_checks_pass', cases: completed,
      scope: 'Bounded exact-integer and affine-coefficient diagnostics only; the infinite proof and restricted scheme bound are audited in A-SIX-STEP-AUDIT.md. Not human collaborator approval or Lean certification.'};
    if (options.write) atomic(output, result);
    else assert.deepEqual(result, JSON.parse(readFileSync(output, 'utf8')), 'tracked result differs; inspect before --write');
    log('complete', {completed: completed.length, total: cases.length, output,
      elapsed_seconds: (performance.now() - started) / 1000, outcome: result.status});
    console.log(JSON.stringify({status: 'pass', cases: completed.length, resumed_cases: initial, scope: result.scope}));
  }
} catch (error) {
  log('error', {message: error.message, checkpoint});
  console.error(error);
  process.exitCode = 1;
}
