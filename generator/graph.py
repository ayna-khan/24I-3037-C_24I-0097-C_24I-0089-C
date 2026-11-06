# graph.py - network part: locations, roads, waves and targets
import heapq
import math
from collections import deque

# allowed average degree (low, high) for each study (study 5 is built separately)
DEGREE = {1: (2.2, 3.2), 2: (2.0, 2.6), 3: (2.4, 3.4), 4: (3.6, 5.0), 6: (2.4, 3.4)}
# how likely each penalty (0, 1, 2, 4, 6) is, per study
PENALTY_W = {1: [2, 2, 3, 2, 1.5], 2: [3, 3, 2, 1, 1], 3: [3, 3, 2, 1, 1],
             4: [3, 3, 2, 1, 1], 5: [3, 3, 2, 1, 1], 6: [3, 3, 2, 1, 1]}
PENALTIES = [0, 1, 2, 4, 6]


# route helpers (needed for the tier S variety rule and trap 48)
def adjacency(V, roads, penalty):
    adj = [[] for _ in range(V)]
    for u, v, minutes, _cable in roads:
        adj[u].append((v, minutes + penalty[v]))   # cost of step u->v
        adj[v].append((u, minutes + penalty[u]))
    return adj


def cheapest_costs(adj, src=0):
    dist = [math.inf] * len(adj)
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    return dist


def fewest_roads_costs(adj, src=0):
    """bfs layers: hops[v] = fewest roads to v, best[v] = cheapest cost among routes with that many roads"""
    V = len(adj)
    hops = [-1] * V
    best = [math.inf] * V
    hops[src] = 0
    best[src] = 0
    queue = deque([src])
    while queue:
        u = queue.popleft()
        for v, w in adj[u]:
            if hops[v] == -1:
                hops[v] = hops[u] + 1
                queue.append(v)
            if hops[v] == hops[u] + 1:
                best[v] = min(best[v], best[u] + w)
    return hops, best


def shortest_looks_cheapest_nodes(V, roads, penalty):
    """locations where every fewest-roads route costs more than the cheapest route"""
    adj = adjacency(V, roads, penalty)
    cheap = cheapest_costs(adj)
    hops, best = fewest_roads_costs(adj)
    return [v for v in range(1, V) if best[v] > cheap[v]]


# building the graph
def tree_edges(rng, V, window=None):
    """random spanning tree, node i is attached to an earlier node"""
    edges = set()
    for i in range(1, V):
        low = 0 if window is None else max(0, i - window)
        edges.add((rng.randint(low, i - 1), i))
    return edges


def general_edges(rng, V, study):
    lo, hi = DEGREE[study]
    e_low = max(V - 1, math.ceil(lo * V / 2))
    e_high = min(3 * V, V * (V - 1) // 2, math.floor(hi * V / 2))
    E = rng.randint(e_low, max(e_low, e_high))
    edges = tree_edges(rng, V, window=3 if study == 2 else None)
    while len(edges) < E:
        a, b = rng.sample(range(V), 2)
        edges.add((min(a, b), max(a, b)))
    return edges, None


def corridor_edges(rng, V):
    """study 5: one highway 0-1-...-(V-1) with a few small detours. the road (cut, cut+1) gets no detour"""
    cut = rng.randint(V // 2, V - 3)
    edges = {(i, i + 1) for i in range(V - 1)}
    degree = [2] * V
    degree[0] = degree[V - 1] = 1
    extra_max = math.floor(1.2 * V) - (V - 1)          # so that 2E/V stays <= 2.4
    extra = rng.randint(0, max(0, extra_max))
    candidates = [(i, i + d) for i in range(V) for d in (2, 3) if i + d < V
                  and not (i <= cut < i + d)]           # no detour may jump over the cut
    rng.shuffle(candidates)
    for a, b in candidates:
        if extra == 0:
            break
        if degree[a] < 4 and degree[b] < 4:
            edges.add((a, b))
            degree[a] += 1
            degree[b] += 1
            extra -= 1
    return edges, cut


def make_types(rng, V, study):
    """type of every location, location 0 is the HQ (depot)"""
    n_s = max(1, round(V * rng.uniform(0.12, 0.25)))
    if study == 3:
        n_s = math.ceil(0.25 * V) + rng.randint(0, 2)
    n_h = max(1, round(V * rng.uniform(0.06, 0.14)))
    while n_s + n_h < 3:
        n_s += 1
    n_s = min(n_s, V - 1 - n_h)
    types = ["S"] * n_s + ["H"] * n_h + ["J"] * (V - 1 - n_s - n_h)
    rng.shuffle(types)
    return ["D"] + types


def make_penalties(rng, V, study):
    pen = [0] + rng.choices(PENALTIES, weights=PENALTY_W[study], k=V - 1)
    if study == 1:                                      # study 1 needs at least 40% of locations with penalty >= 2
        need = math.ceil(0.4 * V)
        low = [i for i in range(1, V) if pen[i] < 2]
        rng.shuffle(low)
        have = sum(1 for p in pen if p >= 2)
        for i in low[:max(0, need - have)]:
            pen[i] = rng.choice([2, 4, 6])
    return pen


def make_waves(rng, E, forced_road=None):
    """makes the closure waves (disjoint). forced_road (the cut of study 5) goes into wave 1"""
    n_waves = min(rng.randint(3, 5), E)
    cap = max(1, E // 6)
    pool = [r for r in range(E) if r != forced_road]
    rng.shuffle(pool)
    waves = []
    for w in range(n_waves):
        size = rng.randint(1, cap)
        wave = []
        if w == 0 and forced_road is not None:
            wave.append(forced_road)
            size -= 1
        while size > 0 and pool:
            wave.append(pool.pop())
            size -= 1
        waves.append(sorted(wave))
    return waves


def reachable(V, roads, closed):
    adj = [[] for _ in range(V)]
    for r, (u, v, _m, _c) in enumerate(roads):
        if r not in closed:
            adj[u].append(v)
            adj[v].append(u)
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def choose_targets(rng, types, must_have=None, beyond=None):
    """picks 3 different shelters/hospitals. must_have / beyond force one of them"""
    cands = [i for i, t in enumerate(types) if t in ("S", "H")]
    first = []
    if must_have is not None:
        first.append(must_have)
    if beyond is not None:
        pool = [c for c in cands if c >= beyond and c not in first]
        if pool:
            first.append(rng.choice(pool))
    rest = [c for c in cands if c not in first]
    rng.shuffle(rest)
    targets = (first + rest)[:3]
    rng.shuffle(targets)
    return targets


def make_roads(rng, edges, study, backbone=False):
    roads = []
    for u, v in sorted(edges):
        lo = 5 if study == 5 else 1
        roads.append([u, v, rng.randint(lo, 60), rng.randint(1, 100)])
    return roads


# whole network of one case
def make_network(rng, V, study, want_costlier=False):
    """returns the network as a dict. tries again if the tier S variety rule is wanted and not met yet"""
    for attempt in range(400):
        if study == 5:
            edges, cut = corridor_edges(rng, V)
        else:
            edges, cut = general_edges(rng, V, study)
        roads = make_roads(rng, edges, study)
        types = make_types(rng, V, study)
        if study == 5 and types[V - 1] == "J":          # one target has to be beyond the cut
            j = rng.choice([i for i, t in enumerate(types) if t in ("S", "H")])
            types[V - 1], types[j] = types[j], types[V - 1]
        penalty = make_penalties(rng, V, study)
        cut_road = None
        if study == 5:
            cut_road = next(r for r, (u, v, _m, _c) in enumerate(roads) if (u, v) == (cut, cut + 1))
        waves = make_waves(rng, len(roads), cut_road)
        must = None
        if want_costlier:
            good = [v for v in shortest_looks_cheapest_nodes(V, roads, penalty) if types[v] in ("S", "H")]
            if not good and attempt < 399:
                continue
            must = rng.choice(good) if good else None
        targets = choose_targets(rng, types, must_have=must, beyond=(cut + 1) if study == 5 else None)
        return dict(types=types, penalty=penalty, roads=roads, waves=waves, targets=targets)


def make_trap48_network(rng):
    """case 48: very long highway with one expensive direct road to a target (the trap)"""
    V = rng.randint(1500, 3000)
    t = 8                                               # trap target
    edges = {(i, i + 1) for i in range(V - 1)}
    edges.add((0, t))                                   # direct road: only 1 road but 60 minutes
    for i in range(V - 2):                              # small shortcuts that skip one node only
        if rng.random() < 0.3:
            edges.add((i, i + 2))
    roads = []
    for u, v in sorted(edges):
        minutes = 60 if (u, v) == (0, t) else rng.randint(1, 3)
        roads.append([u, v, minutes, rng.randint(1, 100)])
    types = make_types(rng, V, 1)
    types[t] = "S"
    penalty = make_penalties(rng, V, 3)
    for i in range(1, t):
        penalty[i] = 0                                  # so the detour through 1..t-1 is cheap
    penalty[t] = 2
    waves = make_waves(rng, len(roads))
    targets = choose_targets(rng, types, must_have=t)
    return dict(types=types, penalty=penalty, roads=roads, waves=waves, targets=targets)
