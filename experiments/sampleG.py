"""Samples, pools and readable sample outputs of module G (chains and cuts).

    python experiments/sampleG.py --master PATH/TO/MASTER             sample outputs
    python experiments/sampleG.py --master PATH/TO/MASTER --fixture   rebuilds tests/fixtures/pipeline-sample.csv and drum-sample.csv

The sampling rules are those of experiments/mastersample.py (group seed 41, positions seed mod 7, +7, +14, ...
of the tier list, master order = row order of cases.csv); the functions of that file are used as they are.
This file adds what module G needs:
  * readers for pipeline_dims.csv and drum_prices.csv (streamed) and for the drum claims of tier S;
  * chain pools. Any list of whole numbers >= 1 is a valid chain p0, ..., pn, so the dimension lists of
    consecutive cases of one tier are concatenated (in master order, starting at the first case of the
    sample) and the pool is cut after the first n + 1 dimensions. The statement fixes n <= 300 per case; pools
    go beyond that (n = 640) only for the growth experiment.
  * drum instances. A drum of length L only uses the prices of the lengths 1..L, so the first L prices of a real
    price table are a valid instance of size L. Prices of different cases are never joined (a table of prices
    that rises and then restarts would be no price list). The largest table in the sample is used for all sizes:
    the first case of the seed-41 samples of tier L and then tier X that has at least 2000 prices (case 12-47).
runG.py imports these functions.
"""
import argparse
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from experiments import mastersample as ms  # noqa: E402
from src.modules import chains as G  # noqa: E402

FIX_DIR = os.path.join(ROOT, "tests", "fixtures")
PIPELINE_FIXTURE = os.path.join(FIX_DIR, "pipeline-sample.csv")
DRUM_FIXTURE = os.path.join(FIX_DIR, "drum-sample.csv")


def read_dims(master_dir, case_ids):
    """{case_id: [p0, p1, ..., pn]} (ordered by idx), for the wanted case ids only."""
    wanted = set(case_ids)
    rows = {cid: [] for cid in wanted}
    with open(os.path.join(master_dir, "pipeline_dims.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["case_id"] in wanted:
                rows[r["case_id"]].append((int(r["idx"]), int(r["dim"])))
    return {cid: [d for _, d in sorted(v)] for cid, v in rows.items()}


def read_drums(master_dir, case_ids):
    """{case_id: [price of length 1, price of length 2, ...]} for the wanted case ids only."""
    wanted = set(case_ids)
    rows = {cid: [] for cid in wanted}
    with open(os.path.join(master_dir, "drum_prices.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["case_id"] in wanted:
                rows[r["case_id"]].append((int(r["length"]), int(r["price"])))
    return {cid: [p for _, p in sorted(v)] for cid, v in rows.items()}


def read_claims(master_dir):
    """{case_id: drum_opt} of the tier S cases."""
    with open(os.path.join(master_dir, "claims.csv"), newline="", encoding="utf-8") as f:
        return {r["case_id"]: int(r["drum_opt"]) for r in csv.DictReader(f)}


def pool_dims(cases_in_order, dims_by_case, n):
    """(dims, joined case ids) for a chain of exactly n matrices (n + 1 dimensions)."""
    joined, out = [], []
    for c in cases_in_order:
        joined.append(c["case_id"])
        out.extend(dims_by_case[c["case_id"]])
        if len(out) >= n + 1:
            break
    if len(out) < n + 1:
        raise ValueError(f"the cases offered hold only {len(out)} dimensions, {n + 1} needed")
    return out[:n + 1], joined


def first_sample(cases, tier):
    return ms.sample_cases(cases, tier, 1)[0]["case_id"]


def trap_sample(cases, case_no, count):
    """Cases of trap `case_no` (tier X), at the sample positions inside that list."""
    pool = [c for c in ms.tier_cases(cases, "X") if c["case_no"] == str(case_no)]
    return [pool[i] for i in range(ms.GROUP_SEED % 7, len(pool), 7)][:count]


def long_drum_case(master, cases, need=2000):
    """(case_id, prices) of the first case of the samples of tier L and then tier X (12 cases each) with >= `need` prices."""
    sample = ms.sample_cases(cases, "L", 12) + ms.sample_cases(cases, "X", 12)
    drums = read_drums(master, [c["case_id"] for c in sample])
    for c in sample:
        if len(drums[c["case_id"]]) >= need:
            return c["case_id"], drums[c["case_id"]]
    raise ValueError(f"no case of the samples has {need} prices")


# ------------------------------------------------------------ the test fixtures
def write_fixture(master, cases):
    """20 tier S cases (with the drum claims), 2 of tier M, 1 of tier L, 1 of each trap case 46 to 49."""
    chosen = [(c, "S") for c in ms.sample_cases(cases, "S", 20)]
    chosen += [(c, "M") for c in ms.sample_cases(cases, "M", 2)]
    chosen += [(c, "L") for c in ms.sample_cases(cases, "L", 1)]
    for no in (46, 47, 48, 49):
        chosen += [(c, "X") for c in trap_sample(cases, no, 1)]
    ids = [c["case_id"] for c, _ in chosen]
    dims, drums, claims = read_dims(master, ids), read_drums(master, ids), read_claims(master)
    os.makedirs(FIX_DIR, exist_ok=True)
    with open(PIPELINE_FIXTURE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "tier", "case_no", "idx", "dim"])
        for c, tier in chosen:
            for i, d in enumerate(dims[c["case_id"]]):
                w.writerow([c["case_id"], tier, c["case_no"], i, d])
    with open(DRUM_FIXTURE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "tier", "case_no", "drum_opt", "length", "price"])
        for c, tier in chosen:
            for k, price in enumerate(drums[c["case_id"]], 1):
                w.writerow([c["case_id"], tier, c["case_no"], claims.get(c["case_id"], ""), k, price])
    print(f"wrote {PIPELINE_FIXTURE} and {DRUM_FIXTURE}: {len(chosen)} cases")


# ------------------------------------------------------------- sample outputs
def ops_text(ops):
    keep = {k: v for k, v in ops.items() if v and k not in ("pre", "calls")}
    return keep or "none"


def show_chain(title, dims):
    lines = [f"== {title}: {len(dims) - 1} matrices =="]
    for method, label in (("dp", "bottom-up DP (shipped)"), ("memo", "memoised recursion (baseline)"), ("brute", "brute force (baseline)")):
        p = G.solve_chain(dims, method)
        text = p.bracketing if len(p.bracketing) <= 70 else p.bracketing[:67] + "..."
        lines.append(f"{label}: status {p.status}, cost {p.cost}, operations {ops_text(p.ops)}" + (f" ({p.note})" if p.note else ""))
        if p.status == "OK":
            lines.append(f"    bracketing: {text}")
    return lines


def show_drum(title, prices, length, claim=None):
    lines = [f"== {title}: drum of length {length} =="]
    for method, label in (("dp", "bottom-up DP (shipped)"), ("memo", "memoised recursion (baseline)"),
                          ("greedy", "greedy by price per length (baseline)"), ("brute", "brute force (baseline)")):
        p = G.solve_drum(prices, length, method)
        shown = list(p.pieces) if len(p.pieces) <= 14 else f"{list(p.pieces[:14])} ... ({len(p.pieces)} pieces)"
        lines.append(f"{label}: status {p.status}, price {p.price}, operations {ops_text(p.ops)}" + (f" ({p.note})" if p.note and p.status != 'OK' else ""))
        if p.status == "OK":
            lines.append(f"    pieces: {shown}")
    if claim is not None:
        lines.append(f"claim of the master data: {claim}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "sample-outputs"))
    ap.add_argument("--fixture", action="store_true", help="rebuild the two fixtures in tests/fixtures and stop")
    a = ap.parse_args()
    cases = ms.read_cases(a.master)
    if a.fixture:
        write_fixture(a.master, cases)
        return
    s_case = ms.sample_cases(cases, "S", 1)[0]
    m_case = ms.sample_cases(cases, "M", 1)[0]
    ids = [s_case["case_id"], m_case["case_id"]]
    dims, drums, claims = read_dims(a.master, ids), read_drums(a.master, ids), read_claims(a.master)
    lines = ["Sample outputs of module G (master data, group seed 41)", ""]
    lines += show_chain(f"chain, tier S case {s_case['case_id']}", dims[s_case["case_id"]])
    lines += [""] + show_drum(f"tier S case {s_case['case_id']}", drums[s_case["case_id"]], len(drums[s_case["case_id"]]), claims.get(s_case["case_id"]))
    m_dims = dims[m_case["case_id"]]
    lines += [""] + show_chain(f"chain, tier M case {m_case['case_id']} (brute force refuses)", m_dims)
    m_prices = drums[m_case["case_id"]]
    lines += [""] + show_drum(f"tier M case {m_case['case_id']} (brute force refuses)", m_prices, len(m_prices))
    lines += ["", "-- bad input and refused sizes are reported, not hidden --"]
    for label, plan in (("one dimension", G.solve_chain([5], "dp")), ("a zero dimension", G.solve_chain([3, 0, 4], "dp")),
                        ("a fractional dimension", G.solve_chain([3, 2.5, 4], "dp")), ("drum of length 0", G.solve_drum([1, 2], 0)),
                        ("a missing price", G.solve_drum([1, 2], 3)), ("greedy for a chain", G.solve_chain([2, 3, 4], "greedy")),
                        ("brute force on 30 matrices", G.solve_chain([2] * 31, "brute")),
                        ("memoised recursion 30,000 deep", G.solve_drum([1] * 30000, 30000, "memo"))):
        lines.append(f"{label}: status {plan.status}, note: {plan.note}")
    os.makedirs(a.out, exist_ok=True)
    text = "\n".join(lines) + "\n"
    with open(os.path.join(a.out, "module-G.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
