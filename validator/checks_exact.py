# checks_exact.py - exhaustive / exact methods used to re-check the tier S claims (different from the generator)
import itertools


def exhaustive_knapsack(crates, cap):
    """tries every subset by doubling a list (real exhaustive search)"""
    subsets = [(0, 0)]
    for _id, _c, w, v, _e, _s in crates:
        subsets += [(sw + w, sv + v) for sw, sv in subsets if sw + w <= cap]
    return max(sv for sw, sv in subsets)


def exhaustive_windows(wins, by_value):
    wins = sorted(wins, key=lambda w: w[0])

    def go(i, last_finish):
        best = 0
        for j in range(i, len(wins)):
            s, f, v = wins[j]
            if s >= last_finish:
                best = max(best, (v if by_value else 1) + go(j + 1, f))
        return best

    return go(0, 0)


def exhaustive_drum(prices):
    def go(left):
        if left == 0:
            return 0
        return max(prices[c - 1] + go(left - c) for c in range(1, left + 1))
    return go(len(prices))


def held_karp(points):
    n = len(points)
    d = lambda a, b: abs(points[a][0] - points[b][0]) + abs(points[a][1] - points[b][1])
    best = {(1 << j, j): d(0, j) for j in range(1, n)}
    for size in range(2, n):
        for sub in itertools.combinations(range(1, n), size):
            mask = sum(1 << j for j in sub)
            for j in sub:
                prev = mask ^ (1 << j)
                best[(mask, j)] = min(best[(prev, i)] + d(i, j) for i in sub if i != j)
    full = sum(1 << j for j in range(1, n))
    return min(best[(full, j)] + d(j, 0) for j in range(1, n))


def min_cover_branching(edges, budget):
    """smallest vertex cover size: take an uncovered edge and try both ends"""
    def go(es, k):
        if not es:
            return True
        if k == 0:
            return False
        u, v = es[0]
        return go([e for e in es if u not in e], k - 1) or go([e for e in es if v not in e], k - 1)
    for k in range(budget + 1):
        if go(list(edges), k):
            return k
    return None
