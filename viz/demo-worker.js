const PYODIDE_BASE = 'https://cdn.jsdelivr.net/pyodide/v0.28.3/full/';

importScripts(`${PYODIDE_BASE}pyodide.js`);

const runtimePromise = loadPyodide({indexURL: PYODIDE_BASE});

runtimePromise
  .then(() => self.postMessage({type: 'ready'}))
  .catch(error => self.postMessage({type: 'boot-error', error: error.stack || String(error)}));

self.addEventListener('message', async event => {
  if (event.data?.type !== 'run') return;

  try {
    const pyodide = await runtimePromise;
    if (typeof event.data.source !== 'string') throw new Error('Missing Python source.');
    pyodide.setStdout({batched: line => self.postMessage({type: 'line', line})});
    pyodide.setStderr({batched: line => self.postMessage({type: 'line', line})});
    pyodide.globals.set('DEMO_SOURCE', event.data.source);
    pyodide.globals.set('DEMO_LENGTH', event.data.length);
    self.postMessage({type: 'running'});
    await pyodide.runPythonAsync(`
namespace = {
    "__name__": "gaussian_walk",
    "__file__": "gaussian_walk.py",
    "__package__": None,
}
exec(compile(DEMO_SOURCE, "gaussian_walk.py", "exec"), namespace)
from itertools import islice
points = list(islice(namespace["gaussian_walk"](), DEMO_LENGTH))
print(f"Generated the first {len(points):,} points of the infinite walk.")
print("First eight points:")
for n, point in enumerate(points[:8]):
    print(f"  P_{n} = {point}")
print(f"Last point: P_{len(points) - 1} = {points[-1]}")
`);
    self.postMessage({type: 'done'});
  } catch (error) {
    self.postMessage({type: 'run-error', error: error.stack || String(error)});
  }
});
