"""Seven-day coordinator. Calendar rules are data, never hidden in solvers."""
from copy import deepcopy

from .models import InvalidInputError
from .network import integer, budget
from .modules import inventory, emergencyqueue, rescue, chains, routes, networkplan


def validate_calendar(calendar, case):
    if not isinstance(calendar, dict) or set(calendar) - {'name', 'note', 'inventory_mode', 'days'}:
        raise InvalidInputError('calendar must contain name/note, inventory_mode and days only')
    if calendar.get('inventory_mode', 'daily') not in ('daily', 'consume'):
        raise InvalidInputError('inventory_mode must be daily or consume')
    days = calendar.get('days')
    if not isinstance(days, list) or len(days) != 7:
        raise InvalidInputError('calendar requires exactly seven days in order')
    known = {'day', 'target', 'close_waves', 'close_roads', 'open_roads', 'multipliers',
             'extra_alarms', 'hour', 'capacity', 'load', 'objective', 'review'}
    node_ids, road_ids = {n.loc_id for n in case.locations}, {r.road_no for r in case.roads}
    for expected, event in enumerate(days, 1):
        if not isinstance(event, dict) or set(event) - known:
            raise InvalidInputError('calendar has an unknown daily field')
        integer(event.get('day'), 'day', 1)
        if event['day'] != expected:
            raise InvalidInputError('calendar days must be exactly 1..7')
        target = event.get('target', case.metadata['target_0'])
        if type(target) is not int or target not in node_ids:
            raise InvalidInputError('calendar target is unknown')
        for field, ids in [('close_waves', case.waves), ('close_roads', road_ids), ('open_roads', road_ids)]:
            values = event.get(field, [])
            if not isinstance(values, list) or any(type(v) is not int or v not in ids for v in values):
                raise InvalidInputError(f'calendar {field} contains unknown ids')
        if set(event.get('open_roads', [])) & set(event.get('close_roads', [])):
            raise InvalidInputError('cannot explicitly open and close a road on the same day')
        if 'hour' in event:
            integer(event['hour'], 'hour')
        if 'capacity' in event:
            integer(event['capacity'], 'capacity')
        for field in ('load', 'review'):
            if field in event and type(event[field]) is not bool:
                raise InvalidInputError(f'{field} must be a boolean')
        if event.get('objective', 'value') not in ('count', 'value'):
            raise InvalidInputError('objective must be count or value')
        multipliers = event.get('multipliers', {})
        if not isinstance(multipliers, dict):
            raise InvalidInputError('multipliers must map category numbers to integers')
        for cat, multiplier in multipliers.items():
            if str(cat) not in ('0', '1', '2', '3', '4'):
                raise InvalidInputError('unknown multiplier category')
            integer(multiplier, 'multiplier')
        extras = event.get('extra_alarms', [])
        if not isinstance(extras, list):
            raise InvalidInputError('extra_alarms must be a list')
        for alarm in extras:
            if not isinstance(alarm, (list, tuple)) or len(alarm) != 2:
                raise InvalidInputError('extra alarm must be [tick, priority]')
            tick, priority = alarm
            integer(tick, 'alarm tick')
            integer(priority, 'alarm priority', 1)
            if priority > 10:
                raise InvalidInputError('alarm priority exceeds 10')


def run_campaign(case, calendar, policy='optimized', deadline=None):
    """Apply cumulative road changes, daily values/filtering and A/B/C/D.

    Baseline: ratio load, BFS route, earliest-finish value schedule, FIFO queue.
    It runs independently from the optimized policy (including stock state).
    F/G are optional review actions; original case/calendar are never modified.
    A day without a route has no dispatch, but still schedules rescue/alarms.
    """
    validate_calendar(calendar, case)
    if policy not in ('optimized', 'simple'):
        raise InvalidInputError('policy must be optimized or simple')
    closed, consumed, outputs = set(), set(), []
    for event in calendar['days']:
        budget(deadline)
        day = event['day']
        for wave in event.get('close_waves', []):
            closed.update(case.waves[wave])
        closed.update(event.get('close_roads', []))
        closed.difference_update(event.get('open_roads', []))
        target = event.get('target', case.metadata['target_0'])
        route = routes.solve(case.locations, case.roads, target,
                              'dijkstra' if policy == 'optimized' else 'bfs', closed, deadline=deadline)
        base = [c for c in case.crates if c.crate_id not in consumed
                and ('hour' not in event or c.expiry >= event['hour'])]
        crates = inventory.with_day_values(base, {int(k): v for k, v in event.get('multipliers', {}).items()})
        load = None
        if event.get('load', True) and route.status == 'OK':
            load = inventory.solve(crates, event.get('capacity', case.metadata['capacity']),
                                    'dp' if policy == 'optimized' else 'greedy', deadline)
            if calendar.get('inventory_mode', 'daily') == 'consume':
                consumed.update(load.selected)
        available = rescue.available_on_day(case.windows, day)
        objective = event.get('objective', 'value')
        schedule = rescue.solve(available, objective,
                                ('greedy' if objective == 'count' else 'dp') if policy == 'optimized' else 'greedy', deadline)
        alarms = emergencyqueue.with_extra_alarms(case.alarms, event.get('extra_alarms', []))
        queue = (emergencyqueue.release_order(alarms, 'heap', deadline) if policy == 'optimized'
                 else emergencyqueue.release_fifo(alarms, deadline))
        release_ticks = dict(queue.releases)
        urgent_waits = [release_ticks[a.alarm_id] - a.tick for a in alarms if a.priority >= 9]
        entry = dict(day=day, target=target, closed_roads=sorted(closed), route=route._asdict(),
                     load=load._asdict() if load else None,
                     dispatch_status=('SKIPPED' if not event.get('load', True)
                                      else (load.status if load else route.status)),
                     rescue=schedule._asdict(), alarms=queue._asdict(),
                     alarm_metrics=dict(urgent_count=len(urgent_waits), urgent_wait=sum(urgent_waits),
                                        urgent_max_wait=max(urgent_waits, default=0)))
        if event.get('review', False):
            entry['network'] = networkplan.solve(case.locations, case.roads, blocked=closed,
                                                  vertices=route.reachable, deadline=deadline)._asdict()
            entry['chain'] = chains.solve_chain(case.dims, 'dp', deadline)._asdict()
            entry['drum'] = chains.solve_drum(case.prices, len(case.prices), 'dp', deadline)._asdict()
        outputs.append(entry)
    return dict(case_id=case.metadata['case_id'], calendar=deepcopy(calendar), policy=policy, days=outputs,
                summary=dict(delivered_value=sum(d['load']['total_value'] for d in outputs if d['load']),
                             route_cost=sum(d['route']['cost'] for d in outputs
                                            if d['load'] and d['load']['selected']),
                             unreachable_days=sum(d['route']['status'] == 'NO_ROUTE' for d in outputs),
                             rescue_total=sum(d['rescue']['total'] for d in outputs),
                             alarm_wait=sum(d['alarms']['total_wait'] for d in outputs),
                             urgent_mean_wait=(sum(d['alarm_metrics']['urgent_wait'] for d in outputs)
                                               / max(1, sum(d['alarm_metrics']['urgent_count'] for d in outputs)))))
