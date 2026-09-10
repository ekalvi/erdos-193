#!/usr/bin/env node
// Tiny, serial CLI regression; all child processes inherit the caller's CPU affinity.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { spawn, spawnSync } from 'node:child_process';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = process.argv[2] ?? '.checkpoint-five-marker-tests';
if (process.argv.includes('--help')) {
  console.log('Usage: taskset -c 0 node --single-threaded test.mjs [WORK_DIR]\nBounded serial regression, rerun on restart. Logs and isolated test states stay in WORK_DIR.');
  process.exit(0);
}
fs.mkdirSync(root, { recursive: true });
const work = fs.mkdtempSync(path.join(root, 'run-'));
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
function log(event, extra = {}) {
  const row = { utc: new Date().toISOString(), event, ...extra };
  fs.appendFileSync(path.join(work, 'test.jsonl'), JSON.stringify(row) + '\n'); console.log(JSON.stringify(row));
}
const env = { ...process.env, OMP_NUM_THREADS: '1', OPENBLAS_NUM_THREADS: '1', MKL_NUM_THREADS: '1', NUMEXPR_NUM_THREADS: '1', UV_THREADPOOL_SIZE: '1' };
const commandArgs = (script, args) => ['--single-threaded', '--v8-pool-size=1', path.join(here, script), ...args];
function run(script, args, expected = 0) {
  const result = spawnSync(process.execPath, commandArgs(script, args), { env, encoding: 'utf8', timeout: 10_000 });
  fs.appendFileSync(path.join(work, 'children.jsonl'), JSON.stringify({ script, args, status: result.status, stdout: result.stdout, stderr: result.stderr }) + '\n');
  assert.equal(result.status, expected, `${script}: ${result.stderr}`); return result;
}
function load(dir) { return JSON.parse(fs.readFileSync(path.join(dir, 'state.json'))); }
function interrupted(script, args, event) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, commandArgs(script, args), { env, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '', stderr = '', sent = false;
    const timeout = setTimeout(() => { child.kill('SIGKILL'); reject(Error('signal regression timed out')); }, 10_000);
    child.stdout.on('data', bytes => {
      stdout += bytes;
      if (!sent && stdout.includes(`"event":"${event}"`)) { sent = true; child.kill('SIGTERM'); }
    });
    child.stderr.on('data', bytes => { stderr += bytes; });
    child.on('error', reject);
    child.on('close', (code, signal) => {
      clearTimeout(timeout);
      fs.appendFileSync(path.join(work, 'children.jsonl'), JSON.stringify({ script, args, code, signal, stdout, stderr }) + '\n');
      try { assert(sent); assert.equal(signal, null); assert.equal(code, 143); resolve(); } catch (error) { reject(error); }
    });
  });
}
function rejectionTests(script, goodDir, argsFor) {
  for (const kind of ['corrupt', 'incompatible', 'invalid-cursor']) {
    const dir = path.join(work, `${script}-${kind}`); fs.mkdirSync(dir);
    const state = load(goodDir);
    if (kind === 'corrupt') state.sha256 = '0'.repeat(64);
    else {
      if (kind === 'incompatible') state.payload.identity.schema = -1;
      else if (script === 'search.mjs') state.payload.next = [];
      else state.payload.completed[0].stage = 'not-a-stage';
      state.sha256 = sha(JSON.stringify(state.payload));
    }
    fs.writeFileSync(path.join(dir, 'state.json'), JSON.stringify(state));
    const result = run(script, argsFor(dir), 1);
    assert.match(result.stderr, kind === 'corrupt' ? /corrupt checkpoint/ : kind === 'incompatible' ? /incompatible checkpoint/ : /AssertionError/);
  }
}
const started = Date.now();
log('start', { work, sourceSha256: sha(fs.readFileSync(fileURLToPath(import.meta.url))),
  resources: { children: 'serial', affinity: fs.readFileSync('/proc/self/status', 'utf8').match(/^Cpus_allowed_list:\s*(.*)$/m)?.[1] },
  estimatedSeconds: '2-5' });
try {
  const search = path.join(work, 'search');
  run('search.mjs', ['--state-dir', search, '--budget-ms', '0']); assert.equal(load(search).payload.attempts, 0);
  run('search.mjs', ['--state-dir', search]); assert.equal(load(search).payload.status, 'found');
  const searchResult = fs.readFileSync(path.join(search, 'result.json'), 'utf8');
  const attempts = load(search).payload.attempts;
  run('search.mjs', ['--state-dir', search]);
  assert.equal(load(search).payload.attempts, attempts); assert.equal(fs.readFileSync(path.join(search, 'result.json'), 'utf8'), searchResult);
  assert.equal(JSON.parse(searchResult).word, JSON.parse(fs.readFileSync(path.join(here, 'examples.json'))).outerEndpointCounterexample.word);
  rejectionTests('search.mjs', search, dir => ['--state-dir', dir]);
  const searchSignal = path.join(work, 'search-signal');
  await interrupted('search.mjs', ['--state-dir', searchSignal], 'start');
  const savedAttempts = load(searchSignal).payload.attempts;
  assert(savedAttempts < attempts);
  run('search.mjs', ['--state-dir', searchSignal]);
  assert.equal(load(searchSignal).payload.attempts, attempts);
  assert.equal(fs.readFileSync(path.join(searchSignal, 'result.json'), 'utf8'), searchResult);
  log('search-tests-passed', { completed: 1, total: 2, attempts, signalCheckpointAttempts: savedAttempts });

  const verify = path.join(work, 'verify');
  run('verify.mjs', [verify, '--stop-after', '1']); assert.equal(load(verify).payload.completed.length, 1);
  const firstStage = JSON.stringify(load(verify).payload.completed[0]);
  run('verify.mjs', [verify]); assert.equal(JSON.stringify(load(verify).payload.completed[0]), firstStage);
  const verifyResult = fs.readFileSync(path.join(verify, 'result.json'), 'utf8');
  run('verify.mjs', [verify]); assert.equal(fs.readFileSync(path.join(verify, 'result.json'), 'utf8'), verifyResult);
  rejectionTests('verify.mjs', verify, dir => [dir]);
  const verifySignal = path.join(work, 'verify-signal');
  await interrupted('verify.mjs', [verifySignal], 'stage-start');
  const savedStages = load(verifySignal).payload.completed.length;
  assert(savedStages > 0 && savedStages < 5);
  run('verify.mjs', [verifySignal]);
  assert.equal(fs.readFileSync(path.join(verifySignal, 'result.json'), 'utf8'), verifyResult);
  log('complete', { status: 'pass', completed: 2, total: 2, elapsedMs: Date.now() - started,
    assertions: ['budget resume', 'completed reuse', 'source/config rejection', 'checksum rejection', 'cursor validation', 'SIGTERM flush/resume', 'identical independent results'],
    verifySignalCompletedStages: savedStages });
} catch (error) { log('error', { message: error.stack, elapsedMs: Date.now() - started }); process.exitCode = 1; }
