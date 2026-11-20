"""Samples, pools and readable sample outputs of module C (rescue scheduling).

    python experiments/sampleC.py --master PATH/TO/master_release_v1             sample outputs
    python experiments/sampleC.py --master PATH/TO/master_release_v1 --fixture   rebuilds tests/fixtures/windows-sample.csv

The sampling rules are those of experiments/mastersample.py (group seed 41, positions
seed mod 7, +7, +14, ... of the tier list, master order = row order of cases.csv); the
functions of that file are used as they are. This file adds what module C needs:
  * a reader for windows.csv (streamed, 1.5 million rows);
  * pools: consecutive tier cases are joined, the windows of the i-th case are shifted by
    1440 * i minutes (a case lives inside one day of 1440 minutes, so joined cases never
    overlap in time), and the ids are renumbered 1, 2, 3, ... in the joined order;
    the pool is cut after the first n windows.
runC.py imports these functions.
"""
import argparse
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from experiments import mastersample as ms  # noqa: E402
from src.modules import rescue as C  # noqa: E402

DAY_MINUTES = 1440
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "windows-sample.csv")


def read_windows(master_dir, case_ids):
    """{case_id: [Window, ...]} in file order, for the wanted case ids only."""
    wanted = set(case_ids)
    out = {cid: [] for cid in wanted}
    with open(os.path.join(master_dir, "windows.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["case_id"] in wanted:
                out[r["case_id"]].append(C.Window(int(r["window_id"]), int(r["start"]), int(r["finish"]), int(r["value"])))
    return out


def read_claims(master_dir):
    """{case_id: (window_count_opt, window_value_opt)} of the tier S cases."""
    with open(os.path.join(master_dir, "claims.csv"), newline="", encoding="utf-8") as f:
        return {r["case_id"]: (int(r["window_count_opt"]), int(r["window_value_opt"])) for r in csv.DictReader(f)}


def pool_windows(cases_in_order, windows_by_case, n):
    """(windows, joined case ids) for a pool of exactly n windows, ids 1..n."""
    joined, out = [], []
    for i, c in enumerate(cases_in_order):
        joined.append(c["case_id"])
        shift = DAY_MINUTES * i
        for w in windows_by_case[c["case_id"]]:
            out.append((w.start + shift, w.finish + shift, w.value))
        if len(out) >= n:
            break
    if len(out) < n:
        raise ValueError(f"the cases offered hold only {len(out)} windows, {n} needed")
    return [C.Window(i + 1, s, f, v) for i, (s, f, v) in enumerate(out[:n])], joined


def first_sample(cases, tier):
    return ms.sample_cases(cases, tier, 1)[0]["case_id"]


def trap_sample(cases, case_no, count):
    """Cases of trap `case_no` (tier X), at the sample positions inside that list."""
    pool = [c for c in ms.tier_cases(cases, "X") if c["case_no"] == str(case_no)]
    return [pool[i] for i in range(ms.GROUP_SEED % 7, len(pool), 7)][:count]


# ------------------------------------------------------------ the test fixture
def write_fixture(master, cases):
    """tests/fixtures/windows-sample.csv: 20 tier S cases with their claims, 2 of tier M, 1 of tier L, 1 of each trap case."""
    chosen = [(c, "S") for c in ms.sample_cases(cases, "S", 20)]
    chosen += [(c, "M") for c in ms.sample_cases(cases, "M", 2)]
    chosen += [(c, "L") for c in ms.sample_cases(cases, "L", 1)]
    for no in (46, 47, 48, 49):
        chosen += [(c, "X") for c in trap_sample(cases, no, 1)]
    wins = read_windows(master, [c["case_id"] for c, _ in chosen])
    claims = read_claims(master)
    os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
    with open(FIXTURE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "tier", "case_no", "count_opt", "value_opt", "window_id", "start", "finish", "value"])
        for c, tier in chosen:
            cnt, val = claims.get(c["case_id"], ("", ""))
            for x in wins[c["case_id"]]:
                w.writerow([c["case_id"], tier, c["case_no"], cnt, val, x.window_id, x.start, x.finish, x.value])
    print(f"wrote {FIXTURE}: {len(chosen)} cases")


# ------------------------------------------------------------- sample outputs
def show(title, windows, claim=None):
    lines = [f"== {title}: {len(windows)} windows =="]
    for objective, method, label in (("count", "greedy", "count, earliest-finish greedy (shipped)"),
                                     ("count", "dp", "count, DP with binary search"),
                                     ("value", "dp", "value, DP with binary search (shipped)"),
                                     ("value", "dpquad", "value, plain O(n^2) DP"),
                                     ("value", "greedy", "value, earliest-finish greedy (baseline, ignores values)")):
        p = C.solve(windows, objective, method)
        shown = list(p.chosen) if len(p.chosen) <= 12 else f"{list(p.chosen[:12])} ... ({len(p.chosen)} windows)"
        lines.append(f"{label}: status {p.status}, total {p.total}, operations {ops_text(p.ops)}")
        lines.append(f"    windows: {shown}")
    if claim:
        lines.append(f"claims of the master data: count {claim[0]}, value {claim[1]}")
    return lines


def ops_text(ops):
    keep = {k: v for k, v in ops.items() if v and k != "pre" and k != "calls"}
    return keep or "none"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "sample-outputs"))
    ap.add_argument("--fixture", action="store_true", help="rebuild tests/fixtures/windows-sample.csv and stop")
    a = ap.parse_args()
    cases = ms.read_cases(a.master)
    if a.fixture:
        write_fixture(a.master, cases)
        return
    s_case = ms.sample_cases(cases, "S", 1)[0]
    x_case = trap_sample(cases, 47, 1)[0]
    l_case = ms.sample_cases(cases, "L", 1)[0]
    ids = [s_case["case_id"], x_case["case_id"], l_case["case_id"]]
    wins = read_windows(a.master, ids)
    claims = read_claims(a.master)
    lines = ["Sample outputs of module C (master_release_v1, group seed 41)", ""]
    lines += show(f"tier S case {s_case['case_id']}", wins[s_case["case_id"]], claims.get(s_case["case_id"]))
    lines += [""] + show(f"trap case 47 {x_case['case_id']}", wins[x_case["case_id"]])
    lines += [""] + show(f"tier L case {l_case['case_id']}", wins[l_case["case_id"]])
    all_w = wins[s_case["case_id"]]
    on_day = C.available_on_day(all_w, 3)
    lines += ["", "-- day filter, empty and invalid situations are reported, not hidden --",
              f"S case {s_case['case_id']}: {len(all_w)} windows, {len(on_day)} available on day 3, "
              f"unavailable ids {sorted(w.window_id for w in all_w if w not in on_day)}",
              f"no windows: {C.solve([], 'count').status}, note: {C.solve([], 'count').note}",
              f"all windows unavailable: {C.solve(C.available_on_day([C.Window(5, 0, 10, 4)], 5), 'value').status}",
              f"a window finishing before it starts: {C.solve([(1, 9, 3, 5)], 'count').status}, note: {C.solve([(1, 9, 3, 5)], 'count').note}",
              f"unknown objective: {C.solve(all_w, 'speed').status}, note: {C.solve(all_w, 'speed').note}"]
    os.makedirs(a.out, exist_ok=True)
    text = "\n".join(lines) + "\n"
    with open(os.path.join(a.out, "module-C.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
