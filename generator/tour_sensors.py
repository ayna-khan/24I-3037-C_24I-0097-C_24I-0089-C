# tour_sensors.py - relief sites with the planted tour, and the sensor graph with its cover
import itertools

from common import pick_size


# sites and tour
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def tour_length(points, order):
    return sum(manhattan(points[order[i]], points[order[(i + 1) % len(order)]]) for i in range(len(order)))


def nearest_neighbour_tour(points):
    left = set(range(1, len(points)))
    order = [0]
    while left:
        last = points[order[-1]]
        nxt = min(left, key=lambda j: (manhattan(last, points[j]), j))
        order.append(nxt)
        left.remove(nxt)
    return order


def two_opt(points, order):
    """2-opt: reverse a part of the tour while it makes the closed tour shorter (site 0 stays first)"""
    n = len(order)
    improved, passes = True, 0
    while improved and passes < 25:
        improved = False
        passes += 1
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a, b = points[order[i - 1]], points[order[i]]
                c, d = points[order[j]], points[order[(j + 1) % n]]
                if manhattan(a, c) + manhattan(b, d) < manhattan(a, b) + manhattan(c, d):
                    order[i:j + 1] = reversed(order[i:j + 1])
                    improved = True
    return order


def make_tour(rng, k, tier):
    n = pick_size(rng, tier, "sites")
    cells = rng.sample(range(1000 * 1000), n)            # all points different
    points = [(c // 1000, c % 1000) for c in cells]
    order = two_opt(points, nearest_neighbour_tour(points))
    return points, order, tour_length(points, order)


# sensors
def make_sensors(rng, tier):
    """returns (n, edges, cover). every edge touches the cover"""
    n = pick_size(rng, tier, "sensors")
    kk = rng.randint(max(2, n // 3), n // 2)
    cover = sorted(rng.sample(range(n), kk))
    inside = set(cover)
    pairs = [(a, b) for a in range(n) for b in range(a + 1, n) if a in inside or b in inside]
    m = rng.randint(n - 1, min(len(pairs), 2 * n))
    edges = sorted(rng.sample(pairs, m))
    return n, edges, cover


def vertex_cover_min(n, edges):
    for size in range(n + 1):
        for subset in itertools.combinations(range(n), size):
            s = set(subset)
            if all(u in s or v in s for u, v in edges):
                return size
