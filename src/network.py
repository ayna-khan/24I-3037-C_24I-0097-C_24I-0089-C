"""Network records, validation and a counted binary heap shared by B and F."""
from time import perf_counter
from typing import NamedTuple

from .models import InvalidInputError, TimeBudgetExceeded
from .sorting import merge_sort


class Location(NamedTuple):
    loc_id: int
    kind: str
    penalty: int


class Road(NamedTuple):
    road_no: int
    u: int
    v: int
    minutes: int
    cable: int


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise InvalidInputError(f'{name} must be an integer >= {minimum}')
    return value


def budget(deadline):
    if deadline is not None and perf_counter() >= deadline:
        raise TimeBudgetExceeded('network calculation exceeded its time budget')


def validate(locations, roads, blocked=(), source=0):
    nodes = {}
    for loc in locations:
        integer(loc.loc_id, 'location id')
        integer(loc.penalty, 'location penalty')
        if loc.loc_id in nodes or loc.kind not in ('D', 'S', 'H', 'J'):
            raise InvalidInputError('duplicate location or unknown location type')
        nodes[loc.loc_id] = loc
    if type(source) is not int or source not in nodes:
        raise InvalidInputError('source must identify a location')
    seen = set()
    for r in roads:
        for key in ('road_no', 'u', 'v'):
            integer(getattr(r, key), key)
        integer(r.minutes, 'road minutes', 1)
        integer(r.cable, 'road cable', 1)
        if r.road_no in seen or r.u == r.v or r.u not in nodes or r.v not in nodes:
            raise InvalidInputError('duplicate road, self loop or missing endpoint')
        seen.add(r.road_no)
    blocked = set(blocked)
    if any(type(x) is not int or x not in seen for x in blocked):
        raise InvalidInputError('closure refers to an unknown road')
    return nodes, blocked


def ordered(items, key, ops):
    return merge_sort(list(items), lambda a, b: key(a) < key(b), ops)


def adjacency(nodes, roads, blocked, ops):
    adj = {v: [] for v in nodes}
    for r in roads:
        if r.road_no not in blocked:
            adj[r.u].append((r.v, r))
            adj[r.v].append((r.u, r))
    preprocessing = {'comparisons': 0, 'moves': 0}
    for v in adj:
        adj[v] = ordered(adj[v], lambda pair: (pair[0], pair[1].road_no), preprocessing)
    ops['pre_comparisons'] = ops.get('pre_comparisons', 0) + preprocessing['comparisons']
    ops['pre_moves'] = ops.get('pre_moves', 0) + preprocessing['moves']
    return adj


class Heap:
    """Min-heap; comparisons and heap-slot writes are explicit operations."""
    def __init__(self, ops):
        self.data = []
        self.ops = ops

    def __bool__(self):
        return bool(self.data)

    def before(self, a, b):
        self.ops['comparisons'] += 1
        return a < b

    def push(self, item):
        a = self.data
        a.append(item)
        self.ops['moves'] += 1
        i = len(a) - 1
        while i:
            p = (i - 1) // 2
            if not self.before(item, a[p]):
                break
            a[i] = a[p]
            self.ops['moves'] += 1
            i = p
        a[i] = item
        self.ops['moves'] += 1

    def pop(self):
        a = self.data
        result, last = a[0], a.pop()
        if a:
            i = 0
            while 2 * i + 1 < len(a):
                child = 2 * i + 1
                if child + 1 < len(a) and self.before(a[child + 1], a[child]):
                    child += 1
                if not self.before(a[child], last):
                    break
                a[i] = a[child]
                self.ops['moves'] += 1
                i = child
            a[i] = last
            self.ops['moves'] += 1
        return result


def counts():
    return dict(comparisons=0, moves=0, edge_tests=0, relaxations=0, finds=0,
                pre_comparisons=0, pre_moves=0)
