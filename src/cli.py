"""python -m src.cli --master MASTER campaign --case 41-00 --calendar ..."""
import argparse
import json
from pathlib import Path

from .backend import Backend
from .loader import verify_checksums
from .models import InvalidInputError, TimeBudgetExceeded


def main(argv=None):
    parser = argparse.ArgumentParser(description='LIFELINE campaign and planning')
    parser.add_argument('--master', default='MASTER')
    parser.add_argument('--output', help='save JSON output')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('cases')
    sub.add_parser('verify')
    campaign = sub.add_parser('campaign')
    campaign.add_argument('--case', required=True)
    campaign.add_argument('--calendar', required=True)
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
            calendar = json.loads(Path(args.calendar).read_text(encoding='utf-8'))
            result = backend.campaign(args.case, calendar)
            if args.compare:
                result = {'optimized': result, 'simple': backend.campaign(args.case, calendar, 'simple')}
        text = json.dumps(result, indent=2, allow_nan=False)
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
