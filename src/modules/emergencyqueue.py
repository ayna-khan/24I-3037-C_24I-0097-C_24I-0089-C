"""Module D: emergency queue (which alarm to answer first).

Problem. Alarms arrive at integer ticks with a priority 1..10 (10 is the most
urgent). The command can answer ONE alarm per tick. At every tick the alarms
present are those that have arrived (tick <= now) and are not yet answered;
the one answered is the most urgent present, where the urgency order is
    priority descending, then arrival tick ascending, then alarm_id ascending.
When nothing is present the tick passes with no release, and the clock jumps
to the next arrival. Output: the release order with the tick of each release.

Methods:
  release_heap  primary: binary min-heap on (-priority, tick, alarm_id),
                O(m log m) time, O(backlog) extra space.
  release_scan  baseline: keep the present alarms in a list and scan the whole
                list for the most urgent one at every tick, O(m * backlog).

Both give exactly the same release order for every input (the order is total
because the alarm id breaks every tie); the tests check this.
"""
from time import perf_counter
from typing import NamedTuple

from ..models import Alarm, InvalidInputError, TimeBudgetExceeded
from ..sorting import merge_sort

PRIORITY_MIN, PRIORITY_MAX = 1, 10


class ReleasePlan(NamedTuple):
    status: str          # 'OK' or 'EMPTY' (no alarms)
    releases: tuple      # ((alarm_id, release_tick), ...) in release order
    max_backlog: int     # most alarms waiting at the same time, after arrivals of a tick
    total_wait: int      # sum over alarms of (release tick - arrival tick)
    max_wait: int
    ops: dict            # operation counts, defined in the README
    note: str = ""


# ----------------------------------------------------------------- helpers
def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def validate_alarms(alarms):
    """Raise InvalidInputError unless the input meets the contract of module D."""
    seen = set()
    for a in alarms:
        if not (_is_int(a.alarm_id) and _is_int(a.tick) and _is_int(a.priority)):
            raise InvalidInputError(f"alarm {a.alarm_id!r}: id, tick and priority must be whole numbers")
        if a.tick < 0:
            raise InvalidInputError(f"alarm {a.alarm_id}: tick must be >= 0, got {a.tick}")
        if not PRIORITY_MIN <= a.priority <= PRIORITY_MAX:
            raise InvalidInputError(
                f"alarm {a.alarm_id}: priority must be {PRIORITY_MIN}..{PRIORITY_MAX}, got {a.priority}")
        if a.alarm_id in seen:
            raise InvalidInputError(f"alarm id {a.alarm_id} appears twice")
        seen.add(a.alarm_id)


def with_extra_alarms(alarms, extras):
    """Return the alarms plus new ones, for the storm (day 2) and medical (day 5) events.

    `extras` is a list of (tick, priority). New ids continue after the largest
    existing id, so an added alarm loses every tie against an old alarm that
    has the same priority and tick (id ascending).
    """
    next_id = max((a.alarm_id for a in alarms), default=0) + 1
    out = list(alarms)
    for offset, (tick, priority) in enumerate(extras):
        out.append(Alarm(next_id + offset, tick, priority))
    return out


def _tick_before(a, b):
    return a.tick < b.tick


def _arrival_order(alarms, ops):
    """Alarms with non-decreasing tick (stable). Preprocessing, counted separately.

    One pass checks the order (m - 1 key comparisons); the master data is
    normally already in order, so the merge sort only runs when it is needed.
    """
    pre = ops["pre"]
    n = len(alarms)
    in_order = True
    for i in range(1, n):
        pre["comparisons"] += 1
        if alarms[i].tick < alarms[i - 1].tick:
            in_order = False
            break
    if in_order:
        return list(alarms)
    counts = {"comparisons": 0, "moves": 0}
    out = merge_sort(alarms, _tick_before, counts)
    pre["comparisons"] += counts["comparisons"]
    pre["moves"] += counts["moves"]
    return out


def _new_ops():
    return {"comparisons": 0, "moves": 0, "pushes": 0, "pops": 0,
            "pre": {"comparisons": 0, "moves": 0}}


def _summary(releases, arrival, backlog_peak, ops):
    waits = [t - arrival[i] for i, t in releases]
    return ReleasePlan("OK", tuple(releases), backlog_peak, sum(waits), max(waits), ops)


def _empty(ops):
    return ReleasePlan("EMPTY", (), 0, 0, 0, ops, "no alarms")


# --------------------------------------------------------- primary: binary heap
def release_heap(alarms, deadline=None):
    """Release order by a binary min-heap keyed (-priority, tick, alarm_id).

    Counted operations: a key comparison is one `<` between two keys; a move is
    one heap slot written (sifting uses a hole, so a swap would count 2 but
    costs 1 move per level here).
    """
    validate_alarms(alarms)
    ops = _new_ops()
    if not alarms:
        return _empty(ops)
    arr = _arrival_order(alarms, ops)
    m = len(arr)
    arrival = {a.alarm_id: a.tick for a in arr}
    heap = []
    releases = []
    comparisons = moves = 0
    i = 0
    now = arr[0].tick
    backlog_peak = 0
    while len(releases) < m:
        if not heap and arr[i].tick > now:
            now = arr[i].tick                                  # idle: jump to the next arrival
        while i < m and arr[i].tick <= now:                    # push the arrivals of this tick
            a = arr[i]
            i += 1
            key = (-a.priority, a.tick, a.alarm_id)
            heap.append(key)
            pos = len(heap) - 1
            while pos > 0:                                     # sift up with a hole
                parent = (pos - 1) >> 1
                comparisons += 1
                if key < heap[parent]:
                    heap[pos] = heap[parent]
                    moves += 1
                    pos = parent
                else:
                    break
            heap[pos] = key
            moves += 1
        if len(heap) > backlog_peak:
            backlog_peak = len(heap)
        top = heap[0]                                          # pop the most urgent
        last = heap.pop()
        size = len(heap)
        if size:
            pos = 0
            while True:                                        # sift down with a hole
                child = 2 * pos + 1
                if child >= size:
                    break
                if child + 1 < size:
                    comparisons += 1
                    if heap[child + 1] < heap[child]:
                        child += 1
                comparisons += 1
                if heap[child] < last:
                    heap[pos] = heap[child]
                    moves += 1
                    pos = child
                else:
                    break
            heap[pos] = last
            moves += 1
        releases.append((top[2], now))
        now += 1
        if len(releases) & 255 == 0 and deadline is not None and perf_counter() > deadline:
            raise TimeBudgetExceeded("module D exceeded its time budget")
    ops.update(comparisons=comparisons, moves=moves, pushes=m, pops=m)
    return _summary(releases, arrival, backlog_peak, ops)


# ------------------------------------------------------ baseline: linear scan
def release_scan(alarms, deadline=None):
    """Release order by scanning every waiting alarm at every tick.

    Counted operations: one key comparison per alarm looked at during a scan
    (backlog - 1 per release), one move per alarm appended to the waiting list
    and one per removal (the released alarm is replaced by the last one).
    """
    validate_alarms(alarms)
    ops = _new_ops()
    if not alarms:
        return _empty(ops)
    arr = _arrival_order(alarms, ops)
    m = len(arr)
    arrival = {a.alarm_id: a.tick for a in arr}
    waiting = []
    releases = []
    comparisons = moves = 0
    i = 0
    now = arr[0].tick
    backlog_peak = 0
    while len(releases) < m:
        if not waiting and arr[i].tick > now:
            now = arr[i].tick
        while i < m and arr[i].tick <= now:
            a = arr[i]
            i += 1
            waiting.append((-a.priority, a.tick, a.alarm_id))
            moves += 1
        size = len(waiting)
        if size > backlog_peak:
            backlog_peak = size
        best = 0
        best_key = waiting[0]
        for j in range(1, size):                               # the scan
            key = waiting[j]
            if key < best_key:
                best = j
                best_key = key
        comparisons += size - 1
        waiting[best] = waiting[-1]
        waiting.pop()
        moves += 1
        releases.append((best_key[2], now))
        now += 1
        if len(releases) & 255 == 0 and deadline is not None and perf_counter() > deadline:
            raise TimeBudgetExceeded("module D exceeded its time budget")
    ops.update(comparisons=comparisons, moves=moves, pushes=m, pops=m)
    return _summary(releases, arrival, backlog_peak, ops)


# ------------------------------- simple policy for the campaign comparison only
def release_fifo(alarms, deadline=None):
    """First come, first served: priority is ignored. NOT a solution of module D.

    It is the 'simple choice' that the campaign and the quality experiment compare
    against: it answers every alarm in arrival order (tick, then id), one per tick.
    """
    validate_alarms(alarms)
    ops = _new_ops()
    if not alarms:
        return _empty(ops)
    arr = _arrival_order(alarms, ops)
    arrival = {a.alarm_id: a.tick for a in arr}
    ordered = sorted(arr, key=lambda a: (a.tick, a.alarm_id))   # arrival order only; same-tick ids ascending
    releases = []
    now = ordered[0].tick
    for a in ordered:
        now = max(now, a.tick)
        releases.append((a.alarm_id, now))
        now += 1
    peak = 0
    j = 0
    for k, (_, t) in enumerate(releases):                       # backlog just before each release
        while j < len(ordered) and ordered[j].tick <= t:
            j += 1
        peak = max(peak, j - k)
    return _summary(releases, arrival, peak, ops)


METHODS = {"heap": release_heap, "scan": release_scan}


def release_order(alarms, method="heap", deadline=None):
    """Entry point for the campaign: method is 'heap' (shipped) or 'scan' (baseline)."""
    try:
        fn = METHODS[method]
    except KeyError:
        raise InvalidInputError(f"unknown method {method!r}; choose one of {sorted(METHODS)}") from None
    return fn(alarms, deadline)
