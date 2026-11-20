"""Module C: rescue scheduling (which rescue windows to staff).

Problem. A window has an id, a start minute, a finish minute and a value. Two
windows are compatible when one starts at or after the finish of the other
(windows that only touch are compatible: start >= previous finish). Choose a
set of pairwise compatible windows with
    objective "count": the largest number of windows, or
    objective "value": the largest total value.
On day d the window with (window_id + d) % 5 == 0 is unavailable;
`available_on_day` removes those before `solve` is called.

Methods (see the README for the choice and the measurements):
  greedy  primary for "count": windows in order of finish (ties by window id),
          take each one that starts at or after the finish of the last taken
          window. O(n log n); optimal for the count (exchange argument), NOT
          optimal for the value (it never looks at values).
  dp      primary for "value": weighted-interval dynamic programming. Windows in
          order of finish; p(i) = number of earlier windows that finish at or
          before the start of window i, found by binary search;
          best[i] = max(best[i-1], best[p(i)] + weight(i)). O(n log n).
  dpquad  baseline: the chain recurrence f[i] = weight(i) + max f[j] over the
          earlier windows j compatible with i, every j looked at. O(n^2).
  brute   baseline for n <= 22: all 2^n subsets in Gray-code order, O(2^n).

Ties. Windows with the same finish are ordered by window id ascending. In `dp`
a window is taken only when that is strictly better, so among sets of equal
total the back-tracking (latest window first) returns the one that prefers
earlier windows in that order. The total is unique; the chosen set is
deterministic for a given set of windows, whatever their order in the input.
`dpquad` takes the first best predecessor and `brute` the first best subset it
meets, so for equal totals they may return another set (only the total is part
of their contract).

Contract of all methods: the chosen windows are pairwise compatible; the total
is the count or the value of exactly those windows; no windows (or none left
after the day filter) is status 'EMPTY' with a note; broken input or a bad
objective or method is status 'INVALID' with a note, never an exception and
never a made-up plan. Only a passed time budget raises TimeBudgetExceeded (the
experiment harness records it as DNF).
"""
from time import perf_counter
from typing import NamedTuple

from ..models import InvalidInputError, TimeBudgetExceeded
from ..sorting import merge_sort

BRUTE_FORCE_LIMIT = 22
OBJECTIVES = ("count", "value")
UNAVAILABLE_MODULUS = 5


class Window(NamedTuple):
    window_id: int
    start: int      # minute, >= 0
    finish: int     # minute, > start
    value: int      # >= 0


class RescuePlan(NamedTuple):
    status: str        # 'OK', 'EMPTY' or 'INVALID'
    chosen: tuple      # window_ids in ascending order
    total: int         # number of windows (objective "count") or their total value (objective "value")
    ops: dict          # operation counts, defined in the README
    note: str = ""

    @property
    def selected(self):
        """Same as `chosen`; the name used by the plan of module A."""
        return self.chosen


# ----------------------------------------------------------------- helpers
def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _as_window(w):
    """The Window of a Window, of any object with the four attributes, or of a 4-sequence."""
    if hasattr(w, "window_id") and hasattr(w, "start") and hasattr(w, "finish") and hasattr(w, "value"):
        return Window(w.window_id, w.start, w.finish, w.value)
    try:
        return Window(*w)
    except TypeError:
        raise InvalidInputError(f"a window needs exactly (window_id, start, finish, value), got {w!r}") from None


def validate_windows(windows):
    """Return the windows as a list of Window, or raise InvalidInputError."""
    try:
        items = list(windows)
    except TypeError:
        raise InvalidInputError(f"windows must be a list of windows, got {type(windows).__name__}") from None
    out, seen = [], set()
    for raw in items:
        w = _as_window(raw)
        if not (_is_int(w.window_id) and _is_int(w.start) and _is_int(w.finish) and _is_int(w.value)):
            raise InvalidInputError(f"window {w.window_id!r}: id, start, finish and value must be whole numbers")
        if w.start < 0:
            raise InvalidInputError(f"window {w.window_id}: start must be >= 0, got {w.start}")
        if w.finish <= w.start:
            raise InvalidInputError(f"window {w.window_id}: finish must be after start, got {w.start}..{w.finish}")
        if w.value < 0:
            raise InvalidInputError(f"window {w.window_id}: value must be >= 0, got {w.value}")
        if w.window_id in seen:
            raise InvalidInputError(f"window id {w.window_id} appears twice")
        seen.add(w.window_id)
        out.append(w)
    return out


def _id_of(w):
    if hasattr(w, "window_id"):
        return w.window_id
    try:
        return w[0]
    except (TypeError, IndexError, KeyError):
        raise InvalidInputError(f"cannot read a window id from {w!r}") from None


def available_on_day(windows, day):
    """The windows that can be staffed on `day`: those with (window_id + day) % 5 != 0, in the given order.

    The windows themselves are returned (same objects, input unchanged). `day` must be a whole
    number and every window must have a whole-number id, otherwise InvalidInputError is raised
    (this function returns a list, so it has no status to report). All-unavailable gives [].
    """
    if not _is_int(day):
        raise InvalidInputError(f"day must be a whole number, got {day!r}")
    try:
        items = list(windows)
    except TypeError:
        raise InvalidInputError(f"windows must be a list of windows, got {type(windows).__name__}") from None
    out = []
    for w in items:
        wid = _id_of(w)
        if not _is_int(wid):
            raise InvalidInputError(f"window id must be a whole number, got {wid!r}")
        if (wid + day) % UNAVAILABLE_MODULUS != 0:
            out.append(w)
    return out


def _new_ops():
    return {"comparisons": 0, "moves": 0, "probes": 0, "items_examined": 0, "cells": 0,
            "subsets": 0, "calls": 1, "pre": {"items_examined": 0, "pair_tests": 0}}


def _empty(ops, note):
    return RescuePlan("EMPTY", (), 0, ops, note)


def _invalid(ops, note):
    return RescuePlan("INVALID", (), 0, ops, "invalid input: " + note)


def _plan(chosen, objective, ops, note=""):
    ids = tuple(sorted(w.window_id for w in chosen))
    total = len(chosen) if objective == "count" else sum(w.value for w in chosen)
    return RescuePlan("OK", ids, total, ops, note)


def _check_budget(deadline):
    if deadline is not None and perf_counter() > deadline:
        raise TimeBudgetExceeded("module C exceeded its time budget")


def _finish_before(a, b):
    """True if window a comes before window b: earlier finish, ties by window id."""
    if a.finish != b.finish:
        return a.finish < b.finish
    return a.window_id < b.window_id


def _by_finish(cand, ops):
    """Windows in order of finish (ties by id), with our merge sort; comparisons and moves are counted."""
    counts = {"comparisons": 0, "moves": 0}
    order = merge_sort(cand, _finish_before, counts)
    ops["comparisons"] += counts["comparisons"]
    ops["moves"] += counts["moves"]
    return order


# ------------------------------------------------- earliest-finish greedy
def _greedy(cand, objective, ops, deadline):
    """Take each window, in order of finish, that starts at or after the finish of the last one taken."""
    _check_budget(deadline)
    order = _by_finish(cand, ops)
    chosen = []
    last_finish = None
    for w in order:
        ops["items_examined"] += 1
        if last_finish is None or w.start >= last_finish:
            chosen.append(w)
            last_finish = w.finish
    note = ""
    if objective == "value":
        note = "earliest-finish greedy ignores values: not optimal for the value objective"
    return _plan(chosen, objective, ops, note)


# ---------------------------- weighted-interval DP with binary search
def _dp(cand, objective, ops, deadline):
    _check_budget(deadline)
    order = _by_finish(cand, ops)
    m = len(order)
    finishes = [w.finish for w in order]
    count = objective == "count"
    best = [0] * (m + 1)          # best[i] = optimum over the first i windows of the order
    pred = [0] * (m + 1)          # pred[i] = p(i): how many earlier windows are compatible with window i
    probes = 0
    for i in range(1, m + 1):
        w = order[i - 1]
        lo, hi = 0, i - 1         # search the first i - 1 windows for the first one that finishes after w starts
        while lo < hi:
            mid = (lo + hi) >> 1
            probes += 1
            if finishes[mid] <= w.start:
                lo = mid + 1
            else:
                hi = mid
        pred[i] = lo
        take = best[lo] + (1 if count else w.value)
        best[i] = take if take > best[i - 1] else best[i - 1]
    ops["probes"] += probes
    ops["items_examined"] += m
    ops["cells"] += m
    chosen = []
    i = m
    while i > 0:                  # back-tracking: window i was taken exactly when it improved the table
        if best[i] != best[i - 1]:
            chosen.append(order[i - 1])
            i = pred[i]
        else:
            i -= 1
    return _plan(chosen, objective, ops)


# ------------------------------------------------ baseline 1: plain O(n^2) DP
def _dpquad(cand, objective, ops, deadline):
    _check_budget(deadline)
    order = _by_finish(cand, ops)
    m = len(order)
    finishes = [w.finish for w in order]
    count = objective == "count"
    f = [0] * m                   # f[i] = best total of a chain that ends with window i
    pred = [-1] * m
    for i in range(m):
        if i & 0xFF == 0:
            _check_budget(deadline)
        s = order[i].start
        best_f, best_j = 0, -1
        for j in range(i):        # every earlier window is looked at
            if finishes[j] <= s and f[j] > best_f:
                best_f, best_j = f[j], j
        ops["items_examined"] += i
        f[i] = best_f + (1 if count else order[i].value)
        pred[i] = best_j
    ops["cells"] += m
    top = 0
    for i in range(1, m):
        if f[i] > f[top]:
            top = i
    chosen = []
    i = top
    while i != -1:
        chosen.append(order[i])
        i = pred[i]
    return _plan(chosen, objective, ops)


# ------------------------------------------------ baseline 2: all subsets
def _brute(cand, objective, ops, deadline):
    """Every subset in Gray-code order; a subset counts when it has no overlapping pair."""
    n = len(cand)
    if n > BRUTE_FORCE_LIMIT:
        return _invalid(ops, f"brute force is limited to {BRUTE_FORCE_LIMIT} windows, got {n}")
    _check_budget(deadline)
    items = list(cand)
    conflict = [0] * n            # conflict[i]: bit j set when windows i and j overlap
    for i in range(n):
        for j in range(i + 1, n):
            ops["pre"]["pair_tests"] += 1
            if items[i].start < items[j].finish and items[j].start < items[i].finish:
                conflict[i] |= 1 << j
                conflict[j] |= 1 << i
    ops["items_examined"] += n
    weight = [1 if objective == "count" else w.value for w in items]
    mask = 0
    overlapping_pairs = 0
    current = 0
    best, best_mask = 0, 0
    subsets = 1                                   # the empty set
    for step in range(1, 1 << n):
        if step & 0xFFFF == 0:
            _check_budget(deadline)
        bit = (step & -step).bit_length() - 1     # the one window that changes in Gray code
        b = 1 << bit
        if mask & b:
            mask ^= b
            overlapping_pairs -= (mask & conflict[bit]).bit_count()
            current -= weight[bit]
        else:
            overlapping_pairs += (mask & conflict[bit]).bit_count()
            mask |= b
            current += weight[bit]
        subsets += 1
        if overlapping_pairs == 0 and current > best:
            best, best_mask = current, mask
    ops["subsets"] += subsets
    return _plan([items[i] for i in range(n) if best_mask >> i & 1], objective, ops)


METHODS = {"greedy": _greedy, "dp": _dp, "dpquad": _dpquad, "brute": _brute}
PRIMARY = {"count": "greedy", "value": "dp"}


def solve(windows, objective="count", method=None, deadline=None):
    """Entry point for the campaign.

    objective 'count' or 'value'; method 'greedy', 'dp', 'dpquad' or 'brute'
    (None: the shipped one, greedy for 'count' and dp for 'value').
    Never raises for bad input: the plan then has status 'INVALID' and a note.
    """
    ops = _new_ops()
    if not (isinstance(objective, str) and objective in OBJECTIVES):
        return _invalid(ops, f"objective must be one of {list(OBJECTIVES)}, got {objective!r}")
    if method is None:
        method = PRIMARY[objective]
    if not (isinstance(method, str) and method in METHODS):
        return _invalid(ops, f"unknown method {method!r}; choose one of {sorted(METHODS)}")
    try:
        wins = validate_windows(windows)
    except InvalidInputError as exc:
        return _invalid(ops, str(exc))
    ops["pre"]["items_examined"] = len(wins)
    cand = wins if objective == "count" else [w for w in wins if w.value > 0]
    if not cand:
        why = ("no windows (none given, or all of them unavailable)" if not wins
               else "no window with positive value")
        return _empty(ops, why)
    return METHODS[method](cand, objective, ops, deadline)
