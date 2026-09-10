#!/usr/bin/env node
// Independent finite verification: no imports from the discovery search.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { setImmediate as yieldNow } from 'node:timers/promises';

const here = path.dirname(fileURLToPath(import.meta.url));
if (process.argv.includes('--help')) {
  console.log(`Usage: node --single-threaded verify.mjs [STATE_DIR] [--stop-after N]
Exact finite checks only. Atomic stage checkpoints validate code/data/config hashes
and payload checksums; completed stages are reused. SIGINT/SIGTERM finish the
current bounded stage, save, then exit. --stop-after limits stages per invocation.
Logs/checkpoints/results go in STATE_DIR (default .checkpoint-five-marker-verify).
No packages, workers, Python, native numerical libraries, or infinite-word test.`);
  process.exit(0);
}
const args = process.argv.slice(2);
let stateDir = '.checkpoint-five-marker-verify', stopAfter = Infinity;
if (args.length && !args[0].startsWith('--')) stateDir = args.shift();
if (args.length) {
  assert.equal(args.shift(), '--stop-after'); stopAfter = Number(args.shift());
  assert(Number.isSafeInteger(stopAfter) && stopAfter >= 0);
}
assert.equal(args.length, 0);
fs.mkdirSync(stateDir, { recursive: true });
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
const dataBytes = fs.readFileSync(path.join(here, 'examples.json'));
const data = JSON.parse(dataBytes);
const identity = { schema: 1, sourceSha256: sha(fs.readFileSync(fileURLToPath(import.meta.url))),
  examplesSha256: sha(dataBytes), alphabet: 5, arithmetic: 'BigInt word oracles; bounded exact integer count grid',
  stages: ['witnesses', 'fraction-profiles', 'balanced-two', 'count-graphs', 'periodic-local-extension'] };
const checkpoint = path.join(stateDir, 'state.json'), logPath = path.join(stateDir, 'run.jsonl');
function atomic(file, value) {
  const tmp = `${file}.tmp`; fs.writeFileSync(tmp, JSON.stringify(value, null, 2) + '\n'); fs.renameSync(tmp, file);
}
function log(event, extra = {}) {
  const row = { utc: new Date().toISOString(), event, ...extra };
  fs.appendFileSync(logPath, JSON.stringify(row) + '\n'); console.log(JSON.stringify(row));
}
let state = { identity, completed: [] };
const resumed = fs.existsSync(checkpoint);
if (resumed) {
  const saved = JSON.parse(fs.readFileSync(checkpoint));
  assert.equal(saved.sha256, sha(JSON.stringify(saved.payload)), 'corrupt checkpoint checksum');
  assert.deepEqual(saved.payload.identity, identity, 'incompatible checkpoint');
  state = saved.payload;
  assert.deepEqual(state.completed.map(row => row.stage), identity.stages.slice(0, state.completed.length));
  assert(state.completed.length <= identity.stages.length);
}
const save = () => atomic(checkpoint, { payload: state, sha256: sha(JSON.stringify(state)) });
let signal = null;
process.on('SIGINT', () => { signal = 'SIGINT'; }); process.on('SIGTERM', () => { signal = 'SIGTERM'; });
const pairs = []; for (let a = 0; a < 5; a++) for (let b = a + 1; b < 5; b++) pairs.push([a, b]);
const key = ([a, b]) => `${a}${b}`;
const letters = word => [...word].map(Number);
function counts(word) {
  const v = [0n, 0n, 0n, 0n, 0n]; for (const a of word) v[a]++; return v;
}
function gcd(a, b) { while (b) [a, b] = [b, a % b]; return a; }
function primitive(v) {
  const g = v.reduce(gcd, 0n); assert(g > 0n); return v.map(x => x / g).join(',');
}
// Raw slices and gcd-normalized directions, unlike the search's prefix/time products.
function auditSquares(word) {
  const violations = []; let triples = 0, unequalTriples = 0;
  for (let i = 0; i < word.length - 1; i++) for (let j = i + 1; j < word.length; j++) for (let k = j + 1; k <= word.length; k++) {
    const U = counts(word.slice(i, j)), V = counts(word.slice(j, k)); triples++;
    if (j - i !== k - j) unequalTriples++;
    if (primitive(U) === primitive(V)) violations.push([i, j, k]);
  }
  return { triples, unequalTriples, violations };
}
function levelGraph(word, num, den) {
  num = BigInt(num); den = BigInt(den);
  assert(0n < num && num < den);
  const T = counts(word);
  assert(T.every(x => x > 0n && x * num % den === 0n));
  const target = T.map(x => x * num / den);
  // Derive split windows from occurrence positions, not from pair-return equations.
  const windows = target.map((t, a) => {
    const positions = word.flatMap((b, i) => a === b ? [i] : []);
    return [positions[Number(t) - 1] + 1, positions[Number(t)]];
  });
  const edges = pairs.filter(([a, b]) => Math.max(windows[a][0], windows[b][0]) <= Math.min(windows[a][1], windows[b][1])).map(key);
  const missing = pairs.map(key).filter(p => !edges.includes(p));
  const lo = Math.max(...windows.map(w => w[0])), hi = Math.min(...windows.map(w => w[1]));
  const common = lo <= hi;
  const exactCuts = [];
  for (let j = 1; j < word.length; j++) if (counts(word.slice(0, j)).every((v, a) => v === target[a])) exactCuts.push(j);
  assert.equal(common, exactCuts.length > 0, 'Helly synchronization');
  assert.equal(edges.length === 10, common, 'pairwise interval Helly');
  return { fraction: `${num}/${den}`, windows, edges, missing, commonCuts: exactCuts,
    bridgeCuts: common ? null : [hi, lo], bridgeWord: common ? null : word.slice(hi, lo).join('') };
}
function projectionLevels(word) {
  const out = {};
  for (const [a, b] of pairs) {
    const projected = word.filter(c => c === a || c === b);
    const A = BigInt(projected.filter(c => c === a).length), B = BigInt(projected.filter(c => c === b).length);
    assert(A > 0n && B > 0n);
    const fractions = new Set(); let ca = 0n, cb = 0n;
    for (const c of projected) {
      if (c === a) ca++; else cb++;
      if (ca > 0n && ca < A && cb > 0n && cb < B && ca * B === cb * A) {
        const g = gcd(ca, A); fractions.add(`${ca / g}/${A / g}`);
      }
    }
    out[`${a}${b}`] = [...fractions].sort();
  }
  return out;
}
function auditBridge(word, graph) {
  if (graph.commonCuts.length) return;
  const [r, l] = graph.bridgeCuts;
  const nonuniversal = new Set(graph.missing.join(''));
  assert([...word.slice(r, l)].every(a => nonuniversal.has(String(a))));
  if (graph.edges.length === 9) {
    assert.equal(l - r, 2, 'nine pairs leave exactly one adjacent swap');
    assert.notEqual(word[r], word[r + 1]);
    assert.equal([...graph.bridgeWord].sort().join(''), graph.missing[0]);
    const [num, den] = graph.fraction.split('/').map(BigInt);
    const m = Number(BigInt(word.length) * num / den);
    assert.deepEqual([r, l], [m - 1, m + 1]);
    const repaired = [...word]; [repaired[r], repaired[r + 1]] = [repaired[r + 1], repaired[r]];
    assert.equal(primitive(counts(repaired.slice(0, m))), primitive(counts(repaired.slice(m))));
  }
  if (graph.edges.length >= 8) {
    assert(nonuniversal.size <= 3, 'two missing edges cannot be disjoint');
    assert(l - r <= 7, 'ternary bridge bound');
  }
}
function witnesses() {
  let triples = 0, unequalTriples = 0;
  const words = [data.outerEndpointCounterexample.word, data.ninePairsOneLevel.word, ...data.sameCutCounterexamples.map(x => x.word)];
  for (const text of words) {
    const result = auditSquares(letters(text)); assert.deepEqual(result.violations, [], `not avoiding: ${text}`);
    triples += result.triples; unequalTriples += result.unequalTriples;
  }
  const main = letters(data.outerEndpointCounterexample.word);
  assert.deepEqual(counts(main).map(Number), data.outerEndpointCounterexample.totalCounts);
  const levels = projectionLevels(main);
  assert.deepEqual(levels, data.outerEndpointCounterexample.levelsByPair);
  const intersection = Object.values(levels).reduce((a, b) => a.filter(x => b.includes(x)));
  assert.deepEqual(intersection, []);
  const graphs = [levelGraph(main, 1, 3), levelGraph(main, 2, 3)];
  graphs.forEach(g => auditBridge(main, g));
  const selectedWitnesses = pairs.map(([a, b]) => {
    const [num, den] = levels[`${a}${b}`][0].split('/').map(BigInt), T = counts(main);
    for (let j = 1; j < main.length; j++) {
      const U = counts(main.slice(0, j)), V = counts(main.slice(j));
      if (den * U[a] !== num * T[a] || den * U[b] !== num * T[b]) continue;
      const m = U[a] + U[b], n = V[a] + V[b]; assert(m > 0n && n > 0n);
      assert.equal(n * U[b], m * V[b]);
      const remainder = [0, 1, 2, 3, 4].filter(c => c !== a && c !== b);
      const defect = remainder.map(c => n * U[c] - m * V[c]);
      assert(defect.some(v => v !== 0n), 'remaining counts accidentally synchronized');
      return { pair: `${a}${b}`, fraction: `${num}/${den}`, cuts: [0, j, main.length],
        markerIncrements: [Number(m), Number(n)], remainingLetters: remainder, gapResidual: defect.map(Number) };
    }
    throw Error('no physical witness for projected return');
  });
  const half = letters(data.ninePairsOneLevel.word), halfGraph = levelGraph(half, 1, 2);
  assert.deepEqual(counts(half).map(Number), data.ninePairsOneLevel.totalCounts);
  assert.deepEqual(halfGraph.missing, data.ninePairsOneLevel.missingPairs);
  assert.deepEqual(halfGraph.bridgeCuts, data.ninePairsOneLevel.bridgeCuts);
  assert.equal(halfGraph.bridgeWord, data.ninePairsOneLevel.bridgeWord); auditBridge(half, halfGraph);
  const sameCuts = data.sameCutCounterexamples.map(example => {
    const word = letters(example.word), [i, j, k] = example.cuts;
    const U = counts(word.slice(i, j)), V = counts(word.slice(j, k));
    assert.deepEqual(U.map(Number), example.leftCounts); assert.deepEqual(V.map(Number), example.rightCounts);
    const zero = pairs.filter(([a, b]) => U[a] * V[b] === U[b] * V[a]);
    for (const [a, b] of zero) assert(U[a] + U[b] > 0n && V[a] + V[b] > 0n, 'marker layers not strictly increasing');
    assert.deepEqual(zero.map(key), example.zeroMinorPairs);
    assert.notEqual(primitive(U), primitive(V)); return { word: example.word, cuts: example.cuts, zeroPairs: zero.map(key) };
  });
  return { words: words.length, triples, unequalTriples, allAvoiding: true, levels, levelIntersection: intersection,
    graphs, selectedWitnesses, halfGraph, sameCuts };
}
function fractionProfiles() {
  let seed = 193005;
  function random(n) { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed % n; }
  function shuffle(word) {
    const out = [...word]; for (let i = out.length - 1; i > 0; i--) { const j = random(i + 1); [out[i], out[j]] = [out[j], out[i]]; } return out;
  }
  function expand(profile, multiplier) { return profile.flatMap((n, a) => Array(n * multiplier).fill(a)); }
  const specimens = [{ word: [0, 1, 2, 3, 4], plantedCut: null }];
  for (let t = 0; t < 120; t++) {
    const R = Array.from({ length: 5 }, () => 1 + random(3)), g = 2 + t % 6, p = 1 + random(g - 1);
    const left = shuffle(expand(R, p)), right = shuffle(expand(R, g - p));
    specimens.push({ word: [...left, ...right], plantedCut: left.length });
    specimens.push({ word: shuffle(expand(R, g)), plantedCut: null });
  }
  let fractions = 0, splitComparisons = 0, positiveUnequalSplits = 0, maxLength = 0;
  for (const { word, plantedCut } of specimens) {
    maxLength = Math.max(maxLength, word.length);
    const T = counts(word), G = T.reduce(gcd, 0n), projected = projectionLevels(word);
    const commonFractions = Object.values(projected).reduce((a, b) => a.filter(x => b.includes(x))).sort();
    const direct = [];
    for (let j = 1; j < word.length; j++) {
      splitComparisons++;
      const U = counts(word.slice(0, j));
      // This outer-interval oracle uses physical lengths and all five coordinates.
      if (U.every((v, a) => BigInt(word.length) * v === BigInt(j) * T[a])) {
        const d = gcd(BigInt(j), BigInt(word.length)); direct.push(`${BigInt(j) / d}/${BigInt(word.length) / d}`);
        if (2 * j !== word.length) positiveUnequalSplits++;
      }
    }
    assert.deepEqual(commonFractions, direct.sort());
    if (plantedCut !== null) {
      const d = gcd(BigInt(plantedCut), BigInt(word.length));
      assert(commonFractions.includes(`${BigInt(plantedCut) / d}/${BigInt(word.length) / d}`));
    }
    for (let r = 1n; r < G; r++) {
      const d = gcd(r, G), graph = levelGraph(word, r / d, G / d); fractions++;
      const edges = Object.entries(projected).filter(([, values]) => values.includes(graph.fraction)).map(([pair]) => pair).sort();
      assert.deepEqual(graph.edges, edges);
    }
  }
  assert(positiveUnequalSplits > 0);
  return { scope: 'fixed-seed finite tests, NOT exhaustive word enumeration or avoidance evidence',
    seed: 193005, words: specimens.length, plantedWords: 120, ratios: 'planted reduced ratios drawn from p:(g-p), 2<=g<=7; all prefix splits tested',
    maxLength, splitComparisons, fractions, positiveUnequalSplits };
}
function balancedTwo() {
  let words = 0, avoiding = 0, triples = 0, nine = 0, eight = 0;
  const edgeHistogram = {}, avoidingEdgeHistogram = {};
  const word = [], used = [0, 0, 0, 0, 0];
  function visit(maxUsed) {
    if (word.length === 10) {
      words++; const graph = levelGraph(word, 1, 2);
      edgeHistogram[graph.edges.length] = (edgeHistogram[graph.edges.length] ?? 0) + 1;
      const audit = auditSquares(word); triples += audit.triples;
      // Also check graph edges directly from binary projections, independent of windows.
      const projected = projectionLevels(word);
      assert.deepEqual(Object.entries(projected).filter(([, v]) => v.includes('1/2')).map(([p]) => p).sort(), graph.edges);
      if (audit.violations.length === 0) {
        avoiding++; auditBridge(word, graph);
        avoidingEdgeHistogram[graph.edges.length] = (avoidingEdgeHistogram[graph.edges.length] ?? 0) + 1;
        if (graph.edges.length === 9) nine++; if (graph.edges.length === 8) eight++;
      }
      return;
    }
    for (let a = 0; a <= Math.min(4, maxUsed + 1); a++) if (used[a] < 2) {
      used[a]++; word.push(a); visit(Math.max(maxUsed, a)); word.pop(); used[a]--;
    }
  }
  visit(-1); assert.equal(words, 945); // 10! / (2!^5 5!), first-occurrence canonical words.
  return { scope: 'all 945 canonical five-letter words with each letter twice', words, labeledEquivalent: words * 120,
    triples, avoiding, nine, eight, edgeHistogram, avoidingEdgeHistogram };
}
function countGraphs() {
  const vectors = Array.from({ length: 1024 }, (_, index) => {
    const v = []; for (let a = 0; a < 5; a++) { v.push(index % 4); index = Math.floor(index / 4); } return v;
  });
  const observedBadMasks = new Set(), eligibleSpectra = { 0: new Set(), 1: new Set() };
  let cases = 0, nonproportional = 0;
  for (const U of vectors) for (const V of vectors) {
    if (!U.some(Boolean) || !V.some(Boolean)) continue;
    const active = U.map((u, a) => u + V[a] > 0), z = active.filter(x => !x).length;
    if (z > 1) continue; cases++;
    let mask = 0;
    pairs.forEach(([a, b], bit) => { if (U[a] * V[b] === U[b] * V[a]) mask |= 1 << bit; });
    if (mask !== 1023) { nonproportional++; observedBadMasks.add(mask); }
    if (U.filter(Boolean).length >= 4 && V.filter(Boolean).length >= 4) eligibleSpectra[z].add(pairs.filter((_, bit) => mask & (1 << bit)).length);
  }
  function connected(mask, omit = -1) {
    const vertices = [0, 1, 2, 3, 4].filter(a => a !== omit), seen = new Set([vertices[0]]);
    for (let round = 0; round < 5; round++) pairs.forEach(([a, b], bit) => {
      if (!(mask & (1 << bit)) || a === omit || b === omit) return;
      if (seen.has(a)) seen.add(b); if (seen.has(b)) seen.add(a);
    });
    return seen.size === vertices.length;
  }
  let sufficient = 0, minimumEdges = 11;
  for (let graph = 0; graph < 1024; graph++) {
    const noGridCounterexample = ![...observedBadMasks].some(mask => (mask & graph) === graph);
    const twoConnected = connected(graph) && [0, 1, 2, 3, 4].every(z => connected(graph, z));
    assert.equal(noGridCounterexample, twoConnected, `graph ${graph}: robust synchronization classification`);
    if (twoConnected) { sufficient++; minimumEdges = Math.min(minimumEdges, pairs.filter((_, bit) => graph & (1 << bit)).length); }
  }
  const spectrum = Object.fromEntries(Object.entries(eligibleSpectra).map(([z, set]) => [z, [...set].sort((a, b) => a - b)]));
  assert.deepEqual(spectrum, { 0: [0, 1, 2, 3, 4, 6, 10], 1: [4, 5, 6, 7, 10] });
  assert.equal(minimumEdges, 5);
  return { scope: 'count vectors in {0,1,2,3}^5 with nonzero sums and union support at least four; not word enumeration',
    cases, nonproportional, graphs: 1024, sufficientGraphs: sufficient, minimumEdges, eligibleZeroEdgeSpectrum: spectrum };
}
function periodicLocal() {
  const period = letters(data.outerEndpointCounterexample.word), repeated = [...period, ...period, ...period];
  let gaps = 0, maxGapLength = 0;
  for (const [a, b] of pairs) {
    const positions = repeated.flatMap((c, i) => c === a || c === b ? [i] : []);
    for (let t = 0; t + 1 < positions.length; t++) {
      if (positions[t] < period.length || positions[t] >= 2 * period.length) continue;
      const gap = repeated.slice(positions[t] + 1, positions[t + 1]); gaps++;
      maxGapLength = Math.max(maxGapLength, gap.length);
      assert(gap.length <= 7); assert.deepEqual(auditSquares(gap).violations, []);
    }
  }
  assert.equal(gaps, 60);
  const U = counts(period), V = counts(period); assert.equal(primitive(U), primitive(V));
  return { period: period.join(''), markerGapOccurrencesPerPeriod: gaps, maxGapLength,
    ternaryGapGrammarExtendsPeriodically: true, NOT_an_avoiding_extension: true, squareCuts: [0, 15, 30] };
}
const functions = [witnesses, fractionProfiles, balancedTwo, countGraphs, periodicLocal];
const started = Date.now(); let runStages = 0;
log(resumed ? 'resume' : 'start', { identity, checkpoint, completed: state.completed.length, total: functions.length,
  resources: { workers: 0, affinity: fs.readFileSync('/proc/self/status', 'utf8').match(/^Cpus_allowed_list:\s*(.*)$/m)?.[1],
    OMP_NUM_THREADS: process.env.OMP_NUM_THREADS, OPENBLAS_NUM_THREADS: process.env.OPENBLAS_NUM_THREADS,
    MKL_NUM_THREADS: process.env.MKL_NUM_THREADS, NUMEXPR_NUM_THREADS: process.env.NUMEXPR_NUM_THREADS,
    UV_THREADPOOL_SIZE: process.env.UV_THREADPOOL_SIZE } });
try {
  while (state.completed.length < functions.length && !signal && runStages < stopAfter) {
    const index = state.completed.length, t = Date.now();
    log('stage-start', { stage: identity.stages[index], completed: index, total: functions.length, eta: 'bounded stages, expected under ten seconds total' });
    const result = functions[index](); state.completed.push({ stage: identity.stages[index], result }); save(); runStages++;
    log('stage-complete', { stage: identity.stages[index], stageMs: Date.now() - t, elapsedMs: Date.now() - started,
      completed: state.completed.length, total: functions.length, stagesPerSecond: 1000 * runStages / Math.max(1, Date.now() - started), checkpoint });
    await yieldNow();
  }
  save();
  if (state.completed.length === functions.length) atomic(path.join(stateDir, 'result.json'), state);
  log(signal ? 'interrupted' : state.completed.length === functions.length ? 'complete' : 'budget-stop', {
    completed: state.completed.length, total: functions.length, elapsedMs: Date.now() - started, checkpoint, signal });
  if (signal) process.exitCode = signal === 'SIGINT' ? 130 : 143;
} catch (error) { save(); log('error', { message: error.stack, checkpoint }); process.exitCode = 1; }
