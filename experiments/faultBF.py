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
]


def run(root):
    env = dict(os.environ, PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE='1')
    return subprocess.run([sys.executable, '-m', 'unittest', 'tests.testhamza'], cwd=root,
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
        (target / 'tests').mkdir()
        (target / 'tests/__init__.py').write_text('')
        shutil.copy2(ROOT / 'tests/testhamza.py', target / 'tests/testhamza.py')
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
