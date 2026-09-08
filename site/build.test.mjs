import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, cp, mkdir, readFile, writeFile, rm, readdir, rename } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const run = (dir, ...args) => spawnSync(process.execPath, [path.join(dir, 'site/build.mjs'), ...args], { encoding: 'utf8' });

test('generated pages are current, have shared metadata, and retain page-specific navigation', async () => {
  const result = run(root, '--check');
  assert.equal(result.status, 0, result.stderr);
  const pages = (await readdir(path.join(here, 'pages'))).filter(name => name.endsWith('.html'));
  assert.equal(pages.length, 8);
  for (const page of pages) {
    const html = await readFile(path.join(root, 'viz', page), 'utf8');
    assert.equal((html.match(/<meta charset=/g) || []).length, 1, page);
    assert.equal((html.match(/<meta name="viewport"/g) || []).length, 1, page);
    assert.equal((html.match(/<title>/g) || []).length, 1, page);
    assert(!html.includes('{{ include '), page);
    for (const icon of ['favicon.ico', 'favicon.png', 'favicon.svg', 'apple-touch-icon.png']) {
      assert(html.includes(`href="${icon}"`), page);
      await readFile(path.join(root, 'viz', icon));
    }
    if (page.startsWith('unit-step-')) {
      assert(html.includes('content="noindex,nofollow"'), page);
      assert(!html.includes('aria-label="Main navigation"'), page);
    } else {
      assert(html.includes('aria-label="Main navigation"'), page);
      const active = [...html.matchAll(/<a class="cur" aria-current="page" href="([^"]+)"/g)];
      assert.equal(active.length, page === 'learn.html' ? 0 : 1, page);
      if (active.length) assert.equal(active[0][1], page === 'index.html' ? '/' : page);
    }
  }
});

test('build detects drift, propagates shared edits, is idempotent, and rejects unknown includes', async () => {
  const dir = await mkdtemp(path.join(tmpdir(), 'erdos-site-test-'));
  try {
    await cp(here, path.join(dir, 'site'), { recursive: true });
    await mkdir(path.join(dir, 'viz'));
    assert.equal(run(dir, '--check').status, 1);
    assert.equal(run(dir).status, 0);
    assert.equal(run(dir, '--check').status, 0);
    assert.match(run(dir).stdout, /0 changed/);
    const partial = path.join(dir, 'site/partials/icons.html');
    await writeFile(partial, (await readFile(partial, 'utf8')) + '<!-- shared edit -->\n');
    const stale = run(dir, '--check');
    assert.equal(stale.status, 1);
    assert.match(stale.stderr, /index.html/);
    assert.equal(run(dir).status, 0);
    for (const page of await readdir(path.join(dir, 'viz'))) {
      assert((await readFile(path.join(dir, 'viz', page), 'utf8')).includes('<!-- shared edit -->'));
    }
    const page = path.join(dir, 'site/pages/index.html');
    await writeFile(page, '{{ include missing }}');
    assert.match(run(dir).stderr, /unknown partial missing/);
    await writeFile(page, '{{ include invalid/path }}');
    assert.match(run(dir).stderr, /unresolved template directive/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('deleted and renamed templates remove only owned outputs, even when every template is deleted', async () => {
  const dir = await mkdtemp(path.join(tmpdir(), 'erdos-site-orphans-'));
  try {
    await cp(here, path.join(dir, 'site'), { recursive: true });
    await mkdir(path.join(dir, 'viz'));
    assert.equal(run(dir).status, 0);
    const unmanaged = '<!doctype html><title>Hand-authored page</title>';
    await writeFile(path.join(dir, 'viz/manual.html'), unmanaged);
    await rm(path.join(dir, 'site/pages/demo.html'));
    await rename(path.join(dir, 'site/pages/learn.html'), path.join(dir, 'site/pages/guide.html'));
    const before = await readFile(path.join(dir, 'viz/demo.html'), 'utf8');
    const check = run(dir, '--check');
    assert.equal(check.status, 1);
    assert.match(check.stderr, /Orphaned generated pages: demo.html, learn.html/);
    assert.equal(await readFile(path.join(dir, 'viz/demo.html'), 'utf8'), before, '--check must not delete');
    assert.match(run(dir).stdout, /2 removed/);
    const outputs = await readdir(path.join(dir, 'viz'));
    assert(!outputs.includes('demo.html'));
    assert(!outputs.includes('learn.html'));
    assert(outputs.includes('guide.html'));
    assert.equal(await readFile(path.join(dir, 'viz/manual.html'), 'utf8'), unmanaged);
    assert.equal(run(dir, '--check').status, 0);
    assert.match(run(dir).stdout, /0 changed, 0 removed/);
    for (const page of await readdir(path.join(dir, 'site/pages'))) {
      await rm(path.join(dir, 'site/pages', page));
    }
    assert.equal(run(dir, '--check').status, 1);
    assert.match(run(dir).stdout, /7 removed/);
    assert.deepEqual(await readdir(path.join(dir, 'viz')), ['manual.html']);
    assert.equal(run(dir, '--check').status, 0);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
