"""B: BFS reachability/fewest roads; positive-cost Dijkstra or Bellman-Ford.

Roads are undirected, but u -> v costs minutes + penalty[v]. Source penalty
is not charged. Equal distances keep the first predecessor. Adjacencies and
heap ties use location id then road id, making output independent of file order.
"""
from collections import deque
from typing import NamedTuple

from ..models import InvalidInputError
from ..network import Heap, adjacency, budget, counts, ordered, validate


class RoutePlan(NamedTuple):
    status: str
    source: int
    target: int
    path: tuple
    road_ids: tuple
    cost: object
    reachable: tuple
    distances: dict
    fewest_path: tuple
    fewest_cost: object
    ops: dict
    note: str = ''


def _path(parent, source, target):
    if target != source and target not in parent:
        return (), ()
    vertices, edges = [target], []
    while vertices[-1] != source:
        prev, rid = parent[vertices[-1]]
        vertices.append(prev)
        edges.append(rid)
    return tuple(reversed(vertices)), tuple(reversed(edges))


def solve(locations, roads, target, method='dijkstra', blocked=(), source=0, deadline=None):
    budget(deadline)
    locations, roads = tuple(locations), tuple(roads)
    nodes, blocked = validate(locations, roads, blocked, source)
    if type(target) is not int or target not in nodes:
        raise InvalidInputError('target must identify a location')
    if method not in ('dijkstra', 'bellman', 'bfs'):
        raise InvalidInputError('route method must be dijkstra, bellman or bfs')
    ops = counts()
    adj = adjacency(nodes, roads, blocked, ops)
    hops, bfs_parent, queue = {source: 0}, {}, deque([source])
    while queue:
        budget(deadline)
        u = queue.popleft()
        for v, r in adj[u]:
            ops['edge_tests'] += 1
            if v not in hops:
                hops[v] = hops[u] + 1
                bfs_parent[v] = (u, r.road_no)
                queue.append(v)
    dist, parent = {v: None for v in nodes}, {}
    dist[source] = 0
    if method == 'dijkstra':
        heap = Heap(ops)
        heap.push((0, source))
        while heap:
            budget(deadline)
            du, u = heap.pop()
            if du != dist[u]:
                continue
            for v, r in adj[u]:
                ops['edge_tests'] += 1
                candidate = du + r.minutes + nodes[v].penalty
                if dist[v] is None or candidate < dist[v]:
                    dist[v], parent[v] = candidate, (u, r.road_no)
                    ops['relaxations'] += 1
                    heap.push((candidate, v))
    elif method == 'bellman':
        order = ordered(nodes, lambda x: x, ops)
        for _ in range(len(nodes) - 1):
            budget(deadline)
            changed = False
            for u in order:
                budget(deadline)
                if dist[u] is None:
                    continue
                for v, r in adj[u]:
                    ops['edge_tests'] += 1
                    candidate = dist[u] + r.minutes + nodes[v].penalty
                    if dist[v] is None or candidate < dist[v]:
                        dist[v], parent[v] = candidate, (u, r.road_no)
                        ops['relaxations'] += 1
                        changed = True
            if not changed:
                break
    else:
        parent = bfs_parent
        for v in hops:  # BFS discovery order: parent distance is already known
            if v != source:
                u, rid = parent[v]
                road = next(r for w, r in adj[u] if w == v and r.road_no == rid)
                dist[v] = dist[u] + road.minutes + nodes[v].penalty
    path, road_ids = _path(parent, source, target)
    fewest, fewest_edges = _path(bfs_parent, source, target)
    by_id = {r.road_no: r for r in roads}
    fewest_cost = (sum(by_id[rid].minutes + nodes[v].penalty
                       for rid, v in zip(fewest_edges, fewest[1:])) if fewest else None)
    return RoutePlan('OK' if path else 'NO_ROUTE', source, target, path, road_ids,
                     dist[target], tuple(ordered(hops, lambda x: x, ops)), dist,
                     fewest, fewest_cost, ops,
                     'BFS minimizes road count, not travel cost' if method == 'bfs' else '')
