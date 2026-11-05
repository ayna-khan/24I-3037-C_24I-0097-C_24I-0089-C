# crates.py - crates module (truck crates, capacity) and the traps 46 and 47
import math
from fractions import Fraction

from common import pick_size


CAT_RULE = {1: ((0, 1), 0.55), 2: ((2, 3), 0.45), 4: ((4,), 0.10), 6: ((2, 1), 0.55)}


def make_categories(rng, n, study):
    cats = []
    if study in CAT_RULE:
        group, frac = CAT_RULE[study]
        need = math.ceil(frac * n) + rng.randint(0, n // 10)
        cats = [rng.choice(group) for _ in range(need)]
    cats += [rng.randint(0, 4) for _ in range(n - len(cats))]
    rng.shuffle(cats)
    return cats


def knapsack_best(crates, capacity):
    """best value by dp over capacity. crates is a list of (weight, value)"""
    best = [0] * (capacity + 1)
    for w, v in crates:
        for c in range(capacity, w - 1, -1):
            best[c] = max(best[c], best[c - w] + v)
    return best[capacity]


def greedy_density(crates, capacity):
    """greedy: highest value per kg first (exact fraction), skip the crates that do not fit"""
    order = sorted(range(len(crates)), key=lambda i: (-Fraction(crates[i][1], crates[i][0]), i))
    left, total = capacity, 0
    for i in order:
        w, v = crates[i]
        if w <= left:
            left -= w
            total += v
    return total


def make_crates(rng, k, tier, study, want_greedy_fail=False):
    """returns (rows, capacity), a row is (crate_id, cat, weight, value, expiry, serial)"""
    for attempt in range(300):
        if k == 47:
            weights, values, cats, capacity = trap47(rng)
            n = len(weights)
        else:
            n = rng.randint(1500, 3000) if k == 46 else pick_size(rng, tier, "crates")
            weights = [rng.randint(1, 20) for _ in range(n)]
            values = [rng.randint(10, 100) for _ in range(n)]
            cats = make_categories(rng, n, study)
            capacity = None
        expiry = [rng.randint(0, 999) for _ in range(n)]
        if study == 6 and k != 47:                      # at least half of the crates expire by hour 300
            for i in rng.sample(range(n), math.ceil(0.55 * n)):
                expiry[i] = rng.randint(0, 300)
        serial = rng.sample(range(10_000_000, 100_000_000), n)
        if k == 46:                                     # trap 46: crate list is sorted in 4 of the 5 fields
            values.sort()
            weights.sort()
            expiry.sort(reverse=True)
            serial.sort()
        if capacity is None:
            total = sum(weights)
            capacity = max(1, round(total * rng.uniform(0.25, 0.55)))
        pairs = list(zip(weights, values))
        if not want_greedy_fail or greedy_density(pairs, capacity) < knapsack_best(pairs, capacity):
            break
    rows = [(i + 1, cats[i], weights[i], values[i], expiry[i], serial[i]) for i in range(n)]
    return rows, capacity


def trap47(rng):
    """trap 47: one bait crate (11 kg, value 61) has the best value per kg but blocks two good crates (10 kg, value 55).
    capacity is 20, so greedy takes the bait and nothing else fits (61) while the best is two good crates (110)"""
    n = rng.randint(12, 16)
    items = [(11, 61, rng.randint(0, 4))]
    for _ in range(rng.randint(2, 4)):
        items.append((10, 55, rng.randint(0, 4)))
    while len(items) < n:                               # filler crates: weight 10 or 11, lower value per kg than the bait
        w = rng.choice([10, 11])
        items.append((w, rng.randint(10, int(5.4 * w)), rng.randint(0, 4)))
    rng.shuffle(items)
    return [i[0] for i in items], [i[1] for i in items], [i[2] for i in items], 20
