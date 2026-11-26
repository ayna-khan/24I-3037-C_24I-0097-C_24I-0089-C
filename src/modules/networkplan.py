"""F: minimum cable forest using Kruskal/union-find or independent heap Prim.

By default spans all components. Pass vertices=route.reachable for HQ-only
planning. Equal-cost edges use road id, then endpoints, as a total order.
"""
from typing import NamedTuple

from ..models import InvalidInputError
from ..network import Heap, adjacency, budget, counts, ordered, validate


class NetworkPlan(NamedTuple):
    status: str
    road_ids: tuple
    cost: int
    components: tuple
    ops: dict
    note: str = ''


def solve(locations, roads, method='kruskal', blocked=(), vertices=None, source=0, deadline=None):
    budget(deadline)
    locations, roads = tuple(locations), tuple(roads)
    nodes, blocked = validate(locations, roads, blocked, source)
    if method not in ('kruskal', 'prim'):
        raise InvalidInputError('network method must be kruskal or prim')
    selected = set(nodes) if vertices is None else set(vertices)
    if any(type(v) is not int or v not in nodes for v in selected):
        raise InvalidInputError('network subset contains an unknown location')
    ops = counts()
    edges = [r for r in roads if r.road_no not in blocked and r.u in selected and r.v in selected]
    parent, size = {v: v for v in selected}, {v: 1 for v in selected}

    def find(u):
        ops['finds'] += 1
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
            ops['finds'] += 1
        return u

    def union(u, v):
        u, v = find(u), find(v)
        if u == v:
            return False
        if size[u] < size[v]:
            u, v = v, u
        parent[v] = u
        size[u] += size[v]
        return True

    chosen = []
    if method == 'kruskal':
        for r in ordered(edges, lambda r: (r.cable, r.road_no, r.u, r.v), ops):
            budget(deadline)
            ops['edge_tests'] += 1
            if union(r.u, r.v):
                chosen.append(r)
    else:
        adj = adjacency(selected, edges, (), ops)
        seen, by_id = set(), {r.road_no: r for r in edges}
        for root in ordered(selected, lambda x: x, ops):
            if root in seen:
                continue
            heap = Heap(ops)
            heap.push((0, -1, root, root))
            while heap:
                budget(deadline)
                _, rid, u, prev = heap.pop()
                if u in seen:
                    continue
                seen.add(u)
                if rid != -1:
                    chosen.append(by_id[rid])
                    union(u, prev)
                for v, r in adj[u]:
                    ops['edge_tests'] += 1
                    if v not in seen:
                        heap.push((r.cable, r.road_no, v, u))
    groups = {}
    for v in ordered(selected, lambda x: x, ops):
        groups.setdefault(find(v), []).append(v)
    components = tuple(tuple(g) for g in groups.values())
    return NetworkPlan('EMPTY' if not selected else ('FOREST' if len(components) > 1 else 'OK'),
                       tuple(ordered((r.road_no for r in chosen), lambda x: x, ops)),
                       sum(r.cable for r in chosen), components, ops)
