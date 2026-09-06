#!/usr/bin/env node
/** Exact arithmetic checks for D-SHALLIT-PROJECTION.md.
 * Fixed-size BigInt algebra, no dependencies, workers, prefix search, or writes.
 * This sub-second certificate verifier has no accumulated search/resume state.
 * The all-iterate obstruction is a written proof, not a finite power test.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';

const startedAt = new Date().toISOString();
const started = performance.now();
const codeSha = createHash('sha256').update(readFileSync(new URL(import.meta.url))).digest('hex');

// Polynomial coefficients are low degree first. All arithmetic is exact.
const trim = polynomial => {
  const result = [...polynomial];
  while (result.length > 1 && result.at(-1) === 0n) result.pop();
  return result;
};
const add = (a, b) => trim(Array.from({length: Math.max(a.length, b.length)},
  (_, i) => (a[i] ?? 0n) + (b[i] ?? 0n)));
const scale = (a, c) => trim(a.map(x => x * c));
const multiply = (a, b) => {
  const result = Array(a.length + b.length - 1).fill(0n);
  for (let i = 0; i < a.length; i++) {
    for (let j = 0; j < b.length; j++) result[i + j] += a[i] * b[j];
  }
  return trim(result);
};
const evaluate = (a, x) => a.reduceRight((value, coefficient) => value * x + coefficient, 0n);
const determinant = matrix => {
  if (matrix.length === 0) return [1n];
  let result = [0n];
  for (let j = 0; j < matrix.length; j++) {
    const minor = matrix.slice(1).map(row => row.filter((_, k) => k !== j));
    result = add(result, scale(multiply(matrix[0][j], determinant(minor)), j % 2 ? -1n : 1n));
  }
  return result;
};
const characteristic = matrix => determinant(matrix.map((row, i) => row.map((x, j) =>
  i === j ? [-x, 1n] : [-x])));
const transpose = matrix => matrix[0].map((_, j) => matrix.map(row => row[j]));
const matrixMultiply = (a, b) => a.map(row => b[0].map((_, j) =>
  row.reduce((sum, x, k) => sum + x * b[k][j], 0n)));
const identity = n => Array.from({length: n}, (_, i) =>
  Array.from({length: n}, (_, j) => i === j ? 1n : 0n));

// A few independent fixtures guard coefficient/sign conventions in the checker.
assert.deepEqual(multiply([-2n, 1n], [3n, 1n]), [-6n, 1n, 1n]);
assert.deepEqual(characteristic([[1n, 2n], [3n, 4n]]), [-2n, -5n, 1n]);
assert.deepEqual(characteristic(identity(3)), [-1n, 3n, -3n, 1n]);

// Reconstruct the incidence columns from Shallit's actual substitution, not
// from the saved algebra diagnostic or a pre-entered incidence matrix.
const image = [...'01213101314310'].map(Number);
const images = Array.from({length: 5}, (_, r) => image.map(letter => (letter + r) % 5));
const matrix = Array.from({length: 5}, (_, r) => images.map(word =>
  BigInt(word.filter(letter => letter === r).length)));
const counts = matrix.map(row => row[0]);
assert.deepEqual(counts, [3n, 6n, 1n, 3n, 1n]);
assert.equal(image.length, 14);
assert.equal(image[0], 0); // Prolongable fixed point.
assert.deepEqual([...new Set(image)].sort(), [0, 1, 2, 3, 4]);
assert.deepEqual(matrix, [
  [3n, 1n, 3n, 1n, 6n],
  [6n, 3n, 1n, 3n, 1n],
  [1n, 6n, 3n, 1n, 3n],
  [3n, 1n, 6n, 3n, 1n],
  [1n, 3n, 1n, 6n, 3n],
]);
for (const row of [...matrix, ...transpose(matrix)]) {
  assert.equal(row.reduce((sum, x) => sum + x, 0n), 14n);
}
// H = {sum u_r = 0}, with basis e_0-e_4, ..., e_3-e_4.
const hBasis = Array.from({length: 5}, (_, i) => Array.from({length: 4}, (_, j) =>
  i === 4 ? -1n : i === j ? 1n : 0n));
const hMatrix = matrix.slice(0, 4).map(row => row.slice(0, 4).map(x => x - row[4]));
assert.deepEqual(matrixMultiply(matrix, hBasis), matrixMultiply(hBasis, hMatrix));
const quartic = [421n, -51n, 31n, -1n, 1n];
assert.deepEqual(characteristic(hMatrix), quartic);
assert.deepEqual(characteristic(matrix), multiply([-14n, 1n], quartic));
assert.equal(determinant(matrix.map(row => row.map(x => [x])))[0], 14n * 421n);

// Work in Z[zeta] = Z[x]/Phi_5(x). Phi_5(x+1) is Eisenstein at 5.
const phi = [1n, 1n, 1n, 1n, 1n];
const substitute = (a, b) => a.reduceRight((value, coefficient) =>
  add(multiply(value, b), [coefficient]), [0n]);
assert.deepEqual(substitute(phi, [1n, 1n]), [5n, 10n, 10n, 5n, 1n]);
const reduce = polynomial => {
  const result = [...polynomial];
  for (let k = result.length - 1; k >= 4; k--) {
    const coefficient = result[k];
    for (let j = 0; j <= 4; j++) result[k - 4 + j] -= coefficient;
  }
  return Array.from({length: 4}, (_, i) => result[i] ?? 0n);
};
const ringMultiply = (a, b) => reduce(multiply(a, b));
const ringEvaluate = (a, x) => a.reduceRight((value, coefficient) =>
  reduce(add(ringMultiply(value, x), [coefficient])), [0n, 0n, 0n, 0n]);
const zeta = [0n, 1n, 0n, 0n];
const ringPower = (x, n) => {
  let result = [1n, 0n, 0n, 0n];
  for (let k = 0; k < n; k++) result = ringMultiply(result, x);
  return result;
};
assert.deepEqual(reduce(phi), [0n, 0n, 0n, 0n]);
assert.deepEqual(ringPower(zeta, 5), [1n, 0n, 0n, 0n]);
const conjugates = [1, 2, 3, 4].map(a => ringEvaluate(counts, ringPower(zeta, a)));
assert.deepEqual(conjugates[0], [2n, 5n, 0n, 2n]);
assert.deepEqual(conjugates.reduce(ringMultiply, [1n, 0n, 0n, 0n]), [421n, 0n, 0n, 0n]);
for (const alpha of conjugates) {
  assert.deepEqual(ringEvaluate(quartic, alpha), [0n, 0n, 0n, 0n]);
}
// Verify the rational-coordinate identification T(Mu) = alpha*T(u) on H.
const tMap = point => reduce(point);
for (let j = 0; j < 4; j++) {
  const basisVector = hBasis.map(row => row[j]);
  const imageVector = matrixMultiply(matrix, basisVector.map(x => [x])).map(row => row[0]);
  assert.deepEqual(tMap(imageVector), ringMultiply(conjugates[0], tMap(basisVector)));
}

// A single modular zero separates alpha^t from EVERY other Galois conjugate
// for EVERY t >= 1. No bounded list of powers is being used as a substitute.
const prime = 421n;
const mod = x => ((x % prime) + prime) % prime;
for (let divisor = 2n; divisor * divisor <= prime; divisor++) {
  assert.notEqual(prime % divisor, 0n, '421 must be prime');
}
const root = 279n;
assert.notEqual(root, 1n);
assert.equal(mod(root ** 5n), 1n);
assert.equal(mod(evaluate(phi, root)), 0n);
const residues = [1, 2, 3, 4].map(a => {
  const rootPower = mod(root ** BigInt(a));
  return {automorphism: a, root: rootPower, f_at_root: mod(evaluate(counts, rootPower))};
});
assert.equal(new Set(residues.map(row => row.root)).size, 4);
assert.equal(residues[0].f_at_root, 0n);
for (const row of residues.slice(1)) assert.notEqual(row.f_at_root, 0n);
// For any distinct conjugate labels, a Galois relabeling sends the first
// to the zero residue and the second to a nonzero residue.
let conjugatePairs = 0;
for (let a = 1; a <= 4; a++) {
  for (let b = a + 1; b <= 4; b++) {
    const inverse = [1, 2, 3, 4].find(c => a * c % 5 === 1);
    assert.equal(residues[a * inverse % 5 - 1].f_at_root, 0n);
    assert.notEqual(residues[b * inverse % 5 - 1].f_at_root, 0n);
    conjugatePairs++;
  }
}
assert.equal(conjugatePairs, 6);

// Expansivity needed to remove arbitrary bounded errors in a scaling law.
// An integer sum-of-squares identity is enough: M^T M = 11 I + 4 D^T D + 37 J,
// where (Dx)_r = x_{r+1}-x_r and J is the all-ones matrix.
const differences = Array.from({length: 5}, (_, r) => Array.from({length: 5}, (_, s) =>
  s === r ? -1n : s === (r + 1) % 5 ? 1n : 0n));
const differenceGram = matrixMultiply(transpose(differences), differences);
const gram = matrixMultiply(transpose(matrix), matrix);
assert.deepEqual(gram, differenceGram.map((row, i) => row.map((x, j) =>
  4n * x + 37n + (i === j ? 11n : 0n))));
// Also cross-check the previously recorded exact singular-value polynomial.
// beta = |alpha|^2 has polynomial t^2 - 42t + 421.
const betaPolynomial = [421n, -42n, 1n];
for (let a = 1; a <= 4; a++) {
  const beta = ringMultiply(conjugates[a - 1], conjugates[5 - a - 1]);
  assert.deepEqual(ringEvaluate(betaPolynomial, beta), [0n, 0n, 0n, 0n]);
}
assert.deepEqual(gram, matrixMultiply(matrix, transpose(matrix))); // Normal.
assert.deepEqual(characteristic(gram),
  multiply([-196n, 1n], multiply(betaPolynomial, betaPolynomial)));

const result = {
  status: 'pass',
  started_at: startedAt,
  completed_at: new Date().toISOString(),
  code_sha256: codeSha,
  workers: 1,
  image0: image.join(''),
  incidence_matrix: matrix,
  deviation_characteristic_low_to_high: quartic,
  cyclotomic_norm: 421n,
  separating_prime: prime,
  conjugate_residues: residues,
  conjugate_pairs: conjugatePairs,
  gram_sum_of_squares: {identity: 11, cyclic_difference_gram: 4, all_ones: 37},
  gram_characteristic_low_to_high: characteristic(gram),
  elapsed_seconds: (performance.now() - started) / 1000,
  scope: 'Exact arithmetic certificate checks only. The all-iterate, bounded-error rational-projection obstruction is proved in D-SHALLIT-PROJECTION.md; no general projection or five-step impossibility claim.',
};
// Decimal strings keep the machine-readable certificate lossless.
console.log(JSON.stringify(result, (_, value) => typeof value === 'bigint' ? value.toString() : value));
