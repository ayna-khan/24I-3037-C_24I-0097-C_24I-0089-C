"""Readable sample outputs of modules A and D on master-data cases (results/sample-outputs/).

    python experiments/sampleAD.py --master PATH/TO/master_release_v1
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from experiments import mastersample as ms  # noqa: E402
from src.modules import emergencyqueue as D, inventory as A  # noqa: E402


def show_load(title, crates, capacity):
    lines = [f"== {title}: {len(crates)} crates, capacity {capacity} kg =="]
    for name, plan in (("DP (shipped)", A.solve_dp(crates, capacity)), ("ratio greedy (baseline)", A.solve_greedy(crates, capacity))):
        lines.append(f"{name}: status {plan.status}, {len(plan.selected)} crates, weight {plan.total_weight}/{capacity}, "
                     f"value {plan.total_value}, operations {plan.ops}")
        lines.append(f"    crates loaded: {list(plan.selected)}")
    return lines


def show_queue(title, alarms, first=12):
    lines = [f"== {title}: {len(alarms)} alarms =="]
    for name, fn in (("binary heap (shipped)", D.release_heap), ("linear scan (baseline)", D.release_scan)):
        plan = fn(alarms)
        lines.append(f"{name}: status {plan.status}, maximum backlog {plan.max_backlog}, total wait {plan.total_wait}, "
                     f"longest wait {plan.max_wait}")
        lines.append(f"    first {first} releases (alarm id, tick): {list(plan.releases[:first])}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "sample-outputs"))
    a = ap.parse_args()
    cases = ms.read_cases(a.master)
    s_case = ms.sample_cases(cases, "S", 1)[0]
    x47 = [c for c in ms.tier_cases(cases, "X") if c["case_no"] == "47"]
    x_case = [x47[i] for i in range(ms.GROUP_SEED % 7, len(x47), 7)][0]
    l_case = ms.sample_cases(cases, "L", 1)[0]
    ids = [s_case["case_id"], x_case["case_id"], l_case["case_id"]]
    crates, alarms = ms.read_crates(a.master, ids), ms.read_alarms(a.master, ids)
    lines = ["Sample outputs of modules A and D (master_release_v1, group seed 41)", ""]
    lines += show_load(f"module A, tier S case {s_case['case_id']}", crates[s_case["case_id"]], int(s_case["capacity"]))
    lines += [""] + show_load(f"module A, trap 47 case {x_case['case_id']}", crates[x_case["case_id"]], int(x_case["capacity"]))
    lines += [""] + show_queue(f"module D, tier S case {s_case['case_id']}", alarms[s_case["case_id"]])
    lines += [""] + show_queue(f"module D, tier L case {l_case['case_id']}", alarms[l_case["case_id"]])
    lines += ["", "-- infeasible and empty situations are reported, not hidden --",
              f"A, capacity 0: {A.solve_dp(crates[s_case['case_id']], 0).status}, note: {A.solve_dp(crates[s_case['case_id']], 0).note}",
              f"A, no crates: {A.solve_dp([], 50).status}, note: {A.solve_dp([], 50).note}",
              f"D, no alarms: {D.release_heap([]).status}, note: {D.release_heap([]).note}"]
    os.makedirs(a.out, exist_ok=True)
    text = "\n".join(lines) + "\n"
    with open(os.path.join(a.out, "modules-A-D.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
