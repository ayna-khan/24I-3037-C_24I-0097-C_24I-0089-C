# safety_rations.py - safety rules (3-CNF) and ration quantities
from common import pick_size


# safety
def make_safety(rng, k, tier):
    """rules built around a hidden assignment. rules per switch depends on k (variety rule 3)"""
    nvars = pick_size(rng, tier, "vars")
    if tier in ("M", "L"):
        band = k % 3                                     # 0 = low ratio, 1 = middle, 2 = high
        lo, hi = [(2.6, 3.3), (3.7, 4.6), (5.0, 5.8)][band]
    else:
        lo, hi = 2.0, 6.0
    rules_n = round(rng.uniform(lo, hi) * nvars)
    planted = [rng.randint(0, 1) for _ in range(nvars)]  # planted[j-1] is switch j
    rules = []
    for _ in range(rules_n):
        switches = rng.sample(range(1, nvars + 1), 3)
        lits = [j if rng.random() < 0.5 else -j for j in switches]
        if not any((l > 0) == (planted[abs(l) - 1] == 1) for l in lits):
            i = rng.randrange(3)
            lits[i] = -lits[i]                           # flip one literal so the planted assignment satisfies the rule
        rules.append(lits)
    return nvars, rules, planted


# rations
def make_rations(rng, tier):
    n = pick_size(rng, tier, "rations")
    values = [rng.randint(1, 1000) for _ in range(n)]
    chosen = set(rng.sample(range(n), rng.randint(max(2, n // 4), max(3, n // 2))))
    target = sum(values[i] for i in chosen)
    return values, [1 if i in chosen else 0 for i in range(n)], target
