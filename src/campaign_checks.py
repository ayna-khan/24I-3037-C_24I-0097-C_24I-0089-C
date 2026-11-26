"""Independent output verification, separate from the evaluated algorithms.

The standard-library heap below is a verifier, never a decision algorithm.
Checks fail explicitly rather than persisting a plausible invalid campaign.
"""
import heapq
import re

from .models import InvalidInputError


def require(condition, note):
    if not condition:
        raise InvalidInputError('campaign output invariant failed: ' + note)


def verify_day(locations, roads, closed, target, crates, capacity, windows, alarms,
               route, load, schedule, queue, objective, policy):
    nodes = {n.loc_id: n for n in locations}
    by_road = {r.road_no: r for r in roads}
    adj = {v: [] for v in nodes}
    for r in roads:
        if r.road_no not in closed:
            adj[r.u].append(r.v)
            adj[r.v].append(r.u)
    reachable, pending = {0}, [0]
    while pending:
        for v in adj[pending.pop()]:
            if v not in reachable:
                reachable.add(v)
                pending.append(v)
    require(set(route.reachable) == reachable, 'reachable set')
    if target not in reachable:
        require(route.status == 'NO_ROUTE' and not route.path and route.cost is None and load is None,
                'unreachable destination must skip dispatch')
    else:
        require(route.status == 'OK' and route.path[0] == 0 and route.path[-1] == target,
                'route endpoints and status')
        require(len(route.road_ids) == len(route.path) - 1, 'route length')
        cost = 0
        for u, v, rid in zip(route.path, route.path[1:], route.road_ids):
            require(rid in by_road and rid not in closed, 'route uses an open road')
            r = by_road[rid]
            require({u, v} == {r.u, r.v}, 'route road endpoints')
            cost += r.minutes + nodes[v].penalty
        require(cost == route.cost, 'route cost matches daily weights')
    if load is not None:
        by_crate = {c.crate_id: c for c in crates}
        require(load.status in ('OK', 'EMPTY') and len(set(load.selected)) == len(load.selected), 'load status/ids')
        require(set(load.selected) <= by_crate.keys(), 'load uses eligible crates')
        require(sum(by_crate[i].weight for i in load.selected) == load.total_weight <= capacity,
                'load capacity and weight')
        require(sum(by_crate[i].value for i in load.selected) == load.total_value, 'daily load value')
    by_window = {w.window_id: w for w in windows}
    require(schedule.status in ('OK', 'EMPTY') and len(set(schedule.chosen)) == len(schedule.chosen), 'rescue status/ids')
    require(set(schedule.chosen) <= by_window.keys(), 'rescue availability')
    chosen = sorted((by_window[i] for i in schedule.chosen), key=lambda w: (w.start, w.finish))
    require(all(a.finish <= b.start for a, b in zip(chosen, chosen[1:])), 'rescue compatibility')
    require(schedule.total == (len(chosen) if objective == 'count' else sum(w.value for w in chosen)),
            'rescue objective total')
    arrival = sorted(alarms, key=lambda a: (a.tick, a.alarm_id))
    expected, heap, i, now = [], [], 0, 0
    while i < len(arrival) or heap:
        if not heap:
            now = max(now, arrival[i].tick)
        while i < len(arrival) and arrival[i].tick <= now:
            a = arrival[i]
            key = (a.tick, a.alarm_id) if policy == 'simple' else (-a.priority, a.tick, a.alarm_id)
            heapq.heappush(heap, (key, a.alarm_id))
            i += 1
        _, aid = heapq.heappop(heap)
        expected.append((aid, now))
        now += 1
    require(tuple(expected) == queue.releases, 'alarm arrival, urgency/FIFO, one release per tick')
    return dict(reachability=True, route_open_roads_and_cost=True, capacity_and_load_value=True,
                rescue_availability_compatibility_and_total=True, alarm_order_and_release_ticks=True)


def verify_review(case, roads, closed, reachable, network, chain, drum):
    require(network.status == 'OK', 'HQ component must have a cable tree')
    subset, chosen = set(reachable), set(network.road_ids)
    require(len(chosen) == len(network.road_ids) == max(0, len(subset) - 1), 'tree edge count')
    edges = {r.road_no: r for r in roads}
    adj = {v: [] for v in subset}
    for rid in chosen:
        require(rid in edges and rid not in closed, 'cable road must be open')
        r = edges[rid]
        require(r.u in subset and r.v in subset, 'cable endpoints in HQ component')
        adj[r.u].append(r.v)
        adj[r.v].append(r.u)
    seen, pending = {0}, [0]
    while pending:
        for v in adj[pending.pop()]:
            if v not in seen:
                seen.add(v)
                pending.append(v)
    require(seen == subset and sum(edges[i].cable for i in chosen) == network.cost, 'cable connectivity/cost')
    require(chain.status == drum.status == 'OK', 'G review must produce a valid plan')
    stack = []
    for token in re.findall(r'A\d+|[()]', chain.bracketing):
        if token == '(':
            stack.append(token)
        elif token.startswith('A'):
            i = int(token[1:])
            require(1 <= i < len(case.dims), 'matrix id range')
            stack.append((i, i, 0))
        else:
            require(len(stack) >= 3, 'matrix bracketing structure')
            right, left, opening = stack.pop(), stack.pop(), stack.pop()
            require(opening == '(' and isinstance(left, tuple) and isinstance(right, tuple), 'matrix bracket pairs')
            require(left[1] + 1 == right[0], 'matrix order')
            cost = left[2] + right[2] + case.dims[left[0] - 1] * case.dims[left[1]] * case.dims[right[1]]
            stack.append((left[0], right[1], cost))
    require(stack == [(1, len(case.dims) - 1, chain.cost)], 'matrix coverage/cost')
    require(all(type(n) is int and 1 <= n <= len(case.prices) for n in drum.pieces), 'drum pieces')
    require(sum(drum.pieces) == len(case.prices), 'drum length')
    require(sum(case.prices[n - 1] for n in drum.pieces) == drum.price, 'drum revenue')
    return dict(cable_tree_connects_hq_component=True, chain_bracketing_cost=True, drum_length_and_price=True)
