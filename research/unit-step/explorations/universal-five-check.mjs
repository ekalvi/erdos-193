#!/usr/bin/env node
// Small exact audit of the two-marker reduction; not an extension-tree search.
// No worker threads or dependencies. Each bounded stage is atomically cached.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

if (process.argv.includes('--help')) {
  console.log('Usage: node --single-threaded universal-five-check.mjs [WORK_DIR]\n'
    + 'Default WORK_DIR=.checkpoint-universal-five. Completed bounded stages resume\n'
    + 'only after source/config and result-digest validation. Fresh audit: use a new directory.\n'
    + 'JSONL progress and atomic checkpoints stay in WORK_DIR; stdout is the small result.');
  process.exit(0);
}
const directory = process.argv[2] ?? '.checkpoint-universal-five';
fs.mkdirSync(directory, { recursive: true });
const hash = x => crypto.createHash('sha256').update(x).digest('hex');
const source = hash(fs.readFileSync(fileURLToPath(import.meta.url)));
const config = { version: 1, alphabet: 5, markers: [0, 1], gapBound: 7,
  exhaustivePairGapBound: 4, seed: 193005, sampledWords: 1000 };
const identity = hash(JSON.stringify({ source, config }));
const checkpoint = path.join(directory, 'state.json');
const logFile = path.join(directory, 'run.jsonl');
const started = Date.now();
function log(event, extra = {}) {
  fs.appendFileSync(logFile, JSON.stringify({ timestamp: new Date().toISOString(),
    event, elapsedSeconds: (Date.now() - started) / 1000, ...extra }) + '\n');
}
let results = {};
if (fs.existsSync(checkpoint)) {
  const saved = JSON.parse(fs.readFileSync(checkpoint, 'utf8'));
  assert.equal(saved.identity, identity, 'incompatible source/config');
  assert.equal(saved.digest, hash(JSON.stringify(saved.results)), 'corrupt results');
  results = saved.results;
}
log('start', { source, config, checkpoint, completedStages: Object.keys(results),
  resources: { workers: 0, nativeThreads: 1 }, estimatedSeconds: '1-15' });
function persist() {
  const temporary = `${checkpoint}.tmp-${process.pid}`;
  fs.writeFileSync(temporary, JSON.stringify({ identity, results,
    digest: hash(JSON.stringify(results)) }, null, 2) + '\n');
  fs.renameSync(temporary, checkpoint);
}
function stage(name, computation) {
  if (Object.hasOwn(results, name)) { log('resume-stage', { name }); return; }
  const begin = Date.now();
  results[name] = computation();
  persist();
  log('completed-stage', { name, stageSeconds: (Date.now() - begin) / 1000,
    completedStages: Object.keys(results).length, totalStages: 3,
    outcome: results[name] });
}
function counts(word, alphabet = 5) {
  const p = [Array(alphabet).fill(0)];
  for (const c of word) { const a = [...p.at(-1)]; ++a[c]; p.push(a); }
  return p;
}
function ordinaryFree(word) {
  const p = counts(word);
  for (let end = 2; end <= word.length; ++end) {
    for (let half = 1; 2 * half <= end; ++half) {
      if (p[end].every((x, r) => x - p[end - half][r]
        === p[end - half][r] - p[end - 2 * half][r])) return false;
    }
  }
  return true;
}
const gaps = [];
function enumerate(word) {
  if (!ordinaryFree(word)) return;
  gaps.push(word);
  if (word.length < 8) for (const c of [2, 3, 4]) enumerate([...word, c]);
}
enumerate([]);
const vectorKey = a => a.join(',');
stage('gap-alphabet', () => {
  const rows = Array(9).fill(0), q = new Set(), prefixes = new Set();
  let incidences = 0;
  for (const u of gaps) {
    ++rows[u.length];
    const p = counts(u).map(a => a.slice(2));
    q.add(vectorKey(p.at(-1)));
    for (const a of p) prefixes.add(vectorKey(a));
    incidences += p.length;
  }
  assert.deepEqual(rows, [1, 3, 6, 12, 18, 30, 30, 18, 0]);
  assert.equal(q.size, 42); assert.equal(prefixes.size, 42);
  assert.equal(incidences, 697);
  return { rows, gaps: gaps.length, returnWords: 2 * gaps.length,
    returnCountVectors: 2 * q.size, prefixVectors: prefixes.size,
    coloredWordPrefixIncidences: 2 * incidences };
});
function sections(word) {
  // Parse first, independently of the full five-dimensional prefix construction.
  const runs = [{ marker: null, gap: [] }];
  for (const c of word) {
    if (c < 2) runs.push({ marker: c, gap: [] });
    else runs.at(-1).gap.push(c);
  }
  const vertices = [];
  let h = 0, x = [0, 0, 0];
  for (let t = 0; t < runs.length; ++t) {
    const { marker, gap } = runs[t];
    assert(ordinaryFree(gap) && gap.length <= 7);
    if (marker === 1) ++h;
    vertices.push([t, h, ...x]);
    for (const c of gap) { ++x[c - 2]; vertices.push([t, h, ...x]); }
  }
  return vertices;
}
let words = 0, triples = 0, violations = 0, unequalViolations = 0;
function check(word) {
  ++words;
  const p = counts(word), c = sections(word);
  assert.deepEqual(c, p.map(a => [a[0] + a[1], a[1], ...a.slice(2)]));
  for (let i = 0; i < p.length; ++i) for (let j = i + 1; j < p.length; ++j) {
    for (let k = j + 1; k < p.length; ++k) {
      ++triples;
      const direct = p[i].every((_, r) => (k - j) * (p[j][r] - p[i][r])
        === (j - i) * (p[k][r] - p[j][r]));
      const m = c[j][0] - c[i][0], n = c[k][0] - c[j][0];
      const returned = m > 0 && n > 0 && [1, 2, 3, 4].every(r =>
        n * (c[j][r] - c[i][r]) === m * (c[k][r] - c[j][r]));
      assert.equal(returned, direct, `word=${word.join('')} triple=${i},${j},${k}`);
      if (direct) { ++violations; if (j - i !== k - j) ++unequalViolations; }
    }
  }
}
stage('short-return-pairs', () => {
  const short = gaps.filter(u => u.length <= 4);
  for (const u of short) for (const v of short) for (const c of [0, 1]) {
    for (const d of [0, 1]) check([0, ...u, c, ...v, d]);
  }
  return { words, triples, violations, unequalViolations, maximumWordLength: 11 };
});
stage('full-gaps-and-unequal-examples', () => {
  words = 0; triples = 0; violations = 0; unequalViolations = 0;
  let seed = config.seed;
  const random = bound => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed % bound; };
  for (const u of gaps) for (const c of [0, 1]) check([0, ...u, c]);
  for (let t = 0; t < config.sampledWords; ++t) {
    const a = gaps[random(gaps.length)], b = gaps[random(gaps.length)],
      c = gaps[random(gaps.length)];
    check([...a, 0, ...b, random(2), ...c, random(2)]);
  }
  check([...('010213230213')].map(Number)); // Prior 4:8 partial-endpoint witness.
  check([...('012340123401234')].map(Number)); // Both marker colors, 5:10 ratio.
  assert(unequalViolations > 0);
  return { words, triples, violations, unequalViolations, maximumWordLength: 24 };
});
log('finish', { status: 'passed', completedStages: 3, totalStages: 3,
  throughputStagesPerSecond: 3 / Math.max(0.001, (Date.now() - started) / 1000),
  estimatedRemainingSeconds: 0 });
console.log(JSON.stringify({ source, config, results }, null, 2));
