#!/usr/bin/env node
/** Bounded exact checks for FOUR-LETTER-RETURN-REDUCTION.md (one JS worker).
 * --write regenerates the finite certificate; default compares it with disk.
 * Completed stages resume from an identity- and digest-checked atomic checkpoint.
 * SIGINT/SIGTERM stop after the current short stage. No unbounded prefix search.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {appendFileSync, existsSync, mkdirSync, readFileSync, renameSync, writeFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {setImmediate} from 'node:timers/promises';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log(`Usage: node research/unit-step/tracks/check_four_letter_returns.mjs [--write]
    [--work-dir PATH] [--output PATH]
Default: recompute or resume bounded checks, then compare the tracked certificate.
--write: atomically regenerate it. Paths are relative to the working directory.
Default work directory: .checkpoint-unit-step-four-returns (repository root).
Default output: research/unit-step/checks/four-letter-returns.json.
Stages are identity/digest checked and checkpointed atomically. A different source
requires a fresh work directory. SIGINT/SIGTERM stop at the next stage boundary.
Use a fresh --work-dir for an independent rerun. Logs stay in the work directory.
No workers or numerical libraries; at most one computational core.`);
  process.exit(0);
}
let write = false;
let workDir = resolve(root, '.checkpoint-unit-step-four-returns');
let output = resolve(root, 'research/unit-step/checks/four-letter-returns.json');
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--write') write = true;
  else if (['--work-dir', '--output'].includes(args[i]) && args[i + 1] && !args[i + 1].startsWith('--')) {
    const key = args[i++];
    if (key === '--work-dir') workDir = resolve(args[i]);
    else output = resolve(args[i]);
  } else throw Error(`Unknown or incomplete argument: ${args[i]}`);
}

const sha = data => createHash('sha256').update(data).digest('hex');
const identity = {schema: 1, code_sha256: sha(readFileSync(new URL(import.meta.url))),
  ternary_maximum_length: 8, shortest_obstruction_length: 12, gap_pairs: 117 ** 2};
mkdirSync(workDir, {recursive: true});
const checkpoint = resolve(workDir, 'state.json');
const logPath = resolve(workDir, 'run.jsonl');
const atomicWrite = (path, data) => {
  mkdirSync(dirname(path), {recursive: true});
  const temp = `${path}.${process.pid}.tmp`;
  writeFileSync(temp, data);
  renameSync(temp, path);
};
const started = performance.now();
const log = record => {
  const line = JSON.stringify({time: new Date().toISOString(), ...record}) + '\n';
  appendFileSync(logPath, line);
  process.stdout.write(line);
};
let stopped = null;
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => { stopped = signal; });
let state = {identity, completed: {}};
const save = () => atomicWrite(checkpoint, JSON.stringify({state, digest: sha(JSON.stringify(state))}) + '\n');

// Small integers only: all tested words have at most 17 letters, so products
// below are <= 17^2. These are exact integers, not floating-point tolerances.
const parikh = (word, alphabet = 4) => {
  const p = Array(alphabet).fill(0);
  for (const c of word) p[Number(c)]++;
  return p;
};
const add = (u, v) => u.map((x, r) => x + v[r]);
const sub = (u, v) => u.map((x, r) => x - v[r]);
const prefixes = (word, alphabet = 4) => {
  const points = [Array(alphabet).fill(0)];
  for (const c of word) {
    const p = [...points.at(-1)]; p[Number(c)]++; points.push(p);
  }
  return points;
};
const ordinarySuffix = word => {
  for (let m = 1; 2 * m <= word.length; m++) {
    const a = parikh(word.slice(-2 * m, -m)), b = parikh(word.slice(-m));
    if (a.every((x, r) => x === b[r])) return true;
  }
  return false;
};
const ordinaryFree = word => {
  for (let k = 2; k <= word.length; k++) if (ordinarySuffix(word.slice(0, k))) return false;
  return true;
};
const canonical = word => {
  const labels = new Map();
  return [...word].map(c => {if (!labels.has(c)) labels.set(c, labels.size); return labels.get(c);}).join('');
};
const nextLayer = (layer, alphabet) => {
  const next = [];
  for (const w of layer) {
    const highest = w.length ? Math.min(alphabet - 1, Math.max(...[...w].map(Number)) + 1) : 0;
    for (let c = 0; c <= highest; c++) if (!ordinarySuffix(w + c)) next.push(w + c);
  }
  return next;
};
// Independent collinearity oracle: all six 2x2 minors, NOT the marker clock
// or the equal-length suffix test used to generate the extension tree.
const rankOne = (u, v) => {
  for (let r = 0; r < u.length; r++) for (let s = r + 1; s < u.length; s++) {
    if (u[r] * v[s] !== u[s] * v[r]) return false;
  }
  return true;
};
const rankWitnesses = (points, indices = points.map((_, i) => i)) => {
  const hits = [];
  for (let i = 0; i < points.length; i++) for (let j = i + 1; j < points.length; j++) {
    const u = sub(points[j], points[i]);
    for (let k = j + 1; k < points.length; k++) {
      if (rankOne(u, sub(points[k], points[j]))) hits.push([indices[i], indices[j], indices[k]]);
    }
  }
  return hits;
};
// Rebuild cross-sections from ternary gap words, without using 4D prefixes.
// The final gap may be empty to represent a finite word ending in the marker.
const clouds = gaps => {
  const layers = [[{index: 0, point: [0, 0, 0]}]];
  let base = [0, 0, 0], index = 1;
  for (const gap of gaps) {
    const offsets = prefixes([...gap].map(c => Number(c) - 1), 3);
    layers.push(offsets.map((offset, r) => ({index: index + r, point: add(base, offset)})));
    base = add(base, offsets.at(-1)); index += gap.length + 1;
  }
  return layers;
};
const cloudWitnesses = layers => {
  const hits = [];
  for (let a = 0; a < layers.length; a++) for (let b = a + 1; b < layers.length; b++) {
    for (let c = b + 1; c < layers.length; c++) {
      for (const x of layers[a]) for (const y of layers[b]) for (const z of layers[c]) {
        if (x.point.every((v, r) => (c - b) * (y.point[r] - v) === (b - a) * (z.point[r] - y.point[r]))) {
          hits.push([x.index, y.index, z.index]);
        }
      }
    }
  }
  return hits.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
};
const compareClouds = gaps => {
  const word = '0' + gaps.join('0');
  const layers = clouds(gaps);
  const points = prefixes(word);
  const rebuilt = layers.flatMap((layer, t) => layer.map(({index, point}) => {
    assert.equal(index, points.findIndex(p => p[0] === t && p.slice(1).every((x, r) => x === point[r])));
    return [t, ...point];
  }));
  assert.deepEqual(rebuilt, points, `cross-section reconstruction: ${word}`);
  const direct = rankWitnesses(points);
  assert.deepEqual(cloudWitnesses(layers), direct, `all-ratios test: ${word}`);
  return direct;
};

const stages = [
  ['ternary', () => {
    const layers = [['']];
    for (let n = 1; n <= 8; n++) layers.push(nextLayer(layers.at(-1), 3));
    assert.deepEqual(layers.map(x => x.length), [1, 1, 1, 2, 3, 5, 5, 3, 0]);
    // Independently examine ALL labelled ternary words, including rejected
    // prefixes. Classify ordinary squares using rank witnesses with equal gaps.
    const labelled = Array(9).fill(0), survivors = Array.from({length: 9}, () => new Set());
    const alphabet = [];
    let checked = 0;
    for (let n = 0; n <= 8; n++) for (let code = 0; code < 3 ** n; code++) {
      const w = n ? code.toString(3).padStart(n, '0') : '';
      const hits = rankWitnesses(prefixes(w));
      const free = !hits.some(([i, j, k]) => j - i === k - j);
      assert.equal(free, ordinaryFree(w));
      checked++;
      if (free) {
        assert.equal(hits.length, 0, `ternary ordinary-free implies weak-free: ${w}`);
        labelled[n]++; survivors[n].add(canonical(w));
        if (n) alphabet.push([...w].map(c => Number(c) + 1).join(''));
      }
    }
    for (let n = 0; n <= 8; n++) assert.deepEqual([...survivors[n]].sort(), [...layers[n]].sort());
    assert.deepEqual(labelled, [1, 3, 6, 12, 18, 30, 30, 18, 0]);
    assert.equal(checked, 9841);
    assert.equal(alphabet.length, 117);
    const types = [...new Set(alphabet.map(w => parikh(w).slice(1).join(',')))].sort();
    assert.equal(types.length, 41);
    const endpointCount = alphabet.reduce((sum, w) => sum + w.length + 1, 0);
    assert.equal(endpointCount, 696);
    return {canonical_layers: layers, labelled_counts_by_length: labelled,
      labelled_words_checked: checked, gap_alphabet: alphabet.sort(),
      gap_parikh_vectors: types.map(s => s.split(',').map(Number)),
      distinct_prefix_parikh_vectors_including_zero: types.length + 1,
      gap_and_prefix_pairs: endpointCount};
  }],
  ['shortest', () => {
    let layer = [''];
    const counts = [1], newForbidden = [];
    for (let n = 1; n <= 12; n++) {
      layer = nextLayer(layer, 4); counts.push(layer.length);
      for (const word of layer) {
        const hits = rankWitnesses(prefixes(word));
        if (n < 12) assert.equal(hits.length, 0);
        else if (hits.length) {
          assert.equal(hits.length, 1);
          const [i, j, k] = hits[0];
          assert.equal(i, 0); assert.equal(k, 12); assert([4, 8].includes(j));
          newForbidden.push({word, split: j});
        }
      }
    }
    assert.deepEqual(counts, [1, 1, 1, 2, 4, 11, 27, 66, 149, 328, 640, 1216, 2130]);
    assert.equal(newForbidden.length, 164);
    assert.equal(newForbidden.filter(row => row.split === 4).length, 82);
    assert.equal(newForbidden.filter(row => row.split === 8).length, 82);
    return {ordinary_free_canonical_counts_by_length: counts,
      minimum_length_of_weak_square_without_ordinary_square: 12,
      shortest_forbidden_canonical_factors: newForbidden};
  }],
  ['ratio-examples', () => {
    // Deliberately periodic: not a candidate. Exercises coprime ratios 1:3
    // and 3:1, and common spacing 2, beyond the two-internal-gap cases.
    const gaps = ['123', '123', '123', '123', ''];
    const hits = compareClouds(gaps);
    const selected = [[0, 4, 16], [0, 12, 16], [0, 8, 16]];
    for (const triple of selected) assert(hits.some(row => row.every((n, r) => n === triple[r])));
    return {word: '0' + gaps.join('0'), selected_triples: selected,
      selected_marker_increments: [[1, 3], [3, 1], [2, 2]],
      cloud_and_rank_witness_sets_agree: true};
  }],
  ['boundary-example', () => {
    const word = '010213230213', gaps = ['1', '21323', '213'];
    assert.equal('0' + gaps.join('0'), word);
    assert(ordinaryFree(word));
    assert.deepEqual(compareClouds(gaps), [[0, 8, 12]]);
    const layers = clouds(gaps), cuts = layers.map(layer => layer[0].index);
    const p = prefixes(word);
    assert.deepEqual(rankWitnesses(cuts.map(n => p[n]), cuts), []);
    return {word, gaps, missed_triple: [0, 8, 12],
      blocks: [word.slice(0, 8), word.slice(8)],
      block_parikh_vectors: [parikh(word.slice(0, 8)), parikh(word.slice(8))],
      return_cut_indices_including_origin: cuts,
      return_cut_points: cuts.map(n => p[n]), return_cut_collinear_triples: []};
  }],
];
// Check every pair of the 117 possible internal gaps. All their vertices,
// including the origin and final marker, are tested by both implementations.
for (let batch = 0; batch < 8; batch++) stages.push([`cloud-pairs-${batch}`, () => {
  const alphabet = state.completed.ternary.gap_alphabet;
  const from = batch * 16, to = Math.min(from + 16, alphabet.length);
  let pairs = 0, triples = 0, violatingPairs = 0;
  for (let i = from; i < to; i++) for (const v of alphabet) {
    const gaps = [alphabet[i], v, ''];
    const hits = compareClouds(gaps);
    pairs++; if (hits.length) violatingPairs++;
    const vertices = alphabet[i].length + v.length + 4;
    triples += vertices * (vertices - 1) * (vertices - 2) / 6;
  }
  return {pairs, direct_triples_checked: triples, violating_pairs: violatingPairs};
}]);

try {
  if (existsSync(checkpoint)) {
    const envelope = JSON.parse(readFileSync(checkpoint, 'utf8'));
    assert.equal(envelope.digest, sha(JSON.stringify(envelope.state)), 'corrupt checkpoint digest');
    assert.deepEqual(envelope.state.identity, identity, 'incompatible checkpoint: use a fresh --work-dir');
    state = envelope.state;
    const names = stages.map(([name]) => name);
    assert.deepEqual(Object.keys(state.completed), names.slice(0, Object.keys(state.completed).length),
      'checkpoint stages must form a prefix');
  }
  log({event: 'start/resume', identity, completed: Object.keys(state.completed).length,
    total: stages.length, checkpoint, log: logPath, computational_cores: 1,
    mode: write ? 'write' : 'check'});
  let executed = 0;
  for (const [name, run] of stages) {
    if (stopped) break;
    if (!Object.hasOwn(state.completed, name)) {
      state.completed[name] = run(); save(); executed++;
      const elapsed = (performance.now() - started) / 1000;
      const completed = Object.keys(state.completed).length;
      log({event: 'checkpoint', stage: name, completed, total: stages.length,
        elapsed_seconds: elapsed, stages_per_second: executed / elapsed,
        estimated_remaining_seconds: (stages.length - completed) * elapsed / executed});
    }
    await setImmediate();
  }
  if (stopped) {
    save(); log({event: 'interrupted', signal: stopped, completed: Object.keys(state.completed).length, checkpoint});
    process.exitCode = stopped === 'SIGINT' ? 130 : 143;
  } else {
    const {ternary, shortest, 'boundary-example': example, 'ratio-examples': ratios} = state.completed;
    const batches = Object.entries(state.completed).filter(([key]) => key.startsWith('cloud-pairs-')).map(([, value]) => value);
    const sum = key => batches.reduce((a, row) => a + row[key], 0);
    assert.equal(sum('pairs'), 13689);
    const certificate = {identity,
      scope: 'Exact finite local checks and examples supporting a written reduction; not a 4D impossibility or infinite construction.',
      ternary, shortest, boundary_example: example, ratio_examples: ratios,
      all_gap_pairs: {pairs_checked: sum('pairs'), direct_triples_checked: sum('direct_triples_checked'),
        violating_pairs: sum('violating_pairs'), cloud_and_rank_witness_sets_agree: true}};
    if (write) atomicWrite(output, JSON.stringify(certificate, null, 2) + '\n');
    else assert.deepEqual(JSON.parse(readFileSync(output, 'utf8')), certificate, 'certificate differs');
    log({event: 'pass', completed: stages.length, total: stages.length, output,
      resumed_stages: stages.length - executed, elapsed_seconds: (performance.now() - started) / 1000});
  }
} catch (error) {
  log({event: 'error', message: error.message, completed: Object.keys(state.completed).length, checkpoint});
  process.exitCode = 1;
}
