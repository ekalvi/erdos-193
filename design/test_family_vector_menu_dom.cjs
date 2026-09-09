// JSDOM_MODULE=/path/to/jsdom node design/test_family_vector_menu_dom.cjs
const {JSDOM} = require(process.env.JSDOM_MODULE || 'jsdom');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const read = name => fs.readFileSync(path.join(__dirname, '..', name), 'utf8');
const html = read('results/index.html');
const script = read('results/vector-menu.js');
for (const initialRule of [85, 170, 0, 256]) {
  const dom = new JSDOM(html, {url: `https://erdos-193.q5m.ai/family/?rule=${initialRule}&sheet=2#vector-menu`, runScripts: 'outside-only'});
  const {window} = dom;
  const {document} = window;
  const pattern = rule => rule === 256 ? '+++++++++' : rule.toString(2).padStart(8, '0').replaceAll('0', '+').replaceAll('1', '-');
  window.signedGaussianCurrentRule = {rule: String(initialRule), pattern: pattern(initialRule)};
  window.eval(script);
  for (const rule of [initialRule, 170, 85, 0]) {
    window.dispatchEvent(new window.CustomEvent('signed-gaussian-rule-change', {detail: {rule: String(rule), pattern: pattern(rule)}}));
    const count = [85, 170].includes(rule) ? 6 : 14;
    assert.equal(document.querySelectorAll('#vectorMenuRows .vector-menu-item').length, count);
    assert.equal(document.querySelector('#vectorMenuCount').textContent, String(count));
    assert.match(document.querySelector('#vectorMenuMin').textContent, /^\d+\.\d{2}$/);
    assert.match(document.querySelector('#vectorMenuMax').textContent, /^\d+\.\d{2}$/);
    assert.equal(document.querySelector('#alternatingNotice').hidden, count !== 6);
    assert.equal(document.querySelector('#vectorPermalink').href, `https://erdos-193.q5m.ai/family/?rule=${rule}#vector-menu`);
    assert.match(document.title, new RegExp(`^g${rule} · ${count}`));
    assert.match(document.querySelector('#vectorMenuRows').textContent, /0 →/);
  }
  for (const link of document.querySelectorAll('a[href*="#"]')) {
    const url = new URL(link.href);
    if (url.pathname === '/family/') assert.ok(document.querySelector(url.hash), `missing anchor ${url.hash}`);
  }
  window.close();
}
for (const name of ['viz/index.html', 'viz/progress.html']) {
  const dom = new JSDOM(read(name));
  assert.ok(dom.window.document.querySelector('a[href="family/?rule=85#vector-menu"]'));
  dom.window.close();
}
console.log('PASS: initial deep-link rendering, rule-change events, exact menu links, notices, titles, anchors, homepage and timeline links.');
