"""Seed real faults in disposable copies; require a clean baseline and caught faults."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = [
    ('B-destination-penalty', 'src/modules/routes.py', 'du + r.minutes + nodes[v].penalty', 'du + r.minutes'),
    ('B-wrong-relaxation', 'src/modules/routes.py', 'candidate < dist[v]', 'candidate > dist[v]'),
    ('B-ignore-closures', 'src/modules/routes.py', 'adjacency(nodes, roads, blocked, ops)', 'adjacency(nodes, roads, (), ops)'),
    ('F-descending-edges', 'src/modules/networkplan.py', '(r.cable, r.road_no, r.u, r.v)', '(-r.cable, r.road_no, r.u, r.v)'),
    ('F-discard-tree-edges', 'src/modules/networkplan.py', 'if union(r.u, r.v):', 'if not union(r.u, r.v):'),
    ('F-ignore-closures', 'src/modules/networkplan.py', 'r.road_no not in blocked and', 'True and'),
    ('campaign-skip-day-values', 'src/campaign.py', "{int(k): v for k, v in event.get('multipliers', {}).items()}", '{}'),
    ('campaign-skip-availability', 'src/campaign.py', 'rescue.available_on_day(case.windows, day)', 'list(case.windows)'),
    ('campaign-forget-closures', 'src/campaign.py', 'closed.update(case.waves[wave])', 'closed.update(())'),
    ('loader-truncate-floats', 'src/loader.py', 'else int(v)', 'else int(float(v))'),
    ('calendar-no-storm-ceiling', 'src/campaign.py', '(r.minutes * numerator + denominator - 1) // denominator', '(r.minutes * numerator) // denominator'),
    ('calendar-no-penalty-change', 'src/campaign.py', 'n.penalty * multiplier if n.penalty >= threshold else n.penalty', 'n.penalty'),
    ('calendar-accumulate-daily-waves', 'src/campaign.py', "calendar.get('closure_mode', 'cumulative') == 'daily'", 'False'),
    ('calendar-no-wave-modulo', 'src/campaign.py', 'wave_labels[i % len(wave_labels)]', 'wave_labels[i]'),
    ('calendar-drop-evacuation-cost', 'src/campaign.py', "if d['trip_made']),", "if d['load'] and d['load']['selected']),"),
]


def run(root):
    env = dict(os.environ, PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE='1')
    return subprocess.run([sys.executable, '-m', 'unittest', 'tests.testhamza', 'tests.testofficialcampaign'], cwd=root,
                          env=env, capture_output=True, text=True, timeout=5)


def main():
    baseline = run(ROOT)
    if baseline.returncode:
        raise RuntimeError(baseline.stdout + baseline.stderr)
    report = ['Fault injection of B/F, loader and campaign', 'Baseline: PASS', '']
    killed = 0
    with tempfile.TemporaryDirectory(prefix='lifeline-fault-') as temp:
        target = Path(temp)
        shutil.copytree(ROOT / 'src', target / 'src', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT / 'calendars', target / 'calendars')
        shutil.copytree(ROOT / 'experiments', target / 'experiments', ignore=shutil.ignore_patterns('__pycache__'))
        (target / 'tests').mkdir()
        (target / 'tests/__init__.py').write_text('')
        shutil.copy2(ROOT / 'tests/testhamza.py', target / 'tests/testhamza.py')
        shutil.copy2(ROOT / 'tests/testofficialcampaign.py', target / 'tests/testofficialcampaign.py')
        clean_copy = run(target)
        if clean_copy.returncode:
            raise RuntimeError('Unmodified disposable copy failed: ' + clean_copy.stdout + clean_copy.stderr)
        for name, file, old, new in MUTANTS:
            path = target / file
            original = path.read_text(encoding='utf-8')
            if old not in original:
                raise RuntimeError(f'Mutation anchor missing: {name}')
            path.write_text(original.replace(old, new, 1), encoding='utf-8')
            try:
                try:
                    result = run(target)
                    caught = result.returncode != 0 and ('FAIL:' in result.stderr or 'ERROR:' in result.stderr)
                    reason = 'test assertion/error' if caught else 'no failing test'
                except subprocess.TimeoutExpired:
                    caught, reason = True, '5-second timeout (baseline under one second)'
                killed += caught
                report.append(f'{name}: {"CAUGHT" if caught else "SURVIVED"} ({reason})')
                print(report[-1], flush=True)
            finally:
                path.write_text(original, encoding='utf-8')
    report += ['', f'SUMMARY: {killed}/{len(MUTANTS)} faults caught. Production files untouched.']
    (ROOT / 'results/fault-injection-BF.txt').write_text('\n'.join(report) + '\n')
    return 0 if killed == len(MUTANTS) else 1


if __name__ == '__main__':
    raise SystemExit(main())
