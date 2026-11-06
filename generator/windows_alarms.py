# windows_alarms.py - rescue windows and the alarm stream
import bisect

from common import pick_size


# windows
def overlap_average(wins):
    """average number of other windows overlapping a window (touching does not count)"""
    starts = sorted(w[0] for w in wins)
    finishes = sorted(w[1] for w in wins)
    total = 0
    for s, f, _v in wins:
        total += bisect.bisect_left(starts, f) - bisect.bisect_right(finishes, s) - 1
    return total / len(wins)


def make_windows(rng, k, tier, study):
    n = pick_size(rng, tier, "windows")
    horizon = 1440
    while True:
        wins = []
        for _ in range(n):
            dur = rng.randint(5, 120) if study == 3 else rng.randint(15, 300)
            start = rng.randint(0, horizon - dur)
            wins.append([start, start + dur, rng.randint(1, 100)])
        for _ in range(max(3, n // 8)):                 # make some windows touch: start of one = finish of another
            a, b = rng.sample(range(n), 2)
            dur = wins[b][1] - wins[b][0]
            if wins[a][1] + dur <= 1440:
                wins[b][0] = wins[a][1]
                wins[b][1] = wins[a][1] + dur
        touching = sum(1 for a in wins for b in wins if a[1] == b[0])
        if touching < 2:
            continue                                    # we need at least two touching pairs
        if study != 3 or overlap_average(wins) >= 2.3 or horizon <= 240:
            return wins
        horizon = int(horizon * 0.8)


# incidents
PRIORITY_W = {2: [1, 1, 1, 1, 2, 4, 6, 8, 8, 7]}        # study 2: mostly urgent calls


def make_incidents(rng, k, tier, study):
    n = pick_size(rng, tier, "alarms")
    if tier == "S":
        rate = rng.uniform(0.6, 2.5)
    elif study == 4:
        rate = rng.uniform(1.55, 1.75)
    else:
        rate = rng.uniform(1.25, 1.75)
    T = max(2, round(n / rate))                          # ticks go from 0 to T-1
    weights = [1.0] * T
    for _ in range(max(1, T // 40)):                    # bursts of alarms (aftershocks)
        centre = rng.randrange(T)
        for t in range(max(0, centre - 3), min(T, centre + 4)):
            weights[t] += 6 if study == 2 else 3
    ticks = [0, T - 1] + rng.choices(range(T), weights=weights, k=n - 2)
    ticks.sort()
    pw = PRIORITY_W.get(study, [1] * 10)
    while True:
        pri = rng.choices(range(1, 11), weights=pw, k=n)
        if n >= 6:                                      # make sure 6 different priorities (including 1) are present
            for slot, p in zip(rng.sample(range(n), 6), [1, 2, 3, 4, 5, 6]):
                pri[slot] = p
        if sum(pri) / n >= 6.3 or study != 2:
            break
    return [(i + 1, ticks[i], pri[i]) for i in range(n)]
