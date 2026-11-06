"""makes validator/tests/: valid one-case workbooks and broken copies of them.

    python validator/make_tests.py cases.xlsx

every broken copy has exactly one defect. the test files are checked with --partial (see run_tests.py)
"""
import copy
import os
import sys

from openpyxl import Workbook, load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tests")

# the cases used as valid copies: one small (S) and one medium (M) case
S_CASE, M_CASE = 4, 26


def load_case(path, case_no):
    wb = load_workbook(path, read_only=True)
    sheets, headers = {}, {}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        headers[ws.title] = list(rows[0])
        cid = None
        sheets[ws.title] = []
        for r in rows[1:]:
            if r[0].endswith(f"-{case_no:02d}"):
                sheets[ws.title].append(list(r))
    return headers, sheets


def save(name, headers, sheets):
    wb = Workbook(write_only=True)
    for title, head in headers.items():
        ws = wb.create_sheet(title=title)
        ws.append(head)
        for r in sheets[title]:
            ws.append(r)
    wb.save(os.path.join(OUT, name))


# the defects, one function each
def wrong_pattern_count(s):
    s["radio_patterns"][0][3] += 1


def road_u_ge_v(s):
    r = s["roads"][0]
    r[2], r[3] = r[3], r[2]


def capacity_too_big(s):
    s["cases"][0][5] = sum(c[3] for c in s["crates"])


def wrong_claim(s):
    s["claims"][0][5] += 1


def tour_not_permutation(s):
    s["tour"][2][2] = s["tour"][1][2]


def cover_misses_edge(s):
    s["sensor_cover"].pop(0)
    s["cases"][0][12] -= 1


def road_in_two_waves(s):
    s["waves"].append([s["waves"][0][0], 99, s["waves"][0][2]])
    s["waves"].sort(key=lambda r: (r[0], r[1]))


def penalty_on_hq(s):
    s["locations"][0][3] = 4


def edit_bound_too_low(s):
    s["cases"][0][9] = 0


def disconnect_network(s):
    isolated = s["roads"][0][3]                        # remove every road touching one location
    s["roads"] = [r for r in s["roads"] if isolated not in (r[2], r[3])]
    for i, r in enumerate(s["roads"]):
        r[1] = i
    keep = {r[1] for r in s["roads"]}
    s["waves"] = [w for w in s["waves"] if w[2] in keep]


def alarm_rate_off(s):
    s["incidents"][-1][2] += 3000


def rule_repeats_switch(s):
    r = s["safety_rules"][0]
    r[3] = r[2]


def planted_breaks_rule(s):
    for p in s["safety_planted"]:
        p[2] = 1 - p[2]


def window_too_short(s):
    w = s["windows"][0]
    w[3] = w[2] + 2


def rations_sum_wrong(s):
    s["rations"][0][3] = 1 - s["rations"][0][3]


def duplicate_serial(s):
    s["crates"][1][6] = s["crates"][0][6]


def long_log_part(s):
    s["radio_log"][0][2] = "A" * 10001


def float_in_cell(s):
    s["crates"][0][3] = 3.5


def trap46_unsorted(s):
    c = s["crates"]
    c[0][3], c[-1][3] = c[-1][3], c[0][3]              # weight is no longer sorted
    c[0][5], c[-1][5] = c[-1][5], c[0][5]              # expiry is no longer sorted


def trap47_capacity(s):
    s["cases"][0][5] = 30


def trap48_cheap_shortcut(s):
    for r in s["roads"]:
        if (r[2], r[3]) == (0, 8):
            r[4] = 2


def trap49_not_repetitive(s):
    t = s["radio_log"]
    n = len(t[0][2])
    t[0][2] = "".join("ABCDEFGHIJ"[(i * 7) % 10] for i in range(n // 2)) + t[0][2][n // 2:]


def main():
    src = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    plan = [
        ("valid-S-case", S_CASE, [
            ("S-wrong-pattern-count", wrong_pattern_count), ("S-road-u-ge-v", road_u_ge_v),
            ("S-capacity-too-big", capacity_too_big), ("S-wrong-claim", wrong_claim),
            ("S-tour-not-permutation", tour_not_permutation), ("S-cover-misses-edge", cover_misses_edge),
            ("S-road-in-two-waves", road_in_two_waves), ("S-penalty-on-hq", penalty_on_hq),
            ("S-edit-bound-too-low", edit_bound_too_low), ("S-network-disconnected", disconnect_network)]),
        ("valid-M-case", M_CASE, [
            ("M-alarm-rate-off", alarm_rate_off), ("M-rule-repeats-switch", rule_repeats_switch),
            ("M-planted-breaks-rule", planted_breaks_rule), ("M-window-too-short", window_too_short),
            ("M-rations-sum-wrong", rations_sum_wrong), ("M-duplicate-serial", duplicate_serial),
            ("M-long-log-part", long_log_part), ("M-float-in-cell", float_in_cell)]),
        ("valid-trap46", 46, [("X46-not-monotone", trap46_unsorted)]),
        ("valid-trap47", 47, [("X47-greedy-good-enough", trap47_capacity)]),
        ("valid-trap48", 48, [("X48-cheap-shortcut", trap48_cheap_shortcut)]),
        ("valid-trap49", 49, [("X49-not-repetitive", trap49_not_repetitive)]),
    ]
    for valid_name, case_no, defects in plan:
        headers, sheets = load_case(src, case_no)
        save(valid_name + ".xlsx", headers, sheets)
        for name, fn in defects:
            broken = copy.deepcopy(sheets)
            fn(broken)
            save(name + ".xlsx", headers, broken)
        print(valid_name, "+", len(defects), "broken copies")


if __name__ == "__main__":
    main()
