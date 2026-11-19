"""Numerical predictions of Ayna for modules A and D, written BEFORE the full runs.

Each entry: (id, round, what is measured, point prediction, lowest and highest value
that still counts as a hit, function that extracts the measured value).
`python experiments/predictionsAD.py` compares them with results/ and prints a table
(HIT / MISS and the relative error |prediction - measurement| / measurement).
The same numbers, with the reasoning, are in prediction_log.md.
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
            self.rows = list(csv.DictReader(f))

    def series(self, module, experiment, algorithm, field="time_s", keyfield="size"):
        out = []
        for r in self.rows:
            if (r["module"], r["experiment"], r["algorithm"]) == (module, experiment, algorithm) and r["status"] == "OK" and r[field] != "":
                out.append((float(r[keyfield]), float(r[field])))
        return sorted(out)

    def row(self, module, experiment, algorithm, size):
        for r in self.rows:
            if (r["module"], r["experiment"], r["algorithm"]) == (module, experiment, algorithm) and float(r["size"]) == size:
                return r
        return None

    def quality(self, name):
        with open(os.path.join(self.folder, name), newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


def note_value(row, key):
    for part in row["note"].split(";"):
        part = part.strip()
        if part.startswith(key + "="):
            return float(part.split("=", 1)[1])
    raise KeyError(key)


def slope(res, module, exp, alg, keyfield="size"):
    pts = res.series(module, exp, alg, keyfield=keyfield)
    return measure.fit_loglog([p[0] for p in pts], [p[1] for p in pts])["slope"]


def largest(res, module, exp, alg, field="time_s"):
    pts = res.series(module, exp, alg, field)
    return pts[-1] if pts else (None, None)


def ratio_at(res, module, exp, alg1, alg2, size):
    a, b = res.row(module, exp, alg1, size), res.row(module, exp, alg2, size)
    return float(a["time_s"]) / float(b["time_s"])


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def build(res):
    P = []

    def add(pid, rnd, text, point, lo, hi, fn):
        P.append((pid, rnd, text, point, lo, hi, fn))

    add("1.1", 1, "A dp: log-log slope of time against n (W grows with n)", 2.0, 1.75, 2.25,
        lambda: slope(res, "A", "A-scale-n", "dp"))
    add("1.2", 1, "A greedy: log-log slope of time against n", 1.1, 0.9, 1.3,
        lambda: slope(res, "A", "A-scale-n", "greedy"))
    add("1.3", 1, "A dp: time at n = 6400 (s)", 14.0, 9.0, 21.0,
        lambda: res.series("A", "A-scale-n", "dp")[-1][1])
    add("1.4", 1, "A dp time / greedy time at n = 6400", 450.0, 200.0, 1500.0,
        lambda: ratio_at(res, "A", "A-scale-n", "dp", "greedy", 6400))
    add("1.5", 1, "A dp: smallest value over all sizes of cells / (n*W)", 0.985, 0.97, 1.0,
        lambda: min(float(r["ops"]) / (float(r["size"]) * float(r["size2"])) for r in res.rows
                    if r["experiment"] == "A-scale-n" and r["algorithm"] == "dp" and r["status"] == "OK"))
    add("1.6", 1, "A dp: peak memory / (n*W) at the largest size with memory measured", 1.1, 1.0, 1.3,
        lambda: (lambda pts: pts[-1][1] / (pts[-1][0] * float(res.row("A", "A-scale-n", "dp", pts[-1][0])["size2"])))(
            res.series("A", "A-scale-n", "dp", "mem_bytes")))
    add("1.7", 1, "A greedy: peak memory per crate at n = 6400 (bytes)", 80.0, 40.0, 120.0,
        lambda: float(res.row("A", "A-scale-n", "greedy", 6400)["mem_bytes"]) / 6400)
    add("1.8", 1, "A dp: log-log slope of time against W at fixed n", 0.95, 0.8, 1.1,
        lambda: slope(res, "A", "A-scale-W", "dp", keyfield="size2"))
    add("1.9", 1, "A greedy: log-log slope of time against W at fixed n", 0.0, -0.15, 0.15,
        lambda: slope(res, "A", "A-scale-W", "greedy", keyfield="size2"))
    add("1.10", 1, "A tier S sample: share of cases where greedy is not optimal", 0.55, 0.30, 0.80,
        lambda: 1 - _mean(int(r["greedy_optimal"]) for r in res.quality("quality-A.csv") if r["tier"] == "S"))
    add("1.11", 1, "A tiers M and L samples: mean greedy / dp value", 0.997, 0.990, 1.0,
        lambda: _mean(float(r["greedy_over_dp"]) for r in res.quality("quality-A.csv") if r["tier"] in ("M", "L")))
    add("1.12", 1, "A trap-47 cases: mean greedy / dp value", 0.55, 0.45, 0.65,
        lambda: _mean(float(r["greedy_over_dp"]) for r in res.quality("quality-A.csv") if r["tier"] == "X47"))
    add("1.13", 1, "A tier S sample: share of cases where dp equals the claim", 1.0, 1.0, 1.0,
        lambda: _mean(int(r["dp_matches_claim"]) for r in res.quality("quality-A.csv") if r["tier"] == "S"))

    add("2.1", 2, "A brute force: growth base per extra crate (semi-log fit)", 2.0, 1.85, 2.15,
        lambda: measure.fit_semilog([p[0] for p in res.series("A", "A-small-n", "brute")],
                                    [p[1] for p in res.series("A", "A-small-n", "brute")])["base"])
    add("2.2", 2, "A brute force: time at n = 20 (s)", 0.17, 0.10, 0.30,
        lambda: res.series("A", "A-small-n", "brute")[-1][1])
    add("2.3", 2, "A dp time / greedy time, mean over the five small sizes", 4.0, 2.0, 8.0,
        lambda: _mean(ratio_at(res, "A", "A-small-n", "dp", "greedy", s) for s, _ in res.series("A", "A-small-n", "dp")))
    add("2.4", 2, "A smallest n at which dp is faster than brute force", 8.0, 8.0, 11.0,
        lambda: min(s for s, t in res.series("A", "A-small-n", "dp")
                    if t < dict(res.series("A", "A-small-n", "brute"))[s]))

    add("3.1", 3, "D heap: log-log slope of time against m", 1.1, 0.95, 1.3,
        lambda: slope(res, "D", "D-scale-m", "heap"))
    add("3.2", 3, "D scan: log-log slope of time against m", 1.9, 1.7, 2.1,
        lambda: slope(res, "D", "D-scale-m", "scan"))
    add("3.3", 3, "D scan: key comparisons at m = 8000", 10.9e6, 6e6, 16e6,
        lambda: note_value(res.row("D", "D-scale-m", "scan", 8000), "comparisons"))
    add("3.4", 3, "D scan: time at m = 64000 (s)", 51.0, 25.0, 100.0,
        lambda: res.series("D", "D-scale-m", "scan")[-1][1])
    add("3.5", 3, "D heap: time at m = 64000 (s)", 0.5, 0.25, 1.0,
        lambda: res.series("D", "D-scale-m", "heap")[-1][1])
    add("3.6", 3, "D scan time / heap time at m = 250", 1.2, 0.6, 2.0,
        lambda: ratio_at(res, "D", "D-scale-m", "scan", "heap", 250))
    add("3.7", 3, "D maximum backlog / m at m = 64000", 0.33, 0.20, 0.45,
        lambda: note_value(res.row("D", "D-scale-m", "heap", 64000), "max_backlog") / 64000)
    add("3.8", 3, "D heap: ops/(m log2 m) at m = 64000 divided by the same at m = 250", 1.0, 0.75, 1.25,
        lambda: (lambda a, b: (float(b["ops"]) / (64000 * math.log2(64000))) / (float(a["ops"]) / (250 * math.log2(250))))(
            res.row("D", "D-scale-m", "heap", 250), res.row("D", "D-scale-m", "heap", 64000)))
    add("3.9", 3, "D heap: peak memory per alarm at m = 8000 (bytes)", 250.0, 120.0, 400.0,
        lambda: float(res.row("D", "D-scale-m", "heap", 8000)["mem_bytes"]) / 8000)
    add("3.10", 3, "D: largest difference of the mean wait of all alarms, urgency order against first-come-first-served", 0.0, 0.0, 1e-6,
        lambda: max(abs(float(r["mean_wait_urgency"]) - float(r["mean_wait_fifo"])) for r in res.quality("quality-D.csv")))
    add("3.11", 3, "D tier L: mean wait of priority 9 and 10 alarms, first-come-first-served / urgency order", 80.0, 20.0, 1000.0,
        lambda: _mean(float(r["mean_wait_p9plus_fifo"]) for r in res.quality("quality-D.csv") if r["tier"] == "L")
        / max(1e-9, _mean(float(r["mean_wait_p9plus_urgency"]) for r in res.quality("quality-D.csv") if r["tier"] == "L")))

    add("4.1", 4, "D scan at m = 256000: status (1 = DNF, 0 = finished)", 1.0, 1.0, 1.0,
        lambda: 1.0 if res.row("D", "D-dnf", "scan", 256000)["status"] == "DNF" else 0.0)
    add("4.2", 4, "D scan at m = 256000: extrapolated time from the fit on m <= 64000 (s)", 670.0, 400.0, 1100.0,
        lambda: (lambda pts: 2 ** (lambda f: f["intercept"] + f["slope"] * math.log2(256000))(
            measure.fit_loglog([p[0] for p in pts], [p[1] for p in pts])))(res.series("D", "D-scale-m", "scan")))
    add("4.3", 4, "D heap at m = 256000: time (s)", 2.5, 1.2, 5.0,
        lambda: float(res.row("D", "D-dnf", "heap", 256000)["time_s"]))
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
    for item in evaluate(folder):
        pid, text, point, lo, hi, got = item[:6]
        if got is None:
            lines.append(f"| {pid} | {text} | {point:g} ({lo:g} to {hi:g}) | - | {item[6]} | - |")
        else:
            lines.append(f"| {pid} | {text} | {point:g} ({lo:g} to {hi:g}) | {got:.4g} | {item[6]} | {item[7] * 100:.0f} % |")
    text = "\n".join(lines)
    print(text)
    with open(os.path.join(folder, "predictions-vs-measurements-AD.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
