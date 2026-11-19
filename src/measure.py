"""Measurement helpers shared by all experiments (Section 7.3 of the statement).

Protocol, as stated in the README:
  * one discarded warm-up run, then the median of 5 timed runs with the
    interquartile range (IQR), single-threaded, garbage collector switched off
    while a run is timed, data loading excluded (the input is built before);
  * memory beyond the input = peak of tracemalloc during one extra run;
  * a run past 300 seconds is a DNF (the algorithm gets a deadline and raises
    TimeBudgetExceeded, the harness records status DNF).
Quartiles use linear interpolation between the closest ranks.
"""
import csv
import gc
import math
import os
import platform
import sys
import tracemalloc
from time import perf_counter

from .models import TimeBudgetExceeded

DNF_SECONDS = 300.0
RESULT_COLUMNS = ["module", "experiment", "algorithm", "instance", "size", "size2",
                  "time_s", "time_iqr_s", "ops", "mem_bytes", "status", "note"]

_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
        10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110,
        18: 2.101, 19: 2.093, 20: 2.086, 25: 2.060, 30: 2.042}


# ------------------------------------------------------------- statistics
def quantile(sorted_xs, q):
    """q-quantile of a sorted list, linear interpolation."""
    if not sorted_xs:
        raise ValueError("no data")
    pos = (len(sorted_xs) - 1) * q
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_xs) - 1)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (pos - lo)


def median_iqr(xs):
    s = sorted(xs)
    return quantile(s, 0.5), quantile(s, 0.75) - quantile(s, 0.25)


def t95(df):
    if df in _T95:
        return _T95[df]
    keys = sorted(_T95)
    lower = [k for k in keys if k <= df]
    return _T95[lower[-1]] if df < 30 else 1.96


def ols(xs, ys):
    """Least-squares line y = a + b x with the 95 percent interval of b and R^2."""
    n = len(xs)
    if n < 3:
        raise ValueError("a fit needs at least 3 points (the statement asks for 5)")
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    sse = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    sst = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 if sst == 0 else 1 - sse / sst
    se_b = math.sqrt(sse / (n - 2) / sxx) if n > 2 and sxx > 0 else float("nan")
    return {"intercept": a, "slope": b, "ci95": t95(n - 2) * se_b, "r2": r2, "n": n}


def fit_loglog(sizes, values):
    """Polynomial growth: log2(value) = a + b log2(size); b is the exponent."""
    return ols([math.log2(x) for x in sizes], [math.log2(y) for y in values])


def fit_semilog(sizes, values):
    """Exponential growth: log2(value) = a + b size; the base is 2**b."""
    f = ols(list(sizes), [math.log2(y) for y in values])
    f["base"] = 2 ** f["slope"]
    f["base_ci95"] = (2 ** (f["slope"] - f["ci95"]), 2 ** (f["slope"] + f["ci95"]))
    return f


def relative_error(predicted, measured):
    return abs(predicted - measured) / abs(measured) if measured else float("inf")


# -------------------------------------------------------------- measuring
def time_runs(call, repeats=5, warmup=1):
    """call(deadline) -> result. Returns (times, last_result), or (None, None) on DNF."""
    result = None
    for i in range(warmup + repeats):
        gc.collect()
        gc.disable()
        try:
            start = perf_counter()
            try:
                result = call(start + DNF_SECONDS)
            except TimeBudgetExceeded:
                return None, None
            elapsed = perf_counter() - start
        finally:
            gc.enable()
        if elapsed > DNF_SECONDS:
            return None, None
        if i == 0:
            times = []
        if i >= warmup:
            times.append(elapsed)
    return times, result


def peak_memory(call):
    """Peak bytes allocated by one run of call(deadline), measured with tracemalloc."""
    gc.collect()
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        call(perf_counter() + DNF_SECONDS)
        return tracemalloc.get_traced_memory()[1]
    except TimeBudgetExceeded:
        return None
    finally:
        tracemalloc.stop()


def describe_environment():
    cpu = platform.processor()
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    return {"python": sys.version.split()[0], "implementation": platform.python_implementation(),
            "os": f"{platform.system()} {platform.release()}", "cpu": cpu,
            "logical_cpus": os.cpu_count(), "threads_used": 1}


# ------------------------------------------------------------ results file
def write_results(path, rows, replace_keys):
    """Write rows to results.csv. Old rows with the same (module, experiment) as a new one are replaced."""
    keep = []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if (r["module"], r["experiment"]) not in replace_keys:
                    keep.append(r)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_COLUMNS)
        w.writeheader()
        for r in keep + rows:
            w.writerow({k: r.get(k, "") for k in RESULT_COLUMNS})
