"""Independent reference for module C. Kept apart from src/ on purpose.

Three methods that share no code with the shipped ones:
  * best_total   a timeline DP over the distinct minutes (no sorting of windows, no binary
                 search): best[t] = optimum using only windows that finish at or before minute t;
  * brute_total  every subset by itertools.combinations, tested pair by pair (n <= 14);
  * earliest_finish_ids  the textbook earliest-finish rule with the built-in sorted()
                 (key: finish, window id), for comparing the exact set the greedy returns.
It also holds the invariant checker used by the tests.
"""
from itertools import combinations


def _weight(w, objective):
    return 1 if objective == "count" else w[3]


def best_total(windows, objective):
    """Exact optimum (count or value) of the interval scheduling problem; windows are (id, start, finish, value)."""
    usable = [w for w in windows if objective == "count" or w[3] > 0]
    if not usable:
        return 0
    ending_at = {}
    for w in usable:
        ending_at.setdefault(w[2], []).append(w)
    times = sorted({w[1] for w in usable} | {w[2] for w in usable})
    best = {}
    previous = 0
    for t in times:
        here = previous
        for w in ending_at.get(t, ()):
            here = max(here, best[w[1]] + _weight(w, objective))   # w[1] < t, so best[w[1]] is known
        best[t] = here
        previous = here
    return previous


def compatible(a, b):
    """Two windows can both be staffed: one starts at or after the other finishes."""
    return a[1] >= b[2] or b[1] >= a[2]


def brute_total(windows, objective):
    """Optimum by trying every subset (small inputs only)."""
    usable = [w for w in windows if objective == "count" or w[3] > 0]
    if len(usable) > 14:
        raise ValueError("reference brute force is for at most 14 windows")
    best = 0
    for size in range(1, len(usable) + 1):
        for subset in combinations(usable, size):
            if all(compatible(a, b) for a, b in combinations(subset, 2)):
                best = max(best, sum(_weight(w, objective) for w in subset))
    return best


def earliest_finish_ids(windows):
    """Ids chosen by the earliest-finish rule, sorted ascending."""
    chosen, last = [], None
    for w in sorted(windows, key=lambda x: (x[2], x[0])):
        if last is None or w[1] >= last:
            chosen.append(w[0])
            last = w[2]
    return tuple(sorted(chosen))


def check_plan(windows, objective, plan):
    """Invariants of a plan; returns a list of violated rules (empty list = fine)."""
    problems = []
    by_id = {w[0]: w for w in windows}
    ids = list(plan.chosen)
    if len(set(ids)) != len(ids):
        problems.append("a window is chosen twice")
    if any(i not in by_id for i in ids):
        problems.append("chosen window does not exist")
        return problems
    picked = sorted((by_id[i] for i in ids), key=lambda w: (w[1], w[2], w[0]))
    for a, b in zip(picked, picked[1:]):
        if b[1] < a[2]:
            problems.append(f"windows {a[0]} and {b[0]} overlap")
            break
    expected = len(ids) if objective == "count" else sum(by_id[i][3] for i in ids)
    if plan.total != expected:
        problems.append("reported total differs from the chosen windows")
    if ids != sorted(ids):
        problems.append("chosen ids are not in ascending order")
    if plan.status == "EMPTY" and (ids or plan.total):
        problems.append("status EMPTY but something chosen")
    if plan.status == "OK" and not ids:
        problems.append("status OK but nothing chosen")
    return problems
