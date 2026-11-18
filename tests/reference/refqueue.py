"""Independent reference for module D. Kept apart from src/ on purpose.

Plain simulation, one tick at a time, using a library sort on the urgency key.
Slow and simple on purpose; it shares no code with the shipped heap or scan.
"""


def release_order(alarms):
    """List of (alarm_id, release_tick) following the urgency order, one per tick."""
    waiting = sorted(alarms, key=lambda a: a.tick)
    out = []
    pending = []
    tick = waiting[0].tick if waiting else 0
    k = 0
    while k < len(waiting) or pending:
        while k < len(waiting) and waiting[k].tick <= tick:
            pending.append(waiting[k])
            k += 1
        if not pending:
            tick = waiting[k].tick
            continue
        pending.sort(key=lambda a: (-a.priority, a.tick, a.alarm_id))
        a = pending.pop(0)
        out.append((a.alarm_id, tick))
        tick += 1
    return out


def check_release(alarms, plan):
    """Invariants of a release plan; returns a list of violated rules."""
    problems = []
    by_id = {a.alarm_id: a for a in alarms}
    ids = [i for i, _ in plan.releases]
    if sorted(ids) != sorted(by_id):
        problems.append("not every alarm is released exactly once")
        return problems
    ticks = [t for _, t in plan.releases]
    if any(b <= a for a, b in zip(ticks, ticks[1:])):
        problems.append("more than one release in a tick or ticks not increasing")
    if any(t < by_id[i].tick for i, t in plan.releases):
        problems.append("an alarm is released before it arrives")
    # no alarm that was present and more urgent may be released later
    release_tick = dict(plan.releases)
    key = lambda a: (-a.priority, a.tick, a.alarm_id)
    for i, t in plan.releases:
        for other in alarms:
            if other.alarm_id != i and other.tick <= t < release_tick[other.alarm_id] and key(other) < key(by_id[i]):
                problems.append(f"alarm {other.alarm_id} was present and more urgent at tick {t}")
                return problems
    return problems
