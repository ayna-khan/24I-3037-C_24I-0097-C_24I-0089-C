"""Fits, plots, prediction checks and report-ready B/F comparison tables."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.measure import fit_loglog


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    out = ROOT / 'results'
    with (out / 'results.csv').open(newline='', encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if r['module'] in ('B', 'F') and r['status'] == 'OK']
    with (out / 'quality-BF.csv').open(newline='', encoding='utf-8') as f:
        quality = list(csv.DictReader(f))
    env = json.loads((out / 'environmentBF.json').read_text())
    fits = []
    groups = {}
    for row in rows:
        groups.setdefault((row['module'], row['algorithm']), []).append(row)
    for (module, method), part in groups.items():
        part.sort(key=lambda r: int(r['size']))
        for metric in ('time_s', 'ops', 'mem_bytes'):
            fit = fit_loglog([int(r['size']) for r in part], [float(r[metric]) for r in part])
            fits.append(dict(module=module, algorithm=method, metric=metric, **fit))
    with (out / 'fits-BF.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(fits[0]))
        w.writeheader()
        w.writerows(fits)
    fit_md = ['# B/F growth fits', '',
              f"Source: master_release_v1, case {env['source_case']}; connected BFS prefixes; no networks pooled.",
              'Fits include changing edge density and validation/output construction. They describe this input family only.', '',
              '| Module | Method | Metric | Exponent | 95% half-width | R² | Sizes |',
              '|---|---|---|---:|---:|---:|---:|']
    for fit in fits:
        fit_md.append(f"| {fit['module']} | {fit['algorithm']} | {fit['metric']} | {fit['slope']:.3f} | {fit['ci95']:.3f} | {fit['r2']:.4f} | {fit['n']} |")
    (out / 'fits-BF.md').write_text('\n'.join(fit_md) + '\n', encoding='utf-8')
    ratios = [float(r['bfs_ratio']) for r in quality if r['bfs_ratio']]
    forest = [r for r in quality if r['forest_agrees']]
    biggest = {method: max(part, key=lambda r: int(r['size'])) for (_, method), part in groups.items()}
    def t(method):
        return float(biggest[method]['time_s'])
    slopes = {(f['algorithm'], f['metric']): f['slope'] for f in fits}
    checks = [
        ('BF1', all(r['route_agrees'] == 'True' for r in quality), f'{len(quality)} route comparisons agree'),
        ('BF2', all(r['forest_agrees'] == 'True' for r in forest), f'{len(forest)} forest comparisons agree'),
        ('BF3', all(r >= 1 for r in ratios), f'min BFS/opt = {min(ratios):.3f}'),
        ('BF4', max(ratios) > 1, f'max BFS/opt = {max(ratios):.3f}'),
        ('BF5', .7 <= slopes['dijkstra', 'ops'] <= 1.8, f"Dijkstra operation exponent = {slopes['dijkstra', 'ops']:.3f}"),
        ('BF6', .7 <= slopes['kruskal', 'ops'] <= 1.8, f"Kruskal operation exponent = {slopes['kruskal', 'ops']:.3f}"),
        ('BF7', t('bellman') > t('dijkstra'), f"largest Bellman/Dijkstra time ratio = {t('bellman') / t('dijkstra'):.3f}"),
        ('BF8', len(rows) == 5 * len(env['sizes']), f"{len(rows)} completed growth configurations"),
    ]
    preds = ['# B/F predictions against measurements', '',
             'Predictions were saved in a local commit before running; no absolute-time calibration was used.', '',
             '| ID | Result | Evidence |', '|---|---|---|']
    preds += [f'| {i} | {"HIT" if hit else "MISS"} | {evidence} |' for i, hit, evidence in checks]
    preds += ['', f'{sum(hit for _, hit, _ in checks)} of {len(checks)} predictions met the stated tolerance.',
              'A miss remains a miss; the pre-run prediction was not rewritten.']
    (out / 'predictions-vs-measurements-BF.md').write_text('\n'.join(preds) + '\n', encoding='utf-8')
    comparison = ['# B/F comparison and recommendation', '',
                  f"Master sample: {env['sampled_cases']} cases, {len(quality)} route checks, {len(forest)} forest checks, including cumulative waves.",
                  f"Largest growth input: {env['sizes'][-1]} vertices from case {env['source_case']}.", '',
                  '| Module | Method | Median seconds at largest size | IQR seconds | Operations | Peak bytes beyond input |',
                  '|---|---|---:|---:|---:|---:|']
    for (module, method), part in groups.items():
        r = biggest[method]
        comparison.append(f"| {module} | {method} | {r['time_s']} | {r['time_iqr_s']} | {r['ops']} | {r['mem_bytes']} |")
    comparison += ['',
        f"B: Dijkstra and Bellman-Ford agree in every comparison. BFS chooses a fewest-roads route but its worst cost ratio is {max(ratios):.3f}; mean ratio is {sum(ratios)/len(ratios):.3f} over reachable nonzero-cost targets.",
        f"F: Kruskal and Prim agree on every forest cost. Largest-input Prim/Kruskal time ratio is {t('prim') / t('kruskal'):.3f}.", '',
        'Ship heap Dijkstra for positive travel costs and BFS for reachability/hops. Keep Bellman-Ford as a check; it can be competitive on small, favourably ordered graphs because it stops early. Reject negative minutes/penalties rather than feeding them to Dijkstra.', '',
        'Ship Kruskal with union by size and path compression for sparse cable networks; keep Prim as an independent baseline. A disconnected map returns a forest. For HQ-only cabling pass the reachable set. Reconsider an array Prim implementation for dense graphs; monitor E/V and memory before choosing.', '',
        'Limitations: seven nested prefixes of one real network are not seven independent networks; edge density changes. Quality covers sampled cases, not the complete master release. Timing is one machine/session, power state unverified; IQR and operation counts must accompany comparisons. No 300-second DNF demonstration is claimed: these data sizes finish quickly.', '',
        'Failure-mode paragraph for Ayna: positive-cost routing becomes invalid if a later data source introduces negative weights; stale closure state can dispatch into disconnected locations; unusually dense graphs increase adjacency/sorting memory and can reverse the F-method preference. The new validation, NO_ROUTE checks, independent references and seeded-fault tests exercise these boundaries. Ayna owns the final ranked list.',
    ]
    (out / 'comparison-BF.md').write_text('\n'.join(comparison) + '\n', encoding='utf-8')
    plot_dir = out / 'plots'
    plot_dir.mkdir(exist_ok=True)
    for module in ('B', 'F'):
        for metric, label, suffix in [('time_s', 'Median runtime (s)', 'time'), ('ops', 'Counted operations', 'operations'), ('mem_bytes', 'Peak bytes beyond input', 'memory')]:
            fig, ax = plt.subplots(figsize=(7, 4.4))
            for (mod, method), part in groups.items():
                if mod != module:
                    continue
                xs, ys = [int(r['size']) for r in part], [float(r[metric]) for r in part]
                if metric == 'time_s':
                    ax.errorbar(xs, ys, yerr=[float(r['time_iqr_s']) / 2 for r in part], marker='o', capsize=3, label=method)
                else:
                    ax.plot(xs, ys, marker='o', label=method)
            ax.set(xscale='log', yscale='log', xlabel='Vertices (one real network, connected prefixes)', ylabel=label,
                   title=f'Module {module}: {label.lower()}')
            ax.grid(True, alpha=.25)
            ax.legend()
            fig.tight_layout()
            fig.savefig(plot_dir / f'{module}-{suffix}.png', dpi=160)
            plt.close(fig)
    (plot_dir / 'captions-BF.md').write_text('''# B/F plot captions

All six figures use connected BFS prefixes of one sampled L network, not pooled
networks. Input construction/CSV loading is excluded. Times are medians of five
runs after one discarded warmup; error bars show half the IQR each side (not a
confidence interval). Memory is peak tracemalloc allocation in a separate run,
beyond the input. Counts sum comparisons, moves, edge tests, relaxations and
union-find parent traversals, including ordering for adjacency/output.

- B-time.png / B-operations.png / B-memory.png: positive-cost Dijkstra and
  Bellman-Ford solve the same problem; BFS is only the fewest-roads baseline.
- F-time.png / F-operations.png / F-memory.png: Kruskal and Prim solve the same
  minimum-forest problem. Forest equality across sampled waves is in quality-BF.csv.

Machine details: environmentBF.json. Edge density changes with prefix size, so
the fitted exponents describe this network family, not a universal bound.
''', encoding='utf-8')
    print('\n'.join(preds[-11:]))


if __name__ == '__main__':
    main()
