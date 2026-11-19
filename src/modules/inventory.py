"""Module A: relief inventory (what to load on the truck).

Problem. Given crates with integer weight w_i and value v_i and an integer
truck capacity W, choose a set of whole crates of total weight at most W with
maximum total value (0/1 knapsack).

Methods (see README for the choice and the measurements):
  solve_dp      primary: dynamic programming over the capacity, O(n * W) time,
                O(n * W) bits kept for the back-tracking step.
  solve_greedy  baseline 1: crates in exact ratio order (value / weight
                descending, compared by cross-multiplication, ties by crate_id),
                each crate loaded if it still fits. O(n log n), not optimal.
  solve_brute   baseline 2: every subset, for n <= 22 only. O(2^n).

Contract of all three: the result never exceeds the capacity; an empty load
is reported as status 'EMPTY' with a note, never as a made-up plan; broken
input raises InvalidInputError.
"""
from time import perf_counter
from typing import NamedTuple

from ..models import Crate, InvalidInputError, TimeBudgetExceeded
from ..sorting import merge_sort

BRUTE_FORCE_LIMIT = 22


class LoadPlan(NamedTuple):
    status: str        # 'OK' or 'EMPTY'
    selected: tuple    # crate_ids in ascending order
    total_weight: int
    total_value: int
    ops: dict          # operation counts, defined in the README
    note: str = ""


# ----------------------------------------------------------------- helpers
def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def validate_crates(crates, capacity):
    """Raise InvalidInputError unless the input meets the contract of module A."""
    if not _is_int(capacity) or capacity < 0:
        raise InvalidInputError(f"capacity must be a whole number >= 0, got {capacity!r}")
    seen = set()
    for c in crates:
        if not (_is_int(c.crate_id) and _is_int(c.weight) and _is_int(c.value)):
            raise InvalidInputError(f"crate {c.crate_id!r}: id, weight and value must be whole numbers")
        if c.weight <= 0:
            raise InvalidInputError(f"crate {c.crate_id}: weight must be > 0, got {c.weight}")
        if c.value < 0:
            raise InvalidInputError(f"crate {c.crate_id}: value must be >= 0, got {c.value}")
        if c.crate_id in seen:
            raise InvalidInputError(f"crate id {c.crate_id} appears twice")
        seen.add(c.crate_id)


def with_day_values(crates, multipliers):
    """Return the crates with value = floor(base value * multiplier of the category).

    `multipliers` maps a category number to a whole-number multiplier (2 or 3 in
    the campaign calendar). Categories not listed keep their value. Integer
    arithmetic only, so the floor is exact.
    """
    for cat, m in multipliers.items():
        if not _is_int(m) or m < 0:
            raise InvalidInputError(f"multiplier of category {cat} must be a whole number >= 0")
    return [c._replace(value=c.value * multipliers.get(c.cat, 1)) for c in crates]


def _empty(ops, note):
    return LoadPlan("EMPTY", (), 0, 0, ops, note)


def _plan(chosen, ops):
    ids = tuple(sorted(c.crate_id for c in chosen))
    return LoadPlan("OK", ids, sum(c.weight for c in chosen), sum(c.value for c in chosen), ops)


def _check_budget(deadline):
    if deadline is not None and perf_counter() > deadline:
        raise TimeBudgetExceeded("module A exceeded its time budget")


# ------------------------------------------------------- primary: DP over W
def solve_dp(crates, capacity, deadline=None):
    """Optimal load by dynamic programming over the capacity.

    best[c] = largest value of a load of total weight at most c using the
    crates examined so far. For crate i (weight w, value v) and c >= w:
        best_i[c] = max(best_{i-1}[c], best_{i-1}[c - w] + v).
    One byte per cell records whether crate i was taken, for the back-tracking.

    Ties. A crate is taken only if it is strictly better, so among load sets of
    equal value the back-tracking (last crate first) returns the one that takes
    earlier crates in the given order. The total value is unique; the set is
    deterministic for a fixed input order.

    Crates heavier than the capacity and crates of value 0 can never be needed
    and are dropped. The table width is min(capacity, total weight of the rest).
    """
    validate_crates(crates, capacity)
    ops = {"items_examined": len(crates), "cells": 0, "calls": 1}
    items = [c for c in crates if c.weight <= capacity and c.value > 0]
    if not items:
        why = "no crates" if not crates else (
            "capacity is 0" if capacity == 0 else "no crate with positive value fits the capacity")
        return _empty(ops, why)

    width = min(capacity, sum(c.weight for c in items))
    best = [0] * (width + 1)
    taken_rows = []
    cells = 0
    for c in items:
        _check_budget(deadline)
        w, v = c.weight, c.value
        take =[y + v > x for x, y in zip(best[w:], best)]       # strictly better to take?
        tail = [y + v if t else x for t, x, y in zip(take, best[w:], best)]
        best = best[:w] + tail
        taken_rows.append(bytearray(w) + bytearray(take))
        cells += width - w + 1
    ops["cells"] = cells

    chosen = []
    cap = width
    for idx in range(len(items) - 1, -1, -1):                    # back-tracking
        if taken_rows[idx][cap]:
            chosen.append(items[idx])
            cap -= items[idx].weight
    if not chosen:
        return _empty(ops, "no crate improves the load")
    return _plan(chosen, ops)


# ---------------------------------------------------- baseline 1: ratio greedy
def _ratio_before(a, b):
    """True if crate a precedes crate b: a.value/a.weight > b.value/b.weight (exact), ties by id."""
    left = a.value * b.weight
    right = b.value * a.weight
    if left != right:
        return left > right
    return a.crate_id < b.crate_id


def solve_greedy(crates, capacity, deadline=None):
    """Fast rule of thumb: crates in exact ratio order, load each one that still fits.

    Continues past a crate that does not fit (it may still load lighter ones).
    Not optimal: see trap case 47.
    """
    validate_crates(crates, capacity)
    counts = {"comparisons": 0, "moves": 0}
    order = merge_sort([c for c in crates if c.weight <= capacity and c.value > 0], _ratio_before, counts)
    ops = {"items_examined": len(crates), "comparisons": counts["comparisons"],
           "moves": counts["moves"], "calls": 1}
    load = 0
    chosen = []
    for c in order:
        ops["items_examined"] += 1
        if load + c.weight <= capacity:
            chosen.append(c)
            load += c.weight
    if not chosen:
        why = "no crates" if not crates else (
            "capacity is 0" if capacity == 0 else "no crate with positive value fits the capacity")
        return _empty(ops, why)
    return _plan(chosen, ops)


# ------------------------------------------------- baseline 2: all subsets
def solve_brute(crates, capacity, deadline=None):
    """Exhaustive search over all 2^n subsets in Gray-code order (n <= 22).

    Used as an exact baseline and as a check of the DP on small inputs. Equal
    values are not tie-broken; only the total value is part of the contract.
    """
    validate_crates(crates, capacity)
    items = list(crates)
    n = len(items)
    if n > BRUTE_FORCE_LIMIT:
        raise InvalidInputError(f"brute force is limited to {BRUTE_FORCE_LIMIT} crates, got {n}")
    ops = {"items_examined": n, "subsets": 0, "calls": 1}
    if n == 0:
        return _empty(ops, "no crates")
    weights = [c.weight for c in items]
    values = [c.value for c in items]
    in_set = [False] * n
    cur_w = cur_v = 0
    best_v, best_mask_items = 0, ()
    subsets = 1                                   # the empty set
    for step in range(1, 1 << n):
        if step & 0xFFFF == 0:
            _check_budget(deadline)
        bit = (step & -step).bit_length() - 1     # the one item that changes in Gray code
        if in_set[bit]:
            in_set[bit] = False
            cur_w -= weights[bit]
            cur_v -= values[bit]
        else:
            in_set[bit] = True
            cur_w += weights[bit]
            cur_v += values[bit]
        subsets += 1
        if cur_w <= capacity and cur_v > best_v:
            best_v = cur_v
            best_mask_items = tuple(i for i in range(n) if in_set[i])
    ops["subsets"] = subsets
    if best_v == 0:
        return _empty(ops, "no subset with positive value fits the capacity")
    return _plan([items[i] for i in best_mask_items], ops)


METHODS = {"dp": solve_dp, "greedy": solve_greedy, "brute": solve_brute}


def solve(crates, capacity, method="dp", deadline=None):
    """Entry point for the campaign: method is 'dp' (shipped), 'greedy' or 'brute' (baselines)."""
    try:
        fn = METHODS[method]
    except KeyError:
        raise InvalidInputError(f"unknown method {method!r}; choose one of {sorted(METHODS)}") from None
    return fn(crates, capacity, deadline)
