"""Numerical predictions of Adan for module G, written BEFORE the full runs.

Each entry: (id, round, what is measured, point prediction, lowest and highest value
that still counts as a hit, function that extracts the measured value).
`python experiments/predictionsG.py` compares them with results/ and prints a table
(HIT / MISS and the relative error |prediction - measurement| / measurement).
The same numbers, with the reasoning, are in predlogG.md (same ids). The numbers
here must not be changed after a run: a wrong prediction stays a MISS and is explained
in the "After the run" part of predlogG.md.
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import measure  # noqa: E402


class Results:
    def __init__(self, folder):
        self.folder = folder
        with open(os.path.join(folder, "results.csv"), newline="", encoding="utf-8") as f:
            self.rows = [r for r in csv.DictReader(f) if r["module"] == "G"]

    def series(self, experiment, algorithm, field="time_s"):
        out = []
        for r in self.rows:
            if (r["experiment"], r["algorithm"]) == (experiment, algorithm) and r["status"] == "OK" and r[field] != "":
                out.append((float(r["size"]), float(r[field])))
        return sorted(out)

    def row(self, experiment, algorithm, size):
        for r in self.rows:
            if (r["experiment"], r["algorithm"]) == (experiment, algorithm) and float(r["size"]) == size:
                return r
        raise KeyError(f"no row {experiment} {algorithm} {size}")

    def quality(self):
        with open(os.path.join(self.folder, "quality-G.csv"), newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


def note_value(row, key):
    for part in row["note"].split(";"):
        part = part.strip()
        if part.startswith(key + "="):
            return float(part.split("=", 1)[1])
    raise KeyError(key)


def slope(res, exp, alg, field="time_s"):
    pts = [p for p in res.series(exp, alg, field) if p[1] > 0]
    return measure.fit_loglog([p[0] for p in pts], [p[1] for p in pts])["slope"]


def at(res, exp, alg, size, field="time_s"):
    return float(res.row(exp, alg, size)[field])


def ratio(res, exp, a, b, size):
    return at(res, exp, a, size) / at(res, exp, b, size)


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def mean_ratio(res, exp, a, b):
    return _mean(ratio(res, exp, a, b, s) for s, _ in res.series(exp, b))


def all_same(res, exp, alg):
    return _mean(note_value(r, "same_answer_all") for r in res.rows if (r["experiment"], r["algorithm"]) == (exp, alg) and r["status"] == "OK")


def first_faster(res, exp, fast, slow):
    slow_t = dict(res.series(exp, slow))
    return min(s for s, t in res.series(exp, fast) if t < slow_t[s])


def brute_base(res, exp):
    pts = res.series(exp, "brute")
    return measure.fit_semilog([p[0] for p in pts], [p[1] for p in pts])["base"]


def build(res):
    P = []

    def add(pid, rnd, text, point, lo, hi, fn):
        P.append((pid, rnd, text, point, lo, hi, fn))

    C, D, SC, SD = "G-chain-n", "G-drum-L", "G-small-chain", "G-small-drum"
    add("G1.1", 1, "chain dp: log-log slope of time against n", 2.85, 2.6, 3.1, lambda: slope(res, C, "dp"))
    add("G1.2", 1, "chain memo: log-log slope of time against n", 2.85, 2.6, 3.1, lambda: slope(res, C, "memo"))
    add("G1.3", 1, "chain dp: ops at n = 320", 5512320.0, 5512320.0, 5512320.0, lambda: at(res, C, "dp", 320, "ops"))
    add("G1.4", 1, "chain memo: recursive calls at n = 320", 10922561.0, 10922561.0, 10922561.0, lambda: note_value(res.row(C, "memo", 320), "calls"))
    add("G1.5", 1, "chain dp: time at n = 640 (s)", 14.0, 8.0, 28.0, lambda: at(res, C, "dp", 640))
    add("G1.6", 1, "chain memo: time at n = 640 (s)", 65.0, 30.0, 140.0, lambda: at(res, C, "memo", 640))
    add("G1.7", 1, "chain memo time / dp time at n = 640", 4.5, 2.5, 7.5, lambda: ratio(res, C, "memo", "dp", 640))
    add("G1.8", 1, "chain dp and memo return the same cost and bracketing (share of sizes)", 1.0, 1.0, 1.0, lambda: all_same(res, C, "dp"))
    add("G1.9", 1, "chain dp: peak memory per n^2 at n = 160 (bytes)", 40.0, 25.0, 70.0, lambda: at(res, C, "dp", 160, "mem_bytes") / 160 ** 2)
    add("G1.10", 1, "chain memo peak memory / dp peak memory at n = 160", 0.8, 0.5, 1.1,
        lambda: at(res, C, "memo", 160, "mem_bytes") / at(res, C, "dp", 160, "mem_bytes"))
    add("G1.11", 1, "chain dp: time at n = 160 (s)", 0.23, 0.12, 0.5, lambda: at(res, C, "dp", 160))
    add("G1.12", 1, "chain dp: time at n = 640 / time at n = 320", 8.0, 6.5, 10.0, lambda: at(res, C, "dp", 640) / at(res, C, "dp", 320))
    add("G1.13", 1, "chain dp: log-log slope of the counted operations against n", 2.95, 2.90, 3.00, lambda: slope(res, C, "dp", "ops"))

    add("G2.1", 2, "drum dp: log-log slope of time against L", 1.95, 1.8, 2.1, lambda: slope(res, D, "dp"))
    add("G2.2", 2, "drum memo: log-log slope of time against L", 1.95, 1.8, 2.1, lambda: slope(res, D, "memo"))
    add("G2.3", 2, "drum greedy: log-log slope of time against L", 1.1, 0.9, 1.3, lambda: slope(res, D, "greedy"))
    add("G2.4", 2, "drum dp: ops at L = 2000", 2003000.0, 2003000.0, 2003000.0, lambda: at(res, D, "dp", 2000, "ops"))
    add("G2.5", 2, "drum memo: recursive calls at L = 2000", 2001001.0, 2001001.0, 2001001.0, lambda: note_value(res.row(D, "memo", 2000), "calls"))
    add("G2.6", 2, "drum dp: time at L = 2000 (s)", 0.4, 0.2, 0.9, lambda: at(res, D, "dp", 2000))
    add("G2.7", 2, "drum memo: time at L = 2000 (s)", 1.7, 0.8, 4.0, lambda: at(res, D, "memo", 2000))
    add("G2.8", 2, "drum greedy: time at L = 2000 (s)", 0.007, 0.003, 0.020, lambda: at(res, D, "greedy", 2000))
    add("G2.9", 2, "drum memo time / dp time at L = 2000", 4.0, 2.0, 7.0, lambda: ratio(res, D, "memo", "dp", 2000))
    add("G2.10", 2, "drum dp time / greedy time at L = 2000", 55.0, 15.0, 200.0, lambda: ratio(res, D, "dp", "greedy", 2000))
    add("G2.11", 2, "drum dp and memo return the same price and pieces (share of sizes)", 1.0, 1.0, 1.0, lambda: all_same(res, D, "dp"))
    add("G2.12", 2, "drum dp: peak memory per unit of length at L = 2000 (bytes)", 50.0, 25.0, 120.0, lambda: at(res, D, "dp", 2000, "mem_bytes") / 2000)

    add("G3.1", 3, "tier S: share of cases where the dp price equals the claim", 1.0, 1.0, 1.0,
        lambda: _mean(int(r["dp_matches_claim"]) for r in res.quality() if r["tier"] == "S"))
    add("G3.2", 3, "all sampled cases: share where the greedy price is not above the dp price", 1.0, 1.0, 1.0,
        lambda: _mean(int(int(r["drum_greedy_price"]) <= int(r["drum_dp_price"])) for r in res.quality()))
    add("G3.3", 3, "all sampled cases: share where the greedy price equals the dp price", 0.85, 0.65, 0.97,
        lambda: _mean(int(r["greedy_optimal"]) for r in res.quality()))
    add("G3.4", 3, "all sampled cases: mean greedy price / dp price", 0.998, 0.990, 1.0,
        lambda: _mean(float(r["greedy_over_dp"]) for r in res.quality()))
    add("G3.5", 3, "all sampled cases: worst greedy price / dp price", 0.93, 0.80, 0.99,
        lambda: min(float(r["greedy_over_dp"]) for r in res.quality()))
    add("G3.6", 3, "all sampled cases: mean (pieces of the dp cut) / L", 0.75, 0.45, 1.0,
        lambda: _mean(float(r["dp_pieces_over_length"]) for r in res.quality()))
    add("G3.7", 3, "tier S: mean (cost left to right) / (optimal cost)", 1.35, 1.05, 2.2,
        lambda: _mean(float(r["left_to_right_over_opt"]) for r in res.quality() if r["tier"] == "S"))
    add("G3.8", 3, "tier L: mean (cost left to right) / (optimal cost)", 6.0, 2.0, 25.0,
        lambda: _mean(float(r["left_to_right_over_opt"]) for r in res.quality() if r["tier"] == "L"))

    add("G4.1", 4, "chain brute: bracketings enumerated at n = 12", 58786.0, 58786.0, 58786.0, lambda: note_value(res.row(SC, "brute", 12), "enumerated"))
    add("G4.2", 4, "chain brute: growth factor per extra matrix of the enumerated count (semi-log fit)", 3.2, 3.1, 3.35,
        lambda: measure.fit_semilog([float(r["size"]) for r in res.rows if (r["experiment"], r["algorithm"]) == (SC, "brute")],
                                    [note_value(r, "enumerated") for r in res.rows if (r["experiment"], r["algorithm"]) == (SC, "brute")])["base"])
    add("G4.3", 4, "chain brute: time at n = 12 (s)", 0.6, 0.25, 2.0, lambda: at(res, SC, "brute", 12))
    add("G4.4", 4, "chain: smallest n at which dp is faster than brute", 4.0, 4.0, 6.0, lambda: first_faster(res, SC, "dp", "brute"))
    add("G4.5", 4, "chain: brute time / dp time at n = 12", 4000.0, 1000.0, 20000.0, lambda: ratio(res, SC, "brute", "dp", 12))
    add("G4.6", 4, "chain: memo time / dp time, mean over the five sizes", 2.0, 1.3, 4.0, lambda: mean_ratio(res, SC, "memo", "dp"))
    add("G4.7", 4, "chain: dp, memo and brute return the same bracketing (share of sizes)", 1.0, 1.0, 1.0, lambda: all_same(res, SC, "dp"))
    add("G4.8", 4, "drum brute: cuts enumerated at L = 20", 524288.0, 524288.0, 524288.0, lambda: note_value(res.row(SD, "brute", 20), "enumerated"))
    add("G4.9", 4, "drum brute: growth factor per extra unit of length of the time (semi-log fit)", 2.0, 1.85, 2.15, lambda: brute_base(res, SD))
    add("G4.10", 4, "drum brute: time at L = 20 (s)", 0.9, 0.4, 2.0, lambda: at(res, SD, "brute", 20))
    add("G4.11", 4, "drum: smallest L at which dp is faster than brute", 8.0, 8.0, 11.0, lambda: first_faster(res, SD, "dp", "brute"))
    add("G4.12", 4, "drum: brute time / dp time at L = 20", 12000.0, 3000.0, 50000.0, lambda: ratio(res, SD, "brute", "dp", 20))
    add("G4.13", 4, "drum: memo time / dp time, mean over the five sizes", 1.6, 1.1, 3.0, lambda: mean_ratio(res, SD, "memo", "dp"))
    add("G4.14", 4, "drum: dp, memo and brute return the same cut (share of sizes)", 1.0, 1.0, 1.0, lambda: all_same(res, SD, "dp"))
    add("G4.15", 4, "drum: dp time / greedy time, mean over the five sizes", 1.0, 0.6, 1.6, lambda: mean_ratio(res, SD, "dp", "greedy"))
    return P


def evaluate(folder, rounds=None):
    res = Results(folder)
    out = []
    for pid, rnd, text, point, lo, hi, fn in build(res):
        if rounds and rnd not in rounds:
            continue
        try:
            got = fn()
        except Exception as exc:                         # missing data: report, do not hide
            out.append((pid, text, point, lo, hi, None, f"not evaluated ({type(exc).__name__}: {exc})"))
            continue
        hit = lo <= got <= hi
        err = measure.relative_error(point, got) if got else (0.0 if point == got else float("inf"))
        out.append((pid, text, point, lo, hi, got, "HIT" if hit else "MISS", err))
    return out


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results")
    lines = ["| id | what | predicted (range) | measured | result | rel. error |", "|---|---|---|---|---|---|"]
    items = evaluate(folder)
    for item in items:
        pid, text, point, lo, hi, got = item[:6]
        if got is None:
            lines.append(f"| {pid} | {text} | {point:g} ({lo:g} to {hi:g}) | - | {item[6]} | - |")
        else:
            lines.append(f"| {pid} | {text} | {point:g} ({lo:g} to {hi:g}) | {got:.6g} | {item[6]} | {item[7] * 100:.0f} % |")
    hits = sum(1 for i in items if i[6] == "HIT")
    miss = sum(1 for i in items if i[6] == "MISS")
    lines.append(f"\n{len(items)} predictions: {hits} hit, {miss} miss, {len(items) - hits - miss} not evaluated (round not run yet).")
    text = "\n".join(lines)
    print(text)
    with open(os.path.join(folder, "predictions-vs-measurements-G.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
