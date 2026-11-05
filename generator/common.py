# common.py - constants (alphabet, size ranges) and small helpers used by the other files
import random

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"   # 38 symbols
PATTERN_LENGTHS = [2, 4, 8, 12, 20, 40]

# (low, high) of every size for each tier. tier X uses the L ranges
RANGES = {
    "S": dict(crates=(8, 20), V=(6, 12), log=(200, 500), report=(10, 30),
              windows=(8, 20), alarms=(10, 40), sites=(5, 9), stages=(4, 8),
              drum=(5, 14), sensors=(6, 14), vars=(6, 15), rations=(8, 20)),
    "M": dict(crates=(40, 200), V=(30, 150), log=(2000, 10000), report=(30, 150),
              windows=(50, 300), alarms=(200, 1000), sites=(10, 16), stages=(15, 60),
              drum=(40, 200), sensors=(20, 40), vars=(20, 50), rations=(24, 40)),
    "L": dict(crates=(500, 1500), V=(500, 2000), log=(20000, 100000), report=(200, 1000),
              windows=(1000, 3000), alarms=(2000, 5000), sites=(200, 500), stages=(100, 300),
              drum=(500, 2000), sensors=(100, 400), vars=(20, 50), rations=(50, 100)),
}


def tier_of(k):
    if k < 20:
        return "S"
    if k < 40:
        return "M"
    if k < 46:
        return "L"
    return "X"


def study_of(k):
    return k % 6 + 1


def pick_size(rng, tier, name):
    """random size for `name` inside the tier range"""
    lo, hi = RANGES["L" if tier == "X" else tier][name]
    return rng.randint(lo, hi)


def module_rng(seed, k, module):
    """every module of every case gets its own rng, so results are the same on every run"""
    return random.Random(f"{seed}-{k}-{module}")


def case_id(seed, k):
    return f"{seed}-{k:02d}"
