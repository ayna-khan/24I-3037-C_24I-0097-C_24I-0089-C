# claims.py - exact optima for tier S (written into sheet claims)
import bisect
import itertools
import math

from tour_sensors import tour_length


# claims (tier s)
def best_window_count(wins):
    last, count = -1, 0
    for s, f, _v in sorted(wins, key=lambda w: w[1]):
        if s >= last:
            count += 1
            last = f
    return count


def best_window_value(wins):
    wins = sorted(wins, key=lambda w: w[1])
    finishes = [w[1] for w in wins]
    best = [0] * (len(wins) + 1)
    for i, (s, f, v) in enumerate(wins):
        p = bisect.bisect_right(finishes, s)             # number of windows finishing at or before s
        best[i + 1] = max(best[i], v + best[min(p, i)])
    return best[-1]


def best_tour(points):
    n = len(points)
    best = math.inf
    for perm in itertools.permutations(range(1, n)):
        best = min(best, tour_length(points, (0,) + perm))
    return best
