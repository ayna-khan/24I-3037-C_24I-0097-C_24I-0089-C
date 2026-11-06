# checks_routes.py - helper checks for the network: breadth-first search and route costs
import heapq
import math
from collections import deque


def bfs_hops(V, adj, src=0, skip=None):
    hops = [-1] * V
    hops[src] = 0
    q = deque([src])
    while q:
        u = q.popleft()
        for v, r in adj[u]:
            if (skip is None or r not in skip) and hops[v] == -1:
                hops[v] = hops[u] + 1
                q.append(v)
    return hops


def route_costs(V, rd, pen, hops0):
    """cheapest cost from the HQ (dijkstra) and cheapest cost among the fewest-roads routes, for every location.
    rd = rows of sheet roads, pen = penalties, hops0 = fewest roads from the HQ (bfs)"""
    w_adj = [[] for _ in range(V)]
    for _c, rn, u, v, mins, cable in rd:
        w_adj[u].append((v, mins + pen[v]))        # cost of step u -> v
        w_adj[v].append((u, mins + pen[u]))
    dist = [math.inf] * V
    dist[0] = 0
    heap = [(0, 0)]
    while heap:
        dd, u = heapq.heappop(heap)
        if dd > dist[u]:
            continue
        for v, w in w_adj[u]:
            if dd + w < dist[v]:
                dist[v] = dd + w
                heapq.heappush(heap, (dist[v], v))
    best_fewest = [math.inf] * V
    best_fewest[0] = 0
    for u in sorted(range(V), key=lambda x: hops0[x]):
        for v, w in w_adj[u]:
            if hops0[v] == hops0[u] + 1:
                best_fewest[v] = min(best_fewest[v], best_fewest[u] + w)
    return dist, best_fewest
