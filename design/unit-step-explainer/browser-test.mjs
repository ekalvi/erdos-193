// No server is started: Playwright intercepts a synthetic origin with local files.
// Usage: PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs node browser-test.mjs
import assert from 'node:assert/strict';
import {readFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=new URL('./',import.meta.url);
const browser=await chromium.launch({args:['--renderer-process-limit=1','--disable-gpu']});
const errors=[];
try {
  const page=await browser.newPage({viewport:{width:1280,height:1000},deviceScaleFactor:1});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
    const url=new URL(route.request().url());
    if(url.origin!=='https://explainer.test')throw Error('Unexpected external request');
    const name=url.pathname==='/'?'index.html':url.pathname.slice(1);
    if(!['index.html','app.mjs','model.mjs'].includes(name)){await route.fulfill({status:404,body:''});return;}
    await route.fulfill({contentType:name.endsWith('html')?'text/html':'text/javascript',body:await readFile(new URL(name,root))});
  });
  await page.goto('https://explainer.test/');
  await page.waitForFunction(()=>document.getElementById('basisReadout').textContent.includes('sum = 69'));
  assert.ok((await page.locator('#mergeResult').innerText()).includes('(3, 2, 2, 3, 4)'));
  assert.ok((await page.locator('#tripleResult').innerText()).includes('Not collinear'));
  await page.locator('#next').click();assert.equal(await page.locator('#position').inputValue(),'70');
  await page.locator('#reset').click();assert.ok((await page.locator('#stepReadout').innerText()).includes('origin'));
  await page.locator('#play').click();await page.waitForTimeout(350);await page.locator('#play').click();
  assert.ok(Number(await page.locator('#position').inputValue())>0);
  await page.locator('#a').fill('99');await page.locator('#b').fill('5');await page.locator('#check').click();
  assert.ok((await page.locator('#tripleResult').innerText()).includes('Choose'));
  await page.locator('#merger').selectOption('0');assert.ok((await page.locator('#mergeResult').innerText()).includes('vertices 3, 4, 5'));
  await page.locator('#position').fill('1023');await page.locator('#position').dispatchEvent('input');
  assert.ok((await page.locator('#basisReadout').innerText()).includes('sum = 1023'));
  await page.locator('#merger').selectOption('14');
  const screenshots=new URL('../../.checkpoint-unit-step-explainer/',root);await mkdir(screenshots,{recursive:true});
  await page.screenshot({path:fileURLToPath(new URL('desktop.png',screenshots)),fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(200);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  await page.screenshot({path:fileURLToPath(new URL('mobile.png',screenshots)),fullPage:true});
  await page.unroute('**/*');
  await page.goto(new URL('standalone.html',root).href);
  await page.waitForFunction(()=>document.getElementById('basisReadout').textContent.includes('sum = 69'));
  await page.locator('#next').click();
  assert.equal(await page.locator('#position').inputValue(),'70');
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'pass',desktop:true,mobile:true,controls:true,offlineFile:true,pageErrors:errors,network:'intercepted or file; no server or hosted URL'}));
} finally {await browser.close();}
