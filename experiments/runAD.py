"""Experiments for modules A (relief inventory) and D (emergency queue).

    python experiments/runAD.py --master PATH/TO/master_release_v1 --round 1
    python experiments/runAD.py --master PATH/TO/master_release_v1 --round all

Rounds (each has an entry in prediction_log.md that is committed BEFORE the round is run):
    1  module A, growth in n and in W, and solution quality (greedy against DP)
    2  module A, small inputs: DP and greedy against brute force (n <= 20)
    3  module D, growth in m, and answer quality (urgency order against first-come-first-served)
    4  module D, one run of the baseline at m = 256000 to document the DNF rule (about 5 minutes)

Writes results/results.csv (rows of these experiments are replaced, others kept),
results/quality-A.csv, results/quality-D.csv and results/environment.json.
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
from src import measure  # noqa: E402
from src.modules import emergencyqueue as D, inventory as A  # noqa: E402

SIZES_A_N = [200, 400, 800, 1600, 3200, 6400]
SIZES_A_SMALL = [8, 11, 14, 17, 20]
SIZES_D_M = [250, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000]
SIZE_D_DNF = 256000
W_SWEEP_N = 1600
W_SWEEP_STEPS = [32, 16, 8, 4, 2, 1]      # W = total weight / step


def measure_row(module, experiment, algorithm, instance, size, size2, call, ops_of, repeats, mem_limit_s=8.0):
    """Run `call(deadline)` with the protocol of Section 7.3 and return one results.csv row."""
    first = perf_counter()
    try:
        call(perf_counter() + measure.DNF_SECONDS)                    # also the calibration for batching
    except Exception as exc:                                         # TimeBudgetExceeded -> DNF
        if type(exc).__name__ != "TimeBudgetExceeded":
            raise
        return dict(module=module, experiment=experiment, algorithm=algorithm, instance=instance, size=size,
                    size2=size2, status="DNF", note="single run passed 300 s; no time recorded")
    one = perf_counter() - first
    batch = max(1, math.ceil(0.01 / one)) if one < 0.01 else 1       # tiny runs: time a batch, divide

    def timed(deadline):
        result = None
        for _ in range(batch):
            result = call(deadline)
        return result

    times, result = measure.time_runs(timed, repeats=repeats, warmup=1)
    if times is None:
        return dict(module=module, experiment=experiment, algorithm=algorithm, instance=instance, size=size,
                    size2=size2, status="DNF", note="a run passed 300 s; no time recorded")
    med, iqr = measure.median_iqr([t / batch for t in times])
    mem, mem_note = "", ""
    if med * batch <= mem_limit_s:
        mem = measure.peak_memory(call)
    else:
        mem_note = "memory not measured (tracemalloc too slow at this size)"
    ops, detail = ops_of(result)
    note = f"{detail}; batch={batch}" if batch > 1 else detail
    if mem_note:
        note += "; " + mem_note
    return dict(module=module, experiment=experiment, algorithm=algorithm, instance=instance, size=size,
                size2=size2, time_s=f"{med:.9g}", time_iqr_s=f"{iqr:.9g}", ops=ops, mem_bytes=mem,
                status="OK", note=note)


def ops_a_dp(plan):
    o = plan.ops
    return o["cells"], f"cells={o['cells']}; items={o['items_examined']}; value={plan.total_value}"


def ops_a_greedy(plan):
    o = plan.ops
    return o["comparisons"] + o["moves"], (f"comparisons={o['comparisons']}; moves={o['moves']}; "
                                            f"value={plan.total_value}")


def ops_a_brute(plan):
    return plan.ops["subsets"], f"subsets={plan.ops['subsets']}; value={plan.total_value}"


def ops_d(plan):
    o, pre = plan.ops, plan.ops["pre"]
    return (o["comparisons"] + o["moves"],
            f"comparisons={o['comparisons']}; moves={o['moves']}; pre_comparisons={pre['comparisons']}; "
            f"pre_moves={pre['moves']}; max_backlog={plan.max_backlog}")


# ------------------------------------------------------------------ rounds
def first_sample(cases, tier):
    return ms.sample_cases(cases, tier, 1)[0]["case_id"]


def round1(master, out, cases, repeats, quick):
    rows = []
    sizes = [100, 200, 400] if quick else SIZES_A_N
    start = first_sample(cases, "L")
    seq = ms.consecutive_cases(cases, "L", start, 14)
    by_case = ms.read_crates(master, [c["case_id"] for c in seq])
    print(f"[round 1] pool of tier L cases starting at {start}", flush=True)
    for n in sizes:
        crates, W, joined = ms.pool_crates(seq, by_case, n)
        inst = f"pool L from {start}, {len(joined)} cases"
        for name, fn, ops_of in (("dp", A.solve_dp, ops_a_dp), ("greedy", A.solve_greedy, ops_a_greedy)):
            row = measure_row("A", "A-scale-n", name, inst, n, W, lambda dl, f=fn: f(crates, W, dl), ops_of, repeats)
            rows.append(row)
            print(f"  n={n} W={W} {name}: {row.get('time_s', row['status'])} s", flush=True)
    # growth in W at fixed n
    n = 400 if quick else W_SWEEP_N
    crates, W0, joined = ms.pool_crates(seq, by_case, n)
    total = sum(c.weight for c in crates)
    for step in W_SWEEP_STEPS:
        W = total // step
        inst = f"pool L from {start}, first {n} crates, total weight {total}"
        for name, fn, ops_of in (("dp", A.solve_dp, ops_a_dp), ("greedy", A.solve_greedy, ops_a_greedy)):
            row = measure_row("A", "A-scale-W", name, inst, n, W, lambda dl, f=fn: f(crates, W, dl), ops_of, repeats)
            rows.append(row)
            print(f"  n={n} W={W} {name}: {row.get('time_s', row['status'])} s", flush=True)
    measure.write_results(os.path.join(out, "results.csv"), rows, {("A", "A-scale-n"), ("A", "A-scale-W")})
    quality_a(master, out, cases, quick)


def quality_a(master, out, cases, quick):
    claims = {}
    with open(os.path.join(master, "claims.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            claims[r["case_id"]] = int(r["cargo_opt"])
    plan = [("S", 20), ("M", 20), ("L", 10), ("X", 12)]
    if quick:
        plan = [("S", 5), ("M", 3), ("L", 1), ("X", 3)]
    chosen = [(t, c) for t, n in plan for c in ms.sample_cases(cases, t, n)]
    # all trap-47 cases (best-looking-crate trap) of the master data, same positions rule inside that list
    trap47 = [c for c in ms.tier_cases(cases, "X") if c["case_no"] == "47"]
    chosen += [("X47", c) for c in [trap47[i] for i in range(ms.GROUP_SEED % 7, len(trap47), 7)][:12 if not quick else 3]]
    crates = ms.read_crates(master, [c["case_id"] for _, c in chosen])
    rows = []
    for tier, c in chosen:
        cr, W = crates[c["case_id"]], int(c["capacity"])
        dp, gr = A.solve_dp(cr, W), A.solve_greedy(cr, W)
        claim = claims.get(c["case_id"], "")
        rows.append(dict(tier=tier, case_id=c["case_id"], case_no=c["case_no"], n=len(cr), capacity=W,
                         dp_value=dp.total_value, greedy_value=gr.total_value,
                         greedy_over_dp=f"{gr.total_value / dp.total_value:.6f}" if dp.total_value else "",
                         greedy_optimal=int(gr.total_value == dp.total_value), claim=claim,
                         dp_matches_claim=("" if claim == "" else int(dp.total_value == claim))))
    write_csv(os.path.join(out, "quality-A.csv"), rows)
    print(f"  quality A: {len(rows)} cases", flush=True)


def round2(master, out, cases, repeats, quick):
    rows = []
    start = first_sample(cases, "S")
    seq = ms.consecutive_cases(cases, "S", start, 6)
    by_case = ms.read_crates(master, [c["case_id"] for c in seq])
    sizes = [8, 11, 14] if quick else SIZES_A_SMALL
    for n in sizes:
        crates, W, joined = ms.pool_crates(seq, by_case, n)
        inst = f"pool S from {start}, {len(joined)} cases"
        for name, fn, ops_of in (("dp", A.solve_dp, ops_a_dp), ("greedy", A.solve_greedy, ops_a_greedy),
                                 ("brute", A.solve_brute, ops_a_brute)):
            row = measure_row("A", "A-small-n", name, inst, n, W, lambda dl, f=fn: f(crates, W, dl), ops_of, repeats)
            rows.append(row)
            print(f"  n={n} W={W} {name}: {row.get('time_s', row['status'])} s", flush=True)
    measure.write_results(os.path.join(out, "results.csv"), rows, {("A", "A-small-n")})


def round3(master, out, cases, repeats, quick):
    rows = []
    sizes = [250, 500, 1000] if quick else SIZES_D_M
    start = first_sample(cases, "L")
    seq = ms.consecutive_cases(cases, "L", start, 6 if quick else 40)
    by_case = ms.read_alarms(master, [c["case_id"] for c in seq])
    print(f"[round 3] pool of tier L alarm streams starting at {start}", flush=True)
    for m in sizes:
        alarms, joined = ms.pool_alarms(seq, by_case, m)
        inst = f"pool L from {start}, {len(joined)} cases"
        for name, fn in (("heap", D.release_heap), ("scan", D.release_scan)):
            row = measure_row("D", "D-scale-m", name, inst, m, "", lambda dl, f=fn: f(alarms, dl), ops_d, repeats)
            rows.append(row)
            print(f"  m={m} {name}: {row.get('time_s', row['status'])} s", flush=True)
    measure.write_results(os.path.join(out, "results.csv"), rows, {("D", "D-scale-m")})
    quality_d(master, out, cases, quick)


def quality_d(master, out, cases, quick):
    plan = [("S", 20), ("M", 20), ("L", 10), ("X", 12)]
    if quick:
        plan = [("S", 5), ("M", 3), ("L", 1), ("X", 3)]
    chosen = [(t, c) for t, n in plan for c in ms.sample_cases(cases, t, n)]
    streams = ms.read_alarms(master, [c["case_id"] for _, c in chosen])
    rows = []
    for tier, c in chosen:
        al = streams[c["case_id"]]
        urgent = {a.alarm_id for a in al if a.priority >= 9}
        res = {}
        for name, fn in (("urgency", D.release_heap), ("fifo", D.release_fifo)):
            plan_ = fn(al)
            arrival = {a.alarm_id: a.tick for a in al}
            waits = {i: t - arrival[i] for i, t in plan_.releases}
            uw = [waits[i] for i in urgent] or [0]
            res[name] = (plan_.total_wait / len(al), max(uw), sum(uw) / len(uw))
        rows.append(dict(tier=tier, case_id=c["case_id"], case_no=c["case_no"], alarms=len(al), urgent_alarms=len(urgent),
                         mean_wait_urgency=f"{res['urgency'][0]:.3f}", mean_wait_fifo=f"{res['fifo'][0]:.3f}",
                         max_wait_p9plus_urgency=res["urgency"][1], max_wait_p9plus_fifo=res["fifo"][1],
                         mean_wait_p9plus_urgency=f"{res['urgency'][2]:.3f}", mean_wait_p9plus_fifo=f"{res['fifo'][2]:.3f}"))
    write_csv(os.path.join(out, "quality-D.csv"), rows)
    print(f"  quality D: {len(rows)} cases", flush=True)


def round4(master, out, cases, repeats, quick):
    start = first_sample(cases, "L")
    seq = ms.consecutive_cases(cases, "L", start, 120)
    by_case = ms.read_alarms(master, [c["case_id"] for c in seq])
    m = 20000 if quick else SIZE_D_DNF
    alarms, joined = ms.pool_alarms(seq, by_case, m)
    inst = f"pool L from {start}, {len(joined)} cases"
    rows = []
    for name, fn in (("heap", D.release_heap), ("scan", D.release_scan)):
        row = measure_row("D", "D-dnf", name, inst, m, "", lambda dl, f=fn: f(alarms, dl), ops_d,
                          repeats=1 if name == "scan" else repeats)
        rows.append(row)
        print(f"  m={m} {name}: {row.get('time_s', row['status'])}", flush=True)
    measure.write_results(os.path.join(out, "results.csv"), rows, {("D", "D-dnf")})


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
    ap.add_argument("--quick", action="store_true", help="tiny sizes and 2 repeats, only to test the script")
    a = ap.parse_args()
    out = a.out if not a.quick else os.path.join(a.out, "_quick")
    os.makedirs(out, exist_ok=True)
    cases = ms.read_cases(a.master)
    repeats = 2 if a.quick else 5
    env = measure.describe_environment()
    env.update(master_release="master_release_v1", group_seed=ms.GROUP_SEED, repeats=repeats, warmup_runs=1,
               dnf_seconds=measure.DNF_SECONDS)
    with open(os.path.join(out, "environment.json"), "w", encoding="utf-8") as f:
        json.dump(env, f, indent=2)
    runners = {"1": round1, "2": round2, "3": round3, "4": round4}
    todo = ["1", "2", "3"] if a.round == "all" else [a.round]
    for r in todo:
        runners[r](a.master, out, cases, repeats, a.quick)


if __name__ == "__main__":
    main()
