"""Real-master B/F growth and quality experiments. Networks are never pooled.

Scale: connected BFS prefixes of ONE sampled L network, 5 or more sizes.
Quality: seed-41 every-seventh master samples, 20 S/20 M/10 L/12 X.
Preserves all A/C/D/G result rows through the existing measurement helper.
"""
import argparse
import csv
import json
import math
import sys
from collections import deque
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import measure
from src.loader import load_cases, read_cases
from src.modules import routes, networkplan


def sample_metadata(master):
    cases = read_cases(master)
    return [r for tier, n in [('S', 20), ('M', 20), ('L', 10), ('X', 12)]
            for r in [c for c in cases if c['tier'] == tier][6::7][:n]]


def prefix(case, n):
    adj = {v.loc_id: [] for v in case.locations}
    for r in case.roads:
        adj[r.u].append(r.v)
        adj[r.v].append(r.u)
    seen, order, queue = {0}, [], deque([0])
    while queue and len(order) < n:
        u = queue.popleft()
        order.append(u)
        for v in sorted(adj[u]):  # input construction, excluded from measured algorithm
            if v not in seen:
                seen.add(v)
                queue.append(v)
    selected = set(order)
    return ([v for v in case.locations if v.loc_id in selected],
            [r for r in case.roads if r.u in selected and r.v in selected], order[-1])


def measured(module, algorithm, cid, nodes, edges, target):
    def call(deadline):
        if module == 'B':
            return routes.solve(nodes, edges, target, algorithm, deadline=deadline)
        return networkplan.solve(nodes, edges, algorithm, deadline=deadline)

    # Calibration only chooses a batch size. One further warmup is discarded.
    start = perf_counter()
    call(start + measure.DNF_SECONDS)
    batch = max(1, min(100, math.ceil(.01 / max(perf_counter() - start, 1e-9))))

    def timed(deadline):
        for _ in range(batch):
            plan = call(deadline)
        return plan

    base = dict(module=module, experiment=f'{module}-scale-V', algorithm=algorithm,
                instance=cid, size=len(nodes), size2=len(edges))
    times, plan = measure.time_runs(timed)
    if times is None:
        return dict(base, status='DNF', note='300 s deadline; input loading excluded')
    med, iqr = measure.median_iqr([t / batch for t in times])
    return dict(base, time_s=f'{med:.9g}', time_iqr_s=f'{iqr:.9g}', ops=sum(plan.ops.values()),
                mem_bytes=measure.peak_memory(call), status=plan.status,
                note=json.dumps(dict(counts=plan.ops, batch=batch, construction='single-network BFS prefix')))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--master', default='MASTER')
    parser.add_argument('--out', default='results')
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    metadata = sample_metadata(args.master)
    cases = load_cases(args.master, [r['case_id'] for r in metadata], graph_only=True)
    source = max((cases[r['case_id']] for r in metadata if r['tier'] == 'L'), key=lambda c: len(c.locations))
    sizes = [n for n in [16, 32, 64, 128, 256, 512, 1024] if n <= len(source.locations)]
    assert len(sizes) >= 5, 'master sample lacks a large enough L network'
    measured_rows = []
    for n in sizes:
        nodes, edges, target = prefix(source, n)
        assert len(nodes) == n, 'scale source must have a connected HQ component'
        for module, methods in [('B', ('dijkstra', 'bellman', 'bfs')), ('F', ('kruskal', 'prim'))]:
            for method in methods:
                row = measured(module, method, source.metadata['case_id'], nodes, edges, target)
                measured_rows.append(row)
                print(module, method, n, row.get('time_s', 'DNF'), flush=True)
    measure.write_results(str(out / 'results.csv'), measured_rows, {('B', 'B-scale-V'), ('F', 'F-scale-V')})
    quality = []
    for meta in metadata:
        c = cases[meta['case_id']]
        blocked = set()
        for wave in [None] + sorted(c.waves):
            if wave is not None:
                blocked.update(c.waves[wave])
            for target in (meta['target_0'], meta['target_1'], meta['target_2']):
                dij = routes.solve(c.locations, c.roads, target, blocked=blocked)
                bf = routes.solve(c.locations, c.roads, target, 'bellman', blocked)
                bfs = routes.solve(c.locations, c.roads, target, 'bfs', blocked)
                assert dij.distances == bf.distances, (meta['case_id'], wave)
                quality.append(dict(case_id=meta['case_id'], tier=meta['tier'], wave='initial' if wave is None else wave,
                                    target=target, status=dij.status, optimal_cost=dij.cost, bfs_cost=bfs.cost,
                                    bfs_ratio=(bfs.cost / dij.cost if dij.cost else ''),
                                    route_agrees=True, forest_agrees='', kruskal_cost='', prim_cost=''))
            kr = networkplan.solve(c.locations, c.roads, blocked=blocked)
            pr = networkplan.solve(c.locations, c.roads, 'prim', blocked)
            assert kr.cost == pr.cost
            quality[-1].update(forest_agrees=True, kruskal_cost=kr.cost, prim_cost=pr.cost)
    with (out / 'quality-BF.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(quality[0]))
        writer.writeheader()
        writer.writerows(quality)
    env = measure.describe_environment()
    env.update(source_case=source.metadata['case_id'], sizes=sizes, sampled_cases=len(metadata),
               warmup=1, repetitions=5, power_state='not verified',
               limitations='One unpooled network for growth; all sampled full networks and cumulative waves for quality.')
    (out / 'environmentBF.json').write_text(json.dumps(env, indent=2) + '\n')
    print('Quality rows:', len(quality), 'all shortest-cost and forest comparisons agree', flush=True)


if __name__ == '__main__':
    main()
