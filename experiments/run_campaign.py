"""Reproduce official-calendar evidence, baseline comparisons and report figures.

Run from the repository root: python experiments/run_campaign.py --master MASTER
Samples follow seed 41: every seventh case of each tier, starting at position 6.
"""
import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.campaign import run_campaign, official_calendar
from src.cli import campaign_text
from src.loader import load_cases, read_cases
from src.models import InvalidInputError

POLICIES = ('optimized', 'baseline', 'simple')


def selected_cases(metadata):
    samples = {tier: [r for r in metadata if r['tier'] == tier][6::7] for tier in 'SMLX'}
    return [samples['S'][0]['case_id'], samples['M'][0]['case_id'], samples['L'][0]['case_id'],
            next(r['case_id'] for r in samples['X'] if r['case_no'] == 47),
            next(r['case_id'] for r in samples['X'] if r['case_no'] == 48)]


def compare(reports):
    for opt, baseline, simple in zip(*(reports[p]['days'] for p in POLICIES)):
        if opt['input'] != baseline['input'] or opt['input'] != simple['input']:
            raise InvalidInputError('campaign comparisons did not receive identical daily inputs')
        if (opt['route']['distances'] != baseline['route']['distances'] or
                opt['rescue']['total'] != baseline['rescue']['total'] or
                opt['alarms']['releases'] != baseline['alarms']['releases']):
            raise InvalidInputError('an exact algorithm baseline disagrees')
        if opt['load'] and opt['load']['total_value'] < baseline['load']['total_value']:
            raise InvalidInputError('load heuristic exceeds exact optimum')
        if opt['route']['cost'] is not None and simple['route']['cost'] < opt['route']['cost']:
            raise InvalidInputError('BFS policy exceeds shortest-cost optimum')
        if 'network' in opt:
            for name, metric in [('network', 'cost'), ('chain', 'cost'), ('drum', 'price')]:
                if opt[name][metric] != baseline[name][metric]:
                    raise InvalidInputError(f'{name} exact baseline disagrees')
    return True


def write_report(out, all_reports, metadata):
    all_reports = {cid: all_reports[cid] for cid in sorted(all_reports)}
    daily, summary = [], []
    for cid, reports in all_reports.items():
        for policy, report in reports.items():
            summary.append(dict(case_id=cid, tier=metadata[cid]['tier'], policy=policy, **report['summary']))
            for d in report['days']:
                daily.append(dict(case_id=cid, tier=metadata[cid]['tier'], policy=policy, day=d['day'],
                                  event=d['event'], target=d['target'], blocked_roads=len(d['closed_roads']),
                                  trip_made=d['trip_made'], trip_status=d['dispatch_status'],
                                  route_cost=d['route']['cost'], load_value=d['load']['total_value'] if d['load'] else 0,
                                  rescue_total=d['rescue']['total'], urgent_mean_wait=d['alarm_metrics']['urgent_wait'] /
                                  max(1, d['alarm_metrics']['urgent_count']), checks_passed=all(d['checks'].values())))
    for name, rows in [('campaign-daily.csv', daily), ('campaign-summary.csv', summary)]:
        with (out / name).open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    md = ['# Official seven-day campaign results', '',
          'Source: Project Statement, section 7.4, page 7. Master: master_release_v1; seed 41.',
          'Five cases from the prescribed every-seventh tier samples, including L and traps 47/48.', '',
          '| Case | Tier | Policy | Delivered value | Outbound travel cost | Unreachable days | Rescue value | Urgent mean wait |',
          '|---|---|---|---:|---:|---:|---:|---:|']
    for r in summary:
        md.append(f"| {r['case_id']} | {r['tier']} | {r['policy']} | {r['delivered_value']} | {r['route_cost']} | "
                  f"{r['unreachable_days']} | {r['rescue_total']} | {r['urgent_mean_wait']:.3f} |")
    trap47 = next(cid for cid in all_reports if metadata[cid]['case_no'] == 47)
    trap48 = next(cid for cid in all_reports if metadata[cid]['case_no'] == 48)
    a = all_reports[trap47]['optimized']['days'][0]['load']['total_value']
    b = all_reports[trap47]['simple']['days'][0]['load']['total_value']
    opt = all_reports[trap48]['optimized']['days'][0]['route']['cost']
    simple = all_reports[trap48]['simple']['days'][0]['route']['cost']
    md += ['', '## Deliberately difficult scenarios', '',
           f'Trap 47 ({trap47}), normal day: exact loading delivers {a}; ratio greedy delivers {b} '
           f'({b/a:.3%} of optimum). The DP handles the hostile weight/value combination, '
           'but its capacity-dependent memory/time remain a limitation.', '',
           f'Trap 48 ({trap48}), normal day: the cheapest route costs {opt}; the fewest-roads '
           f'policy costs {simple} ({simple/opt:.3f} times as much). Dijkstra uses destination '
           'penalties and travel minutes, avoiding the hop-count trap. It cannot create a route '
           'when the flood disconnects the destination; those days explicitly skip the trip.', '',
           '## Daily evidence and invariants', '',
           f'{len(daily)} daily policy records: every recorded invariant passed. Exact Bellman-Ford '
           'distances, quadratic rescue totals, urgency-scan releases, Prim tree costs and memoized G '
           'results agree with the shipped methods on the same inputs. Greedy loading is a '
           'nonoptimal algorithm baseline; BFS/FIFO/value-greedy are additional simple policies.', '',
           'Each case JSON under results/campaign/ contains the complete immutable base input once, '
           'the official calendar and all three runs. Each day includes the resolved target/waves, '
           'changed minutes/penalties, eligible crate/window ids, extra alarms, method choices, '
           'decisions and verified constraints. The base input plus these explicit changes reconstruct '
           'the full daily input. campaign-daily.csv provides the compact daily outcomes.', '',
           'Assumptions made explicit: all daily changes apply afresh to base data; days 2–5 close only '
           'the listed wave, days 6–7 close their union. Zero-based wave positions are resolved in '
           'ascending stored wave-label order to support both 0-based and 1-based master groups. '
           'Daily stock resets; the statement specifies no consumption or expiry cutoff. '
           'Travel cost records the prescribed outbound route; no extra return leg is invented. '
           'Day 7 is counted as travel even though no load is permitted.', '',
           'F/G run in the day-7 planning review; A/B/C/D interact daily. No aggregate score combines '
           'delivered value, travel cost, rescue value or urgency: they are separate objectives. '
           'These are deterministic correctness/quality runs, not timing experiments.', '',
           '## Report artifacts', '',
           '- campaign-daily.csv, campaign-summary.csv and campaign/*.json: tables and daily evidence.',
           '- sample-outputs/campaign-official.txt: readable output from the program.',
           '- plots/campaign-values.png, campaign-urgent-wait.png, campaign-difficult.png and captions-campaign.md.',
           '- test-summary-BF.txt and fault-injection-BF.txt: automated evidence.',
           '- Ayna incorporates these figures/tables into report.pdf; Adan uses the existing backend API.',
           ]
    (out / 'campaign-comparison.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    exact_baselines_agree = all(compare(reports) for reports in all_reports.values())
    predictions = [
        ('CAM1', len(daily) == 105 and all(r['checks_passed'] for r in daily), f'{len(daily)} of {len(daily)} daily records pass'),
        ('CAM2', exact_baselines_agree, 'all exact B/C/D/F/G comparisons agree; compare() independently checks each day'),
        ('CAM3', b / a <= .6, f'trap-47 greedy/DP = {b/a:.6f} (threshold <= 0.60)'),
        ('CAM4', simple / opt > 1, f'trap-48 BFS/cheapest = {simple/opt:.6f} (threshold > 1)'),
    ]
    prediction_text = ['# Official campaign predictions against outcomes', '',
                       'The prediction entry was committed before the full campaign run.', '',
                       '| ID | Outcome | Evidence |', '|---|---|---|']
    prediction_text += [f'| {pid} | {"HIT" if hit else "MISS"} | {note} |' for pid, hit, note in predictions]
    prediction_text += ['', f'{sum(hit for _, hit, _ in predictions)}/{len(predictions)} predictions met their tolerances.']
    (out / 'predictions-vs-measurements-campaign.md').write_text('\n'.join(prediction_text) + '\n', encoding='utf-8')
    plot_results(out, all_reports, metadata, trap47, trap48)
    return summary, daily


def plot_results(out, reports, metadata, trap47, trap48):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cases = list(reports)
    colors = {'optimized': '#2266aa', 'baseline': '#ee9933', 'simple': '#669944'}
    plots = out / 'plots'
    plots.mkdir(exist_ok=True)
    for metric, name, ylabel in [('delivered_value', 'campaign-values.png', 'Delivered value (reachable days 1-6)'),
                                  ('urgent_mean_wait', 'campaign-urgent-wait.png', 'Mean urgent-alarm wait (ticks)')]:
        fig, ax = plt.subplots(figsize=(9, 4.8))
        for offset, policy in enumerate(POLICIES):
            ax.bar([i + (offset - 1) * .24 for i in range(len(cases))],
                   [reports[cid][policy]['summary'][metric] for cid in cases],
                   width=.24, color=colors[policy], label=policy)
        ax.set_xticks(range(len(cases)), [f'{cid} ({metadata[cid]["tier"]})' for cid in cases])
        ax.set(xlabel='Master case', ylabel=ylabel)
        ax.legend()
        ax.grid(axis='y', alpha=.2)
        fig.tight_layout()
        fig.savefig(plots / name, dpi=160)
        plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.5))
    for ax, cid, metric, title in [(axes[0], trap47, 'load', 'Trap 47: load value / optimum'),
                                  (axes[1], trap48, 'route', 'Trap 48: route cost / optimum')]:
        values = []
        for policy in POLICIES:
            d = reports[cid][policy]['days'][0]
            values.append(d['load']['total_value'] if metric == 'load' else d['route']['cost'])
        ax.bar(POLICIES, [v / values[0] for v in values], color=[colors[p] for p in POLICIES])
        ax.axhline(1, color='black', linewidth=.8, linestyle='--')
        ax.set(title=f'{title}\n{cid}, day 1', ylabel='Ratio to exact optimum')
    fig.tight_layout()
    fig.savefig(plots / 'campaign-difficult.png', dpi=160)
    plt.close(fig)
    (plots / 'captions-campaign.md').write_text('''# Official campaign figure captions

All figures are deterministic results from master_release_v1 and the official
section 7.4 calendar, with identical daily inputs for every policy.

- campaign-values.png: cumulative delivered value of reachable day-1–6 loads;
  day 7 has no loading. Optimized is exact knapsack, baseline/simple use ratio
  greedy. Higher is better; values reset to base before the day's multiplier.
- campaign-urgent-wait.png: mean wait of priority-9/10 alarms over all seven
  days. Optimized heap and baseline scan use urgency order; simple uses FIFO.
  Lower is better. This is a scheduling metric, not total alarm wait.
- campaign-difficult.png: normal-day trap 47 loading value ratio (higher is
  better), and trap 48 travel cost ratio (lower is better); a reference at 1
  marks the exact optimum. They demonstrate different failure modes, not a
  combined score. No timing/error bars are implied by these quality plots.
''', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--master', default='MASTER')
    parser.add_argument('--out', default='results')
    parser.add_argument('--cases', nargs='+', help='override the five seed-41 samples')
    args = parser.parse_args()
    metadata = {r['case_id']: r for r in read_cases(args.master)}
    ids = args.cases or selected_cases(list(metadata.values()))
    if len(set(ids)) < 5 or not set(ids) <= metadata.keys():
        raise InvalidInputError('campaign evidence needs at least five distinct known master cases')
    if not any(metadata[cid]['tier'] == 'L' for cid in ids) or not any(metadata[cid]['tier'] == 'X' for cid in ids):
        raise InvalidInputError('campaign evidence must include L and a trap case')
    if not all(any(metadata[cid]['case_no'] == trap for cid in ids) for trap in (47, 48)):
        raise InvalidInputError('this report demonstrates both trap 47 and 48; include both')
    out = Path(args.out)
    (out / 'campaign').mkdir(parents=True, exist_ok=True)
    (out / 'sample-outputs').mkdir(exist_ok=True)
    cases = load_cases(args.master, ids)
    reports, human = {}, []
    for cid in ids:
        reports[cid] = {}
        for policy in POLICIES:
            print(f'{cid}: running {policy}', flush=True)
            reports[cid][policy] = run_campaign(cases[cid], policy=policy)
        compare(reports[cid])
        evidence = dict(master_version='master_release_v1', case_input=asdict(cases[cid]),
                        calendar=official_calendar(), policies=reports[cid])
        (out / 'campaign' / f'{cid}.json').write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        human.append(campaign_text(reports[cid]))
        print(f'{cid}: all daily invariants and exact baselines agree', flush=True)
    (out / 'sample-outputs/campaign-official.txt').write_text('\n'.join(human), encoding='utf-8')
    summary, daily = write_report(out, reports, metadata)
    print(f'Completed {len(reports)} cases, {len(daily)} daily policy records, {len(summary)} summaries.', flush=True)


if __name__ == '__main__':
    main()
