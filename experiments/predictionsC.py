"""Numerical predictions of Adan for module C, written BEFORE the full runs.

Each entry: (id, round, what is measured, point prediction, lowest and highest value
that still counts as a hit, function that extracts the measured value).
`python experiments/predictionsC.py` compares them with results/ and prints a table
(HIT / MISS and the relative error |prediction - measurement| / measurement).
The same numbers, with the reasoning, are in prediction_log.md, section "Module C" (same ids). The numbers
here must not be changed after a run: a wrong prediction stays a MISS and is explained
in the "After the run" part of its entry in prediction_log.md.
"""
import csv
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import measure  # noqa: E402


class Results:
    def __init__(self, folder):
        self.folder = folder
        with open(os.path.join(folder, "results.csv"), newline="", encoding="utf-8") as f:
            self.rows = [r for r in csv.DictReader(f) if r["module"] == "C"]

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
        return None

    def quality(self):
        with open(os.path.join(self.folder, "quality-C.csv"), newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


def note_value(row, key):
    for part in row["note"].split(";"):
        part = part.strip()
        if part.startswith(key + "="):
            return float(part.split("=", 1)[1])
    raise KeyError(key)


def slope(res, exp, alg, field="time_s"):
    pts = res.series(exp, alg, field)
    return measure.fit_loglog([p[0] for p in pts], [p[1] for p in pts])["slope"]


def at(res, exp, alg, size, field="time_s"):
    return float(res.row(exp, alg, size)[field])


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def build(res):
    P = []

    def add(pid, rnd, text, point, lo, hi, fn):
        P.append((pid, rnd, text, point, lo, hi, fn))

    S, N = "C-scale-n", "C-small-n"
    add("C1.1", 1, "greedy: log-log slope of time against n", 1.1, 0.95, 1.3, lambda: slope(res, S, "greedy"))
    add("C1.2", 1, "dp: log-log slope of time against n", 1.1, 0.95, 1.3, lambda: slope(res, S, "dp"))
    add("C1.3", 1, "dpquad: log-log slope of time against n", 1.75, 1.5, 2.05, lambda: slope(res, S, "dpquad"))
    add("C1.4", 1, "dpquad: ops at n = 3000", 4.57e6, 4.55e6, 4.60e6, lambda: at(res, S, "dpquad", 3000, "ops"))
    add("C1.5", 1, "greedy: ops at n = 3000", 69900.0, 64000.0, 76000.0, lambda: at(res, S, "greedy", 3000, "ops"))
    add("C1.6", 1, "dp: ops at n = 3000", 104700.0, 96000.0, 115000.0, lambda: at(res, S, "dp", 3000, "ops"))
    add("C1.7", 1, "greedy: time at n = 3000 (s)", 0.016, 0.008, 0.035, lambda: at(res, S, "greedy", 3000))
    add("C1.8", 1, "dp: time at n = 3000 (s)", 0.022, 0.011, 0.045, lambda: at(res, S, "dp", 3000))
    add("C1.9", 1, "dpquad: time at n = 3000 (s)", 0.30, 0.15, 0.70, lambda: at(res, S, "dpquad", 3000))
    add("C1.10", 1, "dpquad time / dp time at n = 3000", 14.0, 6.0, 40.0,
        lambda: at(res, S, "dpquad", 3000) / at(res, S, "dp", 3000))
    add("C1.11", 1, "dpquad: log-log slope of time against ops", 0.95, 0.85, 1.1,
        lambda: measure.fit_loglog([float(r["ops"]) for r in res.rows if (r["experiment"], r["algorithm"], r["status"]) == (S, "dpquad", "OK")],
                                   [float(r["time_s"]) for r in res.rows if (r["experiment"], r["algorithm"], r["status"]) == (S, "dpquad", "OK")])["slope"])
    add("C1.12", 1, "dp and dpquad return the same total (share of sizes)", 1.0, 1.0, 1.0,
        lambda: _mean(note_value(r, "same_total_as_dp") for r in res.rows if (r["experiment"], r["algorithm"]) == (S, "dpquad") and r["status"] == "OK"))
    add("C1.13", 1, "dp time / greedy time at n = 3000", 1.35, 1.1, 2.0,
        lambda: at(res, S, "dp", 3000) / at(res, S, "greedy", 3000))
    add("C1.14", 1, "greedy: windows chosen at n = 3000", 80.0, 40.0, 160.0, lambda: note_value(res.row(S, "greedy", 3000), "chosen"))
    add("C1.15", 1, "dp: peak memory per window at n = 3000 (bytes)", 230.0, 110.0, 450.0,
        lambda: at(res, S, "dp", 3000, "mem_bytes") / 3000)
    add("C1.16", 1, "smallest n at which dpquad is more than twice as slow as dp", 188.0, 94.0, 375.0,
        lambda: min([s for s, t in res.series(S, "dpquad") if t > 2 * dict(res.series(S, "dp"))[s]] or [math.inf]))

    add("C2.1", 2, "tier S: share of cases where the greedy count equals the claim", 1.0, 1.0, 1.0,
        lambda: _mean(int(r["greedy_count_matches_claim"]) for r in res.quality() if r["tier"] == "S"))
    add("C2.2", 2, "tier S: share of cases where the dp value equals the claim", 1.0, 1.0, 1.0,
        lambda: _mean(int(r["dp_value_matches_claim"]) for r in res.quality() if r["tier"] == "S"))
    add("C2.3", 2, "all sampled cases: share where greedy count equals dp count", 1.0, 1.0, 1.0,
        lambda: _mean(int(r["greedy_count_optimal"]) for r in res.quality()))
    add("C2.4", 2, "tier S: share of cases where the greedy value is not optimal", 0.85, 0.60, 1.0,
        lambda: 1 - _mean(int(r["greedy_value_optimal"]) for r in res.quality() if r["tier"] == "S"))
    for pid, tier, point, lo, hi in (("C2.5", "S", 0.70, 0.58, 0.82), ("C2.6", "M", 0.62, 0.48, 0.76),
                                     ("C2.7", "L", 0.58, 0.42, 0.72), ("C2.8", "X", 0.58, 0.42, 0.72)):
        add(pid, 2, f"tier {tier}: mean greedy value / dp value", point, lo, hi,
            lambda t=tier: _mean(float(r["greedy_over_dp"]) for r in res.quality() if r["tier"] == t))
    add("C2.9", 2, "worst greedy value / dp value over all sampled cases", 0.40, 0.20, 0.55,
        lambda: min(float(r["greedy_over_dp"]) for r in res.quality()))
    add("C2.10", 2, "tiers M and L: mean (windows of the value-optimal plan) / (greedy count)", 0.75, 0.50, 0.95,
        lambda: _mean(int(r["dp_value_plan_windows"]) / int(r["greedy_count"]) for r in res.quality() if r["tier"] in ("M", "L")))

    add("C3.1", 3, "brute: growth base per extra window (semi-log fit)", 2.0, 1.85, 2.15,
        lambda: measure.fit_semilog([p[0] for p in res.series(N, "brute")], [p[1] for p in res.series(N, "brute")])["base"])
    add("C3.2", 3, "brute: subsets at n = 20", 1048576.0, 1048576.0, 1048576.0, lambda: note_value(res.row(N, "brute", 20), "subsets"))
    add("C3.3", 3, "brute: time at n = 20 (s)", 0.5, 0.25, 1.1, lambda: at(res, N, "brute", 20))
    add("C3.4", 3, "smallest n at which dp is faster than brute", 8.0, 8.0, 11.0,
        lambda: min(s for s, t in res.series(N, "dp") if t < dict(res.series(N, "brute"))[s]))
    add("C3.5", 3, "brute time / dp time at n = 20", 5000.0, 1500.0, 15000.0,
        lambda: at(res, N, "brute", 20) / at(res, N, "dp", 20))
    add("C3.6", 3, "dp time / greedy time, mean over the five sizes", 1.3, 1.0, 1.9,
        lambda: _mean(at(res, N, "dp", s) / at(res, N, "greedy", s) for s, _ in res.series(N, "dp")))
    add("C3.7", 3, "brute, dp and dpquad return the same total (share of sizes)", 1.0, 1.0, 1.0,
        lambda: _mean(float(len({note_value(res.row(N, a, s), "total") for a in ("brute", "dp", "dpquad")}) == 1)
                      for s, _ in res.series(N, "dp")))
    add("C3.8", 3, "dpquad time / dp time, mean over the five sizes", 1.15, 0.85, 1.6,
        lambda: _mean(at(res, N, "dpquad", s) / at(res, N, "dp", s) for s, _ in res.series(N, "dp")))

    add("C4.1", 4, "dpquad at the DNF size: status (1 = DNF, 0 = finished)", 1.0, 1.0, 1.0,
        lambda: 1.0 if next(r for r in res.rows if (r["experiment"], r["algorithm"]) == ("C-dnf", "dpquad"))["status"] == "DNF" else 0.0)
    add("C4.2", 4, "dpquad at n = 200 000: time extrapolated from the fit on n <= 3000 (s)", 600.0, 250.0, 1500.0,
        lambda: (lambda pts: 2 ** (lambda f: f["intercept"] + f["slope"] * math.log2(200000))(
            measure.fit_loglog([p[0] for p in pts], [p[1] for p in pts])))(res.series(S, "dpquad")))
    add("C4.3", 4, "dp at n = 200 000: time (s)", 2.5, 1.2, 7.0,
        lambda: float(next(r for r in res.rows if (r["experiment"], r["algorithm"]) == ("C-dnf", "dp"))["time_s"]))
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
            lines.append(f"| {pid} | {text} | {point:g} ({lo:g} to {hi:g}) | {got:.4g} | {item[6]} | {item[7] * 100:.0f} % |")
    hits = sum(1 for i in items if i[6] == "HIT")
    miss = sum(1 for i in items if i[6] == "MISS")
    skipped = len(items) - hits - miss
    lines.append(f"\n{len(items)} predictions: {hits} hit, {miss} miss, {skipped} not evaluated (round not run yet).")
    text = "\n".join(lines)
    print(text)
    with open(os.path.join(folder, "predictions-vs-measurements-C.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
