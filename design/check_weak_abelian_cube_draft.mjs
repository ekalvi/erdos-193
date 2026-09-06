#!/usr/bin/env node
/** Bounded independent checks of the Shallit-supplied cube draft, not an infinite proof.
 * Run without arguments to recompute and verify the tracked result.
 * --write atomically replaces the result after all checks pass. No server or network.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile, writeFile, rename, mkdir} from 'node:fs/promises';

const root = new URL('../', import.meta.url);
const digest = data => createHash('sha256').update(data).digest('hex');
const args = process.argv.slice(2);
if (args.includes('--help')) {
  console.log('Usage: node design/check_weak_abelian_cube_draft.mjs [--write]\n'
    + 'Recompute bounded checks and compare with the tracked result. --write atomically updates it.\n'
    + 'Single core, fixed small workload, idempotent complete result; no infinite-proof claim.');
  process.exit(0);
}
assert(args.length === 0 || (args.length === 1 && args[0] === '--write'), 'unknown arguments');
const pdf = 'paper/followups/2026-09-06-shallit-weak-abelian-cubes.pdf';
const identity = {
  schema: 1,
  code_sha256: digest(await readFile(new URL(import.meta.url))),
  pdf_sha256: digest(await readFile(new URL(pdf, root))),
  ternary_depth: 8,
  auxiliary_depth: 7,
  pair_vertices: 729,
};
const tau = {A: 'AB', B: 'AACA', C: 'ADE', D: 'AACCE', E: 'ADCCA'};
const sigma = ['010', '232', '101', '323'];
const returns = {A: '01', B: '0232', C: '013231', D: '02323231', E: '01323232'};
const coding = {A: '0', B: '1', C: '2', D: '3', E: '3'};
const expectedVectors = {A: [2, 0, 2], B: [-2, 2, 4], C: [0, -2, 6], D: [-4, 0, 8], E: [-4, 0, 8]};
const substitute = (word, morphism) => [...word].map(c => morphism[c]).join('');
const table = [];
for (const a of Object.keys(tau)) {
  assert.equal(substitute(returns[a], sigma), substitute(tau[a], returns), `intertwining at ${a}`);
  const counts = [0, 0, 0, 0];
  for (const c of returns[a]) counts[+c]++;
  assert.equal(returns[a][0], '0');
  assert.equal(counts[0], 1);
  const [p, q, r, s] = counts;
  const displacement = [p + q - r - s, p - q + r - s, returns[a].length];
  assert.deepEqual(displacement, expectedVectors[a]);
  table.push({auxiliary: a, output: coding[a], return_word: returns[a], counts, displacement});
}
assert.deepEqual(expectedVectors.D, expectedVectors.E);
let t = '0';
for (let k = 0; k < identity.ternary_depth; k++) t = substitute(t, sigma);
let auxiliary = 'A';
for (let k = 0; k < identity.auxiliary_depth; k++) auxiliary = substitute(auxiliary, tau);
const expanded = substitute(auxiliary, returns);
const commonLength = Math.min(t.length, expanded.length);
assert.equal(expanded.slice(0, commonLength), t.slice(0, commonLength));
const word = substitute(auxiliary, coding);
assert(word.startsWith('0100200101033010100200100200100223'));

const a = [...t].map(c => +c < 2 ? 1 : -1);
const b = [...t].map(c => +c % 2 === 0 ? 1 : -1);
const X = [0], Y = [0];
for (let n = 0; n < t.length; n++) {
  X.push(X.at(-1) + a[n]);
  Y.push(Y.at(-1) + b[n]);
}
for (let n = 0; 3 * n + 2 < t.length; n++) {
  for (let r = 0; r < 3; r++) {
    assert.equal(a[3 * n + r], b[n]);
    assert.equal(b[3 * n + r], (r === 1 ? -1 : 1) * a[n]);
    assert.equal(X[3 * n + r], 3 * Y[n] + r * b[n]);
    assert.equal(Y[3 * n + r], X[n] + (r === 1 ? a[n] : 0));
  }
}
const valuation = n => {
  assert(Number.isSafeInteger(n) && n !== 0, 'nonzero exact integer required');
  let e = 0;
  while (n % 3 === 0) { n /= 3; e++; }
  return e;
};
let pairs = 0;
for (let m = 0; m < identity.pair_vertices; m++) {
  for (let n = m + 1; n < identity.pair_vertices; n++) {
    if (t[m] !== t[n]) continue;
    const form = (X[n] - X[m]) ** 2 - 3 * (Y[n] - Y[m]) ** 2;
    assert.equal(valuation(form), valuation(n - m));
    pairs++;
  }
}
assert.equal(pairs, 66248);
// This is a counterexample to TRIPLE avoidance, not to the cube draft's claim.
assert.equal(word.slice(2, 4), '00');
const prefixPoint = n => [0, 1, 2, 3].map(c => [...word.slice(0, n)].filter(x => +x === c).length);
const triple = [2, 3, 4].map(prefixPoint);
for (let c = 0; c < 4; c++) assert.equal(triple[0][c] + triple[2][c], 2 * triple[1][c]);

const result = {
  identity,
  status: 'finite_checks_pass',
  substitution_identities_checked: 5,
  return_table: table,
  source_vertices: t.length,
  common_expansion_letters_checked: commonLength,
  equal_state_pairs_checked: pairs,
  coded_prefix: word.slice(0, 64),
  triple_avoidance_counterexample: {indices: [2, 3, 4], vertices: triple, factor: '00'},
  scope: 'Exact finite identities and prefix checks supporting the written cube argument; not an infinite proof, novelty claim, or solution to triple avoidance.',
};
const output = new URL('research/unit-step/checks/weak-abelian-cube.json', root);
if (args.includes('--write')) {
  await mkdir(new URL('.', output), {recursive: true});
  const temporary = new URL(output.href + '.tmp');
  await writeFile(temporary, JSON.stringify(result, null, 2) + '\n');
  await rename(temporary, output);
} else {
  assert.deepEqual(result, JSON.parse(await readFile(output, 'utf8')), 'tracked result differs; inspect before --write');
}
console.log(JSON.stringify({status: 'pass', equal_state_pairs: pairs, scope: result.scope}));
