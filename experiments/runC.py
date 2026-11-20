"""Experiments for module C (rescue scheduling).

    python experiments/runC.py --master PATH/TO/master_release_v1 --round 1
    python experiments/runC.py --master PATH/TO/master_release_v1 --round all

Rounds (each has an entry in predlogC.md that is written BEFORE the round is run):
    1  growth in n of the greedy rule (count), the DP with binary search and the O(n^2) DP (value), n = 47 ... 3000
    2  quality of the greedy rule against the DP on 62 sampled master-data cases (count and value), and the claims of tier S
    3  small inputs (n = 8 ... 20): DP, O(n^2) DP and greedy against brute force
    4  the 5 minute rule: the O(n^2) DP and the DP at n = 200 000 windows (about 5 minutes for the O(n^2) DP if it does not finish)

Protocol (Section 7.3, as in experiments/runAD.py): one warm-up run, 5 timed runs, median and IQR, one thread, garbage collection off while timing,
data loading excluded, DNF at 300 s. Rows are written to results/results.csv: old rows of the same (module, experiment) are replaced,
all other rows (modules A and D) are kept untouched. Also written: results/quality-C.csv and results/environmentC.json
(results/environment.json belongs to the runs of modules A and D and is not touched).
"""
import argparse
import csv
import json
import math
import os
import sys
from time import perf_counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from experiments import mastersample as ms  # noqa: E402
from experiments import sampleC as sc  # noqa: E402
from src import measure  # noqa: E402
from src.modules import rescue as C  # noqa: E402

SIZES_N = [47, 94, 188, 375, 750, 1500, 3000]
SIZES_SMALL = [8, 11, 14, 17, 20]
SIZE_DNF = 200000
QUALITY_PLAN = [("S", 20), ("M", 20), ("L", 10), ("X", 12)]

# (algorithm name, objective, method) of every experiment; greedy is timed for the count, the others for the value
SCALE_ALGS = [("greedy", "count"), ("dp", "value"), ("dpquad", "value")]
SMALL_ALGS = [("dp", "value"), ("dpquad", "value"), ("brute", "value"), ("greedy", "count")]


def total_ops(o):
    """The `ops` column: all counted operations of the algorithm (not `calls`, not the preprocessing in `pre`)."""
    return o["comparisons"] + o["moves"] + o["probes"] + o["items_examined"] + o["cells"] + o["subsets"]


def ops_of(plan, objective):
    o = plan.ops
    detail = (f"objective={objective}; comparisons={o['comparisons']}; moves={o['moves']}; probes={o['probes']}; "
              f"items={o['items_examined']}; cells={o['cells']}; subsets={o['subsets']}; pre_items={o['pre']['items_examined']}; "
              f"pre_pair_tests={o['pre']['pair_tests']}; chosen={len(plan.chosen)}; total={plan.total}")
    return total_ops(o), detail


def measure_row(experiment, algorithm, objective, instance, size, windows, repeats, mem_limit_s=8.0):
    """Run solve(windows, objective, algorithm) with the protocol of Section 7.3 and return one results.csv row."""
    base = dict(module="C", experiment=experiment, algorithm=algorithm, instance=instance, size=size, size2="")

    def call(deadline):
        return C.solve(windows, objective, algorithm, deadline)

    first = perf_counter()
    try:
        call(perf_counter() + measure.DNF_SECONDS)                    # also the calibration for batching
    except Exception as exc:
        if type(exc).__name__ != "TimeBudgetExceeded":
            raise
        return dict(base, status="DNF", note=f"objective={objective}; single run passed 300 s; no time recorded")
    one = perf_counter() - first
    batch = max(1, math.ceil(0.01 / one)) if one < 0.01 else 1       # tiny runs: time a batch, divide

    def timed(deadline):
        result = None
        for _ in range(batch):
            result = call(deadline)
        return result

    times, result = measure.time_runs(timed, repeats=repeats, warmup=1)
    if times is None:
        return dict(base, status="DNF", note=f"objective={objective}; a run passed 300 s; no time recorded")
    if result.status != "OK":
        raise RuntimeError(f"{experiment} {algorithm} n={size}: status {result.status} ({result.note})")
    med, iqr = measure.median_iqr([t / batch for t in times])
    mem, mem_note = "", ""
    if med * batch <= mem_limit_s:
        mem = measure.peak_memory(call)
    else:
        mem_note = "memory not measured (tracemalloc too slow at this size)"
    ops, detail = ops_of(result, objective)
    note = f"{detail}; batch={batch}" if batch > 1 else detail
    if mem_note:
        note += "; " + mem_note
    return dict(base, time_s=f"{med:.9g}", time_iqr_s=f"{iqr:.9g}", ops=ops, mem_bytes=mem, status="OK", note=note)


def report(row, n):
    print(f"  n={n} {row['algorithm']}: {row.get('time_s', row['status'])} s", flush=True)


# ------------------------------------------------------------------ rounds
def tier_pool_source(master, cases, tier, how_many):
    start = sc.first_sample(cases, tier)
    seq = ms.consecutive_cases(cases, tier, start, how_many)
    return start, seq, sc.read_windows(master, [c["case_id"] for c in seq])


def round1(master, out, cases, repeats, quick):
    rows = []
    sizes = [47, 94, 188] if quick else SIZES_N
    start, seq, by_case = tier_pool_source(master, cases, "L", 8)
    print(f"[round 1] pool of tier L cases starting at {start}", flush=True)
    for n in sizes:
        windows, joined = sc.pool_windows(seq, by_case, n)
        inst = f"pool L from {start}, {len(joined)} cases"
        for name, objective in SCALE_ALGS:
            row = measure_row("C-scale-n", name, objective, inst, n, windows, repeats)
            rows.append(row)
            report(row, n)
        dp, quad = C.solve(windows, "value", "dp"), C.solve(windows, "value", "dpquad")
        rows[-1]["note"] += f"; same_total_as_dp={int(dp.total == quad.total)}"
        if dp.total != quad.total:
            print(f"  WARNING: dp and dpquad totals differ at n={n}: {dp.total} against {quad.total}", flush=True)
    measure.write_results(os.path.join(out, "results.csv"), rows, {("C", "C-scale-n")})


def round2(master, out, cases, repeats, quick):
    plan = [("S", 5), ("M", 3), ("L", 1), ("X", 3)] if quick else QUALITY_PLAN
    chosen = [(t, c) for t, n in plan for c in ms.sample_cases(cases, t, n)]
    wins = sc.read_windows(master, [c["case_id"] for _, c in chosen])
    claims = sc.read_claims(master)
    rows = []
    for tier, c in chosen:
        w = wins[c["case_id"]]
        g_count, d_count = C.solve(w, "count", "greedy"), C.solve(w, "count", "dp")
        g_value, d_value = C.solve(w, "value", "greedy"), C.solve(w, "value", "dp")
        claim = claims.get(c["case_id"])
        rows.append(dict(tier=tier, case_id=c["case_id"], case_no=c["case_no"], n=len(w),
                         greedy_count=g_count.total, dp_count=d_count.total, greedy_count_optimal=int(g_count.total == d_count.total),
                         greedy_value=g_value.total, dp_value=d_value.total,
                         greedy_over_dp=f"{g_value.total / d_value.total:.6f}",
                         greedy_value_optimal=int(g_value.total == d_value.total),
                         dp_value_plan_windows=len(d_value.chosen), greedy_plan_windows=len(g_value.chosen),
                         count_claim=claim[0] if claim else "", value_claim=claim[1] if claim else "",
                         greedy_count_matches_claim=int(g_count.total == claim[0]) if claim else "",
                         dp_value_matches_claim=int(d_value.total == claim[1]) if claim else ""))
    write_csv(os.path.join(out, "quality-C.csv"), rows)
    print(f"[round 2] quality C: {len(rows)} cases", flush=True)


def round3(master, out, cases, repeats, quick):
    rows = []
    sizes = [8, 11, 14] if quick else SIZES_SMALL
    start, seq, by_case = tier_pool_source(master, cases, "S", 6)
    print(f"[round 3] pool of tier S cases starting at {start}", flush=True)
    for n in sizes:
        windows, joined = sc.pool_windows(seq, by_case, n)
        inst = f"pool S from {start}, {len(joined)} cases"
        for name, objective in SMALL_ALGS:
            row = measure_row("C-small-n", name, objective, inst, n, windows, repeats)
            rows.append(row)
            report(row, n)
    measure.write_results(os.path.join(out, "results.csv"), rows, {("C", "C-small-n")})


def round4(master, out, cases, repeats, quick):
    n = 20000 if quick else SIZE_DNF
    start, seq, by_case = tier_pool_source(master, cases, "L", 160)
    windows, joined = sc.pool_windows(seq, by_case, n)
    inst = f"pool L from {start}, {len(joined)} cases"
    print(f"[round 4] {n} windows from {len(joined)} cases starting at {start}", flush=True)
    rows = []
    for name in ("dp", "dpquad"):
        row = measure_row("C-dnf", name, "value", inst, n, windows, repeats=1 if name == "dpquad" else repeats)
        rows.append(row)
        print(f"  n={n} {name}: {row.get('time_s', row['status'])}", flush=True)
    measure.write_results(os.path.join(out, "results.csv"), rows, {("C", "C-dnf")})


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--master", required=True, help="folder with the master dataset CSV files")
    ap.add_argument("--round", default="all", help="1, 2, 3, 4 or all (all = 1, 2, 3; round 4 is separate)")
    ap.add_argument("--out", default=os.path.join(ROOT, "results"))
    ap.add_argument("--quick", action="store_true", help="tiny sizes and 2 repeats, only to test the script (writes to results/_quick)")
    a = ap.parse_args()
    out = a.out if not a.quick else os.path.join(a.out, "_quick")
    os.makedirs(out, exist_ok=True)
    cases = ms.read_cases(a.master)
    repeats = 2 if a.quick else 5
    env = measure.describe_environment()
    env.update(master_release="master_release_v1", group_seed=ms.GROUP_SEED, repeats=repeats, warmup_runs=1,
               dnf_seconds=measure.DNF_SECONDS, module="C")
    with open(os.path.join(out, "environmentC.json"), "w", encoding="utf-8") as f:
        json.dump(env, f, indent=2)
    runners = {"1": round1, "2": round2, "3": round3, "4": round4}
    todo = ["1", "2", "3"] if a.round == "all" else [a.round]
    for r in todo:
        runners[r](a.master, out, cases, repeats, a.quick)


if __name__ == "__main__":
    main()
