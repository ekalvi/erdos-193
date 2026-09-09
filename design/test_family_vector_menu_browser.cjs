// PLAYWRIGHT_MODULE=/path/to/playwright node design/test_family_vector_menu_browser.cjs
// Ephemeral loopback server; no deployment, generated artifacts, or persistent service.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://localhost').pathname;
  const base = pathname.startsWith('/family/') ? 'results' : 'viz';
  const relative = pathname.replace(base === 'results' ? /^\/family\// : /^\//, '') || 'index.html';
  const file = path.resolve(root, base, relative);
  if (!file.startsWith(path.join(root, base) + path.sep)) { res.writeHead(403).end(); return; }
  fs.readFile(file, (error, data) => {
    if (error) { res.writeHead(404).end(); return; }
    const mime = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png'};
    res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
    res.end(data);
  });
});
(async () => {
  let browser;
  try {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const base = `http://127.0.0.1:${server.address().port}`;
    browser = await chromium.launch({headless: true, args: ['--no-sandbox', '--renderer-process-limit=2', '--enable-unsafe-swiftshader']});
    const page = await browser.newPage({viewport: {width: 1280, height: 900}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('https://fonts.googleapis.com/**', route => route.abort());
    for (const rule of [85, 170, 0, 256]) {
      await page.goto(`${base}/family/?rule=${rule}#vector-menu`);
      const expected = [85, 170].includes(rule) ? 6 : 14;
      assert.equal(await page.locator('#vectorMenuRows .vector-menu-item').count(), expected);
      assert.equal(await page.locator('#alternatingNotice').isVisible(), expected === 6);
      assert.match(await page.locator('#vectorPermalink').getAttribute('href'), new RegExp(`\\?rule=${rule}#vector-menu$`));
      assert.match(await page.title(), new RegExp(`^g${rule} · ${expected}`));
    }
    // Changing the existing rule input must update the menu without a reload.
    await page.locator('#ruleNumber').fill('85');
    await page.locator('#ruleNumber').press('Tab');
    assert.equal(await page.locator('#vectorMenuRows .vector-menu-item').count(), 6);
    const before = await page.locator('#vectorMenuRows').innerText();
    await page.locator('#increaseDepth').click();
    assert.equal(await page.locator('#vectorMenuRows').innerText(), before);
    await page.locator('#lift3d').click();
    await page.waitForFunction(() => document.querySelector('#lift3d').classList.contains('showing-3d'));
    assert.ok(await page.locator('#liftCanvas').isVisible());
    await page.setViewportSize({width: 390, height: 844});
    await page.goto(`${base}/family/?rule=170#vector-menu`);
    assert.equal(await page.locator('#vectorMenuRows .vector-menu-item').count(), 6);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'mobile horizontal overflow');
    await page.goto(base);
    await page.locator('a[href="family/?rule=85#vector-menu"]').first().click();
    assert.equal(await page.locator('#vectorMenuRows .vector-menu-item').count(), 6);
    await page.goto(`${base}/progress.html#six-vector-family`);
    assert.ok(await page.locator('#six-vector-family').isVisible());
    assert.deepEqual(errors, []);
    console.log('PASS: deep links, rule changes, depth independence, 3D toggle, mobile layout, homepage and timeline; no browser errors.');
  } finally {
    if (browser) await browser.close();
    server.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
