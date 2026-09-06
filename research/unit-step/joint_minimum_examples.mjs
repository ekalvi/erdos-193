#!/usr/bin/env node
/** Bounded, deterministic BigInt checks of the joint-minimum note's finite examples.
 * No network, workers, search checkpoint, or generated proof artifact. This is a
 * seconds-scale test, not an infinite existence or impossibility certification.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';

const started = performance.now();
const codeSha = createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex');
const sub = (u, v) => u.map((x, i) => x - v[i]);
const dot = (u, v) => u.reduce((sum, x, i) => sum + x * v[i], 0n);
const apply = (matrix, point) => matrix.map(row => dot(row, point));
const rankTwo = (u, v) => {
  for (let r = 0; r < u.length; r++) {
    for (let s = r + 1; s < u.length; s++) {
      if (u[r] * v[s] !== u[s] * v[r]) return true;
    }
  }
  return false;
};
const tripleFree = points => {
  for (let i = 0; i < points.length; i++) {
    for (let j = i + 1; j < points.length; j++) {
      for (let k = j + 1; k < points.length; k++) {
        if (!rankTwo(sub(points[j], points[i]), sub(points[k], points[j]))) return false;
      }
    }
  }
  return true;
};
const counts = (word, dimension) => {
  const points = [Array(dimension).fill(0n)];
  for (const letter of word) {
    const next = [...points.at(-1)];
    next[letter]++;
    points.push(next);
  }
  return points;
};

// Generic height is not time: the time-weighted test can miss collinearity.
const triangle = counts([0, 1], 2);
const variableHeight = [[1n, 2n], [0n, 0n], [1n, 2n]];
const image = triangle.map(point => apply(variableHeight, point));
assert(tripleFree(triangle));
assert.deepEqual(image, [[0n, 0n, 0n], [1n, 0n, 1n], [3n, 0n, 3n]]);
assert(!tripleFree(image));
const u = sub(triangle[1], triangle[0]);
const v = sub(triangle[2], triangle[1]);
assert(apply(variableHeight, sub(u, v)).some(x => x !== 0n));
// Collapsing vertices also fails the rank condition.
assert(!tripleFree([[0n, 0n, 0n], [0n, 0n, 0n], [1n, 0n, 0n]]));

// Every word up to six letters over four labels. The base depends on N.
// The map preserves both avoidance and every pre-existing collinear triple.
const alphabet = 4;
let wordsChecked = 0;
let avoidingWords = 0;
let clockTriples = 0;
for (let n = 1; n <= 6; n++) {
  const bound = BigInt(n) ** 2n;
  const base = bound + 2n;
  const matrix = [Array.from({length: alphabet}, (_, r) => base ** BigInt(r)),
    Array(alphabet).fill(0n), Array(alphabet).fill(1n)];
  for (let code = 0; code < alphabet ** n; code++) {
    let remaining = code;
    const word = Array.from({length: n}, () => {
      const letter = remaining % alphabet;
      remaining = Math.floor(remaining / alphabet);
      return letter;
    });
    const source = counts(word, alphabet);
    const projected = source.map(point => apply(matrix, point));
    const free = tripleFree(source);
    assert.equal(tripleFree(projected), free, `finite projection: ${word}`);
    wordsChecked++;
    if (free) avoidingWords++;
    for (let i = 0; i < source.length; i++) {
      for (let j = i + 1; j < source.length; j++) {
        for (let k = j + 1; k < source.length; k++) {
          const left = sub(source[j], source[i]);
          const right = sub(source[k], source[j]);
          const a = BigInt(j - i), b = BigInt(k - j);
          const d = left.map((x, r) => b * x - a * right[r]);
          assert.equal(d.reduce((sum, x) => sum + x, 0n), 0n);
          assert(d.every(x => -bound <= x && x <= bound));
          const projectedD = apply(matrix, d);
          assert.equal(rankTwo(apply(matrix, left), apply(matrix, right)),
            projectedD.some(x => x !== 0n), `clock criterion: ${word}`);
          clockTriples++;
        }
      }
    }
  }
}
assert.equal(wordsChecked, 5460);
assert.equal(clockTriples, 166672);
assert(avoidingWords > 0);
console.log(JSON.stringify({status: 'pass', code_sha256: codeSha, alphabet,
  maximum_steps: 6, words_checked: wordsChecked, avoiding_words: avoidingWords,
  clock_triples_checked: clockTriples, elapsed_seconds: (performance.now() - started) / 1000,
  scope: 'Finite projection and rank-test illustrations only; no infinite theorem certification.'}));
