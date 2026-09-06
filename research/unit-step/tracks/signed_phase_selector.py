#!/usr/bin/env python3
"""Constraint-directed search for <=5-vector subsequences of signed Gaussian lifts.

For q low sign bits choose a nonempty subset J_r of positions 0..2^q-1 in
EVERY block with tail state r. All four minimal realizable tail carry graphs
are covered. Signs, graph, selected vertices, and menu are solved jointly;
this is not sequential enumeration of periodic curves. A satisfying model
has an exact infinite certificate: every allowed block boundary uses the
same finite menu and the walk is a subsequence of the existing tagged lift.

One core. Per-q atomic checkpoints are keyed by source/config/Z3 version;
completed work resumes automatically and is checksum-validated. SIGINT/TERM
flushes completed results; the bounded active solver task may be retried.
Unknown/timeouts are NOT impossibility certificates. Logs and checkpoints
live separately from the optional final JSON.

Run: uv run --with z3-solver==4.15.4.0 python THIS_FILE --levels 1 2 3 4
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import time

# Set before loading native libraries; no solver or build worker fan-out.
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
import z3

DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
TAGS = ((0, 0, 0), (-1, 0, 1), (-1, 1, 2), (0, -1, 3))
# Every realizable change set contains one of these four; each is realizable.
GRAPHS = ((0, 1), (1, 2), (0, 3), (2, 3))
STOP = False
ACTIVE = None


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def handle_signal(_signum, _frame):
    global STOP
    STOP = True
    if ACTIVE is not None:
        ACTIVE.interrupt()


def complex_product(a, b):
    return a[0]*b[0]-a[1]*b[1], a[0]*b[1]+a[1]*b[0]


def geometry(q, low):
    signs = [(-1 if low & (1 << j) else 1) for j in range(q)]
    states = [sum(signs[j] for j in range(q) if n & (1 << j)) % 4 for n in range(1 << q)]
    source = [(0, 0)]
    for s in states:
        source.append(tuple(source[-1][j]+DIRECTIONS[s][j] for j in range(2)))
    points, advances = [], []
    for r in range(4):
        row = []
        for j, s in enumerate(states):
            x, y = complex_product(DIRECTIONS[r], source[j])
            tag = TAGS[(r+s) % 4]
            row.append((2*x+tag[0], 2*y+tag[1], 4*j+tag[2]))
        points.append(row)
        x, y = complex_product(DIRECTIONS[r], source[-1])
        advances.append((2*x, 2*y, 4*(1 << q)))
    return signs, points, advances


def chosen_menu(q, low, changes, selected):
    _, points, advances = geometry(q, low)
    vectors = set()
    for r in range(4):
        for a, b in zip(selected[r], selected[r][1:]):
            vectors.add(tuple(points[r][b][j]-points[r][a][j] for j in range(3)))
        for d in changes:
            s = (r+d) % 4
            vectors.add(tuple(advances[r][j]+points[s][selected[s][0]][j]
                              -points[r][selected[r][-1]][j] for j in range(3)))
    return sorted(vectors)


def solve(q, budget, seconds, log):
    global ACTIVE
    length = 1 << q
    solver = z3.SolverFor('QF_FD')
    solver.set(timeout=round(seconds*1000), random_seed=0)
    ACTIVE = solver
    started = time.monotonic()
    sign_cases = [z3.Bool(f'signs_{low}') for low in range(length)]
    graph_cases = [z3.Bool(f'graph_{g}') for g in range(4)]
    solver.add(z3.PbEq([(v,1) for v in sign_cases], 1))
    solver.add(z3.PbEq([(v,1) for v in graph_cases], 1))
    chosen = [[z3.Bool(f'p_{r}_{j}') for j in range(length)] for r in range(4)]
    first = [[z3.Bool(f'first_{r}_{j}') for j in range(length)] for r in range(4)]
    last = [[z3.Bool(f'last_{r}_{j}') for j in range(length)] for r in range(4)]
    for r in range(4):
        solver.add(z3.Or(chosen[r]))
        for j in range(length):
            solver.add(first[r][j] == z3.And(chosen[r][j], *[z3.Not(p) for p in chosen[r][:j]]))
            solver.add(last[r][j] == z3.And(chosen[r][j], *[z3.Not(p) for p in chosen[r][j+1:]]))
    menu = {}
    def label(vector):
        if vector not in menu:
            menu[vector] = z3.Bool(f'v_{len(menu)}')
        return menu[vector]
    # Consecutive endpoints determine a mandatory displacement. Each clause
    # says either they are not consecutive, this topology is inactive, or
    # that exact displacement belongs to the globally bounded menu.
    clauses = 0
    for low in range(length):
        if STOP:
            return {'q':q, 'status':'interrupted-during-build'}
        _, points, advances = geometry(q, low)
        inactive = z3.Not(sign_cases[low])
        for r in range(4):
            for a in range(length):
                for b in range(a+1, length):
                    vector = tuple(points[r][b][j]-points[r][a][j] for j in range(3))
                    solver.add(z3.Or(inactive, z3.Not(chosen[r][a]), z3.Not(chosen[r][b]),
                                     *chosen[r][a+1:b], label(vector)))
                    clauses += 1
            for d in range(4):
                excluded = z3.And(*[z3.Not(graph_cases[g]) for g, changes in enumerate(GRAPHS) if d in changes])
                s = (r+d) % 4
                for a in range(length):
                    for b in range(length):
                        vector = tuple(advances[r][j]+points[s][b][j]-points[r][a][j] for j in range(3))
                        solver.add(z3.Or(inactive, excluded, z3.Not(last[r][a]), z3.Not(first[s][b]), label(vector)))
                        clauses += 1
        if low % max(1, length//4) == 0:
            elapsed = time.monotonic()-started
            log('build', q=q, completed=low+1, total=length, clauses=clauses,
                elapsedSeconds=elapsed, perSecond=(low+1)/elapsed,
                remainingSeconds=elapsed/(low+1)*(length-low-1)+seconds)
    solver.add(z3.PbLe([(v,1) for v in menu.values()], budget))
    log('solve', q=q, vectorUniverse=len(menu), clauses=clauses,
        timeoutSeconds=seconds, elapsedSeconds=time.monotonic()-started)
    build_seconds = time.monotonic()-started
    status = solver.check()
    result = {'q':q, 'budget':budget, 'status':str(status), 'lowSignCases':length,
              'tailGraphs':GRAPHS, 'vectorUniverse':len(menu), 'clauses':clauses,
              'buildSeconds':build_seconds, 'solveSeconds':time.monotonic()-started-build_seconds}
    if status == z3.sat:
        model = solver.model()
        low = next(low for low,v in enumerate(sign_cases) if z3.is_true(model.eval(v)))
        graph = next(g for g,v in enumerate(graph_cases) if z3.is_true(model.eval(v)))
        selected = [[j for j,p in enumerate(row) if z3.is_true(model.eval(p))] for row in chosen]
        vectors = chosen_menu(q, low, GRAPHS[graph], selected)
        assert len(vectors) <= budget and all(v[2] > 0 for v in vectors)
        result['candidate'] = {'lowSigns':geometry(q,low)[0], 'tailChanges':GRAPHS[graph],
                               'positionsByTailState':selected, 'menu':vectors}
    elif status == z3.unknown:
        result['reason'] = solver.reason_unknown()
    ACTIVE = None
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--levels', nargs='+', type=int, default=[1,2,3,4])
    parser.add_argument('--budget', type=int, default=5)
    parser.add_argument('--seconds', type=float, default=60, help='per-level solve timeout; construction is separate')
    parser.add_argument('--checkpoint-dir', type=Path, default=Path('.checkpoint-signed-phase-selector'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if any(q < 1 or q > 5 for q in args.levels) or args.budget < 1 or args.seconds <= 0:
        parser.error('levels must be 1..5, and budget and seconds must be positive')
    z3.set_param('parallel.enable', False)
    z3.set_param('sat.threads', 1)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    identity = {'schema':1, 'sourceSha256':source_hash, 'z3':z3.get_version_string(),
                'budget':args.budget, 'seconds':args.seconds, 'tags':TAGS}
    config_hash = digest(identity)
    root = args.checkpoint_dir/config_hash
    root.mkdir(parents=True, exist_ok=True)
    def log(event, **fields):
        record = {'timestamp':datetime.now(timezone.utc).isoformat(), 'event':event, **fields}
        text = json.dumps(record, sort_keys=True)
        with (root/'run.jsonl').open('a') as stream:
            stream.write(text+'\n')
            stream.flush()
        print(text, flush=True)
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, handle_signal)
    log('start', identity=identity, levels=args.levels, cores=1, checkpointDirectory=str(root),
        estimatedSolveSeconds=len(args.levels)*args.seconds,
        resume='compatible completed per-level work is reused; interrupted active level restarts')
    results=[]
    for q in args.levels:
        checkpoint = root/f'level-{q}.json'
        if checkpoint.exists():
            saved = json.loads(checkpoint.read_text())
            if saved.get('configHash') != config_hash or saved.get('resultSha256') != digest(saved.get('result')):
                raise ValueError(f'incompatible/corrupt checkpoint: {checkpoint}')
            result = saved['result']
            log('resume', q=q, status=result['status'])
        else:
            result = solve(q,args.budget,args.seconds,log)
            if not STOP:
                atomic(checkpoint, {'configHash':config_hash, 'resultSha256':digest(result), 'result':result})
            log('level-complete', **result)
        results.append(result)
        if STOP or result['status']=='sat':
            break
    if args.output:
        atomic(args.output, {'identity':identity, 'results':results,
                            'scope':'block-state-dependent subsequences with a nonempty selection in every dyadic block; fixed Cambie tags'})
    log('complete' if not STOP else 'interrupted', completed=len(results), total=len(args.levels),
        remainingSeconds=0 if not STOP else None, statuses=[r['status'] for r in results])
    return 130 if STOP else 0


if __name__ == '__main__':
    raise SystemExit(main())
