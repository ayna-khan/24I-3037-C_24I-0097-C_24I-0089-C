"""Independent reference for module A. Kept apart from src/ on purpose.

A different method from the shipped DP: the set of Pareto-optimal
(weight, value) pairs is grown crate by crate (no table over the capacity).
It also holds the invariant checker used by the tests.
"""


def best_value(weights_values, capacity):
    """Exact optimum value of the 0/1 knapsack by a Pareto frontier of (weight, value) pairs."""
    frontier = {0: 0}                       # weight -> best value at exactly that weight
    for w, v in weights_values:
        grown = dict(frontier)
        for fw, fv in frontier.items():
            nw = fw + w
            if nw <= capacity and grown.get(nw, -1) < fv + v:
                grown[nw] = fv + v
        frontier = grown
    return max(frontier.values())


def check_load(crates, capacity, plan):
    """Invariants of a load plan; returns a list of violated rules (empty list = fine)."""
    problems = []
    by_id = {c.crate_id: c for c in crates}
    ids = list(plan.selected)
    if len(set(ids)) != len(ids):
        problems.append("a crate is loaded twice")
    if any(i not in by_id for i in ids):
        problems.append("loaded crate does not exist")
        return problems
    if sum(by_id[i].weight for i in ids) > capacity:
        problems.append("total weight above capacity")
    if sum(by_id[i].weight for i in ids) != plan.total_weight:
        problems.append("reported weight differs from the loaded crates")
    if sum(by_id[i].value for i in ids) != plan.total_value:
        problems.append("reported value differs from the loaded crates")
    if ids != sorted(ids):
        problems.append("selected ids are not in ascending order")
    if plan.status == "EMPTY" and ids:
        problems.append("status EMPTY but crates loaded")
    if plan.status == "OK" and not ids:
        problems.append("status OK but nothing loaded")
    return problems
