#!/usr/bin/env node
// Bounded exact regression checks for new-words.md; NOT an infinite construction.
// No dependencies, workers, or native numerical libraries. Expected runtime <10 s.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

if (process.argv.includes('--help')) {
  console.log('Usage: node research/unit-step/explorations/new-words-check.mjs\n' +
    'Fixed, bounded exact checks (<10 s expected): exhaustive words of total length\n' +
    '2..7 on 4/5 letters, the gcd formula, balanced anchors, and star thresholds.\n' +
    'No search, checkpoint, or claim of infinite avoidance.');
  process.exit(0);
}
assert.equal(process.argv.length, 2, 'No parameters except --help');
const started = Date.now();
const log = (data) => console.log(JSON.stringify({ time: new Date().toISOString(), ...data }));
log({ phase: 'start', sourceSha256: createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex'),
  parameters: { alphabets: [4, 5], maxTotalLength: 7 }, workers: 1,
  threads: { OMP_NUM_THREADS: process.env.OMP_NUM_THREADS, OPENBLAS_NUM_THREADS: process.env.OPENBLAS_NUM_THREADS,
    MKL_NUM_THREADS: process.env.MKL_NUM_THREADS, NUMEXPR_NUM_THREADS: process.env.NUMEXPR_NUM_THREADS,
    UV_THREADPOOL_SIZE: process.env.UV_THREADPOOL_SIZE }, checkpoint: null, resume: 'bounded regression; rerun from start' });
const fact = [1n];
for (let i = 1; i <= 120; ++i) fact[i] = fact[i - 1] * BigInt(i);
const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
const multinomial = (n, counts) => fact[n] / counts.reduce((acc, r) => acc * fact[r], 1n);
function compositions(total, parts, visit, prefix = []) {
  if (parts === 1) return visit([...prefix, total]);
  for (let r = 0; r <= total; ++r) compositions(total - r, parts - 1, visit, [...prefix, r]);
}
function exactCount(d, a, b) {
  const g = gcd(a, b), p = a / g, q = b / g;
  let answer = 0n;
  compositions(g, d, (r) => {
    answer += multinomial(a, r.map(x => p * x)) * multinomial(b, r.map(x => q * x));
  });
  return answer;
}
let checkedPairs = 0, checkedWords = 0;
for (const d of [4, 5]) {
  for (let n = 2; n <= 7; ++n) {
    const word = Array(n).fill(0), totals = Array(d).fill(0), observed = Array(n).fill(0n);
    function visit(pos) {
      if (pos !== n) {
        for (let r = 0; r < d; ++r) {
          word[pos] = r; totals[r]++; visit(pos + 1); totals[r]--;
        }
        return;
      }
      checkedWords++;
      const left = Array(d).fill(0);
      for (let a = 1; a < n; ++a) {
        left[word[a - 1]]++;
        if (left.every((v, r) => (n - a) * v === a * (totals[r] - v))) observed[a]++;
      }
    }
    visit(0);
    for (let a = 1; a < n; ++a) {
      assert.equal(exactCount(d, a, n - a), observed[a], `d=${d}, a=${a}, b=${n-a}`);
      checkedPairs++;
    }
    log({ phase: 'exhaustive', d, totalLength: n, checkedPairs, checkedWords,
      elapsedMs: Date.now() - started });
  }
}
// A short block containing every letter once and a long block with t copies of
// each letter are an explicitly counted subset of all weak squares of ratio 1:t.
const anchors = [];
for (const d of [4, 5, 6]) {
  for (const t of [1, 2, 3, 4]) {
    const anchor = fact[d] * fact[d * t] / fact[t] ** BigInt(d);
    const all = exactCount(d, d, d * t);
    assert(anchor <= all);
    anchors.push({ d, t, anchorCount: String(anchor), allCount: String(all),
      denominator: String(BigInt(d) ** BigInt(d * (t + 1))) });
  }
}
// Exact arithmetic: P(E_{n,n}) >= 1/binomial(n+d-1,d-1), and n disjoint aa
// leaves have joint avoidance probability ((d-1)/d)^n. Find the first n>=2
// where this elementary lower bound certifies the star obstruction.
function choose(n, k) {
  let v = 1n;
  for (let j = 1; j <= k; ++j) v = v * BigInt(n - k + j) / BigInt(j);
  return v;
}
const stars = [];
for (const d of [4, 5, 6]) {
  let n = 2;
  for (; n < 1000; ++n) {
    if (BigInt(d) ** BigInt(n) >= choose(n + d - 1, d - 1) * BigInt(d - 1) ** BigInt(n)) break;
  }
  assert(n < 1000);
  if (n > 2) assert(BigInt(d) ** BigInt(n - 1) < choose(n + d - 2, d - 1) * BigInt(d - 1) ** BigInt(n - 1));
  stars.push({ d, halfLength: n, horizon: 2 * n, parikhSupport: String(choose(n + d - 1, d - 1)) });
}
log({ phase: 'complete', outcome: 'all exact assertions passed', checkedPairs, checkedWords,
  anchors, stars, elapsedMs: Date.now() - started });
