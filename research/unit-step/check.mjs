#!/usr/bin/env node
/** Offline integrity/link/visibility check for the research checkpoint. No network. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {readFile, lstat} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
const digest = data => createHash('sha256').update(data).digest('hex');
const safe = relative => {
  assert(!path.isAbsolute(relative));
  const full = path.resolve(root, relative);
  assert(full.startsWith(root), `outside repository: ${relative}`);
  return full;
};
const read = relative => readFile(safe(relative));
const catalogue = JSON.parse(await read('research/unit-step/artifacts.json'));
assert.equal(catalogue.schema, 1);
assert.equal(catalogue.text_extractor, 'pypdf==6.17.0');
assert.equal(new Set(catalogue.pdfs.map(row => row.id)).size, catalogue.pdfs.length);
const covered = new Set();
for (const row of catalogue.pdfs) {
  for (const field of ['title', 'attribution', 'status', 'text_path']) assert(row[field]?.length, `${row.id}: ${field}`);
  assert(row.source?.kind);
  assert(/^[a-f0-9]{64}$/.test(row.sha256));
  assert(/^[a-f0-9]{64}$/.test(row.text_sha256));
  assert(Number.isInteger(row.pdf_pages) && row.pdf_pages > 0);
  const pdf = await read(row.path);
  assert.equal(pdf.subarray(0, 5).toString(), '%PDF-');
  assert(pdf.subarray(-1024).includes(Buffer.from('%%EOF')));
  assert.equal(digest(pdf), row.sha256, row.path);
  assert.equal(pdf.length, row.pdf_bytes, row.path);
  for (const relative of [row.path, ...(row.aliases ?? [])]) {
    assert(!covered.has(relative), `duplicate PDF: ${relative}`);
    assert((await lstat(safe(relative))).isFile(), relative);
    assert.equal(digest(await read(relative)), row.sha256, relative);
    covered.add(relative);
  }
  const text = await read(row.text_path);
  assert.equal(digest(text), row.text_sha256, row.text_path);
  assert(!/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(text.toString()), `binary controls in ${row.text_path}`);
  assert.equal((text.toString().match(/^=== Page \d+ ===$/gm) ?? []).length, row.pdf_pages);
  for (const relative of [...row.editable_sources, ...(row.dependencies ?? [])]) {
    assert((await lstat(safe(relative))).isFile(), relative);
  }
}
const gitPdfs = execFileSync('git', ['ls-files', '--cached', '--others', '--exclude-standard', '-z', '--', '*.pdf'], {cwd: root})
  .toString().split('\0').filter(Boolean);
assert.deepEqual([...new Set(gitPdfs)].sort(), [...covered].sort(), 'all repository PDFs must be indexed');

const docs = ['README.md', 'paper/followups/README.md',
  'research/unit-step/AI-CHECKPOINT.md', 'research/unit-step/PROBLEM.md', 'research/unit-step/FRAMEWORK.md',
  'design/WEAK-ABELIAN-CUBE-DRAFT-REVIEW.md', 'design/unit-step-explainer/README.md'];
let links = 0;
for (const doc of docs) {
  const markdown = (await read(doc)).toString();
  for (const match of markdown.matchAll(/\]\(([^\s)]+)\)/g)) {
    const target = match[1].split('#')[0];
    if (!target || /^[a-z]+:/i.test(target)) continue;
    const relative = path.posix.normalize(path.posix.join(path.posix.dirname(doc), decodeURIComponent(target)));
    assert((await lstat(safe(relative))).isFile(), `${doc} -> ${target}`);
    links++;
  }
}
const excludedEvidence = ['results/unit-step-dimension-probe.json',
  'results/shallit-five-prefix.json', 'results/shallit-substitution-algebra.json'];
const dockerignore = (await read('.dockerignore')).toString().split('\n');
for (const name of excludedEvidence) {
  assert(dockerignore.lastIndexOf(name) > dockerignore.lastIndexOf('!results/**'), `research data exposed: ${name}`);
}
const dockerfile = (await read('q5m/Dockerfile')).toString();
assert(!/^COPY[^\n]*(?:paper\/|research\/|design\/)/m.test(dockerfile));
const manifest = (await read('q5m.yaml')).toString();
assert(!/^production:/m.test(manifest), 'preview must not declare production');
assert(manifest.includes('root: design/unit-step-explainer/public'));
assert.deepEqual(await read('design/unit-step-explainer/standalone.html'),
  await read('design/unit-step-explainer/public/index.html'));
const prefix = JSON.parse(await read('results/shallit-five-prefix.json'));
assert.equal(prefix.code_sha256, digest(await read('design/verify_unit_step_prefix.cpp')));
assert.equal(prefix.status, 'finite_prefix_pass');
assert.equal(prefix.steps, 38416);
assert.equal(prefix.vertices, 38417);
assert.equal(prefix.chords_checked, 737913736);
const periodic = JSON.parse(await read('research/unit-step/checks/signed-gaussian-period-16.json'));
assert.equal(periodic.code_sha256, digest(await read('design/signed_gaussian_unit_step_audit.py')));
assert.equal(periodic.period, 16);
assert.equal(periodic.patterns_checked, 65536);
assert.deepEqual(periodic.step_count_histogram, {'6': 2, '10': 508, '14': 65026});
assert.deepEqual(periodic.minimizers.map(row => row.index), [21845, 43690]);
console.log(JSON.stringify({status: 'pass', pdf_files: covered.size, distinct_pdf_artifacts: catalogue.pdfs.length,
  local_links: links, research_only_jsons: excludedEvidence.length,
  scope: 'Archive integrity, provenance coverage, and visibility checks; not mathematical proof certification.'}));
