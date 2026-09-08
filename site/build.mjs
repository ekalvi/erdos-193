#!/usr/bin/env node
// Dependency-free static includes. Run from any directory.
import { readFile, readdir, writeFile, rename } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const output = path.resolve(here, '../viz');
const args = process.argv.slice(2);
if (args.some(arg => arg !== '--check')) throw new Error('Usage: node site/build.mjs [--check]');
const check = args.includes('--check');
const pages = (await readdir(path.join(here, 'pages'))).filter(name => name.endsWith('.html')).sort();
const partials = new Map();
for (const name of await readdir(path.join(here, 'partials'))) {
  if (name.endsWith('.html')) partials.set(name.slice(0, -5), (await readFile(path.join(here, 'partials', name), 'utf8')).trimEnd());
}
const stale = [];
for (const page of pages) {
  const source = await readFile(path.join(here, 'pages', page), 'utf8');
  const rendered = source.replace(/\{\{ include ([a-z-]+) \}\}/g, (_, name) => {
    if (!partials.has(name)) throw new Error(`${page}: unknown partial ${name}`);
    return partials.get(name).replace(/\{\{ current ([a-z0-9]+) \}\}/g, (_, key) =>
      page === `${key}.html` ? ' class="cur" aria-current="page"' : '');
  });
  if (/\{\{ (?:include|current)\b/.test(rendered)) throw new Error(`${page}: unresolved template directive`);
  const target = path.join(output, page);
  const previous = await readFile(target, 'utf8').catch(error => {
    if (error.code === 'ENOENT') return null;
    throw error;
  });
  if (previous === rendered) continue;
  stale.push(page);
  if (!check) {
    // Atomic replacement; unchanged files are never touched. Reruns are idempotent.
    await writeFile(`${target}.tmp`, rendered);
    await rename(`${target}.tmp`, target);
  }
}
if (check && stale.length) {
  console.error(`Stale generated pages: ${stale.join(', ')}. Run node site/build.mjs`);
  process.exitCode = 1;
} else {
  console.log(check ? `All ${pages.length} generated pages are current.` : `Built ${pages.length} pages (${stale.length} changed).`);
}
