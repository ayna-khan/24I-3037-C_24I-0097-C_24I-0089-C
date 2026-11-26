"""python -m src.cli --master MASTER campaign --case 41-00 --calendar ..."""
import argparse
import json
from pathlib import Path

from .backend import Backend
from .loader import verify_checksums
from .models import InvalidInputError, TimeBudgetExceeded


def campaign_text(result):
    """Readable daily decisions and checked constraints; full JSON is optional."""
    parts = []
    reports = [result] if 'days' in result else list(result.values())
    for report in reports:
        parts += [f"Case {report['case_id']} | {report['policy']} | {report['calendar']['name']}",
                  'Day | Event | Target | Blocked | Trip | Route cost | Load value | Rescue total | Urgent wait']
        for d in report['days']:
            parts.append(f"{d['day']:>3} | {d['event']} | {d['target']} | {len(d['closed_roads'])} | "
                         f"{d['dispatch_status']} | {d['route']['cost']} | "
                         f"{d['load']['total_value'] if d['load'] else '-'} | {d['rescue']['total']} | "
                         f"{d['alarm_metrics']['urgent_wait'] / max(1, d['alarm_metrics']['urgent_count']):.3f}")
            parts.append(f"    Input: {d['input']['counts']}; capacity={d['input']['capacity']}; "
                         f"wave labels={d['input']['resolved_wave_labels']}; methods={d['methods']}")
            parts.append('    Checked: ' + ', '.join(d['checks']))
        parts += [f"Summary: {report['summary']}", '']
    return '\n'.join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description='LIFELINE campaign and planning')
    parser.add_argument('--master', default='MASTER')
    parser.add_argument('--output', help='save JSON output')
    parser.add_argument('--format', choices=('text', 'json'), help='campaign display format; files default to JSON')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('cases')
    sub.add_parser('verify')
    campaign = sub.add_parser('campaign')
    campaign.add_argument('--case', required=True)
    campaign.add_argument('--calendar', help='custom JSON calendar; defaults to official section 7.4 rules')
    campaign.add_argument('--compare', action='store_true')
    for name in ('route', 'network'):
        p = sub.add_parser(name)
        p.add_argument('--case', required=True)
        p.add_argument('--blocked', type=int, nargs='*', default=[])
        if name == 'route':
            p.add_argument('--target', type=int, required=True)
    args = parser.parse_args(argv)
    backend = Backend(args.master)
    try:
        if args.command == 'verify':
            result = {'verified': verify_checksums(args.master)}
        elif args.command == 'cases':
            result = backend.list_cases()
        elif args.command == 'route':
            result = backend.route(args.case, args.target, blocked=args.blocked)
        elif args.command == 'network':
            result = backend.network(args.case, args.blocked)
        else:
            calendar = json.loads(Path(args.calendar).read_text(encoding='utf-8')) if args.calendar else None
            result = backend.campaign(args.case, calendar)
            if args.compare:
                result = {'optimized': result, 'baseline': backend.campaign(args.case, calendar, 'baseline'),
                          'simple': backend.campaign(args.case, calendar, 'simple')}
        use_text = args.command == 'campaign' and (args.format == 'text' or (not args.format and not args.output))
        text = campaign_text(result) if use_text else json.dumps(result, indent=2, allow_nan=False)
        if args.output:
            dest = Path(args.output)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text + '\n', encoding='utf-8')
        else:
            print(text)
        return 0
    except (InvalidInputError, TimeBudgetExceeded, OSError, ValueError) as exc:
        print(json.dumps({'status': 'INVALID', 'note': str(exc)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
