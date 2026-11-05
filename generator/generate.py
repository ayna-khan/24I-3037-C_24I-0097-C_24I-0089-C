# generate.py - writes cases.xlsx for LIFELINE
# run: python generator/generate.py --seed 41 --out cases.xlsx
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openpyxl import Workbook

import graph
import pipeline
import radio
import safety_rations
import tour_sensors
import windows_alarms
import claims
import crates as crates_mod
from common import case_id, module_rng, pick_size, study_of, tier_of

SHEETS = [
    ("cases", ["case_id", "group_seed", "case_no", "tier", "scenario", "capacity", "target_0", "target_1",
               "target_2", "edit_bound", "tour_length", "sensor_nodes", "sensor_k", "safety_vars",
               "rations_target"]),
    ("crates", ["case_id", "crate_id", "cat", "weight", "value", "expiry", "serial"]),
    ("locations", ["case_id", "loc_id", "type", "penalty"]),
    ("roads", ["case_id", "road_no", "u", "v", "minutes", "cable"]),
    ("waves", ["case_id", "wave_no", "road_no"]),
    ("radio_log", ["case_id", "part", "text"]),
    ("radio_patterns", ["case_id", "pattern_no", "pattern", "count"]),
    ("radio_reports", ["case_id", "report_a", "report_b"]),
    ("windows", ["case_id", "window_id", "start", "finish", "value"]),
    ("incidents", ["case_id", "alarm_id", "tick", "priority"]),
    ("sites", ["case_id", "site_no", "x", "y"]),
    ("tour", ["case_id", "step", "site_no"]),
    ("pipeline_dims", ["case_id", "idx", "dim"]),
    ("drum_prices", ["case_id", "length", "price"]),
    ("sensor_edges", ["case_id", "u", "v"]),
    ("sensor_cover", ["case_id", "node"]),
    ("safety_rules", ["case_id", "rule_no", "lit_1", "lit_2", "lit_3"]),
    ("safety_planted", ["case_id", "switch", "value"]),
    ("rations", ["case_id", "item", "value", "planted"]),
    ("claims", ["case_id", "cargo_opt", "window_count_opt", "window_value_opt", "drum_opt", "tour_opt",
                "cover_min"]),
]


def build_case(seed, k):
    """makes the rows of case k for every sheet (dict: sheet name -> rows)"""
    cid, tier, study = case_id(seed, k), tier_of(k), study_of(k)
    small = tier == "S"
    rows = {name: [] for name, _ in SHEETS}

    # ---- crates ----
    crates, capacity = crates_mod.make_crates(module_rng(seed, k, "crates"), k, tier, study,
                                     want_greedy_fail=small and k % 2 == 0)
    rows["crates"] = [(cid, *c) for c in crates]

    # ---- network ----
    rng = module_rng(seed, k, "network")
    if k == 48:
        net = graph.make_trap48_network(rng)
    else:
        net = graph.make_network(rng, pick_size(rng, tier, "V"), study, want_costlier=small and k % 2 == 1)
    for i, (t, p) in enumerate(zip(net["types"], net["penalty"])):
        rows["locations"].append((cid, i, t, p))
    for r, (u, v, mins, cable) in enumerate(net["roads"]):
        rows["roads"].append((cid, r, u, v, mins, cable))
    for w, roads in enumerate(net["waves"], start=1):
        rows["waves"] += [(cid, w, r) for r in roads]
    t0, t1, t2 = net["targets"]

    # ---- radio ----
    log, patterns, counts = radio.make_radio(module_rng(seed, k, "radio"), k, tier, study)
    for part, start in enumerate(range(0, len(log), 10000), start=1):
        rows["radio_log"].append((cid, part, log[start:start + 10000]))
    rows["radio_patterns"] = [(cid, i, p, c) for i, (p, c) in enumerate(zip(patterns, counts))]
    rep_a, rep_b, edit_bound = radio.make_reports(module_rng(seed, k, "reports"), tier, log)
    rows["radio_reports"] = [(cid, rep_a, rep_b)]

    # windows and incidents
    wins = windows_alarms.make_windows(module_rng(seed, k, "windows"), k, tier, study)
    rows["windows"] = [(cid, i + 1, s, f, v) for i, (s, f, v) in enumerate(wins)]
    rows["incidents"] = [(cid, a, t, p) for a, t, p in
                         windows_alarms.make_incidents(module_rng(seed, k, "incidents"), k, tier, study)]

    # ---- tour ----
    points, order, tour_len = tour_sensors.make_tour(module_rng(seed, k, "tour"), k, tier)
    rows["sites"] = [(cid, i, x, y) for i, (x, y) in enumerate(points)]
    rows["tour"] = [(cid, step, site) for step, site in enumerate(order)]

    # pipeline and drum
    rng = module_rng(seed, k, "pipeline")
    dims = pipeline.make_pipeline(rng, tier)
    rows["pipeline_dims"] = [(cid, i, d) for i, d in enumerate(dims)]
    prices = pipeline.make_drum(rng, tier)
    rows["drum_prices"] = [(cid, j, p) for j, p in enumerate(prices, start=1)]

    # ---- sensors ----
    n_sensors, edges, cover = tour_sensors.make_sensors(module_rng(seed, k, "sensors"), tier)
    rows["sensor_edges"] = [(cid, u, v) for u, v in edges]
    rows["sensor_cover"] = [(cid, c) for c in cover]

    # ---- safety ----
    nvars, rules, planted = safety_rations.make_safety(module_rng(seed, k, "safety"), k, tier)
    rows["safety_rules"] = [(cid, i, *lits) for i, lits in enumerate(rules)]
    rows["safety_planted"] = [(cid, j + 1, v) for j, v in enumerate(planted)]

    # ---- rations ----
    values, flags, target = safety_rations.make_rations(module_rng(seed, k, "rations"), tier)
    rows["rations"] = [(cid, i, v, f) for i, (v, f) in enumerate(zip(values, flags))]

    # claims only for tier S (cases 0-19)
    if small:
        rows["claims"] = [(cid,
                           crates_mod.knapsack_best([(c[2], c[3]) for c in crates], capacity),
                           claims.best_window_count(wins),
                           claims.best_window_value(wins),
                           pipeline.drum_best(prices),
                           claims.best_tour(points),
                           tour_sensors.vertex_cover_min(n_sensors, edges))]

    rows["cases"] = [(cid, seed, k, tier, study, capacity, t0, t1, t2, edit_bound, tour_len,
                      n_sensors, len(cover), nvars, target)]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=41, help="group number")
    ap.add_argument("--out", default="cases.xlsx")
    args = ap.parse_args()

    wb = Workbook(write_only=True)
    sheets = {}
    for name, header in SHEETS:
        ws = wb.create_sheet(title=name)
        ws.append(header)
        sheets[name] = ws
    for k in range(50):
        rows = build_case(args.seed, k)
        for name, _ in SHEETS:
            for row in rows[name]:
                sheets[name].append(list(row))
        print(f"case {case_id(args.seed, k)} done", flush=True)
    wb.save(args.out)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
