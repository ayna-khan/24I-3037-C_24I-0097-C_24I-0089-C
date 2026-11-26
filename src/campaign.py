"""Seven-day coordinator. Calendar rules are data, never hidden in solvers."""
from copy import deepcopy
import json
from pathlib import Path

from .models import InvalidInputError
from .network import integer, budget
from .modules import inventory, emergencyqueue, rescue, chains, routes, networkplan
from .campaign_checks import verify_day, verify_review


def official_calendar():
    """Fresh copy of the prescribed, case-independent section 7.4 calendar."""
    return json.loads((Path(__file__).resolve().parents[1] / 'calendars/official.json').read_text(encoding='utf-8'))


def validate_calendar(calendar, case):
    if not isinstance(calendar, dict) or set(calendar) - {'name', 'note', 'inventory_mode', 'closure_mode', 'days'}:
        raise InvalidInputError('calendar must contain name/note, inventory_mode and days only')
    if calendar.get('inventory_mode', 'daily') not in ('daily', 'consume'):
        raise InvalidInputError('inventory_mode must be daily or consume')
    if calendar.get('closure_mode', 'cumulative') not in ('daily', 'cumulative'):
        raise InvalidInputError('closure_mode must be daily or cumulative')
    days = calendar.get('days')
    if not isinstance(days, list) or len(days) != 7:
        raise InvalidInputError('calendar requires exactly seven days in order')
    known = {'day', 'target', 'close_waves', 'close_roads', 'open_roads', 'multipliers',
             'extra_alarms', 'hour', 'capacity', 'load', 'objective', 'review', 'event',
             'target_key', 'wave_indices', 'all_waves', 'minutes_ratio',
             'penalty_threshold', 'penalty_multiplier', 'evacuation'}
    node_ids, road_ids = {n.loc_id for n in case.locations}, {r.road_no for r in case.roads}
    for expected, event in enumerate(days, 1):
        if not isinstance(event, dict) or set(event) - known:
            raise InvalidInputError('calendar has an unknown daily field')
        integer(event.get('day'), 'day', 1)
        if event['day'] != expected:
            raise InvalidInputError('calendar days must be exactly 1..7')
        if 'target_key' in event and (event['target_key'] not in ('target_0', 'target_1', 'target_2') or 'target' in event):
            raise InvalidInputError('target_key must name one target, without a literal target override')
        target = case.metadata[event['target_key']] if 'target_key' in event else event.get('target', case.metadata['target_0'])
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
        for field in ('load', 'review', 'all_waves', 'evacuation'):
            if field in event and type(event[field]) is not bool:
                raise InvalidInputError(f'{field} must be a boolean')
        if event.get('evacuation', False) and (expected != 7 or event.get('load', True)):
            raise InvalidInputError('evacuation is day 7 with loading disabled')
        indices = event.get('wave_indices', [])
        if not isinstance(indices, list) or any(type(i) is not int or i < 0 for i in indices):
            raise InvalidInputError('wave_indices must be nonnegative integer positions')
        if indices and not case.waves:
            raise InvalidInputError('cannot index a case with no closure waves')
        ratio = event.get('minutes_ratio', [1, 1])
        if not isinstance(ratio, (list, tuple)) or len(ratio) != 2:
            raise InvalidInputError('minutes_ratio must be [positive numerator, denominator]')
        for value in ratio:
            integer(value, 'minutes ratio', 1)
        integer(event.get('penalty_threshold', 0), 'penalty threshold')
        integer(event.get('penalty_multiplier', 1), 'penalty multiplier', 1)
        if 'event' in event and not isinstance(event['event'], str):
            raise InvalidInputError('event label must be text')
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


def run_campaign(case, calendar=None, policy='optimized', deadline=None):
    """Run the official calendar by default; custom calendar remains supported.

    Baseline algorithms: greedy load, Bellman-Ford, quadratic rescue DP, scan
    urgency queue, Prim and memoized G. Simple policy: BFS/value-greedy/FIFO.
    It runs independently from the optimized policy (including stock state).
    F/G are optional review actions; original case/calendar are never modified.
    A day without a route has no dispatch, but still schedules rescue/alarms.
    """
    calendar = official_calendar() if calendar is None else calendar
    validate_calendar(calendar, case)
    if policy not in ('optimized', 'baseline', 'simple'):
        raise InvalidInputError('policy must be optimized, baseline or simple')
    closed, consumed, outputs = set(), set(), []
    for event in calendar['days']:
        budget(deadline)
        day = event['day']
        if calendar.get('closure_mode', 'cumulative') == 'daily':
            closed.clear()
        for wave in event.get('close_waves', []):
            closed.update(case.waves[wave])
        wave_labels = sorted(case.waves)
        resolved_waves = [wave_labels[i % len(wave_labels)] for i in event.get('wave_indices', [])]
        for wave in resolved_waves:
            closed.update(case.waves[wave])
        if event.get('all_waves', False):
            for ids in case.waves.values():
                closed.update(ids)
        closed.update(event.get('close_roads', []))
        closed.difference_update(event.get('open_roads', []))
        target = case.metadata[event['target_key']] if 'target_key' in event else event.get('target', case.metadata['target_0'])
        numerator, denominator = event.get('minutes_ratio', [1, 1])
        roads = tuple(r._replace(minutes=(r.minutes * numerator + denominator - 1) // denominator) for r in case.roads)
        threshold, multiplier = event.get('penalty_threshold', 0), event.get('penalty_multiplier', 1)
        locations = tuple(n._replace(penalty=n.penalty * multiplier if n.penalty >= threshold else n.penalty)
                          for n in case.locations)
        route = routes.solve(locations, roads, target,
                              {'optimized': 'dijkstra', 'baseline': 'bellman', 'simple': 'bfs'}[policy], closed, deadline=deadline)
        base = [c for c in case.crates if c.crate_id not in consumed
                and ('hour' not in event or c.expiry >= event['hour'])]
        crates = inventory.with_day_values(base, {int(k): v for k, v in event.get('multipliers', {}).items()})
        load = None
        capacity = event.get('capacity', case.metadata['capacity'])
        if event.get('load', True) and route.status == 'OK':
            load = inventory.solve(crates, capacity,
                                    'dp' if policy == 'optimized' else 'greedy', deadline)
            if calendar.get('inventory_mode', 'daily') == 'consume':
                consumed.update(load.selected)
        available = rescue.available_on_day(case.windows, day)
        objective = event.get('objective', 'value')
        rescue_method = {'optimized': 'greedy' if objective == 'count' else 'dp',
                         'baseline': 'dpquad', 'simple': 'greedy'}[policy]
        schedule = rescue.solve(available, objective, rescue_method, deadline)
        alarms = emergencyqueue.with_extra_alarms(case.alarms, event.get('extra_alarms', []))
        queue = (emergencyqueue.release_order(alarms, 'heap' if policy == 'optimized' else 'scan', deadline) if policy != 'simple'
                 else emergencyqueue.release_fifo(alarms, deadline))
        release_ticks = dict(queue.releases)
        urgent_waits = [release_ticks[a.alarm_id] - a.tick for a in alarms if a.priority >= 9]
        trip_made = route.status == 'OK' and (event.get('load', True) or event.get('evacuation', False))
        checks = verify_day(locations, roads, closed, target, crates, capacity, available, alarms,
                            route, load, schedule, queue, objective, policy)
        entry = dict(day=day, event=event.get('event', 'Custom'), target=target, closed_roads=sorted(closed), route=route._asdict(),
                     load=load._asdict() if load else None,
                     trip_made=trip_made, trip_kind='evacuation' if event.get('evacuation', False) else 'delivery',
                     dispatch_status=('NO_ROUTE' if route.status == 'NO_ROUTE' else
                                      'EVACUATION' if event.get('evacuation', False) and trip_made else
                                      'SKIPPED' if not event.get('load', True)
                                      else (load.status if load else route.status)),
                     rescue=schedule._asdict(), alarms=queue._asdict(),
                     alarm_metrics=dict(urgent_count=len(urgent_waits), urgent_wait=sum(urgent_waits),
                                        urgent_max_wait=max(urgent_waits, default=0)),
                     checks=checks,
                     input=dict(base_case=case.metadata['case_id'], source=0, target=target, capacity=capacity,
                                resolved_wave_labels=resolved_waves, all_waves=event.get('all_waves', False),
                                changed_minutes={r.road_no: r.minutes for r, base in zip(roads, case.roads) if r.minutes != base.minutes},
                                changed_penalties={n.loc_id: n.penalty for n, base in zip(locations, case.locations) if n.penalty != base.penalty},
                                multipliers=deepcopy(event.get('multipliers', {})),
                                eligible_crate_ids=[c.crate_id for c in crates],
                                available_window_ids=[w.window_id for w in available],
                                objective=objective, extra_alarms=[a._asdict() for a in alarms[len(case.alarms):]],
                                counts=dict(locations=len(locations), roads=len(roads), crates=len(crates),
                                            windows=len(available), alarms=len(alarms))),
                     methods=dict(A='dp' if policy == 'optimized' else 'greedy',
                                  B={'optimized': 'dijkstra', 'baseline': 'bellman', 'simple': 'bfs'}[policy],
                                  C=rescue_method, D={'optimized': 'heap', 'baseline': 'scan', 'simple': 'fifo'}[policy]))
        if event.get('review', False):
            network = networkplan.solve(locations, roads, 'prim' if policy == 'baseline' else 'kruskal', blocked=closed,
                                         vertices=route.reachable, deadline=deadline)
            chain = chains.solve_chain(case.dims, 'memo' if policy == 'baseline' else 'dp', deadline)
            drum = chains.solve_drum(case.prices, len(case.prices), 'memo' if policy == 'baseline' else
                                     'greedy' if policy == 'simple' else 'dp', deadline)
            entry.update(network=network._asdict(), chain=chain._asdict(), drum=drum._asdict())
            entry['checks'].update(verify_review(case, roads, closed, route.reachable, network, chain, drum))
            entry['methods'].update(F='prim' if policy == 'baseline' else 'kruskal',
                                    G_chain='memo' if policy == 'baseline' else 'dp',
                                    G_drum='memo' if policy == 'baseline' else 'greedy' if policy == 'simple' else 'dp')
        outputs.append(entry)
    return dict(case_id=case.metadata['case_id'], calendar=deepcopy(calendar), policy=policy, days=outputs,
                summary=dict(delivered_value=sum(d['load']['total_value'] for d in outputs if d['load']),
                             route_cost=sum(d['route']['cost'] for d in outputs
                                            if d['trip_made']),
                             evacuation_cost=next((d['route']['cost'] for d in outputs
                                                   if d['trip_kind'] == 'evacuation' and d['trip_made']), None),
                             unreachable_days=sum(d['route']['status'] == 'NO_ROUTE' for d in outputs),
                             rescue_total=sum(d['rescue']['total'] for d in outputs),
                             alarm_wait=sum(d['alarms']['total_wait'] for d in outputs),
                             urgent_mean_wait=(sum(d['alarm_metrics']['urgent_wait'] for d in outputs)
                                               / max(1, sum(d['alarm_metrics']['urgent_count'] for d in outputs)))))
