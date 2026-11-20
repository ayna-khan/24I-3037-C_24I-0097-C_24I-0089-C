"""Experiments for module G (chains and cuts).

    python experiments/runG.py --master PATH/TO/MASTER --round 1
    python experiments/runG.py --master PATH/TO/MASTER --round all

Rounds (each has an entry in prediction_log.md (section "Module G") that is written BEFORE the round is run):
    1  growth in n of the chain DP and the memoised recursion, n = 10 ... 640 matrices          (about 10 minutes: the recursion at n = 640)
    2  growth in L of the drum DP, the memoised recursion and the greedy cut, L = 63 ... 2000
    3  quality: greedy cut against DP on 62 sampled cases, best bracketing against left to right
    4  small inputs: DP and memoised recursion against brute force (chain n = 4 ... 12, drum L = 8 ... 20)

Protocol (Section 7.3, as in experiments/runAD.py and runC.py): one warm-up run, 5 timed runs, median and IQR, one thread (the memoised
recursion uses a helper thread only to get a large stack), garbage collection off while timing, data loading excluded, DNF at 300 s.
Rows are written to results/results.csv: old rows of the same (module, experiment) are replaced, all other rows are kept untouched.
Also written: results/quality-G.csv and results/environmentG.json (results/environment.json and environmentC.json are not touched).
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
from experiments import sampleG as sg  # noqa: E402
from src import measure  # noqa: E402
from src.modules import chains as G  # noqa: E402

SIZES_CHAIN = [10, 20, 40, 80, 160, 320, 640]
SIZES_DRUM = [63, 125, 250, 500, 1000, 2000]
SIZES_SMALL_CHAIN = [4, 6, 8, 10, 12]
SIZES_SMALL_DRUM = [8, 11, 14, 17, 20]
QUALITY_PLAN = [("S", 20), ("M", 20), ("L", 10), ("X", 12)]


def total_ops(o):
    """The `ops` column: all counted operations of the algorithm (not `calls`, not the preprocessing in `pre`)."""
    return o["comparisons"] + o["moves"] + o["items_examined"] + o["cells"] + o["candidates"] + o["enumerated"]


def describe(plan):
    o = plan.ops
    what = f"cost={plan.cost}" if hasattr(plan, "bracketing") else f"price={plan.price}; pieces={len(plan.pieces)}"
    return (f"{what}; comparisons={o['comparisons']}; moves={o['moves']}; items={o['items_examined']}; cells={o['cells']}; "
            f"candidates={o['candidates']}; enumerated={o['enumerated']}; calls={o['calls']}; pre_items={o['pre']['items_examined']}")


def answer(plan):
    return plan.bracketing if hasattr(plan, "bracketing") else plan.pieces


def measure_row(experiment, algorithm, solve, instance, size, repeats, mem_limit_s=8.0):
    """Run solve(deadline) with the protocol of Section 7.3. Returns (results.csv row, plan or None when DNF)."""
    base = dict(module="G", experiment=experiment, algorithm=algorithm, instance=instance, size=size, size2="")
    first = perf_counter()
    try:
        solve(perf_counter() + measure.DNF_SECONDS)                    # also the calibration for batching
    except Exception as exc:
        if type(exc).__name__ != "TimeBudgetExceeded":
            raise
        return dict(base, status="DNF", note="single run passed 300 s; no time recorded"), None
    one = perf_counter() - first
    batch = max(1, math.ceil(0.01 / one)) if one < 0.01 else 1       # tiny runs: time a batch, divide

    def timed(deadline):
        result = None
        for _ in range(batch):
            result = solve(deadline)
        return result

    times, result = measure.time_runs(timed, repeats=repeats, warmup=1)
    if times is None:
        return dict(base, status="DNF", note="a run passed 300 s; no time recorded"), None
    if result.status != "OK":
        raise RuntimeError(f"{experiment} {algorithm} size {size}: status {result.status} ({result.note})")
    med, iqr = measure.median_iqr([t / batch for t in times])
    mem, mem_note = "", ""
    if med * batch <= mem_limit_s:
        mem = measure.peak_memory(solve)
    else:
        mem_note = "memory not measured (tracemalloc too slow at this size)"
    note = describe(result) + (f"; batch={batch}" if batch > 1 else "") + ("; " + mem_note if mem_note else "")
    return dict(base, time_s=f"{med:.9g}", time_iqr_s=f"{iqr:.9g}", ops=total_ops(result.ops), mem_bytes=mem, status="OK", note=note), result


def run_size(experiment, algs, instance, size, repeats, rows, label, exact=None):
    """Measure every algorithm on one instance; mark in the notes whether the exact methods gave the same answer.

    `exact` lists the algorithms whose answers must be identical (default: all); the greedy cut is not one of them.
    """
    names = [name for name, _ in algs]
    exact = names if exact is None else exact
    first_row = len(rows)
    plans = {}
    for name, solve in algs:
        row, plan = measure_row(experiment, name, solve, instance, size, repeats)
        rows.append(row)
        plans[name] = plan
        print(f"  {label}={size} {name}: {row.get('time_s', row['status'])} s", flush=True)
    done = [plans[n] for n in exact if plans[n] is not None]
    if len(done) >= 2:
        same = int(all(answer(p) == answer(done[0]) for p in done))
        for r in rows[first_row:]:
            if r["algorithm"] in exact and r["status"] == "OK":
                r["note"] += f"; same_answer_all={same}"
        if not same:
            print(f"  WARNING: the exact algorithms gave different answers at {label}={size}", flush=True)


# ------------------------------------------------------------------ rounds
def round1(master, out, cases, repeats, quick):
    rows = []
    sizes = [10, 20, 40] if quick else SIZES_CHAIN
    start = sg.first_sample(cases, "L")
    seq = ms.consecutive_cases(cases, "L", start, 8)
    by_case = sg.read_dims(master, [c["case_id"] for c in seq])
    print(f"[round 1] chains pooled from tier L cases starting at {start}", flush=True)
    for n in sizes:
        dims, joined = sg.pool_dims(seq, by_case, n)
        inst = f"pool L from {start}, {len(joined)} cases"
        algs = [(m, lambda dl, m=m: G.solve_chain(dims, m, dl)) for m in ("dp", "memo")]
        run_size("G-chain-n", algs, inst, n, repeats, rows, "n")
    measure.write_results(os.path.join(out, "results.csv"), rows, {("G", "G-chain-n")})


def round2(master, out, cases, repeats, quick):
    rows = []
    sizes = [63, 125, 250] if quick else SIZES_DRUM
    need = 250 if quick else 2000
    cid, prices = sg.long_drum_case(master, cases, need)
    print(f"[round 2] drums: prefixes of the price table of case {cid} ({len(prices)} prices)", flush=True)
    for length in sizes:
        table = prices[:length]
        inst = f"first {length} prices of case {cid}"
        algs = [(m, lambda dl, m=m: G.solve_drum(table, length, m, dl)) for m in ("dp", "memo", "greedy")]
        run_size("G-drum-L", algs, inst, length, repeats, rows, "L", exact=["dp", "memo"])      # the greedy cut is not an exact method
    measure.write_results(os.path.join(out, "results.csv"), rows, {("G", "G-drum-L")})


def left_to_right_cost(dims):
    """Cost of ((A1 A2) A3) ... An: the running product has p0 rows, the k-th product costs p0 * p(k) * p(k+1)."""
    return sum(dims[0] * dims[k] * dims[k + 1] for k in range(1, len(dims) - 1))


def round3(master, out, cases, repeats, quick):
    plan = [("S", 5), ("M", 3), ("L", 1), ("X", 3)] if quick else QUALITY_PLAN
    chosen = [(t, c) for t, n in plan for c in ms.sample_cases(cases, t, n)]
    ids = [c["case_id"] for _, c in chosen]
    dims, drums, claims = sg.read_dims(master, ids), sg.read_drums(master, ids), sg.read_claims(master)
    rows = []
    for tier, c in chosen:
        cid = c["case_id"]
        d, prices = dims[cid], drums[cid]
        chain = G.solve_chain(d, "dp")
        dp, greedy = G.solve_drum(prices, len(prices), "dp"), G.solve_drum(prices, len(prices), "greedy")
        naive = left_to_right_cost(d)
        claim = claims.get(cid)
        rows.append(dict(tier=tier, case_id=cid, case_no=c["case_no"], matrices=len(d) - 1, chain_opt_cost=chain.cost,
                         chain_left_to_right_cost=naive, left_to_right_over_opt=f"{naive / chain.cost:.6f}" if chain.cost else "",
                         drum_length=len(prices), drum_dp_price=dp.price, drum_greedy_price=greedy.price,
                         greedy_over_dp=f"{greedy.price / dp.price:.6f}" if dp.price else "",
                         greedy_optimal=int(greedy.price == dp.price), dp_pieces=len(dp.pieces), greedy_pieces=len(greedy.pieces),
                         dp_pieces_over_length=f"{len(dp.pieces) / len(prices):.6f}",
                         claim=claim if claim is not None else "", dp_matches_claim=int(dp.price == claim) if claim is not None else ""))
    write_csv(os.path.join(out, "quality-G.csv"), rows)
    print(f"[round 3] quality G: {len(rows)} cases", flush=True)


def round4(master, out, cases, repeats, quick):
    rows = []
    sizes_c = [4, 6, 8] if quick else SIZES_SMALL_CHAIN
    sizes_d = [8, 11, 14] if quick else SIZES_SMALL_DRUM
    start = sg.first_sample(cases, "S")
    seq = ms.consecutive_cases(cases, "S", start, 6)
    by_case = sg.read_dims(master, [c["case_id"] for c in seq])
    print(f"[round 4] chains pooled from tier S cases starting at {start}", flush=True)
    for n in sizes_c:
        dims, joined = sg.pool_dims(seq, by_case, n)
        inst = f"pool S from {start}, {len(joined)} cases"
        algs = [(m, lambda dl, m=m: G.solve_chain(dims, m, dl)) for m in ("dp", "memo", "brute")]
        run_size("G-small-chain", algs, inst, n, repeats, rows, "n")
    m_case = ms.sample_cases(cases, "M", 1)[0]["case_id"]
    prices = sg.read_drums(master, [m_case])[m_case]
    print(f"[round 4] drums: prefixes of the price table of case {m_case}", flush=True)
    for length in sizes_d:
        table = prices[:length]
        inst = f"first {length} prices of case {m_case}"
        algs = [(m, lambda dl, m=m: G.solve_drum(table, length, m, dl)) for m in ("dp", "memo", "greedy", "brute")]
        run_size("G-small-drum", algs, inst, length, repeats, rows, "L", exact=["dp", "memo", "brute"])
    measure.write_results(os.path.join(out, "results.csv"), rows, {("G", "G-small-chain"), ("G", "G-small-drum")})


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--master", required=True, help="folder with the master dataset CSV files")
    ap.add_argument("--round", default="all", help="1, 2, 3, 4 or all")
    ap.add_argument("--out", default=os.path.join(ROOT, "results"))
    ap.add_argument("--quick", action="store_true", help="tiny sizes and 2 repeats, only to test the script (writes to results/_quick)")
    a = ap.parse_args()
    out = a.out if not a.quick else os.path.join(a.out, "_quick")
    os.makedirs(out, exist_ok=True)
    cases = ms.read_cases(a.master)
    repeats = 2 if a.quick else 5
    env = measure.describe_environment()
    env.update(master_release="master_release_v1", group_seed=ms.GROUP_SEED, repeats=repeats, warmup_runs=1,
               dnf_seconds=measure.DNF_SECONDS, module="G")
    with open(os.path.join(out, "environmentG.json"), "w", encoding="utf-8") as f:
        json.dump(env, f, indent=2)
    runners = {"1": round1, "2": round2, "3": round3, "4": round4}
    todo = ["1", "2", "3", "4"] if a.round == "all" else [a.round]
    for r in todo:
        runners[r](a.master, out, cases, repeats, a.quick)


if __name__ == "__main__":
    main()
