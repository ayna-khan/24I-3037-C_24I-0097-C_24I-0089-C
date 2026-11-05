# radio.py - radio log, patterns, reports and trap 49
from common import ALPHABET, PATTERN_LENGTHS, pick_size


def count_overlapping(text, pattern):
    count, pos = 0, text.find(pattern)
    while pos != -1:
        count += 1
        pos = text.find(pattern, pos + 1)
    return count


def random_text(rng, n):
    return "".join(rng.choice(ALPHABET) for _ in range(n))


def message_log(rng, n):
    """radio log made of a few repeated messages plus some noise"""
    msgs = [random_text(rng, rng.randint(3, 10)) for _ in range(rng.randint(5, 8))]
    parts, size = [], 0
    while size < n:
        piece = rng.choice(msgs) if rng.random() < 0.8 else random_text(rng, rng.randint(1, 5))
        parts.append(piece)
        size += len(piece)
    return "".join(parts)[:n]


def beacon_log(rng, n):
    """study 6: two beacon messages repeated again and again, one symbol is very common"""
    while True:
        dom = rng.choice(ALPHABET)
        beacons = ["".join(dom if rng.random() < 0.55 else rng.choice(ALPHABET) for _ in range(rng.randint(8, 12)))
                   for _ in range(2)]
        parts, size = [], 0
        while size < n:
            piece = rng.choice(beacons) if rng.random() < 0.97 else rng.choice(ALPHABET)
            parts.append(piece)
            size += len(piece)
        log = "".join(parts)[:n]
        if log.count(dom) >= 0.3 * n:
            return log


def near_miss_log(rng, n):
    """trap 49: 92% of the log is one repeated symbol, the rest is random"""
    dom = rng.choice(ALPHABET)
    body = int(0.92 * n)
    return dom * body + random_text(rng, n - body), dom


def make_radio(rng, k, tier, study):
    """returns (log, patterns, counts)"""
    n = rng.randint(50000, 100000) if k == 49 else pick_size(rng, tier, "log")
    patterns = []
    if k == 49:
        log, dom = near_miss_log(rng, n)
        for i, length in enumerate(PATTERN_LENGTHS):
            if i < 2:
                patterns.append(dom * length)           # these two occur in the log
            else:                                       # near miss: same start as the log but the last symbol is wrong
                other = rng.choice([c for c in ALPHABET if c != dom])
                patterns.append(dom * (length - 1) + other)
    else:
        if study == 3:
            log = random_text(rng, n)                   # noisy log, uses almost all 38 symbols
        elif study == 6:
            log = beacon_log(rng, n)
        else:
            log = message_log(rng, n)
        for i, length in enumerate(PATTERN_LENGTHS):
            present = i < 3 or (i == 3 and rng.random() < 0.5) or (i == 4 and rng.random() < 0.5)
            if present:
                start = rng.randrange(n - length + 1)
                patterns.append(log[start:start + length])
            else:
                for _ in range(100):
                    p = random_text(rng, length)
                    if count_overlapping(log, p) == 0:
                        break
                patterns.append(p)
    counts = [count_overlapping(log, p) for p in patterns]
    return log, patterns, counts


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[-1]


def make_reports(rng, tier, log):
    """two reports: b is a with a few random edits. returns (a, b, edit_bound)"""
    lo, hi = {"S": (10, 30), "M": (30, 150), "L": (200, 1000), "X": (200, 1000)}[tier]
    la = rng.randint(lo, hi)
    start = rng.randrange(len(log) - la + 1)
    a = log[start:start + la]
    b = list(a)
    for _ in range(rng.randint(1, max(2, la // 6))):
        op = rng.choice("ids")
        pos = rng.randrange(len(b))
        if op == "i" and len(b) < hi:
            b.insert(pos, rng.choice(ALPHABET))
        elif op == "d" and len(b) > lo:
            del b[pos]
        elif op == "s":
            b[pos] = rng.choice(ALPHABET)
    b = "".join(b)
    bound = min(len(a) + len(b), edit_distance(a, b) + rng.randint(0, 3))
    return a, b, bound
