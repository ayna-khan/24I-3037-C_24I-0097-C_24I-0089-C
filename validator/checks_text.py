# checks_text.py - helper checks for crates and text: edit distance, overlapping counts, greedy by value per kg
import re
from fractions import Fraction


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def count_regex(text, pat):
    return len(re.findall("(?=" + re.escape(pat) + ")", text))


def greedy_value(crates, cap):
    order = sorted(crates, key=lambda c: (-Fraction(c[3], c[2]), c[0]))
    left = cap
    total = 0
    for _id, _cat, w, v, _e, _s in order:
        if w <= left:
            left -= w
            total += v
    return total
