#!/usr/bin/env node
/** Single-core operational tests. Each small test is atomically checkpointed;
 * restart reuses completed tests. Signals stop after the current test, forwarding
 * to an asynchronous child. No checkpoints or logs are final proof artifacts.
 */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn, spawnSync } from 'node:child_process';

const here = path.dirname(fileURLToPath(import.meta.url));
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const digest = value => hash(JSON.stringify(value));
const identity = Object.fromEntries(['boundary.mjs', 'check.mjs', 'test.mjs', 'README.md',
  '../../../../viz/progress.html', 'checks/ratio-1-1.json', 'checks/ratio-1-2.json', 'checks/ratio-2-1.json']
  .map(name => [name, hash(fs.readFileSync(path.join(here, name)))]));
const dir = `.checkpoint-shallit-boundary-tests-${digest(identity).slice(0, 16)}`;
const checkpoint = path.join(dir, 'state.json');
fs.mkdirSync(dir, { recursive: true });
const atomic = (file, data) => {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temp = `${file}.tmp-${process.pid}`;
  fs.writeFileSync(temp, `${JSON.stringify(data, null, 2)}\n`); fs.renameSync(temp, file);
};
const log = (event, fields = {}) => {
  const row = { time: new Date().toISOString(), event, ...fields };
  fs.appendFileSync(path.join(dir, 'run.jsonl'), `${JSON.stringify(row)}\n`);
  console.log(JSON.stringify(row));
};
const expected = fs.readFileSync(path.join(here, 'checks/ratio-1-1.json'));
const args = name => [path.join(here, 'boundary.mjs'), '--p', '1', '--q', '1',
  '--state-dir', path.join(dir, name), '--output', path.join(dir, name, 'result.json')];
const run = (name, extra = []) => spawnSync(process.execPath, [...args(name), ...extra],
  { encoding: 'utf8', timeout: 10000, env: { ...process.env, UV_THREADPOOL_SIZE: '1' } });
const compare = name => assert.deepEqual(fs.readFileSync(path.join(dir, name, 'result.json')), expected);
let activeChild, stopped = false;
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => { stopped = true; activeChild?.kill(sig); });

const tasks = {
  help: () => {
    const result = spawnSync(process.execPath, [path.join(here, 'boundary.mjs'), '--help'], { encoding: 'utf8', timeout: 10000 });
    assert.equal(result.status, 0); assert.match(result.stdout, /resume/);
  },
  documentation_scope: () => {
    const markdown = fs.readFileSync(path.join(here, 'README.md'), 'utf8');
    for (const match of markdown.matchAll(/\]\(([^\s)]+)\)/g)) {
      const target = match[1].split('#')[0];
      if (target && !/^[a-z]+:/i.test(target)) assert(fs.statSync(path.resolve(here, target)).isFile(), target);
    }
    for (const [p, q] of [[1, 1], [1, 2], [2, 1]]) {
      const data = JSON.parse(fs.readFileSync(path.join(here, `checks/ratio-${p}-${q}.json`)));
      assert(markdown.includes(`| ${p}:${q} | ${data.states.length} | ${data.transitions} |`), 'stale result table');
    }
    const viz = fs.readFileSync(path.resolve(here, '../../../../viz/progress.html'), 'utf8');
    assert(viz.includes('ratios <b>1:1, 1:2, and 2:1</b> at every scale'));
    assert(viz.includes('Full weak abelian-square avoidance remains open'));
    assert(viz.includes('research/unit-step/tracks/shallit-five/README.md'));
  },
  bounded_stop_resume_idempotence: () => {
    const target = path.join(dir, 'bounded');
    if (!fs.existsSync(path.join(target, 'state.json'))) {
      const first = run('bounded', ['--max-states', '125']);
      assert.equal(first.status, 2, first.stderr);
      assert(!fs.existsSync(path.join(target, 'result.json')));
      const partial = JSON.parse(fs.readFileSync(path.join(target, 'state.json'))).payload;
      assert(partial.completed > 0 && partial.completed < partial.nodes.length);
    }
    for (let i = 0; i < 2; i++) {
      const result = run('bounded'); assert.equal(result.status, 0, result.stderr); compare('bounded');
    }
    assert.match(fs.readFileSync(path.join(target, 'run.jsonl'), 'utf8'), /bounded_stop/);
  },
  time_boundary: () => {
    const first = run('time', ['--max-seconds', '0.000000001']);
    assert.equal(first.status, 2, first.stderr);
    assert(!fs.existsSync(path.join(dir, 'time', 'result.json')));
    assert.equal(JSON.parse(fs.readFileSync(path.join(dir, 'time', 'state.json'))).payload.completed, 0);
  },
  checkpoint_rejections: () => {
    const original = JSON.parse(fs.readFileSync(path.join(dir, 'bounded', 'state.json')));
    const corrupt = structuredClone(original); corrupt.sha256 = '0'.repeat(64);
    atomic(path.join(dir, 'corrupt', 'state.json'), corrupt);
    const bad = run('corrupt'); assert.notEqual(bad.status, 0); assert.match(bad.stderr, /corrupt checkpoint/);
    const incompatible = structuredClone(original); incompatible.payload.identity.p = 2;
    incompatible.sha256 = digest(incompatible.payload);
    atomic(path.join(dir, 'incompatible', 'state.json'), incompatible);
    const wrong = run('incompatible'); assert.notEqual(wrong.status, 0); assert.match(wrong.stderr, /incompatible checkpoint/);
  },
  signal_resume: async () => {
    const target = path.join(dir, 'signal'), events = path.join(target, 'run.jsonl');
    let prior = fs.existsSync(events) ? fs.readFileSync(events, 'utf8') : '';
    if (!prior.includes('"event":"interrupted"')) {
      // Only this unfinished, isolated test unit may need restarting.
      fs.rmSync(target, { recursive: true, force: true });
      const status = await new Promise((resolve, reject) => {
        activeChild = spawn(process.execPath, args('signal'), { stdio: ['ignore', 'ignore', 'pipe'],
          env: { ...process.env, UV_THREADPOOL_SIZE: '1' } });
        let sent = false, stderr = '';
        const timer = setTimeout(() => { activeChild.kill('SIGTERM'); reject(new Error('signal test timed out')); }, 10000);
        activeChild.stderr.on('data', chunk => {
          stderr += chunk;
          if (!sent && stderr.includes('"event":"start"')) { sent = true; activeChild.kill('SIGTERM'); }
        });
        activeChild.on('error', reject);
        activeChild.on('close', (code, signal) => {
          clearTimeout(timer); activeChild = undefined;
          try { assert(sent); assert.equal(signal, null, stderr); resolve(code); } catch (error) { reject(error); }
        });
      });
      assert.equal(status, 130);
    }
    const resumed = run('signal'); assert.equal(resumed.status, 0, resumed.stderr); compare('signal');
    prior = fs.readFileSync(events, 'utf8');
    assert.match(prior, /interrupted/); assert.match(prior, /resume/);
  },
  parameter_rejections: () => {
    for (const extra of [['--p', '0'], ['--q', '-1'], ['--p', '2', '--q', '2'], ['--p', '1000000'], ['--bad', '1']]) {
      assert.notEqual(run('bad-options', extra).status, 0);
    }
  },
};
let state = { identity, completed: [] };
const started = performance.now();
try {
  if (fs.existsSync(checkpoint)) {
    const saved = JSON.parse(fs.readFileSync(checkpoint, 'utf8'));
    assert.equal(saved.sha256, digest(saved.payload), 'corrupt test checkpoint'); state = saved.payload;
    assert.deepEqual(state.identity, identity, 'incompatible test checkpoint');
  }
  log(state.completed.length ? 'resume' : 'start', { identity, threads: 1, completed: state.completed.length,
    total: Object.keys(tasks).length, checkpoint });
  for (const [name, task] of Object.entries(tasks)) {
    if (state.completed.includes(name)) continue;
    if (stopped) { log('interrupted', { checkpoint }); process.exitCode = 130; break; }
    await task(); state.completed.push(name);
    atomic(checkpoint, { payload: state, sha256: digest(state) });
    log('pass', { task: name, completed: state.completed.length, total: Object.keys(tasks).length,
      elapsed_seconds: (performance.now() - started) / 1000, checkpoint });
  }
  if (!process.exitCode) log('complete', { tests: state.completed.length });
} catch (error) { log('error', { message: error.message, checkpoint }); throw error; }
